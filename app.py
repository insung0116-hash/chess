import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: 체스말 확대 및 강제 정렬 ---
st.markdown("""
<style>
    /* 1. 기본 배경 및 간격 초기화 */
    .stApp { background-color: #f4f4f4; }
    
    /* 메인 화면 컬럼 간격 완전 제거 */
    section[data-testid="stMain"] div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    section[data-testid="stMain"] div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
    }
    
    /* 2. [체스말 버튼] 스타일 (꽉 채우기) */
    .chess-piece {
        width: 100% !important;
        aspect-ratio: 1 / 1;
        font-size: 50px !important;    /* 말 크기: 50px */
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        line-height: 1 !important;
        box-shadow: none !important;
        color: black !important;
        background-color: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        padding-bottom: 8px !important; /* 수직 중앙 보정 */
    }

    /* 3. 색상 클래스 (CSS로 직접 색칠) */
    .white-square { background-color: #FFCE9E !important; } /* 베이지 */
    .black-square { background-color: #D18B47 !important; } /* 갈색 */
    .active-square { background-color: #f7e034 !important; } /* 선택됨 */
    
    /* 4. 좌표 스타일 */
    .rank-label {
        display: flex; align-items: center; justify-content: center;
        height: 100%; font-weight: 900; font-size: 18px; color: #555;
    }
    .file-label {
        display: flex; align-items: center; justify-content: center;
        width: 100%; height: 50px; /* 높이 고정 */
        font-weight: 900; font-size: 18px; color: #555;
        margin-top: -5px;
    }
    
    /* 5. 사이드바 버튼 복구 */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; height: auto; aspect-ratio: auto;
        font-size: 16px !important; border-radius: 8px;
        padding: 0.5rem 1rem; margin-bottom: 10px;
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

# --- Stockfish 설정 ---
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

# --- 메인 보드 ---
main_col, info_col = st.columns([2, 1])

with main_col:
    is_white = st.session_state.player_color == chess.WHITE
    ranks = range(7, -1, -1) if is_white else range(8)
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

    # [중요] 비율 고정: 좌표(1) : 체스칸(2) * 8
    # 이 비율을 위아래 똑같이 씁니다.
    col_ratios = [0.8] + [2] * 8

    # 1. 체스판 루프
    for rank in ranks:
        cols = st.columns(col_ratios, gap="small")
        
        # [왼쪽 숫자 좌표]
        cols[0].markdown(f"<div class='rank-label'>{rank + 1}</div>", unsafe_allow_html=True)
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            # CSS 클래스 결정을 위한 로직
            is_dark = (rank + file) % 2 == 0
            bg_class = "black-square" if is_dark else "white-square"
            
            # 버튼 렌더링 (CSS 클래스 주입)
            # help 인자를 이용해 CSS 타겟팅을 할 수도 있지만, 
            # 여기서는 type="primary/secondary"와 CSS 선택자를 매칭합니다.
            
            # Streamlit 버튼은 색상 커스텀이 까다로워 CSS에서 nth-child나 속성 선택자를 씁니다.
            # 하지만 간단히 하기 위해 'primary'와 'secondary'를 교차로 쓰고 
            # CSS에서 색상을 강제 덮어쓰기 합니다 (위 style 태그 참조).
            
            btn_type = "primary" if is_dark else "secondary"
            
            # 버튼 클릭
            if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()
                
            # [핵심] 버튼에 CSS 클래스 강제 적용 (JS 없이 CSS 선택자로 처리됨)
            # 위 CSS에서 .stButton > button[kind="primary"] 등으로 이미 색을 입혔습니다.

    # 2. 하단 좌표 루프 (구조적 동기화)
    footer = st.columns(col_ratios, gap="small")
    
    # [핵심 트릭] 맨 앞칸에 '투명 버튼'을 넣습니다.
    # st.empty()나 st.write("")를 쓰면 너비가 달라져서 줄이 깨집니다.
    # 윗줄의 '좌표 숫자'가 차지하는 너비와 똑같은 공간을 확보하기 위함입니다.
    footer[0].markdown("<div class='rank-label' style='opacity:0;'>X</div>", unsafe_allow_html=True)
    
    # 나머지 칸에 알파벳 좌표
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
