import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QTreeWidgetItem

from src.tidycore import config_manager
from src.tidycore.database import StatisticsDatabase
from src.tidycore.engine import TidyCoreEngine
from src.tidycore.gui import TidyCoreGUI
from src.tidycore.startup_manager import startup_manager, get_application_path


@pytest.fixture(scope='module')
def app():
    instance = QApplication.instance() or QApplication([])
    instance.setStyle('Fusion')
    instance.setPalette(instance.style().standardPalette())
    return instance


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.setenv('TIDYCORE_DATA_DIR', str(tmp_path))
    monkeypatch.setattr(config_manager, 'CONFIG_PATH', None)
    watch = tmp_path / 'watch'
    watch.mkdir()
    config = {'target_folder': str(watch), 'cooldown_period_seconds': 1,
              'folder_handling_strategy': 'ignore', 'rules': {'Text': ['.txt']},
              'ignore_list': [], 'start_paused': True}
    config_manager.save_config(config)
    engine = TidyCoreEngine(config, StatisticsDatabase(tmp_path / 'history.db'))
    widget = TidyCoreGUI(engine, app)
    widget.show()
    app.processEvents()
    yield widget
    engine.stop()
    widget.tray_icon.hide()
    widget._force_exit = True
    widget.close()
    widget.deleteLater()
    app.processEvents()


def test_ui_persisted_counts_and_truthful_selection(window, app):
    engine = window.engine
    source = engine.target_folder / 'notes.txt'
    source.write_bytes(b'notes')
    engine.is_running = True
    engine._organize_item(str(source))
    window.refresh_history()
    assert window.total_value.text() == '1'
    window.history_table.selectRow(0)
    window.show_selection()
    assert window.undo_button.isEnabled()
    assert engine.undo_operation(window.operations[0]['id'])
    window.refresh_history()
    assert window.total_value.text() == '0'
    assert window.history_table.item(0,3).text() == 'Undone'
    assert not window.undo_button.isEnabled()


def test_settings_roundtrip_empty_subcategory_and_reject_duplicate(window):
    settings = window.settings_page
    settings.rules_tree.clear()
    category = QTreeWidgetItem(settings.rules_tree, ['Docs'])
    QTreeWidgetItem(category, ['Empty'])
    settings.cooldown_spin.setValue(7)
    settings._save_settings()
    saved = config_manager.load_config()
    assert saved['rules'] == {'Docs': {'Empty': []}}
    assert saved['cooldown_period_seconds'] == 7
    before = config_manager.config_path().read_bytes()
    QTreeWidgetItem(settings.rules_tree, ['docs'])
    settings._save_settings()
    assert config_manager.config_path().read_bytes() == before
    assert 'unique' in settings.save_feedback.text()


def test_test_mode_disables_startup_and_external_target(window, tmp_path):
    assert not window.settings_page.startup_checkbox.isEnabled()
    with pytest.raises(RuntimeError, match='disabled'):
        startup_manager.enable()
    with pytest.raises(RuntimeError, match='disabled'):
        startup_manager.disable()
    before = config_manager.config_path().read_bytes()
    window.settings_page.folder_path_edit.setText(str(tmp_path.parent))
    window.settings_page._save_settings()
    assert config_manager.config_path().read_bytes() == before


def test_startup_source_command_has_one_quoted_interpreter():
    command = get_application_path()
    assert 'main.py' in command
    assert not command.startswith('""')


def test_existing_instance_channel_restores_hidden_window(window, app):
    import time
    import uuid
    from PySide6.QtNetwork import QLocalSocket
    from src.tidycore.instance import InstanceServer
    name = 'TidyCore-test-' + uuid.uuid4().hex
    server = InstanceServer(name, window)
    window.hide()
    app.processEvents()
    socket = QLocalSocket()
    socket.connectToServer(name)
    assert socket.waitForConnected(1000)
    socket.write(b'sh')
    socket.flush()
    for _ in range(10):
        app.processEvents()
        time.sleep(.01)
    assert not window.isVisible()
    socket.write(b'ow')
    socket.flush()
    for _ in range(30):
        app.processEvents()
        time.sleep(.01)
        if window.isVisible() and socket.bytesAvailable():
            break
    assert window.isVisible()
    assert bytes(socket.readAll()) == b'ok'
    server.close()


def test_history_search_filters_without_changing_totals_or_undo_identity(window):
    engine=window.engine
    engine.is_running=True
    for name in ('alpha.txt','beta.txt'):
        source=engine.target_folder/name
        source.write_bytes(name.encode())
        engine._organize_item(str(source))
    window.refresh_history()
    window.history_search.setText('alpha')
    assert window.history_table.rowCount()==1
    assert window.displayed_operations[0]['filename']=='alpha.txt'
    window.history_table.selectRow(0)
    selected=window.selected_operation()
    assert selected['filename']=='alpha.txt'
    assert window.total_value.text()=='2'
    assert engine.undo_operation(selected['id'])
    window.refresh_history()
    assert window.history_table.item(0,3).text()=='Undone'
    window.history_filter.setCurrentIndex(1)
    assert window.history_table.rowCount()==0
    assert not window.undo_button.isEnabled()
    assert 'No matching' in window.empty_label.text()
    window.history_filter.setCurrentIndex(2)
    assert window.history_table.rowCount()==1
    window.history_search.clear()
    assert window.total_value.text()=='1'


def test_error_log_expands_and_rule_actions_follow_selection(window):
    assert not window.log_toggle.isChecked()
    window.add_log_message('[ERROR] fixture error')
    assert window.log_toggle.isChecked()
    assert not window.activity_feed.isHidden()
    rules=window.settings_page
    rules.rules_tree.setCurrentItem(rules.rules_tree.topLevelItem(0))
    assert rules.rule_add_extension.isEnabled()
    assert rules.rule_add_subcategory.isEnabled()
    rules.rules_tree.setCurrentItem(rules.rules_tree.topLevelItem(0).child(0))
    assert not rules.rule_add_extension.isEnabled()
    assert not rules.rule_add_subcategory.isEnabled()
    assert rules.rule_remove.isEnabled()


def test_compact_selection_keeps_history_row_and_undo_visible(window, app):
    engine=window.engine
    engine.is_running=True
    source=engine.target_folder/'long descriptive file name.txt'
    source.write_bytes(b'compact fixture')
    engine._organize_item(str(source))
    window.refresh_history()
    window.history_table.selectRow(0)
    window.resize(860,600)
    app.processEvents()
    assert window.metrics_container.isHidden()
    assert window.history_table.viewport().height() >= window.history_table.rowHeight(0)
    assert window.undo_button.isVisible() and window.undo_button.isEnabled()
    assert window.details_label.toolTip().endswith(source.name)
