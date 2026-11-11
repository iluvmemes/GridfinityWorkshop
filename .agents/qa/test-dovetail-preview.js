/* Outside-face visibility and actual rail/tongue extents, independent of GPU. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dir=__dirname+'/../../workshop/',ctx={window:{},console,AbortController};vm.createContext(ctx);
for(const file of ['vendor/three-runtime.js','workshop-three.js'])vm.runInContext(fs.readFileSync(dir+file,'utf8'),ctx);
const T=ctx.window.THREE,{build,materials}=ctx.window.WorkshopThree,mats=materials();
function volume(geometry){
 const p=geometry.attributes.position,index=geometry.index,n=index?index.count:p.count;
 const v=i=>new T.Vector3().fromBufferAttribute(p,index?index.getX(i):i);let sum=0;
 for(let i=0;i<n;i+=3)sum+=v(i).dot(v(i+1).cross(v(i+2)))/6;
 return sum;
}
let cases=0;
for(const [cols,rows] of [[1,1],[2,3],[6,6]])for(const parts of [false,true])for(const showLid of [false,true])for(const rim of [false,true]){
 const c={cols,rows,height:6,interior:'open',rim,magnet:'off',dovetailLid:true,lidRetention:'none'};
 const group=build({family:'standard',c,options:{showLid,parts}},mats);group.updateMatrixWorld(true);
 const meshes=group.children.filter(m=>m.userData.dovetail);
 assert.equal(meshes.length,showLid||parts?3:2);
 for(const mesh of meshes){
  const box=new T.Box3().setFromObject(mesh),center=box.getCenter(new T.Vector3());
  // Probe the guide's full-height outer strip, rather than its sloping face.
  if(mesh.userData.dovetail==='left guide')center.x=box.min.x+.5;
  if(mesh.userData.dovetail==='right guide')center.x=box.max.x-.5;
  assert.ok(volume(mesh.geometry)>0,mesh.userData.dovetail+' must have outward winding');
  const top=new T.Raycaster(new T.Vector3(center.x,box.max.y+10,center.z),new T.Vector3(0,-1,0)).intersectObject(mesh);
  assert.ok(top.length>0,mesh.userData.dovetail+' must be visible from above');
  const underside=new T.Raycaster(new T.Vector3(center.x,box.min.y-10,center.z),new T.Vector3(0,1,0)).intersectObject(mesh);
  assert.ok(underside.length>0,mesh.userData.dovetail+' underside must face outward');
  assert.ok(Math.abs(top[0].point.y-box.max.y)<1e-4);
  assert.ok(Math.abs(underside[0].point.y-box.min.y)<1e-4);
  assert.ok(Math.abs(box.min.y-(42+(mesh.userData.dovetail==='tongue'?.3:0)))<1e-4);
  assert.ok(Math.abs(box.max.y-(42+(mesh.userData.dovetail==='tongue'?2.6:2.3)))<1e-4);
 }
 group.traverse(o=>o.geometry?.dispose());cases++;
}
Object.values(mats).forEach(m=>m.dispose());
console.log(`PASS: ${cases} dovetail preview combinations; outward faces, top/underside visibility and CAD height offsets`);
