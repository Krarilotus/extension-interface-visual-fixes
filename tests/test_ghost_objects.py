"""Ghost Objects: independence from other modules' entity update redirects, refusal
of an unexpected entity update, and the emitted tile-list rebuild on
the game's tick cycle.

The contexts are instruction fragments of the SHC/SHCE 1.41 reference executables
(tests/fixtures/native-contexts.json).
"""
import json
import struct
from pathlib import Path

import pytest
from lua_support import LuaRuntime, aob, framework_core
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
                               UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP,
                               UC_X86_REG_EFLAGS, UC_X86_REG_EIP)

ROOT = Path(__file__).resolve().parents[1]
CONTEXTS = json.loads((ROOT / 'tests/fixtures/native-contexts.json').read_text())
EXPECTED = json.loads((ROOT / 'tests/fixtures/component-bindings.json').read_text())
BASE, CAVE, STATE, STACK = 0x400000, 0x60000000, 0x03000000, 0x60100000
TILES, STRIDE = 80400, 0xE8


def discovery(family='regular', change=None):
    """Production discovery over the executable section from the contexts."""
    memory = bytearray(b'\xcc' * 0x200000)
    for fragment in CONTEXTS[family].values():
        at = fragment['address'] - BASE
        data = bytes.fromhex(fragment['bytes'])
        memory[at:at+len(data)] = data
    if change:
        change(memory, CONTEXTS[family])
    lua = LuaRuntime(component_bindings=False)
    allocations, writes = [], []

    def scan(pattern):
        match = aob(pattern).search(memory)
        assert match, pattern
        return BASE + match.start()

    framework_core(lua, {
        'AOBScan': scan,
        'readInteger': lambda at: struct.unpack_from('<i', memory, at-BASE)[0],
        'readByte': lambda at: memory[at-BASE],
        'allocateCode': lambda size: allocations.append(size) or CAVE,
        'writeCode': lambda at, code: writes.append(at),
    })
    return lua, allocations, writes


def enable(lua, config):
    module = lua.execute((ROOT / 'init.lua').read_text())
    module.enable(module, lua.table_from(config))


def occupy(offset, data):
    def change(memory, chunks):
        at = chunks['EntityUpdate']['address'] - BASE + offset
        memory[at:at+len(data)] = data
    return change


def ghost_logs(lua):
    return [row[2] for row in lua.globals().test_logs.values()]


OFF = 'ghost-objects is off: unexpected entity update loop'


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_redirected_prologue_is_left_alone_and_occupied_loop_start_turns_only_ghost_objects_off(family):
    # What Improved Siegeengines' oil options and Custom Projectiles leave behind at the
    # prologue (jmp rel32 / nop), or any other start: Ghost Objects patches only the
    # loop start after the matched body.
    site = EXPECTED[family]['addresses']['EntityLoopStart']
    for start in (b'\xe9\x10\x20\x30\x40\x90', b'\xcc' * 6):
        lua, allocations, writes = discovery(family, occupy(0, start))
        enable(lua, {'ghost-objects': True})
        assert writes == [CAVE, site] and len(allocations) == 1
        assert 'installed ghost-objects' in ghost_logs(lua)
    # A changed loop start: Ghost Objects stays off with an error and startup continues.
    lua, allocations, writes = discovery(family, occupy(45, b'\xe9\x01\x00\x00\x00'))
    enable(lua, {'ghost-objects': True, 'distinct-dead-tree-sprites': True})
    logs = ghost_logs(lua)
    assert site not in writes and len(allocations) == 1
    assert OFF in logs and 'installed ghost-objects' not in logs
    assert 'installed distinct-dead-tree-sprites' in logs and logs[-1].startswith('startup complete;')


def head_distance(memory, chunks):
    at = chunks['EntityTileWalker']['address'] - BASE + 0x78
    struct.pack_into('<I', memory, at, struct.unpack_from('<I', memory, at)[0] + 2)


def remove_entity_update(memory, chunks):
    fragment = chunks['EntityUpdate']
    at = fragment['address'] - BASE
    size = len(bytes.fromhex(fragment['bytes']))
    memory[at:at+size] = b'\xcc' * size


@pytest.mark.parametrize('family,change,message', (
    ('regular', remove_entity_update, 'EntityUpdate: not found'),
    ('extreme', remove_entity_update, 'EntityUpdate: not found'),
    ('regular', head_distance, 'unexpected entity tile heads'),
))
def test_missing_or_unexpected_layout_turns_only_ghost_objects_off_before_any_patch(family, change, message):
    lua, allocations, writes = discovery(family, change)
    enable(lua, {'ghost-objects': True})
    logs = ghost_logs(lua)
    assert allocations == [] and writes == []
    errors = [row[2] for row in lua.globals().test_logs.values() if row[1] == lua.globals().ERROR]
    assert errors == [f'ghost-objects is off: {message}']
    assert 'installed ghost-objects' not in logs and logs[-1].startswith('startup complete;')


# --- Emitted stub -----------------------------------------------------------------

def emit(family, config):
    extreme = family == 'extreme'
    lua = LuaRuntime(unpack_returned_tuples=True, extreme=extreme)
    A = EXPECTED[family]['addresses']
    update = CONTEXTS[family]['EntityUpdate']
    original = bytes.fromhex(update['bytes'])
    writes, allocations = [], []

    def scan(pattern):
        hits = list(aob(pattern).finditer(original))
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
    assert len(allocations) == 1 and [at for at, _ in writes] == [CAVE, A['EntityLoopStart']]
    assert len(writes[1][1]) == 5 and writes[1][1][:1] == b'\xe9'
    logs = [row[2] for row in lua.globals().test_logs.values()]
    return writes, original, logs


