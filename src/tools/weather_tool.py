import requests
import os
from datetime import datetime, timedelta
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_weather_info(nx=76, ny=114):
    """
    기상청 API를 호출하여 원본 데이터를 가져옵니다.
    nx, ny를 매개변수로 받아 지역별 조회가 가능합니다.
    """
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    # Streamlit Cloud 환경이면 st.secrets를, 로컬이면 os.getenv를 사용
    service_key = st.secrets.get("MET_SERVICE_KEY") or os.getenv("MET_SERVICE_KEY")
    
    now = datetime.now()
    
    # 기상청 단기예보는 발표 후 DB 반영까지 시간이 걸리므로 20분 여유를 둡니다.
    if now.hour < 2 or (now.hour == 2 and now.minute < 20):
        base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
        base_time = "2300"
    else:
        base_date = now.strftime("%Y%m%d")
        available_times = [2, 5, 8, 11, 14, 17, 20, 23]
        last_time = 2
        for t in available_times:
            if now.hour >= t: last_time = t
            else: break
        base_time = f"{last_time:02d}00"

    params = {
        "serviceKey": service_key,
        "numOfRows": "100", 
        "pageNo": "1",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx, 
        "ny": ny 
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        raw_data = response.json()
        # 원본 데이터를 바로 파싱 함수로 넘겨 결과를 반환합니다.
        return parse_weather(raw_data)
    except Exception as e:
        return {"error": str(e)}

def parse_weather(raw_data):
    """
    기상청의 복잡한 JSON 데이터를 앱에서 쓰기 좋게 가공합니다.
    """
    try:
        if not raw_data or "error" in raw_data: return None
        if raw_data.get('response', {}).get('header', {}).get('resultCode') != '00':
            return None

        items = raw_data['response']['body']['items']['item']
        
        # 기본 설정 (첫 번째 데이터 기준)
        target_time = items[0]['fcstTime']
        target_date = items[0]['fcstDate']
        sky_codes = {"1": "맑음 ☀️", "3": "구름많음 ☁️", "4": "흐림 ☁️☁️"}
        
        # main.py에서 기대하는 키 값들로 초기화
        parsed_result = {
            "temp": "N/A",      # 온도
            "humidity": "N/A",  # 습도(REH)
            "rain": "0",        # 강수량(RN1) 혹은 강수확률(POP)
            "sky": "정보없음",
            "weather_timeline": "" # AI 상담용 타임라인
        }
        
        time_summary = {}

        for item in items:
            f_date = item['fcstDate']
            f_time = item['fcstTime']
            category = item['category']
            value = item['fcstValue']
            
            time_key = f"{f_date}_{f_time}"
            if time_key not in time_summary:
                time_summary[time_key] = {"time": f_time, "date": f_date}

            # 시간대별 데이터 저장
            if category == "TMP": time_summary[time_key]['temp'] = value
            elif category == "SKY": time_summary[time_key]['sky'] = sky_codes.get(value, "")
            elif category == "REH": time_summary[time_key]['humidity'] = value

            # 현재 시간(가장 빠른 예보) 데이터 추출
            if f_time == target_time and f_date == target_date:
                if category == "TMP": parsed_result['temp'] = value
                elif category == "REH": parsed_result['humidity'] = value
                elif category == "RN1": parsed_result['rain'] = value if value != "강수없음" else "0"
                elif category == "SKY": parsed_result['sky'] = sky_codes.get(value, "정보없음")

        # AI를 위한 타임라인 생성 (3시간 간격)
        sorted_times = sorted(time_summary.keys())[:12]
        timeline_list = []
        for i, k in enumerate(sorted_times):
            if i % 3 == 0:
                t = time_summary[k]
                timeline_list.append(f"{t['time'][:2]}시({t.get('temp', '-')}°C, {t.get('sky', '-')})")
        
        parsed_result['weather_timeline'] = " -> ".join(timeline_list)
        
        return parsed_result

    except Exception as e:
        print(f"데이터 가공 실패: {e}")
        return None