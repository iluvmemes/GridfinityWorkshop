"""Dovetail retention dimensions in millimeters, independent of Fusion."""
import math
from .request import number


def plan(c):
    c.setdefault('lidRetention', 'none')
    c.setdefault('lidDetentInterference', .1)
    c.setdefault('lidMagnetSize', '6')
    c.setdefault('lidMagnetFit', 'press')
    if c['lidRetention'] not in ('none', 'bump', 'magnet', 'both'):
        raise ValueError('Choose a dovetail lid retention style.')
    if not c.get('dovetailLid') or c.get('family') != 'standard':
        c['lidRetention'] = 'none'
    detent = c['lidRetention'] in ('bump', 'both')
    magnetic = c['lidRetention'] in ('magnet', 'both')
    w, d = c['widthMM'], c['depthMM']
    result = dict(detents=[], seats=[], diameter=0, magnetDepth=2, magnets=0)
    if detent:
        interference = number(c, 'lidDetentInterference', .05, .2)
        # Female sliding plane x-z=1.9; tongue plane x-z=2.2.
        # The sphere center sits inside the tongue, leaving only a small cap.
        radius = .6 / math.sqrt(2) + interference
        result['detents'] = [dict(x=x, y=d-6, z=1.15, radius=radius,
                                  recessRadius=radius+.1, trackEnd=d-8)
                             for x in (3.65, w-3.65)]
    if magnetic:
        if c['lidMagnetSize'] not in ('3', '6'):
            raise ValueError('Choose 3 x 2 mm or 6 x 2 mm lid magnets.')
        if c['lidMagnetFit'] not in ('press', 'clearance'):
            raise ValueError('Choose a lid magnet pocket fit.')
        diameter = int(c['lidMagnetSize']) + (.08 if c['lidMagnetFit']=='press' else .5)
        span = diameter + 3  # 1.5 mm of material around each pocket.
        result.update(diameter=diameter, magnets=4)
        result['seats'] = [dict(x=x, y=d-5.5, span=span) for x in (8.5, w-8.5)]
        if c.get('interior') == 'magnets':
            for seat in result['seats']:
                for q in c['cavities']:
                    # Conservative envelope test preserves the full channel opening.
                    if (q['x'] < seat['x']+span/2 and q['x']+q['w'] > seat['x']-span/2
                            and q['y'] < d-.5 and q['y']+q['d'] > seat['y']-span/2):
                        raise ValueError('Lid magnet ledges overlap storage channels. Reduce the channel array or choose bump retention.')
    return result
