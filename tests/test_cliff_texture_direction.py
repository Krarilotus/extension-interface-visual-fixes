"""Exercise the in-place Lua/FASM selector; no render hook or game asset needed."""
from pathlib import Path
import itertools
import struct
from lupa import LuaRuntime
import pytest
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from test_tower_door_height import assemble

ROOT=Path(__file__).resolve().parents[1]
SITE,END,MAP,STACK=0x4fc95c,0x4fc9b9,0x1a93208,0x60001000
PATTERN=bytes.fromhex('8B 91 9C 48 55 00 85 D2 75 1B 83 F8 01 75 3E 8B 54 24 18 83 E2 1F BE 20 00 00 00 2B F2 89 B1 08 49 55 00 EB 38 83 FA 04 75 10 83 F8 01 75 10 8B 54 24 18 83 E2 1F 03 D0 EB 1D 83 FA 02 75 0E 83 E6 1F 83 C6 01 89 B1 08 49 55 00 EB 10 83 E6 1F BA 20 00 00 00 2B D6 89 91 08 49 55 00')

def emit(moved=False,missing=False):
    lua=LuaRuntime(); writes=[]
    def scan(pattern):
        assert bytes.fromhex(pattern)==PATTERN
        if missing:raise ValueError('Original signature absent')
        return SITE+int(moved)
    lua.globals().core=lua.table_from({'AOBScan':scan,
        'assemble':lambda script,_mapping,origin:lua.table_from(list(assemble(script,origin))),
        'writeCode':lambda at,code:writes.append((at,bytes(code.values())))})
    try:lua.execute((ROOT/'cliff-texture-direction.lua').read_text()).enable()
    except Exception:
        assert not writes
        raise
    assert len(writes)==1 and writes[0][0]==SITE and len(writes[0][1])==93
    return writes[0][1]

def execute(orientation,face,x,y,patched=True):
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    uc.mem_map(0x400000,0x2000000);uc.mem_map(0x60000000,0x2000)
    uc.mem_write(SITE,emit() if patched else PATTERN)
    uc.mem_write(MAP+0x55489c,struct.pack('<I',orientation))
    uc.mem_write(STACK+0x18,struct.pack('<I',x))
    registers={UC_X86_REG_EAX:face,UC_X86_REG_ECX:MAP,UC_X86_REG_ESI:y,
               UC_X86_REG_ESP:STACK,UC_X86_REG_EBX:123,UC_X86_REG_EBP:234,UC_X86_REG_EDI:345}
    for reg,value in registers.items():uc.reg_write(reg,value)
    writes=[]
    uc.hook_add(UC_HOOK_MEM_WRITE,lambda _uc,_a,at,size,value,_d:writes.append((at,size)))
    uc.emu_start(SITE,END,count=80)
    assert uc.reg_read(UC_X86_REG_EIP)==END
    assert writes==[(MAP+0x554908,4)]
    assert {r:uc.reg_read(r) for r in registers if r!=UC_X86_REG_ESI}=={
        r:v for r,v in registers.items() if r!=UC_X86_REG_ESI}
    # Existing, unchanged epilogue folds the special 32 value to frame 1.
    value=struct.unpack('<I',uc.mem_read(MAP+0x554908,4))[0]
    assert 1<=value<=32
    return value if value<32 else 1

@pytest.mark.parametrize('orientation,face',list(itertools.product((0,2,4,6),range(6))))
def test_texture_axis_and_direction_for_every_rotation_and_face(orientation,face):
    # Expected axes/directions from rotating the two native visible face axes.
    axis,direction={0:{True:('x',-1),False:('y',-1)},
                    2:{True:('y',1),False:('x',-1)},
                    4:{True:('x',1),False:('y',1)},
                    6:{True:('y',-1),False:('x',1)}}[orientation][face==1]
    for x,y in ((0,31),(1,32),(7,13),(31,0),(32,1),(398,399),(399,398)):
        coordinate=x if axis=='x' else y
        expected=(coordinate&31)+1 if direction==1 else 32-(coordinate&31)
        assert execute(orientation,face,x,y)==(expected if expected<32 else 1)

@pytest.mark.parametrize('orientation,face',list(itertools.product((0,4),range(6))))
def test_previously_correct_orientations_remain_identical(orientation,face):
    for x,y in ((1,19),(7,13),(31,32),(399,398)):
        assert execute(orientation,face,x,y)==execute(orientation,face,x,y,False)

@pytest.mark.parametrize('orientation',(2,6))
def test_rotated_x_running_face_advances_instead_of_repeating(orientation):
    assert len({execute(orientation,2,x,13,False) for x in range(1,16)})==1
    assert len({execute(orientation,2,x,13) for x in range(1,16)})==15
    assert execute(orientation,1,7,13)==execute(orientation,1,7,13,False)

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
