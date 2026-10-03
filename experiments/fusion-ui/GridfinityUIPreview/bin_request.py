"""Validated bin requests; dimensions in millimeters."""
import math
from .request import number
from .fit_settings import channels,pins


def validate(data):
    if not isinstance(data,dict) or data.get('family') not in ('standard','blank','clasp'):
        raise ValueError('Choose Standard bin, Clasp bin or Custom blank. Cartridge and magazine are previews.')
    c=dict(data)
    clasp=c['family']=='clasp'
    for key,lo,hi in [('cols',2 if clasp else 1,6),('rows',1,6),('height',6 if clasp else 2,20)]:
        c[key]=number(c,key,lo,hi,True)
    if c.get('interior') not in (('open','divided','magnets') if c['family']!='blank' else ('solid','open')):
        raise ValueError('Choose a supported interior.')
    if clasp:
        for key,lo,hi in [('buckle',0,.6),('grip',2,4)]:c[key]=number(c,key,lo,hi)
        pins(c)
        c['rim']=False
    for key in ('rim','scoop','label'):
        if type(c.get(key)) is not bool:raise ValueError(f'{key} must be on or off.')
    if c['scoop'] or c['label']:
        raise ValueError('Scoop and label ledge generation are not enabled yet. Turn them off for this iteration.')
    if c.get('magnet') not in ('off','press','clearance','custom'):raise ValueError('Choose a base magnet fit.')
    if c['magnet']=='press':c['diameter']=6.08
    elif c['magnet']=='clearance':c['diameter']=6.5
    if c['magnet']!='off':
        c['diameter']=number(c,'diameter',3,8)
        c['magnetDepth']=number(c,'magnetDepth',1,3)
    c['widthMM']=c['cols']*42-.5;c['depthMM']=c['rows']*42-.5
    c['heightMM']=c['height']*7;c['overallMM']=c['heightMM']+(3.7 if clasp else 3.8 if c['rim'] else 0)
    c['title']=str(c.get('title','Bin'))[:48]
    c['cavities']=[]
    # A 2 mm native floor above the 5 mm feet. Walls match the preview estimate.
    w,d=c['widthMM']-(12.2 if clasp else 0),c['depthMM']
    if c['interior'] in ('open','divided'):
        nx=number(c,'divX',1,8,True) if c['interior']=='divided' else 1
        ny=number(c,'divY',1,8,True) if c['interior']=='divided' else 1
        cw=(w-4-(nx-1)*1.2)/nx;cd=(d-4-(ny-1)*1.2)/ny
        if min(cw,cd)<3:raise ValueError('Compartments must be at least 3 mm wide and deep.')
        for y in range(ny):
            for x in range(nx):c['cavities'].append(dict(x=2+x*(cw+1.2),y=2+y*(cd+1.2),w=cw,d=cd,r=min(1.75,cw/4,cd/4)))
    elif c['interior']=='magnets':
        shape=c.get('channelShape')
        if shape not in ('round','square','rectangle'):raise ValueError('Choose a channel shape.')
        clearance=number(c,'storedClearance',.1,1)
        cw=(number(c,'storedDiameter',2,30) if shape=='round' else number(c,'channelWidth',2,40))+clearance
        cd=(number(c,'channelDepth',2,80)+clearance) if shape=='rectangle' else cw
        nx=number(c,'channelColumns',1,48,True);ny=number(c,'channelRows',1,48,True)
        gx,gy=channels(c)
        mx=math.floor((w-4+gx)/(cw+gx));my=math.floor((d-4+gy)/(cd+gy))
        if nx>mx or ny>my:raise ValueError(f'Channel layout exceeds capacity {mx} x {my}.')
        x0=(w-(nx*cw+(nx-1)*gx))/2;y0=(d-(ny*cd+(ny-1)*gy))/2
        for y in range(ny):
            for x in range(nx):c['cavities'].append(dict(x=x0+x*(cw+gx),y=y0+y*(cd+gy),w=cw,d=cd,r=0,round=shape=='round'))
    return c
