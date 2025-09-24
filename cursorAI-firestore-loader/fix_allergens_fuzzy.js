const admin = require('firebase-admin');
const fs = require('fs');
const csv = require('csv-parser');
const path = require('path');

admin.initializeApp({ credential: admin.credential.cert(require('./serviceAccountKey.json')) });
const db = admin.firestore();

const CSV = path.join(__dirname, '../db_setup/data/csv/알레르겐_목록.csv');

// -------- util ----------
const stripBOM = s => (s ?? '').toString().replace(/^\uFEFF/, '');
const norm = s => stripBOM(s).trim().replace(/\s+/g,'').replace(/[._\-\/]/g,'');
const toList = s => stripBOM(s).split(/[;|,，、\/·•∙]/).map(v=>v.trim()).filter(Boolean);
const toBool = v => /^(true|1|y|yes|t|참|예)$/i.test((v??'').toString().trim());
const toNum  = v => {
  const t = (v??'').toString().replace(/[^\d.-]/g,'').trim();
  return t === '' ? null : Number(t);
};

// 헤더 후보(퍼지 매칭용)
const COLS = {
  표준명: ['표준명','표시명','이름','항목','품목','표준'],
  동의어: ['동의어','유의어','키워드','동의어리스트','동의어목록'],
  대표군: ['대표군','분류','카테고리','군','그룹'],
  증상:   ['증상','관련증상','주증상','증상구분'],
  보점:   ['보수적점수','보수점수','보수적 점수','보수 점수','보수평가점수'],
  주요:   ['주요알레르겐','주요','메이저','중요']
};

function pick(row, aliases){
  const m = new Map();
  for (const k of Object.keys(row)) m.set(norm(k), k);
  for (const a of aliases){
    const key = m.get(norm(a));
    if (key && row[key] !== undefined) return stripBOM(row[key]);
  }
  return '';
}

(async ()=>{
  // CSV 로드 + 퍼지 매핑
  const rows = [];
  await new Promise((res,rej)=>{
    fs.createReadStream(CSV).pipe(csv())
      .on('data', r => rows.push(r))
      .on('end', res).on('error', rej);
  });

  const batch = db.batch(); const keep = new Set();

  rows.forEach((r, i) => {
    const name  = pick(r, COLS.표준명);
    if (!name) { console.warn('표준명 누락 행 스킵:', i+1); return; }

    const group = pick(r, COLS.대표군);
    const syns  = toList(pick(r, COLS.동의어));
    const sym   = pick(r, COLS.증상);
    const cons  = pick(r, COLS.보점);
    const major = pick(r, COLS.주요);

    const data = {
      '표시명': name,
      '동의어': Array.from(new Set(syns)),
      '분류': group || '',                 // CSV에 없으면 빈문자 (기존값 유지 원하면 조건부로 변경 가능)
      '이름': name,                        // 이름도 기본은 표시명과 동일하게 채움
      '증상': sym || '',
      '보수적점수': toNum(cons),
      '주요알레르겐': toBool(major),
      '업데이트시각': admin.firestore.FieldValue.serverTimestamp(),
    };

    const ref = db.collection('알레르겐_목록').doc(name);
    batch.set(ref, data, { merge: true });
    keep.add(name);
  });

  await batch.commit();
  console.log('알레르겐_목록 퍼지 업서트 완료:', rows.length);

  // CSV에 없는 이전 랜덤 문서 정리(원하면 주석 해제)
  // const snap = await db.collection('알레르겐_목록').get();
  // const b2 = db.batch(); let del = 0;
  // snap.forEach(d => { if (!keep.has(d.id)) { b2.delete(d.ref); del++; }});
  // if (del) await b2.commit(), console.log('정리 삭제:', del);

  process.exit(0);
})();
