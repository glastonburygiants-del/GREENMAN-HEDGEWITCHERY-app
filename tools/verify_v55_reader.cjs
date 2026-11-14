const fs=require('fs');
const http=require('http');
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const dir=process.argv[2],html=fs.readFileSync(dir+'/scribe.html');
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(html)});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1000,height:1600},hasTouch:true});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:'+server.address().port,{waitUntil:'load'});
  await page.evaluate(()=>openBos());
  const show=async selector=>page.evaluate(selector=>{
   const nav=[...document.querySelectorAll('.gmBosPage.gmBosPrintSelected')];
   const ix=nav.findIndex(p=>p.matches(selector));if(ix<0)throw Error('Missing page: '+selector);GM_BOS.show(ix);return ix;
  },selector);
  const visible=async()=>page.evaluate(()=>[...document.querySelectorAll('#gmBosPagePool>.gmBosPage')].filter(p=>getComputedStyle(p).display!=='none').length);
  assert.equal(await visible(),1,'one visible page on opening');
  await show('.gmBosDeityEmptyPage');
  assert.equal(await page.locator('.gmBosDeityEmptyPage .gmV47TitleText').textContent(),'Deities');
  assert.equal(await page.locator('.gmBosDeityEmptyPage .gmV47Initial').count(),1);
  await page.screenshot({path:dir+'/deities-v55.png'});
  const notesSelector='.gmBosMoonPhaseCombinedPage';
  await show(notesSelector);
  const note=page.locator('.gmBosPage.active .gmV54NotesEdit');
  await note.fill('Moon notes saved in their page.');
  await page.evaluate(()=>GM_BOS.next());await show(notesSelector);
  assert.equal(await note.textContent(),'Moon notes saved in their page.');
  await page.reload({waitUntil:'load'});await page.evaluate(()=>openBos());await show(notesSelector);
  assert.equal(await note.textContent(),'Moon notes saved in their page.','notes survive reload');
  await page.screenshot({path:dir+'/moon-notes-v55.png'});
  await show('.gmBosPlanetSavedPage');
  assert.equal(await page.locator('.gmBosPage.active .gmV54NotesEdit').count(),1);
  await page.screenshot({path:dir+'/planet-notes-v55.png'});
  await show('.gmV55ScribeOpener');
  assert.equal(await page.locator('.gmV55ScribeOpener').count(),1);
  assert.equal(await page.locator('.gmV55ScribeOpener .gmV47Initial').getAttribute('data-letter'),'S');
  assert.equal(await page.locator('.gmV55ScribeOpener .gmChapterCard').count(),19);
  assert.match(await page.locator('.gmV55CreativeIntro').textContent(),/not a teaching guide/);
  assert.equal(await page.evaluate(()=>!!document.querySelector('[data-gm-scribe-leaf-id="scribe-cover"]')),false);
  const fit=await page.evaluate(()=>{
   const p=document.querySelector('.gmV55ScribeOpener'),body=p.querySelector('.gmBosPageBody').getBoundingClientRect();
   return [...p.querySelectorAll('.gmChapterCard')].every(e=>e.getBoundingClientRect().bottom<=body.bottom+1);
  });assert.equal(fit,true,'all 19 alphabet links fit inside the opener');
  await page.screenshot({path:dir+'/scribe-opener-v55.png'});
  await page.locator('.gmV55ScribeOpener .gmChapterCard').last().click();
  assert.match(await page.locator('.gmBosPage.active').getAttribute('data-title'),/Greek/);
  const scribeStart=await show('.gmBosScribeLetterPage');
  const count=await page.locator('.gmBosScribeLetterPage').count();assert.equal(count,19);
  for(let i=0;i<count;i++){
   await page.evaluate(i=>GM_BOS.show(i),scribeStart+i);
   assert.equal(await visible(),1,'only the selected Scribe leaf is visible');
   assert.equal(await page.evaluate(()=>document.querySelector('#gmBosViewport').scrollTop),0);
  }
  await show('.gmBosScribeLetterPage');
  await page.screenshot({path:dir+'/scribe-paging-v55.png'});
  const oldTitle=await page.locator('.gmBosPage.active').getAttribute('data-title');
  await page.evaluate(()=>{
   const vp=document.querySelector('#gmBosViewport');const rect=vp.getBoundingClientRect();
   const t=new Touch({identifier:1,target:vp,clientX:rect.left+rect.width*.8,clientY:rect.top+100});
   vp.dispatchEvent(new TouchEvent('touchstart',{touches:[t],changedTouches:[t],bubbles:true}));
   const end=new Touch({identifier:1,target:vp,clientX:rect.left+rect.width*.2,clientY:rect.top+100});
   vp.dispatchEvent(new TouchEvent('touchmove',{touches:[end],changedTouches:[end],bubbles:true,cancelable:true}));
   vp.dispatchEvent(new TouchEvent('touchend',{touches:[],changedTouches:[end],bubbles:true}));
  });
  assert.notEqual(await page.locator('.gmBosPage.active').getAttribute('data-title'),oldTitle,'sideways swipe changes Scribe leaf');
  assert.equal(await visible(),1);
  assert.deepEqual(errors,[],'no JavaScript runtime errors');
  const report={passed:true,scribePages:count,singleVisiblePage:true,sidewaysSwipe:true,deitiesIlluminatedHeading:true,moonNotesPersist:true,planetNotes:true,singleScribeOpener:true,illuminatedS:true,all19LinksFit:true,creativeDisclaimer:true};
  fs.writeFileSync(dir+'/reader-checks.json',JSON.stringify(report,null,2));console.log(report);
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
