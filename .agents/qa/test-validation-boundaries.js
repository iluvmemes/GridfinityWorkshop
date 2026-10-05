const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'../../workshop');
const palette=fs.readFileSync(path.join(root,'palette.js'),'utf8');
const values={'max-columns':6,'max-rows':6,width:125,depth:83.5,clearance:0,'bed-width':70,'bed-depth':100,'magnet-diameter':0};
const ctx={state:{style:'solid',mode:'fit',anchor:4},num:id=>values[id],q:()=>({checked:false}),all:()=>[]};vm.createContext(ctx);
vm.runInContext(palette.slice(palette.indexOf('function bedChunk('),palette.indexOf('function render(')),ctx);
let result=vm.runInContext('calculate()',ctx);
assert.deepEqual(Array.from(result.pieces,p=>p.x1-p.x0),[62.75,62.25]);
for(let anchor=0;anchor<9;anchor++)for(const bed of [60,70,84,100,125]){
 ctx.state.anchor=anchor;values['bed-width']=values['bed-depth']=bed;
 result=vm.runInContext('calculate()',ctx);
 const left=41.5*(anchor%3)/2,feasible=Math.max(42+left,83-left)<=bed;
 assert.equal(!result.error,feasible);
 if(feasible){assert.ok(result.pieces.every(p=>p.x1-p.x0<=bed&&p.y1-p.y0<=bed));assert.equal(result.pieces.reduce((sum,p)=>sum+(p.x1-p.x0)*(p.y1-p.y0),0),125*83.5);}
}
ctx.state.anchor=4;
values.width=1242.06;values.depth=535.94;values.clearance=.5;
for(const [bed,count] of [[220,24],[256,18],[350,10]]){
 values['bed-width']=values['bed-depth']=bed;result=vm.runInContext('calculate()',ctx);
 assert.equal(result.pieces.length,count);assert.equal(result.nx*result.ny,348);
 assert.ok(result.pieces.every(p=>p.cols<=6&&p.rows<=6&&p.x1-p.x0<=bed+1e-8&&p.y1-p.y0<=bed+1e-8));
}
for(const [cols,rows] of [[5,5],[2,5],[5,2],[1,1]]){
 values['max-columns']=cols;values['max-rows']=rows;
 result=vm.runInContext('calculate()',ctx);
 assert.ok(result.pieces.every(p=>p.cols<=cols&&p.rows<=rows));
 assert.equal(result.pieces.reduce((n,p)=>n+p.cols*p.rows,0),348);
 if(cols===5&&rows===5)assert.equal(result.pieces.length,18);
}
const catalog=fs.readFileSync(path.join(root,'catalog.js'),'utf8'),nodes={};
const c={cols:1,rows:1,height:6,drawer:85,interior:'magnets',dovetailLid:true,lidRetention:'magnet',lidMagnetSize:'6',lidMagnetFit:'press',scoop:false,label:false,rim:false,channelShape:'round',storedDiameter:6,storedClearance:.5,channelColumns:5,channelRows:5,channelGapX:1};
const ui={window:{},console,AbortController,document:{querySelectorAll:()=>[]},$:id=>nodes[id]||(nodes[id]={}),state:{family:'standard',configs:{standard:c}},c,f:'standard',v:{w:41.5,d:41.5},calculations:()=>({w:41.5,d:41.5}),pinBores:()=>[],creating:false,fmt:String,retentionSummary:()=>''};vm.createContext(ui);
for(const file of ['vendor/three-runtime.js','workshop-three.js'])vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),ui);
ui.WorkshopThree=ui.window.WorkshopThree;ui.planMagnetChannels=ui.window.planMagnetChannels=require(path.join(root,'channel-layout.js')).planMagnetChannels;
vm.runInContext(catalog.slice(catalog.indexOf('function updateCreation('),catalog.indexOf('function accessoryLayout(')),ui);
const validation=catalog.slice(catalog.indexOf('const issues=[];'),catalog.indexOf("$('#lid-retention-summary')"));
for(const columns of [5,1,5,1]){
 c.channelColumns=c.channelRows=columns;
 vm.runInContext('{'+validation+'updateCreation(issues,retentionValid);}',ui);
 assert.equal(nodes['#create-bin'].disabled,columns===5);
}
console.log('Padding partition, retention collision and Create recovery regressions passed.');
