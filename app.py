import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 틈새 제거 및 기물 중앙 정렬 ---
st.markdown("""
<style>
    /* 1. 기본 배경 및 레이아웃 */
    .stApp { background-color: #e0e0e0; }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem;
        max-width: 900px !important;
    }

    /* 2. 컬럼(가로) 간격 완벽 제거 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
        flex: 1 1 0px !important;
    }

    /* 3. 버튼 컨테이너 여백 제거 */
    div.stButton {
        margin: 0px !important;
        padding: 0px !important;
        width: 100% !important;
        border: 0px !important;
    }

    /* 4. 체스판 버튼 본체 */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        border: none !important;
        border-radius: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
        box-shadow: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 5. 체스말 디자인 (Flexbox 중앙 정렬) */
    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div {
        position: static !important;
        transform: none !important;
        font-size: min(5vw, 50px) !important;
        line-height: 1 !important;
        font-weight: normal !important;
        color: #000000 !important;
        pointer-events: none;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 6. 칸 색상 */
    div.stButton > button[kind="primary"] { background-color: #b58863 !important; }
    div.stButton > button[kind="secondary"] { background-color: #f0d9b5 !important; }

    /* 7. 호버 효과 */
    div.stButton > button:hover {
        background-color: #ffe066 !important;
        cursor: pointer;
    }

    /* 8. 좌표 라벨 */
    .rank-label {
        height: 100%; display: flex; align-items: center; justify-content: flex-end;
        font-weight: bold; font-size: 18px; color: #333; padding-right: 10px;
    }
    .file-label {
        width: 100%; text-align: center; font-weight: bold; font-size: 18px; color: #333;
        padding-top: 5px;
    }
    
    /* 9. 제목 스타일 */
    h1 { margin-top: 0px !important; margin-bottom: 20px !important; text-align: center; }

    /* 10. 사이드바 및 프로모션 버튼 스타일 복원 */
    section[data-testid="stSidebar"] div.stButton > button,
    .promo-box div.stButton > button {
        width: 100% !important;
        aspect-ratio: auto !important;
        background-color: white !important;
        border: 1px solid #ccc !important;
        border-radius: 8px !important;
        margin: 5px 0 !important;
        height: 45px !important;
    }
    section[data-testid="stSidebar"] div.stButton > button p,
    section[data-testid="stSidebar"] div.stButton > button span,
    .promo-box div.stButton > button p,
    .promo-box div.stButton > button span {
        font-size: 16px !important;
        font-weight: bold !important;
        color: #333 !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #ff4b4b !important;
        border: none !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] p,
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] span {
        color: white !important;
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
if 'promotion_pending' not in st.session_state: st.session_state.promotion_pending = None

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
    
    # 기물 선택 단계
    if st.session_state.selected_square is None:
        p = st.session_state.board.piece_at(sq)
        if p and p.color == st.session_state.board.turn:
            st.session_state.selected_square = sq
            st.session_state.msg = f"선택: {chess.square_name(sq)}"
    else:
        # 선택 해제
        if st.session_state.selected_square == sq:
            st.session_state.selected_square = None
            st.session_state.msg = "취소"
        else:
            from_sq = st.session_state.selected_square
            piece = st.session_state.board.piece_at(from_sq)
            
            # 프로모션 검사 (폰이 마지막 행에 도달)
            if piece and piece.piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
                test_move = chess.Move(from_sq, sq, promotion=chess.QUEEN)
                if test_move in st.session_state.board.legal_moves:
                    st.session_state.promotion_pending = (from_sq, sq)
                    st.session_state.msg = "승급할 기물을 선택하세요."
                    return

            # 일반 이동 처리
            m = chess.Move(from_sq, sq)
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

def apply_promotion(piece_type):
    if st.session_state.promotion_pending:
        from_sq, to_sq = st.session_state.promotion_pending
        move = chess.Move(from_sq, to_sq, promotion=piece_type)
        st.session_state.board.push(move)
        st.session_state.selected_square = None
        st.session_state.promotion_pending = None
        st.session_state.redo_stack = []
        st.session_state.msg = "승급 완료"

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

# ================= UI 레이아웃 =================

st.title("♟️ Playing Chess with AI")

# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️️ 게임 설정")
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
        st.session_state.promotion_pending = None
        st.rerun()

# --- 상태 메시지 및 프로모션 선택 UI ---
status_container = st.container()
with status_container:
    if st.session_state.promotion_pending:
        st.warning("👑 승급할 기물을 선택하세요:", icon="👑")
        st.markdown("<div class='promo-box'>", unsafe_allow_html=True)
        p_cols = st.columns(4)
        
        # 기물 선택 옵션 (유니코드 기호 포함)
        pieces = [
            ("♛ 퀸", chess.QUEEN),
            ("♜ 룩", chess.ROOK),
            ("♝ 비숍", chess.BISHOP),
            ("♞ 나이트", chess.KNIGHT)
        ]
        
        for idx, (label, piece_type) in enumerate(pieces):
            if p_cols[idx].button(label, key=f"promo_{piece_type}"):
                apply_promotion(piece_type)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        if "체크!" in st.session_state.msg or "이동 불가" in st.session_state.msg:
            st.error(st.session_state.msg, icon="⚠️")
        elif "힌트" in st.session_state.msg:
            st.warning(st.session_state.msg, icon="💡")
        else:
            st.info(st.session_state.msg, icon="📢")

    if st.session_state.board.is_check():
        st.error("🔥 체크! 왕이 위험합니다.", icon="🔥")

    if st.session_state.board.is_game_over():
        st.success(f"🎉 게임 종료: {st.session_state.board.result()}", icon="🏆")

# --- 체스판 렌더링 ---
is_white = st.session_state.player_color == chess.WHITE
ranks = range(7, -1, -1) if is_white else range(8)
files = range(8) if is_white else range(7, -1, -1)
file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

col_ratios = [0.5] + [1] * 8

for rank in ranks:
    cols = st.columns(col_ratios)
    cols[0].markdown(f"<div class='rank-label'>{rank + 1}</div>", unsafe_allow_html=True)
    
    for i, file in enumerate(files):
        sq = chess.square(file, rank)
        piece = st.session_state.board.piece_at(sq)
        
        symbol = piece.unicode_symbol() if piece else "\u2800"
        
        is_dark = (rank + file) % 2 == 0
        btn_type = "primary" if is_dark else "secondary"
        
        if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
            handle_click(sq)
            st.rerun()

# 하단 파일 알파벳
footer = st.columns(col_ratios)
footer[0].write("")
for i, label in enumerate(file_labels):
    footer[i+1].markdown(f"<div class='file-label'>{label}</div>", unsafe_allow_html=True)

# AI 턴
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color and not st.session_state.promotion_pending:
    play_engine_move(skill)
    st.rerun()
