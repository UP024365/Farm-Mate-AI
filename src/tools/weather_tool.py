import requests
import os
from datetime import datetime, timedelta
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_weather_info(nx=76, ny=114):
    """
    현재 날씨 실황과 단기예보(향후 1~2일)를 결합하여 반환합니다.
    """
    service_key = st.secrets.get("MET_SERVICE_KEY") or os.getenv("MET_SERVICE_KEY")
    now = datetime.now()

    # --- 1. 초단기실황 (현재 온도, 강수량 등 실제 관측값) ---
    ncst_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    # 실황은 매시 40분에 생성되므로 45분 이전이면 1시간 전 데이터를 호출합니다.
    ncst_base_dt = now - timedelta(hours=1) if now.minute < 45 else now
    
    ncst_params = {
        "serviceKey": service_key,
        "numOfRows": "20",
        "dataType": "JSON",
        "base_date": ncst_base_dt.strftime("%Y%m%d"),
        "base_time": ncst_base_dt.strftime("%H00"),
        "nx": nx, "ny": ny
    }

    # --- 2. 단기예보 (내일, 모레까지의 상세 예보) ---
    fcst_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    # 단기예보 발표 시간: 02, 05, 08, 11, 14, 17, 20, 23시 (1일 8회)
    hours = [2, 5, 8, 11, 14, 17, 20, 23]
    if now.hour < 2 or (now.hour == 2 and now.minute < 10):
        fcst_base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
        fcst_base_time = "2300"
    else:
        fcst_base_date = now.strftime("%Y%m%d")
        fcst_last_hour = max([h for h in hours if h <= now.hour])
        fcst_base_time = f"{fcst_last_hour:02d}00"

    fcst_params = {
        "serviceKey": service_key,
        "numOfRows": "200", # 내일 데이터를 충분히 가져오기 위해 행 수 증가
        "dataType": "JSON",
        "base_date": fcst_base_date,
        "base_time": fcst_base_time,
        "nx": nx, "ny": ny
    }

    result = {
        "temp": "N/A", "humidity": "N/A", "rain": "0", 
        "sky": "정보없음", "weather_timeline": "",
        "summary": "날씨 정보를 분석 중입니다..."
    }

    try:
        # 실황(현재 날씨) 데이터 처리
        ncst_res = requests.get(ncst_url, params=ncst_params, timeout=10).json()
        if ncst_res.get('response', {}).get('header', {}).get('resultCode') == '00':
            items = ncst_res['response']['body']['items']['item']
            obs_data = {item['category']: item['obsrValue'] for item in items}
            
            result["temp"] = obs_data.get('T1H', 'N/A')
            result["humidity"] = obs_data.get('REH', 'N/A')
            result["rain"] = obs_data.get('RN1', '0')
            
            # 강수 형태 (PTY) 아이콘
            pty = obs_data.get('PTY', '0')
            pty_map = {"0": "맑음 ☀️", "1": "비 ☔", "2": "비/눈 🌨️", "3": "눈 ❄️", "4": "소나기 🌦️"}
            result["sky"] = pty_map.get(pty, "맑음 ☀️")

        # 단기예보(향후 타임라인) 데이터 처리
        fcst_res = requests.get(fcst_url, params=fcst_params, timeout=10).json()
        if fcst_res.get('response', {}).get('header', {}).get('resultCode') == '00':
            items = fcst_res['response']['body']['items']['item']
            
            sky_codes = {"1": "맑음 ☀️", "3": "구름많음 ☁️", "4": "흐림 ☁️☁️"}
            time_summary = {}
            
            for item in items:
                # 날짜와 시간을 묶어서 키로 사용
                t_key = f"{item['fcstDate']}_{item['fcstTime']}"
                if t_key not in time_summary:
                    time_summary[t_key] = {
                        "date": item['fcstDate'],
                        "time": item['fcstTime'], 
                        "temp": "", "sky": ""
                    }
                
                if item['category'] == "TMP": time_summary[t_key]["temp"] = item['fcstValue']
                elif item['category'] == "SKY": time_summary[t_key]["sky"] = sky_codes.get(item['fcstValue'], "")

            # 향후 24시간(내일 이맘때까지) 데이터를 3시간 간격으로 추출
            sorted_keys = sorted(time_summary.keys())
            timeline_parts = []
            # min(24, ...) -> 24시간치 데이터를 3시간 간격으로 하면 약 8개 지점 노출
            for i in range(0, min(24, len(sorted_keys)), 3):
                t = time_summary[sorted_keys[i]]
                # 날짜 가독성 처리 (ex: 04월 23일)
                f_date = f"{t['date'][4:6]}월 {t['date'][6:8]}일"
                timeline_parts.append(f"{f_date} {t['time'][:2]}시({t['temp']}°C, {t['sky']})")
            
            result["weather_timeline"] = " -> ".join(timeline_parts)
            
            # AI를 위한 요약 텍스트 생성
            if result["temp"] != "N/A":
                result["summary"] = f"현재 {ncst_base_dt.hour}시 기준 기온은 {result['temp']}도, {result['sky']}입니다. " \
                                   f"내일 예보를 포함한 흐름은 다음과 같습니다: {result['weather_timeline']}"

        return result

    except Exception as e:
        print(f"날씨 통합 호출 에러: {e}")
        return result