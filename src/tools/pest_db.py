# Pest_db.py
# 2026년 제4호(4.1~4.30) 병해충 발생정보 바탕으로 작성 [cite: 46]

PEST_ALERTS = {
    "사과": {
        "status": "예보",
        "items": ["과수화상병", "과수가지검은마름병", "검은별무늬병", "나무좀류", "사과응애"],
        "content": "개화기 방제(예측시스템 위험 시 24시간 내 약제 살포) 및 석회보르도액 살포. 나무좀 유인트랩 관찰 필요.",
        "link": "https://www.nongsaro.go.kr/portal/ps/psb/psbk/kidofcomdtyDtl.ps?menuId=PS00067"
    },
    "벼": {
        "status": "예보",
        "items": ["키다리병", "깨씨무늬병", "벼잎선충", "모잘록", "뜸모"],
        "content": "충실한 종자 선별(염수선) 및 온탕소독(60℃, 10분). 못자리 온도 차에 의한 모잘록/뜸모 관리 주의.",
        "link": "https://www.nongsaro.go.kr/portal/ps/psb/psbk/kidofcomdtyDtl.ps?menuId=PS00067"
    },
    "보리/밀": {
        "status": "예보",
        "items": ["맥류 붉은곰팡이병"],
        "content": "출수기 전후 강우 시 발생 증가하므로 예방적 약제 살포 및 배수로 정비.",
        "link": "https://www.nongsaro.go.kr/portal/ps/psb/psbk/kidofcomdtyDtl.ps?menuId=PS00067"
    },
    "마늘/양파": {
        "status": "예보",
        "items": ["노균병", "잎마름병", "흑색썩음균핵병", "고자리파리", "뿌리응애"],
        "content": "기온 15℃ 및 다습 시 노균병 급증 주의. 병든 포기 즉시 제거 및 등록 약제 토양 관주 처리.",
        "link": "https://www.nongsaro.go.kr/portal/ps/psb/psbk/kidofcomdtyDtl.ps?menuId=PS00067"
    },
    "딸기": {
        "status": "예보",
        "items": ["잿빛곰팡이병", "흰가루병"],
        "content": "시설 내 환기로 습도를 낮추고 보온 유의. 발생 초기 계통이 다른 약제로 교호 살포.",
        "link": "https://www.nongsaro.go.kr/portal/ps/psb/psbk/kidofcomdtyDtl.ps?menuId=PS00067"
    },
    "토마토": {
        "status": "예보",
        "items": ["토마토뿔나방", "토마토궤양병", "토마토반점위조바이러스(TSWV)", "토마토황화잎말림바이러스(TYLCV)"],
        "content": "유충의 잎/과실 침입 방지. 매개충(총채벌레, 담배가루이) 방충망 설치 및 정식 초기 예찰 강화.",
        "link": "https://www.nongsaro.go.kr/portal/ps/psb/psbk/kidofcomdtyDtl.ps?menuId=PS00067"
    },
    "배": {
        "status": "예보",
        "items": ["과수화상병", "검은별무늬병", "사과응애"],
        "content": "꽃눈 발아 직후 동제 살포. 감염위험 시간 정보(경고값 2 이상)에 따라 적기 방제 실시.",
        "link": "https://www.nongsaro.go.kr/portal/ps/psb/psbk/kidofcomdtyDtl.ps?menuId=PS00067"
    },
    "복숭아": {
        "status": "예보",
        "items": ["나무좀류", "복숭아씨살이좀벌"],
        "content": "어린 과실(1~2cm) 시기에 성충 산란 관찰 및 5~7일 간격 2~3회 집중 방제.",
        "link": "https://www.nongsaro.go.kr/portal/ps/psb/psbk/kidofcomdtyDtl.ps?menuId=PS00067"
    }
}