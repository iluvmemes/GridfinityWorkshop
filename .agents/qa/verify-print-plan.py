"""Fusion MCP: execute this file, then run(context). Owns and closes only its QA document."""
import sys, types, importlib, json, math
from pathlib import Path
import adsk.core, adsk.fusion
ROOT=Path(r'D:/Code Projects/GridfinityWorkshop')

def verify(overrides=None):
    package=types.ModuleType('qa_print_plan');package.__path__=[str(ROOT/'workshop')];sys.modules[package.__name__]=package
    g=importlib.import_module('qa_print_plan.generation')
    app=adsk.core.Application.get();previous=app.activeDocument
    doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.name='QA print plan disposable'
    results=[]
    try:
        design=adsk.fusion.Design.cast(app.activeProduct)
        data=dict(mode='grid',style='skeleton',columns=6,rows=6,anchor=4,magnets=True,screws=False,magnetDiameter=6.08,magnetDepth=2.4,bedWidth=220,bedDepth=220,maxPlateColumns=3,maxPlateRows=3,planningPreference='repeat',preferSymmetry=True)
        data.update(overrides or {})
        outputs={}
        for mode in ('unique','layout'):
            r=g.generate(dict(data,outputMode=mode));outputs[mode]=r
            bodies=[b for c in design.allComponents for b in c.bRepBodies if b.name.startswith(r['layoutId']+' ')]
            assert len(bodies)==r['pieces'],(r,len(bodies))
            if mode=='unique':
                weighted=sum(b.volume*json.loads(b.attributes.itemByName('GridfinityWorkshop','piece').value)['printQuantity'] for b in bodies)
                assert all('Print ' in b.name for b in bodies)
                representatives={json.loads(b.attributes.itemByName('GridfinityWorkshop','piece').value)['typeId']:b for b in bodies}
            else:
                assert abs(sum(b.volume for b in bodies)-weighted)<1e-6
                manager=adsk.fusion.TemporaryBRepManager.get()
                for b in bodies:
                    p=json.loads(b.attributes.itemByName('GridfinityWorkshop','piece').value)
                    copy=manager.copy(representatives[p['typeId']])
                    transform=adsk.core.Matrix3D.create();transform.setToRotation(math.radians(p['rotation']),adsk.core.Vector3D.create(0,0,1),adsk.core.Point3D.create(0,0,0));manager.transform(copy,transform)
                    a=copy.boundingBox.minPoint;t=b.boundingBox.minPoint
                    transform=adsk.core.Matrix3D.create();transform.translation=adsk.core.Vector3D.create(t.x-a.x,t.y-a.y,t.z-a.z);manager.transform(copy,transform)
                    assert manager.booleanOperation(copy,manager.copy(b),adsk.fusion.BooleanTypes.IntersectionBooleanType)
                    assert abs(copy.volume-b.volume)<1e-6,(p,copy.volume,b.volume)
            results.append(r)
        # Full array volume must equal the original unsplit generator.
        legacy=dict(data,bedWidth=350,bedDepth=350,maxPlateColumns=6,maxPlateRows=6)
        legacy.pop('planningPreference');legacy.pop('preferSymmetry')
        r=g.generate(legacy)
        bodies=[b for c in design.allComponents for b in c.bRepBodies if b.name.startswith(r['layoutId']+' ')]
        assert abs(sum(b.volume for b in bodies)-weighted)<1e-6, (sum(b.volume for b in bodies), weighted)
        assert all(int(f.healthState)==0 for c in design.allComponents for f in c.features)
        out=ROOT/'.agents/qa/runs/print-plan';out.mkdir(parents=True,exist_ok=True)
        (out/('native-'+str(data['anchor'])+'.json')).write_text(json.dumps(results,indent=2),encoding='utf-8')
        print('PASS: unique/full geometry, rotated interchangeability, weighted volumes, legacy envelope and healthy timeline',[(r['pieces'],r['printCount']) for r in results])
    finally:
        doc.close(False)
        if previous: previous.activate()

def run(_context):
    verify()
    verify(dict(mode='fit',width=260,depth=180,clearance=.5,anchor=0,screws=True))
