"""Fusion integration suite; requires the disposable gf_bin_verification session."""
import sys,json,adsk.core,adsk.fusion
from pathlib import Path

def run(_context: str):
    t=sys.modules['gf_bin_verification'];t.document.activate();g=t.generator
    d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    manager=adsk.fusion.TemporaryBRepManager.get()
    original=next(b for c in d.allComponents for b in c.bRepBodies)
    protected=manager.copy(original);token=original.entityToken
    defaults=dict(family='standard',title='Bin verification',cols=2,rows=1,height=6,interior='open',rim=True,scoop=False,label=False,magnet='press',magnetDepth=2.4)
    cases=[dict(cols=6,rows=6,height=2,interior='divided',divX=6,divY=6),dict(interior='magnets',channelShape='round',storedDiameter=6,storedClearance=.5,channelColumns=8,channelRows=4),dict(interior='magnets',channelShape='square',channelWidth=6,storedClearance=.5,channelColumns=8,channelRows=4),dict(interior='magnets',channelShape='rectangle',channelWidth=6,channelDepth=10,storedClearance=.5,channelColumns=8,channelRows=3),dict(family='blank',interior='solid',rim=False,magnet='off'),dict(family='blank',interior='open',rim=True)]
    for case in cases:
        r=g.generate(dict(defaults,**case));b=d.findEntityByToken(r['bodyToken'])[0]
        z=b.boundingBox.maxPoint.z-b.boundingBox.minPoint.z
        assert abs(z*10-r['overallHeightMM'])<1e-4,(z,r)
        parameter=d.userParameters.itemByName(r['heightParameter']);before=parameter.value
        parameter.value=before+.7;d.computeAll()
        b=d.findEntityByToken(r['bodyToken'])[0]
        assert abs(b.boundingBox.maxPoint.z-b.boundingBox.minPoint.z-z-.7)<1e-4
        parameter.value=before;d.computeAll()
        assert all(int(f.healthState)==0 for c in d.allComponents for f in c.features)
        a=manager.copy(d.findEntityByToken(token)[0]);manager.booleanOperation(a,protected,adsk.fusion.BooleanTypes.DifferenceBooleanType)
        b=manager.copy(protected);manager.booleanOperation(b,d.findEntityByToken(token)[0],adsk.fusion.BooleanTypes.DifferenceBooleanType)
        assert a.volume<1e-9 and b.volume<1e-9
        r['heightEditVerified']=True;r['unrelatedBodyDifferenceMM3']=[a.volume*1000,b.volume*1000]
        t.results.append(r)
        print(r['name'],round(r['seconds'],3),'s')
    Path(r'D:\Code Projects\GridfinityWorkshop\experiments\fusion-ui\bin-generation-verification.json').write_text(json.dumps(t.results,indent=2))
