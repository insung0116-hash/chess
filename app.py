import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 체스판과 일반 버튼 스타일 분리 ---
st.markdown("""
<style>
    /* 1. 기본 배경 */
    .stApp { background-color: #f4f4f4; }
    
    /* 2. [중요] '메인 화면(체스판)' 영역의 간격만 없애기 */
    /* 사이드바에는 영향을 주지 않도록 stMain 내부만 타겟팅 */
    section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    section[data-testid="stMain"] div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
    }
    
    /* 3. [핵심 수정] 체스말 스타일은 '메인 화면'에 있는 버튼에만 적용 */
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1;           /* 정사각형 유지 */
        font-size: 100px !important;    /* 말 크기 (여기는 커야 함) */
        font-weight: 500 !important;
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        line-height: 1 !important;
        box-shadow: none !important;
        color: #000000 !important;     /* 잉크색 검정 */
        -webkit-text-fill-color: #000000 !important;
    }

    /* 4. 체스판 색상 (메인 화면 버튼만) */
    section[data-testid="stMain"] div.stButton > button[kind="primary"] {
        background-color: #D18B47 !important; /* 갈색 */
    }
    section[data-testid="stMain"] div.stButton > button[kind="secondary"] {
        background-color: #FFCE9E !important; /* 베이지 */
    }
    section[data-testid="stMain"] div.stButton > button:focus {
        background-color: #f7e034 !important;
        box-shadow: inset 0 0 0 4px #c7c734 !important;
        z-index: 10;
    }

    /* 5. [사이드바 복구] 사이드바 버튼은 정상 크기로 되돌림 */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%;
        height: auto;
        aspect-ratio: auto;        /* 정사각형 해제 */
        font-size: 16px !important; /* 글자 크기 정상화 */
        padding: 0.5rem 1rem;
        margin-bottom: 10px;
        border-radius: 8px;        /* 둥근 모서리 복구 */
    }

    /* 6. 좌표 스타일 (작고 깔끔하게 유지) */
    .coord-rank {
        display: flex; align-items: center; justify-content: center;
        height: 100%; font-weight: bold; font-size: 14px; color: #666; padding-right: 5px;
    }
    .coord-file {
        display: flex; justify-content: center; align-items: flex-start;
        font-weight: bold; font-size: 14px; color: #666; margin-top: 5px;
    }
    
    iframe { display: none; }
</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'msg' not in st.session_state:
    st.session_state.msg = "게임을 시작합니다."
if 'player_color' not in st.session_state:
    st.session_state.player_color = chess.WHITE
if 'hint_move' not in st.session_state:
    st.session_state.hint_move = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'redo_stack' not in st.session_state:
    st.session_state.redo_stack = []

# --- Stockfish ---
stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# --- 로직 함수 ---
def play_engine_move(skill_level):
    if not stockfish_path or st.session_state.board.is_game_over(): return
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        engine.configure({"Skill Level": skill_level})
        result = engine.play(st.session_state.board, chess.engine.Limit(time=0.2))
        st.session_state.board.push(result.move)
        st.session_state.redo_stack = [] 
        st.session_state.hint_move = None
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

# --- 사이드바 ---
with st.sidebar:
    st.header("설정")
    color_opt = st.radio("진영 선택", ["White (선공)", "Black (후공)"])
    new_color = chess.WHITE if "White" in color_opt else chess.BLACK
    skill = st.slider("AI 레벨", 0, 20, 3)
    
    # 사이드바 버튼들은 이제 정상 크기로 나옵니다
    if st.button("🔄 게임 재시작", type="primary", use_container_width=True):
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

# --- 메인 화면 (체스판) ---
main_col, info_col = st.columns([2, 1])

with main_col:
    # 이 영역(main_col) 안의 버튼만 CSS로 커지게 설정됨
    is_white = st.session_state.player_color == chess.WHITE
    ranks = range(7, -1, -1) if is_white else range(8)
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

    col_ratios = [0.5] + [1] * 8

    for rank in ranks:
        cols = st.columns(col_ratios, gap="small")
        cols[0].markdown(f"<div class='coord-rank'>{rank + 1}</div>", unsafe_allow_html=True)
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            is_dark = (rank + file) % 2 == 0
            btn_type = "primary" if is_dark else "secondary"
            
            if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()

    footer = st.columns(col_ratios, gap="small")
    footer[0].write("")
    for i, label in enumerate(file_labels):
        footer[i+1].markdown(f"<div class='coord-file'>{label}</div>", unsafe_allow_html=True)

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
