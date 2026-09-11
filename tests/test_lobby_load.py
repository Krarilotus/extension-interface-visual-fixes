"""Verify actual Lua output, SP-only branches and ABI without game assets."""
from pathlib import Path
import re
import struct
import pytest
from lupa import lua_type
from lua_support import LuaRuntime, with_symbols, flatten_code
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
DRAW,ACTION,MODE,CAVE,STACK=0x42afb2,0x4426e0,0x191dd80,0x60000000,0x61000000
PREP,ITEM,SECONDARY=0x42733a,0x5e9988,0x1fe7d78

def fixture():
    b=bytearray(b'\x90'*(ITEM+80-PREP))
    head=bytes.fromhex('83 3d 80 dd 91 01 63 0f 84 89 02 00 00 39 2d f8 de 91 01 0f 84 6a 03 00 00')
    b[DRAW-PREP:DRAW-PREP+len(head)]=head
    tail=bytes.fromhex('e8 10 c2 03 00 83 f8 02 7c ae be 01 00 00 00 6a 09 b9 a8 65 12 01 89 35 44 66 12 01 e8')
    b[ACTION-5-PREP:ACTION-5-PREP+len(tail)]=tail
    prepare=bytes.fromhex('c7 05 78 7d fe 01 03 00 00 00 89 35 ac 9c fe 01 89 35 b4 7d fe 01')
    b[:len(prepare)]=prepare
    for offset,value in {0:0x02000003,4:444,8:540,24:1,32:0x400001ab,36:3,44:0x149}.items():
        struct.pack_into('<I',b,ITEM+offset-PREP,value)
    return bytes(b)

def emit(blob=None,base=PREP,cave=CAVE,repeat=False):
    blob=fixture() if blob is None else blob
    lua=LuaRuntime(unpack_returned_tuples=True)
    writes=[]
    allocations=[]
    def scan(pattern):
        regex=b''.join(b'.' if p=='?' else re.escape(bytes([int(p,16)])) for p in pattern.split())
        found=list(re.finditer(regex,blob,re.DOTALL))
        if len(found)!=1: raise ValueError('signature not unique')
        return base+found[0].start()
    def write(addr,table):
        out=bytearray()
        def compile_values(values):
            for v in values.values():
                if isinstance(v,int):
                    # UCP core.compile recursively flattens tables. A nested
                    # small integer still emits ONE byte, not a forced dword.
                    if 0<=v<=255: out.append(v)
                    else: out.extend(struct.pack('<I',v&0xffffffff))
                elif lua_type(v)=='table': compile_values(v)
                else: out.extend(v(addr+len(out)))
        compile_values(table)
        writes.append((addr,bytes(out)))
    def allocate(size): allocations.append(size); return cave
    lua.globals().core=lua.table_from({'AOBScan':scan,'readInteger':lambda a:struct.unpack_from('<i',blob,a-base)[0],
        'allocateCode':allocate,'writeCode':write,
        'jmpTo':lambda target:lambda at:b'\xe9'+struct.pack('<i',target-at-5)})
    module=lua.execute((ROOT/'lobby-load.lua').read_text())
    module.enable()
    if repeat: module.enable()
    assert allocations==[73]
    assert len(writes)==5 and len(writes[0][1])==27 and len(writes[1][1])==46
    return writes

@pytest.mark.parametrize('mode',[0,1,2,99,666])
@pytest.mark.parametrize('teams',[-1,0,1,2,8])
def test_action_preserves_other_modes_and_registers(mode,teams):
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    for a,n in [(0x440000,0x4000),(MODE&~4095,4096),(CAVE,4096),(STACK,4096)]: uc.mem_map(a,n)
    for a,b in emit():
        if a not in (ACTION,CAVE): continue
        uc.mem_write(a,b)
    uc.mem_write(MODE,struct.pack('<I',mode))
    regs=[UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP]
    for i,r in enumerate(regs): uc.reg_write(r,STACK+100 if r==UC_X86_REG_ESP else 0x123400+i)
    uc.reg_write(UC_X86_REG_EAX,teams&0xffffffff)
    before=[uc.reg_read(r) for r in regs]
    end=ACTION+5 if mode==99 or teams>=2 else 0x442693
    uc.emu_start(ACTION,end,count=10)
    assert uc.reg_read(UC_X86_REG_EIP)==end
    assert [uc.reg_read(r) for r in regs]==before
    assert uc.reg_read(UC_X86_REG_EAX)==teams&0xffffffff

