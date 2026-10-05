"""Prepare immutable bin interfaces once, from the original generator."""
import sys,types,importlib,json
from pathlib import Path
import adsk.core,adsk.fusion
ROOT=Path(r'D:\Code Projects\GridfinityWorkshop')
OUT=ROOT/'workshop/presets'

def run(_context: str):
    app=adsk.core.Application.get()
    previous=app.activeDocument
    pkg=types.ModuleType('_gf_bin_source');pkg.__path__=[str(ROOT)];sys.modules[pkg.__name__]=pkg
    base=importlib.import_module(pkg.__name__+'.lib.gridfinityUtils.baseGenerator')
    Base=importlib.import_module(pkg.__name__+'.lib.gridfinityUtils.baseGeneratorInput').BaseGeneratorInput
    lip=importlib.import_module(pkg.__name__+'.lib.gridfinityUtils.binBodyLipGenerator')
    Lip=importlib.import_module(pkg.__name__+'.lib.gridfinityUtils.binBodyLipGeneratorInput').BinBodyLipGeneratorInput
    doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name='Bin interface preset preparation'
    d=adsk.fusion.Design.cast(app.activeProduct)
    d.designIntent=adsk.fusion.DesignIntentTypes.HybridDesignIntentType
    state=types.SimpleNamespace(previous=previous,document=doc,base=base,Base=Base,lip=lip,Lip=Lip)
    sys.modules['gf_bin_presets']=state
    c=d.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    cfg=Base();cfg.baseWidth=cfg.baseLength=4.2;cfg.xyClearance=.025
    cfg.originPoint=adsk.core.Point3D.create(-.025,-.025,0)
    body=base.createSingleGridfinityBaseBody(cfg,c)
    base.cutBaseClearance(cfg,1,1,c)
    mgr=adsk.fusion.TemporaryBRepManager.get()
    assert mgr.exportToFile([body],str(OUT/'bin-foot.smt'))
    print('Foot preset',body.volume*1000)
    for x in range(1,7):
        for y in range(1,7):
            occ=d.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            cfg=Lip();cfg.baseWidth=cfg.baseLength=4.2;cfg.binWidth=x;cfg.binLength=y
            cfg.xyClearance=.025;cfg.binCornerFilletRadius=.375;cfg.origin=adsk.core.Point3D.create(0,0,0)
            body=lip.createGridfinityBinBodyLip(cfg,occ.component)
            assert mgr.exportToFile([body],str(OUT/f'bin-rim-{x}x{y}.smt'))
            occ.deleteMe()
    doc.close(False)
    previous.activate()
