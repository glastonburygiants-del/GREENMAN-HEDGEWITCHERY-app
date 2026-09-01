from pathlib import Path
import sys

p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')

start=s.find('function saveQuickToBos(force){')
end=s.find('function adminLog(e){',start)
if start<0 or end<0:
    raise SystemExit('Journal save function not found')

new_save=r'''function saveQuickToBos(force){\n  if(isLite()){toast('Book of Shadows saving is disabled in Lite mode');return;}\n  const list=readLS(LS_QUICK,[]); if(!list.length){toast('No spells to save');return;}\n  if(list.length>1&&!force){openSaveChoice(list.length);return;}\n\n  const entries=readLS(LS_ENTRIES,[]);\n  const admin=readLS(LS_ADMIN,[]);\n  const quickBefore=localStorage.getItem(LS_QUICK);\n  const entriesBefore=localStorage.getItem(LS_ENTRIES);\n  const adminBefore=localStorage.getItem(LS_ADMIN);\n  const nextEntries=JSON.parse(JSON.stringify(entries));\n  const nextAdmin=JSON.parse(JSON.stringify(admin));\n  const leanQuick=JSON.parse(JSON.stringify(list));\n  let savedCount=0;\n\n  const sourceId=x=>String((x&&(x.id||x.sourceId||x.gatherId))||'');\n  const permanentFor=q=>{\n    const sid=sourceId(q);\n    const savedId=String((q&&q.savedEntryId)||'');\n    return nextEntries.find(e=>(sid&&sourceId(e)===sid)||(savedId&&String(e&&e.entryId||'')===savedId))||null;\n  };\n\n  list.forEach((q,ix)=>{\n    let e=permanentFor(q);\n    if(!e){\n      e=JSON.parse(JSON.stringify(q));\n      const sid=sourceId(q)||String(q&&q.entryId||'');\n      if(sid)e.sourceId=sid;\n      e.entryId=uid('bos');\n      e.savedAt=new Date().toISOString();\n      e.saved=true;\n      nextEntries.push(e);\n      nextAdmin.push(adminLog(e));\n      savedCount++;\n    }\n    leanQuick[ix].saved=true;\n    leanQuick[ix].savedEntryId=e.entryId||e.id||'';\n    delete leanQuick[ix].bosSnapshot;\n  });\n\n  const restore=(key,raw)=>{try{if(raw===null)localStorage.removeItem(key);else localStorage.setItem(key,raw);}catch(_e){}};\n  try{\n    localStorage.setItem(LS_QUICK,JSON.stringify(leanQuick));\n    localStorage.setItem(LS_ENTRIES,JSON.stringify(nextEntries));\n    localStorage.setItem(LS_ADMIN,JSON.stringify(nextAdmin));\n  }catch(err){\n    restore(LS_ENTRIES,entriesBefore);\n    restore(LS_ADMIN,adminBefore);\n    restore(LS_QUICK,quickBefore);\n    console.error('Book of Shadows save failed',err);\n    toast('Book of Shadows save failed - storage was left unchanged');\n    return;\n  }\n\n  renderQuick(); renderBosFront();\n  toast(savedCount?savedCount+' spell saved to Book of Shadows':'Already saved');\n}\n'''

s=s[:start]+new_save+s[end:]

start=s.find('function readEntries(){')
end=s.find('function isSpell(e){',start)
if start<0 or end<0:
    raise SystemExit('Scribe entry reader not found')

new_read=r'''function readEntries(){\n const list=store('gm_journal_entries',[]);\n if(!Array.isArray(list))return [];\n const map=new Map();\n list.forEach((e,i)=>{\n   if(!e)return;\n   const id=String(e.entryId||e.id||e.savedAt||e.createdAt||('row_'+i));\n   if(!map.has(id))map.set(id,e);\n });\n return Array.from(map.values()).filter(e=>e&&e.entryType!=='scribeTranslation');\n}\n'''

s=s[:start]+new_read+s[end:]
p.write_text(s,encoding='utf-8')
