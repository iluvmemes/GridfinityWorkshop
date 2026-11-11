'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {textSVG}=require('../../workshop/lettering.js');
const fonts=JSON.parse(fs.readFileSync(path.join(__dirname,'../../workshop/fonts/outlines.json'),'utf8'));
for(const font of Object.keys(fonts)){
 for(const text of ['Workshop','BO8 i','Aa O0 Il1 6.35','Café Ø6 ±0.1']){
  const a=textSVG(text,font,4,100,fonts),b=textSVG(text,font,4,a.width/2,fonts);
  assert.equal(a.height,4);assert.ok(Math.abs(b.height-2)<1e-9);assert.ok(Math.abs(b.width-a.width/2)<1e-9);
  assert.ok(!a.svg.includes('<text'));assert.ok(a.svg.includes('mm"'));assert.ok(a.svg.includes('<path'));
 }
}
for(const text of ['','   ','a\nb','Bolt 🔩','A'.repeat(121)])assert.throws(()=>textSVG(text,'rubik',4,100,fonts));
assert.throws(()=>textSVG('Sample','missing',4,100,fonts));
assert.throws(()=>textSVG('Sample','rubik',NaN,100,fonts));
// Compare browser layout with the independent Python entry point.
const {execFileSync}=require('node:child_process');
const expected=JSON.parse(execFileSync('python',['-c',"import json; from workshop.lettering import text_svg; print(json.dumps([text_svg('AV Workshop BO8',f,4,35) for f in ('rubik','atkinson')]))"],{cwd:path.join(__dirname,'../..'),encoding:'utf8'}));
for(const [i,font] of ['rubik','atkinson'].entries()){
 const actual=textSVG('AV Workshop BO8',font,4,35,fonts);
 assert.ok(Math.abs(actual.width-expected[i].width)<1e-9);assert.ok(Math.abs(actual.height-expected[i].height)<1e-9);
}
console.log('PASS: outlined browser layout, dimensions, invalid input and Python/browser parity');
