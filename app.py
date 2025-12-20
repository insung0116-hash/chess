import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 좌표와 보드를 분리하고, 보드 내부의 틈을 '삭제' ---
st.markdown("""
<style>
    /* 1. 기본 설정 */
    .stApp { background-color: #dddddd; }
    
    /* 2. 전역 변수 초기화 (가장 강력한 갭 제거) */
    :root {
        --column-gap: 0px !important;
        --row-gap: 0px !important;
    }

    /* 3. 체스판이 들어갈 컨테이너의 패딩/마진 제거 */
    div.block-container {
        padding-top: 2rem;
    }

    /* 4. [핵심] 컬럼(Column) 강제 밀착 */
    div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
        /* Flexbox로 꽉 채우기 */
        flex: 1 1 0% !important; 
    }

    /* 5. 가로 줄(Row) 컨테이너: 틈새 0 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        padding: 0px !important;
        /* 아래 줄과의 간격 제거를 위해 음수 마진 사용 */
        margin-bottom: -15px !important;
    }

    /* 6. 버튼 스타일 (체스판 칸) */
    div.stButton > button {
        width: 100% !important;
        /* 정사각형 비율 강제 */
        aspect-ratio: 1 / 1 !important;
        border-radius: 0px !important;
        border: none !important;
        padding: 0px !important;
        line-height: 1 !important;
        
        /* 폰트 반응형 크기 (화면 꽉 차게) */
        font-size: 2.5vw !important; 
        
        /* 텍스트 그림자 (시인성) */
        text-shadow: 2px 0 #fff, -2px 0 #fff, 0 2px #fff, 0 -2px #fff,
                     1px 1px #fff, -1px -1px #fff, 1px -1px #fff, -1px 1px #fff !important;
        color: black !important;
        
        /* 렌더링 틈새 방지용 box-shadow */
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05); 
    }

    /* 7. 마우스 호버 효과 */
    div.stButton > button:hover {
        background-color: #f7e034 !important;
        transform: scale(1.05);
        z-index: 99;
        position: relative;
        box-shadow: 0 0 10px rgba(0,0,0,0.5) !important;
    }

    /* 8. 체스판 색상 */
    div.stButton > button[kind="primary"] {
        background-color: #D18B47 !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #FFCE9E !important;
    }

    /* 9. 사이드바 및 컨트롤 버튼 스타일 복구 */
    section[data-testid="stSidebar"] div.stButton > button,
    div.control-panel div.stButton > button {
        width: 100% !important;
        height: auto !important;
        aspect-ratio: auto !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        margin-bottom: 10px !important;
        box-shadow: none !important;
        padding: 0.5rem 1rem !important;
    }
    
    /* 10. 좌표 스타일 */
    .rank-text {
        font-size: 20px; font-weight: bold; color: #333;
        display: flex; align-items: center; justify-content: flex-end;
        height: 100%; padding-right: 15px; margin-top: -5px;
    }
    .file-text {
        font-size: 20px; font-weight: bold; color: #333;
        text-align: center; width: 100%; display: block;
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
    # 컨트롤 패널 클래스 추가 (CSS 적용용)
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("⬅️ 무르기"): undo_move(); st.rerun()
    with c2: 
        if st.button("➡️ 되살리기"): redo_move(); st.rerun()
    if st.button("💡 힌트"): show_hint(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 메인 화면 레이아웃 분리 ---
# 중요: 좌표용 컬럼과 체스판용 컬럼을 상위 레벨에서 완전히 분리합니다.
layout_cols = st.columns([0.5, 5, 2]) # [좌표, 체스판, 정보창]

with layout_cols[0]: # 좌측 좌표 (1~8)
    st.write("") # 상단 여백 보정
    st.write("") 
    is_white = st.session_state.player_color == chess.WHITE
    ranks = range(7, -1, -1) if is_white else range(8)
    for rank in ranks:
        # 체스판 줄 간격에 맞추기 위해 투명 이미지나 빈 박스로 높이 조절 가능하나
        # 여기서는 CSS .rank-text로 위치를 잡습니다.
        st.markdown(f"<div class='rank-text' style='height: 60px; line-height: 60px;'>{rank + 1}</div>", unsafe_allow_html=True)

with layout_cols[1]: # 중앙 체스판
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

    # 체스판 그리기 루프
    for rank in ranks:
        # 여기서는 오직 8개의 컬럼만 생성합니다. (좌표 섞지 않음)
        cols = st.columns(8) 
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            is_dark = (rank + file) % 2 == 0
            btn_type = "primary" if is_dark else "secondary"
            
            if cols[i].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()
    
    # 하단 알파벳 좌표
    footer_cols = st.columns(8)
    for i, label in enumerate(file_labels):
        footer_cols[i].markdown(f"<div class='file-text'>{label}</div>", unsafe_allow_html=True)

with layout_cols[2]: # 우측 정보창
    st.info(st.session_state.msg)
    if st.session_state.board.is_check(): st.error("🔥 체크!")
    if st.session_state.board.is_game_over():
        st.success(f"종료: {st.session_state.board.result()}")
        if st.button("📊 분석"): analyze_game(); st.rerun()
    if st.session_state.analysis_data: st.line_chart(st.session_state.analysis_data)

# AI 턴
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
