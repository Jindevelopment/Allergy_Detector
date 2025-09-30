# src/services/risk_service.py
from services.db_client import get_db
import re
import operator
from typing import List, Dict, Any

def get_db_instance():
    """지연 초기화를 위한 DB 인스턴스 가져오기"""
    return get_db()

LEVEL_ORDER = ["very_low", "low", "medium", "high", "very_high"]
def _max_level(a: str, b: str) -> str:
    """위험도 우선순위 비교 후 더 높은 단계 반환"""
    try:
        return a if LEVEL_ORDER.index(a) >= LEVEL_ORDER.index(b) else b
    except ValueError:
        # 정의 밖의 값이 오면 a 유지
        return a

def load_allergen_dict() -> Dict[str, List[str]]:
    """
    알레르겐_목록 컬렉션에서 데이터 로드 (fix_allergens_ids.js와 연결)
    반환: {표시명: [동의어..., 표시명]}
    """
    out: Dict[str, List[str]] = {}
    try:
        print("=== load_allergen_dict 디버깅 ===")
        db = get_db_instance()
        print(f"Firestore DB 인스턴스: {db}")
        
        collection_ref = db.collection("알레르겐_목록")
        print(f"컬렉션 참조: {collection_ref}")
        
        docs = list(collection_ref.stream())
        print(f"문서 개수: {len(docs)}")
        
        for doc in docs:
            d = doc.to_dict() or {}
            print(f"문서 ID: {doc.id}, 데이터: {d}")
            # fix_allergens_ids.js에서 설정한 필드명 사용
            name = d.get("표시명") or d.get("이름") or doc.id
            syns = d.get("동의어", []) or []
            if name:
                out[name] = list({*(syns or []), name})
                print(f"추가된 알레르겐: {name} -> {out[name]}")
        
        print(f"최종 로드된 알레르겐 개수: {len(out)}")
        
    except Exception as e:
        print(f"알레르겐 데이터 로드 오류: {e}")
        print("폴백 모드로 기본 알레르겐 데이터 사용")
        # 기본 알레르겐 데이터 제공
        out = {
            "대두": ["대두", "콩", "두부", "간장", "된장", "고추장"],
            "밀": ["밀", "밀가루", "면", "빵", "파스타"],
            "우유": ["우유", "유제품", "치즈", "버터", "크림", "탈지분유", "전지분유"],
            "계란": ["계란", "난백", "난황", "알"],
            "견과류": ["땅콩", "호두", "아몬드", "캐슈넛", "피스타치오"],
            "해산물": ["새우", "게", "조개", "굴", "문어", "오징어"],
            "육류": ["돼지고기", "소고기", "닭고기", "양고기"]
        }
        print(f"폴백 데이터 사용: {len(out)}개 알레르겐")
    
    # Firestore에서 데이터를 로드하지 못한 경우 폴백 모드 사용
    if len(out) == 0:
        print("Firestore 데이터가 비어있어 폴백 모드로 전환")
        out = {
            "대두": ["대두", "콩", "두부", "간장", "된장", "고추장"],
            "밀": ["밀", "밀가루", "면", "빵", "파스타"],
            "우유": ["우유", "유제품", "치즈", "버터", "크림", "탈지분유", "전지분유"],
            "계란": ["계란", "난백", "난황", "알"],
            "견과류": ["땅콩", "호두", "아몬드", "캐슈넛", "피스타치오"],
            "해산물": ["새우", "게", "조개", "굴", "문어", "오징어"],
            "육류": ["돼지고기", "소고기", "닭고기", "양고기"],
            "메밀": ["메밀", "메밀가루", "메밀면"],
            "고등어": ["고등어", "생선", "어류"],
            "복숭아": ["복숭아", "과일"],
            "토마토": ["토마토", "토마토페이스트", "토마토소스"]
        }
        print(f"폴백 데이터 사용: {len(out)}개 알레르겐")
    return out

