"""Run the pinned UCP Lua core; substitute only native I/O and fixture scans."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from lupa.lua54 import LuaRuntime as _LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_HASHES = {
    'core.lua': 'ca51a116111635d3ed1fd47bd00da34ec1ddd86f973831bdebc683f8f731fe1a',
    'utils.lua': '1456f72d280f77a7f3a9e1b22fe806815a9252b4cfa161f225f8049c15c8f813',
}


@lru_cache
def framework_source(name):
    checkout = Path(os.environ.get('UCP_FRAMEWORK', ROOT/'.framework-fixture'))
    path = checkout/'content/ucp/code'/name
    assert path.is_file(), 'Check out the pinned UCP framework for tests; see TESTING.md'
    source = path.read_text(encoding='utf-8')
    assert hashlib.sha256(source.encode()).hexdigest() == FRAMEWORK_HASHES[name], name
    return source


def LuaRuntime(*args, extreme=False, component_bindings=True, **kwargs):
    lua = _LuaRuntime(*args, **kwargs)
    lua.execute('INFO=0; test_logs={}; log=function(level, message) table.insert(test_logs, {level, message}) end')
    lua.globals().core = lua.execute(framework_source('core.lua'))
    lua.globals().package.loaded['core'] = lua.globals().core
    lua.globals().utils = lua.execute(framework_source('utils.lua'))
    lua.globals().package.path = ROOT.as_posix()+'/?.lua;'+lua.globals().package.path
    if component_bindings:
        # Component/ABI tests isolate emitted wrappers from discovery. Actual
        # runtime discovery is exercised separately by test_native_bindings.
        fixture = json.loads((ROOT/'tests/fixtures/component-bindings.json').read_text())[
            'extreme' if extreme else 'regular']
        layout = lua.execute((ROOT/'native-layout.lua').read_text())
        for name, address in fixture['addresses'].items():
            layout.addresses[name] = address
        layout.patterns = lua.table_from(fixture['patterns'])
        layout.prepare = lambda config: None
        lua.globals().package.loaded['native-layout'] = layout
        lua.globals().component_layout = layout
    return lua


@lru_cache
def assemble(script):
    fasm = os.environ.get('FASM') or shutil.which('fasm')
    if not fasm and os.name == 'nt':
        fasm = 'C:/UCPTools/fasm-interface/FASM.EXE'
    assert fasm, 'Install fasm (or set FASM) to exercise the framework assembler'
    with tempfile.TemporaryDirectory() as temp:
        source, output = Path(temp)/'test.asm', Path(temp)/'test.bin'
        source.write_text(script)
        # UCP 3.0.7 embeds FASM with a 64 KB workspace.
        subprocess.run([fasm, '-m', '64', str(source), str(output)], check=True, capture_output=True)
        return output.read_bytes()


def framework_core(lua, native):
    native = dict(native)
    core = lua.globals().package.loaded['core']
    core.AOBScan = native.pop('AOBScan')  # Independent offline fixture oracle.
    if 'writeCode' in native:
        write = native['writeCode']
        native['writeCode'] = lambda address, values: write(address, bytes(values.values()))
    native['assemble'] = assemble
    lua.globals().ucp = lua.table_from({'internal': lua.table_from(native)})
    return core
