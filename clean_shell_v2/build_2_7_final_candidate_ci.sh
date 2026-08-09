#!/usr/bin/env bash
set -euo pipefail

ZIP_FILE="$(find "$GITHUB_WORKSPACE" -maxdepth 1 -type f -name 'GREENMAN_HEDGEWITCHERY_ANDROID_PROJECT_GATHER_FIXED*.zip' -print -quit)"
test -s "$ZIP_FILE"
mkdir -p "$GITHUB_WORKSPACE/extracted-final-27"
unzip -q "$ZIP_FILE" -d "$GITHUB_WORKSPACE/extracted-final-27"
PROJECT_DIR="$(find "$GITHUB_WORKSPACE/extracted-final-27" -type f -name settings.gradle -printf '%h\n' | head -n 1)"
test -n "$PROJECT_DIR"
INDEX_FILE="$PROJECT_DIR/app/src/main/assets/index.html"
JAVA_FILE="$PROJECT_DIR/app/src/main/java/com/greenman/hedgewitchery/MainActivity.java"

python "$GITHUB_WORKSPACE/tools/patch_supply_room.py" "$INDEX_FILE" "$INDEX_FILE"
echo "53224a35f792777ba70d2f13323d81f38a7037dadc9b2bb753b73157fee93cb2  $INDEX_FILE" | sha256sum -c -

python "$GITHUB_WORKSPACE/clean_shell_v2/install_proven_summary_print.py" "$INDEX_FILE" "$INDEX_FILE"
echo "da7cdc5a815fc48879a48d0b044845000bbb27b5d831a723e5b587a7ee4418a1  $INDEX_FILE" | sha256sum -c -

python "$GITHUB_WORKSPACE/clean_shell_v2/install_ui_feedback_v2.py" "$INDEX_FILE" "$INDEX_FILE"
python "$GITHUB_WORKSPACE/clean_shell_v2/install_welcome_mat.py" "$INDEX_FILE" "$INDEX_FILE"
cp "$INDEX_FILE" "$RUNNER_TEMP/GREENMAN_27_PRE_FINAL.html"

python "$GITHUB_WORKSPACE/clean_shell_v2/install_final_tightening.py" "$INDEX_FILE" "$INDEX_FILE"
# 2.7.7: repair the two device-visible layout faults without changing the print owner:
# saved BoS pages must not be crushed to miniature scale, and instruction pages
# are measured only after the packaged Greenman fonts are loaded.
python "$GITHUB_WORKSPACE/clean_shell_v2/install_print_layout_277.py" "$INDEX_FILE" "$INDEX_FILE"
# 2.7.8: recover old BoS snapshots that retained runtime phone/PDF fitting residue.
# Use only each saved page's own A4 CSS, strip stored scale/font-fit inline residue,
# and clean all future BoS captures before they enter localStorage.
python "$GITHUB_WORKSPACE/clean_shell_v2/install_bos_snapshot_recovery_278.py" "$INDEX_FILE" "$INDEX_FILE"
# 2.7.11: keep every Grimoire record on one A4 sheet and replace browser-native grey dialogs with Greenman-styled cards.
python "$GITHUB_WORKSPACE/clean_shell_v2/install_single_grimoire_dialogs_2711.py" "$INDEX_FILE" "$INDEX_FILE"
python "$GITHUB_WORKSPACE/clean_shell_v2/repair_embedded_script_boundaries.py" "$INDEX_FILE" "$INDEX_FILE"
# 2.7.13: fitGrimoirePages (BoS) had its whole-page scale calculation deleted
# by 2.7.11, relying only on per-box text shrinking with no fallback, so long
# entries bleed off the page. fitFlatPages (BoS + Journal) had its adaptive
# best-fit search replaced by 2.7.8 with a single measurement clamped to a
# hard-coded 0.82 minimum scale, which fixed over-shrinking but now bleeds
# any saved page that genuinely needs to shrink further. Both are restored to
# real adaptive measurement while keeping the later patches' genuinely good
# parts (stale-snapshot cleanup, per-box text shrinking).
python "$GITHUB_WORKSPACE/clean_shell_v2/repair_print_fit_regressions.py" "$INDEX_FILE" "$INDEX_FILE"
grep -q "Binary search for the LARGEST scale that still fits" "$INDEX_FILE"
grep -q "Per-box text shrinking runs first" "$INDEX_FILE"
! grep -q "scale=Math.max(.82,scale\*.995)" "$INDEX_FILE"
cp "$INDEX_FILE" "$RUNNER_TEMP/GREENMAN_27_EXPECTED.html"
sha256sum "$INDEX_FILE" | tee "$RUNNER_TEMP/GREENMAN_27_INDEX_SHA256.txt"

