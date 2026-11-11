window.addEventListener('load',()=>{
 const native=window.fusionJavaScriptHandler;
 window.fusionJavaScriptHandler={handle(action,data){
  if(action==='qaFullVisual'){
   const original=JSON.parse(native.handle('inspect','{}')).report.state;
   (async()=>{
    const results=[];
    for(const c of qaVisualCases){
     const row=await qaVisualRun(c.id);
     if(c.id.endsWith('-default'))row.image=window.catalogThree?.capture();
     results.push(row);
    }
    native.handle('setCatalogState',JSON.stringify(original));
    adsk.fusionSendData('response',JSON.stringify({qa:{kind:'full-visual',viewport:[innerWidth,innerHeight],results}}));
   })().catch(e=>adsk.fusionSendData('response',JSON.stringify({qa:{error:String(e)}})));
   return JSON.stringify({queued:true});
  }
  return native.handle(action,data);
 }};
});
