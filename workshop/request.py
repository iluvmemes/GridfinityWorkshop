"""Validated generation intent. Units are millimeters; no Fusion dependency."""
import math


def number(data, key, low, high, integer=False):
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{key} must be a finite number.')
    if value < low or value > high or (integer and value != int(value)):
        raise ValueError(f'{key} must be between {low} and {high}' + (' and a whole number.' if integer else '.'))
    return int(value) if integer else float(value)


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Missing baseplate settings.')
    mode, style = data.get('mode'), data.get('style')
    if mode not in ('fit', 'grid') or style not in ('skeleton', 'solid'):
        raise ValueError('Choose a sizing mode and plate style.')
    anchor = number(data, 'anchor', 0, 8, True)
    for key in ('magnets', 'screws'):
        if type(data.get(key)) is not bool:
            raise ValueError(f'{key} must be on or off.')
    diameter = number(data, 'magnetDiameter', 3, 8) if data['magnets'] else 6.08
    depth = number(data, 'magnetDepth', 1, 3) if data['magnets'] else 2.4
    if style == 'skeleton' and data['magnets'] and diameter > 6.5:
        raise ValueError('Skeletonized plates support magnet holes up to 6.5 mm. Choose Solid for larger holes.')
    bed_w = number(data, 'bedWidth', 60, 350)
    bed_d = number(data, 'bedDepth', 60, 350)
    clearance = 0
    if mode == 'fit':
        clearance = number(data, 'clearance', 0, 5)
        width = number(data, 'width', 42, 253) - 2*clearance
        depth_mm = number(data, 'depth', 42, 253) - 2*clearance
        cols, rows = math.floor((width+0.5)/42), math.floor((depth_mm+0.5)/42)
    else:
        cols, rows = number(data, 'columns', 1, 6, True), number(data, 'rows', 1, 6, True)
        width, depth_mm = cols*42-0.5, rows*42-0.5
    if not (1 <= cols <= 6 and 1 <= rows <= 6):
        raise ValueError('The available space must fit between 1 and 6 full cells per axis.')
    extra_x, extra_y = width-(cols*42-.5), depth_mm-(rows*42-.5)
    left, back = extra_x*(anchor%3)/2, extra_y*(anchor//3)/2
    def chunk_size(count, leading, trailing, bed):
        # Padding belongs only to the outer pieces; the last cell is 0.5 mm shorter.
        for stride in range(count, 0, -1):
            spans = [min(stride, count-start)*42
                     + (leading if start == 0 else 0)
                     + (trailing-.5 if start+stride >= count else 0)
                     for start in range(0, count, stride)]
            if max(spans) <= bed + 1e-8:
                return stride
        raise ValueError('The print bed is too small for one cell with this padding.')
    chunk_x = chunk_size(cols, left, extra_x-left, bed_w)
    chunk_y = chunk_size(rows, back, extra_y-back, bed_d)
    pieces = []
    for y in range(0, rows, chunk_y):
        for x in range(0, cols, chunk_x):
            n, m = min(chunk_x, cols-x), min(chunk_y, rows-y)
            x0, y0 = -left if x == 0 else x*42, -back if y == 0 else y*42
            x1 = cols*42-.5+(extra_x-left) if x+n == cols else (x+n)*42
            y1 = rows*42-.5+(extra_y-back) if y+m == rows else (y+m)*42
            pieces.append({'x':x,'y':y,'columns':n,'rows':m,'x0':x0,'y0':y0,'x1':x1,'y1':y1})
    return dict(data, columns=cols, rows=rows, widthMM=width, depthMM=depth_mm,
                left=left, right=extra_x-left, back=back, front=extra_y-back,
                clearance=clearance, pieces=pieces, chunkX=chunk_x, chunkY=chunk_y,
                magnetDiameter=diameter, magnetDepth=depth)
