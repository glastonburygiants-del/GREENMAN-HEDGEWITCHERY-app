const assert=require('node:assert/strict');
const fs=require('node:fs');
const code=fs.readFileSync('tools/gm_v47_runtime.js','utf8');
const begin=code.indexOf('function gmV47Initial(letter){');
const end=code.indexOf('function gmV47VineRule()',begin);
assert(begin>=0&&end>begin);
const make=new Function(code.slice(begin,end)+';return gmV47Initial;')();
const letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ';
for(const ch of letters){
 const svg=make(ch);
 assert(svg.includes('data-letter="'+ch+'"'), 'missing named initial: '+ch);
 assert(svg.startsWith('<svg')&&svg.endsWith('</svg>'));
 assert(svg.includes('viewBox="0 0 160 184"'));
 assert((svg.match(/<path /g)||[]).length>=18,'too little hand-drawn detail for '+ch);
 for(const pigment of ['#293d64','#733341','#405d58','#e4bc62','#f5d77b','#506d51']){
  assert(svg.includes(pigment),'missing manuscript pigment '+pigment+' in '+ch);
 }
 assert(!/<text[\s>]/.test(svg),'SVG must use original paths, not font glyphs');
 assert(!/https?:|<image|foreignObject|<script|data:image|onload=/i.test(svg),'no remote or scripted image');
}
const s=make('S'),c=make('C');
assert.notEqual(s,c,'different letters need different drawing');
const css=fs.readFileSync('tools/bos_folio_v47.css','utf8');
assert(css.includes('V49 illuminated initials'));
assert(css.includes('gmV47ChapterTitleBlock .gmV47Initial{width:40mm'));
assert(code.includes('stroke="#bd943d"'),'gold checkbox ticks remain');
assert(code.includes('stroke="#6e2431"'),'deep-red checkbox outline remains');
console.log('PASS V49: 26 original offline SVG initials with gilding, lapis, oxblood, verdigris and floral scrollwork');
