# Dangerous_Eating
Cursor AI 활용 경진대회

# 🚨 Dangerous Eating - 알레르기 위험 탐지 웹사이트

AI 기반 성분표 알레르기 위험 탐지 및 맞춤형 경고 웹사이트입니다.

## 🎯 주요 기능

- **OCR 기반 성분표 인식**: pytesseract를 활용한 이미지 텍스트 추출
- **개인 맞춤형 알레르기 탐지**: 사용자 등록 알레르기 정보와 성분표 교차 분석
- **신호등 방식 위험 표시**: 강(빨강), 중(주황), 약(노랑), 안전(초록)으로 직관적 표시
- **분석 이력 관리**: 과거 분석 결과 저장 및 조회
- **프로필 관리**: 알레르기 정보 등록/수정/삭제

## 🛠 기술 스택

- **프론트엔드**: Streamlit
- **백엔드**: Python, SQLite
- **OCR**: pytesseract
- **이미지 처리**: Pillow
- **데이터 처리**: Pandas

## 📋 설치 및 실행

### 1. 저장소 클론
```bash
git clone [repository-url]
cd Dangerout_Eating
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. Tesseract OCR 설치
- **Windows**: https://github.com/UB-Mannheim/tesseract/wiki 에서 다운로드
- **macOS**: `brew install tesseract`
- **Ubuntu**: `sudo apt install tesseract-ocr tesseract-ocr-kor`

### 5. 앱 실행
```bash
streamlit run app.py
```

## 📱 사용 방법

1. **프로필 설정**: 사이드바에서 사용자 ID 입력 후 "내 프로필"에서 알레르기 정보 등록
2. **성분표 분석**: "분석" 페이지에서 성분표 이미지 업로드 후 분석 실행
3. **결과 확인**: 신호등 방식으로 표시되는 위험도 및 감지된 알레르기 성분 확인
4. **이력 조회**: "이력" 페이지에서 과거 분석 결과 확인

## 🎨 디자인 가이드

- **빨강 (#FF4D4F)**: 고위험
- **주황 (#FA8C16)**: 중위험  
- **노랑 (#FAAD14)**: 저위험
- **초록 (#52C41A)**: 안전

## 📊 지원 알레르기 성분

식약처 고시 23종 알레르기 유발 성분:
난류, 우유, 메밀, 땅콩, 대두, 밀, 고등어, 게, 새우, 돼지고기, 복숭아, 토마토, 호두, 닭고기, 쇠고기, 오징어, 전복, 홍합, 굴, 잣, 아몬드, 호박, 쑥

## ⚠️ 주의사항

- 본 서비스는 참고용 도구이며 의학적 진단을 대체하지 않습니다.
- 건강에 대한 우려가 있으시면 의사와 상담하시기 바랍니다.
- OCR 인식 정확도는 이미지 품질에 따라 달라질 수 있습니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

- **이메일**: jinhyeok1001@naver.com
- **전화**: 02-1234-5678
- **운영시간**: 평일 09:00-18:00

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
