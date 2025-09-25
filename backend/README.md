📂 폴더 구조
backend/
├── db_client.py        # Firestore 초기화 및 공용 핸들러
├── auth_service.py     # 회원가입, 로그인
├── profile_service.py  # 사용자 알레르기 관리 (추가/삭제/조회)
├── risk_service.py     # 알레르겐 탐지 + 위험도 계산
├── report_service.py   # 분석 결과 저장 및 조회
└── anon_service.py     # 비회원 모드 분석 (DB 저장 없음)


1️⃣ db_client.py

Firestore 초기화 모듈
	•	init_firestore(key_path=None) → Firestore 클라이언트 초기화
	•	get_db() → 이미 초기화된 DB 핸들 반환

2️⃣ auth_service.py

회원가입 & 로그인 기능
	•	register_user(user_id, password, nickname)
	•	새 사용자 등록 (비밀번호는 bcrypt 해시 저장됨)
	•	check_login(user_id, password)
	•	로그인 시 검증 → 성공하면 {user_id, nickname} 반환
	•	user_exists(user_id)
	•	사용자 존재 여부 확인

3️⃣ profile_service.py

사용자 알레르기 프로필 관리
	•	list_allergies(user_id) → 알레르기 리스트 반환
	•	add_allergy(user_id, allergen_name, severity) → 새 알레르기 추가
	•	remove_allergy(user_id, allergy_doc_id) → 알레르기 삭제

4️⃣ risk_service.py

알레르겐 탐지 + 위험도 계산
	•	load_allergen_dict() → 알레르겐/동의어 목록 불러오기
	•	detect_allergens(text, user_allergies) → OCR 텍스트에서 사용자 알레르겐 탐지
	•	calculate_risk(detected, symptoms) → 점수 계산 + 위험도 판정
	•	analyze_text(text, user_allergies, symptoms) → 탐지부터 판정까지 한번에

5️⃣ report_service.py

분석 결과 저장/조회
	•	save_report(user_id, food_name, detected_allergens, symptom_check, total_score, final_risk)
	•	분석 결과 Firestore에 저장
	•	get_recent_reports(user_id, limit=3)
	•	최근 분석 결과 N건 가져오기

6️⃣ anon_service.py

비회원 분석 (저장 없음)
	•	analyze_text_only(text, symptoms)
	•	DB에 저장하지 않고 탐지/위험도 판정만 수행

🚀 실행/개발 워크플로우
	1.	환경 세팅
    pip install firebase-admin google-cloud-firestore bcrypt
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/serviceAccountKey.json

	2.	회원가입 & 로그인 → 세션 유지
	•	UI 팀은 로그인 성공 시 st.session_state["user_id"] = user["user_id"] 저장
	•	이후 프로필/분석/저장 API 호출 시 user_id를 넘겨주면 됨
	3.	비회원 모드
	•	로그인 세션이 없는 경우 anon_service만 호출
	•	분석 결과는 표시되지만 DB에 저장되지 않음

📊 Firestore 컬렉션 구조 (영문 기준)
	•	users/{uid} : 사용자 정보
	•	allergies/{doc} : 알레르기 항목
	•	allergen_list : 알레르겐 & 동의어
	•	symptom_weights : 증상별 점수
	•	risk_rules : 위험도 판정 규칙
	•	user_reports/{doc} : 분석 결과


