"""Exercise the emitted rotated texture coordinates independently of pixels."""
from pathlib import Path
import itertools
import struct
from lua_support import LuaRuntime, with_symbols, flatten_code
import pytest
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from test_tower_door_height import assemble

ROOT=Path(__file__).resolve().parents[1]
SITE,END,MAP,STACK=0x4fc95c,0x4fc9b9,0x1a93208,0x60001000
PATTERN=bytes.fromhex('8B 91 9C 48 55 00 85 D2 75 1B 83 F8 01 75 3E 8B 54 24 18 83 E2 1F BE 20 00 00 00 2B F2 89 B1 08 49 55 00 EB 38 83 FA 04 75 10 83 F8 01 75 10 8B 54 24 18 83 E2 1F 03 D0 EB 1D 83 FA 02 75 0E 83 E6 1F 83 C6 01 89 B1 08 49 55 00 EB 10 83 E6 1F BA 20 00 00 00 2B D6 89 91 08 49 55 00')

def emit(moved=False,missing=False):
    from test_cliff_texture_source import emit as all_patches
    writes,_=all_patches('cliff-texture-direction',SITE if moved else None,SITE if missing else None)
    result=dict(writes)[SITE]
    assert len(result)==93
    return result


def execute(orientation,face,x,y,patched=True):
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    uc.mem_map(0x400000,0x2000000);uc.mem_map(0x60000000,0x2000)
    uc.mem_write(SITE,emit() if patched else PATTERN)
    uc.mem_write(MAP+0x55489c,struct.pack('<I',orientation))
    uc.mem_write(STACK+0x18,struct.pack('<I',x))
    registers={UC_X86_REG_EAX:face,UC_X86_REG_ECX:MAP,UC_X86_REG_ESI:y,
               UC_X86_REG_ESP:STACK,UC_X86_REG_EBX:123,UC_X86_REG_EBP:234,UC_X86_REG_EDI:345}
    for reg,value in registers.items():uc.reg_write(reg,value)
    # Valid rotations bypass the old 31 clamp; unsupported contexts retain it.
    finish=0x4fc9c0 if patched and orientation in (0,2,4,6) else END
    uc.emu_start(SITE,finish,count=80)
    assert uc.reg_read(UC_X86_REG_EIP)==finish
    assert {r:uc.reg_read(r) for r in registers if r!=UC_X86_REG_ESI}=={
        r:v for r,v in registers.items() if r!=UC_X86_REG_ESI}
    value=struct.unpack('<I',uc.mem_read(MAP+0x554908,4))[0]
    assert 1<=value<=32
    return value if finish==0x4fc9c0 or value<32 else 1


@pytest.mark.parametrize('orientation,face',list(itertools.product((0,2,4,6),range(6))))
def test_each_face_uses_the_same_rotated_corner_phase(orientation,face):
    a,b={0:(1,1),2:(-1,1),4:(-1,-1),6:(1,-1)}[orientation]
    for x,y in ((0,31),(1,32),(7,13),(31,0),(32,1),(398,399),(399,398)):
        assert execute(orientation,face,x,y)==((a*x+b*y)&31)+1


@pytest.mark.parametrize('orientation',(0,2,4,6))
def test_both_face_axes_advance_and_all_32_strips_are_used(orientation):
    assert len({execute(orientation,1,x,13) for x in range(32)})==32
    assert len({execute(orientation,2,7,y) for y in range(32)})==32


@pytest.mark.parametrize('orientation',(1,3,5,7,8,0xffffffff))
def test_unsupported_orientation_retains_original_fallback(orientation):
    for face in range(6):
        assert execute(orientation,face,7,13)==execute(orientation,face,7,13,False)


def test_signature_checked_before_any_write():
    with pytest.raises(Exception,match='unsupported cliff texture'):emit(moved=True)
    with pytest.raises(ValueError):emit(missing=True)


def test_disabled_option_does_not_load_feature():
    lua=LuaRuntime()
    lua.execute('calls=0; require=function() calls=calls+1; return {enable=function() end} end')
    module=lua.execute((ROOT/'init.lua').read_text())
    module.enable(module,lua.table_from({'cliff-texture-direction':False}))
    assert lua.globals().calls==0
