# TidyCore assessment — 2026-11-06

## Baseline and safety

Assessment performed in the existing Windows checkout.
Native Windows, Python 3.12.10, project `.venv`. Git was clean at assessment start.
No existing root database/log was found. Do not launch the unmodified entry point:
it starts the organizer before QApplication and immediately scans the configured
directory. Tests use synthetic directories only; no production startup or updates.

## Prioritized findings before implementation

| Priority | Evidence | Acceptance criterion |
|---|---|---|
| P0 | `utils.py` uses cwd / `_MEIPASS` for config, DB and log. One-file extraction is temporary. | Immutable resources separate from durable per-user state; explicit isolated data-dir option, restart from unrelated cwd preserves data. |
| P0 | Initial scan bypasses cooldown; modifications do not reset it; no moved-event handler. `shutil.move` follows destination semantics and has a check/move collision race. | All arrivals wait for stability, renamed downloads work, partials/links skipped, collision never overwrites or nests into another item, retry locked items. |
| P0 | `pause()` sets the same flag used to end `run()`; `resume()` cannot restart a stopped Python thread. | Pause/resume repeatedly works; shutdown joins worker/observer; cancellation prevents new work. |
| P0 | `reload_config()` changes path without observer rescheduling; cooldown and managed categories stay stale. | Target/rules/cooldown/ignore changes apply together, pending old-target work discarded. |
| P0 | Undo moves blindly, resolves original conflicts to a different name, never writes DB, and watcher immediately sorts restored items again. UI declares success even after failure. | Persisted operation identity, safe undo, no overwrite, restored item survives restart, truthful success/failure. |
| P1 | SQLite exceptions swallowed as success/zero. Connections created per call are not explicitly closed. No migration, integrity/recovery or indexes on history. | Explicit connection lifetime, transactional schema versioning with backup, error propagation, indexed deterministic history, one source of truth for statistics. |
| P1 | Filesystem move precedes DB write; process interruption leaves an untracked move. | Durable pending journal before rename, reconcile interrupted operations conservatively, no false success. |
| P1 | Config overwrites in place; no schema/path validation. Category names can escape target. Source config contains old absolute user path. | Atomic validated settings; safe Windows category components; onboarding starts paused without selecting Downloads. |
| P1 | GUI does not initialize counters/history from persisted operations, chart is not initially drawn, history panel is session-only and folder-only. | Persistent history for files/folders, selected-row undo, honest counts including undone state, clear empty/error state. |
| P1 | Unconditional update check; source updater can rename `sys.executable` (Python); duplicate updater implementations, arbitrary first EXE selection. | No automatic network/install during tests, prevent unsafe self replacement; report update limitation explicitly. |
| P1 | Builder kills processes by name, deletes broad output trees, debug-import build, dozens of speculative hidden imports; release workflows overlap and use obsolete build assumptions. | Deterministic local build with bounded output paths, no process killing, captured log/hash, actual packaged E2E verification. |
| P2 | Large minimum size, gradients/shadows/cards/emojis dominate; right-click-only editor and no focus treatment. Source startup command gets double quotes and failures are swallowed. | Native Qt design tokens, restrained layout, keyboard controls, resizing/DPI verification; startup command correct, disabled in test mode. |

## Functional baseline / claims

The source has flat/mixed category matching and dominant-folder scans, watchdog
events, simple collision suffixes, SQLite aggregate writes, a rules tree, tray
hide/quit, Windows registry startup and two update systems. These exist but do not
establish the README's safety/reliability claims. No tests, migration/recovery,
automatic DB backups, historical trend UI, performance metrics or plugin interface
were found. The two existing GitHub workflows overlap; one calls missing `build.py`, and both use outdated Python/build assumptions. Cross-platform
and ~50 MB claims are unverified. `gui_backup.py` is an empty legacy stub.

## End-to-end contract

Watch/create/rename → debounce + fingerprint stability → validated rule →
non-overwriting rename inside watched volume → persisted journal completion →
history-derived counts → queued Qt refresh → persisted undo with a restoration
exclusion. Folder moves count as one organized item, not their descendant files.
Undone operations remain in history and do not count as currently organized.
Recovery must stop on ambiguous filesystem state rather than guess or delete.

Validation must cover synthetic bytes/hashes, restart, legacy migration, corrupt
DB, transaction failure, collisions, duplicate/renamed events, partial downloads,
locks, pause/resume, retarget, settings, undo/restart, tray/exit and packaged UI.

## Implemented outcome

The baseline reproducer printed `modification_resets_cooldown=False`,
`initial_scan_bypasses_cooldown=True`, and `resume_worker_alive=False`.
Baseline native dashboard/settings screenshots were inspected before UI replacement.
They showed clipped navigation, an oversized empty chart, cramped paths, heavy
gradients and session-only activity. The new design is specified in `DESIGN.md`.

