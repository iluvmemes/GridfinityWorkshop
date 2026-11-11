const assert=require('node:assert/strict');
const {planMagnetChannels:plan}=require('../../workshop/channel-layout.js');
const base={channelShape:'round',storedDiameter:6,storedClearance:.5,channelWidth:6,channelDepth:10,channelColumns:8,channelRows:4};
for(const shape of ['round','square','rectangle']){
 const c={...base,channelShape:shape,channelRows:3};const p=plan(c,{w:83.5,d:41.5},'clasp');
 assert.equal(p.valid,true);assert.equal(p.positions.length,24);
 assert.ok(Math.abs(p.x0-(83.5-(p.x0+p.usedWidth)))<1e-10);
 assert.ok(Math.abs(p.y0-(41.5-(p.y0+p.usedDepth)))<1e-10);
 assert.ok(p.x0>=8.1);assert.ok(p.y0>=2);
 assert.equal(plan({...c,channelColumns:p.maxColumns+1},{w:83.5,d:41.5},'clasp').valid,false);
 assert.equal(plan({...c,channelRows:p.maxRows+1},{w:83.5,d:41.5},'clasp').valid,false);
}
assert.equal(plan({...base,channelColumns:2.5},{w:83.5,d:41.5},'clasp').valid,false);
assert.equal(plan({...base,channelColumns:1,channelRows:1},{w:10.5,d:10.5},'standard').valid,true);
assert.equal(plan({...base,channelColumns:1,channelRows:1},{w:10.49,d:10.5},'standard').valid,false);
assert.equal(plan({...base,channelRows:1},{w:80.2,d:17.5},'cartridge').valid,true);
console.log('Round, square, rectangle, centering, exact-fit and overflow checks passed.');
