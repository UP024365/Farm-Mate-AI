import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_chungju_weather():
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    service_key = os.getenv("MET_SERVICE_KEY")
    
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
        "nx": "76", 
        "ny": "114" 
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def parse_weather(raw_data):
    try:
        if not raw_data or "error" in raw_data: return raw_data
        if raw_data.get('response', {}).get('header', {}).get('resultCode') != '00':
            return {"error": "기상청 응답 오류"}

        items = raw_data['response']['body']['items']['item']
        
        # 1. 기본 설정
        target_time = items[0]['fcstTime']
        target_date = items[0]['fcstDate']
        sky_codes = {"1": "맑음 ☀️", "3": "구름많음 ☁️", "4": "흐림 ☁️☁️"}
        pty_codes = {"0": "없음", "1": "비 ☔", "2": "비/눈 🌨️", "3": "눈 ❄️", "4": "소나기 🌦️"}

        parsed_result = {
            "temperature": "정보없음",
            "sky": "정보없음",
            "pop": "0%",
            "fcst_time": f"{target_time[:2]}:00",
            "timeline": [] # 👈 시간별 흐름을 담을 리스트
        }
        
        # 시간대별 데이터를 임시 저장할 딕셔너리
        time_summary = {}

        for item in items:
            f_date = item['fcstDate']
            f_time = item['fcstTime']
            category = item['category']
            value = item['fcstValue']
            
            time_key = f"{f_date}_{f_time}"
            if time_key not in time_summary:
                time_summary[time_key] = {"time": f_time, "date": f_date}

            # 데이터 분류
            if category == "TMP": time_summary[time_key]['temp'] = value
            elif category == "SKY": time_summary[time_key]['sky'] = sky_codes.get(value, "")
            elif category == "POP": time_summary[time_key]['pop'] = value

            # 2. '현재' 실시간 정보 채우기 (가장 빠른 데이터)
            if f_time == target_time and f_date == target_date:
                if category == "TMP": parsed_result['temperature'] = f"{value}°C"
                elif category == "SKY": parsed_result['sky'] = sky_codes.get(value, "정보없음")
                elif category == "PTY": parsed_result['rain_type'] = pty_codes.get(value, "정보없음")
                elif category == "POP": parsed_result['pop'] = f"{value}%"

        # 3. 🤖 AI를 위한 '기상 타임라인' 생성 (향후 12시간, 3시간 간격)
        sorted_times = sorted(time_summary.keys())[:12] # 앞부분 12개 시간대
        timeline_str = []
        
        for i, k in enumerate(sorted_times):
            # 3시간 간격으로 요약해서 AI의 읽기 부담을 줄임
            if i % 3 == 0:
                t = time_summary[k]
                timeline_str.append(f"{t['time'][:2]}시({t['temp']}°C, {t['sky']})")
        
        parsed_result['weather_timeline'] = " -> ".join(timeline_str)
        
        return parsed_result

    except Exception as e:
        return {"error": f"데이터 가공 실패: {str(e)}"}