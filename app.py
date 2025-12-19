import streamlit as st
import chess
import chess.engine
import shutil

# --- 페이지 설정 ---
st.set_page_config(page_title="Streamlit Chess V2", page_icon="♟️", layout="wide")

# --- 디자인(CSS) 개선: 버튼 간격 없애고 정사각형 만들기 ---
st.markdown("""
<style>
    /* 컬럼 간격 강제 제거 */
    [data-testid="column"] {
        width: 50px !important;
        flex: 0 0 auto !important;
        min-width: 10px !important;
        padding: 1px !important;
    }
    /* 버튼 모양 정사각형으로 */
    div.stButton > button {
        width: 50px;
        height: 50px;
        font-size: 28px;
        padding: 0px;
        margin: 0px;
        line-height: 1;
        border-radius: 5px;
        border: 1px solid #ccc;
    }
    /* 선택된 버튼 강조 */
    div.stButton > button:focus {
        border: 2px solid red;
        color: red;
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'msg' not in st.session_state:
    st.session_state.msg = "게임을 시작합니다! 흰색(White) 차례입니다."

# --- Stockfish 엔진 설정 ---
stockfish_path = shutil.which("stockfish")

# --- AI 턴 함수 ---
def play_engine_move():
    if not stockfish_path:
        st.warning("⚠️ Stockfish가 설치되지 않았습니다. 혼자 두셔야 합니다.")
        return
    
    # 게임이 끝났으면 두지 않음
    if st.session_state.board.is_game_over():
        return

    with st.spinner("🤖 AI가 생각 중..."):
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            # 0.5초만 생각 (속도 향상)
            result = engine.play(st.session_state.board, chess.engine.Limit(time=0.5))
            st.session_state.board.push(result.move)
            engine.quit()
            st.session_state.msg = "당신의 차례입니다!"
        except Exception as e:
            st.error(f"AI 에러: {e}")

# --- 클릭 이벤트 핸들러 ---
def handle_click(square_index):
    board = st.session_state.board
    selected = st.session_state.selected_square
    
    # 1. 첫 번째 클릭 (말 선택)
    if selected is None:
        piece = board.piece_at(square_index)
        if piece and piece.color == board.turn:
            st.session_state.selected_square = square_index
            st.session_state.msg = f"선택: {chess.square_name(square_index)} ➡️ 어디로 갈까요?"
        else:
            st.session_state.msg = "⚠️ 당신의 말을 선택해주세요."
            
    # 2. 두 번째 클릭 (이동)
    else:
        # 같은 말을 또 누르면 취소
        if selected == square_index:
            st.session_state.selected_square = None
            st.session_state.msg = "선택을 취소했습니다."
            return

        # 이동 생성
        move = chess.Move(from_square=selected, to_square=square_index)
        
        # 폰 승진 (자동으로 퀸)
        if board.piece_at(selected).piece_type == chess.PAWN:
            if chess.square_rank(square_index) in [0, 7]:
                move.promotion = chess.QUEEN

        # 유효한 이동인지 확인
        if move in board.legal_moves:
            board.push(move)
            st.session_state.selected_square = None # 선택 해제
            st.session_state.msg = "이동 완료! AI 차례..."
        else:
            # 다른 내 말을 누르면 선택 변경
            piece = board.piece_at(square_index)
            if piece and piece.color == board.turn:
                st.session_state.selected_square = square_index
                st.session_state.msg = f"선택 변경: {chess.square_name(square_index)}"
            else:
                st.session_state.msg = "🚫 그곳으로는 갈 수 없습니다."

# --- 무르기(Undo) 함수 ---
def undo_move():
    # 최소 2수(내 거 + AI 거)가 있어야 정상적인 무르기 가능
    if len(st.session_state.board.move_stack) >= 2:
        st.session_state.board.pop() # AI 수 취소
        st.session_state.board.pop() # 내 수 취소
        st.session_state.msg = "한 수 물렀습니다!"
        st.session_state.selected_square = None
    elif len(st.session_state.board.move_stack) == 1:
        st.session_state.board.pop()
        st.session_state.msg = "첫 수로 돌아왔습니다."
        st.session_state.selected_square = None
    else:
        st.session_state.msg = "더 이상 무를 수 없습니다."

# --- UI 그리기 ---
st.title("♟️ Streamlit Chess V2 (Click & Undo)")

col_board, col_controls = st.columns([1.5, 1])

with col_board:
    # 8x8 그리드 그리기 (CSS로 간격 조절됨)
    for rank in range(7, -1, -1):
        cols = st.columns(8) # 8개 칸 생성
        for file in range(8):
            square_index = chess.square(file, rank)
            piece = st.session_state.board.piece_at(square_index)
            
            # 버튼에 들어갈 텍스트 (말 모양)
            label = piece.unicode_symbol() if piece else "⠀" # 공백 문자(U+2800) 사용으로 버튼 크기 유지
            
            # 선택된 칸은 배경색 다르게 표시 (텍스트로 구분)
            if st.session_state.selected_square == square_index:
                label = f"🟢{label}"
            
            # 버튼 생성 (key는 유일해야 함)
            if cols[file].button(label, key=f"sq_{square_index}"):
                handle_click(square_index)
                st.rerun()

with col_controls:
    st.info(st.session_state.msg)
    
    # 게임 상태
    if st.session_state.board.is_check():
        st.warning("🔥 체크(Check) 상태입니다!")
    if st.session_state.board.is_game_over():
        st.error(f"🏁 게임 종료! ({st.session_state.board.result()})")

    st.markdown("---")
    
    # 기능 버튼들
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔙 무르기 (Undo)"):
            undo_move()
            st.rerun()
    with col_btn2:
        if st.button("🔄 새 게임 (Reset)"):
            st.session_state.board = chess.Board()
            st.session_state.selected_square = None
            st.session_state.msg = "새 게임 시작!"
            st.rerun()

    # AI 턴 실행 로직 (화면 갱신 후 실행)
    if not st.session_state.board.is_game_over() and st.session_state.board.turn == chess.BLACK:
        play_engine_move()
        st.rerun()
