# 🛡️ 알레르기 안전 탐지기

AI 기반 성분표 알레르기 위험 탐지 및 맞춤형 경고 웹사이트

## 📋 프로젝트 개요

사용자가 등록한 알레르기 정보를 기반으로, 식품 성분표를 촬영/업로드하면 자동으로 알레르겐 포함 여부를 판별하고, 위험 수준을 **신호등 방식(강·중·약)**으로 직관적으로 안내하는 개인 맞춤형 알레르기 안전 서비스를 제공합니다.

## 🏗️ 프로젝트 구조

```
📁 Allergy_Detector/
├── 📁 src/                     # 소스 코드
│   ├── 📁 core/                # 핵심 로직
│   │   └── 📁 ocr/             # OCR 처리 엔진
│   │       ├── ocr_utils.py    # OCR 유틸리티 함수
│   │       ├── ocr_new.py      # 새로운 OCR 처리기
│   │       ├── ocr_test.py     # OCR 테스트 스크립트
│   │       └── test_ocr.py     # OCR 단위 테스트
│   ├── 📁 api/                 # API 레이어
│   │   ├── 📁 flask/           # Flask 웹 애플리케이션
│   │   │   └── flask_app.py    # Flask 메인 앱
│   │   └── 📁 streamlit/       # Streamlit 대시보드
│   │       ├── app.py          # Streamlit 메인 앱
│   │       └── OCR_UI.py       # OCR UI 컴포넌트
│   ├── 📁 services/            # 비즈니스 로직 서비스
│   │   ├── 📁 auth/            # 인증 관련
│   │   │   ├── auth_service.py # 사용자 인증 서비스
│   │   │   └── anon_service.py # 익명 사용자 서비스
│   │   ├── 📁 profile/         # 사용자 프로필
│   │   │   └── profile_service.py
│   │   ├── 📁 report/          # 분석 리포트
│   │   │   └── report_service.py
│   │   └── 📁 risk/            # 위험도 평가
│   │       └── risk_service.py
│   └── 📁 database/            # 데이터베이스 레이어
│       ├── 📁 clients/         # DB 클라이언트
│       │   ├── __init__.py
│       │   └── db_client.py    # Firestore 클라이언트
│       ├── 📁 migrations/      # 데이터 마이그레이션
│       │   ├── migrate_collections.py
│       │   └── cleanup_old_collections.py
│       └── README.md           # 데이터베이스 구조 문서
├── 📁 data/                    # 데이터 관리
│   ├── 📁 setup/               # 데이터베이스 초기 설정
│   │   └── 📁 db_setup/        # 스키마 및 초기 데이터
│   │       ├── 📁 data/excel/  # 엑셀 데이터 파일
│   │       ├── 📁 schemas/     # 데이터베이스 스키마
│   │       └── 📁 scripts/     # 설정 스크립트
│   └── 📁 loaders/             # 데이터 로더
│       └── 📁 cursorAI-firestore-loader/  # Firestore 업로드 도구
├── 📁 web/                     # 웹 애플리케이션 자원
│   ├── 📁 static/              # 정적 파일
│   │   ├── 📁 css/             # 스타일시트
│   │   ├── 📁 js/              # JavaScript
│   │   └── 📁 images/          # 이미지 파일
│   ├── 📁 templates/           # HTML 템플릿
│   ├── 📁 uploads/             # 업로드된 파일
│   └── 📁 allergy-guide-app/   # Vite 기반 프론트엔드
├── 📁 docs/                    # 문서
│   └── README.md               # 프로젝트 문서 (현재 파일)
├── 📁 config/                  # 설정 파일
├── 📁 tests/                   # 테스트 파일
└── requirements.txt            # Python 의존성
```

## 🔄 데이터 파이프라인

### 1. 입력 단계 (Input Layer)
- **OCR 처리**: `src/core/ocr/` - 이미지에서 텍스트 추출
- **사용자 입력**: `src/api/` - Flask/Streamlit을 통한 사용자 인터페이스

### 2. 처리 단계 (Processing Layer)
- **인증 서비스**: `src/services/auth/` - 사용자 인증 및 세션 관리
- **위험도 평가**: `src/services/risk/` - 알레르기 위험도 계산
- **프로필 관리**: `src/services/profile/` - 사용자별 알레르기 정보 관리

