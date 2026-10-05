"""Verify the actual release ZIP is portable and contains all offline dependencies."""
from pathlib import Path
import importlib.util, json, re, tempfile, zipfile, compileall
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('release_builder',ROOT/'scripts/build-release.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
with tempfile.TemporaryDirectory() as temp:
    archive=builder.build(Path(temp)/'release.zip')
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        assert all(n.startswith('GridfinityWorkshop/') for n in names)
        assert not any('/'+part+'/' in n for n in names for part in ('experiments','outputs','.agents','__pycache__','commands'))
        assert 'GridfinityWorkshop/workshop/vendor/three-LICENSE.txt' in names
        assert 'GridfinityWorkshop/workshop/presets/clasp-template.f3d' in names
        assert 'GridfinityWorkshop/workshop/presets/cartridge-template.f3d' in names
        for x in range(1,7):
            for y in range(1,7):assert f'GridfinityWorkshop/workshop/presets/bin-rim-{x}x{y}.smt' in names
        z.extractall(temp)
    root=Path(temp)/'GridfinityWorkshop'
    assert json.loads((root/'GridfinityWorkshop.manifest').read_text())['runOnStartup'] is True
    assert compileall.compile_dir(root,quiet=1)
    for path in (root/'workshop').rglob('*'):
        if path.suffix not in ('.html','.svg'):continue
        text=path.read_text(encoding='utf8')
        for target in re.findall(r'(?:src|href)=["\']([^"\']+)',text):
            if target.startswith(('http:', 'https:', '#','data:')):continue
            assert (path.parent/target.split('?')[0]).exists(),(path,target)
    for target in re.findall(r'!\[[^]]*\]\(([^)]+)\)', (root/'README.md').read_text(encoding='utf8')):
        assert (root/target).is_file(), target
    assert len(list((root/'workshop/presets').glob('*.smt')))==39
    print(f'PASS: {len(names)} archive entries; isolated extraction, Python syntax, 39 SMT presets, templates and local HTML/SVG assets.')
