"""Ghost Objects: discovery from both executables' contexts, refusal of a changed
entity update, and the emitted tile-list rebuild on the game's tick cycle.

The contexts are instruction fragments of the SHC/SHCE 1.41 reference executables
(tests/fixtures/native-contexts.json). Complete-executable uniqueness is a separate
private acceptance check; see docs/native-integration-audit.md.
"""
import json
import re
import struct
from pathlib import Path

import pytest
from lua_support import LuaRuntime, framework_core
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
                               UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP,
                               UC_X86_REG_EFLAGS, UC_X86_REG_EIP)

ROOT = Path(__file__).resolve().parents[1]
CONTEXTS = json.loads((ROOT / 'tests/fixtures/native-contexts.json').read_text())
EXPECTED = json.loads((ROOT / 'tests/fixtures/component-bindings.json').read_text())
BASE, CAVE, STATE, STACK = 0x400000, 0x60000000, 0x03000000, 0x60100000
TILES, STRIDE, BYTE_IDS = 80400, 0xE8, 0x19
GHOST = ('EntityUpdateBody', 'EntityUpdate', 'EntityUpdateResume', 'EntityTick', 'EntityTileWalker',
         'EntityByteHeads', 'EntityWordHeads', 'SeagullRemoval', 'EntitySlots', 'ImageBase')
PROLOGUE = bytes.fromhex('51 53 55 56 8B F1')
SIEGE_OPTIONS = r'improved-siegeengines\.oil\.aim and improved-siegeengines\.oil\.spread'


def regex(pattern):
    return re.compile(b''.join(b'.' if t == '?' else re.escape(bytes([int(t, 16)])) for t in pattern.split()),
                      re.S)


def discovery(family='regular', change=None):
    """Production discovery over the contexts, with UCP's first-match scanner semantics."""
    memory = bytearray(b'\xcc' * 0x200000)
    for fragment in CONTEXTS[family].values():
        at = fragment['address'] - BASE
        data = bytes.fromhex(fragment['bytes'])
        memory[at:at+len(data)] = data
    if change:
        change(memory, CONTEXTS[family])
    lua = LuaRuntime(component_bindings=False)
    allocations, writes, scans = [], [], []

    def first(pattern, start=BASE, stop=BASE + len(memory)):
        match = regex(pattern).search(memory, max(start - BASE, 0), stop - BASE)
        return BASE + match.start() if match else None

    def scan(pattern):
        scans.append(pattern)
        return first(pattern)

    framework_core(lua, {
        'AOBScan': scan,
        'scanForAOB': lambda pattern, start, stop: first(pattern, start, stop) or 0,
        'readInteger': lambda at: struct.unpack_from('<i', memory, at-BASE)[0],
        'readByte': lambda at: memory[at-BASE],
        'allocateCode': lambda size: allocations.append(size) or CAVE,
        'writeCode': lambda at, code: writes.append(at),
    })
    return lua, memory, allocations, writes, scans


def enable(lua, config):
    module = lua.execute((ROOT / 'init.lua').read_text())
    module.enable(module, lua.table_from(config))


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_bindings_match_both_reference_executables(family):
    lua, _, allocations, writes, _ = discovery(family)
    layout = lua.eval('require("native-layout")')
    layout = layout[0] if isinstance(layout, tuple) else layout
    layout.prepare(lua.table_from({'ghost-objects': True}))
    expected = EXPECTED[family]['addresses']
    assert {name: layout.addresses[name] for name in GHOST} == {name: expected[name] for name in GHOST}
    assert expected['EntitySlots'] == (6000 if family == 'extreme' else 3000)
    assert expected['EntityByteHeads'] - expected['EntityWordHeads'] == TILES * 2
    assert allocations == [] and writes == []


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_feature_installs_one_jump_into_its_stub(family):
    lua, memory, allocations, writes, _ = discovery(family)
    enable(lua, {'ghost-objects': True})
    site = EXPECTED[family]['addresses']['EntityUpdate']
    assert writes == [CAVE, site] and len(allocations) == 1
    logs = [row[2] for row in lua.globals().test_logs.values()]
    assert 'installed ghost-objects' in logs


