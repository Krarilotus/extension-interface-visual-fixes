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
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_WRITE
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

    def scan(pattern):
        matches = [site for site, original in SITES.items() if original == pattern and site != missing]
        if len(matches) != 1:
            raise ValueError('Original call signature absent')
        return matches[0]-10+(1 if moved == matches[0] else 0)

    def allocate(script):
        first, final = assemble(script, 0), assemble(script, CAVE)
        assert len(first) == len(final)
        allocations.append(len(final))
        writes.append((CAVE, final))
        return CAVE

    def write(address, code):
        result = bytearray()
        for value in code.values():
            result.extend(value(address+len(result)))
        writes.append((address, bytes(result)))

    lua.globals().core = lua.table_from({
        'AOBScan': scan, 'allocateAssembly': allocate, 'writeCode': write,
        'callTo': lambda target: lambda address: b'\xe8'+struct.pack('<i', target-address-5),
    })
    try:
        lua.execute((ROOT/'tower-door-height.lua').read_text()).enable()
    except Exception:
        assert not allocations and not writes
        raise
    assert len(allocations) == 1
    assert [address for address, _ in writes[1:]] == list(SITES)
    assert all(len(code) == 5 for _, code in writes[1:])
    return writes


def execute(kind=75, orientation=0, frame=81, walls=((0, 60, 0x100),), ground=8,
            gm=54, override_width=None):
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(0x400000, 0x2500000)
    uc.mem_map(CAVE, 0x5000)
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
    side = (orientation//2+1+(frame == 90)) % 4
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
    uc.emu_start(CAVE, DRAW, count=1000)
    assert uc.reg_read(UC_X86_REG_EIP) == DRAW
    assert [uc.reg_read(reg) for reg in registers] == before
    result = struct.unpack('<5I', uc.mem_read(STACK,20))
    assert result[:4] == (STOP, gm, frame, 500)
    assert all(STACK-44 <= address and address+size <= STACK or
               address == STACK+16 and size == 4 for address, size in writes)
    assert bytes(uc.mem_read(BUILDING,812)) == bytes(record)
    # Terminal stand-in checks the original renderer's callee cleanup, not pixels.
    uc.mem_write(DRAW, b'\xc2\x10\x00')
    uc.emu_start(DRAW, STOP, count=2)
    assert uc.reg_read(UC_X86_REG_ESP) == STACK+20
    return result[4]


@pytest.mark.parametrize('kind,orientation,frame,ground,rise', list(itertools.product(
    range(75,79), (0,2,4,6), (81,90), (8,40,80), (60,90))))
def test_native_low_high_heights_all_towers_rotations_and_elevations(kind,orientation,frame,ground,rise):
    assert execute(kind,orientation,frame,((0,rise,0x100),),ground) == 500+90-rise


@pytest.mark.parametrize('kind,orientation,frame', list(itertools.product(range(75,79),(0,2,4,6),(81,90))))
def test_last_boundary_tile_and_mixed_heights(kind,orientation,frame):
    width={75:4,76:5,77:6,78:6}[kind]
    assert execute(kind,orientation,frame,((width-1,60,0x10100),)) == 530
    assert execute(kind,orientation,frame,((0,60,0x10100),(width-1,90,0x100))) == 500
    assert execute(kind,orientation,frame,((0,90,0x100),(width-1,60,0x10100))) == 500


@pytest.mark.parametrize('walls', [(), ((0,60,0),), ((0,60,0x102),), ((0,60,0x300),)])
def test_absent_or_ineligible_connection_keeps_original_y(walls):
    assert execute(walls=walls) == 500


@pytest.mark.parametrize('rise,expected', [(44,546),(74,516),(120,470)])
def test_wall_height_is_relative_to_tower_terrain(rise,expected):
    # Steps and walls on neighboring elevated ground use actual absolute height.
    assert execute(walls=((0,rise,0x100),),ground=40) == expected


@pytest.mark.parametrize('kwargs', [dict(kind=74),dict(kind=79),dict(gm=55),dict(frame=80),
    dict(frame=91),dict(orientation=1),dict(orientation=8),dict(override_width=3),dict(override_width=7)])
def test_shared_exit_call_and_unsupported_contexts_untouched(kwargs):
    assert execute(**kwargs) == 500


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
