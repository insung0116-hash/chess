import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 체스판 스타일 & 말 색상 구분(핵심) ---
st.markdown("""
<style>
    /* 1. 배경 설정 */
    .stApp { background-color: #f4f4f4; }
    
    /* 2. 메인 화면의 컬럼 간격/여백 제거 (칼각 정렬) */
    section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    section[data-testid="stMain"] div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
    }
    
    /* 3. [핵심] 체스말 디자인 (흑백 구분 명확화) */
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1;
        
        /* 폰트 설정 */
        font-size: 55px !important;  /* 말 크기 적절히 조절 */
        font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif !important;
        font-weight: 600 !important;
        
        /* [중요] 색상 구분 로직 */
        color: #000000 !important;   /* 기본 잉크는 검정 */
        
        /* [마법의 CSS] 흰색 외곽선을 두껍게 주어 흑/백을 분리하고 가독성을 높임 */
        text-shadow: 
            2px 0 #fff, -2px 0 #fff, 0 2px #fff, 0 -2px #fff,
            1px 1px #fff, -1px -1px #fff, 1px -1px #fff, -1px 1px #fff !important;
            
        /* 버튼 기본 스타일 제거 */
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        line-height: 1 !important;
        box-shadow: none !important;
        background-color: transparent;
        
        /* 중앙 정렬 */
        display: flex;
        align-items: center;
        justify-content: center;
        padding-bottom: 8px !important;
    }

    /* 4. 체스판 바닥 색상 (갈색/베이지) */
    section[data-testid="stMain"] div.stButton > button[kind="primary"] {
        background-color: #D18B47 !important; /* 진한 갈색 */
    }
    section[data-testid="stMain"] div.stButton > button[kind="secondary"] {
        background-color: #FFCE9E !important; /* 밝은 베이지 */
    }
    
    /* 선택/포커스 효과 */
    section[data-testid="stMain"] div.stButton > button:focus {
        background-color: #f7e034 !important;
        box-shadow: inset 0 0 0 4px #c7c734 !important;
        z-index: 10;
    }

    /* 5. 사이드바 버튼 (정상 크기 복구) */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; height: auto; aspect-ratio: auto;
        font-size: 16px !important; text-shadow: none !important;
        padding: 0.5rem 1rem; margin-bottom: 10px; border-radius: 8px;
    }

    /* 6. 좌표 스타일 */
    .rank-label {
        display: flex; align-items: center; justify-content: center;
        height: 100%; font-weight: 900; font-size: 18px; color: #555;
    }
    .file-label {
        display: flex; align-items: center; justify-content: center;
        width: 100%; height: 50px; 
        font-weight: 900; font-size: 18px; color: #555;
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

    # 비율 설정 (좌표 : 체스판)
    col_ratios = [0.8] + [2] * 8

    # 1. 체스판 그리기
    for rank in ranks:
        cols = st.columns(col_ratios, gap="small")
        # 숫자 좌표
        cols[0].markdown(f"<div class='rank-label'>{rank + 1}</div>", unsafe_allow_html=True)
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            
            # [중요] 말 기호 처리
            # 유니코드는 기본적으로 White(♔:속이 빔), Black(♚:속이 참)으로 구분되어 있습니다.
            # CSS에서 흰색 테두리(text-shadow)를 주었으므로:
            # - White말: 검은 외곽선 + 흰색 그림자 -> 하얗게 보임
            # - Black말: 검은 채움 + 흰색 그림자 -> 검게 보임
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            is_dark = (rank + file) % 2 == 0
            btn_type = "primary" if is_dark else "secondary"
            
            if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()

    # 2. 하단 좌표 (너비 맞춤용 투명 버튼 사용)
    footer = st.columns(col_ratios, gap="small")
    footer[0].markdown("""
        <div class="stButton" style="visibility:hidden; pointer-events:none;">
            <button style="font-size:55px !important; padding:0 !important; border:none !important;">X</button>
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
