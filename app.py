import streamlit as st
import chess
import chess.svg
import chess.engine
import shutil

# --- 페이지 설정 ---
st.set_page_config(page_title="Grandmaster Chess", page_icon="🏆", layout="wide")

st.title("🏆 그랜드마스터 AI (Stockfish)")
st.markdown("세계 최강 엔진 **Stockfish**가 탑재되었습니다. 이제 진짜 체스를 경험해보세요.")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

if 'redo_stack' not in st.session_state:
    st.session_state.redo_stack = []

board = st.session_state.board

# --- 2. 스톡피쉬 엔진 경로 찾기 ---
# 시스템에 설치된 stockfish의 위치를 찾습니다.
stockfish_path = shutil.which("stockfish")

# 로컬(내 컴퓨터) 테스트용 경로 (필요시 수정)
if stockfish_path is None:
    # 윈도우나 맥 등 로컬에서 돌릴 땐 경로를 직접 지정해야 할 수도 있습니다.
    # 예: stockfish_path = "/usr/games/stockfish" 
    pass

# --- 3. AI 함수 (엔진 사용) ---
def get_engine_move(board, skill_level=1, time_limit=0.1):
    """
    Stockfish 엔진을 사용하여 수를 둡니다.
    skill_level: 0 (가장 못함) ~ 20 (신)
    time_limit: 생각하는 시간 (초)
    """
    if stockfish_path is None:
        return None

    try:
        # 엔진 실행
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        
        # 난이도 설정
        engine.configure({"Skill Level": skill_level})
        
        # 수 계산 요청
        result = engine.play(board, chess.engine.Limit(time=time_limit))
        
        # 엔진 종료
        engine.quit()
        
        return result.move
    except Exception as e:
        st.error(f"엔진 오류: {e}")
        return None

# --- 4. 사이드바 ---
with st.sidebar:
    st.header("⚙️ 게임 설정")
    board_size = st.slider("체스판 크기", 300, 1000, 600, 50)
    
    # [NEW] 스톡피쉬 난이도 조절
    st.markdown("### 🤖 AI 수준 (Elo)")
    difficulty = st.select_slider(
        "난이도를 선택하세요",
        options=["입문자 (Lv 0)", "초보 (Lv 3)", "중수 (Lv 7)", "고수 (Lv 12)", "그랜드마스터 (Lv 20)"],
        value="초보 (Lv 3)"
    )
    
    # 선택된 텍스트를 숫자로 변환
    if "Lv 0" in difficulty: skill = 0
    elif "Lv 3" in difficulty: skill = 3
    elif "Lv 7" in difficulty: skill = 7
    elif "Lv 12" in difficulty: skill = 12
    else: skill = 20

    st.markdown("---")
    
    # 제어 버튼들
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

    if stockfish_path is None:
        st.error("⚠️ Stockfish 엔진을 찾을 수 없습니다. packages.txt 파일을 확인하세요.")

    st.markdown("---")
    if board.turn == chess.WHITE: st.info("🟢 당신의 차례")
    else: st.warning("🔴 AI 생각 중...")
    
    with st.expander("📜 이동 기록"):
        move_log = []
        temp_board = chess.Board()
        for i, move in enumerate(board.move_stack):
            san = temp_board.san(move)
            temp_board.push(move)
            if i % 2 == 0: move_log.append(f"{i//2 + 1}. {san}")
            else: move_log[-1] += f" {san}"
        st.text("\n".join(move_log))

# --- 5. 메인 화면 ---
col1, col2 = st.columns([2, 1])

with col1:
    last_move = board.peek() if board.move_stack else None
    board_svg = chess.svg.board(board=board, lastmove=last_move, size=board_size)
    st.markdown(f'<div style="display: flex; justify-content: center;">{board_svg}</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 🕹️ 조작 및 특수 규칙")
    with st.expander("규칙 가이드", expanded=True):
        st.markdown("""
        - **입력**: `e4`, `Nf3`, `O-O` (캐슬링)
        - **난이도 설명**:
            - **입문자**: 마구잡이로 두기도 합니다.
            - **중수**: 웬만한 사람은 이기기 힘듭니다.
            - **그랜드마스터**: 인류 최강 수준입니다. 절대 못 이깁니다.
        """)

    if not board.is_game_over():
        with st.form(key='move_form'):
            user_move = st.text_input("나의 수 입력", key="input", placeholder="예: e4, O-O")
            submit = st.form_submit_button("두기")
            
        if submit and user_move:
            try:
                move = board.parse_san(user_move)
                if move in board.legal_moves:
                    st.session_state.redo_stack = []
                    board.push(move)
                    
                    if not board.is_game_over():
                        with st.spinner("AI가 최적의 수를 찾는 중..."):
                            # 엔진 호출
                            ai_move = get_engine_move(board, skill_level=skill, time_limit=0.5)
                            
                            if ai_move:
                                ai_san = board.san(ai_move)
                                board.push(ai_move)
                                st.toast(f"AI ({difficulty}): {ai_san}")
                            else:
                                st.error("AI 엔진 오류 발생")
                    st.rerun()
                else:
                    st.error("불가능한 수입니다.")
            except ValueError:
                st.error("표기법 오류입니다.")
    else:
        if board.is_checkmate():
            winner = "흑(AI)" if board.turn == chess.WHITE else "백(당신)"
            st.success(f"체크메이트! {winner} 승리!")
        else:
            st.info(f"게임 종료: {board.result()}")
