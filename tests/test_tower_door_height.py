"""Execute the actual Lua/FASM wrapper, including its original draw-call ABI."""
from functools import lru_cache
from pathlib import Path
import itertools
import os
import shutil
import struct
import subprocess
import tempfile

from lupa import LuaRuntime
import pytest
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
CAVE, STACK, DRAW, STOP = 0x60000000, 0x60003000, 0x455300, 0x60004000
BUILDING = 0xF98534 + 812
LOGIC, HEIGHT, TERRAIN, ROWS = 0x1BF8368, 0x1D32C38, 0x1D46648, 0x2337300
SITES = {
    0x4E3681: 'DC 52 50 6A 36 B9 90 A0 FE 01 E8 7A 1C F7 FF',
    0x4E36D1: 'DC 52 50 6A 36 B9 90 A0 FE 01 E8 2A 1C F7 FF',
    0x4E3724: 'CC 52 50 6A 36 B9 90 A0 FE 01 E8 D7 1B F7 FF',
    0x4E3777: 'CD 52 50 6A 36 B9 90 A0 FE 01 E8 84 1B F7 FF',
    0x4E3807: '03 D5 52 51 50 B9 90 A0 FE 01 E8 F4 1A F7 FF',
}

DATA = 0x60010000
UPDATES = {0x41B7FF:'89 9C 0F 94 02 00 00',
           0x41B855:'03 81 28 E0 18 00 8B 04 85 68 83 BF 01 A9 00 01 00 00 74 1C A8 02 75 18 A9',
           0x512450:'51 A1 54 EC 1A 02 53 55 8B 2D 50 EC 1A 02 56 89 44 24 0C'}


@lru_cache
def assemble(script, origin):
    fasm = os.environ.get('FASM') or shutil.which('fasm')
    if not fasm and os.name == 'nt':
        fasm = 'C:/UCPTools/fasm-interface/FASM.EXE'
    assert fasm, 'Install fasm (or set FASM) to exercise the framework assembler'
    with tempfile.TemporaryDirectory() as temp:
        source, output = Path(temp)/'test.asm', Path(temp)/'test.bin'
        source.write_text(f'use32\norg {origin}\n{script}')
        subprocess.run([fasm, str(source), str(output)], check=True, capture_output=True)
        return output.read_bytes()


def emit(moved=None, missing=None):
    lua = LuaRuntime(unpack_returned_tuples=True)
    allocations, writes = [], []
    patterns = {**SITES, **UPDATES}

    def scan(pattern):
        matches = [site for site, original in patterns.items() if original == pattern and site != missing]
        if len(matches) != 1:
            raise ValueError('Original signature absent')
        site = matches[0]
        return site-(10 if site in SITES else 6 if site==0x41B855 else 0)+(1 if moved == site else 0)

    def allocate(script):
        origin = CAVE + sum(allocations)
        first, final = assemble(script, 0), assemble(script, origin)
        assert len(first) == len(final)
        allocations.append(len(final))
        writes.append((origin, final))
        return origin

    def data(size, zero):
        assert size == 65540 and zero is True
        writes.append((DATA, bytes(size)))
        return DATA

    def write(address, code):
        result = bytearray()
        for value in code.values():
            if isinstance(value,int): result.append(value)
            else: result.extend(value(address+len(result)))
        writes.append((address, bytes(result)))

    lua.globals().core = lua.table_from({
        'AOBScan': scan, 'allocateAssembly': allocate, 'allocate':data, 'writeCode': write,
        'callTo': lambda target: lambda address: b'\xe8'+struct.pack('<i', target-address-5),
        'jmpTo': lambda target: lambda address: b'\xe9'+struct.pack('<i', target-address-5),
    })
    try:
        lua.execute((ROOT/'tower-door-height.lua').read_text()).enable()
    except Exception:
        if moved or missing: assert not allocations and not writes
        raise
    assert len(allocations) == 6
    assert {address for address, _ in writes if address < CAVE} == set(patterns)
    assert all(len(code) == 5 for address, code in writes if address in SITES)
    return writes


def render_address():
    call = dict(emit())[0x4e3681]
    return 0x4e3686 + struct.unpack('<i',call[1:])[0]


