const admin=require('firebase-admin');
const fs=require('fs'); const csv=require('csv-parser'); const path=require('path');
admin.initializeApp({ credential: admin.credential.cert(require('./serviceAccountKey.json')) });
const db=admin.firestore();
const CSV=path.join(__dirname,'../db_setup/data/csv/위험도_규칙.csv');
const strip=s=>(s??'').toString().replace(/^\uFEFF/,'').trim();

(async()=>{
  const rows=[]; await new Promise((res,rej)=>{
    fs.createReadStream(CSV).pipe(csv())
      .on('data',r=>{const n={}; for(const k of Object.keys(r)) n[strip(k)]=strip(r[k]); rows.push(n);})
      .on('end',res).on('error',rej);
  });
  // 위험도별 규칙 배열로 묶기
  const bySeverity={};
  for (const r of rows){
    const sev=(r['위험도']||'').toLowerCase(); if(!sev) continue;
    (bySeverity[sev]??=[]).push({ 구분:r['구분']||'', 패턴:r['한글 키워드(정규식)']||'' });
  }
  const batch=db.batch();
  for (const [sev, rules] of Object.entries(bySeverity)){
    const title = (sev[0]||'').toUpperCase()+sev.slice(1); // High/Medium/Low
    const ref=db.collection('위험도_규칙').doc(sev);
    batch.set(ref,{
      '위험도': title,
      '중증도': title,
      '조건': { '키워드규칙': rules.filter(x=>x.구분||x.패턴) },
      '업데이트시각': admin.firestore.FieldValue.serverTimestamp(),
    }, { merge:true });
    // 이전 배열형 필드가 남아있으면 제거
    batch.update(ref,{ '조건.알레르겐_포함': admin.firestore.FieldValue.delete(),
                       '조건.증상_포함': admin.firestore.FieldValue.delete() });
  }
  await batch.commit();
  console.log('위험도_규칙: 키워드 규칙 업로드 완료');
  process.exit(0);
})();
