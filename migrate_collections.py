import firebase_admin
from firebase_admin import credentials, firestore

# ✅ 서비스 계정 키 절대 경로
KEY_PATH = "/Users/mealkuo/Desktop/cursorAI_project/cursorAI-firestore-loader/serviceAccountKey.json"

# Firebase 초기화
cred = credentials.Certificate(KEY_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

# ✅ 컬렉션명 매핑 (한글 → 영어)
collection_mapping = {
    "알레르겐_목록": "allergen_list",
    "증상_가중치": "symptom_weights",
    "위험도_규칙": "risk_rules",
    "사용자_정보": "users",
    "사용자_보고": "user_reports",
}

# ✅ 필드명 매핑 (한글 → 영어)
field_mappings = {
    "알레르겐_목록": {
        "표시명": "display_name",
        "이름": "name",
        "분류": "category",
        "동의어": "synonyms",
        "증상": "symptom",
        "보수적점수": "base_score",
        "주요알레르겐": "is_major",
    },
    "증상_가중치": {
        "증상계통": "symptom_system",
        "대표증상": "examples",
        "기본점수": "base_score",
        "보수규칙": "rule",
        "비고": "note",
    },
    "위험도_규칙": {
        "조건": "condition",
        "위험도": "risk_level",
        "중증도": "severity",
    },
    "사용자_정보": {
        "id": "user_id",
        "닉네임": "nickname",
        "알레르겐": "allergens",
    },
    "사용자_보고": {
        "id": "report_id",
        "사용자UID": "user_id",
        "음식명": "food_name",
        "알레르겐_탐지": "detected_allergens",
        "증상_체크": "symptom_check",
        "총점": "total_score",
        "최종위험도": "final_risk",
    },
}


def migrate_collection(old_name, new_name, mapping):
    print(f"\n🚀 Migrating collection: {old_name} → {new_name}")
    docs = db.collection(old_name).stream()

    for doc in docs:
        data = doc.to_dict()
        new_data = {}

        # 필드명 변환
        for key, value in data.items():
            if key in mapping:
                new_data[mapping[key]] = value
            else:
                new_data[key] = value  # 매핑 없는 필드는 그대로

        # 새 컬렉션에 저장
        db.collection(new_name).document(doc.id).set(new_data)
        print(f"   ✅ Migrated doc: {doc.id}")

    print(f"🎉 Done: {old_name} → {new_name}")


def main():
    for old, new in collection_mapping.items():
        mapping = field_mappings.get(old, {})
        migrate_collection(old, new, mapping)

    print("\n✨ All collections migrated successfully!")


if __name__ == "__main__":
    main()