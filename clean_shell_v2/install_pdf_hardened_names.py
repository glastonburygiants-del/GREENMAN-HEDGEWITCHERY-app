#!/usr/bin/env python3
from pathlib import Path
import base64, json, re, sys

if len(sys.argv) != 4:
    raise SystemExit('usage: install_pdf_hardened_names.py INPUT_JAVA OUTPUT_JAVA INDEX_HTML')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
index_path = Path(sys.argv[3])
s = src.read_text(encoding='utf-8')
index = index_path.read_text(encoding='utf-8')

for marker in ('function hardenPrintClone(', 'gm-pdf-hardened-print', 'function printJobName('):
    if marker in s:
        raise SystemExit('PDF hardening/name owner already installed')

# Pull the exact approved God/Goddess SVGs from the Crystal Tumbler room in THIS app build.
assign = re.search(r'PAGES\.cupboard\s*=\s*', index)
if not assign:
    raise SystemExit('PAGES.cupboard assignment not found')
cupboard, _ = json.JSONDecoder().raw_decode(index[assign.end():])
m = re.search(r"const CRYSTAL_TUMBLER_ROOM_B64='([^']+)'", cupboard)
if not m:
    raise SystemExit('Crystal Tumbler room payload not found')
room = base64.b64decode(m.group(1)).decode('utf-8')

def extract_svg(pattern, label):
    mm = re.search(pattern, room, re.S | re.I)
    if not mm:
        raise SystemExit(f'{label} SVG not found in Crystal Tumbler room')
    svg = mm.group(0).strip()
    try:
        svg.encode('ascii')
    except UnicodeEncodeError:
        raise SystemExit(f'{label} SVG unexpectedly contains non-ASCII text')
    return svg

god_svg = extract_svg(r'<svg\b[^>]*class="lr-god-symbol"[^>]*>.*?</svg>', 'God')
goddess_svg = extract_svg(r'<svg\b[^>]*class="goddess-symbol"[^>]*>.*?</svg>', 'Goddess')
GOD_B64 = base64.b64encode(god_svg.encode('ascii')).decode('ascii')
GODDESS_B64 = base64.b64encode(goddess_svg.encode('ascii')).decode('ascii')

# The native shell is still the proven 2.7.1 owner. Only its frozen PRINT COPY is simplified.
freeze_old = '''                + "function freeze(doc){"
                + "var clone=doc.documentElement.cloneNode(true);copyFormState(doc,clone);freezeFrames(doc,clone);"
                + "var head=clone.querySelector('head');if(head&&!head.querySelector('base')){var base=clone.ownerDocument.createElement('base');base.setAttribute('href',doc.baseURI||'https://greenman.local/index.html');head.insertBefore(base,head.firstChild);}"
                + "return '<!doctype html>'+clone.outerHTML;"
                + "}"'''

font_css = r"""@font-face{font-family:'Cinzel';src:url('https://greenman.local/fonts/Cinzel.ttf') format('truetype');font-style:normal;font-weight:400 900;font-display:block;}@font-face{font-family:'IM Fell English';src:url('https://greenman.local/fonts/IMFellEnglish-Regular.ttf') format('truetype');font-style:normal;font-weight:400;font-display:block;}@font-face{font-family:'IM Fell English';src:url('https://greenman.local/fonts/IMFellEnglish-Italic.ttf') format('truetype');font-style:italic;font-weight:400;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-Regular.ttf') format('truetype');font-style:normal;font-weight:400;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-Italic.ttf') format('truetype');font-style:italic;font-weight:400;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-SemiBold.ttf') format('truetype');font-style:normal;font-weight:600;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-SemiBoldItalic.ttf') format('truetype');font-style:italic;font-weight:600;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-Bold.ttf') format('truetype');font-style:normal;font-weight:700;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-BoldItalic.ttf') format('truetype');font-style:italic;font-weight:700;font-display:block;}"""

# Keep the exact room artwork. Print CSS only controls its inline size/position.
star_svg = '<svg class="gm-pdf-star-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 1.8 L14.4 9.6 L22.2 12 L14.4 14.4 L12 22.2 L9.6 14.4 L1.8 12 L9.6 9.6 Z" fill="currentColor"/></svg>'
star_b64 = base64.b64encode(star_svg.encode('ascii')).decode('ascii')

