import streamlit as st
import chess
import chess.svg

# --- 페이지 설정 ---
st.set_page_config(page_title="Streamlit Chess", page_icon="♟️")

st.title("♟️ Streamlit 체스")
st.markdown("라이브러리 호환성 문제로 인해 **텍스트 입력 방식**으로 전환되었습니다.")
st.markdown("기보(예: `e4`, `Nf3`)를 입력하여 플레이하세요.")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

# --- 2. 사이드바: 게임 정보 ---
with st.sidebar:
    st.header("게임 현황")
    turn_str = "백(White) 차례" if board.turn == chess.WHITE else "흑(Black) 차례"
    st.info(f"현재: **{turn_str}**")
    
    if board.is_check():
        st.warning("⚠️ 체크 상태입니다!")
    if board.is_game_over():
        st.error(f"게임 종료! 결과: {board.result()}")
    
    if st.button("게임 재시작"):
        st.session_state.board = chess.Board()
        st.rerun()

# --- 3. 체스판 시각화 (SVG 사용) ---
# 호환성 문제 없는 SVG 방식 사용
board_svg = chess.svg.board(board=board)
st.markdown(
    f'<div style="display: flex; justify-content: center; margin-bottom: 20px;">{board_svg}</div>',
    unsafe_allow_html=True
)

# --- 4. 이동 입력 (Form 사용) ---
with st.form(key='move_form'):
    col1, col2 = st.columns([4, 1])
    with col1:
        # 텍스트 입력창
        move_input = st.text_input("이동할 위치 입력 (예: e2e4, Nf3)", key="move_input")
    with col2:
        # 실행 버튼
        submit_button = st.form_submit_button("이동")

    if submit_button and move_input:
        try:
            # 입력값으로 이동 시도
            move = board.parse_san(move_input)
            
            if move in board.legal_moves:
                board.push(move)
                st.success(f"이동 완료: {move_input}")
                st.rerun()
            else:
                st.error("규칙에 어긋나는 이동입니다.")
        except ValueError:
            st.error("잘못된 표기법입니다. (예: e4, Nf3 처럼 입력해보세요)")

# --- 5. 이동 가능한 수 힌트 ---
with st.expander("🤔 이동 가능한 수 보기 (힌트)"):
    legal_moves = [board.san(move) for move in board.legal_moves]
    st.write(", ".join(legal_moves))