def execute(kind=75, orientation=0, frame=81, walls=((0, 60, 0x100),), ground=8,
            gm=54, override_width=None, context=False):
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(0x400000, 0x2500000)
    uc.mem_map(CAVE, 0x30000)
    for address, code in emit():
        uc.mem_write(address, code)
    width = override_width if override_width is not None else {75:4,76:5,77:6,78:6}.get(kind, 4)
    x, y = 204, 86
    # Same native diagonal-row serialization as the fixture at these coordinates.
    for row in range(400):
        uc.mem_write(ROWS+row*12, struct.pack('<i', row*(row+1)))
    def tile(tx, ty):
        return ty*(ty+1)+tx
    origin = tile(x, y)
    record = bytearray(812)
    struct.pack_into('<H', record, 0xD2, kind)
    struct.pack_into('<HH', record, 0xEE, x, y)
    struct.pack_into('<i', record, 0xF4, origin)
    struct.pack_into('<i', record, 0xF8, width)
    uc.mem_write(BUILDING, bytes(record))
    uc.mem_write(TERRAIN+origin, bytes([ground]))
    uc.mem_write(0x1FE7AA4, struct.pack('<i', orientation))
    # Original 0x40B7B0 selects frame81; 0x40B720 selects frame90.
    # Independent one-hot entrance probes give these sides (not implementation math).
    side = {0:{81:2,90:1},2:{81:3,90:2},4:{81:0,90:3},6:{81:1,90:0}}.get(
        orientation,{81:2,90:1}).get(frame,1)
    points = [[(x+n,y-1) for n in range(width)],
              [(x+width,y+n) for n in range(width)],
              [(x+width-1-n,y+width) for n in range(width)],
              [(x-1,y+width-1-n) for n in range(width)]]
    for index, rise, logic in walls:
        position = tile(*points[side][index])
        uc.mem_write(LOGIC+position*4, struct.pack('<I', logic))
        uc.mem_write(HEIGHT+position, bytes([ground+rise]))
    uc.mem_write(STACK, struct.pack('<5I', STOP, gm, frame, 500, 500))
    registers = [UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
                 UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP,
                 UC_X86_REG_EFLAGS]
    before = [0x123, 0x456, 0x1FEA090, 0x789, 812, 0x234, 0x345, STACK, 0xA93]
    for reg, value in zip(registers, before):
        uc.reg_write(reg, value)
    writes = []
    uc.hook_add(UC_HOOK_MEM_WRITE, lambda _uc, _access, address, size, value, _data:
                writes.append((address, size)))
    uc.emu_start(render_address(), DRAW, count=3000)
    assert uc.reg_read(UC_X86_REG_EIP) == DRAW
    assert [uc.reg_read(reg) for reg in registers] == before
    result = struct.unpack('<5I', uc.mem_read(STACK,20))
    assert result[:3] == (STOP, gm, frame)
    assert all(STACK-128 <= address and address+size <= STACK or
               address in (STACK+12,STACK+16) and size == 4 or
               DATA <= address and address+size <= DATA+65540 for address, size in writes)
    assert bytes(uc.mem_read(BUILDING,812)) == bytes(record)
    # Terminal stand-in checks the original renderer's callee cleanup, not pixels.
    uc.mem_write(DRAW, b'\xc2\x10\x00')
    uc.emu_start(DRAW, STOP, count=2)
    assert uc.reg_read(UC_X86_REG_ESP) == STACK+20
    if context:
        return dict(uc=uc,points=points,tile=tile,registers=registers,before=before,
                    side=side,width=width,record=bytes(record),first_xy=result[3:])
    return result[3:]


def expected(kind=75,frame=81,index=0,rise=60):
    width={75:4,76:5,77:6,78:6}[kind]
    # Isometric displacement from the midpoint, including even-width half tiles.
    displacement=index-(width-1)/2
    return (int(500-16*displacement),
            int(500+90-rise+(-8 if frame==81 else 8)*displacement))


@pytest.mark.parametrize('kind,orientation,frame,ground,rise', list(itertools.product(
    range(75,79), (0,2,4,6), (81,90), (8,40,80), (60,90))))
def test_native_low_high_heights_all_towers_rotations_and_elevations(kind,orientation,frame,ground,rise):
    assert execute(kind,orientation,frame,((0,rise,0x100),),ground) == expected(kind,frame,0,rise)


