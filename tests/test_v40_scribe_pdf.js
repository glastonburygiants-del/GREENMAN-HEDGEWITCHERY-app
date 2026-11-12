// V40 Scribe PDF structural checks (no Android/native side effects).
const assert=require('node:assert/strict');
const fs=require('node:fs');
const src=fs.readFileSync('tools/bos_scribe_a4_v40.js','utf8');
assert.match(src,/function gmScribeV40ImagePdf\(/);
assert.match(src,/async function gmScribeExportA4Pdf\(/);
assert.match(src,/beginPdfCopy/);
assert.match(src,/appendPdfCopyChunk/);
assert.doesNotMatch(src,/localStorage|sessionStorage|fetch\(|XMLHttpRequest|navigator\.sendBeacon/);
const make=new Function(src+';return gmScribeV40ImagePdf')();
const jpeg='data:image/jpeg;base64,/9j/2Q==';
(async()=>{
  for(const landscape of [false,true]){
    const blob=make([{url:jpeg,width:800,height:1123},{url:jpeg,width:800,height:900}],landscape);
    assert.equal(blob.type,'application/pdf');
    const data=Buffer.from(await blob.arrayBuffer());
    const s=data.toString('latin1');
    assert(s.startsWith('%PDF-1.4\n'));
    assert(s.includes('/Count 2'));
    assert(s.includes('/DCTDecode'));
    assert(s.includes('/Im0 Do'));
    const xrefPos=s.indexOf('xref\n0 9\n');
    assert(xrefPos>0);
    assert(s.includes('startxref\n'+xrefPos+'\n%%EOF'));
    const positions=[...s.matchAll(/^(\d+) 0 obj$/gm)].map(x=>({id:Number(x[1]),offset:x.index}));
    assert.equal(positions.length,8);
    const xref=s.slice(xrefPos).split('\n');
    for(let i=1;i<9;i++)assert.equal(Number(xref[i+2].slice(0,10)),positions[i-1].offset,'xref '+i);
    assert(landscape?s.includes('841.89 595.28'):s.includes('595.28 841.89'));
  }
  console.log('PASS: portrait/landscape 2-page PDF object offsets, streams and A4 geometry');
})().catch(e=>{console.error(e);process.exitCode=1});
