"""Journaled file replacement for the M15 extension and guarded replay readers."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _stage(path, data):
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return Path(name)


@contextmanager
def data_lock(root, symbol, exclusive=False):
    directory = Path(root) / 'data/validated'
    with (directory / f'.{symbol}_M15.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        if (directory / f'.{symbol}_M15.pending.json').exists():
            raise RuntimeError(f'{symbol}: interrupted update; inspect pending journal before recovery')
        yield


def read_frame(root, symbol):
    import pandas as pd
    with data_lock(root, symbol):
        return pd.read_parquet(Path(root) / 'data/validated' / f'{symbol}_M15.parquet')


def commit_files(root, symbol, outputs, expected):
    """Atomic per-file replacements; journal blocks guarded readers on interruption.

    This is not a filesystem-wide multi-file transaction. Other readers must use
    data_lock/read_frame to avoid observing a partially installed generation.
    """
    journal = Path(root) / 'data/validated' / f'.{symbol}_M15.pending.json'
    with data_lock(root, symbol, exclusive=True):
        for path, old_hash in expected.items():
            actual = sha(path.read_bytes()) if path.exists() else None
            if actual != old_hash:
                raise RuntimeError(f'Concurrent source change: {path.name}')
        entries = []
        for path, data in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            backup = _stage(path, path.read_bytes()) if path.exists() else None
            staged = _stage(path, data)
            entries.append(dict(path=str(path), staged=str(staged),
                                backup=str(backup) if backup else None,
                                before=expected[path], after=sha(data)))
            _sync_dir(path.parent)
        with journal.open('x') as stream:
            json.dump({'symbol': symbol, 'files': entries}, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        _sync_dir(journal.parent)
        # On failure leave the journal and backups intact; never guess recovery.
        for entry in entries:
            os.replace(entry['staged'], entry['path'])
            _sync_dir(Path(entry['path']).parent)
        journal.unlink()
        _sync_dir(journal.parent)
        for entry in entries:
            if entry['backup']:
                Path(entry['backup']).unlink()


def recover_files(root, symbol):
    """Explicit rollback of a pending generation; refuses unknown file changes."""
    root = Path(root).resolve()
    directory = root / 'data/validated'
    journal = directory / f'.{symbol}_M15.pending.json'
    with (directory / f'.{symbol}_M15.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not journal.exists():
            return False
        entries = json.loads(journal.read_text())['files']
        for entry in entries:
            for key in ('path', 'backup', 'staged'):
                if entry[key] and root not in Path(entry[key]).resolve().parents:
                    raise ValueError('Recovery path escapes project')
            path = Path(entry['path'])
            current = sha(path.read_bytes()) if path.exists() else None
            if current not in (entry['before'], entry['after']):
                raise RuntimeError('Recovery refused: file changed outside transaction')
            if entry['backup'] and sha(Path(entry['backup']).read_bytes()) != entry['before']:
                raise RuntimeError('Recovery backup hash mismatch')
        for entry in entries:
            path = Path(entry['path'])
            if entry['backup']:
                staged = _stage(path, Path(entry['backup']).read_bytes())
                os.replace(staged, path)
            elif path.exists():
                path.unlink()
            _sync_dir(path.parent)
        journal.unlink()
        _sync_dir(directory)
        for entry in entries:
            for key in ('backup', 'staged'):
                if entry[key]:
                    Path(entry[key]).unlink(missing_ok=True)
        return True
