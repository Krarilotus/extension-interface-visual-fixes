"""Execute emitted source resolution with synthetic, replaceable GM9 pixels."""
from pathlib import Path
import struct
from lua_support import LuaRuntime, with_symbols, flatten_code
import pytest
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_READ, UC_HOOK_CODE
from unicorn.x86_const import *
from test_tower_door_height import assemble

ROOT = Path(__file__).resolve().parents[1]
CAVE, STACK, STOP, RAW = 0x60000000, 0x61001000, 0x61001800, 0x30000000
PATTERNS = {
    0x453bdb: bytes.fromhex('A1 74 31 ED 00 8B 14 85 10 BA D0 00 01 55 F0 A1 6C 31 ED 00 8B 14 85 10 BA D0 00 01 55 F8'),
    0x45417b: bytes.fromhex('8B 15 74 31 ED 00 8B 04 95 10 BA D0 00 01 45 EC 8B 15 6C 31 ED 00 8B 04 95 10 BA D0 00 01 45 FC'),
    0x4e8cf0: bytes.fromhex('83 EC 64 A1 94 83 F9 00 53 55 56 8B D9 57 33 FF 33 F6'),
}


def emit(module='cliff-texture-source', moved=None, missing=None, extreme=False):
    from test_cliff_texture_direction import PATTERN, SITE
    patterns = {**PATTERNS, SITE:PATTERN}
    if extreme:
        patterns={
            0x453e0b:bytes.fromhex('A1 F4 35 ED 00 8B 14 85 B0 BB D0 00 01 55 F0 A1 EC 35 ED 00 8B 14 85 B0 BB D0 00 01 55 F8'),
            0x4543ab:bytes.fromhex('8B 15 F4 35 ED 00 8B 04 95 B0 BB D0 00 01 45 EC 8B 15 EC 35 ED 00 8B 04 95 B0 BB D0 00 01 45 FC'),
            0x4e9080:bytes.fromhex('83 EC 64 A1 14 88 F9 00 53 55 56 8B D9 57 33 FF 33 F6'),
        }
    lua = LuaRuntime(extreme=extreme); writes=[]; allocations=[]; modules={}; next_address=CAVE
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


def fixture(index=100,extreme=False):
    writes,allocations=emit(extreme=extreme)
    uc=Uc(UC_ARCH_X86,UC_MODE_32)
    for at,size in [(0x32000000,0x800000),(0x400000,0x2c00000),(CAVE,0x200000),(0x61000000,0x2000),(RAW,0x60000)]:uc.mem_map(at,size)
    translations={0x1fea108:0x2a7d608,0xd7ceb4:0xd7d054,
                  0x59e108:0x59e10c,0x59e170:0x59e174,0x59e0cc:0x59e0d0}
    def address(at):
        if not extreme:return at
        for start,end,delta in [(0xd0ba10,0xd0ba10+4*1000,0x1a0),
                                (0xc9a590,0xc9a590+4*1000,0x1a0),
                                (0xb98790,0xb98790+16*1000,0x1a0)]:
            if start<=at<end:return at+delta
        return translations.get(at,at)
    uc.iv_address=address
    def write(at,data):uc.mem_write(address(at),data)
    heap = {'next':0x32000000, 'calls':[], 'fail':False}
    def api(u, address, _size, _data):
        esp=u.reg_read(UC_X86_REG_ESP)
        if address==STOP+0x100: result=1
        else:
            size=struct.unpack('<I',u.mem_read(esp+(16 if address==STOP+0x120 else 12),4))[0]
            heap['calls'].append((address,size))
            result=0 if heap['fail'] else heap['next']
            if result:heap['next']+=(size+4095)&~4095
        u.reg_write(UC_X86_REG_EAX,result)
        u.reg_write(UC_X86_REG_ECX,0xbad)
        u.reg_write(UC_X86_REG_EDX,0xbad)
    for iat,entry,args in [(0x59e108,STOP+0x100,0),(0x59e170,STOP+0x110,12),(0x59e0cc,STOP+0x120,16)]:
        write(iat,struct.pack('<I',entry))
        write(entry,b'\xc2'+struct.pack('<H',args))
        uc.hook_add(UC_HOOK_CODE,api,begin=entry,end=entry)
    uc.iv_heap=heap
    for at,data in writes:write(at,data)
    write(0x1fea108,struct.pack('<I',RAW))
    write(0xd7ceb4,struct.pack('<I',100))
    for i in range(100,134):
        write(0xd0ba10+4*i,struct.pack('<I',(i-100)*9600))
        write(0xc9a590+4*i,struct.pack('<I',9600))
        write(0xb98790+16*i,struct.pack('<HH',30,167))
        write(RAW+(i-100)*9600,struct.pack('<4800H',*(n^(i*31) for n in range(4800))))
    resolve=next(at for at,data in writes if data.startswith(bytes.fromhex('9c608b3485b0bbd000' if extreme else '9c608b348510bad000')))
    return uc,resolve,allocations[0][0]


