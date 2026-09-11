"""Execute the actual R130 Lua-emitted x86 with the native acknowledgement ABI."""
from pathlib import Path
import re, struct
import pytest
from lupa import lua_type
from lua_support import LuaRuntime, with_symbols, flatten_code
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
SITE, ENTRY, ORIGINAL, CAVE, STACK, TILE = 0x516a0f,0x5162d0,0x4b5300,0x60000000,0x60100000,0x1a93208

def fixture(extreme=False):
    notify,entry_at,original=(0x516d8f,0x516650,0x4b5470) if extreme else (SITE,ENTRY,ORIGINAL)
    b=bytearray(b'\x90'*0x120000)
    entry=bytes.fromhex('83 ec 08 53 55 8b 6c 24 18 56 8b f1 8b 4c 24 24')
    b[entry_at-0x400000:entry_at-0x400000+len(entry)]=entry
    site=bytes.fromhex('53 b9 10 16 a3 01 e8')+struct.pack('<i',original-notify-5)+bytes.fromhex('8b 44 24 2c 83 f8 05 7f 07')
    b[notify-6-0x400000:notify-6-0x400000+len(site)]=site
    return bytes(b)

def emit(blob=None, base=0x400000, cave=CAVE, extreme=False):
    blob = fixture(extreme) if blob is None else blob
    lua = LuaRuntime(unpack_returned_tuples=True,extreme=extreme)
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
    lua.execute((ROOT/'unique-placement.lua').read_text()).enable()
    assert allocations == [87]
    return writes

def execute(mapper=77, selected=None, actor=1, local=1, mode=3, caller=None, flags=0xA93, extreme=False):
    site,original,tile,game_mode,local_player=(0x516d8f,0x4b5470,0x2526708,0x2a7b278,0x24baadc) if extreme else (SITE,ORIGINAL,TILE,0x1fe7d78,0x1a275dc)
    if caller is None:caller=0x48210c if extreme else 0x481f3c
    selected=mapper if selected is None else selected
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    uc.mem_map(0x400000,0x3000000)
    uc.mem_map(CAVE,0x1000);uc.mem_map(STACK,0x3000)
    uc.mem_write(0x400000,fixture(extreme))
    for a,b in emit(extreme=extreme):uc.mem_write(a,b)
    # Execute to the original notification entry, observing its exact input ABI.
    sp=STACK+0x1000
    frame=bytearray(b'\xab'*0x80)
    struct.pack_into('<I',frame,0,1) # native minimap argument before CALL
    struct.pack_into('<I',frame,0x14,mapper & 0xffffffff) # original local +0x10
    struct.pack_into('<I',frame,0x1c,caller)
    struct.pack_into('<I',frame,0x20,actor)
    uc.mem_write(sp,bytes(frame))
    uc.mem_write(tile+0x5548e4,struct.pack('<I',selected))
    uc.mem_write(local_player,struct.pack('<I',local))
    uc.mem_write(game_mode,struct.pack('<I',mode))
    regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_EFLAGS]
    values=[0xdeadbeef,1,0x1a31610,0xfedcba,tile,0x245,0x123,flags]
    for r,v in zip(regs,values):uc.reg_write(r,v)
    uc.reg_write(UC_X86_REG_ESP,sp)
    uc.emu_start(site,original,count=100)
    assert uc.reg_read(UC_X86_REG_EIP)==original
    assert [uc.reg_read(r) for r in regs]==values
    assert uc.reg_read(UC_X86_REG_ESP)==sp-4
    assert struct.unpack('<I',uc.mem_read(sp-4,4))[0]==site+5
    assert bytes(uc.mem_read(sp,len(frame)))==bytes(frame)
    # Original RET4 consumes exactly the original argument and return address.
    uc.mem_write(original,bytes.fromhex('c2 04 00'))
    uc.emu_start(original,site+5,count=2)
    assert uc.reg_read(UC_X86_REG_ESP)==sp+4
    return struct.unpack('<I',uc.mem_read(tile+0x5548e4,4))[0]

@pytest.mark.parametrize('extreme',[False,True])
@pytest.mark.parametrize('mapper',[77,86,87,88,89])
@pytest.mark.parametrize('flags',[0x202,0x246,0xA93])
def test_local_committed_unique_clears_matching_tool(mapper,flags,extreme):
    assert execute(mapper=mapper,flags=flags,extreme=extreme)==0

@pytest.mark.parametrize('extreme',[False,True])
@pytest.mark.parametrize('mapper',[0,51,60,61,62,80,81,85,90,0xffffffff])
def test_ordinary_expandable_keep_and_unrecognized_tools_unchanged(mapper,extreme):
    assert execute(mapper=mapper,extreme=extreme)==mapper

@pytest.mark.parametrize('extreme',[False,True])
@pytest.mark.parametrize('kwargs',[
    {'actor':2},{'local':2},{'selected':0},{'selected':51},{'mode':1},{'mode':6},
    {'caller':0x4ed601},{'caller':0x441d64},{'caller':0x481f3d}])
def test_remote_cancel_changed_tool_editor_and_noncommand_callers_unchanged(kwargs,extreme):
    assert execute(**kwargs,extreme=extreme)==kwargs.get('selected',77)

def test_unsupported_layout_fails_before_write():
    with pytest.raises(Exception):emit(bytes(0x120000))
    b=bytearray(fixture());b[SITE+1-0x400000]^=1
    with pytest.raises(Exception,match='notification was changed'):emit(bytes(b))

def test_disabled_and_repeated_enable():
    lua=LuaRuntime();lua.execute('calls=0; require=function() return {enable=function() calls=calls+1 end} end')
    m=lua.execute((ROOT/'init.lua').read_text());m.enable(m,lua.table_from({'clear-unique-building-preview':False}))
    assert lua.globals().calls==0
    m=lua.execute((ROOT/'init.lua').read_text());cfg=lua.table_from({'clear-unique-building-preview':True})
    m.enable(m,cfg);m.enable(m,cfg);assert lua.globals().calls==1
