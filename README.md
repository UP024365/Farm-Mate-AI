⚠️ 실행 전 필수 설정 (Prerequisites)
이 프로젝트는 보안 및 데이터 용량 문제로 일부 설정 파일과 데이터베이스를 GitHub에 포함하지 않습니다. 정상적인 실행을 위해 아래 설정을 반드시 완료해 주세요.

1. 환경 변수 및 API 키 설정
본 프로젝트는 OpenAI, 기상청, KAMIS, 농사로 API 및 이메일 알림, 외부 접속을 위한 총 6가지 외부 설정을 사용합니다. 프로젝트 루트의 .env 파일과 src/.streamlit/secrets.toml 파일을 각각 생성하여 아래 양식대로 키를 입력해야 합니다.

A. .env 파일 양식 (프로젝트 루트 폴더)######################################################################################

# 1. OpenAI 설정
OPENAI_API_KEY=your_openai_api_key_here

# 2. 이메일 알림 설정 (Gmail 앱 비밀번호 16자리 사용)
EMAIL_ADDRESS=your_gmail_address@gmail.com
EMAIL_PASSWORD=your_16digit_app_password
EMAIL_RECEIVER=receiver_email_address@gmail.com

# 3. 공공데이터 API 키
MET_SERVICE_KEY=your_weather_api_key
KAMIS_SERVICE_KEY=your_market_price_api_key
NONG_SERVICE_KEY=your_nongsaro_api_key

# 4. 네트워크 설정
NGROK_AUTHTOKEN=your_ngrok_authtoken_here

B. secrets.toml 파일 양식 (src/.streamlit/ 폴더)###########################################################################

OPENAI_API_KEY = "your_openai_api_key_here"
MET_SERVICE_KEY = "your_weather_api_key"
KAMIS_SERVICE_KEY = "your_market_price_api_key"
NONG_SERVICE_KEY = "your_nongsaro_api_key"

2. 농업 지식 데이터베이스 (Vector DB)
프로젝트 실행 시 구글 드라이브에서 농업 전문 지식이 담긴 chroma_db.zip을 자동으로 동기화합니다.

    - 동기화 로직: 프로젝트 루트에 chroma_db/ 폴더가 없는 경우에만 최초 1회 다운로드를 진행합니다.

    - 주의사항: 로컬 환경에 이미 chroma_db/ 폴더가 존재한다면 절대 삭제하지 마세요. 폴더를 유지해야 구글 드라이브의 일일 다운로드 횟수 제한(Quota)으로 인한 차단을 방지할 수 있습니다.

3. 권장 프로젝트 구조
파일 배치는 반드시 아래 구조를 유지해야 정상적으로 API 키를 인식합니다.

Plaintext
Farm-Mate-AI/
├── chroma_db/           # 자동 생성 및 유지 (삭제 금지)
├── src/
│   ├── .streamlit/
│   │   └── secrets.toml # 직접 생성 (TOML 양식)
│   ├── main.py          # 메인 실행 파일
│   └── tools/           # weather, price, pest, tech 등 도구 모음
├── .env                 # 직접 생성 (ENV 양식)
├── run_app.py           # ngrok 및 서버 통합 실행 스크립트
└── requirements.txt     # 필수 라이브러리 목록

보안 주의: 위 설정 파일(.env, secrets.toml)과 데이터베이스 폴더(chroma_db/)는 .gitignore에 등록되어 GitHub 저장소에 공유되지 않도록 관리되고 있습니다. 새로운 환경에서 실행 시 본 가이드를 따라 수동으로 설정해 주시기 바랍니다.