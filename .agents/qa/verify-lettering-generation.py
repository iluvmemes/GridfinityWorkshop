"""Fusion MCP: actual SVG dimensions, counters, target isolation and planar faces.

Creates and closes only a disposable design; leaves user documents untouched.
When loaded with exec, set __file__ to this script in the execution namespace.
"""
import importlib,json,sys
from pathlib import Path
import adsk.core,adsk.fusion

def run(_context: str):
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
    from workshop import lettering,lettering_generation as g
    importlib.reload(lettering);importlib.reload(g)
    from workshop.bin_generation import sketch,rectangle,extrude,P
    app=adsk.core.Application.get();previous=app.activeDocument
    protected=[(doc,doc.isModified) for doc in app.documents]
    doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.name='QA - Outlined lettering disposable'
    design=adsk.fusion.Design.cast(app.activeProduct);comp=design.rootComponent;cases=[]
    for font in ('rubik','atkinson'):
        for operation in ('raised','engrave','separate'):
            s=sketch(comp,'QA base','0 mm');rectangle(s,0,0,60,40)
            body=extrude(comp,s,'3 mm','QA target').bodies.item(0)
            # Overlapping sentinel must not participate in a lettering cut/join.
            s=sketch(comp,'QA sentinel','0 mm');rectangle(s,0,0,60,40)
            sentinel=extrude(comp,s,'3 mm','QA protected solid').bodies.item(0);volume=sentinel.volume
            face=next(f for f in body.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.pointOnFace.z-.3)<1e-6)
            recipe=dict(text='BO8 i',font=font,operation=operation,height=4,maxWidth=50,depth=.6,rotation=25)
            result=g.on_face(recipe,face,P(3,2,.3))
            assert abs(result['height']-4)<.01,result
            assert abs(sentinel.volume-volume)<1e-8
            assert body.isSolid and body.lumps.count==1
            letter_sketch=comp.sketches.item(comp.sketches.count-1)
            assert letter_sketch.sketchTexts.count==0
            assert len(g.filled_profiles(letter_sketch))==5 # B, O, 8, i stem, i dot
            if operation=='raised':assert body.volume>volume
            elif operation=='engrave':assert body.volume<volume
            else:assert result['bodies']==5
            cases.append(dict(font=font,operation=operation,**{k:v for k,v in result.items() if k!='operation'}))
    # Side face and opposite normal test: engraved text must enter the solid.
    for axis in ('side','bottom'):
        s=sketch(comp,'QA orientation base','0 mm');rectangle(s,0,0,60,40)
        body=extrude(comp,s,'20 mm','QA orientation target').bodies.item(0);volume=body.volume
        face=next(f for f in body.faces if isinstance(f.geometry,adsk.core.Plane) and
                  (abs(f.pointOnFace.y)<1e-6 if axis=='side' else abs(f.pointOnFace.z)<1e-6))
        point=P(3,0,1) if axis=='side' else P(3,2,0)
        result=g.on_face(dict(text='O8',operation='engrave'),face,point)
        assert body.volume<volume and body.isSolid
        cases.append(dict(orientation=axis,**result))
    # Custom compound paths: keep a hole and an island inside that hole.
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M0 0h20v20h-20z M3 3v14h14v-14z M7 7h6v6h-6z"/></svg>'
    s=sketch(comp,'QA imported outlines','0 mm');s.isComputeDeferred=False
    size=g.import_art(comp,s,lettering.clean_svg(svg),10,100)
    assert abs(size['height']-10)<.01 and len(g.filled_profiles(s))==2
    assert all(s.sketchTexts.count==0 for s in comp.sketches)
    assert all(int(f.healthState)==0 for f in comp.features if not f.isSuppressed)
    cases.append(dict(customSVG=True,nestedIsland=True,**size))
    transform=adsk.core.Matrix3D.create()
    transform.setToRotation(.6,adsk.core.Vector3D.create(0,0,1),P(0,0,0))
    transform.translation=adsk.core.Vector3D.create(7,8,2)
    occurrence=comp.occurrences.addNewComponent(transform);child=occurrence.component
    s=sketch(child,'QA assembly base','0 mm');rectangle(s,0,0,60,40)
    body=extrude(child,s,'3 mm','QA assembly target').bodies.item(0);volume=body.volume
    face=next(f for f in body.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.pointOnFace.z-.3)<1e-6)
    point=P(3,2,.3);point.transformBy(occurrence.transform2)
    result=g.on_face(dict(text='BO8',operation='engrave'),face.createForAssemblyContext(occurrence),point)
    a,b,c,d=g.bounds(child.sketches.item(child.sketches.count-1))
    assert body.volume<volume and abs((a+c)/2-3)<1e-5 and abs((b+d)/2-2)<1e-5
    cases.append(dict(assemblyPlacement=True,**result))
    doc.close(False)
    for protected_doc,modified in protected:assert protected_doc.isModified==modified
    if previous:previous.activate()
    output=root/'.agents/qa/runs/local';output.mkdir(parents=True,exist_ok=True)
    (output/'lettering-native.json').write_text(json.dumps(cases,indent=2),encoding='utf8')
    print(json.dumps(dict(passed=True,cases=cases,userDesignsPreserved=True)))
