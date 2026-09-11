"""Execute emitted source resolution with synthetic, replaceable GM9 pixels."""
from pathlib import Path
import struct
from lua_support import LuaRuntime, with_symbols, flatten_code
import pytest
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_READ
from unicorn.x86_const import *
from test_tower_door_height import assemble

ROOT = Path(__file__).resolve().parents[1]
CAVE, STACK, STOP, RAW = 0x60000000, 0x61001000, 0x61001800, 0x30000000
PATTERNS = {
    0x453bdb: bytes.fromhex('A1 74 31 ED 00 8B 14 85 10 BA D0 00 01 55 F0 A1 6C 31 ED 00 8B 14 85 10 BA D0 00 01 55 F8'),
    0x45417b: bytes.fromhex('8B 15 74 31 ED 00 8B 04 95 10 BA D0 00 01 45 EC 8B 15 6C 31 ED 00 8B 04 95 10 BA D0 00 01 45 FC'),
    0x4e8cf0: bytes.fromhex('83 EC 64 A1 94 83 F9 00 53 55 56 8B D9 57 33 FF 33 F6'),
}


def emit(module='cliff-texture-source', moved=None, missing=None):
    from test_cliff_texture_direction import PATTERN, SITE
    patterns = {**PATTERNS, SITE:PATTERN}
    lua = LuaRuntime(); writes=[]; allocations=[]; modules={}; next_address=CAVE
    def scan(pattern):
        matches=[at for at,data in patterns.items() if data==bytes.fromhex(pattern) and at!=missing]
        if not matches: raise ValueError('Original signature absent')
        return matches[0]+int(matches[0]==moved)
    def allocate(size, zero=False):
        nonlocal next_address
        at=next_address;next_address+=size;allocations.append((at,size))
        if zero:writes.append((at,bytes(size)))
        return at
    def assembly(source, mapping=None):
        source=with_symbols(source,mapping)
        size=len(assemble(source,0));at=allocate(size)
        writes.append((at,assemble(source,at)));return at
    def write(at,table):
        data=bytearray()
        for item in table.values():
            if isinstance(item,int):data.append(item)
            else:data.extend(item(at+len(data)))
        writes.append((at,bytes(data)))
    def require(name):
        if name not in modules:modules[name]=lua.execute((ROOT/f'{name}.lua').read_text())
        return modules[name]
    lua.globals().require=require
    lua.globals().core=lua.table_from({
        'AOBScan':scan,'allocate':allocate,'allocateAssembly':assembly,'writeCode':write,
        'assemble':lambda source,_m,at:lua.table_from(list(assemble(with_symbols(source,_m),at))),
        'jmpTo':lambda target:lambda at:b'\xe9'+struct.pack('<i',target-at-5),
    })
    require(module).enable()
    return writes,allocations


def fixture(index=100):
    writes,allocations=emit()
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    for at,size in [(0x400000,0x2500000),(CAVE,0x200000),(0x61000000,0x2000),(RAW,0x60000)]:uc.mem_map(at,size)
    for at,data in writes:uc.mem_write(at,data)
    uc.mem_write(0x1fea108,struct.pack('<I',RAW))
    uc.mem_write(0xd7ceb4,struct.pack('<I',100))
    for i in range(100,134):
        uc.mem_write(0xd0ba10+4*i,struct.pack('<I',(i-100)*9600))
        uc.mem_write(0xc9a590+4*i,struct.pack('<I',9600))
        uc.mem_write(0xb98790+16*i,struct.pack('<HH',30,167))
        uc.mem_write(RAW+(i-100)*9600,struct.pack('<4800H',*(n^(i*31) for n in range(4800))))
    resolve=next(at for at,data in writes if data.startswith(bytes.fromhex('9c608b348510bad000')))
    return uc,resolve,allocations[0][0]


