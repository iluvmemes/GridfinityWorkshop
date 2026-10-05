"""Offline repository checks, safe to execute with a read-only CI token."""
import ast,json,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
for name in tracked:
    p=root/name
    if name.endswith('.py') and p.is_file():ast.parse(p.read_text(encoding='utf-8-sig'),filename=name)
for p in (root/'.github/workflows').glob('*.y*ml'):
    for action in re.findall(r'uses:\s*([^\s#]+)',p.read_text()):
        if not action.startswith('./') and not re.fullmatch(r'[\w./-]+@[0-9a-f]{40}',action):
            raise SystemExit(f'{p.name}: pin action to a full commit SHA: {action}')
inventory=root/'.github/dependencies/package.json'
if inventory.exists():
    version=json.loads(inventory.read_text())['dependencies']['three']
    for vendor in [root/'workshop/vendor',root/'experiments/fusion-ui/GridfinityUIPreview/vendor']:
        if vendor.exists():
            assert f'Three.js {version} (MIT)' in (vendor/'README.txt').read_text(), 'Update the bundled Three.js and its provenance with the dependency inventory'
runner=root/'.agents/qa/run-unit.py'
if runner.exists():subprocess.run([sys.executable,str(runner),str(root/'dist/security-tests')],cwd=root,check=True)
print('PASS: Python syntax, immutable action references, dependency inventory and available local regression suites.')
