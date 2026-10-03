"""Fusion MCP benchmark. Run phases individually; never touch pre-existing documents."""
import adsk.core
import adsk.fusion
import importlib
import json
import math
from pathlib import Path
import statistics
import sys
import time
import types

ROOT = Path(r'D:\Code Projects\GridfinityWorkshop')
OUT = ROOT / 'experiments' / 'workflow-benchmark'
pkg = types.ModuleType('gridfinity_benchmark_source')
pkg.__path__ = [str(ROOT)]
sys.modules[pkg.__name__] = pkg
gen = importlib.import_module(pkg.__name__ + '.lib.gridfinityUtils.baseplateGenerator')
Input = importlib.import_module(pkg.__name__ + '.lib.gridfinityUtils.baseplateGeneratorInput').BaseplateGeneratorInput
shape = gen.shapeUtils
fillet = gen.filletUtils
face = gen.faceUtils
combine = gen.combineUtils
mgr = adsk.fusion.TemporaryBRepManager.get()
app = adsk.core.Application.get()
ops = adsk.fusion.FeatureOperations
V = adsk.core.ValueInput.createByString
P = adsk.core.Point3D.create
documents = {}
retained = {}
references = {}
meshes = {}
report = {'fusionVersion': app.version, 'settings': {'sizes': [1, 3, 6], 'repeats': 6, 'magnetDiameterMM': 6.5, 'magnetDepthMM': 2.4, 'bottomExtensionMM': 3.4, 'zClearanceMM': 0.5}, 'generation': {}, 'preparation': {}, 'customization': {}, 'preview': {}}

def write_report():
    (OUT / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

def summary(times):
    return {'firstSeconds': times[0], 'warmMedianSeconds': statistics.median(times[1:]), 'warmMinSeconds': min(times[1:]), 'warmMaxSeconds': max(times[1:]), 'allSeconds': times}

def collection(items):
    result = adsk.core.ObjectCollection.create()
    for item in items:
        result.add(item)
    return result

def new_document(name):
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = 'GF experiment - ' + name
    d = adsk.fusion.Design.cast(app.activeProduct)
    d.designType = adsk.fusion.DesignTypes.ParametricDesignType
    d.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
    documents[name] = d
    return d

def insert(c, body, name):
    bf = c.features.baseFeatures.add()
    bf.name = name
    assert bf.startEdit()
    c.bRepBodies.add(body, bf)
    assert bf.finishEdit()
    return bf.bodies.item(0), bf

def sentinel(c):
    box = adsk.core.OrientedBoundingBox3D.create(P(0.5, 0.5, -0.45), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0), 1.0, 1.0, 0.7)
    temp = mgr.createBox(box)
    body, _ = insert(c, temp, 'Unrelated overlapping body')
    body.name = 'SENTINEL - must remain unchanged'
    return body, temp

def inputs(n):
    i = Input()
    i.baseWidth = i.baseLength = 4.2
    i.baseplateWidth = i.baseplateLength = n
    i.hasExtendedBottom = True
    i.hasSkeletonizedBottom = True
    i.hasMagnetCutouts = True
    i.magnetCutoutsDiameter = 0.65
    i.magnetCutoutsDepth = 0.24
    i.bottomExtensionHeight = 0.34
    i.binZClearance = 0.05
    i.xyClearance = 0.025
    i.cornerFilletRadius = 0.4
    i.hasPadding = i.hasScrewHoles = i.hasConnectionHoles = False
    i.paddingLeft = i.paddingRight = i.paddingTop = i.paddingBottom = 0
    return i

def difference(a, b):
    extra, missing = mgr.copy(a), mgr.copy(b)
    assert mgr.booleanOperation(extra, b, adsk.fusion.BooleanTypes.DifferenceBooleanType)
    assert mgr.booleanOperation(missing, a, adsk.fusion.BooleanTypes.DifferenceBooleanType)
    return {'extraMM3': extra.volume * 1000, 'missingMM3': missing.volume * 1000}

def health(d):
    return [{'name': t.name, 'state': int(t.healthState), 'message': t.errorOrWarningMessage} for t in d.timeline if int(t.healthState) != 0]

def metrics(b):
    box = b.boundingBox
    return {'volumeMM3': b.volume * 1000, 'dimensionsMM': [(getattr(box.maxPoint, k)-getattr(box.minPoint, k))*10 for k in ('x', 'y', 'z')], 'solid': b.isSolid, 'lumps': b.lumps.count, 'faces': b.faces.count}

