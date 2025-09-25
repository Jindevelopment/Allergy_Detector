const admin = require('firebase-admin');
admin.initializeApp({ credential: admin.credential.cert(require('./serviceAccountKey.json')) });
const db = admin.firestore();

function pad(n){return String(n).padStart(2,'0');}
function fmt(ts){
  const d = ts && ts.toDate ? ts.toDate() : new Date();
  return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}
// Firestore 문서 ID에서 금지문자 '/'만 다른 기호로 치환
function safeIdPart(s){
  return (s ?? '').toString().trim().replace(/\//g, '·').replace(/\s+/g,' ').slice(0,40);
}

(async () => {
  const coll = db.collection('사용자_보고');
  const snap = await coll.get();
  let moved = 0;

  for (const doc of snap.docs) {
    const data = doc.data() || {};
    const uid  = data['사용자UID'] || 'unknown';
    const ts   = data['생성시각'] || doc.createTime; // 필드가 없으면 생성시간 사용
    const food = safeIdPart(data['음식명'] || '보고');

    const newIdBase = `${uid}_${fmt(ts)}_${food}`;
    if (doc.id === newIdBase) continue; // 이미 좋은 ID면 스킵

    // 중복 방지
    let newId = newIdBase, idx = 1;
    while ((await coll.doc(newId).get()).exists) newId = `${newIdBase}_${idx++}`;

    const newRef = coll.doc(newId);

    // 새 문서 생성 후 원본 삭제
    await newRef.set(data, { merge: true });
    await doc.ref.delete();
    moved++;
  }
  console.log('사용자_보고 rekey 완료. 이동:', moved);
  process.exit(0);
})();
