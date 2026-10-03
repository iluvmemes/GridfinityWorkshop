"""Build Fusion PNG command icons; Pillow is needed only to regenerate assets."""
from pathlib import Path
import math
from PIL import Image, ImageDraw

OUT = Path(__file__).parent / 'GridfinityUIPreview' / 'resources'
OUT.mkdir(exist_ok=True)

def skeleton():
    points=[]
    # Captured cell outline, including the four concave magnet lands.
    for cx,cy,start,end,tail in [
        (7.75,7.75,0,90,[(2.7,12),(2.7,29.5),(7.75,29.5)]),
        (7.75,33.75,-90,0,[(12,38.8),(29.5,38.8),(29.5,33.75)]),
        (33.75,33.75,180,270,[(38.8,29.5),(38.8,12),(33.75,12)]),
        (33.75,7.75,90,180,[(29.5,2.7),(12,2.7),(12,7.75)])]:
        points += [(cx+4.25*math.cos(math.radians(start+(end-start)*i/24)),
                    cy+4.25*math.sin(math.radians(start+(end-start)*i/24))) for i in range(25)]
        points += tail
    return points

for size in (16,32,64):
    scale=8
    im=Image.new('RGBA',(size*scale,size*scale))
    draw=ImageDraw.Draw(im)
    u=size*scale/96
    def box(coords): return tuple(v*u for v in coords)
    draw.rounded_rectangle(box((3,4,93,94)),radius=8*u,fill='#3d5567')
    draw.rounded_rectangle(box((3,2,93,92)),radius=8*u,fill='#bacdd9',outline='#415e73',width=max(1,round(u)))
    for y in (5,47):
        for x in (6,48):
            for inset,radius,color in [(0,3.75,'#7795ab'),(1.9,1.85,'#c1d4df'),(2.7,1.05,'#e8eef3')]:
                draw.rounded_rectangle(box((x+inset,y+inset,x+41.5-inset,y+41.5-inset)),radius=radius*u,fill=color)
            draw.polygon([((x+px)*u,(y+py)*u) for px,py in skeleton()],fill=(0,0,0,0))
            if size>=32:
                for mx in (7.75,33.75):
                    for my in (7.75,33.75):
                        r=3.04
                        draw.ellipse(box((x+mx-r,y+my-r,x+mx+r,y+my+r)),fill='#48687e')
    im.resize((size,size),Image.Resampling.LANCZOS).save(OUT/f'{size}x{size}.png')
print(OUT)
