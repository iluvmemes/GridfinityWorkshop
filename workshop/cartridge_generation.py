"""Editable cartridge enclosure, isolated in a new design imported from its native preset."""
import json,re,time
from pathlib import Path
import adsk.core,adsk.fusion
from .bin_request import validate
from .clasp_generation import interior,configure_pins


def generate(data,*,storage_builder=None):
    c=validate(data)
    if c['family']!='cartridge':raise ValueError('Expected a cartridge recipe.')
    app=adsk.core.Application.get();previous=app.activeDocument;doc=None
    path=Path(__file__).parent/'presets'/'cartridge-template.f3d'
    if not path.is_file():raise ValueError('The cartridge template is missing.')
    started=time.perf_counter()
    try:
        doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
        if not doc:raise RuntimeError('Fusion could not open the cartridge template.')
        d=adsk.fusion.Design.cast(app.activeProduct)
        title=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',c['title']).strip() or 'Cartridge'
        name=f"{title} - {c['cartLength']:g}x{c['cartWidth']:g} mm {c['height']}U - {c['interior']}"
        if c['interior']=='magnets':name+=f" - {c['channelShape']} {c['channelColumns']}x{c['channelRows']} channels"
        doc.name=name
        d.timeline.markerPosition=0
        for key,value in {'Length':f"{c['cartLength']} mm",'Width':f"{c['cartWidth']} mm",
            'HeightUnits':str(c['height']),'BuckleExtra':f"{c['buckle']} mm",'GripThickness':f"{c['grip']} mm"}.items():
            d.userParameters.itemByName(key).expression=value
        d.timeline.moveToEnd()
        configure_pins(d,c,('d32','d87','d100','d129'))
        body=next(comp for comp in d.allComponents if comp.name=='Body')
        # A local one-off builder can reuse the proven enclosure and fit controls.
        # The public catalog always takes the normal validated interior path.
        (storage_builder or interior)(d,body,c)
        # Shared storage builder uses exactly the same 2 mm walls and floor.
        for comp in d.allComponents:
            for obj in list(comp.features)+list(comp.sketches):
                if obj.name.startswith('Clasp - '):obj.name=obj.name.replace('Clasp - ','Cartridge - ',1)
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
        if len(parts)!=3:raise RuntimeError('Expected one cartridge body, lid and buckle.')
        d.rootComponent.attributes.add('GridfinityWorkshop','binRecipe',json.dumps(c))
        d.rootComponent.attributes.add('GridfinityWorkshop','cartridgeEnvelope',json.dumps(dict(
            revision=1,lengthMM=c['widthMM'],widthMM=c['depthMM'],heightMM=c['overallMM'],flatBase=True)))
        d.timeline.timelineGroups.add(0,d.timeline.count-1).name='Cartridge enclosure - native template and storage'
        app.activeViewport.fit()
        return dict(name=name,parts=parts,seconds=time.perf_counter()-started,newDocument=True,
            overallHeightMM=c['overallMM'],parameters=['Length','Width','HeightUnits','BuckleExtra','PinDiameter','PinAllowance','GripThickness'],
            channels=len(c['cavities']) if c['interior']=='magnets' else 0)
    except Exception:
        if doc:doc.close(False)
        if previous and previous.isValid:previous.activate()
        raise
