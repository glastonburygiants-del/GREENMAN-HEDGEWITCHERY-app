#!/usr/bin/env python3
"""FV3.4 first-install country choice + UK-only Greenman shop visibility.

Country is stored in WebView localStorage. Android preserves localStorage across
normal app updates and clears it when the app is uninstalled / its data is
cleared, so a fresh installation asks again. Wildwood sale paths are untouched.
"""
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_fv34_country_sales_gate.py INPUT OUTPUT')

src, out = map(Path, sys.argv[1:])
outer = src.read_text(encoding='utf-8')

# First-install country overlay in the outer app shell.
country_gate = r'''
<style id="gm-country-first-install-style">
#gmCountryFirstInstall{position:fixed;inset:0;z-index:2147483000;background:rgba(14,10,5,.94);display:flex;align-items:center;justify-content:center;padding:22px;box-sizing:border-box}
#gmCountryFirstInstall .gm-country-card{width:min(92vw,520px);max-height:88vh;overflow:auto;background:#f2ead8;border:2px solid #98752f;border-radius:18px;padding:24px 20px;box-shadow:0 18px 70px rgba(0,0,0,.55);color:#251b0d;font-family:Georgia,serif;text-align:center}
#gmCountryFirstInstall h2{margin:0 0 10px;color:#28451d;font-size:25px}
#gmCountryFirstInstall p{font-size:16px;line-height:1.45;margin:10px 0 18px}
#gmCountryFirstInstall select{width:100%;font:700 17px Georgia,serif;padding:13px 12px;border:2px solid #80652d;border-radius:10px;background:#fffdf7;color:#20180d}
#gmCountryFirstInstall button{margin-top:18px;width:100%;padding:14px 12px;border:0;border-radius:11px;background:#2d4a1e;color:#fff6d7;font:700 17px Georgia,serif;letter-spacing:.04em}
#gmCountryFirstInstall button:disabled{opacity:.45}
#gmCountryFirstInstall .gm-country-note{font-size:13px;color:#614b27;margin-top:13px}
</style>
<script id="gm-country-first-install-script">
(function(){
  'use strict';
  const KEY='gm_user_country_v1';
  if(localStorage.getItem(KEY))return;
  const codes=('GB IE FR DE ES IT PT NL BE LU DK SE NO FI IS CH AT PL CZ SK HU RO BG GR HR SI EE LV LT MT CY US CA AU NZ ZA IN PK BD LK NP JP KR CN HK SG MY TH PH ID VN AE SA QA KW BH OM IL TR EG MA TN DZ NG GH KE UG TZ ZW ZM BW NA MZ AO CM SN CI ET RU UA BY MD GE AM AZ KZ UZ KG TJ TM AF IR IQ JO LB SY YE BR AR CL UY PY BO PE EC CO VE GY SR MX GT BZ SV HN NI CR PA CU JM HT DO BS BB TT GD LC VC AG DM KN BZ AL AD BA ME MK RS XK LI MC SM VA MD').split(/\s+/);
  const fallback={GB:'United Kingdom',IE:'Ireland',US:'United States',CA:'Canada',AU:'Australia',NZ:'New Zealand',ZA:'South Africa',IN:'India',FR:'France',DE:'Germany',ES:'Spain',IT:'Italy',PT:'Portugal',NL:'Netherlands',BE:'Belgium',CH:'Switzerland',AT:'Austria',PL:'Poland',SE:'Sweden',NO:'Norway',DK:'Denmark',FI:'Finland',IS:'Iceland'};
  let dn=null;try{dn=new Intl.DisplayNames(['en'],{type:'region'});}catch(e){}
  const seen=new Set(),countries=[];
  for(const code of codes){if(!code||seen.has(code))continue;seen.add(code);let name='';try{name=dn?dn.of(code):'';}catch(e){}name=name||fallback[code]||code;countries.push({code,name});}
  countries.sort((a,b)=>a.name.localeCompare(b.name));
  const ov=document.createElement('div');ov.id='gmCountryFirstInstall';
  const opts=['<option value="" selected disabled>Select your country</option>','<option value="GB">United Kingdom</option>']
    .concat(countries.filter(x=>x.code!=='GB').map(x=>'<option value="'+x.code+'">'+String(x.name).replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</option>')).join('');
  ov.innerHTML='<div class="gm-country-card"><h2>Your Country</h2><p>Please choose your country for this installation of Greenman HedgeWitchery.</p><select id="gmCountryFirstSelect">'+opts+'</select><button id="gmCountryFirstSave" disabled>SAVE COUNTRY</button><div class="gm-country-note">Spell purchases are currently available for UK delivery only. The rest of the app remains available wherever you are.</div></div>';
  document.body.appendChild(ov);
  const sel=document.getElementById('gmCountryFirstSelect'),btn=document.getElementById('gmCountryFirstSave');
  sel.addEventListener('change',()=>{btn.disabled=!sel.value;});
  btn.addEventListener('click',()=>{
    if(!sel.value)return;
    localStorage.setItem(KEY,sel.value);
    ov.remove();
    try{window.dispatchEvent(new CustomEvent('gm-country-ready',{detail:{country:sel.value}}));}catch(e){}
  });
})();
</script>
'''
body_at = outer.rfind('</body>')
if body_at < 0:
    raise SystemExit('outer closing body not found')
