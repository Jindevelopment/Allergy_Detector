# CursorAI Allergy Detector

## 📌 프로젝트 개요
OCR 기반으로 식품 성분표를 스캔하여 **알레르겐 탐지 및 위험도 판정**을 지원하는 시스템입니다.  
Firestore를 백엔드 DB로 사용하며, Streamlit 대시보드에서 데이터를 확인할 수 있습니다.

---

## 📂 프로젝트 구조
cursorAI_project/
├── Allergy_Detector/ # Streamlit 앱 (OCR + Firestore 연동)
│ ├── app.py # 메인 Streamlit 실행 파일
│ ├── streamlit_quick_view.py # Firestore 뷰어 (DB 확인용)
│ └── ... # OCR 유틸, UI 관련 코드
│
├── cursorAI-firestore-loader/ # CSV → Firestore 업로드 로더
│ ├── reset_allergens_from_csv.js
│ ├── write_one_from_csv.js
│ └── ...
│
├── db_setup/ # 가상환경 및 초기 세팅
│ └── cursorAI/ # Python venv (gitignore 처리됨)
│
├── .gitignore # Firebase 키, venv, 캐시 무시 설정
└── README.md

---

## 🔑 Firestore 컬렉션 구조

### 1. `알레르겐_목록`
- `표시명` (string) : 알레르겐 명칭 (예: 밀, 땅콩, 계란)
- `이름` (string) : 동일 (검색용)
- `분류` (string) : 알레르겐 분류 (곡류, 견과류 등)
- `동의어` (list[string]) : 다른 표기 (예: 밀가루, 소맥)
- `증상` (string) : 주된 증상 계통
- `보수적점수` (int) : 기본 점수
- `주요알레르겐` (bool) : 표시 대상 여부

---

### 2. `증상_가중치`
- `증상계통` (string) : 구강, 호흡기, 피부, 위장관 등
- `대표증상` (list[string]) : 해당 계통 대표 증상
- `기본점수` (int) : 기본 점수
- `보수규칙` (string) : 가중치 규칙
- `비고` (string)

---

### 3. `위험도_규칙`
- `조건` : 키워드/패턴 규칙
- `위험도` : High, Medium, Low, Very High
- `중증도` : 같은 의미 (판정 단계)

---

### 4. `사용자_정보`
- `id` : UID
- `닉네임` : 사용자 이름
- `알레르겐` : 사용자가 보유한 알레르겐 리스트

---

### 5. `사용자_보고`
- `id` : `${uid}_${timestamp}_${음식명}`
- `사용자UID` : UID
- `음식명` : 스캔한 음식 이름
- `알레르겐_탐지` : 탐지된 알레르겐 리스트
- `증상_체크` : 체크된 증상 계통
- `총점` : 계산된 점수
- `최종위험도` : 최종 판정 단계

---

## 🚀 실행 방법

### 1) 가상환경 활성화
```bash
cd ~/Desktop/cursorAI_project/Allergy_Detector
source ../db_setup/cursorAI/bin/activate
2) 패키지 설치
pip install -q firebase-admin streamlit
3) Streamlit 실행
python -m streamlit run streamlit_quick_view.py
✅ QA 시나리오 (테스트 케이스)
Case A: FREE 문구
입력: FREE 샘플
예상 위험도: 낮음
Case B: 땅콩 + 호흡기 증상
입력: 음식명 땅콩 과자
알레르겐: 땅콩
증상: 호흡기
예상 위험도: 매우 높음
Case C: 밀+대두 + 2계통 증상
입력: 음식명 밀·대두 요리
알레르겐: 밀, 대두
증상: 호흡기, 피부
예상 위험도: 높음
🛠️ 개발 워크플로우
dev 브랜치에서 작업 후 PR 생성
main 은 안정화된 버전만 유지
Firestore 컬렉션 변경 시 → CSV 갱신 후 cursorAI-firestore-loader 사용
⚠️ 보안 주의
serviceAccountKey.json 은 .gitignore 처리되어 GitHub에 올라가지 않음
반드시 로컬에서만 관리할 것

---

👉 이렇게 하면 팀원들이 구조/DB/실행법/QA 다 이해 가능해.  
바로 `README.md` 생성해서 넣고,  

```bash
git checkout -b dev
git add .
git commit -m "Add README and Firestore integration guide"
git push origin dev