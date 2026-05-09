import openai
import datetime
import os
import re
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv

load_dotenv()
def summarize_pdf_to_db(pdf_path="./data/latest_pest_info.pdf"):
    """
    최신 병해충 PDF를 분석하여 10대 작물에 대한 PEST_ALERTS 딕셔너리를 생성합니다.
    """
    print(f"🔍 PDF 분석 시작: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ 오류: 파일을 찾을 수 없습니다. ({pdf_path})")
        return None

    try:
        # 1. PDF 텍스트 추출 (앞부분 5페이지 위주)
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        full_text = "\n".join([page.page_content for page in pages[:5]])

        # 2. GPT API 호출을 위한 설정
        # API 키는 환경 변수나 main.py의 설정을 따르는 것이 좋습니다.
        api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=api_key)
        
        target_crops = ["사과", "마늘", "양파", "복숭아", "고추", "감자", "무", "딸기", "고구마", "토마토"]
        
        prompt = f"""
        너는 농촌진흥청의 공보 데이터를 정확하게 추출하는 데이터 분석가야. 
        제공된 PDF 본문 내용을 바탕으로 우리 서비스의 **10개 주요 작물**에 대한 실시간 병해충 정보를 요약해.

        [대상 작물 리스트]
        {', '.join(target_crops)}

        [엄격 요약 규칙 - 반드시 준수]
        1. **존재 기반 추출**: 제공된 PDF 본문에 해당 작물 명칭이 **명시적으로 언급된 경우에만** 딕셔너리에 포함해. 
        2. **지식 활용 금지**: PDF에 없는 내용을 네 지식으로 지어내거나 추측해서 채우지 마. 언급되지 않은 작물은 결과 리스트에서 완전히 제외해.
        3. **내용 근거**: 'content'(방제 요령)는 반드시 PDF 본문에 적힌 대응 지침을 바탕으로 요약해.
        4. **필드 구성**: 
           - status: PDF의 위험도에 따라 '예보', '주의보', '경보' 중 선택.
           - items: PDF에서 언급된 해당 작물의 병해충 명칭들.
           - content: PDF 본문의 방제 요령을 핵심만 요약.
           - link: "https://www.nongsaro.go.kr/portal/ps/psb/psbk/kidofcomdtyDtl.ps?menuId=PS00067"
        5. **출력 형식**: 다른 설명 없이 `PEST_ALERTS = {{ ... }}` 형식의 파이썬 코드만 출력해.

        [분석할 PDF 내용]
        {full_text}
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 농업 병해충 전문가이자 파이썬 개발자야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        generated_code = response.choices[0].message.content.strip()
        
        # 만약 GPT가 ```python ... ``` 형태로 줬을 경우를 대비한 정규식 추출
        code_match = re.search(r"PEST_ALERTS\s*=\s*\{.*\}", generated_code, re.DOTALL)
        if code_match:
            generated_code = code_match.group(0)

        # 3. 파일 저장 (날짜 주석 포함)
        update_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db_content = f'# Last Updated: {update_date}\n\n{generated_code}\n'
        
        db_path = "src/tools/pest_db.py"
        with open(db_path, "w", encoding="utf-8") as f:
            f.write(db_content)
            
        print(f"✅ 업데이트 성공! 파일 저장 완료: {db_path}")
        return update_date

    except Exception as e:
        print(f"❌ 요약 중 오류 발생: {e}")
        return None

# --- 파일 실행 시 동작하는 부분 ---
if __name__ == "__main__":
    # 테스트 실행
    summarize_pdf_to_db()