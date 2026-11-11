import json,sys,struct,tempfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from workshop.filament_colors import COLORS,color
from workshop.lid_export import package
from workshop.lid_label import plan
assert len(COLORS)==12
data=json.loads((ROOT/'workshop/filament-colors.json').read_text())
assert json.loads((ROOT/'workshop/filament-colors.js').read_text().removeprefix('window.WorkshopFilaments=').strip().removesuffix(';'))==data
for key in COLORS:assert len(color(key)['hex'])==7
for invalid in ('neon',None,[],12):
    try:color(invalid)
    except ValueError:pass
    else:raise AssertionError(invalid)
try:plan(dict(lidColor='unknown'))
except ValueError:pass
else:raise AssertionError('Invalid stored color accepted')
tmp=ROOT/'outputs/qa/tmp';tmp.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(dir=tmp) as directory:
    folder=Path(directory);v=[(0,0,10),(1,0,10),(0,1,10),(0,0,11)]
    triangles=[(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
    raw=b'\0'*80+struct.pack('<I',4)+b''.join(struct.pack('<12fH',0,0,0,*(n for i in tri for n in v[i]),0) for tri in triangles)
    (folder/'lid.stl').write_bytes(raw);(folder/'label-01.stl').write_bytes(raw)
    out=package(folder,folder/'colors.3mf','blue','yellow',offset=(0,0,10))
    with zipfile.ZipFile(out) as z:
        xml=z.read('3D/3dmodel.model')
        assert b"encoding='utf-8'" in xml and b"encoding='utf8'" not in xml
        # Python's XML wrapper accepts extra codec aliases; test raw Expat too.
        import ctypes,os
        expat_path=Path(r'C:\Program Files\Git\mingw64\bin\libexpat-1.dll')
        if os.name=='nt' and expat_path.exists():
            lib=ctypes.CDLL(str(expat_path))
            lib.XML_ParserCreate.argtypes=[ctypes.c_char_p];lib.XML_ParserCreate.restype=ctypes.c_void_p
            lib.XML_Parse.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int,ctypes.c_int];lib.XML_Parse.restype=ctypes.c_int
            lib.XML_ParserFree.argtypes=[ctypes.c_void_p]
            parser=lib.XML_ParserCreate(None)
            try:assert lib.XML_Parse(parser,xml,len(xml),1)==1
            finally:lib.XML_ParserFree(parser)
        model=ET.fromstring(xml);ns={'c':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
        bases=model.findall('c:resources/c:basematerials/c:base',ns)
        assert [(b.get('name'),b.get('displaycolor')) for b in bases]==[('Blue','#1729ABFF'),('Yellow','#FFF13FFF')]
        objects=model.findall('c:resources/c:object',ns)
        assert objects[0].get('name')=='Lid - Blue' and objects[0].get('pindex')=='0'
        assert objects[1].get('name')=='Label - Yellow' and objects[1].get('pindex')=='1'
        assert len(model.findall('c:build/c:item',ns))==1
        assert min(float(n.get('z')) for n in model.findall('.//c:vertex',ns))==0
print('PASS: 12 swatches, shared data, invalid settings, named colored 3MF parts and aligned units')
