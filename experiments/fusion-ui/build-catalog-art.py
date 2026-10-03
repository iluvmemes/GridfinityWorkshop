"""Generate scalable isometric artwork for the five bin catalog selectors."""
from pathlib import Path
OUT=Path(__file__).parent/'GridfinityUIPreview'/'catalog-art'
OUT.mkdir(exist_ok=True)

def artwork(kind):
    def p(x,y,z): return (77+.82*(x-y),65+.38*(x+y)-z)
    def poly(points,fill,stroke='#567387',width=.85):
        q=' '.join(f'{a:.2f},{b:.2f}' for a,b in [p(*v) for v in points])
        return f'<polygon points="{q}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"/>'
    def box(x,y,z,w,d,h,top='#d4e4ed',front='#90b3c9',side='#638ba5'):
        return (poly([(x,y+d,z),(x+w,y+d,z),(x+w,y+d,z+h),(x,y+d,z+h)],front)+
                poly([(x+w,y,z),(x+w,y+d,z),(x+w,y+d,z+h),(x+w,y,z+h)],side)+
                poly([(x,y,z+h),(x+w,y,z+h),(x+w,y+d,z+h),(x,y+d,z+h)],top))
    def tray(w,d,h):
        s=box(0,0,0,w,d,h,top='#e0ecf2')
        s+=poly([(4,4,h),(w-4,4,h),(w-4,d-4,h),(4,d-4,h)],'#52748b')
        s+=poly([(4,4,h),(w-4,4,h),(w-4,4,h-14),(4,4,h-14)],'#82a5bd')
        s+=poly([(4,4,h-14),(w-4,4,h-14),(w-4,d-4,h),(4,d-4,h)],'#afcbdc')
        s+=poly([(4,4,h),(4,4,h-14),(4,d-4,h)],'#6e91ab')
        return s
    def feet(w,d):
        s=''
        for y in (3,d-17):
            for x in (4,w-27):s+=box(x,y,-6,22,13,6,'#b5cbd8','#7597ac','#466b85')
        return s
    def clasp(x,y,w,d,h,color='#c8deea'):
        s=box(x,y,0,w,d,h,top=color)
        s+=box(x-1,y-1,h,w+2,d+2,4,'#e2edf3','#a7c5d7','#7c9eb6')
        s+=poly([(x+5,y+5,h+4.2),(x+w-5,y+5,h+4.2),(x+w-5,y+d-5,h+4.2),(x+5,y+d-5,h+4.2)],color,stroke='#9bbacc')
        mid=y+d/2
        s+=box(x+w+.8,mid-7,h-21,3,14,19,'#ead7a7','#cda75e','#b78b41')
        s+=box(x+w+3.8,mid-8,h-24,4,16,5,'#f4e4bd','#d2b071','#b78b41')
        s+=box(x-2,mid-6,h-4,3,12,6,'#acc5d5','#7599b0','#4e718a')
        return s
    s='<ellipse cx="88" cy="122" rx="66" ry="8" fill="#315775" opacity=".09"/>'
    if kind=='standard':
        s+=feet(80,54)+tray(80,54,38)
        s+=poly([(39,5,36),(42,5,36),(42,48,36),(39,48,36)],'#e1edf3')
        s+=poly([(39,5,36),(39,48,36),(39,48,25),(39,5,25)],'#83a6bc')
        s+=poly([(10,45,39),(29,45,39),(29,53,34),(10,53,34)],'#e5d6b2')
    elif kind=='clasp':s+=feet(80,54)+clasp(0,0,80,54,39)
    elif kind=='cartridge':s+=clasp(0,12,88,23,45)
    elif kind=='magazine':
        s+=feet(86,62)+tray(86,62,16)
        for y,color in [(4,'#b7d2e2'),(23,'#d0e2ec'),(42,'#a6c8dc')]:s+=clasp(4,y,73,13,51,color)
        s+=poly([(0,62,0),(86,62,0),(86,62,16),(0,62,16)],'#93b7cd')
        s+=poly([(86,0,0),(86,62,0),(86,62,16),(86,0,16)],'#648ea9')
    else:
        s+=feet(80,54)+box(0,0,0,80,54,38,'#dce8ef','#a5bfd0','#7595ae')
        for x in (26,53):
            a,b=p(x,0,38.2),p(x,54,38.2)
            s+=f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}" stroke="#9db6c7" stroke-dasharray="3 3" stroke-width=".8"/>'
        a,b=p(0,27,38.2),p(80,27,38.2)
        s+=f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}" stroke="#9db6c7" stroke-dasharray="3 3" stroke-width=".8"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 140" role="img" aria-label="{kind} in perspective"><title>{kind.title()} perspective illustration</title>{s}</svg>'

for family in ('standard','clasp','cartridge','magazine','blank'):
    (OUT/f'{family}.svg').write_text(artwork(family),encoding='utf-8')
