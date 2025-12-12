import streamlit as st
import chess
import chess.svg
import random
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="Streamlit Chess AI", page_icon="🤖", layout="wide")

st.title("🤖 인공지능과 체스 대결")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

# --- 2. 간단한 AI 함수 ---
def get_ai_move(curr_board):
    legal_moves = list(curr_board.legal_moves)
    if not legal_moves:
        return None
    # 공격 기회(Capture)가 있으면 우선 선택
    for move in legal_moves:
        if curr_board.is_capture(move):
            return move
    # 없으면 무작위
    return random.choice(legal_moves)

# --- 3. 사이드바: 설정 및 게임 제어 ---
with st.sidebar:
    st.header("⚙️ 게임 설정")
    board_size = st.slider("체스판 크기 조절 (px)", 300, 1000, 600, 50)

    st.markdown("---")
    st.header("게임 제어")
    
    # [NEW] 무르기 버튼
    # AI와 대결 중이므로 내 수 + AI 수 = 총 2번을 되돌려야 함
    if st.button("↩️ 무르기 (Undo)"):
        if len(board.move_stack) >= 2:
            board.pop() # AI의 수 취소
            board.pop() # 나의 수 취소
            st.toast("한 수 물렀습니다! 다시 생각해보세요.")
            st.rerun()
        elif len(board.move_stack) == 1:
            # 혹시 한 수만 두어진 상태라면 하나만 취소
            board.pop()
            st.rerun()
        else:
            st.warning("더 이상 무를 수가 없습니다 (게임 시작 상태).")

    # 새 게임 버튼
    if st.button("🔄 새 게임 시작"):
        st.session_state.board = chess.Board()
        st.rerun()
    
    st.markdown("---")
    
    # 상태 표시
    if board.turn == chess.WHITE:
        st.info("🟢 당신의 차례 (White)")
    else:
        st.warning("🔴 AI 생각 중... (Black)")

    if board.is_check():
        st.warning("⚠️ 체크 상태입니다!")
    if board.is_game_over():
        st.error(f"게임 종료! 결과: {board.result()}")
    
    # 이동 기록
    with st.expander("📜 이동 기록"):
        move_log = []
        temp_board = chess.Board()
        for i, move in enumerate(board.move_stack):
            san = temp_board.san(move)
            temp_board.push(move)
            if i % 2 == 0:
                move_log.append(f"{i//2 + 1}. {san}")
            else:
                move_log[-1] += f" {san}"
        st.text("\n".join(move_log))

# --- 4. 레이아웃 구성 ---
col1, col2 = st.columns([2, 1])

with col1:
    last_move = board.peek() if board.move_stack else None
    board_svg = chess.svg.board(
        board=board, 
        lastmove=last_move,
        size=board_size
    )
    st.markdown(
        f'<div style="display: flex; justify-content: center;">{board_svg}</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown("### 🕹️ 조작 방법")
    st.markdown("""
    - **이동**: `e4`, `Nf3`, `Bxc4` 등을 입력하고 엔터.
    - **무르기**: 사이드바의 '무르기' 버튼 사용.
    """)

    # --- 5. 게임 로직 ---
    if not board.is_game_over():
        with st.form(key='move_form'):
            user_move = st.text_input("나의 수 입력", key="input", placeholder="예: e4, Nf3")
            submit = st.form_submit_button("두기 (Move)")
                
        if submit and user_move:
            try:
                move = board.parse_san(user_move)
                if move in board.legal_moves:
                    board.push(move)
                    
                    # AI 턴
                    if not board.is_game_over():
                        with st.spinner("AI가 생각 중입니다..."):
                            time.sleep(0.3)
                            ai_move = get_ai_move(board)
                            if ai_move:
                                board.push(ai_move)
                                st.toast(f"AI: {board.san(ai_move)}")
                    
                    st.rerun()
                else:
                    st.error("규칙에 어긋나는 수입니다.")
            except ValueError:
                st.error("잘못된 표기법입니다.")
    else:
        st.success("게임이 끝났습니다!")
