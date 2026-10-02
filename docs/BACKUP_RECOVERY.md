# Backup & Recovery (RPO/RTO honest)

- RPO: MySQL `mysqldump --single-transaction` via cron (see
  `deploy/scripts/backup.sh`); 14-day retention. SQLite dev: file copy.
- RTO: minutes (restore dump + restart services).
- Restore: `bash deploy/scripts/restore.sh <backup-dir>` (DB + config +
  service restart). Verify with `status.sh` + dashboard counts.
- Restore smoke test: `tests/integration/test_backup_restore.py`
  (snapshot → mutate → restore → exact state). Run it in CI.
- Secrets strategy: `.env` is in `config.tar.gz`; production `.env` must live
  outside webroot backups with restricted permissions; rotate `SECRET_KEY`
  invalidates login tokens (by design), `CREDENTIALS_KEY` rotation requires
  re-encrypting stored secrets (Fernet supports multi-key in code on request).
