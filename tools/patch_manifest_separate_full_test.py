#!/usr/bin/env python3
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_manifest_separate_full_test.py AndroidManifest.xml")

path = Path(sys.argv[1])
old = "com.greenman.hedgewitchery"
new = "com.greenman.hedgewitchery.apothecary"
android = "http://schemas.android.com/apk/res/android"
A = "{" + android + "}"

ET.register_namespace("android", android)
tree = ET.parse(path)
root = tree.getroot()

if root.get("package") != old:
    raise SystemExit(f"unexpected manifest package: {root.get('package')!r}")

# Keep every native Java/Smali class in its original package. Relative
# component names would otherwise resolve against the new test package.
component_tags = {"application", "activity", "activity-alias", "service", "receiver", "provider"}
for elem in root.iter():
    if elem.tag.split("}")[-1] in component_tags:
        name = elem.get(A + "name")
        if name:
            if name.startswith("."):
                elem.set(A + "name", old + name)
            elif "." not in name:
                elem.set(A + "name", old + "." + name)

# Give Android a genuinely separate install identity.
root.set("package", new)

# Authorities and app-specific permission names must not collide with the
# installed production app.
for elem in root.iter():
    for attr in ("authorities", "permission", "readPermission", "writePermission", "taskAffinity"):
        key = A + attr
        value = elem.get(key)
        if value and old in value:
            elem.set(key, value.replace(old, new))

# Custom permission declarations/usages can also carry the package prefix.
for elem in root.iter():
    tag = elem.tag.split("}")[-1]
    if tag in {"permission", "uses-permission"}:
        key = A + "name"
        value = elem.get(key)
        if value and value.startswith(old + "."):
            elem.set(key, new + value[len(old):])

app = root.find("application")
if app is None:
    raise SystemExit("application element missing")
app.set(A + "label", "Greenman HedgeWitchery Apothecary CLEAN")

tree.write(path, encoding="utf-8", xml_declaration=True)

# Post-write guards.
text = path.read_text(encoding="utf-8")
if f'package="{new}"' not in text:
    raise SystemExit("new package was not written")
if "ScribePdfService" in text:
    raise SystemExit("unexpected ScribePdfService present")
if "android.permission.FOREGROUND_SERVICE" in text:
    raise SystemExit("unexpected FOREGROUND_SERVICE present")

print(f"clean full-app package: {new}")
print("native component classes remain in com.greenman.hedgewitchery")
