"""Cached standard interfaces and native, target-scoped bin interiors."""
import json,math,re,time,uuid
from pathlib import Path
import adsk.core,adsk.fusion
from .bin_request import validate
from .generation import collection
from .naming import next_layout_id
P=adsk.core.Point3D.create
V=adsk.core.ValueInput.createByReal
E=adsk.core.ValueInput.createByString
OP=adsk.fusion.FeatureOperations
_cache={}


def preset(name):
    mgr=adsk.fusion.TemporaryBRepManager.get()
    if name not in _cache:_cache[name]=mgr.createFromFile(str(Path(__file__).parent/'presets'/name)).item(0)
    return mgr.copy(_cache[name])


def sketch(component,name,z):
    pi=component.constructionPlanes.createInput();pi.setByOffset(component.xYConstructionPlane,E(z))
    plane=component.constructionPlanes.add(pi);plane.name=name+' plane';plane.isLightBulbOn=False
    s=component.sketches.add(plane);s.name=name;s.isComputeDeferred=True
    return s


def rectangle(s,x,y,w,d,r=0):
    x,y,w,d,r=[v/10 for v in (x,y,w,d,r)]
    curves=[]
    if r:
        points=[(x+r,y),(x+w-r,y),(x+w,y+r),(x+w,y+d-r),(x+w-r,y+d),(x+r,y+d),(x,y+d-r),(x,y+r)]
        centers=[(x+w-r,y+r),(x+w-r,y+d-r),(x+r,y+d-r),(x+r,y+r)]
        for i in range(4):
            a,b=points[2*i],points[2*i+1]
            curves.append(s.sketchCurves.sketchLines.addByTwoPoints(P(*a,0),P(*b,0)))
            center=centers[i]
            curves.append(s.sketchCurves.sketchArcs.addByCenterStartSweep(P(*center,0),P(*b,0),math.pi/2))
    else:
        curves=list(s.sketchCurves.sketchLines.addTwoPointRectangle(P(x,y,0),P(x+w,y+d,0)))
    for curve in curves:curve.isFixed=True


def extrude(component,s,distance,name,operation=OP.NewBodyFeatureOperation,target=None):
    s.isComputeDeferred=False
    profiles=collection(list(s.profiles))
    inp=component.features.extrudeFeatures.createInput(profiles,operation)
    inp.setDistanceExtent(False,E(distance))
    if target is not None:inp.participantBodies=[target]
    f=component.features.extrudeFeatures.add(inp);f.name=name;s.isVisible=False
    return f


def insert(component,bodies,name):
    f=component.features.baseFeatures.add();f.name=name
    if not f.startEdit():raise RuntimeError('Could not insert cached interfaces.')
    try:
        for b in bodies:
            if not component.bRepBodies.add(b,f):raise RuntimeError('Cached body insertion failed.')
    finally:f.finishEdit()
    return f


def join(component,target,tools,name):
    inp=component.features.combineFeatures.createInput(target,collection(tools));inp.operation=OP.JoinFeatureOperation
    f=component.features.combineFeatures.add(inp);f.name=name
    return f.bodies.item(0)


