"""Verify the generated label examples have closed, aligned millimeter meshes."""
from pathlib import Path
import collections,struct,json,zipfile
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]/'outputs/labeled-lids'

def verify():
    results=[];volumes={}
    for mode in ('cutout','raised','embedded'):
        allpoints=[];volume=0;meshes=0
        for path in (ROOT/mode).glob('*.stl'):
            data=path.read_bytes();count=struct.unpack_from('<I',data,80)[0]
            assert len(data)==84+50*count
            edges=collections.Counter();mesh_volume=0
            for i in range(count):
                raw=struct.unpack_from('<12fH',data,84+50*i)[3:12]
                tri=[tuple(raw[j:j+3]) for j in (0,3,6)];allpoints+=tri;a,b,c=tri
                mesh_volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
                for j in range(3):edges[tuple(sorted(tuple(round(v,5) for v in tri[k]) for k in (j,(j+1)%3)))]+=1
            assert all(n==2 for n in edges.values()),path
            assert mesh_volume>0
            volume+=mesh_volume;meshes+=1
        size=[max(v[k] for v in allpoints)-min(v[k] for v in allpoints) for k in range(3)]
        assert all(abs(a-b)<.001 for a,b in zip(size,[83.5,41.5,5.9 if mode=='raised' else 5.3]))
        with zipfile.ZipFile(ROOT/('Dovetail-label-'+mode+'.3mf')) as archive:
            m=ET.fromstring(archive.read('3D/3dmodel.model'));ns={'c':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
            assert m.get('unit')=='millimeter'
            assert len(m.findall('c:build/c:item',ns))==1
            assert len(m.findall('c:resources/c:object/c:mesh',ns))==(2 if any((ROOT/mode).glob('label-*.stl')) else 1)
        volumes[mode]=volume;results.append(dict(mode=mode,dimensionsMM=size,meshes=meshes,closed=True,singleAssembly=True,volumeMM3=volume))
    assert volumes['raised']>volumes['embedded']>volumes['cutout']
    # Independent tessellation of the curved cavities and inserts differs slightly.
    assert abs((volumes['raised']-volumes['embedded'])-(volumes['embedded']-volumes['cutout']))<.002*(volumes['embedded']-volumes['cutout'])
    (ROOT/'mesh-verification.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print(json.dumps(results))

if __name__=='__main__':verify()
