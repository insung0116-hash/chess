import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Streamlit Chess Pro", page_icon="♟️", layout="centered")

# --- 스타일(CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    
    /* 버튼 스타일 */
    div.stButton > button {
        width: 45px !important;
        height: 45px !important;
        font-size: 28px !important;
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        line-height: 1 !important;
        border-radius: 4px !important;
    }
    
    /* 포커스 효과 */
    div.stButton > button:focus {
        border: 2px solid #e6bf00 !important;
        color: black !important;
    }

    [data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        padding: 0 !important;
        gap: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'msg' not in st.session_state:
    st.session_state.msg = "게임을 시작합니다! (White)"
if 'redo_stack' not in st.session_state:
    st.session_state.redo_stack = []
if 'hint_move' not in st.session_state:
    st.session_state.hint_move = None  # 힌트 저장용

# --- Stockfish 경로 ---
stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# --- 1. AI 수 두기 ---
def play_engine_move(skill_level):
    if not stockfish_path: return
    
    with st.spinner(f"🤖 AI(Lv.{skill_level}) 생각 중..."):
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            engine.configure({"Skill Level": skill_level})
            think_time = 0.1 + (skill_level * 0.05)
            result = engine.play(st.session_state.board, chess.engine.Limit(time=think_time))
            
            st.session_state.board.push(result.move)
            st.session_state.redo_stack = [] # 새 미래 생성
            st.session_state.hint_move = None # 힌트 초기화
            
            engine.quit()
            st.session_state.msg = "당신의 차례입니다!"
        except Exception as e:
            st.error(f"AI 에러: {e}")

# --- 2. 힌트 보기 (New!) ---
def show_hint():
    if not stockfish_path:
        st.warning("엔진이 없어서 힌트를 볼 수 없습니다.")
        return
    
    with st.spinner("💡 최선의 수를 찾는 중..."):
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            # 힌트는 항상 최강의 실력으로 조언 (시간 1.5초 사용)
            result = engine.play(st.session_state.board, chess.engine.Limit(time=1.5))
            st.session_state.hint_move = result.move
            
            # 사람이 읽기 쉬운 좌표로 변환
            move_san = st.session_state.board.san(result.move)
            st.session_state.msg = f"💡 추천 수: {move_san} (파란색 칸 확인)"
            engine.quit()
        except Exception as e:
            st.error(f"힌트 에러: {e}")

# --- 3. 무르기/다시실행 ---
def undo_move():
    if len(st.session_state.board.move_stack) >= 2:
        m1 = st.session_state.board.pop()
        m2 = st.session_state.board.pop()
        st.session_state.redo_stack.append(m2)
        st.session_state.redo_stack.append(m1)
        st.session_state.hint_move = None
        st.session_state.msg = "한 수 물렀습니다."
        st.session_state.selected_square = None
    else:
        st.session_state.msg = "무를 수 없습니다."

def redo_move():
    if len(st.session_state.redo_stack) >= 2:
        m1 = st.session_state.redo_stack.pop()
        m2 = st.session_state.redo_stack.pop()
        st.session_state.board.push(m1)
        st.session_state.board.push(m2)
        st.session_state.hint_move = None
        st.session_state.msg = "다시 실행했습니다."

# --- 4. 클릭 처리 ---
def handle_click(square_index):
    board = st.session_state.board
    selected = st.session_state.selected_square
    
    # 클릭하면 힌트 표시는 사라지는 게 깔끔함
    st.session_state.hint_move = None

    if selected is None:
        piece = board.piece_at(square_index)
        if piece and piece.color == board.turn:
            st.session_state.selected_square = square_index
            st.session_state.msg = f"선택: {chess.square_name(square_index)}"
        else:
            st.session_state.msg = "내 말을 선택하세요."
    else:
        if selected == square_index:
            st.session_state.selected_square = None
            st.session_state.msg = "선택 취소."
            return

        move = chess.Move(from_square=selected, to_square=square_index)
        if board.piece_at(selected).piece_type == chess.PAWN and chess.square_rank(square_index) in [0, 7]:
            move.promotion = chess.QUEEN

        if move in board.legal_moves:
            board.push(move)
            st.session_state.selected_square = None
            st.session_state.redo_stack = []
            st.session_state.msg = "이동 완료!"
        else:
            piece = board.piece_at(square_index)
            if piece and piece.color == board.turn:
                st.session_state.selected_square = square_index
                st.session_state.msg = f"변경: {chess.square_name(square_index)}"
            else:
                st.session_state.msg = "이동 불가."

# ================= UI 구성 =================
st.title("♟️ Streamlit Chess Pro")

# 상단 컨트롤
col_ctrl1, col_ctrl2 = st.columns([1, 2])
with col_ctrl1:
    skill = st.slider("난이도 (Level)", 0, 20, 3)
with col_ctrl2:
    st.info(st.session_state.msg)

col_main, col_side = st.columns([1.5, 1])

# --- 보드 렌더링 ---
with col_main:
    for rank in range(7, -1, -1):
        cols = st.columns(8, gap="small")
        for file in range(8):
            square_index = chess.square(file, rank)
            piece = st.session_state.board.piece_at(square_index)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            # --- 색상 로직 (중요) ---
            # 1. 기본 체크무늬
            is_light = (rank + file) % 2 != 0
            bg_color = "#f0d9b5" if is_light else "#b58863"
            
            # 2. 마지막 수 강조 (연두색)
            if st.session_state.board.move_stack:
                last = st.session_state.board.peek()
                if square_index in [last.from_square, last.to_square]:
                    bg_color = "#cdd26a"

            # 3. 힌트 강조 (하늘색) - 우선순위 높음
            if st.session_state.hint_move:
                if square_index in [st.session_state.hint_move.from_square, st.session_state.hint_move.to_square]:
                    bg_color = "#89cff0" # Baby Blue

            # 4. 현재 선택된 말 (노란색) - 최우선 순위
            if st.session_state.selected_square == square_index:
                bg_color = "#f7e034"

            # 버튼 생성 (배경색은 Streamlit 한계로 완벽하진 않으나 선택/힌트는 구분됨)
            # 여기서는 선택/힌트 표시를 위해 텍스트 색이나 테두리 대신
            # "이모지"와 "메시지"로 보완하고, CSS로 focus 효과를 줍니다.
            
            # 힌트가 있는 칸이면 표식을 좀 더 명확히 (버튼 텍스트 옆에 점 찍기 등은 칸 깨짐)
            # 색상 적용이 제한적이므로 힌트 칸은 아이콘을 변경할 수도 있지만,
            # 깔끔하게 위에서 계산한 로직대로 동작합니다.
            
            # 버튼 렌더링
            btn = cols[file].button(symbol, key=f"{square_index}")
            
            # 힌트 위치 표시를 위한 마킹 (텍스트 색상은 못 바꾸지만...)
            # *Streamlit pure python으로는 배경색 개별 지정 불가*
            # 따라서 힌트 위치는 메시지와 아래 '💡' 버튼으로 확인해야 함.
            # 하지만 힌트 좌표가 텍스트로 나오므로 충분히 알 수 있음.

            if btn:
                handle_click(square_index)
                st.rerun()

# --- 사이드바 메뉴 ---
with col_side:
    st.write("### 게임 메뉴")
    
    if st.button("💡 힌트 보기 (Hint)", type="primary", use_container_width=True):
        show_hint()
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ 무르기"):
            undo_move()
            st.rerun()
    with c2:
        if st.button("➡️ 되살리기"):
            redo_move()
            st.rerun()
            
    st.markdown("---")
    if st.button("🔄 새 게임"):
        st.session_state.board = chess.Board()
        st.session_state.redo_stack = []
        st.session_state.hint_move = None
        st.session_state.msg = "새 게임!"
        st.rerun()

    # 상태 정보
    if st.session_state.hint_move:
        # 힌트 텍스트 강조
        st.warning(f"추천: {st.session_state.board.san(st.session_state.hint_move)}")

    if st.session_state.board.is_check():
        st.error("🔥 체크!")
    if st.session_state.board.is_game_over():
        st.success(f"게임 종료: {st.session_state.board.result()}")

# AI 자동 실행
if not st.session_state.board.is_game_over() and st.session_state.board.turn == chess.BLACK:
    play_engine_move(skill)
    st.rerun()
