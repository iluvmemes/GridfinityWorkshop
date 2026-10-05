const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dir=__dirname+'/GridfinityUIPreview/';
const ctx={window:{},console,AbortController};vm.createContext(ctx);
for(const file of ['vendor/three-runtime.js','cell-profiles.js','workshop-three.js'])vm.runInContext(fs.readFileSync(dir+file,'utf8'),ctx);
ctx.window.planMagnetChannels=require(dir+'channel-layout.js').planMagnetChannels;
const {testPlan,fitDefaults}=require(dir+'fit-tests.js');
const {build,materials}=ctx.window.WorkshopThree,T=ctx.window.THREE,mats=materials();
const base={...fitDefaults,cols:2,rows:1,height:6,interior:'open',rim:true,magnet:'press',diameter:6.08,magnetDepth:2.4,divX:2,divY:2,scoopRadius:25,labelLength:40,labelDepth:13,cartLength:68,cartWidth:17.5,cartridgeHeight:8,quantity:2,slot:.3,orientation:'0',channelShape:'round',storedDiameter:6,storedClearance:.5,channelWidth:6,channelDepth:10,channelColumns:4,channelRows:1};
let count=0;
function check(recipe){const start=performance.now(),g=build(recipe,mats);g.updateMatrixWorld(true);const box=new T.Box3().setFromObject(g);assert.ok(!box.isEmpty());g.traverse(o=>{if(o.geometry)for(const key of ['position','normal'])assert.ok([...o.geometry.attributes[key].array].every(Number.isFinite),key);});count++;g.traverse(o=>o.geometry?.dispose());return {box,ms:performance.now()-start};}
for(const family of ['standard','blank','clasp','cartridge'])for(const change of [{},{interior:'solid'},{interior:'divided'},{interior:'magnets'},{interior:'magnets',channelShape:'rectangle'},{scoop:true,label:true},{cols:6,rows:6,height:20},{cols:1,rows:1,height:2}])check({family,c:{...base,...change},options:{showLid:true,parts:true}});
for(const rot of [false,true])for(const magazineCutouts of [false,true])check({family:'magazine',c:{...base,height:2,cols:rot?1:2,rows:rot?2:1,orientation:rot?'90':'0',magazineCutouts}});
for(const testType of ['pin','closure','magnet','spacing','envelope']){const c={...base,channelRows:2,testType,testStart:testType==='magnet'?6:testType==='spacing'?2:.15};check({family:'tests',c,testPlan:testPlan(c)});}
for(const n of [1,6])for(const style of ['skeleton','solid'])check({family:'baseplate',layout:{pw:n*42,pd:n*42,left:0,back:0,pieces:[{x:0,y:0,cols:n,rows:n,x0:0,y0:0,x1:n*42,y1:n*42}]},options:{style,magnets:true,screws:true,magnetDiameter:6.08}});
assert.throws(()=>build({family:'standard',c:{...base,cols:7}},mats));
assert.throws(()=>build({family:'magazine',c:{...base,quantity:30}},mats));
assert.throws(()=>build({family:'cartridge',c:{...base,interior:'magnets',channelColumns:48}},mats));
// A vertical ray through an open bin must hit its floor, not a filled cavity.
const g=build({family:'standard',c:{...base,rim:false}},mats);g.updateMatrixWorld(true);
const hits=new T.Raycaster(new T.Vector3(0,100,0),new T.Vector3(0,-1,0)).intersectObject(g,true);assert.ok(Math.abs(hits[0].point.y-7)<.001);
g.traverse(o=>o.geometry?.dispose());Object.values(mats).forEach(m=>m.dispose());
console.log(`${count} shared preview geometry cases passed; invalid inputs and open cavity checked. GPU validation is separate.`);
