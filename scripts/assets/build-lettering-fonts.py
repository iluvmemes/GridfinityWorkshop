"""Build offline SVG glyph outlines. Requires fontTools only on the build machine.

Source: google/fonts ofl/rubik and ofl/atkinsonhyperlegiblenext (SIL OFL).
Keep the original fonts and their licenses alongside the generated outline assets.
"""
import hashlib,json
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

ROOT=Path(__file__).resolve().parents[2]/'workshop/fonts'

def build():
    result={}
    for key,filename,name,weight in [('rubik','Rubik.ttf','Rubik SemiBold',600),
            ('atkinson','AtkinsonHyperlegibleNext.ttf','Atkinson Hyperlegible Next Bold',700)]:
        font=instantiateVariableFont(TTFont(ROOT/filename),{'wght':weight},inplace=True)
        gs=font.getGlyphSet();cmap=font.getBestCmap()
        chars={chr(cp):g for cp,g in cmap.items() if 32<=cp<=591 or cp in (0x2013,0x2014,0x2019,0x2022,0x2212,0x2300)}
        glyphs={}
        for ch,g in chars.items():
            pen=SVGPathPen(gs,ntos=lambda n:format(n,'.5f').rstrip('0').rstrip('.') if n else '0')
            gs[g].draw(TransformPen(pen,(1,0,0,-1,0,0)))
            bp=BoundsPen(gs);gs[g].draw(bp)
            bounds=bp.bounds
            glyphs[ch]={'path':pen.getCommands(),'advance':gs[g].width,
                        'bounds':[bounds[0],-bounds[3],bounds[2],-bounds[1]] if bounds else None}
        # Resolve GPOS pair/class kerning into a small runtime character-pair map.
        pairs={}
        if 'GPOS' in font:
            lookups=font['GPOS'].table.LookupList.Lookup
            for lookup in lookups:
                for raw in lookup.SubTable:
                    sub=raw.ExtSubTable if lookup.LookupType==9 else raw
                    if not hasattr(sub,'PairSet') and not hasattr(sub,'Class1Record'):continue
                    coverage=set(sub.Coverage.glyphs)
                    for left,lg in chars.items():
                        if lg not in coverage:continue
                        if sub.Format==1:
                            records=sub.PairSet[sub.Coverage.glyphs.index(lg)].PairValueRecord
                            values={r.SecondGlyph:getattr(r.Value1,'XAdvance',0) for r in records}
                            for right,rg in chars.items():
                                value=values.get(rg,0)
                                if value:pairs[left+right]=pairs.get(left+right,0)+value
                        elif sub.Format==2:
                            row=sub.Class1Record[sub.ClassDef1.classDefs.get(lg,0)]
                            for right,rg in chars.items():
                                value=getattr(row.Class2Record[sub.ClassDef2.classDefs.get(rg,0)].Value1,'XAdvance',0)
                                if value:pairs[left+right]=pairs.get(left+right,0)+value
        result[key]={'name':name,'weight':weight,'unitsPerEm':font['head'].unitsPerEm,'glyphs':glyphs,'kerning':pairs,
                     'source':filename,'sha256':hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()}
    encoded=json.dumps(result,ensure_ascii=True,separators=(',',':'))
    (ROOT/'outlines.json').write_text(encoded,encoding='utf8')
    (ROOT/'outlines.js').write_text('window.WorkshopFonts='+encoded+';\n',encoding='utf8')
    print({key:len(value['glyphs']) for key,value in result.items()})

if __name__=='__main__':build()
