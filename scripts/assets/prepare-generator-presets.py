"""One-time preset preparation, run through Fusion MCP. Not used by Create."""
import json
from pathlib import Path
import adsk.core
import adsk.fusion

ROOT = Path(r'D:\Code Projects\GridfinityWorkshop')
OUT = ROOT / 'workshop/presets'


def run(_context: str):
    OUT.mkdir(exist_ok=True)
    manager = adsk.fusion.TemporaryBRepManager.get()
    p = adsk.core.Point3D.create
    v = adsk.core.Vector3D.create
    full_tool = manager.createFromFile(str(ROOT / 'scripts/assets/source/socket-tool.smt')).item(0)
    # The captured socket floor is Z=-5 mm. Strip all skeleton/hardware extensions
    # below it, retaining the standard mating interface unchanged.
    clip = manager.createBox(adsk.core.OrientedBoundingBox3D.create(
        p(2.075, 2.075, -0.2), v(1,0,0), v(0,1,0), 6, 6, 0.6))
    assert manager.booleanOperation(full_tool, clip, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    assert full_tool.isSolid and full_tool.lumps.count == 1
    assert manager.exportToFile([full_tool], str(OUT / 'standard-socket.smt'))

    app = adsk.core.Application.get()
    previous = app.activeDocument
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = 'Gridfinity preset preparation'
    design = adsk.fusion.Design.cast(app.activeProduct)
    component = design.rootComponent
    sketch = component.sketches.add(component.xYConstructionPlane)
    data = json.loads((ROOT / 'scripts/assets/source/original-profiles.json').read_text())
    profile = next(s for s in data['profiles'] if s['name'] == 'Skeleton opening')
    for curve in profile['curves']:
        a = curve['startPointMM']
        start = p(a[0]/10,a[1]/10,0)
        if curve['type'] == 'Line3D':
            b = curve['endPointMM']
            entity = sketch.sketchCurves.sketchLines.addByTwoPoints(start,p(b[0]/10,b[1]/10,0))
        else:
            c = curve['centerMM']
            entity = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(
                p(c[0]/10,c[1]/10,0),start,
                (curve['endAngle']-curve['startAngle'])*curve['normal'][2])
        entity.isFixed = True
    assert sketch.profiles.count == 1
    feature = component.features.extrudeFeatures.addSimple(sketch.profiles.item(0),
        adsk.core.ValueInput.createByReal(0.34),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    skeleton = manager.copy(feature.bodies.item(0))
    transform = adsk.core.Matrix3D.create()
    transform.translation = v(0,0,-0.84)
    assert manager.transform(skeleton,transform)
    assert manager.exportToFile([skeleton],str(OUT / 'standard-skeleton.smt'))
    print(json.dumps({'socketVolumeMM3':full_tool.volume*1000,'skeletonVolumeMM3':skeleton.volume*1000,
        'assets':[str(OUT/'standard-socket.smt'),str(OUT/'standard-skeleton.smt')]}))
    # Only the disposable document created above is closed.
    doc.close(False)
    if previous:
        previous.activate()
