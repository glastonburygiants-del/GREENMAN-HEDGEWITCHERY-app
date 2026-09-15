#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, re, subprocess, sys, tarfile, tempfile, zipfile
from pathlib import Path

# Exact current tablet-tested package baseline:
# GREENMAN_HEDGEWITCHERY_PAGE2_297MM_PRINT_COPY_FIXED_TEST.apk
DONOR_INDEX_SHA='abf9cb3b472b1b6792d640377a1e9c7963176c32365b44970c094fe98608dd9d'
CURRENT_INDEX_SHA='3d5870c9cd72589dada7a2092014076443cd4184d82b79de9c5ba815f6c72ce1'
FINAL_INDEX_SHA='d73707cc257c323e546b054dc5601a443dee649cf5d8d579d2b29b23a464bc64'
INSTRUCTION_GIT_COMMIT='ec05f17e4084df3585490991a605e613eb678873'
PAYLOAD_SHA={
 'native_zst':'3ce16f54616035d07deac05e6071484f6ce59800135e9f2d119e3fc7b88dd42f',
 'index_delta_zst':'6c5f38a333a1d22cf06f59ac2874505a625cb719f8c0811d33fad06408ec4413',
}
EXPECTED_PAGE_SHA={
 'home':'156f4c41599b4fa87541e07f3696e5ee2ea9e00319451495481f5296a12de611',
 'admin':'2c4b57ea52ab311708738e76ba45ffee983e2e9a4bab572a43f6ffec7523a5e3',
 'spellBuilder':'50c86d90fae2d285268e8b551e288233507f53d23c484cf5b219bb085cba7d44',
 'journal':'7c890559e8f770917b19ea241ac693db02d28509af57d95f3354ab737c9c6d95',
 'bos':'d11143c41c005170f8d6b5676a72ce026743cd8cd699bc3100cee3a7b11c19b4',
 'grimoire':'000643c36a079554c933d7c1e8d9a7ecb366a1aff22fb120852dfe0a179a6612',
 'planets':'3b5828d781e7c2d3921b1a008b0d8071236307422dd0a492a35605b83630200b',
 'planetTiming':'c045e30e59e395c6b2de49f93f10b1c7368fe18d6094c6eef98734674ca2dfa9',
 'moon':'467ac4798e99f3bde8a177003a558c5e146eaecd16b432ab724cedcd204c596b',
 'numerology':'2dae1ee534f588e4629ed5dfa9db0b1065dbb66f92a60d74e41c1d8cae3611b8',
}
EXPECTED_FILES={
 'AndroidManifest.xml':'bef31f278809f3775dacfc4a1ca424c26e850db812b24e7e2c5ab7d152455967',
 'META-INF/com/android/build/gradle/app-metadata.properties':'7dcf130d4874270e450dec50649304c0f56f8c866e2bd002530aa66413d88c2d',
 'assets/fonts/Cinzel.ttf':'f4d83d34d1f6c741193e4acf4b3dff9531e5a67b6aa65228d00a7db72a4e0f34',
 'assets/fonts/CrimsonText-Bold.ttf':'a3a0765fc5e8d0b49b540a23aefe0184887dd79f06a0bdf4db7035cea6befa93',
 'assets/fonts/CrimsonText-BoldItalic.ttf':'467013e913e46304760461c46661c994b2aa1769e3fbd31371026300315181b4',
 'assets/fonts/CrimsonText-Italic.ttf':'4ed1699ac7c64e8b3d33f6bb8323c3d7206b0d7bacb9ee2d65c697e6014d29de',
 'assets/fonts/CrimsonText-Regular.ttf':'48e6c5d5ad1d01599d374ecb817e15890d1feb3b8a3a88e527d44c90389e1f06',
 'assets/fonts/CrimsonText-SemiBold.ttf':'802e84000740fec2a9fbe0ae09b6b6811bd86a78a0173b15d44450a1530e9410',
 'assets/fonts/CrimsonText-SemiBoldItalic.ttf':'8f4a0db2d181ba4493a4ad53042edc3b57ab50fedd8fa32c7b2ad57173208543',
 'assets/fonts/IMFellEnglish-Italic.ttf':'47cd75dce54b1f2e0831359d22d5e688f519d68ae45706b664fd310fd0e3ccf7',
 'assets/fonts/IMFellEnglish-Regular.ttf':'fe9705bbde51af802719246d4608d08d37bde956ab99d9a590da996a5221a24c',
 'assets/fonts/licenses/cinzel-OFL.txt':'f2b3029aba64c378bf0963b62945eee15e564fe4330b934c8f2eb058282b5e83',
 'assets/fonts/licenses/crimsontext-OFL.txt':'50fd67cddc097377a5c871e8452b778bc5aedfa3480a705cb27c5e3a078218df',
 'assets/fonts/licenses/imfellenglish-OFL.txt':'2a3ca501fc4d5efcad9798531e3e06962b1e20c60e464f6cbd6c17630112c773',
 'assets/index.html':FINAL_INDEX_SHA,
 'classes.dex':'704d95b77cbbff847bef9378c1a9626cd3020609742ac9f7e078f57f59e2a5eb',
 'classes2.dex':'970f30180df74964f2c01c8efa75db0ba1eaee6e480fd41a970ade8a29799149',
 'res/drawable/ic_launcher_foreground.xml':'794a77a8d5f42eb0c3769ec596eb2755f6ee3d5ee0438880d5540af66c559620',
 'res/drawable-nodpi-v4/greenman_launcher_art.webp':'0915a0ddfee14a7bbba4b998128b4da04d5aa139b0bcbcc81cba0253e8090dc1',
 'res/mipmap-anydpi-v26/ic_launcher.xml':'7a1eef1cf5d79a350ecfbf4e76c8011e71d497562ba88b0ebc69a25452a3dc09',
 'res/mipmap-anydpi-v26/ic_launcher_round.xml':'7a1eef1cf5d79a350ecfbf4e76c8011e71d497562ba88b0ebc69a25452a3dc09',
 'resources.arsc':'543897bbd285ecbbd4ae3f2dd6a3dc1a069cdde8ed458e6964767624bb7f365a',
}
STORED={'classes.dex','classes2.dex','resources.arsc','res/drawable-nodpi-v4/greenman_launcher_art.webp'}

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return sha_bytes(p.read_bytes())

