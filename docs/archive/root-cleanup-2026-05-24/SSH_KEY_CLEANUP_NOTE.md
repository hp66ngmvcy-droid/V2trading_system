# SSH Key Cleanup Note - 2026-05-24

## What Was Found

During the root cleanup, two accidental root-level files were identified as an
OpenSSH key pair:

```text
eval "$(ssh-agent -s)"
eval "$(ssh-agent -s)".pub
```

These filenames look like a shell command was accidentally used as a file name.

## What Was Done

The files were moved out of the repository root into:

```text
.local_private/root-key-cleanup-2026-05-24/
```

The `.local_private/` folder was added to `.gitignore` so future local private
cleanup material is not accidentally added.

## Important Risk

Git still reports these files as tracked/deleted, which means the key files were
already known to the repository history before this cleanup.

If this repository has ever been pushed, shared, zipped, backed up externally,
or exposed to another machine, treat that key as compromised.

## Required Follow-Up

1. Rotate/revoke the SSH key before using it again.
2. Remove the old key from any GitHub, server, or service account where it was
   added.
3. Commit the deletion of the tracked key files.
4. If the repo was pushed/shared, consider removing the key from git history
   before making the repo public or sharing it further.

## Do Not Do

- Do not move these files back to the repo root.
- Do not commit files from `.local_private/`.
- Do not reuse the private key after exposure risk.
