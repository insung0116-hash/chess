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
    
    /* 1. 수평/수직 간격 강제 제거 (제일 중요) */
    [data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
        min-width: 0 !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0 !important; /* 버튼 사이 틈 없애기 */
    }

    /* 2. 체스판 버튼 공통 스타일 */
    div.stButton > button {
        width: 100% !important;        /* 컬럼 너비 꽉 채우기 */
        aspect-ratio: 1 / 1;           /* 정사각형 비율 유지 */
        font-size: 40px !important;    /* 말 크기 */
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
    
    /* 3. 체크무늬 색상 구현 (Primary/Secondary 속성 활용) */
    /* 밝은 칸 (Secondary Type) -> 베이지색 */
    div.stButton > button[kind="secondary"] {
        background-color: #f0d9b5 !important;
        color: black !important;
    }
    /* 어두운 칸 (Primary Type) -> 갈색 */
    div.stButton > button[kind="primary"] {
        background-color: #b58863 !important;
        color: black !important;
    }

    /* 4. 선택된 말 / 포커스 효과 (노란색) */
    div.stButton > button:focus {
        background-color: #f7e034 !important;
        border: 2px solid #e6bf00 !important;
        z-index: 10; /* 다른 칸보다 위에 뜨게 */
        transform: scale(1.05); /* 살짝 커짐 */
    }

    /* 5. 좌표 스타일 */
    .coord-rank {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%; /* 버튼 높이와 맞춤 */
        font-weight: bold;
        font-size: 16px;
        color: #555;
    }
    .coord-file {
        text-align: center;
        font-weight: bold;
        font-size: 16px;
        color: #555;
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
# 보드(2) : 정보창(1) 비율
main_col, info_col = st.columns([2, 1])

with main_col:
    # 흑/백 시점에 따라 랭크/파일 순서 결정
    is_white = st.session_state.player_color == chess.WHITE
    ranks = range(7, -1, -1) if is_white else range(8)
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

    # --- 체스판 렌더링 루프 ---
    for rank in ranks:
        # 좌측 좌표(0.5) + 8칸(1씩) 의 비율
        cols = st.columns([0.5] + [1]*8, gap="small")
        
        # 1. 좌측 좌표 (1~8)
        cols[0].markdown(f"<div class='coord-rank'>{rank + 1}</div>", unsafe_allow_html=True)
        
        # 2. 체스칸 (8개)
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀" # 빈 공간은 특수공백
            
            # --- 색상 결정 로직 (중요) ---
            # 체크무늬: (rank + file)이 홀수/짝수냐에 따라 색 결정
            # Streamlit의 type="primary"를 '어두운 갈색칸'으로, "secondary"를 '밝은 베이지칸'으로 둔갑시킴
            is_dark_square = (rank + file) % 2 == 0
            btn_type = "primary" if is_dark_square else "secondary"
            
            # 선택된 칸이나 힌트 칸은 CSS focus가 처리하거나, 여기서 type을 바꿀 수도 있지만
            # CSS :focus 효과가 가장 강력하므로 그대로 둡니다.

            # 버튼 생성
            if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()

    # --- 하단 좌표 (A~H) ---
    # 위와 동일한 비율로 컬럼을 만들고 좌표를 배치
    footer = st.columns([0.5] + [1]*8, gap="small")
    for i, label in enumerate(file_labels):
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

# AI 턴
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