def decode_parts(payload:Path, stem:str, out:Path)->None:
    parts=sorted(payload.glob(f'{stem}.part*.b85'))
    if not parts: raise SystemExit('missing payload '+stem)
    raw=base64.b85decode(''.join(p.read_text().strip() for p in parts))
    if sha_bytes(raw)!=PAYLOAD_SHA[stem]: raise SystemExit(stem+' payload hash mismatch')
    out.write_bytes(raw)

def safe_extract(tar_path:Path,dest:Path)->None:
    with tarfile.open(tar_path,'r') as tf:
        root=dest.resolve()
        for m in tf.getmembers():
            target=(dest/m.name).resolve()
            if target!=root and root not in target.parents: raise SystemExit('unsafe tar path')
        tf.extractall(dest)

def patch_instruction_pages(index:Path)->None:
    if sha_file(index)!=CURRENT_INDEX_SHA: raise SystemExit('current baseline index hash mismatch')
    text=index.read_text('utf-8'); marker='const PAGES = '; start=text.index(marker)+len(marker)
    pages,used=json.JSONDecoder().raw_decode(text[start:]); end=start+used
    # Exact four-line surgery from Git commit ec05f17... only.
    anchor="""    if(activeOnly!=null&&i!==activeOnly)return;\n    var cls='gm-flat-'+(++GM_FLAT_SEQ);"""
    replacement="""    if(activeOnly!=null&&i!==activeOnly)return;\n    if(i===3||i===4){\n      container.appendChild(makeBosSnapshotPage(e,pg,false));\n      return;\n    }\n    var cls='gm-flat-'+(++GM_FLAT_SEQ);"""
    for key in ('journal','bos'):
        if pages[key].count(anchor)!=1: raise SystemExit(key+': exact Git surgery anchor mismatch')
        pages[key]=pages[key].replace(anchor,replacement,1)
    enc=json.dumps(pages,ensure_ascii=False,separators=(',',':'))
    enc=re.sub(r'</script',r'<\\/script',enc,flags=re.I)
    index.write_text(text[:start]+enc+text[end:],'utf-8')
    if sha_file(index)!=FINAL_INDEX_SHA: raise SystemExit('instruction-only final index hash mismatch')
    final=index.read_text('utf-8'); s=final.index(marker)+len(marker); fp,_=json.JSONDecoder().raw_decode(final[s:])
    got={k:sha_bytes(v.encode()) for k,v in fp.items()}
    if got!=EXPECTED_PAGE_SHA: raise SystemExit('page-level hash audit failed')

