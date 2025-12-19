import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Real Chess Board", page_icon="♟️", layout="wide")

# --- CSS: 체스판 디자인의 핵심 ---
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp { background-color: #f0f2f6; }
    
    /* 1. 수평/수직 간격 강제 제거 (Gap 삭제) */
    /* Streamlit의 수평 레이아웃 컨테이너를 직접 타격하여 간격을 없앱니다 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0rem !important;
    }
    
    /* 컬럼 내부 패딩 제거 */
    div[data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
        min-width: 0 !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* 2. 체스판 버튼 공통 스타일 */
    div.stButton > button {
        width: 100% !important;        /* 컬럼 너비 꽉 채우기 */
        aspect-ratio: 1 / 1;           /* 정사각형 비율 유지 */
        font-size: 42px !important;    /* 말 크기 */
        padding: 0px !important;
        margin: 0px !important;
        border-radius: 0px !important; /* 모서리 각지게 */
        border: none !important;
        line-height: 1 !important;
        box-shadow: none !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* 3. 체크무늬 색상 구현 */
    div.stButton > button[kind="secondary"] {
        background-color: #f0d9b5 !important; /* 밝은 칸 (베이지) */
        color: black !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #b58863 !important; /* 어두운 칸 (갈색) */
        color: black !important;
        border: none !important;
    }

    /* 4. 선택/포커스 효과 */
    div.stButton > button:focus {
        background-color: #f7e034 !important;
        border: 3px solid #e6bf00 !important;
        z-index: 999; 
        transform: scale(1.02);
        outline: none !important;
    }
    div.stButton > button:active {
        background-color: #f7e034 !important;
        color: black !important;
    }

    /* 5. 좌표 스타일 */
    .coord-rank {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        font-weight: bold;
        font-size: 18px;
        color: #333;
    }
    .coord-file {
        display: flex;
        align-items: flex-start; /* 글자를 위쪽으로 붙여서 보드와 가깝게 */
        justify-content: center; /* 가로 중앙 정렬 */
        width: 100%;
        font-weight: bold;
        font-size: 18px;
        color: #333;
        padding-top: 5px;
    }

</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'msg' not in st.session_state:
    st.session_state.msg = "게임을 시작합니다!"
if 'player_color' not in st.session_state:
    st.session_state.player_color = chess.WHITE
if 'hint_move' not in st.session_state:
    st.session_state.hint_move = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None

# --- Stockfish 경로 ---
stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# --- 로직 함수들 ---
def play_engine_move(skill_level):
    if not stockfish_path or st.session_state.board.is_game_over(): return
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        engine.configure({"Skill Level": skill_level})
        result = engine.play(st.session_state.board, chess.engine.Limit(time=0.2 + (skill_level * 0.05)))
        st.session_state.board.push(result.move)
        st.session_state.hint_move = None
        engine.quit()
        st.session_state.msg = "당신의 차례입니다!"
    except: pass

def analyze_game():
    if not stockfish_path or not st.session_state.board.move_stack: return
    scores = []
    board_copy = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    prog = st.progress(0)
    for i, m in enumerate(st.session_state.board.move_stack):
        board_copy.push(m)
        info = engine.analyse(board_copy, chess.engine.Limit(time=0.05))
        scores.append(info["score"].white().score(mate_score=1000))
        prog.progress((i+1)/len(st.session_state.board.move_stack))
    engine.quit()
    st.session_state.analysis_data = scores
    prog.empty()

def show_hint():
    if not stockfish_path: return
    with st.spinner("계산 중..."):
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        res = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
        st.session_state.hint_move = res.move
        st.session_state.msg = f"추천: {st.session_state.board.san(res.move)}"
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
            st.session_state.msg = "취소됨"
        else:
            m = chess.Move(st.session_state.selected_square, sq)
            if st.session_state.board.piece_at(st.session_state.selected_square).piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
                m.promotion = chess.QUEEN
            if m in st.session_state.board.legal_moves:
                st.session_state.board.push(m)
                st.session_state.selected_square = None
                st.session_state.msg = "이동 완료!"
            else:
                p = st.session_state.board.piece_at(sq)
                if p and p.color == st.session_state.board.turn:
                    st.session_state.selected_square = sq
                    st.session_state.msg = "선택 변경"
                else:
                    st.session_state.msg = "이동 불가"

# ================= UI 구성 =================
st.title("♟️ Real Chess Board")

# --- 사이드바 ---
with st.sidebar:
    st.header("설정")
    color_opt = st.radio("내 진영", ["White (선공)", "Black (후공)"])
    new_color = chess.WHITE if "White" in color_opt else chess.BLACK
    skill = st.slider("AI 레벨", 0, 20, 5)
    
    if st.button("🔄 새 게임", type="primary", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.player_color = new_color
        st.session_state.analysis_data = None
        st.session_state.hint_move = None
        st.rerun()
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("⬅️ 무르기"):
            if len(st.session_state.board.move_stack) >= 2:
                st.session_state.board.pop(); st.session_state.board.pop(); st.rerun()
    with c2:
        if st.button("💡 힌트"): show_hint(); st.rerun()

# --- 메인 화면 레이아웃 ---
main_col, info_col = st.columns([2, 1])

with main_col:
    is_white = st.session_state.player_color == chess.WHITE
    ranks = range(7, -1, -1) if is_white else range(8)
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

    # --- 1. 보드 렌더링 ---
    for rank in ranks:
        # 비율: [좌측좌표(0.5)] + [체스칸 8개(1.0씩)]
        cols = st.columns([0.5] + [1]*8, gap="small")
        
        # 좌측 좌표 (1~8)
        cols[0].markdown(f"<div class='coord-rank'>{rank + 1}</div>", unsafe_allow_html=True)
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            # 색상: (rank+file)%2==0 -> Dark(갈색/Primary)
            is_dark_square = (rank + file) % 2 == 0
            btn_type = "primary" if is_dark_square else "secondary"
            
            if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()

    # --- 2. 하단 좌표 (A~H) 수정됨 ---
    # [중요] 첫 번째 빈 컬럼의 비율을 0.5 -> 0.2로 줄임
    # 이렇게 하면 A~H가 전체적으로 왼쪽으로 당겨져서 정렬이 맞게 됩니다.
    footer = st.columns([0.2] + [1]*8, gap="small")
    
    # 첫 번째 칸은 빈칸(좌표 없음)
    footer[0].write("") 
    
    for i, label in enumerate(file_labels):
        # 좌표 텍스트 출력
        footer[i+1].markdown(f"<div class='coord-file'>{label}</div>", unsafe_allow_html=True)

with info_col:
    st.info(st.session_state.msg)
    
    if st.session_state.board.is_check(): st.error("🔥 체크!")
    if st.session_state.board.is_game_over():
        st.success(f"결과: {st.session_state.board.result()}")
        if st.button("📊 게임 분석", use_container_width=True):
            analyze_game(); st.rerun()

    if st.session_state.analysis_data:
        st.line_chart(st.session_state.analysis_data)
        st.caption("그래프: 위(백 유리) / 아래(흑 유리)")

if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
