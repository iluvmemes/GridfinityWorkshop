window.addEventListener('load',()=>{
 const native=window.fusionJavaScriptHandler,wait=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
 const report=()=>JSON.parse(native.handle('inspect','{}')).report;
 function set(id,v){const e=document.getElementById('gw-'+id);if(e.type==='checkbox')e.checked=v;else e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));}
 const click=s=>document.querySelector(s).click();
 async function suite(){const results=[];async function step(id,fn,invalid=false){fn();await wait();const r=report();results.push({id,pass:!r.errors.length&&(invalid?r.generationDisabled:!r.validation&&r.threePreview.ready&&!r.threePreview.error),report:r});}
 await step('drawer',()=>click('[data-mode="fit"]'));
 await step('padding-anchor',()=>click('[data-anchor="0"]'));
 await step('grid-1x1',()=>{click('[data-mode="grid"]');set('columns',1);set('rows',1);});
 await step('press-fit',()=>set('press-fit',true));
 await step('depth',()=>set('magnet-depth',3));
 await step('screws',()=>set('screws',true));
 await step('solid',()=>click('[data-style="solid"]'));
 await step('grid-6x6',()=>{set('columns',6);set('rows',6);});
 await step('pieces',()=>click('[data-view="pieces"]'));
 await step('2d',()=>click('#gw-view-mode'));
 await step('3d',()=>click('#gw-view-mode'));
 await step('invalid-grid',()=>set('columns',61),true);
 await step('recover-grid',()=>set('columns',6));
 await step('invalid-bed',()=>set('bed-width',20),true);
 await step('recover-bed',()=>set('bed-width',220));
 adsk.fusionSendData('response',JSON.stringify({qa:{kind:'baseplate-ui',results}}));}
 window.fusionJavaScriptHandler={handle(action,data){if(action==='qaSuite'){suite().catch(e=>adsk.fusionSendData('response',JSON.stringify({qa:{error:String(e)}})));return JSON.stringify({queued:true});}if(action==='qaCreate'){click('[data-mode="grid"]');set('columns',1);set('rows',1);set('bed-width',220);click('[data-style="skeleton"]');set('press-fit',true);setTimeout(()=>click('#gw-create'),0);return JSON.stringify({queued:true});}return native.handle(action,data);}};
});
