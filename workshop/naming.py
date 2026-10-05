"""Human-readable, filename-safe identities shared by a generated layout."""
import re


def next_layout_id(existing_names):
    numbers = [int(m.group(1)) for name in existing_names
               if (m := re.match(r'^GF(\d+)\b', name))]
    return f'GF{max(numbers, default=0)+1:02d}'


def labels(settings, layout_id):
    source = (f"Drawer{settings['width']:g}x{settings['depth']:g}mm"
              if settings['mode'] == 'fit' else f"Grid{settings['columns']}x{settings['rows']}")
    hardware = []
    if settings['magnets']:
        hardware.append(f"M{settings['magnetDiameter']:g}x{settings['magnetDepth']:g}")
    if settings['screws']:
        hardware.append('Screws')
    variant = ' '.join([settings['style'].title()] + hardware)
    identity = f'{layout_id} {source}'
    layout = f"{identity} - {settings['columns']}x{settings['rows']} - {variant}"
    pieces = []
    for index, piece in enumerate(settings['pieces'], 1):
        row = piece['y']//settings['chunkY']+1
        column = piece['x']//settings['chunkX']+1
        width, depth = piece['x1']-piece['x0'], piece['y1']-piece['y0']
        pieces.append(f"{identity} - P{index:02d}of{len(settings['pieces']):02d} R{row}C{column}"
                      f" - {piece['columns']}x{piece['rows']} - {width:g}x{depth:g}mm - {variant}")
    return layout, pieces
