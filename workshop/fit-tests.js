'use strict';
const fitDefaults={channelGapX:1,channelGapY:1,channelGapLinked:true,pinDiameter:1.75,pinAllowance:.25,pinOverrides:false,
 bodyPinAllowance:.25,lidPinAllowance:.25,lidLatchAllowance:.25,bucklePinAllowance:.25,
 testType:'pin',testSource:'clasp',testStart:.15,testStep:.05,testCount:5,testSelected:1,testPinTarget:'all',testAxis:'both',testStackDepth:28,testPosts:false};
const pinKeys=['bodyPinAllowance','lidPinAllowance','lidLatchAllowance','bucklePinAllowance'];
const fitKeys=[...Object.keys(fitDefaults).filter(k=>!k.startsWith('test')),'buckle','grip','magnet','diameter','magnetDepth','storedClearance'];
function upgradeFit(old){
 const c={...fitDefaults,...old};
 if(old.pinDiameter===undefined&&old.pin!==undefined){c.pinDiameter=1.75;c.pinAllowance=old.pin-1.75;c.pinOverrides=true;
  c.bodyPinAllowance=c.lidPinAllowance=old.pin-1.75;c.lidLatchAllowance=c.bucklePinAllowance=old.pin+.2-1.75;}
 return c;
}
function pinBores(c){return pinKeys.map(k=>c.pinDiameter+(c.pinOverrides?c[k]:c.pinAllowance));}
function testPlan(c){
 const kind=c.testType,samples=[],errors=[];
 const fail=t=>errors.push(t);
 if(!['pin','closure','magnet','spacing','envelope'].includes(kind))fail('Choose a fit test.');
 if(['pin','closure'].includes(kind)&&c.testSource!=='clasp')fail('Pin and closure tests apply to the Clasp bin recipe.');
 if(kind==='closure')samples.push({label:'Working closure',w:83.5,d:41.5,h:28.7});
 else if(kind==='envelope')samples.push({label:`${c.cols*42-.5} x ${c.rows*42-.5}`,w:c.cols*42-.5,d:c.rows*42-.5,h:c.testPosts?c.height*7+(c.testSource==='clasp'?3.7:(c.rim?3.8:0)+(c.testSource==='standard'&&c.dovetailLid?5.6:0)):3});
 else{
  if(!Number.isFinite(c.testStart))fail('Enter a finite starting value.');
  if(!Number.isInteger(c.testCount)||c.testCount<1||c.testCount>7||!Number.isFinite(c.testStep)||c.testStep<.01||c.testStep>10)fail('Use 1-7 samples and a step from 0.01 to 10 mm.');
  for(let i=0;i<Math.min(Math.max(0,c.testCount),7);i++){
   const value=Number((c.testStart+i*c.testStep).toFixed(6));
   if(kind==='pin'){
    const bore=c.pinDiameter+value;
    if(value<0||value>1||bore<1.8-1e-8||bore>2.7+1e-8)fail('Test bores must be 1.80 to 2.70 mm.');
    samples.push({value,bore,label:bore.toFixed(2),w:14,d:10,h:8});
   }else if(kind==='magnet'){
    if(value<3||value>8)fail('Magnet test diameters must be 3 to 8 mm.');
    samples.push({value,bore:value,label:value.toFixed(2),w:14,d:19,h:c.magnetDepth+2});
   }else if(kind==='spacing'){
    const gx=['both','x'].includes(c.testAxis)?value:c.channelGapX,gy=['both','y'].includes(c.testAxis)?value:c.channelGapLinked?c.channelGapX:c.channelGapY;
    const cw=(c.channelShape==='round'?c.storedDiameter:c.channelWidth)+c.storedClearance,cd=(c.channelShape==='rectangle'?c.channelDepth:c.channelShape==='square'?c.channelWidth:c.storedDiameter)+c.storedClearance;
    if([gx,gy].some(v=>!Number.isFinite(v)||v<1||v>30))fail('Channel separations must be 1 to 30 mm.');
    if(![c.channelColumns,c.channelRows].every(n=>Number.isInteger(n)&&n>=2&&n<=5))fail('Spacing tests use 2-5 channels in each direction.');
    samples.push({value,gapX:gx,gapY:gy,cw,cd,label:`${gx}x${gy}`,w:4+c.channelColumns*cw+(c.channelColumns-1)*gx,d:10+c.channelRows*cd+(c.channelRows-1)*gy,h:c.testStackDepth+2});
   }
  }
 }
 let x=0,y=0,row=0;
 for(const q of samples){if(![q.w,q.d,q.h].every(Number.isFinite)||q.w>251.5||q.d>251.5)fail('A sample exceeds the 6x6 print area.');if(x+q.w>251.5){x=0;y+=row+8;row=0;}if(y+q.d>251.5)fail('The sample set exceeds a 6x6 print area; reduce count.');q.x=x;q.y=y;x+=q.w+8;row=Math.max(row,q.d);}
 return {samples,errors:[...new Set(errors)],valid:!errors.length};
}
function fitVisibility(c){
 const tests=state.family==='tests',kind=c.testType,closure=['clasp','cartridge'].includes(state.family)||(tests&&kind==='closure');
 const visible={'test-fields':tests,'test-range':tests&&!['closure','envelope'].includes(kind),'test-spacing':tests&&kind==='spacing','test-posts':tests&&kind==='envelope','test-selection':tests&&kind!=='envelope','pin-fields':closure||(tests&&kind==='pin'),'pin-overrides':c.pinOverrides,'height-fields':!tests||kind==='envelope','height-note':!tests||kind==='envelope'};
 for(const [id,show] of Object.entries(visible))$('#'+id).hidden=!show;
 document.querySelector('[data-view="parts"]').hidden=tests;
 if(tests&&state.view==='parts')state.view='3d';
 $('#channelGapY').disabled=c.channelGapLinked;if(c.channelGapLinked)$('#channelGapY').value=c.channelGapX;
 $('#pin-summary').textContent=['Body','Lid hinge','Lid latch','Buckle'].map((name,i)=>`${name}: ${fmt(pinBores(c)[i])} mm`).join(' | ');
 $('#testPinTarget').parentElement.hidden=kind!=='pin';$('#testSelected').parentElement.hidden=kind==='closure';
 $('#testSelected').max=c.testCount;
 for(const option of $('#testSource').options)option.disabled=['pin','closure'].includes(kind)&&option.value!=='clasp';
 $('#test-start-label').textContent=kind==='magnet'?'Starting hole diameter':kind==='spacing'?'Starting channel separation':'Starting bore allowance';
 $('#channelColumns').min=$('#channelRows').min=tests?2:1;$('#channelColumns').max=$('#channelRows').max=tests?5:48;
 if(tests){$('#grid-fields').hidden=kind!=='envelope';$('#interior-fields').hidden=kind!=='spacing';$('#storage-fields').hidden=kind!=='spacing';$('#storage-choice').hidden=true;$('#divider-fields').hidden=true;$('#closure-fields').hidden=kind!=='closure';$('#hardware-fields').hidden=kind!=='magnet';$('#magnet-selector').hidden=true;$('#magnet-diameter').hidden=true;$('#magnet-fields').hidden=false;}
 else{$('#storage-choice').hidden=false;$('#magnet-selector').hidden=false;$('#magnet-diameter').hidden=false;}
}
function updateFitTest(){
 const c=state.configs.tests,p=testPlan(c),invalid=[...document.querySelectorAll('input[type=number]')].some(e=>e.id!=='testSelected'&&!e.closest('[hidden]')&&!e.disabled&&!e.checkValidity());
 const pinError=['pin','closure'].includes(c.testType)&&pinBores(c).some(v=>v<1.8-1e-8||v>2.7+1e-8);
 if(pinError)p.errors.push('Resulting pin bores must be 1.80 to 2.70 mm.');
 if(invalid)p.errors.push('Enter values within the field limits.');
 $('#create-bin').disabled=creating||p.errors.length>0;$('#create-bin').textContent='Create fit tests';
 if(!creating)$('#create-status').textContent='Creates test pieces in a new design.';
 $('#subtitle').textContent='Print, compare, then apply the selected settings.';
 $('#errors').textContent=[...new Set(p.errors)].join(' ');
 $('#metrics').innerHTML=`<div><small>Test pieces</small><b>${c.testType==='closure'?3:p.samples.length}</b></div><div><small>Source recipe</small><b>${escape(families[c.testSource].name)}</b></div><div><small>${c.testType==='spacing'?'Stack depth':'Sample height'}</small><b>${fmt(c.testType==='spacing'?c.testStackDepth:p.samples[0]?.h||0)} mm</b></div>`;
 $('#parts').innerHTML=p.samples.map((q,i)=>`<li>${i+1}: ${escape(q.label)} mm${c.testType==='pin'?` bore (+${fmt(q.value)} allowance)`:''}</li>`).join('');
 $('#review').textContent=c.testType==='closure'?'Actual clasp geometry at 2x1 / 6U, with the lower body removed. Print Body, Lid and Buckle separately in the same orientations as the full parts.':c.testType==='envelope'?'Thin footprint frame with optional posts at the selected closed height. No feet or storage geometry.':c.testType==='spacing'?'Edge-to-edge separation is engraved on each sample. Use the selected stack depth and test one sample at a time, away from the other loaded samples.':c.testType==='magnet'?'Diameters are engraved on top. Pockets open underneath, matching bin feet; print with the text facing up. Match material and layer height to the final bin.':'Sample bore diameters are engraved on the parts. Pin coupons use horizontal bores. Match material, layer height and print orientation to the final parts.';
 $('#apply-test').disabled=p.errors.length>0||!Number.isInteger(c.testSelected)||c.testSelected<1||c.testSelected>c.testCount;
 drawFitTest(p,c);
}
function drawFitTest(p,c){
 if(!p.valid){$('#drawing').textContent=p.errors.join(' ');return;}
 const w=Math.max(...p.samples.map(q=>q.x+q.w),1),d=Math.max(...p.samples.map(q=>q.y+q.d),1),scale=Math.min(470/w,205/d),ox=(540-w*scale)/2,oy=25;
 let s='';
 for(const [i,q] of p.samples.entries()){
  const x=ox+q.x*scale,y=oy+q.y*scale,ww=q.w*scale,dd=(c.testType==='pin'?q.h:q.d)*scale;s+=rect(x,y,ww,dd,'#c2d6e2',2);
  if(c.testType==='envelope')s+=rect(x+3*scale,y+3*scale,ww-6*scale,dd-6*scale,'#f3f6f8',0);
  if(c.testType==='pin'||c.testType==='magnet')s+=`<circle cx="${x+ww/2}" cy="${y+(c.testType==='pin'?dd/2:7*scale)}" r="${q.bore*scale/2}" fill="#658a9f"/>`;
  if(c.testType==='spacing')for(let row=0;row<c.channelRows;row++)for(let col=0;col<c.channelColumns;col++){
   const px=x+(2+col*(q.cw+q.gapX))*scale,py=y+(2+row*(q.cd+q.gapY))*scale;
   s+=c.channelShape==='round'?`<circle cx="${px+q.cw*scale/2}" cy="${py+q.cd*scale/2}" r="${q.cw*scale/2}" fill="#658a9f"/>`:rect(px,py,q.cw*scale,q.cd*scale,'#658a9f',0);
  }
  if(c.testType==='closure')s+=rect(x+ww*.12,y+dd*.12,ww*.76,dd*.76,'#f3f6f8',0)+rect(x+ww*.82,y+dd*.3,ww*.15,dd*.4,'#658a9f',1);
  s+=`<text x="${x+ww/2}" y="${y+dd+15}">${i+1}: ${escape(q.label)}</text>`;
 }
 const caption=c.testType==='pin'?'Front view - horizontal pin bores':c.testType==='magnet'?'Underside view - magnet pockets':'Layout illustration';
 $('#drawing').innerHTML=`<svg viewBox="0 0 540 290" role="img" aria-label="Fit test layout"><g font-family="Segoe UI,Arial" font-size="11" text-anchor="middle" fill="#39596d">${s}<text x="270" y="280">${caption} - dimensions in mm</text></g></svg>`;
}
function copyTestSource(){const c=state.configs.tests,src=state.configs[c.testSource];for(const key of Object.keys(src))if(!key.startsWith('test')&&key!=='title')c[key]=src[key];c.channelColumns=Math.min(3,Math.max(2,c.channelColumns));c.channelRows=Math.min(3,Math.max(2,c.channelRows));populate();}
function changeTestType(){const c=state.configs.tests;const values={pin:[.15,.05,5],magnet:[5.98,.05,5],spacing:[1,1,3]};if(values[c.testType])[c.testStart,c.testStep,c.testCount]=values[c.testType];if(['pin','closure'].includes(c.testType))c.testSource='clasp';c.testSelected=1;populate();}
function applyTest(){
 const c=state.configs.tests,p=testPlan(c),q=p.samples[c.testSelected-1],target=state.configs[c.testSource];if(!p.valid||(!q&&c.testType!=='closure'))return;
 if(c.testType==='pin'){
  target.pinDiameter=c.pinDiameter;
  if(c.testPinTarget==='all'){target.pinAllowance=q.value;target.pinOverrides=false;}
  else{if(!target.pinOverrides)for(const key of pinKeys)target[key]=target.pinAllowance;target.pinOverrides=true;target[c.testPinTarget]=q.value;}
 }else if(c.testType==='magnet'){target.magnet='custom';target.diameter=q.value;target.magnetDepth=c.magnetDepth;}
 else if(c.testType==='spacing'){target.channelGapLinked=c.testAxis==='both';target.channelGapX=q.gapX;target.channelGapY=q.gapY;}
 else if(c.testType==='closure')for(const key of ['pinDiameter','pinAllowance','pinOverrides',...pinKeys,'buckle','grip'])target[key]=c[key];
 for(const key of fitKeys)c[key]=target[key];
 populate();
 $('#test-apply-status').textContent=`Applied to ${families[c.testSource].name}. Existing Fusion designs are unchanged.`;
}
let fitProfiles={};
function profileOptions(){const select=$('#fit-profiles');select.innerHTML='<option value="">Choose a fit profile</option>'+Object.keys(fitProfiles).map(k=>`<option value="${escape(k)}">${escape(k)}</option>`).join('');}
function initFitProfiles(){try{const p=JSON.parse(localStorage.getItem('gridfinity-fit-profiles-v1')||'{}');if(p&&typeof p==='object'&&!Array.isArray(p))fitProfiles=p;}catch{}profileOptions();}
function fitProfileAction(save){
 const c=state.configs[state.family];
 if(save){const name=$('#fit-profile-name').value.trim();if(!name){$('#fit-profile-status').textContent='Give the printer/material profile a name.';return;}
  const next={...fitProfiles,[name]:Object.fromEntries(fitKeys.map(k=>[k,c[k]]))};try{localStorage.setItem('gridfinity-fit-profiles-v1',JSON.stringify(next));fitProfiles=next;profileOptions();$('#fit-profiles').value=name;$('#fit-profile-status').textContent='Fit profile saved.';}catch{$('#fit-profile-status').textContent='Local storage unavailable; profile was not saved.';}
 }else{const p=fitProfiles[$('#fit-profiles').value];if(!p||fitKeys.some(k=>typeof p[k]!==typeof c[k]||(typeof p[k]==='number'&&!Number.isFinite(p[k])))){$('#fit-profile-status').textContent='Choose a valid fit profile.';return;}for(const k of fitKeys)c[k]=p[k];populate();$('#fit-profile-status').textContent='Fit profile applied to this recipe.';}
}
if(typeof module!=='undefined')module.exports={fitDefaults,upgradeFit,pinBores,testPlan};
