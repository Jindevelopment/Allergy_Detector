# backend/risk_service.py
from backend.db_client import get_db
import re
import operator
from typing import List, Dict, Any

db = get_db()

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
    allergen_list 문서: { display_name, synonyms: [..] }
    반환: {display_name: [synonyms..., display_name]}
    """
    out: Dict[str, List[str]] = {}
    for doc in db.collection("allergen_list").stream():
        d = doc.to_dict() or {}
        name = d.get("display_name")
        syns = d.get("synonyms", []) or []
        if name:
            out[name] = list({*(syns or []), name})
    return out

def load_symptom_weights() -> Dict[str, int]:
    """
    symptom_weights 문서: { symptom_system, base_score }
    예) {"respiratory": 4, "cardiovascular":5, "skin":1, "gi":2, "oas":1}
    """
    out: Dict[str, int] = {}
    for doc in db.collection("symptom_weights").stream():
        d = doc.to_dict() or {}
        key = d.get("symptom_system")
        val = d.get("base_score", 0)
        if key:
            out[key] = int(val)
    return out

def load_risk_rules() -> List[Dict[str, Any]]:
    """
    risk_rules 문서 예시
      - 점수형: {"condition":"score>=9", "risk_level":"very_high"}
      - 키워드형: {"condition":{"키워드규칙":[{"구분":"포함","패턴":"함유|포함|첨가"}, ...]},
                  "risk_level":"high"}
    선택: {"priority": 10} 를 두어 평가 순서를 제어 가능(낮을수록 먼저)
    """
    rules = []
    for doc in db.collection("risk_rules").stream():
        d = doc.to_dict() or {}
        rules.append(d)
    # priority가 있으면 오름차순으로, 없으면 그대로
    rules.sort(key=lambda r: r.get("priority", 9999))
    return rules

def detect_allergens(text: str, user_allergies: List[str], allergen_dict: Dict[str, List[str]] | None=None) -> List[str]:
    """
    사용자 프로필 알레르겐(user_allergies)만 대상으로 텍스트 매칭
    """
    if allergen_dict is None:
        allergen_dict = load_allergen_dict()
    t = (text or "").lower()
    detected = []
    for allergen in user_allergies or []:
        for s in allergen_dict.get(allergen, []):
            if s and str(s).lower() in t:
                detected.append(allergen)
                break
    return list(set(detected))

def _apply_basic_adjustments(score: int, symptoms: List[str], options: Dict[str, Any] | None) -> int:
    """보수적 보정: 다기관/fast_onset/free_label"""
    # 다기관
    distinct = len(set(symptoms or []))
    if distinct >= 3: score += 4
    elif distinct == 2: score += 2

    # 빠른 발현
    if options and options.get("fast_onset"):
        if "respiratory" in (symptoms or []) or "cardiovascular" in (symptoms or []):
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

# risk_service.py (calculate_risk 위에 추가)
def _apply_basic_adjustments(score: int, symptoms: list[str], options: dict | None) -> int:
    """보수적 보정: 다기관/fast_onset/free_label"""
    # 다기관 가산
    distinct = len(set(symptoms or []))
    if distinct >= 3:
        score += 4
    elif distinct == 2:
        score += 2

    # 빠른 발현
    if options and options.get("fast_onset"):
        if "respiratory" in (symptoms or []) or "cardiovascular" in (symptoms or []):
            score += 2
        else:
            score += 1

    # FREE/무첨가 문구 감산
    if options and options.get("free_label"):
        score = max(0, score - 3)

    return score


def calculate_risk(
    detected: List[str],
    symptoms: List[str],
    options: Dict[str, Any] | None = None,
    *,
    text: str = ""
) -> Dict[str, Any]:
    """
    1) symptom_weights로 기본 점수
    2) 보정(다기관/fast_onset/free)
    3) risk_rules:
       - 문자열 condition: 점수 임계
       - dict condition: 키워드 규칙 → 텍스트 매칭
    두 형태가 동시에 매칭되면 더 높은 위험도로 합산.
    """
    weights = load_symptom_weights()
    rules   = load_risk_rules()

    base = sum(int(weights.get(s, 0)) for s in (symptoms or []))
    score = _apply_basic_adjustments(base, symptoms or [], options)

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
    options: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    allergen_dict = load_allergen_dict()
    detected = detect_allergens(text, user_allergies, allergen_dict)
    risk = calculate_risk(detected, symptoms, options, text=text or "")
    return {"detected_allergens": detected, **risk}