def resolve(uc,entry,index):
    registers={UC_X86_REG_EAX:index,UC_X86_REG_EBX:321,UC_X86_REG_ECX:432,
               UC_X86_REG_EDX:543,UC_X86_REG_ESI:654,UC_X86_REG_EDI:765,
               UC_X86_REG_EBP:876,UC_X86_REG_ESP:STACK,UC_X86_REG_EFLAGS:0x646}
    uc.mem_write(STACK,struct.pack('<I',STOP))
    for reg,value in registers.items():uc.reg_write(reg,value)
    uc.emu_start(entry,STOP,count=3000000)
    assert uc.reg_read(UC_X86_REG_EIP)==STOP
    for reg,value in registers.items():
        if reg not in (UC_X86_REG_EAX,UC_X86_REG_ESP):assert uc.reg_read(reg)==value
    assert uc.reg_read(UC_X86_REG_ESP)==STACK+4
    return uc.reg_read(UC_X86_REG_EAX)


def test_faces_use_successive_whole_strips_without_changing_sources():
    uc,entry,epoch=fixture();uc.mem_write(epoch,struct.pack('<I',1))
    original=bytes(uc.mem_read(RAW,9600));pointer=resolve(uc,entry,100)
    pixels=struct.unpack('<4800H',uc.mem_read(pointer,9600))
    source=struct.unpack('<4800H',original)
    neighbour=struct.unpack('<4800H',uc.mem_read(RAW+9600,9600))
    for y in (0,7,50,159):
        assert pixels[y*30]==source[y*30]
        assert pixels[y*30+14]==source[y*30+29]
        assert pixels[y*30+15]==neighbour[y*30]
        assert pixels[y*30+29]==neighbour[y*30+29]
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
    assert all(bytes(uc.mem_read(pointer+y*60,30))==b'\x76\x98'*15 for y in range(160))


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


def set_strip(uc,rows,width=30,index=100,offset=0,salt=0):
    size=rows*width*2
    uc.mem_write(uc.iv_address(0xc9a590+index*4),struct.pack('<I',size))
    uc.mem_write(uc.iv_address(0xb98790+index*16),struct.pack('<HH',width,rows+7))
    uc.mem_write(uc.iv_address(0xd0ba10+index*4),struct.pack('<I',offset))
    data=struct.pack('<'+str(rows*width)+'H',*((i+salt)%65536 for i in range(rows*width)))
    uc.mem_write(RAW+offset,data)
    return data


