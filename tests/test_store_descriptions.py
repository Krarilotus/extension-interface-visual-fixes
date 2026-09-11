"""Prevent publishing another package whose description viewer is empty."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('en', 'de', 'fr', 'ru', 'hu', 'tr', 'ch', 'es', 'fa')


@pytest.mark.parametrize('language', LANGUAGES)
def test_each_description_is_packaged_concise_and_has_real_screenshots(language):
    entries = [item.attrib['src'] for item in
               ET.parse(ROOT / 'files.xml').findall('./files/file')]
    assert 'locale' in entries
    text = (ROOT / 'locale' / f'description-{language}.md').read_text(encoding='utf-8')
    assert text.startswith('# Interface and Visual Fixes\n')
    assert len(re.findall(r'^- ', text, re.M)) == 7
    assert len(text.split()) < 230
    assert '\ufffd' not in text and 'stair6' in text.lower()
    images = re.findall(r'!\[([^\]]+)\]\(([^)]+)\)', text)
    assert len(images) == 2
    for caption, url in images:
        assert caption.strip()
        match = re.fullmatch(
            r'https://raw.githubusercontent.com/Krarilotus/extension-interface-visual-fixes/'
            r'[0-9a-f]{40}/(docs/store/[^/]+\.png)', url)
        assert match, 'Installed and Store viewers need immutable absolute image URLs'
        assert (ROOT / match[1]).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')


def test_description_update_has_a_new_package_version():
    definition = yaml.safe_load((ROOT / 'definition.yml').read_text())
    assert definition['version'] != '0.1.0', 'The Store reuses already-published versions'

