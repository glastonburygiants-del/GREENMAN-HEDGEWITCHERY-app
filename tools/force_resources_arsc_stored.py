#!/usr/bin/env python3
"""Android 11+ (API 30+) refuses to install any APK whose resources.arsc entry
isn't stored uncompressed and 4-byte aligned - PackageManager fails parsing
with "Targeting R+ (version 30 and above) requires the resources.arsc of
installed APKs to be stored uncompressed and aligned on a 4-byte boundary"
and the install silently never completes.

apktool's rebuild step does not reliably guarantee this: depending on its
aapt2 invocation, resources.arsc can come out DEFLATEd instead of STORED.
zipalign cannot fix this after the fact - it only aligns entries that are
already stored, it never re-stores a compressed one. So this has to be
corrected between `apktool b` and `zipalign`, and asserted in CI so a build
that regresses this can never again be shipped without failing loudly first.

Rewrites the given APK in place (via a temp file + atomic replace),
preserving every entry's bytes, name, compression method, and modified
timestamp exactly except resources.arsc, which is rewritten as ZIP_STORED.
"""
from pathlib import Path
import sys
import zipfile

if len(sys.argv) != 2:
    raise SystemExit('usage: force_resources_arsc_stored.py APK')

apk = Path(sys.argv[1])
tmp = apk.with_suffix(apk.suffix + '.restore-tmp')

with zipfile.ZipFile(apk, 'r') as src:
    names = src.namelist()
    if 'resources.arsc' not in names:
        raise SystemExit('resources.arsc missing from APK')

    with zipfile.ZipFile(tmp, 'w') as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            new_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new_info.external_attr = info.external_attr
            new_info.create_system = info.create_system
            if info.filename == 'resources.arsc':
                new_info.compress_type = zipfile.ZIP_STORED
            else:
                new_info.compress_type = info.compress_type
            dst.writestr(new_info, data)

tmp.replace(apk)

with zipfile.ZipFile(apk, 'r') as check:
    info = check.getinfo('resources.arsc')
    if info.compress_type != zipfile.ZIP_STORED:
        raise SystemExit('resources.arsc is still compressed after rewrite')

print('resources.arsc forced to ZIP_STORED (uncompressed)')
