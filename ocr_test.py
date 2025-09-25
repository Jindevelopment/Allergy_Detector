#이 코드는 ocr test를 위한 코드입니다. 
#!/usr/bin/env python3
# ocr_test.py
#source venv/bin/activate
# ocr_test_optimized.py
import cv2
import pytesseract
import numpy as np
from PIL import Image
import sys
import re
import easyocr
import time
import torch

def check_gpu_availability():
    """
    맥북 GPU 가용성 확인 함수
    """
    print("🔍 시스템 정보 확인 중...")
    
    # MPS (Metal Performance Shaders) 확인
    if torch.backends.mps.is_available():
        print("✅ MPS(Metal Performance Shaders) 사용 가능!")
        print("🚀 맥북 M1/M2/M3 칩 GPU 가속 지원")
        return True
    elif torch.cuda.is_available():
        print("✅ CUDA GPU 사용 가능!")
        return True
    else:
        print("❌ GPU 사용 불가 - CPU 모드로 실행")
        return False

def apply_advanced_preprocessing(image):
    """
    고급 이미지 전처리 함수 (Subeen lab 블로그 참고)
    https://subeen-lab.tistory.com/121
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
        import torch
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
    향상된 전처리 + 고성능 OCR 함수
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
            import torch
            if torch.backends.mps.is_available():
                print("🚀 맥북 GPU(MPS) 가속 사용 중...")
                reader = easyocr.Reader(['ko', 'en'], gpu=True)
            else:
                print("💻 CPU 모드로 실행 중...")
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
        else:
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
        
        # 모든 결과를 합치고  제거
        combined_text = " ".join(all_texts)
        return combined_text.strip()
    
    except Exception as e:
        print(f"향상된 OCR 오류: {e}")
        return ""

def extract_ingredients_from_text(text):
    """
    OCR로 추출된 텍스트에서 원재료명만 추출하는 함수 (한국 식품 성분표 특화 - 개선된 버전)
    """
    ingredients = []
    
    # 먼저 직접 패턴 매칭으로 주요 재료들 추출
    ingredients = extract_direct_patterns(text)
    
    # 원재료명 섹션 찾기
    ingredient_section = find_ingredient_section(text)
    
    if ingredient_section:
        # 원재료명 섹션에서 추가 추출
        section_ingredients = extract_from_ingredient_section(ingredient_section)
        ingredients.extend(section_ingredients)
    else:
        # 전체 텍스트에서 원재료명 패턴 찾기
        full_text_ingredients = extract_from_full_text(text)
        ingredients.extend(full_text_ingredients)
    
    # 중복 제거 및 정렬
    ingredients = list(set(ingredients))
    ingredients.sort()
    
    # 알레르기 유발 성분만 필터링
    allergen_ingredients = filter_allergen_ingredients(ingredients)
    
    return allergen_ingredients

def extract_from_ingredient_section(section_text):
    """
    원재료명 섹션에서 성분을 추출하는 함수
    """
    ingredients = []
    
    # 1. 쉼표로 구분된 재료명들 추출 (가장 일반적인 패턴)
    comma_pattern = r'([가-힣]+(?:\([^)]*\))?(?:\{[^}]*\})?)'
    matches = re.findall(comma_pattern, section_text)
    
    for match in matches:
        # 각 재료명을 개별적으로 처리
        individual_ingredients = split_compound_ingredient(match)
        for ingredient in individual_ingredients:
            cleaned = clean_ingredient_text(ingredient)
            if cleaned and is_valid_ingredient(cleaned):
                ingredients.append(cleaned)
    
    # 2. 특수 패턴들 추출
    special_patterns = [
        # 백분율이 포함된 재료명 (예: 가공유크림31.86%)
        r'([가-힣]+(?:\d+\.?\d*%)?)',
        # 괄호 안에 상세 정보가 있는 재료명
        r'([가-힣]+\([^)]*\))',
        # 중괄호 안에 복합 정보가 있는 재료명
        r'([가-힣]+\{[^}]*\})',
    ]
    
    for pattern in special_patterns:
        matches = re.findall(pattern, section_text)
        for match in matches:
            cleaned = clean_ingredient_text(match)
            if cleaned and is_valid_ingredient(cleaned):
                ingredients.append(cleaned)
    
    return ingredients

def remove_duplicate_allergens(ingredients):
    """
    중복된 알레르기 유발 성분을 제거하는 함수 (개선된 버전)
    """
    if not ingredients:
        return []
    
    # 알레르기 성분 매핑 (중복 제거 및 표준화)
    allergen_mapping = {
        # 밀 관련 - 밀가루로 통일
        '밀': '밀가루',
        '밀가루': '밀가루',
        '밀글루텐': '밀가루',
        '밀전분': '밀가루',
        '밀효소': '밀가루',
        '밀단백질': '밀가루',
        
        # 난류 관련 - 달걀로 통일
        '계란': '달걀',
        '달걀': '달걀',
        '전란액': '달걀',
        '난황액': '달걀',
        '난백분': '달걀',
        '난황분말': '달걀',
        '난백분말': '달걀',
        
        # 우유 관련 - 우유로 통일
        '우유': '우유',
        '전지분유': '우유',
        '탈지분유': '우유',
        '유크림': '우유',
        '가공유크림': '우유',
        '유당': '우유',
        '유청단백분말': '우유',
        '혼합분유': '우유',
        '연유': '우유',
        '버터': '우유',
        '마가린': '우유',
        '치즈': '우유',
        '요거트': '우유',
        
        # 대두 관련 - 대두로 통일
        '대두': '대두',
        '콩': '대두',
        '두부': '대두',
        '된장': '대두',
        '간장': '대두',
        '고추장': '대두',
        '콩기름': '대두',
        '대두단백질': '대두',
        '대두분말': '대두',
        '대두유': '대두',
        '식물성단백가수분해물': '대두',
        
        # 땅콩 관련 - 땅콩으로 통일
        '땅콩': '땅콩',
        '피넛': '땅콩',
        '땅콩버터': '땅콩',
        '땅콩오일': '땅콩',
        '땅콩분말': '땅콩',
        
        # 견과류 - 각각 유지
        '호두': '호두',
        '잣': '잣',
        '아몬드': '아몬드',
        '캐슈넛': '캐슈넛',
        '피스타치오': '피스타치오',
        '마카다미아': '마카다미아',
        
        # 메밀 관련 - 메밀로 통일
        '메밀': '메밀',
        '메밀가루': '메밀',
        '메밀면': '메밀',
        
        # 갑각류 - 각각 유지
        '새우': '새우',
        '새우분말': '새우',
        '게': '게',
        '게분말': '게',
        '랍스터': '랍스터',
        '가재': '가재',
        
        # 조개류 - 조개로 통일
        '조개': '조개',
        '조개류': '조개',
        '굴': '조개',
        '전복': '조개',
        '홍합': '조개',
        '바지락': '조개',
        '관자': '조개',
        
        # 어류 - 어류로 통일
        '고등어': '어류',
        '연어': '어류',
        '참치': '어류',
        '멸치': '어류',
        '오징어': '어류',
        '문어': '어류',
        '어류': '어류',
        
        # 육류 - 각각 유지
        '쇠고기': '쇠고기',
        '소고기': '쇠고기',
        '돼지고기': '돼지고기',
        '돼지': '돼지고기',
        '닭고기': '닭고기',
        '양고기': '양고기',
        
        # 복숭아 관련 - 복숭아로 통일
        '복숭아': '복숭아',
        '복숭아즙': '복숭아',
        '복숭아향료': '복숭아',
        
        # 토마토 관련 - 토마토로 통일
        '토마토': '토마토',
        '토마토페이스트': '토마토',
        '토마토소스': '토마토',
        '토마토추출물': '토마토',
        
        # 아황산류 관련 - 아황산류로 통일
        '아황산나트륨': '아황산류',
        '아황산칼륨': '아황산류',
        '아황산수소나트륨': '아황산류',
        '아황산류': '아황산류',
        
        # 기타 - 각각 유지
        '카라멜색소': '카라멜색소',
        '아질산나트륨': '아질산나트륨',
        '복합조미료': '복합조미료',
        'MSG': 'MSG',
        '조미료': '조미료'
    }
    
    # 중복 제거된 성분들을 저장할 세트
    unique_allergens = set()
    processed_ingredients = []
    
    for ingredient in ingredients:
        # 각 성분에서 알레르기 성분 매핑 찾기
        found_allergen = None
        for key, mapped_allergen in allergen_mapping.items():
            if key in ingredient:
                found_allergen = mapped_allergen
                break
        
        # 매핑된 알레르기 성분이 있고 아직 추가되지 않았다면 추가
        if found_allergen and found_allergen not in unique_allergens:
            unique_allergens.add(found_allergen)
            processed_ingredients.append(found_allergen)
    
    return processed_ingredients

def filter_allergen_ingredients(ingredients):
    """
    추출된 재료명 중에서 알레르기 유발 성분만 필터링하고 중복 제거하는 함수
    """
    # 알레르기 유발 성분 목록 (식약처 지정 23종 + 관련 재료)
    allergen_list = [
        # 곡물류 (밀)
        '밀가루', '밀', '밀글루텐', '밀전분', '밀효소', '밀단백질',
        
        # 난류 (달걀)
        '달걀', '계란', '전란액', '난황액', '난백분', '난황분말', '난백분말',
        
        # 우유
        '우유', '전지분유', '탈지분유', '유크림', '가공유크림', '유당', '유청단백분말',
        '혼합분유', '연유', '버터', '마가린', '치즈', '요거트',
        
        # 대두
        '대두', '콩', '두부', '된장', '간장', '고추장', '콩기름', '대두단백질',
        '대두분말', '대두유', '식물성단백가수분해물',
        
        # 땅콩
        '땅콩', '피넛', '땅콩버터', '땅콩오일', '땅콩분말',
        
        # 견과류
        '호두', '잣', '아몬드', '캐슈넛', '피스타치오', '마카다미아',
        
        # 메밀
        '메밀', '메밀가루', '메밀면',
        
        # 갑각류
        '새우', '게', '랍스터', '가재', '새우분말', '게분말',
        
        # 조개류
        '조개', '굴', '전복', '홍합', '바지락', '관자', '조개류',
        
        # 어류
        '고등어', '연어', '참치', '멸치', '오징어', '문어', '어류',
        
        # 육류
        '쇠고기', '돼지고기', '닭고기', '양고기', '소고기', '돼지',
        
        # 복숭아
        '복숭아', '복숭아즙', '복숭아향료',
        
        # 토마토
        '토마토', '토마토페이스트', '토마토소스', '토마토추출물',
        
        # 아황산류
        '아황산나트륨', '아황산칼륨', '아황산수소나트륨', '아황산류',
        
        # 기타 알레르기 관련
        '카라멜색소', '아질산나트륨', '복합조미료', 'MSG', '조미료'
    ]
    
    # 알레르기 유발 성분만 필터링
    filtered_ingredients = []
    
    for ingredient in ingredients:
        # 기본 재료명에서 알레르기 성분 확인
        for allergen in allergen_list:
            if allergen in ingredient:
                filtered_ingredients.append(ingredient)
                break
        
        # 괄호 안의 원산지 정보에서도 알레르기 성분 확인
        if '(' in ingredient and ')' in ingredient:
            origin_text = ingredient[ingredient.find('(')+1:ingredient.find(')')]
            for allergen in allergen_list:
                if allergen in origin_text:
                    filtered_ingredients.append(ingredient)
                    break
    
    # 중복 제거 적용
    unique_ingredients = remove_duplicate_allergens(filtered_ingredients)
    
    return unique_ingredients

def extract_from_full_text(text):
    """
    전체 텍스트에서 원재료명 패턴을 찾는 함수
    """
    ingredients = []
    
    # 원재료명 관련 키워드 주변에서 추출
    ingredient_keywords = [
        r'원재료명?\s*[:：]\s*([^가-힣]*[가-힣]+[^가-힣]*(?:[가-힣]+[^가-힣]*)*)',
        r'성분\s*[:：]\s*([^가-힣]*[가-힣]+[^가-힣]*(?:[가-힣]+[^가-힣]*)*)',
    ]
    
    for pattern in ingredient_keywords:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            individual_ingredients = split_compound_ingredient(match)
            for ingredient in individual_ingredients:
                cleaned = clean_ingredient_text(ingredient)
                if cleaned and is_valid_ingredient(cleaned):
                    ingredients.append(cleaned)
    
    return ingredients

def split_compound_ingredient(ingredient_text):
    """
    복합 재료명을 개별 재료로 분리하는 함수
    """
    ingredients = []
    
    # 쉼표로 분리
    parts = re.split(r'[,，]', ingredient_text)
    
    for part in parts:
        part = part.strip()
        if part:
            # 괄호 안의 원산지 정보는 제거하고 기본 재료명만 추출
            base_ingredient = re.sub(r'\([^)]*\)', '', part).strip()
            if base_ingredient:
                ingredients.append(base_ingredient)
            
            # 괄호 안의 원산지 정보도 별도로 저장 (예: 밀가루(밀:미국산)에서 "밀")
            origin_match = re.search(r'\(([^)]*)\)', part)
            if origin_match:
                origin_text = origin_match.group(1)
                # 원산지에서 실제 재료명 추출 (예: "밀:미국산"에서 "밀")
                origin_ingredient = re.search(r'([가-힣]+)', origin_text)
                if origin_ingredient:
                    ingredients.append(origin_ingredient.group(1))
    
    return ingredients

def extract_direct_patterns(text):
    """
    직접 패턴 매칭으로 재료명을 추출하는 함수
    """
    ingredients = []
    
    # 알레르기 유발 성분들 (식약처 지정 23종 + 관련 재료)
    known_ingredients = [
        # 곡물류 (밀)
        '밀가루', '밀', '밀글루텐', '밀전분', '밀효소', '밀단백질',
        
        # 난류 (달걀)
        '달걀', '계란', '전란액', '난황액', '난백분', '난황분말', '난백분말',
        
        # 우유
        '우유', '전지분유', '탈지분유', '유크림', '가공유크림', '유당', '유청단백분말',
        '혼합분유', '연유', '버터', '마가린', '치즈', '요거트',
        
        # 대두
        '대두', '콩', '두부', '된장', '간장', '고추장', '콩기름', '대두단백질',
        '대두분말', '대두유', '식물성단백가수분해물',
        
        # 땅콩
        '땅콩', '피넛', '땅콩버터', '땅콩오일', '땅콩분말',
        
        # 견과류
        '호두', '잣', '아몬드', '캐슈넛', '피스타치오', '마카다미아',
        
        # 메밀
        '메밀', '메밀가루', '메밀면',
        
        # 갑각류
        '새우', '게', '랍스터', '가재', '새우분말', '게분말',
        
        # 조개류
        '조개', '굴', '전복', '홍합', '바지락', '관자', '조개류',
        
        # 어류
        '고등어', '연어', '참치', '멸치', '오징어', '문어', '어류',
        
        # 육류
        '쇠고기', '돼지고기', '닭고기', '양고기', '소고기', '돼지',
        
        # 복숭아
        '복숭아', '복숭아즙', '복숭아향료',
        
        # 토마토
        '토마토', '토마토페이스트', '토마토소스', '토마토추출물',
        
        # 아황산류
        '아황산나트륨', '아황산칼륨', '아황산수소나트륨', '아황산류',
        
        # 기타 알레르기 관련
        '카라멜색소', '아질산나트륨', '복합조미료', 'MSG', '조미료'
    ]
    
    for ingredient in known_ingredients:
        if ingredient in text:
            ingredients.append(ingredient)
    
    # 복합 패턴 검색 (괄호나 특수문자 포함)
    complex_patterns = [
        r'([가-힣]+\([^)]*\))',  # 괄호 포함 재료명
        r'([가-힣]+\[[^\]]*\])',  # 대괄호 포함 재료명
        r'([가-힣]+(?:가루|분말|유지|오일|유|제|료|분유|매스|탕|닝|류|품|액|크림|시럽|추출물|분해물|믹스))',  # 접미사 패턴
    ]
    
    for pattern in complex_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            cleaned = clean_ingredient_text(match)
            if cleaned and is_valid_ingredient(cleaned):
                ingredients.append(cleaned)
    
    return ingredients

def find_ingredient_section(text):
    """
    원재료명 섹션을 찾는 함수 (개선된 버전)
    """
    # 다양한 패턴으로 원재료명 섹션 찾기
    patterns = [
        # 기본 패턴
        r'원재료명?\s*[:：]\s*([\s\S]*?)(?=\n\n|\n[가-힣]+:|$)',
        # "원재료:" 패턴
        r'원재료\s*[:：]\s*([\s\S]*?)(?=\n\n|\n[가-힣]+:|$)',
        # 더 유연한 패턴
        r'원재료명?\s*[:：]\s*([^가-힣]*[가-힣]+[^가-힣]*(?:[가-힣]+[^가-힣]*)*)',
        # 성분 관련 패턴
        r'성분\s*[:：]\s*([\s\S]*?)(?=\n\n|\n[가-힣]+:|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            section = match.group(1).strip()
            # 너무 짧거나 비어있지 않은지 확인
            if len(section) > 10:
                return section
    
    # 원재료명 키워드가 없는 경우, 텍스트에서 성분 관련 내용 찾기
    # 쉼표로 구분된 긴 텍스트 블록 찾기
    long_text_pattern = r'([가-힣]+(?:\([^)]*\))?(?:,|\s*,\s*)[가-힣]+(?:\([^)]*\))?(?:,|\s*,\s*)[가-힣]+(?:\([^)]*\))?(?:,|\s*,\s*)[가-힣]+(?:\([^)]*\))?)'
    match = re.search(long_text_pattern, text, re.MULTILINE)
    
    if match:
        return match.group(1).strip()
    
    return None

def is_valid_ingredient(text):
    """
    유효한 재료명인지 확인하는 함수 (한국 식품 성분표 특화)
    """
    if not text or len(text) < 2:
        return False
    
    # 너무 긴 텍스트 제외 (30자 이상)
    if len(text) > 30:
        return False
    
    # 한국어 비율 확인 (50% 이상)
    korean_chars = len(re.findall(r'[가-힣]', text))
    if korean_chars < len(text) * 0.5:
        return False
    
    # 제외할 단어들 (더 구체적으로)
    exclude_words = [
        # 제품 정보
        '제품명', '식품유형', '소비기한', '품목보고번호', '포장재질', '업소명', '소재지',
        '측면표기일까지', '즉면표기일까지', '제조원', '대륙식품', '덕계공장',
        
        # 주소/위치 정보
        '서울시', '영등포구', '경남', '양산시', '그린공단', '말레이시아산', '미국산', '싱가포르산',
        
        # 안전/보관 정보
        '직사광선', '습기', '피해', '보관', '개봉', '후', '가급적', '빨리', '드세요',
        '부정불량식품', '신고', '국번없이', '1399', '고객센터', '전화', '문자', '반품처',
        '본사', '구입한', '공기주입', '방식을', '사용하였습니다', '소비자', '기본법', '의한', '피해보상',
        
        # 영양정보
        '기준치에', '대한', '내용량당', '콜레스테롤', '포화지방', '총', '개', '함량', '기타',
        
        # 일반적인 설명
        '생길', '있으나', '인체에', '무해하니', '드셔도', '괜찮습니다', '나누어', '조금씩',
        '하안', '주', '주 내용량당',
        
        # OCR 오류로 인한 잘못된 추출
        '불량식품', '폴리프로필렌 소비기한', '변질품'
    ]
    
    # 정확히 일치하는 경우만 제외
    for word in exclude_words:
        if text == word or text.startswith(word + '(') or text.endswith(')' + word):
            return False
    
    # 알레르기 관련 문구가 포함된 경우 제외
    if any(phrase in text for phrase in ['함유', '혼입 가능', '포함', '혼입가능']):
        return False
    
    # 실제 식품 원재료명 패턴 확인 (확장된 목록)
    valid_ingredients = [
        # 곡물류
        '밀가루', '밀', '옥수수', '쌀', '보리', '귀리',
        
        # 당류
        '설탕', '백설탕', '당류', '당류가공품', '포도당', '과당', '유당',
        
        # 유지류
        '쇼트닝', '가공유지', '식물성유지', '팜유', '팡유', '팡에스테르화유',
        '해바라기유', '올레오레진로즈메리', '버터', '마가린',
        
        # 유제품
        '전지분유', '탈지분유', '유청단백분말', '우유', '유크림', '가공유크림',
        '혼합분유', '연유', '카라기난',
        
        # 코코아/초콜릿
        '코코아매스', '코코아프리퍼레이션', '고코아매스', '전지분골드',
        
        # 첨가물
        '산도조절제', '유화제', '혼합제제', '불활성건조효모', '효모', '생이스트',
        '합성팽창제', '탄산수소나트륨', '산성피로인산나트륨', '제일인산칼슘', '젖산칼슘',
        '스테아릴젖산나트륨', '비타민C', 'α-아밀라아제', '자일라나아제',
        '초산나트륨', '초산', '비타민B₁라우릴황산염',
        
        # 향료/향신료
        '향료', '바닐라', '바닐라추출물', '바닐라크림', '바닐린', '효소제', '구면신',
        '설탕시럽', '플러스로스트콘맛씨즈닝', '간장분말', '진간장', '복합조미식품',
        
        # 기타
        '정제소금', '전란액', '난황액', '난백분', '슈가파우더', '기타가공품',
        '변성전분', '옥수수전분', '식물성단백가수분해물', '대두',
        '노티드도넛믹스', '영양강화밀가루', '밀글루텐', '헤미셀룰라아제', '황산칼슘'
    ]
    
    # 실제 재료명과 유사한 패턴이 있는지 확인
    for ingredient in valid_ingredients:
        if ingredient in text:
            return True
    
    # 일반적인 식품 관련 패턴 (확장된 패턴)
    food_patterns = [
        r'.*가루$', r'.*분말$', r'.*유지$', r'.*오일$', r'.*유$', r'.*제$', r'.*료$',
        r'.*분유$', r'.*매스$', r'.*탕$', r'.*닝$', r'.*류$', r'.*품$', r'.*액$',
        r'.*크림$', r'.*시럽$', r'.*추출물$', r'.*분해물$', r'.*믹스$', r'.*강화.*$'
    ]
    
    for pattern in food_patterns:
        if re.match(pattern, text):
            return True
    
    return False

def clean_ingredient_text(text):
    """
    추출된 재료명 텍스트를 정제하는 함수 (한국 식품 성분표 특화 - 개선된 버전)
    """
    if not text:
        return ""
    
    # 앞뒤 공백 제거
    text = text.strip()
    
        # OCR 오류로 인한 잘못된 문자들 수정 (더 포괄적으로)
    ocr_corrections = {
        # 일반적인 OCR 오류
        '0': 'O', '1': 'l', '2': 'Z', '5': 'S', '8': 'B',
        
        # 한국어 재료명 OCR 오류 수정
        '설 탕': '설탕', '정제소 금': '정제소금', '산도조절 제': '산도조절제',
        '유화 제': '유화제', '혼합 제제': '혼합제제', '바닐 라': '바닐라',
        '전지분 유': '전지분유', '유청단백분 말': '유청단백분말',
        '불활성건조효 모': '불활성건조효모', '고코아매 스': '고코아매스',
        '코코아프리퍼레이 션': '코코아프리퍼레이션', '팡에스테르화 유': '팡에스테르화유',
        
        # 공백 제거가 필요한 경우들
        '밀 가루': '밀가루', '마가 린': '마가린', '효 모': '효모',
        '전란 액': '전란액', '난황 액': '난황액', '혼합분 유': '혼합분유',
        '생이 스트': '생이스트', '슈가파우 더': '슈가파우더',
        
        # 특수 문자 정리
        '·': ' ', '：': ':', '，': ',',
        
        # 추가 OCR 오류 수정
        '설탕': '설탕',  # 이미 올바른 형태
    }
    
    # OCR 오류 수정 적용
    for wrong, correct in ocr_corrections.items():
        text = text.replace(wrong, correct)
    
    # 불필요한 문자들 제거 (괄호는 제거하지 않음 - 원산지 정보 포함)
    unwanted_chars = ['[', ']', ';', '；', '|', '\\', '/', '·', '·']
    for char in unwanted_chars:
        text = text.replace(char, ' ')
    
    # 백분율 정보 정리 (예: "가공유크림31.86%" → "가공유크림")
    text = re.sub(r'\d+\.?\d*%', '', text)
    
    # 숫자와 특수문자 정리 (재료명에 포함된 숫자 제거하되, 재료명 자체는 보존)
    # 단, 숫자만으로 이루어진 부분은 제거
    text = re.sub(r'\b\d+\b', '', text)
    
    # 연속된 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    
    # 앞뒤 공백 다시 제거
    text = text.strip()
    
    # 너무 짧은 텍스트 제외 (1글자)
    if len(text) < 2:
        return ""
    
    # 너무 긴 텍스트 제외 (50자)
    if len(text) > 50:
        return ""
    
    return text

def extract_ingredients_from_image(image_path_or_object, use_easyocr=True, fast_mode=False):
    """
    이미지에서 성분표를 인식하고 원재료명만 추출하는 메인 함수 (업그레이드 버전)
    use_easyocr: EasyOCR 사용 여부 (기본값: True)
    fast_mode: 빠른 모드 사용 여부 (기본값: False)
    """
    try:
        start_time = time.time()
        
        if use_easyocr:
            # 🚀 EasyOCR 사용 (고성능)
            print("🔥 EasyOCR 엔진 사용 중...")
            extracted_text = ocr_with_enhanced_preprocessing(image_path_or_object, use_easyocr=True)
            engine_name = "EasyOCR"
        else:
            # 📜 Tesseract 사용 (기존)
            print("📜 Tesseract OCR 엔진 사용 중...")
            extracted_text = ocr_image_with_opencv(image_path_or_object, "kor+eng", fast_mode)
            engine_name = "Tesseract"
        
        # 원재료명 추출
        ingredients = extract_ingredients_from_text(extracted_text)
        
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        
        return {
            'full_text': extracted_text,
            'ingredients': ingredients,
            'ingredient_count': len(ingredients),
            'processing_time': processing_time,
            'engine': engine_name,
            'mode': 'fast' if fast_mode else 'precise'
        }
    except Exception as e:
        return {
            'error': str(e),
            'full_text': '',
            'ingredients': [],
            'ingredient_count': 0,
            'processing_time': 0,
            'engine': 'Error',
            'mode': 'fast' if fast_mode else 'precise'
        }

# -------------------------------
# 터미널에서 실행 시
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python ocr_test.py [이미지파일경로] [--tesseract]")
        print("  --tesseract: Tesseract OCR 사용 (기본값: EasyOCR)")
        sys.exit(1)

    # 명령행 인수 처리
    use_easyocr = True
    image_path = '/Users/oseli/Desktop/Cursor AI/data/과자:빵류/오프라인 데이터/빠다코코넛.jpeg'
    
    if len(sys.argv) > 1:
        if '--tesseract' in sys.argv:
            use_easyocr = False
            print("📜 Tesseract OCR 모드 선택됨")
        else:
            image_path = sys.argv[1]
    
    try:
        print("🚀 OCR 엔진 업그레이드 버전 테스트 시작!")
        print(f"📁 이미지: {image_path}")
        print(f"🔧 엔진: {'EasyOCR' if use_easyocr else 'Tesseract'}")
        print("-" * 60)
        
        # GPU 가용성 확인
        gpu_available = check_gpu_availability()
        print("-" * 60)
        
        # 원재료명 추출 실행 (EasyOCR 우선)
        result = extract_ingredients_from_image(image_path, use_easyocr=use_easyocr, fast_mode=False)
        
        if 'error' in result:
            print("❌ 오류 발생:", result['error'])
        else:
            print("\n=== 🎯 성분표 분석 결과 ===")
            print(f"⚡ 처리 시간: {result['processing_time']}초")
            print(f"🔧 사용 엔진: {result['engine']}")
            print(f"📊 모드: {result['mode']}")
            print(f"⚠️ 총 {result['ingredient_count']}개의 알레르기 유발 성분 발견!")
            
            print("\n📝 전체 OCR 텍스트:")
            print("-" * 50)
            print(result['full_text'])
            print("-" * 50)
            
            print("\n🚨 발견된 알레르기 유발 성분:")
            print("-" * 30)
            for i, ingredient in enumerate(result['ingredients'], 1):
                print(f"{i:2d}. {ingredient}")
            
            if result['ingredient_count'] == 0:
                print("✅ 알레르기 유발 성분이 발견되지 않았습니다!")
                print("\n💡 성능 개선 팁:")
                print("  - EasyOCR이 더 정확합니다")
                print("  - 이미지 품질이 좋을수록 결과가 향상됩니다")
                print("  - 다른 이미지로도 테스트해보세요!")
                
    except Exception as e:
        print("❌ 실행 중 오류:", e)
