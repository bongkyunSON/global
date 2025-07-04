"""
이미지 크기 조정 및 OCR 처리 모듈
"""

import cv2
import os
import base64
import requests
from typing import Optional

# poster_chain 기능을 위한 추가 import
from langchain_upstage import ChatUpstage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate

# 포스터 정보 추출을 위한 프롬프트 템플릿
POSTER_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """
    ### 역할 ###
    너는 해당 포스터의 내용을 보고 정보를 추출해야합니다.

    **분야** 같은 경우는 해당 리스트에서 최대 5개를 추출하고 꼭 굳이 5개가 아니여도돼
    **좌장, 패널** 같은 경우는 출력할때 이름 뿐만 아니라 소속 기관도 함께 출력해야해

    ### 입력 ###
    {poster_context}

    
    ### 포스터 정보 ###
    1. 세미나 일시: 
    2. 제목:
    3. 주최 장소:  
    4. 주최(국회의원):
    5. 주최(그외):
    6. 주관 및 후원:
    7. 분야(최대 5개선택):
     [경제, 인권, 정치, 사법, 보훈, 금융, 재정, 교육, 외교, 통일, 국방, 선거, 체육, 산업, 보건, 복지, 환경, 노동, 국토, 교통, 기타, 지자체, 공정거래, 과학기술, 공공안전, 문화관광, 해양수산, 여성가족, 정보방송통신, 농림축산식품, 중소거업 벤처]

    8. 키워드:
    9. 좌장:
    10. 패널:


    ### 출력 형식 ###
    Instructions: {instructions}

    """
)


def perform_ocr(input_path, api_key=None):
    """이미지에서 OCR 수행하여 텍스트 추출 (Upstage API 사용)"""
    # Check file extension
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        print("지원하지 않는 파일 형식입니다:", ext)
        return "지원하지 않는 파일 형식입니다."

    # 이미지 존재 확인
    if not os.path.exists(input_path):
        print("이미지 파일을 찾을 수 없습니다:", input_path)
        return "이미지 파일을 찾을 수 없습니다."

    # API 키 확인
    if not api_key:
        return "OCR API 키가 필요합니다."

    try:
        url = "https://api.upstage.ai/v1/document-digitization"
        headers = {"Authorization": f"Bearer {api_key}"}

        files = {"document": open(input_path, "rb")}
        data = {"model": "ocr"}
        response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            # Upstage API 응답에서 텍스트 추출
            if "text" in result:
                return result["text"]
            elif "content" in result:
                return result["content"]
            else:
                return str(result)
        else:
            return f"OCR API 오류: {response.status_code} - {response.text}"

    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {str(e)}")
        return f"OCR 처리 중 오류 발생: {str(e)}"


def resize_image(input_path, output_path=None, width=400, api_key=None):
    """이미지 크기 조정"""
    # Check file extension
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        print("지원하지 않는 파일 형식입니다:", ext)
        return None

    # width가 None이면 OCR만 수행
    if width is None:
        return perform_ocr(input_path, api_key)

    # Load image
    image = cv2.imread(input_path)
    if image is None:
        print("이미지를 불러올 수 없습니다:", input_path)
        return None

    # 원본 사이즈 가져오기
    h, w = image.shape[:2]
    if w == 0 or h == 0:
        print("이미지의 가로 또는 세로 길이가 잘못되었습니다.")
        return None

    # 비율에 맞게 높이 조정
    ratio = width / w
    new_height = int(h * ratio)
    resized_image = cv2.resize(image, (width, new_height), interpolation=cv2.INTER_AREA)

    # 출력 파일명 지정
    if output_path is None:
        basename, ext = os.path.splitext(os.path.basename(input_path))
        output_path = f"{basename}_resized{ext}"

    # 이미지 저장
    success = cv2.imwrite(output_path, resized_image)
    if success:
        print(f"이미지 저장 완료: {output_path} (가로: {width}, 세로: {new_height})")
        return output_path
    else:
        print("이미지 저장에 실패하였습니다.")
        return None


