const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');

admin.initializeApp({ credential: admin.credential.cert(require('./serviceAccountKey.json')) });
const db = admin.firestore();

const CSV = path.join(__dirname, '../db_setup/data/csv/알레르겐_목록.csv');
const PRUNE = process.argv.includes('--prune'); // CSV에 없는 문서 삭제
const DRY   = process.argv.includes('--dry-run'); // 미리보기만

// ---------- utils ----------
const stripBOM = s => (s ?? '').toString().replace(/^\uFEFF/, '');
const norm = s => stripBOM(s).trim().replace(/\s+/g,'').replace(/[._\-\/]/g,'');
const toList = s => stripBOM(s).split(/[;|,，、\/·•∙]/).map(v=>v.trim()).filter(Boolean);
const toBool = v => /^(true|1|y|yes|t|참|예)$/i.test((v??'').toString().trim());
const toNum  = v => {
  const t = (v??'').toString().replace(/[^\d.-]/g,'').trim();
  return t === '' ? null : Number(t);
};

// 헤더 퍼지 매칭 후보
const COLS = {
  표준명: ['표준명','표시명','이름','항목','품목','표준'],
  동의어: ['동의어','유의어','키워드','동의어리스트','동의어목록'],
  대표군: ['대표군','분류','카테고리','군','그룹'],
  증상:   ['증상','관련증상','주증상','증상구분'],
  보수점: ['보수적점수','보수 점수','보수점수','보수평가점수','보수적 점수'],
  주요:   ['주요알레르겐','주요','메이저','중요']
};

function resolveKeyMap(row) {
  const keys = Object.keys(row);
  const map = {}; // logical -> real
  const inv = new Map(keys.map(k => [norm(k), k]));
  for (const [logical, aliases] of Object.entries(COLS)) {
    for (const a of aliases) {
      const r = inv.get(norm(a));
      if (r) { map[logical] = r; break; }
    }
  }
  return { map, keys };
}

(async () => {
  // 0) 읽어서 헤더 매핑 확인
  const rows = [];
  await new Promise((res, rej) => {
    fs.createReadStream(CSV).pipe(csv())
      .on('data', r => rows.push(r))
      .on('end', res).on('error', rej);
  });
  if (!rows.length) { console.error('CSV에 행이 없습니다.'); process.exit(1); }

  const { map, keys } = resolveKeyMap(rows[0]);
  console.log('[CSV 헤더]', keys);
  console.log('[매핑]', map);

  // 1) 백업(안전용)
  const backup = [];
  const snap0 = await db.collection('알레르겐_목록').get();
  snap0.forEach(d => backup.push({ id: d.id, data: d.data() }));
  const bakPath = path.join(__dirname, `backup_알레르겐_목록_${Date.now()}.json`);
  fs.writeFileSync(bakPath, JSON.stringify(backup, null, 2));
  console.log('[백업] 저장됨 →', bakPath);

  // 2) CSV → Firestore (강제 덮어쓰기: merge=false)
  const keep = new Set();
  let i = 0;
  for (const r of rows) {
    const name = stripBOM(r[map.표준명] ?? '').trim();
    if (!name) { console.warn('표준명 누락 행 스킵', r); continue; }
    keep.add(name);

    const data = {
      // ← 최종 스키마를 여기에 “정확히” 정의
      '표시명': name,
      '이름'  : name,                                                // 기본 = 표준명
      '분류'  : stripBOM(r[map.대표군] ?? ''),                        // 대표군/분류
      '증상'  : stripBOM(r[map.증상]   ?? ''),                        // 증상
      '보수적점수': toNum(r[map.보수점] ?? ''),                       // 숫자
      '동의어': Array.from(new Set(toList(r[map.동의어] ?? ''))),     // 배열
      '주요알레르겐': toBool(r[map.주요] ?? false),
      '업데이트시각': admin.firestore.FieldValue.serverTimestamp(),
    };

    if (DRY) {
      console.log('[DRY]', name, data);
      continue;
    }

    // 완전 덮어쓰기(불일치 필드 제거)
    await db.collection('알레르겐_목록').doc(name).set(data, { merge: false });
    if (++i % 50 === 0) console.log(`... ${i}개 처리`);
  }
  console.log('[업로드] 완료. 총 처리:', DRY ? 'DRY' : i);

  // 3) CSV에 없는 이전 문서 제거 (옵션)
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
