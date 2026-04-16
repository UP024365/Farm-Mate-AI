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
    from langchain_community.vectorstores import Chroma
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_classic.chains import RetrievalQA
except ImportError:
    st.error("필수 라이브러리가 없습니다. 'requirements.txt'를 확인하여 패키지를 설치해주세요.")
    st.stop()

load_dotenv()

# --- 지역 데이터 정의 ---
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

# --- [강화된 로직] 구글 드라이브 데이터 동기화 함수 ---
@st.cache_resource
def load_vector_db_safely():
    """
    로컬에 폴더가 있으면 다운로드 로직을 아예 실행하지 않습니다.
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(BASE_DIR, "chroma_db")

    # 1. 로컬에 이미 폴더가 존재하는지 최우선 확인
    if os.path.exists(db_path):
        # 폴더 내부에 파일이 하나라도 있는지 확인 (비어있는 폴더 방지)
        if len(os.listdir(db_path)) > 0:
            return True

    # 2. 서버(Streamlit Cloud) 환경에서만 작동할 다운로드 로직
    file_id = '16jCvj7bhMmb1Ai29IiX9zCs+H6H_HSyT'
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    zip_path = os.path.join(BASE_DIR, "chroma_db.zip")

    with st.spinner("서버에 데이터베이스가 없어 동기화를 시도합니다..."):
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
            st.error(f"데이터 로드 실패: 로컬 chroma_db 폴더를 확인해주세요. ({e})")
            return False

# 로드 실행
load_vector_db_safely()

# --- [수정] API 키 참조 오류 방지 ---
@st.cache_resource
def init_qa_robot():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(BASE_DIR, "chroma_db")
    
    if not os.path.exists(db_path):
        st.error("데이터베이스 폴더(chroma_db)를 찾을 수 없습니다.")
        return None, None
        
    try:
        # OpenAI API 키 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # 로컬 .env에 없으면 st.secrets 확인
            api_key = st.secrets.get("OPENAI_API_KEY")

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
        vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0, streaming=True, openai_api_key=api_key)
        return vector_db, llm
    except Exception as e:
        st.error(f"로봇 초기화 실패: {e}")
        return None, None

vector_db, llm = init_qa_robot()

# --- 사이드바 및 설정 ---
with st.sidebar:
    st.title("🌱 Farm-Mate")
    
    st.header("📍 지역 설정")
    selected_location = st.selectbox(
        "날씨를 확인할 지역을 선택하세요",
        options=list(LOCATIONS.keys()),
        index=0
    )
    target_coords = LOCATIONS[selected_location]
    
    st.divider()

    def reset_chat():
        st.session_state.messages = []

    crop_name_map = {
        "사과": "apple", "마늘": "garlic", "양파": "onion", 
        "복숭아": "peach", "고추": "pepper", "감자": "potato", 
        "무": "radish", "딸기": "strawberry", "고구마": "sweet_potato", 
        "토마토": "tomato"
    }

    selected_crop_ko = st.selectbox(
        "오늘의 분석 작물",
        list(crop_name_map.keys()),
        on_change=reset_chat
    )
    
    selected_crop_en = crop_name_map[selected_crop_ko]
    st.info(f"현재 **{selected_crop_ko}** 분석 모드입니다.")

# --- 실시간 데이터 로딩 ---
weather = get_weather_info(nx=target_coords['nx'], ny=target_coords['ny'])
price = get_crop_price(selected_crop_ko)
pest = get_pest_info() 
tech = get_crop_tech_info(selected_crop_ko) 
weekly = get_weekly_farming_info() 

st.title(f"👨‍🌾 {selected_crop_ko} 실시간 영농 리포트")

# --- 섹션 1: 대시보드 ---
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader(f"🌤️ {selected_location} 날씨")
    if weather:
        st.metric("현재 온도", f"{weather.get('temp')}°C")
        st.write(f"상태: **{weather.get('sky')}**")
        st.caption(f"습도: {weather.get('humidity')}% | 강수: {weather.get('rain')}")
    else:
        st.write("날씨 정보를 불러올 수 없습니다.")

with col2:
    st.subheader(f"💰 {selected_crop_ko} 시세")
    if price:
        st.metric(price['item_name'], price['price'], delta=f"{price['direction']} {price['value']}원")
        if price.get('recommendation'):
            st.info(price['recommendation'])

with col3:
    st.subheader("🐛 병해충 특보")
    if isinstance(pest, dict) and "data" in pest:
        crop_pests = [p for p in pest['data'] if selected_crop_ko in p['name']]
        if crop_pests:
            for p in crop_pests:
                st.error(f"⚠️ {p['name']}")
        else:
            st.info(f"✅ {selected_crop_ko} 관련 특보 없음")
            st.caption("전국 주요 특보:")
            for p in pest['data'][:2]:
                st.write(f"🚩 {p['name']}")

st.divider()

# --- 섹션 2: 전문 지침 ---
col_a, col_b = st.columns(2)
with col_a:
    st.subheader(f"📖 {selected_crop_ko} 재배 기술")
    if isinstance(tech, dict) and "data" in tech:
        for t in tech['data']:
            st.write(f"- {t['title']} ({t['date']})")

with col_b:
    st.subheader("🗓️ 주간 영농 지침")
    if isinstance(weekly, dict) and "data" in weekly:
        for w in weekly['data'][:3]:
            st.info(f"📍 {w['subject']}")

st.divider()

# --- 섹션 3: AI 상담소 (RAG) ---
st.subheader(f"🤖 {selected_crop_ko} 지능형 상담")
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role): st.markdown(msg.content)

if prompt := st.chat_input(f"{selected_crop_ko}에 대해 궁금한 점을 물어보세요."):
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        if vector_db and llm:
            message_placeholder = st.empty()
            with st.spinner("전문 데이터를 분석 중입니다..."):
                pest_summary = ", ".join([p['name'] for p in pest.get('data', [])]) if isinstance(pest, dict) and "data" in pest else "특이사항 없음"
                weekly_summary = ", ".join([w['subject'] for w in weekly.get('data', [])[:2]]) if isinstance(weekly, dict) and "data" in weekly else "정보 없음"
                
                weather_context = f"""
                [현재 실시간 정보]
                - 위치: {selected_location}
                - 날씨: {weather.get('temp')}°C / {weather.get('sky')}
                - 기상흐름: {weather.get('weather_timeline')}
                - 병해충: {pest_summary}
                - 주간지침: {weekly_summary}
                """
                
                search_kwargs = {"k": 3, "filter": {"crop": selected_crop_en}}
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm, 
                    chain_type="stuff",
                    retriever=vector_db.as_retriever(search_kwargs=search_kwargs),
                    return_source_documents=True
                )
                
                system_instruction = f"""
                너는 농업 전문가 'Farm-Mate' AI야. 
                제공된 [실시간 정보]와 [재배 지침서]를 바탕으로 '{selected_crop_ko}' 재배에 대해 구체적으로 답변해줘.
                필요하다면 현재 지역({selected_location})의 날씨나 시세를 고려한 행동 지침을 강력하게 추천해줘.
                """
                
                final_query = f"{system_instruction}\n\n{weather_context}\n\n질문: {prompt}"
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
                    with st.expander("📍 답변의 근거 문서"):
                        for doc in res["source_documents"]:
                            st.write(f"- {os.path.basename(doc.metadata.get('source', '지침서'))}")
            
            st.session_state.messages.append(AIMessage(content=full_response))
        else:
            st.error("AI 상담 시스템이 준비되지 않았습니다. DB 구성을 확인해주세요.")