import requests
import urllib3
import ssl
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 보안 장벽을 뚫는 어댑터 ---
class KAMISAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT@SECLEVEL=1') # 핵심: 보안 수준 하향
        context.minimum_version = ssl.TLSVersion.TLSv1 # 추가: 구형 TLS 허용
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def get_crop_price(crop_name="사과"):
    # 품목 코드 매핑 (사용자님 제공 데이터)
    crop_map = {
        "사과": {"code": "411", "cat": "400"},
        "배": {"code": "412", "cat": "400"},
        "포도": {"code": "414", "cat": "400"},
        "마늘": {"code": "244", "cat": "200"},
        "양파": {"code": "245", "cat": "200"},
        "무": {"code": "231", "cat": "200"},
        "배추": {"code": "211", "cat": "200"},
        "쌀": {"code": "111", "cat": "100"}
    }

    target_info = crop_map.get(crop_name, crop_map["사과"])

    session = requests.Session()
    session.mount("https://", KAMISAdapter())

    base_url = "https://www.kamis.or.kr/service/price/xml.do"

    # 최근 7일간의 데이터를 뒤져서 가장 최신 평일 데이터를 찾음
    for i in range(8):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

        params = {
            "action": "dailyPriceByCategoryList", # 더 안정적인 액션으로 변경
            "p_cert_key": "49be2073-c510-4e68-a02d-2e1c2451a1ae",
            "p_cert_id": "7590",
            "p_returntype": "json",
            "p_product_cls_code": "01", # 소매
            "p_item_category_code": target_info["cat"],
            "p_regday": target_date,
            "p_convert_kg_yn": "N"
        }

        try:
            response = session.get(base_url, params=params, verify=False, timeout=10)
            
            if not response.text.strip():
                continue

            data = response.json()
            
            # KAMIS 응답 구조 파싱 (data -> item 리스트)
            if "data" not in data or not isinstance(data["data"], dict):
                continue
                
            items = data["data"].get("item", [])
            
            # 내가 찾는 품목 코드와 일치하는 데이터 필터링
            target_item = next((x for x in items if x.get('item_code') == target_info['code']), None)

            if target_item:
                # 가격 데이터 정제
                def clean_p(p):
                    if not p: return 0
                    p = str(p).replace(",", "").strip()
                    try:
                        return int(float(p))
                    except:
                        return 0

                curr_p = clean_p(target_item.get("dpr1")) # 당일 가격
                prev_p = clean_p(target_item.get("dpr2")) # 1일전 가격

                # 오늘 가격이 없으면 어제 가격이라도 사용 (fallback)
                if curr_p == 0 and prev_p != 0:
                    curr_p = prev_p

                if curr_p == 0:
                    continue

                # 등락 계산
                diff = curr_p - prev_p
                direction = "▲" if diff > 0 else "▼" if diff < 0 else "-"

                return {
                    "item_name": f"{crop_name}({target_item.get('kind_name', '상품')})",
                    "price": f"{curr_p:,}원",
                    "direction": direction,
                    "value": f"{abs(diff):,}",
                    "unit": target_item.get("unit", "-"),
                    "status": f"{target_date} 최신 시세"
                }

        except Exception:
            continue

    return {
        "item_name": f"{crop_name}(조회불가)",
        "price": "확인불가",
        "direction": "",
        "value": "0",
        "unit": "-",
        "status": "안내: 최근 7일 내 집계된 시세가 없습니다."
    }

if __name__ == "__main__":
    # 테스트 실행
    result = get_crop_price("배추")
    print(f"=== {result['status']} ===")
    print(f"품목: {result['item_name']}")
    print(f"가격: {result['price']} ({result['direction']} {result['value']})")
    print(f"단위: {result['unit']}")