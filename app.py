import streamlit as st
import chess
import chess.engine
import shutil

# --- 페이지 설정 ---
st.set_page_config(page_title="Clickable Chess", page_icon="♟️", layout="wide")

# --- 스타일(CSS) 커스텀: 버튼 간격 줄이기 ---
st.markdown("""
<style>
    div[data-testid="column"] {
        width: fit-content !important;
        flex: 0 1 auto !important;
    }
    div.stButton > button {
        width: 50px;
        height: 50px;
        font-size: 24px;
        padding: 0;
        line-height: 1;
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None  # 선택된 말의 위치

if 'msg' not in st.session_state:
    st.session_state.msg = "흰색(White) 차례입니다. 옮길 말을 클릭하세요."

# --- Stockfish 엔진 경로 ---
stockfish_path = shutil.which("stockfish")

# --- 함수: AI(Stockfish) 턴 ---
def play_engine_move():
    if not stockfish_path:
        st.warning("Stockfish 엔진을 찾을 수 없습니다.")
        return
    
    with st.spinner("컴퓨터가 생각 중..."):
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            result = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
            st.session_state.board.push(result.move)
            engine.quit()
            st.session_state.msg = "당신의 차례입니다."
        except Exception as e:
            st.error(f"AI 오류: {e}")

# --- 함수: 클릭 이벤트 처리 ---
def handle_click(square_index):
    board = st.session_state.board
    selected = st.session_state.selected_square

    # 1. 말을 선택하지 않은 상태에서 클릭함
    if selected is None:
        piece = board.piece_at(square_index)
        if piece and piece.color == board.turn:
            st.session_state.selected_square = square_index
            st.session_state.msg = f"선택됨: {chess.square_name(square_index)}. 어디로 이동할까요?"
        else:
            st.session_state.msg = "자신의 말을 선택해야 합니다."
    
    # 2. 이미 말을 선택했고, 이동할 곳(두 번째 클릭)을 누름
    else:
        # 같은 말을 다시 누르면 취소
        if selected == square_index:
            st.session_state.selected_square = None
            st.session_state.msg = "선택을 취소했습니다."
            return

        # 이동 시도
        move = chess.Move(from_square=selected, to_square=square_index)
        
        # 승진(Promotion) 처리 (일단 퀸으로 자동 승진)
        if chess.square_rank(square_index) in [0, 7]:
            piece = board.piece_at(selected)
            if piece and piece.piece_type == chess.PAWN:
                move = chess.Move(from_square=selected, to_square=square_index, promotion=chess.QUEEN)

        if move in board.legal_moves:
            board.push(move)
            st.session_state.selected_square = None # 선택 초기화
            st.session_state.msg = "이동 완료! 컴퓨터 차례..."
            
            # AI 턴 즉시 실행 여부는 스트림릿 리런 구조상 여기서 처리
            # 화면이 갱신된 후 AI가 두도록 하기 위해 일단 둡니다.
        else:
            # 다른 내 말을 클릭했으면 선택 변경
            piece = board.piece_at(square_index)
            if piece and piece.color == board.turn:
                st.session_state.selected_square = square_index
                st.session_state.msg = f"선택 변경: {chess.square_name(square_index)}"
            else:
                st.session_state.msg = "그곳으로 이동할 수 없습니다."


# --- UI 구성 ---
st.title("🖱️ Click-to-Move Chess")

col1, col2 = st.columns([2, 1])

with col1:
    # 8x8 버튼 그리드 생성
    # 체스판은 위(8랭크)에서 아래(1랭크)로 그려야 함
    for rank in range(7, -1, -1):
        cols = st.columns(8) # 한 줄에 8개 컬럼
        for file in range(8):
            square_index = chess.square(file, rank)
            piece = st.session_state.board.piece_at(square_index)
            
            # 말 아이콘 가져오기 (없으면 공백)
            piece_symbol = piece.unicode_symbol() if piece else " "
            
            # 버튼 배경색 (체스판 체크무늬 효과)
            is_dark_square = (rank + file) % 2 == 0
            
            # 선택된 말 강조
            if st.session_state.selected_square == square_index:
                label = f"[{piece_symbol}]" # 선택됨 표시
            else:
                label = piece_symbol

            # 버튼 그리기 (키 값 유일하게 설정)
            if cols[file].button(label, key=f"sq_{square_index}"):
                handle_click(square_index)
                st.rerun()

with col2:
    st.info(st.session_state.msg)
    
    # 게임 상태 표시
    if st.session_state.board.is_game_over():
        st.error(f"게임 종료! 결과: {st.session_state.board.result()}")
    
    # 턴 확인 및 AI 실행 트리거
    if not st.session_state.board.is_game_over() and st.session_state.board.turn == chess.BLACK:
        play_engine_move()
        st.rerun()

    st.markdown("---")
    if st.button("게임 재시작"):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.msg = "새 게임 시작!"
        st.rerun()