@pytest.mark.parametrize('kind,orientation,frame', list(itertools.product(range(75,79),(0,2,4,6),(81,90))))
def test_last_boundary_tile_and_mixed_heights(kind,orientation,frame):
    width={75:4,76:5,77:6,78:6}[kind]
    assert execute(kind,orientation,frame,((width-1,60,0x10100),)) == expected(kind,frame,width-1,60)
    assert execute(kind,orientation,frame,((0,60,0x10100),(width-1,90,0x100))) == expected(kind,frame,width-1,90)
    assert execute(kind,orientation,frame,((0,90,0x100),(width-1,60,0x10100))) == expected(kind,frame,0,90)


@pytest.mark.parametrize('walls', [(), ((0,60,0),), ((0,60,0x102),), ((0,60,0x300),)])
def test_absent_or_ineligible_connection_keeps_original_y(walls):
    assert execute(walls=walls) == (500,500)


@pytest.mark.parametrize('rise,expected_y', [(44,546),(74,516),(120,470)])
def test_wall_height_is_relative_to_tower_terrain(rise,expected_y):
    # Steps and walls on neighboring elevated ground use actual absolute height.
    assert execute(walls=((0,rise,0x100),),ground=40) == (524,expected_y+12)


@pytest.mark.parametrize('kwargs', [dict(kind=74),dict(kind=79),dict(gm=55),dict(frame=80),
    dict(frame=91),dict(orientation=1),dict(orientation=8),dict(override_width=3),dict(override_width=7)])
def test_shared_exit_call_and_unsupported_contexts_untouched(kwargs):
    assert execute(**kwargs) == (500,500)


@pytest.mark.parametrize('site', list(SITES))
def test_every_site_is_validated_before_any_write(site):
    with pytest.raises(Exception, match='unsupported tower door renderer layout'):
        emit(moved=site)
    with pytest.raises(ValueError):
        emit(missing=site)


def test_disabled_and_repeated_enable():
    lua=LuaRuntime()
    lua.execute('calls=0; require=function() return {enable=function() calls=calls+1 end} end')
    module=lua.execute((ROOT/'init.lua').read_text())
    module.enable(module,lua.table_from({'tower-door-height':False}))
    assert lua.globals().calls == 0
    module=lua.execute((ROOT/'init.lua').read_text())
    config=lua.table_from({'tower-door-height':True})
    module.enable(module,config)
    module.enable(module,config)
    assert lua.globals().calls == 1


def draw_again(ctx):
    uc=ctx['uc']
    uc.mem_write(STACK,struct.pack('<5I',STOP,54,81,500,500))
    for reg,value in zip(ctx['registers'],ctx['before']): uc.reg_write(reg,value)
    uc.emu_start(render_address(),STOP,count=3000)
    return struct.unpack('<2I',uc.mem_read(STACK+12,8))


def refresh_connections(ctx):
    uc=ctx['uc']
    uc.reg_write(UC_X86_REG_ESP,STACK)
    uc.reg_write(UC_X86_REG_ECX,0xF98520)
    uc.reg_write(UC_X86_REG_EDI,812)
    uc.reg_write(UC_X86_REG_EBX,0)
    uc.emu_start(0x41B7FF,0x41B806,count=300)
    assert bytes(uc.mem_read(BUILDING,812)) == ctx['record']
    for side,points in enumerate(ctx['points']):
        for n,xy in enumerate(points):
            tile=ctx['tile'](*xy)
            values={UC_X86_REG_EAX:tile,UC_X86_REG_EBX:side*ctx['width']+n,
                    UC_X86_REG_ECX:0xF98520,UC_X86_REG_EDI:812,
                    UC_X86_REG_ESI:0x12345,UC_X86_REG_EBP:0x23456,
                    UC_X86_REG_EDX:0x34567,UC_X86_REG_ESP:STACK,
                    UC_X86_REG_EFLAGS:0xA93}
            for reg,value in values.items(): uc.reg_write(reg,value)
            uc.emu_start(0x41B855,0x41B85C,count=300)
            values[UC_X86_REG_EAX]=struct.unpack('<I',uc.mem_read(LOGIC+tile*4,4))[0]
            assert {reg:uc.reg_read(reg) for reg in values}==values
    assert bytes(uc.mem_read(BUILDING,812)) == ctx['record']