def load_symptom_weights() -> Dict[str, int]:
    """
    증상_가중치 컬렉션에서 데이터 로드 (fix_symptoms.js와 연결)
    한국어와 영어 증상명 모두 지원
    예) {"호흡기": 4, "심혈관":5, "피부":1, "소화기":2, "respiratory": 4, "cardiovascular": 5}
    """
    out: Dict[str, int] = {}
    try:
        db = get_db_instance()
        for doc in db.collection("증상_가중치").stream():
            d = doc.to_dict() or {}
            # fix_symptoms.js에서 설정한 필드명 사용
            korean_key = d.get("증상계통") or d.get("표시명") or doc.id
            val = d.get("기본점수") or d.get("가중치") or 0
            
            if korean_key and val is not None:
                # 한국어 키 추가
                out[korean_key] = int(val)
                
                # 영어 매핑도 추가
                english_key = _map_korean_symptoms_to_english([korean_key])[0]
                if english_key != korean_key:
                    out[english_key] = int(val)
    except Exception as e:
        print(f"증상 가중치 로드 오류: {e}")
        print("폴백 모드로 기본 증상 가중치 사용")
        # 기본 증상 가중치 제공 (한국어 + 영어)
        out = {
            "호흡기": 4, "respiratory": 4,
            "심혈관": 5, "cardiovascular": 5,
            "피부": 1, "skin": 1,
            "소화기": 2, "gi": 2,
            "신경계": 3, "neurological": 3,
            "구강알레르기": 1, "oas": 1
        }
    return out

def load_risk_rules() -> List[Dict[str, Any]]:
    """
    위험도_규칙 컬렉션에서 데이터 로드 (fix_rules_keywords.js와 연결)
    키워드 규칙과 점수 규칙을 모두 처리
    """
    rules = []
    try:
        db = get_db_instance()
        for doc in db.collection("위험도_규칙").stream():
            d = doc.to_dict() or {}
            if d:
                # fix_rules_keywords.js에서 설정한 구조에 맞게 변환
                rule = {}
                
                # 위험도 레벨
                risk_level = d.get("위험도") or d.get("중증도") or "low"
                rule["risk_level"] = risk_level.lower()
                
                # 조건 처리
                condition = d.get("조건", {})
                if isinstance(condition, dict):
                    # 키워드 규칙이 있는 경우
                    keyword_rules = condition.get("키워드규칙", [])
                    if keyword_rules:
                        rule["condition"] = {"키워드규칙": keyword_rules}
                    else:
                        # 점수 기반 규칙으로 변환
                        if risk_level.lower() == "very_high":
                            rule["condition"] = "score>=9"
                        elif risk_level.lower() == "high":
                            rule["condition"] = "score>=7"
                        elif risk_level.lower() == "medium":
                            rule["condition"] = "score>=5"
                        elif risk_level.lower() == "low":
                            rule["condition"] = "score>=3"
                        else:
                            rule["condition"] = "score>=1"
                else:
                    rule["condition"] = condition
                
                # 우선순위 설정
                rule["priority"] = d.get("priority", 9999)
                
                rules.append(rule)
    except Exception as e:
        print(f"위험도 규칙 로드 오류: {e}")
        print("폴백 모드로 기본 위험도 규칙 사용")
        # 기본 위험도 규칙 제공
        rules = [
            {"condition": "score>=9", "risk_level": "very_high", "priority": 1},
            {"condition": "score>=7", "risk_level": "high", "priority": 2},
            {"condition": "score>=5", "risk_level": "medium", "priority": 3},
            {"condition": "score>=3", "risk_level": "low", "priority": 4},
            {"condition": {"키워드규칙": [{"구분": "포함", "패턴": "함유|포함|첨가"}]}, "risk_level": "high", "priority": 5}
        ]
    
    # priority가 있으면 오름차순으로, 없으면 그대로
    rules.sort(key=lambda r: r.get("priority", 9999))
    return rules

def detect_all_allergens(text: str, allergen_dict: Dict[str, List[str]] = None) -> List[str]:
    """
    텍스트에서 모든 알레르기 성분을 감지 (사용자 프로필과 무관하게)
    """
    if allergen_dict is None:
        allergen_dict = load_allergen_dict()
    t = (text or "").lower()
    detected = []
    
    print(f"=== detect_all_allergens 디버깅 ===")
    print(f"입력 텍스트 길이: {len(text) if text else 0}")
    print(f"텍스트 샘플: {text[:200] if text else 'None'}...")
    print(f"알레르겐 딕셔너리 키 개수: {len(allergen_dict)}")
    print(f"알레르겐 딕셔너리 키들: {list(allergen_dict.keys())}")
    
    # 모든 알레르기 성분을 대상으로 감지
    for allergen_name, synonyms in allergen_dict.items():
        for synonym in synonyms:
            if synonym and str(synonym).lower() in t:
                detected.append(allergen_name)
                print(f"매칭 발견: '{synonym}' -> '{allergen_name}'")
                break
    
    print(f"최종 감지된 알레르기: {detected}")
    return list(set(detected))

