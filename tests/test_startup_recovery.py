"""Downloaded executable inside a previously watched folder cannot lock out Settings."""
import json
import sys

import pytest

from src.tidycore import config_manager
from src.tidycore.database import StatisticsDatabase
from src.tidycore.engine import TidyCoreEngine
from src.tidycore.gui import TidyCoreGUI
from PySide6.QtWidgets import QApplication


@pytest.mark.parametrize('protected', ['executable', 'state', 'resources'])
def test_overlapping_saved_target_opens_paused_without_rewriting(tmp_path, monkeypatch, protected):
    watch = tmp_path / 'Downloads'
    watch.mkdir()
    state = tmp_path / 'state'
    state.mkdir()
    monkeypatch.setenv('TIDYCORE_DATA_DIR', str(state))
    monkeypatch.setenv('TIDYCORE_TEST_MODE', '0')
    monkeypatch.setattr(config_manager, 'resource_root', lambda: tmp_path / 'resources')
    if protected == 'executable':
        monkeypatch.setattr(sys, 'frozen', True, raising=False)
        monkeypatch.setattr(sys, 'executable', str(watch / 'TidyCore.exe'))
    elif protected == 'state':
        monkeypatch.setenv('TIDYCORE_DATA_DIR', str(watch / 'state'))
    else:
        monkeypatch.setattr(config_manager, 'resource_root', lambda: watch / 'resources')
    path = state / 'config.json'
    monkeypatch.setattr(config_manager, 'CONFIG_PATH', str(path))
    stored = {'target_folder': str(watch), 'start_paused': False,
              'cooldown_period_seconds': 10, 'rules': {'Text': ['.txt']},
              'ignore_list': ['skip.txt'], 'folder_handling_strategy': 'ignore'}
    path.write_text(json.dumps(stored), encoding='utf-8')
    original = path.read_bytes()
    warnings = []
    recovered = config_manager.load_config(on_target_error=warnings.append)
    assert recovered['target_folder'] == '' and recovered['start_paused']
    assert recovered['rules'] == stored['rules'] and recovered['ignore_list'] == stored['ignore_list']
    assert len(warnings) == 1
    assert path.read_bytes() == original
    with pytest.raises(config_manager.UnsafeWatchTarget):
        config_manager.save_config(stored)
    assert path.read_bytes() == original
    # A corrupt rule must still fail rather than being silently replaced.
    path.write_text(json.dumps(dict(stored, cooldown_period_seconds=-1)), encoding='utf-8')
    with pytest.raises(ValueError, match='Cooldown'):
        config_manager.load_config()
    path.write_bytes(original)
    app = QApplication.instance() or QApplication([])
    db = StatisticsDatabase(state / 'history.db')
    db.record_file_operation('existing.txt', 'original', 'destination', 'Text')
    engine = TidyCoreEngine(recovered, db)
    window = TidyCoreGUI(engine, app)
    try:
        window.select_page(1)
        assert window.settings_page.folder_path_edit.text() == ''
        assert 'Move TidyCore outside' in window.settings_page.target_warning.text()
        assert not engine.is_running and engine.target_folder is None
        assert db.get_total_stats() == 1
        assert path.read_bytes() == original
    finally:
        window.tray_icon.hide()
        window._force_exit = True
        window.close()
        window.deleteLater()
        app.processEvents()
