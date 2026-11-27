"""Real instruction fragments exercise discovery independently of ABI fixtures.

Full executable scans are a separate private acceptance check. These small
contexts let CI check relocation and unsupported/occupied capabilities without
redistributing game executables or assuming fixed bindings in production.
"""
import json
import struct
from pathlib import Path

import pytest
from lua_support import LuaRuntime, aob, framework_core

ROOT = Path(__file__).resolve().parents[1]
CONTEXTS = json.loads((ROOT / 'tests/fixtures/native-contexts.json').read_text())
EXPECTED = json.loads((ROOT / 'tests/fixtures/component-bindings.json').read_text())
BASE = 0x400000
OPTIONS = ('clear-unique-building-preview', 'building-preview-during-camera-movement',
           'distinct-dead-tree-sprites', 'tower-door-height', 'lobby-load',
           'cliff-texture-direction', 'ghost-objects')


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
        hits = list(aob(pattern).finditer(memory))
        # Offline uniqueness oracle, not an alternative production scanner.
        assert len(hits) == 1, (pattern, len(hits))
        scans.append(pattern)
        return BASE + hits[0].start()

    def scan_unique(pattern):
        scans.append(pattern)
        hits = [BASE + hit.start() for hit in aob(pattern).finditer(memory)]
        return (hits + [None, None])[:2] + [None]

    framework_core(lua, {
        'AOBScan': scan,
        'scanForAOBInMainModule': lambda pattern: tuple(scan_unique(pattern)),
        'readInteger': lambda at: struct.unpack_from('<i', memory, at-BASE)[0],
        'readByte': lambda at: memory[at-BASE],
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
    expected = {name: address for name, address in EXPECTED[family]['addresses'].items()
                if name != 'ImageBase'}
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


@pytest.mark.parametrize('name,affected', (
    ('RenderMapEntry', {'tower-door-height', 'cliff-texture-direction'}),
    ('ProcessHeap', {'cliff-texture-direction'}),
    ('PlacementEntry', {'clear-unique-building-preview'}),
    ('MinimapNotify', {'clear-unique-building-preview'}),
    ('LobbyLoadItem', {'lobby-load'}),
    ('ImageHeaders', {'tower-door-height', 'cliff-texture-direction'}),
    ('CameraPreviewBranch', {'building-preview-during-camera-movement'}),
    ('TreeFrameLoad', {'distinct-dead-tree-sprites'}),
    *[(site, {'cliff-texture-direction'}) for site in ('CliffSelector', 'CliffSource', 'CliffOffsetSource')],
    *[(site, {'tower-door-height'}) for site in (
        'TowerDoorCall1', 'TowerDoorCall2', 'TowerDoorCall3', 'TowerDoorCall4', 'TowerDoorCall5',
        'FoundationDrawCall', 'BuildingRefresh', 'BuildingRefreshTile', 'MapReset', 'TowerFoundationSelect',
    )],
))
def test_missing_capability_disables_only_affected_features(name, affected):
    lua, layout, memory, chunks, _, allocations = fixture()
    memory[chunks[name]['address'] - BASE] = 0x90
    off = layout.prepare(lua.table_from(dict.fromkeys(OPTIONS, True)))
    assert set(off) == affected
    logs = [row[2] for row in lua.globals().test_logs.values() if row[1] == 2]
    assert {line.split(' is off:')[0] for line in logs} == affected
    assert len(logs) == len(affected) and allocations == []


@pytest.mark.parametrize('offset', (4, 8, 24, 32, 36, 44))
def test_changed_load_item_disables_only_lobby_load(offset):
    lua, layout, memory, chunks, _, allocations = fixture()
    memory[chunks['LobbyLoadItem']['address'] - BASE + offset] ^= 1
    off = layout.prepare(lua.table_from(dict.fromkeys(OPTIONS, True)))
    assert set(off) == {'lobby-load'} and allocations == []


@pytest.mark.parametrize('name,call_offset', (('TowerDoorCall1', 10),
                                            ('FoundationDrawCall', 0),
                                            ('PlacementNotifyCall', 6)))
def test_redirected_call_is_not_accepted_by_wildcarded_operand(name, call_offset):
    lua, layout, memory, chunks, _, allocations = fixture()
    operand = chunks[name]['address'] - BASE + call_offset + 1
    old = struct.unpack_from('<i', memory, operand)[0]
    struct.pack_into('<i', memory, operand, old + 9)
    off = layout.prepare(lua.table_from(dict.fromkeys(OPTIONS, True)))
    assert set(off) == ({'clear-unique-building-preview'} if name == 'PlacementNotifyCall'
                        else {'tower-door-height'})
    assert allocations == []


def test_disabled_feature_does_not_require_its_context():
    lua, layout, memory, chunks, _, _ = fixture()
    memory[chunks['CliffSource']['address'] - BASE] = 0x90
    off = layout.prepare(lua.table_from({'building-preview-during-camera-movement': True}))
    assert not list(off)


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
