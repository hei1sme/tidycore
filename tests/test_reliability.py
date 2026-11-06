import copy
from concurrent.futures import ThreadPoolExecutor
import ctypes
from datetime import date, timedelta
import json
import os
from pathlib import Path
import sqlite3
import time

import pytest

from src.tidycore.config_manager import load_config, save_config, validate_config
from src.tidycore.database import StatisticsDatabase
from src.tidycore.engine import TidyCoreEngine


def wait_for(predicate, timeout=10):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if predicate():
            return
        time.sleep(.05)
    assert predicate(), 'Timed out waiting for real worker behavior'


@pytest.fixture
def engine(tmp_path, monkeypatch):
    monkeypatch.setenv('TIDYCORE_DATA_DIR', str(tmp_path))
    watch = tmp_path / 'watch'
    watch.mkdir()
    db = StatisticsDatabase(tmp_path / 'history.db')
    config = {'target_folder': str(watch), 'rules': {'Documents': {'Text': ['.txt'], '__extensions__': ['.pdf']}, 'Images': ['.png']},
              'ignore_list': [], 'cooldown_period_seconds': 1, 'folder_handling_strategy': 'smart_scan', 'start_paused': False}
    item = TidyCoreEngine(config, db)
    yield item
    item.stop()
    item.join()


def test_initial_scan_debounces_and_modifications_reset(engine):
    source = engine.target_folder / 'growing.txt'
    source.write_bytes(b'first')
    engine.initial_scan()
    assert source.exists() and engine.db.get_total_stats() == 0
    first = engine.cooldown_files[str(source)]
    time.sleep(.02)
    source.write_bytes(b'second')
    engine._queue_item_for_processing(str(source))
    assert engine.cooldown_files[str(source)] > first
    engine._process_cooldown_files()
    assert source.exists()


def test_watch_create_rename_restart_undo_and_no_loss(engine):
    engine.start()
    partial = engine.target_folder / 'résumé.txt.crdownload'
    partial.write_bytes(b'fixture contents\x00\xff')
    time.sleep(2.2)
    assert partial.exists() and engine.db.get_total_stats() == 0
    source = partial.with_suffix('')
    partial.rename(source)
    destination = engine.target_folder / 'Documents' / 'Text' / source.name
    wait_for(destination.exists)
    assert destination.read_bytes() == b'fixture contents\x00\xff'
    wait_for(lambda: engine.db.get_total_stats() == 1)
    assert engine.db.get_today_stats() == 1
    assert engine.db.get_category_stats_today() == {'Documents': 1}
    operation = engine.db.get_recent_operations()[0]
    engine.stop()
    engine.join()
    reopened = StatisticsDatabase(engine.db.db_path)
    restarted = TidyCoreEngine(engine.config, reopened)
    try:
        assert reopened.get_total_stats() == 1
        assert restarted.undo_operation(operation['id'])
        assert source.read_bytes() == b'fixture contents\x00\xff'
        assert reopened.get_total_stats() == 0
        assert reopened.get_operation(operation['id'])['status'] == 'undone'
        restarted.start()
        time.sleep(2.5)
        assert source.exists() and not destination.exists()
        assert not restarted._should_process(source)
    finally:
        restarted.stop()
        restarted.join()


def test_collision_preserves_both_and_undo_refuses_occupied_original(engine):
    source = engine.target_folder / 'notes.txt'
    source.write_bytes(b'new')
    directory = engine.target_folder / 'Documents' / 'Text'
    directory.mkdir(parents=True)
    existing = directory / source.name
    existing.write_bytes(b'old')
    assert engine._organize_item(str(source))
    row = engine.db.get_recent_operations()[0]
    assert existing.read_bytes() == b'old'
    assert Path(row['destination_path']).read_bytes() == b'new'
    source.write_bytes(b'replacement')
    assert not engine.undo_operation(row['id'])
    assert source.read_bytes() == b'replacement'
    assert engine.db.get_total_stats() == 1


def test_changed_contents_refuse_undo(engine):
    source = engine.target_folder / 'notes.txt'
    source.write_bytes(b'original')
    engine._organize_item(str(source))
    row = engine.db.get_recent_operations()[0]
    Path(row['destination_path']).write_bytes(b'edited')
    assert not engine.undo_operation(row['id'])
    assert not source.exists()


