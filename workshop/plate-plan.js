/* Pure planner. Keep parity with plate_plan.py; tested against shared requests. */
(function(root){
function axis(count,leading,trailing,bed,maximum){
 const found=new Map(),add=p=>{if(!p.length||p.reduce((a,b)=>a+b,0)!==count||Math.min(...p)<1||Math.max(...p)>maximum)return;if(p.every((n,i)=>n*42+(i===0?leading-.25:0)+(i===p.length-1?trailing-.25:0)<=bed+1e-8))found.set(p.join(','),p);};
 for(let size=1;size<=maximum;size++){const n=Math.floor(count/size),rem=count%size,a=Array(n).fill(size);add([...a,...(rem?[rem]:[])]);add([...(rem?[rem]:[]),...a]);if(rem)add([...a.slice(0,Math.floor(n/2)),rem,...a.slice(Math.floor(n/2))]);for(let e=1;e<=size;e++){const m=count-2*e;if(m>=0&&m%size===0)add([e,...Array(m/size).fill(size),e]);}}
 for(let n=Math.ceil(count/maximum);n<=count;n++){const lo=Math.floor(count/n),rem=count%n;add([...Array(rem).fill(lo+1),...Array(n-rem).fill(lo)]);add([...Array(n-rem).fill(lo),...Array(rem).fill(lo+1)]);}
 const paths=new Map([[0,[]]]);for(let start=0;start<count;start++){if(!paths.has(start))continue;for(let size=1;size<=Math.min(maximum,count-start);size++){const end=start+size,p=[...paths.get(start),size],span=size*42+(start===0?leading-.25:0)+(end===count?trailing-.25:0);if(span<=bed+1e-8&&(!paths.has(end)||p.length<paths.get(end).length))paths.set(end,p);}}if(paths.has(count))add(paths.get(count));
 const result=[...found.values()].sort((a,b)=>a.length-b.length||compare(a,b));if(!result.length)throw Error('The print bed is too small for one cell with this padding.');return result;
}
function compare(a,b){for(let i=0;i<Math.min(a.length,b.length);i++){const d=Array.isArray(a[i])?compare(a[i],b[i]):a[i]-b[i];if(d)return d;}return a.length-b.length;}
const signature=p=>[p.columns,p.rows,...p.margins,...p.edges];
const rotate=s=>{const[c,r,l,rt,b,f,el,er,eb,ef]=s;return[r,c,f,b,l,rt,ef,eb,el,er];};
const key=s=>s.map(n=>Math.round(Number(n)*1e6)/1e6).join(',');
function group(pieces){const types=[],lookup=new Map();for(const p of pieces){const k=key(signature(p));if(!lookup.has(k)){types.push({...p,typeId:types.length<26?String.fromCharCode(65+types.length):'T'+(types.length+1),quantity:0});let s=signature(p);for(let r=0;r<4;r++){if(!lookup.has(key(s)))lookup.set(key(s),[types.length-1,r*90]);s=rotate(s);}}const[i,r]=lookup.get(k);types[i].quantity++;Object.assign(p,{typeId:types[i].typeId,rotation:r,typeIndex:i});}return types;}
function piecesFor(xs,ys,s){const result=[];let y=0;ys.forEach((rows,iy)=>{let x=0;xs.forEach((columns,ix)=>{const edges=[ix===0,ix===xs.length-1,iy===0,iy===ys.length-1],margins=[edges[0]?s.left:.25,edges[1]?s.right:.25,edges[2]?s.back:.25,edges[3]?s.front:.25],l=margins[0],r=margins[1],b=margins[2],f=margins[3];result.push({x,y,columns,rows,x0:x*42-l,y0:y*42-b,x1:(x+columns)*42-.5+r,y1:(y+rows)*42-.5+f,margins,edges,layoutRow:iy+1,layoutColumn:ix+1});x+=columns;});y+=rows;});return result;}
function plan(s){const preference=s.planningPreference||'repeat',symmetry=s.preferSymmetry!==false,outputMode=s.outputMode||'unique';const xs=axis(s.columns,s.left,s.right,s.bedWidth,s.maxPlateColumns),ys=axis(s.rows,s.back,s.front,s.bedDepth,s.maxPlateRows),minimum=xs[0].length*ys[0].length,candidates=[];
 const diversity=(p,l,r)=>new Set(p.map((n,i)=>key([n,i===0?l:.25,i===p.length-1?r:.25,i===0,i===p.length-1]))).size;
 for(const x of xs)for(const y of ys){const total=x.length*y.length;if(preference==='plates'&&total!==minimum||preference==='repeat'&&total>Math.ceil(minimum*1.25))continue;const unique=diversity(x,s.left,s.right)*diversity(y,s.back,s.front),asym=symmetry?[x,y].reduce((a,p)=>a+p.reduce((b,n,i)=>b+Math.abs(n-p[p.length-1-i]),0),0):0;candidates.push([unique,total,asym,x,y]);}
 candidates.sort(compare);const finalists=[...candidates.slice(0,48),...candidates.slice().sort((a,b)=>a[1]-b[1]||a[0]-b[0]||a[2]-b[2]||compare(a,b)).slice(0,8)];let best;
 for(const[_,total,asym,x,y]of finalists){const pieces=piecesFor(x,y,s),plateTypes=group(pieces),score=preference==='plates'?[total,plateTypes.length,asym,x,y]:[plateTypes.length,total,asym,x,y];if(!best||compare(score,best.score)<0)best={score,pieces,plateTypes,xSections:x,ySections:y,chunkX:Math.max(...x),chunkY:Math.max(...y)};}
 delete best.score;return{...best,minimumPlateCount:minimum,planningPreference:preference,preferSymmetry:symmetry,outputMode};
}
root.PlatePlan={plan,group,rotate};if(typeof module!=='undefined')module.exports=root.PlatePlan;
})(typeof window!=='undefined'?window:globalThis);
