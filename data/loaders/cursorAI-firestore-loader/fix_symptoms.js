const admin = require('firebase-admin');
const fs = require('fs');
const csv = require('csv-parser');
const path = require('path');

admin.initializeApp({ credential: admin.credential.cert(require('./serviceAccountKey.json')) });
const db = admin.firestore();
const CSV = path.join(__dirname, '../db_setup/data/csv/증상_가중치.csv');

const strip = s => (s ?? '').toString().replace(/^\uFEFF/, '').trim();
// 쉼표/세미콜론/슬래시/중점 등 대부분 분리자 대응
const toList = s => strip(s).replace(/[·•∙]/g, ',').split(/[;,，、/]/).map(v=>v.trim()).filter(Boolean);
const toNum  = s => { const v = strip(s).replace(/[^\d.\-]/g,''); return v===''?null:Number(v); };

(async () => {
  const rows=[];
  await new Promise((res,rej)=>{
    fs.createReadStream(CSV).pipe(csv())
      .on('data', r => {
        const n={}; for (const k of Object.keys(r)) n[strip(k)] = strip(r[k]); rows.push(n);
      }).on('end',res).on('error',rej);
  });

  const batch = db.batch(); const keep = new Set();
  for (const r of rows) {
    const name  = r['증상계통'] || r['표시명'] || r['이름'] || '';
    if (!name) continue;
    const reps  = toList(r['대표증상'] || r['증상목록'] || '');
    const score = toNum(r['기본점수'] || r['가중치'] || '');
    const rule  = r['보수규칙'] || '';
    const note  = r['비고'] || '';

    const ref = db.collection('증상_가중치').doc(name); keep.add(name);
    batch.set(ref, {
      '증상계통': name,
      '대표증상': reps,              // 배열
      '기본점수': score,             // 숫자
      '보수규칙': rule || admin.firestore.FieldValue.delete(),
      '비고':     note || admin.firestore.FieldValue.delete(),
      '업데이트시각': admin.firestore.FieldValue.serverTimestamp(),
    }, { merge:true });
  }
  await batch.commit();

  // 예전에 생긴 빈 문서 정리
  const snap = await db.collection('증상_가중치').get();
  const b2 = db.batch(); let del=0;
  snap.forEach(d=>{
    const x=d.data()||{}; const reps=x['대표증상']||x['증상목록']||[];
    const sc=x['기본점수']; const bad=(Array.isArray(reps)&&reps.length===0)&&(sc===null||sc===undefined);
    if (!keep.has(d.id) && bad) { b2.delete(d.ref); del++; }
  });
  if (del) await b2.commit();
  console.log('증상_가중치 교정 완료. 입력행:', rows.length, '정리된 문서:', del);
  process.exit(0);
})();
