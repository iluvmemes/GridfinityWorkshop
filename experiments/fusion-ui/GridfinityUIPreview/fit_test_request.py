"""Printable calibration recipes; bounded geometry, with no Fusion dependency."""
from .request import number
from .fit_settings import channels,pins


def validate(data):
    if not isinstance(data,dict) or data.get('family')!='tests':raise ValueError('Expected a fit test recipe.')
    c=dict(data);c.pop('closure',None);kind=c.get('testType')
    if kind not in ('pin','closure','magnet','spacing','envelope'):raise ValueError('Choose a fit test.')
    c.setdefault('testSource','clasp')
    if c['testSource'] not in ('clasp','standard','blank'):raise ValueError('Choose a supported source recipe.')
    if kind in ('pin','closure') and c['testSource']!='clasp':raise ValueError('Pin and closure tests apply to the Clasp bin recipe.')
    c['title']=str(c.get('title','Fit tests'))[:48]
    c['samples']=[]
    if kind=='closure':
        from .bin_request import validate as bin_validate
        c['closure']=bin_validate(dict(c,family='clasp',cols=2,rows=1,height=6,interior='open',magnet='off',rim=False,scoop=False,label=False))
        c['samples']=[dict(label='Working closure',w=83.5,d=41.5,h=28.7)]
    elif kind=='envelope':
        for key in ['cols','rows']:c[key]=number(c,key,1,6,True)
        c['height']=number(c,'height',2,20,True)
        if type(c.get('testPosts')) is not bool:raise ValueError('Height posts must be on or off.')
        source=c.get('testSource','clasp')
        c['envelopeHeight']=c['height']*7+(3.7 if source=='clasp' else 3.8 if c.get('rim',False) else 0)
        c['samples']=[dict(label=f"{c['cols']*42-.5:g}x{c['rows']*42-.5:g}",w=c['cols']*42-.5,d=c['rows']*42-.5,h=c['envelopeHeight'] if c['testPosts'] else 3)]
    else:
        count=number(c,'testCount',1,7,True);step=number(c,'testStep',.01,10)
        limits={'pin':(0,1),'magnet':(3,8),'spacing':(1,30)}
        start=number(c,'testStart',*limits[kind]);end=start+(count-1)*step
        if end>limits[kind][1]+1e-8:raise ValueError('The final sample exceeds the allowed range; reduce start, step or count.')
        if kind=='pin':
            pins(c)
            if c['pinDiameter']+start<1.8 or c['pinDiameter']+end>2.7+1e-8:raise ValueError('Test bores must be 1.80 to 2.70 mm.')
        elif kind=='magnet':c['magnetDepth']=number(c,'magnetDepth',1,3)
        else:
            channels(c)
            if c.get('testAxis') not in ('both','x','y'):raise ValueError('Choose the spacing direction.')
            c['testStackDepth']=number(c,'testStackDepth',3,120)
            c['channelColumns']=number(c,'channelColumns',2,5,True);c['channelRows']=number(c,'channelRows',2,5,True)
            clearance=number(c,'storedClearance',.1,1)
            shape=c.get('channelShape')
            if shape not in ('round','square','rectangle'):raise ValueError('Choose a channel shape.')
            c['cw']=(number(c,'storedDiameter',2,30) if shape=='round' else number(c,'channelWidth',2,40))+clearance
            c['cd']=number(c,'channelDepth',2,80)+clearance if shape=='rectangle' else c['cw']
        for index in range(count):
            value=round(start+index*step,6)
            if kind=='pin':sample=dict(value=value,bore=c['pinDiameter']+value,w=14,d=10,h=8,label=f'{c["pinDiameter"]+value:.2f}')
            elif kind=='magnet':sample=dict(value=value,bore=value,w=14,d=19,h=c['magnetDepth']+2,label=f'{value:.2f}')
            else:
                gx=value if c['testAxis'] in ('both','x') else c['channelGapX'];gy=value if c['testAxis'] in ('both','y') else c['channelGapY']
                w=4+c['channelColumns']*c['cw']+(c['channelColumns']-1)*gx
                d=4+c['channelRows']*c['cd']+(c['channelRows']-1)*gy
                sample=dict(value=value,gapX=gx,gapY=gy,w=w,d=d+6,h=c['testStackDepth']+2,label=f'{gx:g}x{gy:g}')
            c['samples'].append(sample)
    # All samples are separate solids arranged within a maximum 6x6 print area.
    x=y=row=0
    for sample in c['samples']:
        w,d=sample['w'],sample['d']
        if w>251.5 or d>251.5:raise ValueError('A sample exceeds a 6x6 footprint; reduce channels or spacing.')
        if x+w>251.5:x=0;y+=row+8;row=0
        if y+d>251.5:raise ValueError('The sample set exceeds a 6x6 print area; reduce sample count.')
        sample.update(x=x,y=y);x+=w+8;row=max(row,d)
    return c
