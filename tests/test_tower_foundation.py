"""Execute the emitted foundation branch with its native caller frame."""
import itertools
import struct
import pytest
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from test_tower_door_height import emit,STACK,BUILDING

MAP,TILE,SITE,CONTINUE,FALLBACK=0x1a93208,3210,0x50edaf,0x50ee19,0x50edb5

def execute(kind=75,orientation=0,face=1,x=13,y=21):
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    uc.mem_map(0x400000,0x2000000);uc.mem_map(0x60000000,0x50000)
    for at,data in emit():uc.mem_write(at,data)
    frame=STACK+0x400
    for offset,value in ((-0x30,1),(-0xe4,MAP),(-0x1c,face),(-0x3c,x)):
        uc.mem_write(frame+offset,struct.pack('<I',value))
    uc.mem_write(BUILDING+0xd2,struct.pack('<H',kind))
    uc.mem_write(MAP+0x55489c,struct.pack('<I',orientation))
    uc.mem_write(MAP+0x554a38,struct.pack('<I',y))
    uc.mem_write(MAP+0x554a3c,struct.pack('<I',TILE))
    uc.mem_write(0xd7ceb8,struct.pack('<I',6000))
    pillar,misc=MAP+0xc80e0+TILE*2,MAP+0x301c80+TILE*2
    uc.mem_write(pillar,struct.pack('<H',5810))
    uc.mem_write(misc,struct.pack('<H',0x2863))
    registers={UC_X86_REG_ESP:STACK,UC_X86_REG_EBP:frame,UC_X86_REG_EAX:91,
               UC_X86_REG_EBX:92,UC_X86_REG_ECX:93,UC_X86_REG_EDX:94,
               UC_X86_REG_ESI:95,UC_X86_REG_EDI:96,UC_X86_REG_EFLAGS:0x247}
    for reg,value in registers.items():uc.reg_write(reg,value)
    expected=CONTINUE if 75<=kind<=78 and orientation in (0,2,4,6) else FALLBACK
    writes=[]
    uc.hook_add(UC_HOOK_MEM_WRITE,lambda _u,_a,at,size,_v,_d:writes.append((at,size)))
    uc.emu_start(SITE,expected,count=150)
    assert uc.reg_read(UC_X86_REG_EIP)==expected
    if expected==FALLBACK:registers[UC_X86_REG_EDX]=MAP
    assert {reg:uc.reg_read(reg) for reg in registers}==registers
    outside_stack=[(at,size) for at,size in writes if not STACK-40<=at<STACK]
    assert outside_stack==([(pillar,2),(misc,2)] if expected==CONTINUE else [])
    return struct.unpack('<H',uc.mem_read(pillar,2))[0]-5999,struct.unpack('<H',uc.mem_read(misc,2))[0]

@pytest.mark.parametrize('kind,orientation,face',list(itertools.product(range(75,79),(0,2,4,6),(1,2))))
def test_native_wall_column_sequence_and_refresh_abi(kind,orientation,face):
    # Native wall selector's straight X/Y strip formulas, without its wall-only
    # connectivity scan. The caller has already classified the exposed face.
    axis_x=(face==1)==(orientation in (0,4))
    for x,y in ((0,15),(15,0),(13,21),(31,32),(398,399)):
        c=(x if axis_x else y)&15
        if axis_x:
            expected={0:17-c,2:1 if c==0 else c+17,4:c+2,6:1 if c==15 else 32-c}[orientation]
        else:
            expected={0:1 if c==15 else 32-c,2:17-c,4:1 if c==0 else c+17,6:c+2}[orientation]
        assert execute(kind,orientation,face,x,y)==(expected,0x2063)

@pytest.mark.parametrize('kind',[0,10,54,74,79,80,84,65535])
def test_other_buildings_keep_original_cliff_branch(kind):
    assert execute(kind=kind)==(-189,0x2863)

@pytest.mark.parametrize('orientation',[1,3,5,7,8,0xffffffff])
def test_unsupported_orientation_keeps_original_branch(orientation):
    assert execute(orientation=orientation)==(-189,0x2863)

@pytest.mark.parametrize('orientation,face',list(itertools.product((0,2,4,6),(0,3,4,5))))
def test_other_cliff_classifications_stay_in_native_masonry_range(orientation,face):
    index,misc=execute(orientation=orientation,face=face)
    assert 1<=index<=32 and misc==0x2063
