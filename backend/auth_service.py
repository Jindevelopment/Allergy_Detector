import bcrypt
from datetime import datetime
from backend.db_client import get_db

db = get_db()

def user_exists(user_id: str) -> bool:
    doc = db.collection("users").document(user_id).get()
    return doc.exists

def register_user(user_id: str, password: str, nickname: str) -> dict:
    if user_exists(user_id):
        raise ValueError("이미 존재하는 사용자입니다.")

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    payload = {
        "user_id": user_id,
        "nickname": nickname,
        "password_hash": hashed_pw,
        "created_at": datetime.utcnow(),
        "last_login": None,
    }
    db.collection("users").document(user_id).set(payload)
    return {"user_id": user_id, "nickname": nickname}

def check_login(user_id: str, password: str) -> dict:
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        raise ValueError("사용자가 존재하지 않습니다.")

    data = doc.to_dict()
    if bcrypt.checkpw(password.encode(), data["password_hash"].encode()):
        db.collection("users").document(user_id).update(
            {"last_login": datetime.utcnow()}
        )
        return {"user_id": user_id, "nickname": data["nickname"]}
    else:
        raise ValueError("비밀번호가 일치하지 않습니다.")

def get_user(user_id: str) -> dict | None:
    doc = db.collection("users").document(user_id).get()
    return doc.to_dict() if doc.exists else None