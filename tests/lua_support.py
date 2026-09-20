"""Native framework assembler mappings and Lua game-version context for tests."""
from pathlib import Path
import struct
import json
from lupa import LuaRuntime as _LuaRuntime, lua_type
ROOT=Path(__file__).resolve().parents[1]

def LuaRuntime(*args, extreme=False, component_bindings=True, **kwargs):
    lua=_LuaRuntime(*args, **kwargs)
    lua.execute('data={version={isExtreme=function() return '+str(extreme).lower()+' end}}')
    lua.globals().package.path=ROOT.as_posix()+'/?.lua;'+lua.globals().package.path
    if component_bindings:
        # Component/ABI tests isolate emitted wrappers from discovery. Actual
        # runtime discovery is exercised separately by test_native_bindings.
        fixture=json.loads((ROOT/'tests/fixtures/component-bindings.json').read_text())[
            'extreme' if extreme else 'regular']
        layout=lua.execute((ROOT/'native-layout.lua').read_text())
        for name,address in fixture['addresses'].items(): layout.addresses[name]=address
        layout.patterns=lua.table_from(fixture['patterns'])
        layout.prepare=lambda config:None
        lua.globals().package.loaded['native-layout']=layout
        lua.globals().component_layout=layout
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
