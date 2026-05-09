from pyngrok import ngrok
import os
from dotenv import load_dotenv

# .env 파일로부터 환경변수 로드
load_dotenv()

# 1. 환경변수에서 Ngrok 토큰 가져오기
NGROK_TOKEN = os.getenv("NGROK_AUTHTOKEN")

if not NGROK_TOKEN:
    print("❌ 오류: .env 파일에 'NGROK_AUTHTOKEN'이 설정되지 않았습니다.")
else:
    # 인증 토큰 설정
    ngrok.set_auth_token(NGROK_TOKEN)

    try:
        # 2. Streamlit 기본 포트(8501)에 터널링 연결
        # 이미 열려있는 터널이 있을 경우를 대비해 기존 터널을 확인하거나 새로 생성합니다.
        tunnels = ngrok.get_tunnels()
        if not tunnels:
            public_url = ngrok.connect(8501).public_url
        else:
            public_url = tunnels[0].public_url

        print("\n" + "="*50)
        print(f"🚀 Farm-Mate 외부 접속 주소: {public_url}")
        print("="*50 + "\n")

        # 3. Streamlit 앱 실행
        # src/main.py 경로를 지정하여 실행합니다.
        os.system("streamlit run src/main.py")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")