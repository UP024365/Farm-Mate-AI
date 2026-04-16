import streamlit as st
import os
import time
import zipfile
import requests
from datetime import datetime
from dotenv import load_dotenv

# 1. 도구 임포트
from tools.weather_tool import get_weather_info 
from tools.price_tool import get_crop_price
from tools.pest_tool import get_pest_info
from tools.tech_tool import get_crop_tech_info
from tools.weekly_tool import get_weekly_farming_info

# 라이브러리 체크
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_chroma import Chroma  # 최신 버전 반영
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_classic.chains import RetrievalQA
except ImportError:
    st.error("필수 라이브러리가 없습니다. 'requirements.txt'를 확인해주세요.")
    st.stop()

load_dotenv()

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="Farm-Mate-AI", page_icon="🌱", layout="wide")

# --- 커스텀 CSS (심플 & 각진 디자인) ---
st.markdown("""
    <style>
    /* 전체 배경 및 폰트 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    
    html, body, [data-testid="stsidebar"] {
        font-family: 'Inter', sans-serif;
    }

    /* 각진 카드 컨테이너 */
    .farm-card {
        background-color: #1a1c24;
        border: 1px solid #30363d;
        border-radius: 0px; /* 각지게 설정 */
        padding: 24px;
        margin-bottom: 20px;
        height: 100%;
    }

    /* 카드 타이틀 (작고 연한 회색) */
    .card-label {
        color: #8b949e;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    /* 카드 메인 수치 (크고 하얀색) */
    .card-value {
        color: #ffffff;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    /* 카드 하단 보조 텍스트 */
    .card-sub {
        color: #58a6ff;
        font-size: 14px;
    }

    /* 구분선 스타일 */
    hr {
        border: 0;
        border-top: 1px solid #30363d;
        margin: 30px 0;
    }

    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [로직] 데이터 로드 및 초기화 ---
@st.cache_resource
def load_vector_db_safely():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(BASE_DIR, "chroma_db")
    if os.path.exists(db_path) and len(os.listdir(db_path)) > 0:
        return True
    
    file_id = '16jCvj7bhMmb1Ai29IiX9zCs+H6H_HSyT'
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    zip_path = os.path.join(BASE_DIR, "chroma_db.zip")

    with st.spinner("데이터베이스 동기화 중..."):
        try:
            response = requests.get(url, stream=True, timeout=30)
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(BASE_DIR)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return True
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            return False

load_vector_db_safely()

@st.cache_resource
def init_qa_robot():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(BASE_DIR, "chroma_db")
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    
    if not os.path.exists(db_path): return None, None
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
    vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0, streaming=True, openai_api_key=api_key)
    return vector_db, llm

vector_db, llm = init_qa_robot()

# --- 사이드바 설정 ---
LOCATIONS = {
    "충청북도 충주시": {"nx": 76, "ny": 114},
    "충청북도 청주시": {"nx": 69, "ny": 107},
    "서울특별시": {"nx": 60, "ny": 127},
    "경기도 수원시": {"nx": 60, "ny": 121},
    "강원도 춘천시": {"nx": 73, "ny": 134},
    "경상북도 안동시": {"nx": 91, "ny": 106},
    "전라남도 나주시": {"nx": 56, "ny": 71},
    "제주특별자치도": {"nx": 52, "ny": 38}
}

with st.sidebar:
    st.title("🌱 Farm-Mate")
    selected_location = st.selectbox("LOCATION", options=list(LOCATIONS.keys()))
    target_coords = LOCATIONS[selected_location]
    
    st.divider()

    crop_name_map = {
        "사과": "apple", "마늘": "garlic", "양파": "onion", "복숭아": "peach", 
        "고추": "pepper", "감자": "potato", "무": "radish", "딸기": "strawberry", 
        "고구마": "sweet_potato", "토마토": "tomato"
    }
    selected_crop_ko = st.selectbox("TARGET CROP", list(crop_name_map.keys()))
    selected_crop_en = crop_name_map[selected_crop_ko]

# --- 실시간 데이터 처리 ---
weather = get_weather_info(nx=target_coords['nx'], ny=target_coords['ny'])
price = get_crop_price(selected_crop_ko)
pest = get_pest_info()
tech = get_crop_tech_info(selected_crop_ko)
weekly = get_weekly_farming_info()

# --- 섹션 1: 대시보드 (상세 로직 포함) ---
st.markdown(f"### 👨‍🌾 {selected_crop_ko} 영농 통합 대시보드")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {selected_location}")

col1, col2, col3 = st.columns(3)

# 1. 날씨 카드 (기존 유지)
with col1:
    st.markdown(f"""
        <div class="farm-card">
            <div class="card-label">Real-time Weather</div>
            <div class="card-value">{weather.get('temp', 'N/A')}°C</div>
            <div class="card-sub">{weather.get('sky', '정보없음')} | 습도 {weather.get('humidity', '0')}%</div>
        </div>
    """, unsafe_allow_html=True)

# 2. 가격 카드 (종윤 님이 말씀하신 추천 로직 반영)
with col2:
    if price:
        # 시세 추천 로직 (price_tool이나 main에서 계산된 recommendation 변수 활용)
        # 만약 price 데이터 안에 recommendation 문구가 들어있다면 그대로 출력합니다.
        rec_text = price.get('recommendation', '시세 정보를 분석 중입니다...')
        
        delta_color = "#ff7b72" if "상승" in price.get('direction', '') else "#58a6ff"
        
        st.markdown(f"""
            <div class="farm-card">
                <div class="card-label">{selected_crop_ko} Market Price</div>
                <div class="card-value">{price['price']}원</div>
                <div style="color:{delta_color}; font-size:14px; margin-bottom:10px;">
                    {price.get('direction')} {price.get('value')}원
                </div>
                <div style="color:#d1d5da; font-size:13px; line-height:1.4; border-top:1px solid #30363d; pt-10;">
                    {rec_text}
                </div>
            </div>
        """, unsafe_allow_html=True)

# 3. 병해충 카드 (상세 리스트 로직 반영)
with col3:
    # 해당 작물 특보 필터링
    crop_pests = [p for p in pest['data'] if selected_crop_ko in p['name']] if isinstance(pest, dict) and "data" in pest else []
    
    status_text = "위험" if crop_pests else "양호"
    status_color = "#ff7b72" if crop_pests else "#3fb950"
    
    # 카드 상단 요약
    st.markdown(f"""
        <div class="farm-card">
            <div class="card-label">Pest & Disease Status</div>
            <div class="card-value" style="color:{status_color};">{status_text}</div>
            <div id="pest-list" style="margin-top:10px; border-top:1px solid #30363d; padding-top:10px;">
    """, unsafe_allow_html=True)
    
    # 카드 내부 상세 리스트 로직
    if crop_pests:
        for p in crop_pests:
            st.markdown(f"<div style='color:#ff7b72; font-size:13px;'>⚠️ {p['name']} 발령 중</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='color:#8b949e; font-size:13px;'>✅ {selected_crop_ko} 관련 특보 없음</div>", unsafe_allow_html=True)
        # 전국 주요 특보 1~2개 추가 노출 (말씀하신 전국 정보 띄우기)
        if isinstance(pest, dict) and "data" in pest:
            st.markdown("<div style='color:#8b949e; font-size:12px; margin-top:5px; border-top:1px dashed #30363d;'>전국 주요:</div>", unsafe_allow_html=True)
            for p in pest['data'][:2]:
                st.markdown(f"<div style='color:#d1d5da; font-size:12px;'>🚩 {p['name']}</div>", unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
# 섹션 2: 기술 정보 및 지침
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="farm-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">Agricultural Technology</div>', unsafe_allow_html=True)
    if isinstance(tech, dict) and "data" in tech:
        for t in tech['data'][:4]:
            st.markdown(f"**·** {t['title']} <span style='color:#8b949e; font-size:12px;'>({t['date']})</span>", unsafe_allow_html=True)
    else:
        st.write("데이터를 찾을 수 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="farm-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">Weekly Farming Guide</div>', unsafe_allow_html=True)
    if isinstance(weekly, dict) and "data" in weekly:
        for w in weekly['data'][:3]:
            st.info(f"📍 {w['subject']}")
    else:
        st.write("지침 정보를 불러올 수 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# 섹션 3: AI 상담소
st.markdown(f"#### 🤖 {selected_crop_ko} 지능형 상담 센터")
if "messages" not in st.session_state: st.session_state.messages = []

# 채팅창을 카드 스타일로 감싸기 위해 컨테이너 사용
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role): st.markdown(msg.content)

if prompt := st.chat_input(f"{selected_crop_ko} 재배에 대해 무엇이든 물어보세요."):
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        if vector_db and llm:
            message_placeholder = st.empty()
            with st.spinner("AI 전문가가 데이터를 분석 중입니다..."):
                pest_summary = ", ".join([p['name'] for p in pest.get('data', [])]) if isinstance(pest, dict) and "data" in pest else "특이사항 없음"
                weather_context = f"""
                [현재 정보] 위치:{selected_location}, 날씨:{weather.get('temp')}도, 병해충:{pest_summary}
                """
                
                search_kwargs = {"k": 3, "filter": {"crop": selected_crop_en}}
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm, chain_type="stuff",
                    retriever=vector_db.as_retriever(search_kwargs=search_kwargs),
                    return_source_documents=True
                )
                
                final_query = f"너는 농업 전문가야. {weather_context}를 참고해서 답변해. 질문: {prompt}"
                res = qa_chain.invoke({"query": final_query})
                full_response = res["result"]
                
                # 타이핑 효과
                temp_text = ""
                for char in full_response:
                    temp_text += char
                    message_placeholder.markdown(temp_text + "▌")
                    time.sleep(0.005)
                message_placeholder.markdown(full_response)
                
                if res.get("source_documents"):
                    with st.expander("📍 답변의 근거 확인"):
                        for doc in res["source_documents"]:
                            st.write(f"- {os.path.basename(doc.metadata.get('source', '지침서'))}")
            
            st.session_state.messages.append(AIMessage(content=full_response))