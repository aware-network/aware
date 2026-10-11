import os
from pathlib import Path

import pytest
from aware_specification_fs_sdk_adapter import SpecificationFsInputObservationProvider
from aware_specification_fs_sdk_adapter import input_observation as owner
from aware_specification_sdk import (
    SPECIFICATION_INPUT_LIMIT,
    SpecificationInputCleanup,
    SpecificationInputObservationClient,
    SpecificationInputObservationError,
    SpecificationInputObservationRequest,
)


def observe(path, base):
    return SpecificationInputObservationClient(
        SpecificationFsInputObservationProvider()
    ).observe_draft_input(SpecificationInputObservationRequest(str(path), str(base)))


def descriptors():
    return set(os.listdir("/proc/self/fd"))


@pytest.mark.parametrize("size", [0, 1, 65536, SPECIFICATION_INPUT_LIMIT])
def test_original_bytes_limit_and_descriptor_restoration(tmp_path, size):
    body = b"x" * size
    (tmp_path / "input").write_bytes(body)
    before = descriptors()
    result = observe("input", tmp_path)
    assert result.body == body
    assert result.source_ref == str(tmp_path / "input")
    assert result.cleanup is SpecificationInputCleanup.CLOSED
    assert descriptors() == before


@pytest.mark.parametrize("kind", ["missing", "directory", "fifo", "symlink", "large"])
def test_original_refusals_are_typed_and_restore_descriptors(tmp_path, kind):
    source = tmp_path / "input"
    if kind == "directory":
        source.mkdir()
    elif kind == "fifo":
        os.mkfifo(source)
    elif kind == "symlink":
        source.symlink_to(tmp_path / "other")
    elif kind == "large":
        source.write_bytes(b"x" * (SPECIFICATION_INPUT_LIMIT + 1))
    before = descriptors()
    with pytest.raises(SpecificationInputObservationError) as caught:
        observe(source, tmp_path)
    assert caught.value.effect == "none"
    assert descriptors() == before


@pytest.mark.parametrize("fault", [KeyboardInterrupt, SystemExit, OSError])
def test_interrupted_read_preserves_closed_cleanup(tmp_path, monkeypatch, fault):
    source = tmp_path / "input"
    source.write_bytes(b"x")
    before = descriptors()

    def interrupted(*args):
        raise fault("stop")

    monkeypatch.setattr(owner.os, "read", interrupted)
    with pytest.raises(SpecificationInputObservationError) as caught:
        observe(source, tmp_path)
    assert caught.value.cleanup is SpecificationInputCleanup.CLOSED
    assert descriptors() == before


@pytest.mark.parametrize("replacement", [True, False])
def test_original_change_detection(tmp_path, monkeypatch, replacement):
    source = tmp_path / "input"
    source.write_bytes(b"original")
    read = owner.os.read
    changed = False

    def mutate(fd, count):
        nonlocal changed
        body = read(fd, count)
        if body and not changed:
            changed = True
            if replacement:
                other = tmp_path / "other"
                other.write_bytes(b"original")
                other.replace(source)
            else:
                source.write_bytes(b"changed")
        return body

    monkeypatch.setattr(owner.os, "read", mutate)
    before = descriptors()
    with pytest.raises(SpecificationInputObservationError, match="draft_input_changed"):
        observe(source, tmp_path)
    assert descriptors() == before


def test_close_failure_preserves_bytes_and_unknown_cleanup(tmp_path, monkeypatch):
    source = tmp_path / "input"
    source.write_bytes(b"read bytes")
    close = owner.os.close

    def interrupted(fd):
        close(fd)  # Actual disposal occurs, but its observation is interrupted.
        raise KeyboardInterrupt("unverified")

    monkeypatch.setattr(owner.os, "close", interrupted)
    before = descriptors()
    with pytest.raises(SpecificationInputObservationError) as caught:
        observe(source, tmp_path)
    assert caught.value.observed_body_hex == b"read bytes".hex()
    assert caught.value.cleanup is SpecificationInputCleanup.UNKNOWN
    assert caught.value.effect == "unknown"
    assert descriptors() == before


def test_base_is_explicit_not_process_cwd(tmp_path, monkeypatch):
    (tmp_path / "input").write_bytes(b"x")
    monkeypatch.chdir("/")
    assert observe("input", tmp_path).body == b"x"
    with pytest.raises(
        SpecificationInputObservationError, match="base_absolute_required"
    ):
        observe("input", Path("relative"))


def test_parent_symlink_limitation_is_preserved(tmp_path):
    directory = tmp_path / "directory"
    directory.mkdir()
    (directory / "input").write_bytes(b"x")
    (tmp_path / "link").symlink_to(directory, target_is_directory=True)
    assert observe("link/input", tmp_path).body == b"x"


@pytest.mark.parametrize("fault", [KeyboardInterrupt, OSError])
def test_late_result_failure_preserves_original_closed_read(
    tmp_path, monkeypatch, fault
):
    source = tmp_path / "input"
    source.write_bytes(b"observed")
    before = descriptors()

    def fail(*args):
        raise fault("late metadata failure")

    monkeypatch.setattr(owner.metadata, "version", fail)
    with pytest.raises(SpecificationInputObservationError) as caught:
        observe(source, tmp_path)
    assert caught.value.observed_body_hex == b"observed".hex()
    assert caught.value.cleanup is SpecificationInputCleanup.CLOSED
    assert caught.value.effect == "none"
    assert descriptors() == before