### 3. 저장 단계 (Storage Layer)
- **데이터베이스**: `src/database/` - Firestore 연동 및 데이터 관리
- **리포트 생성**: `src/services/report/` - 분석 결과 저장 및 관리

### 4. 출력 단계 (Output Layer)
- **웹 인터페이스**: `web/` - 사용자에게 결과 표시
- **API 응답**: `src/api/` - JSON 형태의 구조화된 응답

## ✨ 주요 기능

### 🔍 OCR 기반 성분표 인식
- pytesseract 등 OCR 라이브러리를 활용하여 이미지에서 텍스트를 자동 추출
- 영문 및 한글 성분 모두 인식 지원

### 👤 사용자 프로필 매칭
- 사용자가 사전에 등록한 알레르기 정보와 성분표에서 인식한 텍스트를 교차 분석
- 다국어 및 동의어 매칭 (예: "난류 = 계란", "soy = 대두")

### 🚦 위험 신호등 경고
- 위험도 수준을 색상으로 직관적으로 표시
  - 🔴 **강 (빨강)**: 다수 알레르겐 또는 고위험 성분 포함
  - 🟠 **중 (주황)**: 일부 알레르겐 포함
  - 🟡 **약 (노랑)**: 경미한 주의 필요
  - 🟢 **안전 (초록)**: 알레르겐 미탐지

### 📊 다중 인터페이스 지원
- **Flask 웹앱**: RESTful API 및 웹 인터페이스
- **Streamlit 대시보드**: 실시간 분석 및 시각화

## 🛠️ 기술 스택

- **백엔드/분석**: Python, pytesseract (OCR), Pandas (데이터 처리)
- **웹 프레임워크**: Flask, Streamlit
- **데이터베이스**: Firebase Firestore
- **프론트엔드**: HTML/CSS/JavaScript, Vite
- **AI 보조**: Cursor AI (위험 근거 문구 생성 등)

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd Allergy_Detector
```

### 2. 가상환경 생성 (권장)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. Tesseract OCR 설치
- **Windows**: [Tesseract 설치 파일](https://github.com/UB-Mannheim/tesseract/wiki) 다운로드 및 설치
- **macOS**: `brew install tesseract tesseract-lang`
- **Ubuntu**: `sudo apt-get install tesseract-ocr tesseract-ocr-kor tesseract-ocr-eng`

### 5. 애플리케이션 실행

#### Streamlit 대시보드
```bash
streamlit run src/api/streamlit/app.py
```

#### Flask 웹 애플리케이션
```bash
python src/api/flask/flask_app.py
```

## 📱 사용 방법

### 1. 알레르기 정보 등록
- 사이드바의 "👤 내 프로필" 메뉴에서 알레르기 성분을 등록
- 심각도(심각/주의/경미) 선택 가능

### 2. 성분표 분석
- "🔍 분석" 메뉴에서 성분표 이미지 업로드
- "성분 분석 시작" 버튼 클릭
- OCR 결과 및 위험도 확인

### 3. 분석 이력 조회
- "📊 이력" 메뉴에서 과거 분석 결과 확인

## 🗃️ 데이터베이스 구조

### Firestore 컬렉션
- `알레르겐_목록`: 알레르기 성분 마스터 데이터
- `증상_가중치`: 증상별 위험도 가중치
- `위험도_규칙`: 위험도 판정 규칙
- `사용자_정보`: 사용자 프로필 및 알레르기 정보
- `사용자_보고`: 분석 결과 및 이력

자세한 데이터베이스 구조는 `src/database/README.md`를 참조하세요.

## ⚠️ 주의사항

- 본 서비스는 의학적 진단을 대체하지 않습니다
- 정확한 알레르기 정보는 의사와 상담하시기 바랍니다
- OCR 인식 정확도는 이미지 품질에 따라 달라질 수 있습니다

## 🔮 향후 확장 기능

- 대체 식품 추천 (안전한 유사 제품 안내)
- 영양 성분 리포트 생성
- 사용자 맞춤형 식단 관리 기능
- 다국어 지원 (영어, 일본어, 중국어)
- 실시간 카메라 촬영 지원

## 📞 지원 및 문의

- **이메일**: jinhyeok1001@naver.com 
- **전화**: 1588-0000
- **운영시간**: 평일 09:00 - 18:00

## 📄 라이선스

© 2025 알레르기 안전 탐지기. 모든 권리 보유.