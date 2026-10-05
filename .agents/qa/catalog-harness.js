// QA-only bridge wrapper, loaded only by the harness HTML under .agents.
window.addEventListener('load',()=>{
 const native=window.fusionJavaScriptHandler;const receipts=[];
 const send=result=>adsk.fusionSendData('response',JSON.stringify({qa:result}));
 const wait=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
 function set(id,value){const e=document.getElementById(id);if(!e)throw Error('Missing control '+id);if(e.type==='checkbox')e.checked=value;else e.value=value;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));}
 function click(selector){const e=document.querySelector(selector);if(!e)throw Error('Missing button '+selector);e.click();}
 async function suite(){const results=[],original=JSON.parse(JSON.stringify(state));
  async function record(id,action,expected=true){try{action();await wait();const r=JSON.parse(JSON.stringify(report()));const p=r.threePreview;const pass=!r.errors.length&&!r.overflow&&r.selectorArt.every(a=>a.loaded)&&(expected?!!p?.ready&&!p.error&&(state.view==='layout'||p.family===state.family):!r.generationEnabled);results.push({id,pass,report:r});}catch(e){results.push({id,pass:false,error:String(e)});}}
  for(const family of Object.keys(families))await record('family-'+family,()=>{click('[data-family="'+family+'"]');click('[data-view="3d"]');});
  click('[data-family="standard"]');
  for(const [id,changes] of [['small',{cols:1,rows:1,height:2}],['large',{cols:6,rows:6,height:20}],['divided',{cols:2,rows:2,height:6,interior:'divided',divX:3,divY:2}],['scoop',{scoop:true}],['label',{label:true}],['lid',{scoop:false,label:false,dovetailLid:true}],['channels',{dovetailLid:false,interior:'magnets',channelColumns:4,channelRows:3}],['square',{channelShape:'square'}],['rectangle',{channelShape:'rectangle'}],['spacing',{channelGapX:3}],['press-fit',{magnet:'press'}]])await record(id,()=>Object.entries(changes).forEach(([k,v])=>set(k,v)));
  await record('invalid-channels',()=>set('channelColumns',48),false);
  await record('recover-channels',()=>set('channelColumns',4));
  await record('parts',()=>click('[data-view="parts"]'));
  await record('layout',()=>click('[data-view="layout"]'));
  await record('return-3d',()=>click('[data-view="3d"]'));
  click('[data-family="magazine"]');
  await record('magazine-rotated',()=>{set('cols',1);set('rows',2);set('orientation','90');});
  await record('magazine-cutouts',()=>set('magazineCutouts',true));
  await record('magazine-overcapacity',()=>set('quantity',48),false);
  await record('magazine-recovery',()=>set('quantity',2));
  click('[data-family="tests"]');for(const type of ['pin','magnet','spacing','envelope','closure'])await record('test-'+type,()=>set('testType',type));
  // Save/load through the real controls, then restore the user's storage verbatim.
  const key='gridfinity-bin-favorites-v1',saved=localStorage.getItem(key);
  await record('favorite-roundtrip',()=>{set('title','QA temporary favorite');click('#save');set('height',7);click('#load');if(state.configs[state.family].height===7)throw Error('Favorite did not restore height');});
  if(saved===null)localStorage.removeItem(key);else localStorage.setItem(key,saved);
  native.handle('setCatalogState',JSON.stringify(original));await wait();send({kind:'ui-suite',results});
 }
 window.fusionJavaScriptHandler={handle(action,data){if(action==='creationStatus'){receipts.push(JSON.parse(data));if(receipts.length>20)receipts.shift();}if(action==='qaReceipt')return JSON.stringify({qa:{kind:'receipt',receipts,report:report()}});if(action==='qaPing')return JSON.stringify({qa:{kind:'ready',url:location.href,handler:'catalog-harness-v6',state:report().state}});if(action==='qaSuite'){suite().catch(e=>send({error:String(e)}));return JSON.stringify({queued:true});}if(action==='qaCreate'){const p=JSON.parse(data);const restored=JSON.parse(native.handle('setCatalogState',JSON.stringify(p)));if(!restored.ok)return JSON.stringify({qa:{kind:'restore-failed'}});setTimeout(()=>click('#create-bin'),50);return JSON.stringify({qa:{kind:'create-dispatched',disabled:document.querySelector('#create-bin').disabled,family:state.family}});}return native.handle(action,data);}};
});
