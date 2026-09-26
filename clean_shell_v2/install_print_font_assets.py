#!/usr/bin/env python3
from pathlib import Path
import sys, urllib.request

if len(sys.argv) != 2:
    raise SystemExit('usage: install_print_font_assets.py PROJECT_DIR')

project = Path(sys.argv[1]).resolve()
assets = project / 'app' / 'src' / 'main' / 'assets' / 'fonts'
assets.mkdir(parents=True, exist_ok=True)

# Pin Google Fonts so the APK build is reproducible and entirely offline at runtime.
REV='2d85e20401920891efb7cd6272d6339685df2820'
BASE=f'https://raw.githubusercontent.com/google/fonts/{REV}/ofl'
FILES={
    'Cinzel.ttf': f'{BASE}/cinzel/Cinzel%5Bwght%5D.ttf',
    'IMFellEnglish-Regular.ttf': f'{BASE}/imfellenglish/IMFeENrm28P.ttf',
    'IMFellEnglish-Italic.ttf': f'{BASE}/imfellenglish/IMFeENit28P.ttf',
    'CrimsonText-Regular.ttf': f'{BASE}/crimsontext/CrimsonText-Regular.ttf',
    'CrimsonText-Italic.ttf': f'{BASE}/crimsontext/CrimsonText-Italic.ttf',
    'CrimsonText-SemiBold.ttf': f'{BASE}/crimsontext/CrimsonText-SemiBold.ttf',
    'CrimsonText-SemiBoldItalic.ttf': f'{BASE}/crimsontext/CrimsonText-SemiBoldItalic.ttf',
    'CrimsonText-Bold.ttf': f'{BASE}/crimsontext/CrimsonText-Bold.ttf',
    'CrimsonText-BoldItalic.ttf': f'{BASE}/crimsontext/CrimsonText-BoldItalic.ttf',
}

for name,url in FILES.items():
    target=assets/name
    print('Fetching', name)
    req=urllib.request.Request(url,headers={'User-Agent':'Greenman-HedgeWitchery-build'})
    with urllib.request.urlopen(req, timeout=40) as r:
        data=r.read()
    if len(data) < 10000:
        raise SystemExit(f'font download too small: {name} ({len(data)} bytes)')
    target.write_bytes(data)

# Ship the OFL texts inside the APK beside the fonts.
license_dir=assets/'licenses'
license_dir.mkdir(exist_ok=True)
for family in ('cinzel','imfellenglish','crimsontext'):
    url=f'{BASE}/{family}/OFL.txt'
    req=urllib.request.Request(url,headers={'User-Agent':'Greenman-HedgeWitchery-build'})
    with urllib.request.urlopen(req, timeout=40) as r:
        data=r.read()
    if len(data) < 1000:
        raise SystemExit(f'license download too small: {family}')
    (license_dir/f'{family}-OFL.txt').write_bytes(data)

print('Installed local print fonts:', len(FILES))
