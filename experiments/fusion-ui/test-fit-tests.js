const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {fitDefaults,upgradeFit,pinBores,testPlan}=require('./GridfinityUIPreview/fit-tests.js');
assert.deepEqual(pinBores(upgradeFit({pin:2})),[2,2,2.2,2.2]);
assert.deepEqual(pinBores({...fitDefaults}),[2,2,2,2]);
assert.equal(testPlan({...fitDefaults,testStart:NaN}).valid,false);
assert.equal(testPlan({...fitDefaults,testStart:.8,testStep:.1}).valid,false);
let c={...fitDefaults,testType:'spacing',testStart:1,testStep:1,testCount:3,channelColumns:3,channelRows:3,
 channelShape:'round',storedDiameter:6,storedClearance:.5,channelWidth:6,channelDepth:10};
assert.deepEqual(testPlan(c).samples.map(s=>[s.w,s.d]),[[25.5,31.5],[27.5,33.5],[29.5,35.5]]);
assert.equal(testPlan({...c,channelRows:1}).valid,false);
assert.equal(testPlan({...c,testStart:29,testStep:1}).valid,false);
assert.equal(testPlan({...c,channelColumns:5,channelRows:5,storedDiameter:30,testStart:30,testCount:1}).valid,false);
const nodes={},memory={};
const context={state:{family:'tests',configs:{tests:{...fitDefaults,testSelected:4,testSource:'clasp',testType:'pin'},clasp:{...fitDefaults,buckle:.2,grip:2,magnet:'press',diameter:6.08,magnetDepth:2.4,storedClearance:.5}}},families:{clasp:{name:'Clasp bin'}},
 $:id=>nodes[id]||(nodes[id]={value:'',textContent:''}),populate(){},escape:s=>String(s),localStorage:{setItem(k,v){memory[k]=v},getItem(k){return memory[k]}}};
vm.createContext(context);vm.runInContext(fs.readFileSync(require.resolve('./GridfinityUIPreview/fit-tests.js'),'utf8'),context);
vm.runInContext('applyTest()',context);
assert.equal(context.state.configs.clasp.pinAllowance,.3);
assert.equal(context.state.configs.tests.pinAllowance,.3);
context.$('#fit-profile-name').value='PETG / printer';vm.runInContext('fitProfileAction(true)',context);
assert.equal(JSON.parse(memory['gridfinity-fit-profiles-v1'])['PETG / printer'].pinAllowance,.3);
context.state.configs.tests.testPinTarget='bucklePinAllowance';context.state.configs.tests.testSelected=5;
vm.runInContext('applyTest()',context);
assert.equal(context.state.configs.clasp.pinOverrides,true);
assert.equal(context.state.configs.clasp.bodyPinAllowance,.3);
assert.equal(context.state.configs.clasp.bucklePinAllowance,.35);
console.log('Fit migration, bounded layouts, selection transfer and measured profile persistence passed.');
