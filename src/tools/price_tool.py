import requests
import urllib3
import ssl
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class KAMISAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def get_crop_price(crop_name="사과"):
    # 품목 코드 매핑
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

    # ✅ 수정 1: 올바른 API URL
    base_url = "https://www.kamis.or.kr/service/price/xml.do"

    # 최근 7일 조회 (fallback)
    for i in range(8):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

        params = {
            "action": "dailySalesList",
            "p_cert_key": "49be2073-c510-4e68-a02d-2e1c2451a1ae",
            "p_cert_id": "7590",
            "p_returntype": "json",
            "p_product_cls_code": "01",  # 소매
            "p_item_category_code": target_info["cat"],
            "p_item_code": target_info["code"],
            "p_convert_kg_yn": "N",  # ✅ 수정 2: 추가
            "p_regday": target_date
        }

        try:
            response = session.get(base_url, params=params, verify=False, timeout=10)

            # 🔍 디버깅용 (문제 있으면 주석 해제)
            # print("URL:", response.url)
            # print("응답:", response.text[:200])

            if not response.text.strip():
                continue

            data = response.json()

            # 데이터 구조 대응
            items = data.get("price", {}).get("item", [])
            if not items and isinstance(data.get("data"), list):
                items = data["data"]

            if items:
                latest = items[0] if isinstance(items, list) else items

                # 가격 정제 함수
                def clean_p(p):
                    p = str(p).replace(",", "").strip()
                    return int(float(p)) if p not in ["-", "", "None", "0"] else 0

                curr_p = clean_p(latest.get("dpr1", 0))
                prev_p = clean_p(latest.get("dpr2", 0))

                # ✅ 수정 3: fallback 처리
                if curr_p == 0 and prev_p != 0:
                    curr_p = prev_p

                if curr_p == 0:
                    continue

                # 등락 계산
                diff = curr_p - prev_p
                direction = "▲" if diff > 0 else "▼" if diff < 0 else ""

                return {
                    "item_name": f"{crop_name}({latest.get('rank', '상품')})",
                    "price": f"{curr_p:,}원",
                    "direction": direction,
                    "value": f"{abs(diff):,}",
                    "unit": latest.get("unit", "-"),
                    "status": f"{target_date} 최신 시세"
                }

        except Exception as e:
            # print("에러:", e)  # 필요하면 확인
            continue

    # 실패 시
    return {
        "item_name": f"{crop_name}(조회불가)",
        "price": "확인불가",
        "direction": "",
        "value": "0",
        "unit": "-",
        "status": "안내: 최근 7일 내 집계된 시세가 없습니다."
    }


if __name__ == "__main__":
    print(get_crop_price("사과"))