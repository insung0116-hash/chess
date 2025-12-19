import streamlit as st
import chess
import chess.engine
import chess.svg
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Chess Master Pro", page_icon="♟️", layout="wide")

# --- 스타일(CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    div.stButton > button {
        width: 45px !important; height: 45px !important;
        font-size: 28px !important; padding: 0 !important;
        border-radius: 4px !important; border: none !important;
        line-height: 1 !important;
    }
    div.stButton > button:focus {
        border: 2px solid #e6bf00 !important; color: black !important;
    }
    [data-testid="column"] { gap: 0 !important; padding: 0 !important; }
</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'msg' not in st.session_state:
    st.session_state.msg = "환영합니다! 진영을 선택하고 게임을 시작하세요."
if 'player_color' not in st.session_state:
    st.session_state.player_color = chess.WHITE # 기본값: 백
if 'hint_move' not in st.session_state:
    st.session_state.hint_move = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None # 분석 데이터 저장

# --- Stockfish 경로 확인 ---
stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# ================= 기능 함수들 =================

# 1. AI 수 두기
def play_engine_move(skill_level):
    if not stockfish_path or st.session_state.board.is_game_over(): return
    
    with st.spinner(f"🤖 AI(Lv.{skill_level}) 생각 중..."):
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            engine.configure({"Skill Level": skill_level})
            limit = chess.engine.Limit(time=0.1 + (skill_level * 0.05))
            result = engine.play(st.session_state.board, limit)
            
            st.session_state.board.push(result.move)
            st.session_state.hint_move = None
            engine.quit()
            st.session_state.msg = "당신의 차례입니다!"
        except Exception as e:
            st.error(f"AI 에러: {e}")

# 2. 게임 리뷰 (분석)
def analyze_game():
    if not stockfish_path: return
    
    move_stack = st.session_state.board.move_stack
    if not move_stack:
        st.warning("둔 수가 없어서 분석할 수 없습니다.")
        return

    scores = []
    board_copy = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 처음부터 끝까지 복기
    # 점수는 백(White) 기준 Centipawn (1폰 = 100점)
    for i, move in enumerate(move_stack):
        status_text.text(f"분석 중... ({i+1}/{len(move_stack)})")
        board_copy.push(move)
        
        # 각 수마다 0.1초씩만 빠르게 분석
        info = engine.analyse(board_copy, chess.engine.Limit(time=0.05))
        score = info["score"].white().score(mate_score=1000)
        scores.append(score)
        progress_bar.progress((i + 1) / len(move_stack))
    
    engine.quit()
    st.session_state.analysis_data = scores
    status_text.text("분석 완료!")
    progress_bar.empty()

# 3. 힌트
def show_hint():
    if not stockfish_path: return
    with st.spinner("💡 힌트 계산 중..."):
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        result = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
        st.session_state.hint_move = result.move
        st.session_state.msg = f"추천: {st.session_state.board.san(result.move)}"
        engine.quit()

# 4. 클릭 핸들러
def handle_click(square_index):
    # 내 차례가 아니면 클릭 무시
    if st.session_state.board.turn != st.session_state.player_color:
        st.session_state.msg = "아직 AI가 두는 중입니다."
        return

    board = st.session_state.board
    selected = st.session_state.selected_square
    st.session_state.hint_move = None

    if selected is None:
        piece = board.piece_at(square_index)
        if piece and piece.color == board.turn:
            st.session_state.selected_square = square_index
            st.session_state.msg = f"선택: {chess.square_name(square_index)}"
        else:
            st.session_state.msg = "당신의 말을 선택하세요."
    else:
        if selected == square_index:
            st.session_state.selected_square = None; st.session_state.msg = "취소됨"; return

        move = chess.Move(from_square=selected, to_square=square_index)
        if board.piece_at(selected).piece_type == chess.PAWN and chess.square_rank(square_index) in [0, 7]:
            move.promotion = chess.QUEEN

        if move in board.legal_moves:
            board.push(move)
            st.session_state.selected_square = None
            st.session_state.msg = "이동 완료!"
        else:
            piece = board.piece_at(square_index)
            if piece and piece.color == board.turn:
                st.session_state.selected_square = square_index; st.session_state.msg = "선택 변경"
            else:
                st.session_state.msg = "이동 불가"

