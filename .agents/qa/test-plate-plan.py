"""Planner parity, coverage, exact type matching and practical large-drawer cases."""
import sys,json,subprocess,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from workshop.request import validate
from workshop.plate_plan import signature,rotate,key
base=dict(mode='fit',style='skeleton',width=1242.06,depth=535.94,clearance=.5,anchor=4,magnets=True,screws=False,magnetDiameter=6.08,magnetDepth=2.4,bedWidth=220,bedDepth=220,maxPlateColumns=5,maxPlateRows=5)
cases=[]
for mode in ('repeat','plates','unique'):
 for anchor in (0,4,8):
  for dims in ((230,190),(1242.06,535.94),(2500,2500)):
   cases.append(validate(dict(base,planningPreference=mode,preferSymmetry=True,outputMode='unique',anchor=anchor,width=dims[0],depth=dims[1])))
js="const p=require('./workshop/plate-plan.js');let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>console.log(JSON.stringify(JSON.parse(s).map(x=>p.plan(x)))));"
result=subprocess.run(['node','-e',js],input=json.dumps(cases),text=True,capture_output=True,cwd=ROOT,check=True)
for s,j in zip(cases,json.loads(result.stdout)):
 for field in ('pieces','plateTypes','xSections','ySections','minimumPlateCount'): assert s[field]==j[field],field
 assert sum(p['columns']*p['rows'] for p in s['pieces'])==s['columns']*s['rows']
 assert math.isclose(sum((p['x1']-p['x0'])*(p['y1']-p['y0']) for p in s['pieces']),s['widthMM']*s['depthMM'])
 assert sum(t['quantity'] for t in s['plateTypes'])==len(s['pieces'])
 for p in s['pieces']:
  assert p['x1']-p['x0']<=s['bedWidth']+1e-8 and p['y1']-p['y0']<=s['bedDepth']+1e-8
  t=s['plateTypes'][p['typeIndex']];sig=signature(t)
  for _ in range(p['rotation']//90):sig=rotate(sig)
  assert key(sig)==key(signature(p))
print('PASS: 27 planner cases, Python/JS parity, coverage, grouping and printer constraints')
