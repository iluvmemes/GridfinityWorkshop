"""Style native line captures as SVG assets without redrawing model geometry."""
import base64
from pathlib import Path

ROOT=Path(__file__).parent/'GridfinityUIPreview'/'catalog-art'
PALETTE={
    'standard':('Standard bin','#235b80','#dceef9'),
    'clasp':('Clasp bin','#345b70','#e6edf3'),
    'cartridge':('Cartridge','#236979','#dff0f2'),
    'magazine':('Cartridge magazine','#355f87','#e1eafa'),
    'blank':('Custom blank','#536887','#e9eaf4'),
    'tests':('Fit tests','#7b623b','#f5ebd9'),
}

def build():
    for family,(title,ink,wash) in PALETTE.items():
        rgb=[int(ink[i:i+2],16)/255 for i in (1,3,5)]
        matrix=' '.join(f'0 0 0 0 {v:.5f}' for v in rgb)+' 0 0 0 1 0'
        data=base64.b64encode((ROOT/(family+'.png')).read_bytes()).decode('ascii')
        svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="560" viewBox="0 0 720 560" role="img" aria-label="{title}, model-derived line illustration">
<title>{title}</title><desc>Visible edges captured from the native Fusion model. Styling does not alter the geometry.</desc>
<defs><radialGradient id="wash"><stop stop-color="{wash}"/><stop offset="1" stop-color="{wash}" stop-opacity="0"/></radialGradient>
<filter id="ink" x="-2%" y="-2%" width="104%" height="104%" color-interpolation-filters="sRGB"><feMorphology operator="dilate" radius="0.2"/><feColorMatrix type="matrix" values="{matrix}"/></filter></defs>
<ellipse cx="360" cy="288" rx="316" ry="236" fill="url(#wash)"/>
<image width="720" height="560" href="data:image/png;base64,{data}" filter="url(#ink)"/>
</svg>'''
        (ROOT/(family+'-styled.svg')).write_text(svg,encoding='utf-8')

if __name__=='__main__':build()
