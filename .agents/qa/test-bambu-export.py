"""Check lossless grouping, transformed instances, color resources and safe failure."""
from pathlib import Path
import sys
import tempfile
import zipfile
from xml.etree import ElementTree as ET
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop.bambu_export import group_archive, NS

Q = '{'+NS+'}'
fixture = f'''<model xmlns="{NS}" xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02" unit="millimeter">
<resources><m:colorgroup id="1"><m:color color="#00AA00FF"/><m:color color="#AA00AAFF"/></m:colorgroup>
<object id="2" name="Small part" type="model" pid="1" pindex="1"><mesh><vertices><vertex x="0" y="0" z="0"/></vertices><triangles/></mesh></object>
<object id="3" type="model"><components><component objectid="2" transform="0 1 0 -1 0 0 0 0 1 20 30 40"/></components></object></resources>
<build><item objectid="2" transform="1 0 0 0 1 0 0 0 1 -11 2 3"/><item objectid="3"/></build></model>'''
with tempfile.TemporaryDirectory() as folder:
    source = Path(folder)/'source.3mf'
    destination = Path(folder)/'output.3mf'
    with zipfile.ZipFile(source, 'w') as z:
        z.writestr('3D/3dmodel.model', fixture)
        z.writestr('Metadata/thumbnail.png', b'unchanged image')
    original = ET.fromstring(fixture)
    info = group_archive(source, destination, 'Test & colors')
    assert info['parts'] == 2 and info['unit'] == 'millimeter'
    with zipfile.ZipFile(destination) as z:
        grouped = ET.fromstring(z.read('3D/3dmodel.model'))
        assert z.read('Metadata/thumbnail.png') == b'unchanged image'
    assert len(grouped.find(Q+'build')) == 1
    old = original.find(Q+'resources')
    new = grouped.find(Q+'resources')
    assert all(ET.tostring(a) == ET.tostring(b) for a,b in zip(old,new))
    assert new[-1].attrib['id'] == '4'
    refs = new[-1].find(Q+'components')
    for item, ref in zip(original.find(Q+'build'), refs):
        assert item.attrib == ref.attrib
    # Supports replacing a file in place on Windows.
    group_archive(destination, destination)
    before = destination.read_bytes()
    with zipfile.ZipFile(source, 'w') as z:
        z.writestr('3D/3dmodel.model', fixture.replace('objectid="2" transform="1', 'printable="0" objectid="2" transform="1'))
    try:
        group_archive(source, destination)
        raise AssertionError('Non-printable objects should not silently become printable')
    except ValueError:
        pass
    assert destination.read_bytes() == before
print('PASS: transforms, nested/repeated instances, names, colors, geometry, attachments, in-place export and safe failure')
