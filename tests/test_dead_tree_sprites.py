"""Run actual Lua-emitted code through the original input/scroll branch."""
from pathlib import Path
import itertools
import re
import struct
import pytest
from lupa import LuaRuntime
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
SITE, CAVE, STACK = 0x4eb831, 0x60000000, 0x60002000
RESUME = SITE + 6
PATTERN = bytes.fromhex('69 f6 9c 00 00 00 0f bf 86 58 cc f2 00 85 c0 8b 96 54 cc f2 00 8b 0c 85 90 ce d7 00')


def emit(blob=PATTERN, base=SITE-15):
    lua = LuaRuntime(unpack_returned_tuples=True)
    writes, allocations = [], []

    def scan(pattern):
        needle = bytes.fromhex(pattern)
        matches = list(re.finditer(re.escape(needle), blob))
        if len(matches) != 1:
            raise ValueError('Expected one original tree renderer')
        return base + matches[0].start()

    def write(address, values):
        code = bytearray()
        for v in values.values():
            if isinstance(v, int):
                code.append(v)
            else:
                code.extend(v(address + len(code)))
        writes.append((address, bytes(code)))

    def allocate(size):
        allocations.append(size)
        return CAVE

    lua.globals().core = lua.table_from({
        'AOBScan': scan, 'allocateCode': allocate, 'writeCode': write,
        'jmpTo': lambda target: lambda address: b'\xe9'+struct.pack('<i', target-address-5),
    })
    lua.execute((ROOT/'dead-tree-sprites.lua').read_text()).enable()
    assert allocations == [48]
    assert [len(code) for _, code in writes] == [48, 6]
    return writes


@pytest.mark.parametrize('kind,stage,frame', list(itertools.product(
    (0, 1, 2, 3, 4, 5, 15, 65535), (0, 3, 4, 5, 6), (1, 26, 51, 76, 146, 147, 148))))
def test_only_standing_dead_frame_changes_without_state_writes(kind, stage, frame):
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(0x4eb000, 0x1000)
    uc.mem_map(0xf2c000, 0x2000)
    uc.mem_map(CAVE, 0x4000)
    for address, code in emit():
        uc.mem_write(address, code)
    tree = bytearray(b'\xab' * 156)
    struct.pack_into('<i', tree, 0, frame)
    struct.pack_into('<H', tree, 0x46, kind)
    struct.pack_into('<i', tree, 0x80, stage)
    uc.mem_write(0xf2cc54+156, bytes(tree))
    regs = [UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDI,
            UC_X86_REG_EBP, UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EFLAGS]
    values = [0xdeadbeef, 0x123, 0x456, 0x789, 0xabc, 156, STACK, 0xa93]
    for reg, value in zip(regs, values):
        uc.reg_write(reg, value)
    uc.emu_start(SITE, RESUME, count=30)
    expected = 147 if 1 <= kind <= 4 and stage == 5 and frame == 146 else frame
    assert uc.reg_read(UC_X86_REG_EDX) == expected
    assert [uc.reg_read(reg) for reg in regs] == values
    assert bytes(uc.mem_read(0xf2cc54+156, 156)) == bytes(tree)


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


