import streamlit as st
import os
from dotenv import load_dotenv

# 1. 필수 라이브러리 임포트 (경로 에러 방지 처리)
try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import Chroma
    # 최신 버전과 구버전 경로를 모두 체크합니다.
    try:
        from langchain.chains import RetrievalQA
    except ImportError:
        from langchain.chains.retrieval_qa.base import RetrievalQA
except ImportError as e:
    st.error(f"라이브러리 로드 실패: {e}\n터미널에서 패키지 재설치가 필요합니다.")
    st.stop()

# 2. 환경 변수 및 페이지 설정
load_dotenv()
st.set_page_config(page_title="농사메이트 AI", page_icon="🌱", layout="centered")

# 간단한 디자인 적용
st.markdown("""
    <style>
    .stApp { background-color: #f9fbf9; }
    .stChatMessage { border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 농사메이트: 10대 작물 재배 AI")
st.caption("2,800페이지의 농사 지식 데이터를 바탕으로 답변합니다.")
st.divider()

# 3. 벡터 DB 로드 함수 (캐싱 적용)
@st.cache_resource
def init_db():
    db_path = "./chroma_db"
    if not os.path.exists(db_path):
        st.error(f"❌ '{db_path}' 폴더가 없습니다! 'python ingest.py'를 먼저 실행해 주세요.")
        st.stop()
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(persist_directory=db_path, embedding_function=embeddings)

vector_db = init_db()

# 4. RAG 체인 생성
def get_qa_robot():
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

qa_robot = get_qa_robot()

# 5. 채팅 인터페이스
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 메시지 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 질문 입력 및 답변 처리
if prompt := st.chat_input("재배법이나 병해충에 대해 물어보세요!"):
    # 사용자 질문 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("전문 문서를 분석 중입니다..."):
            try:
                # 질문 던지기
                response = qa_robot.invoke({"query": prompt})
                answer = response["result"]
                source_docs = response["source_documents"]

                # 결과 출력
                st.markdown(answer)
                
                # 참고 문헌 표시
                if source_docs:
                    with st.expander("📍 답변의 근거 (참고 문서)"):
                        # 중복 제거 후 파일명만 추출
                        sources = {os.path.basename(doc.metadata.get('source', '알 수 없음')) for doc in source_docs}
                        for s in sources:
                            st.write(f"- {s}")

                # 답변 저장
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error(f"답변 중 오류가 발생했습니다: {e}")