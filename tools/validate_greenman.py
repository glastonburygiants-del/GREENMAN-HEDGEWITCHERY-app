from pathlib import Path
import re, json, subprocess, tempfile, sys

path=Path(sys.argv[1])
s=path.read_text(encoding='utf-8')
errors=[]
script_re=re.compile(r'<script\b([^>]*)>(.*?)</script\s*>',re.I|re.S)
outer_scripts=list(script_re.finditer(s))
if len(outer_scripts)!=s.lower().count('</script>'):
    errors.append(f'Outer script extraction mismatch: {len(outer_scripts)} vs {s.lower().count("</script>")}')

def node_check(code,label):
    code=code.strip()
    if code.startswith('<![CDATA[') and code.endswith(']]>'):
        code=code[len('<![CDATA['):-len(']]>')]
    with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8') as f:
        f.write(code); tmp=f.name
    p=subprocess.run(['node','--check',tmp],capture_output=True,text=True)
    Path(tmp).unlink(missing_ok=True)
    if p.returncode: errors.append(label+'\n'+p.stderr[:2000])

for i,m in enumerate(outer_scripts,1):
    attrs=m.group(1).lower()
    if 'application/json' in attrs or 'text/plain' in attrs: continue
    node_check(m.group(2),f'Outer script {i} syntax error')

pages={}
marker='const PAGES = '
idx=s.find(marker)
if idx<0: errors.append('const PAGES object not found')
else:
    pos=idx+len(marker)
    try:
        obj,used=json.JSONDecoder().raw_decode(s[pos:])
        if isinstance(obj,dict): pages.update(obj)
        else: errors.append('PAGES is not an object')
    except Exception as e: errors.append('PAGES JSON decode failed: '+repr(e))

for m in re.finditer(r'PAGES\.([A-Za-z0-9_]+)\s*=\s*',s):
    key=m.group(1); pos=m.end()
    try:
        val,used=json.JSONDecoder().raw_decode(s[pos:])
        if isinstance(val,str): pages[key]=val
    except Exception: pass

embedded=0
for key,html in pages.items():
    if not isinstance(html,str): continue
    for j,m in enumerate(script_re.finditer(html),1):
        attrs=m.group(1).lower()
        if 'application/json' in attrs or 'text/plain' in attrs: continue
        embedded+=1; node_check(m.group(2),f'Embedded page {key} script {j} syntax error')

if not re.search(r'showPage\(\s*[\'\"]home[\'\"]\s*\)',s): errors.append('Exact showPage(home) boot route not found')
print('file',path)
print('outer_scripts',len(outer_scripts))
print('pages',len(pages))
print('embedded_scripts_checked',embedded)
print('raw_closing_scripts',s.lower().count('</script>'))
print('escaped_closing_scripts',s.lower().count('<\\/script>'))
if errors:
    print('VALIDATION_FAILED',len(errors))
    for e in errors[:20]: print('\n---\n'+e)
    sys.exit(1)
print('VALIDATION_OK')
