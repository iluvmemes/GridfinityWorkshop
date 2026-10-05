"""Cached cell cutters + native padded blank. Every operation is component scoped."""
import json
from pathlib import Path
import time
import uuid

import adsk.core
import adsk.fusion
from .request import validate
from .naming import next_layout_id, labels

_cache = {}
P = adsk.core.Point3D.create
V = adsk.core.ValueInput.createByReal
E = adsk.core.ValueInput.createByString
OPS = adsk.fusion.FeatureOperations
BOOL = adsk.fusion.BooleanTypes


def collection(items):
    result = adsk.core.ObjectCollection.create()
    for item in items:
        result.add(item)
    return result


def cell_tool(settings):
    key = (settings['style'], settings['magnets'], settings['magnetDiameter'] if settings['magnets'] else None,
           settings['magnetDepth'] if settings['magnets'] else None, settings['screws'])
    manager = adsk.fusion.TemporaryBRepManager.get()
    if key in _cache:
        return manager.copy(_cache[key])
    folder = Path(__file__).parent / 'presets'
    body = manager.createFromFile(str(folder/'standard-socket.smt')).item(0)

    def join(tool):
        if not tool or not manager.booleanOperation(body, tool, BOOL.UnionBooleanType):
            raise RuntimeError('Could not assemble the cached cell cutter.')

    if settings['style'] == 'skeleton':
        join(manager.createFromFile(str(folder/'standard-skeleton.smt')).item(0))
    for x in (.775, 3.375):
        for y in (.775, 3.375):
            if settings['magnets']:
                radius = settings['magnetDiameter']/20
                join(manager.createCylinderOrCone(P(x,y,-.5),radius,
                    P(x,y,-.5-settings['magnetDepth']/10),radius))
            if settings['screws']:
                join(manager.createCylinderOrCone(P(x,y,-.5),.15,P(x,y,-.85),.15))
                join(manager.createCylinderOrCone(P(x,y,-.79),.30,P(x,y,-.64),.15))
                join(manager.createCylinderOrCone(P(x,y,-.85),.30,P(x,y,-.79),.30))
    _cache[key] = manager.copy(body)
    return body


def padded_blank(component, settings, parameters, plate_name, layout_id):
    """Pad widths drive the outside dimensions while the cell origin stays fixed."""
    s = component.sketches.add(component.xYConstructionPlane)
    s.name = plate_name + ' - Envelope (editable padding)'
    w, d = settings['columns']*4.2-.05, settings['rows']*4.2-.05
    left, right, back, front = [settings[k]/10 for k in ('left','right','back','front')]
    points = [P(-left,-back,0),P(w+right,-back,0),P(w+right,d+front,0),P(-left,d+front,0)]
    lines = []
    for i in range(4):
        start = points[i] if i == 0 else lines[-1].endSketchPoint
        end = points[(i+1)%4] if i < 3 else lines[0].startSketchPoint
        line = s.sketchCurves.sketchLines.addByTwoPoints(start,end)
        (s.geometricConstraints.addHorizontal if i%2==0 else s.geometricConstraints.addVertical)(line)
        lines.append(line)
    marker = s.sketchPoints.add(P(-10,-10,0))
    marker.isFixed = True
    dims, orientation = s.sketchDimensions, adsk.fusion.DimensionOrientations
    def dim(a,b,o,expr):
        item = dims.addDistanceDimension(a,b,o,P(-1,-1,0))
        item.parameter.expression = expr
    dim(marker,lines[0].startSketchPoint,orientation.HorizontalDimensionOrientation,'100 mm - '+parameters['left'])
    dim(marker,lines[0].startSketchPoint,orientation.VerticalDimensionOrientation,'100 mm - '+parameters['back'])
    dim(lines[0].startSketchPoint,lines[0].endSketchPoint,orientation.HorizontalDimensionOrientation,
        f"{settings['columns']*42-.5} mm + {parameters['left']} + {parameters['right']}")
    dim(lines[1].startSketchPoint,lines[1].endSketchPoint,orientation.VerticalDimensionOrientation,
        f"{settings['rows']*42-.5} mm + {parameters['back']} + {parameters['front']}")
    extrude = component.features.extrudeFeatures.addSimple(s.profiles.item(0),V(.79),OPS.NewBodyFeatureOperation)
    extrude.name = layout_id + ' - Plate blank 7.9 mm'
    body = extrude.bodies.item(0)
    vertical = [edge for edge in body.edges if abs(edge.boundingBox.maxPoint.z-edge.boundingBox.minPoint.z-.79)<1e-6]
    fillet_input = component.features.filletFeatures.createInput()
    fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(collection(vertical),V(.375),False)
    component.features.filletFeatures.add(fillet_input).name = layout_id + ' - Outer corners R3.75 mm'
    bottom = next(face for face in body.faces if abs(face.boundingBox.maxPoint.z)<1e-6)
    chamfer = component.features.chamferFeatures.createInput2()
    chamfer.chamferEdgeSets.addEqualDistanceChamferEdgeSet(collection(bottom.edges),V(.05),True)
    component.features.chamferFeatures.add(chamfer).name = layout_id + ' - Bottom chamfer 0.5 mm'
    s.isVisible = False
    return body


