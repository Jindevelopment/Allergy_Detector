const admin=require('firebase-admin');const fs=require('fs');const csv=require('csv-parser');const path=require('path');
admin.initializeApp({credential:admin.credential.cert(require('./serviceAccountKey.json'))});const db=admin.firestore();
const CSV=path.join(__dirname,'../db_setup/data/csv/알레르겐_목록.csv');
const strip=s=>(s??'').toString().replace(/^\uFEFF/,'').trim();
(async()=>{
  const ids=new Set();
  await new Promise((res,rej)=>{
    fs.createReadStream(CSV).pipe(csv())
      .on('data',r=>{
        const name=strip(r['표준명']||r['표시명']||r['이름']||''); if(name) ids.add(name);
      }).on('end',res).on('error',rej);
  });
  const snap=await db.collection('알레르겐_목록').get();
  let del=0; for(const d of snap.docs){ if(!ids.has(d.id)){ await d.ref.delete(); del++; } }
  console.log('삭제된 랜덤/불일치 문서:', del);
  process.exit(0);
})();
