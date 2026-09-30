#!/usr/bin/env python3
# EXP4 build trigger
"""Wire live customer GM access keys into the existing HedgeWitchery Full gate.

Preserves:
- Lite mode and existing Lite button/behaviour.
- Existing owner Full password.
- Existing Master/Admin password.
- Existing Home and every app page.

Adds:
- GM-XXXX-XXXX redemption through greenman-access-redeem.
- Android-only key enforcement.
- Persisted entitlement token/status metadata.
- Online/resume status checks for revoked/deleted/expired entitlements.
- Approved customer welcome before entering the existing Full Home.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_customer_access_gate_v1.py INPUT OUTPUT")

src, out = map(Path, sys.argv[1:])
text = src.read_text(encoding="utf-8")
original = text

if "gm-customer-access-gate-v1" in text:
    raise SystemExit("customer access gate patch already present")

head_end = text.find("</head>")
if head_end < 0:
    raise SystemExit("outer </head> not found")

style = r"""
<style id="gm-customer-access-gate-v1-style">
#gmAccessWelcome{position:fixed;inset:0;z-index:2147483200;display:none;align-items:center;justify-content:center;background:rgba(10,7,3,.88);padding:22px;box-sizing:border-box}
#gmAccessWelcome.open{display:flex}
#gmAccessWelcomeCard{width:min(430px,100%);background:#f5ead0;color:#241608;border:2px solid #c9a84c;border-radius:14px;padding:24px 20px;text-align:center;box-shadow:0 16px 48px rgba(0,0,0,.58);font-family:Georgia,serif}
#gmAccessWelcomeCard h2{margin:0 0 15px;color:#2d4a1e;font-size:23px;line-height:1.2}
#gmAccessWelcomeCard p{margin:0 0 10px;font-size:16px;line-height:1.48;color:#3a2010}
#gmAccessWelcomeEnter{width:100%;margin-top:12px;padding:13px 12px;border:2px solid #c9a84c;border-radius:8px;background:#2d4a1e;color:#fff4d2;font:700 15px Georgia,serif;letter-spacing:.04em}
</style>
"""
text = text[:head_end] + style + text[head_end:]

gate_end = '''</div>

<div id="gmPrintFullscreenReturn"'''
welcome = '''</div>
<div id="gmAccessWelcome" aria-modal="true" role="dialog">
  <div id="gmAccessWelcomeCard">
    <h2>Welcome to Greenman HedgeWitchery Apothecary.</h2>
    <p>You’ve found the door. Come in.</p>
    <p>The cupboards are stocked, the moon is turning, and your Book of Shadows is waiting.</p>
    <button id="gmAccessWelcomeEnter" type="button">ENTER THE APOTHECARY</button>
  </div>
</div>

<div id="gmPrintFullscreenReturn"'''
if text.count(gate_end) != 1:
    raise SystemExit(f"gate DOM anchor count {text.count(gate_end)}")
text = text.replace(gate_end, welcome, 1)

text = text.replace(
    '<div class="gate-title">Greenman Gate</div>',
    '<div class="gate-title">HedgeWitchery Gate</div>',
    1,
)

sec_anchor = """async function gmSecVerify(secret,meta){try{return gmSecConstEq(await gmSecPbkdf2B64(secret,meta),meta.hash)}catch(e){console.error(e);return false}}

