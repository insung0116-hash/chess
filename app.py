import streamlit as st
import chess
import chess.engine
import shutil
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="Classic Chess", page_icon="♟️", layout="wide")

# --- CSS: CSS Grid를 이용한 강제 통합 및 여백 삭제 ---
st.markdown("""
<style>
    /* 1. 전체 배경 */
    .stApp { background-color: #e0e0e0; }
    
    /* 2. Streamlit 기본 여백 제거 (가장 중요) */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 900px; /* 체스판이 너무 퍼지지 않게 중앙 고정 */
    }

    /* 3. 컬럼 컨테이너(Row)를 강제로 붙이기 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
    }

    /* 4. 개별 컬럼(Column) 패딩 제거 및 너비 강제 */
    div[data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        min-width: 0px !important;
        flex: 1 !important; /* 비율대로 꽉 채움 */
    }

    /* 5. 버튼(체스 칸) 스타일: 완전한 정사각형 & 꽉 채우기 */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important; /* 정사각형 강제 */
        border: none !important;
        border-radius: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
        line-height: 1 !important;
        
        /* 폰트 설정 */
        font-size: 2.8vw !important; /* 화면 너비 비례 폰트 */
        font-weight: bold;
        
        /* 텍스트 렌더링 최적화 */
        display: flex;
        align-items: center;
        justify-content: center;
        padding-bottom: 5px !important; /* 이모지 수직 중앙 보정 */
        
        /* 그림자 제거 (흰 선 원인 차단) */
        box-shadow: none !important;
        outline: none !important;
        
        /* 텍스트 외곽선 (가독성) */
        color: black !important;
        text-shadow: 
            1.5px 1.5px 0 #fff, -1.5px 1.5px 0 #fff, 
            1.5px -1.5px 0 #fff, -1.5px -1.5px 0 #fff !important;
    }
    
    /* 미세 조정: 모바일/좁은 화면에서 폰트 크기 제한 */
    @media (min-width: 900px) {
        div.stButton > button { font-size: 36px !important; }
    }

    /* 6. 마우스 호버 효과 */
    div.stButton > button:hover {
        background-color: #ffe066 !important;
        z-index: 2; /* 호버 시 위로 올라오게 */
        box-shadow: inset 0 0 0 3px rgba(0,0,0,0.2) !important;
    }
    
    /* 7. 선택된 칸 효과 */
    div.stButton > button:focus {
        background-color: #ffcc00 !important;
        box-shadow: inset 0 0 0 4px #d9534f !important; /* 붉은 테두리 */
        color: black !important;
    }

    /* 8. 체스판 색상 (클래식 우드 스타일) */
    div.stButton > button[kind="primary"] {
        background-color: #b58863 !important; /* 갈색 (Dark) */
    }
    div.stButton > button[kind="secondary"] {
        background-color: #f0d9b5 !important; /* 베이지색 (Light) */
    }

    /* 9. 좌표 스타일 */
    .rank-label {
        height: 100%; display: flex; align-items: center; justify-content: flex-end;
        font-weight: bold; font-size: 18px; color: #555; padding-right: 10px;
        margin-top: -3px;
    }
    .file-label {
        width: 100%; text-align: center; font-weight: bold; font-size: 18px; color: #555;
        margin-top: 5px;
    }
    
    /* 10. 사이드바 등 외부 버튼은 정상적으로 표시 */
    section[data-testid="stSidebar"] div.stButton > button,
    div.control-area div.stButton > button {
        width: 100% !important; aspect-ratio: auto !important;
        border-radius: 4px !important; margin: 5px 0 !important;
        font-size: 16px !important; text-shadow: none !important;
        background-color: #ffffff !important; border: 1px solid #ccc !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 세션 초기화 ---
if 'board' not in st.session_state: st.session_state.board = chess.Board()
if 'selected_square' not in st.session_state: st.session_state.selected_square = None
if 'msg' not in st.session_state: st.session_state.msg = "게임을 시작합니다."
if 'player_color' not in st.session_state: st.session_state.player_color = chess.WHITE
if 'hint_move' not in st.session_state: st.session_state.hint_move = None
if 'analysis_data' not in st.session_state: st.session_state.analysis_data = None
if 'redo_stack' not in st.session_state: st.session_state.redo_stack = []

stockfish_path = shutil.which("stockfish")
if not stockfish_path and os.path.exists("/usr/games/stockfish"):
    stockfish_path = "/usr/games/stockfish"

# --- 로직 함수들 ---
def play_engine_move(skill_level):
    if not stockfish_path or st.session_state.board.is_game_over(): return
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        engine.configure({"Skill Level": skill_level})
        result = engine.play(st.session_state.board, chess.engine.Limit(time=0.2))
        st.session_state.board.push(result.move)
        st.session_state.redo_stack = [] 
        engine.quit()
        st.session_state.msg = "당신의 차례입니다."
    except: pass

def show_hint():
    if not stockfish_path: return
    with st.spinner("생각 중..."):
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        res = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
        st.session_state.hint_move = res.move
        st.session_state.msg = f"힌트: {st.session_state.board.san(res.move)}"
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
            st.session_state.msg = "취소"
        else:
            m = chess.Move(st.session_state.selected_square, sq)
            if st.session_state.board.piece_at(st.session_state.selected_square).piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
                m.promotion = chess.QUEEN
            if m in st.session_state.board.legal_moves:
                st.session_state.board.push(m)
                st.session_state.selected_square = None
                st.session_state.redo_stack = [] 
                st.session_state.msg = "착수 완료"
            else:
                p = st.session_state.board.piece_at(sq)
                if p and p.color == st.session_state.board.turn:
                    st.session_state.selected_square = sq
                    st.session_state.msg = "선택 변경"
                else:
                    st.session_state.msg = "이동 불가"

def undo_move():
    if len(st.session_state.board.move_stack) >= 2:
        m1 = st.session_state.board.pop(); m2 = st.session_state.board.pop()
        st.session_state.redo_stack.extend([m2, m1])
        st.session_state.msg = "무르기 완료"

def redo_move():
    if len(st.session_state.redo_stack) >= 2:
        m1 = st.session_state.redo_stack.pop(); m2 = st.session_state.redo_stack.pop()
        st.session_state.board.push(m1); st.session_state.board.push(m2)
        st.session_state.msg = "되돌리기 완료"

def analyze_game():
    if not stockfish_path or not st.session_state.board.move_stack: return
    scores = []
    board_copy = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    for m in st.session_state.board.move_stack:
        board_copy.push(m)
        info = engine.analyse(board_copy, chess.engine.Limit(time=0.05))
        scores.append(info["score"].white().score(mate_score=1000))
    engine.quit()
    st.session_state.analysis_data = scores

# ================= UI 레이아웃 =================
st.title("♟️ Classic Chess")

# 컨트롤 패널
st.markdown('<div class="control-area">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns([1,1,1,2])
with col1:
    if st.button("⬅️ 무르기"): undo_move(); st.rerun()
with col2:
    if st.button("➡️ 되살리기"): redo_move(); st.rerun()
with col3:
    if st.button("🔄 재시작"): 
        st.session_state.board.reset()
        st.session_state.redo_stack = []
        st.rerun()
with col4:
    if st.button("💡 힌트 보기"): show_hint(); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 메인 체스판 루프 (구조적 통합) ---
is_white = st.session_state.player_color == chess.WHITE
ranks = range(7, -1, -1) if is_white else range(8)
files = range(8) if is_white else range(7, -1, -1)
file_labels = ['A','B','C','D','E','F','G','H'] if is_white else ['H','G','F','E','D','C','B','A']

# [중요] 9개의 컬럼 비율 설정: (좌표 0.4) + (체스판 8칸 * 1.0)
col_ratios = [0.4] + [1] * 8

for rank in ranks:
    # 좌표와 체스판을 '같은 줄'에 생성하여 높이 불일치 문제 해결
    cols = st.columns(col_ratios)
    
    # 1. 왼쪽 좌표 (첫 번째 컬럼)
    cols[0].markdown(f"<div class='rank-label'>{rank + 1}</div>", unsafe_allow_html=True)
    
    # 2. 체스판 8칸 (나머지 컬럼들)
    for i, file in enumerate(files):
        sq = chess.square(file, rank)
        piece = st.session_state.board.piece_at(sq)
        symbol = piece.unicode_symbol() if piece else "⠀"  # 공백 문자
        
        # 체스판 색상 계산
        is_dark = (rank + file) % 2 == 0
        btn_type = "primary" if is_dark else "secondary"
        
        # 버튼 생성
        if cols[i+1].button(symbol, key=f"sq_{sq}", type=btn_type):
            handle_click(sq)
            st.rerun()

# --- 하단 알파벳 좌표 ---
footer = st.columns(col_ratios)
footer[0].write("") # 좌표 아래 공백
for i, label in enumerate(file_labels):
    footer[i+1].markdown(f"<div class='file-label'>{label}</div>", unsafe_allow_html=True)

# --- 상태 메시지 ---
st.write("")
st.info(f"📢 {st.session_state.msg}")

if st.session_state.board.is_check():
    st.error("🔥 체크!")

if st.session_state.board.is_game_over():
    st.success(f"게임 종료: {st.session_state.board.result()}")
    if st.button("📊 게임 분석 그래프 보기"):
        analyze_game()
        st.rerun()

if st.session_state.analysis_data:
    st.line_chart(st.session_state.analysis_data)

# AI 턴 자동 실행
if not st.session_state.board.is_game_over() and st.session_state.board.turn != st.session_state.player_color:
    play_engine_move(3) # 난이도 3
    st.rerun()
