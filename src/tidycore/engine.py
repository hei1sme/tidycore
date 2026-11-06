"""One serialized organizer worker, cancellable stability checks and durable undo."""
import copy
import hashlib
import logging
import os
from pathlib import Path
import queue
import sqlite3
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config_manager import ConfigManager, PARTIAL_EXTENSIONS, validate_config
from .database import statistics_db
from .signals import signals


class Cancelled(Exception):
    pass


def linked(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


class TidyCoreEngine(FileSystemEventHandler):
    def __init__(self, config, database=None):
        super().__init__()
        self.logger = logging.getLogger('TidyCore')
        self.db = database if database is not None else statistics_db
        self.config_manager = ConfigManager()
        self.stop_event = threading.Event()
        self._wake = threading.Event()
        self._lock = threading.RLock()
        self.cooldown_lock = threading.Lock()
        self.cooldown_files = {}
        self._snapshots = {}
        self._retries = {}
        self._commands = queue.Queue()
        self.observer = None
        self.thread = None
        self.last_error = ''
        self._apply_config(validate_config(config))
        self.is_running = bool(self.target_folder) and not config.get('start_paused', True)
        self.files_organized_today = self.db.get_today_stats()
        self.files_organized_total = self.db.get_total_stats()

    def _apply_config(self, config):
        self.config = copy.deepcopy(config)
        self.target_folder = Path(config['target_folder']) if config['target_folder'] else None
        self.rules = config.get('rules', {})
        self.ignore_list = [x.casefold() for x in config.get('ignore_list', [])]
        self.cooldown_period = config.get('cooldown_period_seconds', 5)
        self.managed_categories = {x.casefold() for x in self.rules} | {'others'}

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self.run, name='TidyCoreOrganizer', daemon=False)
        self.thread.start()

    def run(self):
        try:
            with self._lock:
                self.recover_operations()
            current_target = None
            next_scan = 0
            while not self.stop_event.is_set():
                with self._lock:
                    if current_target != self.target_folder or (self.observer and not self.observer.is_alive()):
                        self._cleanup_observer()
                        current_target = self.target_folder
                        if current_target:
                            self.observer = Observer()
                            self.observer.schedule(self, str(current_target), recursive=True)
                            self.observer.start()
                        self.initial_scan()
                    self._drain_commands()
                    if self.is_running:
                        if time.monotonic() >= next_scan:
                            self.initial_scan()  # Catch pre-existing or missed events.
                            next_scan = time.monotonic() + 3
                        self._process_cooldown_files()
                self._wake.wait(.2)
                self._wake.clear()
        except Cancelled:
            pass
        except Exception as exc:
            self.last_error = str(exc)
            self.is_running = False
            self._report(f'Engine stopped: {exc}', error=True)
        finally:
            self.is_running = False
            self._cleanup_observer()
            signals.status_changed.emit(False)

    def _cleanup_observer(self):
        if self.observer is not None:
            self.observer.stop()
            if self.observer.ident is not None:
                self.observer.join(timeout=5)
            self.observer = None

    def pause(self):
        # Set before acquiring the operation lock so hashing/scanning can cancel.
        self.is_running = False
        self._wake.set()
        signals.status_changed.emit(False)

    def resume(self):
        if not self.target_folder:
            self._report('Choose a folder in Settings before starting.', error=True)
            return False
        if self.stop_event.is_set() or self.last_error:
            self._report('Restart TidyCore after resolving the reported engine error.', error=True)
            return False
        with self._lock:
            self.is_running = True
            self.initial_scan()
        self._wake.set()
        signals.status_changed.emit(True)
        return True

    def stop(self):
        self.is_running = False
        self.stop_event.set()
        self._wake.set()

    def join(self, timeout=15):
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout)
            if self.thread.is_alive():
                raise RuntimeError('Organizer has not stopped; do not start another instance.')

    def request_status(self):
        signals.status_changed.emit(self.is_running)

    def get_health_status(self):
        return {'is_running': self.is_running,
                'observer_alive': bool(self.observer and self.observer.is_alive()),
                'target_folder_exists': bool(self.target_folder and self.target_folder.is_dir()),
                'cooldown_files_count': len(self.cooldown_files), 'error': self.last_error,
                'files_organized_today': self.files_organized_today,
                'files_organized_total': self.files_organized_total}

    def reload_config(self, new_config):
        config = validate_config(new_config)
        self._commands.put(('config', config))
        self._wake.set()

    def request_undo(self, operation_id):
        self._commands.put(('undo', operation_id))
        self._wake.set()

    def _drain_commands(self):
        while not self._commands.empty() and not self.stop_event.is_set():
            command, value = self._commands.get_nowait()
            if command == 'config':
                changed_target = value['target_folder'] != (str(self.target_folder) if self.target_folder else '')
                self._apply_config(value)
                if changed_target:
                    self.is_running = False  # New folder requires explicit Start.
                with self.cooldown_lock:
                    self.cooldown_files.clear()
                    self._snapshots.clear()
                    self._retries.clear()
                signals.status_changed.emit(self.is_running)
                self._report('Settings applied. Start watching when ready.' if changed_target else 'Settings applied.')
            elif command == 'undo':
                ok = self.undo_operation(value)
                signals.command_completed.emit(ok, 'Restored item and excluded its original path from future organization.' if ok else 'Undo failed; see activity for details.')

    def initial_scan(self):
        if not self.target_folder or not self.is_running:
            return
        for path in self.target_folder.iterdir():
            if self.stop_event.is_set() or not self.is_running:
                break
            self._queue_item_for_processing(str(path), reset=False)

    def _top_level(self, path):
        if not self.target_folder:
            return None
        try:
            relative = Path(os.path.abspath(path)).relative_to(self.target_folder)
            return self.target_folder / relative.parts[0] if relative.parts else None
        except ValueError:
            return None

    def _queue_item_for_processing(self, path, reset=True):
        top = self._top_level(path)
        if top is None or not self._should_process(top):
            return
        key = str(top)
        with self.cooldown_lock:
            if reset or key not in self.cooldown_files:
                self.cooldown_files[key] = time.monotonic()
                self._snapshots.pop(key, None)
        self._wake.set()

    def on_created(self, event):
        self._queue_item_for_processing(event.src_path)

    def on_modified(self, event):
        self._queue_item_for_processing(event.src_path)

    def on_moved(self, event):
        self._queue_item_for_processing(event.dest_path)

    def _should_process(self, path):
        p = Path(path)
        if not self.target_folder or p.parent != self.target_folder or not p.exists() or linked(p):
            return False
        if p.name.startswith('.') or p.name.casefold() in self.ignore_list:
            return False
        if p.suffix.casefold() in PARTIAL_EXTENSIONS or p.suffix.casefold() in self.ignore_list:
            return False
        if p.is_dir() and (p.name.casefold() in self.managed_categories
                          or self.db.is_managed_directory(p)
                          or self.config['folder_handling_strategy'] == 'ignore'):
            return False
        # Persistent exclusions include undo and unresolved journal entries.
        return not self.db.is_restored(str(p))

    def _check_cancel(self, require_running=True):
        if self.stop_event.is_set() or (require_running and not self.is_running):
            raise Cancelled()

    def _entries(self, path, require_running=True):
        if linked(path):
            raise ValueError('Symbolic links and junctions are not organized.')
        yield path
        if path.is_dir():
            def walk_error(error):
                raise error
            for root, dirs, files in os.walk(path, followlinks=False, onerror=walk_error):
                self._check_cancel(require_running)
                for name in sorted(dirs + files):
                    child = Path(root) / name
                    if linked(child):
                        raise ValueError('Folder contains a link or junction; leave it in place.')
                    if child.suffix.casefold() in PARTIAL_EXTENSIONS:
                        raise PermissionError('Folder contains an unfinished download.')
                    yield child

    def _snapshot(self, path):
        result = []
        for item in self._entries(path):
            self._check_cancel()
            stat = item.stat()
            result.append((str(item.relative_to(path)), stat.st_size, stat.st_mtime_ns))
        return tuple(result)

    def fingerprint(self, path, require_running=False):
        """Content digest, including directory names and empty folders, for safe undo."""
        path = Path(path)
        digest = hashlib.sha256()
        for item in sorted(self._entries(path, require_running), key=lambda p: str(p.relative_to(path))):
            self._check_cancel(require_running)
            digest.update(('D' if item.is_dir() else 'F').encode())
            digest.update(str(item.relative_to(path)).encode('utf-8'))
            digest.update(b'\0')
            if item.is_file():
                content = hashlib.sha256()
                with item.open('rb') as handle:
                    while chunk := handle.read(1024 * 1024):
                        self._check_cancel(require_running)
                        content.update(chunk)
                digest.update(content.digest())
        return digest.hexdigest()

    def _process_cooldown_files(self):
        with self.cooldown_lock:
            ready = [p for p, since in self.cooldown_files.items() if time.monotonic() - since >= self.cooldown_period]
        for key in ready:
            if not self.is_running or self.stop_event.is_set():
                break
            path = Path(key)
            try:
                if not self._should_process(path):
                    self._forget(key)
                    continue
                snapshot = self._snapshot(path)
                if snapshot != self._snapshots.get(key):
                    with self.cooldown_lock:
                        self._snapshots[key] = snapshot
                        self.cooldown_files[key] = time.monotonic()
                    continue
                self._organize_item(key)
                self._forget(key)
            except Cancelled:
                return
            except (OSError, ValueError) as exc:
                attempts = self._retries.get(key, 0) + 1
                self._retries[key] = attempts
                if attempts == 1 or attempts % 30 == 0:
                    self._report(f'Waiting for {path.name}: {exc}', error=True)
                with self.cooldown_lock:
                    self.cooldown_files[key] = time.monotonic() + min(attempts, 10)

    def _forget(self, key):
        with self.cooldown_lock:
            self.cooldown_files.pop(key, None)
            self._snapshots.pop(key, None)
            self._retries.pop(key, None)

    def _get_category(self, path):
        path = Path(path)
        if path.is_dir():
            if self.config['folder_handling_strategy'] != 'smart_scan':
                return 'Others', None
            counts = {}
            for item in self._entries(path):
                self._check_cancel()
                if item.is_file():
                    category, _ = self._get_category(item)
                    counts[category] = counts.get(category, 0) + 1
            return (max(counts, key=counts.get) if counts else 'Others'), None
        ext = path.suffix.casefold()
        for category, values in self.rules.items():
            if isinstance(values, list) and ext in values:
                return category, None
            if isinstance(values, dict):
                for sub, extensions in values.items():
                    if ext in extensions:
                        return category, None if sub == '__extensions__' else sub
        return 'Others', None

    def _safe_destination(self, directory):
        # Validate every component before mkdir and again immediately before rename.
        relative = directory.relative_to(self.target_folder)
        current = self.target_folder
        if linked(current):
            raise ValueError('Target was replaced by a link.')
        for part in relative.parts:
            current = current / part
            if linked(current):
                raise ValueError('Destination contains a link or junction.')
            current.mkdir(exist_ok=True)
        directory.resolve().relative_to(self.target_folder.resolve())

    def _resolve_conflict(self, destination):
        candidate = destination
        counter = 1
        while os.path.lexists(candidate):
            candidate = destination.with_name(f'{destination.stem} ({counter}){destination.suffix}')
            counter += 1
        return candidate

    def _organize_item(self, path):
        with self._lock:
            source = Path(path)
            if not self._should_process(source):
                return False
            self._check_cancel()
            before = self._snapshot(source)
            category, subcategory = self._get_category(source)
            directory = self.target_folder / category
            if subcategory:
                directory /= subcategory
            self._safe_destination(directory)
            destination = self._resolve_conflict(directory / source.name)
            fingerprint = self.fingerprint(source, require_running=True)
            if before != self._snapshot(source):
                raise PermissionError('Item changed during inspection.')
            self._check_cancel()
            operation_id = self.db.begin_operation(source.name, source, destination, category, subcategory, fingerprint)
            try:
                self._safe_destination(directory)
                self._check_cancel()
                # Windows rename is same-volume and fails if destination exists.
                # No shutil fallback: copying/deleting across volumes is not atomic.
                os.rename(source, destination)
            except BaseException as exc:
                self.db.set_status(operation_id, 'failed', str(exc))
                raise
            # If this commit fails, retain pending row and stop: restart reconciles it.
            self.db.set_status(operation_id, 'completed')
            self._refresh_stats()
            self._report(f'Moved {source.name} → {destination.relative_to(self.target_folder)}')
            signals.file_organized.emit(category)
            return True

    def recover_operations(self):
        for row in self.db.unfinished_operations():
            source, destination = Path(row['source_path']), Path(row['destination_path'])
            undo = row['status'] == 'undo_pending'
            existing = source if undo else destination
            absent = destination if undo else source
            try:
                if existing.exists() and not absent.exists() and row['fingerprint'] and self.fingerprint(existing) == row['fingerprint']:
                    if undo:
                        self.db.complete_undo(row['id'])
                    else:
                        self.db.set_status(row['id'], 'completed')
                elif absent.exists() and not existing.exists() and row['fingerprint'] and self.fingerprint(absent) == row['fingerprint']:
                    self.db.set_status(row['id'], 'completed' if undo else 'failed', 'Recovered: rename was not applied.')
                else:
                    self.db.set_status(row['id'], 'review', 'Interrupted operation has ambiguous paths or changed contents; inspect manually.')
            except (OSError, ValueError) as exc:
                self.db.set_status(row['id'], 'review', str(exc))
        self._refresh_stats()

    def undo_operation(self, operation_id):
        with self._lock:
            try:
                row = self.db.get_operation(operation_id)
                if not row or row['status'] != 'completed':
                    raise ValueError('Select a completed operation.')
                source, original = Path(row['destination_path']), Path(row['source_path'])
                if os.path.lexists(original):
                    raise FileExistsError('Original path is occupied; undo will not overwrite it.')
                if not row['fingerprint']:
                    raise ValueError('Legacy history has no content fingerprint; restore manually.')
                # Refuse traversal through replaced category/target directories.
                for path in (source, *source.parents, original.parent, *original.parent.parents):
                    if linked(path):
                        raise ValueError('Undo path contains a link or junction.')
                if self.fingerprint(source) != row['fingerprint']:
                    raise ValueError('Organized contents have changed; undo requires manual review.')
                self._check_cancel(require_running=False)
                self.db.set_status(operation_id, 'undo_pending')
                try:
                    os.rename(source, original)
                except OSError:
                    self.db.set_status(operation_id, 'completed')
                    raise
                self.db.complete_undo(operation_id)
                self._forget(str(original))
                self._refresh_stats()
                self._report(f'Undone: {original.name}. Original path stays excluded from organization.')
                return True
            except (OSError, ValueError) as exc:
                self._report(f'Cannot undo: {exc}', error=True)
                return False

    def undo_move(self, source_path, original_path):
        # Compatibility for the old folder-decision widget; persisted identity only.
        for row in self.db.get_recent_operations(1000):
            if row['destination_path'] == source_path and row['source_path'] == original_path:
                return self.undo_operation(row['id'])
        return False

    def add_to_ignore_list(self, item_name):
        config = copy.deepcopy(self.config)
        if item_name not in config['ignore_list']:
            config['ignore_list'].append(item_name)
            self.config_manager.save_config(config)
            self.reload_config(config)
            signals.config_changed.emit()

    def _refresh_stats(self):
        self.files_organized_today = self.db.get_today_stats()
        self.files_organized_total = self.db.get_total_stats()
        signals.update_stats.emit(self.files_organized_today, self.files_organized_total)
        signals.activity_changed.emit()

    def _report(self, message, error=False):
        (self.logger.error if error else self.logger.info)(message)
        signals.log_message.emit(('[ERROR] ' if error else '') + message)
        signals.activity_changed.emit()
