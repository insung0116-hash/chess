import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 격자 구조 복구 + 시각적 확대 전략 ---
st.markdown("""
<style>
    /* 1. 기본 배경 */
    .stApp { background-color: #e0e0e0; }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 800px;
    }

    /* 2. 컬럼 및 로우 간격 제거 (물리적 틈 제거) */
    div[data-testid="column"] {
        padding: 0 !important; margin: 0 !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0 !important; padding: 0 !important; margin: 0 !important;
    }

    /* 3. 버튼 컨테이너 초기화 */
    div.stButton {
        margin: 0 !important; padding: 0 !important;
        width: 100% !important; border: 0 !important;
        /* 버튼 높이를 강제로 통일하여 계단 현상 방지 */
        height: auto !important;
    }

    /* 4. [핵심] 버튼 본체 스타일 (격자 복구) */
    div.stButton > button {
        width: 100% !important;  /* 115% 제거 -> 100%로 정위치 */
        aspect-ratio: 1 / 1 !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin: 0 !important; /* 마진 0으로 격자 딱 맞춤 */
        
        /* [중요] 격자는 유지하되, 시각적으로만 3% 확대하여 미세한 틈을 덮어버림 */
        transform: scale(1.03); 
        
        /* 내용물 정렬 */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        
        z-index: 1;
    }

    /* 5. [체스말 크기] 내부 텍스트 강제 확대 */
    div.stButton > button * {
        /* 폰트 크기: 버튼의 70% 정도를 차지하도록 설정 */
        font-size: min(8vw, 65px) !important; 
        
        /* 줄 간격을 0으로 만들어 높이 왜곡 방지 */
        line-height: 0 !important; 
        
        /* 폰트 굵기 및 외곽선 */
        font-weight: 900 !important;
        color: black !important;
        
        /* 텍스트 외곽선 (가독성) */
        text-shadow: 
            2px 2px 0 #fff, -2px 2px 0 #fff, 
            2px -2px 0 #fff, -2px -2px 0 #fff !important;
            
        /* 미세 위치 조정 (이모지 특성상 살짝 위로 쏠리는 것 보정) */
        position: relative;
        top: -3px; 
    }

    /* 6. 색상 및 줄눈 효과 */
    div.stButton > button[kind="primary"] {
        background-color: #b58863 !important;
        /* 버튼 자체의 색상으로 경계선 확장 */
        outline: 1px solid #b58863 !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #f0d9b5 !important;
        outline: 1px solid #f0d9b5 !important;
    }

    /* 7. 마우스 호버 및 클릭 효과 */
    div.stButton > button:hover {
        background-color: #ffe066 !important;
        outline: 2px solid #ffe066 !important;
        z-index: 100 !important; /* 호버 시 맨 위로 */
        cursor: pointer;
        transform: scale(1.1) !important; /* 호버 시 조금 더 커짐 */
    }
    div.stButton > button:focus {
        background-color: #ffcc00 !important;
        box-shadow: inset 0 0 0 4px #d9534f !important;
        z-index: 50 !important;
    }

    /* 8. 좌표 및 외부 UI 정리 */
    .rank-label {
        height: 100%; display: flex; align-items: center; justify-content: flex-end;
        font-weight: bold; font-size: 20px; color: #333; padding-right: 15px;
    }
    .file-label {
        width: 100%; text-align: center; font-weight: bold; font-size: 20px; color: #333;
        padding-top: 10px;
    }
    
    /* 컨트롤 버튼 등 다른 버튼은 정상 크기로 유지 */
    .control-area div.stButton > button, 
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100% !important; margin: 5px 0 !important;
        aspect-ratio: auto !important; 
        background-color: white !important; border: 1px solid #ccc !important;
        box-shadow: none !important; transform: none !important;
        outline: none !important;
    }
    .control-area div.stButton > button *,
    section[data-testid="stSidebar"] div.stButton > button * {
        font-size: 16px !important; line-height: 1.5 !important; top: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 및 기본 설정 ---
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

# --- 메인 체스판 ---
is_white = st.session_state.player_color == chess.WHITE
ranks = range(7, -1, -1) if is_white else range(8)
files = range(8) if is_white else range(7, -1, -1)
file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

# 좌표와 체스판 비율
col_ratios = [0.5] + [1] * 8

for rank in ranks:
    cols = st.columns(col_ratios)
    cols[0].markdown(f"<div class='rank-label'>{rank + 1}</div>", unsafe_allow_html=True)
    
    for i, file in enumerate(files):
        sq = chess.square(file, rank)
        piece = st.session_state.board.piece_at(sq)
        symbol = piece.unicode_symbol() if piece else "⠀"
        
        is_dark = (rank + file) % 2 == 0
        btn_type = "primary" if is_dark else "secondary"
        
        # 버튼 생성 (빈 칸일 때도 공간 유지)
        if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
            handle_click(sq)
            st.rerun()

# 하단 알파벳
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
