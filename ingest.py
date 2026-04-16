import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. 환경 변수 로드
load_dotenv()

def ingest_data():
    DATA_PATH = "./data"      # 영어 파일명이 담긴 폴더
    DB_PATH = "./chroma_db"    # 생성될 벡터 DB 경로

    if not os.path.exists(DATA_PATH):
        print(f"❌ '{DATA_PATH}' 폴더를 찾을 수 없습니다.")
        return

    all_documents = []
    
    # 2. 파일별로 루프를 돌며 메타데이터 삽입
    print("🚀 PDF 파일 스캔 및 메타데이터(작물명) 부여 시작...")
    pdf_files = [f for f in os.listdir(DATA_PATH) if f.endswith(".pdf")]
    
    for file_name in pdf_files:
        file_path = os.path.join(DATA_PATH, file_name)
        
        # 파일명에서 확장자를 뺀 것을 작물 코드로 사용 (예: apple.pdf -> apple)
        # main.py의 selected_crop(영어)과 일치하게 됩니다.
        crop_tag = os.path.splitext(file_name)[0]
        
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        # 각 페이지 객체에 'crop' 메타데이터 주입
        for doc in docs:
            doc.metadata["crop"] = crop_tag
            
        all_documents.extend(docs)
        print(f"✅ {file_name} 로드 완료 (Tag: {crop_tag})")

    # 3. 텍스트 분할 (메타데이터는 분할된 조각들에도 유지됩니다)
    print(f"\n✂️ 총 {len(all_documents)} 페이지를 작은 조각으로 나누는 중...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(all_documents)
    print(f"✅ 총 {len(texts)}개의 텍스트 조각 생성 완료!")

    # 4. 임베딩 및 저장
    print("🧠 OpenAI 임베딩 진행 중 (text-embedding-3-small)...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # 기존 DB가 있다면 덮어쓰거나 새로 생성
    vector_db = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=DB_PATH
    )
    
    print(f"\n✨ 모든 작업이 끝났습니다! '{DB_PATH}'에 저장된 데이터는 이제 작물별로 필터링이 가능합니다.")

if __name__ == "__main__":
    ingest_data()