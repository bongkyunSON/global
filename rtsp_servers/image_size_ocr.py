import cv2
import os
import base64
from paddleocr import PaddleOCR
from typing import Optional


def perform_ocr(input_path):
    """이미지에서 OCR 수행하여 텍스트 추출"""
    # Check file extension
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        print("지원하지 않는 파일 형식입니다:", ext)
        return "지원하지 않는 파일 형식입니다."

    # 이미지 존재 확인
    if not os.path.exists(input_path):
        print("이미지 파일을 찾을 수 없습니다:", input_path)
        return "이미지 파일을 찾을 수 없습니다."
    
    try:
        total_text = ""
        ocr = PaddleOCR(use_angle_cls=True, lang='korean')
        result = ocr.ocr(input_path, cls=True)
        
        if result:
            for line in result:
                for text_info in line:
                    total_text += text_info[1][0] + "\n"
            
            return total_text if total_text else "추출된 텍스트가 없습니다."
        else:
            return "추출된 텍스트가 없습니다."
    except Exception as e:
        print(f"OCR 처리 중 오류 발생: {str(e)}")
        return f"OCR 처리 중 오류 발생: {str(e)}"


def resize_image(input_path, output_path=None, width=400):
    """이미지 크기 조정"""
    # Check file extension
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        print("지원하지 않는 파일 형식입니다:", ext)
        return None
    
    # width가 None이면 OCR만 수행
    if width is None:
        return perform_ocr(input_path)

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
def process_image_for_web(file_path: str, width: Optional[int] = 400):
    """웹 API를 위한 이미지 처리 함수"""
    result = {
        "success": False,
        "ocr_text": "",
        "resized_image": "",
        "original_filename": os.path.basename(file_path),
        "width": width,
        "height": 0
    }
    
    try:
        # OCR 처리
        ocr_text = perform_ocr(file_path)
        if ocr_text and "오류" not in ocr_text and "찾을 수 없습니다" not in ocr_text:
            result["ocr_text"] = ocr_text
        
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
                
                resized_image = cv2.resize(image, (width, new_height), interpolation=cv2.INTER_AREA)
                
                # 이미지 저장
                cv2.imwrite(output_path, resized_image)
                
                # 이미지를 base64로 인코딩
                with open(output_path, "rb") as img_file:
                    base64_image = base64.b64encode(img_file.read()).decode('utf-8')
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