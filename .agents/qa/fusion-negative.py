"""Negative request checks in the disposable anchor; no model mutation expected."""
import sys,json,adsk.core,adsk.fusion
from pathlib import Path
OUT=Path(r'D:\Code Projects\GridfinityWorkshop\.agents\qa\runs\2026-10-04')
def run(_context):
 m=next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and str(getattr(m,'__file__','')).replace('\\','/').endswith('/GridfinityUIPreview/GridfinityUIPreview.py'))
 sys._gf_qa_anchor.activate();a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct)
 before=(a.documents.count,d.timeline.count,sum(c.bRepBodies.count for c in d.allComponents));rows=[]
 cases=[('bin oversized',m.catalog.request_creation,dict(sys._qa_catalog_state['configs']['standard'],family='standard',cols=7)),('invalid baseplate',m.request_creation,{'mode':'grid','columns':7,'rows':1}),('magazine overcapacity',m.catalog.request_creation,dict(sys._qa_catalog_state['configs']['magazine'],**sys._qa_catalog_state['cartridge'],family='magazine',cartridgeHeight=8,quantity=48)),('invalid pin bore',m.catalog.request_creation,dict(sys._qa_catalog_state['configs']['tests'],family='tests',testType='pin',testStart=2,testStep=.05,testCount=3))]
 def rejected(fn,data):
  try:fn(data)
  except ValueError as e:return str(e)
  raise AssertionError('Invalid request was accepted')
 for name,fn,data in cases:
  error=rejected(fn,data);assert m._pending is None and m.catalog._pending is None
  assert before==(a.documents.count,d.timeline.count,sum(c.bRepBodies.count for c in d.allComponents))
  rows.append({'case':name,'pass':True,'message':error})
 (OUT/'negative-requests.json').write_text(json.dumps(rows,indent=2),encoding='utf8');print(json.dumps(rows))
