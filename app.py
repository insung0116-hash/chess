import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 격자 붕괴 방지 및 폰트 유동적 조절 ---
st.markdown("""
<style>
    /* 1. 배경 및 기본 설정 */
    .stApp { background-color: #e0e0e0; }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 850px; /* 전체 폭 제한 */
    }

    /* 2. 컬럼(칸) 설정: 내용물이 커도 절대 늘어나지 않음 */
    div[data-testid="column"] {
        padding: 0 !important; margin: 0 !important;
        min-width: 0px !important; /* 최소 너비 0 허용 */
        overflow: hidden !important; /* 내용물이 넘치면 잘라버림 (칸 크기 사수) */
    }
    
    div[data-testid="stHorizontalBlock"] {
        gap: 0 !important; padding: 0 !important; margin: 0 !important;
    }

    /* 3. 버튼 초기화 */
    div.stButton {
        margin: 0 !important; padding: 0 !important;
        width: 100% !important; border: 0 !important;
        height: auto !important;
    }

    /* 4. 버튼 본체 (정사각형 유지) */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important; /* 1:1 비율 강제 */
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        
        /* 틈새 메우기 */
        transform: scale(1.02);
        
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        
        /* 중요: 글자가 버튼 밖으로 튀어나와도 버튼 크기는 영향 안 받음 */
        overflow: hidden !important; 
    }

    /* 5. [핵심 해결책] 체스말(텍스트) 스타일 */
    div.stButton > button * {
        /* 화면 너비(vw)의 4.5%로 설정. 
           px로 고정하면 화면이 작을 때 칸을 뚫고 나가지만, 
           vw를 쓰면 칸과 함께 글자도 작아집니다. 
        */
        font-size: 4.5vw !important; 
        
        /* PC에서 너무 커지는 것 방지 (최대 55px) */
        @media (min-width: 1000px) {
            font-size: 55px !important;
        }

        line-height: 1 !important; 
        font-weight: 400 !important; 
        color: black !important;
        
        text-shadow: 
            1px 1px 0 #fff, -1px 1px 0 #fff, 
            1px -1px 0 #fff, -1px -1px 0 #fff !important;
            
        /* 위치 미세 조정 */
        position: relative !important;
        top: 5% !important; 
        
        pointer-events: none; 
    }

    /* 6. 색상 */
    div.stButton > button[kind="primary"] {
        background-color: #b58863 !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #f0d9b5 !important;
    }

    /* 7. 호버 */
    div.stButton > button:hover {
        background-color: #ffe066 !important;
        cursor: pointer;
    }
    
    /* 8. 좌표 라벨 */
    .rank-label {
        height: 100%; display: flex; align-items: center; justify-content: flex-end;
        font-weight: bold; font-size: 16px; color: #333; padding-right: 10px;
    }
    .file-label {
        width: 100%; text-align: center; font-weight: bold; font-size: 16px; color: #333;
        padding-top: 5px;
    }

    /* 9. 사이드바 버튼 리셋 (영향 받지 않도록) */
    section[data-testid="stSidebar"] div.stButton > button {
        aspect-ratio: auto !important; 
        background-color: white !important; 
        margin: 5px 0 !important;
        border: 1px solid #ccc !important;
    }
    section[data-testid="stSidebar"] div.stButton > button * {
        font-size: 16px !important;
        top: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 및 로직 ---
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
    st.header("⚙️ 게임 설정")
    color_opt = st.radio("진영 선택", ["White (선공)", "Black (후공)"])
    new_color = chess.WHITE if "White" in color_opt else chess.BLACK
    skill = st.slider("🤖 AI 레벨", 0, 20, 3)
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 무르기", use_container_width=True): undo_move(); st.rerun()
    with col2:
        if st.button("➡️ 되살리기", use_container_width=True): redo_move(); st.rerun()
            
    if st.button("💡 힌트 보기", use_container_width=True): show_hint(); st.rerun()
    st.divider()
    if st.button("🔄 게임 재시작", type="primary", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.player_color = new_color
        st.session_state.redo_stack = []
        st.session_state.analysis_data = None
        st.rerun()

# --- 메인 체스판 ---
is_white = st.session_state.player_color == chess.WHITE
ranks = range(7, -1, -1) if is_white else range(8)
files = range(8) if is_white else range(7, -1, -1)
file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

# 비율: 왼쪽 라벨(0.5) + 보드(1.0 * 8)
col_ratios = [0.5] + [1] * 8

for rank in ranks:
    cols = st.columns(col_ratios)
    # 랭크 라벨 (좌측)
    cols[0].markdown(f"<div class='rank-label'>{rank + 1}</div>", unsafe_allow_html=True)
    
    for i, file in enumerate(files):
        sq = chess.square(file, rank)
        piece = st.session_state.board.piece_at(sq)
        symbol = piece.unicode_symbol() if piece else "⠀"
        
        is_dark = (rank + file) % 2 == 0
        btn_type = "primary" if is_dark else "secondary"
        
        # 버튼 생성
        if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
            handle_click(sq)
            st.rerun()

# 하단 파일 라벨
footer = st.columns(col_ratios)
footer[0].write("")
for i, label in enumerate(file_labels):
    footer[i+1].markdown(f"<div class='file-label'>{label}</div>", unsafe_allow_html=True)

st.divider()
st.info(st.session_state.msg)

# 상태 표시
if st.session_state.board.is_check(): st.error("🔥 체크!")
if st.session_state.board.is_game_over():
    st.success(f"종료: {st.session_state.board.result()}")
    if st.button("📊 분석"): analyze_game(); st.rerun()
if st.session_state.analysis_data: st.line_chart(st.session_state.analysis_data)

# AI 턴
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
