#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_web_app_v1.py input.html output.html')

src=Path(sys.argv[1]); dst=Path(sys.argv[2])
text=src.read_text(encoding='utf-8')

required=[
    'gm-customer-access-gate-v1',
    "expected_access_type:'android'",
    'Welcome to Greenman HedgeWitchery Apothecary.',
    "buildTabs(); syncModeClass(); showPage('home'); gmAccessRestoreOnLaunch();",
]
for item in required:
    if item not in text:
        raise SystemExit(f'missing expected full-app access anchor: {item}')

text=text.replace("expected_access_type:'android'", "expected_access_type:'web'")
text=text.replace("data.access_type||'android'", "data.access_type||'web'")
text=text.replace("d.access_type||'android'", "d.access_type||'web'")

style_anchor='</style>\\n</head>'
web_style=r'''<style id="gm-web-app-access-v1-style">
#gmOpenFullFloat{display:none!important}
#gmWebAccessScreen{position:fixed;inset:0;z-index:2147483300;display:none;align-items:center;justify-content:center;overflow:auto;background:linear-gradient(180deg,rgba(10,22,10,.97),rgba(30,16,6,.98));padding:18px;box-sizing:border-box}
#gmWebAccessScreen.open{display:flex}
#gmWebAccessCard{width:min(520px,100%);margin:auto;background:linear-gradient(#f7ebca,#efe0b9);color:#2b1b0d;border:3px solid #a98027;border-radius:15px;padding:22px 18px;box-shadow:0 0 0 4px #39240c,0 18px 55px rgba(0,0,0,.62);font-family:Georgia,'Times New Roman',serif;text-align:center}
#gmWebAccessCard h1{margin:0;color:#285f2a;font-size:clamp(24px,6vw,34px);line-height:1.12}
#gmWebAccessCard .gm-web-sub{margin:7px 0 18px;color:#6d5221;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:13px}
#gmWebAccessCard .gm-web-intro{margin:0 0 14px;line-height:1.45;font-size:16px;color:#3b2812}
.gm-web-pay-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
.gm-web-pay{min-height:68px;border:2px solid #173e19;border-radius:10px;background:linear-gradient(#3d7c40,#225b26);color:#fff4d0;font:700 16px Georgia,serif;padding:10px;cursor:pointer}
.gm-web-pay small{display:block;font-size:12px;font-weight:400;margin-top:4px;color:#e7dbad}
.gm-web-or{display:flex;align-items:center;gap:8px;margin:18px 0 12px;color:#856827;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.08em}
.gm-web-or:before,.gm-web-or:after{content:'';height:1px;background:#b28b35;flex:1}
#gmWebAccessKey{width:100%;min-height:46px;border:2px solid #9c792c;border-radius:8px;background:#fffdf7;color:#25170b;padding:10px 11px;font:16px ui-monospace,monospace;text-transform:uppercase;box-sizing:border-box}
#gmWebUseKey{width:100%;min-height:46px;margin-top:8px;border:2px solid #7c5a1d;border-radius:8px;background:#fff9e7;color:#3c2a12;font:700 15px Georgia,serif;cursor:pointer}
#gmWebAccessMsg{min-height:22px;margin-top:10px;font-size:14px;line-height:1.35;color:#7a2b1f}
#gmWebAccessMsg.good{color:#245a27}
.gm-web-backup-row{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:18px;padding-top:15px;border-top:1px solid #b8964a}
.gm-web-backup-row button{min-height:40px;border:1px solid #8c6a20;border-radius:7px;background:#fdf7e8;color:#4b3414;padding:8px 11px;font:700 12px Georgia,serif;cursor:pointer}
.gm-web-sandbox{margin-top:12px;color:#876c36;font-size:11px;font-style:italic}
@media(max-width:520px){.gm-web-pay-grid{grid-template-columns:1fr}}
</style>
'''
if text.count(style_anchor) < 1:
    raise SystemExit('head style anchor missing')
text=text.replace(style_anchor, web_style+style_anchor, 1)

