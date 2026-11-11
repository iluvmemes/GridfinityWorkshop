"""Fit one to four outlined text lines into the protected center of a lid."""
from .lettering import text_svg,fonts
from .request import number
from .filament_colors import color

DEFAULTS=dict(lidLabelMode='off',lidLabelText='',lidLabelFont='rubik',lidLabelLayout='single',lidLabelHeight=5,lidLabelDepth=.6,lidColor='grey',lidLabelColor='white')

def plan(c):
    for key,value in DEFAULTS.items():c.setdefault(key,value)
    color(c['lidColor']);color(c['lidLabelColor'])
    mode=c['lidLabelMode']
    if mode not in ('off','cutout','raised','embedded'):raise ValueError('Choose a lid label style.')
    if c.get('family')!='standard' or not c.get('dovetailLid'):return None
    if mode=='off':return None
    text=c['lidLabelText']
    if not isinstance(text,str) or not text.strip() or len(text)>120:raise ValueError('Enter 1–120 characters for the lid label.')
    if c['lidLabelFont'] not in fonts():raise ValueError('Choose a bundled label font.')
    if c['lidLabelLayout'] not in ('single','multi'):raise ValueError('Choose single or multiple label lines.')
    height=number(c,'lidLabelHeight',2,12);depth=number(c,'lidLabelDepth',.2,1.5)
    width=c['widthMM']-12;available=c['depthMM']-12
    # Six mm of edge clearance avoids the stacking lip and rounded corners.
    def art(line):return text_svg(line,c['lidLabelFont'],height,10000)
    if c['lidLabelLayout']=='single':lines=[' '.join(text.split())]
    else:
        lines=[]
        for paragraph in text.replace('\r\n','\n').replace('\r','\n').split('\n'):
            if not paragraph.strip():raise ValueError('Remove blank label lines.')
            current=''
            for word in paragraph.split():
                candidate=(current+' '+word).strip()
                if current and art(candidate)['width']>width:lines.append(current);current=word
                else:current=candidate
            if current:lines.append(current)
        if len(lines)>4:raise ValueError('Use at most four label lines; shorten text or reduce letter height.')
    artworks=[art(line) for line in lines]
    gap=height*.35;total=height*len(lines)+gap*(len(lines)-1)
    scale=min(1,width/max(a['width'] for a in artworks),available/total)
    actual=height*scale
    if actual<1.5:raise ValueError('Label would be smaller than 1.5 mm. Shorten it or use multiple lines/a larger lid.')
    total*=scale;rows=[]
    for index,(line,a) in enumerate(zip(lines,artworks)):
        # First entered line is at the back/top of the lid in plan view.
        rows.append(dict(text=line,svg=a['svg'],width=a['width']*scale,height=actual,
                         x=c['widthMM']/2,y=c['depthMM']/2+total/2-actual/2-index*(height+gap)*scale))
    return dict(mode=mode,depth=depth,rows=rows,height=actual,width=max(r['width'] for r in rows),
                totalHeight=total,scale=scale,margin=6)
