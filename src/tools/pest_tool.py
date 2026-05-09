import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def get_pest_info():
    """
    농사로 '병해충 발생정보' API 호출 및 최신 정보 필터링
    """
    url = "http://api.nongsaro.go.kr/service/dbyhsCccrrncInfo/dbyhsCccrrncInfoList"
    api_key = "20260413Q3XSJWMQYU1TRV8QFLULTA" # 매뉴얼상 인증키 필수 [cite: 177]
    params = {"apiKey": api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.encoding = 'utf-8' # 모든 데이터는 UTF-8 제공 [cite: 156]
        
        if "<resultCode>00</resultCode>" not in response.text: # 정상 처리 코드 00 [cite: 194]
            return {"error": "API 호출 실패", "log": response.text}

        root = ET.fromstring(response.content)
        items = root.findall('.//item') # 서비스 항목은 item 하위 제공 [cite: 159]
        pest_list = []
        
        # 현재 날짜 (매월 1일 업데이트 체크용)
        current_month = datetime.now().strftime("%Y.%m")
        
        for item in items:
            name = item.find('cntntsSj').text if item.find('cntntsSj') is not None else "" # 응답변수 cntntsSj 
            date = item.find('registDt').text if item.find('registDt') is not None else "" # 응답변수 registDt 
            
            if name:
                # 이번 달 최신 정보인지 여부 표시
                is_latest = current_month in name or current_month in date
                pest_list.append({
                    "name": name, 
                    "date": date,
                    "is_latest": is_latest,
                    "content": "상세 내용은 농사로 홈페이지 또는 앱 내 지침서 참조"
                })

        if not pest_list:
            return {"status": "현재 주의 단계인 병해충 정보가 없습니다."}

        return {"data": pest_list}
            
    except Exception as e:
        return {"error": f"시스템 연결 실패: {str(e)}"}