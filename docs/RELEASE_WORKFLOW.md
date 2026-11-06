# Local artifact workflow

1. Run the isolated regression suite from the Windows `.venv`.
2. Build with `scripts/build_release.py`.
3. Launch the generated EXE with `--data-dir <absolute-fixture-dir> --test-mode`.
4. Exercise moves, hashes, settings, restart, undo, tray and clean exit. Inspect
   the actual executable UI at ordinary and reduced sizes and non-default DPI.
5. Record artifact path/hash, environment, results and unresolved limits in
   [VALIDATION.md](VALIDATION.md).

Publication, Git tags, remote pushes, signing purchases and GitHub releases are
separate explicit actions. Windows regression checks run on main pushes and pull requests; workflow_dispatch additionally builds a portable artifact. Release publication remains an explicit action.
