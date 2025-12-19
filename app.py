import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Master Chess Board", page_icon="♟️", layout="wide")

# --- CSS: 디자인의 핵심 (여백 제거 + 바둑판 무늬) ---
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp { background-color: #f0f2f6; }
    
    /* [중요] 컬럼 사이의 흰색 틈(Gap) 강제 삭제 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    
    /* 컬럼 내부 여백 삭제 */
    div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
        flex: 1 1 auto !important; /* 비율 강제 조정 */
    }

    /* 버튼 스타일 (정사각형) */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1;
        font-size: 40px !important;
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        line-height: 1 !important;
    }

    /* 체스판 색상 (클래식 우드 테마로 복귀 - 눈이 가장 편함) */
    /* 어두운 칸 (Primary) -> 갈색 */
    div.stButton > button[kind="primary"] {
        background-color: #b58863 !important;
        color: white !important;
    }
    /* 밝은 칸 (Secondary) -> 베이지색 */
    div.stButton > button[kind="secondary"] {
        background-color: #f0d9b5 !important;
        color: black !important;
    }

    /* 선택/포커스 효과 */
    div.stButton > button:focus {
        background-color: #f7e034 !important; /* 노란색 강조 */
        color: black !important;
        z-index: 10;
        box-shadow: inset 0 0 0 3px #e6bf00 !important; /* 테두리 대신 내부 그림자로 깨짐 방지 */
    }

    /* 좌표 스타일 */
    .coord-rank {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        font-weight: bold;
        font-size: 16px;
        color: #555;
    }
    .coord-file {
        display: flex;
        justify-content: center;
        padding-top: 5px;
        font-weight: bold;
        font-size: 16px;
        color: #555;
    }
    
    /* 모바일 글자 크기 조정 */
    @media (max-width: 600px) {
        div.stButton > button { font-size: 24px !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state:
    st.session_state.selected_square = None
if 'msg' not in st.session_state:
    st.session_state.msg = "게임을 시작합니다!"
if 'player_color' not in st.session_state:
    st.session_state.player_color = chess.WHITE
if 'hint_move' not in st.session_state:
    st.session_state.hint_move = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'redo_stack' not in st.session_state: # [복구] 다시 실행 스택
    st.session_state.redo_stack = []

# --- Stockfish 경로 ---
stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# --- 로직 함수들 ---
def play_engine_move(skill_level):
    if not stockfish_path or st.session_state.board.is_game_over(): return
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        engine.configure({"Skill Level": skill_level})
        result = engine.play(st.session_state.board, chess.engine.Limit(time=0.2 + (skill_level * 0.05)))
        st.session_state.board.push(result.move)
        st.session_state.redo_stack = [] # 새 수가 두어지면 redo 기록 삭제
        st.session_state.hint_move = None
        engine.quit()
        st.session_state.msg = "당신의 차례입니다!"
    except: pass

def show_hint():
    if not stockfish_path: return
    with st.spinner("힌트 계산 중..."):
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        res = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
        st.session_state.hint_move = res.move
        st.session_state.msg = f"추천 수: {st.session_state.board.san(res.move)}"
        engine.quit()

def handle_click(sq):
    if st.session_state.board.turn != st.session_state.player_color: return
    
    st.session_state.hint_move = None
    if st.session_state.selected_square is None:
        p = st.session_state.board.piece_at(sq)
        if p and p.color == st.session_state.board.turn:
            st.session_state.selected_square = sq
            st.session_state.msg = f"선택: {chess.square_name(sq)}"
    else:
        if st.session_state.selected_square == sq:
            st.session_state.selected_square = None
            st.session_state.msg = "취소됨"
        else:
            m = chess.Move(st.session_state.selected_square, sq)
            if st.session_state.board.piece_at(st.session_state.selected_square).piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
                m.promotion = chess.QUEEN
            if m in st.session_state.board.legal_moves:
                st.session_state.board.push(m)
                st.session_state.selected_square = None
                st.session_state.redo_stack = [] # 새 행동 시 Redo 불가
                st.session_state.msg = "이동 완료!"
            else:
                p = st.session_state.board.piece_at(sq)
                if p and p.color == st.session_state.board.turn:
                    st.session_state.selected_square = sq
                    st.session_state.msg = "선택 변경"
                else:
                    st.session_state.msg = "이동 불가"

def undo_move():
    if len(st.session_state.board.move_stack) >= 2:
        m1 = st.session_state.board.pop()
        m2 = st.session_state.board.pop()
        st.session_state.redo_stack.append(m2)
        st.session_state.redo_stack.append(m1)
        st.session_state.msg = "무르기 완료"

def redo_move(): # [복구] 다시 실행 함수
    if len(st.session_state.redo_stack) >= 2:
        m1 = st.session_state.redo_stack.pop()
        m2 = st.session_state.redo_stack.pop()
        st.session_state.board.push(m1)
        st.session_state.board.push(m2)
        st.session_state.msg = "다시 실행 완료"
    else:
        st.session_state.msg = "되돌릴 수가 없습니다."

def analyze_game():
    if not stockfish_path or not st.session_state.board.move_stack: return
    scores = []
    board_copy = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    prog = st.progress(0)
    for i, m in enumerate(st.session_state.board.move_stack):
        board_copy.push(m)
        info = engine.analyse(board_copy, chess.engine.Limit(time=0.05))
        scores.append(info["score"].white().score(mate_score=1000))
        prog.progress((i+1)/len(st.session_state.board.move_stack))
    engine.quit()
    st.session_state.analysis_data = scores
    prog.empty()

# ================= UI 구성 =================
st.title("♟️ Master Chess Board")

# --- 사이드바 ---
with st.sidebar:
    st.header("설정")
    color_opt = st.radio("내 진영", ["White (선공)", "Black (후공)"])
    new_color = chess.WHITE if "White" in color_opt else chess.BLACK
    skill = st.slider("AI 레벨", 0, 20, 5)
    
    if st.button("🔄 새 게임", type="primary", use_container_width=True):
        st.session_state.board = chess.Board()
        st.session_state.selected_square = None
        st.session_state.player_color = new_color
        st.session_state.redo_stack = []
        st.session_state.analysis_data = None
        st.session_state.hint_move = None
        st.rerun()
    
    st.divider()
    
    # [복구] 무르기 / 앞으로 가기 버튼 배치
    col_undo, col_redo = st.columns(2)
    with col_undo:
        if st.button("⬅️ 무르기"):
            undo_move()
            st.rerun()
    with col_redo:
        if st.button("➡️ 되살리기"): # Redo 버튼
            redo_move()
            st.rerun()
            
    if st.button("💡 힌트 보기", use_container_width=True):
        show_hint()
        st.rerun()

# --- 메인 화면 레이아웃 ---
main_col, info_col = st.columns([2, 1])

with main_col:
    is_white = st.session_state.player_color == chess.WHITE
    ranks = range(7, -1, -1) if is_white else range(8)
    files = range(8) if is_white else range(7, -1, -1)
    file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

    # 비율: 좌표(0.7) + 8칸(1)
    col_ratios = [0.7] + [1] * 8

    # --- 보드 렌더링 ---
    for rank in ranks:
        # gap="0"을 넣어도 CSS가 우선 적용되지만, 명시적으로 넣음
        cols = st.columns(col_ratios, gap="small")
        
        # 좌측 좌표
        cols[0].markdown(f"<div class='coord-rank'>{rank + 1}</div>", unsafe_allow_html=True)
        
        for i, file in enumerate(files):
            sq = chess.square(file, rank)
            piece = st.session_state.board.piece_at(sq)
            symbol = piece.unicode_symbol() if piece else "⠀"
            
            # 색상: (rank + file) % 2 == 0 이면 어두운 색
            is_dark_square = (rank + file) % 2 == 0
            btn_type = "primary" if is_dark_square else "secondary"
            
            if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
                handle_click(sq)
                st.rerun()

    # --- 하단 좌표 ---
    footer = st.columns(col_ratios, gap="small")
    footer[0].write("")
    for i, label in enumerate(file_labels):
        footer[i+1].markdown(f"<div class='coord-file'>{label}</div>", unsafe_allow_html=True)

with info_col:
    st.info(st.session_state.msg)
    
    if st.session_state.board.is_check(): st.error("🔥 체크!")
    if st.session_state.board.is_game_over():
        st.success(f"게임 종료: {st.session_state.board.result()}")
        if st.button("📊 게임 분석", use_container_width=True):
            analyze_game(); st.rerun()

    if st.session_state.analysis_data:
        st.line_chart(st.session_state.analysis_data)
        st.caption("그래프: 위(백 유리) / 아래(흑 유리)")

# AI 턴 실행
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(skill)
    st.rerun()
