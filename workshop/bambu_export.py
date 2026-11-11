"""Preserve Fusion's native meshes and colors in one printable 3MF assembly."""
from pathlib import Path
import os
import tempfile
import zipfile
import uuid
from xml.etree import ElementTree as ET

NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'


def group_archive(source, destination, name='Printable assembly'):
    """Wrap native build items; do not remesh, recolor, or change coordinates."""
    destination = Path(destination)
    with zipfile.ZipFile(source) as archive:
        path = '3D/3dmodel.model'
        data = archive.read(path)
        import io
        for _, (prefix, uri) in ET.iterparse(io.BytesIO(data), events=('start-ns',)):
            ET.register_namespace(prefix, uri)
        root = ET.fromstring(data)
        resources = root.find('{'+NS+'}resources')
        build = root.find('{'+NS+'}build')
        if resources is None or build is None:
            raise ValueError('The exported 3MF has no model resources or build.')
        items = list(build.findall('{'+NS+'}item'))
        if not items:
            raise ValueError('There are no printable bodies in this selection.')
        if any(item.get('printable', '1') in ('0', 'false') for item in items):
            raise ValueError('The export contains non-printable build items. Select only the parts to print.')
        identifier = str(max(int(obj.get('id')) for obj in resources) + 1)
        obj = ET.SubElement(resources, '{'+NS+'}object', id=identifier, type='model', name=name)
        production_uuid = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}UUID'
        production = production_uuid in build.attrib
        if production:
            obj.set(production_uuid, str(uuid.uuid4()))
        components = ET.SubElement(obj, '{'+NS+'}components')
        for item in items:
            attrs = {'objectid': item.attrib['objectid']}
            if 'transform' in item.attrib:
                attrs['transform'] = item.attrib['transform']
            if production:
                attrs[production_uuid] = item.get(production_uuid, str(uuid.uuid4()))
            # Fusion's native exports use local object IDs. Refuse extensions
            # here rather than silently dropping cross-file references.
            if any(k.startswith('{') and k not in (
                    '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}UUID',
                    '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}uuid') for k in item.attrib):
                raise ValueError('This build uses an unsupported 3MF extension reference.')
            ET.SubElement(components, '{'+NS+'}component', attrs)
            build.remove(item)
        assembly_item = ET.SubElement(build, '{'+NS+'}item', objectid=identifier)
        if production:
            assembly_item.set(production_uuid, str(uuid.uuid4()))
        payload = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        # Replace atomically, including when source and destination are the same.
        fd, temp = tempfile.mkstemp(suffix='.3mf', dir=destination.parent)
        os.close(fd)
        try:
            with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as output:
                for info in archive.infolist():
                    output.writestr(info, payload if info.filename == path else archive.read(info.filename))
            # Close the input before replacement on Windows.
        except Exception:
            Path(temp).unlink(missing_ok=True)
            raise
    try:
        os.replace(temp, destination)
    finally:
        Path(temp).unlink(missing_ok=True)
    return {'filename': str(destination), 'parts': len(items), 'unit': root.get('unit', 'millimeter')}


def export(design, geometry, filename):
    import adsk.fusion
    if not geometry or not geometry.isValid:
        raise ValueError('Select a component or solid body in the active design.')
    with tempfile.TemporaryDirectory(prefix='workshop-bambu-') as folder:
        native = Path(folder) / 'fusion.3mf'
        options = design.exportManager.createC3MFExportOptions(geometry, str(native))
        if not options:
            raise ValueError('Fusion cannot export that selection. Select a component or solid body.')
        options.isOneFilePerBody = False
        options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        options.sendToPrintUtility = False
        if not design.exportManager.execute(options):
            raise RuntimeError('Fusion could not export the selected geometry.')
        return group_archive(native, filename, geometry.name)
