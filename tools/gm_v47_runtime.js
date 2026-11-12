function gmV47Initial(letter){
 const l=String(letter||'C').slice(0,1).toUpperCase();
 const paths={C:'M108 35 C91 13 50 15 34 41 C12 72 24 123 61 133 C83 140 101 124 110 106',S:'M110 32 C94 15 56 13 39 32 C24 49 31 66 51 78 L83 93 C121 112 107 140 69 139 C46 138 28 128 18 114',A:'M23 133 L68 24 L112 133 M40 93 L95 93',M:'M19 136 L31 28 L67 96 L104 27 L118 136',P:'M24 137 L24 26 L77 26 C124 26 120 93 68 93 L24 93',N:'M24 136 L24 25 L108 137 L108 24',E:'M104 25 L28 25 L28 135 L106 135 M28 79 L87 79',D:'M25 25 L25 136 L61 136 C127 136 130 25 61 25 Z',O:'M67 20 C4 20 9 141 66 141 C126 141 129 20 67 20 Z',R:'M26 137 L26 24 L74 24 C121 24 115 87 75 87 L26 87 M70 87 L114 138',T:'M16 27 L118 27 M67 27 L67 136',I:'M38 25 L95 25 M66 25 L66 136 M36 136 L97 136',L:'M24 24 L24 135 L112 135',B:'M25 26 L25 135 L79 135 C121 135 121 80 72 80 L25 80 M72 80 C117 79 111 26 78 26 L25 26'};
 const main=paths[l]||paths.C;
 return '<svg class="gmV47Initial" viewBox="0 0 140 160" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><rect x="7" y="7" width="126" height="146" rx="2" fill="none" stroke="#b49867" stroke-width="1.6"/><path d="M13 25 Q27 14 37 15 M103 145 Q117 146 127 132" fill="none" stroke="#8b8060" stroke-width="2"/><path d="'+main+'" fill="none" stroke="#d8b77b" stroke-linecap="round" stroke-linejoin="round" stroke-width="17"/><path d="'+main+'" fill="none" stroke="#84352f" stroke-linecap="round" stroke-linejoin="round" stroke-width="13"/><path d="'+main+'" fill="none" stroke="#ac6447" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8"/><path d="M18 145 C17 122 30 114 41 108 C52 100 60 87 53 70" fill="none" stroke="#3f5541" stroke-width="2.5"/><path d="M31 121 C16 114 13 98 18 91 C32 97 34 109 31 121 Z M40 109 C55 108 65 95 63 86 C47 91 40 98 40 109 Z M22 138 C39 138 48 145 50 150 C32 153 24 148 22 138 Z" fill="#5e714d" stroke="#354738" stroke-width=".8"/><path d="M119 15 C115 35 104 40 98 51" fill="none" stroke="#3f5541" stroke-width="2"/><path d="M113 24 C101 20 96 11 98 6 C110 8 115 15 113 24 Z M104 39 C117 35 124 27 125 19 C111 21 104 28 104 39 Z" fill="#71835b" stroke="#405441" stroke-width=".8"/><circle cx="19" cy="18" r="2.1" fill="#b49356"/><circle cx="120" cy="143" r="2.1" fill="#b49356"/></svg>';
}
function gmV47VineRule(){return '<svg class="gmV47VineRule" viewBox="0 0 720 27" preserveAspectRatio="none" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><path d="M0 14 H328 Q350 14 358 5 Q365 0 371 7 Q378 14 360 14 Q343 14 353 22 Q361 28 371 20 Q383 14 397 14 H720" fill="none" stroke="#9a754d" stroke-width="1.3"/><path d="M339 14 C329 5 322 4 318 2 C318 12 328 17 339 14 Z M379 14 C388 5 397 4 402 2 C400 13 390 16 379 14 Z" fill="#64734e" stroke="#3e5a45" stroke-width="1"/><circle cx="361" cy="14" r="2.3" fill="#943d33"/></svg>'}
function gmV47Tick(input){return '<label class="gmBosTocSelect gmV47TickBox">'+input+'<svg viewBox="0 0 24 24" focusable="false" aria-hidden="true"><rect x="1" y="1" width="22" height="22" fill="none" stroke="#ad6654" stroke-width="1.2"/><path d="M3 12 L9 18 L21 4" fill="none" stroke="#9d4235" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round"/></svg></label>'}
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
 const group=!block.continued&&c.id==='spell-list'?'<div class="gmV47GroupTitle">The book of spells</div>':(!block.continued&&c.id==='numerology'?'<div class="gmV47GroupTitle">The book of lore</div>':'');
 return group+'<section class="gmBosTocChapter gmV47Chapter'+cont+'" data-row="'+esc(c.id)+'"><div class="gmBosTocChapterHead gmV47ChapterRow">'+check+'<span class="gmBosTocChapterNumber gmV47ChapterNo">'+esc(c.num)+'</span><button type="button" class="gmBosTocChapterText gmV47ChapterLink" data-chapter-jump="'+esc(c.id)+'"><span class="gmBosTocChapterTitle">'+esc(c.title)+'</span></button><span class="gmBosContentsPages gmV47Pages" data-chapter-pages="'+esc(c.id)+'">—</span></div>'+block.items.map(gmBosTocItemHTML).join('')+'</section>';
}
function addContents(){
 GM_BOS_TOC_PACKS=gmBosTocPackSections(gmBosTocSections(),18);
 GM_BOS_TOC_PACKS.forEach((pack,i)=>{
 const sub=GM_BOS_TOC_PACKS.length>1?'Part '+(i+1)+' of '+GM_BOS_TOC_PACKS.length:'Register of chapters';
 const p=page('contents','Contents',sub,'gmBosContentsPage');p.classList.add('gmBosV47Page');
 const h=p.querySelector('.gmBosChapterHead');if(h)h.innerHTML='';
 const filter=i===0?'<div class="gmBosContentsActions gmV47ContentsFilter"><button type="button" id="gmBosSelectAll">All chapters</button><button type="button" id="gmBosSelectSpell">Spell chapters</button><button type="button" id="gmBosSelectReference">Lore chapters</button></div>':'';
 body(p).innerHTML='<div class="gmV47ContentsBody"><div class="gmV47Opener">'+gmV47Initial('C')+'<div class="gmV47MainTitle"><div class="gmV47Kicker">Liber umbrarum · the register</div><h1 class="gmV47TitleText">Contents</h1><div class="gmV47TitleCaption">'+esc(sub)+'</div></div></div>'+gmV47VineRule()+filter+'<div class="gmBosContentsRows gmV47Register" data-gm-contents-pack="'+i+'"></div></div>';
 });
}
function addChapterContentsPages(){
 const chapters=CHAPTERS.filter(c=>c.id!=='index');
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