function openGate(admin){"""
access_code = r"""async function gmSecVerify(secret,meta){try{return gmSecConstEq(await gmSecPbkdf2B64(secret,meta),meta.hash)}catch(e){console.error(e);return false}}

/* gm-customer-access-gate-v1: generated access keys share the existing Full gate. */
const GM_ACCESS_REDEEM_URL='https://zzfgufuyetybxaeidcxu.supabase.co/functions/v1/greenman-access-redeem';
const GM_ACCESS_PUBLISHABLE_KEY='sb_publishable_v5C9faTqdknJP9sdbgahCQ_MZVw_2gG';
const GM_ACCESS_TOKEN_KEY='gm_access_entitlement_token_v1';
const GM_ACCESS_META_KEY='gm_access_entitlement_meta_v1';
const GM_ACCESS_SOURCE_KEY='gm_full_access_source_v1';
let gmGateAdminRequest=false;
let gmAccessCheckBusy=false;

function gmAccessIsCode(v){return /^GM-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$/.test(String(v||'').trim().toUpperCase())}
async function gmAccessApi(body){
  const r=await fetch(GM_ACCESS_REDEEM_URL,{method:'POST',headers:{'Content-Type':'application/json','apikey':GM_ACCESS_PUBLISHABLE_KEY},body:JSON.stringify(body||{})});
  let d={};try{d=await r.json()}catch(_e){}
  if(!r.ok)throw new Error(d.error||('Access check failed ('+r.status+')'));
  return d;
}
function gmAccessReadMeta(){try{return JSON.parse(localStorage.getItem(GM_ACCESS_META_KEY)||'null')}catch(_e){return null}}
function gmAccessStore(data){
  localStorage.setItem(GM_ACCESS_TOKEN_KEY,String(data.entitlement_token||''));
  localStorage.setItem(GM_ACCESS_META_KEY,JSON.stringify({access_type:data.access_type||'android',duration_months:data.duration_months==null?null:data.duration_months,redeemed_at:data.redeemed_at||null,expires_at:data.expires_at||null}));
  localStorage.setItem(GM_ACCESS_SOURCE_KEY,'customer');
}
function gmAccessClearCustomer(){
  localStorage.removeItem(GM_ACCESS_TOKEN_KEY);
  localStorage.removeItem(GM_ACCESS_META_KEY);
  if(localStorage.getItem(GM_ACCESS_SOURCE_KEY)==='customer')localStorage.removeItem(GM_ACCESS_SOURCE_KEY);
}
function gmAccessDowngradeCustomer(){
  if(localStorage.getItem(GM_ACCESS_SOURCE_KEY)!=='customer')return;
  gmAccessClearCustomer();
  localStorage.setItem('gm_app_mode','lite');
  localStorage.setItem('gm_lite_mode','1');
  localStorage.removeItem('greenman_full_app_unlocked');
  syncModeClass();
  if(currentPage==='admin')showPage('home');else refreshCurrent();
}
function gmShowCustomerWelcome(){
  const w=document.getElementById('gmAccessWelcome');if(w)w.classList.add('open');
}
function gmHideCustomerWelcome(){
  const w=document.getElementById('gmAccessWelcome');if(w)w.classList.remove('open');
}
async function gmAccessRefreshEntitlement(){
  if(gmAccessCheckBusy)return;
  if(localStorage.getItem(GM_ACCESS_SOURCE_KEY)!=='customer')return;
  const token=String(localStorage.getItem(GM_ACCESS_TOKEN_KEY)||'').trim();
  if(!token){gmAccessDowngradeCustomer();return}
  const meta=gmAccessReadMeta();
  if(meta&&meta.expires_at&&new Date(meta.expires_at).getTime()<=Date.now()){gmAccessDowngradeCustomer();return}
  if(typeof navigator!=='undefined'&&navigator.onLine===false)return;
  gmAccessCheckBusy=true;
  try{
    const d=await gmAccessApi({action:'status',entitlement_token:token,expected_access_type:'android'});
    if(!d.active){gmAccessDowngradeCustomer();return}
    localStorage.setItem(GM_ACCESS_META_KEY,JSON.stringify({access_type:d.access_type||'android',duration_months:d.duration_months==null?null:d.duration_months,redeemed_at:d.redeemed_at||null,expires_at:d.expires_at||null}));
  }catch(_e){/* Offline/temporary service failure does not break a locally valid entitlement. */}
  finally{gmAccessCheckBusy=false}
}
function gmAccessRestoreOnLaunch(){
  if(localStorage.getItem(GM_ACCESS_SOURCE_KEY)!=='customer')return;
  const meta=gmAccessReadMeta();
  if(meta&&meta.expires_at&&new Date(meta.expires_at).getTime()<=Date.now()){gmAccessDowngradeCustomer();return}
  gmAccessRefreshEntitlement();
}
window.addEventListener('online',gmAccessRefreshEntitlement);
document.addEventListener('visibilitychange',function(){if(!document.hidden)gmAccessRefreshEntitlement()});

function openGate(admin){"""
if text.count(sec_anchor) != 1:
    raise SystemExit(f"security anchor count {text.count(sec_anchor)}")
text = text.replace(sec_anchor, access_code, 1)

old_open = """function openGate(admin){
  const g=document.getElementById('gmGate');
  g.classList.add('open');"""
new_open = """function openGate(admin){
  gmGateAdminRequest=!!admin;
  const g=document.getElementById('gmGate');
  g.classList.add('open');"""
if text.count(old_open) != 1:
    raise SystemExit(f"openGate anchor count {text.count(old_open)}")
text = text.replace(old_open, new_open, 1)

old_submit = """async function submitGate(){
  const input=document.getElementById('gateInput'),btn=document.getElementById('gateOpenBtn'),msg=document.getElementById('gateMsg'),val=(input.value||'').trim().toUpperCase();
  if(!val){msg.textContent='Enter your app key.';return}
  btn.disabled=true;msg.textContent='Checking key…';
  try{
    if(await gmSecVerify(val,GM_GATE_SECURITY.full)){ setMode('full'); closeGate(); return; }
    if(await gmSecVerify(val,GM_GATE_SECURITY.master)){ setMode('master'); closeGate(); showPage('admin'); return; }
    msg.textContent='That key did not open the gate.';
  }finally{btn.disabled=false}
}"""
new_submit = """async function submitGate(){
  const input=document.getElementById('gateInput'),btn=document.getElementById('gateOpenBtn'),msg=document.getElementById('gateMsg'),val=(input.value||'').trim().toUpperCase();
  if(!val){msg.textContent='Enter your app key.';return}
  btn.disabled=true;msg.textContent='Checking key…';
  try{
    if(await gmSecVerify(val,GM_GATE_SECURITY.full)){
      localStorage.setItem(GM_ACCESS_SOURCE_KEY,'owner');
      setMode('full'); closeGate(); return;
    }
    if(await gmSecVerify(val,GM_GATE_SECURITY.master)){
      localStorage.setItem(GM_ACCESS_SOURCE_KEY,'master');
      setMode('master'); closeGate(); showPage('admin'); return;
    }
    if(gmAccessIsCode(val)){
      if(gmGateAdminRequest){msg.textContent='Access codes open the Full app, not the Admin ledger.';return}
      msg.textContent='Checking access key…';
      try{
        const d=await gmAccessApi({action:'redeem',code:val,expected_access_type:'android'});
        gmAccessStore(d);
        closeGate();
        gmShowCustomerWelcome();
        return;
      }catch(e){msg.textContent=String(e&&e.message||'That access key could not be checked.');return}
    }
    msg.textContent='That key did not open the gate.';
  }finally{btn.disabled=false}
}"""
if text.count(old_submit) != 1:
    raise SystemExit(f"submitGate anchor count {text.count(old_submit)}")
text = text.replace(old_submit, new_submit, 1)

listener_anchor = """document.getElementById('gmOpenFullFloat').addEventListener('click', ()=>openGate(false));
document.getElementById('gmCupboardKey').addEventListener('click', ()=>showPage('cupboardDoor'));"""
listener_replace = """document.getElementById('gmOpenFullFloat').addEventListener('click', ()=>openGate(false));
document.getElementById('gmAccessWelcomeEnter').addEventListener('click', function(){
  gmHideCustomerWelcome();
  setMode('full');
  showPage('home');
});
document.getElementById('gmCupboardKey').addEventListener('click', ()=>showPage('cupboardDoor'));"""
if text.count(listener_anchor) != 1:
    raise SystemExit(f"listener anchor count {text.count(listener_anchor)}")
text = text.replace(listener_anchor, listener_replace, 1)

startup = "buildTabs(); syncModeClass(); showPage('home');"
startup_new = "buildTabs(); syncModeClass(); showPage('home'); gmAccessRestoreOnLaunch();"
if text.count(startup) != 1:
    raise SystemExit(f"startup anchor count {text.count(startup)}")
text = text.replace(startup, startup_new, 1)

if text == original:
    raise SystemExit("no change")

for required in (
    "gm-customer-access-gate-v1",
    "expected_access_type:'android'",
    "ENTER THE APOTHECARY",
    "gm_access_entitlement_token_v1",
    "HedgeWitchery Gate",
):
    if required not in text:
        raise SystemExit("missing " + required)

out.write_text(text, encoding="utf-8")
print(f"wrote {out} bytes={len(text)}")
print("Customer GM access keys now share the existing Full gate; Lite, owner Full password and Master/Admin password are preserved.")
