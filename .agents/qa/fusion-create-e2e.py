"""Native palette Create-button E2E helpers. Load via Fusion MCP.
prepare(family), then inspect in a separate MCP call with finish(family).
For in-document families: finish; execute UndoCommand; check_undo;
execute RedoCommand; check_redo; cleanup. Imported designs close via cleanup.
"""
from pathlib import Path
import adsk.core,adsk.fusion,sys,json,time
OUT=Path(getattr(sys,'_gf_qa_out',r'D:\Code Projects\GridfinityWorkshop\.agents\qa\runs\local'))
OUT.mkdir(parents=True,exist_ok=True)
def module():
 return next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and str(getattr(m,'__file__','')).replace('\\','/').endswith('/workshop/app.py'))
def measure():
 a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct)
 return dict(document=a.activeDocument.name,bodies=[b.name for c in d.allComponents for b in c.bRepBodies],timeline=d.timeline.count,groups=[g.name for g in d.timeline.timelineGroups],unhealthy=[f.name for c in d.allComponents for f in c.features if not f.isSuppressed and int(f.healthState)!=0],sketches=[{'name':s.name,'constrained':s.isFullyConstrained} for c in d.allComponents for s in c.sketches])
def request_ready():
 m=module();m.catalog._last_response=None
 adsk.core.Application.get().userInterface.palettes.itemById(m.catalog.PALETTE_ID).sendInfoToHTML('qaPing','{}')
 print('Await qaPing response in a later MCP call before prepare')
def prepare(family):
 a=adsk.core.Application.get();m=module()
 if family!='baseplate':
  ready=(m.catalog._last_response or {}).get('qa',{})
  palette=a.userInterface.palettes.itemById(m.catalog.PALETTE_ID)
  assert ready.get('kind')=='ready' and ready.get('handler')=='catalog-harness-v6', 'Request qaPing and await the actual ready acknowledgement before prepare'
  assert ready['url']==palette.htmlFileURL, 'Ready acknowledgement belongs to a different page'
  sys._qa_catalog_state=ready['state']
 doc=a.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.name='QA E2E '+family
 d=adsk.fusion.Design.cast(a.activeProduct);g=m.catalog.bin_generation
 s=g.sketch(d.rootComponent,'QA sentinel sketch','0 mm');g.rectangle(s,0,0,30,30)
 body=g.extrude(d.rootComponent,s,'40 mm','QA existing solid').bodies.item(0);body.name='QA existing solid'
 before=measure();sys._qa_e2e={'family':family,'doc':doc,'before':before,'sentinel':body,'volume':body.volume,'start':time.perf_counter()}
 m.catalog._last_creation=None;m._last_creation=None
 state=json.loads(json.dumps(getattr(sys,'_qa_catalog_state',{'configs':{}})));state['family']=family;state['view']='3d';c=state['configs'].get(family)
 if c:
  c.update(title='QA '+family,cols=2,rows=1,height=2 if family=='magazine' else 6,drawer=200,interior='solid' if family=='blank' else 'open',scoop=False,label=False,dovetailLid=family=='standard',quantity=2,testType='pin',testStart=.15,testStep=.05,testCount=3)
 if family=='baseplate':a.userInterface.palettes.itemById(m.PALETTE_ID).sendInfoToHTML('qaCreate','{}')
 else:a.userInterface.palettes.itemById(m.catalog.PALETTE_ID).sendInfoToHTML('qaCreate',json.dumps(state))
 print('Create button dispatched',family)
def finish(family):
 a=adsk.core.Application.get();m=module();t=sys._qa_e2e
 result=m._last_creation if family=='baseplate' else m.catalog._last_creation
 assert result,'No creation result: '+str(m.catalog._last_response)
 after=measure();assert not after['unhealthy'],after
 assert t['sentinel'].isValid and abs(t['sentinel'].volume-t['volume'])<1e-9
 assert len(after['bodies'])>(1 if a.activeDocument==t['doc'] else 0)
 t['createdDoc']=a.activeDocument;t['after']=after
 row={'family':family,'result':{k:v for k,v in result.items() if 'Token' not in k},'before':t['before'],'after':after,'sentinelPreserved':True,'route':'synthetic DOM click -> HTML event -> production request -> native command/import'}
 (OUT/('create-'+family+'.json')).write_text(json.dumps(row,indent=2),encoding='utf8')
 print(json.dumps({'family':family,'bodies':after['bodies'],'groups':after['groups'],'seconds':result.get('seconds'),'newDocument':a.activeDocument!=t['doc']}))
def check_undo():
 t=sys._qa_e2e;now=measure();assert now['bodies']==t['before']['bodies'] and now['timeline']==t['before']['timeline'],now
 t['undo']=True;print('Single Undo restored sentinel-only design')
def check_redo():
 t=sys._qa_e2e;now=measure();assert sorted(now['bodies'])==sorted(t['after']['bodies']) and now['timeline']==t['after']['timeline'],now
 p=OUT/('create-'+t['family']+'.json');r=json.loads(p.read_text());r.update(singleUndoVerified=t['undo'],redoVerified=True);p.write_text(json.dumps(r,indent=2),encoding='utf8');print('Redo restored generated bodies')
def cleanup():
 t=sys._qa_e2e
 if t.get('createdDoc') and t['createdDoc']!=t['doc']:t['createdDoc'].close(False)
 t['doc'].close(False);sys._gf_qa_anchor.activate()
