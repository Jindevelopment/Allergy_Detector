#OCR 유틸리티 모듈
#OCR 기능 전담 모듈

import cv2
import pytesseract
import numpy as np
from PIL import Image

def ocr_image_with_opencv(image, lang="kor+eng"):
    """
    OpenCV + Tesseract OCR 전처리 및 텍스트 추출 함수
    image: PIL.Image 또는 파일 경로
    lang: OCR 언어 설정
    """
    # 이미지가 PIL 객체라면 OpenCV 형식으로 변환
    if isinstance(image, Image.Image):
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    elif isinstance(image, str):  # 파일 경로일 경우
        image = cv2.imread(image)

    # 전처리 (그레이스케일 + 이진화)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # OCR 수행
    config = "--psm 6"
    text = pytesseract.image_to_string(thresh, lang=lang, config=config)

    return text.strip()
