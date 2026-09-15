#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: install_pdf_lightweight_names.py INPUT_JAVA OUTPUT_JAVA')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')

if 'function slimPrintClone(' in s or 'function printJobName(' in s:
    raise SystemExit('PDF lightweight/name owner already installed')

# Simplify only the static clone handed to Android printing. The live app remains untouched.
freeze_old = '''                + "function freeze(doc){"
                + "var clone=doc.documentElement.cloneNode(true);copyFormState(doc,clone);freezeFrames(doc,clone);"
                + "var head=clone.querySelector('head');if(head&&!head.querySelector('base')){var base=clone.ownerDocument.createElement('base');base.setAttribute('href',doc.baseURI||'https://greenman.local/index.html');head.insertBefore(base,head.firstChild);}"
                + "return '<!doctype html>'+clone.outerHTML;"
                + "}"'''

freeze_new = '''                + "function slimPrintClone(clone){try{"
                + "Array.prototype.forEach.call(clone.querySelectorAll('script,noscript,template'),function(n){if(n&&n.parentNode)n.parentNode.removeChild(n);});"
                + "Array.prototype.forEach.call(clone.querySelectorAll('style'),function(st){var t=String(st.textContent||'');if(/dashed|dotted/i.test(t))st.textContent=t.replace(/\\\\bdashed\\\\b/gi,'solid').replace(/\\\\bdotted\\\\b/gi,'solid');});"
                + "Array.prototype.forEach.call(clone.querySelectorAll('[style]'),function(el){var t=String(el.getAttribute('style')||'');if(/dashed|dotted/i.test(t))el.setAttribute('style',t.replace(/\\\\bdashed\\\\b/gi,'solid').replace(/\\\\bdotted\\\\b/gi,'solid'));});"
                + "var h=clone.querySelector('head');if(h&&!h.querySelector('#gm-pdf-lightweight-print')){var st=clone.ownerDocument.createElement('style');st.id='gm-pdf-lightweight-print';st.textContent='@media print{*{box-shadow:none!important;text-shadow:none!important;filter:none!important}}';h.appendChild(st);}"
                + "}catch(_e){}return clone;}"
                + "function freeze(doc){"
                + "var clone=doc.documentElement.cloneNode(true);copyFormState(doc,clone);freezeFrames(doc,clone);slimPrintClone(clone);"
                + "var head=clone.querySelector('head');if(head&&!head.querySelector('base')){var base=clone.ownerDocument.createElement('base');base.setAttribute('href',doc.baseURI||'https://greenman.local/index.html');head.insertBefore(base,head.firstChild);}"
                + "return '<!doctype html>'+clone.outerHTML;"
                + "}"'''

if s.count(freeze_old) != 1:
    raise SystemExit(f'freeze anchor count was {s.count(freeze_old)}, expected 1')
s = s.replace(freeze_old, freeze_new, 1)

# Nested BoS/saved-page frames are serialized as srcdoc. Simplify each nested clone too.
frame_old = '''                + "dst[i].removeAttribute('src');dst[i].setAttribute('srcdoc','<!doctype html>'+ic.outerHTML);"'''
frame_new = '''                + "slimPrintClone(ic);dst[i].removeAttribute('src');dst[i].setAttribute('srcdoc','<!doctype html>'+ic.outerHTML);"'''
if s.count(frame_old) != 1:
    raise SystemExit(f'nested-frame anchor count was {s.count(frame_old)}, expected 1')
s = s.replace(frame_old, frame_new, 1)

