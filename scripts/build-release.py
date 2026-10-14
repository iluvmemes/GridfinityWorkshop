"""Build a self-contained Fusion add-in ZIP with a stable install folder."""
from pathlib import Path
import argparse, json, zipfile
ROOT = Path(__file__).resolve().parents[1]

def build(output=None):
    version = json.loads((ROOT/'GridfinityWorkshop.manifest').read_text(encoding='utf8'))['version']
    destination = Path(output) if output else ROOT/'dist'/f'GridfinityWorkshop-v{version}.zip'
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = [ROOT/name for name in ('GridfinityWorkshop.py', 'GridfinityWorkshop.manifest', 'README.md', 'LICENSE.md', 'documentation/PRIVACY_POLICY.md')]
    for directory in ('workshop', 'documentation/images'):
        files += [p for p in (ROOT/directory).rglob('*') if p.is_file() and not any(part.startswith('.') or part=='__pycache__' for part in p.relative_to(ROOT).parts) and p.suffix not in ('.pyc', '.pyo')]
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, 'GridfinityWorkshop/'+path.relative_to(ROOT).as_posix())
    print(destination)
    return destination

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    build(parser.parse_args().output)
