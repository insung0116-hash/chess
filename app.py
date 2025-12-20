import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 사용자님의 '누적 이동' 아이디어 적용 ---
st.markdown("""
<style>
    /* 1. 기본 배경 */
    .stApp { background-color: #f4f4f4; }
    
    /* 2. [핵심] 열(Column)별 누적 이동 (등차수열 적용) */
    /* Streamlit의 gap이 누적되는 것을 상쇄하기 위해 뒤로 갈수록 더 많이 당깁니다 */
    
    /* 2번째 열 (체스판 A열) -> -40px */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2) { margin-left: -100px !important; }
    
    /* 3번째 열 (체스판 B열) -> -80px */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(3) { margin-left: -200px !important; }
    
    /* 4번째 열 -> -120px */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(4) { margin-left: -300px !important; }
    
    /* 5번째 열 -> -160px */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(5) { margin-left: -400px !important; }
    
    /* 6번째 열 -> -200px */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(6) { margin-left: -500px !important; }
    
    /* 7번째 열 -> -240px */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(7) { margin-left: -600px !important; }
    
    /* 8번째 열 -> -280px */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(8) { margin-left: -700px !important; }
    
    /* 9번째 열 (체스판 H열) -> -320px */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(9) { margin-left: -800px !important; }

    /* 3. 공통 레이아웃 정리 */
    div[data-testid="column"] {
        padding: 0px !important;
        min-width: 0px !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        padding: 0px !important;
        overflow: visible !important; /* 당겨진 요소가 잘리지 않도록 */
    }

    /* 4. 체스말 버튼 (2.0배 확대) */
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1;
        
        font-size: 45px !important; 
        transform: scale(2.0) !important;
        transform-origin: center center !important;
        
        color: #000000 !important;
        text-shadow: 
            1.5px 0 #fff, -1.5px 0 #fff, 0 1.5px #fff, 0 -1.5px #fff,
            1px 1px #fff, -1px -1px #fff, 1px -1px #fff, -1px 1px #fff !important;
            
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        line-height: 1 !important;
        overflow: visible !important;
        padding-bottom: 8px !important; 
    }

    /* 5. 체스판 색상 */
    section[data-testid="stMain"] div.stButton > button[kind="primary"] {
        background-color: #D18B47 !important;
        border: 0px !important;
    }
    section[data-testid="stMain"] div.stButton > button[kind="secondary"] {
        background-color: #FFCE9E !important;
        border: 0px !important;
    }
    section[data-testid="stMain"] div.stButton > button:focus {
        background-color: #f7e034 !important;
        z-index: 100; /* 겹쳐졌을 때 위로 올라오게 z-index 강화 */
        outline: none !important;
    }

    /* 6. 사이드바 버튼 보호 */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; height: auto; aspect-ratio: auto;
        font-size: 16px !important; transform: none !important;
        text-shadow: none !important;
        padding: 0.5rem 1rem; margin-bottom: 10px; border-radius: 8px;
    }

    /* 7. 좌표 디자인 */
    .rank-label {
        display: flex; align-items: center; justify-content: center;
        height: 100%; font-weight: 900; font-size: 20px; color: #555;
        padding-right: 15px; 
    }
    
    .file-label {
        display: flex; align-items: center; justify-content: center;
        width: 100%; height: 50px; 
        font-weight: 900; font-size: 20px; color: #555;
        margin-top: -5px;
        transform: translateX(-10px); /* 알파벳 미세 조정 */
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

    col_ratios = [0.7] + [2] * 8

    # 1. 체스판
    for rank in ranks:
        cols = st.columns(col_ratios, gap="small")
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

    # 2. 하단 좌표 (CSS가 여기서도 작동하여 자동으로 정렬됩니다)
    footer = st.columns(col_ratios, gap="small")
    footer[0].markdown("""
        <div class="stButton" style="visibility:hidden; pointer-events:none;">
            <button style="font-size:45px !important; transform: scale(1.8); padding:0 !important; border:none !important;">X</button>
        </div>
        """, unsafe_allow_html=True)
    
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
