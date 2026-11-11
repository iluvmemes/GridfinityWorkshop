import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from workshop.lid_label import plan
BASE=dict(family='standard',dovetailLid=True,cols=2,rows=1,widthMM=83.5,depthMM=41.5,lidLabelMode='embedded',lidLabelText='M3 HARDWARE\nBOLTS & NUTS',lidLabelLayout='multi')
for font in ('rubik','atkinson'):
    for mode in ('cutout','raised','embedded'):
        p=plan(dict(BASE,lidLabelFont=font,lidLabelMode=mode))
        assert len(p['rows'])==2 and p['height']==5 and p['depth']==.6
        assert p['rows'][0]['y']>p['rows'][1]['y']
        for r in p['rows']:
            assert r['x']-r['width']/2>=6 and r['x']+r['width']/2<=77.5
            assert r['y']-r['height']/2>=6 and r['y']+r['height']/2<=35.5
assert len(plan(dict(BASE,lidLabelLayout='single'))['rows'])==1
p=plan(dict(BASE,lidLabelText='HARDWARE STORAGE',lidLabelHeight=12,lidLabelLayout='single'))
assert p['height']<12 and p['width']<=71.5+1e-8
assert plan(dict(BASE,lidLabelMode='off')) is None
assert plan(dict(BASE,family='blank')) is None
for change in (dict(lidLabelText=''),dict(lidLabelText='A\nB\nC\nD\nE'),dict(lidLabelText='\nA'),dict(lidLabelDepth=3),dict(lidLabelHeight=float('nan')),dict(lidLabelText='🔩'),dict(lidLabelFont='Arial')):
    try:plan(dict(BASE,**change))
    except ValueError:pass
    else:raise AssertionError(change)
print('PASS: lid label layout, multiline fit, edge clearance, styles and invalid settings')
