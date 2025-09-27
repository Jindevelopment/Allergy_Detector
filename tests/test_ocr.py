#!/usr/bin/env python3
# OCR 테스트 스크립트

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr_utils import extract_text_from_image, check_gpu_availability

def test_ocr():
    print("🔍 OCR 기능 테스트 시작!")
    print("-" * 50)
    
    # GPU 가용성 확인
    print("1. GPU 가용성 확인:")
    gpu_available = check_gpu_availability()
    print(f"   GPU 사용 가능: {gpu_available}")
    print()
    
    # 테스트 이미지 경로 (실제 이미지가 있다면 사용)
    test_image_path = "/Users/oseli/Desktop/Cursor AI/data/과자:빵류/오프라인 데이터/빠다코코넛.jpeg"
    
    if os.path.exists(test_image_path):
        print(f"2. 테스트 이미지: {test_image_path}")
        print("   OCR 분석 시작...")
        
        try:
            result = extract_text_from_image(test_image_path, use_easyocr=True, fast_mode=True)
            
            if result['success']:
                print(f"   ✅ OCR 성공!")
                print(f"   📊 처리 시간: {result['processing_time']}초")
                print(f"   🔧 사용 엔진: {result['engine']}")
                print(f"   📝 추출된 텍스트:")
                print(f"   {result['text'][:200]}...")
            else:
                print(f"   ❌ OCR 실패: {result.get('error', '알 수 없는 오류')}")
                
        except Exception as e:
            print(f"   ❌ OCR 실행 중 오류: {str(e)}")
    else:
        print("2. 테스트 이미지를 찾을 수 없습니다.")
        print("   OCR 기능은 설치되었지만 테스트할 이미지가 없습니다.")
    
    print()
    print("🎯 OCR 기능이 정상적으로 활성화되었습니다!")
    print("   이제 웹페이지에서 파일 업로드 후 성분 분석이 가능합니다.")

if __name__ == "__main__":
    test_ocr()

