# TidyCore development

- Native Windows Python/PySide6 desktop application. Keep the stack and existing
  checkout unless a migration is requested. Preserve uncommitted source edits.
- Runtime: Python 3.12.10, project `.venv\Scripts\python.exe`; dependencies in
  `requirements.txt` and `requirements-dev.txt`. Never reuse Linux environments.
- Read `README.md`, `DESIGN.md`, `docs/ASSESSMENT.md` and `docs/VALIDATION.md`.
- Reconstruct: `& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`.
  Verify with `-m pytest -q` and `-m pip check` using that interpreter.
- Build: `& .\.venv\Scripts\python.exe scripts/build_release.py`. Keep unique
  build outputs and logs. Never kill processes by name or broadly delete builds.
- Run tests only with disposable files, config and databases. Native UI testing
  uses `--data-dir <isolated-directory> --test-mode`; watch targets must be inside
  that directory. Never organize personal or synced folders as fixtures.
- First launch is paused. Do not enable real autostart or automatic updates during
  testing. Back up real state before any explicitly requested migration.
- Inspect source and the actual packaged EXE. Verify byte preservation, restart,
  settings, undo, tray/exit, focus and resizing. A build alone is insufficient.
- Keep writable state separate from bundled resources; preserve journal/rename
  recovery consistency. Metrics describe recorded operations, not a live inventory.
- Use the computer-use skill for native inspection when available. Update design
  tokens before substantial visual work. No web-stack rewrite for styling.
- Public docs/assets must contain synthetic examples, not private state, credentials
  or machine-specific build logs. Keep local diagnostic evidence under `work/`.
- Publication, tags and remote pushes require explicit user intent. Do not purchase
  signing, APIs or paid services without explicit authorization.