def baseline(c, n, capture=False):
    original_cut = combine.cutBody
    if capture:
        def capture_cut(target, tools, component):
            # Capture the completed negative cell immediately before final subtraction.
            assert mgr.exportToFile([mgr.copy(tools.item(0))], str(OUT / 'socket-tool.smt'))
            return original_cut(target, tools, component)
        combine.cutBody = capture_cut
    try:
        body = gen.createGridfinityBaseplate(inputs(n), c)
    finally:
        combine.cutBody = original_cut
    return body, {}

def whole(c, n):
    bodies = list(mgr.createFromFile(str(OUT / ('plate-%d.smt' % n))))
    body, bf = insert(c, bodies[0], 'Cached standard plate')
    return body, {'baseFeature': bf}

def tool(c, n):
    width = n*4.2-0.05
    body = shape.simpleBox(c.xYConstructionPlane, -0.05, width, width, -0.79, P(0,0,0), c)
    s = c.sketches.item(0)
    for dim in s.sketchDimensions:
        dim.parameter.expression = 'gridCount * 42 mm - 0.5 mm'
    fillet.filletEdgesByLength(body.faces, 0.375, 0.79, c)
    fillet.createChamfer(collection(list(face.getBottomFace(body).edges)), 0.05, c)
    seed = list(mgr.createFromFile(str(OUT / 'socket-tool.smt')))[0]
    cutter, bf = insert(c, seed, 'Cached standard socket cutter')
    pi = c.features.rectangularPatternFeatures.createInput(collection([cutter]), c.xConstructionAxis, V('gridCount'), V('42 mm'), adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    pi.directionTwoEntity = c.yConstructionAxis
    pi.quantityTwo = V('gridCount')
    pi.distanceTwo = V('42 mm')
    pattern = c.features.rectangularPatternFeatures.add(pi)
    pattern.name = 'Standard cells'
    cutters = list(pattern.bodies)
    if not any(x == cutter for x in cutters):
        cutters.append(cutter)
    cut = combine.cutBody(body, collection(cutters), c)
    cut.name = 'Cut only the generated plate'
    return body, {'pattern': pattern, 'blankSketch': s}

def generate_case(kind, n):
    d = new_document('%s %dx%d' % (kind, n, n))
    if kind == 'tool':
        d.userParameters.add('gridCount', V(str(n)), '', 'Editable native pattern count')
    times, runs = [], []
    previous = None
    for repeat in range(6):
        if previous is not None:
            assert previous.deleteMe()  # Only this benchmark's preceding disposable run.
        occurrence = d.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c = occurrence.component
        c.name = '%s %dx%d' % (kind, n, n)
        sent, sent_ref = sentinel(c)
        start_index = d.timeline.count
        start = time.perf_counter()
        if kind == 'baseline':
            body, handles = baseline(c, n)
        elif kind == 'whole':
            body, handles = whole(c, n)
        else:
            body, handles = tool(c, n)
        elapsed = time.perf_counter()-start
        times.append(elapsed)
        body.name = 'Generated plate'
        sent.isVisible = False
        for s in c.sketches:
            s.isVisible = False
        for plane in c.constructionPlanes:
            plane.isLightBulbOn = False
        runs.append({'generationSeconds': elapsed, 'geometry': metrics(body), 'sentinelVolumeUnchanged': abs(sent.volume-sent_ref.volume)<1e-10, 'timelineItems': d.timeline.count-start_index, 'health': health(d)})
        previous = occurrence
    key = '%s-%d' % (kind,n)
    retained[key] = {'design':d, 'component':c, 'body':body, 'sentinel':sent, 'sentinelRef':sent_ref, 'handles':handles}
    if kind == 'baseline':
        start = time.perf_counter()
        references[n] = mgr.copy(body)
        assert mgr.exportToFile([body], str(OUT / ('plate-%d.smt' % n)))
        report['preparation'][str(n)] = {'sourceGenerationSeconds': times[0], 'exportSeconds': time.perf_counter()-start, 'fileBytes': (OUT / ('plate-%d.smt' % n)).stat().st_size}
        equality = {'extraMM3':0, 'missingMM3':0}
    else:
        equality = difference(body, references[n])
    result = {'timing':summary(times), 'runs':runs, 'geometryDifference':equality, 'sentinelDifference':difference(sent,sent_ref)}
    report['generation'][key] = result
    write_report()
    app.activeViewport.fit()
    return {'case':key, 'timing':summary(times), 'geometryDifference':equality, 'sentinelDifference':result['sentinelDifference'], 'last':runs[-1]}

def prepare_tool():
    d = new_document('socket preset preparation')
    start = time.perf_counter()
    body, _ = baseline(d.rootComponent, 1, True)
    report['preparation']['socketTool'] = {'generationAndCaptureSeconds':time.perf_counter()-start, 'fileBytes': (OUT/'socket-tool.smt').stat().st_size}
    write_report()
    return report['preparation']['socketTool']

def add_padding(item, n):
    d, c = item['design'], item['component']
    extent = 'gridCount * 42 mm - 0.5 mm' if d.userParameters.itemByName('gridCount') else '%s mm' % (n*42-0.5)
    d.userParameters.add('plateExtent', V(extent), 'mm', 'Padding length follows plate size')
    parameter = d.userParameters.add('leftPadding', V('3 mm'), 'mm', 'Editable outward padding width')
    s = c.sketches.add(c.yZConstructionPlane)
    s.name = 'Padding on origin plane'
    lines = s.sketchCurves.sketchLines.addTwoPointRectangle(P(0.05,0,0), P(0.84,n*4.2-0.05,0))
    lines.item(0).startSketchPoint.isFixed = True
    for j in range(4):
        if j % 2 == 0:
            s.geometricConstraints.addHorizontal(lines.item(j))
        else:
            s.geometricConstraints.addVertical(lines.item(j))
    for j, orientation, expression in [(0,adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,'7.9 mm'), (1,adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,'plateExtent')]:
        line = lines.item(j)
        dimension = s.sketchDimensions.addDistanceDimension(line.startSketchPoint,line.endSketchPoint,orientation,P(1,-1,0))
        dimension.parameter.expression = expression
    ei = c.features.extrudeFeatures.createInput(s.profiles.item(0), ops.NewBodyFeatureOperation)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V('leftPadding')), adsk.fusion.ExtentDirections.NegativeExtentDirection)
    ext = c.features.extrudeFeatures.add(ei)
    ext.name = 'Editable left padding'
    join = combine.joinBodies(item['body'],collection([ext.bodies.item(0)]),c)
    join.name = 'Join padding only to generated plate'
    assert c.bRepBodies.count == 2, 'Padding must join the plate; only plate and sentinel may remain'
    s.isVisible = False
    item['padding'] = parameter
    return parameter

