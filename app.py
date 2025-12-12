import streamlit as st
import chess
import chess.svg
import random
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="Streamlit Chess AI", page_icon="🤖")

st.title("🤖 인공지능과 체스 대결")
st.markdown("당신은 **백(White)**입니다. 기보(예: `e4`, `Nf3`)를 입력하면 AI가 응수합니다!")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

# --- 2. 간단한 AI 함수 (봇) ---
def get_ai_move(curr_board):
    """
    현재 보드 상태에서 둘 수 있는 수 중 하나를 무작위로 선택합니다.
    (나중에 더 똑똑한 로직으로 바꿀 수 있습니다)
    """
    legal_moves = list(curr_board.legal_moves)
    if not legal_moves:
        return None
    
    # 1. 상대를 잡을 수 있는 수가 있다면 우선적으로 둠 (약간의 공격성 추가)
    for move in legal_moves:
        if curr_board.is_capture(move):
            return move
            
    # 2. 없다면 무작위로 선택
    return random.choice(legal_moves)

# --- 3. 사이드바: 게임 정보 ---
with st.sidebar:
    st.header("게임 현황")
    
    # 차례 표시
    if board.turn == chess.WHITE:
        st.info("당신의 차례입니다 (White)")
    else:
        st.warning("AI가 생각 중입니다... (Black)")

    # 체크/게임종료 상태 확인
    if board.is_check():
        st.warning("⚠️ 체크 상태입니다!")
    if board.is_game_over():
        st.error(f"게임 종료! 결과: {board.result()}")
    
    # 리셋 버튼
    if st.button("새 게임 시작"):
        st.session_state.board = chess.Board()
        st.rerun()

# --- 4. 체스판 시각화 ---
# 최근에 둔 수를 화살표로 표시
last_move = board.peek() if board.move_stack else None
board_svg = chess.svg.board(
    board=board, 
    lastmove=last_move,
    size=400
)

st.markdown(
    f'<div style="display: flex; justify-content: center; margin-bottom: 20px;">{board_svg}</div>',
    unsafe_allow_html=True
)

# --- 5. 게임 로직 (사용자 입력 -> AI 응수) ---

# 게임이 끝나지 않았을 때만 입력창 표시
if not board.is_game_over():
    
    # [사용자 턴]
    with st.form(key='move_form'):
        col1, col2 = st.columns([4, 1])
        with col1:
            user_move = st.text_input("나의 수 입력 (예: e4, Nf3)", key="input")
        with col2:
            submit = st.form_submit_button("두기")
            
    if submit and user_move:
        try:
            # 1. 사용자 이동 시도
            move = board.parse_san(user_move)
            if move in board.legal_moves:
                board.push(move) # 사용자 수 적용
                
                # 2. 게임 종료 여부 확인
                if not board.is_game_over():
                    # 3. AI 턴 (흑)
                    with st.spinner("AI가 수를 생각하는 중..."):
                        time.sleep(0.5) # 생각하는 척 연출
                        ai_move = get_ai_move(board)
                        if ai_move:
                            board.push(ai_move) # AI 수 적용
                            st.success(f"당신: {user_move}  vs  AI: {board.san(ai_move)}")
                
                st.rerun() # 화면 갱신
            else:
                st.error("둘 수 없는 수입니다 (규칙 위반).")
        except ValueError:
            st.error("잘못된 표기법입니다. (예: e4, Nf3, exd5)")

# --- 6. 이동 기록 로그 ---
with st.expander("📜 이동 기록 (History)"):
    move_log = []
    temp_board = chess.Board()
    for i, move in enumerate(board.move_stack):
        san = temp_board.san(move)
        temp_board.push(move)
        if i % 2 == 0:
            move_log.append(f"{i//2 + 1}. {san}") # 백
        else:
            move_log[-1] += f" {san}" # 흑
            
    st.text("\n".join(move_log))
