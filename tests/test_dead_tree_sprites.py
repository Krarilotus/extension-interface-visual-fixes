"""Execute the Lua-emitted tree frame load, preserving native harvest state."""
from pathlib import Path
import itertools
import re
import struct
import pytest
from lua_support import LuaRuntime, with_symbols, flatten_code
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
SITE, CAVE, STACK = 0x4eb831, 0x60000000, 0x60002000
RESUME = SITE + 6
PATTERN = bytes.fromhex('69 f6 9c 00 00 00 0f bf 86 58 cc f2 00 85 c0 8b 96 54 cc f2 00 8b 0c 85 90 ce d7 00')


EXTREME_PATTERN=bytes.fromhex("69 f6 9c 00 00 00 0f bf 86 d8 d0 f2 00 85 c0 8b 96 d4 d0 f2 00 8b 0c 85 30 d0 d7 00")

def emit(blob=None, base=None, extreme=False):
    if blob is None:blob=EXTREME_PATTERN if extreme else PATTERN
    if base is None:base=(0x4ebbc1 if extreme else SITE)-15
    lua = LuaRuntime(unpack_returned_tuples=True,extreme=extreme)
    writes, allocations = [], []

    def scan(pattern):
        needle = bytes.fromhex(pattern)
        matches = list(re.finditer(re.escape(needle), blob))
        if len(matches) != 1:
            raise ValueError('Expected one original tree renderer')
        return base + matches[0].start()

    def write(address, values):
        writes.append((address, flatten_code(values,address)))

    def allocate(size):
        allocations.append(size)
        return CAVE

    lua.globals().core = lua.table_from({
        'AOBScan': scan, 'allocateCode': allocate, 'writeCode': write,
        'jmpTo': lambda target: lambda address: b'\xe9'+struct.pack('<i', target-address-5),
    })
    lua.execute((ROOT/'dead-tree-sprites.lua').read_text()).enable()
    assert allocations == [58]
    assert [len(code) for _, code in writes] == [58, 6]
    return writes


@pytest.mark.parametrize('extreme',[False,True])
@pytest.mark.parametrize('kind,stage,frame', list(itertools.product(
    (0, 1, 2, 3, 4, 5, 15, 65535), (0, 3, 4, 5, 6), (1, 26, 51, 76, 146, 147, 148))))
def test_only_standing_dead_frame_changes_without_state_writes(kind, stage, frame, extreme, harvest_state=0):
    site=0x4ebbc1 if extreme else SITE
    tree_frame=0xf2d0d4 if extreme else 0xf2cc54
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(0x4eb000, 0x1000)
    uc.mem_map(0xf2c000, 0x2000)
    uc.mem_map(CAVE, 0x4000)
    for address, code in emit(extreme=extreme):
        uc.mem_write(address, code)
    tree = bytearray(b'\xab' * 156)
    struct.pack_into('<i', tree, 0, frame)
    struct.pack_into('<H', tree, 0x46, kind)
    struct.pack_into('<H', tree, 0x76, harvest_state)
    struct.pack_into('<i', tree, 0x80, stage)
    uc.mem_write(tree_frame+156, bytes(tree))
    regs = [UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDI,
            UC_X86_REG_EBP, UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EFLAGS]
    values = [0xdeadbeef, 0x123, 0x456, 0x789, 0xabc, 156, STACK, 0xa93]
    for reg, value in zip(regs, values):
        uc.reg_write(reg, value)
    uc.emu_start(site, site+6, count=30)
    expected = 147 if 1 <= kind <= 4 and stage == 5 and frame == 146 and harvest_state == 0 else frame
    assert uc.reg_read(UC_X86_REG_EDX) == expected
    assert [uc.reg_read(reg) for reg in regs] == values
    assert bytes(uc.mem_read(tree_frame+156, 156)) == bytes(tree)


@pytest.mark.parametrize('kind,harvest_state', list(itertools.product(range(1, 5), (1, 2))))
def test_felled_stage_five_tree_keeps_original_log(kind, harvest_state):
    # Original damageTreeAndTriggerDeathIfDepleted writes 1; harvest writes 2.
    # Neither advances stage 5, and original UpdateTree1 keeps frame 146.
    test_only_standing_dead_frame_changes_without_state_writes(kind, 5, 146, False, harvest_state)


def test_unknown_moved_or_already_changed_renderer_rejected():
    with pytest.raises(ValueError):
        emit(bytes(40))
    with pytest.raises(ValueError):
        emit(PATTERN+PATTERN)
    with pytest.raises(Exception, match='unsupported tree renderer layout'):
        emit(base=SITE-14)


def test_disabled_and_repeated_enable():
    lua = LuaRuntime()
    lua.execute('calls=0; require=function() return {enable=function() calls=calls+1 end} end')
    module = lua.execute((ROOT/'init.lua').read_text())
    module.enable(module, lua.table_from({'distinct-dead-tree-sprites':False}))
    assert lua.globals().calls == 0
    module = lua.execute((ROOT/'init.lua').read_text())
    config = lua.table_from({'distinct-dead-tree-sprites':True})
    module.enable(module, config)
    module.enable(module, config)
    assert lua.globals().calls == 1


