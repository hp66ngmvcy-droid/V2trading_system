from pathlib import Path
import pytest
from scripts import market_data_io as io


def paths(tmp_path):
    (tmp_path / 'data/validated').mkdir(parents=True)
    a, b = tmp_path / 'raw', tmp_path / 'validated'
    a.write_bytes(b'old-a')
    b.write_bytes(b'old-b')
    return a, b


def test_commit_installs_pair(tmp_path):
    a, b = paths(tmp_path)
    io.commit_files(tmp_path, 'BTCUSD', {a:b'new-a', b:b'new-b'}, {a:io.sha(b'old-a'), b:io.sha(b'old-b')})
    assert a.read_bytes() == b'new-a' and b.read_bytes() == b'new-b'
    with io.data_lock(tmp_path, 'BTCUSD'):
        pass


def test_concurrent_change_rejected(tmp_path):
    a, b = paths(tmp_path)
    with pytest.raises(RuntimeError, match='Concurrent'):
        io.commit_files(tmp_path, 'BTCUSD', {a:b'new'}, {a:'wrong'})
    assert a.read_bytes() == b'old-a'


def test_interrupted_pair_blocks_reader_and_retains_backups(tmp_path, monkeypatch):
    a, b = paths(tmp_path)
    original = io.os.replace
    def fail_second(src, dst):
        if Path(dst) == b:
            raise OSError('injected interruption')
        original(src, dst)
    monkeypatch.setattr(io.os, 'replace', fail_second)
    with pytest.raises(OSError):
        io.commit_files(tmp_path, 'BTCUSD', {a:b'new-a', b:b'new-b'}, {a:io.sha(b'old-a'), b:io.sha(b'old-b')})
    assert a.read_bytes() == b'new-a' and b.read_bytes() == b'old-b'
    with pytest.raises(RuntimeError, match='interrupted'):
        with io.data_lock(tmp_path, 'BTCUSD'):
            pass
    assert list(tmp_path.glob('.raw.*'))
    monkeypatch.setattr(io.os, 'replace', original)
    assert io.recover_files(tmp_path, 'BTCUSD')
    assert a.read_bytes() == b'old-a' and b.read_bytes() == b'old-b'
    assert not io.recover_files(tmp_path, 'BTCUSD')
