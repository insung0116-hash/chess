import streamlit as st
import chess
import chess.svg
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="Strategic Chess AI", page_icon="♟️", layout="wide")

st.title("♟️ 전략가 AI와 체스 대결")
st.markdown("AI가 **'명당 자리(Position)'**를 이해합니다. 구석에 있는 말보다 중앙에 있는 말을 더 선호합니다.")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

if 'redo_stack' not in st.session_state:
    st.session_state.redo_stack = []

board = st.session_state.board
redo_stack = st.session_state.redo_stack

# --- 2. AI 엔진 (전략적 평가 함수) ---

# 기물 기본 점수
piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# [NEW] 위치 점수표 (Piece-Square Tables)
# 백(White) 기준: 아래쪽(a1)이 0, 위쪽(h8)이 63
# 중앙에 있을수록, 전진할수록 점수가 높도록 설정

# 폰: 중앙 전진 장려, 시작 위치는 0
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

# 나이트: 중앙 장악 장려, 구석(패널티) 기피
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

# 비숍: 좋은 대각선 및 중앙 선호
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

# 룩: 7번째 랭크(상대 진영 깊숙이) 선호, 중앙 열 선호
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

# 퀸: 중앙 활동성 중시
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

# 킹: 초반에는 구석(캐슬링) 안전 선호
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
        if board.turn: return -99999 # 백 차례에 체크메이트 당함 = 흑 승리
        else: return 99999
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    # 모든 위치를 순회하며 점수 계산
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            # 1. 기물 기본 점수
            value = piece_values[piece.piece_type]
            
            # 2. 위치 가산점 (PST)
            if piece.piece_type == chess.PAWN:
                table = pawntable
            elif piece.piece_type == chess.KNIGHT:
                table = knightstable
            elif piece.piece_type == chess.BISHOP:
                table = bishopstable
            elif piece.piece_type == chess.ROOK:
                table = rookstable
            elif piece.piece_type == chess.QUEEN:
                table = queenstable
            elif piece.piece_type == chess.KING:
                table = kingstable
            else:
                table = [0] * 64

            # 흑(Black)일 경우 테이블을 뒤집어서(Mirror) 적용해야 함
            if piece.color == chess.WHITE:
                position_score = table[square]
                score += (value + position_score)
            else:
                # 흑은 위쪽(63)이 본진이므로 테이블 대칭 적용
                position_score = table[chess.square_mirror(square)]
                score -= (value + position_score)
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    legal_moves = list(board.legal_moves)
    # 캡처 움직임을 먼저 탐색하도록 정렬 (효율성 증가)
    legal_moves.sort(key=lambda move: board.is_capture(move), reverse=True)

    if maximizing_player:
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
    else:
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

def get_best_move(board, depth):
    best_move = None
    best_value = float('inf') # 흑(AI)은 점수를 낮춰야 함
    
    legal_moves = list(board.legal_moves)
    legal_moves.sort(key=lambda move: board.is_capture(move), reverse=True)

    # 첫 번째 수에 대해서는 진행 상황을 보여주기 어려우므로 그냥 계산
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
    st.header("⚙️ 게임 설정")
    board_size = st.slider("체스판 크기 (px)", 300, 1000, 600, 50)
    
    # 난이도 설정
    difficulty = st.selectbox("AI 난이도", ["초급 (Depth 1)", "중급 (Depth 2 - 추천)", "고급 (Depth 3 - 느림)"])
    ai_depth = 1 if "초급" in difficulty else (2 if "중급" in difficulty else 3)

    st.markdown("---")
    st.header("제어")
    
    col_u, col_r = st.columns(2)
    with col_u:
        if st.button("⬅️ 무르기"):
            if len(board.move_stack) >= 2:
                st.session_state.redo_stack.append(board.pop())
                st.session_state.redo_stack.append(board.pop())
                st.toast("무르기 완료")
                st.rerun()
    with col_r:
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
    
    if board.is_check(): st.warning("⚠️ 체크!")
    if board.is_game_over(): st.error(f"게임 종료! {board.result()}")
    
    with st.expander("이동 기록"):
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
    st.markdown("### 🕹️ 조작")
    if not board.is_game_over():
        with st.form(key='move_form'):
            user_move = st.text_input("나의 수 입력", key="input", placeholder="예: e4, Nf3")
            submit = st.form_submit_button("두기")
            
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
                    st.error("규칙 위반입니다.")
            except ValueError:
                st.error("잘못된 표기법입니다.")
    else:
        st.success("게임 종료!")
