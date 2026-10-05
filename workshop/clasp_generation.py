"""Native clasp template, imported into its own editable design outside Command events."""
import json,re,time
from pathlib import Path
import adsk.core,adsk.fusion
from .bin_request import validate
from .bin_generation import sketch,extrude,collection,E,P,OP


def pattern(component,feature,nx,ny,dx,dy,name):
    if nx==ny==1:return
    i=component.features.rectangularPatternFeatures.createInput(collection([feature]),component.xConstructionAxis,
        E(str(nx)),E(dx),adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    i.directionTwoEntity=component.yConstructionAxis;i.quantityTwo=E(str(ny));i.distanceTwo=E(dy)
    i.patternComputeOption=adsk.fusion.PatternComputeOptions.OptimizedPatternCompute
    f=component.features.rectangularPatternFeatures.add(i);f.name=name


def interior(design,component,c):
    """One dimensioned seed cut; native pattern preserves edits to CellsL/CellsW."""
    def parameter(name,expression):
        return design.userParameters.add(name,E(expression),'mm','Clasp storage layout; keep cavities inside the 2 mm enclosure walls.')
    divided=c['interior']=='divided';channels=c['interior']=='magnets'
    nx=c['channelColumns'] if channels else c['divX'] if divided else 1
    ny=c['channelRows'] if channels else c['divY'] if divided else 1
    gx=c['channelGapX'] if channels else 1.2
    gy=c['channelGapY'] if channels else 1.2
    if channels:
        parameter('ChannelGapX',f'{gx} mm')
        parameter('ChannelGapY','ChannelGapX' if c['channelGapLinked'] else f'{gy} mm')
    ex='ChannelGapX' if channels else '1.2 mm'
    ey='ChannelGapY' if channels else '1.2 mm'
    if channels:
        q=c['cavities'][0];cw=f"{q['w']:g} mm";cd=f"{q['d']:g} mm"
    else:
        cw=f'(Length - 4 mm - {nx-1} * {ex}) / {nx}'
        cd=f'(Width - 4 mm - {ny-1} * {ey}) / {ny}'
    pw=parameter('StorageWidth',cw);pd=parameter('StorageDepth',cd)
    w=pw.value;h=pd.value
    usedw=nx*w+(nx-1)*gx/10;usedh=ny*h+(ny-1)*gy/10
    s=sketch(component,'Clasp - '+('Channel seed' if channels else 'Compartment seed'),'2 mm')
    dims=s.sketchDimensions;orient=adsk.fusion.DimensionOrientations
    def dim(a,b,horizontal,expr):
        q=dims.addDistanceDimension(a,b,orient.HorizontalDimensionOrientation if horizontal else orient.VerticalDimensionOrientation,P(-1,-1,0))
        q.parameter.expression=expr
    if channels and c['channelShape']=='round':
        cx=-(usedw-w)/2;cy=-(usedh-h)/2
        circle=s.sketchCurves.sketchCircles.addByCenterRadius(P(cx,cy,0),w/2)
        dims.addDiameterDimension(circle,P(cx+w,cy+w,0)).parameter.expression='StorageWidth'
        point=circle.centerSketchPoint
        if nx==1 and ny==1:s.geometricConstraints.addCoincident(point,s.originPoint)
        else:
            if nx==1:s.geometricConstraints.addVerticalPoints(point,s.originPoint)
            else:dim(point,s.originPoint,True,f'{nx-1} * (StorageWidth + {ex}) / 2')
            if ny==1:s.geometricConstraints.addHorizontalPoints(point,s.originPoint)
            else:dim(point,s.originPoint,False,f'{ny-1} * (StorageDepth + {ey}) / 2')
    else:
        lines=s.sketchCurves.sketchLines.addTwoPointRectangle(P(-usedw/2,-usedh/2,0),P(-usedw/2+w,-usedh/2+h,0))
        for index,line in enumerate(lines):
            if index%2:s.geometricConstraints.addVertical(line)
            else:s.geometricConstraints.addHorizontal(line)
        dim(lines.item(0).startSketchPoint,lines.item(0).endSketchPoint,True,'StorageWidth')
        dim(lines.item(1).startSketchPoint,lines.item(1).endSketchPoint,False,'StorageDepth')
        point=lines.item(0).startSketchPoint
        dim(point,s.originPoint,True,f'({nx} * StorageWidth + {nx-1} * {ex}) / 2')
        dim(point,s.originPoint,False,f'({ny} * StorageDepth + {ny-1} * {ey}) / 2')
    f=extrude(component,s,'BodyHeight - 0.5 mm','Clasp - Cut storage in body only',OP.CutFeatureOperation,component.bRepBodies.item(0))
    if not s.isFullyConstrained:raise RuntimeError('Storage sketch is not fully constrained.')
    pattern(component,f,nx,ny,f'StorageWidth + {ex}',f'StorageDepth + {ey}','Clasp - Storage array')


def generate(data):
    c=validate(data)
    if c['family']!='clasp':raise ValueError('Expected a clasp recipe.')
    app=adsk.core.Application.get();previous=app.activeDocument
    path=Path(__file__).parent/'presets'/'clasp-template.f3d'
    if not path.is_file():raise ValueError('The clasp template is missing.')
    started=time.perf_counter();doc=None
    try:
        doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
        if not doc:raise RuntimeError('Fusion could not open the clasp template.')
        d=adsk.fusion.Design.cast(app.activeProduct)
        title=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',c['title']).strip() or 'Clasp bin'
        name=f"{title} - {c['cols']}x{c['rows']} {c['height']}U - {c['interior']}"
        if c['magnet']!='off':name+=f" - M{c['diameter']:g}x{c['magnetDepth']:g}"
        if c['interior']=='magnets':name+=f" - {c['channelShape']} {c['channelColumns']}x{c['channelRows']} channels"
        doc.name=name
        values={'CellsL':str(c['cols']),'CellsW':str(c['rows']),'HeightUnits':str(c['height']),
                'BuckleExtra':f"{c['buckle']} mm",'GripThickness':f"{c['grip']} mm"}
        if c['magnet']!='off':values.update(BaseMagnetHole=f"{c['diameter']} mm",BaseMagnetDepth=f"{c['magnetDepth']} mm")
        # Roll back once so each parameter assignment does not rebuild the assembly.
        d.timeline.markerPosition=0
        for key,value in values.items():d.userParameters.itemByName(key).expression=value
        d.timeline.moveToEnd()
        configure_pins(d,c)
        body=next(comp for comp in d.allComponents if comp.name=='Body')
        if c['magnet']!='off':
            for key in ('Extrude13','Base magnets per cell','Base magnets all cells'):body.features.itemByName(key).isSuppressed=False
        interior(d,body,c)
        d.computeAll()
        issues=[f'{comp.name}: {f.name}: {f.errorOrWarningMessage}' for comp in d.allComponents for f in comp.features if not f.isSuppressed and int(f.healthState)!=0]
        if issues:raise RuntimeError('; '.join(issues))
        parts=[]
        for comp in d.allComponents:
            if comp==d.rootComponent:continue
            role=comp.name
            for b in comp.bRepBodies:
                if not b.isSolid or b.lumps.count!=1:raise RuntimeError(f'{role} is not a connected solid.')
                b.name=name+' - '+role;parts.append(b.name)
            comp.name=name+' - '+role
            for s in comp.sketches:s.isVisible=False
        if len(parts)!=3:raise RuntimeError('Expected one body, lid and buckle.')
        d.rootComponent.attributes.add('GridfinityWorkshop','binRecipe',json.dumps(c))
        d.timeline.timelineGroups.add(0,d.timeline.count-1).name='Clasp enclosure - native template and storage'
        app.activeViewport.fit()
        return dict(name=name,parts=parts,seconds=time.perf_counter()-started,overallHeightMM=c['overallMM'],newDocument=True,
                    parameters=['CellsL','CellsW','HeightUnits','BuckleExtra','PinDiameter','PinAllowance','GripThickness'],channels=len(c['cavities']) if c['interior']=='magnets' else 0)
    except Exception:
        if doc:doc.close(False)
        if previous and previous.isValid:previous.activate()
        raise


def configure_pins(design,c,model_ids=('d24','d80','d93','d121')):
    def add(name,expr,comment):
        p=design.userParameters.itemByName(name)
        if p:p.expression=expr
        else:design.userParameters.add(name,E(expr),'mm',comment)
    add('PinDiameter',f"{c['pinDiameter']} mm",'Physical pin diameter.')
    add('PinAllowance',f"{c['pinAllowance']} mm",'Added to the full diameter, not per side.')
    for index,(key,param,bore,model) in enumerate([('bodyPinAllowance','BodyPinAllowance','BodyPinBore','d24'),
        ('lidPinAllowance','LidPinAllowance','LidHingeBore','d80'),
        ('lidLatchAllowance','LidLatchAllowance','LidLatchBore','d93'),
        ('bucklePinAllowance','BucklePinAllowance','BucklePinBore','d121')]):
        add(param,f"{c[key]} mm" if c['pinOverrides'] else 'PinAllowance','Per-part full-diameter allowance.')
        add(bore,'PinDiameter + '+param,'Resulting bore diameter; keep within 1.8..2.7 mm.')
        design.allParameters.itemByName(model_ids[index]).expression=bore
    design.userParameters.itemByName('PinHole').expression='BodyPinBore'
    design.userParameters.itemByName('PinHole').comment='Legacy alias for BodyPinBore. Edit PinDiameter / PinAllowance.'
