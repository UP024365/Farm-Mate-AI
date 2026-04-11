import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def get_chungju_weather():
    """
    기상청 단기예보 API를 호출하여 충주 지역의 날씨 원본 데이터를 가져옵니다.
    """
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    service_key = os.getenv("MET_SERVICE_KEY")
    
    now = datetime.now()
    
    # 02:10분 이전이면 '어제 23:00' 데이터를 가져옴 (기상청 발표 시간 고려)
    if now.hour < 2 or (now.hour == 2 and now.minute < 10):
        base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
        base_time = "2300"
    else:
        base_date = now.strftime("%Y%m%d")
        available_times = [2, 5, 8, 11, 14, 17, 20, 23]
        last_time = 2
        for t in available_times:
            if now.hour >= t:
                last_time = t
            else:
                break
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
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"기상청 서버 응답 에러: {response.status_code}"}
    except Exception as e:
        return {"error": f"API 호출 중 예외 발생: {str(e)}"}

def parse_weather(raw_data):
    """
    기상청에서 받은 복잡한 JSON 데이터를 사용하기 편하게 한글 딕셔너리로 가공합니다.
    """
    try:
        # 데이터가 정상인지 확인
        if not raw_data or "error" in raw_data:
            return raw_data if raw_data else {"error": "데이터가 비어있습니다."}
            
        if raw_data.get('response', {}).get('header', {}).get('resultCode') != '00':
            return {"error": "기상청 응답 오류 (키 설정이나 시간을 확인하세요)"}

        items = raw_data['response']['body']['items']['item']
        
        # 기상청 코드 한글 변환 매핑
        sky_codes = {"1": "맑음 ☀️", "3": "구름많음 ☁️", "4": "흐림 ☁️☁️"}
        pty_codes = {"0": "없음", "1": "비 ☔", "2": "비/눈 🌨️", "3": "눈 ❄️", "4": "소나기 🌦️"}

        parsed_result = {}
        
        for item in items:
            category = item['category']
            value = item['fcstValue']
            
            if category == "TMP": # 기온
                parsed_result['temperature'] = f"{value}°C"
            elif category == "REH": # 습도
                parsed_result['humidity'] = f"{value}%"
            elif category == "SKY": # 하늘상태
                parsed_result['sky'] = sky_codes.get(value, "정보없음")
            elif category == "PTY": # 강수형태
                parsed_result['rain_type'] = pty_codes.get(value, "정보없음")
            elif category == "WSD": # 풍속
                parsed_result['wind_speed'] = f"{value}m/s"

        return parsed_result

    except Exception as e:
        return {"error": f"데이터 가공 실패: {str(e)}"}