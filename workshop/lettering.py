"""Offline, deterministic text outlines and bounded SVG import (no Fusion text)."""
import json,re
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET
from .request import number

@lru_cache(maxsize=1)
def fonts():
    return json.loads((Path(__file__).parent/'fonts/outlines.json').read_text(encoding='utf8'))

def text_svg(text,font='rubik',height=4,max_width=200):
    if font not in fonts():raise ValueError('Choose Rubik or Atkinson.')
    if not isinstance(text,str) or not text.strip() or len(text)>120:raise ValueError('Enter 1–120 characters of single-line text.')
    data=fonts()[font];glyphs=data['glyphs'];cursor=0;previous='';items=[];bounds=[]
    for ch in text:
        if ch not in glyphs:raise ValueError(f'Unsupported character {ch!r}. Use Latin lettering or import outlined SVG artwork.')
        cursor+=data['kerning'].get(previous+ch,0);g=glyphs[ch]
        if g['bounds']:
            a,b,c,d=g['bounds'];bounds.append((a+cursor,b,c+cursor,d))
            items.append(f'<path transform="translate({cursor:g} 0)" d="{g["path"]}"/>')
        cursor+=g['advance'];previous=ch
    if not bounds:raise ValueError('Text has no printable outlines.')
    x=min(b[0] for b in bounds);y=min(b[1] for b in bounds)
    w=max(b[2] for b in bounds)-x;h=max(b[3] for b in bounds)-y
    scale=min(height/h,max_width/w)
    return dict(svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*scale:.8f}mm" height="{h*scale:.8f}mm" viewBox="{x:g} {y:g} {w:g} {h:g}"><g fill="black">'+''.join(items)+'</g></svg>',
                width=w*scale,height=h*scale,fontName=data['name'])

def clean_svg(source):
    """Keep only inert, closed vector artwork; fail loudly on text/strokes/effects.

    Illustrator metadata/defs are discarded. Convert text and strokes to outlines,
    expand appearances, and flatten overlaps before importing.
    """
    if not isinstance(source,str) or len(source.encode('utf8'))>500_000:raise ValueError('SVG must be smaller than 500 KB.')
    if re.search(r'<!\s*(?:DOCTYPE|ENTITY)',source,re.I):raise ValueError('Export a plain SVG without a document type or entities.')
    try:root=ET.fromstring(source)
    except ET.ParseError as error:raise ValueError('The SVG is not valid XML.') from error
    if root.tag.split('}')[-1]!='svg':raise ValueError('Choose an SVG file.')
    allowed={'svg','g','path','rect','circle','ellipse','polygon'}
    discard={'metadata','title','desc','defs','namedview'}
    attrs={'viewBox','width','height','x','y','rx','ry','cx','cy','r','d','points','transform','fill','fill-rule','stroke','style','opacity','fill-opacity','stroke-width','version'}
    def copy(node):
        tag=node.tag.split('}')[-1]
        if tag in discard:return None
        if tag not in allowed:raise ValueError(f'SVG element {tag!r} is unsupported. Outline text/strokes and expand artwork first.')
        out=ET.Element(tag)
        for key,value in node.attrib.items():
            if '}' in key:continue
            if key.startswith('on') or key in ('href','filter','clip-path','mask'):raise ValueError('SVG references, scripts, masks and effects are unsupported; expand artwork first.')
            if key not in attrs:continue
            if any(s in value.lower() for s in ('url(', 'javascript:', 'expression(')):raise ValueError('SVG references are unsupported.')
            out.set(key,value)
        style={}
        for entry in out.attrib.pop('style','').split(';'):
            if ':' in entry:
                key,value=entry.split(':',1);style[key.strip()]=value.strip()
        for key,value in style.items():
            if key not in ('fill','fill-rule','stroke','stroke-width','opacity','fill-opacity'):raise ValueError('Expand SVG appearances and remove CSS before importing.')
            out.set(key,value)
        if out.get('stroke','none').lower() not in ('none',''):raise ValueError('Convert SVG strokes to filled outlines before importing.')
        if out.get('fill','black').lower()=='none':raise ValueError('SVG must contain filled outlines.')
        if any(out.get(k,'1')!='1' for k in ('opacity','fill-opacity')):raise ValueError('Remove SVG transparency before importing.')
        if tag=='path':
            d=out.get('d','').strip()
            # Each subpath must be explicitly closed, including counters.
            parts=re.split('[Mm]',d)[1:]
            if not parts or any(not p.rstrip().endswith(('z','Z')) for p in parts):raise ValueError('Close every SVG path before importing.')
            if re.search(r'[^MmZzLlHhVvCcSsQqTtAa0-9eE+.,\s-]',d) or re.search(r'(?:nan|inf)',d,re.I):raise ValueError('Invalid SVG path data.')
        for child in node:
            item=copy(child)
            if item is not None:out.append(item)
        return out
    output=copy(root)
    if not any(n.tag in allowed-{'svg','g'} for n in output.iter()):raise ValueError('SVG has no outlined artwork.')
    output.set('xmlns','http://www.w3.org/2000/svg')
    return ET.tostring(output,encoding='unicode')

def validate(data):
    if not isinstance(data,dict):raise ValueError('Missing lettering settings.')
    c=dict(data)
    if c.get('source','text') not in ('text','svg'):raise ValueError('Choose text or SVG artwork.')
    if c.get('operation','engrave') not in ('engrave','raised','separate'):raise ValueError('Choose engraved, raised or separate bodies.')
    for key,default,lo,hi in [('height',4,1,50),('maxWidth',100,1,240),('depth',.6,.1,5),('offsetX',0,-240,240),('offsetY',0,-240,240),('rotation',0,-180,180)]:
        c.setdefault(key,default);c[key]=number(c,key,lo,hi)
    c.setdefault('source','text');c.setdefault('operation','engrave');c.setdefault('font','rubik');c.setdefault('text','Workshop')
    if c['source']=='text':c.update(text_svg(c['text'],c['font'],c['height'],c['maxWidth']))
    else:c['svg']=clean_svg(c.get('svg',''))
    return c

def coupon_plan():
    """Two plates with paired raised/engraved rows at four actual outline heights."""
    plates=[]
    for font in ('rubik','atkinson'):
        rows=[];y=5
        header=text_svg(fonts()[font]['name'],font,3,100)
        rows.append(dict(header,x=5,y=y,operation='engrave',depth=.4,label='Font name'));y+=8
        for height in (2,3,4,5):
            for operation,code in [('raised','R'),('engrave','E')]:
                art=text_svg(f'{height}mm {code}: Aa B8 O0 Il1 6.35',font,height,110)
                rows.append(dict(art,x=5,y=y,operation=operation,depth=.6,label=f'{height} mm {operation}'))
                y+=height+4
        plates.append(dict(font=font,name=fonts()[font]['name'],w=120,d=y+2,h=2,rows=rows))
    return plates
