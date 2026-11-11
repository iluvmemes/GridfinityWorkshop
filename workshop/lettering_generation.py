"""SVG-only lettering on planar faces and printable font comparison plates."""
import json,math,tempfile,time
from pathlib import Path
import adsk.core,adsk.fusion
from . import lettering
from .bin_generation import P,E,OP,sketch,rectangle,extrude
from .generation import collection

COMMAND_ID='GridfinityWorkshop_Lettering_Create'
_handlers=[]
_pending=None
_status=lambda message:None

def bounds(s):
    boxes=[c.boundingBox for c in s.sketchCurves if not c.isConstruction]
    if not boxes:raise ValueError('The SVG did not produce any sketch curves.')
    return (min(b.minPoint.x for b in boxes),min(b.minPoint.y for b in boxes),
            max(b.maxPoint.x for b in boxes),max(b.maxPoint.y for b in boxes))

def filled_profiles(s):
    """Select alternating nested regions, preserving counters and islands.

    A counter's outer boundary is another region's inner boundary. Build the
    adjacency using the actual sketch entities (not centroid guesses, which fail
    for letters such as B and O). Entity tokens are only keys within this read.
    """
    profiles=list(s.profiles)
    def signature(loop):return frozenset(pc.sketchEntity.entityToken for pc in loop.profileCurves)
    outer={};inners={}
    for i,p in enumerate(profiles):
        for loop in p.profileLoops:
            if loop.isOuter:outer[i]=signature(loop)
            else:inners.setdefault(i,[]).append(signature(loop))
    parents={child:parent for child,key in outer.items() for parent,keys in inners.items() if key in keys}
    def depth(i):
        seen=set()
        while i in parents:
            if i in seen:raise ValueError('SVG regions could not be resolved. Flatten overlapping outlines first.')
            seen.add(i);i=parents[i]
        return len(seen)
    result=[p for i,p in enumerate(profiles) if depth(i)%2==0]
    if not result:raise ValueError('The SVG has no closed printable profiles.')
    return result

def import_art(comp,s,svg,height,max_width,x=0,y=0,center=True,rotation=0):
    """Measure Fusion's SVG interpretation and normalize physical size explicitly.

    SVG units/viewBox handling varies between exporters. A temporary XY sketch
    provides measured bounds; the final import uses a uniform scale in cm.
    """
    probe=comp.sketches.add(comp.xYConstructionPlane)
    try:
        with tempfile.TemporaryDirectory(prefix='workshop-svg-') as tmp:
            path=Path(tmp)/'outlines.svg';path.write_text(svg,encoding='utf8')
            if not probe.importSVG(str(path),0,0,1):raise ValueError('Fusion could not import this SVG.')
            a,b,c,d=bounds(probe);w=c-a;h=d-b
            if min(w,h)<=1e-8 or not all(math.isfinite(v) for v in (a,b,c,d)):raise ValueError('SVG has invalid or empty bounds.')
            scale=min(height/10/h,max_width/10/w)
            ox=x/10-(a+(w/2 if center else 0))*scale
            oy=y/10-(b+(h/2 if center else 0))*scale
            if not s.importSVG(str(path),ox,oy,scale):raise ValueError('Fusion could not place this SVG.')
    finally:
        probe.deleteMe()
    s.isComputeDeferred=False
    actual=bounds(s)
    actual_width=(actual[2]-actual[0])*10;actual_height=(actual[3]-actual[1])*10
    if abs(actual_width-w*scale*10)>.01 or abs(actual_height-h*scale*10)>.01:
        raise ValueError('SVG dimensions changed on final import. Export a plain SVG with flattened transforms.')
    if rotation:
        for curve in s.sketchCurves:curve.isFixed=False
        for point in s.sketchPoints:
            if not point.isReference:point.isFixed=False
        matrix=adsk.core.Matrix3D.create()
        matrix.setToRotation(math.radians(rotation),adsk.core.Vector3D.create(0,0,1),P(x/10,y/10,0))
        if not s.move(collection(list(s.sketchCurves)),matrix):raise ValueError('Could not rotate the SVG.')
    return dict(width=actual_width,height=actual_height)

def apply_profiles(comp,s,body,operation,depth,sign=1,name='Outlined lettering'):
    profiles=filled_profiles(s)
    op={'engrave':OP.CutFeatureOperation,'raised':OP.JoinFeatureOperation,'separate':OP.NewBodyFeatureOperation}[operation]
    i=comp.features.extrudeFeatures.createInput(collection(profiles),op)
    distance=depth*sign*(-1 if operation=='engrave' else 1)
    i.setDistanceExtent(False,E(f'{distance:g} mm'))
    if operation!='separate':i.participantBodies=[body]
    f=comp.features.extrudeFeatures.add(i);f.name=name
    if int(f.healthState)!=0:raise RuntimeError(f.errorOrWarningMessage)
    for b in f.bodies:
        if not b.isSolid:raise ValueError('The artwork did not produce solid geometry.')
        if operation=='separate':b.name=name+' - color body'
    s.isVisible=False
    return f