class World:
    """Synthetic entity state: records of 232 bytes, word heads, byte heads."""

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
    site = A['EntityLoopStart']
    update = CONTEXTS[family]['EntityUpdate']['address']
    uc.mem_map(update & ~0xFFF, 0x2000)
    uc.mem_write(update, original)
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
    registers = {UC_X86_REG_EAX: 0x11111111, UC_X86_REG_EBX: 0x22222222, UC_X86_REG_ECX: 0x33333333,
                 UC_X86_REG_EDX: 0x44444444, UC_X86_REG_ESI: STATE, UC_X86_REG_EDI: 0x66666666,
                 UC_X86_REG_EBP: 0x77777777, UC_X86_REG_ESP: STACK, UC_X86_REG_EFLAGS: flags}
    for reg, value in registers.items():
        uc.reg_write(reg, value)
    stray = []
    allowed = ((A['EntityWordHeads'], A['EntityWordHeads'] + 2 * TILES),
               (A['EntityByteHeads'], A['EntityByteHeads'] + TILES),
               (STATE, STATE + len(world.records)), (STACK - 0x100, STACK))
    uc.hook_add(UC_HOOK_MEM_WRITE, lambda _u, _a, at, size, _v, _d: stray.append(at) if not any(
        lo <= at and at + size <= hi for lo, hi in allowed) else None)
    uc.emu_start(site, A['EntityLoopResume'], count=5_000_000)
    assert uc.reg_read(UC_X86_REG_EIP) == A['EntityLoopResume']
    assert stray == []
    # The displaced `mov ebx, 1` ran; every other register and the flags are unchanged.
    after = {reg: uc.reg_read(reg) for reg in registers}
    assert after == {**registers, UC_X86_REG_EBX: 1}
    result = World.__new__(World)
    result.A, result.slots = A, world.slots
    result.records = bytearray(uc.mem_read(STATE, len(world.records)))
    result.words = list(struct.unpack(f'<{TILES}H', uc.mem_read(A['EntityWordHeads'], 2 * TILES)))
    result.bytes = list(uc.mem_read(A['EntityByteHeads'], TILES))
    return result, logs


def same(a, b):
    return a.records == b.records and a.words == b.words and a.bytes == b.bytes


def assert_rebuilt(result, world):
    # Each live entity is listed on its own tile, lowest id first; ids below 25
    # use the byte heads. Dead entities and those without a map tile are unlinked,
    # off-map tiles are set to 0, slot 0 is never touched and no other field changes.
    assert {tile: head for tile, head in enumerate(result.bytes) if head} == {100: 3, 500: 24}
    assert {tile: head for tile, head in enumerate(result.words) if head} == {
        100: 30, 200: 31, 500: 25, TILES - 1: world.slots - 1}
    expected = World.__new__(World)
    expected.records = bytearray(world.records)
    for slot in range(1, world.slots):
        expected.set(slot, next={3: 5, 30: 33}.get(slot, 0))
    expected.set(50, tile=0)
    assert result.records == expected.records


@pytest.mark.parametrize('family', ('regular', 'extreme'))
def test_due_tick_rebuilds_tangled_lists_from_each_entitys_tile(family):
    world = tangled(family)
    result, logs = run(family, world, 0, {'ghost-objects': True})
    assert_rebuilt(result, world)
    slots = 6000 if family == 'extreme' else 3000
    assert logs[-1] == ("ghost objects: tile object lists rebuilt every 10 ticks of the game's "
                        f"tick cycle ({slots} slots)")


@pytest.mark.parametrize('interval,tick,due', (
    (10, 0, True), (10, 9, False), (1, 137, True), (200, 100, False), (7, 196, True), (7, 199, False),
))
def test_schedule_follows_the_saved_tick_cycle(interval, tick, due):
    world = tangled('regular')
    result, _ = run('regular', world, tick, {'ghost-objects': True, 'ghost-objects-interval': interval})
    if due:
        assert_rebuilt(result, world)
    else:
        assert same(result, world)


def test_caller_direction_flag_is_cleared_for_the_fill_and_restored():
    # With DF=1 a fill without `cld` would run backwards below the head arrays
    # (caught as stray writes) and leave the lists wrong.
    world = tangled('regular')
    result, _ = run('regular', world, 0, {'ghost-objects': True}, flags=0x0A93 | 0x400)
    assert_rebuilt(result, world)


@pytest.mark.parametrize('value,effective,problem', (
    (None, 10, None), (1, 1, None), (200, 200, None),
    (0, 10, 'whole number'), (500, 10, 'whole number'), (2.5, 10, 'whole number'),
    ('ten', 10, 'be a number'),
))
def test_invalid_interval_uses_default(value, effective, problem):
    config = {'ghost-objects': True}
    if value is not None:
        config['ghost-objects-interval'] = value
    _, _, logs = emit('regular', config)
    assert logs[-1].startswith(f'ghost objects: tile object lists rebuilt every {effective} ticks ')
    if problem:
        assert sum(problem in line for line in logs) == 1