All P0 rows above have implemented fixes and regression or packaged evidence.
The database now uses schema version 2, indexed journal history, explicit closing
of connections, WAL/FULL synchronization, backup before upgrades and conservative
pending-operation reconciliation. Corruption is reported and retained, not repaired
automatically. The old aggregate tables are retained only for legacy inspection.
The new UI takes history and statistics from one SQLite read snapshot and refreshes
local-date totals when the date rolls over.

Settings are atomic and validated, live target changes reschedule watching and
start paused, cancellation and pause no longer terminate the worker, and undo is
content-checked and persisted. Known partial files and reparse links are excluded;
initial files use the same stability path as later events. Windows rename avoids
shutil's overwrite/nesting/cross-volume fallback semantics. Output directories
remain protected after rule changes. A per-user local IPC channel restores a hidden
existing window when its EXE is launched again; one data directory has one worker.

The unsafe updater was retired in favor of a manual official-release link. The
builder now uses bounded unique paths, absolute bundle inputs, a pinned compatible
setuptools, native vector icon, build log and SHA-256; it performs no process killing
or publication. Source and final packaged flows were executed with disposable data.
See `VALIDATION.md` for the actual scope, artifact identity and remaining limits.

## Module coverage

| Area | Assessment / disposition |
|---|---|
| `main.py` | Replaced engine-before-Qt startup and post-GUI infinite loop with explicit CLI isolation, data lock, app lifecycle and joined worker. |
| `database.py` | Replaced swallowed errors, leaked connection lifetimes and drifting aggregates with a recoverable journal; tested migration, concurrency, errors and integrity. |
| `engine.py` | Reworked shared stop/pause flag, event debounce, folder scan, rule reload, conflict move and blind undo; exercised real watchdog and Windows sharing/junction behavior. |
| `config_manager.py`, `utils.py` | Separated immutable resources/user data; safe defaults, schema/path validation, atomic save and previous-file backup. |
| `logger.py`, `signals.py` | Rotating logs with closed replaced handlers; queued Qt activity/status/command signals. |
| `gui.py`, `settings_page.py` | Persistent truthful history, read-snapshot counts, accessible text/actions, explicit palette, resizing and anchored save; fixed temporary top-level Save-button flash. |
| `startup_manager.py` | Correct command quoting, explicit errors, test-mode hard block, deferred application on save; real boot/registry changes intentionally not tested. |
| `updater.py`, `update_manager.py` | Removed unsafe executable replacement and duplicate update logic; manual-update compatibility entry point only. |
| `instance.py` | New scoped local activation channel, partial-request handling and socket timeout; unit and packaged reopening tested. |
| `about_page.py`, `folder_decision_widget.py`, `pie_chart_widget.py`, `update_dialog.py`, `gui_backup.py` | Legacy unused components/stub, inspected and excluded from current entry-point imports. Their older styling/behaviors are not the current UI. |
| `build_release.py` | Replaced broad cleanup/name-based termination and speculative imports with a real validated Windows build and manifest. |
| Unicode/IDNA hook scripts | Historical speculative compatibility workarounds; not used by the new build. |
| `manage_version.py` | Optional cwd-relative maintenance helper, not a runtime/build dependency; version is read from the package by the builder. |
| README/docs/workflows | Corrected unsupported first-run, auto-update, recovery, memory and release-pipeline claims; the duplicate outdated GitHub workflows were replaced with one Windows validation workflow. |

## Primary references consulted

- [PyInstaller runtime paths](https://pyinstaller.org/en/stable/runtime-information.html): `_MEIPASS` is an extraction/resource directory, not durable state.
- [SQLite WAL](https://www.sqlite.org/wal.html) and [PRAGMA reference](https://www.sqlite.org/pragma.html): synchronization, integrity checks and schema versioning.
- [Qt for Python system tray](https://doc.qt.io/qtforpython-6.10/PySide6/QtWidgets/QSystemTrayIcon.html), [signals/slots](https://wiki.qt.io/Qt_for_Python_Signals_and_Slots), and [QLocalServer](https://doc.qt.io/qtforpython-6/PySide6/QtNetwork/QLocalServer.html): native lifecycle and local activation.
- [Setuptools removal of pkg_resources](https://setuptools.pypa.io/en/stable/deprecated/pkg_resources.html): explains the reproduced build dependency failure and compatible toolchain pin.
- [Linear DESIGN.md reference](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/linear.app/DESIGN.md): reviewed token structure and hierarchy; Qt-specific design and palette were authored locally.

## v2.2 release follow-up

The Fluent UI, history search/state filters, tabbed settings, executable version metadata and portable release packaging were added after the original reliability assessment. The earlier report incorrectly described the workflow files as empty; direct inspection confirmed two nonempty, overlapping pipelines. v2.2 consolidates them into Windows validation on main/PRs and an optional manually requested build. Local evidence and machine-specific build logs are excluded from the public repository/package.
