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


def execute(orientation,face,x,y,patched=True,configure=None):
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    uc.mem_map(0x400000,0x2000000);uc.mem_map(0x60000000,0x2000)
    if patched:
        from test_cliff_texture_source import emit as all_patches
        for at,data in all_patches('cliff-texture-direction')[0]:uc.mem_write(at,data)
    else:uc.mem_write(SITE,PATTERN)
    uc.mem_write(MAP+0x55489c,struct.pack('<I',orientation))
    uc.mem_write(STACK+0x18,struct.pack('<I',x))
    if configure:configure(uc)
    registers={UC_X86_REG_EAX:face,UC_X86_REG_ECX:MAP,UC_X86_REG_ESI:y,
               UC_X86_REG_ESP:STACK,UC_X86_REG_EBX:123,UC_X86_REG_EBP:234,UC_X86_REG_EDI:345}
    for reg,value in registers.items():uc.reg_write(reg,value)
    writes=[]
    uc.hook_add(UC_HOOK_MEM_WRITE,lambda _u,_a,at,size,_v,_d:writes.append((at,size)))
    # Valid rotations bypass the old 31 clamp; unsupported contexts retain it.
    finish=0x4fc9c0 if patched and orientation in (0,2,4,6) else END
    uc.emu_start(SITE,finish,count=500)
    assert uc.reg_read(UC_X86_REG_EIP)==finish
    assert all(STACK-512<=at and at+size<=STACK+32 or
               MAP+0x554908<=at and at+size<=MAP+0x55490c for at,size in writes)
    assert {r:uc.reg_read(r) for r in registers if r!=UC_X86_REG_ESI}=={
        r:v for r,v in registers.items() if r!=UC_X86_REG_ESI}
    value=struct.unpack('<I',uc.mem_read(MAP+0x554908,4))[0]
    assert 1<=value<=32
    return value if finish==0x4fc9c0 or value<32 else 1


@pytest.mark.parametrize('orientation,face',list(itertools.product((0,2,4,6),range(6))))
def test_base_phase_follows_rotated_horizontal_projection(orientation,face):
    a,b={0:(1,-1),2:(-1,-1),4:(-1,1),6:(1,1)}[orientation]
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


DIRECTIONS=((0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1))
PHASE={0:(1,-1),2:(-1,-1),4:(-1,1),6:(1,1)}

def terrain_fixture(orientation,face,shape='depth',wall=False):
    """Independent diamond-grid geometry and native eight-neighbour offsets."""
    rows=[]
    total=0
    for y in range(400):
        width=2*min(y+1,400-y);first=max(199-y,y-200)
        rows.append((total-first,first,total+width));total+=width
    assert total==80400
    a,b=PHASE[orientation]
    outward=(orientation+(4 if face==1 else 2))%8
    dx,dy=DIRECTIONS[outward]
    def configure(uc):
        uc.mem_write(STACK+0x14,struct.pack('<I',104))
        uc.mem_write(MAP+0x5548a4,struct.pack('<3I',(orientation+3)%8,(orientation+2)%8,(orientation+4)%8))
        for y,(base,first,end) in enumerate(rows):
            uc.mem_write(0x2337300+y*12,struct.pack('<iii',base,first,end))
            offsets=[rows[y+oy][0]-base+ox if 0<=y+oy<400 else 100000 for ox,oy in DIRECTIONS]
            uc.mem_write(MAP+y*32,struct.pack('<8i',*offsets))
        for y in range(65,136):
            for x in range(165,236):
                distance=(a*dx+b*dy)*(a*(x-200)+b*(y-100)) if shape=='depth' else dx*(x-200)+dy*(y-100)
                height=104 if distance<=0 else 8
                tile=rows[y][0]+x
                uc.mem_write(0x1d32c38+tile,bytes([200 if wall else height]))
                uc.mem_write(0x1d46648+tile,bytes([height]))
                if wall:uc.mem_write(0x1bf8368+tile*4,struct.pack('<I',0x100))
    return configure


@pytest.mark.parametrize('orientation,face',list(itertools.product((0,2,4,6),(1,2))))
def test_straight_faces_keep_consecutive_strips_with_real_neighbour_geometry(orientation,face):
    a,b=PHASE[orientation];dx,dy=DIRECTIONS[(orientation+(4 if face==1 else 2))%8]
    configure=terrain_fixture(orientation,face,'straight')
    points=[(200+dy*n,100-dx*n) for n in range(8)]
    assert [execute(orientation,face,x,y,configure=configure) for x,y in points]==[((a*x+b*y)&31)+1 for x,y in points]


@pytest.mark.parametrize('orientation,face,wall',list(itertools.product((0,2,4,6),(1,2),(False,True))))
def test_depth_staircases_vary_stably_without_using_wall_top_height(orientation,face,wall):
    dx,dy=DIRECTIONS[(orientation+3)%8]
    configure=terrain_fixture(orientation,face,wall=wall)
    points=[(200+dx*n,100+dy*n) for n in range(12)]
    values=[execute(orientation,face,x,y,configure=configure) for x,y in points]
    assert len(set(values))>=6
    assert values==[execute(orientation,face,x,y,configure=configure) for x,y in points]


@pytest.mark.parametrize('orientation',(0,2,4,6))
def test_front_diagonal_enumerates_both_faces_and_wraps_without_skipping(orientation):
    a,b=PHASE[orientation]
    sequence=[]
    for n in range(20):
        first=execute(orientation,5,200+a*n,100+b*n)-1
        sequence.extend((first,(first+1)&31))
    assert all(second==(first+1)&31 for first,second in zip(sequence,sequence[1:]))
