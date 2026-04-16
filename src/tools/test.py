import requests
import xml.etree.ElementTree as ET

class NongsaroIntegratedTool:
    def __init__(self):
        # 발급받으신 인증키 [cite: 24, 50, 74]
        self.api_key = "20260413Q3XSJWMQYU1TRV8QFLULTA"
        self.base_url = "http://api.nongsaro.go.kr/service/"

    def fetch_data(self, service_type):
        """
        service_type: 'pest' (병해충), 'weekly' (주간농사), 'tech' (작목기술)
        """
        configs = {
            'pest': {
                'url': f"{self.base_url}dbyhsCccrrncInfo/dbyhsCccrrncInfoList", # 
                'title_field': 'cntntsSj', # 
                'extra_field': 'registDt' # 
            },
            'weekly': {
                'url': f"{self.base_url}weekFarmInfo/weekFarmInfoList", # 
                'title_field': 'subject', # 
                'extra_field': 'regDt' # 
            },
            'tech': {
                # (신)작목별 기술정보 대분류 조회 
                'url': f"{self.base_url}cropEbook/mainCategoryList", # 
                'title_field': 'mainCategoryNm', # 
                'extra_field': 'mainCategoryCode' # 
            }
        }

        config = configs.get(service_type)
        if not config:
            return {"error": "지원하지 않는 서비스 타입입니다."}

        params = {"apiKey": self.api_key}
        
        try:
            response = requests.get(config['url'], params=params, timeout=10)
            response.encoding = 'utf-8' # 모든 데이터는 UTF-8 제공 
            
            if response.status_code != 200:
                return {"error": f"HTTP 연결 실패 ({response.status_code})"}

            root = ET.fromstring(response.content)
            result_code = root.find('.//resultCode').text # [cite: 24, 49, 73]
            
            if result_code != "00": # 00이 정상 처리 
                return {"error": f"API 오류 (코드 {result_code})", "msg": root.find('.//resultMsg').text}

            items = root.findall('.//item')
            data_list = []
            
            for item in items:
                title = item.find(config['title_field']).text if item.find(config['title_field']) is not None else "N/A"
                extra = item.find(config['extra_field']).text if item.find(config['extra_field']) is not None else "N/A"
                
                data_list.append({
                    "title": title,
                    "info": extra
                })

            return data_list

        except Exception as e:
            return {"error": f"시스템 예외 발생: {str(e)}"}

if __name__ == "__main__":
    app = NongsaroIntegratedTool()
    
    # 1. 병해충 발생정보 테스트
    print("\n--- [1] 병해충 발생정보 목록 ---")
    pest_data = app.fetch_data('pest')
    print(pest_data[:3] if isinstance(pest_data, list) else pest_data)

    # 2. 주간농사정보 테스트
    print("\n--- [2] 주간농사정보 목록 ---")
    weekly_data = app.fetch_data('weekly')
    print(weekly_data[:3] if isinstance(weekly_data, list) else weekly_data)

    # 3. (신)작목별 농업기술정보(대분류) 테스트
    print("\n--- [3] 작목별 기술정보 (대분류) ---")
    tech_data = app.fetch_data('tech')
    print(tech_data[:3] if isinstance(tech_data, list) else tech_data)