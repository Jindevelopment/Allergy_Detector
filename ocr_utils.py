# OCR 유틸리티 모듈 (고급 전처리 포함)
# 웹페이지용 OCR 기능 전담 모듈

import cv2
import pytesseract
import numpy as np
from PIL import Image
import re
import easyocr
import time
import torch

def check_gpu_availability():
    """
    맥북 GPU 가용성 확인 함수
    """
    try:
        # MPS (Metal Performance Shaders) 확인
        if torch.backends.mps.is_available():
            print("✅ MPS(Metal Performance Shaders) 사용 가능!")
            return True
        elif torch.cuda.is_available():
            print("✅ CUDA GPU 사용 가능!")
            return True
        else:
            print("❌ GPU 사용 불가 - CPU 모드로 실행")
            return False
    except Exception as e:
        print(f"GPU 확인 중 오류: {e}")
        return False

def apply_advanced_preprocessing(image):
    """
    고급 이미지 전처리 함수
    """
    # 1️⃣ 그레이스케일 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 2️⃣ 다양한 Blur 방법들 적용
    # Gaussian Blur
    gaussian_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Median Blur (노이즈 제거에 효과적)
    median_blur = cv2.medianBlur(gray, 5)
    
    # Bilateral Filter (엣지 보존하면서 노이즈 제거)
    bilateral_blur = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # 3️⃣ 히스토그램 균등화
    equalized = cv2.equalizeHist(gray)
    
    # 4️⃣ CLAHE (적응형 히스토그램 균등화)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    clahe_applied = clahe.apply(gray)
    
    # 5️⃣ 채도 조절 (Saturation Adjustment)
    # HSV 색상 공간으로 변환
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # 채도 증가 (1.5배)
    hsv_image[:, :, 1] = np.clip(hsv_image[:, :, 1] * 1.5, 0, 255)
    # 다시 BGR로 변환
    saturated_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
    saturated_gray = cv2.cvtColor(saturated_image, cv2.COLOR_BGR2GRAY)
    
    return {
        'original': gray,
        'gaussian_blur': gaussian_blur,
        'median_blur': median_blur,
        'bilateral_blur': bilateral_blur,
        'equalized': equalized,
        'clahe': clahe_applied,
        'saturated': saturated_gray
    }

def apply_morphology_operations(image):
    """
    모폴로지 연산 적용 (침식, 팽창, 닫힘, 열림)
    """
    # 커널 생성
    kernel = np.ones((3, 3), np.uint8)
    
    # 침식 연산 (텍스트를 얇게)
    erosion = cv2.erode(image, kernel, iterations=1)
    
    # 팽창 연산 (텍스트를 두껍게)
    dilation = cv2.dilate(image, kernel, iterations=1)
    
    # 닫힘 연산 (텍스트 내부 구멍 메우기)
    closing = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    
    # 열림 연산 (작은 노이즈 제거)
    opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    
    return {
        'erosion': erosion,
        'dilation': dilation,
        'closing': closing,
        'opening': opening
    }

def apply_multiple_thresholding(image):
    """
    다양한 이진화 방법 적용
    """
    # OTSU 이진화
    _, thresh_otsu = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 적응형 이진화 - Gaussian
    thresh_adapt_gaussian = cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # 적응형 이진화 - Mean
    thresh_adapt_mean = cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # 임계값 이진화
    _, thresh_binary = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY)
    
    return {
        'otsu': thresh_otsu,
        'adapt_gaussian': thresh_adapt_gaussian,
        'adapt_mean': thresh_adapt_mean,
        'binary': thresh_binary
    }

