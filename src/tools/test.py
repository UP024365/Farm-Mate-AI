import requests
import urllib3
import ssl
from requests.adapters import HTTPAdapter

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 최후의 수단: SSL 보안 수준 강제 하향 어댑터 ---
class UltraLegacyAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        # 최신 OpenSSL에서도 구형 TLS/암호화 방식을 허용하도록 설정
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1') # 보안 수준 1단계로 하향
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        # TLS 버전을 구형부터 신형까지 다 허용
        ctx.minimum_version = ssl.TLSVersion.TLSv1
        
        kwargs['ssl_context'] = ctx
        return super(UltraLegacyAdapter, self).init_poolmanager(*args, **kwargs)

def get_kamis_price():
    # 인증 정보
    CERT_ID = "7590"
    CERT_KEY = "49be2073-c510-4e68-a02d-2e1c2451a1ae"
    
    # API URL (주말에는 데이터가 없으므로 최근 평일인 4월 10일 데이터 요청)
    url = "https://www.kamis.or.kr/service/price/xml.do"
    params = {
        "action": "dailyPriceByCategoryList",
        "p_cert_key": CERT_KEY,
        "p_cert_id": CERT_ID,
        "p_returntype": "json",
        "p_product_cls_code": "01",
        "p_item_category_code": "100", # 식량작물
        "p_regday": "2026-04-10",
        "p_convert_kg_yn": "N"
    }

    session = requests.Session()
    # 모든 https 접속에 대해 보안 하향 어댑터 적용
    session.mount("https://", UltraLegacyAdapter())

    try:
        print("🚀 KAMIS 서버에 직접 연결 시도 중...")
        response = session.get(url, params=params, verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and isinstance(data["data"], dict):
                print("✅ 연결 성공! 데이터를 가져왔습니다.")
                items = data["data"]["item"]
                
                print("-" * 50)
                print(f"{'품목명':<10} | {'단위':<5} | {'당일가격':>10}")
                print("-" * 50)
                for item in items[:10]: # 상위 10개만 출력
                    name = item['item_name']
                    unit = item['unit']
                    price = item['dpr1']
                    print(f"{name:<10} | {unit:<5} | {price:>10}원")
                print("-" * 50)
            else:
                print(f"⚠️ 서버 응답은 성공했으나 데이터가 없습니다: {data.get('return_msg', '정보 없음')}")
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 최종 시도 실패: {e}")

if __name__ == "__main__":
    get_kamis_price()