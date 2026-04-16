import requests
import xml.etree.ElementTree as ET

def get_pest_info():
    """
    농사로 '병해충 발생정보' API 호출 (최종 교정본)
    """
    # 1. URL 수정: 매뉴얼에 명시된 정확한 서비스 경로로 변경 
    url = "http://api.nongsaro.go.kr/service/dbyhsCccrrncInfo/dbyhsCccrrncInfoList"
    api_key = "20260413Q3XSJWMQYU1TRV8QFLULTA"
    params = {"apiKey": api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.encoding = 'utf-8' # 농사로는 모든 데이터를 UTF-8로 제공함 
        
        response_text = response.text
        
        # 2. 인증 오류 체크 (결과코드 11, 12, 13, 15 등) 
        if "<resultCode>00</resultCode>" not in response_text:
            return {"error": "API 호출 실패", "log": response_text}

        # 3. XML 파싱
        try:
            root = ET.fromstring(response.content)
            # 매뉴얼상 목록 데이터는 item 태그 안에 담겨 있음 [cite: 24]
            items = root.findall('.//item')
            pest_list = []
            
            for item in items:
                # 4. 태그명 수정: 매뉴얼 기준 제목 태그는 'cntntsSj'임 
                name = item.find('cntntsSj').text if item.find('cntntsSj') is not None else ""
                date = item.find('registDt').text if item.find('registDt') is not None else ""
                
                if name:
                    pest_list.append({
                        "name": name, 
                        "date": date,
                        "content": "상세 정보는 농사로 홈페이지 참조"
                    })

            if not pest_list:
                return {"status": "현재 주의 단계인 병해충 정보가 없습니다.", "raw_response": response_text}

            return {"data": pest_list}
            
        except ET.ParseError:
            return {"error": "XML 파싱 실패", "log": response_text}

    except Exception as e:
        return {"error": f"농사로 연결 실패: {str(e)}"}

if __name__ == "__main__":
    print("🔍 농사로 병해충 API 호출 테스트 중...")
    result = get_pest_info()
    
    if "error" in result:
        print("\n❌ 오류 발생!")
        print(f"메시지: {result.get('error')}")
        print(f"--- 상세 로그 ---\n{result.get('log')}\n------------------")
    else:
        print(f"\n✅ 성공: {result}")