def resolve(uc,entry,index):
    registers={UC_X86_REG_EAX:index,UC_X86_REG_EBX:321,UC_X86_REG_ECX:432,
               UC_X86_REG_EDX:543,UC_X86_REG_ESI:654,UC_X86_REG_EDI:765,
               UC_X86_REG_EBP:876,UC_X86_REG_ESP:STACK,UC_X86_REG_EFLAGS:0x646}
    uc.mem_write(STACK,struct.pack('<I',STOP))
    for reg,value in registers.items():uc.reg_write(reg,value)
    uc.emu_start(entry,STOP,count=100000)
    assert uc.reg_read(UC_X86_REG_EIP)==STOP
    for reg,value in registers.items():
        if reg not in (UC_X86_REG_EAX,UC_X86_REG_ESP):assert uc.reg_read(reg)==value
    assert uc.reg_read(UC_X86_REG_ESP)==STACK+4
    return uc.reg_read(UC_X86_REG_EAX)


def test_face_uses_whole_strip_and_mirrors_the_corner_without_changing_source():
    uc,entry,epoch=fixture();uc.mem_write(epoch,struct.pack('<I',1))
    original=bytes(uc.mem_read(RAW,9600));pointer=resolve(uc,entry,100)
    pixels=struct.unpack('<4800H',uc.mem_read(pointer,9600))
    source=struct.unpack('<4800H',original)
    for y in (0,7,50,159):
        # Shared corner columns agree. Both extreme columns use the start of the
        # strip; both centre columns use its end, with native skew left intact.
        assert pixels[y*30]==pixels[y*30+29]==source[y*30]
        assert pixels[y*30+14]==pixels[y*30+15]==source[y*30+29]
    assert bytes(uc.mem_read(RAW,9600))==original


def test_repeated_draws_do_not_rescan_source_and_next_frame_detects_in_place_change():
    uc,entry,epoch=fixture();uc.mem_write(epoch,struct.pack('<I',1))
    pointer=resolve(uc,entry,100);before=bytes(uc.mem_read(pointer,9600))
    reads=[]
    hook=uc.hook_add(UC_HOOK_MEM_READ,lambda _u,_a,at,size,_v,_d:reads.append((at,size)) if RAW<=at<RAW+9600 else None)
    assert resolve(uc,entry,100)==pointer
    assert reads==[]
    uc.mem_write(RAW,struct.pack('<H',12345))
    uc.mem_write(epoch,struct.pack('<I',2))
    assert resolve(uc,entry,100)==pointer
    assert reads and bytes(uc.mem_read(pointer,2))==struct.pack('<H',12345)
    assert bytes(uc.mem_read(pointer,9600))!=before
    uc.hook_del(hook)


def test_individual_image_swap_reset_and_reused_address():
    uc,entry,epoch=fixture();uc.mem_write(epoch,struct.pack('<I',1))
    pointer=resolve(uc,entry,100);stock=bytes(uc.mem_read(pointer,9600))
    uc.mem_write(0xd0ba10+400,struct.pack('<I',9600))
    uc.mem_write(epoch,struct.pack('<I',2));resolve(uc,entry,100)
    assert bytes(uc.mem_read(pointer,9600))!=stock
    uc.mem_write(0xd0ba10+400,struct.pack('<I',0))
    uc.mem_write(epoch,struct.pack('<I',3));resolve(uc,entry,100)
    assert bytes(uc.mem_read(pointer,9600))==stock
    uc.mem_write(RAW,b'\x76\x98'*4800)
    uc.mem_write(epoch,struct.pack('<I',4));resolve(uc,entry,100)
    assert bytes(uc.mem_read(pointer,9600))==b'\x76\x98'*4800


@pytest.mark.parametrize('index',(132,133))
def test_waterfall_images_pass_through(index):
    uc,entry,_=fixture();assert resolve(uc,entry,index)==RAW+(index-100)*9600


@pytest.mark.parametrize('at,value',[(0xc9a590+400,9598),(0xb98790+1600,0x00a70020)])
def test_incompatible_dimensions_or_size_pass_through(at,value):
    uc,entry,_=fixture();uc.mem_write(at,struct.pack('<I',value))
    assert resolve(uc,entry,100)==RAW


@pytest.mark.parametrize('site',PATTERNS)
def test_guarded_source_and_shared_frame_sites(site):
    with pytest.raises(Exception,match='unsupported'):emit(moved=site)
    with pytest.raises(ValueError):emit(missing=site)