def detect_allergens(text: str, user_allergies: List[str], allergen_dict: Dict[str, List[str]] = None) -> List[str]:
    """
    사용자 프로필 알레르겐(user_allergies)만 대상으로 텍스트 매칭
    개선: 사용자 알레르기명이 데이터베이스 키와 다를 때도 매칭되도록 함
    """
    if allergen_dict is None:
        allergen_dict = load_allergen_dict()
    t = (text or "").lower()
    detected = []
    
    print(f"사용자 알레르기 목록: {user_allergies}")
    print(f"알레르기 데이터베이스 키: {list(allergen_dict.keys())}")
    
    for user_allergen in user_allergies or []:
        user_allergen_lower = user_allergen.lower()
        found_match = False
        
        print(f"사용자 알레르기 '{user_allergen}' 매칭 시도 중...")
        
        # 1. 직접 키 매칭 시도
        if user_allergen in allergen_dict:
            print(f"직접 키 매칭 성공: {user_allergen}")
            for synonym in allergen_dict[user_allergen]:
                if synonym and str(synonym).lower() in t:
                    detected.append(user_allergen)
                    print(f"텍스트에서 '{synonym}' 발견 -> '{user_allergen}' 추가")
                    found_match = True
                    break
        
        # 2. 직접 키 매칭이 안 되면 모든 키에서 사용자 알레르기명을 동의어로 찾기
        if not found_match:
            for allergen_name, synonyms in allergen_dict.items():
                # 사용자 알레르기명이 이 알레르기의 동의어에 포함되어 있는지 확인
                if user_allergen_lower in [str(syn).lower() for syn in synonyms]:
                    print(f"동의어 매칭 성공: '{user_allergen}' -> '{allergen_name}'")
                    # 텍스트에서 이 알레르기의 모든 동의어를 찾기
                    for synonym in synonyms:
                        if synonym and str(synonym).lower() in t:
                            detected.append(user_allergen)  # 사용자가 선택한 원래 이름으로 추가
                            print(f"텍스트에서 '{synonym}' 발견 -> '{user_allergen}' 추가")
                            found_match = True
                            break
                    if found_match:
                        break
        
        # 3. 특별한 매칭 규칙 (난류 -> 계란 등)
        if not found_match:
            special_mappings = {
                '난류': ['계란', '알', '달걀', '전란액', '난황액', '난백분'],
                '메밀': ['메밀', '메밀가루', '메밀면'],
                '고등어': ['고등어', '생선', '어류'],
                '복숭아': ['복숭아', '과일'],
                '밀': ['밀', '밀가루', '밀글루텐', '밀전분', '밀효소'],
                '우유': ['우유', '전지분유', '탈지분유', '유크림', '가공유크림', '유당'],
                '대두': ['대두', '콩', '두부', '된장', '간장', '고추장', '콩기름'],
                '땅콩': ['땅콩', '피넛', '땅콩버터', '땅콩오일'],
                '견과류': ['호두', '잣', '아몬드', '캐슈넛', '피스타치오', '마카다미아'],
                '갑각류': ['새우', '게', '랍스터', '가재'],
                '조개류': ['조개', '굴', '전복', '홍합', '바지락', '관자'],
                '육류': ['쇠고기', '돼지고기', '닭고기', '양고기', '소고기', '돼지']
            }
            
            if user_allergen in special_mappings:
                print(f"특별 매핑 규칙 적용: '{user_allergen}'")
                for synonym in special_mappings[user_allergen]:
                    if synonym.lower() in t:
                        detected.append(user_allergen)
                        print(f"텍스트에서 '{synonym}' 발견 -> '{user_allergen}' 추가")
                        found_match = True
                        break
        
        # 4. 여전히 매칭이 안 되면 사용자 알레르기명을 직접 텍스트에서 찾기
        if not found_match and user_allergen_lower in t:
            detected.append(user_allergen)
            print(f"직접 텍스트 매칭: '{user_allergen}' 발견")
        
        if not found_match:
            print(f"매칭 실패: '{user_allergen}'")
    
    print(f"최종 사용자 알레르기 매칭 결과: {detected}")
    return list(set(detected))