def generate(data):
    settings = validate(data)
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design or design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise ValueError('Open a parametric Fusion design before creating a baseplate.')
    if design.timeline.markerPosition != design.timeline.count:
        raise ValueError('Move the timeline marker to the end before creating a baseplate.')
    start_time = time.perf_counter()
    seed = cell_tool(settings)  # Validate/prepare temporary geometry before document changes.
    existing_names = [item.name for c in design.allComponents
                      for item in list(c.bRepBodies) + list(c.sketches)]
    layout_id = next_layout_id(existing_names)
    plate_name, piece_names = labels(settings, layout_id)
    uid = 'gf_' + uuid.uuid4().hex[:8]
    start_index = design.timeline.count
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(settings['left']/10,settings['back']/10,0)
    is_part = design.designIntent == adsk.fusion.DesignIntentTypes.PartDesignIntentType
    occurrence = None if is_part else design.rootComponent.occurrences.addNewComponent(transform)
    component = design.rootComponent if is_part else occurrence.component
    if occurrence:
        component.name = plate_name
    feature_start = component.features.count
    params = {}
    try:
        for side in ('left','right','back','front'):
            name = uid + '_padding_' + side
            design.userParameters.add(name,V(settings[side]/10),'mm',f'{plate_name}: {side} edge padding')
            params[side] = name
        body = padded_blank(component,settings,params,plate_name,layout_id)
        manager = adsk.fusion.TemporaryBRepManager.get()
        base = component.features.baseFeatures.add()
        base.name = layout_id + ' - Cached standard cell array'
        if not base.startEdit():
            raise RuntimeError('Could not start cached cell insertion.')
        try:
            for y in range(settings['rows']):
                for x in range(settings['columns']):
                    tool = manager.copy(seed)
                    t = adsk.core.Matrix3D.create()
                    t.translation = adsk.core.Vector3D.create(x*4.2,y*4.2,.84)
                    if not manager.transform(tool,t):
                        raise RuntimeError('Could not position the cached cell cutter.')
                    if not component.bRepBodies.add(tool,base):
                        raise RuntimeError('Could not insert the cached cell cutter.')
        finally:
            base.finishEdit()
        cut = component.features.combineFeatures.createInput(body,collection(base.bodies))
        cut.operation = OPS.CutFeatureOperation
        cut.isKeepToolBodies = False
        cut_feature = component.features.combineFeatures.add(cut)
        cut_feature.name = layout_id + ' - Cut cells and hardware'
        plate_bodies = list(cut_feature.bodies)
        # Split only this component's plate; never discover participants in the root.
        for axis, count, stride in [('x',settings['columns'],settings['chunkX']),('y',settings['rows'],settings['chunkY'])]:
            for index in range(stride,count,stride):
                offset = index*4.2
                pi = component.constructionPlanes.createInput()
                origin_plane = component.yZConstructionPlane if axis=='x' else component.xZConstructionPlane
                normal = getattr(origin_plane.geometry.normal,axis)
                pi.setByOffset(origin_plane,V(offset/normal))
                plane = component.constructionPlanes.add(pi)
                plane.name = f'{layout_id} - Print seam {axis.upper()} = {offset*10:g} mm'
                for candidate in list(plate_bodies):
                    bounds = candidate.boundingBox
                    if getattr(bounds.minPoint,axis)+1e-6 < offset < getattr(bounds.maxPoint,axis)-1e-6:
                        si = component.features.splitBodyFeatures.createInput(candidate,plane,True)
                        split = component.features.splitBodyFeatures.add(si)
                        split.name = f'{layout_id} - Split {axis.upper()} at {offset*10:g} mm'
                        plate_bodies.remove(candidate)
                        plate_bodies.extend(list(split.bodies))
                plane.isLightBulbOn = False
        bodies = plate_bodies
        if len(bodies) != len(settings['pieces']):
            raise RuntimeError('The generated piece count does not match the layout.')
        bodies.sort(key=lambda b:(round(b.boundingBox.minPoint.y,5),round(b.boundingBox.minPoint.x,5)))
        for index, b in enumerate(bodies):
            if not b.isSolid or b.lumps.count != 1:
                raise RuntimeError('A generated piece is not one connected solid.')
            b.name = piece_names[index]
            b.attributes.add('GridfinityWorkshop','layout',plate_name)
            b.attributes.add('GridfinityWorkshop','piece',json.dumps(dict(settings['pieces'][index],
                number=index+1, name=piece_names[index])))
        unhealthy = [feature.errorOrWarningMessage for feature in list(component.features)[feature_start:]
                     if int(feature.healthState) != 0]
        if unhealthy:
            raise RuntimeError('Fusion reported an unhealthy feature: '+'; '.join(unhealthy))
        component.attributes.add('GridfinityWorkshop_'+uid,'settings',json.dumps(settings))
        component.attributes.add('GridfinityWorkshop_'+uid,'paddingParameters',json.dumps(params))
        feature_count = component.features.count-feature_start
        group = design.timeline.timelineGroups.add(start_index,design.timeline.count-1)
        group.name = plate_name
        return {'component':component.name,'plate':plate_name,'pieces':len(bodies),'seconds':time.perf_counter()-start_time,
                'layoutId':layout_id,'pieceNames':piece_names,
                'paddingParameters':params,'featureCount':feature_count,
                'dimensionsMM':[settings['widthMM'],settings['depthMM'],7.9],
                'magnetDiameterMM':settings['magnetDiameter'] if settings['magnets'] else None,
                'occurrenceToken':occurrence.entityToken if occurrence else None}
    except Exception:
        # These are the only model entities this function owns.
        if occurrence:
            occurrence.deleteMe()
        else:
            # The enclosing native command rolls back root-part changes atomically.
            raise
        for name in params.values():
            parameter = design.userParameters.itemByName(name)
            if parameter:
                parameter.deleteMe()
        raise
