"""Run through Fusion MCP. Prepare actual-model line art and a cached scoop demo.

All preparation happens in disposable documents; runtime preview uses graphics only.
"""
import importlib,json,math,sys
from pathlib import Path
import adsk.core,adsk.fusion

ROOT=Path(__file__).parent/'GridfinityUIPreview'
P=adsk.core.Point3D.create
V=adsk.core.Vector3D.create


def mesh_record(body):
    calculator=body.meshManager.createMeshCalculator()
    calculator.surfaceTolerance=.005
    mesh=calculator.calculate()
    lines=[]
    for edge in body.edges:
        ok,start,end=edge.evaluator.getParameterExtents();assert ok
        ok,points=edge.evaluator.getStrokes(start,end,.005);assert ok
        lines.append([v for p in points for v in (p.x,p.y,p.z)])
    return dict(coordinates=list(mesh.nodeCoordinatesAsDouble),indices=list(mesh.nodeIndices),
                normals=list(mesh.normalVectorsAsDouble),lines=lines)


def camera(app,bodies):
    box=bodies[0].boundingBox.copy()
    for body in bodies[1:]:box.combine(body.boundingBox)
    center=P((box.minPoint.x+box.maxPoint.x)/2,(box.minPoint.y+box.maxPoint.y)/2,(box.minPoint.z+box.maxPoint.z)/2)
    cam=app.activeViewport.camera
    cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
    cam.target=center;cam.eye=P(center.x+12,center.y+18,center.z+22);cam.upVector=V(0,0,1)
    cam.isSmoothTransition=False;cam.isFitView=True;app.activeViewport.camera=cam
    cam=app.activeViewport.camera;ok,w,h=cam.getExtents();assert ok
    cam.isFitView=False;cam.setExtents(w*1.2,h*1.2);app.activeViewport.camera=cam


def run(_context):
    app=adsk.core.Application.get();original=app.activeDocument
    originals=[(d,d.name,d.isModified) for d in app.documents]
    module=next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and str(getattr(m,'__file__','')).replace('\\','/').endswith('/GridfinityUIPreview/GridfinityUIPreview.py'))
    pkg=module.generation.__package__
    bins=importlib.import_module(pkg+'.bin_generation')
    configs=module.catalog._last_response['report']['state']['configs']
    mgr=adsk.fusion.TemporaryBRepManager.get()
    art=ROOT/'catalog-art';art.mkdir(exist_ok=True)
    assets=ROOT/'preview-assets';assets.mkdir(exist_ok=True)
    sources={};report={}
    oldstyle=app.activeViewport.visualStyle
    for family in ('standard','blank','clasp','cartridge','magazine','tests'):
        cfg=dict(configs[family],family=family,title='Illustration source',scoop=False,label=False,dovetailLid=False,magnet='off')
        if family in ('standard','blank','magazine'):
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            cfg.update(cols=2,rows=2 if family!='magazine' else 1,height=6 if family!='magazine' else 2,
                       interior='solid' if family=='blank' else 'open',rim=family=='standard')
            if family=='magazine':
                cfg.update(cartLength=68,cartWidth=17.5,cartridgeHeight=8,quantity=2,slot=.3,orientation='0',magazineCutouts=False)
                importlib.import_module(pkg+'.magazine_generation').generate(cfg)
            else:bins.generate(cfg)
        elif family in ('clasp','cartridge'):
            cfg.update(cols=2,rows=1,height=6,interior='open',cartLength=68,cartWidth=17.5)
            importlib.import_module(pkg+'.'+family+'_generation').generate(cfg);doc=app.activeDocument
        else:
            cfg.update(testType='pin',testSource='clasp',testCount=3,testStart=.15,testStep=.1)
            importlib.import_module(pkg+'.fit_test_generation').generate(cfg);doc=app.activeDocument
        doc.name='Workshop illustration source - '+family
        design=adsk.fusion.Design.cast(app.activeProduct)
        bodies=[b for c in design.allComponents for b in c.bRepBodies]
        assert all(b.isSolid for b in bodies)
        sources[family]=[mgr.copy(b) for b in bodies]
        doc.close(False)
    # Add a quarter-circle scoop to the standard source using temporary BRep only.
    standard=mgr.copy(sources['standard'][0])
    ramp=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(P(4.175,1.425,1.95),V(1,0,0),V(0,1,0),7.97,2.55,2.5))
    cutter=mgr.createCylinderOrCone(P(0,2.7,3.2),2.5,P(8.35,2.7,3.2),2.5)
    assert mgr.booleanOperation(ramp,cutter,adsk.fusion.BooleanTypes.DifferenceBooleanType)
    assert mgr.booleanOperation(standard,ramp,adsk.fusion.BooleanTypes.UnionBooleanType)
    assert standard.isSolid and standard.lumps.count==1
    sources['standard']=[standard]
    demo=mesh_record(standard)
    demo.update(schema=1,units='cm',grid=[2,2],heightU=6,scoopRadiusMM=25,source='Standard generator with a demo-only quarter-circle scoop',boundsMM=[83.5,83.5,45.8])
    (assets/'standard-scoop.json').write_text(json.dumps(demo,separators=(',',':')),encoding='utf-8')
    for family,bodies in sources.items():
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.name='Line illustration - '+family
        design=adsk.fusion.Design.cast(app.activeProduct)
        feature=bins.insert(design.rootComponent,bodies,'Actual category geometry')
        design.rootComponent.isOriginFolderLightBulbOn=False
        design.rootComponent.isConstructionFolderLightBulbOn=False
        camera(app,list(feature.bodies))
        app.activeViewport.visualStyle=adsk.core.VisualStyles.WireframeWithVisibleEdgesOnlyVisualStyle
        app.activeViewport.refresh()
        options=adsk.core.SaveImageFileOptions.create(str(art/(family+'.png')))
        options.width=720;options.height=560;options.isAntiAliased=True;options.isBackgroundTransparent=True
        assert app.activeViewport.saveAsImageFileWithOptions(options)
        report[family]=dict(bodies=len(bodies),source='Native BRep, orthographic visible-edge capture',file=family+'.png')
        doc.close(False)
    original.activate();app.activeViewport.visualStyle=oldstyle
    assert all(d.isValid and d.name==name and d.isModified==modified for d,name,modified in originals)
    (art/'model-art-manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(art=report,previewTriangles=len(demo['indices'])//3)))
