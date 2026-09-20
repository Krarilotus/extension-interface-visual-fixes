"""Real instruction fragments exercise discovery independently of ABI fixtures.

Full executable scans are a separate private acceptance check. These small
contexts let CI check relocation and unsupported/occupied capabilities without
redistributing game executables or assuming fixed bindings in production.
"""
import json
import re
import struct
from pathlib import Path

import pytest
from lua_support import LuaRuntime, framework_core

ROOT = Path(__file__).resolve().parents[1]
CONTEXTS = json.loads((ROOT / 'tests/fixtures/native-contexts.json').read_text())
EXPECTED = json.loads((ROOT / 'tests/fixtures/component-bindings.json').read_text())
BASE = 0x400000
OPTIONS = ('clear-unique-building-preview', 'building-preview-during-camera-movement',
           'distinct-dead-tree-sprites', 'tower-door-height', 'lobby-load',
           'cliff-texture-direction')


def fixture(family='regular'):
    memory = bytearray(b'\xcc' * 0x200000)
    chunks = CONTEXTS[family]
    for fragment in chunks.values():
        at = fragment['address'] - BASE
        data = bytes.fromhex(fragment['bytes'])
        memory[at:at+len(data)] = data
    lua = LuaRuntime(component_bindings=False)
    scans, allocations = [], []

    def scan(pattern):
        regex = b''.join(b'.' if t == '?' else re.escape(bytes([int(t, 16)]))
                         for t in pattern.split())
        hits = list(re.finditer(regex, memory, re.S))
        # Offline uniqueness oracle, not an alternative production scanner.
        assert len(hits) == 1, (pattern, len(hits))
        scans.append(pattern)
        return BASE + hits[0].start()

    framework_core(lua, {
        'AOBScan': scan,
        'readInteger': lambda at: struct.unpack_from('<i', memory, at-BASE)[0],
        'allocateCode': lambda size: allocations.append(size),
    })
    layout = lua.eval('require("native-layout")')
    # Lua 5.4 require may additionally return loader data on first load.
    if isinstance(layout, tuple):
        layout = layout[0]
    return lua, layout, memory, chunks, scans, allocations


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_all_bindings_match_independent_reference_and_are_retained(family):
    lua, layout, _, _, scans, allocations = fixture(family)
    layout.prepare(lua.table_from(dict.fromkeys(OPTIONS, True)))
    expected = EXPECTED[family]['addresses']
    assert {name: layout.addresses[name] for name in expected} == expected
    count = len(scans)
    logs = [row[2] for row in lua.globals().test_logs.values()]
    assert set(logs) == {f'native binding {name}=0x{address:08X}' for name, address in expected.items()}
    assert len(logs) == len(expected)
    for _ in range(10):
        for name in expected:
            assert layout.addresses[name] == expected[name]
    assert len(scans) == count
    assert [row[2] for row in lua.globals().test_logs.values()] == logs
    assert allocations == []


@pytest.mark.parametrize('name', ('RenderMapEntry', 'ProcessHeap', 'PlacementEntry',
                                  'MinimapNotify', 'LobbyLoadItem', 'ImageHeaders'))
def test_missing_capability_stops_before_any_patch_allocation(name):
    lua, _, memory, chunks, _, allocations = fixture()
    memory[chunks[name]['address'] - BASE] = 0x90
    init = lua.execute((ROOT / 'init.lua').read_text())
    enabled = dict.fromkeys(OPTIONS, True)
    enabled['lobby-map-descriptions'] = True
    with pytest.raises(Exception, match='unsupported or occupied native capability'):
        init.enable(init, lua.table_from(enabled))
    assert allocations == []


@pytest.mark.parametrize('name,call_offset', (('TowerDoorCall1', 10),
                                            ('FoundationDrawCall', 0),
                                            ('PlacementNotifyCall', 6)))
def test_redirected_call_is_not_accepted_by_wildcarded_operand(name, call_offset):
    lua, layout, memory, chunks, _, allocations = fixture()
    operand = chunks[name]['address'] - BASE + call_offset + 1
    old = struct.unpack_from('<i', memory, operand)[0]
    struct.pack_into('<i', memory, operand, old + 9)
    with pytest.raises(Exception, match='inconsistent or occupied native capability'):
        layout.prepare(lua.table_from(dict.fromkeys(OPTIONS, True)))
    assert allocations == []


def test_disabled_feature_does_not_require_its_context():
    lua, layout, memory, chunks, _, _ = fixture()
    memory[chunks['CliffSource']['address'] - BASE] = 0x90
    layout.prepare(lua.table_from({'building-preview-during-camera-movement': True}))


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_moved_render_entry_and_changed_image_operand_are_used(family):
    lua, layout, memory, chunks, _, _ = fixture(family)
    fragment = chunks['RenderMapEntry']
    start = fragment['address'] - BASE
    data = bytes.fromhex(fragment['bytes'])
    memory[start:start+len(data)] = b'\xcc' * len(data)
    memory[start+0x100000:start+0x100000+len(data)] = data
    struct.pack_into('<I', memory, chunks['ImageHeaders']['address'] - BASE + 3, 0x35000000)
    layout.prepare(lua.table_from({'cliff-texture-direction': True}))
    assert layout.addresses.RenderMapEntry == fragment['address'] + 0x100000
    assert layout.addresses.RenderMapResume == fragment['address'] + 0x100008
    assert layout.addresses.ImageHeaders == 0x35000000
