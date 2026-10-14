"""Run existing deep CAD suites through Fusion MCP; all fresh evidence goes here.
Execute this file in a Fusion MCP script, then call run_suite(name).
Requires the loaded add-in and a disposable anchor created by the QA session.
"""
from pathlib import Path
import adsk.core,adsk.fusion,sys,types,time,json,re,importlib,contextlib,io
ROOT=Path(r'D:\Code Projects\GridfinityWorkshop')
OUT=Path(getattr(sys,'_gf_qa_out',ROOT/'.agents/qa/runs/local'))
OUT.mkdir(parents=True,exist_ok=True)
def module():
 return next(m for n,m in list(sys.modules.items()) if n.startswith('__main__') and str(getattr(m,'__file__','')).replace('\\','/').endswith('/workshop/app.py'))
def run_suite(name):
 app=adsk.core.Application.get();sys._gf_qa_anchor.activate();m=module()
 source=(ROOT/'.agents/qa'/('verify-'+name+'-generation.py')).read_text(encoding='utf8') if name!='baseplate' else (ROOT/'.agents/qa/verify-generation.py').read_text(encoding='utf8')
 # Redirect legacy evidence paths while retaining fixture paths and original assertions.
 source=re.sub(r"Path\(r'[^']+\\([^\\']+\.json)'\)",lambda hit:'Path('+repr(str(OUT/(name+'-'+hit.group(1))))+')',source)
 source=source.replace("ROOT/'.agents/qa/runs/local/generation-verification.json'","OUT/'baseplate-generation.json'")
 source=source.replace("Path(r'D:\\Code Projects\\GridfinityWorkshop\\.agents\\qa\\runs\\local\\magazine')","OUT/'magazine'")
 source=source.replace("Path(r'D:\\Code Projects\\GridfinityWorkshop\\.agents\\qa\\runs\\local\\dovetail')","OUT/'dovetail'")
 if name in ('baseplate','bin'):
  doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);doc.name='QA disposable '+name
  g=m.generation if name=='baseplate' else m.catalog.bin_generation
  d=adsk.fusion.Design.cast(app.activeProduct);b=m.catalog.bin_generation
  occ=d.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create());comp=occ.component
  s=b.sketch(comp,'QA overlapping sentinel','0 mm');b.rectangle(s,0,0,30,30);b.extrude(comp,s,'40 mm','QA sentinel')
  if name=='baseplate':
   # Legacy suite reloads generation via this package alias.
   pkg=types.ModuleType('gf_creation_verification');pkg.__path__=[str(ROOT/'workshop')];pkg.document=doc;sys.modules[pkg.__name__]=pkg
  else:
   pkg=types.ModuleType('gf_bin_verification');pkg.document=doc;pkg.generator=g;pkg.results=[];sys.modules[pkg.__name__]=pkg
 ns={'OUT':OUT,'__name__':'qa_suite'};exec(compile(source,name,'exec'),ns)
 started=time.perf_counter();log=io.StringIO()
 with contextlib.redirect_stdout(log):ns['run']('')
 elapsed=time.perf_counter()-started
 (OUT/(name+'-stdout.txt')).write_text(log.getvalue(),encoding='utf8')
 if name in ('baseplate','bin'):doc.close(False)
 sys._gf_qa_anchor.activate()
 ledger=OUT/'cad-suite-results.json';rows=json.loads(ledger.read_text()) if ledger.exists() else []
 rows.append({'suite':name,'status':'PASS','seconds':elapsed});ledger.write_text(json.dumps(rows,indent=2),encoding='utf8')
 print('QA SUITE PASS',name,round(elapsed,2),'seconds')