# JS goes into the shell bridge as Java string fragments. Keep each literal modest in size.
js_lines = [
    "var GM_PDF_GOD_SVG=atob('"+GOD_B64+"'),GM_PDF_GODDESS_SVG=atob('"+GODDESS_B64+"'),GM_PDF_STAR_SVG=atob('"+star_b64+"');",
    "function gmFirstGradientColor(v){var m=String(v||'').match(/rgba?\\([^)]*\\)|#[0-9a-f]{3,8}/i);return m?m[0]:'';}",
    "function gmMakeInline(doc,kind){var span=doc.createElement('span');span.className='gm-pdf-inline-symbol gm-pdf-'+kind;if(kind==='god')span.innerHTML=GM_PDF_GOD_SVG;else if(kind==='goddess')span.innerHTML=GM_PDF_GODDESS_SVG;else span.innerHTML=GM_PDF_STAR_SVG;return span;}",
    "function gmReplaceHeavyGlyphs(root){try{var doc=root.ownerDocument||root,w=doc.createTreeWalker(root,4,null,false),nodes=[],n;while((n=w.nextNode()))nodes.push(n);for(var i=0;i<nodes.length;i++){n=nodes[i];var p=n.parentNode;if(!p||!n.nodeValue||!/[☀☽☾✦₂]/.test(n.nodeValue))continue;var tag=String(p.nodeName||'').toLowerCase();if(tag==='style'||tag==='script'||tag==='svg'||tag==='text')continue;var bits=n.nodeValue.split(/([☀☽☾✦₂])/),f=doc.createDocumentFragment();for(var j=0;j<bits.length;j++){var b=bits[j];if(!b)continue;if(b==='☀')f.appendChild(gmMakeInline(doc,'god'));else if(b==='☽'||b==='☾')f.appendChild(gmMakeInline(doc,'goddess'));else if(b==='✦')f.appendChild(gmMakeInline(doc,'star'));else if(b==='₂'){var sub=doc.createElement('sub');sub.className='gm-pdf-sub2';sub.textContent='2';f.appendChild(sub);}else f.appendChild(doc.createTextNode(b));}p.replaceChild(f,n);}}catch(_e){}}",
    "function gmFlattenPair(srcRoot,cloneRoot){try{var win=(srcRoot.ownerDocument||srcRoot).defaultView||window,src=[srcRoot],dst=[cloneRoot],sa=srcRoot.querySelectorAll?srcRoot.querySelectorAll('*'):[],da=cloneRoot.querySelectorAll?cloneRoot.querySelectorAll('*'):[];for(var x=0;x<sa.length;x++)src.push(sa[x]);for(var y=0;y<da.length;y++)dst.push(da[y]);var lim=Math.min(src.length,dst.length);for(var i=0;i<lim;i++){var a=src[i],b=dst[i];if(!a||!b||!a.nodeType||a.nodeType!==1)continue;var cs;try{cs=win.getComputedStyle(a);}catch(_e){continue;}var bg=String(cs.backgroundImage||'');if(/gradient\\(/i.test(bg)){var col=gmFirstGradientColor(bg);b.style.setProperty('background-image','none','important');if(col)b.style.setProperty('background-color',col,'important');}b.style.setProperty('box-shadow','none','important');b.style.setProperty('text-shadow','none','important');b.style.setProperty('filter','none','important');var tag=String(b.nodeName||'').toLowerCase();if(tag!=='svg'&&tag!=='circle'&&tag!=='ellipse'&&tag!=='img')b.style.setProperty('border-radius','0','important');}}catch(_e){}}",
    "function hardenPrintClone(srcDoc,clone){try{gmFlattenPair(srcDoc.documentElement||srcDoc,clone);Array.prototype.forEach.call(clone.querySelectorAll('script,noscript,template'),function(n){if(n&&n.parentNode)n.parentNode.removeChild(n);});gmReplaceHeavyGlyphs(clone);var head=clone.querySelector('head');if(head&&!head.querySelector('#gm-pdf-hardened-print')){var st=clone.ownerDocument.createElement('style');st.id='gm-pdf-hardened-print';st.textContent=" + json.dumps(font_css + r"@media print{*,*::before,*::after{box-shadow:none!important;text-shadow:none!important;filter:none!important;background-image:none!important;}*:not(svg):not(circle):not(ellipse):not(img),*::before,*::after{border-radius:0!important}.gm-pdf-inline-symbol{display:inline-flex!important;align-items:center!important;justify-content:center!important;width:1.05em!important;height:1.05em!important;vertical-align:-.16em!important;margin:0 .08em!important;color:currentColor!important}.gm-pdf-inline-symbol svg{display:block!important;position:static!important;left:auto!important;top:auto!important;transform:none!important;width:1.05em!important;height:1.05em!important;max-width:1.05em!important;max-height:1.05em!important;opacity:1!important;filter:none!important}.gm-pdf-star svg{width:.78em!important;height:.78em!important}.gm-pdf-sub2{font-size:.72em!important;vertical-align:sub!important;line-height:0!important}}") + ";head.appendChild(st);}}catch(_e){}return clone;}",
]

