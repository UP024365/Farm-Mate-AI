import streamlit as st
import os
import time
import zipfile
import requests
from datetime import datetime
from dotenv import load_dotenv

# 스타일 모듈 임포트
from styles.style import apply_custom_style

# 1. 도구 임포트
from tools.weather_tool import get_weather_info 
from tools.price_tool import get_crop_price
from tools.pest_tool import get_pest_info
from tools.pest_db import PEST_ALERTS
from tools.tech_tool import get_crop_tech_info
from tools.weekly_tool import get_weekly_farming_info

# 라이브러리 체크
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_classic.chains import RetrievalQA
except ImportError:
    st.error("필수 라이브러리가 없습니다. 'requirements.txt'를 확인해주세요.")
    st.stop()

load_dotenv()

# --- 1. 페이지 기본 설정 ---
st.set_page_config(page_title="Farm-Mate-AI", page_icon="🌱", layout="wide")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. 사이드바 설정 ---
with st.sidebar:
    st.title("🌱 Farm-Mate")
    
    # 위치 선택
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
    selected_location = st.selectbox("LOCATION", options=list(LOCATIONS.keys()))
    target_coords = LOCATIONS[selected_location]
    
    st.divider()

    # 작물 선택
    crop_name_map = {
        "사과": "apple", "마늘": "garlic", "양파": "onion", "복숭아": "peach", 
        "고추": "pepper", "감자": "potato", "무": "radish", "딸기": "strawberry", 
        "고구마": "sweet_potato", "토마토": "tomato"
    }
    selected_crop_ko = st.selectbox("TARGET CROP", list(crop_name_map.keys()))
    selected_crop_en = crop_name_map[selected_crop_ko]

# 🔥 [핵심 위치] 사이드바 설정이 모두 끝난 바깥에서 호출!
# 함수를 실행하면서 반환된 색상 변수들을 txt_col 등에 저장합니다.
txt_col, sub_txt_col, border_col, bg_col = apply_custom_style()

# --- 3. 데이터 로드 및 초기화 ---
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

load_vector_db_safely()
vector_db, llm = init_qa_robot()

# 실시간 데이터 수집
weather = get_weather_info(nx=target_coords['nx'], ny=target_coords['ny'])
price = get_crop_price(selected_crop_ko)
pest = get_pest_info()
tech = get_crop_tech_info(selected_crop_ko)
weekly = get_weekly_farming_info()

# --- 4. 섹션 1: 통합 대시보드 ---
st.markdown(f"### 👨‍🌾 {selected_crop_ko} 영농 통합 대시보드")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {selected_location}")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <div class="farm-card">
            <div class="card-label">Real-time Weather</div>
            <div class="card-value">{weather.get('temp', 'N/A')}°C</div>
            <div class="card-sub">{weather.get('sky', '정보없음')} | 습도 {weather.get('humidity', '0')}%</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    if price:
        rec_text = price.get('recommendation', '시세 정보를 분석 중입니다...')
        delta_color = "#ff7b72" if "상승" in price.get('direction', '') else "#58a6ff"
        st.markdown(f"""
            <div class="farm-card">
                <div class="card-label">{selected_crop_ko} Market Price</div>
                <div class="card-value">{price['price']}원</div>
                <div style="color:{delta_color}; font-size:14px; margin-bottom:10px;">
                    {price.get('direction')} {price.get('value')}원
                </div>
                <div style="color:#8b949e; font-size:13px; line-height:1.4; border-top:1px solid #30363d; padding-top:10px;">
                    {rec_text}
                </div>
            </div>
        """, unsafe_allow_html=True)

with col3:
    crop_pests = [p for p in pest['data'] if selected_crop_ko in p['name']] if isinstance(pest, dict) and "data" in pest else []
    
    # 상태에 따른 색상 및 문구 정의
    if crop_pests:
        status_text = "주의/위험"
        status_color = "#ff7b72"  # 빨간색
        sub_msg = f"관련 특보 {len(crop_pests)}건 발령 중"
    else:
        status_text = "양호"
        status_color = "#3fb950"  # 초록색
        sub_msg = "현재 관련 특보 없음"

    st.markdown(f"""
        <div class="farm-card">
            <div class="card-label">Overall Health Status</div>
            <div class="card-value" style="color:{status_color};">{status_text}</div>
            <div style='color: #8b949e; font-size: 14px; margin-top: 10px;'>{sub_msg}</div>
        </div>
    """, unsafe_allow_html=True)

