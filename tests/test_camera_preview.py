"""Run actual Lua-emitted code through the original input/scroll branch."""
from pathlib import Path
import itertools
import re
import struct
import pytest
from lua_support import LuaRuntime, with_symbols, flatten_code
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
SITE, CAVE, STACK = 0x445263, 0x60000000, 0x60002000
RESUME, FINISH = SITE + 6, 0x4467c2
PATTERN = bytes.fromhex('39 1d 70 b0 12 01 0f 85 59 15 00 00 8b 3d e0 eb 1a 02')


EXTREME_PATTERN=bytes.fromhex("39 1d f0 b4 12 01 0f 85 59 15 00 00 8b 3d e0 20 c4 02")

def emit(blob=None, base=None, extreme=False):
    if blob is None:blob=EXTREME_PATTERN if extreme else PATTERN
    if base is None:base=(0x445493 if extreme else SITE)-6
    lua = LuaRuntime(unpack_returned_tuples=True,extreme=extreme)
    writes, allocations = [], []

    def scan(pattern):
        needle = bytes.fromhex(pattern)
        matches = list(re.finditer(re.escape(needle), blob))
        if len(matches) != 1:
            raise ValueError('Expected one original scrolling guard')
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
    lua.execute((ROOT/'camera-preview.lua').read_text()).enable()
    assert allocations == [39]
    assert [len(code) for _, code in writes] == [39, 6]
    return writes


@pytest.mark.parametrize('extreme',[False,True])
@pytest.mark.parametrize('scrolling,start,held,released,size', list(itertools.product(
    (0, 1), (0, 1), (0, 1), (0, 1), (-1, 0, 1, 3, 13))))
def test_existing_input_gate_and_abi(scrolling, start, held, released, size, extreme):
    site,finish=(0x445493,0x4469f2) if extreme else (SITE,FINISH)
    resume=site+6
    delta=0x480 if extreme else 0
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(0x400000, 0x3000000)
    uc.mem_map(CAVE, 0x4000)
    # Original left-start comparison, pushes and jump around the scroll guard.
    uc.mem_write(site-16, b'\x39\x1d'+struct.pack('<I',0xf2c9e4+delta)+bytes.fromhex('55 57 75 0c')+(EXTREME_PATTERN if extreme else PATTERN))
    for a, code in emit(extreme=extreme):
        uc.mem_write(a, code)
    for a, value in {0x112b070+delta:scrolling, 0xf2c9e4+delta:start, 0xf2c9f0+delta:held,
                     0xf2c9d8+delta:released, (0x2a7aff0 if extreme else 0x1fe7af0):size}.items():
        uc.mem_write(a, struct.pack('<i', value))
    regs = [UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
            UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP]
    values = [0x123, 0, 0x456, 0x789, 0xabc, 0xdef, 0x135]
    for r, v in zip(regs, values):
        uc.reg_write(r, v)
    uc.reg_write(UC_X86_REG_ESP, STACK)
    observed = {}

    def stop(uc, a, n, user):
        if a == site:
            observed['flags'] = uc.reg_read(UC_X86_REG_EFLAGS)
        if a in (resume, finish):
            uc.emu_stop()

    uc.hook_add(UC_HOOK_CODE, stop)
    uc.emu_start(site-16, 0, count=50)
    allowed = start or not scrolling or (size > 0 and not held and not released)
    assert uc.reg_read(UC_X86_REG_EIP) == (resume if allowed else finish)
    assert [uc.reg_read(r) for r in regs] == values
    assert uc.reg_read(UC_X86_REG_ESP) == STACK-8
    assert struct.unpack('<II', uc.mem_read(STACK-8, 8)) == (values[5], values[6])
    if not start:
        assert uc.reg_read(UC_X86_REG_EFLAGS) == observed['flags']


def test_unknown_moved_or_already_changed_guard_rejected():
    with pytest.raises(ValueError):
        emit(bytes(40))
    with pytest.raises(ValueError):
        emit(PATTERN+PATTERN)
    with pytest.raises(Exception, match='unsupported camera preview layout'):
        emit(base=SITE-5)


def test_disabled_and_repeated_enable():
    lua = LuaRuntime()
    lua.execute('calls=0; require=function() return {enable=function() calls=calls+1 end} end')
    module = lua.execute((ROOT/'init.lua').read_text())
    module.enable(module, lua.table_from({'building-preview-during-camera-movement':False}))
    assert lua.globals().calls == 0
    module = lua.execute((ROOT/'init.lua').read_text())
    config = lua.table_from({'building-preview-during-camera-movement':True})
    module.enable(module, config)
    module.enable(module, config)
    assert lua.globals().calls == 1
