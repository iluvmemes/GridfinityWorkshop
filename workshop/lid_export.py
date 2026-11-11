"""Colored, aligned lid 3MF export. Standard named parts, no printer profiles."""
import struct,zipfile,tempfile,json
from pathlib import Path
from xml.etree import ElementTree as ET

NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)
def node(tag,**attrs):return ET.Element('{'+NS+'}'+tag,{k:str(v) for k,v in attrs.items()})

def triangles(path):
    data=path.read_bytes();count=struct.unpack_from('<I',data,80)[0]
    if len(data)!=84+count*50:raise ValueError('Expected a binary STL: '+str(path))
    for i in range(count):
        values=struct.unpack_from('<12fH',data,84+i*50)[3:12]
        yield [tuple(values[j:j+3]) for j in (0,3,6)]

def mesh_object(paths,identifier,name,color,offset=(0,0,0)):
    obj=node('object',id=identifier,type='model',name=name,pid=1,pindex=color)
    mesh=node('mesh');vertices=node('vertices');faces=node('triangles');lookup={}
    for path in paths:
        for triangle in triangles(path):
            indices=[]
            for raw_vertex in triangle:
                vertex=tuple(v-o for v,o in zip(raw_vertex,offset))
                if vertex not in lookup:
                    lookup[vertex]=len(lookup);vertices.append(node('vertex',x=format(vertex[0],'.9g'),y=format(vertex[1],'.9g'),z=format(vertex[2],'.9g')))
                indices.append(lookup[vertex])
            faces.append(node('triangle',v1=indices[0],v2=indices[1],v3=indices[2]))
    mesh.extend([vertices,faces]);obj.append(mesh)
    return obj

def package(folder,destination=None,lid_color='grey',label_color='white',offset=(0,0,0)):
    from .filament_colors import color
    lid_spec=color(lid_color);label_spec=color(label_color)
    model=node('model',unit='millimeter');model.set('{http://www.w3.org/XML/1998/namespace}lang','en-US')
    resources=node('resources');materials=node('basematerials',id=1)
    materials.extend([node('base',name=lid_spec['name'],displaycolor=lid_spec['hex']+'FF'),node('base',name=label_spec['name'],displaycolor=label_spec['hex']+'FF')]);resources.append(materials)
    resources.append(mesh_object([folder/'lid.stl'],2,'Lid - '+lid_spec['name'],0,offset))
    labels=sorted(folder.glob('label-*.stl'))
    if labels:resources.append(mesh_object(labels,3,'Label - '+label_spec['name'],1,offset))
    assembly=node('object',id=4,type='model',name='Labeled dovetail lid')
    components=node('components');components.append(node('component',objectid=2))
    if labels:components.append(node('component',objectid=3))
    assembly.append(components);resources.append(assembly);model.append(resources)
    build=node('build');build.append(node('item',objectid=4));model.append(build)
    destination=Path(destination) if destination else folder.parent/('Dovetail-label-'+folder.name+'.3mf')
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        archive.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        # Expat (used by Bambu's importer) does not accept the alias "utf8".
        archive.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
    return destination

def export_latest(result,filename):
    import adsk.core,adsk.fusion
    if not result or not result.get('lidToken'):raise ValueError('Create a dovetail bin in this panel first, then export its lid.')
    app=adsk.core.Application.get();design=adsk.fusion.Design.cast(app.activeProduct)
    if not design:raise ValueError('Activate the design containing the new lid.')
    found=design.findEntityByToken(result['lidToken'])
    if not found:raise ValueError('Activate the design containing the most recently created lid.')
    lid=found[0];recipe=json.loads(lid.attributes.itemByName('GridfinityWorkshop','binRecipe').value)
    labels=[]
    for token in result.get('labelTokens',[]):
        bodies=design.findEntityByToken(token)
        if not bodies:raise ValueError('A label body has been removed. Create the labeled lid again before exporting.')
        labels.append(bodies[0])
    with tempfile.TemporaryDirectory(prefix='workshop-lid-export-') as tmp:
        folder=Path(tmp)
        for index,body in enumerate([lid]+labels):
            path=folder/('lid.stl' if index==0 else f'label-{index:03d}.stl')
            options=design.exportManager.createSTLExportOptions(body,str(path))
            options.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
            options.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            if not design.exportManager.execute(options):raise RuntimeError('Could not mesh the lid for export.')
        package(folder,filename,recipe.get('lidColor','grey'),recipe.get('lidLabelColor','white'),offset=(0,0,lid.boundingBox.minPoint.z*10))
    return dict(filename=str(filename),parts=2 if labels else 1)