def _map_korean_symptoms_to_english(symptoms: List[str]) -> List[str]:
    """
    한국어 증상명을 영어로 매핑 (fix_symptoms.js와 연결)
    """
    korean_to_english = {
        "호흡기": "respiratory",
        "심혈관": "cardiovascular", 
        "피부": "skin",
        "소화기": "gi",
        "신경계": "neurological",
        "구강알레르기": "oas"
    }
    
    mapped = []
    for symptom in symptoms or []:
        english_symptom = korean_to_english.get(symptom, symptom)
        mapped.append(english_symptom)
    
    return mapped

def _apply_basic_adjustments(score: int, symptoms: List[str], options: Dict[str, Any] = None) -> int:
    """보수적 보정: 다기관/fast_onset/free_label"""
    # 한국어 증상을 영어로 매핑
    english_symptoms = _map_korean_symptoms_to_english(symptoms)
    
    # 다기관
    distinct = len(set(english_symptoms or []))
    if distinct >= 3: score += 4
    elif distinct == 2: score += 2

    # 빠른 발현
    if options and options.get("fast_onset"):
        if "respiratory" in (english_symptoms or []) or "cardiovascular" in (english_symptoms or []):
            score += 2
        else:
            score += 1

    # FREE 문구
    if options and options.get("free_label"):
        score = max(0, score - 3)

    return score

def _condition_met(cond: str, score: int) -> bool:
    """
    'score>=9' 같은 비교식만 안전하게 평가.
    """
    if not isinstance(cond, str):
        return False
    txt = cond.replace(" ", "")
    ops = [(">=", operator.ge), ("<=", operator.le), (">", operator.gt),
           ("<", operator.lt), ("==", operator.eq)]
    for sym, fn in ops:
        if sym in txt:
            left, right = txt.split(sym, 1)
            if left != "score":
                return False
            try:
                threshold = int(right)
            except ValueError:
                return False
            return fn(score, threshold)
    return False

def _keyword_hit(text: str, condition: Dict[str, Any]) -> bool:
    """
    키워드 규칙 평가.
    condition 예:
      {"키워드규칙":[{"구분":"포함","패턴":"함유|포함|첨가"}, {"구분":"유래/추출","패턴":"유래|추출물|농축액|엑기스|가수분해|단백"}]}
    - '패턴'은 정규식 파이프(|) 형태 권장.
    """
    if not isinstance(condition, dict):
        return False

    # 지원 키: "키워드규칙" or "keyword_rules"
    rules = condition.get("키워드규칙") or condition.get("keyword_rules")
    if not isinstance(rules, list):
        return False

    txt = text or ""
    for r in rules:
        patt = (r or {}).get("패턴") or (r or {}).get("pattern")
        if patt:
            try:
                if re.search(patt, txt, flags=re.IGNORECASE):
                    return True
            except re.error:
                # 정규식 오류는 무시
                continue
    return False



def calculate_risk(
    detected: List[str],
    symptoms: List[str],
    options: Dict[str, Any] = None,
    *,
    text: str = ""
) -> Dict[str, Any]:
    """
    1) symptom_weights로 기본 점수
    2) 알레르기 성분 수에 따른 추가 점수
    3) 보정(다기관/fast_onset/free)
    4) risk_rules:
       - 문자열 condition: 점수 임계
       - dict condition: 키워드 규칙 → 텍스트 매칭
    두 형태가 동시에 매칭되면 더 높은 위험도로 합산.
    """
    weights = load_symptom_weights()
    rules   = load_risk_rules()

    # 기본 점수: 증상 기반
    base = sum(int(weights.get(s, 0)) for s in (symptoms or []))
    
    # 알레르기 성분 수에 따른 추가 점수
    allergen_count = len(detected) if detected else 0
    allergen_bonus = allergen_count * 2  # 알레르기 성분 1개당 2점 추가
    
    # 총 기본 점수
    total_base = base + allergen_bonus
    
    score = _apply_basic_adjustments(total_base, symptoms or [], options)

    level = "very_low"
    matched_any = False

    for r in rules:
        cond = (r or {}).get("condition")
        rl   = (r or {}).get("risk_level", "very_low").lower()

        # 점수 규칙
        if isinstance(cond, str) and _condition_met(cond, score):
            level = _max_level(level, rl)
            matched_any = True
            continue

        # 키워드 규칙
        if isinstance(cond, dict) and _keyword_hit(text, cond):
            level = _max_level(level, rl)
            matched_any = True
            continue

    # 규칙이 하나도 매칭되지 않은 경우 기본 맵 적용
    if not matched_any:
        default_map = [(9, "very_high"), (7, "high"), (5, "medium"), (3, "low")]
        for th, lv in default_map:
            if score >= th:
                level = lv
                break

    return {"score": score, "level": level}

