const admin = require('firebase-admin');
const fs = require('fs');
const csv = require('csv-parser');
const path = require('path');

admin.initializeApp({ credential: admin.credential.cert(require('./serviceAccountKey.json')) });
const db = admin.firestore();

const CSV = path.join(__dirname, '../db_setup/data/csv/알레르겐_목록.csv');
const strip = s => (s ?? '').toString().replace(/^\uFEFF/, '').trim();
const toList = s => strip(s).split(/[;|,，、]/).map(v=>v.trim()).filter(Boolean);
const toNum  = s => { const v = strip(s).replace(/[^\d.\-]/g,''); return v===''?null:Number(v); };

(async () => {
  // 1) CSV 파싱 (헤더/값 BOM 제거)
  const rows = [];
  await new Promise((res, rej) => {
    fs.createReadStream(CSV)
      .pipe(csv())
      .on('data', r => { const n={}; for (const k of Object.keys(r)) n[strip(k)] = strip(r[k]); rows.push(n); })
      .on('end', res).on('error', rej);
  });

  // 2) 표준명(=표시명)을 Doc ID로 업서트
  const keep = new Set();
  const batch = db.batch();
  for (const r of rows) {
    const name = r['표준명'] || r['표시명'] || r['이름'] || '';
    if (!name) { console.warn('WARN: 표준명 없음, 건너뜀:', r); continue; }
    keep.add(name);
    const ref = db.collection('알레르겐_목록').doc(name);

    const data = {
      '표시명': name,
      '분류': r['대표군'] || r['분류'] || '',
      '증상': r['증상'] || '',
      '보수적점수': toNum(r['보수적점수'] || r['보수점수'] || ''),
      '동의어': Array.from(new Set(toList(r['동의어'] || ''))),
      '업데이트시각': admin.firestore.FieldValue.serverTimestamp(),
    };

    if (r['주요알레르겐'] !== undefined) {
      const b = r['주요알레르겐'];
      data['주요알레르겐'] = /^(true|1|y|yes|t|참|예)$/i.test(b);
    }

    batch.set(ref, data, { merge: true });
  }
  await batch.commit();

  // 3) CSV에 없는 기존 랜덤-ID 문서 삭제
  const snap = await db.collection('알레르겐_목록').get();
  const b2 = db.batch(); let del = 0;
  snap.forEach(d => { if (!keep.has(d.id)) { b2.delete(d.ref); del++; }});
  if (del) await b2.commit();

  console.log('알레르겐_목록 재정렬 완료. 입력행:', rows.length, '삭제:', del);
  process.exit(0);
})();