grep -q "gm-final-book-owner-v1" "$INDEX_FILE"
grep -q "gm-admin-book-printer-v1" "$INDEX_FILE"
grep -q "gm-admin-master-book-owner-v1" "$INDEX_FILE"
grep -q "Greenman Book Printer" "$INDEX_FILE"
grep -q "Final identity owner" "$INDEX_FILE"
grep -q "if(g==='Sundries')renderSundries()" "$INDEX_FILE"
grep -q "Your record of spells cast and magic worked." "$INDEX_FILE"
grep -q "data:image/webp;base64," "$INDEX_FILE"
! grep -q "gm-journal-bos-print-wait-patch-v4" "$INDEX_FILE"
grep -q "gmEnsureJournalPrintFonts" "$INDEX_FILE"
grep -q "GM_LOCAL_PRINT_FONT_CSS" "$INDEX_FILE"
grep -q "data-gm-instruction-fit" "$INDEX_FILE"
grep -q "gmRecoverBosSnapshotPage" "$INDEX_FILE"
grep -q "gm-bos-native" "$INDEX_FILE"
grep -q "gmCleanBosSnapshotClone" "$INDEX_FILE"
grep -q "gm-grimoire-single-page-v2" "$INDEX_FILE"
grep -q "gm-grimoire-one" "$INDEX_FILE"
grep -q "gm-greenman-dialog-style" "$INDEX_FILE"
grep -q "__GM_GREENMAN_DIALOG_SHIM__" "$INDEX_FILE"
! grep -q "gm-grimoire-split-1" "$INDEX_FILE"
! grep -q "gm-grimoire-split-2" "$INDEX_FILE"

python - <<'PY'
from pathlib import Path
import json,re,subprocess,tempfile,os
before=Path(os.environ['RUNNER_TEMP']+'/GREENMAN_27_PRE_FINAL.html').read_text(encoding='utf-8')
after=Path(os.environ['RUNNER_TEMP']+'/GREENMAN_27_EXPECTED.html').read_text(encoding='utf-8')

def pages_with_raw(s):
    m='const PAGES = '; st=s.index(m)+len(m); obj,end=json.JSONDecoder().raw_decode(s[st:]); return obj,s[st:st+end]

a,raw_before=pages_with_raw(before)
b,raw_after=pages_with_raw(after)
unsafe=raw_after.lower().count('</script>')
protected=raw_after.lower().count('<\\/script>')
assert unsafe==0, f'FATAL: {unsafe} unsafe inner </script> boundaries remain'
assert protected==70, f'expected 70 protected inner script closers, got {protected}'
print('Boundary guard passed: 0 unsafe,',protected,'protected inner script closers')

for key in ('home','moon','numerology','planetTiming','planets'):
    assert a[key]==b[key], f'unexpected page changed: {key}'
def assigned(page,mark):
    i=page.index(mark)+len(mark); return json.JSONDecoder().raw_decode(page[i:].lstrip())[0]
assert assigned(a['grimoire'],'const ITEMS =')==assigned(b['grimoire'],'const ITEMS ='),'Grimoire ITEMS changed'
assert assigned(a['spellBuilder'],'window.GM_DATA =')==assigned(b['spellBuilder'],'window.GM_DATA ='),'Spell Builder GM_DATA changed'
assert 'gmEnsureJournalPrintFonts' in b['journal'] and 'data-gm-instruction-fit' in b['spellBuilder'],'2.7.7 print layout repair missing'
assert 'gmRecoverBosSnapshotPage' in b['journal'] and 'gmCleanBosSnapshotClone' in b['spellBuilder'],'2.7.8 BoS snapshot recovery missing'
assert "String(pg.css||'').trim()||String(snap.css||'')" in b['journal'],'2.7.8 must prefer page-local CSS over captured global fit CSS'
assert "data-gm-print-fit','1.0000" in b['journal'],'2.7.8 native BoS fit lock missing'
assert 'gm-grimoire-single-page-v2' in b['bos'] and 'gm-grimoire-one' in b['bos'],'2.7.11 single-page Grimoire owner missing'
assert 'gm-grimoire-split-1' not in b['bos'] and 'gm-grimoire-split-2' not in b['bos'],'abandoned split Grimoire code survived'
for _name,_html in b.items():
    assert not re.search(r'\bconfirm\s*\(',_html), f'native confirm survived in {_name}'
    if re.search(r'\balert\s*\(',_html):
        assert '__GM_GREENMAN_DIALOG_SHIM__' in _html, f'alert page lacks Greenman dialog shim: {_name}'

