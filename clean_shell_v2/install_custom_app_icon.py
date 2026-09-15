#!/usr/bin/env python3
from pathlib import Path
import base64, hashlib, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: install_custom_app_icon.py ANDROID_PROJECT_DIR')

project = Path(sys.argv[1])
res = project / 'app/src/main/res'
source_b64 = Path(__file__).with_name('greenman_custom_app_icon_192_webp.b64')
raw = base64.b64decode(source_b64.read_text(encoding='ascii'))
expected = '0915a0ddfee14a7bbba4b998128b4da04d5aa139b0bcbcc81cba0253e8090dc1'
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise SystemExit(f'approved Greenman icon checksum mismatch: {actual}')

# Store the approved Greenman image once. 192px is the native xxxhdpi legacy
# launcher size; Android scales it for the other density buckets and adaptive mask.
drawable_nodpi = res / 'drawable-nodpi'
drawable_nodpi.mkdir(parents=True, exist_ok=True)
art = drawable_nodpi / 'greenman_launcher_art.webp'
art.write_bytes(raw)

# Pre-Android-8 launcher resources use the approved image directly.
legacy = '''<?xml version="1.0" encoding="utf-8"?>
<bitmap xmlns:android="http://schemas.android.com/apk/res/android"
    android:src="@drawable/greenman_launcher_art"
    android:gravity="fill"
    android:filter="true"
    android:antialias="true" />
'''
legacy_dir = res / 'mipmap-anydpi'
legacy_dir.mkdir(parents=True, exist_ok=True)
(legacy_dir / 'ic_launcher.xml').write_text(legacy, encoding='utf-8')
(legacy_dir / 'ic_launcher_round.xml').write_text(legacy, encoding='utf-8')

# Adaptive foreground keeps the whole gold rim and Greenman shield comfortably
# inside common Samsung/Pixel launcher masks.
foreground = '''<?xml version="1.0" encoding="utf-8"?>
<inset xmlns:android="http://schemas.android.com/apk/res/android"
    android:drawable="@drawable/greenman_launcher_art"
    android:insetLeft="14dp"
    android:insetTop="14dp"
    android:insetRight="14dp"
    android:insetBottom="14dp" />
'''
drawable = res / 'drawable'
drawable.mkdir(parents=True, exist_ok=True)
(drawable / 'ic_launcher_foreground.xml').write_text(foreground, encoding='utf-8')

# Existing adaptive owners stay authoritative and must still point at our foreground.
for name in ('ic_launcher.xml', 'ic_launcher_round.xml'):
    p = res / 'mipmap-anydpi-v26' / name
    if not p.exists():
        raise SystemExit(f'missing adaptive icon owner: {p}')
    text = p.read_text(encoding='utf-8')
    if '@drawable/ic_launcher_foreground' not in text:
        raise SystemExit(f'adaptive icon does not use foreground owner: {p}')

if hashlib.sha256(art.read_bytes()).hexdigest() != expected:
    raise SystemExit('installed Greenman launcher art changed during write')

print('Installed approved Greenman picture as Android launcher icon')
