"""Native retention acceptance. Load via Fusion MCP and call run_case(index)."""
from pathlib import Path
import adsk.core,adsk.fusion,importlib,sys,types,json
ROOT=Path(r'D:\Code Projects\GridfinityWorkshop');OUT=ROOT/'.agents/qa/runs/2026-10-05-lid-retention';OUT.mkdir(parents=True,exist_ok=True)
if '_gf_retention_native' not in sys.modules:
    pkg=types.ModuleType('_gf_retention_native');pkg.__path__=[str(ROOT/'workshop')];sys.modules[pkg.__name__]=pkg
G=importlib.import_module('_gf_retention_native.bin_generation')
BASE=dict(family='standard',title='Retention QA',cols=1,rows=1,height=2,interior='open',rim=False,dovetailLid=True,scoop=False,label=False,magnet='off',divX=2,divY=2)
CASES=[dict(lidRetention='none'),dict(lidRetention='bump'),dict(lidRetention='magnet'),dict(lidRetention='both'),dict(lidRetention='magnet',lidMagnetSize='3',lidMagnetFit='clearance'),dict(lidRetention='both',cols=6,rows=6,height=20,rim=True,interior='divided',divX=6,divY=6),dict(lidRetention='both',lidDetentInterference=.2,rim=True)]

def run_case(index):
    app=adsk.core.Application.get();previous=app.activeDocument;originals=[(d,d.name,d.isModified) for d in app.documents]
    c=G.validate(dict(BASE,**CASES[index]));doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.name='QA Lid retention '+str(index)
    d=adsk.fusion.Design.cast(app.activeProduct);mgr=adsk.fusion.TemporaryBRepManager.get()
    def overlap(a,b):
        copy=mgr.copy(a);assert mgr.booleanOperation(copy,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
        return copy.volume*1000
    def shifted(body,y):
        copy=mgr.copy(body);t=adsk.core.Matrix3D.create();t.translation=adsk.core.Vector3D.create(0,y/10,0);assert mgr.transform(copy,t);return copy
    try:
        s=G.sketch(d.rootComponent,'QA overlapping sentinel','0 mm');G.rectangle(s,0,0,30,30)
        sentinel=G.extrude(d.rootComponent,s,'160 mm','QA sentinel').bodies.item(0);volume=sentinel.volume
        result=G.generate(c);body=d.findEntityByToken(result['bodyToken'])[0];lid=d.findEntityByToken(result['lidToken'])[0]
        assert body.isSolid and lid.isSolid and body.lumps.count==lid.lumps.count==1
        assert abs(sentinel.volume-volume)<1e-9
        assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features)
        closed=overlap(body,lid);assert closed<1e-6,('closed interference',closed)
        travel=[0,-.25,-.5,-.75,-1,-1.25,-1.5,-1.75,-2,-2.5,-3,-c['depthMM']/2,-c['depthMM']-2]
        intersections=[overlap(body,shifted(lid,y)) for y in travel]
        if c['lidRetentionPlan']['detents']:assert max(intersections)>1e-6,('missing detent',intersections)
        else:assert max(intersections)<1e-6,('unexpected sliding interference',intersections)
        assert max(intersections[-3:])<1e-6,('runout/captive obstruction',intersections)
        plate=next(f for comp in d.allComponents for f in comp.features if f.name.endswith(' - Lid plate 3 mm'))
        assert abs(plate.extentOne.distance.value*10-3)<1e-6
        pockets=[]
        if c['lidRetentionPlan']['seats']:
            radius=c['lidRetentionPlan']['diameter']/20
            for part, bottom in [(body,c['heightMM']-2),(lid,c['heightMM']+.3)]:
                faces=[face for face in part.faces if face.geometry.objectType==adsk.core.Cylinder.classType() and abs(face.geometry.radius-radius)<1e-7 and abs(face.boundingBox.minPoint.z*10-bottom)<1e-5 and abs(face.boundingBox.maxPoint.z*10-bottom-2)<1e-5]
                assert len(faces)==2,('magnet pockets',part.name,len(faces));pockets.append(len(faces))
        new_height=c['heightMM']+7;d.userParameters.itemByName(result['heightParameter']).expression=f'{new_height} mm';d.computeAll()
        assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features)
        assert abs(lid.boundingBox.maxPoint.z*10-(new_height+5.6+(3.8 if c['rim'] else 0)))<1e-5
        assert overlap(body,lid)<1e-6
        row={k:v for k,v in result.items() if 'Token' not in k};row.update(case=index,mode=c['lidRetention'],closedOverlapMM3=closed,slideOffsetsMM=travel,slideOverlapMM3=intersections,magnetPocketCounts=pockets,fixedPlateMM=3,heightEditPassed=True,sentinelPreserved=True)
        (OUT/f'case-{index}.json').write_text(json.dumps(row,indent=2),encoding='utf8')
        if index==3:
            sentinel.isVisible=False;lid.isVisible=False
            camera=app.activeViewport.camera;camera.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation;camera.isFitView=True;app.activeViewport.camera=camera
            assert app.activeViewport.saveAsImageFile(str(OUT/'magnet-ledges-and-detent-rails.png'),1100,800)
            body.isVisible=False;lid.isVisible=True
            camera=app.activeViewport.camera;camera.viewOrientation=adsk.core.ViewOrientations.IsoBottomRightViewOrientation;camera.isFitView=True;app.activeViewport.camera=camera
            assert app.activeViewport.saveAsImageFile(str(OUT/'lid-underside-retention.png'),1100,800)
        print(json.dumps({'case':index,'mode':c['lidRetention'],'seconds':row['seconds'],'closedOverlap':closed,'peakDetentOverlap':max(intersections),'freeRunoutOverlap':max(intersections[-3:]),'magnetPockets':pockets,'heightEdit':True}))
    finally:
        doc.close(False)
        if previous and previous.isValid:previous.activate()
        assert all(doc.isValid and doc.name==name and doc.isModified==modified for doc,name,modified in originals)