markup_anchor='''<div id="gmAccessWelcome" aria-modal="true" role="dialog">
  <div id="gmAccessWelcomeCard">
    <h2>Welcome to Greenman HedgeWitchery Apothecary.</h2>
    <p>You’ve found the door. Come in.</p>
    <p>The cupboards are stocked, the moon is turning, and your Book of Shadows is waiting.</p>
    <button id="gmAccessWelcomeEnter" type="button">ENTER THE APOTHECARY</button>
  </div>
</div>
'''
if text.count(markup_anchor)!=1:
    raise SystemExit(f'welcome markup anchor count {text.count(markup_anchor)}')
web_markup=markup_anchor+r'''
<div id="gmWebAccessScreen" aria-modal="true" role="dialog" aria-label="HedgeWitchery Web App access">
  <div id="gmWebAccessCard">
    <h1>Greenman HedgeWitchery Apothecary</h1>
    <div class="gm-web-sub">HedgeWitchery Web App</div>
    <p class="gm-web-intro">Choose Web App access, or use an access key or promo code.</p>
    <div class="gm-web-pay-grid">
      <button class="gm-web-pay" id="gmWebPayMonthly" type="button">1 MONTH · £5.99<small>PayPal sandbox</small></button>
      <button class="gm-web-pay" id="gmWebPayYearly" type="button">1 YEAR · £49.99<small>PayPal sandbox</small></button>
    </div>
    <div class="gm-web-or">Access key or promo code</div>
    <input id="gmWebAccessKey" type="text" inputmode="text" autocomplete="off" maxlength="14" placeholder="GM-XXXX-XXXX" aria-label="Web App access key or promo code">
    <button id="gmWebUseKey" type="button">OPEN WITH KEY</button>
    <div id="gmWebAccessMsg" aria-live="polite"></div>
    <div class="gm-web-backup-row">
      <button id="gmWebAccessExport" type="button">EXPORT BACKUP</button>
      <button id="gmWebAccessImport" type="button">IMPORT BACKUP</button>
    </div>
    <div class="gm-web-sandbox">Sandbox payment testing only.</div>
  </div>
</div>
'''
text=text.replace(markup_anchor,web_markup,1)

old_down='''  syncModeClass();
  if(currentPage==='admin')showPage('home');else refreshCurrent();
}'''
new_down='''  syncModeClass();
  if(currentPage==='admin')showPage('home');else refreshCurrent();
  if(typeof gmWebShowAccess==='function')gmWebShowAccess('Your Web App access has ended. Your saved work is still on this device.');
}'''
if text.count(old_down)!=1:
    raise SystemExit(f'downgrade anchor count {text.count(old_down)}')
text=text.replace(old_down,new_down,1)

old_store="""  localStorage.setItem(GM_ACCESS_META_KEY,JSON.stringify({access_type:data.access_type||'web',duration_months:data.duration_months==null?null:data.duration_months,redeemed_at:data.redeemed_at||null,expires_at:data.expires_at||null}));"""
new_store="""  localStorage.setItem(GM_ACCESS_META_KEY,JSON.stringify({access_type:data.access_type||'web',duration_code:data.duration_code||null,duration_months:data.duration_months==null?null:data.duration_months,plan_code:data.plan_code||null,source:data.source||'key',redeemed_at:data.redeemed_at||null,expires_at:data.expires_at||null}));"""
if text.count(old_store)!=1:
    raise SystemExit(f'access store anchor count {text.count(old_store)}')
text=text.replace(old_store,new_store,1)
old_refresh="""    localStorage.setItem(GM_ACCESS_META_KEY,JSON.stringify({access_type:d.access_type||'web',duration_months:d.duration_months==null?null:d.duration_months,redeemed_at:d.redeemed_at||null,expires_at:d.expires_at||null}));"""
new_refresh="""    localStorage.setItem(GM_ACCESS_META_KEY,JSON.stringify({access_type:d.access_type||'web',duration_code:d.duration_code||null,duration_months:d.duration_months==null?null:d.duration_months,plan_code:d.plan_code||null,source:d.source||null,redeemed_at:d.redeemed_at||null,expires_at:d.expires_at||null}));
    setMode('full');
    if(typeof gmWebHideAccess==='function')gmWebHideAccess();"""