def occupy_prologue(memory, chunks):
    # What Improved Siegeengines' oil options leave behind: jmp rel32 / nop.
    at = chunks['EntityUpdate']['address'] - BASE
    memory[at:at+6] = b'\xe9\x10\x20\x30\x40\x90'


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_changed_entity_update_is_refused_before_any_patch(family):
    lua, _, allocations, writes, _ = discovery(family, occupy_prologue)
    config = {'ghost-objects': True, 'distinct-dead-tree-sprites': True}
    with pytest.raises(Exception, match=SIEGE_OPTIONS):
        enable(lua, config)
    assert allocations == [] and writes == []


def copy_update(address):
    def change(memory, chunks):
        data = bytes.fromhex(chunks['EntityUpdate']['bytes'])
        memory[address-BASE:address-BASE+len(data)] = data
    return change


# Inside the reference executables' code section (.text ends at 0x59D806 / 0x59DC36).
duplicate_update = copy_update(0x590000)


def missing_header(memory, chunks):
    memory[0] = ord('X')  # no image header


def short_code_section(memory, chunks):
    # .text (first section) no longer reaches the entity update.
    pe = struct.unpack_from('<I', memory, 0x3C)[0]
    struct.pack_into('<I', memory, pe + 0x18 + 0xE0 + 8, 0x100)


def foreign_header(memory, chunks):
    pe = struct.unpack_from('<I', memory, 0x3C)[0]
    struct.pack_into('<I', memory, pe + 0x34, 0x10000000)  # describes another image


def word_heads_opcode(memory, chunks):
    memory[chunks['EntityTileWalker']['address'] - BASE + 0x74] = 0x8B


def head_distance(memory, chunks):
    at = chunks['EntityTileWalker']['address'] - BASE + 0x78
    struct.pack_into('<I', memory, at, struct.unpack_from('<I', memory, at)[0] + 2)


def slot_count(value):
    def change(memory, chunks):
        struct.pack_into('<I', memory, chunks['SeagullRemoval']['address'] - BASE + 0x42, value)
    return change


def slot_opcode(memory, chunks):
    memory[chunks['SeagullRemoval']['address'] - BASE + 0x40] = 0x83


@pytest.mark.parametrize('change,message', (
    (duplicate_update, 'ambiguous native capability entity update'),
    (missing_header, 'unsupported or occupied native capability ImageHeader'),
    (short_code_section, 'unsupported or occupied native capability entity update section'),
    (foreign_header, 'unsupported or occupied native capability entity update section'),
    (word_heads_opcode, 'inconsistent or occupied native capability entity word heads'),
    (head_distance, 'inconsistent or occupied native capability entity tile heads'),
    (slot_count(50), 'inconsistent or occupied native capability entity slot count'),
    (slot_count(30000), 'inconsistent or occupied native capability entity slot count'),
    (slot_opcode, 'inconsistent or occupied native capability entity slot count'),
))
def test_unexpected_layout_is_refused_before_any_patch(change, message):
    lua, _, allocations, writes, _ = discovery('regular', change)
    with pytest.raises(Exception, match=message):
        enable(lua, {'ghost-objects': True})
    assert allocations == [] and writes == []


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_copy_outside_the_code_section_is_not_ambiguous(family):
    # A copy of the code bytes in data or heap memory is not a second entity update.
    lua, _, allocations, writes, _ = discovery(family, copy_update(0x5F0000))
    enable(lua, {'ghost-objects': True})
    assert writes == [CAVE, EXPECTED[family]['addresses']['EntityUpdate']] and len(allocations) == 1


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_code_section_end_comes_from_the_image_headers(family):
    lua, _, _, _, _ = discovery(family)
    layout = lua.eval('require("native-layout")')
    layout = layout[0] if isinstance(layout, tuple) else layout
    body = EXPECTED[family]['addresses']['EntityUpdateBody']
    assert layout.codeSectionEnd(body) == (0x59DC36 if family == 'extreme' else 0x59D806)
    # An address in the image headers is in no section.
    assert layout.codeSectionEnd(BASE + 0x10) is None


