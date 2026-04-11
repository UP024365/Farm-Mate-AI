import requests
import json
import urllib3
import ssl
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# 1. SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 2. 구형 서버 호환성을 위한 SSL 어댑터 (Handshake Failure 방지)
class KAMISAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1') # 보안 수준 하향
        kwargs['ssl_context'] = context
        return super(KAMISAdapter, self).init_poolmanager(*args, **kwargs)

def get_crop_price(crop_name="사과"):
    # 최신 코드표 반영 (사과 411, 배 412, 배추 211)
    crop_map = {
        "사과": {"code": "411", "cat": "400"},
        "배": {"code": "412", "cat": "400"},
        "배추": {"code": "211", "cat": "200"}
    }
    
    target_info = crop_map.get(crop_name, crop_map["사과"])
    
    session = requests.Session()
    session.mount("https://", KAMISAdapter())
    
    # [핵심] 정확한 API 호출 경로 (xml.do 지만 p_returntype=json이면 JSON으로 옴)
    base_url = "https://www.kamis.or.kr/service/price/xml.do"
    
    # 테스트 날짜 (데이터가 확실히 있는 과거 평일)
    test_date = "2024-04-05" 
    
    params = {
        "action": "dailySalesList",
        "p_cert_key": "49be2073-c510-4e68-a02d-2e1c2451a1ae",
        "p_cert_id": "7590",
        "p_returntype": "json",
        "p_product_cls_code": "01", # 소매
        "p_item_category_code": target_info["cat"],
        "p_item_code": target_info["code"],
        "p_regday": test_date
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # verify=False와 함께 정확한 base_url 호출
        response = session.get(base_url, params=params, headers=headers, verify=False, timeout=15)
        
        # HTML이 왔는지 체크 (에러 방지)
        if "<html" in response.text.lower():
            return {"item_name": crop_name, "status": "실패", "reason": "서버가 JSON 대신 HTML 홈페이지를 반환함 (URL 확인 필요)"}

        data = response.json()
        
        # 데이터 구조 파싱 (KAMIS 응답: {"price": {"item": [...]}})
        price_data = data.get("price")
        if isinstance(price_data, dict):
            items = price_data.get("item", [])
            if items:
                # 첫 번째 항목의 가격(dpr1) 추출
                latest = items[0] if isinstance(items, list) else items
                raw_p = str(latest.get("dpr1", "0")).replace(",", "")
                curr_p = int(float(raw_p))
                return {
                    "item_name": crop_name, 
                    "price": f"{curr_p:,}원", 
                    "status": "성공",
                    "date": test_date
                }
        
        return {"item_name": crop_name, "status": "데이터 없음", "raw_data": data}

    except Exception as e:
        return {"item_name": crop_name, "status": "에러", "detail": str(e)}

if __name__ == "__main__":
    result = get_crop_price("사과")
    print(f"\n최종 테스트 결과: {result}")