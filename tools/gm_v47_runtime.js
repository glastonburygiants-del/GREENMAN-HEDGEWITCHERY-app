/* V47 folio refinement: small deep-red boxes / gold pen ticks, clean headings. */
/* V49: original illuminated initials. All ornament is offline SVG penwork. */
function gmV47Initial(letter){
 const l=(String(letter||'C').toUpperCase().match(/[A-Z]/)||['C'])[0];
 const paths={C:'M108 35 C91 13 50 15 34 41 C12 72 24 123 61 133 C83 140 101 124 110 106',S:'M110 32 C94 15 56 13 39 32 C24 49 31 66 51 78 L83 93 C121 112 107 140 69 139 C46 138 28 128 18 114',A:'M23 133 L68 24 L112 133 M40 93 L95 93',M:'M19 136 L31 28 L67 96 L104 27 L118 136',P:'M24 137 L24 26 L77 26 C124 26 120 93 68 93 L24 93',N:'M24 136 L24 25 L108 137 L108 24',E:'M104 25 L28 25 L28 135 L106 135 M28 79 L87 79',D:'M25 25 L25 136 L61 136 C127 136 130 25 61 25 Z',O:'M67 20 C4 20 9 141 66 141 C126 141 129 20 67 20 Z',R:'M26 137 L26 24 L74 24 C121 24 115 87 75 87 L26 87 M70 87 L114 138',T:'M16 27 L118 27 M67 27 L67 136',I:'M38 25 L95 25 M66 25 L66 136 M36 136 L97 136',L:'M24 24 L24 135 L112 135',B:'M25 26 L25 135 L79 135 C121 135 121 80 72 80 L25 80 M72 80 C117 79 111 26 78 26 L25 26'};
 Object.assign(paths,{
  F:'M25 136 L25 26 L111 26 M25 80 L90 80',
  G:'M113 43 C93 18 48 18 32 44 C14 76 28 132 67 137 C94 140 113 117 114 93 L81 93',
  H:'M24 26 L24 136 M112 26 L112 136 M24 81 L112 81',
  J:'M40 27 L112 27 M87 27 L87 117 Q79 143 56 136 Q35 130 33 112',
  K:'M24 26 L24 136 M112 26 L28 88 L116 136',
  Q:'M67 20 C4 20 9 141 66 141 C126 141 129 20 67 20 Z M84 116 L119 148',
  U:'M24 26 L24 102 Q22 138 68 138 Q113 138 112 102 L112 26',
  V:'M20 26 L66 138 L115 26',
  W:'M15 26 L40 139 L67 72 L94 139 L122 26',
  X:'M23 26 L113 137 M113 26 L23 137',
  Y:'M19 26 L67 83 L115 26 M67 83 L67 138',
  Z:'M19 26 L118 26 L20 136 L120 136'
 });
 const main=paths[l]||paths.C;
 const inks=['#782e40','#8d362d','#274d63','#3c5a4b'];
 const letterInk=inks[(l.charCodeAt(0)-65)%inks.length];
 const letterPath=(colour,width)=>'<path d="'+main+'" transform="translate(6 12) scale(1.035 1.025)" fill="none" stroke="'+colour+'" stroke-width="'+width+'" stroke-linecap="round" stroke-linejoin="round"/>';
 const leaves='<path d="M17 105 C31 108 35 120 33 132 C20 128 15 116 17 105 Z M31 94 C38 80 51 78 57 78 C55 91 43 98 31 94 Z M30 151 C39 139 54 143 58 149 C51 160 38 160 30 151 Z M116 34 C107 24 104 17 107 12 C123 14 129 23 116 34 Z M119 52 C130 42 142 43 148 50 C142 61 130 60 119 52 Z M114 142 C129 130 141 135 146 143 C141 154 126 154 114 142 Z" fill="#506d51" stroke="#c2aa63" stroke-width="1.6"/>';
 const veins='<path d="M23 113 L33 132 M35 90 L52 82 M34 151 L54 148 M113 23 L118 31 M124 52 L144 50 M122 144 L142 142" fill="none" stroke="#d6bd7c" stroke-width="1"/>';
 const rosette=(x,y,shade)=>'<g transform="translate('+x+' '+y+')"><path d="M0 -8 Q4 -4 0 0 Q-4 -4 0 -8 M8 0 Q4 4 0 0 Q4 -4 8 0 M0 8 Q-4 4 0 0 Q4 4 0 8 M-8 0 Q-4 -4 0 0 Q-4 4 -8 0" fill="'+shade+'" stroke="#d7b263" stroke-width="1.1"/><circle r="2.1" fill="#f5d77b"/></g>';
 return '<svg class="gmV47Initial gmV49Illuminated" data-letter="'+l+'" viewBox="0 0 160 184" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
 +'<rect x="4.5" y="4.5" width="151" height="175" rx="1.5" fill="#e5d7b5" stroke="#513126" stroke-width="2"/>'
 +'<rect x="9" y="9" width="142" height="166" fill="#293d64" stroke="#c59b44" stroke-width="2.9"/>'
 +'<path d="M12 12 L60 12 Q29 33 12 65 Z M148 172 L100 172 Q131 148 148 119 Z" fill="#733341"/>'
 +'<path d="M148 12 L111 12 Q139 31 148 65 Z M12 172 L52 172 Q27 152 12 126 Z" fill="#405d58"/>'
 +'<rect x="14" y="14" width="132" height="156" rx="2" fill="none" stroke="#e7c16d" stroke-width=".95"/>'
 +'<path d="M22 22 Q80 15 138 22 M22 161 Q80 168 138 161 M22 22 Q13 91 22 161 M138 22 Q147 91 138 161" fill="none" stroke="#b99258" stroke-width=".9"/>'
 +'<path d="M20 93 C10 70 29 47 38 36 C53 17 31 16 32 30 M139 99 C151 80 125 65 127 48 C128 33 145 36 139 24 M20 150 C19 129 44 120 48 105 C53 85 35 82 28 96 M139 160 C131 141 116 140 113 124 C107 108 122 103 133 113" fill="none" stroke="#b79c5c" stroke-width="2.15" stroke-linecap="round"/>'
 +'<path d="M16 105 C27 98 26 95 31 90 C34 87 44 93 46 102 M28 155 C30 141 43 132 43 122 M141 141 C130 130 125 115 124 103 M145 52 C134 45 122 44 115 34" fill="none" stroke="#2b524c" stroke-width="2.8" stroke-linecap="round"/>'
 +leaves+veins
 +letterPath('#231f2e',25)+letterPath('#e4bc62',21)+letterPath('#fff1b1',17)+letterPath(letterInk,14)+letterPath('#bc7c58',2)
 +'<path d="M17 42 C28 51 27 66 22 73 M136 97 C131 107 136 121 143 124 M57 164 Q79 154 102 164" fill="none" stroke="#e8cb87" stroke-width="1.4" stroke-dasharray="2.1 3.5"/>'
 +rosette(29,37,'#a34749')+rosette(131,147,'#7b3044')
 +'<g fill="#f0d07b" stroke="#a27639" stroke-width=".6"><circle cx="22" cy="18" r="2"/><circle cx="139" cy="18" r="2"/><circle cx="22" cy="167" r="2"/><circle cx="139" cy="167" r="2"/><path d="M78 12 L82 17 L78 22 L74 17 Z M78 163 L82 168 L78 173 L74 168 Z"/></g>'
 +'<g fill="#e0b15b"><circle cx="52" cy="24" r="1.7"/><circle cx="109" cy="24" r="1.7"/><circle cx="44" cy="158" r="1.5"/><circle cx="108" cy="161" r="1.5"/><circle cx="146" cy="84" r="1.5"/></g>'
 +'<g fill="#f3e5c0" stroke="#cbaa57" stroke-width=".8"><circle cx="20" cy="88" r="3.5"/><circle cx="142" cy="103" r="3.5"/></g>'
 +'</svg>';
}
function gmV47VineRule(){return '<svg class="gmV47VineRule" viewBox="0 0 720 27" preserveAspectRatio="none" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><path d="M0 14 H328 Q350 14 358 5 Q365 0 371 7 Q378 14 360 14 Q343 14 353 22 Q361 28 371 20 Q383 14 397 14 H720" fill="none" stroke="#9a754d" stroke-width="1.3"/><path d="M339 14 C329 5 322 4 318 2 C318 12 328 17 339 14 Z M379 14 C388 5 397 4 402 2 C400 13 390 16 379 14 Z" fill="#64734e" stroke="#3e5a45" stroke-width="1"/><circle cx="361" cy="14" r="2.3" fill="#943d33"/></svg>'}
function gmV47Tick(input){return '<label class="gmBosTocSelect gmV47TickBox">'+input+'<svg viewBox="0 0 24 24" focusable="false" aria-hidden="true"><rect x="2.5" y="2.5" width="19" height="19" rx="0.4" fill="none" stroke="#6e2431" stroke-width="1.7"/><path d="M4.5 11.5 L9.5 16.7 L19.6 5.8" fill="none" stroke="#bd943d" stroke-width="2.9" stroke-linecap="round" stroke-linejoin="round"/></svg></label>'}
function gmBosTocItemHTML(it){
 let attrs='',cls='',key=gmBosTocItemKey(it);
 if(it.kind==='spell'){cls=' spell';attrs=' data-gm-spell-page-ref="'+esc(it.chapter)+'" data-gm-spell-id="'+esc(it.id||'')+'" data-gm-spell-key="'+esc(it.key||'')+'"'}
 else if(it.kind==='entry'){attrs=' data-gm-toc-entry-ref="'+esc(it.id||'')+'" data-gm-toc-entry-chapter="'+esc(it.chapter)+'"'}
 else if(it.kind==='ref'){cls=' reference';attrs=' data-gm-toc-ref-range="'+esc(it.chapter)+'"'}
 else if(it.kind==='range'){cls=' reference';attrs=' data-gm-toc-range-chapter="'+esc(it.chapter)+'"'}
 else if(it.kind==='title'){cls=' reference';attrs=' data-gm-toc-title-ref="'+esc(it.title||it.label)+'" data-gm-toc-title-chapter="'+esc(it.chapter)+'"'}
 return '<div class="gmBosTocItem gmV47Item'+cls+'" data-gm-toc-item-row="'+esc(key)+'">'+gmV47Tick('<input type="checkbox" aria-label="Include '+esc(it.label)+'" data-gm-toc-item-select="'+esc(key)+'" '+(gmBosItemSelected(it)?'checked':'')+'>').replace('gmBosTocSelect gmV47TickBox','gmBosTocItemSelect gmV47TickBox')+'<button type="button" class="gmBosTocItemLabelBtn gmV47ItemLink" data-gm-toc-item-open="'+esc(key)+'">'+esc(it.label)+'</button><span class="gmBosTocItemPage gmV47ItemPages"'+attrs+'>—</span></div>';
}
function gmBosTocChapterHTML(block){
 const c=block.chapter,fixed=c.id==='contents',cont=block.continued?' gmBosTocContinuation':'';
 const check=fixed?'<span class="gmBosTocFixedMark gmV47FixedMarker">◆</span>':gmV47Tick('<input type="checkbox" aria-label="Include '+esc(c.title)+'" data-chapter-check="'+esc(c.id)+'" '+(selected.has(c.id)?'checked':'')+'>');
 const group=!block.continued&&c.id==='spell-list'?'<div class="gmV47GroupTitle">Spell chapters</div>':(!block.continued&&c.id==='numerology'?'<div class="gmV47GroupTitle">Reference chapters</div>':'');
 return group+'<section class="gmBosTocChapter gmV47Chapter'+cont+'" data-row="'+esc(c.id)+'"><div class="gmBosTocChapterHead gmV47ChapterRow">'+check+'<span class="gmBosTocChapterNumber gmV47ChapterNo">'+esc(c.num)+'</span><button type="button" class="gmBosTocChapterText gmV47ChapterLink" data-chapter-jump="'+esc(c.id)+'"><span class="gmBosTocChapterTitle">'+esc(c.title)+'</span></button><span class="gmBosContentsPages gmV47Pages" data-chapter-pages="'+esc(c.id)+'">—</span></div>'+block.items.map(gmBosTocItemHTML).join('')+'</section>';
}
function addContents(){
 GM_BOS_TOC_PACKS=gmBosTocPackSections(gmBosTocSections(),18);
 GM_BOS_TOC_PACKS.forEach((pack,i)=>{
 const sub=GM_BOS_TOC_PACKS.length>1?'Part '+(i+1)+' of '+GM_BOS_TOC_PACKS.length:'Register of chapters';
 const p=page('contents','Contents',sub,'gmBosContentsPage');p.classList.add('gmBosV47Page');
 const h=p.querySelector('.gmBosChapterHead');if(h)h.innerHTML='';
 const filter=i===0?'<div class="gmBosContentsActions gmV47ContentsFilter"><button type="button" id="gmBosSelectAll">All chapters</button><button type="button" id="gmBosSelectSpell">Spell chapters</button><button type="button" id="gmBosSelectReference">Lore chapters</button></div>':'';
 body(p).innerHTML='<div class="gmV47ContentsBody"><div class="gmV47Opener">'+gmV47Initial('C')+'<div class="gmV47MainTitle"><h1 class="gmV47TitleText">Contents</h1><div class="gmV47TitleCaption">'+esc(sub)+'</div></div></div>'+gmV47VineRule()+filter+'<div class="gmBosContentsRows gmV47Register" data-gm-contents-pack="'+i+'"></div></div>';
 });
}
function addChapterContentsPages(){
 const chapters=CHAPTERS.filter(c=>c.id!=='contents');
 chapters.forEach(c=>{
 const targets=pages.filter(p=>p.dataset.chapter===c.id&&!p.classList.contains('gmBosChapterContentsPage'));
 if(!targets.length)return;
 targets.forEach((p,i)=>p.dataset.gmChapterTargetKey='gm-chapter-'+c.id+'-'+i);
 const rows=targets.map((p,i)=>{const title=gmBosChapterTargetLabel(p,c,i+1);return {key:p.dataset.gmChapterTargetKey,title:title,kind:gmBosChapterTargetKind(p,c,title),seq:i+1}}),count=rows.length;
 const density=count<=9?'roomy':count<=20?'normal':count<=30?'compact':'dense';
 const firstTarget=targets[0],at=pages.indexOf(firstTarget),p=page(c.id,c.title,c.sub,'gmBosChapterContentsPage');
 pages.pop();pages.splice(at,0,p);p.classList.add('gmBosV47Page','gmV47ChapterPage');p.dataset.density=density;
 const head=p.querySelector('.gmBosChapterHead');if(head){head.innerHTML='';head.setAttribute('data-gm-chapter-number',c.num)}
 const cards=rows.map(r=>'<button type="button" class="gmChapterCard gmV47Entry" data-gm-page-target-key="'+esc(r.key)+'"><span class="gmV47EntryNumber">'+String(r.seq).padStart(2,'0')+'</span><span class="gmChapterCardName gmV47EntryText">'+esc(r.title)+'</span><span class="gmChapterCardPage gmV47EntryPage" data-gm-chapter-page-ref="'+esc(r.key)+'">fol. —</span></button>').join('');
 body(p).innerHTML='<div class="gmV47ChapterOpener"><div class="gmV47ChapterTitleBlock">'+gmV47Initial(c.title.slice(0,1))+'<div class="gmV47MainTitle"><div class="gmV47Kicker">Chapter '+esc(c.num)+'</div><h1 class="gmV47TitleText">'+esc(c.title)+'</h1><div class="gmV47TitleCaption">'+esc(c.sub)+'</div></div></div>'+gmV47VineRule()+'<div class="gmV47ChapterPrelude"><p>'+count+' '+(count===1?'entry':'entries')+' in this chapter</p><span class="gmV47FolioRef" data-chapter-pages="'+esc(c.id)+'">—</span></div><div class="gmV47ChapterEntriesTitle">Leaves of this chapter</div><div class="gmV47ChapterEntries">'+cards+'</div></div>';
 });
}
