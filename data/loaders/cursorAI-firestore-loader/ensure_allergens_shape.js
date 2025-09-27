const admin = require('firebase-admin');
const fs = require('fs');
const csv = require('csv-parser');
const path = require('path');

admin.initializeApp({ credential: admin.credential.cert(require('./serviceAccountKey.json')) });
const db = admin.firestore();

const STRICT = process.argv.includes('--strict');
const PRUNE  = process.argv.includes('--prune');

const CSV = path.join(__dirname, '../db_setup/data/csv/알레르겐_목록.csv');
const strip = s => (s ?? '').toString().replace(/^\uFEFF/, '').trim();
const toList = s => strip(s).split(/[;|,，、]/).map(v=>v.trim()).filter(Boolean);
const toBoolLike = v => /^(true|1|y|yes|t|참|예)$/i.test(String(v||'').trim());

// ❗️여기에 '증상', '보수적점수' 추가
const ALLOWED = new Set(['표시명','동의어','주요알레르겐','분류','이름','증상','보수적점수','업데이트시각']);

(async () => {
  const rows = [];
  await new Promise((res, rej) => {
    fs.createReadStream(CSV).pipe(csv())
      .on('data', r => { const n={}; for(const k of Object.keys(r)) n[strip(k)] = strip(r[k]); rows.push(n); })
      .on('end', res).on('error', rej);
  });

  const keep = new Set();
  const batch = db.batch();

  for (const r of rows) {
    const name = r['표준명'] || r['표시명'] || r['이름'] || '';
    if (!name) continue;
    keep.add(name);

    // CSV에 있는 값들을 그대로 반영
    const data = {
      '표시명': name,
      '동의어': Array.from(new Set(toList(r['동의어'] || ''))),
      '주요알레르겐': r['주요알레르겐'] !== undefined ? toBoolLike(r['주요알레르겐']) : false,
      '분류': r['대표군'] || r['분류'] || '',
      '이름': r['이름'] || '',
      '증상': r['증상'] || '',
      // 숫자 파싱(없으면 null)
      '보수적점수': (() => { const v=(r['보수적점수']||r['보수점수']||'').replace(/[^\d.\-]/g,''); return v?Number(v):null; })(),
      '업데이트시각': admin.firestore.FieldValue.serverTimestamp(),
    };

    const ref = db.collection('알레르겐_목록').doc(name);
    batch.set(ref, data, { merge: true });
  }
  await batch.commit();

  if (STRICT) {
    const snap = await db.collection('알레르겐_목록').get();
    const b2 = db.batch(); let delKeys = 0;
    snap.forEach(d => {
      const x = d.data() || {};
      Object.keys(x).forEach(k => {
        if (!ALLOWED.has(k)) { b2.update(d.ref, { [k]: admin.firestore.FieldValue.delete() }); delKeys++; }
      });
    });
    if (delKeys) await b2.commit();
    console.log('불필요 필드 삭제:', delKeys);
  }

  if (PRUNE) {
    const snap = await db.collection('알레르겐_목록').get();
    const b3 = db.batch(); let delDocs = 0;
    snap.forEach(d => { if (!keep.has(d.id)) { b3.delete(d.ref); delDocs++; }});
    if (delDocs) await b3.commit();
    console.log('CSV에 없는 문서 삭제:', delDocs);
  }

  console.log('알레르겐_목록 정렬 완료. 입력행:', rows.length);
  process.exit(0);
})();
