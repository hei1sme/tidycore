# State, migration and recovery

Close every instance before manually copying or replacing state. The active
directory is `%LOCALAPPDATA%\TidyCore` unless `--data-dir` or `TIDYCORE_DATA_DIR`
explicitly overrides it. The About page shows the actual directory.

## Back up

For an offline backup, close the app and copy the entire state directory. If WAL
files remain, preserve them alongside the DB. An online backup must use SQLite's
backup API, not a copy of just the main DB file. `StatisticsDatabase.backup()` uses
that API. Automatic backups are made **before schema upgrades**, not periodically.

## Legacy schema

Schema version 0 (2.0.1) receives additive journal fields and indexes. Version 2
also remembers category output directories so later rule edits cannot turn them
back into inputs. A timestamped `.backup-*` is created before upgrading an
existing database; the migration runs in a transaction. Legacy aggregate tables
remain unchanged for inspection, but journal rows drive the current UI. If old
aggregate totals disagree with detailed history, current counts follow history.
Legacy UTC timestamps are assigned local dates during migration; pre-existing
history lacks fingerprints and cannot safely offer automatic undo.

## Interrupted operations

`pending` is committed before an organization rename, and `completed` afterward.
Undo similarly uses `undo_pending` followed by `undone` plus a persistent original
path exclusion in the same DB transaction. On restart, a single surviving path
with the recorded content fingerprint determines whether the rename took place.
Both paths, neither path, changed contents or unreadable data result in `review`.
Nothing is deleted or guessed. Inspect the row paths, error and actual contents;
take an offline backup before any manual resolution. Review paths stay excluded.

Failed rename attempts remain in history as `failed`, and locked items retry.
Failure to commit after a rename stops the worker, preserving the pending record
for reconciliation. Pending/review/failed operations do not count as organized.

## Corruption / newer schema

Startup fails visibly if SQLite integrity checking fails, the file cannot be
opened, or its schema version is newer. The original file is not overwritten.
Keep the failing directory and log. Verify a backup with SQLite `PRAGMA
integrity_check`, then restore it **offline** to a separate data directory first.
Inspect paths before starting the organizer. Do not assume restoring a database
also restores the physical files: the filesystem and journal must agree.

Backups created before migration retain their original schema; a newer app may
migrate a copy again. Retain both the original and backup until validation ends.
