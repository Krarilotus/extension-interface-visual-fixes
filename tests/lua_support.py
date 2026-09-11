"""Native framework assembler mappings and Lua game-version context for tests."""
from pathlib import Path
import struct
from lupa import LuaRuntime as _LuaRuntime, lua_type
ROOT=Path(__file__).resolve().parents[1]

def LuaRuntime(*args, extreme=False, **kwargs):
    lua=_LuaRuntime(*args, **kwargs)
    lua.execute('data={version={isExtreme=function() return '+str(extreme).lower()+' end}}')
    lua.globals().package.path=ROOT.as_posix()+'/?.lua;'+lua.globals().package.path
    return lua

def with_symbols(script, mapping=None):
    if mapping is not None:
        script=''.join(f'{name} = 0x{value:X}\n' for name,value in mapping.items())+script
    return script

def flatten_code(table,address):
    out=bytearray()
    def add(values):
        for v in values.values():
            if isinstance(v,int):out.extend(bytes([v]) if 0<=v<=255 else struct.pack('<I',v&0xffffffff))
            elif lua_type(v)=='table':add(v)
            else:out.extend(v(address+len(out)))
    add(table)
    return bytes(out)
