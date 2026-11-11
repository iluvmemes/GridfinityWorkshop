const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'../../workshop'),ctx={window:{},console,AbortController};vm.createContext(ctx);
for(const name of ['filament-colors.js','fonts/outlines.js','lettering.js','lid-label.js','vendor/three-runtime.js','workshop-three.js'])vm.runInContext(fs.readFileSync(path.join(root,name),'utf8'),ctx);
const W=ctx.window.WorkshopThree,mats=W.materials();
for(const color of ctx.window.WorkshopFilaments.colors){
 const c={family:'standard',cols:2,rows:1,height:6,interior:'open',magnet:'off',rim:false,dovetailLid:true,lidColor:color.id,lidLabelColor:'white',lidLabelMode:'embedded',lidLabelText:'M3',lidLabelFont:'rubik'};
 const group=W.build({family:'standard',c,options:{showLid:true}},mats);
 const letters=group.children.filter(m=>m.userData.lidLabel);assert.ok(letters.length);
 for(const mesh of letters)assert.equal(mesh.material.color.getHexString(),'ffffff');
 const lidMeshes=group.children.filter(m=>m.userData.ownedMaterial&&!m.userData.lidLabel);assert.ok(lidMeshes.length);
 for(const mesh of lidMeshes)assert.equal(mesh.material.color.getHexString(),color.hex.slice(1).toLowerCase());
 group.traverse(m=>{m.geometry?.dispose();if(m.userData.ownedMaterial)m.material.dispose();});
}
assert.throws(()=>ctx.window.WorkshopLidLabel.plan({lidColor:'unknown'}));
Object.values(mats).forEach(m=>m.dispose());
console.log('PASS: selected lid/label colors reach actual preview materials; invalid swatches rejected');