if text.count(old_refresh)!=1:
    raise SystemExit(f'access refresh anchor count {text.count(old_refresh)}')
text=text.replace(old_refresh,new_refresh,1)

js_anchor="""window.addEventListener('online',gmAccessRefreshEntitlement);
document.addEventListener('visibilitychange',function(){if(!document.hidden)gmAccessRefreshEntitlement()});

function openGate(admin){"""
if text.count(js_anchor)!=1:
    raise SystemExit(f'web JS anchor count {text.count(js_anchor)}')
web_js=r'''window.addEventListener('online',gmAccessRefreshEntitlement);
document.addEventListener('visibilitychange',function(){if(!document.hidden)gmAccessRefreshEntitlement()});

/* gm-web-app-access-v1: browser access screen + PayPal sandbox + local backup. */
const GM_WEB_PAY_CREATE_URL='https://zzfgufuyetybxaeidcxu.supabase.co/functions/v1/greenman-web-access-paypal-create';
const GM_WEB_PAY_CLAIM_URL='https://zzfgufuyetybxaeidcxu.supabase.co/functions/v1/greenman-web-access-paypal-claim';
const GM_WEB_BACKUP_VERSION=1;
const GM_WEB_ACCESS_KEYS=new Set([
  GM_ACCESS_TOKEN_KEY,GM_ACCESS_META_KEY,GM_ACCESS_SOURCE_KEY,
  'greenman_full_app_unlocked','gm_app_mode','gm_lite_mode'
]);

function gmWebAccessMsg(message,good){
  const el=document.getElementById('gmWebAccessMsg');if(!el)return;
  el.textContent=String(message||'');el.classList.toggle('good',!!good);
}
function gmWebShowAccess(message){
  const el=document.getElementById('gmWebAccessScreen');if(el)el.classList.add('open');
  if(message)gmWebAccessMsg(message,false);
}
function gmWebHideAccess(){
  const el=document.getElementById('gmWebAccessScreen');if(el)el.classList.remove('open');
  gmWebAccessMsg('',false);
}
function gmWebCleanReturnUrl(){
  try{history.replaceState({},document.title,location.pathname+location.hash)}catch(_e){}
}
async function gmWebJsonPost(url,body){
  const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','apikey':GM_ACCESS_PUBLISHABLE_KEY},body:JSON.stringify(body||{})});
  let d={};try{d=await r.json()}catch(_e){}
  if(!r.ok)throw new Error(d.error||('Request failed ('+r.status+')'));
  return d;
}
async function gmWebStartPayment(plan){
  const monthly=document.getElementById('gmWebPayMonthly'),yearly=document.getElementById('gmWebPayYearly');
  if(monthly)monthly.disabled=true;if(yearly)yearly.disabled=true;
  gmWebAccessMsg('Opening PayPal sandbox…',true);
  try{
    const d=await gmWebJsonPost(GM_WEB_PAY_CREATE_URL,{plan:plan});
    if(!d.approval_url)throw new Error('PayPal did not return an approval page.');
    location.assign(d.approval_url);
  }catch(e){
    gmWebAccessMsg(String(e&&e.message||e),false);
    if(monthly)monthly.disabled=false;if(yearly)yearly.disabled=false;
  }
}
async function gmWebRedeemKey(){
  const input=document.getElementById('gmWebAccessKey'),btn=document.getElementById('gmWebUseKey');
  const code=String(input&&input.value||'').trim().toUpperCase();
  if(!gmAccessIsCode(code)){gmWebAccessMsg('Enter a valid GM access key or promo code.',false);return}
  if(btn)btn.disabled=true;gmWebAccessMsg('Checking Web App access…',true);
  try{
    const d=await gmAccessApi({action:'redeem',code:code,expected_access_type:'web'});
    gmAccessStore(d);setMode('full');gmWebHideAccess();showPage('home');
  }catch(e){gmWebAccessMsg(String(e&&e.message||e),false)}
  finally{if(btn)btn.disabled=false}
}
async function gmWebClaimPayment(claim){
  gmWebShowAccess('Confirming PayPal sandbox payment…');
  try{
    const d=await gmWebJsonPost(GM_WEB_PAY_CLAIM_URL,{claim_token:claim});
    gmAccessStore(d);setMode('full');gmWebHideAccess();gmWebCleanReturnUrl();showPage('home');
    return true;
  }catch(e){gmWebCleanReturnUrl();gmWebShowAccess(String(e&&e.message||e));return false}
}
function gmWebExportBackup(){
  try{
    const data={};
    for(let i=0;i<localStorage.length;i++){
      const k=localStorage.key(i);if(!k||GM_WEB_ACCESS_KEYS.has(k))continue;
      data[k]=localStorage.getItem(k);
    }
    const payload={product:'Greenman HedgeWitchery Apothecary',kind:'HedgeWitchery Web App Backup',version:GM_WEB_BACKUP_VERSION,created_at:new Date().toISOString(),localStorage:data};
    const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
    const day=new Date().toISOString().slice(0,10);
    a.href=url;a.download='HedgeWitchery_Backup_'+day+'.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1200);
  }catch(e){alert('Backup could not be exported: '+String(e&&e.message||e))}
}
function gmWebImportBackup(){
  const input=document.createElement('input');input.type='file';input.accept='.json,application/json';
  input.onchange=async function(){
    const file=input.files&&input.files[0];if(!file)return;
    try{
      const payload=JSON.parse(await file.text());
      if(!payload||payload.kind!=='HedgeWitchery Web App Backup'||!payload.localStorage||typeof payload.localStorage!=='object')throw new Error('That is not a HedgeWitchery Web App backup file.');
      if(!confirm('Restore this backup on this device? Current saved app data on this device will be replaced. Your Web App access will not be changed.'))return;
      const preserve={};GM_WEB_ACCESS_KEYS.forEach(k=>{const v=localStorage.getItem(k);if(v!==null)preserve[k]=v});
      const remove=[];for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k&&!GM_WEB_ACCESS_KEYS.has(k))remove.push(k)}
      remove.forEach(k=>localStorage.removeItem(k));
      Object.entries(payload.localStorage).forEach(([k,v])=>{if(!GM_WEB_ACCESS_KEYS.has(k)&&typeof v==='string')localStorage.setItem(k,v)});
      Object.entries(preserve).forEach(([k,v])=>localStorage.setItem(k,v));
      alert('Backup restored. The Web App will reload now.');location.reload();
    }catch(e){alert('Backup could not be imported: '+String(e&&e.message||e))}
  };
  input.click();
}
function gmWebInstallBackupPanel(){
  const f=document.getElementById('pageFrame');if(!f||currentPage!=='home')return false;
  let d;try{d=f.contentDocument||f.contentWindow.document}catch(_e){return false}
  if(!d||!d.body||d.getElementById('gmWebBackupPanel'))return !!(d&&d.getElementById('gmWebBackupPanel'));
  const host=d.querySelector('.page-scroll')||d.body;
  const style=d.createElement('style');style.id='gmWebBackupStyle';style.textContent='#gmWebBackupPanel{margin:18px auto 6px;padding:15px 14px;max-width:440px;border:1px solid #9e7d38;border-radius:10px;background:rgba(245,232,192,.96);color:#34220f;text-align:center;font-family:Georgia,serif}#gmWebBackupPanel h3{margin:0 0 6px;color:#2d4a1e;font-size:15px}#gmWebBackupPanel p{margin:0 0 10px;font-size:12px;line-height:1.4;color:#6e552b}.gmWebBackupButtons{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}.gmWebBackupButtons button{min-height:40px;padding:8px 11px;border:1px solid #8c6a20;border-radius:7px;background:#fff9e7;color:#3f2c13;font:700 12px Georgia,serif}';d.head.appendChild(style);
  const panel=d.createElement('section');panel.id='gmWebBackupPanel';panel.innerHTML='<h3>DATA &amp; BACKUP</h3><p>Move your saved HedgeWitchery work to another browser or device.</p><div class="gmWebBackupButtons"><button type="button" id="gmWebHomeExport">EXPORT BACKUP</button><button type="button" id="gmWebHomeImport">IMPORT BACKUP</button></div>';
  host.appendChild(panel);
  d.getElementById('gmWebHomeExport').onclick=gmWebExportBackup;d.getElementById('gmWebHomeImport').onclick=gmWebImportBackup;
  return true;
}
function gmWebScheduleBackupPanel(){[80,250,600].forEach(ms=>setTimeout(gmWebInstallBackupPanel,ms))}
const gmWebOriginalShowPage=showPage;
showPage=function(page){const r=gmWebOriginalShowPage.apply(this,arguments);if(page==='home')gmWebScheduleBackupPanel();return r};
async function gmWebAccessBoot(){
  const q=new URLSearchParams(location.search),claim=String(q.get('claim')||''),pay=String(q.get('paypal')||'');
  if(claim){await gmWebClaimPayment(claim);return}
  if(pay==='cancel'){gmWebShowAccess('PayPal payment was cancelled. Your saved work has not been changed.');gmWebCleanReturnUrl();return}
  if(pay==='error'){gmWebShowAccess('PayPal could not complete the sandbox payment. Please try again.');gmWebCleanReturnUrl();return}
  const source=localStorage.getItem(GM_ACCESS_SOURCE_KEY),token=String(localStorage.getItem(GM_ACCESS_TOKEN_KEY)||'').trim(),meta=gmAccessReadMeta();
  if(source==='owner'||source==='master'){gmWebHideAccess();return}
  if(source==='customer'&&token&&(!meta||!meta.expires_at||new Date(meta.expires_at).getTime()>Date.now())){
    setMode('full');gmWebHideAccess();gmAccessRefreshEntitlement();return;
  }
  if(source==='customer')gmAccessClearCustomer();
  setMode('lite');gmWebShowAccess('');
}
window.gmWebExportBackup=gmWebExportBackup;window.gmWebImportBackup=gmWebImportBackup;

function openGate(admin){'''
text=text.replace(js_anchor,web_js,1)

