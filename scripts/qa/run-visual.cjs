const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),out=path.resolve(process.argv[2]||'outputs/full-qa/current');
fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'chrome'}),rows=[],errors=[];
 const page=await browser.newPage({reducedMotion:'reduce'});page.on('pageerror',e=>errors.push(e.message));
 try{
  for(const [width,height] of [[1000,780],[480,742],[360,540]]){
   await page.setViewportSize({width,height});
   await page.goto('file:///'+root.replaceAll('\\','/')+'/workshop/catalog.html');
   await page.addScriptTag({path:path.join(__dirname,'visual-cases.js')});
   const ids=await page.evaluate(()=>qaVisualCases.map(c=>c.id));
   for(const id of ids){
    const row=await page.evaluate(id=>qaVisualRun(id),id);row.viewport=[width,height];
    row.screenshot=`${width}-${id}.png`;await page.screenshot({path:path.join(out,row.screenshot)});rows.push(row);
    console.log(row.pass?'PASS':'FAIL',width,id,row.failures.join('; '));
   }
   await page.click('#open-lettering');await page.screenshot({path:path.join(out,`${width}-lettering.png`)});
   rows.push({id:'lettering-dialog',viewport:[width,height],pass:await page.locator('.lettering-card').isVisible()});
   await page.goto('file:///'+root.replaceAll('\\','/')+'/workshop/palette.html');
   const set=async(id,value)=>page.locator('#gw-'+id).evaluate((e,v)=>{if(e.type==='checkbox')e.checked=v;else e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));},value);
   const steps=[['default',async()=>{}],['solid',()=>page.click('[data-style="solid"]')],['grid1',async()=>{await page.click('[data-mode="grid"]');await set('columns',1);await set('rows',1);}],['grid6',async()=>{await set('columns',6);await set('rows',6);}],['press-screws',async()=>{await set('press-fit',true);await set('screws',true);}],['print',()=>page.click('#gw-next')],['layout',()=>page.click('#gw-view-mode')],['return3d',()=>page.click('#gw-view-mode')]];
   for(const [id,fn]of steps){await fn();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));const r=await page.evaluate(()=>JSON.parse(fusionJavaScriptHandler.handle('inspect','{}')).report);const pass=!r.errors.length&&!r.validation&&r.threePreview?.ready&&!r.threePreview.error&&await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);rows.push({id:'baseplate-'+id,viewport:[width,height],pass,report:r});await page.screenshot({path:path.join(out,`${width}-baseplate-${id}.png`)});console.log(pass?'PASS':'FAIL',width,'baseplate-'+id);}
  }
 }finally{await browser.close();fs.writeFileSync(path.join(out,'visual-results.json'),JSON.stringify({rows,errors},null,2));}
 const failures=rows.filter(r=>!r.pass);console.log(`${rows.length} cases; ${failures.length} failures; ${errors.length} runtime errors`);process.exitCode=failures.length||errors.length?1:0;
})().catch(e=>{console.error(e);process.exitCode=1;});
