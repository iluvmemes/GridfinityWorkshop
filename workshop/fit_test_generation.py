"""Small, labeled test pieces. Imports closure geometry only through the native template."""
import json,time
import adsk.core,adsk.fusion
from .fit_test_request import validate
from .bin_generation import sketch,rectangle,extrude,insert,P,E,OP
from . import clasp_generation


def label(comp,body,text,x,y,w,h,z):
    s=sketch(comp,'Sample marking - '+text,f'{z} mm');s.isComputeDeferred=False
    i=s.sketchTexts.createInput3("'"+text+"'",E('1.8 mm'))
    i.fontName='Arial'
    i.setAsMultiLine(P(x/10,y/10,0),P((x+w)/10,(y+h)/10,0),
        adsk.core.HorizontalAlignments.CenterHorizontalAlignment,adsk.core.VerticalAlignments.MiddleVerticalAlignment,0)
    textobj=s.sketchTexts.add(i)
    inp=comp.features.extrudeFeatures.createInput(textobj,OP.CutFeatureOperation)
    inp.setDistanceExtent(False,E('-0.3 mm'));inp.participantBodies=[body]
    f=comp.features.extrudeFeatures.add(inp);f.name='Engrave '+text;s.isVisible=False


def block(manager,x,y,w,d,h):
    return manager.createBox(adsk.core.OrientedBoundingBox3D.create(P((x+w/2)/10,(y+d/2)/10,h/20),
        adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),w/10,d/10,h/10))


def generate(data):
    c=validate(data);app=adsk.core.Application.get();previous=app.activeDocument;doc=None;started=time.perf_counter()
    try:
        kind=c['testType']
        if kind=='closure':
            clasp_generation.generate(c['closure']);doc=app.activeDocument
            design=adsk.fusion.Design.cast(app.activeProduct)
            comp=next(comp for comp in design.allComponents if comp.name.endswith(' - Body'))
            s=sketch(comp,'Closure sample - lower material removal','-5 mm');rectangle(s,-60,-40,120,80)
            extrude(comp,s,'17 mm','Closure sample - keep hinge and catch envelope',OP.CutFeatureOperation,comp.bRepBodies.item(0))
            for component in design.allComponents:
                for b in component.bRepBodies:b.name='Closure test - '+b.name
        else:
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(app.activeProduct);comp=design.rootComponent
            manager=adsk.fusion.TemporaryBRepManager.get();difference=adsk.fusion.BooleanTypes.DifferenceBooleanType
            for index,q in enumerate(c['samples']):
                x,y,w,d,h=q['x'],q['y'],q['w'],q['d'],q['h']
                if kind=='envelope':
                    s=sketch(comp,'Drawer footprint - outer and inner boundary','0 mm')
                    rectangle(s,0,0,w,d);rectangle(s,3,3,w-6,d-6);s.isComputeDeferred=False
                    ring=next(p for p in s.profiles if p.profileLoops.count==2)
                    i=comp.features.extrudeFeatures.createInput(ring,OP.NewBodyFeatureOperation);i.setDistanceExtent(False,E('3 mm'))
                    body=comp.features.extrudeFeatures.add(i).bodies.item(0);s.isVisible=False
                    if c['testPosts']:
                        s=sketch(comp,'Closed-height corner posts','3 mm')
                        for px in (0,w-3):
                            for py in (0,d-3):rectangle(s,px,py,3,3)
                        extrude(comp,s,f'{h-3} mm','Height posts',OP.JoinFeatureOperation,body)
                    label(comp,body,q['label'],5,0,w-10,3,3)
                else:
                    temp=block(manager,x,y,w,d,h)
                    if kind=='pin':
                        tool=manager.createCylinderOrCone(P((x+w/2)/10,y/10,.4),q['bore']/20,P((x+w/2)/10,(y+d)/10,.4),q['bore']/20)
                        assert manager.booleanOperation(temp,tool,difference)
                    elif kind=='magnet':
                        # Match bin feet: pocket opens toward the print bed, with a roof above.
                        tool=manager.createCylinderOrCone(P((x+w/2)/10,(y+7)/10,0),q['bore']/20,P((x+w/2)/10,(y+7)/10,c['magnetDepth']/10),q['bore']/20)
                        assert manager.booleanOperation(temp,tool,difference)
                    else:
                        # A low labeling tab saves material and leaves channel depth unchanged.
                        tab=block(manager,x,y+d-6,w,6,h-2)
                        transform=adsk.core.Matrix3D.create();transform.translation=adsk.core.Vector3D.create(0,0,.2);manager.transform(tab,transform)
                        assert manager.booleanOperation(temp,tab,difference)
                        for row in range(c['channelRows']):
                            for col in range(c['channelColumns']):
                                px=x+2+col*(c['cw']+q['gapX']);py=y+2+row*(c['cd']+q['gapY'])
                                if c['channelShape']=='round':
                                    tool=manager.createCylinderOrCone(P((px+c['cw']/2)/10,(py+c['cd']/2)/10,.2),c['cw']/20,P((px+c['cw']/2)/10,(py+c['cd']/2)/10,h/10),c['cw']/20)
                                else:
                                    tool=block(manager,px,py,c['cw'],c['cd'],h-2)
                                    transform=adsk.core.Matrix3D.create();transform.translation=adsk.core.Vector3D.create(0,0,.2);manager.transform(tool,transform)
                                assert manager.booleanOperation(temp,tool,difference)
                    body=insert(comp,[temp],f'Sample {index+1} - {kind} {q["label"]}').bodies.item(0)
                    label(comp,body,q['label'],x,y+(0 if kind=='pin' else d-5),w,10 if kind=='pin' else 5,2 if kind=='spacing' else h)
                body.name=f'Fit test {index+1} - {kind} {q["label"]} mm'
        doc.name=f"{c['title']} - {kind} test"
        bodies=[b for comp in design.allComponents for b in comp.bRepBodies]
        if any(not b.isSolid or b.lumps.count!=1 for b in bodies):raise RuntimeError('A test piece is not a connected solid.')
        issues=[f.errorOrWarningMessage for comp in design.allComponents for f in comp.features if not f.isSuppressed and int(f.healthState)!=0]
        if issues:raise RuntimeError('; '.join(issues))
        design.rootComponent.attributes.add('GridfinityWorkshop','fitTestRecipe',json.dumps(c))
        app.activeViewport.fit()
        return dict(name=doc.name,seconds=time.perf_counter()-started,newDocument=True,samples=c['samples'],parts=[b.name for b in bodies])
    except Exception:
        if doc:doc.close(False)
        if previous and previous.isValid:previous.activate()
        raise
