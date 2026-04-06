# Farm-Mate-AI

Agri-Pal-AI/ (또는 정하신 프로젝트 이름)
├── .github/              # 깃허브 액션 등 설정 (선택사항)
├── data/                 # 농사로에서 받은 PDF 지침서 보관함
│   └── manuals/          # 사과, 배추 등 작물별 PDF
├── src/                  # 실제 소스 코드가 들어가는 곳
│   ├── __init__.py       
│   ├── main.py           # 스트림릿 실행 파일 (UI 구성)
│   ├── agents.py         # 랭체인 에이전트 및 체인 설정
│   ├── tools/            # 우리가 만들 '커스텀 툴' 모음
│   │   ├── __init__.py
│   │   ├── weather_tool.py   # 기상청 API 연결 함수
│   │   ├── price_tool.py     # KAMIS API 연결 함수
│   │   └── pest_tool.py      # 농사로 API 연결 함수
│   └── database/         # Vector DB 관련 코드
│       └── vector_store.py   # PDF를 벡터로 변환 및 검색하는 로직
├── .env                  # API 키 보관 (로컬 테스트용, 깃허브 업로드 금지!)
├── .gitignore            # 깃허브에 올리지 않을 파일 목록 (.env, __pycache__ 등)
├── requirements.txt      # 필요한 라이브러리 목록 (streamlit, langchain 등)
└── README.md             # 프로젝트 소개 및 실행 방법
