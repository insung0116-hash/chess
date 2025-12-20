import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 격자 유지 + 시각적 확대 + 폰트 두께 조절 ---
st.markdown("""
<style>
    /* 1. 기본 배경 */
    .stApp { background-color: #e0e0e0; }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 800px;
    }

    /* 2. 컬럼 및 로우 간격 제거 */
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
        height: auto !important;
    }

    /* 4. 버튼 본체 스타일 (격자 유지 + 틈새 메우기) */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        
        /* 시각적 확대로 틈새 커버 */
        transform: scale(1.03); 
        
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        
        z-index: 1;
    }

    /* 5. [수정] 체스말(텍스트) 스타일: 두께 줄임 */
    div.stButton > button * {
        font-size: min(8vw, 65px) !important; 
        line-height: 0 !important; 
        
        /* [요청 반영] 폰트 두께를 900(Ultra Bold)에서 400(Normal)으로 변경 */
        font-weight: 400 !important; 
        color: black !important;
        
        /* 외곽선도 조금 더 얇게 조정하여 둔탁함 제거 */
        text-shadow: 
            1px 1px 0 #fff, -1px 1px 0 #fff, 
            1px -1px 0 #fff, -1px -1px 0 #fff !important;
            
        position: relative;
        top: -3px; 
    }

    /* 6. 색상 및 줄눈 효과 */
    div.stButton > button[kind="primary"] {
        background-color: #b58863 !important;
        outline: 1px solid #b58863 !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #f0d9b5 !important;
        outline: 1px solid #f0d9b5 !important;
    }

    /* 7. 호버 및 포커스 */
    div.stButton > button:hover {
        background-color: #ffe066 !important;
        outline: 2px solid #ffe066 !important;
        z-index: 100 !important;
        cursor: pointer;
        transform: scale(1.1) !important;
    }
    div.stButton > button:focus {
        background-color: #ffcc00 !important;
        box-shadow: inset 0 0 0 4px #d9534f !important;
        z-index: 50 !important;
    }

    /* 8. 좌표 스타일 */
    .rank-label {
        height: 100%; display: flex; align-items: center; justify-content: flex-end;
        font-weight: bold; font-size: 20px; color: #333; padding-right: 15px;
    }
    .file-label {
        width: 100%; text-align: center; font-weight: bold; font-size: 20px; color: #333;
        padding-top: 10px;
    }
    
    /* 9. 사이드바 버튼 스타일 */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100% !important; margin: 5px 0 !important;
        aspect-ratio: auto !important; 
        background-color: white !important; border: 1px solid #ccc !important;
        box-shadow: none !important; transform: none !important;
        outline: none !important;
        padding: 0.5rem !important;
    }
    section[data-testid="stSidebar"] div.stButton > button * {
        font-size: 16px !important; line-height: 1.5 !important; top: 0; font-weight: normal !important;
        text-shadow: none !important;
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

# [수정됨] 모든 설정 및 컨트롤 버튼을 사이드바로 이동
with st.sidebar:
    st.header("⚙️ 게임 설정")
    
    # 진영 선택
    color_opt = st.radio("진영 선택", ["White (선공)", "Black (후공)"])
    new_color = chess.WHITE if "White" in color_opt else chess.BLACK
    
    # 난이도
    skill = st.slider("🤖 AI 레벨", 0, 20, 3)
    
    st.divider()
    
    # 게임 제어 버튼들 (사이드바에 통합)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 무르기", use_container_width=True): 
            undo_move()
            st.rerun()
    with col2:
        if st.button("➡️ 되살리기", use_container_width=True): 
            redo_move()
            st.rerun()
            
    if st.button("💡 힌트 보기", use_container_width=True): 
        show_hint()
        st.rerun()
        
    st.divider()
    
    if st.button("🔄 게임 재시작", type="primary", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.player_color = new_color
        st.session_state.redo_stack = []
        st.session_state.analysis_data = None
        st.rerun()

# --- 메인 체스판 ---
is_white = st.session_state.player_color == chess.WHITE
ranks = range(7, -1, -1) if is_white else range(8)
files = range(8) if is_white else range(7, -1, -1)
file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

# 비율 설정
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
        
        if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
            handle_click(sq)
            st.rerun()

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
