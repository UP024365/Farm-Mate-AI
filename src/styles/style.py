import streamlit as st

def apply_custom_style(theme="Dark"):
    """
    Streamlit의 최상단 루트 요소부터 채팅창 내부 및 위젯까지 
    모든 레이어의 스타일을 강제 적용합니다.
    """
    if theme == "Dark":
        bg_col, side_col, card_col = "#0D1117", "#0D1117", "#161B22"
        txt_col, sub_txt_col, border_col = "#FFFFFF", "#8B949E", "#30363D"
        widget_bg, chat_bg = "#21262D", "#161B22"
        icon_filter = "none"
    else:
        # 라이트 모드 설정
        bg_col, side_col, card_col = "#FFFFFF", "#F6F8FA", "#F6F8FA"
        txt_col, sub_txt_col, border_col = "#1A1C24", "#57606A", "#D0D7DE"
        widget_bg, chat_bg = "#FFFFFF", "#FFFFFF"
        icon_filter = "invert(0.8)"

    st.markdown(f"""
        <style>
        /* 1. 최상단 루트 컨테이너 및 배경 (위아래 검은 영역 해결) */
        [data-testid="stAppViewContainer"], .stApp, .stAppViewMainContainer, section.main, section.main > div:first-child {{
            background-color: {bg_col} !important;
        }}
        
        /* 헤더 및 푸터 투명화 */
        header, [data-testid="stHeader"], [data-testid="stFooterVisualizer"] {{
            background-color: rgba(0,0,0,0) !important;
            color: {txt_col} !important;
        }}

        /* 메인 콘텐츠 영역 여백 조정 */
        .main .block-container {{
            background-color: {bg_col} !important;
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
        }}

        /* 2. 전역 텍스트 색상 */
        .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp li {{
            color: {txt_col} !important;
        }}

        /* 3. 사이드바 및 선택창(Selectbox) 스타일 강제 */
        [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
            background-color: {side_col} !important;
            border-right: 1px solid {border_col} !important;
        }}
        /* 선택창 박스 및 내부 텍스트 */
        div[data-baseweb="select"] > div {{
            background-color: {widget_bg} !important;
            color: {txt_col} !important;
            border: 1px solid {border_col} !important;
        }}
        div[data-baseweb="select"] * {{
            color: {txt_col} !important;
        }}

        /* 4. 채팅 메시지 (내부 요소까지 강제) */
        [data-testid="stChatMessage"] {{
            background-color: {chat_bg} !important;
            border: 1px solid {border_col} !important;
        }}
        [data-testid="stChatMessage"] * {{
            color: {txt_col} !important;
        }}

        /* 5. 채팅 입력창 (wrapper까지 완벽 덮기) */
        [data-testid="stChatInput"] {{
            background-color: {bg_col} !important;
            border-top: 1px solid {border_col} !important;
        }}
        [data-testid="stChatInput"] > div {{
            background-color: {bg_col} !important;
        }}
        [data-testid="stChatInput"] textarea {{
            background-color: {widget_bg} !important;
            color: {txt_col} !important;
            border: 1px solid {border_col} !important;
        }}

        /* 6. 대시보드 카드 스타일 */
        .farm-card {{
            background-color: {card_col} !important;
            border: 1px solid {border_col} !important;
            padding: 24px;
            margin-bottom: 20px;
        }}
        .card-label {{ color: {sub_txt_col} !important; font-size: 12px; font-weight: bold; }}
        .card-value {{ color: {txt_col} !important; font-size: 32px; font-weight: bold; }}

        /* 7. 아이콘 보정 */
        [data-testid="stIcon"], [data-testid="stAvatar"] svg {{
            filter: {icon_filter} !important;
        }}
        </style>
        """, unsafe_allow_html=True)