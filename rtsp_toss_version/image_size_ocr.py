"""
이미지 크기 조정 및 OCR 처리 모듈
"""

import cv2
import os
import base64
from typing import Optional

# LangChain 및 Gemini 관련 라이브러리로 교체
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough


# 포스터 정보 추출을 위한 프롬프트 템플릿 (기존과 동일하게 유지)
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

# --- Gemini 기반 분석을 위한 새로운 헬퍼 함수 ---

def create_multimodal_message(input_dict: dict) -> list[HumanMessage]:
    """이미지 경로와 텍스트 프롬프트를 받아 HumanMessage 객체를 생성합니다."""
    file_path = input_dict["image_path"]
    prompt = input_dict["prompt"]

    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension in [".jpg", ".jpeg"]:
        image_type = "jpeg"
    elif file_extension == ".png":
        image_type = "png"
    else:
        raise ValueError("지원하지 않는 파일 형식입니다. JPG, PNG만 가능합니다.")

    with open(file_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": f"data:image/{image_type};base64,{encoded_image}",
            },
        ]
    )
    return [message]


def perform_ocr(input_path, api_key=None):
    """이미지에서 OCR 수행하여 텍스트 추출 (Gemini API 사용)"""
    if not api_key:
        return "Gemini API 키가 필요합니다."

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, api_key=api_key)
        
        ocr_chain = RunnableLambda(create_multimodal_message) | llm | StrOutputParser()
        
        prompt_text = "이 이미지에서 보이는 모든 텍스트를 순서대로 정확하게 추출해줘."
        ocr_text = ocr_chain.invoke({"image_path": input_path, "prompt": prompt_text})
        
        return ocr_text

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"OCR 처리 중 예외 발생: {str(e)}")
        print(f"상세 에러: {error_detail}")
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

def _run_full_poster_analysis(file_path: str, api_key: str):
    """OCR과 포스터 정보 분석을 모두 수행하는 내부 헬퍼 함수 (Gemini 사용)"""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, api_key=api_key)

    # 1. OCR 체인
    ocr_chain = RunnableLambda(create_multimodal_message) | llm | StrOutputParser()

    # 2. JSON 추출 체인
    json_parser = JsonOutputParser()
    json_extraction_prompt = POSTER_ANALYSIS_PROMPT.partial(
        instructions=json_parser.get_format_instructions()
    )
    json_extraction_chain = json_extraction_prompt | llm | json_parser

    # 3. 두 체인을 연결하여 실행
    chain = (
        {"poster_context": ocr_chain}
        | json_extraction_chain
    )
    
    # OCR 텍스트를 별도로 얻기 위해 ocr_chain을 한 번 더 실행해야 하지만, 
    # 효율성을 위해 전체 텍스트를 먼저 받고 그것을 json chain에 넘겨줍니다.
    ocr_text = ocr_chain.invoke({"image_path": file_path, "prompt": "이 이미지의 텍스트를 모두 추출해줘."})
    if "오류 발생" in ocr_text:
         raise Exception(f"OCR 단계에서 오류 발생: {ocr_text}")

    poster_info = json_extraction_chain.invoke({"poster_context": ocr_text})

    return {"ocr_text": ocr_text, "poster_info": poster_info}


def poster_analysis_for_web(file_path: str, api_key: str):
    """포스터 이미지에서 구조화된 정보를 추출하는 함수 (Gemini 사용)"""
    result = {
        "success": False,
        "poster_info": {},
        "original_filename": os.path.basename(file_path),
    }

    try:
        analysis_result = _run_full_poster_analysis(file_path, api_key)
        result["poster_info"] = analysis_result["poster_info"]
        result["success"] = True
        return result

    except Exception as e:
        print(f"포스터 분석 중 오류 발생: {str(e)}")
        result["error"] = str(e)
        return result


def extract_poster_info_with_ocr(file_path: str, api_key: str):
    """OCR과 포스터 정보 추출을 함께 수행하는 함수 (Gemini 사용)"""
    result = {
        "success": False,
        "ocr_text": "",
        "poster_info": {},
        "original_filename": os.path.basename(file_path),
    }

    try:
        analysis_result = _run_full_poster_analysis(file_path, api_key)
        result["ocr_text"] = analysis_result["ocr_text"]
        result["poster_info"] = analysis_result["poster_info"]
        result["success"] = True
        return result

    except Exception as e:
        print(f"포스터 정보 추출 중 오류 발생: {str(e)}")
        result["error"] = str(e)
        return result


# 사용 예시
if __name__ == "__main__":
    # 이 스크립트를 직접 실행할 경우, 환경 변수에서 API 키를 가져오도록 설정
    # 예: export GOOGLE_API_KEY="your_api_key"
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        print("경고: GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
        # 필요하다면 아래에 직접 키를 입력하여 테스트할 수 있습니다.
        # gemini_api_key = "..."
    
    input_img = "poster.jpeg"  # 분석할 이미지 경로
    if not os.path.exists(input_img):
        print(f"테스트 이미지 파일을 찾을 수 없습니다: {input_img}")
    else:
        print(f"--- 테스트 시작: {input_img} ---")
        
        # 1. OCR만 테스트
        print("\n[1. OCR 단독 테스트]")
        ocr_result = ocr_only_for_web(input_img, gemini_api_key)
        if ocr_result["success"]:
            print("OCR 성공:")
            # 텍스트가 너무 길 수 있으므로 일부만 출력
            print(ocr_result["ocr_text"][:300] + "...")
        else:
            print("OCR 실패:", ocr_result)

        # 2. 포스터 분석만 테스트
        print("\n[2. 포스터 분석 단독 테스트]")
        analysis_result = poster_analysis_for_web(input_img, gemini_api_key)
        if analysis_result["success"]:
            import json
            print("분석 성공:")
            print(json.dumps(analysis_result["poster_info"], indent=2, ensure_ascii=False))
        else:
            print("분석 실패:", analysis_result)

        # 3. OCR + 분석 함께 테스트
        print("\n[3. OCR + 포스터 분석 통합 테스트]")
        full_result = extract_poster_info_with_ocr(input_img, gemini_api_key)
        if full_result["success"]:
            print("통합 분석 성공:")
            print("--- OCR 결과 ---")
            print(full_result["ocr_text"][:300] + "...")
            print("\n--- AI 분석 결과 ---")
            print(json.dumps(full_result["poster_info"], indent=2, ensure_ascii=False))
        else:
            print("통합 분석 실패:", full_result)
