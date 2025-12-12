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

# [NEW] 앞으로 가기(Redo)를 위한 임시 저장소
if 'redo_stack' not in st.session_state:
    st.session_state.redo_stack = []

board = st.session_state.board
redo_stack = st.session_state.redo_stack

# --- 2. 간단한 AI 함수 ---
def get_ai_move(curr_board):
    legal_moves = list(curr_board.legal_moves)
    if not legal_moves:
        return None
    for move in legal_moves:
        if curr_board.is_capture(move):
            return move
    return random.choice(legal_moves)

# --- 3. 사이드바: 설정 및 제어 ---
with st.sidebar:
    st.header("⚙️ 게임 설정")
    board_size = st.slider("체스판 크기 조절 (px)", 300, 1000, 600, 50)

    st.markdown("---")
    st.header("게임 제어")
    
    # 버튼을 가로로 배치
    b_col1, b_col2 = st.columns(2)
    
    # [무르기 (Undo)]
    with b_col1:
        if st.button("⬅️ 뒤로 (Undo)"):
            if len(board.move_stack) >= 2:
                # 1. AI 수 취소 및 저장
                ai_move = board.pop()
                st.session_state.redo_stack.append(ai_move)
                
                # 2. 내 수 취소 및 저장
                my_move = board.pop()
                st.session_state.redo_stack.append(my_move)
                
                st.toast("두 수 물렀습니다.")
                st.rerun()
            else:
                st.warning("더 이상 뒤로 갈 수 없습니다.")

    # [앞으로 가기 (Redo)]
    with b_col2:
        if st.button("➡️ 앞으로 (Redo)"):
            if len(st.session_state.redo_stack) >= 2:
                # 1. 내 수 복구
                # 스택은 LIFO(Last In First Out)이므로 나중에 넣은 내 수가 먼저 나옴
                my_move = st.session_state.redo_stack.pop()
                board.push(my_move)
                
                # 2. AI 수 복구
                ai_move = st.session_state.redo_stack.pop()
                board.push(ai_move)
                
                st.toast("다시 앞으로 갔습니다.")
                st.rerun()
            else:
                st.warning("복구할 미래가 없습니다.")

    # [새 게임]
    if st.button("🔄 새 게임 시작", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.redo_stack = [] # 저장된 미래도 초기화
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
    
    # 기록 표시
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

# --- 4. 레이아웃 ---
col1, col2 = st.columns([2, 1])

with col1:
    last_move = board.peek() if board.move_stack else None
    board_svg = chess.svg.board(board=board, lastmove=last_move, size=board_size)
    st.markdown(f'<div style="display: flex; justify-content: center;">{board_svg}</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 🕹️ 조작 방법")
    st.markdown("""
    - **입력**: `e4`, `Nf3` 등 입력 후 엔터.
    - **탐색**: '뒤로', '앞으로' 버튼으로 시점을 이동할 수 있습니다.
    - **주의**: 과거로 돌아가서 **새로운 수**를 두면, '앞으로 가기' 목록은 사라집니다.
    """)

    if not board.is_game_over():
        with st.form(key='move_form'):
            user_move = st.text_input("나의 수 입력", key="input", placeholder="예: e4, Nf3")
            submit = st.form_submit_button("두기 (Move)")
                
        if submit and user_move:
            try:
                move = board.parse_san(user_move)
                if move in board.legal_moves:
                    
                    # [중요] 새로운 수를 두면, 저장해둔 미래(redo_stack)는 무효화됨
                    st.session_state.redo_stack = []
                    
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