def padding_case(kind,n):
    key = '%s-%d' % (kind,n)
    item = retained[key]
    d = item['design']
    d.parentDocument.activate()
    start = time.perf_counter()
    parameter = add_padding(item,n)
    creation = time.perf_counter()-start
    times = []
    samples = []
    for width in [4,6,3,8,5,4]:
        start = time.perf_counter()
        parameter.expression = '%d mm' % width
        times.append(time.perf_counter()-start)
        assert abs(item['body'].boundingBox.minPoint.x*10+width)<1e-6
        samples.append({'widthMM':width,'geometry':metrics(item['body']),'health':health(d)})
    result = {'creationSeconds':creation,'editTiming':summary(times),'samples':samples,'sentinelDifference':difference(item['sentinel'],item['sentinelRef']), 'paddingSketchConstrained':item['component'].sketches.item(item['component'].sketches.count-1).isFullyConstrained}
    report['customization'][key] = result
    write_report()
    return {'case':key, 'creationSeconds':creation, 'edits':summary(times),'last':samples[-1], 'sentinelDifference':result['sentinelDifference']}

def prepare_meshes():
    result = {}
    for n in [1,3,6]:
        start = time.perf_counter()
        body = references[n]
        calc = body.meshManager.createMeshCalculator()
        calc.setQuality(adsk.fusion.TriangleMeshQualityOptions.LowQualityTriangleMesh)
        calc.surfaceTolerance = 0.005  # 0.05 mm display tolerance; never manufacturing geometry.
        mesh = calc.calculate()
        meshes[n] = {'coordinates':list(mesh.nodeCoordinatesAsDouble),'indices':list(mesh.nodeIndices),'normals':list(mesh.normalVectorsAsDouble)}
        elapsed = time.perf_counter()-start
        filename = OUT / ('preview-%d.json' % n)
        filename.write_text(json.dumps(meshes[n]),encoding='utf-8')
        result[str(n)] = {'meshPreparationSeconds':elapsed,'triangles':mesh.triangleCount,'fileBytes':filename.stat().st_size}
    report['preparation']['meshes'] = result
    write_report()
    return result

