(function(root){
 'use strict';
 const colors=root.WorkshopFilaments.colors;
 function refresh(c){
  for(const key of ['lidColor','lidLabelColor']){
   for(const button of document.querySelectorAll(`[data-color-target="${key}"]`))button.setAttribute('aria-pressed',String(button.dataset.color===c[key]));
   const selected=colors.find(color=>color.id===c[key]);
   document.getElementById(key+'-name').textContent=selected?selected.name:'';
  }
  document.getElementById('lid-label-color').hidden=!['raised','embedded'].includes(c.lidLabelMode);
 }
 for(const key of ['lidColor','lidLabelColor']){
  const select=document.getElementById(key),group=document.getElementById(key+'-swatches');
  for(const color of colors){
   const option=document.createElement('option');option.value=color.id;option.textContent=color.name;select.append(option);
   const button=document.createElement('button');button.type='button';button.className='filament-swatch';button.dataset.colorTarget=key;button.dataset.color=color.id;
   button.style.setProperty('--swatch-color',color.hex);button.title=color.name;button.setAttribute('aria-label',button.title);button.setAttribute('aria-pressed','false');
   button.addEventListener('click',()=>{select.value=color.id;select.dispatchEvent(new Event('input',{bubbles:true}));});group.append(button);
  }
 }
 document.getElementById('export-lid-3mf').addEventListener('click',async event=>{
  const button=event.currentTarget,status=document.getElementById('lid-export-status');button.disabled=true;
  try{const reply=await root.FusionBridge.submit('exportLid3MF',{});status.textContent=reply.cancelled?'Export cancelled.':`Exported ${reply.result.parts} named color part${reply.result.parts===1?'':'s'}. Map them to your loaded filaments in Bambu Studio.`;}
  catch(error){status.textContent=error.message;}finally{button.disabled=false;}
 });
 root.WorkshopSwatches={refresh};
})(window);
