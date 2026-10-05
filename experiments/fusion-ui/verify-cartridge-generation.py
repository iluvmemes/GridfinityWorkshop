"""Fusion MCP checks on disposable generated documents, never the source prototype."""
import importlib,itertools,json,sys
from pathlib import Path
import adsk.core,adsk.fusion

def run(_context):
    app=adsk.core.Application.get();previous=app.activeDocument
    originals=[(doc,doc.name,doc.isModified) for doc in app.documents]
    module=next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and
        str(getattr(m,'__file__','')).replace('\\','/').endswith('/GridfinityUIPreview/GridfinityUIPreview.py'))
    g=importlib.import_module(module.generation.__package__+'.cartridge_generation')
    cfg=dict(family='cartridge',title='Cartridge verification',cartLength=68,cartWidth=17.5,height=8,
        interior='open',buckle=.2,grip=2,magnet='off',pinDiameter=1.75,pinAllowance=.25,pinOverrides=True,
        bodyPinAllowance=.1,lidPinAllowance=.2,lidLatchAllowance=.3,bucklePinAllowance=.4,
        divX=3,divY=2,channelShape='round',storedDiameter=6,storedClearance=.5,
        channelWidth=6,channelDepth=10,channelColumns=8,channelRows=1,
        channelGapX=1,channelGapY=2,channelGapLinked=False)
    cases=[{},dict(cartLength=30,cartWidth=12,height=4,grip=4,buckle=.6,pinOverrides=False,pinAllowance=.95),
        dict(cartLength=220,cartWidth=80,height=20,grip=4,interior='divided'),
        dict(interior='magnets'),dict(interior='magnets',channelShape='square'),
        dict(interior='magnets',channelShape='rectangle'),
        dict(interior='magnets',channelColumns=1,channelRows=1,height=4,pinOverrides=False,pinAllowance=.05,buckle=0),
        dict(interior='magnets',cartWidth=40,channelColumns=6,channelRows=3,channelGapX=3,channelGapY=4)]
    mgr=adsk.fusion.TemporaryBRepManager.get();results=[]
    inside=adsk.fusion.PointContainment.PointInsidePointContainment
    outside=adsk.fusion.PointContainment.PointOutsidePointContainment
    P=adsk.core.Point3D.create
    for index,change in enumerate(cases):
        c=g.validate({**cfg,**change});result=g.generate(c);doc=app.activeDocument
        d=adsk.fusion.Design.cast(app.activeProduct)
        bodies=[b for comp in d.allComponents for b in comp.bRepBodies]
        overlaps=[]
        for a,b in itertools.combinations(bodies,2):
            temp=mgr.copy(a);assert mgr.booleanOperation(temp,mgr.copy(b),adsk.fusion.BooleanTypes.IntersectionBooleanType)
            overlaps.append(temp.volume*1000)
        assert max(overlaps)<1e-6,overlaps
        lo=[min(getattr(b.boundingBox.minPoint,axis) for b in bodies)*10 for axis in ('x','y','z')]
        hi=[max(getattr(b.boundingBox.maxPoint,axis) for b in bodies)*10 for axis in ('x','y','z')]
        expected=[c['widthMM'],c['depthMM'],c['overallMM']]
        assert all(abs(b-a-e)<1e-5 for a,b,e in zip(lo,hi,expected)),(lo,hi,expected)
        body=next(b for b in bodies if b.name.endswith(' - Body'))
        for q in c['cavities']:
            x=(q['x']+q['w']/2-c['cartLength']/2)/10
            y=(q['y']+q['d']/2-c['cartWidth']/2)/10
            assert body.pointContainment(P(x,y,.1))==inside
            assert body.pointContainment(P(x,y,.3))==outside
        for role,keys in [('Body',['bodyPinAllowance']),('Lid',['lidPinAllowance','lidLatchAllowance']),('Buckle',['bucklePinAllowance'])]:
            part=next(b for b in bodies if b.name.endswith(' - '+role))
            bores=[f.geometry.radius*20 for f in part.faces if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.axis.y)>.99]
            for key in keys:assert any(abs(v-c['pinBores'][key])<1e-6 for v in bores),(role,key,bores)
        seed=next(s for comp in d.allComponents for s in comp.sketches if 'seed' in s.name)
        assert seed.isFullyConstrained
        if index==0:
            d.timeline.markerPosition=0
            for key,value in [('Length','92 mm'),('Width','24 mm'),('HeightUnits','4'),('GripThickness','4 mm')]:
                d.userParameters.itemByName(key).expression=value
            d.timeline.moveToEnd();d.computeAll()
            assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features)
            points=[p.geometry for p in seed.sketchPoints if p!=seed.originPoint]
            xs=[p.x for p in points];ys=[p.y for p in points]
            assert abs(max(xs)+min(xs))<1e-6 and abs(max(ys)+min(ys))<1e-6
            assert abs((max(xs)-min(xs))*10-88)<1e-6
            result['nativeSizeEditVerified']=True
        if index==7:
            d.userParameters.itemByName('ChannelGapX').expression='4 mm'
            d.computeAll()
            assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features)
            centers={(round(f.geometry.origin.x*10,5),round(f.geometry.origin.y*10,5)) for f in body.faces
                if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.axis.z)>.99 and abs(f.geometry.radius*10-3.25)<1e-6}
            assert len(centers)==18,centers
            xs=sorted({x for x,y in centers});ys=sorted({y for x,y in centers})
            assert abs(xs[1]-xs[0]-10.5)<1e-6 and abs(ys[1]-ys[0]-10.5)<1e-6
            result['editableChannelSpacingVerified']=True
        result.update(overlapMM3=overlaps,measuredEnvelopeMM=[b-a for a,b in zip(lo,hi)],floorAndBoresVerified=True)
        results.append(result);doc.close(False)
    previous.activate()
    assert all(doc.isValid and doc.name==name and doc.isModified==modified for doc,name,modified in originals)
    Path(r'D:\Code Projects\GridfinityWorkshop\experiments\fusion-ui\cartridge\verified-generation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results))
