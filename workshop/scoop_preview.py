"""Small, cached custom-graphics study. Never creates manufacturing geometry."""
import json,time
from pathlib import Path
import adsk.core,adsk.fusion

_document=None
_group=None
_asset=None


def counts(design):
    return dict(bodies=sum(c.bRepBodies.count for c in design.allComponents),
                sketches=sum(c.sketches.count for c in design.allComponents),
                meshBodies=sum(c.meshBodies.count for c in design.allComponents),timeline=design.timeline.count)


def show(mode='solid'):
    global _document,_group,_asset
    if mode not in ('solid','ghost'):raise ValueError('Choose solid or ghost preview.')
    if _asset is None:
        _asset=json.loads((Path(__file__).parent/'preview-assets'/'standard-scoop.json').read_text(encoding='utf-8'))
    app=adsk.core.Application.get()
    if app.userInterface.activeCommand!='SelectCommand':
        raise ValueError('Finish or cancel the active Fusion command before opening the demo.')
    fresh=_document is None or not _document.isValid
    if fresh:
        _document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        _document.name='Scoop preview demo - 2x2 6U - graphics only'
        _group=None
    else:_document.activate()
    design=adsk.fusion.Design.cast(app.activeProduct);before=counts(design)
    started=time.perf_counter()
    if _group is not None and _group.isValid:_group.deleteMe()
    group=design.rootComponent.customGraphicsGroups.add();group.isSelectable=False
    color=adsk.core.Color.create(62,143,205,255)
    group.color=adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(color,color,
        adsk.core.Color.create(170,200,220,255),adsk.core.Color.create(0,0,0,255),20,1 if mode=='solid' else .4)
    coords=adsk.fusion.CustomGraphicsCoordinates.create(_asset['coordinates'])
    group.addMesh(coords,_asset['indices'],_asset['normals'],[])
    points=[];lengths=[]
    for line in _asset['lines']:
        points.extend(line);lengths.append(len(line)//3)
    edges=group.addLines(adsk.fusion.CustomGraphicsCoordinates.create(points),[],True,lengths)
    edges.color=adsk.fusion.CustomGraphicsSolidColorEffect.create(adsk.core.Color.create(27,77,112,255))
    _group=group
    if fresh:
        cam=app.activeViewport.camera;cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
        cam.target=adsk.core.Point3D.create(4.175,4.175,2.29)
        cam.eye=adsk.core.Point3D.create(16.175,22.175,22.29)
        cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isSmoothTransition=False;cam.isFitView=True
        app.activeViewport.camera=cam
    app.activeViewport.visualStyle=adsk.core.VisualStyles.ShadedVisualStyle
    app.activeViewport.refresh()
    after=counts(design)
    assert before==after==dict(bodies=0,sketches=0,meshBodies=0,timeline=0)
    return dict(mode=mode,triangles=len(_asset['indices'])//3,seconds=time.perf_counter()-started,
                counts=after,scoopRadiusMM=25,document=_document.name)
