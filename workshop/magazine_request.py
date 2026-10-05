"""Matched cartridge magazine layout, millimeters. No Fusion dependency."""
import math
from .request import number


def validate(data):
    if not isinstance(data,dict) or data.get('family')!='magazine':raise ValueError('Expected a magazine recipe.')
    c=dict(data)
    # Recipes saved before the toggle always generated access cutouts.
    c.setdefault('magazineCutouts',True)
    if type(c['magazineCutouts']) is not bool:raise ValueError('Buckle access cutouts must be on or off.')
    for key,lo,hi,integer in [('cols',1,6,True),('rows',1,6,True),('height',2,20,True),
        ('cartLength',30,220,False),('cartWidth',12,80,False),('cartridgeHeight',4,20,True),
        ('slot',.1,.8,False),('quantity',1,48,True)]:c[key]=number(c,key,lo,hi,integer)
    if c.get('orientation') not in ('0','90'):raise ValueError('Choose a cartridge orientation.')
    if c.get('magnet') not in ('off','press','clearance','custom'):raise ValueError('Choose a base magnet fit.')
    if c['magnet']=='press':c['diameter']=6.08
    if c['magnet']=='clearance':c['diameter']=6.5
    if c['magnet']!='off':
        c['diameter']=number(c,'diameter',3,8);c['magnetDepth']=number(c,'magnetDepth',1,3)
    c['title']=str(c.get('title','Cartridge magazine'))[:48]
    c['widthMM']=c['cols']*42-.5;c['depthMM']=c['rows']*42-.5
    c['heightMM']=c['height']*7;c['overallMM']=7+c['cartridgeHeight']*7+3.7
    if c['heightMM']>c['cartridgeHeight']*7-3:
        raise ValueError('Lower the guide walls: leave at least 10 mm of cartridge body exposed above them.')
    if not c['magazineCutouts'] and c['heightMM']>c['cartridgeHeight']*7-17:
        raise ValueError('Enable buckle access cutouts or lower the rim to clear the cartridge pull tab.')
    a=c['cartLength']+12.2+2*c['slot'];b=c['cartWidth']+2*c['slot']
    if c['orientation']=='90':a,b=b,a
    nx=math.floor((c['widthMM']-1.2)/(a+1.2)+1e-9)
    ny=math.floor((c['depthMM']-1.2)/(b+1.2)+1e-9)
    c['capacity']=max(0,nx)*max(0,ny)
    if c['quantity']>c['capacity']:raise ValueError(f"Only {c['capacity']} cartridge seats fit; enlarge the grid, rotate, or reduce quantity.")
    # Center the capacity grid. Only requested seats are cut; unused positions stay solid.
    x0=(c['widthMM']-(nx*a+(nx-1)*1.2))/2
    y0=(c['depthMM']-(ny*b+(ny-1)*1.2))/2
    c['seats']=[dict(x=x0+(i%nx)*(a+1.2),y=y0+(i//nx)*(b+1.2),w=a,d=b) for i in range(c['quantity'])]
    c['windows']=[]
    for index,q in enumerate(c['seats']):
        # End openings clear the full closure envelope and expose the buckle.
        # Keep side guides intact; no directional key is claimed for the symmetric base.
        if c['orientation']=='0':
            for lo,hi in [(0 if index%nx==0 else q['x']-.61,q['x']+6.5),
                (q['x']+q['w']-6.5,c['widthMM'] if index%nx==nx-1 else q['x']+q['w']+.61)]:
                c['windows'].append(dict(x=lo,y=q['y']+2,w=hi-lo,d=q['d']-4))
        else:
            for lo,hi in [(0 if index//nx==0 else q['y']-.61,q['y']+6.5),
                (q['y']+q['d']-6.5,c['depthMM'] if index//nx==ny-1 else q['y']+q['d']+.61)]:
                c['windows'].append(dict(x=q['x']+2,y=lo,w=q['w']-4,d=hi-lo))
    # Merge paired access openings so no later cut targets an already empty web.
    horizontal=c['orientation']=='0';axis,size,cross,cross_size=('x','w','y','d') if horizontal else ('y','d','x','w')
    merged=[]
    for q in sorted(c['windows'],key=lambda q:(q[cross],q[axis])):
        if merged and abs(merged[-1][cross]-q[cross])<1e-8 and q[axis]<=merged[-1][axis]+merged[-1][size]:
            merged[-1][size]=max(merged[-1][axis]+merged[-1][size],q[axis]+q[size])-merged[-1][axis]
        else:merged.append(q)
    c['windows']=merged
    return c
