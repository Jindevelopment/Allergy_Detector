const fs = require("fs");
const path = require("path");
const csv = require("csv-parser");
const admin = require("firebase-admin");

const keyPath = path.resolve(__dirname, "serviceAccountKey.json");
if (!fs.existsSync(keyPath)) {
  console.error("[ERR] serviceAccountKey.json 이 없습니다. 콘솔에서 발급해서 이 폴더에 넣어주세요.");
  process.exit(1);
}
admin.initializeApp({ credential: admin.credential.cert(require(keyPath)) });
const db = admin.firestore();
const FieldValue = admin.firestore.FieldValue;

const CSV_DIR = path.resolve(__dirname, "../db_setup/data/csv");

// ── 유틸
const strip = (s) => (typeof s === "string" ? s.replace(/\uFEFF/g, "").trim() : s);
const splitArr = (s) => !s ? [] : strip(s).split(/[|,\/，、;；]/).map(x=>x.trim()).filter(Boolean);
const toBool  = (s) => ["true","1","yes","y","예","참","t"].includes(String(s).toLowerCase().trim());
const toNum   = (s) => { if(s===""||s==null) return null; const n=Number(String(s).replace(/,/g,"")); return Number.isNaN(n)?null:n; };
const slug    = (s) => strip(s).toLowerCase().replace(/[^\w가-힣]+/g,"-").replace(/^-+|-+$/g,"");

// 후보 키들 중 실제 CSV에 존재하는 "출력용 키 이름"을 결정
const resolveOutputKeys = (headerRow, candidatesMap) => {
  const out = {};
  for (const [slot, candidates] of Object.entries(candidatesMap)) {
    out[slot] = candidates.find(k => Object.prototype.hasOwnProperty.call(headerRow, k)) || candidates[0];
  }
  return out;
};
// 여러 후보 키에서 값 꺼내기
const pick = (row, keys=[]) => {
  for (const k of keys) {
    if (k in row && row[k] != null && String(row[k]).trim() !== "") return strip(row[k]);
  }
  return "";
};
// 자동/명시 ID
const docRef = (col, id) => (id ? db.collection(col).doc(id) : db.collection(col).doc());

// ── 헤더 별칭(한글 우선 + 영문/변형 허용)
const H = {
  allergen: {
    id:       ["문서ID","아이디","ID","id"],
    name:     ["표시명","이름","명칭","displayName","name"],
    syn:      ["동의어","유의어","synonyms"],
    cat:      ["분류","카테고리","category"],
    major:    ["주요알레르겐","주요","isMajorAllergen"],
  },
  symptom: {
    id:       ["문서ID","아이디","ID","id"],
    name:     ["표시명","이름","displayName","name"],
    list:     ["증상목록","증상_목록","증상","symptoms"],
    weight:   ["가중치","점수","weight"],
  },
  rule: {
    id:       ["문서ID","아이디","ID","id"],
    a_any:    ["알레르겐_포함","알레르겐포함","알레르겐_any","allergens_any"],
    s_any:    ["증상_포함","증상포함","증상_any","symptoms_any"],
    delta:    ["점수증가","점수변화","점수","scoreDelta"],
    sev:      ["중증도","위험도","severity"],
    condWrap: ["조건","conditions"], // 맵 이름(없으면 '조건' 사용)
  },
  user: {
    id:       ["문서ID","아이디","ID","id"],
    nick:     ["닉네임","별명","nickname","name"],
    alls:     ["알레르겐","알레르겐목록","allergens"],
  },
  report: {
    id:       ["문서ID","아이디","ID","id"],
    uid:      ["사용자UID","UID","uid","userId","user_id"],
    food:     ["음식명","음식","foodName"],
    a_det:    ["알레르겐_탐지","탐지된_알레르겐","알레르겐","allergensDetected"],
    s_chk:    ["증상_체크","증상체크","증상","symptomsChecked"],
    total:    ["총점","점수","totalScore"],
    fsev:     ["최종위험도","위험도","finalSeverity"],
    created:  ["생성시각","작성시각","createdAt"], // 비어있으면 서버 타임스탬프
    updated:  ["업데이트시각","updatedAt"],
  }
};

// ── 공통 CSV 로더
function loadCsv(file){
  return new Promise((resolve,reject)=>{
    const rows=[];
    fs.createReadStream(file)
      .pipe(csv())
      .on("data",(raw)=>{
        const row={};
        for (const [k,v] of Object.entries(raw)) row[strip(k)]=strip(v);
        rows.push(row);
      })
      .on("end",()=>resolve(rows))
      .on("error",reject);
  });
}

// ── 배치 커밋
async function commitBatches(ops,size=450){
  if (ops.length === 0) return;
  for (let i=0;i<ops.length;i+=size){
    const batch=db.batch();
    const slice=ops.slice(i,i+size);
    slice.forEach(({ref,data})=>batch.set(ref,data,{merge:true}));
    await batch.commit();
    console.log(`[OK] batch commit ${i+slice.length}/${ops.length}`);
  }
}

// ── 알레르겐_목록: CSV 헤더 그대로 필드명 사용
async function uploadAllergenList(){
  const file=path.join(CSV_DIR,"알레르겐_목록.csv");
  if(!fs.existsSync(file)) return console.log("[SKIP] 알레르겐_목록.csv 없음");
  const rows=await loadCsv(file);
  const OUT = resolveOutputKeys(rows[0]||{}, { name:H.allergen.name, syn:H.allergen.syn, cat:H.allergen.cat, major:H.allergen.major });
  const ops=rows.map(r=>{
    const id = pick(r, H.allergen.id) || slug(pick(r, H.allergen.name));
    const data={};
    data[OUT.name]  = pick(r, H.allergen.name);
    data[OUT.cat]   = pick(r, H.allergen.cat);
    data[OUT.syn]   = splitArr(pick(r, H.allergen.syn));
    data[OUT.major] = toBool(pick(r, H.allergen.major));
    data["업데이트시각"] = FieldValue.serverTimestamp();
    const ref=docRef("알레르겐_목록", id);
    return {ref,data};
  });
  await commitBatches(ops);
}

