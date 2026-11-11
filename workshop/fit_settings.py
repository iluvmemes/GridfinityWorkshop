"""Shared mechanical fit settings and migration of pre-allowance recipes (mm)."""
from .request import number


def channels(c):
    c.setdefault('channelGapX',1)
    c.setdefault('channelGapY',1)
    c.setdefault('channelGapLinked',True)
    if type(c['channelGapLinked']) is not bool:raise ValueError('Channel spacing link must be on or off.')
    c['channelGapX']=number(c,'channelGapX',1,30)
    if c['channelGapLinked']:c['channelGapY']=c['channelGapX']
    else:c['channelGapY']=number(c,'channelGapY',1,30)
    return c['channelGapX'],c['channelGapY']


def pins(c):
    if 'pinDiameter' not in c:
        # Old PinHole drove body/lid hinge; lid latch and buckle added 0.20 mm.
        old=number(c,'pin',1.8,2.5) if 'pin' in c else 2
        c.update(pinDiameter=1.75,pinAllowance=old-1.75,pinOverrides=True,
                 bodyPinAllowance=old-1.75,lidPinAllowance=old-1.75,
                 lidLatchAllowance=old+.2-1.75,bucklePinAllowance=old+.2-1.75)
    c['pinDiameter']=number(c,'pinDiameter',1.5,2.5)
    c['pinAllowance']=number(c,'pinAllowance',0,1)
    c.setdefault('pinOverrides',False)
    if type(c['pinOverrides']) is not bool:raise ValueError('Pin overrides must be on or off.')
    result={}
    for key in ['bodyPinAllowance','lidPinAllowance','lidLatchAllowance','bucklePinAllowance']:
        if c['pinOverrides']:allowance=number(c,key,0,1)
        else:allowance=c['pinAllowance'];c[key]=allowance
        value=c['pinDiameter']+allowance
        if not 1.8-1e-8<=value<=2.7+1e-8:raise ValueError('Resulting pin bores must be 1.80 to 2.70 mm.')
        result[key]=value
    c['pinBores']=result
    return result
