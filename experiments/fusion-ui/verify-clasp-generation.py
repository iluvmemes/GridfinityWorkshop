"""Run through Fusion MCP. Uses disposable imported designs, never source documents."""
import importlib,itertools,json,sys
from pathlib import Path
import adsk.core,adsk.fusion


def run(_context: str):
    app=adsk.core.Application.get();previous=app.activeDocument
    module=next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and
        str(getattr(m,'__file__','')).replace('\\','/').endswith('/GridfinityUIPreview/GridfinityUIPreview.py'))
    generator=importlib.import_module(module.generation.__package__+'.clasp_generation')
    cfg=dict(family='clasp',title='Clasp verification',cols=2,rows=1,height=6,interior='open',rim=False,
             scoop=False,label=False,buckle=.2,pin=2,grip=2,magnet='press',diameter=6.08,magnetDepth=2.4,
             divX=2,divY=2,channelShape='round',storedDiameter=6,storedClearance=.5,
             channelWidth=6,channelDepth=10,channelColumns=8,channelRows=2)
    cases=[{},dict(interior='divided',cols=6,rows=6,height=20,buckle=.6,pin=2.5,grip=4),
           dict(interior='magnets',channelShape='round'),dict(interior='magnets',channelShape='square'),
           dict(interior='magnets',channelShape='rectangle'),dict(interior='magnets',channelColumns=1,channelRows=1,magnet='off',grip=2,pin=1.8,buckle=0)]
    results=[];mgr=adsk.fusion.TemporaryBRepManager.get()
    for settings in cases:
        c={**cfg,**settings};result=generator.generate(c);doc=app.activeDocument
        d=adsk.fusion.Design.cast(app.activeProduct)
        bodies=[b for comp in d.allComponents for b in comp.bRepBodies]
        overlaps=[]
        for a,b in itertools.combinations(bodies,2):
            temp=mgr.copy(a);assert mgr.booleanOperation(temp,mgr.copy(b),adsk.fusion.BooleanTypes.IntersectionBooleanType)
            overlaps.append(temp.volume*1000)
        assert max(overlaps)<1e-6,overlaps
        result['overlapMM3']=overlaps
        seed=next(s for comp in d.allComponents for s in comp.sketches if 'seed' in s.name)
        assert seed.isFullyConstrained
        result['fullyConstrainedInterior']=True
        if not settings:
            # Grid and height edits must keep the cavity rectangular and centered.
            d.timeline.markerPosition=0
            for key,value in [('CellsL','3'),('CellsW','2'),('HeightUnits','8')]:d.userParameters.itemByName(key).expression=value
            d.timeline.moveToEnd();d.computeAll()
            points=[p.geometry for p in seed.sketchPoints if p!=seed.originPoint]
            xs=[p.x for p in points];ys=[p.y for p in points]
            assert abs(max(xs)+min(xs))<1e-6 and abs(max(ys)+min(ys))<1e-6
            assert abs((max(xs)-min(xs))*10-(3*42-.5-12.2-4))<1e-6
            assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features if not f.isSuppressed)
            result['gridHeightEditVerified']=True
        results.append(result);doc.close(False)
        Path(r'D:\Code Projects\GridfinityWorkshop\experiments\fusion-ui\clasp\verified-generation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    previous.activate()
    Path(r'D:\Code Projects\GridfinityWorkshop\experiments\fusion-ui\clasp\verified-generation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results))
