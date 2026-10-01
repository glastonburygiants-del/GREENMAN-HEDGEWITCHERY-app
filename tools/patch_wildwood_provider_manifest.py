#!/usr/bin/env python3
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv)!=2:
    raise SystemExit("usage: patch_wildwood_provider_manifest.py AndroidManifest.xml")
p=Path(sys.argv[1])
android="http://schemas.android.com/apk/res/android"; A="{"+android+"}"
ET.register_namespace("android",android)
tree=ET.parse(p); root=tree.getroot()
if root.get("package")!="com.greenman.hedgewitchery":
    raise SystemExit("Wildwood provider must be added to the normal HedgeWitchery Android App package")

perm="com.greenman.hedgewitchery.permission.WILDWOOD_STOCK_BRIDGE"
authority="com.greenman.hedgewitchery.stockbridge"

if not any(x.tag.split("}")[-1]=="permission" and x.get(A+"name")==perm for x in root):
    el=ET.Element("permission")
    el.set(A+"name",perm)
    el.set(A+"protectionLevel","signature")
    root.insert(0,el)

app=root.find("application")
if app is None: raise SystemExit("application element missing")
providers=[x for x in app if x.tag.split("}")[-1]=="provider" and x.get(A+"authorities")==authority]
if len(providers)>1: raise SystemExit("duplicate Wildwood provider")
if not providers:
    el=ET.Element("provider")
    el.set(A+"name","com.greenman.hedgewitchery.WildwoodStockProvider")
    el.set(A+"authorities",authority)
    el.set(A+"exported","true")
    el.set(A+"readPermission",perm)
    el.set(A+"writePermission",perm)
    app.append(el)

tree.write(p,encoding="utf-8",xml_declaration=True)
s=p.read_text(encoding="utf-8")
for marker in (perm,authority,"WildwoodStockProvider",'android:protectionLevel="signature"'):
    if marker not in s: raise SystemExit("missing provider marker: "+marker)
print("added signature-protected Wildwood stock provider")
