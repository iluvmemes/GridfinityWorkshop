"""Render the recorded Fusion experiment; no third-party dependencies."""
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parent
r = json.loads((ROOT / 'results.json').read_text(encoding='utf-8'))
names = {'baseline':'Existing generator','whole':'Cached whole plate','tool':'Cached socket tools'}

def number(value):
    return f'{value*1000:,.1f}'

def row(label, timing, extra=''):
    return f'<tr><td>{html.escape(label)}</td><td>{number(timing["firstSeconds"])}</td><td><b>{number(timing["warmMedianSeconds"])}</b></td><td>{number(timing["warmMinSeconds"])}–{number(timing["warmMaxSeconds"])}</td>{extra}</tr>'

def table(rows, extra=''):
    return '<table><thead><tr><th>Case</th><th>First (ms)</th><th>Warm median (ms)</th><th>Warm range (ms)</th>'+extra+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table>'

generation = table([row(f'{n}×{n} · {names[k]}',r['generation'][f'{k}-{n}']['timing'],f'<td>{r["generation"][f"{k}-{n}"]["runs"][-1]["timelineItems"]}</td>') for n in [1,3,6] for k in names],'<th>Core timeline items</th>')
padding = table([row(f'{n}×{n} · {names[k]}',r['customization'][f'{k}-{n}']['editTiming']) for n in [1,3,6] for k in names])
resize = table([row(f'To {n}×{n} · {names[k]}',r['resize'][f'{k}-to-{n}']['timing']) for n in [1,3,6] for k in names])
preview = table([row(f'{n}×{n} shaded preview',r['preview']['updates'][str(n)]) for n in [1,3,6]])
preparation = ''.join(f'<tr><td>{n}×{n}</td><td>{number(r["preparation"][str(n)]["sourceGenerationSeconds"])}</td><td>{number(r["preparation"][str(n)]["exportSeconds"])}</td><td>{number(r["preparation"]["meshes"][str(n)]["meshPreparationSeconds"])}</td><td>{r["preparation"][str(n)]["fileBytes"]:,}</td></tr>' for n in [1,3,6])
methodology = ''.join('<dt>'+html.escape(k)+'</dt><dd>'+html.escape(str(v))+'</dd>' for k,v in r['methodology'].items())
page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Gridfinity workflow benchmark</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{{font:16px/1.55 system-ui,sans-serif;color:#172536;background:#f1f4f7;margin:0}}main{{max-width:1050px;margin:auto;padding:40px 24px 80px}}h1{{font-size:34px;line-height:1.15}}h2{{margin-top:42px;font-size:23px}}p{{max-width:850px}}.lead{{font-size:20px}}.card{{background:white;border:1px solid #dce3ea;border-radius:12px;padding:22px;margin:22px 0}}table{{border-collapse:collapse;width:100%;font-size:14px;background:white}}td,th{{padding:10px 12px;border-bottom:1px solid #e3e8ed;text-align:right}}td:first-child,th:first-child{{text-align:left}}th{{background:#e7edf3;font-size:13px}}.scroll{{overflow:auto}}a{{color:#1764a0}}dt{{font-weight:700;margin-top:12px}}dd{{margin:3px 0 0}}small{{color:#4c6073}}.finding{{border-left:5px solid #c58327}}code{{background:#e7edf3;padding:2px 4px}}</style>
<main><small>3 October 2026 · Fusion {r['fusionVersion']} · 1×1, 3×3 and 6×6</small>
<h1>Cached geometry and lightweight previews work.</h1>
<p class="lead">At 6×6, cached whole-plate generation took 499 ms versus 2,403 ms for the current generator. A shaded graphics preview updated in 29 ms without creating model geometry.</p>
<div class="card"><b>Recommendation</b><p>Use cached whole plates for common configurations, cached socket tools for other configurations, custom graphics during input, and ordinary native features for padding. Keep explicit body targets for every Boolean operation.</p></div>
<h2>Generation</h2><p>One initial run and five subsequent runs per case. Preparation and verification are excluded and reported separately. The core timeline counts exclude the test component and sentinel.</p><div class="scroll">{generation}</div>
<h2>Shaded preview updates</h2><p>Replacement of cached mesh graphics, a changing padding strip, a placement transform, and viewport refresh. No BRep bodies, mesh bodies, sketches or timeline items were created. The first graphics update includes a visible initialization cost; these are API timings, not input-to-photon latency.</p><div class="scroll">{preview}</div>
<h2>Native padding edits</h2><p>One origin-plane sketch, an outward extrusion, and an explicitly targeted join. Widths tested: 4, 6, 3, 8, 5, 4 mm. Cached whole-plate padding edits ranged from 12 ms at 1×1 to 51 ms at 6×6 by warm median.</p><div class="scroll">{padding}</div>
<h2>Grid-size changes with padding</h2><p>Whole plates replace the Base Feature body and update the padding length. Socket tools update the native pattern and explicitly refresh the Combine tool selection. The baseline rebuilds the core and recreates the same padding. Source-size resets are outside the measured interval.</p><div class="scroll">{resize}</div>
<div class="card finding"><b>Found: healthy timeline, incorrect geometry</b><p>Changing only the socket-tool pattern from 1×1 to 3×3 left eight new cutter bodies outside the original Combine selection. Fusion reported no feature errors, but only the original socket was cut. Refreshing <code>CombineFeature.toolBodies</code> after resizing corrected the geometry and passed all subsequent checks. A bare grid-count parameter is therefore insufficient for this implementation.</p></div>
<h2>Upfront preset preparation</h2><p>The source-generation values below are the initial baseline runs. Export and mesh calculation are separate costs. The captured socket tool took {number(r['preparation']['socketTool']['generationAndCaptureSeconds'])} ms to generate and capture and occupies {r['preparation']['socketTool']['fileBytes']:,} bytes.</p><div class="scroll"><table><tr><th>Preset</th><th>Source generation (ms)</th><th>Export (ms)</th><th>Mesh calculation (ms)</th><th>BRep file bytes</th></tr>{preparation}</table></div>
<h2>Correctness and isolation</h2><p>All final cached solids, padded solids and resized solids matched their baseline counterparts under Fusion Boolean symmetric-difference checks: zero extra and zero missing volume. Final models were single-lump solids with healthy features. Every overlapping sentinel body was unchanged. These results cover the tested baseplate workflow; they do not clear unrelated bin or lid cutting behavior.</p>
<h2>Method and limits</h2><dl>{methodology}</dl>
<h2>Reproduce and inspect</h2><p><a href="results.json">Raw results</a> · <a href="runner.py">Fusion benchmark runner</a> · <a href="render_report.py">Report renderer</a></p><p>Import runner.py into Fusion's Python context once and call <code>run_phase</code> for the bounded phases documented in that function. Experimental documents remain unsaved. The production add-in is unchanged.</p></main></html>'''
(ROOT / 'report.html').write_text(page,encoding='utf-8')
print(ROOT / 'report.html')
