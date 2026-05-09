import requests
import os
import xml.etree.ElementTree as ET
from datetime import datetime

def download_latest_pest_pdf(save_path="./data/latest_pest_info.pdf"):
    """
    농사로 API를 통해 최신 병해충 발생정보 PDF를 다운로드합니다.
    """
    url = "http://api.nongsaro.go.kr/service/dbyhsCccrrncInfo/dbyhsCccrrncInfoList"
    api_key = "20260413Q3XSJWMQYU1TRV8QFLULTA"
    params = {"apiKey": api_key}

    try:
        # 1. API 호출하여 목록 및 파일 경로 가져오기
        response = requests.get(url, params=params, timeout=10)
        response.encoding = 'utf-8'
        
        if "<resultCode>00</resultCode>" not in response.text:
            return {"success": False, "error": "API 호출 실패"}

        root = ET.fromstring(response.content)
        # 가장 첫 번째 item이 최신 공보임
        item = root.find('.//item')
        
        if item is None:
            return {"success": False, "error": "데이터가 없습니다."}

        file_url = item.find('downFile').text if item.find('downFile') is not None else ""
        file_name = item.find('rtnOrginlFileNm').text if item.find('rtnOrginlFileNm') is not None else "pest_info.pdf"
        
        if not file_url:
            return {"success": False, "error": "다운로드 경로를 찾을 수 없습니다."}

        # 2. PDF 다운로드 실행
        print(f"📂 최신 파일 다운로드 중: {file_name}")
        pdf_res = requests.get(file_url, timeout=30)
        
        # 저장 폴더 생성
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, "wb") as f:
            f.write(pdf_res.content)
            
        return {
            "success": True, 
            "file_name": file_name, 
            "save_path": save_path,
            "title": item.find('cntntsSj').text
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    result = download_latest_pest_pdf()
    print(result)