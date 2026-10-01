#!/usr/bin/env python3
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv)!=2:
    raise SystemExit("usage: patch_stocktake_manifest.py AndroidManifest.xml")
p=Path(sys.argv[1])
old="com.greenman.hedgewitchery"
new="com.greenman.hedgewitchery.stocktake"
bridge="com.greenman.hedgewitchery.permission.WILDWOOD_STOCK_BRIDGE"
android="http://schemas.android.com/apk/res/android"; A="{"+android+"}"
ET.register_namespace("android",android)
tree=ET.parse(p); root=tree.getroot()
if root.get("package")!=old: raise SystemExit("unexpected base package")

component_tags={"application","activity","activity-alias","service","receiver","provider"}
for elem in root.iter():
    if elem.tag.split("}")[-1] in component_tags:
        name=elem.get(A+"name")
        if name:
            if name.startswith("."): elem.set(A+"name",old+name)
            elif "." not in name: elem.set(A+"name",old+"."+name)

root.set("package",new)
# Existing app-specific authorities from the base APK must not collide.
for elem in root.iter():
    for attr in ("authorities","permission","readPermission","writePermission","taskAffinity"):
        key=A+attr; value=elem.get(key)
        if value and old in value: elem.set(key,value.replace(old,new))

def ensure_use(name):
    if not any(x.tag.split("}")[-1]=="uses-permission" and x.get(A+"name")==name for x in root):
        el=ET.Element("uses-permission");el.set(A+"name",name);root.insert(0,el)

ensure_use("android.permission.INTERNET")
# Intentionally request the NORMAL app's signature permission, not the stocktake package version.
ensure_use(bridge)

# Android 11+ package visibility: explicitly declare the provider authority the Stocktake talks to.
queries=root.find("queries")
if queries is None:
    queries=ET.Element("queries")
    # queries belongs before application.
    app_pos=list(root).index(root.find("application")) if root.find("application") is not None else len(list(root))
    root.insert(app_pos,queries)
if not any(x.tag.split("}")[-1]=="provider" and x.get(A+"authorities")=="com.greenman.hedgewitchery.stockbridge" for x in queries):
    q=ET.Element("provider")
    q.set(A+"authorities","com.greenman.hedgewitchery.stockbridge")
    queries.append(q)

app=root.find("application")
if app is None: raise SystemExit("application missing")
app.set(A+"label","Greenman HedgeWitchery Apothecary Stocktake")

tree.write(p,encoding="utf-8",xml_declaration=True)
s=p.read_text(encoding="utf-8")
for marker in (f'package="{new}"',bridge,"android.permission.INTERNET","com.greenman.hedgewitchery.stockbridge","Greenman HedgeWitchery Apothecary Stocktake"):
    if marker not in s: raise SystemExit("missing stocktake manifest marker: "+marker)
print("configured standalone Stocktake package and protected Wildwood bridge permission")
