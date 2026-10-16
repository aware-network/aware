"""Original C target reads; no tree effects or substitute physical writer."""

import hashlib
import os

import pytest
from aware_workspace_fs_adapter.repository_source_projection import (
    FilesystemSourceProjectionPort,
)
from aware_workspace_sdk.repository_tree_projection_codec import (
    WorkspaceTreeProjectionValueError,
    repository_tree_projection_value_to_json,
)


@pytest.fixture
def port(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "tree-read-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    root = tmp_path / "root"
    root.mkdir()
    return FilesystemSourceProjectionPort(
        repository_root=root,
        state_root=tmp_path / "state",
        execution_id="codex-tree-read-test",
    )


def test_original_modes_bytes_and_directory_stat_are_retained(port):
    path = port.root / "script.py"
    path.write_bytes(b"print(1)\n")
    path.chmod(0o755)
    result = port.read_tree_entry("script.py")
    assert result.body == path.read_bytes()
    assert result.entry.mode == 0o755 and result.entry.link_count == 1
    assert (
        result.entry.content_digest
        == "sha256:" + hashlib.sha256(result.body).hexdigest()
    )
    (port.root / "directory").mkdir(mode=0o750)
    directory = port.read_tree_entry("directory")
    assert directory.body is None and directory.entry.content_digest is None
    assert directory.entry.mode == 0o750
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_json(result)


@pytest.mark.parametrize("path", ["absent", "new/absent", "new/deep/absent"])
def test_missing_parent_and_leaf_are_typed_absence_not_implicit_creation(port, path):
    result = port.read_tree_entry(path)
    assert not result.entry.exists and result.body is None
    assert not list(port.root.iterdir())


def test_16mib_profile_does_not_expand_v0_reader(port):
    path = port.root / "large"
    data = b"x" * (5 * 1024 * 1024)
    path.write_bytes(data)
    assert port.read_tree_entry("large").body == data
    with pytest.raises(ValueError):
        port.read_source("large")
    with pytest.raises(ValueError):
        port.read_tree_entry("large", maximum_bytes=4 * 1024 * 1024)


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_nonregular_and_aliased_leaves_refuse_before_body_read(port, kind):
    original = port.root / "original"
    original.write_text("content")
    leaf = port.root / "bad"
    if kind == "symlink":
        leaf.symlink_to(original)
    elif kind == "hardlink":
        os.link(original, leaf)
    else:
        os.mkfifo(leaf)
    with pytest.raises(ValueError):
        port.read_tree_entry("bad")


def test_65_component_path_uses_constant_descriptor_footprint(port, monkeypatch):
    parts = ["a"] * 65
    path = port.root
    for part in parts[:-1]:
        path = path / part
        path.mkdir()
    (path / parts[-1]).write_bytes(b"body")
    original = os.open
    live = set(os.listdir("/proc/self/fd"))
    peaks = []

    def opened(*args, **kwargs):
        result = original(*args, **kwargs)
        peaks.append(len(set(os.listdir("/proc/self/fd")) - live))
        return result

    monkeypatch.setattr(os, "open", opened)
    assert port.read_tree_entry("/".join(parts)).body == b"body"
    assert max(peaks) <= 3 and set(os.listdir("/proc/self/fd")) == live


@pytest.mark.parametrize("phase", ["read", "fstat"])
def test_acquisition_and_read_interruptions_release_every_descriptor(
    port, monkeypatch, phase
):
    (port.root / "file").write_bytes(b"body")
    before = set(os.listdir("/proc/self/fd"))
    interruption = KeyboardInterrupt("interrupted original read")

    def interrupt(*args, **kwargs):
        raise interruption

    monkeypatch.setattr(os, phase, interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        port.read_tree_entry("file")
    assert caught.value is interruption and set(os.listdir("/proc/self/fd")) == before


def test_late_close_failure_preserves_interruption_and_releases_other_originals(
    port, monkeypatch
):
    (port.root / "file").write_bytes(b"body")
    original_close, original_read = os.close, os.read
    interruption = KeyboardInterrupt("original read")
    calls = []

    def read(*args, **kwargs):
        raise interruption

    def close(descriptor):
        calls.append(descriptor)
        original_close(descriptor)
        if len(calls) == 1:
            raise OSError("cleanup report lost after close")

    before = set(os.listdir("/proc/self/fd"))
    monkeypatch.setattr(os, "read", read)
    monkeypatch.setattr(os, "close", close)
    with pytest.raises(KeyboardInterrupt) as caught:
        port.read_tree_entry("file")
    assert (
        caught.value is interruption
        and "tree_read_cleanup_unknown" in caught.value.__notes__
    )
    assert len(calls) == 2 and len(set(calls)) == 2
    monkeypatch.setattr(os, "read", original_read)
    assert set(os.listdir("/proc/self/fd")) == before
