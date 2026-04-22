import streamlit as st

def apply_custom_style():
    """
    스트림릿 시스템 테마를 감지하여 배경색 빈틈을 메우고, 
    채팅창 및 카드의 스타일과 색상 변수를 반환합니다.
    """
    # 1. 시스템 테마 감지 (다크/라이트)
    try:
        base_theme = st.get_option("theme.base")
    except:
        base_theme = "dark"

    if base_theme == "dark":
        bg_col, side_col, card_col = "#0D1117", "#0D1117", "#161B22"
        txt_col, sub_txt_col, border_col = "#FFFFFF", "#8B949E", "#30363D"
        widget_bg, chat_bg = "#21262D", "#161B22"
        icon_filter = "none"
    else:
        # 라이트 모드 (흰색 배경, 짙은 글자)
        bg_col, side_col, card_col = "#FFFFFF", "#F6F8FA", "#F6F8FA"
        txt_col, sub_txt_col, border_col = "#1A1C24", "#57606A", "#D0D7DE"
        widget_bg, chat_bg = "#FFFFFF", "#FFFFFF"
        icon_filter = "invert(0.8)"

    # 2. CSS 적용
    st.markdown(f"""
        <style>
        /* 최상단 루트 컨테이너 배경 (위아래 공백 해결) */
        [data-testid="stAppViewContainer"], 
        [data-testid="stAppViewMainContainer"],
        .stApp, header, section.main {{
            background-color: {bg_col} !important;
            color: {txt_col} !important;
        }}

        /* 전역 텍스트 색상 */
        .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp li, .stApp div {{
            color: {txt_col} !important;
        }}

        /* 사이드바 스타일 */
        [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
            background-color: {side_col} !important;
            border-right: 1px solid {border_col} !important;
        }}
        [data-testid="stSidebar"] * {{
            color: {txt_col} !important;
        }}

        /* 하단 채팅 입력창 (검은 배경 및 글씨 안 보임 해결) */
        [data-testid="stChatInput"] {{
            background-color: {bg_col} !important;
            border-top: 1px solid {border_col} !important;
            padding: 15px !important;
        }}
        [data-testid="stChatInput"] textarea {{
            background-color: {widget_bg} !important;
            color: {txt_col} !important; 
            border: 1px solid {border_col} !important;
            caret-color: {txt_col} !important;
        }}
        [data-testid="stChatInput"] button svg {{
            fill: {txt_col} !important;
        }}

        /* 대시보드 카드 스타일 (각진 디자인) */
        .farm-card {{
            background-color: {card_col} !important;
            border: 1px solid {border_col} !important;
            padding: 24px;
            margin-bottom: 20px;
            border-radius: 0px !important;
        }}
        .card-label {{ color: {sub_txt_col} !important; font-size: 12px; font-weight: bold; }}
        .card-value {{ color: {txt_col} !important; font-size: 32px; font-weight: bold; }}

        /* 아이콘 보정 */
        [data-testid="stIcon"], [data-testid="stAvatar"] svg {{
            filter: {icon_filter} !important;
        }}
        hr {{ border-top: 1px solid {border_col} !important; }}
        </style>
        """, unsafe_allow_html=True)

    # main.py에서 사용할 수 있도록 색상 변수 반환
    return txt_col, sub_txt_col, border_col, bg_col