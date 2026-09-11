"""Build only files declared by the module's package manifest."""
from pathlib import Path
import hashlib
import json
import yaml
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parents[1]
files=[]
for entry in ET.parse(root/'files.xml').findall('./files/file'):
    target=root/entry.attrib['src']
    files.extend(sorted(target.rglob('*')) if target.is_dir() else [target])
files=sorted({f for f in files if f.is_file()})
out=root/'dist';out.mkdir(exist_ok=True)
definition=yaml.safe_load((root/'definition.yml').read_text(encoding='utf-8'))
archive=out/f"{definition['name']}-{definition['version']}.zip"
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
    for file in files:z.write(file,file.relative_to(root).as_posix())
print(json.dumps(dict(archive=str(archive),files=len(files),bytes=archive.stat().st_size,
    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
    contents=[f.relative_to(root).as_posix() for f in files]),indent=2))
