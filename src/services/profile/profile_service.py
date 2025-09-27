from datetime import datetime
from src.database.clients.db_client import get_db

db = get_db()

def list_allergies(user_id: str) -> list[dict]:
    docs = db.collection("users").document(user_id).collection("allergies").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

def add_allergy(user_id: str, allergen_name: str, severity: str) -> bool:
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
    db.collection("users").document(user_id).collection("allergies").document(allergy_doc_id).delete()