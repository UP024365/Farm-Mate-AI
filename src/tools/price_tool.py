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
        context.minimum_version = ssl.TLSVersion.TLSv1
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def get_crop_price(crop_name="사과"):
    crop_map = {
        "사과": {"code": "411", "cat": "400"},
        "배추": {"code": "211", "cat": "200"},
        "고추": {"code": "223", "cat": "200"},
        "마늘": {"code": "258", "cat": "200"},
        "감자": {"code": "152", "cat": "100"},
        "오이": {"code": "224", "cat": "200"},
        "복숭아": {"code": "413", "cat": "400"},
        "딸기": {"code": "226", "cat": "200"},
        "고구마": {"code": "151", "cat": "100"},
        "토마토": {"code": "225", "cat": "200"}
    }

    target_info = crop_map.get(crop_name, crop_map["사과"])
    session = requests.Session()
    session.mount("https://", KAMISAdapter())
    base_url = "https://www.kamis.or.kr/service/price/xml.do"

    for i in range(8):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        params = {
            "action": "dailyPriceByCategoryList",
            "p_cert_key": "49be2073-c510-4e68-a02d-2e1c2451a1ae",
            "p_cert_id": "7590",
            "p_returntype": "json",
            "p_product_cls_code": "01",
            "p_item_category_code": target_info["cat"],
            "p_regday": target_date,
            "p_convert_kg_yn": "N"
        }

        try:
            response = session.get(base_url, params=params, verify=False, timeout=10)
            if not response.text.strip(): continue
            data = response.json()
            if "data" not in data or not isinstance(data["data"], dict): continue
            items = data["data"].get("item", [])
            target_item = next((x for x in items if x.get('item_code') == target_info['code']), None)

            if target_item:
                def clean_p(p):
                    if not p or p == "-": return 0
                    p = str(p).replace(",", "").strip()
                    try: return int(float(p))
                    except: return 0

                # 다양한 시세 데이터 추출
                curr_p = clean_p(target_item.get("dpr1"))  # 당일
                prev_p = clean_p(target_item.get("dpr2"))  # 1일전
                week_p = clean_p(target_item.get("dpr3"))  # 1주일전
                month_p = clean_p(target_item.get("dpr5")) # 1개월전
                year_p = clean_p(target_item.get("dpr6"))  # 1년전
                avg_p = clean_p(target_item.get("dpr7"))   # 평년

                if curr_p == 0: continue

                # --- 🧠 인공지능 출하 추천 로직 ---
                analysis = []
                recommendation = "정보 분석 중..."
                
                # 1. 평년 대비 분석
                if avg_p > 0:
                    if curr_p > avg_p * 1.1: analysis.append("평년 대비 고시세 형성 중입니다.")
                    elif curr_p < avg_p * 0.9: analysis.append("평년 대비 가격이 낮은 편입니다.")
                
                # 2. 추세 분석 (1주일 전 대비)
                if week_p > 0:
                    if curr_p > week_p: analysis.append("최근 1주일간 상승 흐름을 보이고 있습니다.")
                    elif curr_p < week_p: analysis.append("최근 가격이 하락세를 보이고 있습니다.")

                # 3. 최종 추천 결정
                if curr_p > week_p and curr_p > avg_p:
                    recommendation = "🚀 [판매 추천] 시세가 정점에 도달했을 가능성이 높습니다. 출하를 고려해보세요."
                elif curr_p < week_p and curr_p < avg_p:
                    recommendation = "⏳ [관망 추천] 가격이 저점입니다. 시세 회복을 기다리며 보관 관리에 신경 쓰세요."
                elif curr_p > week_p:
                    recommendation = "📈 [상승 중] 가격이 오르는 추세입니다. 며칠 더 추이를 지켜보는 것도 좋습니다."
                else:
                    recommendation = "⚖️ [보합세] 시세 변화가 크지 않습니다. 작업 일정에 맞춰 출하하세요."

                diff = curr_p - prev_p
                direction = "▲" if diff > 0 else "▼" if diff < 0 else "-"

                return {
                    "item_name": f"{crop_name}({target_item.get('kind_name', '상품')})",
                    "price": f"{curr_p:,}원",
                    "direction": direction,
                    "value": f"{abs(diff):,}",
                    "unit": target_item.get("unit", "-"),
                    "status": f"{target_date} 최신 시세",
                    "analysis": " ".join(analysis),
                    "recommendation": recommendation
                }
        except Exception: continue

    return {
        "item_name": f"{crop_name}(조회불가)", "price": "확인불가", "direction": "", "value": "0", "unit": "-",
        "status": "안내: 최근 7일 내 집계된 시세가 없습니다.", "analysis": "", "recommendation": "데이터 확인 불가"
    }