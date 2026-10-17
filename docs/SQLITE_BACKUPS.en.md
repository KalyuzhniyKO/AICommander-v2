# Preparation #22: verifiable SQLite backup/restore

[Русский](SQLITE_BACKUPS.md) · [Issue #22](https://github.com/KalyuzhniyKO/AICommander-v3/issues/22)

`python -m backend.app.storage.backup` is an explicit stdlib-only offline tool for
AICommander/budget state. It does not read .env, discover databases, start the app,
run migrations/models/recovery or change installed services.

On your own existing **test** database, with an explicit workspace:

```bash
mkdir -p .aicommander-backups
python -m backend.app.storage.backup create --root . --source fixture.sqlite3 --output .aicommander-backups/state.aic-backup.zip
python -m backend.app.storage.backup verify --root . --source .aicommander-backups/state.aic-backup.zip
python -m backend.app.storage.backup restore --root . --source .aicommander-backups/state.aic-backup.zip --output restored-new.sqlite3
```

Success returns exit0/JSON verified=true. Failure returns exit2/static code without
paths, SQL, row data or raw exception text. Output parents must already exist.
Defaults: 30 seconds and 256 MiB; bounds 1–120 seconds and 1 byte–1 GiB. Progress
checks cover backup, SQL and streamed reads/hashes, not uninterruptible OS I/O.

Snapshot v1 is an uncompressed ZIP with exactly state.sqlite3/manifest.json. No
extractall, ZIP64, comments, arbitrary paths or compressed members. Directory
counts/size are checked before ZipFile allocation. Member types, CRC/size, JSON
keys, SHA-256 and derived metadata are checked. Manifest exposes versions/counts
and unresolved-state counts, not paths or task/model text.

SQLite Connection.backup includes committed WAL data. The copied database switches
to DELETE journal mode and passes integrity/FK/schema checks; the archive is read
back before publication. Verify/restore repeat checks. Supported schemas: legacy
app, taskflow migrations 1/2/3, panel1, budget1. Partial/future schemas fail closed.
No automatic migration. Separate app/budget files do not form one snapshot
transaction; stop all writers before copying them as a coordinated set. Use matching
app/tool versions. Hash/CRC establish
integrity, not authenticity; use trusted backups only. A snapshot is a point in
time, not replication of future writes.

Resolved paths stay inside an explicit workspace, including Windows junction redirects; parent traversal, symlink components,
source WAL/SHM/journal symlinks, hardlink sources, home/root scope and existing outputs are rejected. This is not
an OS sandbox against the workspace owner. Private staging on the destination
filesystem, file fsync and exclusive hardlink publication prevent overwrites.
Unsupported hardlink filesystems fail without an unsafe fallback. POSIX mode is
0600; Windows directory ACLs still matter. Cross-platform power-loss/directory
persistence is not guaranteed. Rare cleanup failures after publication may leave
a complete artifact; verify before retrying.

Restore writes a new filename only, rejecting existing files and stale WAL/SHM/
journal sidecars. It never changes DATABASE_URL or replaces a working database.
The full SQLite content is private, unredacted data; ZIP is not encrypted.
Standalone .env, SSH keys, Git or Hermes/OmniRoute/model configuration files are
not added. Gitignore excludes conventional snapshot/SQLite/sidecar names, but
still review every commit.

Rows/IDs/versions, v1/v2 artifacts/provenance, idempotency, operations and budget
reservations survive unchanged. Running/result_ready/unknown and budget reserved/
dispatched/unknown are not marked successful, retried or refunded. Recovery flags
are stored-state warnings, not process-liveness checks. **Stop the application and
all workers, including workers using the original database, before using a
restored file.** Two copies are independent and could duplicate external effects.
Review [operation recovery](OPERATIONS.en.md) and [budget limits](BUDGETS.en.md)
explicitly. A snapshot can predate an already completed external call, rolling
back idempotency/claim records. Stopping workers alone does not make reserved or
missing operations safe to send again. Restore always returns
external_effects_reconciliation_required=true, even if the snapshot has no unresolved
rows. Reconcile with trusted external receipts/billing before resuming; snapshot
restoration does not establish inference/billing outcomes.

[QA](qa-issue-22-backup.json) · [Synthetic manifest example](contracts/sqlite-backup-v1.example.json).
Tests use actual temporary SQLite/WAL, a concurrent writer and subprocess CLI,
covering schema/artifact preservation, unknown/budget fences, corruption/checksums,
path/archive guards, no overwrite, publication races, limits and cleanup.

Full #22 remains open for clean Zorin installation/update/rollback, protected
MacBook access, operational health/metrics and owner acceptance. This preparation
adds no deployment, systemd/Compose unit, scheduled backup or Zorin access.
