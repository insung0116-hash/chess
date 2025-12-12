import streamlit as st
import chess
import chess.svg
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="Strategic Chess AI", page_icon="♟️", layout="wide")

st.title("♟️ 전략가 AI와 체스 대결")
st.markdown("캐슬링, 앙파상 등 **체스의 모든 규칙**이 지원됩니다.")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

if 'redo_stack' not in st.session_state:
    st.session_state.redo_stack = []

board = st.session_state.board
redo_stack = st.session_state.redo_stack

# --- 2. AI 엔진 (전략적 평가 함수 & 미니맥스) ---

# 기물 기본 점수
piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# 위치 점수표 (PST) - AI가 똑똑하게 두기 위한 위치 데이터
pawntable = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]
knightstable = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]
bishopstable = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]
rookstable = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]
queenstable = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]
kingstable = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

def evaluate_board(board):
    if board.is_checkmate():
        if board.turn: return -99999
        else: return 99999
    if board.is_stalemate() or board.is_insufficient_material(): return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.piece_type == chess.PAWN: table = pawntable
            elif piece.piece_type == chess.KNIGHT: table = knightstable
            elif piece.piece_type == chess.BISHOP: table = bishopstable
            elif piece.piece_type == chess.ROOK: table = rookstable
            elif piece.piece_type == chess.QUEEN: table = queenstable
            elif piece.piece_type == chess.KING: table = kingstable
            else: table = [0]*64

            if piece.color == chess.WHITE:
                score += (value + table[square])
            else:
                score -= (value + table[chess.square_mirror(square)])
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    legal_moves = list(board.legal_moves)
    legal_moves.sort(key=lambda move: board.is_capture(move), reverse=True)

    if maximizing_player:
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha: break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha: break
        return min_eval

def get_best_move(board, depth):
    best_move = None
    best_value = float('inf')
    legal_moves = list(board.legal_moves)
    legal_moves.sort(key=lambda move: board.is_capture(move), reverse=True)

    for move in legal_moves:
        board.push(move)
        board_value = minimax(board, depth - 1, -float('inf'), float('inf'), True)
        board.pop()
        if board_value < best_value:
            best_value = board_value
            best_move = move
    return best_move

# --- 3. 사이드바 ---
with st.sidebar:
    st.header("⚙️ 설정")
    board_size = st.slider("체스판 크기", 300, 1000, 600, 50)
    difficulty = st.selectbox("AI 난이도", ["초급 (Depth 1)", "중급 (Depth 2)", "고급 (Depth 3)"])
    ai_depth = 1 if "초급" in difficulty else (2 if "중급" in difficulty else 3)

    st.markdown("---")
    st.header("제어")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ 무르기"):
            if len(board.move_stack) >= 2:
                st.session_state.redo_stack.append(board.pop())
                st.session_state.redo_stack.append(board.pop())
                st.toast("무르기 완료")
                st.rerun()
    with c2:
        if st.button("➡️ 앞으로"):
            if len(st.session_state.redo_stack) >= 2:
                board.push(st.session_state.redo_stack.pop())
                board.push(st.session_state.redo_stack.pop())
                st.toast("앞으로 가기 완료")
                st.rerun()

    if st.button("🔄 새 게임", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.redo_stack = []
        st.rerun()
    
    st.markdown("---")
    if board.turn == chess.WHITE: st.info("🟢 당신의 차례")
    else: st.warning("🔴 AI 생각 중...")

    if board.is_check(): st.warning("⚠️ 체크!")
    if board.is_game_over(): st.error(f"게임 종료! {board.result()}")
    
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
    st.markdown("### 🕹️ 조작 및 특수 규칙")
    
    # [NEW] 특수 규칙 설명 추가
    with st.expander("🏰 캐슬링 & 특수 규칙 입력법", expanded=True):
        st.markdown("""
        - **기본 이동**: `e4`, `Nf3`, `Bxc4`
        - **🏰 캐슬링 (Castling)**:
            - 킹사이드 (오른쪽): **`O-O`** (대문자 O)
            - 퀸사이드 (왼쪽): **`O-O-O`**
        - **♟️ 앙파상 (En Passant)**:
            - 그냥 잡는 위치를 입력 (예: **`exd6`**)
        - **👑 프로모션 (승격)**:
            - 도착 위치 + 기물 (예: **`e8Q`**, `a1R`)
        """)

    if not board.is_game_over():
        with st.form(key='move_form'):
            user_move = st.text_input("나의 수 입력", key="input", placeholder="예: e4, O-O")
            submit = st.form_submit_button("두기 (Move)")
            
        if submit and user_move:
            try:
                move = board.parse_san(user_move)
                if move in board.legal_moves:
                    st.session_state.redo_stack = []
                    board.push(move)
                    
                    if not board.is_game_over():
                        with st.spinner("AI가 전략을 구상 중입니다..."):
                            time.sleep(0.1)
                            ai_move = get_best_move(board, depth=ai_depth)
                            if ai_move:
                                ai_san = board.san(ai_move)
                                board.push(ai_move)
                                st.toast(f"AI: {ai_san}")
                    st.rerun()
                else:
                    st.error("규칙 위반이거나 불가능한 수입니다.")
            except ValueError:
                st.error("잘못된 표기법입니다. (예: O-O, e8Q)")
    else:
        st.success("게임이 끝났습니다!")
