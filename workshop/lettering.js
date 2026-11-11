/* The browser and Fusion use the same bundled SVG glyph outlines. */
(function(root){
 'use strict';
 function textSVG(text,font,height,maxWidth,fonts=root.WorkshopFonts){
  if(!fonts?.[font])throw Error('Choose Rubik or Atkinson.');
  if(typeof text!=='string'||!text.trim()||text.length>120)throw Error('Enter 1–120 characters of single-line text.');
  if(!Number.isFinite(height)||height<1||height>50||!Number.isFinite(maxWidth)||maxWidth<1||maxWidth>240)throw Error('Use a height of 1–50 mm and a maximum width of 1–240 mm.');
  const data=fonts[font],items=[],bounds=[];let cursor=0,previous='';
  for(const ch of text){
   const g=data.glyphs[ch];if(!g)throw Error(`Unsupported character ${ch}. Use Latin lettering or import outlined SVG artwork.`);
   cursor+=data.kerning[previous+ch]||0;
   if(g.bounds){const [a,b,c,d]=g.bounds;bounds.push([a+cursor,b,c+cursor,d]);items.push(`<path transform="translate(${cursor} 0)" d="${g.path}"/>`);}
   cursor+=g.advance;previous=ch;
  }
  if(!bounds.length)throw Error('Text has no printable outlines.');
  const x=Math.min(...bounds.map(b=>b[0])),y=Math.min(...bounds.map(b=>b[1]));
  const w=Math.max(...bounds.map(b=>b[2]))-x,h=Math.max(...bounds.map(b=>b[3]))-y,scale=Math.min(height/h,maxWidth/w);
  return {svg:`<svg xmlns="http://www.w3.org/2000/svg" width="${w*scale}mm" height="${h*scale}mm" viewBox="${x} ${y} ${w} ${h}"><g fill="black">${items.join('')}</g></svg>`,width:w*scale,height:h*scale,fontName:data.name};
 }
 function cleanSVG(source){
  if(typeof source!=='string'||new TextEncoder().encode(source).length>500000)throw Error('SVG must be smaller than 500 KB.');
  if(/<!\s*(DOCTYPE|ENTITY)/i.test(source))throw Error('Export a plain SVG without a document type or entities.');
  const doc=new DOMParser().parseFromString(source,'image/svg+xml');
  if(doc.querySelector('parsererror')||doc.documentElement.localName!=='svg')throw Error('Choose a valid SVG file.');
  const allowed=new Set(['svg','g','path','rect','circle','ellipse','polygon']),discard=new Set(['metadata','title','desc','defs','namedview']);
  const attrs=new Set(['viewBox','width','height','x','y','rx','ry','cx','cy','r','d','points','transform','fill','fill-rule','stroke','style','opacity','fill-opacity','stroke-width','version']);
  function visit(node){
   if(discard.has(node.localName)){node.remove();return;}
   if(!allowed.has(node.localName))throw Error(`SVG element ${node.localName} is unsupported. Outline text/strokes and expand artwork first.`);
   for(const attr of [...node.attributes]){
    if(attr.name.startsWith('on')||['href','filter','clip-path','mask'].includes(attr.localName))throw Error('SVG references, scripts, masks and effects are unsupported; expand artwork first.');
    if(attr.namespaceURI||!attrs.has(attr.name)){node.removeAttributeNode(attr);continue;}
    if(/url\(|javascript:|expression\(/i.test(attr.value))throw Error('SVG references are unsupported.');
   }
   for(const entry of (node.getAttribute('style')||'').split(';')){
    const i=entry.indexOf(':');if(i<0)continue;const key=entry.slice(0,i).trim(),value=entry.slice(i+1).trim();
    if(!['fill','fill-rule','stroke','stroke-width','opacity','fill-opacity'].includes(key))throw Error('Expand SVG appearances and remove CSS before importing.');
    node.setAttribute(key,value);
   }
   node.removeAttribute('style');
   if(!['none',''].includes((node.getAttribute('stroke')||'none').toLowerCase()))throw Error('Convert SVG strokes to filled outlines before importing.');
   if((node.getAttribute('fill')||'black').toLowerCase()==='none')throw Error('SVG must contain filled outlines.');
   if(['opacity','fill-opacity'].some(k=>node.hasAttribute(k)&&node.getAttribute(k)!=='1'))throw Error('Remove SVG transparency before importing.');
   if(node.localName==='path'){
    const d=(node.getAttribute('d')||'').trim(),parts=d.split(/[Mm]/).slice(1);
    if(!parts.length||parts.some(p=>!/[zZ]$/.test(p.trim())))throw Error('Close every SVG path before importing.');
    if(/[^MmZzLlHhVvCcSsQqTtAa0-9eE+.,\s-]/.test(d)||/nan|inf/i.test(d))throw Error('Invalid SVG path data.');
   }
   for(const child of [...node.children])visit(child);
  }
  visit(doc.documentElement);
  if(!doc.querySelector('path,rect,circle,ellipse,polygon'))throw Error('SVG has no outlined artwork.');
  return new XMLSerializer().serializeToString(doc.documentElement);
 }
 root.WorkshopLettering={textSVG,cleanSVG};
 if(typeof module!=='undefined')module.exports={textSVG,cleanSVG};
 if(typeof document==='undefined')return;
 const $=id=>document.getElementById(id),panel=$('lettering-panel');if(!panel)return;
 let imported='',current=null,busy=false,previousFocus=null;
 function settings(){return {source:$('lettering-source').value,text:$('lettering-text').value,font:$('lettering-font').value,
  height:Number($('lettering-height').value),maxWidth:Number($('lettering-width').value),operation:$('lettering-operation').value,
  depth:Number($('lettering-depth').value),offsetX:Number($('lettering-x').value),offsetY:Number($('lettering-y').value),rotation:Number($('lettering-rotation').value),svg:imported};}
 function update(){
  const c=settings();$('lettering-text-fields').hidden=c.source!=='text';$('lettering-svg-fields').hidden=c.source!=='svg';current=null;
  try{
   for(const input of panel.querySelectorAll('input[type=number]'))if(!input.checkValidity())throw Error('Enter values within the field limits.');
   let art;
   if(c.source==='text')art=textSVG(c.text,c.font,c.height,c.maxWidth);
   else{
    if(!imported)throw Error('Choose an outlined SVG file.');
    const sanitized=cleanSVG(imported);$('lettering-preview').innerHTML=sanitized;
    const svg=$('lettering-preview').firstElementChild;svg.setAttribute('width','100%');svg.setAttribute('height','130');
    const box=svg.getBBox();if(box.width<=0||box.height<=0||![box.x,box.y,box.width,box.height].every(Number.isFinite))throw Error('SVG has empty or invalid bounds.');
    const scale=Math.min(c.height/box.height,c.maxWidth/box.width);
    svg.setAttribute('viewBox',`${box.x} ${box.y} ${box.width} ${box.height}`);
    svg.setAttribute('width',`${box.width*scale}mm`);svg.setAttribute('height',`${box.height*scale}mm`);
    art={svg:new XMLSerializer().serializeToString(svg),width:box.width*scale,height:box.height*scale};
   }
   $('lettering-preview').innerHTML=art.svg;
   const svg=$('lettering-preview').firstElementChild;svg.setAttribute('width','100%');svg.setAttribute('height','130');svg.setAttribute('role','img');svg.setAttribute('aria-label','Actual lettering outlines');
   current=art;$('lettering-dimensions').textContent=`${art.width.toFixed(2)} × ${art.height.toFixed(2)} mm actual outline bounds${art.height<c.height-.01?' · reduced proportionally to fit maximum width':''}`;
   $('lettering-error').textContent='';
  }catch(error){$('lettering-preview').replaceChildren();$('lettering-dimensions').textContent='';$('lettering-error').textContent=error.message;}
  $('lettering-place').disabled=!current||busy;$('lettering-save-svg').disabled=!current||busy;
 }
 function open(){previousFocus=document.activeElement;panel.hidden=false;update();$('lettering-text').focus();}
 function close(){panel.hidden=true;previousFocus?.focus();}
 $('open-lettering').addEventListener('click',open);$('close-lettering').addEventListener('click',close);
 panel.addEventListener('keydown',event=>{if(event.key==='Escape')close();if(event.key==='Tab'){const items=[...panel.querySelectorAll('button,input,select,a')].filter(e=>!e.disabled&&!e.closest('[hidden]'));const first=items[0],last=items.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}});
 panel.addEventListener('input',event=>{if(event.target.type!=='file')update();});
 $('lettering-file').addEventListener('change',async event=>{
  imported='';try{const file=event.target.files[0];if(file){if(file.size>500000)throw Error('SVG must be smaller than 500 KB.');imported=cleanSVG(await file.text());}update();}
  catch(error){update();$('lettering-error').textContent=error.message;}
 });
 $('lettering-save-svg').addEventListener('click',async()=>{if(!current)return;try{const result=await root.FusionBridge.submit('saveLetteringSVG',{...settings(),svg:settings().source==='svg'?current.svg:undefined});$('lettering-status').textContent=result.cancelled?'Save cancelled.':'Outlined SVG saved.';}catch(error){$('lettering-status').textContent=error.message;}});
 $('lettering-place').addEventListener('click',async()=>{
  if(!current||busy)return;busy=true;update();
  try{await root.FusionBridge.submit('createLettering',settings());close();$('lettering-status').textContent='Click a planar face in Fusion at the center of your lettering, then confirm placement.';}
  catch(error){$('lettering-status').textContent=error.message;}finally{busy=false;update();}
 });
 $('lettering-coupon').addEventListener('click',async()=>{
  if(busy)return;busy=true;$('lettering-coupon').disabled=true;update();$('lettering-status').textContent='Creating two font comparison plates…';
  try{const result=await root.FusionBridge.submit('createFontCoupon',{});$('lettering-status').textContent=`Created ${result.result.plates} font comparison plates in a new design. Print flat with lettering up.`;}
  catch(error){$('lettering-status').textContent=error.message;}finally{busy=false;$('lettering-coupon').disabled=false;update();}
 });
 root.WorkshopLettering.status=message=>{$('lettering-status').textContent=message;};
})(typeof window==='undefined'?globalThis:window);
