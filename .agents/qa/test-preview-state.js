// Regressions found by E2E: returning to a cached valid recipe clears its error.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'../../workshop');
const ctx={window:{},console,AbortController,performance,ResizeObserver:class{observe(){}disconnect(){}},requestAnimationFrame:()=>1,cancelAnimationFrame(){}};vm.createContext(ctx);for(const f of ['vendor/three-runtime.js','workshop-three.js'])vm.runInContext(fs.readFileSync(path.join(root,f),'utf8'),ctx);
const T=ctx.window.THREE;T.WebGLRenderer=class{constructor(){this.domElement={addEventListener(){}};this.info={render:{triangles:0},memory:{geometries:0}};}setPixelRatio(){}setClearColor(){}setSize(){}render(){}dispose(){}};
const status={},p=new ctx.window.WorkshopThree.Preview({appendChild(){},getBoundingClientRect(){return{width:600,height:400}}},status);
const valid={family:'standard',c:{cols:2,rows:1,height:6,interior:'open',magnet:'off',rim:true}};
p.update(valid);p.flush();const original=p.group;assert.equal(p.stats.error,null);
p.update({...valid,c:{...valid.c,cols:7}});p.flush();assert.ok(p.stats.error);assert.equal(p.group,original);
p.update(valid);p.flush();assert.equal(p.stats.error,null);assert.equal(p.group,original);assert.ok(!status.textContent.includes('Last valid'));
let disposed=0;original.traverse(o=>o.geometry?.addEventListener('dispose',()=>disposed++));p.update({...valid,c:{...valid.c,height:8}});p.flush();assert.ok(disposed>0);p.dispose();console.log('Cached-state recovery and replaced geometry disposal passed.');
