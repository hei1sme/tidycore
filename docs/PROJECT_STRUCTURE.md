# Project structure

| Path | Purpose |
|---|---|
| `main.py` | CLI isolation, QApplication, single-instance data lock, engine lifecycle |
| `src/tidycore/instance.py` | User-scoped local activation channel for reopening the same instance |
| `src/tidycore/engine.py` | Watcher, stability queue, safe rename, recovery and undo |
| `src/tidycore/database.py` | Versioned SQLite journal, backups and snapshot statistics |
| `src/tidycore/config_manager.py` | Configuration validation and atomic persistence |
| `src/tidycore/gui.py`, `theme.py` | Fluent-inspired Activity, searchable history, status badges, About and tray |
| `src/tidycore/settings_page.py` | Folder/rules/ignore/stability/startup controls |
| `src/tidycore/startup_manager.py` | Explicit Windows registry integration |
| `src/tidycore/utils.py`, `logger.py`, `signals.py` | Resource/state paths, bounded logs, Qt signals |
| `src/tidycore/updater.py`, `update_manager.py` | Manual-update compatibility aliases; no installer |
| `config/config.json` | Safe bundled defaults; never live user state |
| `assets/tidycore.svg` | Native vector application icon |
| `tests` | Disposable filesystem/SQLite/watcher/Qt regression fixtures |
| `scripts/build_release.py` | Local unique-output PyInstaller build |
| `requirements*.txt` | Pinned Windows environment reconstruction |
| `DESIGN.md`, `docs` | Design, assessment, recovery, verification and handoff |

Older `about_page`, `folder_decision_widget`, `pie_chart_widget`, `update_dialog`
and the empty `gui_backup` are retained as legacy source and are not used by the
current window. Old custom PyInstaller hooks are not invoked by the new builder.
Build/release/work directories, virtual environments, logs and state are ignored.
