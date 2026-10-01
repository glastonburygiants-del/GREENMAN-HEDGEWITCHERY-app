/* HedgeWitchery Web App V2
   Account login, subscription portability and user-created-data sync.
   Loaded after the proven V1 full Web App shell. */
(function(){
'use strict';

const PROJECT_URL='https://zzfgufuyetybxaeidcxu.supabase.co';
const LOGIN_URL=PROJECT_URL+'/functions/v1/greenman-web-login';
const ACCOUNT_URL=PROJECT_URL+'/functions/v1/greenman-web-account-status';
const SYNC_URL=PROJECT_URL+'/functions/v1/greenman-web-user-sync';

const SESSION_KEY='gm_web_auth_session_v1';
const DEVICE_KEY='gm_web_device_id_v1';
const MANIFEST_KEY='gm_web_sync_manifest_v1';
const SINCE_KEY='gm_web_sync_since_v1';
const USER_KEY='gm_web_local_user_id_v1';

const ARRAY_COLLECTIONS={
  journal:'gm_journal_entries',
  castings:'gm_bos_castings',
  scribe:'gm_scribe_books_v1',
  scribe_bos:'gm_scribe_bos_books_v1'
};
const KV_KEYS=[
  'gm_scribe_draft_v1',
  'gm_scribe_counters_v1',
  'gm_scribe_ui_v2',
  'gm_scribe_bos_selected_chapters_v1',
  'gm_scribe_bos_selected_chapters_v2',
  'gm_scribe_bos_selected_items_v1',
  'greenman_shared_timing_db_v1',
  'gm_journal_quick_list'
];

try{
  if(typeof GM_WEB_ACCESS_KEYS!=='undefined' && GM_WEB_ACCESS_KEYS && GM_WEB_ACCESS_KEYS.add){
    [SESSION_KEY,DEVICE_KEY,MANIFEST_KEY,SINCE_KEY,USER_KEY].forEach(function(k){GM_WEB_ACCESS_KEYS.add(k);});
  }
}catch(_e){}

function byId(id){return document.getElementById(id);}
function message(id,text,good){
  const el=byId(id); if(!el)return;
  el.textContent=String(text||'');
  el.classList.toggle('good',!!good);
}
function loginMessage(text,good){message('gmWebLoginMsg',text,good);}
function accessMessage(text,good){
  if(typeof gmWebAccessMsg==='function')gmWebAccessMsg(text,good);
}
async function post(url,body,accessToken){
  const headers={'Content-Type':'application/json','apikey':GM_ACCESS_PUBLISHABLE_KEY};
  if(accessToken)headers.Authorization='Bearer '+accessToken;
  const r=await fetch(url,{method:'POST',headers:headers,body:JSON.stringify(body||{})});
  let d={};try{d=await r.json();}catch(_e){}
  if(!r.ok)throw new Error(d.error||('Request failed ('+r.status+')'));
  return d;
}

function readSession(){
  try{
    const x=JSON.parse(localStorage.getItem(SESSION_KEY)||'null');
    return x&&typeof x==='object'?x:null;
  }catch(_e){return null;}
}
function saveSession(session,user){
  if(!session||!session.access_token||!session.refresh_token)return false;
  let exp=Number(session.expires_at||0);
  if(!exp&&session.expires_in)exp=Math.floor(Date.now()/1000)+Number(session.expires_in);
  const saved={
    access_token:String(session.access_token),
    refresh_token:String(session.refresh_token),
    expires_at:exp||0,
    user:user||null
  };
  localStorage.setItem(SESSION_KEY,JSON.stringify(saved));
  if(user&&user.id)localStorage.setItem(USER_KEY,String(user.id));
  return true;
}
function clearSession(){localStorage.removeItem(SESSION_KEY);}
async function ensureSession(){
  let s=readSession();
  if(!s||!s.refresh_token)return null;
  const exp=Number(s.expires_at||0);
  if(s.access_token&&(!exp||exp*1000>Date.now()+120000))return s;
  try{
    const d=await post(LOGIN_URL,{action:'refresh',refresh_token:s.refresh_token});
    saveSession(d.session,d.user);
    return readSession();
  }catch(_e){
    clearSession();
    return null;
  }
}

function showSignedState(session){
  const signedOut=byId('gmWebSignedOut');
  const signedIn=byId('gmWebSignedIn');
  const choices=byId('gmWebAccessChoices');
  const txt=byId('gmWebSignedInText');
  const email=session&&session.user&&session.user.email?String(session.user.email):'';
  if(session&&session.access_token){
    if(signedOut)signedOut.style.display='none';
    if(signedIn)signedIn.classList.add('open');
    if(choices)choices.classList.add('open');
    if(txt)txt.textContent='Signed in as '+email;
  }else{
    if(signedOut)signedOut.style.display='block';
    if(signedIn)signedIn.classList.remove('open');
    if(choices)choices.classList.remove('open');
    if(txt)txt.textContent='';
  }
}

async function sendLoginCode(){
  const email=String((byId('gmWebLoginEmail')||{}).value||'').trim().toLowerCase();
  const btn=byId('gmWebSendCode');
  if(!email){loginMessage('Enter your email address.',false);return;}
  if(btn)btn.disabled=true;
  loginMessage('Sending your login code…',true);
  try{
    await post(LOGIN_URL,{action:'request',email:email});
    const area=byId('gmWebCodeArea');if(area)area.style.display='block';
    loginMessage('Code sent. Check your email and enter the 6 digits here.',true);
    setTimeout(function(){const x=byId('gmWebLoginCode');if(x)x.focus();},50);
  }catch(e){
    loginMessage(String(e&&e.message||e),false);
  }finally{
    if(btn)btn.disabled=false;
  }
}

async function verifyLoginCode(){
  const email=String((byId('gmWebLoginEmail')||{}).value||'').trim().toLowerCase();
  const code=String((byId('gmWebLoginCode')||{}).value||'').replace(/\D/g,'').slice(0,6);
  const btn=byId('gmWebVerifyCode');
  if(!email||code.length!==6){loginMessage('Enter the email and 6-digit code.',false);return;}
  if(btn)btn.disabled=true;
  loginMessage('Signing in…',true);
  try{
    const d=await post(LOGIN_URL,{action:'verify',email:email,code:code});
    saveSession(d.session,d.user);
    const s=readSession();
    showSignedState(s);
    loginMessage('',true);
    await checkAccount(true);
  }catch(e){
    loginMessage(String(e&&e.message||e),false);
  }finally{
    if(btn)btn.disabled=false;
  }
}

async function signOut(){
  try{await syncNow(true);}catch(_e){}
  clearSession();
  localStorage.removeItem(SINCE_KEY);
  localStorage.removeItem(MANIFEST_KEY);
  localStorage.removeItem(USER_KEY);
  try{localStorage.removeItem(GM_ACCESS_TOKEN_KEY);}catch(_e){}
  try{localStorage.removeItem(GM_ACCESS_META_KEY);}catch(_e){}
  try{localStorage.removeItem(GM_ACCESS_SOURCE_KEY);}catch(_e){}
  localStorage.setItem('gm_app_mode','lite');
  localStorage.setItem('gm_lite_mode','1');
  localStorage.removeItem('greenman_full_app_unlocked');
  if(typeof syncModeClass==='function')syncModeClass();
  showSignedState(null);
  if(typeof gmWebShowAccess==='function')gmWebShowAccess('Signed out. Your saved work remains on this device.');
}

async function checkAccount(showInactive){
  const s=await ensureSession();
  showSignedState(s);
  if(!s){
    if(typeof setMode==='function')setMode('lite');
    if(showInactive!==false&&typeof gmWebShowAccess==='function')gmWebShowAccess('Sign in to open your Web App account.');
    return false;
  }
  try{
    const d=await post(ACCOUNT_URL,{action:'status'},s.access_token);
    if(d.active){
      localStorage.setItem(GM_ACCESS_SOURCE_KEY,'web-account');
      localStorage.setItem(GM_ACCESS_META_KEY,JSON.stringify({
        access_type:'web',
        source:d.source||'account',
        plan_code:d.plan_code||null,
        duration_code:d.duration_code||null,
        expires_at:d.expires_at||null
      }));
      if(typeof setMode==='function')setMode('full');
      if(typeof gmWebHideAccess==='function')gmWebHideAccess();
      if(typeof showPage==='function')showPage('home');
      startSync();
      return true;
    }
    if(typeof setMode==='function')setMode('lite');
    if(showInactive!==false&&typeof gmWebShowAccess==='function'){
      gmWebShowAccess('You are signed in. Choose Web App access below, or use an access key or promo code.');
    }
    return false;
  }catch(e){
    if(typeof setMode==='function')setMode('lite');
    if(showInactive!==false&&typeof gmWebShowAccess==='function')gmWebShowAccess(String(e&&e.message||e));
    return false;
  }
}

async function startPayment(plan){
  const monthly=byId('gmWebPayMonthly'),yearly=byId('gmWebPayYearly');
  if(monthly)monthly.disabled=true;if(yearly)yearly.disabled=true;
  accessMessage('Opening PayPal sandbox…',true);
  try{
    const s=await ensureSession();
    if(!s)throw new Error('Sign in before starting a Web App payment.');
    const d=await post(GM_WEB_PAY_CREATE_URL,{plan:plan},s.access_token);
    if(!d.approval_url)throw new Error('PayPal did not return an approval page.');
    location.assign(d.approval_url);
  }catch(e){
    accessMessage(String(e&&e.message||e),false);
    if(monthly)monthly.disabled=false;if(yearly)yearly.disabled=false;
  }
}

async function redeemKey(){
  const input=byId('gmWebAccessKey'),btn=byId('gmWebUseKey');
  const code=String(input&&input.value||'').trim().toUpperCase();
  if(!gmAccessIsCode(code)){accessMessage('Enter a valid GM access key or promo code.',false);return;}
  if(btn)btn.disabled=true;
  accessMessage('Checking Web App access…',true);
  try{
    const s=await ensureSession();
    if(!s)throw new Error('Sign in before using a Web App access key or promo code.');
    const r=await fetch(GM_ACCESS_REDEEM_URL,{
      method:'POST',
      headers:{
        'Content-Type':'application/json',
        'apikey':GM_ACCESS_PUBLISHABLE_KEY,
        'Authorization':'Bearer '+s.access_token
      },
      body:JSON.stringify({action:'redeem',code:code,expected_access_type:'web'})
    });
    let d={};try{d=await r.json();}catch(_e){}
    if(!r.ok)throw new Error(d.error||('Access check failed ('+r.status+')'));
    await checkAccount(true);
  }catch(e){
    accessMessage(String(e&&e.message||e),false);
  }finally{
    if(btn)btn.disabled=false;
  }
}

function deviceId(){
  let id=String(localStorage.getItem(DEVICE_KEY)||'');
  if(id)return id;
  id='web_'+Date.now().toString(36)+'_'+Math.random().toString(36).slice(2,10);
  localStorage.setItem(DEVICE_KEY,id);
  return id;
}
function manifest(){
  try{
    const x=JSON.parse(localStorage.getItem(MANIFEST_KEY)||'{}');
    return x&&typeof x==='object'?x:{};
  }catch(_e){return {};}
}
function saveManifest(x){localStorage.setItem(MANIFEST_KEY,JSON.stringify(x||{}));}
async function hashValue(v){
  const b=new TextEncoder().encode(String(v==null?'':v));
  const h=new Uint8Array(await crypto.subtle.digest('SHA-256',b));
  return Array.from(h).map(function(x){return x.toString(16).padStart(2,'0');}).join('');
}
function readArray(key){
  try{const x=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(x)?x:[];}catch(_e){return [];}
}
function writeArray(key,a){localStorage.setItem(key,JSON.stringify(Array.isArray(a)?a:[]));}
function stableId(collection,item,index){
  if(item&&typeof item==='object'){
    if(collection==='journal')return String(item.entryId||item.id||item.savedAt||item.createdAt||('journal_'+index));
    if(collection==='castings')return String(item.castingId||item.id||item.createdAt||item.savedAt||('casting_'+index));
    if(collection==='scribe')return String(item.id||[item.scriptId,item.shelfId,item.savedAt,item.title].filter(Boolean).join('|')||('scribe_'+index));
    if(collection==='scribe_bos')return String(item.id||item.entryId||[item.scriptId,item.shelfId,item.savedAt,item.title].filter(Boolean).join('|')||('scribe_bos_'+index));
  }
  return collection+'_'+index;
}
async function localRecords(){
  const records=[],present=new Set(),dev=deviceId();
  for(const pair of Object.entries(ARRAY_COLLECTIONS)){
    const collection=pair[0],key=pair[1],arr=readArray(key);
    for(let i=0;i<arr.length;i++){
      const item=arr[i],id=stableId(collection,item,i),raw=JSON.stringify(item);
      const h=await hashValue(raw),mk=collection+':'+id;
      records.push({collection:collection,item_id:id,payload:item,content_hash:h,device_id:dev,_manifest_key:mk});
      present.add(mk);
    }
  }
  for(const key of KV_KEYS){
    const value=localStorage.getItem(key);
    if(value===null)continue;
    const h=await hashValue(value),mk='kv:'+key;
    records.push({collection:'kv',item_id:key,payload:{value:value},content_hash:h,device_id:dev,_manifest_key:mk});
    present.add(mk);
  }
  return {records:records,present:present};
}
function removeArrayItem(collection,itemId){
  const key=ARRAY_COLLECTIONS[collection];if(!key)return;
  const arr=readArray(key);
  const next=arr.filter(function(x,i){return stableId(collection,x,i)!==String(itemId);});
  if(next.length!==arr.length)writeArray(key,next);
}
function upsertArrayItem(collection,itemId,payload){
  const key=ARRAY_COLLECTIONS[collection];
  if(!key||!payload||typeof payload!=='object')return;
  const arr=readArray(key);
  const idx=arr.findIndex(function(x,i){return stableId(collection,x,i)===String(itemId);});
  if(idx>=0)arr[idx]=payload;else arr.push(payload);
  writeArray(key,arr);
}
function applyRemote(rec,m){
  const mk=String(rec.collection)+':'+String(rec.item_id);
  if(rec.deleted_at){
    if(rec.collection==='kv')localStorage.removeItem(String(rec.item_id));
    else removeArrayItem(String(rec.collection),String(rec.item_id));
    delete m[mk];
    return;
  }
  if(rec.collection==='kv'){
    const v=rec.payload&&typeof rec.payload.value==='string'?rec.payload.value:null;
    if(v!==null)localStorage.setItem(String(rec.item_id),v);
  }else{
    upsertArrayItem(String(rec.collection),String(rec.item_id),rec.payload);
  }
  m[mk]=String(rec.content_hash||'');
}
let syncBusy=false,syncTimer=null;
function syncStatus(text,good){
  try{
    const f=byId('pageFrame');
    const d=f&&(f.contentDocument||f.contentWindow.document);
    const el=d&&d.getElementById('gmWebSyncStatus');
    if(el){el.textContent=text||'';el.className='gm-web-sync-line'+(good?' good':'');}
  }catch(_e){}
}
async function pullRemote(session,since){
  return post(SYNC_URL,{action:'pull',since:since||null},session.access_token);
}
async function syncNow(silent){
  if(syncBusy||navigator.onLine===false)return false;
  syncBusy=true;
  if(!silent)syncStatus('Syncing your saved work…',true);
  try{
    const s=await ensureSession();if(!s)return false;
    let m=manifest();
    let since=String(localStorage.getItem(SINCE_KEY)||'');

    /* First sync on a device is cloud-first. This prevents an older device
       from overwriting a newer cloud copy merely because it just signed in. */
    if(!since){
      const first=await pullRemote(s,'');
      for(const rec of (first.records||[]))applyRemote(rec,m);
      saveManifest(m);
      if(first.server_time){since=String(first.server_time);localStorage.setItem(SINCE_KEY,since);}
    }

    const local=await localRecords(),changed=[];
    for(const rec of local.records){
      if(m[rec._manifest_key]!==rec.content_hash){
        const clean=Object.assign({},rec);delete clean._manifest_key;changed.push(clean);
      }
    }
    for(const mk of Object.keys(m)){
      if(!local.present.has(mk)){
        const p=mk.indexOf(':');
        changed.push({collection:mk.slice(0,p),item_id:mk.slice(p+1),deleted:true,device_id:deviceId()});
      }
    }
    if(changed.length){
      await post(SYNC_URL,{action:'push',records:changed},s.access_token);
      const refreshed=await localRecords();
      m=manifest();
      for(const rec of refreshed.records)m[rec._manifest_key]=rec.content_hash;
      for(const mk of Object.keys(m))if(!refreshed.present.has(mk))delete m[mk];
      saveManifest(m);
    }

    const pulled=await pullRemote(s,since);
    m=manifest();
    for(const rec of (pulled.records||[]))applyRemote(rec,m);
    saveManifest(m);
    if(pulled.server_time)localStorage.setItem(SINCE_KEY,String(pulled.server_time));

    const stamp=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
    syncStatus('Synced · '+stamp,true);
    return true;
  }catch(e){
    if(!silent)syncStatus('Sync waiting · '+String(e&&e.message||e),false);
    return false;
  }finally{
    syncBusy=false;
  }
}
function startSync(){
  syncNow(true);
  if(syncTimer)clearInterval(syncTimer);
  syncTimer=setInterval(function(){syncNow(true);},20000);
}

function installHomePanel(){
  const f=byId('pageFrame');
  if(!f||typeof currentPage!=='undefined'&&currentPage!=='home')return false;
  let d;try{d=f.contentDocument||f.contentWindow.document;}catch(_e){return false;}
  if(!d||!d.body)return false;
  let panel=d.getElementById('gmWebBackupPanel');
  if(!panel)return false;
  panel.innerHTML='<h3>YOUR HEDGEWITCHERY DATA</h3>'+
    '<p>Your saved Book of Shadows, Journal and Scribe work follows your Web App login between devices.</p>'+
    '<div id="gmWebSyncStatus" class="gm-web-sync-line">Sync ready</div>'+
    '<div class="gmWebBackupButtons">'+
      '<button type="button" id="gmWebHomeSync">SYNC NOW</button>'+
      '<button type="button" id="gmWebHomeExport">EXPORT BACKUP</button>'+
      '<button type="button" id="gmWebHomeImport">IMPORT BACKUP</button>'+
    '</div>';
  const sync=d.getElementById('gmWebHomeSync');
  const exp=d.getElementById('gmWebHomeExport');
  const imp=d.getElementById('gmWebHomeImport');
  if(sync)sync.onclick=function(){syncNow(false);};
  if(exp)exp.onclick=gmWebExportBackup;
  if(imp)imp.onclick=gmWebImportBackup;
  return true;
}
function scheduleHomePanel(){[100,300,700,1200].forEach(function(ms){setTimeout(installHomePanel,ms);});}

function replaceClickHandler(id,handler){
  const old=byId(id);if(!old||!old.parentNode)return null;
  const fresh=old.cloneNode(true);
  old.parentNode.replaceChild(fresh,old);
  fresh.addEventListener('click',handler);
  return fresh;
}
function wireUi(){
  const send=byId('gmWebSendCode');if(send)send.onclick=sendLoginCode;
  const verify=byId('gmWebVerifyCode');if(verify)verify.onclick=verifyLoginCode;
  const signout=byId('gmWebSignOut');if(signout)signout.onclick=signOut;
  const email=byId('gmWebLoginEmail');if(email)email.addEventListener('keydown',function(e){if(e.key==='Enter')sendLoginCode();});
  const otp=byId('gmWebLoginCode');if(otp)otp.addEventListener('keydown',function(e){if(e.key==='Enter')verifyLoginCode();});
  replaceClickHandler('gmWebUseKey',redeemKey);
  replaceClickHandler('gmWebPayMonthly',function(){startPayment('monthly');});
  replaceClickHandler('gmWebPayYearly',function(){startPayment('yearly');});
}

async function boot(){
  wireUi();
  scheduleHomePanel();
  const q=new URLSearchParams(location.search);
  const pay=String(q.get('paypal')||'');
  const source=localStorage.getItem(GM_ACCESS_SOURCE_KEY);
  if(source==='owner'||source==='master'){
    if(typeof gmWebHideAccess==='function')gmWebHideAccess();
    return;
  }
  const s=await ensureSession();
  showSignedState(s);
  if(pay==='cancel'){
    if(typeof gmWebCleanReturnUrl==='function')gmWebCleanReturnUrl();
    if(typeof gmWebShowAccess==='function')gmWebShowAccess('PayPal payment was cancelled. Your saved work has not been changed.');
    return;
  }
  if(pay==='error'){
    if(typeof gmWebCleanReturnUrl==='function')gmWebCleanReturnUrl();
    if(typeof gmWebShowAccess==='function')gmWebShowAccess('PayPal could not complete the sandbox payment. Please try again.');
    return;
  }
  if(pay==='success'){
    if(typeof gmWebCleanReturnUrl==='function')gmWebCleanReturnUrl();
    await checkAccount(true);
    return;
  }
  if(s){await checkAccount(true);return;}
  if(typeof setMode==='function')setMode('lite');
  if(typeof gmWebShowAccess==='function')gmWebShowAccess('Sign in to use your Web App account on this device.');
}

window.gmWebV2SyncNow=syncNow;
window.gmWebV2CheckAccount=checkAccount;
window.gmWebV2Boot=boot;

window.addEventListener('online',function(){syncNow(true);});
document.addEventListener('visibilitychange',function(){if(!document.hidden)syncNow(true);});

/* V1 has already run its local-only boot by the time this file loads.
   Re-run access through the account-aware V2 path immediately. */
setTimeout(boot,0);
})();