def preview_case():
    d = new_document('shaded preview - no model bodies')
    c = d.rootComponent
    diffuse = adsk.core.Color.create(70,160,220,255)
    material = adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(diffuse,diffuse,adsk.core.Color.create(220,220,220,255),adsk.core.Color.create(0,0,0,255),40,0.85)
    old = None
    rows = {}
    counts_before = [c.bRepBodies.count,d.timeline.count,c.sketches.count,c.meshBodies.count]
    for n in [1,3,6]:
        times = []
        for repeat in range(6):
            start = time.perf_counter()
            if old is not None:
                old.deleteMe()
            g = c.customGraphicsGroups.add()
            g.color = material
            g.isSelectable = False
            mesh = meshes[n]
            coords = adsk.fusion.CustomGraphicsCoordinates.create(mesh['coordinates'])
            g.addMesh(coords,mesh['indices'],mesh['normals'],[])
            width = (repeat+2)/10
            length = n*4.2-0.05
            points = [-width,0,-0.84, 0,0,-0.84, 0,length,-0.84, -width,length,-0.84, -width,0,-0.05, 0,0,-0.05, 0,length,-0.05, -width,length,-0.05]
            indices = [0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,1,2,6,1,6,5,2,3,7,2,7,6,3,0,4,3,4,7]
            g.addMesh(adsk.fusion.CustomGraphicsCoordinates.create(points),indices,[],[])
            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(repeat*0.1,repeat*0.1,0)
            g.transform = transform
            app.activeViewport.refresh()
            times.append(time.perf_counter()-start)
            old = g
        rows[str(n)] = summary(times)
    app.activeViewport.fit()
    counts_after = [c.bRepBodies.count,d.timeline.count,c.sketches.count,c.meshBodies.count]
    report['preview'] = {'updates':rows,'countsBefore':counts_before,'countsAfter':counts_after,'countOrder':['BRep bodies','timeline items','sketches','mesh bodies'],'timingScope':'Graphics API creation, replacement, translation, padding and viewport refresh; not input-to-photon GPU latency. Mesh preparation excluded and reported separately.'}
    write_report()
    return report['preview']

def current_plate(item):
    return next(b for b in item['component'].bRepBodies if b.name == 'Generated plate')

def resize(item,kind,n):
    d,c = item['design'],item['component']
    if kind == 'whole':
        new_body = list(mgr.createFromFile(str(OUT / ('plate-%d.smt' % n))))[0]
        bf = item['handles']['baseFeature']
        bf.timelineObject.rollTo(False)
        assert bf.startEdit()
        assert bf.updateBody(bf.sourceBodies[0],new_body)
        assert bf.finishEdit()
        d.timeline.moveToEnd()
        d.userParameters.itemByName('plateExtent').expression = '%s mm' % (n*42-0.5)
    else:
        d.userParameters.itemByName('gridCount').expression = str(n)
        cut = c.features.combineFeatures.item(0)
        cut.timelineObject.rollTo(True)
        cutters = list(item['handles']['pattern'].bodies)
        seed = c.features.baseFeatures.item(1).bodies.item(0)
        if not any(b == seed for b in cutters):
            cutters.append(seed)
        cut.toolBodies = collection(cutters)
        d.timeline.moveToEnd()

def resize_case(kind,n):
    item = retained[kind+'-1']
    d,c = item['design'],item['component']
    d.parentDocument.activate()
    times,samples = [],[]
    for repeat in range(6):
        resize(item,kind,3 if n==1 else 1)
        start = time.perf_counter()
        resize(item,kind,n)
        times.append(time.perf_counter()-start)
        b = current_plate(item)
        expected = current_plate(retained['baseline-%d' % n])
        assert c.bRepBodies.count == 2
        assert abs(b.volume-expected.volume)<1e-7
        samples.append({'geometry':metrics(b),'health':health(d)})
    result = {'timing':summary(times),'samples':samples,'geometryDifference':difference(b,expected),'sentinelDifference':difference(item['sentinel'],item['sentinelRef'])}
    report.setdefault('resize',{})['%s-to-%d' % (kind,n)] = result
    write_report()
    return {'kind':kind,'to':n,'timing':summary(times),'geometryDifference':result['geometryDifference'],'sentinelDifference':result['sentinelDifference'],'last':samples[-1]}