events_anchor="""document.getElementById('gmAccessWelcomeEnter').addEventListener('click', function(){
  gmHideCustomerWelcome();
  setMode('full');
  showPage('home');
});
document.getElementById('gmCupboardKey').addEventListener('click', ()=>showPage('cupboardDoor'));"""
if text.count(events_anchor)!=1:
    raise SystemExit(f'event anchor count {text.count(events_anchor)}')
web_events=events_anchor+r'''
document.getElementById('gmWebPayMonthly').addEventListener('click',()=>gmWebStartPayment('monthly'));
document.getElementById('gmWebPayYearly').addEventListener('click',()=>gmWebStartPayment('yearly'));
document.getElementById('gmWebUseKey').addEventListener('click',gmWebRedeemKey);
document.getElementById('gmWebAccessKey').addEventListener('keydown',e=>{if(e.key==='Enter')gmWebRedeemKey()});
document.getElementById('gmWebAccessExport').addEventListener('click',gmWebExportBackup);
document.getElementById('gmWebAccessImport').addEventListener('click',gmWebImportBackup);'''
text=text.replace(events_anchor,web_events,1)

startup="buildTabs(); syncModeClass(); showPage('home'); gmAccessRestoreOnLaunch();"
if text.count(startup)!=1:
    raise SystemExit(f'startup anchor count {text.count(startup)}')
text=text.replace(startup,"buildTabs(); syncModeClass(); showPage('home'); gmAccessRestoreOnLaunch(); gmWebAccessBoot();",1)

checks=[
    "expected_access_type:'web'",
    'greenman-web-access-paypal-create',
    'greenman-web-access-paypal-claim',
    'gmWebExportBackup',
    'gmWebImportBackup',
    'HedgeWitchery Web App',
    '1 MONTH · £5.99',
    '1 YEAR · £49.99',
]
for item in checks:
    if item not in text:
        raise SystemExit(f'web app output check missing: {item}')
if "expected_access_type:'android'" in text:
    raise SystemExit('Android customer access type survived in web build')

dst.write_text(text,encoding='utf-8')
print('patched HedgeWitchery Web App access/payment/backup v1')
