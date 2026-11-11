"""Named display colors, shared by preview and 3MF export."""
import json
from pathlib import Path
COLORS={c['id']:c for c in json.loads((Path(__file__).parent/'filament-colors.json').read_text(encoding='utf8'))['colors']}

def color(key):
    if not isinstance(key,str) or key not in COLORS:raise ValueError('Choose a color swatch.')
    return COLORS[key]

def apply(design,body,key):
    import adsk.core
    c=color(key);name='PLA - '+c['name'];appearance=design.appearances.itemByName(name)
    if not appearance:
        template=next((a for lib in adsk.core.Application.get().materialLibraries for a in lib.appearances if a.name=='Plastic - Matte (White)'),None)
        if not template:raise RuntimeError('The Fusion matte plastic appearance library is unavailable.')
        appearance=design.appearances.addByCopy(template,name)
        rgb=tuple(int(c['hex'][i:i+2],16) for i in (1,3,5))
        appearance.appearanceProperties.itemById('opaque_albedo').value=adsk.core.Color.create(*rgb,255)
    body.appearance=appearance
    body.attributes.add('GridfinityWorkshop','filamentColor',json.dumps(c))