def test_duplicate_events_one_move_and_pause_resume(engine):
    engine.start()
    engine.pause()
    source = engine.target_folder / 'held.txt'
    source.write_bytes(b'held')
    for _ in range(10):
        engine._queue_item_for_processing(str(source))
    time.sleep(2.2)
    assert source.exists() and engine.thread.is_alive()
    assert engine.resume()
    wait_for(lambda: engine.db.get_total_stats() == 1)
    engine.pause()
    time.sleep(.4)
    assert engine.thread.is_alive()
    assert engine.resume()
    time.sleep(.3)
    assert engine.db.get_total_stats() == 1


def test_retarget_refreshes_observer_rules_and_cooldown(engine, tmp_path):
    engine.start()
    wait_for(lambda: engine.observer is not None and engine.observer.is_alive())
    new_target = tmp_path / 'new-watch'
    new_target.mkdir()
    old_target = engine.target_folder
    config = copy.deepcopy(engine.config)
    config.update(target_folder=str(new_target), rules={'Renamed': ['.txt']}, cooldown_period_seconds=2, ignore_list=['skip.txt'])
    engine.reload_config(config)
    wait_for(lambda: engine.target_folder == new_target)
    assert not engine.is_running
    assert engine.cooldown_period == 2 and 'renamed' in engine.managed_categories
    assert engine.resume()
    (old_target / 'old.txt').write_bytes(b'old')
    (new_target / 'new.txt').write_bytes(b'new')
    (new_target / 'skip.txt').write_bytes(b'ignored')
    wait_for(lambda: (new_target / 'Renamed' / 'new.txt').exists(), timeout=12)
    # Rename becomes visible before the journal completion transaction commits.
    wait_for(lambda: engine.db.get_total_stats() == 1)
    assert (old_target / 'old.txt').exists() and (new_target / 'skip.txt').exists()
    assert engine.db.get_total_stats() == 1


def test_folder_partial_download_and_managed_categories(engine):
    folder = engine.target_folder / 'bundle'
    folder.mkdir()
    partial = folder / 'active.part'
    partial.write_bytes(b'partial')
    with pytest.raises(PermissionError):
        engine._snapshot(folder)
    partial.rename(folder / 'finished.txt')
    assert engine._organize_item(str(folder))
    row = engine.db.get_recent_operations()[0]
    assert row['category'] == 'Documents'
    assert engine.db.get_total_stats() == 1
    assert not engine._should_process(engine.target_folder / 'Documents')
    assert engine.undo_operation(row['id'])
    assert (folder / 'finished.txt').read_bytes() == b'partial'


def test_windows_locked_file_is_retried_without_history_success(engine):
    if os.name != 'nt':
        pytest.skip('Windows sharing semantics')
    source = engine.target_folder / 'locked.txt'
    source.write_bytes(b'locked')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateFileW(str(source), 0x80000000, 0, None, 3, 0, None)
    assert handle != ctypes.c_void_p(-1).value
    engine.start()
    try:
        time.sleep(2.8)
        assert source.exists() and engine.db.get_total_stats() == 0
    finally:
        kernel.CloseHandle(handle)
    wait_for(lambda: engine.db.get_total_stats() == 1)
    assert (engine.target_folder / 'Documents' / 'Text' / source.name).read_bytes() == b'locked'


def test_db_failure_before_move_preserves_source(engine, monkeypatch):
    source = engine.target_folder / 'safe.txt'
    source.write_bytes(b'safe')
    def fail(*args):
        raise sqlite3.OperationalError('injected disk full')
    monkeypatch.setattr(engine.db, 'begin_operation', fail)
    with pytest.raises(sqlite3.OperationalError):
        engine._organize_item(str(source))
    assert source.read_bytes() == b'safe'


