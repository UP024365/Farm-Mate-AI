import streamlit as st
from tools.weather_tool import get_chungju_weather, parse_weather
from tools.price_tool import get_crop_price
from tools.pest_tool import get_pest_info

st.set_page_config(page_title="Farm-Mate-AI", page_icon="👨‍🌾", layout="wide")

st.title("👨‍🌾 Farm-Mate-AI 종합 대시보드")
st.info("충주 지역 농민을 위한 실시간 통합 정보 서비스입니다.")

# 1. 데이터 미리 로드 (화면 그리기 전에 한꺼번에 가져오기)
raw_weather = get_chungju_weather()
weather = parse_weather(raw_weather)
price_data = get_crop_price()
pest_data = get_pest_info()

# 3구역으로 화면 나누기
col_weather, col_price, col_pest = st.columns(3)

# --- 1. 날씨 섹션 ---
with col_weather:
    st.subheader("🌤️ 실시간 날씨")
    if "error" not in weather:
        st.metric("온도", weather.get('temperature'))
        st.write(f"**상태:** {weather.get('sky')}")
        st.write(f"**습도:** {weather.get('humidity')}")
        st.write(f"**풍속:** {weather.get('wind_speed')}")
    else:
        st.error(f"날씨 로드 실패: {weather['error']}")

# --- 2. 시세 섹션 (가공된 데이터 표시) ---
with col_price:
    st.subheader("💰 오늘의 시세")
    # API 응답 구조에 맞춰 데이터 추출
    if "price" in price_data: # 가짜 데이터 모드일 때
        st.success("실시간 시세 로드 성공")
        st.metric(f"{price_data['item_name']} ({price_data['unit']})", 
                  price_data['price'], 
                  delta=f"{price_data['direction']}{price_data['value']}원")
    elif "data" in price_data: # 실제 KAMIS 데이터일 때
        # 첫 번째 품목의 가격 정보를 가져옴
        item = price_data['data']['item'][0]
        st.success("전국 평균 시세 로드")
        st.metric(f"{item['item_name']} ({item['kind_name']})", 
                  f"{item['dpr1']}원", 
                  delta=f"{item['direction']} {item['value']}원")
    else:
        st.error("시세 정보를 해석할 수 없습니다.")

# --- 3. 병해충 섹션 (최종 보정본) ---
with col_pest:
    st.subheader("🐛 병해충 알림")
    
    # 데이터가 아예 없을 때
    if not pest_data:
        st.info("병해충 정보를 불러오는 중입니다...")
    
    # 1. 딕셔너리 형태일 때 (가장 일반적)
    elif isinstance(pest_data, dict):
        if "data" in pest_data:
            st.warning("⚠️ 주의 병해충 발생!")
            for p in pest_data['data']:
                st.write(f"📍 **{p['name']}**")
                st.caption(p['content'])
        elif "status" in pest_data:
            st.success("✅ 현재 특이사항 없음")
            st.write(pest_data['status'])
        elif "error" in pest_data:
            st.error(f"에러: {pest_data['error']}")
        else:
            st.info("병해충 상세 정보를 분석 중입니다...")

    # 2. 결과가 그냥 글자(String)로 왔을 때 (예비용)
    elif isinstance(pest_data, str):
        if "없습니다" in pest_data or "성공" in pest_data:
            st.success("✅ 현재 특이사항 없음")
            st.write(pest_data)
        else:
            st.warning("⚠️ 정보 확인")
            st.write(pest_data)
            
# 토큰을 안 쓰기 위해 chat_input은 일단 모양만 둡니다.
st.chat_input("아직 AI 상담을 시작하지 않았습니다. (토큰 보존 중)")