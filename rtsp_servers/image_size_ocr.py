import cv2
import os
from paddleocr import PaddleOCR


def resize_image(input_path, output_path=None, width=400):
    # Check file extension
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        print("지원하지 않는 파일 형식입니다:", ext)
        return

    # Load image
    image = cv2.imread(input_path)
    if image is None:
        print("이미지를 불러올 수 없습니다:", input_path)
        return
    
    total_text = ""
    ocr = PaddleOCR(use_angle_cls=True, lang='korean')
    result = ocr.ocr(input_path, cls=True)
    for line in result:
        for text_info in line:
            total_text += text_info[1][0] + "\n"
        return total_text
    # 원본 사이즈 가져오기
    h, w = image.shape[:2]
    if w == 0 or h == 0:
        print("이미지의 가로 또는 세로 길이가 잘못되었습니다.")
        return

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
    else:
        print("이미지 저장에 실패하였습니다.")

# 사용 예시
# if __name__ == "__main__":
#     input_img = "/Users/sbk/global/rtsp_servers/test/135667_홈플러스 사태로 본 투기자본 MBK 규제 방안 마련 토론회.jpg"  # 또는 png 확장자 가능
#     print(resize_image(input_img))