def generate(data,group_timeline=True):
    c=validate(data);app=adsk.core.Application.get();design=adsk.fusion.Design.cast(app.activeProduct)
    if c['family'] in ('clasp','cartridge'):raise ValueError('Closure generation must use its new-design template workflow.')
    if not design or design.designType!=adsk.fusion.DesignTypes.ParametricDesignType:raise ValueError('Open a parametric Design document.')
    if design.timeline.markerPosition!=design.timeline.count:raise ValueError('Move the timeline to the end first.')
    # Validate all assets before touching the document.
    foot=foot_with_hardware(c);rim=preset(f"bin-rim-{c['cols']}x{c['rows']}.smt") if c['rim'] else None
    started=time.perf_counter();start=design.timeline.count
    names=[e.name for comp in design.allComponents for e in list(comp.bRepBodies)+list(comp.sketches)]
    uid=next_layout_id(names)
    title=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',c['title']).strip() or 'Bin'
    name=f"{uid} {title} - {c['cols']}x{c['rows']} {c['height']}U - {c['interior']}"
    if c['interior']=='magnets':name+=f" - {c['channelShape']} {c['channelColumns']}x{c['channelRows']} channels"
    if c['magnet']!='off':name+=f" - M{c['diameter']:g}x{c['magnetDepth']:g}"
    if c['dovetailLid']:
        name+=' - dovetail lid'
        if c['lidRetention']!='none':name+=' - '+c['lidRetention']+' retention'
    comp=design.rootComponent
    if design.designIntent!=adsk.fusion.DesignIntentTypes.PartDesignIntentType:
        comp=comp.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component;comp.name=name
    feature_start=comp.features.count
    parameter=uid+'_bin_height';suffix=uuid.uuid4().hex[:5]
    if design.userParameters.itemByName(parameter):parameter+='_'+suffix
    design.userParameters.add(parameter,V(c['heightMM']/10),'mm',name+' nominal height, minimum 14 mm')
    s=sketch(comp,name+' - Envelope','5 mm');rectangle(s,0,0,c['widthMM'],c['depthMM'],3.75)
    body=extrude(comp,s,parameter+' - 5 mm',uid+' - Body envelope').bodies.item(0)
    mgr=adsk.fusion.TemporaryBRepManager.get();feet=[]
    for y in range(c['rows']):
        for x in range(c['cols']):
            b=mgr.copy(foot);t=adsk.core.Matrix3D.create();t.translation=adsk.core.Vector3D.create(x*4.2,y*4.2,.5)
            assert mgr.transform(b,t);feet.append(b)
    base=insert(comp,feet,uid+' - Cached standard feet')
    body=join(comp,body,list(base.bodies),uid+' - Join feet to this bin')
    if c['cavities']:
        s=sketch(comp,name+' - '+('Magnet channels' if c['interior']=='magnets' else 'Compartments'),'7 mm')
        for q in c['cavities']:
            if q.get('round'):
                curve=s.sketchCurves.sketchCircles.addByCenterRadius(P((q['x']+q['w']/2)/10,(q['y']+q['d']/2)/10,0),q['w']/20);curve.isFixed=True
            else:rectangle(s,q['x'],q['y'],q['w'],q['d'],q['r'])
        extrude(comp,s,parameter+' - 7 mm',uid+' - Cut interior in this bin',OP.CutFeatureOperation,body)
    lid=None
    if c['dovetailLid']:
        from . import dovetail_generation
        body,lid=dovetail_generation.add(design,comp,body,c,parameter,name)
    elif rim:
        base=insert(comp,[rim],uid+' - Cached standard stacking rim')
        ri=comp.features.moveFeatures.createInput2(collection(list(base.bodies)))
        ri.defineAsTranslateXYZ(V(0),V(0),E(parameter),False)
        move=comp.features.moveFeatures.add(ri);move.name=uid+' - Rim follows height'
        # Source rim intersects the outer 2 mm walls; solid stock also joins directly.
        body=join(comp,body,list(move.bodies),uid+' - Join stacking rim')
    body.name=name+' - Body'
    if not body.isSolid or body.lumps.count!=1:raise RuntimeError('The generated bin is not one connected solid.')
    issues=[f.errorOrWarningMessage for f in list(comp.features)[feature_start:] if int(f.healthState)!=0]
    if issues:raise RuntimeError('; '.join(issues))
    body.attributes.add('GridfinityWorkshop','binRecipe',json.dumps(c))
    body.attributes.add('GridfinityWorkshop','heightParameter',parameter)
    if lid:
        lid.attributes.add('GridfinityWorkshop','binRecipe',json.dumps(c))
        lid.attributes.add('GridfinityWorkshop','heightParameter',parameter)
    if group_timeline:design.timeline.timelineGroups.add(start,design.timeline.count-1).name=name
    return dict(name=body.name,seconds=time.perf_counter()-started,heightParameter=parameter,
                overallHeightMM=c['overallMM'],features=comp.features.count-feature_start,
                bodyToken=body.entityToken,lidToken=lid.entityToken if lid else None,
                parts=[body.name]+([lid.name] if lid else []),
                interior=c['interior'],channels=len(c['cavities']) if c['interior']=='magnets' else 0)


def foot_with_hardware(c):
    manager=adsk.fusion.TemporaryBRepManager.get()
    key=('foot',c['magnet']!='off',c.get('diameter'),c.get('magnetDepth'))
    if key not in _cache:
        b=preset('bin-foot.smt')
        if c['magnet']!='off':
            radius=c['diameter']/20
            for x in (.775,3.375):
                for y in (.775,3.375):
                    tool=manager.createCylinderOrCone(P(x,y,-.5),radius,P(x,y,-.5+c['magnetDepth']/10),radius)
                    if not manager.booleanOperation(b,tool,adsk.fusion.BooleanTypes.DifferenceBooleanType):
                        raise RuntimeError('Could not prepare magnet sockets in the cached foot.')
        _cache[key]=b
    return manager.copy(_cache[key])
