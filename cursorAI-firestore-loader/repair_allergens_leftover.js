const admin = require('firebase-admin');
admin.initializeApp({ credential: admin.credential.cert(require('./serviceAccountKey.json')) });
const db = admin.firestore();

(async () => {
  const coll = db.collection('알레르겐_목록');
  const snap = await coll.get();
  let moved = 0, fixed = 0;

  for (const doc of snap.docs) {
    const x = doc.data() || {};
    const name = (x['표시명'] || '').toString().trim();

    // 표시명이 비어 있으면 동의어[0] 또는 기존 ID를 사용
    if (!name) {
      const syn = Array.isArray(x['동의어']) && x['동의어'][0] ? x['동의어'][0] : doc.id;
      const newId = syn;

      if (newId === doc.id) {
        // ID는 그대로 두고 표시명만 채움
        await doc.ref.set({ '표시명': newId }, { merge: true });
        fixed++;
      } else {
        // 새 문서로 복사 후 원본 삭제
        const newRef = coll.doc(newId);
        await newRef.set({ ...x, '표시명': newId }, { merge: true });
        await doc.ref.delete();
        moved++;
      }
    }
  }
  console.log(`leftover 처리: 표시명만 채움 ${fixed}건, 재키 ${moved}건`);
  process.exit(0);
})();