@pytest.mark.parametrize('name', ('EntityUpdate', 'EntityTileWalker', 'SeagullRemoval'))
def test_missing_context_is_unsupported(name):
    def remove(memory, chunks):
        memory[chunks[name]['address'] - BASE + 7] ^= 0xFF
    lua, _, allocations, writes, _ = discovery('regular', remove)
    with pytest.raises(Exception, match='unsupported or occupied native capability ' + name):
        enable(lua, {'ghost-objects': True})
    assert allocations == [] and writes == []


def test_switched_off_feature_needs_none_of_its_contexts():
    def remove_all(memory, chunks):
        for name in ('EntityUpdate', 'EntityTileWalker', 'SeagullRemoval'):
            memory[chunks[name]['address'] - BASE + 7] ^= 0xFF
    lua, _, _, _, scans = discovery('regular', remove_all)
    enable(lua, {'ghost-objects': False, 'ghost-objects-interval': 10, 'distinct-dead-tree-sprites': True})
    layout = lua.eval('require("native-layout")')
    layout = layout[0] if isinstance(layout, tuple) else layout
    assert not {layout.patterns[name] for name in ('EntityUpdate', 'EntityTileWalker', 'SeagullRemoval')} & set(scans)


# --- Emitted stub -----------------------------------------------------------------

def emit(family, config):
    extreme = family == 'extreme'
    lua = LuaRuntime(unpack_returned_tuples=True, extreme=extreme)
    A = EXPECTED[family]['addresses']
    update = CONTEXTS[family]['EntityUpdate']
    original = bytes.fromhex(update['bytes'])
    writes, allocations = [], []

    def scan(pattern):
        hits = list(regex(pattern).finditer(original))
        assert len(hits) == 1, pattern
        return update['address'] + hits[0].start()

    def allocate(size):
        allocations.append(size)
        return CAVE

    framework_core(lua, {
        'AOBScan': scan, 'allocateCode': allocate, 'writeCode': lambda at, code: writes.append((at, code)),
        'readByte': lambda at: original[at - update['address']],
    })
    lua.execute((ROOT / 'ghost-objects.lua').read_text()).enable(lua.table_from(config))
    assert len(allocations) == 1 and [at for at, _ in writes] == [CAVE, A['EntityUpdate']]
    assert len(writes[1][1]) == 6 and writes[1][1][:1] == b'\xe9' and writes[1][1][5:] == b'\x90'
    logs = [row[2] for row in lua.globals().test_logs.values()]
    return writes, original, logs


class World:
    """Synthetic entity state: records of 232 bytes, word heads, byte heads, tick."""

    def __init__(self, family):
        self.A = EXPECTED[family]['addresses']
        self.slots = self.A['EntitySlots']
        self.records = bytearray(b'\x5a' * (self.slots * STRIDE))
        for slot in range(self.slots):
            self.set(slot, live=0, tile=0, next=0)
        self.words = [0] * TILES
        self.bytes = [0] * TILES

    def set(self, slot, live=None, tile=None, next=None):
        base = slot * STRIDE
        if live is not None:
            struct.pack_into('<H', self.records, base + 0x3C, live)
        if tile is not None:
            struct.pack_into('<i', self.records, base + 0x60, tile)
        if next is not None:
            struct.pack_into('<H', self.records, base + 0x32, next)

    def get(self, slot):
        base = slot * STRIDE
        return (struct.unpack_from('<H', self.records, base + 0x3C)[0],
                struct.unpack_from('<i', self.records, base + 0x60)[0],
                struct.unpack_from('<H', self.records, base + 0x32)[0])

    def rebuilt(self):
        """Independent reference: lists from each live entity's own tile, ascending ids."""
        expected = World.__new__(World)
        expected.A, expected.slots = self.A, self.slots
        expected.records = bytearray(self.records)
        expected.words, expected.bytes = [0] * TILES, [0] * TILES
        for slot in range(self.slots - 1, 0, -1):
            live, tile, _ = self.get(slot)
            if live == 0 or tile <= 0:
                expected.set(slot, next=0)
            elif tile >= TILES:
                expected.set(slot, tile=0, next=0)
            elif slot < BYTE_IDS:
                expected.set(slot, next=expected.bytes[tile])
                expected.bytes[tile] = slot
            else:
                expected.set(slot, next=expected.words[tile])
                expected.words[tile] = slot
        return expected


