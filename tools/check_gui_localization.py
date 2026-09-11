"""Check the built package with an external checkout of the real UCP GUI resolver."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
import yaml

parser=argparse.ArgumentParser()
parser.add_argument('--gui',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
definition=yaml.safe_load((root/'definition.yml').read_text(encoding='utf-8'))
archive=root/'dist'/f"{definition['name']}-{definition['version']}.zip"
languages=yaml.safe_load((args.gui/'resources/lang/languages.yaml').read_text(encoding='utf-8'))
with zipfile.ZipFile(archive) as z:
    options=yaml.safe_load(z.read('options.yml'))['options']
    locales={lang:yaml.safe_load(z.read(f'locale/{lang}.yml')) for lang in languages}
    assert {Path(n).stem for n in z.namelist() if n.startswith('locale/') and n.endswith('.yml')}==set(languages)
for lang,catalog in locales.items():
    assert all(isinstance(k,str) and isinstance(v,str) and v.strip() for k,v in catalog.items()),lang
    assert set(catalog)==set(locales['en']),lang
    assert all('\ufffd' not in v for v in catalog.values()),lang
    for key in ('lobby_load_text','lobby_load_description'):
        assert '{{' not in catalog[key] and '}}' not in catalog[key],(lang,key)
        if lang!='en': assert catalog[key]!=locales['en'][key],(lang,key)
resolver=(args.gui/'src/function/extensions/locale/locale.ts').resolve()
result=subprocess.run(['node',str(root/'tools/check_gui_localization.mjs'),resolver.as_uri()],
    input=json.dumps({'options':options,'locales':locales}),capture_output=True,text=True,encoding='utf-8',check=True)
report=json.loads(result.stdout)
report['gui_resolver_sha256']=hashlib.sha256(resolver.read_bytes()).hexdigest()
report['package_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
(root/'dist/LOCALIZATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'dist/SHA256SUMS.txt').write_text(f"{report['package_sha256']}  {archive.name}\n",encoding='utf-8')
print(f"PASS: packaged category/title/description resolve in all {len(locales)} GUI languages: {', '.join(locales)}")
