from backend.risk_service import analyze_text

def analyze_text_only(text: str, symptoms: list[str], options=None):
    """
    비회원 분석: DB 저장하지 않고 위험도 계산만 반환
    """
    # 비회원은 user_allergies 없음 → 전체 allergen_list 기준?
    # 혹은 알레르겐 선택 UI 없이 증상 기반만?
    # 여기서는 "알레르겐 매칭 없이 증상 기반 점수" 버전으로 둠
    return analyze_text(text, [], symptoms, options)