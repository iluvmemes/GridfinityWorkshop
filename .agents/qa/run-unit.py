from pathlib import Path
import subprocess,json,time,sys
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'.agents/qa/runs/local'
OUT.mkdir(parents=True,exist_ok=True)
results=[]
for p in sorted((ROOT/'experiments/fusion-ui').glob('test-*'))+sorted(p for p in (ROOT/'.agents/qa').glob('test-*') if p.name!='test-release.py'):
 if p.suffix not in ('.py','.js'):continue
 command=([sys.executable] if p.suffix=='.py' else ['node'])+[str(p)]
 start=time.perf_counter();r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
 row=dict(test=p.name,command=command,exitCode=r.returncode,seconds=time.perf_counter()-start,stdout=r.stdout,stderr=r.stderr);results.append(row)
 print(p.name,r.returncode,flush=True)
(OUT/'unit-results.json').write_text(json.dumps(results,indent=2),encoding='utf8')
sys.exit(any(r['exitCode'] for r in results))
