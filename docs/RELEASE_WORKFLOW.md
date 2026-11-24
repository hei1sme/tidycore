# Local artifact workflow

1. Run the isolated regression suite from the Windows `.venv`.
2. Build with `scripts/build_release.py`.
3. Launch the generated EXE with `--data-dir <absolute-fixture-dir> --test-mode`.
4. Exercise moves, hashes, settings, restart, undo, tray and clean exit. Inspect
   the actual executable UI at ordinary and reduced sizes and non-default DPI.
5. Record artifact path/hash, environment, results and unresolved limits in
   [VALIDATION.md](VALIDATION.md).

## Update checks and installation

The checker reads metadata from the repository's [latest published stable release](https://docs.github.com/en/rest/releases/releases#get-the-latest-release).
About can check on demand. The startup check requires an explicit preference
and both checks are disabled in isolated test mode. Downloads are manual.

Before enabling self-installation, establish a maintainer-controlled signing key
and release signing process, and ship a trusted public key or pinned publisher
identity in the client. A checksum served alongside an unsigned executable can
verify integrity against a known value. A compromised release can replace both.
The signed update metadata must bind the intended version, platform and artifact.
Verify that interrupted replacement or a failed launch restores the known-good
executable using disposable signed packages before enabling installation.

Publication, Git tags, remote pushes, signing purchases and GitHub releases are
separate explicit actions. Windows regression checks run on main pushes and pull requests; workflow_dispatch additionally builds a portable artifact. Release publication remains an explicit action.
