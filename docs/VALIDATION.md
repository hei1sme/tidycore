# Windows validation — v2.2.1

The startup patch adds three regression cases for saved targets overlapping the
downloaded executable, resources and state directory. Each constructs the Qt
window offscreen, verifies Settings remains accessible while watching is disabled,
checks persisted history and byte-for-byte settings preservation, and confirms
unsafe saves and unrelated invalid settings remain rejected. Interactive desktop
inspection is deferred at the user's request; the v2.2.0 inspection below remains
the visual baseline.

Validation uses Python 3.12.10, PySide6 6.9.1, watchdog 6.0.0, SQLite and a
project-local native Windows `.venv`. PyInstaller 6.14.1 / hooks 2025.5 and
setuptools 80.9.0 form the pinned build toolchain.

## Regression coverage

Run `& .\.venv\Scripts\python.exe -m pytest -q` and `-m pip check`.
The suite covers real watcher events, debounce and download renames, pause/resume,
retargeting, shutdown, exclusive Windows locks, collision races, real junctions,
byte preservation, persisted undo and exclusions, concurrent SQLite writes,
migration backups, query indexes, corrupt/newer databases and interrupted journal
recovery. Qt tests cover persisted metrics, rule validation, search/state filters,
undo identity after filtering, error-log expansion, startup isolation and local
single-instance activation.

## Native inspection

Source and packaged flows use synthetic files in explicit isolated data directories.
No personal Downloads, synced or school folders are used. No real startup entries
or automatic updates are enabled. Screenshots in `assets/screenshots` show actual
Qt windows and synthetic activity, not fabricated metrics.

The release check includes startup, real moves and collisions, exact contents,
settings roundtrip, search/filters, undo, restart persistence, close-to-tray,
background moves, reopening the same instance, explicit exit, minimum sizing and
125% process-local Qt scaling. Asset identities and source hashes are recorded in
the release `BUILD.json`; executable SHA-256 is in `SHA256SUMS.txt`.

## Limits

The EXE is unsigned. Tests on one Windows environment do not certify other machines
or operating systems. Actual Windows login/startup writes are not tested; quoting
and isolation guards are. Updates are manual. Physical power cuts, network shares,
cloud sync, alternate data streams, hostile concurrent path changes and large-folder
performance are not validated. Crash tests inject failures at journal boundaries.
Undo exclusions persist without a reset UI, and legacy rows without fingerprints
require manual restoration. Counts summarize journal state rather than disk inventory.

## Release outcome

- **37 automated tests passed** in the final native Windows run (21.57 seconds).
  `pip check` and `git diff --check` passed.
- Source and EXE were visually inspected. Real fixture checks covered collision
  preservation, download rename, search/filtered undo, settings, live retarget,
  tray/background organization, instance reopening, restart and clean exit.
- Final fixture state: **12 files with exact bytes verified**, **11 journal rows**,
  **9 completed / 2 undone**, SQLite integrity check `ok`. Restored exclusions
  survived restart. No production autostart or automatic updates were enabled.
- Inspected the final EXE at normal and 125% process scaling. At the 860×600 Qt
  client minimum, compact mode hides the secondary metrics strip and keeps
  selected records, path tooltips and Undo visible. Added a regression test for
  the compact-selection clipping found during inspection.
- Windows executable metadata reports ProductVersion **2.2.0** and description
  **TidyCore file organizer**.
- EXE SHA-256: `2446ec8b2e15ed7d7decf22b697f3246a919cbf9514385a60f6f73b1003b3a56`.

An earlier packaged candidate exercised the full organization sequence; the final
candidate then verified restart/persistence and the compact-layout fix. The only
application differences were responsive presentation and elided path details.
Published screenshot examples are synthetic local activity from the final EXE.
