// Geometry checks use real Three.js with a stub renderer; GPU rendering is
// checked separately inside Fusion. No browser or CAD geometry is created here.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=__dirname+'/../../workshop/';
const nodes={};for(const id of ['cols','rows','height','radius','scoop','rim','canvas','reset','error','status','dimensions','height-label','radius-label','scoop-note'])nodes[id]={value:({cols:2,rows:2,height:6,radius:25})[id],checked:true,textContent:'',addEventListener(){},appendChild(){},getBoundingClientRect(){return{width:640,height:500}}};
let rendered=null,disposed=0;
const context={window:{devicePixelRatio:1,addEventListener(){}},document:{getElementById:id=>nodes[id],querySelectorAll:()=>[]},console,performance,AbortController,ResizeObserver:class{observe(){}},requestAnimationFrame:()=>1,cancelAnimationFrame(){}};
vm.createContext(context);vm.runInContext(fs.readFileSync(root+'vendor/three-runtime.js','utf8'),context);
const T=context.window.THREE;
T.WebGLRenderer=class{constructor(){this.domElement={addEventListener(){}};this.info={render:{triangles:0},memory:{geometries:0}};this.capabilities={isWebGL2:true};}setPixelRatio(){}setClearColor(){}setSize(){}render(scene){rendered=scene;scene.traverse(o=>{if(o.geometry&&!o.geometry._testSeen){o.geometry._testSeen=true;o.geometry.addEventListener('dispose',()=>disposed++);}});}dispose(){}};
vm.runInContext(fs.readFileSync(root+'three-demo.js','utf8'),context);
function set(p){return JSON.parse(context.window.fusionJavaScriptHandler.handle('setParameters',JSON.stringify(p)));}
for(const change of [{},{height:2,radius:40},{cols:6,rows:6,height:20},{cols:1,rows:1,height:4,rim:false,scoop:false}]){
 const r=set(change);assert.equal(r.error,null);assert.equal(r.ready,true);
 const b=new T.Box3().setFromObject(rendered),s=b.getSize(new T.Vector3());
 assert.ok(Math.abs(s.x-r.parameters.width)<.001);
 assert.ok(Math.abs(s.z-r.parameters.depth)<.001);
 assert.ok(Math.abs(s.y-r.parameters.overallHeight)<.001);
 assert.ok(Math.abs(b.min.y)<.001,'Feet remain at zero');
 if(r.parameters.scoop)assert.ok(r.parameters.effectiveRadius<=r.parameters.nominalHeight-7);
 rendered.traverse(o=>{if(o.geometry){assert.ok([...o.geometry.attributes.position.array].every(Number.isFinite));assert.ok([...o.geometry.attributes.normal.array].every(Number.isFinite));}});
}
assert.ok(disposed>0,'Replaced geometry is disposed');
assert.ok(set({cols:7}).error,'Oversize inputs are rejected');
assert.equal(set({cols:2,rows:2,height:6,scoop:true,rim:true,radius:25}).error,null);
console.log('Three.js geometry bounds, fixed floor, scoop limits, finite normals, invalid input, and replacement disposal passed. GPU validation remains separate.');
