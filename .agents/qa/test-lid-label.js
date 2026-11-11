const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const dir=path.resolve(__dirname,'../../workshop'),ctx={window:{},console,AbortController};vm.createContext(ctx);
for(const name of ['fonts/outlines.js','lettering.js','lid-label.js','vendor/three-runtime.js','workshop-three.js'])vm.runInContext(fs.readFileSync(path.join(dir,name),'utf8'),ctx);
const {WorkshopLidLabel:L,WorkshopThree:W,THREE:T}=ctx.window;
const base={family:'standard',dovetailLid:true,cols:2,rows:1,height:6,interior:'open',magnet:'off',rim:false,lidLabelMode:'embedded',lidLabelText:'M3 HARDWARE\nBOLTS & NUTS',lidLabelLayout:'multi',lidLabelFont:'rubik',lidLabelHeight:5,lidLabelDepth:.6};
const mats=W.materials();
for(const font of ['rubik','atkinson'])for(const mode of ['cutout','raised','embedded']){
 const c={...base,lidLabelMode:mode,lidLabelFont:font},p=L.plan(c);assert.equal(p.rows.length,2);
 const g=W.build({family:'standard',c,options:{showLid:true}},mats);g.updateMatrixWorld(true);
 g.traverse(o=>{if(o.geometry){assert.ok([...o.geometry.attributes.position.array].every(Number.isFinite));o.geometry.dispose();}});
 const labels=g.children.filter(o=>o.userData.lidLabel);assert.equal(labels.length>0,mode!=='cutout');
 if(labels.length){const box=new T.Box3().setFromObject(new T.Group().add(...labels));assert.ok(Math.abs(box.max.y-(47.6+(mode==='raised'?.6:0)))<1e-4);}
 const python=JSON.parse(require('node:child_process').execFileSync('python',['-c',`import json; from workshop.lid_label import plan; c=json.loads(${JSON.stringify(JSON.stringify({...c,widthMM:83.5,depthMM:41.5}))}); print(json.dumps(plan(c)))`],{cwd:path.dirname(dir),encoding:'utf8'}));
 assert.ok(Math.abs(p.height-python.height)<1e-8);assert.ok(Math.abs(p.width-python.width)<1e-8);assert.deepEqual(Array.from(p.rows,r=>r.text),Array.from(python.rows,r=>r.text));
}
const p=L.plan({...base,lidLabelText:'BO8 i',lidLabelLayout:'single'}),shapes=L.shapes(p.rows[0],'rubik',T);
assert.equal(shapes.length,5);assert.equal(shapes.reduce((n,s)=>n+s.holes.length,0),5);
assert.throws(()=>L.plan({...base,lidLabelText:'A\nB\nC\nD\nE'}));
Object.values(mats).forEach(m=>m.dispose());
console.log('PASS: lid label preview geometry, letter holes, modes and Python/browser layout parity');
