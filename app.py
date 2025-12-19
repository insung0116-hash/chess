import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Ultimate Chess Pro", page_icon="♟️", layout="wide")

# --- 스타일(CSS) 커스텀 ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    
    /* 1. 버튼(체스칸) 스타일: 꽉 찬 느낌 */
    div.stButton > button {
        width: 60px !important;
        height: 60px !important;
        font-size: 52px !important;  /* 말 크기 대폭 확대 */
        padding: 0px !important;
        padding-bottom: 8px !important; /* 시각적 중심 보정 */
        margin: 0px !important;
        border-radius: 0px !important; /* 완전 사각형 */
        border: none !important;
        line-height: 1 !important;
        background-color: transparent !important; /* 배경색은 상위 컨테이너 등에서 처리 불가하므로 기본값 덮어쓰기 위해 투명도 고려 */
    }
    
    /* 버튼 클릭 시/포커스 시 */
    div.stButton > button:focus {
        border: 4px solid #e6bf00 !important; /* 강조 테두리 두껍게 */
        color: black !important;
        z-index: 99; /* 다른 요소보다 위에 표시 */
        transform: scale(1.02);
    }

    /* 2. 좌표 텍스트 스타일 */
    .coord-text {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 60px; /* 버튼 높이와 동일하게 */
        font-size: 18px;
        font-weight: bold;
        color: #333;
    }
    
    .coord-header {
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 5px;
    }

    /* 3. 컬럼 간격 완전 제거 */
    [data-testid="column"] {
        padding: 0 !important;
        gap: 0 !important;
        min-width: 0 !important;
    }
    
    /* 모바일 대응 */
    @media (max-width: 700px) {
        div.stButton > button {
            width: 40px !important; height: 40px !important; font-size: 32px !important;
        }
        .coord-text { height: 40px; font-size: 14px; }
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'msg' not in st.session_state:
    st.session_state.msg = "환영합니다! 게임을 시작하세요."
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

def show_hint():
    if not stockfish_path: return
    with st.spinner("생각 중..."):
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        res = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
        st.session_state.hint_move = res.move
        st.session_state.msg = f"추천: {st.session_state.board.san(res.move)}"
        engine.quit()

# ================= UI 구성 =================
st.title("♟️ Ultimate Chess Pro")

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
    if st.button("💡 힌트"): show_hint(); st.rerun()
    if st.button("⬅️ 무르기"):
        if len(st.session_state.board.move_stack) >= 2:
            st.session_state.board.pop(); st.session_state.board.pop(); st.rerun()

# --- 메인 보드 렌더링 ---
col_board, col_right = st.columns([2, 1])

with col_board:
    # 흑백 진영에 따른 순서 결정
    is_white = st.session_state.player_color == chess.WHITE
    ranks = range(7, -1, -1) if is_white else range(8)
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['a','b','c','d','e','f','g','h'] if is_white else ['h','g','f','e','d','c','b','a']

    # 1. 상단 좌표 (File: a b c...)
    # 레이아웃: [빈칸(좌표용)] + [8칸] + [빈칸]
    header_cols = st.columns([0.6] + [1]*8 + [0.6], gap="small")
    for i, label in enumerate(file_labels):
        header_cols[i+1].markdown(f"<div class='coord-header'>{label.upper()}</div>", unsafe_allow_html=True)

    # 2. 보드 본문 (Rank + 8 Buttons + Rank)
    for rank in ranks:
        # 레이아웃: [좌측좌표] + [8칸] + [우측좌표]
        row_cols = st.columns([0.6] + [1]*8 + [0.6], gap="0")
        
        # 좌측 좌표 (1~8)
        rank_label = str(rank + 1)
        row_cols[0].markdown(f"<div class='coord-text'>{rank_label}</div>", unsafe_allow_html=True)
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            # 버튼 그리기
            # CSS를 통해 크기는 60px, 폰트는 52px로 강제됨
            if row_cols[i+1].button(symbol, key=f"btn_{sq}"):
                handle_click(sq)
                st.rerun()

        # 우측 좌표 (1~8) - 대칭을 위해
        row_cols[-1].markdown(f"<div class='coord-text'>{rank_label}</div>", unsafe_allow_html=True)

    # 3. 하단 좌표 (File: a b c...)
    footer_cols = st.columns([0.6] + [1]*8 + [0.6], gap="small")
    for i, label in enumerate(file_labels):
        footer_cols[i+1].markdown(f"<div class='coord-header'>{label.upper()}</div>", unsafe_allow_html=True)


with col_right:
    st.info(st.session_state.msg)
    
    if st.session_state.board.is_check(): st.error("🔥 체크!")
    if st.session_state.board.is_game_over():
        st.success(f"게임 종료! ({st.session_state.board.result()})")
        if st.button("📊 분석하기"): analyze_game(); st.rerun()

    if st.session_state.analysis_data:
        st.line_chart(st.session_state.analysis_data)
        st.caption("그래프 위쪽: 백 유리 / 아래쪽: 흑 유리")

# AI 턴 실행
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
