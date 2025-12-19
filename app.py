import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Ultimate Chess", page_icon="♟️", layout="wide")

# --- CSS: 격자 틈새 완벽 제거 (가장 중요) ---
st.markdown("""
<style>
    /* 1. 기본 배경 및 레이아웃 보정 */
    .stApp { background-color: #eef0f3; }
    
    /* 2. 컬럼 간격(Gap) 강제 삭제 */
    /* Streamlit의 수평 배치 컨테이너를 찾아서 간격을 0으로 만듭니다. */
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }
    
    /* 3. 각 컬럼(칸) 내부 여백 삭제 */
    div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 10px !important; /* 최소 너비 제한 해제 */
    }
    
    /* 4. 버튼(체스말) 스타일: 꽉 채우기 */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1;           /* 정사각형 비율 고정 */
        font-size: 38px !important;    /* 말 크기 적절히 조절 */
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important; /* 직각 */
        line-height: 1 !important;
        box-shadow: none !important;   /* 그림자 제거 */
    }

    /* 5. 체스판 색상 테마 (가장 깔끔한 클래식 우드) */
    /* 어두운 칸 (갈색) */
    div.stButton > button[kind="primary"] {
        background-color: #B58863 !important;
        color: white !important;
    }
    /* 밝은 칸 (베이지) */
    div.stButton > button[kind="secondary"] {
        background-color: #F0D9B5 !important;
        color: black !important;
    }

    /* 6. 선택된 칸 강조 (노란색 테두리 대신 배경색 변경) */
    div.stButton > button:focus {
        background-color: #F6F669 !important;
        color: black !important;
        box-shadow: inset 0 0 0 4px #c7c734 !important; /* 안쪽 테두리 효과 */
        z-index: 10;
    }

    /* 7. 좌표 폰트 스타일 */
    .coord-rank {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        font-weight: 800;
        font-size: 16px;
        color: #555;
    }
    .coord-file {
        display: flex;
        justify-content: center;
        padding-top: 4px;
        font-weight: 800;
        font-size: 16px;
        color: #555;
    }
    
    /* iframe 등 숨김 처리 */
    iframe { display: none; }
    
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
if 'redo_stack' not in st.session_state:
    st.session_state.redo_stack = []

# --- Stockfish 설정 ---
stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# --- 기능 함수 ---
def play_engine_move(skill_level):
    if not stockfish_path or st.session_state.board.is_game_over(): return
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        engine.configure({"Skill Level": skill_level})
        result = engine.play(st.session_state.board, chess.engine.Limit(time=0.2 + (skill_level * 0.05)))
        st.session_state.board.push(result.move)
        st.session_state.redo_stack = [] # 새 수 두면 redo 기록 삭제
        st.session_state.hint_move = None
        engine.quit()
        st.session_state.msg = "당신의 차례입니다."
    except: pass

def show_hint():
    if not stockfish_path: return
    with st.spinner("수 읽는 중..."):
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
            st.session_state.msg = "선택 취소"
        else:
            m = chess.Move(st.session_state.selected_square, sq)
            # 폰 승급 (자동 퀸)
            if st.session_state.board.piece_at(st.session_state.selected_square).piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
                m.promotion = chess.QUEEN
            
            if m in st.session_state.board.legal_moves:
                st.session_state.board.push(m)
                st.session_state.selected_square = None
                st.session_state.redo_stack = [] # 가지치기 (새 역사 시작)
                st.session_state.msg = "착수 완료"
            else:
                p = st.session_state.board.piece_at(sq)
                if p and p.color == st.session_state.board.turn:
                    st.session_state.selected_square = sq
                    st.session_state.msg = "선택 변경"
                else:
                    st.session_state.msg = "둘 수 없는 곳입니다."

def undo_move():
    if len(st.session_state.board.move_stack) >= 2:
        m1 = st.session_state.board.pop() # 상대 수
        m2 = st.session_state.board.pop() # 내 수
        st.session_state.redo_stack.append(m2)
        st.session_state.redo_stack.append(m1)
        st.session_state.msg = "무르기 완료"

def redo_move():
    if len(st.session_state.redo_stack) >= 2:
        m1 = st.session_state.redo_stack.pop()
        m2 = st.session_state.redo_stack.pop()
        st.session_state.board.push(m1)
        st.session_state.board.push(m2)
        st.session_state.msg = "다시 실행"
    else:
        st.session_state.msg = "되살릴 수가 없습니다."

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

# ================= UI 레이아웃 =================
st.title("♟️ Ultimate Chess")

# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️ 게임 설정")
    
    # 진영 선택 시 초기화
    new_color_label = st.radio("플레이어 선택", ["백 (White)", "흑 (Black)"])
    new_color = chess.WHITE if "백" in new_color_label else chess.BLACK
    
    skill = st.slider("AI 난이도", 0, 20, 3)
    
    # 새 게임 버튼
    if st.button("🔄 게임 초기화", type="primary", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.player_color = new_color
        st.session_state.redo_stack = []
        st.session_state.analysis_data = None
        st.session_state.hint_move = None
        st.rerun()

    st.divider()
    
    # [복구된 기능] 무르기 / 앞으로 가기
    col_undo, col_redo = st.columns(2)
    with col_undo:
        if st.button("⬅️ 무르기"):
            undo_move()
            st.rerun()
    with col_redo:
        if st.button("➡️ 되살리기"):
            redo_move()
            st.rerun()
            
    if st.button("💡 힌트 보기", use_container_width=True):
        show_hint()
        st.rerun()

# --- 메인 보드 ---
main_col, info_col = st.columns([2, 1])

with main_col:
    # 흑/백 시점에 따른 렌더링 순서
    is_white = st.session_state.player_color == chess.WHITE
    
    # 백일 땐 7~0(위에서 아래로), 흑일 땐 0~7(위에서 아래로)
    ranks = range(7, -1, -1) if is_white else range(8)
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

    # 비율 설정: [좌표 0.7] + [보드 8칸]
    col_ratios = [0.7] + [1] * 8

    # --- 보드 그리기 루프 ---
    for rank in ranks:
        # gap='small'이 기본값이지만 CSS로 0px 강제 적용됨
        cols = st.columns(col_ratios, gap="small")
        
        # 1. 좌측 숫자 좌표
        cols[0].markdown(f"<div class='coord-rank'>{rank + 1}</div>", unsafe_allow_html=True)
        
        # 2. 체스칸 배치
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            # 체스판 색상 로직: (Rank + File)이 짝수면 Dark, 홀수면 Light
            # 플레이어 시점과 무관하게 고정된 좌표값 사용 -> 색상 엉킴 방지
            is_dark_square = (rank + file) % 2 == 0
            btn_type = "primary" if is_dark_square else "secondary"
            
            if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()

    # --- 하단 알파벳 좌표 ---
    footer = st.columns(col_ratios, gap="small")
    footer[0].write("") # 맨 앞칸 비우기
    for i, label in enumerate(file_labels):
        footer[i+1].markdown(f"<div class='coord-file'>{label}</div>", unsafe_allow_html=True)

with info_col:
    st.info(st.session_state.msg)
    
    if st.session_state.board.is_check(): st.error("🔥 체크!")
    if st.session_state.board.is_game_over():
        st.success(f"게임 종료: {st.session_state.board.result()}")
        if st.button("📊 분석 그래프 보기", use_container_width=True):
            analyze_game(); st.rerun()

    if st.session_state.analysis_data:
        st.line_chart(st.session_state.analysis_data)
        st.caption("그래프가 위면 백 유리, 아래면 흑 유리")

# AI 턴 자동 실행
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