@pytest.mark.parametrize('extreme',(False,True))
@pytest.mark.parametrize('rows',(1,3,7,8,159,160,161,240,320,511,1024))
def test_metadata_height_full_pixels_and_bounds(rows,extreme):
    uc,entry,epoch=fixture(extreme=extreme);original=set_strip(uc,rows)
    neighbour=set_strip(uc,rows,index=101,offset=0x20000,salt=12345)
    uc.mem_write(epoch,struct.pack('<I',1))
    reads=[]
    uc.hook_add(UC_HOOK_MEM_READ,lambda _u,_a,at,size,_v,_d:reads.append((at,size)),begin=RAW,end=RAW+0x5ffff)
    pointer=resolve(uc,entry,100)
    assert pointer!=RAW
    expected=[]
    for y in range(rows):
        for x in range(30):
            sx=int((x%15)*29/14+0.5)
            skew=min(sx//2,14-sx//2)
            expected.append((((y-skew)%rows)*30+sx+(12345 if x>=15 else 0))%65536)
    assert bytes(uc.mem_read(pointer,rows*60))==struct.pack('<'+str(len(expected))+'H',*expected)
    assert bytes(uc.mem_read(RAW,len(original)))==original
    assert bytes(uc.mem_read(RAW+0x20000,len(neighbour)))==neighbour
    assert all(any(start<=at and at+size<=start+len(original) for start in (RAW,RAW+0x20000)) for at,size in reads)
    assert len(uc.iv_heap['calls'])==2
    reads.clear();resolve(uc,entry,100)
    assert reads==[] and len(uc.iv_heap['calls'])==2


def test_height_replacement_grows_then_reuses_capacity_and_allocation_failure_is_safe():
    uc,entry,epoch=fixture()
    stock=resolve(uc,entry,100)
    set_strip(uc,320);uc.mem_write(epoch,struct.pack('<I',2))
    tall=resolve(uc,entry,100)
    assert tall!=stock and len(uc.iv_heap['calls'])==3
    set_strip(uc,240);uc.mem_write(epoch,struct.pack('<I',3))
    assert resolve(uc,entry,100)!=RAW and len(uc.iv_heap['calls'])==3
    uc.iv_heap['fail']=True
    set_strip(uc,1024);uc.mem_write(epoch,struct.pack('<I',4))
    assert resolve(uc,entry,100)==RAW
    uc.iv_heap['fail']=False
    assert resolve(uc,entry,100)!=RAW


def test_initial_allocation_failure_passes_original_source():
    uc,entry,_=fixture();uc.iv_heap['fail']=True
    assert resolve(uc,entry,100)==RAW


@pytest.mark.parametrize('index',(100,131))
def test_neighbour_change_invalidates_preceding_pair_including_bank_wrap(index):
    uc,entry,epoch=fixture();uc.mem_write(epoch,struct.pack('<I',1))
    neighbour=100+(index-99)%32
    pointer=resolve(uc,entry,index)
    before=bytes(uc.mem_read(pointer,9600))
    uc.mem_write(RAW+(neighbour-100)*9600,b'\x45\x23'*4800)
    uc.mem_write(epoch,struct.pack('<I',2))
    resolve(uc,entry,neighbour)  # Neighbour rendered first must invalidate us.
    assert resolve(uc,entry,index)==pointer
    for y in range(160):
        assert bytes(uc.mem_read(pointer+y*60,30))==before[y*60:y*60+30]
        assert bytes(uc.mem_read(pointer+y*60+30,30))==b'\x45\x23'*15


def test_shared_neighbour_is_checked_once_per_frame_and_no_warm_allocations():
    uc,entry,epoch=fixture();uc.mem_write(epoch,struct.pack('<I',1))
    for i in range(100,132):resolve(uc,entry,i)
    assert len(uc.iv_heap['calls'])==32
    reads=[]
    uc.hook_add(UC_HOOK_MEM_READ,lambda _u,_a,at,size,_v,_d:reads.append((at,size)),begin=RAW,end=RAW+32*9600-1)
    uc.mem_write(epoch,struct.pack('<I',2))
    for i in range(100,132):resolve(uc,entry,i)
    assert sum(size for _,size in reads)==32*9600
    reads.clear()
    for i in range(100,132):resolve(uc,entry,i)
    assert reads==[] and len(uc.iv_heap['calls'])==32


def test_unavailable_neighbour_is_stable_and_recovers_without_stale_pair():
    uc,entry,epoch=fixture();uc.mem_write(epoch,struct.pack('<I',1))
    uc.mem_write(0xb98790+101*16,struct.pack('<H',32))
    pointer=resolve(uc,entry,100)
    before=bytes(uc.mem_read(pointer,9600))
    # Repeated invalid metadata must not reconvert an unchanged fallback pair.
    writes=[]
    from unicorn import UC_HOOK_MEM_WRITE
    uc.hook_add(UC_HOOK_MEM_WRITE,lambda _u,_a,at,size,_v,_d:writes.append(at),begin=pointer,end=pointer+9599)
    resolve(uc,entry,100);assert writes==[]
    uc.mem_write(0xb98790+101*16,struct.pack('<H',30))
    resolve(uc,entry,100)
    assert writes and bytes(uc.mem_read(pointer,9600))!=before
