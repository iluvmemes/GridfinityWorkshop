"""Fusion MCP one-off batch. Uses the catalog cartridge generator and preserves originals."""
import collections,importlib,itertools,json,sys,time
from pathlib import Path
import adsk.core,adsk.fusion

ROOT=Path(r'D:\Code Projects\GridfinityWorkshop\outputs\magnet-cartridge-set-ascending-2026-10-04')


def run(_context):
    app=adsk.core.Application.get();previous=app.activeDocument
    originals=[(doc,doc.name,doc.isModified) for doc in app.documents]
    m=next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and str(getattr(m,'__file__','')).replace('\\','/').endswith('/workshop/app.py'))
    pkg=m.generation.__package__;g=importlib.reload(importlib.import_module(pkg+'.cartridge_generation'))
    b=importlib.import_module(pkg+'.bin_generation');mgr=adsk.fusion.TemporaryBRepManager.get()
    plan=json.loads((ROOT/'channel-layout.json').read_text(encoding='utf-8'))
    cfg=m.catalog._last_response['report']['state']['configs']['cartridge'].copy()
    cfg.update(family='cartridge',cartLength=68,cartWidth=17.5,height=8,interior='magnets',channelShape='round',
        storedDiameter=3,storedClearance=.5,channelColumns=1,channelRows=1,channelGapX=3,channelGapY=3,channelGapLinked=True)
    plan['fitSettings']={key:cfg[key] for key in ['buckle','grip','pinDiameter','pinAllowance','pinOverrides',
        'bodyPinAllowance','lidPinAllowance','lidLatchAllowance','bucklePinAllowance']}
    snapshots=[];results=[];counts=collections.Counter()
    for spec in plan['cartridges']:
        started=time.perf_counter()
        def storage(design,comp,c):
            # Revalidate the imported plan before building any channels.
            qs=spec['channels'];assert len(qs) in (4,8,12)
            for i,q in enumerate(qs):
                r=q['diameterMM']/2;assert abs(q['diameterMM']-(q['sizeMM']+.5))<1e-8
                assert abs(q['x'])+r<=32+1e-8 and abs(q['y'])+r<=6.75+1e-8
                for other in qs[i+1:]:
                    assert ((q['x']-other['x'])**2+(q['y']-other['y'])**2)**.5-r-other['diameterMM']/2>=3-1e-8
            s=b.sketch(comp,spec['id']+' - Mixed magnet channels','2 mm')
            for q in qs:
                circle=s.sketchCurves.sketchCircles.addByCenterRadius(b.P(q['x']/10,q['y']/10,0),q['diameterMM']/20)
                circle.isFixed=True
            b.extrude(comp,s,'BodyHeight - 0.5 mm',spec['id']+' - Cut mixed channels in body only',b.OP.CutFeatureOperation,comp.bRepBodies.item(0))
            assert s.isFullyConstrained
            c.update(oneOffMixedChannels=spec['channels'],oneOffId=spec['id'],channelLayoutFixed=True,
                cavities=[dict(x=q['x']+34-q['diameterMM']/2,y=q['y']+8.75-q['diameterMM']/2,
                    w=q['diameterMM'],d=q['diameterMM'],r=0,round=True) for q in qs])
        g.generate(dict(cfg,title=spec['name']),storage_builder=storage)
        doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);doc.name=spec['name']+' - 68x17.5 mm 8U'
        parts={}
        for comp in d.allComponents:
            if comp==d.rootComponent:continue
            role=comp.name.rsplit(' - ',1)[-1]
            comp.name=spec['name']+' - '+role
            body=comp.bRepBodies.item(0);body.name=comp.name;parts[role]=body
            assert body.isSolid and body.lumps.count==1
        assert set(parts)=={'Body','Lid','Buckle'}
        cylinders=[f.geometry for f in parts['Body'].faces if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.axis.z)>.999
            and any(abs(f.geometry.radius*20-q['diameterMM'])<1e-6 for q in spec['channels'])]
        assert len(cylinders)==len(spec['channels'])
        for q in spec['channels']:
            assert any(abs(c.radius*20-q['diameterMM'])<1e-6 and abs(c.origin.x*10-q['x'])<1e-6 and abs(c.origin.y*10-q['y'])<1e-6 for c in cylinders)
            assert parts['Body'].pointContainment(b.P(q['x']/10,q['y']/10,.1))==adsk.fusion.PointContainment.PointInsidePointContainment
            assert parts['Body'].pointContainment(b.P(q['x']/10,q['y']/10,.3))==adsk.fusion.PointContainment.PointOutsidePointContainment
            counts[q['sizeMM']]+=1
        for a,tool in itertools.combinations(parts.values(),2):
            probe=mgr.copy(a);assert mgr.booleanOperation(probe,tool,adsk.fusion.BooleanTypes.IntersectionBooleanType)
            assert probe.volume<1e-9
        assert all(int(f.healthState)==0 for comp in d.allComponents for f in comp.features)
        d.timeline.timelineGroups.item(0).name=spec['name']+' - enclosure and channels; plain lid'
        d.rootComponent.attributes.add('GridfinityWorkshop','mixedChannelSet',json.dumps(spec))
        folder=ROOT/spec['id'];folder.mkdir(exist_ok=True)
        stem=spec['id']+'_'+ '_'.join(str(n)+'mm' for n in spec['sizesMM'])+'_4-each_8U'
        assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(folder/(stem+'.f3d'))))
        for role,body in parts.items():
            options=d.exportManager.createSTLExportOptions(body,str(folder/(stem+'_'+role+'.stl')))
            options.isBinaryFormat=True;options.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
            options.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            assert d.exportManager.execute(options)
        snapshots.append((spec,[(role,mgr.copy(body)) for role,body in parts.items()]))
        results.append(dict(id=spec['id'],sizesMM=spec['sizesMM'],channels=len(spec['channels']),
            minimumSeparationMM=spec['minimumSeparationMM'],channelDepthToOpeningMM=55.5,closedHeightMM=59.7,
            measuredChannelsVerified=True,plainLid=True,lidVolumeCM3=parts['Lid'].volume,lidFaces=parts['Lid'].faces.count,overlapMM3=0,seconds=time.perf_counter()-started))
        (ROOT/'verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        doc.close(False)
    assert counts=={size:4 for size in range(3,14)}
    plan['verification']=results;(ROOT/'channel-layout.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    # A compact inspection assembly; individual archives retain the editable native histories.
    overview=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);overview.name='Ascending magnet cartridge set - 3 to 13 mm - 44 channels'
    d=adsk.fusion.Design.cast(app.activeProduct)
    for index,(spec,parts) in enumerate(snapshots):
        comp=d.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component;comp.name=spec['name']
        copies=[]
        for role,body in parts:
            t=adsk.core.Matrix3D.create();t.translation=adsk.core.Vector3D.create((index%2)*9,(index//2)*3.5,0)
            assert mgr.transform(body,t);copies.append(body)
        feature=b.insert(comp,copies,spec['id']+' - Verified cartridge assembly')
        for body,(role,source) in zip(feature.bodies,parts):body.name=spec['name']+' - '+role
        comp.attributes.add('GridfinityWorkshop','mixedChannelLayout',json.dumps(spec))
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(ROOT/'Complete-set-overview.f3d')))
    for comp in d.allComponents:
        for body in comp.bRepBodies:
            if body.name.endswith(' - Lid'):body.isLightBulbOn=False
    app.activeViewport.fit()
    assert all(doc.isValid and doc.name==name and doc.isModified==modified for doc,name,modified in originals)
    print(json.dumps(dict(cartridges=len(results),channels=sum(counts.values()),sizes=dict(counts),output=str(ROOT),results=results)))