// ── 증상_가중치
async function uploadSymptomWeights(){
  const file=path.join(CSV_DIR,"증상_가중치.csv");
  if(!fs.existsSync(file)) return console.log("[SKIP] 증상_가중치.csv 없음");
  const rows=await loadCsv(file);
  const OUT = resolveOutputKeys(rows[0]||{}, { name:H.symptom.name, list:H.symptom.list, weight:H.symptom.weight });
  const ops=rows.map(r=>{
    const id = pick(r, H.symptom.id) || slug(pick(r, H.symptom.name));
    const data={};
    data[OUT.name]   = pick(r, H.symptom.name);
    data[OUT.list]   = splitArr(pick(r, H.symptom.list));
    data[OUT.weight] = toNum(pick(r, H.symptom.weight));
    data["업데이트시각"] = FieldValue.serverTimestamp();
    const ref=docRef("증상_가중치", id);
    return {ref,data};
  });
  await commitBatches(ops);
}

// ── 위험도_규칙 (조건 맵 안에, 내부 키도 CSV 헤더 그대로)
async function uploadRiskRules(){
  const file=path.join(CSV_DIR,"위험도_규칙.csv");
  if(!fs.existsSync(file)) return console.log("[SKIP] 위험도_규칙.csv 없음");
  const rows=await loadCsv(file);
  const OUT = resolveOutputKeys(rows[0]||{}, { a_any:H.rule.a_any, s_any:H.rule.s_any, delta:H.rule.delta, sev:H.rule.sev, condWrap:H.rule.condWrap });
  const condKey = OUT.condWrap || "조건";
  const ops=rows.map(r=>{
    const sev = pick(r, H.rule.sev) || "규칙";
    const id  = pick(r, H.rule.id) || slug(`${sev}-${pick(r,H.rule.a_any)}-${pick(r,H.rule.s_any)}`);
    const data={};
    data[condKey] = {
      [OUT.a_any]: splitArr(pick(r, H.rule.a_any)),
      [OUT.s_any]: splitArr(pick(r, H.rule.s_any)),
    };
    data[OUT.delta] = toNum(pick(r, H.rule.delta));
    data[OUT.sev]   = sev;
    data["업데이트시각"] = FieldValue.serverTimestamp();
    const ref=docRef("위험도_규칙", id);
    return {ref,data};
  });
  await commitBatches(ops);
}

// ── 사용자_정보 (선택)
async function uploadUserSeeds(){
  const file=path.join(CSV_DIR,"사용자_정보.csv");
  if(!fs.existsSync(file)) return console.log("[SKIP] 사용자_정보.csv 없음");
  const rows=await loadCsv(file);
  const OUT = resolveOutputKeys(rows[0]||{}, { nick:H.user.nick, alls:H.user.alls });
  const ops=rows.map(r=>{
    const id = pick(r, H.user.id) || slug(pick(r, H.user.nick) || "user");
    const data={};
    data[OUT.nick] = pick(r, H.user.nick);
    data[OUT.alls] = splitArr(pick(r, H.user.alls));
    data["생성시각"] = FieldValue.serverTimestamp();
    data["업데이트시각"] = FieldValue.serverTimestamp();
    const ref=docRef("사용자_정보", id);
    return {ref,data};
  });
  await commitBatches(ops);
}

// ── 사용자_보고 (선택)
async function uploadUserReports(){
  const file=path.join(CSV_DIR,"사용자_보고.csv");
  if(!fs.existsSync(file)) return console.log("[SKIP] 사용자_보고.csv 없음");
  const rows=await loadCsv(file);
  const OUT = resolveOutputKeys(rows[0]||{}, { uid:H.report.uid, food:H.report.food, a_det:H.report.a_det, s_chk:H.report.s_chk, total:H.report.total, fsev:H.report.fsev, created:H.report.created, updated:H.report.updated });
  const ops=rows.map(r=>{
    const id  = pick(r, H.report.id); // 없으면 자동 ID
    const data={};
    data[OUT.uid]   = pick(r, H.report.uid);
    data[OUT.food]  = pick(r, H.report.food);
    data[OUT.a_det] = splitArr(pick(r, H.report.a_det));
    data[OUT.s_chk] = splitArr(pick(r, H.report.s_chk));
    data[OUT.total] = toNum(pick(r, H.report.total));
    data[OUT.fsev]  = pick(r, H.report.fsev);
    data[OUT.created] = FieldValue.serverTimestamp();
    data[OUT.updated] = FieldValue.serverTimestamp();
    const ref=docRef("사용자_보고", id);
    return {ref,data};
  });
  await commitBatches(ops);
}

async function main(){
  const onlyBase    = process.argv.includes("--base");         // 기준 3개만
  const seedUsers   = process.argv.includes("--seed-users");   // 사용자_정보
  const seedReports = process.argv.includes("--seed-reports"); // 사용자_보고
  console.log("[INFO] CSV DIR:", CSV_DIR);

  await uploadAllergenList();
  await uploadSymptomWeights();
  await uploadRiskRules();

  if (!onlyBase && seedUsers)   await uploadUserSeeds();
  if (!onlyBase && seedReports) await uploadUserReports();

  console.log("[DONE] 업로드 완료");
  process.exit(0);
}

main().catch(e=>{ console.error(e); process.exit(1); });
