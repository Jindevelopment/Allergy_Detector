import firebase_admin
from firebase_admin import credentials, firestore

CRED = "/Users/mealkuo/Desktop/cursorAI_project/cursorAI-firestore-loader/serviceAccountKey.json"
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(CRED))
db = firestore.client()

for col in ["알레르겐_목록", "증상_가중치", "위험도_규칙"]:
    docs = list(db.collection(col).limit(3).stream())
    print(f"\n== {col} ({len(docs)}) ==")
    for d in docs:
        print(d.id, d.to_dict())

TEST_UID = "testUser1"

db.collection("사용자_정보").document(TEST_UID).set(
    {"닉네임":"성경","알레르겐":["peanut","wheat"]},
    merge=True,
)
print("\n[WRITE] 사용자_정보/testUser1 upsert 완료")

def add_report(uid, food, allergens, symptoms, score, severity):
    db.collection("사용자_보고").add({
        "사용자UID": uid,
        "음식명": food,
        "알레르겐_탐지": allergens,
        "증상_체크": symptoms,
        "총점": score,
        "최종위험도": severity,
    })

add_report(TEST_UID, "FREE 샘플", [], [], 5, "낮음")
add_report(TEST_UID, "땅콩 과자", ["peanut"], ["respiratory"], 95, "매우 높음")
add_report(TEST_UID, "밀·대두 요리", ["wheat","soy"], ["respiratory","skin"], 85, "높음")
print("[WRITE] 사용자_보고 QA 3건 작성 완료")

# 사용자_정보: 문서 ID로 직접 확인
info_doc = db.collection("사용자_정보").document(TEST_UID).get()
info_cnt = 1 if info_doc.exists else 0

# 사용자_보고: 한글 필드명은 백틱으로 escape
report_cnt = sum(1 for _ in db.collection("사용자_보고")
                 .where("`사용자UID`", "==", TEST_UID).stream())

print(f"\n[VERIFY] 사용자_정보 문서수(testUser1): {info_cnt}")
print(f"[VERIFY] 사용자_보고 문서수(testUser1): {report_cnt}")
print("\n[OK] Day3 테스트 완료")
