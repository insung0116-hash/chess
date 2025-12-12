import streamlit as st
import chess
import chess.svg
import random
import time

# --- 페이지 설정 ---
# layout="wide"로 설정하면 가로 공간을 더 넓게 씁니다.
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

# --- 3. 사이드바: 설정 및 게임 정보 ---
with st.sidebar:
    st.header("⚙️ 게임 설정")
    
    # [NEW] 체스판 크기 조절 슬라이더
    board_size = st.slider("체스판 크기 조절 (px)", min_value=300, max_value=1000, value=600, step=50)

    st.markdown("---")
    st.header("게임 현황")
    
    # 차례 표시
    if board.turn == chess.WHITE:
        st.info("당신의 차례 (White)")
    else:
        st.warning("AI 생각 중... (Black)")

    # 체크 확인
    if board.is_check():
        st.warning("⚠️ 체크 상태입니다!")
    if board.is_game_over():
        st.error(f"게임 종료! 결과: {board.result()}")
    
    if st.button("새 게임 시작"):
        st.session_state.board = chess.Board()
        st.rerun()
    
    # 이동 기록 (사이드바로 이동)
    st.markdown("---")
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

# --- 4. 레이아웃 구성 (체스판 | 입력창) ---
# 화면을 2개 컬럼으로 나눠서 왼쪽엔 체스판, 오른쪽엔 설명을 둡니다.
col1, col2 = st.columns([2, 1])

with col1:
    # 체스판 시각화
    last_move = board.peek() if board.move_stack else None
    board_svg = chess.svg.board(
        board=board, 
        lastmove=last_move,
        size=board_size  # 슬라이더 값 적용
    )
    
    # 중앙 정렬하여 표시
    st.markdown(
        f'<div style="display: flex; justify-content: center;">{board_svg}</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown("### 🕹️ 조작 방법")
    st.markdown("""
    1. **기보 입력**: 아래 입력창에 말을 어디로 움직일지 적으세요.
    2. **표기법 (SAN)**:
       - 폰: 도착 위치 (예: `e4`)
       - 나이트(N), 비숍(B), 룩(R), 퀸(Q), 킹(K) + 위치
       - 예: `Nf3`, `Bc4`
       - 잡기: `exd5`, `Qxe5`
    """)

    # --- 5. 게임 로직 ---
    if not board.is_game_over():
        with st.form(key='move_form'):
            user_move = st.text_input("나의 수 입력", key="input", placeholder="예: e4, Nf3")
            submit = st.form_submit_button("두기 (Move)")
                
        if submit and user_move:
            try:
                # 사용자 턴
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
                                st.toast(f"AI가 {board.san(ai_move)}로 응수했습니다.")
                    
                    st.rerun()
                else:
                    st.error("규칙에 어긋나는 수입니다.")
            except ValueError:
                st.error("잘못된 표기법입니다.")
    else:
        st.success("게임이 끝났습니다! 사이드바에서 '새 게임 시작'을 누르세요.")
