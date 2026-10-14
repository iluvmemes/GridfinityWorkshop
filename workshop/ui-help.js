/* Progressive disclosure shared by Fusion palettes. No model operations. */
(()=>{
 const bin=!!document.getElementById('controls');
 function fold(section,title){if(!section)return;const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent=title;details.append(summary);while(section.firstChild)details.append(section.firstChild);section.append(details);}
 if(!bin){
  const section=document.getElementById('gw-print-settings'),fields=section.querySelector('.gw-fields'),heading=section.querySelector('.gw-heading'),limits=document.createElement('details'),summary=document.createElement('summary');
  limits.append(summary);heading.replaceWith(limits);limits.append(fields);document.querySelector('.gw-viewbar').append(heading.querySelector('.gw-switch'));
  const update=()=>{summary.textContent=`Printer: ${document.getElementById('gw-bed-width').value} × ${document.getElementById('gw-bed-depth').value} mm · max ${document.getElementById('gw-max-columns').value} × ${document.getElementById('gw-max-rows').value}`;};update();fields.addEventListener('input',update);
 }
 if(bin){
  for(const[id,title]of [['pin-fields','Pin fit'],['closure-fields','Clasp fit and grip'],['fit-profile-fields','Printer / material profiles']])fold(document.getElementById(id),title);
  const favorite=document.getElementById('favorites').closest('section');
  const name=document.getElementById('title').closest('label');favorite.prepend(name);fold(favorite,'Saved configurations');
  document.querySelector('.review').hidden=true;
  const intro=document.getElementById('family-description');intro.hidden=true;
  const errors=document.getElementById('errors');document.getElementById('controls').prepend(errors);
  document.getElementById('parts').closest('article').hidden=true;
  const parts=document.createElement('details');parts.innerHTML='<summary>Parts to create</summary>';const article=document.getElementById('parts').closest('article');article.hidden=false;article.replaceWith(parts);parts.append(article);document.getElementById('controls').append(parts);
 }
 // Help remains keyboard/click accessible, rather than relying on native title text.
 const selector=bin?'section p.note:not([role]):not(#channel-summary):not(#pin-summary):not(#accessory-summary):not(#lid-retention-summary),#height-note':'p.help-note';
 document.querySelectorAll(selector).forEach((note,i)=>{
  const help=document.createElement('details');help.className='field-help';const summary=document.createElement('summary');summary.textContent='ⓘ';summary.setAttribute('aria-label','Help: '+(note.closest('section')?.querySelector('h3,h2')?.textContent||'setting'));help.append(summary);note.replaceWith(help);help.append(note);help.hidden=note.hidden;new MutationObserver(()=>help.hidden=note.hidden).observe(note,{attributes:true,attributeFilter:['hidden']});
  help.addEventListener('mouseenter',()=>help.open=true);help.addEventListener('mouseleave',()=>{if(!help.contains(document.activeElement))help.open=false;});help.addEventListener('keydown',e=>{if(e.key==='Escape'){help.open=false;summary.focus();}});
 });
 const preview=document.querySelector(bin?'main':'.gw-view'),bar=preview.querySelector(bin?'.viewbar':'.gw-viewbar');
 // The viewport has one toolbar and a flexible canvas; supporting details belong in the form.
 if(bin){
  bar.append(document.getElementById('preview-3d-controls'));
  const controls=document.getElementById('controls'),first=controls.querySelector('section');first.querySelector('h2').after(document.getElementById('subtitle'));
  document.getElementById('preview-title').hidden=true;
  const dimensions=document.createElement('details');dimensions.innerHTML='<summary>Dimensions</summary>';dimensions.append(document.getElementById('metrics'));controls.append(dimensions);
  [...preview.children].filter(e=>e.matches('p.note')&&e.id!=='preview-3d-status').forEach(e=>e.hidden=true);
 }else{
  bar.append(document.getElementById('gw-fit-view'));
  document.querySelector('.gw-panel section').append(document.getElementById('gw-dimensions'));
  document.querySelector('.gw-caption').hidden=true;document.querySelector('.gw-preview-note').hidden=true;
 }
 preview.classList.add('fixed-preview');bar.classList.add('preview-toolbar');
 const expand=document.createElement('button');expand.textContent='Expand';expand.setAttribute('aria-expanded','false');bar.append(expand);expand.addEventListener('click',()=>{const active=document.body.classList.toggle('preview-expanded');expand.textContent=active?'Compact':'Expand';expand.setAttribute('aria-expanded',String(active));});
 document.querySelectorAll('input[type=number]').forEach(el=>{const wrapper=el.closest('.unit-input');if(wrapper){const sync=()=>{wrapper.classList.toggle('unit-invalid',el.getAttribute('aria-invalid')==='true');wrapper.classList.toggle('unit-disabled',el.disabled);};sync();new MutationObserver(sync).observe(el,{attributes:true,attributeFilter:['aria-invalid','disabled']});}el.addEventListener('blur',()=>{el.setAttribute('aria-invalid',String(!el.checkValidity()));let error=el.closest('label').querySelector('.field-error');if(!error){error=document.createElement('span');error.className='field-error';el.closest('label').append(error);}error.textContent=el.checkValidity()?'':`Use ${el.min} to ${el.max}.`;});el.addEventListener('input',()=>{if(el.checkValidity()){el.removeAttribute('aria-invalid');const error=el.closest('label').querySelector('.field-error');if(error)error.textContent='';}});});
})();
