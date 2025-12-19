import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 말 크기 대폭 확대 및 정렬 ---
st.markdown("""
<style>
    /* 1. 배경 및 기본 설정 */
    .stApp { background-color: #f4f4f4; }
    
    /* 2. 메인 보드 레이아웃 강제 정렬 (틈새 제거) */
    section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    section[data-testid="stMain"] div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
    }
    
    /* 3. [핵심] 체스말 버튼 스타일 (초대형 사이즈) */
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1;
        
        /* 폰트 크기: 75px (칸을 거의 꽉 채움) */
        font-size: 75px !important; 
        
        /* 유니코드 폰트 강제 지정 (깨짐 방지 및 볼륨감) */
        font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif !important;
        
        /* 버튼 내부 여백 제거 */
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        
        /* [중요] 수직 정렬 보정 */
        /* 글자가 너무 커서 버튼 밖으로 나가는 것을 방지하고 중앙에 위치시킴 */
        line-height: 1 !important; 
        display: flex;
        align-items: center;
        justify-content: center;
        padding-bottom: 12px !important; /* 바닥에서 살짝 띄움 */
        
        /* 색상 및 테두리 효과 (흑/백 구분) */
        color: #000000 !important;
        text-shadow: 
            2px 0 #fff, -2px 0 #fff, 0 2px #fff, 0 -2px #fff,
            2px 2px #fff, -2px -2px #fff, 2px -2px #fff, -2px 2px #fff !important;
            
        background-color: transparent;
        transition: transform 0.1s; /* 클릭 시 살짝 눌리는 느낌 */
    }

    /* 4. 체스판 바닥 색상 */
    section[data-testid="stMain"] div.stButton > button[kind="primary"] {
        background-color: #D18B47 !important; /* 갈색 */
    }
    section[data-testid="stMain"] div.stButton > button[kind="secondary"] {
        background-color: #FFCE9E !important; /* 베이지 */
    }
    
    /* 포커스(클릭 대기) 효과 */
    section[data-testid="stMain"] div.stButton > button:focus {
        background-color: #f7e034 !important;
        transform: scale(0.95); /* 누르면 살짝 작아짐 */
        z-index: 10;
    }

    /* 5. 사이드바 버튼 복구 (영향 안 받게) */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; height: auto; aspect-ratio: auto;
        font-size: 16px !important; text-shadow: none !important;
        padding: 0.5rem 1rem; margin-bottom: 10px; border-radius: 8px;
        padding-bottom: 0.5rem !important; /* 위의 padding-bottom 덮어쓰기 */
    }

    /* 6. 좌표 폰트 */
    .rank-label {
        display: flex; align-items: center; justify-content: center;
        height: 100%; font-weight: 900; font-size: 20px; color: #555;
    }
    .file-label {
        display: flex; align-items: center; justify-content: center;
        width: 100%; height: 50px; 
        font-weight: 900; font-size: 20px; color: #555;
        margin-top: -5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if 'board' not in st.session_state: st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state: st.session_state.selected_square = None
if 'msg' not in st.session_state: st.session_state.msg = "게임을 시작합니다."
if 'player_color' not in st.session_state: st.session_state.player_color = chess.WHITE
if 'hint_move' not in st.session_state: st.session_state.hint_move = None
if 'analysis_data' not in st.session_state: st.session_state.analysis_data = None
if 'redo_stack' not in st.session_state: st.session_state.redo_stack = []

stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# --- 게임 로직 ---
def play_engine_move(skill_level):
    if not stockfish_path or st.session_state.board.is_game_over(): return
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        engine.configure({"Skill Level": skill_level})
        result = engine.play(st.session_state.board, chess.engine.Limit(time=0.2))
        st.session_state.board.push(result.move)
        st.session_state.redo_stack = [] 
        engine.quit()
        st.session_state.msg = "당신의 차례입니다."
    except: pass

def show_hint():
    if not stockfish_path: return
    with st.spinner(".."):
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        res = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
        st.session_state.hint_move = res.move
        st.session_state.msg = f"힌트: {st.session_state.board.san(res.move)}"
        engine.quit()

def handle_click(sq):
    if st.session_state.board.turn != st.session_state.player_color: return
    st.session_state.hint_move = None
    if st.session_state.selected_square is None:
        p = st.session_state.board.piece_at(sq)
        if p and p.color == st.session_state.board.turn:
            st.session_state.selected_square = sq
            st.session_state.msg = f"선택: {chess.square_name(sq)}"
    else:
        if st.session_state.selected_square == sq:
            st.session_state.selected_square = None
            st.session_state.msg = "취소"
        else:
            m = chess.Move(st.session_state.selected_square, sq)
            if st.session_state.board.piece_at(st.session_state.selected_square).piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
                m.promotion = chess.QUEEN
            if m in st.session_state.board.legal_moves:
                st.session_state.board.push(m)
                st.session_state.selected_square = None
                st.session_state.redo_stack = [] 
                st.session_state.msg = "착수 완료"
            else:
                p = st.session_state.board.piece_at(sq)
                if p and p.color == st.session_state.board.turn:
                    st.session_state.selected_square = sq
                    st.session_state.msg = "선택 변경"
                else:
                    st.session_state.msg = "이동 불가"

def undo_move():
    if len(st.session_state.board.move_stack) >= 2:
        m1 = st.session_state.board.pop(); m2 = st.session_state.board.pop()
        st.session_state.redo_stack.extend([m2, m1])
        st.session_state.msg = "무르기 완료"

def redo_move():
    if len(st.session_state.redo_stack) >= 2:
        m1 = st.session_state.redo_stack.pop(); m2 = st.session_state.redo_stack.pop()
        st.session_state.board.push(m1); st.session_state.board.push(m2)
        st.session_state.msg = "되돌리기 완료"

def analyze_game():
    if not stockfish_path or not st.session_state.board.move_stack: return
    scores = []
    board_copy = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    for m in st.session_state.board.move_stack:
        board_copy.push(m)
        info = engine.analyse(board_copy, chess.engine.Limit(time=0.05))
        scores.append(info["score"].white().score(mate_score=1000))
    engine.quit()
    st.session_state.analysis_data = scores

# ================= UI 레이아웃 =================
st.title("♟️ Classic Chess")

with st.sidebar:
    st.header("설정")
    color_opt = st.radio("진영 선택", ["White (선공)", "Black (후공)"])
    new_color = chess.WHITE if "White" in color_opt else chess.BLACK
    skill = st.slider("AI 레벨", 0, 20, 3)
    
    if st.button("🔄 게임 재시작", type="primary"):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.player_color = new_color
        st.session_state.redo_stack = []
        st.session_state.analysis_data = None
        st.rerun()
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("⬅️ 무르기"): undo_move(); st.rerun()
    with c2: 
        if st.button("➡️ 되살리기"): redo_move(); st.rerun()
    if st.button("💡 힌트"): show_hint(); st.rerun()

# --- 메인 보드 ---
main_col, info_col = st.columns([2, 1])

with main_col:
    is_white = st.session_state.player_color == chess.WHITE
    ranks = range(7, -1, -1) if is_white else range(8)
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

    col_ratios = [0.7] + [2] * 8

    # 1. 체스판 그리기
    for rank in ranks:
        cols = st.columns(col_ratios, gap="small")
        # 숫자 좌표
        cols[0].markdown(f"<div class='rank-label'>{rank + 1}</div>", unsafe_allow_html=True)
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            is_dark = (rank + file) % 2 == 0
            btn_type = "primary" if is_dark else "secondary"
            
            # 버튼 클릭
            if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()

    # 2. 하단 좌표 (너비 맞춤용 투명 버튼)
    footer = st.columns(col_ratios, gap="small")
    footer[0].markdown("""
        <div class="stButton" style="visibility:hidden; pointer-events:none;">
            <button style="font-size:75px !important; padding:0 !important; border:none !important;">X</button>
        </div>
        """, unsafe_allow_html=True)
    
    for i, label in enumerate(file_labels):
        footer[i+1].markdown(f"<div class='file-label'>{label}</div>", unsafe_allow_html=True)

with info_col:
    st.info(st.session_state.msg)
    if st.session_state.board.is_check(): st.error("🔥 체크!")
    if st.session_state.board.is_game_over():
        st.success(f"종료: {st.session_state.board.result()}")
        if st.button("📊 분석"): analyze_game(); st.rerun()
    if st.session_state.analysis_data: st.line_chart(st.session_state.analysis_data)

if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
