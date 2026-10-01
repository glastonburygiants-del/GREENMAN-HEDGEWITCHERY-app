#!/usr/bin/env python3
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv)!=2:
    raise SystemExit("usage: patch_stocktake_manifest_safe.py AndroidManifest.xml")
p=Path(sys.argv[1])
old="com.greenman.hedgewitchery"
new="com.greenman.hedgewitchery.stocktake"
android="http://schemas.android.com/apk/res/android"; A="{"+android+"}"
ET.register_namespace("android",android)
tree=ET.parse(p); root=tree.getroot()
if root.get("package")!=old:
    raise SystemExit(f"unexpected normal base package: {root.get('package')!r}")

component_tags={"application","activity","activity-alias","service","receiver","provider"}
for elem in root.iter():
    if elem.tag.split("}")[-1] in component_tags:
        name=elem.get(A+"name")
        if name:
            if name.startswith("."): elem.set(A+"name",old+name)
            elif "." not in name: elem.set(A+"name",old+"."+name)

root.set("package",new)

for elem in root.iter():
    for attr in ("authorities","permission","readPermission","writePermission","taskAffinity"):
        key=A+attr; value=elem.get(key)
        if value and old in value: elem.set(key,value.replace(old,new))

if not any(x.tag.split("}")[-1]=="uses-permission" and x.get(A+"name")=="android.permission.INTERNET" for x in root):
    el=ET.Element("uses-permission");el.set(A+"name","android.permission.INTERNET");root.insert(0,el)

app=root.find("application")
if app is None: raise SystemExit("application missing")
app.set(A+"label","Greenman HedgeWitchery Apothecary Stocktake")

tree.write(p,encoding="utf-8",xml_declaration=True)
s=p.read_text(encoding="utf-8")
for marker in (f'package="{new}"',"android.permission.INTERNET","Greenman HedgeWitchery Apothecary Stocktake"):
    if marker not in s: raise SystemExit("missing safe Stocktake marker: "+marker)
for forbidden in ("WILDWOOD_STOCK_BRIDGE","com.greenman.hedgewitchery.stockbridge","WildwoodStockProvider"):
    if forbidden in s: raise SystemExit("native bridge marker must not be present: "+forbidden)
print("configured standalone Stocktake without native inter-app bridge")
