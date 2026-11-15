from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
root=Path(__file__).resolve().parents[1]
output=root/'public/earthtrace-source.zip'
skip={'.git','.next','.next-dev','node_modules','out','.openai','.venv','__pycache__','.pytest_cache'}
with ZipFile(output,'w',ZIP_DEFLATED) as z:
 for p in root.rglob('*'):
  relative=p.relative_to(root)
  if not p.is_file() or any(part in skip for part in relative.parts) or p==output or p.name=='qa-mobile.html':continue
  if p.name.startswith('.env') and p.name!='.env.example':continue
  if p.suffix in {'.pyc','.db','.tsbuildinfo'} or p.name=='firebase-service-account.json':continue
  z.write(p,Path('earthtrace')/relative)
print(output)
