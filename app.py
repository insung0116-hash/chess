import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: [핵심] Streamlit 그리드 시스템 강제 무력화 ---
st.markdown("""
<style>
    /* 1. 기본 배경 및 변수 초기화 */
    .stApp { background-color: #f4f4f4; }
    :root { --column-gap: 0px !important; }

    /* 2. [가로 해결] 컬럼(Column) 간격 강제 제거 */
    /* Streamlit이 계산한 width를 무시하고 flex-grow로 꽉 채웁니다 */
    div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        gap: 0px !important;
        min-width: 0px !important;
        flex: 1 1 auto !important; /* 강제로 늘려서 빈 공간 없앰 */
    }

    /* 3. [가로 해결] 가로 줄(Row) 컨테이너 설정 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        padding: 0px !important;
        margin-bottom: -18px !important; /* 세로 줄 간격 당기기 */
        display: flex !important; /* Flexbox 강제 적용 */
        justify-content: center !important; /* 중앙 정렬 */
    }

    /* 4. 버튼(체스판 칸) 스타일 */
    div.stButton {
        padding: 0px !important;
        margin: 0px !important;
        width: 100% !important;
        border: 0px !important;
    }
    
    div.stButton > button {
        /* 너비 100%로 꽉 채움 (Flex가 이미 붙여놓음) */
        width: 100% !important;
        aspect-ratio: 1 / 1 !important; /* 정사각형 유지 */
        
        /* 폰트 및 디자인 */
        font-size: 3vw !important; /* 화면 크기에 따라 글자 크기 조절 */
        line-height: 1 !important;
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        
        /* 텍스트 스타일 */
        color: #000000 !important;
        text-shadow: 
            1px 0 #fff, -1px 0 #fff, 0 1px #fff, 0 -1px #fff !important;
    }

    /* 5. 마우스 호버 효과 */
    div.stButton > button:hover {
        background-color: #f7e034 !important;
        transform: scale(1.02);
        z-index: 10;
        position: relative;
    }

    /* 6. 체스판 색상 */
    div.stButton > button[kind="primary"] {
        background-color: #D18B47 !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #FFCE9E !important;
    }

    /* 7. 좌표 폰트 스타일 */
    .rank-label {
        font-weight: bold; font-size: 20px; color: #555;
        display: flex; align-items: center; justify-content: center; height: 100%;
        margin-top: -5px;
    }
    .file-label {
        font-weight: bold; font-size: 20px; color: #555;
        display: flex; justify-content: center; width: 100%;
    }

    /* 8. 사이드바 등 외부 버튼은 정상적으로 */
    section[data-testid="stSidebar"] div.stButton > button,
    div[data-testid="stVerticalBlock"] > div > button {
        width: auto !important; aspect-ratio: auto !important;
        border-radius: 5px !important; font-size: 16px !important;
        padding: 0.5rem 1rem !important; margin-bottom: 10px !important;
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

# --- 로직 함수들 ---
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

# --- 메인 화면 ---
main_col, info_col = st.columns([2, 1])

with main_col:
    is_white = st.session_state.player_color == chess.WHITE
    ranks = range(7, -1, -1) if is_white else range(8)
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

    # 비율 조정: 왼쪽 좌표용(0.5) + 체스판 8칸(1.0씩)
    # 비율을 1:1:1로 주면 Flexbox가 균등하게 배분하려 노력합니다.
    col_ratios = [0.5] + [1] * 8

    # --- 1. 체스판 루프 ---
    for rank in ranks:
        # gap="small" 조차 제거하고 CSS로 제어합니다. (여기서 gap 인자 생략 시 기본값인데 CSS가 덮음)
        cols = st.columns(col_ratios)
        
        # 숫자 좌표 (왼쪽)
        cols[0].markdown(f"<div class='rank-label'>{rank + 1}</div>", unsafe_allow_html=True)
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            is_dark = (rank + file) % 2 == 0
            btn_type = "primary" if is_dark else "secondary"
            
            # 버튼 렌더링
            if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()

    # --- 2. 하단 좌표 ---
    footer = st.columns(col_ratios)
    footer[0].write("")
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