def regeneration_case(n):
    d = new_document('baseline regenerate to %d' % n)
    times,previous = [],None
    for repeat in range(6):
        if previous is not None:
            previous.deleteMe()
            d.userParameters.itemByName('plateExtent').deleteMe()
            d.userParameters.itemByName('leftPadding').deleteMe()
        occurrence = d.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c = occurrence.component
        sent,sent_ref = sentinel(c)
        start = time.perf_counter()
        body,_ = baseline(c,n)
        body.name = 'Generated plate'
        item = {'design':d,'component':c,'body':body}
        parameter = add_padding(item,n)
        parameter.expression = '4 mm'
        times.append(time.perf_counter()-start)
        sent.isVisible = False
        previous = occurrence
    expected = current_plate(retained['baseline-%d' % n])
    result = {'timing':summary(times),'geometryDifference':difference(body,expected),'sentinelDifference':difference(sent,sent_ref),'health':health(d),'scope':'Rebuild core and recreate native padding, because the current generator has no core-size edit command. Component and sentinel creation excluded.'}
    report.setdefault('resize',{})['baseline-to-%d' % n] = result
    write_report()
    return result

def verify_and_finish():
    for kind in ['whole','tool']:
        item = retained[kind+'-1']
        item['design'].parentDocument.activate()
        resize(item,kind,1)
    checks = {}
    for n in [1,3,6]:
        expected = current_plate(retained['baseline-%d' % n])
        for kind in ['whole','tool']:
            key = '%s-%d' % (kind,n)
            item = retained[key]
            checks[key] = {'paddedGeometryDifference':difference(current_plate(item),expected),'sentinelDifference':difference(item['sentinel'],item['sentinelRef']),'health':health(item['design'])}
    report['finalVerification'] = checks
    report['methodology'] = {
        'date':'2026-10-03',
        'timing':'time.perf_counter inside Fusion; first invocation and five subsequent invocations recorded separately. First does not mean disk-cold.',
        'generation':'Per-case document; each repetition replaces only its own previous test component. Component creation, sentinel insertion, verification, file export, and screenshots are excluded.',
        'display':'Preview times include graphics creation and viewport.refresh; they do not measure input-to-photon latency. Exact plate mesh data is prepared once, then reused.',
        'padding':'One full-length left strip, 7.9 mm high, extending outward from the origin YZ plane; joined explicitly to the generated plate. Tested widths 4,6,3,8,5,4 mm. This is an experiment, not a complete four-sided padding implementation.',
        'resize':'Targets 1,3,6. Before each measured resize, whole/tool source size is reset to 3 for target 1, otherwise to 1. Reset excluded. Existing native padding retained. Baseline rebuilds core and recreates padding.',
        'geometry':'Boolean symmetric differences on last repetition per case and final padded models; bounds, volume, solid/lump count and health recorded. Reference is this repository generator, not independently certified Gridfinity CAD.',
        'limits':'One machine and one session; not randomized; undo history, caches and CPU scheduling can affect timings. No sizes above 6x6, screws, connectors, multiple clearance profiles, or other add-in commands were tested.'}
    write_report()
    documents['shaded preview - no model bodies'].parentDocument.activate()
    app.activeViewport.fit()
    return checks

def run_phase(phase):
    """MCP entry helper after import; use bounded phases, retaining this module in sys.modules.

    Order: prepare; baseline-1/3/6; whole-1/3/6; tool-1/3/6;
    padding-baseline-1 ... padding-tool-6; preview;
    resize-whole-1/3/6; resize-tool-1/3/6; regenerate-1/3/6; finish.
    Each generation/resize phase records one initial and five subsequent runs.
    """
    parts = phase.split('-')
    if phase == 'prepare':
        return prepare_tool()
    if phase == 'preview':
        prepare_meshes()
        return preview_case()
    if phase == 'finish':
        return verify_and_finish()
    if parts[0] == 'padding':
        return padding_case(parts[1],int(parts[2]))
    if parts[0] == 'resize':
        return resize_case(parts[1],int(parts[2]))
    if parts[0] == 'regenerate':
        return regeneration_case(int(parts[1]))
    return generate_case(parts[0],int(parts[1]))
