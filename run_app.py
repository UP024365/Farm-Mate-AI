from pyngrok import ngrok
import os

# 1. Ngrok 인증 토큰 설정
ngrok.set_auth_token("3DTy2rJXcpK6a5aM1N340g3aiGq_5QfyQM9uT512FXgLSZ9ut")

try:
    # 2. Streamlit 기본 포트(8501)에 터널링 연결
    public_url = ngrok.connect(8501).public_url
    print("\n" + "="*50)
    print(f"🚀 Farm-Mate 외부 접속 주소: {public_url}")
    print("="*50 + "\n")

    # 3. Streamlit 앱 실행
    # 현재 위치가 최상위 폴더이므로 src/main.py 경로를 지정합니다.
    os.system("streamlit run src/main.py")

except Exception as e:
    print(f"❌ 오류 발생: {e}")