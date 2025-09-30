from datetime import datetime
from services.db_client import get_db

def get_db_instance():
    """지연 초기화를 위한 DB 인스턴스 가져오기"""
    return get_db()

def list_allergies(user_id: str) -> list[dict]:
    db = get_db_instance()
    docs = db.collection("users").document(user_id).collection("allergies").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

def add_allergy(user_id: str, allergen_name: str, severity: str) -> bool:
    db = get_db_instance()
    allergies_ref = db.collection("users").document(user_id).collection("allergies")
    existing = allergies_ref.where("allergen_name", "==", allergen_name).get()
    if existing:
        return False
    payload = {
        "allergen_name": allergen_name,
        "severity": severity,
        "created_at": datetime.utcnow()
    }
    allergies_ref.add(payload)
    return True

def remove_allergy(user_id: str, allergy_doc_id: str) -> None:
    db = get_db_instance()
    db.collection("users").document(user_id).collection("allergies").document(allergy_doc_id).delete()