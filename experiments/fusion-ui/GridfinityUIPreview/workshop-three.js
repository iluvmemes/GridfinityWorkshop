/* Shared local preview renderer. Approximate display meshes, never CAD bodies. */
(function(root){
'use strict';
const T=root.THREE;
function rounded(x,y,w,d,r=0){
 if(!(w>0&&d>0))throw Error('Preview dimensions must be positive.');
 r=Math.max(0,Math.min(r,w/2,d/2));const s=new T.Shape();
 s.moveTo(x+r,y);s.lineTo(x+w-r,y);s.quadraticCurveTo(x+w,y,x+w,y+r);s.lineTo(x+w,y+d-r);s.quadraticCurveTo(x+w,y+d,x+w-r,y+d);s.lineTo(x+r,y+d);s.quadraticCurveTo(x,y+d,x,y+d-r);s.lineTo(x,y+r);s.quadraticCurveTo(x,y,x+r,y);return s;
}
function circle(x,y,r){const p=new T.Path();p.absarc(x,y,r,0,Math.PI*2,false);return p;}
function extruded(shape,z,height){
 if(!(height>0))throw Error('Preview height must be positive.');
 const g=new T.ExtrudeGeometry(shape,{depth:height,bevelEnabled:false,curveSegments:8});const p=g.attributes.position;
 for(let i=0;i<p.count;i++){const x=p.getX(i),y=p.getY(i),h=p.getZ(i);p.setXYZ(i,x,z+h,-y);}g.computeVertexNormals();return g;
}
function materials(){return {body:new T.MeshStandardMaterial({color:0x83b6d0,roughness:.8}),accent:new T.MeshStandardMaterial({color:0x4d94bc,roughness:.8}),lid:new T.MeshStandardMaterial({color:0xc1d9e6,roughness:.8}),hardware:new T.MeshStandardMaterial({color:0xc9a566,roughness:.72}),selected:new T.MeshStandardMaterial({color:0x4c9ec7,roughness:.8})};}
function builder(mats){const group=new T.Group();
 const add=(g,mat='body')=>{const m=new T.Mesh(g,mats[mat]);group.add(m);return m;};
 const block=(x,y,w,d,z,h,r=0,holes=[],mat='body')=>{const s=rounded(x,y,w,d,r);s.holes.push(...holes);return add(extruded(s,z,h),mat);};
 return {group,add,block};
}
function feet(b,c,w,d){// Geometry still has feet without magnets.
 for(let y=0;y<c.rows;y++)for(let x=0;x<c.cols;x++){
  const cx=(x-(c.cols-1)/2)*42,cy=(y-(c.rows-1)/2)*42,holes=[];
  if(c.magnet!=='off')for(const dx of [-13,13])for(const dy of [-13,13])holes.push(circle(cx+dx,cy+dy,(c.diameter||6.08)/2));
  const depth=c.magnet!=='off'?(c.magnetDepth||2.4):0;
  if(depth)b.block(cx-19.25,cy-19.25,38.5,38.5,0,depth,3,holes);
  b.block(cx-19.25,cy-19.25,38.5,38.5,depth,5-depth,3);
 }}
function ramp(b,q,floor,r){const shape=new T.Shape(),front=q.y;
 shape.moveTo(front,floor);shape.lineTo(front,floor+r);
 for(let i=1;i<=32;i++){const a=Math.PI*i/64;shape.lineTo(front+r-r*Math.cos(a),floor+r-r*Math.sin(a));}shape.closePath();
 const g=new T.ExtrudeGeometry(shape,{depth:q.w,bevelEnabled:false});const p=g.attributes.position;
 for(let i=0;i<p.count;i++){const y=p.getX(i),z=p.getY(i),x=p.getZ(i);p.setXYZ(i,q.x+x,z,-y);}g.computeVertexNormals();b.add(g,'accent');
}
function bin(b,c,family,opts={}){
 const closure=['clasp','cartridge'].includes(family),flat=family==='cartridge';
 const w=flat?c.cartLength: c.cols*42-.5-(closure?12.2:0),d=flat?c.cartWidth:c.rows*42-.5;
 const h=c.height*7,floor=flat?2:7,top=closure?h+1.5:h,base=flat?0:5;
 if(![w,d,h].every(Number.isFinite)||w<4||d<4||h<14||h>140)throw Error('Enter valid bin dimensions.');
 if(!flat)feet(b,c,w,d);
 b.block(-w/2,-d/2,w,d,base,floor-base,3.75);
 const holes=[],cells=[];
 if(c.interior==='magnets'){
  const env={w:w+(closure?12.2:0),d},p=root.planMagnetChannels(c,env,family);
  if(!p.valid)throw Error(p.error);
  for(const q of p.positions){const x=q.x-env.w/2,y=q.y-d/2;holes.push(p.shape==='round'?circle(x+p.width/2,y+p.depth/2,p.width/2):rounded(x,y,p.width,p.depth,.15));}
 }else if(c.interior!=='solid'){
  const nx=c.interior==='divided'?c.divX:1,ny=c.interior==='divided'?c.divY:1;
  if(!Number.isInteger(nx)||!Number.isInteger(ny)||nx<1||ny<1||nx>8||ny>8)throw Error('Enter valid compartment counts.');
  const cw=(w-4-(nx-1)*1.2)/nx,cd=(d-4-(ny-1)*1.2)/ny;
  if(Math.min(cw,cd)<3)throw Error('Compartments are too small.');
  for(let y=0;y<ny;y++)for(let x=0;x<nx;x++){const q={x:-w/2+2+x*(cw+1.2),y:-d/2+2+y*(cd+1.2),w:cw,d:cd};cells.push(q);holes.push(rounded(q.x,q.y,cw,cd,closure?0:1.75));}
 }
 b.block(-w/2,-d/2,w,d,floor,top-floor,3.75,holes);
 if(family==='standard')for(const q of cells){
  if(c.scoop)ramp(b,q,floor,Math.min(c.scoopRadius,h-floor,q.d/2));
  if(c.label){const length=Math.min(c.labelLength,q.w),depth=Math.min(c.labelDepth,q.d/2,h-floor);b.block(q.x+(q.w-length)/2,q.y+q.d-depth,length,depth,h-2,2,.5,[],'hardware');}
 }
 const lid=closure||(family==='standard'&&c.dovetailLid);
 if(c.rim&&!closure&&!c.dovetailLid)b.block(-w/2,-d/2,w,d,h,3.8,3.75,[rounded(-w/2+2,-d/2+2,w-4,d-4,1.75)],'lid');
 if(closure){
  // Hardware is a positional illustration; bore sizes remain real inputs.
  const bore=(c.pinDiameter||1.75)+(c.pinOverrides?c.bodyPinAllowance:c.pinAllowance||.25);
  for(const x of [-w/2-6.1,w/2])b.block(x,-d/2+3,6.1,Math.max(3,d-6),Math.max(base,h-14),12,1,[],'accent');
  b.block(w/2+1,-5,4,10,h-15,12,1,[],'hardware');
  const pin=new T.Mesh(new T.CylinderGeometry(bore/2,bore/2,Math.max(3,d-6),16),b.group.children[0].material);pin.rotation.x=Math.PI/2;pin.position.set(-w/2-3,h-4,0);b.group.add(pin);
 }
 if(lid&&(opts.showLid||opts.parts)){
  const x=opts.parts?w/2+15:-w/2,y=-d/2,z=closure?h+.7:h+2.6;
  b.block(x,y,w,d,z,3,3.75,[],'lid');
  if(c.rim&&!closure)b.block(x,y,w,d,z+3,3.8,3.75,[rounded(x+2,y+2,w-4,d-4,1.75)],'lid');
 }
 return {width:w,depth:d,height:top,hasLid:lid};
}
function magazine(b,c){
 const w=c.cols*42-.5,d=c.rows*42-.5,h=c.height*7;
 let a=c.cartLength+12.2+2*c.slot,depth=c.cartWidth+2*c.slot;if(c.orientation==='90')[a,depth]=[depth,a];
 const nx=Math.floor((w-1.2)/(a+1.2)+1e-9),ny=Math.floor((d-1.2)/(depth+1.2)+1e-9);
 if(c.quantity>nx*ny||c.quantity<1)throw Error('The requested cartridges do not fit.');
 if(h>c.cartridgeHeight*7-(c.magazineCutouts?3:17))throw Error('Lower the magazine guides to clear the matched cartridge.');
 const holes=[],voids=[],windows=[],x0=-(nx*a+(nx-1)*1.2)/2,y0=-(ny*depth+(ny-1)*1.2)/2;
 for(let i=0;i<c.quantity;i++){const x=x0+(i%nx)*(a+1.2),y=y0+Math.floor(i/nx)*(depth+1.2),rot=c.orientation==='90';
  const q=rot?{x,y:y+6.1,w:a,d:depth-12.2}:{x:x+6.1,y,w:a-12.2,d:depth};voids.push(q);holes.push(rounded(q.x,q.y,q.w,q.d));
  if(rot){windows.push({x:x+2,y:-d/2,w:a-4,d:y+6.5+d/2},{x:x+2,y:y+depth-6.5,w:a-4,d:d/2-y-depth+6.5});}
  else{windows.push({x:-w/2,y:y+2,w:x+6.5+w/2,d:depth-4},{x:x+a-6.5,y:y+2,w:w/2-x-a+6.5,d:depth-4});}
 }
 feet(b,c,w,d);b.block(-w/2,-d/2,w,d,5,2,3.75);
 if(!c.magazineCutouts)b.block(-w/2,-d/2,w,d,7,h-7,3.75,holes);
 else{
  b.block(-w/2,-d/2,w,d,7,2,3.75,holes);
  // Union of rectangular openings, triangulated as non-overlapping material tiles.
  const cuts=voids.concat(windows),xs=[-w/2,w/2],ys=[-d/2,d/2];
  for(const q of cuts){xs.push(Math.max(-w/2,q.x),Math.min(w/2,q.x+q.w));ys.push(Math.max(-d/2,q.y),Math.min(d/2,q.y+q.d));}
  const xx=[...new Set(xs)].sort((a,b)=>a-b),yy=[...new Set(ys)].sort((a,b)=>a-b);
  for(let j=0;j<yy.length-1;j++)for(let i=0;i<xx.length-1;i++){const x=(xx[i]+xx[i+1])/2,y=(yy[j]+yy[j+1])/2;if(!cuts.some(q=>x>q.x&&x<q.x+q.w&&y>q.y&&y<q.y+q.d))b.block(xx[i],yy[j],xx[i+1]-xx[i],yy[j+1]-yy[j],9,h-9);}
 }
 return {width:w,depth:d,height:h};
}
function tests(b,c,plan){if(!plan.valid)throw Error(plan.errors.join(' '));
 for(const q of plan.samples){
  if(c.testType==='closure'){const start=b.group.children.length;bin(b,{...c,cols:2,rows:1,cartLength:71.3,cartWidth:41.5,height:25/7,interior:'open',magnet:'off',rim:false},'cartridge',{showLid:true});for(const m of b.group.children.slice(start))m.position.x+=q.x+q.w/2;continue;}
  if(c.testType==='envelope'){b.block(q.x,q.y,q.w,q.d,0,3,0,[rounded(q.x+3,q.y+3,q.w-6,q.d-6)]);if(c.testPosts&&q.h>3)for(const x of [q.x,q.x+q.w-3])for(const y of [q.y,q.y+q.d-3])b.block(x,y,3,3,3,q.h-3);continue;}
  if(c.testType==='pin'){
   const s=rounded(q.x,0,q.w,q.h);s.holes.push(circle(q.x+q.w/2,4,q.bore/2));const g=new T.ExtrudeGeometry(s,{depth:q.d,bevelEnabled:false,curveSegments:16});g.translate(0,0,-q.y-q.d);b.add(g);continue;
  }
  const holes=[];
  if(c.testType==='magnet')holes.push(circle(q.x+q.w/2,q.y+7,q.bore/2));
  else for(let y=0;y<c.channelRows;y++)for(let x=0;x<c.channelColumns;x++){const px=q.x+2+x*(q.cw+q.gapX),py=q.y+2+y*(q.cd+q.gapY);holes.push(c.channelShape==='round'?circle(px+q.cw/2,py+q.cd/2,q.cw/2):rounded(px,py,q.cw,q.cd));}
  if(c.testType==='magnet'){b.block(q.x,q.y,q.w,q.d,0,c.magnetDepth,0,holes);b.block(q.x,q.y,q.w,q.d,c.magnetDepth,q.h-c.magnetDepth);}
  else{b.block(q.x,q.y,q.w,q.d,0,2);b.block(q.x,q.y,q.w,q.d,2,q.h-2,0,holes);}
 }
}
// The captured baseplate profiles contain only circular A arcs and M/L/Z.
function profile(data,ox,oy){const tok=data.match(/[MLAZ]|[-+]?\d*\.?\d+(?:e[-+]?\d+)?/gi);let i=0,x=0,y=0;const p=new T.Path();
 while(i<tok.length){const cmd=tok[i++];if(cmd==='Z'){p.closePath();continue;}if(cmd==='M'||cmd==='L'){x=+tok[i++];y=+tok[i++];p[cmd==='M'?'moveTo':'lineTo'](x+ox,y+oy);continue;}
  if(cmd!=='A')throw Error('Unsupported captured profile command.');const r=+tok[i++];i++;i++;const large=+tok[i++],sweep=+tok[i++],xx=+tok[i++],yy=+tok[i++],dx=x-xx,dy=y-yy,d=Math.hypot(dx,dy);const h=Math.sqrt(Math.max(0,r*r-d*d/4)),sign=large===sweep?-1:1,cx=(x+xx)/2+sign*dy*h/d,cy=(y+yy)/2-sign*dx*h/d;
  p.absarc(cx+ox,cy+oy,r,Math.atan2(y-cy,x-cx),Math.atan2(yy-cy,xx-cx),!sweep);x=xx;y=yy;
 }return p;}
function plate(b,data,o){const profiles=typeof GRIDFINITY_CELL_PROFILES!=='undefined'?GRIDFINITY_CELL_PROFILES:root.GRIDFINITY_CELL_PROFILES;
 for(const [index,p] of data.pieces.entries()){
  const start=b.group.children.length,cells=[];for(let y=p.y;y<p.y+p.rows;y++)for(let x=p.x;x<p.x+p.cols;x++)cells.push([data.left+x*42-data.pw/2,data.back+y*42-data.pd/2]);
  const holes=(s,hardware=false,radius=o.magnets?o.magnetDiameter/2:1.5)=>{const list=[];for(const [x,y] of cells){if(s)list.push(profile(profiles[s],x,y));if(hardware)for(const [mx,my] of profiles.magnetCenters)list.push(circle(x+mx,y+my,radius));}return list;};
  const x=p.x0-data.pw/2,y=p.y0-data.pd/2,w=p.x1-p.x0,d=p.y1-p.y0,mat=index===o.selected?'selected':'body';
  const pocketDepth=Math.min(3.4,Math.max(.1,o.magnetDepth||2.4)),bottom=3.4-pocketDepth;
  if(bottom>0)b.block(x,y,w,d,0,bottom,0,holes(o.style==='skeleton'?'skeleton':null,o.screws,1.5),mat);
  b.block(x,y,w,d,bottom,pocketDepth,0,holes(o.style==='skeleton'?'skeleton':null,o.magnets||o.screws),mat);
  for(const [z,h,section] of [[3.4,.7,'floor'],[4.1,2,'shoulder'],[6.1,2.3,'mouth']])b.block(x,y,w,d,z,h,0,holes(section),mat);
  if(o.exploded)for(const m of b.group.children.slice(start)){m.position.x+=p.x*2;m.position.z-=p.y*2;}
 }}
function build(recipe,mats){const b=builder(mats);try{
 const {family,c,options={}}=recipe;
 if(c&&(![c.cols,c.rows].every(v=>Number.isInteger(v)&&v>=1&&v<=6)))throw Error('Use 1–6 grid cells per axis.');
 if(family==='baseplate')plate(b,recipe.layout,options);
 else if(family==='tests')tests(b,c,recipe.testPlan);
 else if(family==='magazine')magazine(b,c);
 else bin(b,c,family,options);
 return b.group;
 }catch(e){b.group.traverse(o=>o.geometry?.dispose());throw e;}}
class Preview{
 constructor(container,status){this.container=container;this.status=status;this.mats=materials();this.az=.65;this.polar=.85;this.zoom=1;this.stats={ready:false};
 try{this.renderer=new T.WebGLRenderer({antialias:true});this.renderer.setPixelRatio(Math.min(root.devicePixelRatio||1,1.5));this.renderer.setClearColor(0xf3f7fa);container.appendChild(this.renderer.domElement);
 this.scene=new T.Scene();this.camera=new T.PerspectiveCamera(38,1,.1,5000);this.scene.add(new T.HemisphereLight(0xffffff,0x738897,2.3));const light=new T.DirectionalLight(0xffffff,2.2);light.position.set(-80,180,100);this.scene.add(light);
 const canvas=this.renderer.domElement;let drag;canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});canvas.addEventListener('pointermove',e=>{if(!drag)return;this.az-=(e.clientX-drag[0])*.008;this.polar=Math.max(.12,Math.min(3.02,this.polar+(e.clientY-drag[1])*.008));drag=[e.clientX,e.clientY];this.render();});for(const type of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(type,()=>drag=null);
 canvas.addEventListener('wheel',e=>{e.preventDefault();this.zoom=Math.max(.3,Math.min(5,this.zoom*Math.exp(e.deltaY*.001)));this.render();},{passive:false});canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();this.fail('3D graphics unavailable. Use the 2D layout or reopen the catalog.');});
 this.observer=new ResizeObserver(()=>this.resize());this.observer.observe(container);this.resize();
 }catch(e){this.fail('3D graphics unavailable. Use the 2D layout. '+e.message);}}
 fail(message){this.stats.error=message;this.status.textContent=message;}
 update(recipe){this.pending=recipe;if(!this.frame)this.frame=requestAnimationFrame(()=>this.flush());}
 flush(){this.frame=0;if(!this.renderer)return;try{const start=performance.now(),key=JSON.stringify(this.pending);if(key===this.key){if(!this.stats.error?.startsWith('3D graphics')){this.stats.error=null;this.status.textContent='Drag to orbit · Scroll to zoom · Approximate geometry; interfaces and hardware simplified.';}this.resize();return;}const next=build(this.pending,this.mats),box=new T.Box3().setFromObject(next);if(box.isEmpty())throw Error('No preview geometry.');
 if(this.group){this.scene.remove(this.group);this.group.traverse(o=>o.geometry?.dispose());}this.group=next;this.scene.add(next);this.target=box.getCenter(new T.Vector3());this.size=box.getSize(new T.Vector3());if(this.family!==this.pending.family){this.zoom=1;this.family=this.pending.family;}this.key=key;this.resize();
 this.stats={ready:true,family:this.family,updateMS:performance.now()-start,triangles:this.renderer.info.render.triangles,geometries:this.renderer.info.memory.geometries,bounds:[this.size.x,this.size.y,this.size.z],error:null};
 this.status.textContent='Drag to orbit · Scroll to zoom · Approximate geometry; interfaces and hardware simplified.';
 }catch(e){this.fail('Last valid preview: '+e.message);}}
 render(){if(!this.target||!this.renderer||this.stats.error?.startsWith('3D graphics'))return;const max=Math.max(this.size.x,this.size.y,this.size.z),dist=max*2.1*Math.max(1,1/this.camera.aspect)*this.zoom;
 this.camera.position.set(this.target.x+dist*Math.sin(this.polar)*Math.sin(this.az),this.target.y+dist*Math.cos(this.polar),this.target.z+dist*Math.sin(this.polar)*Math.cos(this.az));this.camera.lookAt(this.target);this.renderer.render(this.scene,this.camera);}
 resize(){if(!this.renderer)return;const b=this.container.getBoundingClientRect();if(b.width<1||b.height<1)return;this.renderer.setSize(b.width,b.height);this.camera.aspect=b.width/b.height;this.camera.updateProjectionMatrix();this.render();}
 fit(){this.zoom=1;this.az=.65;this.polar=.85;this.render();}
 capture(){this.flush();this.render();return this.renderer.domElement.toDataURL('image/png');}
 dispose(){if(this.frame)cancelAnimationFrame(this.frame);this.observer?.disconnect();this.group?.traverse(o=>o.geometry?.dispose());Object.values(this.mats).forEach(m=>m.dispose());this.renderer?.dispose();}
}
root.WorkshopThree={Preview,build,materials};
})(window);
