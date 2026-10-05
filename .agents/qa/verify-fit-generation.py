"""Run in Fusion MCP: geometry measurements, independent bores, spacing and test pieces."""
import importlib,json,sys
from pathlib import Path
import adsk.core,adsk.fusion


def run(_context: str):
    app=adsk.core.Application.get();previous=app.activeDocument
    module=next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and
        str(getattr(m,'__file__','')).replace('\\','/').endswith('/workshop/app.py'))
    pkg=module.generation.__package__;clasp=importlib.import_module(pkg+'.clasp_generation');tests=importlib.import_module(pkg+'.fit_test_generation')
    protected=[(doc,doc.isModified,[(b,b.volume) for comp in adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')).allComponents for b in comp.bRepBodies]) for doc in app.documents]
    c=dict(family='clasp',title='Fit verification',cols=2,rows=1,height=6,interior='magnets',rim=False,scoop=False,label=False,
        buckle=.2,pinDiameter=1.75,pinAllowance=.3,pinOverrides=True,bodyPinAllowance=.1,lidPinAllowance=.2,lidLatchAllowance=.3,bucklePinAllowance=.4,
        grip=2,magnet='off',diameter=6.08,magnetDepth=2.4,divX=2,divY=2,channelShape='round',storedDiameter=6,storedClearance=.5,
        channelWidth=6,channelDepth=10,channelColumns=6,channelRows=3,channelGapLinked=False,channelGapX=3,channelGapY=5)
    result=clasp.generate(c);doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct)
    for comp in d.allComponents:
        role=comp.name.rsplit(' - ',1)[-1]
        expected={'Body':[.925],'Lid':[.975,1.025],'Buckle':[1.075]}.get(role,[])
        radii=[f.geometry.radius*10 for b in comp.bRepBodies for f in b.faces if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.axis.y)>.99]
        assert all(any(abs(r-want)<1e-6 for r in radii) for want in expected),(role,radii,expected)
    body=next(b for comp in d.allComponents for b in comp.bRepBodies if b.name.endswith(' - Body'))
    centers={(round(f.geometry.origin.x*10,5),round(f.geometry.origin.y*10,5)) for f in body.faces if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.radius*10-3.25)<1e-6}
    assert centers=={(round(-23.75+i*9.5,5),round(-11.5+j*11.5,5)) for i in range(6) for j in range(3)},centers
    d.userParameters.itemByName('ChannelGapX').expression='4 mm';d.computeAll()
    assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features if not f.isSuppressed)
    result.update(independentBoresMeasured=True,channelCentersMeasured=True,spacingParameterEditVerified=True)
    results=[result];doc.close(False)
    base=dict(c,family='tests',title='Fit test verification',testCount=3,testStart=1,testStep=1,testType='spacing',
              testAxis='both',testStackDepth=28,channelColumns=3,channelRows=3,testPosts=True,testSource='clasp')
    inside=adsk.fusion.PointContainment.PointInsidePointContainment;outside=adsk.fusion.PointContainment.PointOutsidePointContainment
    for change in [dict(testType='pin',testStart=.15,testStep=.05),dict(testType='magnet',testStart=5.98,testStep=.05),
                   dict(channelShape='round'),dict(channelShape='square'),dict(channelShape='rectangle'),dict(testType='envelope'),dict(testType='closure')]:
        recipe=dict(base,**change);result=tests.generate(recipe);doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct)
        bodies=[b for comp in d.allComponents for b in comp.bRepBodies]
        for index,q in enumerate(result['samples']):
            if recipe['testType']=='closure':
                assert abs((max(b.boundingBox.maxPoint.z for b in bodies)-min(b.boundingBox.minPoint.z for b in bodies))*10-q['h'])<1e-6
                continue
            body=next(b for b in bodies if b.name.startswith(f'Fit test {index+1} -'))
            if recipe['testType']=='envelope':
                assert abs(body.boundingBox.maxPoint.z*10-q['h'])<1e-6
            elif recipe['testType']=='pin':
                radii=[f.geometry.radius*20 for f in body.faces if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.axis.y)>.99]
                assert any(abs(diameter-q['bore'])<1e-6 for diameter in radii)
            elif recipe['testType']=='magnet':
                p=lambda z:adsk.core.Point3D.create((q['x']+q['w']/2)/10,(q['y']+7)/10,z/10)
                assert body.pointContainment(p(1))==outside and body.pointContainment(p(recipe['magnetDepth']+1))==inside
            else:
                cw=(recipe['storedDiameter'] if recipe['channelShape']=='round' else recipe['channelWidth'])+recipe['storedClearance']
                cd=recipe['channelDepth']+recipe['storedClearance'] if recipe['channelShape']=='rectangle' else cw
                for x in range(3):
                    for y in range(3):
                        px=q['x']+2+x*(cw+q['gapX'])+cw/2;py=q['y']+2+y*(cd+q['gapY'])+cd/2
                        assert body.pointContainment(adsk.core.Point3D.create(px/10,py/10,1))==outside
                        assert body.pointContainment(adsk.core.Point3D.create(px/10,py/10,.1))==inside
        result['geometryMeasured']=True;results.append(result);doc.close(False)
    for doc,modified,bodies in protected:
        assert doc.isModified==modified
        assert all(b.isValid and abs(b.volume-volume)<1e-8 for b,volume in bodies)
    previous.activate()
    path=Path(r'D:\Code Projects\GridfinityWorkshop\.agents\qa\runs\local\clasp\fit-measurement-verification.json')
    path.write_text(json.dumps(dict(existingDesignsPreserved=True,cases=results),indent=2),encoding='utf-8')
    print(json.dumps(dict(existingDesignsPreserved=True,cases=[dict(name=r['name'],seconds=r['seconds']) for r in results])))
