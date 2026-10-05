"""Fusion native verification; creates and closes only disposable test documents."""
import importlib,itertools,json,math,sys
from pathlib import Path
import adsk.core,adsk.fusion

def run(_context):
    app=adsk.core.Application.get();previous=app.activeDocument
    originals=[(doc,doc.name,doc.isModified) for doc in app.documents]
    m=next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and str(getattr(m,'__file__','')).replace('\\','/').endswith('/workshop/app.py'))
    pkg=m.generation.__package__;g=importlib.import_module(pkg+'.magazine_generation');cg=importlib.import_module(pkg+'.cartridge_generation')
    bins=g.bins;mgr=adsk.fusion.TemporaryBRepManager.get();P=adsk.core.Point3D.create
    default=dict(family='magazine',title='Magazine verification',cols=2,rows=1,height=4,cartLength=68,cartWidth=17.5,
        cartridgeHeight=8,slot=.3,quantity=2,orientation='0',magnet='press',magnetDepth=2.4)
    cases=[{},dict(height=2,magazineCutouts=False),dict(height=2,cols=1,rows=2,orientation='90',magazineCutouts=False),dict(cols=1,rows=2,orientation='90'),dict(quantity=1,slot=.1,magnet='off'),
        dict(cartridgeHeight=4,height=3),dict(cols=6,rows=6,quantity=12,slot=.8,orientation='90'),
        dict(cols=6,rows=6,cartLength=220,cartWidth=80,cartridgeHeight=20,height=19,quantity=3,magnet='custom',diameter=8,magnetDepth=3),
        dict(cols=6,rows=6,cartLength=30,cartWidth=12,quantity=48,height=2)]
    results=[];cache={}
    for index,change in enumerate(cases):
        c=g.validate({**default,**change});key=(c['cartLength'],c['cartWidth'],c['cartridgeHeight'])
        if key not in cache:
            cg.generate(dict(family='cartridge',title='Magazine fit reference',cartLength=key[0],cartWidth=key[1],height=key[2],
                interior='open',buckle=.2,grip=4,pinDiameter=1.75,pinAllowance=.25,pinOverrides=False))
            d=adsk.fusion.Design.cast(app.activeProduct)
            cache[key]=[mgr.copy(b) for comp in d.allComponents for b in comp.bRepBodies]
            app.activeDocument.close(False)
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.name='Disposable magazine verification'
        d=adsk.fusion.Design.cast(app.activeProduct)
        # An existing overlapping solid must not be cut by the magazine workflow.
        s=bins.sketch(d.rootComponent,'Existing solid test','0 mm');bins.rectangle(s,0,0,30,30)
        sentinel=bins.extrude(d.rootComponent,s,'40 mm','Existing solid').bodies.item(0);sentinel.name='Existing solid'
        volume=sentinel.volume
        result=g.generate(c);body=d.findEntityByToken(result['bodyToken'])[0]
        assert abs(sentinel.volume-volume)<1e-9
        assert body.isSolid and body.lumps.count==1
        assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features)
        overlaps=[]
        for seat in c['seats']:
            t=adsk.core.Matrix3D.create()
            t.setToRotation(math.pi/2 if c['orientation']=='90' else 0,adsk.core.Vector3D.create(0,0,1),P(0,0,0))
            t.translation=adsk.core.Vector3D.create((seat['x']+seat['w']/2)/10,(seat['y']+seat['d']/2)/10,.7)
            for original in cache[key]:
                cartridge=mgr.copy(original);assert mgr.transform(cartridge,t)
                probe=mgr.copy(body);assert mgr.booleanOperation(probe,cartridge,adsk.fusion.BooleanTypes.IntersectionBooleanType)
                overlaps.append(probe.volume*1000)
            cx=(seat['x']+seat['w']/2)/10;cy=(seat['y']+seat['d']/2)/10
            assert body.pointContainment(P(cx,cy,.6))==adsk.fusion.PointContainment.PointInsidePointContainment
            assert body.pointContainment(P(cx,cy,.8))==adsk.fusion.PointContainment.PointOutsidePointContainment
            sx=(seat['x']+3)/10 if c['orientation']=='0' else cx
            sy=(seat['y']+3)/10 if c['orientation']=='90' else cy
            assert body.pointContainment(P(sx,sy,.8))==adsk.fusion.PointContainment.PointInsidePointContainment
            assert body.pointContainment(P(sx,sy,1))==(adsk.fusion.PointContainment.PointOutsidePointContainment if c['magazineCutouts'] else adsk.fusion.PointContainment.PointInsidePointContainment)
        q=c['seats'][0]
        probe=P(.05,(q['y']+q['d']/2)/10,1.1) if c['orientation']=='0' else P((q['x']+q['w']/2)/10,.05,1.1)
        assert body.pointContainment(probe)==(adsk.fusion.PointContainment.PointOutsidePointContainment if c['magazineCutouts'] else adsk.fusion.PointContainment.PointInsidePointContainment)
        assert result['features']==(5 if c['magazineCutouts'] else 4)
        assert max(overlaps)<1e-6,(index,max(overlaps))
        for axis,expected in [('x',c['widthMM']),('y',c['depthMM']),('z',c['heightMM'])]:
            assert abs((getattr(body.boundingBox.maxPoint,axis)-getattr(body.boundingBox.minPoint,axis))*10-expected)<1e-5
        if c['magnet']!='off':
            radii=[f.geometry.radius*20 for f in body.faces if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.axis.z)>.99]
            assert sum(abs(v-c['diameter'])<1e-6 for v in radii)==c['cols']*c['rows']*4
        if index==0:
            d.userParameters.itemByName(result['heightParameter']).expression='21 mm';d.computeAll()
            assert abs(body.boundingBox.maxPoint.z*10-21)<1e-6
            assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features)
        result.pop('bodyToken');result.update(maxCartridgeOverlapMM3=max(overlaps),existingBodyUnchanged=True,floorVerified=True)
        results.append(result);doc.close(False)
    previous.activate()
    assert all(doc.isValid and doc.name==name and doc.isModified==modified for doc,name,modified in originals)
    path=Path(r'D:\Code Projects\GridfinityWorkshop\.agents\qa\runs\local\magazine');path.mkdir(exist_ok=True)
    (path/'verified-generation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results))
