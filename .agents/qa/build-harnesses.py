from pathlib import Path
root=Path.cwd();assets=root/'workshop';qa=root/'.agents/qa'
for source,target,script in [('catalog.html','catalog-harness.html','catalog-harness.js'),('palette.html','baseplate-harness.html','baseplate-harness.js')]:
 s=(assets/source).read_text(encoding='utf8').replace('<head>','<head><base href="'+assets.as_uri()+'/">').replace('</head>','<script defer src="'+(qa/script).as_uri()+'?qa=4"></script></head>')
 (qa/target).write_text(s,encoding='utf8')