# 웹 API용 함수들
def resize_image_only_for_web(file_path: str, width: int = 400):
    """이미지 크기 조정만 수행하는 함수"""
    result = {
        "success": False,
        "resized_image": "",
        "original_filename": os.path.basename(file_path),
        "width": width,
        "height": 0,
    }

    try:
        # 이미지 로드 및 리사이징
        image = cv2.imread(file_path)
        if image is not None:
            h, w = image.shape[:2]
            ratio = width / w
            new_height = int(h * ratio)
            result["height"] = new_height

            resized_image = cv2.resize(
                image, (width, new_height), interpolation=cv2.INTER_AREA
            )

            # 임시 출력 파일 생성
            basename, ext = os.path.splitext(os.path.basename(file_path))
            output_path = f"temp_{basename}_resized{ext}"

            # 이미지 저장
            cv2.imwrite(output_path, resized_image)

            # 이미지를 base64로 인코딩
            with open(output_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")
                result["resized_image"] = base64_image

            # 임시 파일 삭제
            if os.path.exists(output_path):
                os.remove(output_path)
        else:
            result["error"] = "이미지를 불러올 수 없습니다."
            return result

        result["success"] = True
        return result

    except Exception as e:
        print(f"이미지 크기 조정 중 오류 발생: {str(e)}")
        result["error"] = str(e)
        return result


def ocr_only_for_web(file_path: str, api_key: str):
    """OCR만 수행하는 함수"""
    result = {
        "success": False,
        "ocr_text": "",
        "original_filename": os.path.basename(file_path),
    }

    try:
        # OCR 처리
        if api_key:
            ocr_text = perform_ocr(file_path, api_key)
            if (
                ocr_text
                and "오류" not in ocr_text
                and "찾을 수 없습니다" not in ocr_text
                and "API 키가 필요합니다" not in ocr_text
            ):
                result["ocr_text"] = ocr_text
                result["success"] = True
            else:
                result["ocr_text"] = ocr_text  # 오류 메시지도 전달
                result["success"] = False
        else:
            result["ocr_text"] = "OCR API 키가 필요합니다."
            result["success"] = False

        return result

    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {str(e)}")
        result["error"] = str(e)
        return result


def process_image_for_web(
    file_path: str, width: Optional[int] = 400, api_key: Optional[str] = None
):
    """웹 API를 위한 이미지 처리 함수"""
    result = {
        "success": False,
        "ocr_text": "",
        "resized_image": "",
        "original_filename": os.path.basename(file_path),
        "width": width,
        "height": 0,
    }

    try:
        # OCR 처리
        if api_key:
            ocr_text = perform_ocr(file_path, api_key)
            if (
                ocr_text
                and "오류" not in ocr_text
                and "찾을 수 없습니다" not in ocr_text
                and "API 키가 필요합니다" not in ocr_text
            ):
                result["ocr_text"] = ocr_text
            else:
                result["ocr_text"] = ocr_text  # 오류 메시지도 전달
        else:
            result["ocr_text"] = "OCR API 키가 필요합니다."

        # 이미지 리사이징
        if width:
            # 임시 출력 파일 생성
            basename, ext = os.path.splitext(os.path.basename(file_path))
            output_path = f"temp_{basename}_resized{ext}"

            # 이미지 로드 및 리사이징
            image = cv2.imread(file_path)
            if image is not None:
                h, w = image.shape[:2]
                ratio = width / w
                new_height = int(h * ratio)
                result["height"] = new_height

                resized_image = cv2.resize(
                    image, (width, new_height), interpolation=cv2.INTER_AREA
                )

                # 이미지 저장
                cv2.imwrite(output_path, resized_image)

                # 이미지를 base64로 인코딩
                with open(output_path, "rb") as img_file:
                    base64_image = base64.b64encode(img_file.read()).decode("utf-8")
                    result["resized_image"] = base64_image

                # 임시 파일 삭제
                if os.path.exists(output_path):
                    os.remove(output_path)

        result["success"] = True
        return result

    except Exception as e:
        print(f"이미지 처리 중 오류 발생: {str(e)}")
        result["error"] = str(e)
        return result


def poster_analysis_for_web(file_path: str, api_key: str):
    """포스터 이미지에서 구조화된 정보를 추출하는 함수"""
    result = {
        "success": False,
        "poster_info": {},
        "original_filename": os.path.basename(file_path),
    }

    try:
        # 먼저 OCR로 텍스트 추출
        ocr_text = perform_ocr(file_path, api_key)
        
        if not ocr_text or "오류" in ocr_text or "찾을 수 없습니다" in ocr_text:
            result["error"] = "OCR 처리에 실패했습니다."
            return result

        # LangChain을 사용하여 포스터 정보 분석
        json_parser = JsonOutputParser()
        llm = ChatUpstage(api_key=api_key, model="solar-pro2-preview")
        template = POSTER_ANALYSIS_PROMPT.partial(instructions=json_parser.get_format_instructions())

        chain = (
            {
                "poster_context": RunnablePassthrough(),
            }
            | template
            | llm
            | json_parser
        )

        poster_info = chain.invoke({"poster_context": ocr_text})
        
        result["poster_info"] = poster_info
        result["success"] = True
        return result

    except Exception as e:
        print(f"포스터 분석 중 오류 발생: {str(e)}")
        result["error"] = str(e)
        return result


def extract_poster_info_with_ocr(file_path: str, api_key: str):
    """OCR과 포스터 정보 추출을 함께 수행하는 함수"""
    result = {
        "success": False,
        "ocr_text": "",
        "poster_info": {},
        "original_filename": os.path.basename(file_path),
    }

    try:
        # OCR 처리
        ocr_text = perform_ocr(file_path, api_key)
        
        if not ocr_text or "오류" in ocr_text or "찾을 수 없습니다" in ocr_text:
            result["ocr_text"] = ocr_text or "OCR 처리 실패"
            result["error"] = "OCR 처리에 실패했습니다."
            return result
        
        result["ocr_text"] = ocr_text

        # 포스터 정보 분석
        json_parser = JsonOutputParser()
        llm = ChatUpstage(api_key=api_key, model="solar-pro2-preview")
        template = POSTER_ANALYSIS_PROMPT.partial(instructions=json_parser.get_format_instructions())

        chain = (
            {
                "poster_context": RunnablePassthrough(),
            }
            | template
            | llm
            | json_parser
        )

        poster_info = chain.invoke({"poster_context": ocr_text})
        
        result["poster_info"] = poster_info
        result["success"] = True
        return result

    except Exception as e:
        print(f"포스터 정보 추출 중 오류 발생: {str(e)}")
        result["error"] = str(e)
        return result


# 사용 예시
if __name__ == "__main__":
    input_img = "test.jpg"  # 입력 이미지 경로

    # OCR 수행
    ocr_text = perform_ocr(input_img)
    print("추출된 텍스트:")
    print(ocr_text)

    # 이미지 리사이징
    output_path = resize_image(input_img, width=400)
    print(f"리사이징된 이미지 저장 경로: {output_path}")
