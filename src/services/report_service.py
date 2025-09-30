from datetime import datetime
from services.db_client import get_db

def get_db_instance():
    """지연 초기화를 위한 DB 인스턴스 가져오기"""
    return get_db()

def save_report(user_id: str, food_name: str, detected_allergens: list[str], symptom_check: list[str], total_score: int, final_risk: str) -> str:
    payload = {
        "user_id": user_id,
        "food_name": food_name,
        "detected_allergens": detected_allergens,
        "symptom_check": symptom_check,
        "total_score": total_score,
        "final_risk": final_risk,
        "created_at": datetime.utcnow()
    }
    db = get_db_instance()
    ref = db.collection("user_reports").add(payload)
    return ref[1].id

def get_recent_reports(user_id: str, limit: int = 3) -> list[dict]:
    db = get_db_instance()
    docs = (
        db.collection("user_reports")
        .where("user_id", "==", user_id)
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]