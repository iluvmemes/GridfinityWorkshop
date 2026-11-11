"""Physical dimensions, offline font assets, safe SVGs and coupon coverage."""
import json,math,sys,hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from workshop.lettering import fonts,text_svg,clean_svg,validate,coupon_plan

for key,font in fonts().items():
    assert hashlib.sha256((ROOT/'workshop/fonts'/font['source']).read_bytes()).hexdigest()==font['sha256']
    assert 'SIL OPEN FONT LICENSE' in (ROOT/'workshop/fonts'/font['source'].replace('.ttf','-OFL.txt')).read_text()
    for text in ('Workshop','BO8 i','Aa O0 Il1 6.35','M3 × 0.5','Café Ø6 ±0.1'):
        a=text_svg(text,key,4,100);root=ET.fromstring(a['svg'])
        assert math.isclose(a['height'],4)
        assert all(n.tag.split('}')[-1]!='text' for n in root.iter())
        assert len(root.findall('.//{*}path'))>=len(text.replace(' ',''))
        small=text_svg(text,key,4,a['width']/2)
        assert math.isclose(small['height'],2) and math.isclose(small['width'],a['width']/2)
        clean_svg(a['svg'])
    # Revalidation must preserve font keys and proportional dimensions.
    request=validate({'text':'Workshop','font':key,'maxWidth':10})
    assert validate(request)['font']==key

def rejects(call):
    try:call()
    except ValueError:return
    raise AssertionError('Invalid request was accepted')

for text in ('','   ','a\nb','Bolt 🔩','A'*121):rejects(lambda:text_svg(text))
for change in ({'depth':True},{'height':float('nan')},{'rotation':181},{'maxWidth':0},{'font':'system-font'},{'operation':'cut-all'}):
    rejects(lambda:validate(dict(text='Sample',**change)))
good='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><g><path d="M0 0h10v10h-10z M2 2v6h6v-6z"/></g></svg>'
assert 'path' in clean_svg(good)
for bad in ('<svg><text>Hello</text></svg>','<svg><path d="M0 0L1 1"/></svg>',
            '<svg><script>alert(1)</script></svg>','<svg><image href="https://example.com"/></svg>',
            '<svg><path d="M0 0h1v1z" style="fill:url(https://example.com)"/></svg>',
            '<!DOCTYPE svg [<!ENTITY x "boom">]><svg/>','<svg><path d="M0 0h1v1z" stroke="black"/></svg>',
            '<svg><use href="#a"/></svg>','<svg><path d="M0 0h1v1z M2 2L3 3"/></svg>'):
    rejects(lambda:clean_svg(bad))
plates=coupon_plan();assert len(plates)==2
for p in plates:
    assert p['w']==120 and p['d']==75 and p['h']==2
    for height in (2,3,4,5):
        rows=[r for r in p['rows'] if r['label'].startswith(f'{height} mm')]
        assert {r['operation'] for r in rows}=={'raised','engrave'}
        assert all(math.isclose(r['height'],height) and r['width']<=110 and r['y']+height<p['d'] for r in rows)
print('PASS: bundled font integrity/licenses, physical dimensions, proportional fit, Latin labels, SVG validation and 16 coupon samples')
