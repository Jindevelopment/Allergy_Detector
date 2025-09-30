# 팀원용 설치 및 실행 가이드

## 🚀 빠른 시작 가이드

### 1. 저장소 클론
```bash
git clone https://github.com/Jindevelopment/Allergy_Detector.git
cd Allergy_Detector
```

### 2. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 3. 필요한 패키지 설치
```bash
pip install flask pillow requests google-cloud-firestore easyocr pytesseract opencv-python
```

### 4. 환경 설정

#### 방법 1: 데모 모드로 실행 (권장)
데이터베이스 없이 기본 기능만 사용하려면:
```bash
python src/api/flask_app.py
```

#### 방법 2: 전체 기능 사용 (선택사항)
Firestore 데이터베이스를 사용하려면:
1. `config/firestore-loader/serviceAccountKey.json` 파일 추가
2. 또는 환경변수 설정

### 5. 애플리케이션 실행
```bash
python src/api/flask_app.py
```

브라우저에서 `http://localhost:3000` 접속

## 🔧 문제 해결

### "백엔드 서비스가 사용 불가능합니다" 오류
이 오류는 정상적인 동작입니다. 다음 기능들은 여전히 사용 가능합니다:
- ✅ 바코드 스캔 분석
- ✅ OCR 이미지 분석
- ✅ 알레르기 위험도 분석

### 로그인/회원가입이 안 되는 경우
데모 모드에서는 데이터베이스 연결이 없어 로그인이 제한됩니다. 하지만 다음 기능들은 모두 사용 가능합니다:
- 바코드 스캔
- 이미지 업로드 및 분석
- 알레르기 설정 (세션 기반)

### 패키지 설치 오류
```bash
# macOS에서 tesseract 설치
brew install tesseract

# Ubuntu/Debian에서 tesseract 설치
sudo apt-get install tesseract-ocr

# Windows에서 tesseract 설치
# https://github.com/UB-Mannheim/tesseract/wiki 에서 다운로드
```

## 📱 사용 가능한 기능

### 바코드 스캔
- 테스트용 바코드: `8801045522678` (농심 진짬뽕)
- 카메라 스캔 또는 수동 입력 가능

### OCR 이미지 분석
- 성분표 사진 업로드
- 카메라로 직접 촬영

### 알레르기 분석
- 개인 알레르기 설정
- 위험도 신호등 표시

## 🆘 추가 도움이 필요한 경우
1. 팀장에게 문의
2. GitHub Issues에 문제 보고
3. README.md 파일 참조
