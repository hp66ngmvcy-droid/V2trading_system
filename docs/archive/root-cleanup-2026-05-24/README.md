# Root Cleanup Archive - 2026-05-24

This folder contains root-level files moved during the safe cleanup pass.

The cleanup goal was to make the repository root easier for humans and agents
to scan while preserving old reports, notes, logs, and stray files.

## Moved Here

- One-off markdown reports and summaries
- Old validation/audit/completion notes
- Root log/planning files
- Stray empty or accidental root files

## Not Moved Here

The accidental SSH key pair found in the root was moved to:

```text
.local_private/root-key-cleanup-2026-05-24/
```

That path is ignored by git. If this repository has ever been pushed with those
key files tracked, rotate that SSH key and remove it from git history before
sharing the repository.

See `SSH_KEY_CLEANUP_NOTE.md` for the required follow-up.
