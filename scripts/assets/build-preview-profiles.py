"""Export the previously captured Fusion section curves as lightweight SVG data."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'source' / 'original-profiles.json'
profiles = {s['name']: s for s in json.loads(SOURCE.read_text())['profiles']}


def point(v):
    return tuple(round(n, 6) for n in v[:2])


def path_from_curves(curves):
    remaining = list(curves)
    current = point(remaining[0]['startPointMM'])
    start = current
    parts = [f'M {current[0]} {current[1]}']
    while remaining:
        for i, curve in enumerate(remaining):
            a, b = point(curve['startPointMM']), point(curve['endPointMM'])
            if current == a:
                target = b
            elif current == b:
                target = a
            else:
                continue
            if curve['type'] == 'Line3D':
                parts.append(f'L {target[0]} {target[1]}')
            else:
                assert curve['type'] == 'Arc3D'
                assert math.isclose(abs(curve['endAngle'] - curve['startAngle']), math.pi / 2)
                cx, cy = point(curve['centerMM'])
                cross = (current[0]-cx)*(target[1]-cy)-(current[1]-cy)*(target[0]-cx)
                r = round(curve['radius'], 6)
                parts.append(f'A {r} {r} 0 0 {int(cross > 0)} {target[0]} {target[1]}')
            current = target
            remaining.pop(i)
            break
        else:
            raise ValueError('Captured profile is not a connected loop')
    assert current == start
    return ' '.join(parts) + ' Z'


data = {
    'source': 'scripts/assets/source/original-profiles.json',
    'pitch': 42,
    'skeleton': path_from_curves(profiles['Skeleton opening']['curves']),
    'mouth': path_from_curves(profiles['Socket mouth']['curves']),
    'shoulder': path_from_curves(profiles['Socket lower shoulder']['curves']),
    'floor': path_from_curves(profiles['Socket floor']['curves']),
    'magnetCenters': [list(point(c['centerMM'])) for c in profiles['Magnet pockets']['curves']],
}
(HERE.parents[1] / 'workshop' / 'cell-profiles.js').write_text(
    '// Derived from captured Fusion sections; do not hand-edit the outlines.\n'
    'const GRIDFINITY_CELL_PROFILES = Object.freeze(' + json.dumps(data, indent=2) + ');\n',
    encoding='utf-8',
)
print('Exported four closed captured profiles and four magnet centers.')
