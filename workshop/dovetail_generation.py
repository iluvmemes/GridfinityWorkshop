"""Fixed 3 mm lid plate over a 2 mm dovetail; native features follow bin height.

Slides toward -Y. Dimensions below are mm; no user-editable lid-thickness parameter.
"""
import adsk.core,adsk.fusion
from . import bin_generation as b

PLATE=3.0
RAIL=2.3
PLATE_BASE=2.6
TOP=PLATE_BASE+PLATE


def move_up(comp,body,height,name):
    i=comp.features.moveFeatures.createInput2(b.collection([body]))
    i.defineAsTranslateXYZ(b.V(0),b.V(0),b.E(height),False)
    f=comp.features.moveFeatures.add(i);f.name=name
    return f.bodies.item(0)


def prism(comp,points,y,length,height,name):
    """XZ section, extruded along +Y and moved by the native height parameter."""
    pi=comp.constructionPlanes.createInput();pi.setByOffset(comp.xZConstructionPlane,b.E(f'{y} mm'))
    plane=comp.constructionPlanes.add(pi);plane.name=name+' plane';plane.isLightBulbOn=False
    s=comp.sketches.add(plane);s.name=name+' profile';s.isComputeDeferred=True
    for a,z in zip(points,points[1:]+points[:1]):
        line=s.sketchCurves.sketchLines.addByTwoPoints(b.P(a[0]/10,-a[1]/10,0),b.P(z[0]/10,-z[1]/10,0));line.isFixed=True
    body=b.extrude(comp,s,f'{length} mm',name).bodies.item(0)
    return move_up(comp,body,height,name+' follows height')


def add(design,comp,body,c,height,name):
    w,d=c['widthMM'],c['depthMM']
    s=b.sketch(comp,name+' - Dovetail collar',height);b.rectangle(s,0,0,w,d,3.75)
    collar=b.extrude(comp,s,f'{RAIL} mm',name+' - Raised guide collar').bodies.item(0)
    body=b.join(comp,body,[collar],name+' - Join guides to this bin')
    # 45 degree undercuts, .30 horizontal clearance on each sliding face.
    tool=prism(comp,[(1.9,0),(w-1.9,0),(w-5.2,3.3),(5.2,3.3)],-1,d-1,height,name+' - Female dovetail tool')
    i=comp.features.combineFeatures.createInput(body,b.collection([tool]));i.operation=b.OP.CutFeatureOperation
    f=comp.features.combineFeatures.add(i);f.name=name+' - Cut rails in this bin only';body=f.bodies.item(0)
    # .30 mm above the floor/rails. Rear contact seats the lid flush to the footprint.
    tongue=prism(comp,[(2.5,.3),(w-2.5,.3),(w-4.5,2.3),(w-4.5,2.6),(4.5,2.6),(4.5,2.3)],
        .3,d-2.3,height,name+' - Male dovetail')
    s=b.sketch(comp,name+' - Fixed 3 mm lid plate',height+' + 2.6 mm');b.rectangle(s,0,0,w,d,3.75)
    plate=b.extrude(comp,s,'3 mm',name+' - Lid plate 3 mm').bodies.item(0)
    lid=b.join(comp,plate,[tongue],name+' - Join tongue to lid')
    body,lid=add_retention(comp,body,lid,c,height,name)
    if c['rim']:
        base=b.insert(comp,[b.preset(f"bin-rim-{c['cols']}x{c['rows']}.smt")],name+' - Standard stacking lip on lid')
        rim=move_up(comp,base.bodies.item(0),height+' + 5.6 mm',name+' - Lip above lid')
        lid=b.join(comp,lid,[rim],name+' - Join stacking lip to lid')
    lid.name=name+' - Dovetail lid'+(' with stacking lip' if c['rim'] else '')
    if not lid.isSolid or lid.lumps.count!=1:raise RuntimeError('Dovetail lid is not one connected solid.')
    lid.attributes.add('GridfinityWorkshop','lidPlateThicknessMM','3')
    lid.attributes.add('GridfinityWorkshop','slideDirection','-Y; slide out through the front')
    return body,lid


def cut_tools(comp, target, tools, height, name):
    base=b.insert(comp,tools,name+' tools')
    moved=[move_up(comp,tool,height,name+' follows height') for tool in list(base.bodies)]
    i=comp.features.combineFeatures.createInput(target,b.collection(moved))
    i.operation=b.OP.CutFeatureOperation
    f=comp.features.combineFeatures.add(i);f.name=name
    return f.bodies.item(0)


def add_retention(comp, body, lid, c, height, name):
    plan=c['lidRetentionPlan'];mgr=adsk.fusion.TemporaryBRepManager.get()
    if plan['detents']:
        bumps=[];tools=[]
        for q in plan['detents']:
            center=b.P(q['x']/10,q['y']/10,q['z']/10)
            bumps.append(mgr.createSphere(center,q['radius']/10))
            tools.append(mgr.createSphere(center,q['recessRadius']/10))
            end=b.P(q['x']/10,q['trackEnd']/10,q['z']/10)
            track=mgr.createCylinderOrCone(b.P(q['x']/10,-.1,q['z']/10),q['recessRadius']/10,end,q['recessRadius']/10)
            cap=mgr.createSphere(end,q['recessRadius']/10)
            if not mgr.booleanOperation(track,cap,adsk.fusion.BooleanTypes.UnionBooleanType):
                raise RuntimeError('Could not round the detent runout track.')
            tools.append(track)
        base=b.insert(comp,bumps,name+' - Rounded lid detent bumps')
        moved=[move_up(comp,tool,height,name+' - Detent follows height') for tool in list(base.bodies)]
        lid=b.join(comp,lid,moved,name+' - Join detent bumps to lid')
        body=cut_tools(comp,body,tools,height,name+' - Detent seats and free-sliding runout')
    if plan['seats']:
        s=b.sketch(comp,name+' - Lid magnet support ledges',height+' - 3 mm')
        for q in plan['seats']:
            # Extend the rear of each ledge into the existing rear wall.
            b.rectangle(s,q['x']-q['span']/2,q['y']-q['span']/2,q['span'],c['depthMM']-(q['y']-q['span']/2)-.5,.5)
        ledges=b.extrude(comp,s,'3 mm',name+' - Rear magnet ledges').bodies
        body=b.join(comp,body,list(ledges),name+' - Join magnet ledges to bin')
        for target,z,label in [(body,height+' - 2 mm','Body'),(lid,height+' + 0.3 mm','Lid')]:
            s=b.sketch(comp,name+' - '+label+' retention magnet pockets',z)
            for q in plan['seats']:
                circle=s.sketchCurves.sketchCircles.addByCenterRadius(b.P(q['x']/10,q['y']/10,0),plan['diameter']/20)
                circle.isFixed=True
            b.extrude(comp,s,'2 mm',name+' - '+label+' magnet pockets 2 mm',b.OP.CutFeatureOperation,target)
        lid.attributes.add('GridfinityWorkshop','lidMagnets',f"4 x {c['lidMagnetSize']}x2 mm discs; opposed pairs; check polarity before fitting")
    lid.attributes.add('GridfinityWorkshop','lidRetention',c['lidRetention'])
    return body,lid