def test_reconcile_crash_after_rename_and_after_undo(engine, monkeypatch):
    source = engine.target_folder / 'recover.txt'
    source.write_bytes(b'recover')
    original_set = engine.db.set_status
    def fail_completion(operation_id, status, error=None):
        if status == 'completed':
            raise sqlite3.OperationalError('injected commit failure')
        original_set(operation_id, status, error)
    monkeypatch.setattr(engine.db, 'set_status', fail_completion)
    with pytest.raises(sqlite3.OperationalError):
        engine._organize_item(str(source))
    assert not source.exists()
    row = engine.db.get_recent_operations()[0]
    assert row['status'] == 'pending'
    monkeypatch.setattr(engine.db, 'set_status', original_set)
    engine.recover_operations()
    assert engine.db.get_total_stats() == 1
    engine.db.set_status(row['id'], 'undo_pending')
    Path(row['destination_path']).rename(source)
    engine.recover_operations()
    assert engine.db.get_operation(row['id'])['status'] == 'undone'
    assert engine.db.is_restored(source)


def test_ambiguous_recovery_preserves_both_and_blocks_source(engine):
    source = engine.target_folder / 'ambiguous.txt'
    source.write_bytes(b'a')
    destination = engine.target_folder / 'other.txt'
    destination.write_bytes(b'b')
    operation_id = engine.db.begin_operation(source.name, source, destination, 'Documents', fingerprint=engine.fingerprint(source))
    engine.recover_operations()
    assert engine.db.get_operation(operation_id)['status'] == 'review'
    assert source.read_bytes() == b'a' and destination.read_bytes() == b'b'
    assert not engine._should_process(source)


def test_database_concurrent_transactions_and_restart(tmp_path):
    db = StatisticsDatabase(tmp_path / 'concurrent.db')
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda i: db.record_file_operation(str(i), f's{i}', f'd{i}', 'Text'), range(60)))
    assert StatisticsDatabase(db.db_path).get_total_stats() == 60
    assert db.get_today_stats() == 60 and db.get_category_stats_today() == {'Text': 60}
    with db.connection() as conn:
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        plan = conn.execute("EXPLAIN QUERY PLAN SELECT category,COUNT(*) FROM file_operations WHERE status='completed' AND operation_date=? GROUP BY category", (date.today().isoformat(),)).fetchall()
        assert any('INDEX' in row['detail'] for row in plan)


def test_legacy_migration_backup_and_counts(tmp_path):
    path = tmp_path / 'legacy.db'
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE file_operations(id INTEGER PRIMARY KEY,filename TEXT NOT NULL,source_path TEXT NOT NULL,destination_path TEXT NOT NULL,category TEXT NOT NULL,subcategory TEXT,operation_type TEXT,timestamp TEXT)')
    conn.execute("INSERT INTO file_operations VALUES(1,'legacy.txt','s','d','Documents',NULL,'organize',CURRENT_TIMESTAMP)")
    conn.execute('CREATE TABLE daily_stats(date TEXT PRIMARY KEY,files_organized INTEGER)')
    conn.execute("INSERT INTO daily_stats VALUES('2020-01-01',999)")
    conn.commit()
    conn.close()
    db = StatisticsDatabase(path)
    assert db.get_total_stats() == 1
    assert db.get_recent_operations()[0]['fingerprint'] is None
    assert len(list(tmp_path.glob('legacy.db.backup-*'))) == 1
    assert StatisticsDatabase(path).get_total_stats() == 1


def test_corrupt_and_future_databases_fail_without_replacement(tmp_path):
    corrupt = tmp_path / 'corrupt.db'
    corrupt.write_bytes(b'not a database')
    with pytest.raises(sqlite3.DatabaseError):
        StatisticsDatabase(corrupt)
    assert corrupt.read_bytes() == b'not a database'
    future = tmp_path / 'future.db'
    with sqlite3.connect(future) as conn:
        conn.execute('PRAGMA user_version=999')
    with pytest.raises(sqlite3.DatabaseError, match='newer'):
        StatisticsDatabase(future)


@pytest.mark.parametrize('category', ['../escape', 'C:\\escape', 'CON', 'nested/name', 'bad.', '.hidden', 'trailing '])
def test_unsafe_rules_rejected(engine, category):
    config = copy.deepcopy(engine.config)
    config['rules'] = {category: ['.txt']}
    with pytest.raises(ValueError):
        validate_config(config)


