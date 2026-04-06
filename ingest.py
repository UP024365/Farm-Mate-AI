import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
# 아래 부분이 최신 라이브러리 규격에 맞게 수정되었습니다.
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. API 키 로드 (.env 파일에 OPENAI_API_KEY가 있어야 함)
load_dotenv()

def ingest_data():
    # 데이터 경로 설정
    DATA_PATH = "./data"
    DB_PATH = "./chroma_db"

    # 2. PDF 로드 (DirectoryLoader로 폴더 내 모든 pdf 한꺼번에 읽기)
    print("🚀 PDF 파일들을 읽어들이는 중입니다... (용량이 커서 시간이 걸릴 수 있어요)")
    # 300MB가 넘는 대용량 파일이므로 로딩에 시간이 좀 걸립니다.
    loader = DirectoryLoader(DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    print(f"✅ 총 {len(documents)} 페이지 로드 완료!")

    # 3. 텍스트 쪼개기 (Chunking)
    # 한글 성능을 위해 chunk_size 1000, overlap 200 정도로 설정합니다.
    print("✂️ 텍스트를 작은 조각으로 나누는 중...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    print(f"✅ 총 {len(texts)}개의 텍스트 조각 생성 완료!")

    # 4. 임베딩 및 벡터 DB 저장
    print("🧠 OpenAI 임베딩 모델로 벡터화 진행 중... (토큰 소모 발생)")
    # 가성비가 가장 좋은 최신 임베딩 모델을 사용합니다.
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # DB 생성 및 로컬 저장
    vector_db = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=DB_PATH
    )
    
    print(f"✨ 모든 작업이 완료되었습니다! '{DB_PATH}' 폴더를 확인하세요.")

if __name__ == "__main__":
    ingest_data()