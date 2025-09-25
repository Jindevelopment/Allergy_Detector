const admin=require('firebase-admin'),fs=require('fs'),csv=require('csv-parser'),path=require('path');
admin.initializeApp({credential:admin.credential.cert(require('./serviceAccountKey.json'))});
const db=admin.firestore(), CSV=path.join(__dirname,'../db_setup/data/csv/알레르겐_목록.csv');
const want='계란'; // 필요하면 다른 표준명 넣어서 반복 실행
const strip=s=>(s??'').toString().replace(/^\uFEFF/,'').trim(); const norm=s=>strip(s).replace(/\s+/g,'').replace(/[._\-\/]/g,'');
const toList=s=>strip(s).split(/[;|,，、\/·•∙]/).map(v=>v.trim()).filter(Boolean);
const toBool=v=>/^(true|1|y|yes|t|참|예)$/i.test((v??'').toString().trim());
const toNum=v=>{const t=(v??'').toString().replace(/[^\d.-]/g,'').trim();return t===''?null:Number(t);};
const COLS={표준명:['표준명','표시명','이름','항목','품목','표준'],동의어:['동의어','유의어','키워드','동의어리스트','동의어목록'],대표군:['대표군','분류','카테고리','군','그룹'],증상:['증상','관련증상','주증상','증상구분'],보수점:['보수적점수','보수 점수','보수점수','보수평가점수','보수적 점수'],주요:['주요알레르겐','주요','메이저','중요']};
function pick(row,aliases){const inv=new Map(Object.keys(row).map(k=>[norm(k),k]));for(const a of aliases){const k=inv.get(norm(a));if(k) return strip(row[k]);}return '';}
(async()=>{
  let found=null;
  await new Promise((res,rej)=>{fs.createReadStream(CSV).pipe(csv()).on('data',r=>{const name=pick(r,COLS.표준명); if(name.includes('계란')||name.includes('알류')){found=r;res();}}).on('end',res).on('error',rej);});
  if(!found){console.error('CSV에서 계란/알류 못 찾음');process.exit(1);}
  const name=pick(found,COLS.표준명)||'계란';
  const data={'표시명':name,'이름':name,'분류':pick(found,COLS.대표군)||'','증상':pick(found,COLS.증상)||'','보수적점수':toNum(pick(found,COLS.보수점)),'동의어':Array.from(new Set(toList(pick(found,COLS.동의어)))),'주요알레르겐':toBool(pick(found,COLS.주요)),'업데이트시각':admin.firestore.FieldValue.serverTimestamp()};
  console.log('[WRITE]',name,data);
  await db.collection('알레르겐_목록').doc(name).set(data,{merge:false}); // 완전 덮어쓰기
  const d=await db.collection('알레르겐_목록').doc(name).get(); console.log('[READBACK]',d.id,d.data());
  process.exit(0);
})();
