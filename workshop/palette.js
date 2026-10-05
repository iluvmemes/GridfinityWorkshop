
const runtimeErrors = [];
window.addEventListener('error', event => {
  runtimeErrors.push(event.message);
  if (typeof adsk !== 'undefined' && typeof adsk.fusionSendData === 'function') {
    adsk.fusionSendData('uiError', JSON.stringify({message:event.message}));
  }
});
(()=>{const root=document.getElementById('gf-workshop'),q=s=>root.querySelector(s),all=s=>[...root.querySelectorAll(s)];const state={mode:'fit',style:'skeleton',view:'assembled',anchor:4,selected:0};const names=['Back left','Back center','Back right','Middle left','Centered','Middle right','Front left','Front center','Front right'];const arrows=['↖','↑','↗','←','•','→','↙','↓','↘'];q('.gw-anchor').innerHTML=names.map((n,i)=>`<button aria-label="${n}" data-anchor="${i}" aria-pressed="${i===4}">${arrows[i]}</button>`).join('');const num=id=>Number(q('#gw-'+id).value),fmt=n=>Number(n.toFixed(2)).toString();let last; let creating=false; let useThree=true; let previewThree=null;
function validNumber(el) {
  const value = Number(el.value);
  const min = Number(el.getAttribute('min'));
  const max = Number(el.getAttribute('max'));
  const step = Number(el.getAttribute('step') || 1);
  if (String(el.value).trim() === '' || !Number.isFinite(value)) return false;
  if (value < min || value > max) return false;
  return Math.abs((value - min) / step - Math.round((value - min) / step)) < 0.000001;
}
function bedChunk(count,leading,trailing,bed){
  for(let stride=count;stride>=1;stride--){
    let fits=true;
    for(let start=0;start<count;start+=stride){
      const span=Math.min(stride,count-start)*42+(start===0?leading:0)+(start+stride>=count?trailing-.5:0);
      if(span>bed+1e-8){fits=false;break;}
    }
    if(fits)return stride;
  }
  return 0;
}
function calculate(){if(state.style==='skeleton'&&q('#gw-magnets').checked&&num('magnet-diameter')>6.5)return {error:'Skeletonized plates support magnet holes up to 6.5 mm. Choose Solid for larger holes.'};const fit=state.mode==='fit',clear=fit?num('clearance'):0,w=fit?num('width'):num('columns')*42-.5,d=fit?num('depth'):num('rows')*42-.5;for(const el of all('input[type=number]')){if(el.closest('[hidden]')||el.id.startsWith('gw-magnet-')&&!q('#gw-magnets').checked)continue;if(!validNumber(el))return {error:'Enter a valid value within the field limits.'};}const nx=fit?Math.floor((w-clear*2+.5)/42):num('columns'),ny=fit?Math.floor((d-clear*2+.5)/42):num('rows');if(nx<1||ny<1||nx>6||ny>6)return{error:'Baseplates support 1–6 full cells per axis. Adjust the space or clearance.'};const pw=w-clear*2,pd=d-clear*2,ex=pw-(nx*42-.5),ey=pd-(ny*42-.5),left=ex*(state.anchor%3)/2,back=ey*Math.floor(state.anchor/3)/2;const cx=bedChunk(nx,left,ex-left,num('bed-width')),cy=bedChunk(ny,back,ey-back,num('bed-depth'));if(!cx||!cy)return{error:'The bed is too small for a cell with this padding.'};let pieces=[];for(let y=0;y<ny;y+=cy)for(let x=0;x<nx;x+=cx){let cols=Math.min(cx,nx-x),rows=Math.min(cy,ny-y),x0=x===0?0:left+x*42,y0=y===0?0:back+y*42,x1=x+cols===nx?pw:left+(x+cols)*42,y1=y+rows===ny?pd:back+(y+rows)*42;pieces.push({x,y,cols,rows,x0,y0,x1,y1});}return{w,d,pw,pd,nx,ny,left,back,right:ex-left,front:ey-back,pieces};}
function render(){q('#gw-press-fit').checked=Math.abs(num('magnet-diameter')-6.08)<0.000001;q('#gw-press-fit').disabled=!q('#gw-magnets').checked;q('#gw-fit').hidden=state.mode!=='fit';q('#gw-grid').hidden=state.mode!=='grid';q('#gw-padding-section').hidden=state.mode!=='fit';for(const key of ['mode','style','view','anchor'])all('[data-'+key+']').forEach(b=>b.setAttribute('aria-pressed',String(String(state[key])===b.dataset[key])));q('#gw-anchor-name').textContent=names[state.anchor];const data=calculate();q('#gw-error').hidden=!data.error;q('#gw-create').disabled=creating||!!data.error;if(data.error){q('#gw-error').textContent=data.error;q('#gw-title').textContent='Last valid preview';return;}last=data;const{w,d,pw,pd,nx,ny,left,back,right,front,pieces}=data;state.selected=Math.max(0,Math.min(state.selected,pieces.length-1));q('#gw-grid-summary').textContent=`${nx} × ${ny} grid · ${nx*ny} usable cells`;['left','right','front','back'].forEach(k=>q('#gw-'+k).textContent=fmt(data[k])+' mm');q('#gw-title').textContent=state.mode==='fit'?'Drawer baseplate':'Grid baseplate';q('#gw-dimensions').textContent=`${fmt(pw)} × ${fmt(pd)} mm finished plate`;q('#gw-piece-count').textContent=pieces.length===1?'One printable plate':`${pieces.length} printable pieces`;const p=pieces[state.selected];q('#gw-piece-detail').textContent=`Piece ${state.selected+1} · ${p.cols} × ${p.rows} cells · ${fmt(p.x1-p.x0)} × ${fmt(p.y1-p.y0)} mm`;q('#gw-piece-buttons').innerHTML=pieces.map((p,i)=>`<button data-piece="${i}" aria-pressed="${i===state.selected}">Piece ${i+1}</button>`).join('');draw();}
function draw() {
  if (!last) return;
  q('#gw-three').hidden=!useThree;q('#gw-drawing').hidden=useThree;q('#gw-fit-view').hidden=!useThree;q('#gw-three-status').hidden=!useThree;
  if(useThree){if(!previewThree)previewThree=new WorkshopThree.Preview(q('#gw-three'),q('#gw-three-status'));previewThree.update({family:'baseplate',layout:last,options:{style:state.style,exploded:state.view==='pieces',magnets:q('#gw-magnets').checked,screws:q('#gw-screws').checked,magnetDiameter:num('magnet-diameter'),magnetDepth:num('magnet-depth'),selected:state.selected}});}
  drawGridfinityPreview(q('#gw-drawing'), last, {
    style: state.style, exploded: state.view === 'pieces', fit: state.mode === 'fit',
    magnets:q('#gw-magnets').checked, screws:q('#gw-screws').checked,
    magnetDiameter:num('magnet-diameter'), clearance:state.mode === 'fit' ? num('clearance') : 0,
    showSplits:q('#gw-splits').checked, selected:state.selected
  });
}
root.addEventListener('click', e => {
  const b = e.target && typeof e.target.closest === 'function' ? e.target.closest('button') : null;
  if (!b || b.disabled) return;
  if(b.id==='gw-view-mode'){useThree=!useThree;b.textContent=useThree?'2D layout':'3D preview';draw();return;}
  if(b.id==='gw-fit-view'){previewThree?.fit();return;}
  if (b.id === 'gw-create') {
    const current = calculate();
    if (current.error) { render(); return; }
    if (typeof adsk === 'undefined' || typeof adsk.fusionSendData !== 'function') {
      q('#gw-create-status').textContent='Open this interface inside Fusion to create a plate.';
      return;
    }
    creating=true;
    q('#gw-create-status').textContent='Creating baseplate…';
    render();
    send('create',creationRequest());
    return;
  }
  for (const k of ['mode','style','view','anchor']) {
    if (b.dataset[k] !== undefined) state[k] = k === 'anchor' ? Number(b.dataset[k]) : b.dataset[k];
  }
  if (b.dataset.piece !== undefined) state.selected = Number(b.dataset.piece);
  render();
  save();
});
let diameterBeforePressFit = '6.5';
root.addEventListener('input', event => {
  if (event.target.id === 'gw-press-fit') {
    const diameter = q('#gw-magnet-diameter');
    if (event.target.checked) {
      diameterBeforePressFit = diameter.value;
      diameter.value = '6.08';
    } else {
      diameter.value = diameterBeforePressFit;
    }
  } else if (event.target.id === 'gw-magnet-diameter' && Math.abs(num('magnet-diameter')-6.08)>0.000001) {
    diameterBeforePressFit = event.target.value;
  }
  render();
  save();
});
function creationRequest() {
  return {mode:state.mode,style:state.style,anchor:state.anchor,
    width:num('width'),depth:num('depth'),clearance:num('clearance'),
    columns:num('columns'),rows:num('rows'),magnets:q('#gw-magnets').checked,
    screws:q('#gw-screws').checked,magnetDiameter:num('magnet-diameter'),
    magnetDepth:num('magnet-depth'),bedWidth:num('bed-width'),bedDepth:num('bed-depth')};
}
function send(action, data) {
  if (typeof adsk === 'undefined' || typeof adsk.fusionSendData !== 'function') return;
  const result = adsk.fusionSendData(action, JSON.stringify(data));
  if (result && typeof result.catch === 'function') result.catch(error => {
    creating=false;render();q('#gw-create-status').textContent='Could not contact Fusion. Please try again.';
    console.error(error);
  });
}
window.addEventListener('pagehide',()=>previewThree?.dispose());
function report() {
  const svg = q('#gw-drawing svg');
  return {
    threePreview:previewThree?.stats||null,
    previewOnly: !creating,
    creationStatus: q('#gw-create-status').textContent,
    creationRequest: creationRequest(),
    bridgeAvailable: typeof adsk !== 'undefined' && typeof adsk.fusionSendData === 'function',
    state: {...state},
    inputs: all('input').map(el => ({id:el.id,value:el.value,checked:el.checked})),
    summary: q('#gw-grid-summary').textContent,
    dimensions: q('#gw-dimensions').textContent,
    padding: Object.fromEntries(['left','right','back','front'].map(k => [k,q('#gw-'+k).textContent])),
    pieces: q('#gw-piece-count').textContent,
    selectedPiece: q('#gw-piece-detail').textContent,
    validation: q('#gw-error').hidden ? null : q('#gw-error').textContent,
    generationDisabled: q('.gw-footer button').disabled,
    renderedCells: last ? last.nx * last.ny : 0,
    magnetHoleDiameter: num('magnet-diameter'),
    pressFit: q('#gw-press-fit').checked,
    previewCircleRadii: svg ? [...new Set([...svg.querySelectorAll('circle')].map(el => el.getAttribute('r')))] : [],
    renderedCircles: svg ? svg.querySelectorAll('circle').length : 0,
    hasDrawing: !!svg,
    profileSource: GRIDFINITY_CELL_PROFILES.source,
    skeletonOpenings: svg ? svg.querySelectorAll('[data-through-opening="skeleton"]').length : 0,
    continuousPieces: svg ? svg.querySelectorAll('[data-material="piece"]').length : 0,
    socketFloors: svg ? svg.querySelectorAll('[data-socket-floor]').length : 0,
    styling: {
      supportsLightDark: CSS.supports('color', 'light-dark(white, black)'),
      background: getComputedStyle(root).backgroundColor,
      text: getComputedStyle(root).color,
      inputBorder: getComputedStyle(q('#gw-width')).borderTopColor,
      selectedButton: getComputedStyle(q('[data-mode="' + state.mode + '"]')).backgroundColor,
      svgFills: svg ? [...new Set([...svg.querySelectorAll('[data-material] rect,[data-material] circle,[data-material] path')].map(el => getComputedStyle(el).fill))] : []
    },
    viewport: {width:window.innerWidth,height:window.innerHeight},
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
    errors: runtimeErrors.slice()
  };
}
function save() { send('previewChanged',report()); }
function restore(v) {
  if (!v || typeof v !== 'object') return;
  const m = v.modelContent || {};
  const allowed = {mode:['fit','grid'],style:['skeleton','solid'],view:['assembled','pieces']};
  for (const key of Object.keys(allowed)) if (allowed[key].includes(m[key])) state[key] = m[key];
  if (Number.isInteger(m.anchor) && m.anchor >= 0 && m.anchor <= 8) state.anchor = m.anchor;
  if (Number.isInteger(m.selected) && m.selected >= 0) state.selected = m.selected;
  const inputs = v.privateContent && v.privateContent.inputs;
  if (!Array.isArray(inputs)) return;
  inputs.forEach(i => {
    if (!i || typeof i.id !== 'string') return;
    const el = all('input').find(input => input.id === i.id);
    if (!el) return;
    if (el.type === 'checkbox') {
      if (typeof i.checked === 'boolean') el.checked = i.checked;
    } else if (typeof i.value === 'string' || typeof i.value === 'number') {
      const previous = el.value;
      el.value = String(i.value);
      if (!validNumber(el)) el.value = previous;
    }
  });
}

window.fusionJavaScriptHandler = {
  handle: function(action, data) {
    try {
      if(action==='capture3D')return JSON.stringify({report:report(),image:previewThree?.capture()});
      if (action === 'creationStatus') {
        const status=JSON.parse(data);
        creating=status.phase==='creating';
        q('#gw-create-status').textContent=status.message;
        q('#gw-create-status').classList.toggle('gw-error',status.phase==='error');
        render();
      } else if (action === 'setPreviewState') {
        restore(JSON.parse(data));
        render();
      } else if (action !== 'inspect') {
        return JSON.stringify({ok:false,error:'Unsupported preview action'});
      }
      return JSON.stringify({ok:true,report:report()});
    } catch (error) {
      return JSON.stringify({ok:false,error:String(error)});
    }
  }
};

render();
// Observe width only. Replacing the SVG must not synchronously redraw in a
// ResizeObserver delivery, which can cause the host to report a loop error.
let drawnWidth = q('#gw-drawing').clientWidth;
let resizePending = false;
function onResize() {
  const width = q('#gw-drawing').clientWidth;
  if (!width || Math.abs(width - drawnWidth) < 1 || resizePending) return;
  resizePending = true;
  const schedule = typeof window.requestAnimationFrame === 'function'
    ? callback => window.requestAnimationFrame(callback)
    : callback => window.setTimeout(callback, 0);
  schedule(() => {
    resizePending = false;
    drawnWidth = q('#gw-drawing').clientWidth;
    draw();
  });
}
if (typeof window.ResizeObserver === 'function') {
  const observer = new window.ResizeObserver(onResize);
  observer.observe(q('#gw-drawing'));
} else {
  window.addEventListener('resize', onResize);
}

window.addEventListener('pagehide',()=>previewThree?.dispose());
function ready() { send('ready',report()); }
if (document.readyState === 'complete') ready();
else window.addEventListener('load',ready,{once:true});
})();
