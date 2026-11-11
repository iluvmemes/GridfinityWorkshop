/* QA-only cases. Loaded by the browser runner and disposable Fusion harness. */
(function () {
 const cases=[];
 const add=(id,family,changes={},extra={})=>cases.push({id,family,changes,...extra});
 for(const f of ['standard','clasp','cartridge','magazine','blank','tests']) {
  add(f+'-default',f);
  add(f+'-layout',f,{}, {view:'layout'});
  add(f+'-parts',f,{}, {view:'parts'});
 }
 add('standard-small','standard',{cols:1,rows:1,height:2});
 add('standard-large','standard',{cols:6,rows:6,height:20});
 add('standard-divided','standard',{cols:2,rows:2,interior:'divided',divX:3,divY:2});
 for(const family of ['standard','clasp','cartridge'])for(const channelShape of ['round','square','rectangle'])
  add(family+'-channels-'+channelShape,family,{interior:'magnets',channelShape,channelColumns:3,channelRows:1,channelGapX:2,channelGapY:2});
 for(const lidRetention of ['none','bump','magnet','both'])add('lid-'+lidRetention,'standard',{dovetailLid:true,lidRetention});
 add('lid-flat-3mm-clearance','standard',{dovetailLid:true,rim:false,lidRetention:'both',lidMagnetSize:'3',lidMagnetFit:'clearance'});
 for(const lidLabelMode of ['cutout','embedded','raised'])add('lid-label-'+lidLabelMode,'standard',{dovetailLid:true,lidLabelMode,lidLabelText:'Workshop',lidLabelHeight:4});
 add('lid-label-multiline','standard',{dovetailLid:true,lidLabelMode:'embedded',lidLabelText:'M3 bolts\nWashers',lidLabelLayout:'multi',lidLabelFont:'atkinson'});
 add('lid-hidden','standard',{dovetailLid:true},{showLid:false});
 for(const magnet of ['off','clearance','custom'])add('base-magnet-'+magnet,'standard',{magnet,diameter:6.3});
 add('clasp-minimum','clasp',{height:6});
 add('clasp-divided','clasp',{interior:'divided',divX:2,divY:1});
 add('clasp-pin-overrides','clasp',{pinOverrides:true,bodyPinAllowance:.2,lidPinAllowance:.15,lidLatchAllowance:.1,bucklePinAllowance:.2,buckle:.4,grip:3});
 add('clasp-hide-lid','clasp',{}, {showLid:false});
 add('cartridge-minimum','cartridge',{height:4});
 add('cartridge-wide','cartridge',{}, {cartridge:{cartLength:100,cartWidth:30}});
 add('blank-tall','blank',{height:6});
 add('blank-rim','blank',{rim:true});
 add('blank-open','blank',{height:2,interior:'open'});
 add('blank-invalid-open','blank',{height:1,interior:'open'},{invalid:true});
 add('blank-recover','blank');
 add('magazine-rotated','magazine',{cols:1,rows:2,orientation:'90'});
 add('magazine-cutouts','magazine',{magazineCutouts:true});
 add('magazine-overcapacity','magazine',{quantity:48},{invalid:true});
 add('channels-overcapacity','standard',{interior:'magnets',channelColumns:48,channelRows:48},{invalid:true});
 add('invalid-grid','standard',{cols:7},{invalid:true});
 add('invalid-pin','clasp',{pinDiameter:2.5,pinAllowance:1},{invalid:true});
 for(const testType of ['magnet','spacing','envelope','closure'])add('fit-'+testType,'tests',{testType,testStart:testType==='magnet'?6:testType==='spacing'?2:.15});
 window.qaVisualCases=cases;
 let original;
 window.qaVisualRun=async function(id){
  if(!original)original=JSON.parse(fusionJavaScriptHandler.handle('inspect','{}')).report.state;
  const c=cases.find(c=>c.id===id),s=JSON.parse(JSON.stringify(original));
  s.family=c.family;s.view=c.view||'3d';Object.assign(s.configs[c.family],c.changes);
  if(c.cartridge)Object.assign(s.cartridge,c.cartridge);
  fusionJavaScriptHandler.handle('setCatalogState',JSON.stringify(s));
  const lid=document.querySelector('#preview-lid');lid.checked=c.showLid!==false;lid.dispatchEvent(new Event('change'));
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const r=JSON.parse(fusionJavaScriptHandler.handle('inspect','{}')).report,p=r.threePreview;
  const failures=[];
  if(r.errors.length)failures.push('runtime: '+r.errors.join('; '));
  if(r.overflow)failures.push('horizontal overflow');
  if(!r.selectorArt.every(a=>a.loaded))failures.push('selector art missing');
  if(c.invalid){if(r.generationEnabled)failures.push('invalid Create enabled');}
  else if(!p?.ready||p.error||p.family!==c.family)failures.push('mesh not current: '+JSON.stringify(p));
  if(!c.invalid&&!r.generationEnabled)failures.push('valid Create disabled');
  if(innerWidth<=700&&s.view!=='layout'&&window.catalogThree?.orientation){
   const preview=window.catalogThree,box=preview.container.getBoundingClientRect(),hud=preview.orientation.el.getBoundingClientRect();
   if(preview.viewWidth>hud.left-box.left+1)failures.push('orientation HUD overlaps model viewport');
  }
  const rect=document.querySelector('footer').getBoundingClientRect();
  if(rect.bottom>innerHeight+1||rect.width<100)failures.push('footer outside viewport');
  return {id,family:c.family,view:s.view,pass:!failures.length,failures,report:r};
 };
})();
