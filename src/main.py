import streamlit as st
import os
import time
import gdown
import zipfile
from dotenv import load_dotenv

# 1. 도구 임포트
# weather_tool에서 새로운 로직의 함수를 가져옵니다.
from tools.weather_tool import get_weather_info 
from tools.price_tool import get_crop_price
from tools.pest_tool import get_pest_info
from tools.tech_tool import get_crop_tech_info
from tools.weekly_tool import get_weekly_farming_info

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_classic.chains import RetrievalQA
except ImportError:
    st.error("필수 라이브러리가 없습니다. 'requirements.txt'를 확인하여 패키지를 설치해주세요.")
    st.stop()

load_dotenv()

# --- 지역 데이터 정의 (기상청 nx, ny 좌표) ---
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

# --- 구글 드라이브 데이터 로드 함수 ---
def load_vector_db_from_drive():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(BASE_DIR, "chroma_db")
    zip_path = os.path.join(BASE_DIR, "chroma_db.zip")
    
    file_id = '16jCvj7bhMmb1Ai29IiX9zCsxH6H_HSyT'
    url = f'https://drive.google.com/uc?id={file_id}'

    if not os.path.exists(db_path):
        with st.spinner("구글 드라이브에서 농업 지식 데이터베이스를 불러오는 중입니다..."):
            try:
                gdown.download(url, zip_path, quiet=False)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(BASE_DIR)
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                st.success("데이터베이스 로드 성공!")
            except Exception as e:
                st.error(f"데이터 로드 실패: {e}")

# 앱 시작 시 최우선 실행
load_vector_db_from_drive()

st.set_page_config(page_title="Farm-Mate-AI", page_icon="🌱", layout="wide")

# 2. 벡터 DB 및 LLM 초기화 (캐싱 적용)
@st.cache_resource
def init_qa_robot():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(BASE_DIR, "chroma_db")
    
    if not os.path.exists(db_path):
        return None, None
        
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0, streaming=True)
    return vector_db, llm

vector_db, llm = init_qa_robot()

# --- 사이드바 및 설정 ---
with st.sidebar:
    st.title("🌱 Farm-Mate")
    
    # 지역 선택 기능 추가
    st.header("📍 지역 설정")
    selected_location = st.selectbox(
        "날씨를 확인할 지역을 선택하세요",
        options=list(LOCATIONS.keys()),
        index=0  # 기본값: 충청북도 충주시
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
# 선택된 지역의 좌표를 weather_tool에 전달합니다.
weather = get_weather_info(nx=target_coords['nx'], ny=target_coords['ny'])
price = get_crop_price(selected_crop_ko)
pest = get_pest_info() 
tech = get_crop_tech_info(selected_crop_ko) 
weekly = get_weekly_farming_info() 

st.title(f"👨‍🌾 {selected_crop_ko} 실시간 영농 리포트")

# --- 섹션 1: 대시보드 (날씨, 시세, 특보) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader(f"🌤️ {selected_location} 날씨")
    if weather:
        st.metric("현재 온도", f"{weather.get('temp')}°C")
        st.write(f"습도: **{weather.get('humidity')}%**")
        st.write(f"강수량: **{weather.get('rain')}**")
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
    else:
        st.success("✅ 전국 병해충 특이사항 없음")

st.divider()

# --- 섹션 2: 전문 기술 및 지침 ---
col_a, col_b = st.columns(2)
with col_a:
    st.subheader(f"📖 {selected_crop_ko} 재배 기술")
    if isinstance(tech, dict) and "data" in tech:
        for t in tech['data']:
            st.write(f"- {t['title']} ({t['date']})")
    else:
        st.write("최신 기술 정보를 찾을 수 없습니다.")

with col_b:
    st.subheader("🗓️ 주간 영농 지침")
    if isinstance(weekly, dict) and "data" in weekly:
        for w in weekly['data'][:3]:
            st.info(f"📍 {w['subject']}")
    else:
        st.write("주간 지침 정보를 불러올 수 없습니다.")

st.divider()

# --- 섹션 3: AI 상담소 (RAG 적용) ---
st.subheader(f"🤖 {selected_crop_ko} 지능형 상담")
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role): st.markdown(msg.content)

if prompt := st.chat_input(f"{selected_crop_ko}에 대해 물어보세요."):
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        if vector_db and llm:
            message_placeholder = st.empty()
            with st.spinner("전문 데이터를 분석 중입니다..."):
                pest_summary = ", ".join([p['name'] for p in pest.get('data', [])]) if isinstance(pest, dict) and "data" in pest else "특이사항 없음"
                weekly_summary = ", ".join([w['subject'] for w in weekly.get('data', [])[:2]]) if isinstance(weekly, dict) and "data" in weekly else "정보 없음"
                tech_summary = ", ".join([t['title'] for t in tech.get('data', [])[:2]]) if isinstance(tech, dict) and "data" in tech else "정보 없음"

                weather_context = f"""
                [현재 실시간 정보]
                - 위치: {selected_location}
                - 현재 온도: {weather.get('temp')}°C
                - 현재 습도: {weather.get('humidity')}%
                - 현재 시세: {price.get('price', '정보 없음')} ({price.get('status', '-')})
                - 병해충 특보: {pest_summary}
                - 주간 농사 지침: {weekly_summary}
                - 최신 기술 동향: {tech_summary}
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