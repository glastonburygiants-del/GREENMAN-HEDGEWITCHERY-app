#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, tempfile, zipfile

PARENT_SHA256 = 'b65f9e5d0ca2a886f5646bc263a0939733ca990f4e73e549a273b85ccb9d93de'
EXPECTED_INDEX_SHA256 = 'de2c377e7fe9ca11f120cdea5b3a6da3a2ef95a7c097448b792bb58073bec293'
EXPECTED_SPELL_SHA256 = '7b4fcd320ec869ac8719649207235cffa8a7a38d4bd772402c4586b46b3a8692'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('parent_v5_apk')
    ap.add_argument('output_unsigned_apk')
    ap.add_argument('--patch-script', default='tools/fix_deity_gender_v51.py')
    ap.add_argument('--report', default='deity-gender-audit-v51.json')
    args = ap.parse_args()

    parent = Path(args.parent_v5_apk)
    out = Path(args.output_unsigned_apk)
    if sha(parent) != PARENT_SHA256:
        raise SystemExit('STOP: parent V5 APK hash is not the approved exact V5 standalone')

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        with zipfile.ZipFile(parent, 'r') as zin:
            index = zin.read('assets/index.html').decode('utf-8')
            marker = 'const PAGES = '
            p0 = index.index(marker) + len(marker)
            pages, _ = json.JSONDecoder().raw_decode(index[p0:])
            spell = pages['spellBuilder']
            src = td / 'spellBuilder.html'
            fixed = td / 'spellBuilder.fixed.html'
            src.write_text(spell, encoding='utf-8')
            subprocess.check_call([sys.executable, args.patch_script, str(src), str(fixed), '--report', args.report])
            fixed_spell = fixed.read_text(encoding='utf-8')

            if hashlib.sha256(fixed_spell.encode()).hexdigest() != EXPECTED_SPELL_SHA256:
                raise SystemExit('STOP: patched spellBuilder hash differs from audited V5.1')

            sub = index[p0:]
            key = '"spellBuilder":'
            k = sub.index(key) + len(key)
            while sub[k].isspace():
                k += 1
            _, rel_end = json.JSONDecoder().raw_decode(sub[k:])
            abs_start, abs_end = p0 + k, p0 + k + rel_end
            encoded = json.dumps(fixed_spell, ensure_ascii=False, separators=(',', ':')).replace('</script>', '<\\/script>')
            new_index = index[:abs_start] + encoded + index[abs_end:]

            if hashlib.sha256(new_index.encode()).hexdigest() != EXPECTED_INDEX_SHA256:
                raise SystemExit('STOP: rebuilt index hash differs from audited V5.1')

            new_pages, new_end = json.JSONDecoder().raw_decode(new_index[p0:])
            changed = [key for key in pages if pages[key] != new_pages[key]]
            if changed != ['spellBuilder']:
                raise SystemExit(f'STOP: unexpected PAGES changes: {changed}')
            old_end = json.JSONDecoder().raw_decode(index[p0:])[1]
            if index[:p0] + '__PAGES__' + index[p0 + old_end:] != new_index[:p0] + '__PAGES__' + new_index[p0 + new_end:]:
                raise SystemExit('STOP: index content outside const PAGES changed')

            with zipfile.ZipFile(out, 'w') as zout:
                for info in zin.infolist():
                    if info.filename.upper().startswith('META-INF/'):
                        continue
                    payload = new_index.encode('utf-8') if info.filename == 'assets/index.html' else zin.read(info.filename)
                    zi = zipfile.ZipInfo(info.filename, info.date_time)
                    zi.compress_type = info.compress_type
                    zi.comment = info.comment
                    zi.extra = info.extra
                    zi.internal_attr = info.internal_attr
                    zi.external_attr = info.external_attr
                    zi.create_system = info.create_system
                    zi.create_version = info.create_version
                    zi.extract_version = info.extract_version
                    zi.flag_bits = info.flag_bits
                    zout.writestr(zi, payload)

    print('V5.1 unsigned APK rebuilt from exact V5 parent')
    print('parent_sha256=' + PARENT_SHA256)
    print('index_sha256=' + EXPECTED_INDEX_SHA256)
    print('spellBuilder_sha256=' + EXPECTED_SPELL_SHA256)


if __name__ == '__main__':
    main()