def selected_index(ctx,side=None):
    entry=DATA+((812//4)&2047)*32
    side=ctx['side'] if side is None else side
    rank=struct.unpack('<I',ctx['uc'].mem_read(entry+8+side*4,4))[0]
    return None if not rank else 8-(rank&255)


def test_repeated_draws_do_not_read_wall_or_row_arrays():
    ctx=execute(context=True)
    reads=[]
    def observe(_uc,_access,at,size,_value,_data):
        if any(start <= at < start+length for start,length in (
                (LOGIC,80400*4),(HEIGHT,80400),(ROWS,400*12))): reads.append(at)
    ctx['uc'].hook_add(UC_HOOK_MEM_READ,observe)
    for _ in range(100): assert draw_again(ctx)==expected()
    assert reads==[]


def test_existing_connection_refresh_updates_cached_height_and_removal():
    ctx=execute(context=True)
    uc=ctx['uc']; tile=ctx['tile'](*ctx['points'][2][0])
    uc.mem_write(HEIGHT+tile,bytes([98]))
    assert draw_again(ctx)==expected()  # A draw does not rescan changed geometry.
    refresh_connections(ctx)
    assert draw_again(ctx)==expected(rise=90)
    uc.mem_write(LOGIC+tile*4,bytes(4))
    refresh_connections(ctx)
    assert selected_index(ctx) is None
    assert draw_again(ctx)==(500,500)


@pytest.mark.parametrize('width,kind',[(4,75),(5,76),(6,77),(6,78)])
def test_height_then_centre_then_boundary_order(width,kind):
    walls=tuple((n,60,0x100) for n in range(width))
    ctx=execute(kind=kind,walls=walls,context=True)
    assert selected_index(ctx)==(width-1)//2
    refresh_connections(ctx)
    assert selected_index(ctx)==(width-1)//2
    high=ctx['tile'](*ctx['points'][2][width-1])
    ctx['uc'].mem_write(HEIGHT+high,bytes([98]))
    refresh_connections(ctx)
    assert selected_index(ctx)==width-1
    ctx['uc'].mem_write(LOGIC+high*4,bytes(4))
    refresh_connections(ctx)
    assert selected_index(ctx)==(width-1)//2


def test_final_map_preparation_invalidates_same_uid_and_geometry_on_reload():
    ctx=execute(context=True); uc=ctx['uc']
    tile=ctx['tile'](*ctx['points'][2][0])
    uc.mem_write(HEIGHT+tile,bytes([98]))
    uc.reg_write(UC_X86_REG_ESP,STACK)
    uc.reg_write(UC_X86_REG_ECX,0x1A9B1F4)
    uc.reg_write(UC_X86_REG_EFLAGS,0xA93)
    uc.mem_write(0x21AEC54,struct.pack('<I',777))
    uc.emu_start(0x512450,0x512456,count=20)
    assert uc.reg_read(UC_X86_REG_EAX)==777
    assert uc.reg_read(UC_X86_REG_ECX)==0x1A9B1F4
    assert uc.reg_read(UC_X86_REG_ESP)==STACK-4
    assert uc.reg_read(UC_X86_REG_EFLAGS)==0xA93
    assert draw_again(ctx)==expected(rise=90)


def test_building_uid_reuse_invalidates_entry():
    ctx=execute(context=True); uc=ctx['uc']
    tile=ctx['tile'](*ctx['points'][2][0])
    uc.mem_write(HEIGHT+tile,bytes([98]))
    uc.mem_write(BUILDING+0xD8,struct.pack('<I',123))
    assert draw_again(ctx)==expected(rise=90)


def test_cache_indices_have_no_collision_for_native_building_capacity():
    assert len({((i*812)//4)&2047 for i in range(2000)})==2000


@pytest.mark.parametrize('site',list(UPDATES))
def test_update_and_load_signatures_are_validated_before_allocation(site):
    with pytest.raises(Exception,match='unsupported tower connection update layout'):
        emit(moved=site)
    with pytest.raises(ValueError): emit(missing=site)