count=0
for name,html in b.items():
    for n,js in enumerate(re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',html,re.S|re.I)):
        count+=1
        p=Path(tempfile.gettempdir())/f'greenman27_{name}_{n}.js'; p.write_text(js,encoding='utf-8')
        r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
        if r.returncode:
            print(r.stderr); raise SystemExit(f'JavaScript syntax failure: {name} script {n}')
assert count==70, f'expected 70 embedded scripts, got {count}'
print('Database guard passed; embedded scripts checked:',count)

outer_count=0
for n,js in enumerate(re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',after,re.S|re.I)):
    outer_count+=1
    p=Path(tempfile.gettempdir())/f'greenman27_outer_{n}.js'; p.write_text(js,encoding='utf-8')
    r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if r.returncode:
        print(r.stderr); raise SystemExit(f'Outer-shell JavaScript syntax failure: script {n}')
print('Outer-shell scripts checked:',outer_count)
PY

python "$GITHUB_WORKSPACE/clean_shell_v2/install_custom_app_icon.py" "$PROJECT_DIR"
ICON_FILE="$PROJECT_DIR/app/src/main/res/drawable-nodpi/greenman_launcher_art.webp"
echo "0915a0ddfee14a7bbba4b998128b4da04d5aa139b0bcbcc81cba0253e8090dc1  $ICON_FILE" | sha256sum -c -

# Install the intended Greenman print fonts as LOCAL APK assets. Nothing depends on internet at print time.
python "$GITHUB_WORKSPACE/clean_shell_v2/install_print_font_assets.py" "$PROJECT_DIR"
FONT_DIR="$PROJECT_DIR/app/src/main/assets/fonts"
for font in Cinzel.ttf IMFellEnglish-Regular.ttf IMFellEnglish-Italic.ttf CrimsonText-Regular.ttf CrimsonText-Italic.ttf CrimsonText-SemiBold.ttf CrimsonText-SemiBoldItalic.ttf CrimsonText-Bold.ttf CrimsonText-BoldItalic.ttf; do
  test -s "$FONT_DIR/$font"
done

# Start from the proven 2.7.1 native print owner. Do NOT stack the 2.7.4 patch.
cp "$GITHUB_WORKSPACE/clean_shell_v2/MainActivity.java" "$JAVA_FILE"
python "$GITHUB_WORKSPACE/clean_shell_v2/install_fullscreen_bridge.py" "$JAVA_FILE" "$JAVA_FILE"
echo "08f6e0919be07f805cdac350a2d16b549789037fde724d58760488fd8486cad3  $JAVA_FILE" | sha256sum -c -

# Retain the repaired print bridge + hardening: harden the frozen print copy, use canonical Tumbler God/Goddess SVGs,
# eliminate the known heavy fallback glyphs, load local fonts, and retain dynamic PDF names.
python "$GITHUB_WORKSPACE/clean_shell_v2/install_pdf_hardened_names.py" "$JAVA_FILE" "$JAVA_FILE" "$INDEX_FILE"
grep -q "function hardenPrintClone" "$JAVA_FILE"
grep -q "gm-pdf-hardened-print" "$JAVA_FILE"
grep -q "GM_PDF_GOD_SVG" "$JAVA_FILE"
grep -q "GM_PDF_GODDESS_SVG" "$JAVA_FILE"
grep -q "fonts/Cinzel.ttf" "$JAVA_FILE"
grep -q "fonts/IMFellEnglish-Regular.ttf" "$JAVA_FILE"
grep -q "fonts/CrimsonText-Regular.ttf" "$JAVA_FILE"
grep -q "function printJobName" "$JAVA_FILE"
grep -q "nativeBridge.printDocument(freeze(doc),printJobName(doc))" "$JAVA_FILE"
grep -q 'return "font/ttf";' "$JAVA_FILE"
cp "$JAVA_FILE" "$RUNNER_TEMP/MainActivity_2_7_11_GRIMOIRE_SINGLE_GREENMAN_DIALOGS.java"
sha256sum "$JAVA_FILE" > "$RUNNER_TEMP/GREENMAN_2_7_11_JAVA_SHA256.txt"

# CRITICAL: Java can compile even when the JavaScript bridge string is malformed.
# Extract the exact bridge JavaScript from the generated MainActivity and syntax-check it with Node.
python - "$JAVA_FILE" "$RUNNER_TEMP/GREENMAN_NATIVE_PRINT_BRIDGE.js" <<'PYBRIDGE'
from pathlib import Path
import json,re,sys
src=Path(sys.argv[1]).read_text(encoding='utf-8')
start=src.index('String script = ')
end=src.index(';\n        webView.evaluateJavascript(script, null);', start)
chunk=src[start:end]
lits=re.findall(r'"(?:\\.|[^"\\])*"', chunk)
js=''.join(json.loads(x) for x in lits)
Path(sys.argv[2]).write_text(js, encoding='utf-8')
assert 'win.print=function()' in js
assert 'function hardenPrintClone' in js
assert 'nativeBridge.printDocument(freeze(doc),printJobName(doc))' in js
print('Native print bridge extracted:', len(js), 'chars')
PYBRIDGE
node --check "$RUNNER_TEMP/GREENMAN_NATIVE_PRINT_BRIDGE.js"
echo "Native print bridge syntax guard passed"

test "$(grep -c 'public void printDocument' "$JAVA_FILE")" -eq 1
test "$(grep -c 'private void openPrintDocument' "$JAVA_FILE")" -eq 1
test "$(grep -c 'private void printWebViewDocument' "$JAVA_FILE")" -eq 1
! grep -q "PhoneFriendly" "$JAVA_FILE"
! grep -q "capturePicture" "$JAVA_FILE"
! grep -q "nativePrintHtml" "$JAVA_FILE"
! grep -q "gmNativePrintHtml" "$JAVA_FILE"
! grep -q "function slimPrintClone" "$JAVA_FILE"

sed -i -E 's/versionCode[[:space:]]+[0-9]+/versionCode 30/' "$PROJECT_DIR/app/build.gradle"
sed -i -E 's/versionName[[:space:]]+"[^"]+"/versionName "2.7.13-print-fit-restore"/' "$PROJECT_DIR/app/build.gradle"

python "$GITHUB_WORKSPACE/clean_shell_v2/force_stable_debug_signing.py" "$PROJECT_DIR/app/build.gradle"
grep -q "GREENMAN_STABLE_DEBUG_SIGNING_V1" "$PROJECT_DIR/app/build.gradle"

cd "$PROJECT_DIR"
gradle :app:assembleDebug --no-daemon --stacktrace

APK_FILE="$(find "$PROJECT_DIR/app/build/outputs/apk/debug" -type f -name 'app-debug.apk' -print -quit)"
test -s "$APK_FILE"
unzip -p "$APK_FILE" assets/index.html > "$RUNNER_TEMP/GREENMAN_27_APK_INDEX.html"
cmp -s "$RUNNER_TEMP/GREENMAN_27_EXPECTED.html" "$RUNNER_TEMP/GREENMAN_27_APK_INDEX.html"
unzip -l "$APK_FILE" | grep -q 'greenman_launcher_art.*webp'
unzip -l "$APK_FILE" | grep -q 'assets/fonts/Cinzel.ttf'
unzip -l "$APK_FILE" | grep -q 'assets/fonts/IMFellEnglish-Regular.ttf'
unzip -l "$APK_FILE" | grep -q 'assets/fonts/CrimsonText-Regular.ttf'
"$ANDROID_HOME/build-tools/35.0.0/aapt" dump badging "$APK_FILE" > "$RUNNER_TEMP/GREENMAN_27_BADGING.txt"
grep -q "package: name='com.greenman.hedgewitchery' versionCode='30'" "$RUNNER_TEMP/GREENMAN_27_BADGING.txt"
grep -q "application-label:'Greenman HedgeWitchery'" "$RUNNER_TEMP/GREENMAN_27_BADGING.txt"
sha256sum "$APK_FILE" > "$RUNNER_TEMP/GREENMAN_27_APK_SHA256.txt"

cp "$APK_FILE" "$RUNNER_TEMP/GREENMAN_HEDGEWITCHERY_2.7.11_GRIMOIRE_SINGLE_GREENMAN_DIALOGS.apk"
echo "APK_FILE=$RUNNER_TEMP/GREENMAN_HEDGEWITCHERY_2.7.11_GRIMOIRE_SINGLE_GREENMAN_DIALOGS.apk" >> "$GITHUB_ENV"
