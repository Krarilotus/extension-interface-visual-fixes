"""Prevent publishing another package whose description viewer is empty."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('en', 'de', 'fr', 'ru', 'hu', 'tr', 'ch', 'es', 'fa')


@pytest.mark.parametrize('language', LANGUAGES)
def test_each_description_is_packaged_concise_and_has_real_screenshots(language):
    entries = [item.attrib['src'] for item in
               ET.parse(ROOT / 'files.xml').findall('./files/file')]
    assert 'locale' in entries
    text = (ROOT / 'locale' / f'description-{language}.md').read_text(encoding='utf-8')
    assert text.startswith('# Interface and Visual Fixes\n')
    assert len(re.findall(r'^- ', text, re.M)) == 8
    # The default/plugin paragraph added in 0.2.0; still a short viewer text.
    assert len(text.split()) < 280
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


@pytest.mark.parametrize('language', [language for language in LANGUAGES if language != 'en'])
def test_new_default_paragraph_and_ghost_bullet_are_translated(language):
    # 0.2.0 added the defaults/plugins paragraph and the Ghost Objects bullet; an
    # English copy in another language's viewer is a missing translation.
    def parts(name):
        lines = (ROOT / 'locale' / f'description-{name}.md').read_text(encoding='utf-8').splitlines()
        # Title, blank line, then the defaults/plugins paragraph (one line).
        bullets = [line for line in lines if line.startswith('- ')]
        return lines[2], bullets[-1]
    english, translated = parts('en'), parts(language)
    assert translated[0].strip() and translated[0] != english[0]
    assert translated[1] != english[1]
