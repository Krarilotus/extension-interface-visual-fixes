"""Run the actual Lua output on x86; no copyrighted game fixture is distributed."""
from pathlib import Path
import re
import struct

import pytest
from lupa import lua_type
from lua_support import LuaRuntime, with_symbols, flatten_code
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
SITE, DATA, CAVE, STACK, LOOKUP = 0x401000, 0x600000, 0x700000, 0x800000, 0x402000


def fixture():
    blob = bytearray(b'\x90' * 0x200)
    head = (b'\xe8' + struct.pack('<i', LOOKUP-SITE-5) + bytes.fromhex('8b c8 a1')
            + struct.pack('<I', DATA+16) + bytes.fromhex('83 c0 e0 c1 e0 05 99 83 e2 1f'))
    choice = (bytes.fromhex('83 3d') + struct.pack('<I', DATA)
              + bytes.fromhex('00 75 57 a1') + struct.pack('<I', DATA+16)
              + bytes.fromhex('8b 0d') + struct.pack('<I', DATA+20)
              + bytes.fromhex('2b 35') + struct.pack('<I', DATA+24)
              + bytes.fromhex('83 c0 e0 c1 e0 05'))
    blob[:len(head)] = head
    blob[0xeb:0xeb+len(choice)] = choice
    return bytes.fromhex('8d 44 24 14 50 68')+struct.pack('<I',DATA+100)+bytes(blob)


def emit(blob=None, base=SITE-10, cave=CAVE):
    blob = fixture() if blob is None else blob
    lua = LuaRuntime(unpack_returned_tuples=True)
    writes = []
    allocations = []
    def scan(pattern):
        regex = b''.join(b'.' if p == '?' else re.escape(bytes([int(p,16)]))
                         for p in pattern.split())
        found = list(re.finditer(regex, blob, re.DOTALL))
        if len(found) != 1:
            raise ValueError('AOB must match once: '+str([hex(base+m.start()) for m in found]))
        return base + found[0].start()
    def relative(op, target):
        return lambda address: bytes([op])+struct.pack('<i',target-address-5)
    def write(address, table):
        output = bytearray()
        def flatten(t):
            for v in t.values():
                if isinstance(v, int):
                    output.extend(bytes([v]) if 0 <= v <= 255 else struct.pack('<I',v))
                elif lua_type(v) == 'table':
                    flatten(v)
                else:
                    output.extend(v(address+len(output)))
        flatten(table)
        writes.append((address,bytes(output)))
    def allocate(size):
        allocations.append(size)
        return cave
    lua.globals().core = lua.table_from({
        'AOBScan':scan, 'readInteger':lambda a:struct.unpack_from('<i',blob,a-base)[0],
        'allocateCode':allocate, 'writeCode':write,
        'jmpTo':lambda a:relative(0xe9,a), 'callTo':lambda a:relative(0xe8,a),
    })
    lua.execute((ROOT/'lobby-description.lua').read_text()).enable()
    assert allocations == [15]
    return writes


@pytest.mark.parametrize('stale_source',[0,1,0x1234])
@pytest.mark.parametrize('builtin',[False,True])
@pytest.mark.parametrize('flags',[0x202,0x246,0xA93])
def test_selected_lookup_rebinds_source_and_preserves_abi(stale_source,builtin,flags):
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    for address,size in [(SITE,0x3000),(DATA,0x1000),(CAVE,0x1000),(STACK,0x2000)]:
        uc.mem_map(address,size)
    uc.mem_write(SITE,fixture()[10:])
    for address,code in emit():
        uc.mem_write(address,code)
    # Match the native lookup's two relevant behaviors: custom names leave the
    # source flag untouched; shipped names select the table. Return original arg.
    lookup = (b'\xc7\x05'+struct.pack('<I',DATA)+struct.pack('<I',1) if builtin else b'')
    uc.mem_write(LOOKUP,lookup+bytes.fromhex('8b 44 24 04 c3'))
    uc.mem_write(DATA,struct.pack('<4I',stale_source,0xABCDEF,0x123456,0xFEDCBA))
    uc.mem_write(STACK+0x1000,struct.pack('<2I',DATA+100,DATA+200))
    regs=[UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,
          UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EFLAGS]
    for i,r in enumerate(regs[:6]): uc.reg_write(r,0x123400+i)
    uc.reg_write(UC_X86_REG_ESP,STACK+0x1000)
    uc.reg_write(UC_X86_REG_EFLAGS,flags)
    before=[uc.reg_read(r) for r in regs]
    uc.emu_start(SITE,SITE+5,count=20)
    assert [uc.reg_read(r) for r in regs] == before
    assert uc.reg_read(UC_X86_REG_EAX) == DATA+100
    assert struct.unpack('<4I',uc.mem_read(DATA,16)) == (int(builtin),0xABCDEF,0x123456,0xFEDCBA)
    assert bytes(uc.mem_read(STACK+0x1000,8)) == struct.pack('<2I',DATA+100,DATA+200)


def test_unrecognized_or_moved_layout_rejected():
    with pytest.raises(ValueError,match='AOB must match once'):
        emit(b'\x90'*0x200)
    with pytest.raises(Exception,match='unsupported lobby description layout'):
        emit(fixture()[:0xf5]+b'\x90'+fixture()[0xf5:])


def test_disabled_and_repeated_enable():
    lua=LuaRuntime()
    lua.execute('calls=0; require=function() return {enable=function() calls=calls+1 end} end')
    init=lua.execute((ROOT/'init.lua').read_text())
    init.enable(init,lua.table_from({'lobby-map-descriptions':False}))
    assert lua.globals().calls == 0
    init=lua.execute((ROOT/'init.lua').read_text())
    init.enable(init,lua.table_from({'lobby-map-descriptions':True}))
    init.enable(init,lua.table_from({'lobby-map-descriptions':True}))
    assert lua.globals().calls == 1
