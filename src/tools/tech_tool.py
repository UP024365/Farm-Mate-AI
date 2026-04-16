import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

load_dotenv()

def get_crop_tech_info(crop_name="사과"):
    """
    농사로 '작목별 농업기술정보' API 호출
    """
    url = "http://api.nongsaro.go.kr/service/farmingTechnique/farmingTechniqueList"
    api_key = os.getenv("NONG_SERVICE_KEY")

    params = {
        "apiKey": api_key,
        "srchNm": crop_name,  # 작물 이름으로 검색
        "numOfRows": "3"      # 최신 3건만 가져옴
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        root = ET.fromstring(response.content)
        
        items = root.findall('.//item')
        tech_list = []
        
        for item in items:
            title = item.find('farmingTechniqueNm').text if item.find('farmingTechniqueNm') is not None else "제목 없음"
            date = item.find('refrncDate').text if item.find('refrncDate') is not None else ""
            link = f"https://www.nongsaro.go.kr" # 상세 페이지 연결용 베이스
            
            tech_list.append({"title": title, "date": date})

        if not tech_list:
            return {"status": f"현재 {crop_name}에 대한 최신 기술 정보가 없습니다."}

        return {"data": tech_list}

    except Exception as e:
        return {"error": f"농업 기술정보 호출 실패: {str(e)}"}