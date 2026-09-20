"""Keep ordered feature installation, preflight and diagnostic completion honest."""
from pathlib import Path
import pytest
from lua_support import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]


def test_all_disabled_performs_no_discovery_or_installation_and_enables_once():
    lua = LuaRuntime(component_bindings=False)
    def require(name):
        raise AssertionError(f'disabled feature required {name}')
    lua.globals().require = require
    module = lua.execute((ROOT/'init.lua').read_text())
    config = lua.table_from({'tower-door-height': False, 'cliff-texture-direction': False})
    module.enable(module, config)
    logs = [row[2] for row in lua.globals().test_logs.values()]
    assert len(logs) == 2 and logs[-1].startswith('startup complete;')
    module.enable(module, config)
    assert [row[2] for row in lua.globals().test_logs.values()] == logs


@pytest.mark.parametrize('fail', (False, True))
def test_sparse_features_preserve_order_and_failed_install_does_not_log_completion(fail):
    lua = LuaRuntime(component_bindings=False)
    actions = []
    def install(name):
        actions.append(name)
        if fail and name == 'camera-preview':
            raise ValueError('occupied test site')
    def require(name):
        if name == 'native-layout':
            return lua.table_from({'prepare': lambda config: actions.append('preflight')})
        return lua.table_from({'enable': lambda: install(name)})
    lua.globals().require = require
    module = lua.execute((ROOT/'init.lua').read_text())
    config = lua.table_from({'lobby-map-descriptions': True,
                            'building-preview-during-camera-movement': True,
                            'tower-door-height': False})
    if fail:
        with pytest.raises(ValueError, match='occupied test site'):
            module.enable(module, config)
    else:
        module.enable(module, config)
    assert actions == ['preflight', 'lobby-description', 'camera-preview']
    logs = [row[2] for row in lua.globals().test_logs.values()]
    assert any(message.startswith('startup complete;') for message in logs) == (not fail)
    assert ('installed building-preview-during-camera-movement' in logs) == (not fail)
