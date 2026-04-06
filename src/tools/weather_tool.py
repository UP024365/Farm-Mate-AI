import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# .env 파일의 환경변수 로드
load_dotenv()

def get_chungju_weather():
    """
    기상청 단기예보 API를 호출하여 충주 지역의 날씨 원본 데이터를 가져옵니다.
    """
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    service_key = os.getenv("MET_SERVICE_KEY")
    
    # 기상청 가이드: 단기예보는 02, 05, 08, 11, 14, 17, 20, 23시에 업데이트됨
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = "0500" # 가장 안정적인 새벽 예보 시간 고정
    
    params = {
        "serviceKey": service_key,
        "numOfRows": "50", # 넉넉하게 가져옴
        "pageNo": "1",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": "76", # 충주 nx
        "ny": "114" # 충주 ny
    }

    try:
        # 서비스키가 인코딩된 경우를 대비해 unquote 처리 (에러 방지용)
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": f"API 호출 실패: {str(e)}"}

def parse_weather(raw_data):
    """
    복잡한 JSON 데이터를 한글 딕셔너리로 가공합니다.
    """
    try:
        # 정상 응답 확인
        if raw_data.get('response', {}).get('header', {}).get('resultCode') != '00':
            return {"error": "기상청 응답 에러 (인증키나 시간 설정을 확인하세요)"}

        items = raw_data['response']['body']['items']['item']
        
        # 기상청 코드 변환 표
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

# --- 테스트 실행부 ---
if __name__ == "__main__":
    print("1. 기상청에서 원본 데이터를 가져오는 중...")
    raw = get_chungju_weather()
    
    print("2. 데이터를 한글로 가공하는 중...")
    result = parse_weather(raw)
    
    if "error" in result:
        print(f"❌ 실패: {result['error']}")
    else:
        print("\n✅ [충주 지역 실시간 기상 정보]")
        print(f"- 현재 기온: {result['temperature']}")
        print(f"- 하늘 상태: {result['sky']}")
        print(f"- 현재 습도: {result['humidity']}")
        print(f"- 강수 형태: {result['rain_type']}")
        print(f"- 현재 풍속: {result['wind_speed']}")