def assemble(root:Path,out:Path)->None:
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    if actual!=set(EXPECTED_FILES): raise SystemExit(f'package file-set mismatch extra={sorted(actual-set(EXPECTED_FILES))} missing={sorted(set(EXPECTED_FILES)-actual)}')
    bad=[]
    for rel,want in EXPECTED_FILES.items():
        got=sha_file(root/rel)
        if got!=want: bad.append((rel,want,got))
    if bad: raise SystemExit('package byte audit failed: '+repr(bad))
    with zipfile.ZipFile(out,'w') as z:
        for rel in sorted(EXPECTED_FILES):
            p=root/rel; zi=zipfile.ZipInfo(rel); zi.date_time=(1981,1,1,0,0,0); zi.external_attr=0o100644<<16
            typ=zipfile.ZIP_STORED if rel in STORED else zipfile.ZIP_DEFLATED
            z.writestr(zi,p.read_bytes(),compress_type=typ,compresslevel=9 if typ==zipfile.ZIP_DEFLATED else None)

def main():
    if len(sys.argv)!=5: raise SystemExit('usage: reconstruct_exact_current_apk.py DONOR_INDEX.html PAYLOAD_DIR FONT_ROOT OUT_UNSIGNED.apk')
    donor=Path(sys.argv[1]); payload=Path(sys.argv[2]); fonts=Path(sys.argv[3]); out=Path(sys.argv[4])
    if sha_file(donor)!=DONOR_INDEX_SHA: raise SystemExit('GitHub donor index hash mismatch')
    with tempfile.TemporaryDirectory(prefix='gm-exact-') as td0:
        td=Path(td0); root=td/'apk'; root.mkdir(); (root/'assets').mkdir()
        delta=td/'delta.zst'; decode_parts(payload,'index_delta_zst',delta)
        current=root/'assets/index.html'
        subprocess.run(['zstd','-q','-f','-d',f'--patch-from={donor}',str(delta),'-o',str(current)],check=True)
        if sha_file(current)!=CURRENT_INDEX_SHA: raise SystemExit('delta did not reconstruct exact current app index')
        native_zst=td/'native.tar.zst'; native_tar=td/'native.tar'; decode_parts(payload,'native_zst',native_zst)
        subprocess.run(['zstd','-q','-d',str(native_zst),'-o',str(native_tar)],check=True); safe_extract(native_tar,root)
        # Exact current font tree, fetched and hash-checked by the GitHub workflow.
        for p in fonts.rglob('*'):
            if p.is_file():
                dest=root/'assets/fonts'/p.relative_to(fonts); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(p.read_bytes())
        meta=root/'META-INF/com/android/build/gradle/app-metadata.properties'; meta.parent.mkdir(parents=True,exist_ok=True)
        meta.write_text('appMetadataVersion=1.1\nandroidGradlePluginVersion=8.7.3\n','utf-8')
        patch_instruction_pages(current)
        assemble(root,out)
    print('EXACT CURRENT PACKAGE RECONSTRUCTED')
    print('tablet-tested baseline index:',CURRENT_INDEX_SHA)
    print('instruction-only final index:',FINAL_INDEX_SHA)
    print('Git instruction source:',INSTRUCTION_GIT_COMMIT)
    print('Home/gate/grimoire/native package protected by exact hashes')

if __name__=='__main__': main()