def on_face(data,face,point):
    c=lettering.validate(data)
    if not isinstance(face.geometry,adsk.core.Plane):raise ValueError('Choose a planar face.')
    if face.assemblyContext:
        occurrence=face.assemblyContext
        if occurrence.isReferencedComponent:raise ValueError('Edit the linked source design before adding lettering to it.')
        inverse=occurrence.transform2.copy();inverse.invert()
        point=point.copy();point.transformBy(inverse);face=face.nativeObject
    comp=face.body.parentComponent
    # addWithoutEdges keeps the selected face perimeter out of SVG profile selection.
    s=comp.sketches.addWithoutEdges(face);s.name='SVG outlines - '+(c['text'][:24] if c['source']=='text' else 'Imported artwork')
    p=s.modelToSketchSpace(point)
    dimensions=import_art(comp,s,c['svg'],c['height'],c['maxWidth'],p.x*10+c['offsetX'],p.y*10+c['offsetY'],rotation=c['rotation'])
    ok,normal=face.evaluator.getNormalAtPoint(point)
    if not ok:raise ValueError('Could not determine the face direction.')
    z=s.xDirection.crossProduct(s.yDirection)
    sign=1 if normal.dotProduct(z)>0 else -1
    f=apply_profiles(comp,s,face.body,c['operation'],c['depth'],sign,s.name)
    f.attributes.add('GridfinityWorkshop','letteringRecipe',json.dumps({k:v for k,v in c.items() if k!='svg'}))
    return dict(dimensions,operation=c['operation'],bodies=f.bodies.count)

def coupon():
    app=adsk.core.Application.get();previous=app.activeDocument;doc=None;start=time.perf_counter()
    try:
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name='Workshop - Font comparison 2 3 4 5 mm'
        design=adsk.fusion.Design.cast(app.activeProduct);root=design.rootComponent
        plates=lettering.coupon_plan()
        for index,plate in enumerate(plates):
            occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());comp=occ.component;comp.name=plate['name']
            s=sketch(comp,'2 mm comparison plate','0 mm');rectangle(s,0,0,plate['w'],plate['d'])
            body=extrude(comp,s,'2 mm','Comparison plate').bodies.item(0);body.name=plate['name']+' - font coupon'
            for row in plate['rows']:
                s=sketch(comp,row['label']+' - SVG outlines','2 mm');s.isComputeDeferred=False
                size=import_art(comp,s,row['svg'],row['height'],row['width'],row['x'],row['y'],center=False)
                if abs(size['height']-row['height'])>.01:raise RuntimeError('Coupon letter height changed during import.')
                apply_profiles(comp,s,body,row['operation'],row['depth'],name=row['label'])
            move=adsk.core.Matrix3D.create();move.translation=adsk.core.Vector3D.create(index*12.8,0,0);occ.transform2=move
        issues=[f.errorOrWarningMessage for comp in design.allComponents for f in comp.features if not f.isSuppressed and int(f.healthState)!=0]
        if issues:raise RuntimeError('; '.join(issues))
        root.attributes.add('GridfinityWorkshop','fontCoupon','2,3,4,5 mm; R=raised E=engraved; depth=0.6 mm; plate=2 mm')
        app.activeViewport.fit()
        return dict(name=doc.name,seconds=time.perf_counter()-start,plates=2,sizes=[2,3,4,5])
    except Exception:
        if doc:doc.close(False)
        if previous and previous.isValid:previous.activate()
        raise

class Execute(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__();self.attempted=False
    def notify(self,args):
        self.attempted=True
        try:
            command=args.firingEvent.sender
            selection=command.commandInputs.itemById('letteringFace').selection(0)
            result=on_face(_pending,selection.entity,selection.point)
            _status('Created outlined lettering: '+f"{result['width']:.2f} × {result['height']:.2f} mm. One action, one undo.")
        except Exception as error:
            args.executeFailed=True;args.executeFailedMessage=str(error);_status(str(error))

class Destroy(adsk.core.CommandEventHandler):
    def __init__(self,execute):
        super().__init__();self.execute=execute
    def notify(self,args):
        global _pending
        _pending=None
        if not self.execute.attempted:_status('Lettering placement cancelled; no geometry created.')
        for handler in (self.execute,self):
            if handler in _handlers:_handlers.remove(handler)

class Created(adsk.core.CommandCreatedEventHandler):
    def notify(self,args):
        command=args.command;command.isRepeatable=False;command.isExecutedWhenPreEmpted=False
        select=command.commandInputs.addSelectionInput('letteringFace','Placement face','Click a planar face at the center of your lettering')
        select.addSelectionFilter('PlanarFaces');select.setSelectionLimits(1,1)
        command.commandInputs.addTextBoxCommandInput('letteringHint','',
            'Click the face where the lettering should be centered. X/Y offsets and rotation use the face sketch axes. Separate bodies extend outward for filament assignment.',3,True)
        execute=Execute();destroy=Destroy(execute);command.execute.add(execute);command.destroy.add(destroy);_handlers.extend([execute,destroy])

def start(status):
    global _status
    _status=status
    ui=adsk.core.Application.get().userInterface
    if not ui.commandDefinitions.itemById(COMMAND_ID):
        definition=ui.commandDefinitions.addButtonDefinition(COMMAND_ID,'Place outlined lettering','Select a planar face for SVG lettering.')
        handler=Created();definition.commandCreated.add(handler);_handlers.append(handler)

def stop():
    global _pending
    _pending=None
    definition=adsk.core.Application.get().userInterface.commandDefinitions.itemById(COMMAND_ID)
    if definition:definition.deleteMe()
    _handlers.clear()

def request(data):
    global _pending
    if _pending is not None:raise ValueError('Finish the current lettering placement first.')
    c=lettering.validate(data);app=adsk.core.Application.get();design=adsk.fusion.Design.cast(app.activeProduct)
    if app.userInterface.activeCommand!='SelectCommand':raise ValueError('Finish the active Fusion command first.')
    if not design or design.designType!=adsk.fusion.DesignTypes.ParametricDesignType:raise ValueError('Open a parametric Fusion design first.')
    if design.timeline.markerPosition!=design.timeline.count:raise ValueError('Move the timeline to the end first.')
    _pending=c
    if not app.userInterface.commandDefinitions.itemById(COMMAND_ID).execute():
        _pending=None;raise RuntimeError('Could not start lettering placement.')