def tangled(family):
    world = World(family)
    world.set(3, live=1, tile=100, next=3)        # byte id, self loop
    world.set(5, live=2, tile=100, next=0)
    world.set(7, live=0, tile=100, next=5)        # freed, still linked
    world.set(30, live=1, tile=100, next=31)      # joins two tiles' lists
    world.set(31, live=1, tile=200, next=31)
    world.set(33, live=6, tile=100, next=0)
    world.set(24, live=1, tile=500, next=0)       # last byte-head id
    world.set(25, live=1, tile=500, next=24)      # first word-head id
    world.set(40, live=0, tile=200, next=30)
    world.set(50, live=1, tile=TILES, next=33)    # off the map: quarantined
    world.set(51, live=1, tile=-4, next=33)
    world.set(60, live=1, tile=0, next=5)
    world.set(world.slots - 1, live=1, tile=TILES - 1, next=0)
    world.set(0, live=1, tile=300, next=33)       # slot 0 is never touched
    world.words[100] = 40
    world.words[300] = 7
    world.bytes[100] = 7
    world.bytes[200] = 3
    return world


def run(family, world, tick, config, flags=0x0A93 & ~0x400):
    A = world.A
    writes, original, logs = emit(family, config)
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    site = A['EntityUpdate']
    uc.mem_map(site & ~0xFFF, 0x2000)
    uc.mem_write(site, original)
    uc.mem_map(CAVE, 0x1000)
    uc.mem_map(STACK - 0x1000, 0x2000)
    heads = A['EntityWordHeads'] & ~0xFFF
    uc.mem_map(heads, (A['EntityByteHeads'] + TILES - heads + 0xFFF) & ~0xFFF)
    tick_page = A['EntityTick'] & ~0xFFF
    uc.mem_map(tick_page, 0x1000)
    uc.mem_map(STATE, (len(world.records) + 0xFFF) & ~0xFFF)
    for at, code in writes:
        uc.mem_write(at, code)
    uc.mem_write(A['EntityWordHeads'], struct.pack(f'<{TILES}H', *world.words))
    uc.mem_write(A['EntityByteHeads'], bytes(world.bytes))
    uc.mem_write(A['EntityTick'], struct.pack('<i', tick))
    uc.mem_write(STATE, bytes(world.records))
    registers = {UC_X86_REG_EAX: 0x11111111, UC_X86_REG_EBX: 0x22222222, UC_X86_REG_ECX: STATE,
                 UC_X86_REG_EDX: 0x44444444, UC_X86_REG_ESI: 0x55555555, UC_X86_REG_EDI: 0x66666666,
                 UC_X86_REG_EBP: 0x77777777, UC_X86_REG_ESP: STACK, UC_X86_REG_EFLAGS: flags}
    for reg, value in registers.items():
        uc.reg_write(reg, value)
    stray = []
    allowed = ((A['EntityWordHeads'], A['EntityWordHeads'] + 2 * TILES),
               (A['EntityByteHeads'], A['EntityByteHeads'] + TILES),
               (STATE, STATE + len(world.records)), (STACK - 0x100, STACK))
    uc.hook_add(UC_HOOK_MEM_WRITE, lambda _u, _a, at, size, _v, _d: stray.append(at) if not any(
        lo <= at and at + size <= hi for lo, hi in allowed) else None)
    uc.emu_start(site, A['EntityUpdateResume'], count=5_000_000)
    assert uc.reg_read(UC_X86_REG_EIP) == A['EntityUpdateResume']
    assert stray == []
    # The displaced prologue ran exactly once: push ecx/ebx/ebp/esi, mov esi, ecx.
    assert uc.reg_read(UC_X86_REG_ESP) == STACK - 16
    assert struct.unpack('<4I', uc.mem_read(STACK - 16, 16)) == (
        0x55555555, 0x77777777, 0x22222222, STATE)
    after = {reg: uc.reg_read(reg) for reg in registers}
    assert after[UC_X86_REG_ESI] == STATE
    assert {r: v for r, v in after.items() if r not in (UC_X86_REG_ESI, UC_X86_REG_ESP)} == {
        r: v for r, v in registers.items() if r not in (UC_X86_REG_ESI, UC_X86_REG_ESP)}
    result = World.__new__(World)
    result.A, result.slots = A, world.slots
    result.records = bytearray(uc.mem_read(STATE, len(world.records)))
    result.words = list(struct.unpack(f'<{TILES}H', uc.mem_read(A['EntityWordHeads'], 2 * TILES)))
    result.bytes = list(uc.mem_read(A['EntityByteHeads'], TILES))
    return result, logs


