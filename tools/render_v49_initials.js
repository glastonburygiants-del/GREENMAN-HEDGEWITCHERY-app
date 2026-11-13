const fs=require('node:fs');
const path=require('node:path');
const code=fs.readFileSync(path.join(__dirname,'gm_v47_runtime.js'),'utf8');
const begin=code.indexOf('function gmV47Initial(letter){');
const end=code.indexOf('function gmV47VineRule()',begin);
if(begin<0||end<begin)throw new Error('Decorative initial not found');
const draw=new Function(code.slice(begin,end)+';return gmV47Initial;')();
const out=path.join(__dirname,'..','build','v49-initials');
fs.mkdirSync(out,{recursive:true});
for(const l of ['C','S','A','M','R','N','P','D']){
 const svg=draw(l);
 fs.writeFileSync(path.join(out,'initial-'+l+'.svg'),svg,'utf8');
}
console.log('Saved original SVG initials to',out);