def java_fragment(js):
    # Java string literal for a JS fragment; keep one + "..." per logical line.
    return '                + ' + json.dumps(js, ensure_ascii=False).replace('\\/', '/')

hardening_java = '\n'.join(java_fragment(line) for line in js_lines)
freeze_new = hardening_java + '''
                + "function freeze(doc){"
                + "var clone=doc.documentElement.cloneNode(true);copyFormState(doc,clone);freezeFrames(doc,clone);hardenPrintClone(doc,clone);"
                + "var head=clone.querySelector('head');if(head&&!head.querySelector('base')){var base=clone.ownerDocument.createElement('base');base.setAttribute('href',doc.baseURI||'https://greenman.local/index.html');head.insertBefore(base,head.firstChild);}"
                + "return '<!doctype html>'+clone.outerHTML;"
                + "}"'''

if s.count(freeze_old) != 1:
    raise SystemExit(f'freeze anchor count was {s.count(freeze_old)}, expected 1')
s = s.replace(freeze_old, freeze_new, 1)

# Harden nested saved-page/BoS iframe clones before serialising them to srcdoc.
frame_old = '''                + "dst[i].removeAttribute('src');dst[i].setAttribute('srcdoc','<!doctype html>'+ic.outerHTML);"'''
frame_new = '''                + "hardenPrintClone(idoc,ic);dst[i].removeAttribute('src');dst[i].setAttribute('srcdoc','<!doctype html>'+ic.outerHTML);"'''
if s.count(frame_old) != 1:
    raise SystemExit(f'nested-frame anchor count was {s.count(frame_old)}, expected 1')
s = s.replace(frame_old, frame_new, 1)

# One print-job naming owner. It reads the finished print page so names follow the actual content.
install_anchor = '''                + "function install(win,doc){"'''
name_helpers = [
    "function gmNamePart(v){var s=String(v==null?'':v).replace(/&/g,' and ').replace(/[\\r\\n\\t]+/g,' ').replace(/[^A-Za-z0-9 _-]+/g,' ').replace(/\\s+/g,' ').trim().replace(/ /g,'_').replace(/_+/g,'_').replace(/^_+|_+$/g,'');return s||'Greenman';}",
    "function gmDate(){var d=new Date(),p=function(n){return String(n).padStart(2,'0');};return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());}",
    "function gmText(el){return el?String(el.textContent||'').replace(/\\s+/g,' ').trim():'';}",
    "function gmSpellIdentity(doc){try{var nodes=doc.querySelectorAll('h1,h2,h3,.pp-spell-title,.spell-title,.gm-title');for(var i=0;i<nodes.length;i++){var t=gmText(nodes[i]),m=t.match(/^(.{1,90}?)\\s*[·•]\\s*(Spell Jar|Charm Bag|Smoke(?:\\s*&\\s*|\\s+and\\s+)Flame)\\s*$/i);if(m)return gmNamePart(m[1])+'_'+gmNamePart(m[2]);}var all=gmText(doc.body),m2=all.match(/(?:Greenman HedgeWitchery\\s+)?(.{1,90}?)\\s*[·•]\\s*(Spell Jar|Charm Bag|Smoke(?:\\s*&\\s*|\\s+and\\s+)Flame)/i);if(m2)return gmNamePart(m2[1])+'_'+gmNamePart(m2[2]);}catch(_e){}return'';}",
    "function gmPageKind(all){if(/INSTRUCTIONS\\s*[·:-]?\\s*PAGE\\s*1\\s*OF\\s*2/i.test(all))return'Instructions_Page_1';if(/INSTRUCTIONS\\s*[·:-]?\\s*PAGE\\s*2\\s*OF\\s*2/i.test(all))return'Instructions_Page_2';if(/SUMMARY\\s*[·:-]?\\s*PAGE\\s*1\\s*OF\\s*2/i.test(all))return'Summary_Page_1';if(/SUMMARY\\s*[·:-]?\\s*PAGE\\s*2\\s*OF\\s*2/i.test(all))return'Summary_Page_2';if(/\\bALTAR\\b/i.test(all))return'Altar';if(/ITEM LIST|CORRESPONDENCES/i.test(all))return'Information';return'A4_Page';}",
    "function printJobName(doc){try{var title=String(doc.title||''),all=gmText(doc.body),ident=gmSpellIdentity(doc),date=gmDate();var admin=doc.querySelector('.gm-admin-book-cover-title');if(admin&&gmText(admin))return gmNamePart(gmText(admin))+'_'+date;var gname=doc.querySelector('#sheetName'),gcat=doc.querySelector('#sheetCategory');if(gname&&gmText(gname)){var cat=gmText(gcat).replace(/Information Sheet/i,'').trim()||'Item';return gmNamePart(gmText(gname))+'_'+gmNamePart(cat)+'_Grimoire';}var bosBook=/Book of Shadows/i.test(title)&&/Your record of spells cast and magic worked|\\bContents\\b.*\\bItem Index\\b/i.test(all);if(bosBook)return'Greenman_Book_of_Shadows_'+date;if(/Lite Pack/i.test(title)&&ident)return ident+'_Lite_Pack_'+date;if(/FullPack|Full Pack/i.test(title)&&ident)return ident+'_Full_Pack_'+date;if(/Book of Shadows/i.test(title)&&ident)return ident+'_BoS_Entry_'+date;if(/Journal/i.test(title)&&ident)return ident+'_Journal_Entry_'+date;if(/Journal/i.test(title))return'Greenman_Journal_'+date;if(/(?:_Page\\b|\\bA4 Page\\b|\\bPage\\b)/i.test(title)&&ident)return ident+'_'+gmPageKind(all)+'_'+date;if(ident)return ident+'_'+gmNamePart(title||'PDF')+'_'+date;return gmNamePart(title||'Greenman_HedgeWitchery');}catch(_e){return'Greenman_HedgeWitchery';}}",
]
helpers_java = '\n'.join(java_fragment(x) for x in name_helpers) + '\n                + "function install(win,doc){"'
if s.count(install_anchor) != 1:
    raise SystemExit(f'install anchor count was {s.count(install_anchor)}, expected 1')