def analyze_text(
    text: str,
    user_allergies: List[str],
    symptoms: List[str],
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    OCR로 추출된 텍스트를 기반으로 사용자 알레르기와 매칭하여 위험도 분석
    cursorAI-firestore-loader와 완전 연결된 버전
    """
    allergen_dict = load_allergen_dict()
    
    # 사용자 알레르기만 대상으로 감지
    detected = detect_allergens(text, user_allergies, allergen_dict)
    
    # 전체 알레르기 성분도 감지 (사용자에게 표시용)
    all_detected_allergens = detect_all_allergens(text, allergen_dict)
    
    # 위험도 계산 - 사용자 알레르기가 없으면 모든 감지된 알레르기를 기반으로 계산
    if not user_allergies or len(user_allergies) == 0:
        # 사용자 알레르기가 없는 경우, 감지된 모든 알레르기를 기반으로 위험도 계산
        risk = calculate_risk(all_detected_allergens, symptoms, options, text=text or "")
    else:
        # 사용자 알레르기가 있는 경우, 사용자 알레르기만 기반으로 계산
        risk = calculate_risk(detected, symptoms, options, text=text or "")
    
    # 추가 정보 제공
    result = {
        "detected_allergens": all_detected_allergens,  # 사용자에게 표시할 모든 감지된 알레르기
        "user_specific_allergens": detected,  # 사용자 알레르기와 매칭된 것만 (주의 필요)
        "score": risk["score"],
        "level": risk["level"],
        "user_allergies": user_allergies,  # 사용자가 선택한 알레르기 목록
        "total_ingredients_found": len(all_detected_allergens),  # 전체 감지된 알레르기 수
        "user_matched_count": len(detected),  # 사용자 알레르기와 매칭된 수
        "risk_factors": [],
        "symptoms_used": symptoms,
        "symptoms_mapped": _map_korean_symptoms_to_english(symptoms),
        "data_source": "firestore_connected",
        "matching_details": {
            "user_allergies_provided": len(user_allergies) if user_allergies else 0,
            "total_detected": len(all_detected_allergens),
            "user_matched": len(detected),
            "matching_rate": len(detected) / len(user_allergies) if user_allergies else 0
        }
    }
    
    # 위험 요인 분석
    if detected:
        result["risk_factors"].append(f"사용자 알레르기 {len(detected)}개 감지")
    
    if risk["score"] >= 7:
        result["risk_factors"].append("높은 위험도 점수")
    
    if options and options.get("fast_onset"):
        result["risk_factors"].append("빠른 발현 가능성")
    
    # 키워드 기반 위험도 추가 (fix_rules_keywords.js와 연결)
    if text:
        high_risk_keywords = ["함유", "포함", "첨가", "혼입", "가능"]
        keyword_count = sum(1 for keyword in high_risk_keywords if keyword in text)
        if keyword_count > 0:
            result["risk_factors"].append(f"위험 키워드 {keyword_count}개 발견")
    
    # 데이터베이스 연결 상태 확인
    try:
        allergen_dict = load_allergen_dict()
        symptom_weights = load_symptom_weights()
        risk_rules = load_risk_rules()
        
        result["database_status"] = {
            "allergen_data_loaded": len(allergen_dict) > 0,
            "symptom_weights_loaded": len(symptom_weights) > 0,
            "risk_rules_loaded": len(risk_rules) > 0,
            "total_allergens": len(allergen_dict),
            "total_symptoms": len(symptom_weights),
            "total_rules": len(risk_rules)
        }
    except Exception as e:
        result["database_status"] = {
            "error": str(e),
            "fallback_mode": True
        }
    
    return result