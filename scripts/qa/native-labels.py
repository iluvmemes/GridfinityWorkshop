"""Fusion MCP: disposable labeled lids and the production colored 3MF exporter."""
import adsk.core,adsk.fusion,sys,json,importlib,zipfile
from xml.etree import ElementTree as ET

def run(_context: str):
    app=adsk.core.Application.get();previous=app.activeDocument
    m=sys._qa_module
    exporter=importlib.import_module(m.generation.__package__+'.lid_export')
    rows=[]
    for mode in ('cutout','raised','embedded'):
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name='QA labeled lid '+mode
        recipe=dict(family='standard',title='QA label',cols=2,rows=1,height=6,interior='open',rim=False,
                    magnet='off',scoop=False,label=False,dovetailLid=True,lidLabelMode=mode,
                    lidLabelText='BO8',lidLabelFont='rubik',lidLabelHeight=4,lidLabelDepth=.6,
                    lidLabelLayout='single',lidColor='blue',lidLabelColor='white')
        result=m.catalog.bin_generation.generate(recipe)
        design=adsk.fusion.Design.cast(app.activeProduct)
        lid=design.findEntityByToken(result['lidToken'])[0]
        assert lid.isSolid and lid.lumps.count==1
        labels=[design.findEntityByToken(t)[0] for t in result['labelTokens']]
        assert bool(labels)==(mode in ('raised','embedded'))
        assert all(b.isSolid for b in labels)
        filename=sys._gf_qa_out/('label-'+mode+'.3mf')
        exported=exporter.export_latest(result,filename)
        with zipfile.ZipFile(filename) as archive:
            model=ET.fromstring(archive.read('3D/3dmodel.model'))
            ns={'c':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
            assert model.get('unit')=='millimeter'
            assert len(model.findall('c:build/c:item',ns))==1
            meshes=model.findall('c:resources/c:object/c:mesh',ns)
            assert len(meshes)==(2 if labels else 1)
            assert all(len(mesh.findall('c:triangles/c:triangle',ns))>0 for mesh in meshes)
        assert not [f.name for c in design.allComponents for f in c.features if not f.isSuppressed and int(f.healthState)!=0]
        rows.append({'mode':mode,'pass':True,'labelBodies':len(labels),'exported':exported})
        doc.close(False)
    previous.activate()
    (sys._gf_qa_out/'native-label-results.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    print(json.dumps(rows))