def ocr_image_with_opencv(image, lang="kor+eng", fast_mode=True):
    """
    OpenCV + Tesseract OCR 최적화 함수 (다양한 전처리 방법 적용)
    image: PIL.Image 또는 파일 경로
    lang: OCR 언어 설정
    fast_mode: 빠른 모드 (기본값: True)
    """
    # 이미지가 PIL 객체라면 OpenCV 형식으로 변환
    if isinstance(image, Image.Image):
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    elif isinstance(image, str):  # 파일 경로일 경우
        image = cv2.imread(image)
        if image is None:
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image}")

    # 이미지 크기 조정 (적당한 크기로)
    height, width = image.shape[:2]
    if width > 1200 or height > 1200:
        scale = min(1200/width, 1200/height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

    if fast_mode:
        # 🚀 빠른 모드: 기본 전처리만
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        config = "--psm 3 --oem 3 -c preserve_interword_spaces=1"
        
    else:
        # 🎯 정밀 모드: 다양한 전처리 방법 시도
        # 고급 전처리 적용
        processed_images = apply_advanced_preprocessing(image)
        
        # 가장 효과적인 이미지 선택 (CLAHE 적용된 이미지)
        best_image = processed_images['clahe']
        
        # 모폴로지 연산 적용
        morph_images = apply_morphology_operations(best_image)
        
        # 가장 효과적인 모폴로지 결과 선택 (닫힘 연산)
        best_morph = morph_images['closing']
        
        # 다양한 이진화 방법 적용
        thresh_images = apply_multiple_thresholding(best_morph)
        
        # 가장 효과적인 이진화 결과 선택 (적응형 Gaussian)
        thresh = thresh_images['adapt_gaussian']
        
        # 추가 모폴로지 연산으로 텍스트 영역 강화
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        config = "--psm 6 --oem 3 -c preserve_interword_spaces=1 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz가-힣():.,()[]{}"

    # OCR 수행 (한국어 우선)
    text = pytesseract.image_to_string(thresh, lang=lang, config=config)
    return text.strip()

def ocr_with_easyocr(image_path_or_object, lang=['ko', 'en']):
    """
    EasyOCR을 사용한 고성능 OCR 함수 (한국어 특화 - 맥북 GPU 지원)
    """
    try:
        # 맥북 M1/M2/M3 칩에서 MPS(Metal Performance Shaders) 사용
        if torch.backends.mps.is_available():
            print("🚀 맥북 GPU(MPS) 가속 사용 중...")
            reader = easyocr.Reader(lang, gpu=True)  # MPS 사용
        else:
            print("💻 CPU 모드로 실행 중...")
            reader = easyocr.Reader(lang, gpu=False)
        
        # 이미지 읽기
        if isinstance(image_path_or_object, str):
            image = cv2.imread(image_path_or_object)
        else:
            # PIL Image를 numpy array로 변환
            image = np.array(image_path_or_object)
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # EasyOCR로 텍스트 추출
        results = reader.readtext(image)
        
        # 결과를 텍스트로 변환
        extracted_text = ""
        for (bbox, text, confidence) in results:
            if confidence > 0.5:  # 신뢰도 50% 이상만 사용
                extracted_text += text + " "
        
        return extracted_text.strip()
    
    except Exception as e:
        print(f"EasyOCR 오류: {e}")
        return ""

def ocr_with_enhanced_preprocessing(image_path_or_object, use_easyocr=True):
    """
    향상된 전처리 + 고성능 OCR 함수 (웹페이지용)
    """
    try:
        # 이미지 읽기
        if isinstance(image_path_or_object, str):
            image = cv2.imread(image_path_or_object)
        else:
            image = np.array(image_path_or_object)
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        if image is None:
            return ""
        
        # 고급 전처리 적용
        processed_images = apply_advanced_preprocessing(image)
        
        # 여러 전처리 결과 중 가장 좋은 것들 시도
        best_images = [
            processed_images['clahe'],  # CLAHE 적용
            processed_images['equalized'],  # 히스토그램 균등화
            processed_images['bilateral_blur'],  # Bilateral Filter
            processed_images['original']  # 원본
        ]
        
        all_texts = []
        
        if use_easyocr:
            # EasyOCR 사용 (맥북 GPU 지원)
            try:
                if torch.backends.mps.is_available():
                    reader = easyocr.Reader(['ko', 'en'], gpu=True)
                else:
                    reader = easyocr.Reader(['ko', 'en'], gpu=False)
                
                for img in best_images:
                    try:
                        results = reader.readtext(img)
                        text = ""
                        for (bbox, detected_text, confidence) in results:
                            if confidence > 0.3:  # 낮은 임계값으로 더 많은 텍스트 캡처
                                text += detected_text + " "
                        if text.strip():
                            all_texts.append(text.strip())
                    except:
                        continue
            except Exception as e:
                print(f"EasyOCR 초기화 실패: {e}")
                use_easyocr = False
        
        if not use_easyocr:
            # Tesseract 사용
            for img in best_images:
                try:
                    # 모폴로지 연산 적용
                    morph_images = apply_morphology_operations(img)
                    best_morph = morph_images['closing']
                    
                    # 이진화
                    thresh_images = apply_multiple_thresholding(best_morph)
                    thresh = thresh_images['adapt_gaussian']
                    
                    # OCR 수행
                    text = pytesseract.image_to_string(thresh, lang='kor+eng', config='--psm 6 --oem 3')
                    if text.strip():
                        all_texts.append(text.strip())
                except:
                    continue
        
        # 모든 결과를 합치고 중복 제거
        combined_text = " ".join(all_texts)
        return combined_text.strip()
    
    except Exception as e:
        print(f"향상된 OCR 오류: {e}")
        return ""

def extract_text_from_image(image_path_or_object, use_easyocr=True, fast_mode=False):
    """
    웹페이지용 메인 OCR 함수
    """
    try:
        start_time = time.time()
        
        if use_easyocr:
            # 🚀 EasyOCR 사용 (고성능)
            extracted_text = ocr_with_enhanced_preprocessing(image_path_or_object, use_easyocr=True)
            engine_name = "EasyOCR"
        else:
            # 📜 Tesseract 사용 (기존)
            extracted_text = ocr_image_with_opencv(image_path_or_object, "kor+eng", fast_mode)
            engine_name = "Tesseract"
        
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        
        return {
            'text': extracted_text,
            'processing_time': processing_time,
            'engine': engine_name,
            'mode': 'fast' if fast_mode else 'precise',
            'success': True
        }
    except Exception as e:
        return {
            'text': '',
            'processing_time': 0,
            'engine': 'Error',
            'mode': 'fast' if fast_mode else 'precise',
            'success': False,
            'error': str(e)
        }

# 웹페이지에서 사용할 간단한 OCR 함수 (호환성 유지)
def simple_ocr(image, lang="kor+eng"):
    """
    간단한 OCR 함수 (기존 웹페이지 코드와의 호환성을 위해 유지)
    """
    try:
        result = extract_text_from_image(image, use_easyocr=True, fast_mode=True)
        return result['text']
    except:
        # 실패 시 기본 OCR 방식 사용
        return ocr_image_with_opencv(image, lang, fast_mode=True)