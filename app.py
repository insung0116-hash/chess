import streamlit as st
import chess
import chess.engine
import shutil
import os
from streamlit_chessboard import st_chess_board

# --- 페이지 설정 ---
st.set_page_config(page_title="Grandmaster Chess (Mouse)", page_icon="🖱️", layout="wide")

st.title("🖱️ 마우스로 두는 스톡피쉬 체스")
st.markdown("이제 **마우스 드래그**나 **클릭**으로 말을 움직이세요! (키보드 ❌)")

# --- 1. 게임 상태 초기화 ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()

board = st.session_state.board

# --- 2. 스톡피쉬 엔진 경로 찾기 ---
stockfish_path = shutil.which("stockfish")
if stockfish_path is None:
    possible_paths = ["/usr/games/stockfish", "/usr/bin/stockfish", "/usr/local/bin/stockfish"]
    for path in possible_paths:
        if os.path.exists(path):
            stockfish_path = path
            break

# --- 3. AI 함수 ---
def get_engine_move(board, skill_level=1, time_limit=0.1):
    if not stockfish_path: return None
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        engine.configure({"Skill Level": skill_level})
        result = engine.play(board, chess.engine.Limit(time=time_limit))
        engine.quit()
        return result.move
    except: return None

# --- 4. 사이드바 ---
with st.sidebar:
    st.header("⚙️ 설정")
    # 난이도 조절
    difficulty = st.select_slider("AI 난이도", options=["입문(Lv0)", "초보(Lv3)", "중수(Lv7)", "고수(Lv12)", "신(Lv20)"], value="초보(Lv3)")
    
    if "Lv0" in difficulty: skill = 0
    elif "Lv3" in difficulty: skill = 3
    elif "Lv7" in difficulty: skill = 7
    elif "Lv12" in difficulty: skill = 12
    else: skill = 20

    st.markdown("---")
    
    # [새 게임] 버튼
    if st.button("🔄 새 게임 (Reset)", use_container_width=True):
        st.session_state.board = chess.Board()
        st.rerun()

    # [무르기] 버튼
    if st.button("⬅️ 한 수 무르기"):
        if len(board.move_stack) >= 2:
            board.pop() # AI 수 취소
            board.pop() # 내 수 취소
            st.rerun()

    st.markdown("---")
    
    # 상태 메시지
    if stockfish_path:
        st.success("✅ 엔진 가동 중")
    else:
        st.error("⚠️ Stockfish 없음 (packages.txt 확인)")

    # 이동 기록 표시
    with st.expander("📜 이동 기록"):
        move_log = []
        temp_board = chess.Board()
        for i, move in enumerate(board.move_stack):
            san = temp_board.san(move)
            temp_board.push(move)
            if i % 2 == 0: move_log.append(f"{i//2+1}. {san}")
            else: move_log[-1] += f" {san}"
        st.text("\n".join(move_log))

# --- 5. 메인 화면 (인터랙티브 체스판) ---

col1, col2 = st.columns([3, 1])

with col1:
    # 🚨 여기가 핵심! 마우스 조작 가능한 체스판 렌더링
    # 사용자가 수를 두면 move_data에 정보가 들어옵니다.
    move_data = st_chess_board(
        board=board, 
        key="chess_board", 
        orientation="white"  # 내가 백(White)
    )

    # --- 사용자 입력 처리 ---
    # 사용자가 마우스로 둬서 보드 상태가 변했는지 확인
    if move_data:
        # 라이브러리가 보내준 FEN(보드상태)과 내 내부 보드 상태가 다르면 -> 사용자가 둔 것
        # 하지만 이 라이브러리는 움직임을 감지해서 처리하는 로직이 필요함
        
        # 가장 최근 움직임(UCI)을 가져옴 (예: 'e2e4')
        if 'move' in move_data and move_data['move']:
            uci_move = move_data['move']
            try:
                move = chess.Move.from_uci(uci_move)
                
                # 내 차례이고, 둔 수가 합법적인 수라면
                if board.turn == chess.WHITE and move in board.legal_moves:
                    board.push(move)  # 1. 사용자 수 반영
                    
                    # 2. 게임 안 끝났으면 AI 차례
                    if not board.is_game_over():
                        with st.spinner("AI 생각 중..."):
                            ai_move = get_engine_move(board, skill_level=skill, time_limit=0.5)
                            if ai_move:
                                board.push(ai_move) # 3. AI 수 반영
                    
                    st.rerun() # 화면 갱신
            except:
                pass

with col2:
    st.markdown("### 🎮 조작 방법")
    st.info("""
    - **드래그 앤 드롭**: 말을 잡고 원하는 곳에 놓으세요.
    - **클릭 앤 클릭**: 말을 클릭하고 이동할 곳을 클릭하세요.
    - 더 이상 `e4` 같은 글자를 칠 필요가 없습니다!
    """)
    
    if board.is_checkmate():
        winner = "AI" if board.turn == chess.WHITE else "당신"
        st.error(f"👑 체크메이트! {winner} 승리!")
    elif board.is_game_over():
        st.warning(f"게임 종료: {board.result()}")