s = s.replace(install_anchor, helpers_java, 1)

send_old = '''                + "var send=function(){try{nativeBridge.printDocument(freeze(doc),doc.title||'Greenman HedgeWitchery');}catch(err){nativeBridge.showMessage('The print document could not be sent to Android.');}"'''
send_new = '''                + "var send=function(){try{nativeBridge.printDocument(freeze(doc),printJobName(doc));}catch(err){nativeBridge.showMessage('The print document could not be sent to Android.');}"'''
if s.count(send_old) != 1:
    raise SystemExit(f'print-name handoff anchor count was {s.count(send_old)}, expected 1')
s = s.replace(send_old, send_new, 1)

# Local TTFs are APK assets. Explicit MIME avoids WebView/vendor guessing differences.
mime_old = '''    private static String guessMimeType(String path) {
        String guessed = URLConnection.guessContentTypeFromName(path);'''
mime_new = '''    private static String guessMimeType(String path) {
        String lowerPath = path == null ? "" : path.toLowerCase(Locale.ROOT);
        if (lowerPath.endsWith(".ttf")) {
            return "font/ttf";
        }
        if (lowerPath.endsWith(".woff2")) {
            return "font/woff2";
        }
        String guessed = URLConnection.guessContentTypeFromName(path);'''
if s.count(mime_old) != 1:
    raise SystemExit(f'MIME anchor count was {s.count(mime_old)}, expected 1')
s = s.replace(mime_old, mime_new, 1)

# Give local fonts a little extra time to settle before Android creates the adapter.
delay_old = '''            }, 850L);'''
delay_new = '''            }, 1150L);'''
if s.count(delay_old) != 1:
    raise SystemExit(f'print settle delay anchor count was {s.count(delay_old)}, expected 1')
s = s.replace(delay_old, delay_new, 1)

for forbidden in ('PhoneFriendlyPictureAdapter', 'capturePicture()', 'nativePrintHtml', 'gmNativePrintHtml'):
    if forbidden in s:
        raise SystemExit(f'forbidden print path found after PDF repair: {forbidden}')
for required in (
    'function hardenPrintClone(', 'gm-pdf-hardened-print', 'GM_PDF_GOD_SVG', 'GM_PDF_GODDESS_SVG',
    "fonts/Cinzel.ttf", "fonts/IMFellEnglish-Regular.ttf", "fonts/CrimsonText-Regular.ttf",
    'function printJobName(', 'nativeBridge.printDocument(freeze(doc),printJobName(doc))', 'return "font/ttf";'
):
    if required not in s:
        raise SystemExit(f'PDF repair marker missing: {required}')

out.write_text(s, encoding='utf-8')
print(f'Installed full PDF hardening + canonical Tumbler symbols + dynamic names: {out}')
print('God SVG bytes:', len(god_svg), 'Goddess SVG bytes:', len(goddess_svg))
