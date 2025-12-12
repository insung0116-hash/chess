import streamlit as st
import chess
import chess.svg
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="Smart Chess AI", page_icon="🧠", layout="wide")

st.title("🧠 똑똑해진 AI와 체스 대결")
st.markdown("이제 AI가 **기물 점수**를 계산하고 **수읽기**를 합니다. (난이도: 중급)")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

if 'redo_stack' not in st.session_state:
    st.session_state.redo_stack = []

board = st.session_state.board
redo_stack = st.session_state.redo_stack

# --- 2. AI 엔진 (Minimax 알고리즘) ---

# 기물별 점수 (일반적인 체스 점수)
piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

def evaluate_board(board):
    """현재 보드의 점수를 계산합니다. (백이 유리하면 양수, 흑이 유리하면 음수)"""
    if board.is_checkmate():
        if board.turn: return -99999 # 백 차례인데 체크메이트 = 흑 승리
        else: return 99999 # 흑 차례인데 체크메이트 = 백 승리
    
    score = 0
    # 모든 기물 점수 합산
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """
    재귀함수를 사용하여 수읽기를 진행합니다.
    depth: 몇 수 앞을 볼 것인지 (여기서는 2)
    maximizing_player: 백(True)인지 흑(False)인지
    """
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    legal_moves = list(board.legal_moves)

    if maximizing_player: # 백(White)의 입장 (점수 최대화)
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else: # 흑(Black)의 입장 (점수 최소화 - AI)
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def get_best_move(board, depth=2):
    """최적의 수를 찾습니다."""
    best_move = None
    best_value = float('inf') # 흑(AI)은 점수를 낮춰야 함 (음수가 흑 유리)
    
    legal_moves = list(board.legal_moves)
    
    # 1. 중앙 제어 등을 위한 간단한 정렬 (알파-베타 가지치기 효율 상승)
    # 잡는 수(Capture)를 먼저 검토하게 함
    legal_moves.sort(key=lambda move: board.is_capture(move), reverse=True)

    for move in legal_moves:
        board.push(move)
        board_value = minimax(board, depth - 1, -float('inf'), float('inf'), True)
        board.pop()
        
        if board_value < best_value:
            best_value = board_value
            best_move = move
            
    return best_move

# --- 3. 사이드바: 설정 및 제어 ---
with st.sidebar:
    st.header("⚙️ 게임 설정")
    board_size = st.slider("체스판 크기 (px)", 300, 1000, 600, 50)
    
    # [NEW] 난이도 조절 (깊이)
    difficulty = st.selectbox("AI 난이도 (수읽기)", ["초급 (1수 앞)", "중급 (2수 앞)", "고급 (3수 앞 - 느림)"])
    ai_depth = 1 if "초급" in difficulty else (2 if "중급" in difficulty else 3)

    st.markdown("---")
    st.header("게임 제어")
    
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("⬅️ 뒤로 (Undo)"):
            if len(board.move_stack) >= 2:
                st.session_state.redo_stack.append(board.pop())
                st.session_state.redo_stack.append(board.pop())
                st.toast("무르기 완료")
                st.rerun()
            else:
                st.warning("초기 상태입니다.")
    with b_col2:
        if st.button("➡️ 앞으로 (Redo)"):
            if len(st.session_state.redo_stack) >= 2:
                board.push(st.session_state.redo_stack.pop())
                board.push(st.session_state.redo_stack.pop())
                st.toast("앞으로 가기 완료")
                st.rerun()
            else:
                st.warning("복구할 기록이 없습니다.")

    if st.button("🔄 새 게임 시작", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.redo_stack = []
        st.rerun()
    
    st.markdown("---")
    if board.turn == chess.WHITE:
        st.info("🟢 당신의 차례 (White)")
    else:
        st.warning("🔴 AI 생각 중... (Black)")
    
    if board.is_check():
        st.warning("⚠️ 체크!")
    if board.is_game_over():
        st.error(f"게임 종료! {board.result()}")
    
    with st.expander("📜 이동 기록"):
        move_log = []
        temp_board = chess.Board()
        for i, move in enumerate(board.move_stack):
            san = temp_board.san(move)
            temp_board.push(move)
            if i % 2 == 0: move_log.append(f"{i//2 + 1}. {san}")
            else: move_log[-1] += f" {san}"
        st.text("\n".join(move_log))

# --- 4. 메인 화면 ---
col1, col2 = st.columns([2, 1])

with col1:
    last_move = board.peek() if board.move_stack else None
    board_svg = chess.svg.board(board=board, lastmove=last_move, size=board_size)
    st.markdown(f'<div style="display: flex; justify-content: center;">{board_svg}</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 🕹️ 조작 방법")
    st.markdown("- 입력 예시: `e4`, `Nf3`, `Bxc4`")
    
    if not board.is_game_over():
        with st.form(key='move_form'):
            user_move = st.text_input("나의 수 입력", key="input", placeholder="예: e4")
            submit = st.form_submit_button("두기")
            
        if submit and user_move:
            try:
                move = board.parse_san(user_move)
                if move in board.legal_moves:
                    st.session_state.redo_stack = []
                    board.push(move)
                    
                    if not board.is_game_over():
                        with st.spinner(f"AI가 {ai_depth}수 앞을 내다보는 중..."):
                            # AI가 생각하는 척 (너무 빠르면 재미없음)
                            time.sleep(0.1)
                            
                            # AI 엔진 가동
                            ai_move = get_best_move(board, depth=ai_depth)
                            
                            if ai_move:
                                ai_san = board.san(ai_move)
                                board.push(ai_move)
                                st.toast(f"AI: {ai_san}")
                            else:
                                st.error("AI가 둘 곳이 없습니다.")
                    st.rerun()
                else:
                    st.error("규칙 위반입니다.")
            except ValueError:
                st.error("잘못된 표기법입니다.")
    else:
        st.success("게임 종료!")
