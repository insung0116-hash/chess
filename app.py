import streamlit as st
import chess
from streamlit_chess import st_chess

# --- 페이지 설정 ---
st.set_page_config(page_title="Streamlit Chess", page_icon="♟️")

st.title("♟️ 드래그 앤 드롭 체스")
st.markdown("마우스로 말을 끌어서 이동하세요!")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

# --- 2. 사이드바: 정보 및 리셋 ---
with st.sidebar:
    st.header("게임 상태")
    turn = "White (백)" if board.turn == chess.WHITE else "Black (흑)"
    st.info(f"현재 차례: **{turn}**")
    
    if board.is_check():
        st.warning("⚠️ 체크!")
    if board.is_game_over():
        st.error(f"게임 종료! 결과: {board.result()}")
        
    if st.button("게임 재시작"):
        st.session_state.board = chess.Board()
        st.rerun()

# --- 3. 체스판 렌더링 및 이동 처리 ---
# st_chess 함수는 현재 보드 상태(FEN 문자열)를 받아 그려줍니다.
# 사용자가 말을 움직이면, 움직인 후의 새로운 보드 상태(FEN)를 반환합니다.
new_fen = st_chess(board.fen())

# --- 4. 보드 업데이트 ---
# 만약 반환된 FEN(new_fen)이 현재 보드(board.fen())와 다르다면,
# 사용자가 말을 움직였다는 뜻입니다.
if new_fen and new_fen != board.fen():
    # 사용자가 움직인 상태(new_fen)를 현재 보드에 적용합니다.
    try:
        # FEN 문자열을 이용해 보드 상태 업데이트
        board.set_fen(new_fen)
        
        # 보드 상태가 바뀌었으므로 화면을 갱신합니다.
        st.rerun()
    except ValueError:
        pass
