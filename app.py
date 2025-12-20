import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 틈새 제거에 집중한 스타일링 ---
st.markdown("""
<style>
    /* 1. 기본 배경 및 레이아웃 */
    .stApp { background-color: #e0e0e0; }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem;
        max-width: 1000px !important;
    }

    /* 2. [핵심] 컬럼(가로) 간격 완벽 제거 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
        flex: 1 1 0px !important; /* 컬럼 너비 강제 균등 */
    }

    /* 3. [핵심] 버튼 컨테이너 여백 제거 (세로 간격 제거) */
    div.stButton {
        margin: 0px !important;
        padding: 0px !important;
        width: 100% !important;
        border: 0px !important;
        line-height: 0 !important; /* 높이 영향 제거 */
    }

    /* 4. [핵심] 체스판 버튼 본체 (틈새 메우기) */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        border: none !important;
        border-radius: 0px !important; /* 둥근 모서리 제거 */
        padding: 0px !important;
        margin: 0px !important;
        
        /* 미세한 하얀 선(1px)까지 덮기 위해 150%로 확대 */
        transform: scale(1.5); 
        
        position: relative !important;
        z-index: 1;
        box-shadow: none !important;
    }

    /* 5. 체스말 디자인 */
    div.stButton > button div,
    div.stButton > button p {
        position: absolute !important;
        top: 50% !important;
        left: 50% !important; 
        transform: translate(-50%, -50%) !important;
        width: 100% !important;
        text-align: center !important;
        font-size: min(7vw, 75px) !important;
        line-height: 1 !important;
        font-weight: 400 !important;
        color: black !important;
        text-shadow: 
            1px 1px 0 #fff, -1px 1px 0 #fff, 
            1px -1px 0 #fff, -1px -1px 0 #fff !important;
        pointer-events: none;
    }

    /* 6. 칸 색상 */
    div.stButton > button[kind="primary"] { background-color: #b58863 !important; }
    div.stButton > button[kind="secondary"] { background-color: #f0d9b5 !important; }

    /* 7. 호버 효과 */
    div.stButton > button:hover {
        background-color: #ffe066 !important;
        z-index: 100 !important; /* 호버 시 가장 위로 */
        cursor: pointer;
    }

    /* 8. 좌표 라벨 */
    .rank-label {
        height: 100%; display: flex; align-items: center; justify-content: flex-end;
        font-weight: bold; font-size: 20px; color: #333; padding-right: 15px;
    }
    .file-label {
        width: 100%; text-align: center; font-weight: bold; font-size: 20px; color: #333;
        padding-top: 10px;
    }
    
    /* 9. 제목 스타일 */
    h1 { margin-top: 0px !important; margin-bottom: 20px !important; text-align: center; }

    /* 10. 사이드바 버튼 스타일 (체스판 영향 안 받게 재설정) */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100% !important;
        aspect-ratio: auto !important;
        transform: none !important; /* 확대 취소 */
        background-color: white !important;
        border: 1px solid #ccc !important;
        border-radius: 8px !important;
        margin: 5px 0 !important;
        height: 50px !important;
    }
    section[data-testid="stSidebar"] div.stButton > button * {
        position: static !important;
        transform: none !important;
        font-size: 18px !important;
        font-weight: bold !important;
        color: #333 !important;
    }
    /* 재시작 버튼: 빨강 배경 + 검정 글씨 */
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #ff4b4b !important;
        color: black !important;
        border: none !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] * {
        color: black !important;
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

# 제목
st.title("♟️ Classic Chess")

# --- 사이드바 ---
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

# --- 상태 메시지 (체스판 위) ---
status_container = st.container()
with status_container:
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
        if st.button("📊 이 게임 분석하기", use_container_width=True):
             analyze_game()
             st.rerun()

# --- 체스판 렌더링 (틈새 없음) ---
is_white = st.session_state.player_color == chess.WHITE
ranks = range(7, -1, -1) if is_white else range(8)
files = range(8) if is_white else range(7, -1, -1)
file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

# 열 비율 (좌표칸 + 8개 칸)
col_ratios = [0.5] + [1] * 8

for rank in ranks:
    # gap이 없는 상태에서 columns 생성
    cols = st.columns(col_ratios)
    
    # 왼쪽 랭크 숫자
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

# 하단 파일 알파벳
footer = st.columns(col_ratios)
footer[0].write("")
for i, label in enumerate(file_labels):
    footer[i+1].markdown(f"<div class='file-label'>{label}</div>", unsafe_allow_html=True)

# --- 분석 그래프 ---
if st.session_state.analysis_data:
    st.divider()
    st.markdown("### 📈 형세 분석")
    st.line_chart(st.session_state.analysis_data)

# AI 턴
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
