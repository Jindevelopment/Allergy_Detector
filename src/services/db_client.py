import firebase_admin
from firebase_admin import credentials, firestore
import os

_db = None

def init_firestore(key_path: str = None):
    """
    Firestore 클라이언트 초기화
    key_path 없으면 GOOGLE_APPLICATION_CREDENTIALS 환경변수 사용
    """
    global _db
    if _db:
        return _db

    if not firebase_admin._apps:
        if key_path:
            cred = credentials.Certificate(key_path)
        else:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db

def get_db():
    """이미 초기화된 Firestore 클라이언트 반환"""
    global _db
    if not _db:
        init_firestore()
    return _db