# ================= UI 구성 =================
st.title("♟️ Chess Master Pro")

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 게임 설정")
    
    # 1. 진영 선택
    color_choice = st.radio("당신의 진영 선택:", ["White (선공)", "Black (후공)"], index=0)
    new_player_color = chess.WHITE if "White" in color_choice else chess.BLACK
    
    # 2. 난이도
    skill = st.slider("AI 난이도 (Level)", 0, 20, 5)
    
    st.markdown("---")
    
    # 3. 새 게임 버튼 (설정 적용)
    if st.button("🔄 새 게임 시작 (Reset)", type="primary", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.player_color = new_player_color
        st.session_state.analysis_data = None
        st.session_state.hint_move = None
        st.session_state.msg = "게임을 시작합니다!"
        st.rerun()

    st.markdown("---")
    st.write("**기능 메뉴**")
    if st.button("💡 힌트 보기"): show_hint(); st.rerun()
    if st.button("⬅️ 무르기"): 
        if len(st.session_state.board.move_stack) >= 2:
            st.session_state.board.pop(); st.session_state.board.pop()
            st.session_state.msg = "무르기 완료"; st.rerun()

# --- 메인 화면 ---
col1, col2 = st.columns([1.5, 1])

with col1: # 체스판
    # 흑을 선택했으면 보드를 뒤집어서 보여줌 (User Perspective)
    board_ranks = range(7, -1, -1) if st.session_state.player_color == chess.WHITE else range(8)
    
    for rank in board_ranks:
        cols = st.columns(8, gap="small")
        board_files = range(8) if st.session_state.player_color == chess.WHITE else range(7, -1, -1)
        
        for i, file in enumerate(board_files):
            square_index = chess.square(file, rank)
            piece = st.session_state.board.piece_at(square_index)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            # 색상 로직
            bg_color = "#f0d9b5" if (rank + file) % 2 != 0 else "#b58863"
            
            # 마지막 수 강조
            if st.session_state.board.move_stack:
                last = st.session_state.board.peek()
                if square_index in [last.from_square, last.to_square]: bg_color = "#cdd26a"
            
            # 힌트/선택 강조
            if st.session_state.hint_move and square_index in [st.session_state.hint_move.from_square, st.session_state.hint_move.to_square]:
                bg_color = "#89cff0"
            if st.session_state.selected_square == square_index:
                bg_color = "#f7e034"

            if cols[i].button(symbol, key=f"sq_{square_index}"):
                handle_click(square_index)
                st.rerun()

with col2: # 정보 및 리뷰창
    st.info(st.session_state.msg)
    
    turn_str = "White" if st.session_state.board.turn == chess.WHITE else "Black"
    st.caption(f"현재 차례: {turn_str}")
    
    if st.session_state.board.is_check(): st.error("🔥 체크!")
    
    # --- 게임 종료 시 리뷰 기능 활성화 ---
    if st.session_state.board.is_game_over():
        result = st.session_state.board.result()
        st.success(f"🏁 게임 종료! 결과: {result}")
        
        st.markdown("---")
        st.write("### 📊 게임 리뷰")
        if st.button("게임 분석 실행 (Analyze)", use_container_width=True):
            analyze_game()
            st.rerun()

    # 분석 데이터가 있으면 차트 그리기
    if st.session_state.analysis_data:
        st.write("#### 승률 흐름 (유리함 그래프)")
        st.line_chart(st.session_state.analysis_data)
        st.caption("위로 갈수록 백(White) 유리, 아래는 흑(Black) 유리")
        
        # 간단한 평가
        final_score = st.session_state.analysis_data[-1]
        if final_score > 100: evaluation = "백이 유리하게 끝났습니다."
        elif final_score < -100: evaluation = "흑이 유리하게 끝났습니다."
        else: evaluation = "박빙의 승부였습니다."
        st.write(evaluation)

# --- AI 자동 실행 로직 ---
# 게임 중이고, 내 차례가 아니면 AI가 둠
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
