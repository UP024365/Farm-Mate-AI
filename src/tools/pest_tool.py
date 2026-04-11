import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

load_dotenv()

def get_pest_info():
    """
    농사로 '병해충 발생정보' API 호출 (URL 및 파라미터 교정본)
    """
    # 1. URL 확인: psitMainList 대신 아래 주소를 주로 사용합니다.
    url = "http://api.nongsaro.go.kr/service/psitMain/psitMainList"
    api_key = os.getenv("NONG_SERVICE_KEY")

    # 2. 파라미터에서 'type' 제거 (XML이 기본이라 type=json이 에러를 유발할 수 있음)
    params = {
        "apiKey": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        
        # 만약 응답에 '유효한 요청주소가 아니다'라는 글자가 있으면 IP 등록 문제임
        if "유효한 요청주소가 아닙니다" in response.text:
            return {"error": "농사로 API에 등록된 IP와 현재 내 컴퓨터의 IP가 다릅니다."}

        root = ET.fromstring(response.content)
        
        # 데이터 파싱 로직
        items = root.findall('.//item')
        pest_list = []
        for item in items:
            name = item.find('psitNm').text if item.find('psitNm') is not None else ""
            if name:
                pest_list.append({"name": name, "content": "상세 정보는 농사로 홈페이지 참조"})

        if not pest_list:
            return {"status": "현재 주의 단계인 병해충 정보가 없습니다."}

        return {"data": pest_list}

    except Exception as e:
        return {"error": f"농사로 연결 실패: {str(e)}"}
    
    # ... (기존 코드 생략) ...

if __name__ == "__main__":
    # 직접 실행했을 때 결과를 출력해서 확인해봅니다.
    print("🔍 농사로 병해충 API 호출 테스트 중...")
    result = get_pest_info()
    print(f"결과: {result}")