import requests
import os
from datetime import datetime, timedelta
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_weather_info(nx=76, ny=114):
    """
    실시간 관측(실황)과 향후 예보를 결합하여 반환합니다.
    """
    service_key = st.secrets.get("MET_SERVICE_KEY") or os.getenv("MET_SERVICE_KEY")
    now = datetime.now()

    # --- 1. 실시간 관측 데이터 (지금 온도/강수) ---
    ncst_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    # 실황은 40분 기준 업데이트
    ncst_base_dt = now - timedelta(hours=1) if now.minute < 45 else now
    
    ncst_params = {
        "serviceKey": service_key,
        "numOfRows": "20",
        "dataType": "JSON",
        "base_date": ncst_base_dt.strftime("%Y%m%d"),
        "base_time": ncst_base_dt.strftime("%H00"),
        "nx": nx, "ny": ny
    }

    # --- 2. 단기 예보 데이터 (미래 타임라인) ---
    fcst_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    # 예보는 정해진 시간(2, 5, 8...)에만 발표
    hours = [2, 5, 8, 11, 14, 17, 20, 23]
    if now.hour < 2 or (now.hour == 2 and now.minute < 20):
        fcst_base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
        fcst_base_time = "2300"
    else:
        fcst_base_date = now.strftime("%Y%m%d")
        fcst_last_hour = max([h for h in hours if h <= now.hour])
        fcst_base_time = f"{fcst_last_hour:02d}00"

    fcst_params = {
        "serviceKey": service_key,
        "numOfRows": "100",
        "dataType": "JSON",
        "base_date": fcst_base_date,
        "base_time": fcst_base_time,
        "nx": nx, "ny": ny
    }

    result = {
        "temp": "N/A", "humidity": "N/A", "rain": "0", 
        "sky": "정보없음", "weather_timeline": ""
    }

    try:
        # 실황 데이터 가져오기 (현재 날씨)
        ncst_res = requests.get(ncst_url, params=ncst_params, timeout=10).json()
        if ncst_res.get('response', {}).get('header', {}).get('resultCode') == '00':
            items = ncst_res['response']['body']['items']['item']
            obs_data = {item['category']: item['obsrValue'] for item in items}
            
            result["temp"] = obs_data.get('T1H', 'N/A')
            result["humidity"] = obs_data.get('REH', 'N/A')
            result["rain"] = obs_data.get('RN1', '0')
            
            # 강수 형태 아이콘 설정
            pty = obs_data.get('PTY', '0')
            pty_map = {"0": "맑음 ☀️", "1": "비 ☔", "2": "비/눈 🌨️", "3": "눈 ❄️", "4": "소나기 🌦️"}
            result["sky"] = pty_map.get(pty, "맑음 ☀️")

        # 예보 데이터 가져오기 (타임라인)
        fcst_res = requests.get(fcst_url, params=fcst_params, timeout=10).json()
        if fcst_res.get('response', {}).get('header', {}).get('resultCode') == '00':
            items = fcst_res['response']['body']['items']['item']
            
            sky_codes = {"1": "맑음 ☀️", "3": "구름많음 ☁️", "4": "흐림 ☁️☁️"}
            time_summary = {}
            
            for item in items:
                t_key = f"{item['fcstDate']}_{item['fcstTime']}"
                if t_key not in time_summary:
                    time_summary[t_key] = {"time": item['fcstTime'], "temp": "", "sky": ""}
                
                if item['category'] == "TMP": time_summary[t_key]["temp"] = item['fcstValue']
                elif item['category'] == "SKY": time_summary[t_key]["sky"] = sky_codes.get(item['fcstValue'], "")

            # 향후 12시간 중 3시간 간격으로 4개 지점 추출
            sorted_keys = sorted(time_summary.keys())
            timeline_parts = []
            for i in range(0, min(12, len(sorted_keys)), 3):
                t = time_summary[sorted_keys[i]]
                timeline_parts.append(f"{t['time'][:2]}시({t['temp']}°C, {t['sky']})")
            
            result["weather_timeline"] = " -> ".join(timeline_parts)

        return result

    except Exception as e:
        print(f"날씨 통합 호출 에러: {e}")
        return None