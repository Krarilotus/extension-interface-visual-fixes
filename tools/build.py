"""Build only files declared by the module's package manifest."""
from pathlib import Path
import hashlib
import json
import yaml
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parents[1]
files={}
for entry in ET.parse(root/'files.xml').findall('./files/file'):
    target=root/entry.attrib['src']
    # UCP's build-module-package-files.ps1 copies into target (default root),
    # preserving a directory's name but not an individual file's source parents.
    destination=Path(entry.attrib.get('target', '.'))/target.name
    for file in sorted(target.rglob('*')) if target.is_dir() else [target]:
        if file.is_file():
            name=destination/file.relative_to(target) if target.is_dir() else destination
            files[name.as_posix()]=file
files=dict(sorted(files.items()))
out=root/'dist';out.mkdir(exist_ok=True)
definition=yaml.safe_load((root/'definition.yml').read_text(encoding='utf-8'))
archive=out/f"{definition['name']}-{definition['version']}.zip"
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
    for name,file in files.items():z.write(file,name)
print(json.dumps(dict(archive=str(archive),files=len(files),bytes=archive.stat().st_size,
    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
    contents=list(files)),indent=2))
