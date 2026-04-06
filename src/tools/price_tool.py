import os
import json
import ssl
from urllib.request import Request, urlopen
from dotenv import load_dotenv

load_dotenv()

def get_crop_price():
    cert_key = os.getenv("KAMIS_SERVICE_KEY")
    # 최신 평일 날짜 (데이터가 확실히 있는 4월 3일 금요일 기준 테스트)
    base_url = "https://www.kamis.or.kr/service/price/xml.do"
    params = (
        f"?action=dailyPriceByCategoryList&p_cert_key={cert_key}&p_cert_id=2712"
        "&p_returntype=json&p_item_category_code=200&p_product_cls_code=01"
        "&p_country_code=1101&p_regday=2026-04-03&p_convert_kg_yn=N"
    )
    full_url = base_url + params

    try:
        context = ssl._create_unverified_context()
        req = Request(full_url)
        with urlopen(req, context=context, timeout=15) as response:
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)
            
            # 실제 데이터 안에서 '사과' 찾기 로직
            if "data" in data and isinstance(data["data"], dict):
                item_list = data["data"].get("item", [])
                for item in item_list:
                    # 사과(후지) 데이터만 필터링
                    if item.get("item_name") == "사과" and item.get("kind_name") == "후지":
                        return {
                            "item_name": "사과(후지)",
                            "unit": item.get("unit", "10개"),
                            "price": f"{item.get('dpr1', '0')}원",
                            "direction": "▲" if item.get("direction") == "0" else "▼",
                            "value": item.get("value", "0"),
                            "status": "실시간 데이터 로드 성공"
                        }
            
            # 만약 데이터는 왔는데 사과가 없으면 에러로 간주
            raise Exception("데이터 내 사과 정보 없음")
            
    except Exception as e:
        # 서버 점검, 주말, SSL 에러 등 발생 시 '안전하게' 가짜 데이터 반환
        return {
            "item_name": "사과(후지)",
            "unit": "10개",
            "price": "28,500원",
            "direction": "▲",
            "value": "500",
            "status": f"테스트 데이터 (사유: {str(e)})"
        }

if __name__ == "__main__":
    print(get_crop_price())