# One print-job naming owner. It reads the finished print page so names follow spell,
# method, page type, Grimoire item, Journal entry or book title.
install_anchor = '''                + "function install(win,doc){"'''
helpers = '''                + "function gmNamePart(v){var s=String(v==null?'':v).replace(/&/g,' and ').replace(/[\\\\r\\\\n\\\\t]+/g,' ').replace(/[^A-Za-z0-9 _-]+/g,' ').replace(/\\\\s+/g,' ').trim().replace(/ /g,'_').replace(/_+/g,'_').replace(/^_+|_+$/g,'');return s||'Greenman';}"
                + "function gmDate(){var d=new Date(),p=function(n){return String(n).padStart(2,'0');};return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());}"
                + "function gmText(el){return el?String(el.textContent||'').replace(/\\\\s+/g,' ').trim():'';}"
                + "function gmSpellIdentity(doc){try{var nodes=doc.querySelectorAll('h1,h2,h3,.pp-spell-title,.spell-title,.gm-title');for(var i=0;i<nodes.length;i++){var t=gmText(nodes[i]),m=t.match(/^(.{1,90}?)\\\\s*[·•]\\\\s*(Spell Jar|Charm Bag|Smoke(?:\\\\s*&\\\\s*|\\\\s+and\\\\s+)Flame)\\\\s*$/i);if(m)return gmNamePart(m[1])+'_'+gmNamePart(m[2]);}var all=gmText(doc.body),m2=all.match(/(?:Greenman HedgeWitchery\\\\s+)?(.{1,90}?)\\\\s*[·•]\\\\s*(Spell Jar|Charm Bag|Smoke(?:\\\\s*&\\\\s*|\\\\s+and\\\\s+)Flame)/i);if(m2)return gmNamePart(m2[1])+'_'+gmNamePart(m2[2]);}catch(_e){}return'';}"
                + "function gmPageKind(all){if(/INSTRUCTIONS\\\\s*[·:-]?\\\\s*PAGE\\\\s*1\\\\s*OF\\\\s*2/i.test(all))return'Instructions_Page_1';if(/INSTRUCTIONS\\\\s*[·:-]?\\\\s*PAGE\\\\s*2\\\\s*OF\\\\s*2/i.test(all))return'Instructions_Page_2';if(/SUMMARY\\\\s*[·:-]?\\\\s*PAGE\\\\s*1\\\\s*OF\\\\s*2/i.test(all))return'Summary_Page_1';if(/SUMMARY\\\\s*[·:-]?\\\\s*PAGE\\\\s*2\\\\s*OF\\\\s*2/i.test(all))return'Summary_Page_2';if(/\\\\bALTAR\\\\b/i.test(all))return'Altar';if(/ITEM LIST|CORRESPONDENCES/i.test(all))return'Information';return'A4_Page';}"
                + "function printJobName(doc){try{var title=String(doc.title||''),all=gmText(doc.body),ident=gmSpellIdentity(doc),date=gmDate();var admin=doc.querySelector('.gm-admin-book-cover-title');if(admin&&gmText(admin))return gmNamePart(gmText(admin))+'_'+date;var gname=doc.querySelector('#sheetName'),gcat=doc.querySelector('#sheetCategory');if(gname&&gmText(gname)){var cat=gmText(gcat).replace(/Information Sheet/i,'').trim()||'Item';return gmNamePart(gmText(gname))+'_'+gmNamePart(cat)+'_Grimoire';}var bosBook=/Book of Shadows/i.test(title)&&/Your record of spells cast and magic worked|\\\\bContents\\\\b.*\\\\bItem Index\\\\b/i.test(all);if(bosBook)return'Greenman_Book_of_Shadows_'+date;if(/Lite Pack/i.test(title)&&ident)return ident+'_Lite_Pack_'+date;if(/FullPack|Full Pack/i.test(title)&&ident)return ident+'_Full_Pack_'+date;if(/Book of Shadows/i.test(title)&&ident)return ident+'_BoS_Entry_'+date;if(/Journal/i.test(title)&&ident)return ident+'_Journal_Entry_'+date;if(/Journal/i.test(title))return'Greenman_Journal_'+date;if(/(?:_Page\\\\b|\\\\bA4 Page\\\\b|\\\\bPage\\\\b)/i.test(title)&&ident)return ident+'_'+gmPageKind(all)+'_'+date;if(ident)return ident+'_'+gmNamePart(title||'PDF')+'_'+date;return gmNamePart(title||'Greenman_HedgeWitchery');}catch(_e){return'Greenman_HedgeWitchery';}}"
                + "function install(win,doc){"'''
if s.count(install_anchor) != 1:
    raise SystemExit(f'install anchor count was {s.count(install_anchor)}, expected 1')
s = s.replace(install_anchor, helpers, 1)

send_old = '''                + "var send=function(){try{nativeBridge.printDocument(freeze(doc),doc.title||'Greenman HedgeWitchery');}catch(err){nativeBridge.showMessage('The print document could not be sent to Android.');}"'''
send_new = '''                + "var send=function(){try{nativeBridge.printDocument(freeze(doc),printJobName(doc));}catch(err){nativeBridge.showMessage('The print document could not be sent to Android.');}"'''
if s.count(send_old) != 1:
    raise SystemExit(f'print-name handoff anchor count was {s.count(send_old)}, expected 1')
s = s.replace(send_old, send_new, 1)

for forbidden in ('PhoneFriendlyPictureAdapter', 'capturePicture()', 'nativePrintHtml', 'gmNativePrintHtml'):
    if forbidden in s:
        raise SystemExit(f'forbidden print path found after PDF repair: {forbidden}')
for required in ('function slimPrintClone(', 'gm-pdf-lightweight-print', 'function printJobName(', 'nativeBridge.printDocument(freeze(doc),printJobName(doc))'):
    if required not in s:
        raise SystemExit(f'PDF repair marker missing: {required}')

out.write_text(s, encoding='utf-8')
print(f'Installed lightweight PDF clone + dynamic print names: {out}')
