"""Standard cached feet with native, body-scoped cartridge seats and access windows."""
import json,time
import adsk.core,adsk.fusion
from . import bin_generation as bins
from .magazine_request import validate


def generate(data):
    c=validate(data);started=time.perf_counter()
    # Reuse the native command transaction and standard foot/pocket workflow.
    d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    if not d:raise ValueError('Open a parametric Design document.')
    start=d.timeline.count
    previous_counts=[(comp,comp.features.count) for comp in d.allComponents]
    result=bins.generate({**c,'family':'blank','interior':'solid','rim':False,'scoop':False,'label':False},group_timeline=False)
    body=d.findEntityByToken(result['bodyToken'])[0];comp=body.parentComponent
    name=result['name'].removesuffix(' - Body').replace(' - solid',f" - {c['quantity']} seats {c['cartLength']:g}x{c['cartWidth']:g} mm")
    name+=' - '+('access cutouts' if c['magazineCutouts'] else 'closed ends')
    parameter=result['heightParameter']
    d.userParameters.itemByName(parameter).comment=f"Magazine guide top from base; 14..{c['cartridgeHeight']*7-(3 if c['magazineCutouts'] else 17):g} mm. Seats and footprint fixed at creation."
    s=bins.sketch(comp,name+' - Body indexing pockets','7 mm')
    for q in c['seats']:
        if c['orientation']=='0':bins.rectangle(s,q['x']+6.1,q['y'],q['w']-12.2,q['d'])
        else:bins.rectangle(s,q['x'],q['y']+6.1,q['w'],q['d']-12.2)
    bins.extrude(comp,s,parameter+' - 7 mm','Magazine - Body seats and 2 mm floor',bins.OP.CutFeatureOperation,body)
    # Body indexing pockets leave the end stops flush with the guide rim.
    # The layout merges overlapping intervals, allowing one native cut for all windows.
    if c['magazineCutouts']:
        s=bins.sketch(comp,name+' - End access openings','9 mm')
        for q in c['windows']:bins.rectangle(s,q['x'],q['y'],q['w'],q['d'])
        bins.extrude(comp,s,parameter+' - 9 mm','Magazine - Buckle access',bins.OP.CutFeatureOperation,body)
    if not body.isSolid or body.lumps.count!=1:raise RuntimeError('Magazine must be one connected solid.')
    feature_start=next((count for existing,count in previous_counts if existing==comp),0)
    created_features=list(comp.features)[feature_start:]
    issues=[f.errorOrWarningMessage for f in created_features if int(f.healthState)!=0]
    if issues:raise RuntimeError('; '.join(issues))
    body.name=name+' - Magazine'
    if comp!=d.rootComponent:comp.name=name
    body.attributes.itemByName('GridfinityWorkshop','binRecipe').deleteMe()
    body.attributes.add('GridfinityWorkshop','binRecipe',json.dumps(c))
    body.attributes.add('GridfinityWorkshop','matchedCartridge',json.dumps(dict(revision=1,
        lengthMM=c['cartLength']+12.2,widthMM=c['cartWidth'],heightMM=c['cartridgeHeight']*7+3.7,seatZMM=7)))
    features=len(created_features)
    d.timeline.timelineGroups.add(start,d.timeline.count-1).name=name
    return {**result,'name':body.name,'seconds':time.perf_counter()-started,'interior':'magazine','seats':len(c['seats']),
        'capacity':c['capacity'],'overallHeightMM':c['heightMM'],'loadedHeightMM':c['overallMM'],
        'features':features}
