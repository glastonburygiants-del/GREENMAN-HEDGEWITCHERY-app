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

python - <<'PY'
from pathlib import Path
import json,re,subprocess,tempfile,os
before=Path(os.environ['RUNNER_TEMP']+'/GREENMAN_27_PRE_FINAL.html').read_text(encoding='utf-8')
after=Path(os.environ['RUNNER_TEMP']+'/GREENMAN_27_EXPECTED.html').read_text(encoding='utf-8')
def pages(s):
    m='const PAGES = '; st=s.index(m)+len(m); return json.JSONDecoder().raw_decode(s[st:])[0]
a,b=pages(before),pages(after)
for key in ('home','journal','moon','numerology','planetTiming','planets'):
    assert a[key]==b[key], f'unexpected page changed: {key}'
def assigned(page,mark):
    i=page.index(mark)+len(mark); return json.JSONDecoder().raw_decode(page[i:].lstrip())[0]
assert assigned(a['grimoire'],'const ITEMS =')==assigned(b['grimoire'],'const ITEMS ='),'Grimoire ITEMS changed'
assert assigned(a['spellBuilder'],'window.GM_DATA =')==assigned(b['spellBuilder'],'window.GM_DATA ='),'Spell Builder GM_DATA changed'
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
PY

python "$GITHUB_WORKSPACE/clean_shell_v2/install_custom_app_icon.py" "$PROJECT_DIR"
ICON_FILE="$PROJECT_DIR/app/src/main/res/drawable-nodpi/greenman_launcher_art.webp"
echo "0915a0ddfee14a7bbba4b998128b4da04d5aa139b0bcbcc81cba0253e8090dc1  $ICON_FILE" | sha256sum -c -

cp "$GITHUB_WORKSPACE/clean_shell_v2/MainActivity.java" "$JAVA_FILE"
python "$GITHUB_WORKSPACE/clean_shell_v2/install_fullscreen_bridge.py" "$JAVA_FILE" "$JAVA_FILE"
echo "08f6e0919be07f805cdac350a2d16b549789037fde724d58760488fd8486cad3  $JAVA_FILE" | sha256sum -c -
test "$(grep -c 'public void printDocument' "$JAVA_FILE")" -eq 1
test "$(grep -c 'private void openPrintDocument' "$JAVA_FILE")" -eq 1
test "$(grep -c 'private void printWebViewDocument' "$JAVA_FILE")" -eq 1
! grep -q "nativePrintHtml" "$JAVA_FILE"
! grep -q "gmNativePrintHtml" "$JAVA_FILE"

sed -i -E 's/versionCode[[:space:]]+[0-9]+/versionCode 18/' "$PROJECT_DIR/app/build.gradle"
sed -i -E 's/versionName[[:space:]]+"[^"]+"/versionName "2.7-final-candidate"/' "$PROJECT_DIR/app/build.gradle"

cd "$PROJECT_DIR"
gradle :app:assembleDebug --no-daemon --stacktrace

APK_FILE="$(find "$PROJECT_DIR/app/build/outputs/apk/debug" -type f -name 'app-debug.apk' -print -quit)"
test -s "$APK_FILE"
unzip -p "$APK_FILE" assets/index.html > "$RUNNER_TEMP/GREENMAN_27_APK_INDEX.html"
cmp -s "$RUNNER_TEMP/GREENMAN_27_EXPECTED.html" "$RUNNER_TEMP/GREENMAN_27_APK_INDEX.html"
unzip -l "$APK_FILE" | grep -q 'greenman_launcher_art.*webp'
"$ANDROID_HOME/build-tools/35.0.0/aapt" dump badging "$APK_FILE" > "$RUNNER_TEMP/GREENMAN_27_BADGING.txt"
grep -q "package: name='com.greenman.hedgewitchery' versionCode='18'" "$RUNNER_TEMP/GREENMAN_27_BADGING.txt"
grep -q "application-label:'Greenman HedgeWitchery'" "$RUNNER_TEMP/GREENMAN_27_BADGING.txt"
sha256sum "$APK_FILE" > "$RUNNER_TEMP/GREENMAN_27_APK_SHA256.txt"

cp "$APK_FILE" "$RUNNER_TEMP/GREENMAN_HEDGEWITCHERY_2.7_FINAL_CANDIDATE.apk"
echo "APK_FILE=$RUNNER_TEMP/GREENMAN_HEDGEWITCHERY_2.7_FINAL_CANDIDATE.apk" >> "$GITHUB_ENV"
