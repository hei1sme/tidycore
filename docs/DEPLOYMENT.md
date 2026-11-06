# Local Windows build

From the existing native Windows checkout, use `.venv\Scripts\python.exe` with
Python 3.12.10. Reconstruct dependencies with `requirements-dev.txt`, run
`python -m pytest -q`, then `python scripts/build_release.py` using that interpreter.

Each build has unique bounded output directories. `BUILD.json`, `SHA256SUMS.txt`
and the build log identify the artifact. See [VALIDATION.md](VALIDATION.md) for
actual test evidence and limitations. A successful PyInstaller command alone
does not establish end-to-end reliability. No publishing/signing step is included.
