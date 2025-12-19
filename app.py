import streamlit as st
import chess
import chess.engine
import chess.svg
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Chess Pro", page_icon="♟️", layout="wide")

# --- 스타일(CSS) 대폭 수정: 크기 확대 ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    
    /* 1. 버튼(체스칸) 크기 확대 */
    div.stButton > button {
        width: 65px !important;        /* 너비 키움 (기존 45px -> 65px) */
        height: 65px !important;       /* 높이 키움 */
        font-size: 45px !important;    /* 글자(말) 크기 대폭 확대 (28px -> 45px) */
        padding: 0px !important;
        margin: 0px !important;
        border-radius: 6px !important;
        border: none !important;
        line-height: 1.1 !important;   /* 수직 정렬 보정 */
        transition: transform 0.1s;
    }
    
    /* 2. 마우스 올렸을 때 효과 */
    div.stButton > button:hover {
        transform: scale(1.05);
        z-index: 10;
    }

    /* 3. 선택/포커스 효과 */
    div.stButton > button:focus {
        border: 3px solid #e6bf00 !important;
        color: black !important;
        transform: scale(1.1);
    }
    
    /* 4. 컬럼 간격 강제 제거 (딱 붙이기) */
    [data-testid="column"] {
        width: 65px !important;       /* 컬럼 너비도 버튼에 맞춤 */
        flex: 0 0 auto !important;
        padding: 0 !important;
        gap: 0 !important;
        min-width: 0px !important;
    }
    
    /* 모바일 등 좁은 화면 대응 */
    @media (max-width: 600px) {
        div.stButton > button {
            width: 40px !important;
            height: 40px !important;
            font-size: 28px !important;
        }
        [data-testid="column"] { width: 40px !important; }
    }
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
    st.session_state.player_color = chess.WHITE 
if 'hint_move' not in st.session_state:
    st.session_state.hint_move = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None

# --- Stockfish 경로 ---
stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# ================= 로직 함수들 =================
def play_engine_move(skill_level):
    if not stockfish_path or st.session_state.board.is_game_over(): return
    with st.spinner(f"🤖 AI(Lv.{skill_level}) 생각 중..."):
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            engine.configure({"Skill Level": skill_level})
            # 생각 시간도 조금 늘림
            result = engine.play(st.session_state.board, chess.engine.Limit(time=0.2 + (skill_level * 0.05)))
            st.session_state.board.push(result.move)
            st.session_state.hint_move = None
            engine.quit()
            st.session_state.msg = "당신의 차례입니다!"
        except: pass

def analyze_game():
    if not stockfish_path: return
    move_stack = st.session_state.board.move_stack
    if not move_stack: return
    
    scores = []
    board_copy = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    progress = st.progress(0)
    
    for i, move in enumerate(move_stack):
        board_copy.push(move)
        info = engine.analyse(board_copy, chess.engine.Limit(time=0.05))
        score = info["score"].white().score(mate_score=1000)
        scores.append(score)
        progress.progress((i + 1) / len(move_stack))
    
    engine.quit()
    st.session_state.analysis_data = scores
    progress.empty()

def show_hint():
    if not stockfish_path: return
    with st.spinner("💡 힌트 계산 중..."):
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        result = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
        st.session_state.hint_move = result.move
        st.session_state.msg = f"추천 수: {st.session_state.board.san(result.move)}"
        engine.quit()

def handle_click(square_index):
    if st.session_state.board.turn != st.session_state.player_color:
        st.session_state.msg = "AI 턴입니다. 잠시만요!"
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
            st.session_state.msg = "내 말을 선택하세요."
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
st.title("♟️ 왕 큰 체스 (Big Chess)")

# 사이드바
with st.sidebar:
    st.header("설정")
    color = st.radio("진영:", ["White (선공)", "Black (후공)"])
    new_color = chess.WHITE if "White" in color else chess.BLACK
    skill = st.slider("AI 레벨", 0, 20, 3)
    
    if st.button("🔄 새 게임 (Reset)", type="primary", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.player_color = new_color
        st.session_state.analysis_data = None
        st.session_state.hint_move = None
        st.rerun()
        
    st.divider()
    if st.button("💡 힌트 보기"): show_hint(); st.rerun()
    if st.button("⬅️ 무르기"): 
        if len(st.session_state.board.move_stack) >= 2:
            st.session_state.board.pop(); st.session_state.board.pop(); st.rerun()

# 메인 레이아웃 (보드 공간 확보를 위해 비율 조정)
col_board, col_info = st.columns([2, 1]) 

with col_board:
    # 사용자 시점에 따라 보드 뒤집기
    ranks = range(7, -1, -1) if st.session_state.player_color == chess.WHITE else range(8)
    
    st.write("") # 상단 여백
    
    for rank in ranks:
        # 컬럼 생성 (gap을 0으로 설정해도 CSS가 우선 적용됨)
        cols = st.columns(8, gap="small")
        files = range(8) if st.session_state.player_color == chess.WHITE else range(7, -1, -1)
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            # --- 칸 색상 결정 ---
            is_light = (rank + file) % 2 != 0
            
            # 1. 이동 경로 강조 (연두색)
            highlight = False
            if st.session_state.board.move_stack:
                last = st.session_state.board.peek()
                if sq in [last.from_square, last.to_square]: highlight = True
            
            # 2. 힌트 강조 (하늘색)
            is_hint = False
            if st.session_state.hint_move and sq in [st.session_state.hint_move.from_square, st.session_state.hint_move.to_square]:
                is_hint = True
                
            # 3. 선택됨 (노란색)
            is_selected = (st.session_state.selected_square == sq)

            # 텍스트로 색상 차이 주기 (버튼 배경색 한계 극복용)
            # 힌트나 선택된 칸은 이모지 주변에 특수 공백이나 기호를 넣지 않고
            # CSS focus/active 상태와 위화감 없도록 둠.
            
            # 버튼 그리기
            # key는 유일해야 함
            if cols[i].button(symbol, key=f"btn_{sq}"):
                handle_click(sq)
                st.rerun()

            # *중요* 색상 주입을 위한 HTML 해킹 (Streamlit 공식 지원 아님, 작동 안 할 수 있음)
            # 대신 위 CSS에서 버튼 크기와 폰트 크기를 확실히 키워둠.

with col_info:
    st.markdown(f"### {st.session_state.msg}")
    
    turn_text = "당신의 차례" if st.session_state.board.turn == st.session_state.player_color else "AI 생각 중..."
    st.caption(f"상태: {turn_text}")
    
    if st.session_state.board.is_check(): st.error("🔥 체크!!")
    
    if st.session_state.board.is_game_over():
        st.success(f"게임 종료! ({st.session_state.board.result()})")
        if st.button("📊 게임 분석 실행", type="primary"):
            analyze_game()
            st.rerun()

    if st.session_state.analysis_data:
        st.line_chart(st.session_state.analysis_data)
        st.caption("위쪽: 백 유리 / 아래쪽: 흑 유리")

# AI 턴
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
