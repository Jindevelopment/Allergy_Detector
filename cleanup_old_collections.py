import firebase_admin
from firebase_admin import credentials, firestore

# 🔑 서비스 키 절대 경로 (네 환경에 맞게)
KEY_PATH = "/Users/mealkuo/Desktop/cursorAI_project/cursorAI-firestore-loader/serviceAccountKey.json"

# 삭제할 (한글) 컬렉션 목록
OLD_COLLECTIONS = [
    "알레르겐_목록",
    "증상_가중치",
    "위험도_규칙",
    "사용자_정보",
    "사용자_보고",
]

BATCH_SIZE = 300  # 한 번에 지울 문서 수 (200~500 권장)

def delete_collection(db, collection_name, batch_size=BATCH_SIZE):
    print(f"\n🗑 Deleting collection: {collection_name}")
    col_ref = db.collection(collection_name)

    total_deleted = 0
    while True:
        # batch 단위로 문서 가져와 삭제
        docs = list(col_ref.limit(batch_size).stream())
        if not docs:
            break

        batch = db.batch()
        for doc in docs:
            # 필요한 경우, 하위 subcollection 정리 로직을 여기에 추가할 수 있음
            batch.delete(doc.reference)
        batch.commit()

        total_deleted += len(docs)
        print(f"  - Deleted {len(docs)} docs (accumulated: {total_deleted})")

    print(f"✅ Done: {collection_name} (total deleted: {total_deleted})")

def main():
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    for name in OLD_COLLECTIONS:
        delete_collection(db, name, BATCH_SIZE)

    print("\n🎉 All old (Korean-named) collections have been cleared.")

if __name__ == "__main__":
    main()