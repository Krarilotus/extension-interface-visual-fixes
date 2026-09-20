"""The review ZIP must match UCP's manifest-copy layout used by the Store."""
from pathlib import Path
import runpy
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def test_nested_file_defaults_to_package_root_and_directory_keeps_its_name():
    result = runpy.run_path(str(ROOT/'tools/build.py'))
    with ZipFile(result['archive']) as package:
        assert 'docs/crash-reporting.md' not in package.namelist()
        assert package.read('crash-reporting.md') == (ROOT/'docs/crash-reporting.md').read_bytes()
        assert package.read('locale/description-en.md') == (ROOT/'locale/description-en.md').read_bytes()
        assert not any(name.startswith(('tests/', 'tools/')) for name in package.namelist())
