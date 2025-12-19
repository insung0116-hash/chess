import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Streamlit Chess Pro", page_icon="♟️", layout="centered")

# --- 스타일(CSS) 대폭 개선 ---
st.markdown("""
<style>
    /* 전체 배경을 깔끔하게 */
    .stApp {
        background-color: #f0f2f6;
    }
    
    /* 체스판 버튼 스타일링 */
    div.stButton > button {
        width: 45px !important;
        height: 45px !important;
        font-size: 30px !important;
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        line-height: 1 !important;
        transition: all 0.2s;
        border-radius: 0px !important; /* 각진 사각형 */
    }

    /* 흑/백 칸 색상 지정 (클래스 부여가 안 되므로 data-testid로 우회하되, 파이썬 로직에서 처리) */
    
    /* 선택된 버튼 효과 */
    div.stButton > button:focus {
        background-color: #f7e034 !important; /* 노란색 강조 */
        border: 2px solid #e6bf00 !important;
        transform: scale(1.05);
        color: black !important;
    }
    
    /* 모바일 대응 */
    [data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        padding: 0 !important;
        gap: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'msg' not in st.session_state:
    st.session_state.msg = "게임을 시작합니다! (White)"
if 'redo_stack' not in st.session_state: # 다시 실행을 위한 스택
    st.session_state.redo_stack = []

# --- Stockfish 엔진 경로 설정 ---
stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# --- AI 턴 함수 (난이도 적용) ---
def play_engine_move(skill_level):
    if not stockfish_path:
        st.warning("⚠️ Stockfish가 설치되지 않았습니다.")
        return
    
    if st.session_state.board.is_game_over():
        return

    with st.spinner(f"🤖 AI(Level {skill_level}) 생각 중..."):
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            
            # 난이도 조절 (Skill Level: 0~20)
            engine.configure({"Skill Level": skill_level})
            
            # 생각하는 시간: 레벨이 높을수록 조금 더 길게
            think_time = 0.1 + (skill_level * 0.05)
            
            result = engine.play(st.session_state.board, chess.engine.Limit(time=think_time))
            st.session_state.board.push(result.move)
            
            # AI가 두면 Redo 기록은 사라져야 함 (새로운 미래가 생김)
            st.session_state.redo_stack = []
            
            engine.quit()
            st.session_state.msg = "당신의 차례입니다!"
        except Exception as e:
            st.error(f"AI 에러: {e}")

# --- 무르기 / 다시 실행 함수 ---
def undo_move():
    if len(st.session_state.board.move_stack) >= 2:
        # AI 수와 내 수를 모두 취소하고 redo 스택에 저장
        m1 = st.session_state.board.pop() # AI
        m2 = st.session_state.board.pop() # 나
        st.session_state.redo_stack.append(m2) # 순서 주의
        st.session_state.redo_stack.append(m1)
        st.session_state.msg = "한 수 물렀습니다. (다시 실행 가능)"
        st.session_state.selected_square = None
    else:
        st.session_state.msg = "더 이상 무를 수 없습니다."

def redo_move():
    if len(st.session_state.redo_stack) >= 2:
        # redo 스택에서 꺼내서 다시 둠
        m1 = st.session_state.redo_stack.pop() # 나
        m2 = st.session_state.redo_stack.pop() # AI
        st.session_state.board.push(m1)
        st.session_state.board.push(m2)
        st.session_state.msg = "다시 실행했습니다."
    else:
        st.session_state.msg = "다시 실행할 기록이 없습니다."

# --- 클릭 핸들러 ---
def handle_click(square_index):
    board = st.session_state.board
    selected = st.session_state.selected_square
    
    # 1. 말 선택
    if selected is None:
        piece = board.piece_at(square_index)
        if piece and piece.color == board.turn:
            st.session_state.selected_square = square_index
            st.session_state.msg = f"선택: {chess.square_name(square_index)}"
        else:
            st.session_state.msg = "내 말을 선택하세요."
            
    # 2. 이동
    else:
        if selected == square_index: # 선택 취소
            st.session_state.selected_square = None
            st.session_state.msg = "선택 취소."
            return

        move = chess.Move(from_square=selected, to_square=square_index)
        if board.piece_at(selected).piece_type == chess.PAWN and chess.square_rank(square_index) in [0, 7]:
            move.promotion = chess.QUEEN

        if move in board.legal_moves:
            board.push(move)
            st.session_state.selected_square = None
            st.session_state.redo_stack = [] # 새로운 수를 두면 redo 불가
            st.session_state.msg = "이동 완료!"
        else:
            # 다른 내 말을 누르면 선택 변경
            piece = board.piece_at(square_index)
            if piece and piece.color == board.turn:
                st.session_state.selected_square = square_index
                st.session_state.msg = f"변경: {chess.square_name(square_index)}"
            else:
                st.session_state.msg = "이동 불가."

# ================= UI 구성 =================
st.title("♟️ Premium Streamlit Chess")

# 상단: 컨트롤 패널
col_level, col_info = st.columns([1, 2])
with col_level:
    skill = st.slider("AI 난이도 (0=바보 ~ 20=신)", 0, 20, 1, help="숫자가 높을수록 강력합니다.")
with col_info:
    st.info(st.session_state.msg)

col_main, col_side = st.columns([1.5, 1])

with col_main:
    # 8x8 보드 그리기 (CSS + Python 조합으로 체크무늬 구현)
    for rank in range(7, -1, -1):
        cols = st.columns(8, gap="small") # gap을 줄여서 밀착
        for file in range(8):
            square_index = chess.square(file, rank)
            piece = st.session_state.board.piece_at(square_index)
            
            # 말 아이콘
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            # 칸 색상 결정 (체크무늬)
            is_light = (rank + file) % 2 != 0
            bg_color = "#f0d9b5" if is_light else "#b58863" # 클래식 우드 스타일
            
            # 선택된 칸은 노란색
            if st.session_state.selected_square == square_index:
                bg_color = "#f7e034"
            
            # 마지막 이동 칸 강조 (옵션)
            if st.session_state.board.move_stack:
                last_move = st.session_state.board.peek()
                if square_index in [last_move.from_square, last_move.to_square]:
                    bg_color = "#cdd26a" # 약간 녹색빛
            
            # 버튼 스타일 주입 (개별 색상 적용을 위해 key 활용 HTML 해킹 대신 st.button의 한계 내에서 최선)
            # Streamlit 버튼은 배경색 직접 지정이 어려우므로, 
            # 어두운 칸은 '검은색 말'처럼 보이게 하거나 하는 꼼수보다는
            # 여기서는 'CSS'로 일괄 적용이 힘들어서, '선택됨' 표시만 확실히 하고 
            # 최대한 깔끔하게 배치하는 데 집중했습니다.
            # (버튼 배경색을 칸마다 다르게 주는 건 순수 Streamlit Python만으론 매우 어렵습니다)
            
            if cols[file].button(symbol, key=f"{square_index}"):
                handle_click(square_index)
                st.rerun()

with col_side:
    st.write("### 게임 메뉴")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ 무르기", use_container_width=True):
            undo_move()
            st.rerun()
    with c2:
        if st.button("➡️ 다시 실행", use_container_width=True):
            redo_move()
            st.rerun()
            
    if st.button("🔄 게임 초기화", type="primary", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.redo_stack = []
        st.session_state.msg = "새 게임!"
        st.rerun()

    st.warning(f"현재 턴: {'백(White)' if st.session_state.board.turn else '흑(Black)'}")
    
    if st.session_state.board.is_check():
        st.error("🔥 체크!!")
    if st.session_state.board.is_game_over():
        st.success(f"게임 종료: {st.session_state.board.result()}")

# AI 턴 실행
if not st.session_state.board.is_game_over() and st.session_state.board.turn == chess.BLACK:
    play_engine_move(skill)
    st.rerun()