@pytest.mark.parametrize('mode',[0,1,2,99,666])
def test_draw_only_redirects_singleplayer(mode):
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    uc.mem_map(0x42a000,0x2000);uc.mem_map(MODE&~4095,4096)
    uc.mem_write(DRAW,fixture()[DRAW-PREP:DRAW-PREP+25]);uc.mem_write(MODE,struct.pack('<I',mode))
    uc.mem_write(DRAW+7,dict(emit())[DRAW+7])
    end=0x42affd if mode==99 else DRAW+13
    uc.emu_start(DRAW,end,count=3)
    assert uc.reg_read(UC_X86_REG_EIP)==end

def test_fail_closed_and_idempotent():
    emit(repeat=True)
    with pytest.raises(ValueError): emit(b'\x90'*100)
    with pytest.raises(ValueError): emit(fixture()+fixture())
    with pytest.raises(Exception,match='unsupported SHC'): emit(fixture(),base=PREP+1)
    bad=bytearray(fixture());bad[DRAW-PREP+2]^=1
    with pytest.raises(Exception,match='unsupported SHC'): emit(bytes(bad))

@pytest.mark.parametrize('offset',[0,4,8,24,32,36,44])
def test_rejects_changed_load_item(offset):
    bad=bytearray(fixture());bad[ITEM+offset-PREP]^=1
    with pytest.raises(Exception,match='unsupported SHC'): emit(bytes(bad))

@pytest.mark.parametrize('modes',[(99,1),(1,99),(99,2,99),(99,0),(99,666),(99,99)])
def test_position_follows_lobby_mode_and_preserves_abi(modes):
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    for a in [PREP,ITEM,MODE,SECONDARY,CAVE,STACK]: uc.mem_map(a&~4095,4096)
    for a,b in emit():
        if a in (PREP,CAVE+27): uc.mem_write(a,b)
    uc.mem_write(ITEM,fixture()[ITEM-PREP:ITEM-PREP+80])
    regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,
          UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EFLAGS]
    for mode in modes:
        uc.mem_write(MODE,struct.pack('<I',mode))
        for i,r in enumerate(regs): uc.reg_write(r,STACK+100 if r==UC_X86_REG_ESP else 0x246 if r==UC_X86_REG_EFLAGS else 0x123400+i)
        before=[uc.reg_read(r) for r in regs]
        item_before=bytes(uc.mem_read(ITEM,80))
        uc.emu_start(PREP,PREP+10,count=20)
        assert uc.reg_read(UC_X86_REG_EIP)==PREP+10
        assert [uc.reg_read(r) for r in regs]==before
        assert struct.unpack('<I',uc.mem_read(ITEM+4,4))[0]==(560 if mode==99 else 444)
        assert bytes(uc.mem_read(ITEM,4))==item_before[:4]
        assert bytes(uc.mem_read(ITEM+8,72))==item_before[8:]
        assert struct.unpack('<I',uc.mem_read(SECONDARY,4))[0]==3

def test_load_fits_between_master_and_start_at_minimum_canvas():
    # Original GM frames: Load normal/hover 45x58; master 120x101 at409,452;
    # Start's full native hit rectangle starts at620,484 (opaque hand is later).
    left,top,width,height=560,540,45,58
    assert 409+120 < left and left+width < 620
    assert 0<=top and top+height<=600 and left+width<=800

def test_option_off_and_composition():
    for load,description in [(False,False),(True,False),(False,True),(True,True)]:
        lua=LuaRuntime()
        lua.execute('calls={}; require=function(name) return {enable=function() calls[name]=(calls[name] or 0)+1 end} end')
        module=lua.execute((ROOT/'init.lua').read_text())
        cfg=lua.table_from({'lobby-load':load,'lobby-map-descriptions':description})
        module.enable(module,cfg);module.enable(module,cfg)
        assert (lua.globals().calls['lobby-load'] or 0)==int(load)
        assert (lua.globals().calls['lobby-description'] or 0)==int(description)
