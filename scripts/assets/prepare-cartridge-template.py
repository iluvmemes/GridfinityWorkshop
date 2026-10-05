"""Run via Fusion MCP on the disposable cartridge development copy only."""
import math
from pathlib import Path
import adsk.core, adsk.fusion

def run(_context):
    app=adsk.core.Application.get()
    assert app.activeDocument.name=='Cartridge template development'
    d=adsk.fusion.Design.cast(app.activeProduct)
    E=adsk.core.ValueInput.createByString
    P=adsk.core.Point3D.create
    for name,expr,unit in [('HeightUnits','8',''),('BodyHeight','HeightUnits * 7 mm','mm'),
                           ('BuckleExtra','0.2 mm','mm'),('GripThickness','2 mm','mm')]:
        d.userParameters.add(name,E(expr),unit,'Cartridge template control')
    expressions={'d18':'BodyHeight','d26':'BodyHeight - 4.5 mm','d34':'BodyHeight - 4.5 mm',
        'd47':'BodyHeight - 6.8 mm','d54':'BodyHeight + 1.7 mm',
        'd69':'BodyHeight + 3.7 mm','d80':'BodyHeight + 3.7 mm',
        'd91':'BodyHeight + 3.7 mm','d107':'BodyHeight + 3.7 mm',
        'd119':'BodyHeight - 0.8 mm','d130':'Width - 8.9 mm - BuckleExtra'}
    for name,expr in expressions.items():d.allParameters.itemByName(name).expression=expr
    b=next(c for c in d.allComponents if c.name=='Buckle')
    b.features.itemByName('Chamfer1').deleteMe()
    s=b.sketches.add(b.xZConstructionPlane);s.name='Cartridge - Dimensioned pull tab'
    x=d.userParameters.itemByName('Length').value/2+.61
    y=-(d.userParameters.itemByName('BodyHeight').value-1.6)
    lines=s.sketchCurves.sketchLines
    top=lines.addByTwoPoints(P(x-.2,y,0),P(x,y,0))
    right=lines.addByTwoPoints(top.endSketchPoint,P(x,y+.6,0))
    arc=s.sketchCurves.sketchArcs.addByCenterStartSweep(P(x-.1,y+.6,0),right.endSketchPoint,math.pi)
    left=lines.addByTwoPoints(arc.endSketchPoint,top.startSketchPoint)
    gc=s.geometricConstraints;gc.addHorizontal(top);gc.addVertical(right);gc.addVertical(left)
    gc.addTangent(right,arc);gc.addTangent(left,arc)
    ori=adsk.fusion.DimensionOrientations
    def dim(a,b,h,expr):
        v=s.sketchDimensions.addDistanceDimension(a,b,ori.HorizontalDimensionOrientation if h else ori.VerticalDimensionOrientation,P(x+.5,y-.5,0))
        v.parameter.expression=expr
    dim(top.startSketchPoint,top.endSketchPoint,True,'GripThickness')
    dim(s.originPoint,top.endSketchPoint,True,'Length / 2 + 6.1 mm')
    dim(s.originPoint,top.endSketchPoint,False,'BodyHeight - 16 mm')
    dim(right.startSketchPoint,right.endSketchPoint,False,'6 mm')
    assert s.isFullyConstrained
    i=b.features.extrudeFeatures.createInput(s.profiles.item(0),adsk.fusion.FeatureOperations.JoinFeatureOperation)
    i.setSymmetricExtent(E('Width - 8.9 mm - BuckleExtra'),True)
    i.participantBodies=[b.bRepBodies.item(0)]
    f=b.features.extrudeFeatures.add(i);f.name='Cartridge - Pull tab'
    edges=adsk.core.ObjectCollection.create()
    for face in b.bRepBodies.item(0).faces:
        plane=adsk.core.Plane.cast(face.geometry)
        if plane and abs(plane.normal.y)>.999:
            for edge in face.edges:
                if not edges.contains(edge):edges.add(edge)
    ci=b.features.chamferFeatures.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges,E('0.3 mm'),False)
    b.features.chamferFeatures.add(ci).name='Cartridge - Buckle edge comfort'
    for c in d.allComponents:
        for sk in c.sketches:sk.isVisible=False
    d.computeAll()
    issues=[(c.name,f.name,f.errorOrWarningMessage) for c in d.allComponents for f in c.features if int(f.healthState)!=0]
    assert not issues,issues
    path=Path(r'D:\Code Projects\GridfinityWorkshop\workshop\presets\cartridge-template.f3d')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(path)))
    print({'template':str(path),'fullyConstrainedGrip':s.isFullyConstrained,'parts':sum(c.bRepBodies.count for c in d.allComponents)})
