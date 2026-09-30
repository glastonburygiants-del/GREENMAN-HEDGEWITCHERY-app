#!/usr/bin/env python3
"""Greenman EXP1: Android Admin-only access key maker prototype.

This first experiment is deliberately local-only. It proves the Admin UI,
key format, durations and key-management flow without changing live Supabase
or customer-facing unlock behaviour.
"""
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_exp_access_keys_v1.py INPUT OUTPUT')

src, out = map(Path, sys.argv[1:])
outer = src.read_text(encoding='utf-8')
marker = 'const PAGES = '
root = outer.index(marker) + len(marker)
pages, used = json.JSONDecoder().raw_decode(outer[root:])
admin = pages.get('admin')
if not admin:
    raise SystemExit('admin page not found')
if 'gm-exp-access-keys-v1' in admin:
    raise SystemExit('EXP1 access key patch already present')
if 'id="settings"' not in admin:
    raise SystemExit('Admin Settings panel anchor not found')

payload = r'''
<script id="gm-exp-access-keys-v1">
(function(){
  'use strict';
  const STORE='gm_exp_access_keys_v1';
  const ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

  function read(){try{const x=JSON.parse(localStorage.getItem(STORE)||'[]');return Array.isArray(x)?x:[]}catch(e){return []}}
  function write(x){localStorage.setItem(STORE,JSON.stringify(x))}
  function esc(x){return String(x==null?'':x).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function randomChunk(n){
    const b=new Uint8Array(n);crypto.getRandomValues(b);let s='';
    for(let i=0;i<n;i++)s+=ALPHABET[b[i]%ALPHABET.length];
    return s;
  }
  function newCode(){
    const rows=read();let code='';
    do{code='GM-'+randomChunk(4)+'-'+randomChunk(4)}while(rows.some(r=>r.code===code));
    return code;
  }
  function labelDuration(v){return v==='permanent'?'Permanent':v+' month'+(v==='1'?'':'s')}
  function fmt(ts){try{return new Date(ts).toLocaleString()}catch(e){return ts||''}}
  function copyText(text){
    if(navigator.clipboard&&navigator.clipboard.writeText)return navigator.clipboard.writeText(text);
    const ta=document.createElement('textarea');ta.value=text;document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove();return Promise.resolve();
  }
  function render(){
    const box=document.getElementById('gmExpKeyRows');if(!box)return;
    const rows=read().slice().reverse();
    if(!rows.length){box.innerHTML='<p class="muted">No experimental keys generated yet.</p>';return}
    box.innerHTML=rows.map(function(r){
      const disabled=r.status!=='UNUSED'?' disabled':'';
      return '<div style="border:1px solid #8c6b35;border-radius:8px;padding:10px;margin:8px 0;background:#fffaf0">'
        +'<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap"><b style="font-family:monospace;font-size:16px">'+esc(r.code)+'</b><span>'+esc(r.status)+'</span></div>'
        +'<div class="muted">'+esc(r.access_type==='web'?'Web Access':'Android Full')+' · '+esc(labelDuration(r.duration))+' · '+esc(fmt(r.generated_at))+'</div>'
        +(r.note?'<div class="muted">Note: '+esc(r.note)+'</div>':'')
        +'<div class="button-row" style="margin-top:8px"><button class="btn ghost gmExpCopy" data-code="'+esc(r.code)+'">Copy</button><button class="btn red gmExpRevoke" data-id="'+esc(r.id)+'"'+disabled+'>Revoke</button></div>'
        +'</div>';
    }).join('');
  }
  function install(){
    const settings=document.getElementById('settings')||document.querySelector('.main')||document.body;
    if(document.getElementById('gmExpAccessKeyBox'))return;
    const box=document.createElement('div');box.id='gmExpAccessKeyBox';box.className='card';
    box.innerHTML='<h2>Access Key Maker <span style="font-size:12px">EXP1</span></h2>'
      +'<p class="muted"><b>Experimental local prototype.</b> These keys are stored only on this test installation. They are not yet sent to Supabase and do not unlock customer copies.</p>'
      +'<div class="form-grid">'
      +'<div><label>Unlock</label><select id="gmExpKeyType"><option value="web">Greenman Web</option><option value="android">Android Full Greenman</option></select></div>'
      +'<div><label>Duration</label><select id="gmExpKeyDuration"><option value="1">1 month</option><option value="3">3 months</option><option value="6">6 months</option><option value="12">12 months</option><option value="permanent">Permanent</option></select></div>'
      +'<div><label>Admin note (optional)</label><input id="gmExpKeyNote" maxlength="120" placeholder="Tester, gift, reviewer…"></div>'
      +'</div>'
      +'<div class="button-row"><button class="btn green" id="gmExpGenerateKey">Generate Key</button></div>'
      +'<div id="gmExpGenerated" style="display:none;margin:10px 0;padding:12px;border:2px solid #2d6b2d;border-radius:8px;background:#f4fff0"><div class="muted">Generated key</div><div id="gmExpGeneratedCode" style="font:700 20px monospace;letter-spacing:.08em;margin:4px 0"></div><button class="btn ghost" id="gmExpCopyGenerated">Copy Key</button></div>'
      +'<h3 style="margin-top:16px">Experimental Key List</h3><div id="gmExpKeyRows"></div>';
    settings.insertBefore(box,settings.firstChild);

    const type=document.getElementById('gmExpKeyType'),duration=document.getElementById('gmExpKeyDuration');
    type.addEventListener('change',function(){if(type.value==='android'){duration.value='permanent';duration.disabled=true}else{duration.disabled=false}});
    document.getElementById('gmExpGenerateKey').onclick=function(){
      const rows=read(),code=newCode(),row={
        id:(crypto.randomUUID?crypto.randomUUID():Date.now()+'-'+randomChunk(6)),
        code:code,
        access_type:type.value,
        duration:type.value==='android'?'permanent':duration.value,
        generated_at:new Date().toISOString(),
        status:'UNUSED',
        note:String(document.getElementById('gmExpKeyNote').value||'').trim()
      };
      rows.push(row);write(rows);
      document.getElementById('gmExpGeneratedCode').textContent=code;
      document.getElementById('gmExpGenerated').style.display='block';
      document.getElementById('gmExpKeyNote').value='';
      render();
      try{toast('Experimental key generated')}catch(e){}
    };
    document.getElementById('gmExpCopyGenerated').onclick=function(){copyText(document.getElementById('gmExpGeneratedCode').textContent||'').then(function(){try{toast('Key copied')}catch(e){}})};
    box.addEventListener('click',function(e){
      const c=e.target.closest('.gmExpCopy');if(c){copyText(c.dataset.code||'').then(function(){try{toast('Key copied')}catch(e){}});return}
      const r=e.target.closest('.gmExpRevoke');if(r){const rows=read(),row=rows.find(x=>x.id===r.dataset.id);if(row&&row.status==='UNUSED'){row.status='REVOKED';row.revoked_at=new Date().toISOString();write(rows);render();try{toast('Key revoked')}catch(e){}}}
    });
    render();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else setTimeout(install,0);
  window.gmExpAccessKeys={read:read,render:render,newCode:newCode};
})();
</script>
'''

body_at = admin.rfind('</body>')
if body_at < 0:
    raise SystemExit('Admin closing body not found')
admin = admin[:body_at] + payload + admin[body_at:]
pages['admin'] = admin
encoded = json.dumps(pages, ensure_ascii=False).replace('</script>', '<\\/script>')
outer = outer[:root] + encoded + outer[root+used:]
out.write_text(outer, encoding='utf-8')
print(f'wrote {out} bytes={len(outer)}')
print('EXP1: Admin-only local access-key maker added; customer unlock and Supabase unchanged.')
