"""Run through Fusion MCP: isolated documents, actual sliding and stacking checks."""
import importlib,json,sys
from pathlib import Path
import adsk.core,adsk.fusion

def run(_context):
    app=adsk.core.Application.get();previous=app.activeDocument
    originals=[(doc,doc.name,doc.isModified) for doc in app.documents]
    m=next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and str(getattr(m,'__file__','')).replace('\\','/').endswith('/workshop/app.py'))
    g=importlib.import_module(m.generation.__package__+'.bin_generation')
    cfg=dict(family='standard',title='Dovetail verification',cols=1,rows=1,height=2,interior='open',rim=False,
        dovetailLid=True,scoop=False,label=False,magnet='press',magnetDepth=2.4,divX=2,divY=2,
        channelShape='round',storedDiameter=6,storedClearance=.5,channelWidth=6,channelDepth=10,
        channelColumns=3,channelRows=2)
    cases=[{},dict(rim=True),dict(cols=6,rows=6,height=20,rim=True,interior='divided',divX=6,divY=6),
        dict(cols=1,rows=6,rim=True,interior='magnets'),dict(cols=6,rows=1,interior='magnets',channelShape='rectangle'),
        dict(cols=2,rows=2,rim=True,interior='magnets',channelShape='square',magnet='off')]
    mgr=adsk.fusion.TemporaryBRepManager.get();results=[]
    def shifted(body,x=0,y=0,z=0):
        copy=mgr.copy(body);t=adsk.core.Matrix3D.create();t.translation=adsk.core.Vector3D.create(x/10,y/10,z/10)
        assert mgr.transform(copy,t);return copy
    def overlap(a,b):
        copy=mgr.copy(a);assert mgr.booleanOperation(copy,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
        return copy.volume*1000
    for index,change in enumerate(cases):
        c=g.validate({**cfg,**change})
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.name='Disposable dovetail verification'
        d=adsk.fusion.Design.cast(app.activeProduct)
        s=g.sketch(d.rootComponent,'Existing overlapping body','0 mm');g.rectangle(s,0,0,30,30)
        sentinel=g.extrude(d.rootComponent,s,'160 mm','Existing body').bodies.item(0);volume=sentinel.volume
        result=g.generate(c);body=d.findEntityByToken(result['bodyToken'])[0];lid=d.findEntityByToken(result['lidToken'])[0]
        assert abs(sentinel.volume-volume)<1e-9
        assert body.lumps.count==lid.lumps.count==1 and body.isSolid and lid.isSolid
        assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features)
        depths=[0,-.1,-c['depthMM']/4,-c['depthMM']/2,-c['depthMM']-1]
        clearances=[overlap(body,shifted(lid,y=y)) for y in depths]
        assert max(clearances)<1e-6,(index,clearances)
        assert overlap(body,shifted(lid,y=1))>1,'Missing rear stop'
        assert overlap(body,shifted(lid,z=1))>1,'Dovetail fails to retain upward motion'
        assert abs(lid.boundingBox.maxPoint.z*10-c['overallMM'])<1e-5
        # Verify fixed plate thickness from the native extrusion, not just recipe data.
        plate=next(f for comp in d.allComponents for f in comp.features if f.name.endswith(' - Lid plate 3 mm'))
        assert abs(plate.extentOne.distance.value*10-3)<1e-6
        if c['rim']:
            for x,y in [(0,0),(c['cols']-1,c['rows']-1)]:
                foot=shifted(g.preset('bin-foot.smt'),x=x*42,y=y*42,z=c['heightMM']+5.6+5)
                assert overlap(lid,foot)<1e-6,'Stacking lip interferes with standard foot'
        if index<2:
            d.userParameters.itemByName(result['heightParameter']).expression='35 mm';d.computeAll()
            assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features)
            assert abs(lid.boundingBox.maxPoint.z*10-(35+5.6+(3.8 if c['rim'] else 0)))<1e-6
            assert overlap(body,lid)<1e-6
        result.pop('bodyToken');result.pop('lidToken');result.update(slidingOverlapMM3=clearances,
            rearStopVerified=True,liftRetentionVerified=True,fixedPlateMM=3,existingBodyUnchanged=True)
        results.append(result);doc.close(False)
    previous.activate()
    assert all(doc.isValid and doc.name==name and doc.isModified==modified for doc,name,modified in originals)
    folder=Path(r'D:\Code Projects\GridfinityWorkshop\.agents\qa\runs\local\dovetail');folder.mkdir(exist_ok=True)
    (folder/'verified-generation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results))
