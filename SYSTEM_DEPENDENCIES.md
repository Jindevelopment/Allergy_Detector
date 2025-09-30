# 시스템 의존성 설치 가이드

## 📋 필요한 시스템 패키지

### macOS
```bash
# Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Tesseract OCR 설치
brew install tesseract

# 기타 의존성
brew install libffi
```

### Ubuntu/Debian
```bash
# 시스템 패키지 업데이트
sudo apt-get update

# Tesseract OCR 및 언어팩 설치
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-kor  # 한국어 지원
sudo apt-get install tesseract-ocr-eng  # 영어 지원

# OpenCV 의존성
sudo apt-get install libopencv-dev python3-opencv

# 기타 의존성
sudo apt-get install libffi-dev
sudo apt-get install libssl-dev
```

### Windows
1. **Tesseract OCR 설치**
   - https://github.com/UB-Mannheim/tesseract/wiki 에서 다운로드
   - 설치 후 환경변수 PATH에 추가

2. **Visual C++ Redistributable 설치**
   - Microsoft Visual C++ Redistributable for Visual Studio 2019

3. **Git Bash 또는 WSL 사용 권장**

## 🐍 Python 패키지 설치

```bash
# 가상환경 활성화 후
pip install -r requirements.txt
```

## 🔧 문제 해결

### Tesseract 관련 오류
```bash
# macOS에서 경로 설정
export TESSDATA_PREFIX=/usr/local/share/tessdata

# Ubuntu에서 경로 확인
tesseract --list-langs
```

### OpenCV 관련 오류
```bash
# Ubuntu에서 추가 패키지 설치
sudo apt-get install libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
```

### EasyOCR 관련 오류
```bash
# PyTorch CPU 버전 설치 (GPU 없는 경우)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```
