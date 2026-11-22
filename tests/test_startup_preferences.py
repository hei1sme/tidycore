from contextlib import nullcontext

import pytest

from src.tidycore import config_manager
from src.tidycore import startup_manager as startup_module


def test_fresh_config_auto_watches_but_has_no_target(tmp_path, monkeypatch):
    monkeypatch.setattr(config_manager, 'CONFIG_PATH', str(tmp_path / 'config.json'))
    config = config_manager.load_config()
    assert config['target_folder'] == ''
    assert not config['start_paused'] and config['start_in_tray']


def test_legacy_paused_preference_is_retained():
    config = config_manager.validate_config({'target_folder': '', 'start_paused': True})
    assert config['start_paused']
    assert config['start_in_tray']


@pytest.mark.parametrize('setting', ['start_paused', 'start_in_tray'])
@pytest.mark.parametrize('value', ['false', 0, None])
def test_invalid_launch_preferences_are_rejected(setting, value):
    with pytest.raises(ValueError, match='true or false'):
        config_manager.validate_config({'target_folder': '', setting: value})


def test_startup_commands_and_legacy_registration(monkeypatch):
    command = startup_module.get_application_path(startup=True)
    assert command.endswith(' --startup')
    legacy = startup_module.get_application_path()
    assert command == legacy + ' --startup'
    monkeypatch.setenv('TIDYCORE_TEST_MODE', '0')
    manager = startup_module.StartupManager()
    registry = {manager.app_name: legacy}
    # Every registry call is replaced; no real Windows startup entry is touched.
    monkeypatch.setattr(startup_module.winreg, 'OpenKey', lambda *args: nullcontext('fake-key'))
    monkeypatch.setattr(startup_module.winreg, 'QueryValueEx', lambda key, name: (registry[name], 1))
    monkeypatch.setattr(startup_module.winreg, 'SetValueEx', lambda key, name, reserved, kind, value: registry.update({name: value}))
    monkeypatch.setattr(startup_module.winreg, 'DeleteValue', lambda key, name: registry.pop(name))
    assert manager.is_enabled()
    manager.enable()
    assert registry[manager.app_name] == command
    assert manager.is_enabled()
    manager.disable()
    assert not registry


def test_packaged_startup_command_preserves_spaces(monkeypatch):
    monkeypatch.setattr(startup_module.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(startup_module.sys, 'executable', r'C:\Apps\Tidy Core\TidyCore.exe')
    assert startup_module.get_application_path(startup=True) == '"C:\\Apps\\Tidy Core\\TidyCore.exe" --startup'
