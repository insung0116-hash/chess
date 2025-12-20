import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 모든 여백을 0으로 만들고, 줄 간격을 강제로 닫음 ---
st.markdown("""
<style>
    /* 1. 배경 */
    .stApp { background-color: #e0e0e0; }
    
    /* 2. 메인 컨테이너 너비 제한 (너무 퍼지지 않게) */
    .block-container {
        max-width: 800px;
        padding-top: 1rem;
        padding-bottom: 5rem;
    }

    /* 3. [핵심] Streamlit의 모든 자동 여백 변수 0으로 초기화 */
    :root {
        --column-gap: 0px !important;
        --row-gap: 0px !important;
    }

    /* 4. 가로 줄(Row) 컨테이너: 줄 사이의 틈(1rem)을 강제로 없앰 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
        /* 아래 줄과의 간격을 없애기 위해 음수 마진 적용 */
        margin-bottom: -8px !important; 
    }

    /* 5. 세로 기둥(Column) 컨테이너: 옆 기둥과의 틈 제거 */
    div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
        flex: 1 !important;
    }

    /* 6. 버튼 컨테이너 초기화 */
    div.stButton {
        padding: 0px !important;
        margin: 0px !important;
        border: 0px !important;
        width: 100% !important;
    }

    /* 7. 버튼 본체 스타일: 꽉 채우기 */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important; /* 정사각형 강제 */
        border-radius: 0px !important;
        border: none !important;
        padding: 0px !important;
        margin: 0px !important;
        
        /* 폰트 설정 */
        font-size: 3vw !important;
        line-height: 1 !important;
        font-weight: bold;
        color: black !important;
        text-shadow: 
            1.5px 1.5px 0 #fff, -1.5px 1.5px 0 #fff, 
            1.5px -1.5px 0 #fff, -1.5px -1.5px 0 #fff !important;
        
        /* 렌더링 최적화 */
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* PC 화면에서 폰트 크기 고정 */
    @media (min-width: 800px) {
        div.stButton > button { font-size: 40px !important; }
    }

    /* 8. 미세한 흰 선(Sub-pixel gap) 제거용 그림자 테두리 */
    div.stButton > button {
        /* 버튼 색상과 같은 색의 그림자를 1px 밖으로 그려서 틈새를 메꿈 */
        box-shadow: 0 0 0 1px rgba(0,0,0,0.05) inset !important; 
    }

    /* 9. 마우스 호버 효과 */
    div.stButton > button:hover {
        background-color: #ffe066 !important;
        z-index: 50;
        transform: scale(1.05); /* 약간 확대 */
        box-shadow: 0 0 10px rgba(0,0,0,0.3) !important;
        cursor: pointer;
    }
    
    /* 10. 선택 효과 */
    div.stButton > button:focus {
        background-color: #ffcc00 !important;
        box-shadow: inset 0 0 0 4px #d9534f !important;
    }

    /* 11. 체스판 색상 */
    div.stButton > button[kind="primary"] {
        background-color: #b58863 !important; /* 갈색 */
    }
    div.stButton > button[kind="secondary"] {
        background-color: #f0d9b5 !important; /* 베이지색 */
    }

    /* 12. 좌표 디자인 */
    .rank-label {
        height: 100%; display: flex; align-items: center; justify-content: flex-end;
        font-weight: bold; font-size: 18px; color: #333; padding-right: 10px;
        margin-top: -3px; /* 높이 미세 보정 */
    }
    .file-label {
        width: 100%; text-align: center; font-weight: bold; font-size: 18px; color: #333;
        padding-top: 5px;
    }
    
    /* 13. 외부 UI (사이드바 등) 정상화 */
    .control-area div.stButton > button, 
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100% !important; margin: 5px 0 !important;
        aspect-ratio: auto !important; font-size: 16px !important;
        background-color: white !important; border: 1px solid #ccc !important;
        box-shadow: none !important;
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
    st.divider()
    if st.button("🔄 게임 재시작", type="primary", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.player_color = new_color
        st.session_state.redo_stack = []
        st.session_state.analysis_data = None
        st.rerun()

st.markdown('<div class="control-area">', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1: 
    if st.button("⬅️ 무르기", use_container_width=True): undo_move(); st.rerun()
with c2: 
    if st.button("➡️ 되살리기", use_container_width=True): redo_move(); st.rerun()
with c3: 
    if st.button("💡 힌트", use_container_width=True): show_hint(); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 메인 보드 ---
is_white = st.session_state.player_color == chess.WHITE
ranks = range(7, -1, -1) if is_white else range(8)
files = range(8) if is_white else range(7, -1, -1)
file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

# 비율
col_ratios = [0.4] + [1] * 8

for rank in ranks:
    # 틈새 제거의 핵심: 모든 st.columns 호출은 하나의 div.row로 감싸짐
    # CSS에서 margin-bottom: -8px로 이 틈을 닫음
    cols = st.columns(col_ratios)
    
    # 왼쪽 좌표
    cols[0].markdown(f"<div class='rank-label'>{rank + 1}</div>", unsafe_allow_html=True)
    
    # 보드 칸
    for i, file in enumerate(files):
        sq = chess.square(file, rank)
        piece = st.session_state.board.piece_at(sq)
        symbol = piece.unicode_symbol() if piece else "⠀"
        
        is_dark = (rank + file) % 2 == 0
        btn_type = "primary" if is_dark else "secondary"
        
        if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
            handle_click(sq)
            st.rerun()

# 하단 좌표
footer = st.columns(col_ratios)
footer[0].write("")
for i, label in enumerate(file_labels):
    footer[i+1].markdown(f"<div class='file-label'>{label}</div>", unsafe_allow_html=True)

st.divider()
st.info(st.session_state.msg)
if st.session_state.board.is_check(): st.error("🔥 체크!")
if st.session_state.board.is_game_over():
    st.success(f"종료: {st.session_state.board.result()}")
    if st.button("📊 분석"): analyze_game(); st.rerun()
if st.session_state.analysis_data: st.line_chart(st.session_state.analysis_data)

if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
