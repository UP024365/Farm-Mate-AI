import streamlit as st
import os
import time
from dotenv import load_dotenv

# 1. 도구 임포트 (새로 추가된 도구 포함)
from tools.weather_tool import get_chungju_weather, parse_weather
from tools.price_tool import get_crop_price
from tools.pest_tool import get_pest_info
from tools.tech_tool import get_crop_tech_info      # 👈 추가
from tools.weekly_tool import get_weekly_farming_info # 👈 추가

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

# 2. AI 초기화 (메타데이터 필터링 적용 버전)
@st.cache_resource
def init_qa_robot():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(BASE_DIR, "chroma_db")
    if not os.path.exists(db_path): return None
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0, streaming=True)
    return vector_db, llm

vector_db, llm = init_qa_robot()

# --- 🛠️ 사이드바 수정 (작물 변경 시 대화 리셋 기능 추가) ---
with st.sidebar:
    st.title("🌱 Farm-Mate")
    
    # 작물을 선택할 때마다 이전 대화 기록을 지우는 함수
    def reset_chat():
        st.session_state.messages = []

    selected_crop = st.selectbox(
        "오늘의 분석 작물",
        ["사과", "배추", "고추", "마늘", "감자", "오이", "복숭아", "딸기", "고구마", "토마토"],
        on_change=reset_chat  # 👈 작물이 바뀌면 대화 내역을 초기화합니다!
    )
    st.divider()
    st.info(f"현재 **{selected_crop}** 분석 모드입니다.")
# --- 🏠 메인 화면 ---
st.title(f"👨‍🌾 {selected_crop} 실시간 영농 리포트")

# 실시간 데이터 병렬 로딩
weather = parse_weather(get_chungju_weather())
price = get_crop_price(selected_crop)
pest = get_pest_info()
tech = get_crop_tech_info(selected_crop)    # 👈 추가
weekly = get_weekly_farming_info()          # 👈 추가

# [섹션 1] 핵심 지표 대시보드
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("🌤️ 충주 날씨")
    if "error" not in weather:
        st.metric("현재 온도", weather.get('temperature'))
        st.write(f"상태: **{weather.get('sky')}**")
with col2:
    st.subheader(f"💰 {selected_crop} 시세 및 추천")
    st.metric(price['item_name'], price['price'], delta=f"{price['direction']} {price['value']}원")
    
    # 👈 추천 메시지 추가
    if price.get('recommendation'):
        st.info(price['recommendation'])
        if price.get('analysis'):
            st.caption(price['analysis'])
    
    st.caption(f"단위: {price['unit']} | {price['status']}")
with col3:
    st.subheader("🐛 병해충 실시간 현황")
    if isinstance(pest, dict) and "data" in pest:
        # 필터링 없이 일단 싹 다 보여줘서 데이터가 오는지 확인
        for p in pest['data']:
            st.write(f"🚩 {p['name']}") # 어떤 글자들이 오는지 눈으로 확인!
            
        # 원래 로직
        found = any(selected_crop in p['name'] for p in pest['data'])
        if not found:
            st.info("선택 작물 관련 특보 없음")
    else:
        st.success("✅ 현재 전국 병해충 특이사항 없음")

st.divider()

# [섹션 2] 📖 농사로 실시간 전문 정보 (새로 추가된 영역)
col_a, col_b = st.columns(2)
with col_a:
    st.subheader(f"📖 {selected_crop} 최신 재배 기술")
    if "data" in tech:
        for t in tech['data']:
            st.write(f"- {t['title']} ({t['date']})")
    else:
        st.write(tech.get("status", "정보를 불러올 수 없습니다."))

with col_b:
    st.subheader("🗓️ 주간 영농 지침")
    if "data" in weekly:
        for w in weekly['data'][:3]: # 상위 3개만 표시
            st.info(f"📍 {w['subject']}")
    else:
        st.write(weekly.get("status", "정보를 불러올 수 없습니다."))

st.divider()

# [섹션 3] 🤖 AI 상담소 (날씨 기반 지능형 의사결정 강화)
st.subheader(f"🤖 {selected_crop} 지능형 상담")
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role): st.markdown(msg.content)

if prompt := st.chat_input(f"{selected_crop}에 대해 무엇이든 물어보세요."):
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        if vector_db and llm:
            message_placeholder = st.empty()
            full_response = ""
            
            with st.spinner("전문 문서와 현재 날씨를 분석 중입니다..."):
                search_kwargs = {"k": 3, "filter": {"crop": selected_crop}}
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm, chain_type="stuff",
                    retriever=vector_db.as_retriever(search_kwargs=search_kwargs),
                    return_source_documents=True
                )
                
                # ✅ 날씨 전체 정보를 문장으로 구성하여 AI에게 전달
                # src/main.py 내부 수정 부분
                weather_context = f"""
                [현재 실시간 정보]
                - 온도: {weather.get('temperature')}
                - 하늘상태: {weather.get('sky')}
                - 향후 기상 흐름: {weather.get('weather_timeline')}
                - 강수형태: {weather.get('rain_type')}
                - 현재 강수확률: {weather.get('pop')}
                - 향후 12시간 내 최대 강수확률: {weather.get('max_pop')}  # 👈 이 데이터가 핵심!
                - 현재 시세: {price['price']}
                """
                
                # ✅ AI에게 "전문가로서 판단을 내려라"라고 강하게 지시
                system_instruction = f"""
                너는 30년 경력의 베테랑 농업 전문가이자, 농민의 수익을 최우선으로 생각하는 'Farm-Mate'의 AI 컨설턴트야.
                제공된 [현재 실시간 정보]와 [전문 재배 지침서]를 결합하여 답변해줘.

                답변할 때 아래의 **'필수 원칙'**을 반드시 지켜야 해:

                1. **결단력 있는 태도:** "판단하기 어렵다"거나 "전문가와 상의하라"는 회피성 답변은 절대 금지야. 부족한 정보 속에서도 현재 날씨와 시세를 근거로 '지금 하세요' 또는 '미루세요'라고 명확한 '행동 지침'을 내려줘.
                2. **날씨 데이터 기반 논리:** - 기온이 10°C 미만이면 "뿌리의 흡수력이 낮으니 비료를 미루라"고 해.
                - 강수확률(max_pop)이 60% 이상이면 "비료가 씻겨 내려갈 수 있으니 주의"하거나, "적절한 비 소식이라면 지금이 비료 주기의 골든타임"이라고 판단해줘.
                3. **시세 연동 전략:** 현재 시세 추천이 [판매 추천]이라면 "지금은 재배보다 수확과 출하에 집중할 시기"라고 조언해주고, [관망 추천]이라면 "품질을 높이기 위한 관리에 집중하자"고 말해줘.
                4. **전문성 유지:** 답변 중간에 "농학적으로 봤을 때~" 혹은 "지침서에 따르면~"과 같은 문구를 섞어서 신뢰도를 높여줘.
                """
                
                final_query = f"{system_instruction}\n\n{weather_context}\n\n사용자 질문: {prompt}"
                
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
                    with st.expander("📍 근거 문서"):
                        for doc in res["source_documents"]:
                            st.write(f"- {os.path.basename(doc.metadata.get('source', '알 수 없음'))}")
            st.session_state.messages.append(AIMessage(content=full_response))