def test_atomic_settings_and_invalid_config_preservation(engine, tmp_path, monkeypatch):
    from src.tidycore import config_manager
    path = tmp_path / 'settings.json'
    monkeypatch.setattr(config_manager, 'CONFIG_PATH', str(path))
    save_config(engine.config)
    original = path.read_bytes()
    bad = copy.deepcopy(engine.config)
    bad['cooldown_period_seconds'] = -1
    with pytest.raises(ValueError):
        save_config(bad)
    assert path.read_bytes() == original
    good = copy.deepcopy(engine.config)
    good['cooldown_period_seconds'] = 7
    save_config(good)
    assert load_config()['cooldown_period_seconds'] == 7
    assert path.with_suffix('.json.bak').read_bytes() == original
    path.write_bytes(b'{broken')
    with pytest.raises(json.JSONDecodeError):
        load_config()
    assert path.read_bytes() == b'{broken'


def test_weekly_is_seven_local_calendar_days(engine):
    for days in range(9):
        operation = engine.db.record_file_operation(str(days), 's', 'd', 'Text')
        with engine.db.connection() as conn:
            conn.execute('UPDATE file_operations SET operation_date=? WHERE id=?', ((date.today()-timedelta(days=days)).isoformat(),operation))
    assert len(engine.db.get_weekly_stats()) == 7


def test_shutdown_cancels_pending_work(engine):
    source = engine.target_folder / 'pending.txt'
    source.write_bytes(b'pending')
    engine.start()
    engine.stop()
    engine.join()
    assert source.exists() and not engine.thread.is_alive()


def test_previous_category_stays_managed_after_rule_rename(engine):
    source = engine.target_folder / 'notes.txt'
    source.write_bytes(b'preserved')
    engine._organize_item(str(source))
    config = copy.deepcopy(engine.config)
    config['rules'] = {'New category': ['.txt']}
    engine._apply_config(validate_config(config))
    old_category = engine.target_folder / 'Documents'
    assert not engine._should_process(old_category)
    reopened = StatisticsDatabase(engine.db.db_path)
    assert reopened.is_managed_directory(old_category)


def test_state_and_application_ancestor_cannot_be_watched(engine, tmp_path, monkeypatch):
    state = tmp_path / 'state'
    state.mkdir()
    monkeypatch.setenv('TIDYCORE_DATA_DIR', str(state))
    config = copy.deepcopy(engine.config)
    config['target_folder'] = str(tmp_path)
    with pytest.raises(ValueError, match='application files or its state'):
        validate_config(config)


def test_snapshot_counts_agree_with_history(engine):
    source = engine.target_folder / 'notes.txt'
    source.write_bytes(b'notes')
    engine._organize_item(str(source))
    history, today, total, categories = engine.db.dashboard_snapshot()
    assert today == total == sum(categories.values()) == len(history) == 1


def test_windows_collision_race_never_overwrites(engine, monkeypatch):
    if os.name != 'nt':
        pytest.skip('Windows no-replace rename semantics')
    source = engine.target_folder / 'race.txt'
    source.write_bytes(b'new')
    original_rename = os.rename
    occupied = []
    def race(src, dst):
        Path(dst).write_bytes(b'competing writer')
        occupied.append(Path(dst))
        return original_rename(src, dst)
    monkeypatch.setattr(os, 'rename', race)
    with pytest.raises(FileExistsError):
        engine._organize_item(str(source))
    assert source.read_bytes() == b'new'
    assert occupied[0].read_bytes() == b'competing writer'
    assert engine.db.get_total_stats() == 0


def test_real_windows_junction_does_not_escape_target(engine, tmp_path):
    if os.name != 'nt':
        pytest.skip('Windows junction')
    import _winapi
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'private.txt').write_bytes(b'never move')
    junction = engine.target_folder / 'linked-folder'
    _winapi.CreateJunction(str(outside), str(junction))
    assert junction.is_junction()
    assert not engine._should_process(junction)
    container = engine.target_folder / 'bundle'
    container.mkdir()
    _winapi.CreateJunction(str(outside), str(container / 'nested-link'))
    with pytest.raises(ValueError, match='link or junction'):
        engine._snapshot(container)
    assert (outside / 'private.txt').read_bytes() == b'never move'
