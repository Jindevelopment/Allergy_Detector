const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');

admin.initializeApp({ credential: admin.credential.cert(require('./serviceAccountKey.json')) });
const db = admin.firestore();

const CSV = path.join(__dirname, '../db_setup/data/csv/알레르겐_목록.csv');
const DRY = process.argv.includes('--dry-run');
const PRUNE = process.argv.includes('--prune');

const stripBOM = s => (s ?? '').toString().replace(/^\uFEFF/, '');
const norm = s => stripBOM(s).trim();
const toList = s => stripBOM(s).split(/[;|,，、\/·•∙]/).map(v=>v.trim()).filter(Boolean);
const toBool = v => /^(true|1|y|yes|t|참|예)$/i.test((v??'').toString().trim());
const toNum  = v => { const t=(v??'').toString().replace(/[^\d.-]/g,'').trim(); return t===''?null:Number(t); };

// 문서 ID로 쓸 때 위험문자 치환: "/" 만 금지. (원문은 '표시명'에 그대로 둠)
const safeId = s => norm(s).replace(/\//g, '／'); // U+FF0F

(async () => {
  // CSV 로드
  const rows = [];
  await new Promise((res, rej) => {
    fs.createReadStream(CSV).pipe(csv())
      .on('data', r => rows.push(r))
      .on('end', res).on('error', rej);
  });
  if (!rows.length) { console.error('CSV 행이 없습니다.'); process.exit(1); }

  // 헤더 매핑(완전 관대)
  const headerMap = k => norm(k).replace(/\s+/g,'');
  const keyOf = (row, candidates) => {
    const inv = new Map(Object.keys(row).map(k => [headerMap(k), k]));
    for (const c of candidates) { const real = inv.get(headerMap(c)); if (real) return real; }
    return null;
  };
  const C = {
    표준명: ['표준명','표시명','이름','항목','품목','표준'],
    동의어: ['동의어','유의어','키워드','동의어리스트','동의어목록'],
    대표군: ['대표군','분류','카테고리','군','그룹'],
    증상  : ['증상','관련증상','주증상','증상구분'],
    보수점: ['보수적점수','보수 점수','보수점수','보수평가점수','보수적 점수'],
    주요  : ['주요알레르겐','주요','메이저','중요'],
  };

  const keep = new Set();
  const seen = new Map();  // 안전ID 중복 감지

  // 사전 스캔: 안전ID 충돌 체크
  for (const r of rows) {
    const kStd = keyOf(r, C.표준명);
    const rawName = kStd ? norm(r[kStd]) : '';
    if (!rawName) continue;
    const sid = safeId(rawName);
    if (seen.has(sid) && seen.get(sid) !== rawName) {
      console.warn(`[WARN] 안전ID 충돌: "${seen.get(sid)}" vs "${rawName}" -> ID "${sid}"`);
    } else {
      seen.set(sid, rawName);
    }
  }

  let wrote = 0;
  for (const r of rows) {
    const kStd = keyOf(r, C.표준명);
    const rawName = kStd ? norm(r[kStd]) : '';
    if (!rawName) continue;

    const kSyn = keyOf(r, C.동의어);
    const kGrp = keyOf(r, C.대표군);
    const kSym = keyOf(r, C.증상);
    const kSc  = keyOf(r, C.보수점);
    const kMaj = keyOf(r, C.주요);

    const data = {
      표시명: rawName,                      // 화면/검색용: 원문 유지
      이름  : rawName,
      분류  : kGrp ? norm(r[kGrp]) : '',
      증상  : kSym ? norm(r[kSym]) : '',
      보수적점수: toNum(kSc ? r[kSc] : ''),
      동의어: Array.from(new Set(toList(kSyn ? r[kSyn] : ''))),
      주요알레르겐: toBool(kMaj ? r[kMaj] : false),
      업데이트시각: admin.firestore.FieldValue.serverTimestamp(),
    };

    const docId = safeId(rawName); // ← 문서 ID는 안전문자 사용
    if (DRY) {
      console.log('[DRY]', docId, data);
      continue;
    }
    await db.collection('알레르겐_목록').doc(docId).set(data, { merge: false }); // 완전 덮어쓰기
    keep.add(docId);
    wrote++;
  }

  console.log('[업로드 완료] 문서 수:', DRY ? 'DRY' : wrote);

  // 옵션: CSV에 없는 이전 문서 삭제
  if (!DRY && PRUNE) {
    const snap = await db.collection('알레르겐_목록').get();
    let del = 0;
    for (const d of snap.docs) {
      if (!keep.has(d.id)) { await d.ref.delete(); del++; }
    }
    console.log('[정리 삭제]', del);
  }

  process.exit(0);
})();
