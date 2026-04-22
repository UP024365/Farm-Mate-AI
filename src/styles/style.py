import streamlit as st

def apply_custom_style(theme="Dark"):
    """
    선택된 테마에 따라 CSS 스타일을 동적으로 생성하고 적용합니다.
    """
    # --- 테마별 색상 변수 정의 ---
    if theme == "Dark":
        bg_col, side_col, card_col = "#0D1117", "#0D1117", "#161B22"
        txt_col, sub_txt_col, border_col = "#FFFFFF", "#8B949E", "#30363D"
        widget_bg = "#21262D"  # 선택창 내부 배경
        icon_filter = "none"
    else:
        bg_col, side_col, card_col = "#FFFFFF", "#F6F8FA", "#F6F8FA"
        txt_col, sub_txt_col, border_col = "#1A1C24", "#57606A", "#D0D7DE"
        widget_bg = "#FFFFFF"  # 선택창 내부 배경
        icon_filter = "invert(0.8)"

    # --- 커스텀 CSS 적용 ---
    st.markdown(f"""
        <style>
        /* 전체 앱 배경 및 상단 헤더 영역 */
        .stApp, header, [data-testid="stHeader"] {{
            background-color: {bg_col} !important;
        }}

        /* 텍스트 색상 강제 */
        .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp li {{
            color: {txt_col} !important;
        }}

        /* 사이드바 스타일 */
        [data-testid="stSidebar"], [data-testid="stSidebar"] div, [data-testid="stSidebar"] p {{
            background-color: {side_col} !important;
            color: {txt_col} !important;
        }}

        /* Selectbox(선택창) 스타일 */
        div[data-baseweb="select"] > div {{
            background-color: {widget_bg} !important;
            color: {txt_col} !important;
            border: 1px solid {border_col} !important;
        }}
        div[data-baseweb="popover"] li {{
            background-color: {widget_bg} !important;
            color: {txt_col} !important;
        }}

        /* 대시보드 카드 컨테이너 */
        .farm-card {{
            background-color: {card_col} !important;
            border: 1px solid {border_col} !important;
            border-radius: 0px !important;
            padding: 24px;
            margin-bottom: 20px;
        }}
        .card-label {{ color: {sub_txt_col} !important; font-size: 12px; font-weight: bold; }}
        .card-value {{ color: {txt_col} !important; font-size: 32px; font-weight: bold; }}

        /* 채팅 입력창 (stChatInput) */
        [data-testid="stChatInput"] {{
            background-color: transparent !important;
        }}
        [data-testid="stChatInput"] textarea {{
            background-color: {card_col} !important;
            color: {txt_col} !important;
            border: 1px solid {border_col} !important;
        }}

        /* 채팅 메시지 박스 */
        [data-testid="stChatMessage"] {{
            background-color: {card_col} !important;
            border: 1px solid {border_col} !important;
            border-radius: 0px !important;
        }}

        /* 아이콘 시인성 보정 */
        [data-testid="stIcon"], [data-testid="stAvatar"] svg {{
            filter: {icon_filter} !important;
        }}

        /* 구분선 */
        hr {{ border-top: 1px solid {border_col} !important; }}
        </style>
        """, unsafe_allow_html=True)