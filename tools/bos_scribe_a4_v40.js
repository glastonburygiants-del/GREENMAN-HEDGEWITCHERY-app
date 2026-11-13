/* V40: A4 PDF export for the Scribe desk, using existing native Downloads bridge.
   No new permissions, network access, native code, or storage identifiers. */
function gmScribeV40ImagePdf(images, landscape){
  const encoder=new TextEncoder(),parts=[],offsets=[0];
  let length=0;
  const put=x=>{const b=typeof x==='string'?encoder.encode(x):x;parts.push(b);length+=b.byteLength};
  const obj=(n,callback)=>{offsets[n]=length;put(n+' 0 obj\n');callback();put('endobj\n')};
  const W=landscape?841.89:595.28,H=landscape?595.28:841.89;
  const margin=34.02,innerW=W-2*margin,innerH=H-2*margin;
  put('%PDF-1.4\n%Greenman Scribe A4\n');
  obj(1,()=>put('<< /Type /Catalog /Pages 2 0 R >>\n'));
  obj(2,()=>put('<< /Type /Pages /Count '+images.length+' /Kids ['+images.map((_,i)=>(3+i*3)+' 0 R').join(' ')+'] >>\n'));
  images.forEach((data,i)=>{
    const page=3+i*3,imgId=page+1,streamId=page+2,comma=data.url.indexOf(',');
    if(comma<0)throw new Error('A4 page image encoding failed');
    const raw=atob(data.url.slice(comma+1)),bytes=new Uint8Array(raw.length);
    for(let j=0;j<raw.length;j++)bytes[j]=raw.charCodeAt(j);
    const drawH=Math.min(innerH,innerW*data.height/data.width),baseY=H-margin-drawH;
    obj(page,()=>put('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 '+W+' '+H+'] /Resources << /XObject << /Im0 '+imgId+' 0 R >> >> /Contents '+streamId+' 0 R >>\n'));
    obj(imgId,()=>{
      put('<< /Type /XObject /Subtype /Image /Width '+data.width+' /Height '+data.height+' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length '+bytes.length+' >>\nstream\n');
      put(bytes);put('\nendstream\n');
    });
    const draw='q\n'+innerW.toFixed(3)+' 0 0 '+drawH.toFixed(3)+' '+margin.toFixed(3)+' '+baseY.toFixed(3)+' cm\n/Im0 Do\nQ\n';
    obj(streamId,()=>{put('<< /Length '+encoder.encode(draw).length+' >>\nstream\n');put(draw);put('endstream\n')});
  });
  const start=length,count=3+images.length*3;
  put('xref\n0 '+count+'\n0000000000 65535 f \n');
  for(let i=1;i<count;i++)put(String(offsets[i]).padStart(10,'0')+' 00000 n \n');
  put('trailer\n<< /Size '+count+' /Root 1 0 R >>\nstartxref\n'+start+'\n%%EOF\n');
  return new Blob(parts,{type:'application/pdf'});
}
async function gmScribeExportA4Pdf(){
  if(window.__gmScribeV40PdfBusy)return false;
  window.__gmScribeV40PdfBusy=true;
  let host=null,css=null,cv=null;
  const notice=(t,error)=>{if(typeof gmScribeInlineNotice==='function')gmScribeInlineNotice(t,!!error)};
  try{
    const frame=document.getElementById('deskFrame'),doc=frame&&frame.contentDocument,root=doc&&doc.getElementById('printRoot');
    if(!root||typeof window.html2canvas!=='function')throw new Error('The Scribe writing desk or its print renderer is not ready');
    const landscape=root.classList.contains('verticalBTT');
    const pxW=landscape?1032:703,mmW=landscape?273:186,mmH=landscape?186:273;
    css=doc.createElement('style');
    css.id='gm-scribe-a4-capture-v40';
    css.textContent='#gmScribeA4Host{position:fixed!important;left:-12000px!important;top:0!important;z-index:-1!important;display:block!important;visibility:visible!important;pointer-events:none!important;width:'+pxW+'px!important;max-width:none!important;overflow:visible!important}#gmScribeA4Host #printRoot{position:relative!important;display:block!important;left:auto!important;top:auto!important;transform:none!important;width:'+pxW+'px!important;min-width:'+pxW+'px!important;max-width:'+pxW+'px!important;height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important;margin:0!important;box-shadow:none!important;background:#fff!important}#gmScribeA4Host .scrollViewport,#gmScribeA4Host .scrollPage{position:relative!important;width:100%!important;height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important;background:white!important;box-shadow:none!important}#gmScribeA4Host .scrollPage{padding:8px 5px!important}';
    doc.head.appendChild(css);
    host=doc.createElement('div');host.id='gmScribeA4Host';
    const copy=root.cloneNode(true);host.append(copy);doc.body.append(host);
    if(doc.fonts&&doc.fonts.ready)await doc.fonts.ready;
    notice('Preparing Scribe A4 PDF…',false);
    cv=await window.html2canvas(copy,{scale:1.6,backgroundColor:'#ffffff',useCORS:false,logging:false});
    if(!cv||!cv.width||!cv.height)throw new Error('The A4 page could not be rendered');
    const sliceH=Math.floor(cv.width*mmH/mmW),pageCount=Math.ceil(cv.height/sliceH);
    if(pageCount<1||pageCount>30)throw new Error('The Scribe book is too long for one print job (30 A4 pages maximum)');
    const shots=[];
    for(let i=0;i<pageCount;i++){
      const h=Math.min(sliceH,cv.height-i*sliceH);
      const c=doc.createElement('canvas');c.width=cv.width;c.height=h;
      const ctx=c.getContext('2d',{alpha:false});if(!ctx)throw new Error('A4 image canvas unavailable');
      ctx.fillStyle='#ffffff';ctx.fillRect(0,0,c.width,c.height);
      ctx.drawImage(cv,0,i*sliceH,cv.width,h,0,0,cv.width,h);
      shots.push({url:c.toDataURL('image/jpeg',.9),width:c.width,height:h});
      c.width=c.height=1;
    }
    cv.width=cv.height=1;cv=null;
    const pdf=gmScribeV40ImagePdf(shots,landscape),api=typeof gmBosNativeFiles==='function'?gmBosNativeFiles():null;
    const name='Greenman_Scribe_A4_'+new Date().toISOString().slice(0,10)+'.pdf';
    if(api&&typeof api.beginPdfCopy==='function'&&typeof api.appendPdfCopyChunk==='function'){
      if(!api.beginPdfCopy(name,pdf.size))throw new Error('Android Downloads could not begin saving the A4 document');
      try{
        const step=131072;
        for(let i=0;i<pdf.size;i+=step){
          const data=await gmBosBlobDataUrl(pdf.slice(i,Math.min(pdf.size,i+step)));
          if(!api.appendPdfCopyChunk(data.slice(data.indexOf(',')+1),i+step>=pdf.size))
            throw new Error('Android could not finish saving the A4 document');
        }
      }catch(e){try{api.abortPdfCopy()}catch(_e){}throw e}
      notice('Scribe A4 PDF saved to Downloads / Greenman HedgeWitchery.',false);
    }else{
      const url=URL.createObjectURL(pdf),a=document.createElement('a');
      a.href=url;a.download=name;doc.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),30000);
      notice('Scribe A4 PDF prepared for download.',false);
    }
    return true;
  }catch(e){notice('Scribe A4 PDF could not be saved: '+(e&&e.message||String(e)),true);return false}
  finally{if(cv){cv.width=cv.height=1}if(host)host.remove();if(css)css.remove();window.__gmScribeV40PdfBusy=false}
}
