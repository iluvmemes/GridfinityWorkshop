"""One-off 3..13 mm magnet set in the standard 68 x 17.5 mm cartridge.

Four channels per nominal diameter; +0.5 mm diameter clearance, >=3 mm webs.
All four of each diameter stay in the same cartridge. Coordinates are body-centered.
"""
import collections,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]/'outputs'/'magnet-cartridge-set-ascending-2026-10-04'


def cluster(size,style):
    diameter=size+.5;radius=diameter/2
    if style=='row':
        pitch=diameter+3
        points=[(radius+i*pitch,0) for i in range(4)]
        width=diameter+3*pitch
    elif style=='square':
        pitch=diameter+3
        points=[(radius+x*pitch,(y-.5)*pitch) for x in range(2) for y in range(2)]
        width=diameter+pitch
    else:
        half=(13.5-diameter)/2
        # Opposite rows clear diagonally; every second circle also clears its own row.
        pitch=max((diameter+3)/2,math.sqrt(max(0,(diameter+3)**2-(2*half)**2)))
        points=[(radius+i*pitch,half if i%2 else -half) for i in range(4)]
        width=diameter+3*pitch
    return width,[dict(sizeMM=size,diameterMM=diameter,x=x,y=y) for x,y in points]


def plan():
    recipes=[[(3,'square'),(4,'square'),(5,'row')],[(6,'stagger'),(7,'stagger')]]
    recipes.extend([[(size,'row')] for size in range(8,14)])
    result=[]
    for index,groups in enumerate(recipes,1):
        clusters=[cluster(size,style) for size,style in groups]
        width=sum(w for w,points in clusters)+3*(len(clusters)-1)
        assert width<=64+1e-8
        x0=-width/2;channels=[];labels=[]
        for (size,style),(w,points) in zip(groups,clusters):
            labels.append(dict(sizeMM=size,centerX=x0+w/2,regionWidth=w))
            channels.extend(dict(q,x=q['x']+x0) for q in points);x0+=w+3
        gaps=[]
        for i,q in enumerate(channels):
            r=q['diameterMM']/2
            assert abs(q['x'])+r<=32+1e-8 and abs(q['y'])+r<=6.75+1e-8
            for p in channels[i+1:]:
                gap=math.hypot(q['x']-p['x'],q['y']-p['y'])-(q['diameterMM']+p['diameterMM'])/2
                assert gap>=3-1e-8;gaps.append(gap)
        sizes=[size for size,style in groups]
        result.append(dict(id=f'C{index:02}',sizesMM=sizes,channels=channels,labels=labels,
            usedLengthMM=width,minimumSeparationMM=min(gaps),name=f"C{index:02} - "+' + '.join(f'{n}mm' for n in sizes)+' - 4 each'))
    assert [n for c in result for n in c['sizesMM']]==list(range(3,14))
    counts=collections.Counter(q['sizeMM'] for r in result for q in r['channels'])
    assert counts=={size:4 for size in range(3,14)}
    return dict(bodyLengthMM=68,bodyWidthMM=17.5,heightU=8,channelClearanceMM=.5,
        separationMM=3,omittedSizesMM=[14,15,16],cartridges=result,channelCount=sum(counts.values()))


def write_plan():
    data=plan();ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/'channel-layout.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="1022" viewBox="0 0 1040 1022">',
        '<rect width="1040" height="1022" fill="#f4f7fa"/><g font-family="Arial" fill="#203848">',
        '<text x="32" y="36" font-size="23">Standard cartridge magnet set - 44 channels / 8 cartridges</text>',
        '<text x="32" y="60" font-size="14">Nominal sizes labeled. Channels +0.5 mm; minimum 3 mm separation; 8U height.</text>']
    for index,c in enumerate(data['cartridges']):
        x=210;y=95+index*112
        svg.append(f'<text x="32" y="{y+27}" font-size="18">{c["id"]}</text><text x="32" y="{y+52}" font-size="14">'+ ' + '.join(str(n) for n in c['sizesMM'])+' mm / 4 each</text>')
        # True-scale top views, all at 4.8 px/mm.
        k=4.8;w=68*k;h=17.5*k
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{2*k}" fill="#d1e0e9" stroke="#597e96"/>')
        for q in c['channels']:
            cx=x+(q['x']+34)*k;cy=y+(8.75-q['y'])*k;r=q['diameterMM']/2*k
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#f8fbfd" stroke="#597e96"/><text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="11">{q["sizeMM"]}</text>')
        svg.append(f'<text x="580" y="{y+35}" font-size="14">{len(c["channels"])} channels / min. gap {c["minimumSeparationMM"]:.2f} mm</text>')
    svg.append('<text x="32" y="1011" font-size="14">14-16 mm omitted: too wide for the standard cartridge with clearance and 2 mm walls.</text></g></svg>')
    (ROOT/'channel-layout.svg').write_text('\n'.join(svg),encoding='utf-8')
    return data

if __name__=='__main__':
    data=write_plan()
    for c in data['cartridges']:print(c['name'],round(c['usedLengthMM'],3),round(c['minimumSeparationMM'],3))