def same(a, b):
    return a.records == b.records and a.words == b.words and a.bytes == b.bytes


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_due_tick_rebuilds_tangled_lists_from_each_entitys_tile(family):
    world = tangled(family)
    result, logs = run(family, world, 0, {'ghost-objects': True})
    expected = world.rebuilt()
    assert same(result, expected)
    # Spot checks of the reference: ascending chains, quarantine, untouched slot 0.
    assert result.bytes[100] == 3 and result.get(3)[2] == 5 and result.get(5)[2] == 0
    assert result.words[100] == 30 and result.get(30)[2] == 33 and result.get(33)[2] == 0
    assert result.words[200] == 31 and result.get(31)[2] == 0
    assert result.words[300] == 0 and result.get(7)[2] == 0 and result.get(40)[2] == 0
    assert result.bytes[500] == 24 and result.words[500] == 25 and result.get(25)[2] == 0
    assert result.get(50) == (1, 0, 0) and result.get(51) == (1, -4, 0)
    assert result.get(0) == world.get(0)
    assert result.words[TILES - 1] == world.slots - 1
    slots = 6000 if family == 'extreme' else 3000
    assert logs[-1] == ("ghost objects: tile object lists rebuilt every 10 ticks of the game's "
                        f"tick cycle ({slots} slots)")


@pytest.mark.parametrize('interval,tick,due', (
    (10, 0, True), (10, 10, True), (10, 190, True), (10, 1, False), (10, 9, False), (10, 199, False),
    (1, 0, True), (1, 137, True), (200, 0, True), (200, 100, False), (200, 199, False),
    (7, 0, True), (7, 196, True), (7, 199, False),
))
def test_schedule_follows_the_saved_tick_cycle(interval, tick, due):
    world = tangled('regular')
    result, _ = run('regular', world, tick, {'ghost-objects': True, 'ghost-objects-interval': interval})
    assert same(result, world.rebuilt() if due else world)


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_caller_direction_flag_is_cleared_for_the_fill_and_restored(family):
    # With DF=1 a fill without `cld` would run backwards below the head arrays
    # (caught as stray writes) and leave the lists wrong.
    world = tangled(family)
    result, _ = run(family, world, 0, {'ghost-objects': True}, flags=0x0A93 | 0x400)
    assert same(result, world.rebuilt())


def test_rebuild_is_idempotent():
    world = tangled('regular')
    once, _ = run('regular', world, 20, {'ghost-objects': True})
    twice, _ = run('regular', once, 20, {'ghost-objects': True})
    assert same(once, twice)


@pytest.mark.parametrize('value,effective', (
    (None, 10), (10, 10), (0, 1), (-5, 1), (500, 200), (12.7, 12), ('abc', 10),
))
def test_interval_setting_is_clamped_to_one_tick_cycle(value, effective):
    config = {'ghost-objects': True}
    if value is not None:
        config['ghost-objects-interval'] = value
    _, _, logs = emit('regular', config)
    assert logs[-1].startswith(f'ghost objects: tile object lists rebuilt every {effective} ticks ')
