'use strict';
(() => {
 const el=id=>document.getElementById(id),T=window.THREE;
 let renderer,scene,camera,group,material,accent,scheduled=0,last={},azimuth=.65,polar=.85,distance=170,drag=null,initialized=false;
 const diagnostics={ready:false,error:null,updates:0};
 function error(e){diagnostics.error=String(e.message||e);el('error').textContent=diagnostics.error;}
 function config(){const c={};for(const k of ['cols','rows','height','radius'])c[k]=Number(el(k).value);for(const k of ['scoop','rim'])c[k]=el(k).checked;
  if(!Number.isInteger(c.cols)||!Number.isInteger(c.rows)||c.cols<1||c.cols>6||c.rows<1||c.rows>6||!Number.isInteger(c.height)||c.height<2||c.height>20||!Number.isFinite(c.radius)||c.radius<2||c.radius>40)throw Error('Use 1–6 cells, 2–20U, and a 2–40 mm scoop radius.');return c;}
 function outline(w,d,r){const s=new T.Shape(),x=-w/2,y=-d/2;s.moveTo(x+r,y);s.lineTo(x+w-r,y);s.quadraticCurveTo(x+w,y,x+w,y+r);s.lineTo(x+w,y+d-r);s.quadraticCurveTo(x+w,y+d,x+w-r,y+d);s.lineTo(x+r,y+d);s.quadraticCurveTo(x,y+d,x,y+d-r);s.lineTo(x,y+r);s.quadraticCurveTo(x,y,x+r,y);return s;}
 function mesh(geometry,mat=material){const m=new T.Mesh(geometry,mat);group.add(m);return m;}
 function slab(w,d,r,z,height,thickness=0){const shape=outline(w,d,r);if(thickness){const hole=outline(w-2*thickness,d-2*thickness,Math.max(.25,r-thickness));shape.holes.push(hole);}
  const g=new T.ExtrudeGeometry(shape,{depth:height,bevelEnabled:false,curveSegments:10});const p=g.attributes.position;
  for(let i=0;i<p.count;i++){const x=p.getX(i),y=p.getY(i),zz=p.getZ(i);p.setXYZ(i,x,z+zz,-y);}g.computeVertexNormals();return mesh(g);}
 function scoop(w,d,r){
  // A YZ cross-section, extruded across the interior width. Radius changes are
  // calculated directly; no cached combinations or CAD booleans are involved.
  const front=-d/2+2,shape=new T.Shape();shape.moveTo(front,7);shape.lineTo(front,7+r);
  for(let i=1;i<=40;i++){const a=Math.PI/2*i/40;shape.lineTo(front+r-r*Math.cos(a),7+r-r*Math.sin(a));}shape.closePath();
  const g=new T.ExtrudeGeometry(shape,{depth:w-4,bevelEnabled:false,curveSegments:40});const p=g.attributes.position;
  for(let i=0;i<p.count;i++){const depth=p.getX(i),height=p.getY(i),x=p.getZ(i);p.setXYZ(i,(w-4)/2-x,height,depth);}g.computeVertexNormals();mesh(g,accent);
 }
 function build(){scheduled=0;if(!renderer)return;try{const c=config(),t=performance.now(),w=c.cols*42-.5,d=c.rows*42-.5,h=c.height*7,r=Math.min(c.radius,h-7,(d-4)/2);
  const old=group;group=new T.Group();
  slab(w,d,3.75,5,2);slab(w,d,3.75,7,h-7,2);
  for(let y=0;y<c.rows;y++)for(let x=0;x<c.cols;x++){const foot=slab(38.5,38.5,3,0,5);foot.position.set((x-(c.cols-1)/2)*42,0,(y-(c.rows-1)/2)*42);}
  if(c.rim)slab(w,d,3.75,h,3.8,2);
  if(c.scoop)scoop(w,d,r);
  scene.add(group);if(old){scene.remove(old);old.traverse(o=>{if(o.geometry)o.geometry.dispose();});}
  last={...c,width:w,depth:d,nominalHeight:h,overallHeight:h+(c.rim?3.8:0),effectiveRadius:c.scoop?r:0};
  if(!initialized){distance=Math.max(w,d,h)*2.3;initialized=true;}render();
  diagnostics.ready=true;diagnostics.error=null;diagnostics.updates++;diagnostics.updateMS=performance.now()-t;diagnostics.triangles=renderer.info.render.triangles;diagnostics.geometries=renderer.info.memory.geometries;
  el('error').textContent='';el('height-label').textContent=`${c.height}U / ${h} mm`;el('radius-label').textContent=`${c.radius} mm`;
  el('dimensions').textContent=`${c.cols} × ${c.rows} · ${w} × ${d} × ${last.overallHeight.toFixed(1)} mm`;
  el('status').textContent=`Live Three.js · ${diagnostics.updateMS.toFixed(1)} ms update · Drag to orbit`;
  el('scoop-note').textContent=c.scoop?(r<c.radius?`Scoop limited to ${r.toFixed(1)} mm by the available height/depth.`:`Scoop radius ${r} mm. Floor and feet stay fixed as height changes.`):'Scoop off.';
 }catch(e){error(e);}}
 function render(){if(!renderer||!last.nominalHeight)return;const target=new T.Vector3(0,last.overallHeight/2,0);camera.position.set(distance*Math.sin(polar)*Math.sin(azimuth),target.y+distance*Math.cos(polar),distance*Math.sin(polar)*Math.cos(azimuth));camera.lookAt(target);renderer.render(scene,camera);}
 function resize(){if(!renderer)return;const box=el('canvas').getBoundingClientRect();if(!box.width||!box.height)return;renderer.setSize(box.width,box.height);camera.aspect=box.width/box.height;camera.updateProjectionMatrix();render();}
 function report(){return {...diagnostics,parameters:last,revision:T?.REVISION,webgl2:renderer?.capabilities.isWebGL2,canvas:renderer?[renderer.domElement.width,renderer.domElement.height]:null};}
 window.fusionJavaScriptHandler={handle(action,data){try{if(action==='setParameters'){const c=JSON.parse(data);for(const k of ['cols','rows','height','radius'])if(k in c)el(k).value=c[k];for(const k of ['scoop','rim'])if(k in c)el(k).checked=!!c[k];build();}if(action==='capture'){render();return JSON.stringify({...report(),image:renderer.domElement.toDataURL('image/png')});}return JSON.stringify(report());}catch(e){error(e);return JSON.stringify(report());}}};
 try{
  if(!T)throw Error('The local Three.js library could not be loaded.');
  renderer=new T.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5));renderer.setClearColor(0xf3f7fa);el('canvas').appendChild(renderer.domElement);
  scene=new T.Scene();camera=new T.PerspectiveCamera(38,1,.1,3000);scene.add(new T.HemisphereLight(0xffffff,0x778a9a,2.3));const light=new T.DirectionalLight(0xffffff,2.2);light.position.set(-80,180,100);scene.add(light);
  material=new T.MeshStandardMaterial({color:0x80b5d2,roughness:.78,metalness:0});accent=new T.MeshStandardMaterial({color:0x4d98c3,roughness:.75,metalness:0});
  document.querySelectorAll('input').forEach(input=>input.addEventListener('input',()=>{if(!scheduled)scheduled=requestAnimationFrame(build);}));
  el('reset').onclick=()=>{azimuth=.65;polar=.85;distance=Math.max(last.width,last.depth,last.overallHeight)*2.3;render();};
  const canvas=renderer.domElement;canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{if(!drag)return;azimuth-=(e.clientX-drag.x)*.008;polar=Math.max(.12,Math.min(1.52,polar+(e.clientY-drag.y)*.008));drag={x:e.clientX,y:e.clientY};render();});
  for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,()=>drag=null);
  canvas.addEventListener('wheel',e=>{e.preventDefault();distance=Math.max(25,Math.min(1800,distance*Math.exp(e.deltaY*.001)));render();},{passive:false});
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();error('Graphics context lost. Reopen this preview to restore it.');});
  new ResizeObserver(resize).observe(el('canvas'));build();resize();
  if(typeof adsk!=='undefined')adsk.fusionSendData('ready',JSON.stringify(report()));
 }catch(e){error(e);if(typeof adsk!=='undefined')adsk.fusionSendData('ready',JSON.stringify(report()));}
 window.addEventListener('pagehide',()=>{if(scheduled)cancelAnimationFrame(scheduled);group?.traverse(o=>o.geometry?.dispose());material?.dispose();accent?.dispose();renderer?.dispose();});
})();
