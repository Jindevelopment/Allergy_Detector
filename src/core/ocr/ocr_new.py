from PIL import Image
import pytesseract

# Tesseract OCR 경로 설정
pytesseract.pytesseract.tesseract_cmd = r'#개인 경로'

# 이미지 열기
image_path = "팔도 비빔장 버터간장소스.png"
img = Image.open(image_path)

# 1. 이미지를 흑백(Grayscale)으로 변환
# 'L' 모드는 이미지를 8비트 흑백 픽셀로 변환합니다.
black_white_img = img.convert('L')

# 2. 흑백 이미지에서 한국어+영어 OCR 실행
# lang="kor+eng"는 한국어와 영어를 모두 인식하도록 설정합니다.
extracted_text = pytesseract.image_to_string(black_white_img, lang="kor+eng")

# 추출된 텍스트 출력
print(extracted_text)