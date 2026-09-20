"""Exercise the real shared entry point against all seven synthetic native sites."""
from pathlib import Path
import re
import json
import struct
import xml.etree.ElementTree as ET

from lua_support import LuaRuntime, framework_core
import yaml

import test_camera_preview as camera
import test_dead_tree_sprites as trees
import test_lobby_description as description
import test_lobby_load as load
import test_tower_door_height as doors
import test_unique_placement as placement
import test_cliff_texture_direction as cliffs
import test_cliff_texture_source as cliff_source

ROOT = Path(__file__).resolve().parents[1]
BASE, CAVE = 0x400000, 0x60000000


def test_seven_options_compose_without_duplicate_or_overlapping_patches():
    # Reuse narrow public regression fixtures; no game binary is distributed.
    memory = bytearray(b'\x90' * 0x200000)
    memory[:len(placement.fixture())] = placement.fixture()

    def seed(address, data):
        memory[address-BASE:address-BASE+len(data)] = data

    seed(0x4287BD-10, description.fixture())
    source = load.fixture()
    for address, length in ((load.DRAW, 25), (load.ACTION-5, 32),
                            (load.PREP, 22), (load.ITEM, 80)):
        seed(address, source[address-load.PREP:address-load.PREP+length])
    seed(camera.SITE-6, camera.PATTERN)
    seed(trees.SITE-15, trees.PATTERN)
    seed(cliffs.SITE,cliffs.PATTERN)
    for address,pattern in cliff_source.PATTERNS.items():
        seed(address,pattern)
    for address, pattern in doors.SITES.items():
        seed(address-10, bytes.fromhex(pattern))

    for address, pattern in doors.UPDATES.items():
        seed(address-(6 if address==0x41B855 else 10 if address==0x50EDAF else 0),bytes.fromhex(pattern))

    # Also exercise production discovery/preflight in the composition path;
    # the individual ABI tests intentionally use isolated binding fixtures.
    contexts = json.loads((ROOT/'tests/fixtures/native-contexts.json').read_text())['regular']
    for fragment in contexts.values():
        seed(fragment['address'], bytes.fromhex(fragment['bytes']))
    lua = LuaRuntime(unpack_returned_tuples=True, component_bindings=False)
    writes, allocations, cache = [], [], {}
    next_address = CAVE

    def scan(pattern):
        regex = b''.join(b'.' if p == '?' else re.escape(bytes([int(p, 16)]))
                         for p in pattern.split())
        matches = list(re.finditer(regex, memory, re.DOTALL))
        assert len(matches) == 1, pattern
        return BASE + matches[0].start()

    def allocate(size):
        nonlocal next_address
        result = next_address
        allocations.append((result, size))
        next_address += size
        return result

    def data(size, zero=False):
        address=allocate(size)
        if zero:writes.append((address,bytes(size)))
        return address

    def write(address, code):
        assert all(address+len(code) <= old or old+len(data) <= address
                   for old, data in writes), 'duplicate/overlapping patch write'
        writes.append((address, code))
        if address < CAVE:
            seed(address, code)

    def require(name):
        if name not in cache:
            cache[name] = lua.execute((ROOT/f'{name}.lua').read_text())
        return cache[name]

    framework_core(lua, {
        'AOBScan': scan, 'readInteger': lambda at: struct.unpack_from('<i', memory, at-BASE)[0],
        'allocateCode': allocate, 'allocate': data, 'writeCode': write,
    })
    lua.globals().require = require
    options = yaml.safe_load((ROOT/'options.yml').read_text())['options']
    assert len(options) == 7
    assert all(option['contents']['value'] is True for option in options)
    config = {option['url'].split('.', 1)[1]: option['contents']['value'] for option in options}
    module = lua.execute((ROOT/'init.lua').read_text())
    module.enable(module, lua.table_from(config))
    assert len(cache) == 10
    # Fixed code/cache allocation stays below 160 KiB; cliff pixel storage is
    # allocated lazily for visible image sizes, instead of 32 vanilla strips.
    assert sum(size for _, size in allocations) < 160*1024
    for address, size in allocations:
        initialized = set()
        for start, data in writes:
            initialized.update(range(max(address, start), min(address+size, start+len(data))))
        assert len(initialized) == size, 'wrapper length does not match emitted native bytes'
    assert {address for address, _ in writes if address < CAVE} == {
        0x4287bd, 0x516a0f, 0x445263, 0x4eb831, *doors.SITES,
        0x42afb9, 0x4426e0, 0x42733a, *doors.UPDATES, cliffs.SITE, *cliff_source.PATTERNS,
    }
    before = list(writes)
    logs = [row[2] for row in lua.globals().test_logs.values()]
    assert logs[0] == 'startup diagnostics schema=1; begin'
    assert logs[-1].startswith('startup complete;')
    assert sum(message.startswith('native code entry=') for message in logs) > 0
    assert sum(message.startswith('cliff cache bank=') for message in logs) == 1
    assert sum(message.startswith('render epoch=') for message in logs) == 1
    assert sum(message.startswith('tower depth cache=') for message in logs) == 1
    assert sum(message.startswith('tower connection cache=') for message in logs) == 1
    assert sum(message.startswith('installed ') for message in logs) == 7
    assert all(row[1] == 0 for row in lua.globals().test_logs.values())
    module.enable(module, lua.table_from(config))
    assert writes == before
    assert [row[2] for row in lua.globals().test_logs.values()] == logs
    packaged = {entry.attrib['src'] for entry in ET.parse(ROOT/'files.xml').findall('./files/file')}
    assert {f'{name}.lua' for name in cache} <= packaged
    expected_keys = set(yaml.safe_load((ROOT/'locale/en.yml').read_text(encoding='utf-8')))
    for locale in (ROOT/'locale').glob('*.yml'):
        assert set(yaml.safe_load(locale.read_text(encoding='utf-8'))) == expected_keys
