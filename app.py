import streamlit as st
import chess
from streamlit_chessboard import render_chessboard

# --- 페이지 설정 ---
st.set_page_config(page_title="Streamlit Drag & Drop Chess", page_icon="♟️")

st.title("♟️ 드래그 앤 드롭 체스")
st.markdown("마우스로 말을 끌어서 이동하세요!")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

# --- 2. 사이드바: 정보 및 리셋 ---
with st.sidebar:
    st.header("게임 상태")
    # 누구 차례인지 표시
    turn = "White (백)" if board.turn == chess.WHITE else "Black (흑)"
    st.info(f"현재 차례: **{turn}**")
    
    # 체크/게임종료 상태 확인
    if board.is_check():
        st.warning("⚠️ 체크!")
    if board.is_game_over():
        st.error(f"게임 종료! 결과: {board.result()}")
        
    # 게임 재시작 버튼
    if st.button("게임 재시작"):
        st.session_state.board = chess.Board()
        st.rerun() # 버튼 클릭 시에는 명시적 리런이 필요할 수 있음 (최신 버전은 st.rerun 권장)

# --- 3. 체스판 렌더링 (드래그 앤 드롭 기능) ---
# render_chessboard 함수가 드래그 앤 드롭 기능을 제공합니다.
# 사용자가 말을 움직이면 그 결과(데이터)를 반환합니다.
move_data = render_chessboard(
    board, 
    key="chess_board"
)

# --- 4. 이동 처리 로직 ---
# 사용자가 말을 움직여서 move_data가 들어왔을 때 실행됩니다.
if move_data:
    # move_data['move']에는 'e2e4' 같은 이동 정보가 들어있습니다.
    # from_square, to_square 정보를 가져와서 움직임을 만듭니다.
    try:
        # 라이브러리가 주는 정보 형식에 맞춰 이동 객체 생성
        move = chess.Move.from_uci(move_data['move'])
        
        # 보드에 업데이트
        # 중요: 여기서는 st.experimental_rerun()을 쓰지 않습니다!
        # Streamlit은 위젯(체스판)의 값이 바뀌면 자동으로 스크립트를 재실행하므로
        # session_state만 업데이트하면 알아서 화면이 바뀝니다.
        if move in board.legal_moves:
            board.push(move)
            # 이동 후 별도의 알림이 필요하다면 아래 주석을 해제하세요
            # st.toast(f"이동 완료: {move}")
        else:
            st.warning("규칙에 맞지 않는 이동입니다.")
            
    except Exception as e:
        # 가끔 발생하는 데이터 처리 오류 방지
        pass
