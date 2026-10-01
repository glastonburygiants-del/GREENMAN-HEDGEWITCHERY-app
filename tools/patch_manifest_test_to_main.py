#!/usr/bin/env python3
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv)!=2:
    raise SystemExit("usage: patch_manifest_test_to_main.py AndroidManifest.xml")
p=Path(sys.argv[1])
test="com.greenman.hedgewitchery.fullaccesstest"
main="com.greenman.hedgewitchery"
android="http://schemas.android.com/apk/res/android"; A="{"+android+"}"
ET.register_namespace("android",android)
tree=ET.parse(p); root=tree.getroot()
if root.get("package")!=test:
    raise SystemExit(f"unexpected proven-test package: {root.get('package')!r}")
root.set("package",main)

# The separate-test manifest patch moved app-specific authorities and permissions
# to the test package. Put those identifiers back on the normal app package.
for elem in root.iter():
    for attr in ("authorities","permission","readPermission","writePermission","taskAffinity"):
        key=A+attr; value=elem.get(key)
        if value and test in value: elem.set(key,value.replace(test,main))
    if elem.tag.split("}")[-1] in {"permission","uses-permission"}:
        key=A+"name"; value=elem.get(key)
        if value and value.startswith(test+"."): elem.set(key,main+value[len(test):])

app=root.find("application")
if app is None: raise SystemExit("application missing")
app.set(A+"label","Greenman HedgeWitchery Apothecary")

tree.write(p,encoding="utf-8",xml_declaration=True)
s=p.read_text(encoding="utf-8")
if f'package="{main}"' not in s: raise SystemExit("main package not restored")
if "fullaccesstest" in s: raise SystemExit("test package marker remains")
print("restored proven full-test manifest to the normal HedgeWitchery Android App package")