# 섹션 2: 병해충 경보 및 실시간 영농 알람
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="farm-card"><div class="card-label">📡 병해충 발생 현황 및 분석</div>', unsafe_allow_html=True)
    
    # 1. Pest_db.py에서 현재 선택된 작물의 특보 가져오기
    if selected_crop_ko in PEST_ALERTS:
        alert = PEST_ALERTS[selected_crop_ko]
        
        # 강조된 알림창 출력
        st.error(f"🚨 **{selected_crop_ko} 특보: {alert['status']}**")
        st.markdown(f"""
            <div style="background-color: rgba(255, 123, 114, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #ff7b72;">
                <p style="margin-bottom: 5px;"><strong>⚠️ 주의 병해충:</strong> {', '.join(alert['items'])}</p>
                <p style="font-size: 14px;"><strong>💡 관리 요령:</strong> {alert['content']}</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 15px 0; border-top: 1px dashed #30363d;'>", unsafe_allow_html=True)

    # 2. 기존 전국 주요 발령 정보 (생략 가능하거나 아래로 배치)
    if isinstance(pest, dict) and "data" in pest:
        all_pests = pest['data']
        # 1. 우리 작물 관련 정보 필터링
        crop_pests = [p for p in all_pests if selected_crop_ko in p['name']]
        
        # 2. 전국 주요 발령 정보 드롭다운
        with st.expander(f"📍 전국 주요 발령 정보 ({len(all_pests)}건) 확인하기"):
            for p in all_pests:
                is_target = selected_crop_ko in p['name']
                
                # 우리 작물 관련 정보는 강조 스타일 적용
                bg_style = "background-color: rgba(255, 123, 114, 0.15);" if is_target else ""
                border_style = "border-left: 3px solid #ff7b72;" if is_target else "border-left: 1px solid #30363d;"
                
                st.markdown(f"""
                    <div style='{bg_style} {border_style} padding: 8px 12px; border-radius: 4px; margin-bottom: 5px;'>
                        <span style='font-size: 13px; color: {txt_col};'>{'⚠️ ' if is_target else '• '}{p['name']}</span>
                        <span style='font-size: 11px; color: #8b949e; float: right;'>{p.get('date', '')}</span>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<hr style='margin: 15px 0; border-top: 1px dashed #30363d;'>", unsafe_allow_html=True)

        # 3. 결론: 우리 작물 관련 요약 (이 부분은 항상 노출)
        st.markdown(f"**📢 {selected_crop_ko} 관련 분석 결과**")
        if crop_pests:
            st.error(f"🚨 주의: 현재 {selected_crop_ko} 관련 특보가 {len(crop_pests)}건 확인되었습니다. 하단 AI 상담센터에서 상세 대처법을 문의하세요.")
        else:
            st.success(f"✅ 안심: 현재 전국 특보 중 {selected_crop_ko}와 직접 관련된 정보는 없습니다.")
            
    else:
        st.write("데이터를 불러올 수 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="farm-card"><div class="card-label">🔔 영농 주의보 알람</div>', unsafe_allow_html=True)
    # 날씨 데이터(weather)를 기반으로 자동 알람 생성
    if weather:
        temp = float(weather.get('temp', 20))
        sky = weather.get('sky', '')
        
        alerts = []
        if temp >= 30: alerts.append("☀️ 고온 주의: 정오 시간대 야외 작업을 자제하고 관수에 유의하세요.")
        if temp <= 5: alerts.append("❄️ 저온 주의: 시설하우스 보온 관리에 신경 써주세요.")
        if "비" in sky or "소나기" in sky: alerts.append("☔ 강수 예보: 비료 살포를 미루고 배수로를 점검하세요.")
        if not alerts: alerts.append("🌿 현재 기상 조건이 안정적입니다. 계획된 농작업을 진행하세요.")
        
        for alert in alerts:
            st.info(alert)
    else:
        st.write("알람 정보를 생성할 수 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 섹션 3: AI 상담소 (업데이트된 통합 로직) ---
st.markdown(f"#### 🤖 {selected_crop_ko} 지능형 상담 센터")

# 1. 채팅 출력 컨테이너 (이전 대화 기록 표시)
chat_placeholder = st.container()
with chat_placeholder:
    for msg in st.session_state.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)

# 2. 채팅 입력창
prompt = st.chat_input(f"{selected_crop_ko} 재배에 대해 무엇이든 물어보세요.")

# 사용자가 직접 입력했을 경우 세션에 추가 후 화면 갱신
if prompt:
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.rerun()

# 3. 🔥 AI 답변 생성 시작 (실시간 데이터 컨텍스트 강화)
if st.session_state.messages and isinstance(st.session_state.messages[-1], HumanMessage):
    last_user_msg = st.session_state.messages[-1].content
    
    with st.chat_message("assistant"):
        if vector_db and llm:
            message_placeholder = st.empty()
            with st.spinner(f"AI 전문가가 {selected_crop_ko} 데이터를 정밀 분석 중입니다..."):
                
                # [실시간 정보 요약 생성]
                weather_summary = weather.get('summary', f"현재 기온 {weather.get('temp')}도") if weather else "날씨 정보 없음"
                pest_summary = ", ".join([p['name'] for p in pest.get('data', [])]) if isinstance(pest, dict) and "data" in pest else "특이사항 없음"
                
                # 실시간 시세 정보 요약 (AI가 읽을 수 있도록 추가)
                price_summary = f"현재 {selected_crop_ko} 시세: {price['price']}원 ({price.get('direction', '')} {price.get('value', '0')}원). 추천: {price.get('recommendation', '없음')}" if price else "시세 정보 없음"
                current_alert = PEST_ALERTS.get(selected_crop_ko)
                if current_alert:
                    pest_context = f"{selected_crop_ko} {current_alert['status']} 발령 중: {', '.join(current_alert['items'])}. 핵심 요령: {current_alert['content']}"
                else:
                    pest_context = "현재 선택하신 작물에 대한 특별한 병해충 특보 사항은 없습니다."

                # [통합 컨텍스트 구성]
                context_for_ai = f"""
                [사용자 설정 및 실시간 정보]
                - 선택된 작물: {selected_crop_ko}
                - 현재 위치: {selected_location}
                - 현재 날씨: {weather_summary}
                - 실시간 시세: {price_summary}
                - **최신 병해충 특보: {pest_context}** # 🔥 이 부분이 핵심!
                - 업로드된 PDF 보고서 데이터가 데이터베이스에 포함되어 있음.
                """
                
                # [RAG 체인 설정] 작물 필터링 적용
                search_kwargs = {"k": 3, "filter": {"crop": selected_crop_en}}
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm, 
                    chain_type="stuff",
                    retriever=vector_db.as_retriever(search_kwargs=search_kwargs),
                    return_source_documents=True
                )
                
                # [프롬프트 구성]
                final_query = f"""
                너는 농업 전문가야. 사용자의 질문에 대해 반드시 위에 제공된 [실시간 정보]와 
                학습된 [지침서/보고서] 내용을 바탕으로 종합적인 컨설팅을 제공해줘.
                
                {context_for_ai}
                
                질문: {last_user_msg}
                """
                
                # [답변 생성]
                res = qa_chain.invoke({"query": final_query})
                full_response = res["result"]
                
                # 타이핑 효과
                temp_text = ""
                for char in full_response:
                    temp_text += char
                    message_placeholder.markdown(temp_text + "▌")
                    time.sleep(0.005)
                message_placeholder.markdown(full_response)
                
                # 4. 📍 답변의 근거 및 참고 문헌 (카드형 UI 개선)
                if res.get("source_documents"):
                    with st.expander("📍 답변의 핵심 근거 및 참고 문헌 확인"):
                        for i, doc in enumerate(res["source_documents"]):
                            source_file = os.path.basename(doc.metadata.get('source', '지침서'))
                            page_info = f"{doc.metadata.get('page')}페이지" if doc.metadata.get('page') else "N/A"
                            
                            st.markdown(f"""
                                <div style="border-left: 3px solid #3fb950; padding: 10px; background-color: rgba(63, 185, 80, 0.05); margin-bottom: 10px; border-radius: 4px;">
                                    <span style="font-weight: bold; color: {txt_col};">[{i+1}] {source_file} (p.{page_info})</span><br>
                                    <div style="font-size: 12px; color: {sub_txt_col}; margin-top: 5px;">{doc.page_content.strip()[:300]}...</div>
                                </div>
                            """, unsafe_allow_html=True)
            
            # 대화 기록 저장
            st.session_state.messages.append(AIMessage(content=full_response))