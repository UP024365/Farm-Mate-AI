import streamlit as st
import os
from dotenv import load_dotenv

# 1. 수정된 도구 임포트
from tools.weather_tool import get_chungju_weather, parse_weather
from tools.price_tool import get_crop_price
from tools.pest_tool import get_pest_info

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_classic.chains import RetrievalQA
except ImportError:
    st.error("필수 라이브러리가 없습니다.")
    st.stop()

load_dotenv()
st.set_page_config(page_title="Farm-Mate-AI", page_icon="🌱", layout="wide")

# --- 🎨 가독성 극대화 디자인 ---
st.markdown("""
    <style>
    /* 배경 흰색, 글자 검은색 강제 고정 */
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, h4, h5, h6, p, span, div { color: #212121 !important; }
    
    /* 카드 디자인: 하얀 배경과 대비되도록 연한 회색 테두리 */
    div[data-testid="stMetric"] {
        background-color: #F8F9FA !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 10px;
        padding: 10px;
    }
    /* 메트릭 글자색 보정 */
    div[data-testid="stMetricValue"] > div { color: #1B5E20 !important; }
    
    /* 사이드바 색상 */
    [data-testid="stSidebar"] { background-color: #F1F8E9 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. AI 초기화
@st.cache_resource
def init_qa_robot():
    db_path = "./chroma_db"
    if not os.path.exists(db_path): return None
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    return RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

qa_robot = init_qa_robot()

# --- 🛠️ 사이드바: 작물 선택 ---
with st.sidebar:
    st.title("🌱 Farm-Mate")
    selected_crop = st.selectbox(
        "오늘의 분석 작물",
        ["사과", "배추", "무", "양파", "마늘", "고추", "감자", "대파", "상추", "오이"]
    )
    st.divider()
    st.info(f"현재 {selected_crop} 모드입니다.")

# --- 🏠 메인 화면 ---
st.title(f"👨‍🌾 {selected_crop} 맞춤형 농사 정보")

# 실시간 데이터 로딩
weather = parse_weather(get_chungju_weather())
price = get_crop_price(selected_crop) # 선택한 작물 전달
pest = get_pest_info()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🌤️ 충주 날씨")
    if "error" not in weather:
        st.metric("현재 온도", weather.get('temperature'))
        st.write(f"상태: **{weather.get('sky')}**")
    else:
        st.error("날씨 로드 실패")

with col2:
    st.subheader(f"💰 {selected_crop} 시세")
    st.metric(price['item_name'], price['price'], delta=f"{price['direction']} {price['value']}원")
    st.caption(f"단위: {price['unit']} | {price['status']}")

with col3:
    st.subheader("🐛 병해충 주의보")
    found = False
    if isinstance(pest, dict) and "data" in pest:
        for p in pest['data']:
            if selected_crop in p['name'] or selected_crop == "사과":
                st.warning(f"**{p['name']}**")
                found = True
    if not found:
        st.success("✅ 특이사항 없음")

st.divider()

# --- 🤖 AI 상담소 ---
st.subheader(f"🤖 {selected_crop} 전문 상담")
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role): st.markdown(msg.content)

if prompt := st.chat_input(f"{selected_crop}에 대해 궁금한 점을 물어보세요."):
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        if qa_robot:
            with st.spinner("문서 분석 중..."):
                res = qa_robot.invoke({"query": f"{selected_crop} 재배 관련: {prompt}"})
                st.markdown(res["result"])
                st.session_state.messages.append(AIMessage(content=res["result"]))