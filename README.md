# Allergy Detector - AI 기반 알레르기 성분 감지 시스템

## 프로젝트 개요
AI 기술을 활용하여 식품 성분표를 분석하고 개인별 알레르기 위험도를 평가하는 웹 애플리케이션입니다.

## 주요 기능
- 🍽️ **로고**: "조심해eat!" - 어느 페이지에서든 클릭 시 메인 홈페이지로 이동
- 👤 **사용자 인증**: 회원가입, 로그인, 마이페이지
- ⚠️ **알레르기 관리**: 개인별 알레르기 정보 설정 및 저장
- 📷 **OCR 분석**: 식품 성분표 이미지 업로드 및 텍스트 추출
- 🤖 **AI 분석**: 알레르기 성분 감지 및 위험도 평가
- 📊 **결과 표시**: 신호등 방식의 직관적인 위험도 표시

## 프로젝트 구조
```
Allergy_Detector/
├── src/
│   ├── api/
│   │   └── flask_app.py          # Flask 웹 애플리케이션 메인 파일
│   ├── core/
│   │   └── ocr_utils.py          # OCR 텍스트 추출 유틸리티
│   └── services/
│       ├── auth_service.py       # 사용자 인증 서비스
│       ├── profile_service.py    # 사용자 프로필 관리
│       ├── report_service.py     # 분석 보고서 관리
│       ├── risk_service.py       # 위험도 분석 서비스
│       └── db_client.py          # Firestore 데이터베이스 클라이언트
├── templates/
│   ├── index.html               # 메인 홈페이지
│   ├── login.html               # 로그인 페이지
│   ├── signup.html              # 회원가입 페이지
│   └── mypage.html              # 마이페이지
├── static/
│   ├── css/
│   │   ├── style.css            # 메인 스타일시트
│   │   └── remixicon.css        # 아이콘 폰트
│   └── js/
│       └── script.js            # 프론트엔드 JavaScript
├── config/
│   └── firestore-loader/
│       ├── serviceAccountKey.json # Firestore 서비스 계정 키
│       └── *.js                 # 데이터베이스 관리 스크립트
├── uploads/                     # 업로드된 이미지 저장소
├── venv/                        # Python 가상환경
└── README.md                    # 프로젝트 문서
```

## 설치 및 실행

### 1. 가상환경 활성화
```bash
source venv/bin/activate
```

### 2. 애플리케이션 실행
```bash
python src/api/flask_app.py
```

### 3. 웹 브라우저 접속
```
http://127.0.0.1:3000
```

## 주요 기술 스택
- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Database**: Google Firestore
- **OCR**: EasyOCR, Tesseract
- **AI**: Custom risk analysis algorithms

## API 엔드포인트
- `GET /` - 메인 홈페이지
- `GET /login` - 로그인 페이지
- `POST /login` - 로그인 처리
- `GET /signup` - 회원가입 페이지
- `POST /signup` - 회원가입 처리
- `GET /mypage` - 마이페이지
- `GET /logout` - 로그아웃
- `POST /upload` - 이미지 업로드
- `POST /analyze` - 이미지 분석
- `GET /api/allergies` - 사용자 알레르기 정보 조회
- `POST /api/allergies` - 사용자 알레르기 정보 저장

## 개발자 정보
- **프로젝트명**: 조심해eat! (Allergy Detector)
- **버전**: 1.0.0
- **개발환경**: Python 3.9, Flask 2.x
- **데이터베이스**: Google Firestore

## 라이선스
이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.
