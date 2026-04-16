import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

load_dotenv()

def get_weekly_farming_info():
    """
    농사로 '주간 농사정보' API 호출
    """
    url = "http://api.nongsaro.go.kr/service/weeklyFarmingInfo/weeklyFarmingInfoList"
    api_key = os.getenv("NONG_SERVICE_KEY")

    params = {
        "apiKey": api_key,
        "numOfRows": "5"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        root = ET.fromstring(response.content)
        
        items = root.findall('.//item')
        weekly_list = []
        
        for item in items:
            subject = item.find('subject').text if item.find('subject') is not None else "정보 없음"
            # 파일 다운로드 경로 등이 포함될 수 있으나 여기선 제목 위주로 추출
            weekly_list.append({"subject": subject})

        if not weekly_list:
            return {"status": "이번 주 농사 정보가 아직 업데이트되지 않았습니다."}

        return {"data": weekly_list}

    except Exception as e:
        return {"error": f"주간 농사정보 호출 실패: {str(e)}"}