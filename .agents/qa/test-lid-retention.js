const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'../../workshop'),ctx={window:{},console,AbortController};vm.createContext(ctx);
for(const file of ['vendor/three-runtime.js','workshop-three.js'])vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),ctx);
ctx.window.planMagnetChannels=require(path.join(root,'channel-layout.js')).planMagnetChannels;
const {retentionPlan,build,materials}=ctx.window.WorkshopThree,mats=materials();
const c={cols:1,rows:1,height:2,interior:'open',rim:true,magnet:'off',dovetailLid:true,lidDetentInterference:.1,lidMagnetSize:'6',lidMagnetFit:'press'};
for(const lidRetention of ['none','bump','magnet','both']){
 const config={...c,lidRetention},p=retentionPlan(config,41.5,41.5),g=build({family:'standard',c:config,options:{showLid:true,parts:true}},mats);
 let bumps=0,magnets=0;g.traverse(o=>{if(o.userData.detent)bumps++;if(o.userData.lidMagnet)magnets++;if(o.geometry){assert.ok([...o.geometry.attributes.position.array].every(Number.isFinite));o.geometry.dispose();}});
 assert.equal(bumps,p.detents.length);assert.equal(magnets,p.seats.length*2);
}
assert.throws(()=>retentionPlan({...c,lidRetention:'both',interior:'magnets',channelShape:'round',storedDiameter:6,storedClearance:.5,channelColumns:5,channelRows:5,channelGapX:1,channelGapY:1,channelGapLinked:true},41.5,41.5),/overlap/);
assert.throws(()=>retentionPlan({...c,lidRetention:'bump',lidDetentInterference:.3},41.5,41.5));
console.log('Retention preview hardware, finite meshes, collision rejection and mode separation passed.');