if 'gm-country-first-install-script' in outer:
    raise SystemExit('country gate already present')
outer = outer[:body_at] + country_gate + outer[body_at:]

# Update embedded Journal sales UI.
pages_at = outer.index('const PAGES = ')
key_at = outer.index('"journal":', pages_at) + len('"journal":')
journal, used = json.JSONDecoder().raw_decode(outer[key_at:])

def once(anchor, replacement, label):
    global journal
    n = journal.count(anchor)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly 1 anchor, found {n}')
    journal = journal.replace(anchor, replacement, 1)

once(
    "const GM_SHOP_BASKET='gm_greenman_shop_basket_v1';",
    "const GM_USER_COUNTRY='gm_user_country_v1';\nfunction gmShopCountryEligible(){try{return String(localStorage.getItem(GM_USER_COUNTRY)||'').toUpperCase()==='GB';}catch(e){return false;}}\nconst GM_SHOP_BASKET='gm_greenman_shop_basket_v1';",
    'country helper'
)

once(
    "bar.classList.toggle('show',gmShopMode()==='full');",
    "bar.classList.toggle('show',gmShopMode()==='full'&&gmShopCountryEligible());",
    'hide basket outside UK'
)

once(
    "const canBuy=gmShopMode()==='full'&&e.entryType!=='timing'&&e.entryType!=='grimoire'&&!!gmSaleLevel(e);",
    "const canBuy=gmShopMode()==='full'&&gmShopCountryEligible()&&e.entryType!=='timing'&&e.entryType!=='grimoire'&&!!gmSaleLevel(e);",
    'hide buy buttons outside UK'
)

once(
    "function gmAddSpellToBasket(id){const e=",
    "function gmAddSpellToBasket(id){if(!gmShopCountryEligible())return;const e=",
    'add-to-basket safety gate'
)

once(
    "function gmOpenBasket(){const a=",
    "function gmOpenBasket(){if(!gmShopCountryEligible())return;const a=",
    'open-basket safety gate'
)

once(
    "async function gmCheckoutBasket(){const a=",
    "async function gmCheckoutBasket(){if(!gmShopCountryEligible())return;const a=",
    'checkout safety gate'
)

# If the first-install choice was made while Journal is visible, redraw it at once.
insert_anchor = "window.addEventListener('focus',()=>setTimeout(gmCheckPendingPayment,150));"
insert_repl = "window.addEventListener('gm-country-ready',()=>{try{renderEntries();}catch(e){}try{gmUpdateBasketBar();}catch(e){}});\n" + insert_anchor
once(insert_anchor, insert_repl, 'country-ready redraw')

encoded = json.dumps(journal, ensure_ascii=False).replace('</script>', '<\\/script>')
outer = outer[:key_at] + encoded + outer[key_at+used:]
out.write_text(outer, encoding='utf-8')
print(f'wrote {out} bytes={len(outer)}')
print('FV3.4 country gate: asks once per installation; Greenman Buy Spell and basket are UK-only; Wildwood untouched.')
