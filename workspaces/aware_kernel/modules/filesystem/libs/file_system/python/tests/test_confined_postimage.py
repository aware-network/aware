"""Observed bounded postimages, not namespace sealing or custody approval."""

import hashlib
import os
from dataclasses import FrozenInstanceError

import pytest
from aware_file_system import confined_mutation as native

_CLOSE = os.close


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


class CreationIO:
    """Test capture from the actual original scratch acquisition, not a path."""

    identity = None
    write = staticmethod(os.write)
    fchmod = staticmethod(os.fchmod)
    fsync = staticmethod(os.fsync)
    close = staticmethod(_CLOSE)

    def open(self, *args, **kwargs):
        fd = os.open(*args, **kwargs)
        info = os.fstat(fd)
        self.identity = info.st_dev, info.st_ino
        return fd


@pytest.fixture
def created(tmp_path, request):
    mode = getattr(request, "param", 0o444)
    parent = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    io = CreationIO()
    native._drive_confined_writer(
        native._write_temporary_stream_steps(
            parent_descriptor=parent,
            name="scratch",
            chunks=iter((b"a", b"bc")),
            size_bytes=3,
            content_digest=digest(b"abc"),
            mode=mode,
            _io=io,
        )
    )
    try:
        yield (
            tmp_path,
            {
                "parent_descriptor": parent,
                "leaf": "scratch",
                "expected_identity": io.identity,
                "size_bytes": 3,
                "content_digest": digest(b"abc"),
                "mode": mode,
            },
        )
    finally:
        _CLOSE(parent)


def verify(created, **changes):
    _, kwargs = created
    return native._verify_confined_file_postimage(**(kwargs | changes))


@pytest.mark.parametrize(
    "created", [0o444, 0o555, 0o600, 0o644, 0o700, 0o755], indirect=True
)
def test_original_stream_to_exact_postimage(created):
    _, kwargs = created
    mode = kwargs["mode"]
    result = verify(created)
    assert result.observation.identity == kwargs["expected_identity"]
    assert result.observation.content_digest == digest(b"abc")
    assert result.observation.size_bytes == 3
    assert result.observation.mode == mode
    assert result.observation.read_calls == 2
    assert result.observation.observation_grade == "observed_state"
    assert not hasattr(result.observation, "content")
    assert result.cleanup == native.ConfinedFileReadCleanup("closed", 1, 1, 1)
    os.fstat(kwargs["parent_descriptor"])  # borrowed parent stays owned
    with pytest.raises(FrozenInstanceError):
        result.observation.mode = 0o755


@pytest.mark.parametrize(
    "changes",
    [
        {"leaf": "../scratch"},
        {"leaf": "dir/scratch"},
        {"leaf": "bad\x00"},
        {"leaf": "x" * 1025},
        {"leaf": False},
        {"parent_descriptor": True},
        {"parent_descriptor": -1},
        {"expected_identity": [1, 2]},
        {"expected_identity": (1,)},
        {"expected_identity": (True, 2)},
        {"expected_identity": (1, -2)},
        {"expected_identity": (1, 2**64)},
        {"mode": True},
        {"mode": 0o777},
        {"mode": 0o4755},
        {"mode": 0o1755},
        {"size_bytes": -1},
        {"size_bytes": True},
        {"size_bytes": 256 * 1024 * 1024 + 1},
        {"maximum_chunk_bytes": 0},
        {"maximum_chunk_bytes": True},
        {"maximum_chunk_bytes": 65537},
        {"maximum_read_calls": 0},
        {"maximum_read_calls": True},
        {"maximum_read_calls": 4098},
        {"maximum_read_calls": 1},
        {"content_digest": None},
        {"content_digest": "SHA256:" + "a" * 64},
        {"content_digest": "sha256:" + "A" * 64},
        {"content_digest": "sha256:" + "z" * 64},
        {"size_bytes": 0},
    ],
)
def test_invalid_metadata_has_no_acquisition(created, monkeypatch, changes):
    def forbidden(*args, **kwargs):
        pytest.fail("invalid metadata reached open")

    monkeypatch.setattr(os, "open", forbidden)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created, **changes)
    assert error.value.stage == "validation"
    assert error.value.observation is None
    assert error.value.cleanup == native.ConfinedFileReadCleanup(
        "not_acquired", 0, 0, 0
    )


@pytest.mark.parametrize(
    "change",
    [
        "identity",
        "length",
        "mode",
        "hardlink",
        "fifo",
        "directory",
        "symlink",
        "missing",
    ],
)
def test_wrong_postimage_is_not_read_or_adopted(created, monkeypatch, change):
    root, kwargs = created
    target = root / "scratch"
    changes = {}
    if change == "identity":
        dev, ino = kwargs["expected_identity"]
        changes["expected_identity"] = (dev, ino + 1)
    elif change == "length":
        changes["size_bytes"] = 2
    elif change == "mode":
        target.chmod(0o644)
    elif change == "hardlink":
        os.link(target, root / "alias")
    else:
        target.unlink()
        if change == "fifo":
            os.mkfifo(target)
        elif change == "directory":
            target.mkdir()
        elif change == "symlink":
            (root / "foreign").write_bytes(b"keep")
            target.symlink_to(root / "foreign")

    def forbidden(*args, **kwargs):
        pytest.fail("unmatched postimage reached read")

    monkeypatch.setattr(os, "read", forbidden)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created, **changes)
    assert error.value.observation is None
    assert error.value.cleanup.outcome in {"closed", "not_acquired"}
    if change == "symlink":
        assert (root / "foreign").read_bytes() == b"keep"


def test_hash_mismatch_retains_original_cleanup(created):
    with pytest.raises(native._FilePostimageError) as error:
        verify(created, content_digest=digest(b"xyz"))
    assert error.value.stage == "postimage_digest"
    assert "bytes_mismatch" in str(error.value.primary)
    assert error.value.cleanup == native.ConfinedFileReadCleanup("closed", 1, 1, 1)


def test_stored_content_is_actually_reread(created):
    root, _ = created
    target = root / "scratch"
    target.chmod(0o644)
    target.write_bytes(b"xyz")
    target.chmod(0o444)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.stage == "postimage_digest"


def test_bounded_short_reads_and_eof_probe(created, monkeypatch):
    original = os.read
    requests = []

    def short(fd, amount):
        requests.append(amount)
        return original(fd, min(amount, 1))

    monkeypatch.setattr(os, "read", short)
    result = verify(created, maximum_chunk_bytes=2, maximum_read_calls=4)
    assert result.observation.read_calls == 4
    assert requests == [2, 2, 2, 1]


def test_excess_short_reads_stop_before_another_dispatch(created, monkeypatch):
    original = os.read
    calls = 0

    def short(fd, amount):
        nonlocal calls
        calls += 1
        return original(fd, 1)

    monkeypatch.setattr(os, "read", short)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created, maximum_read_calls=2)
    assert calls == 2
    assert "read_count_exceeded" in str(error.value.primary)
    assert error.value.cleanup.outcome == "closed"


def test_interrupt_preserves_primary_and_closes_once(created, monkeypatch):
    failure = KeyboardInterrupt("read interrupted")
    original_close = os.close
    closes = []

    def interrupted(*args):
        raise failure

    def close(fd):
        closes.append(fd)
        original_close(fd)

    monkeypatch.setattr(os, "read", interrupted)
    monkeypatch.setattr(os, "close", close)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.primary is failure
    assert error.value.__cause__ is failure
    error.value._original_read_ledger.close_all()
    assert len(closes) == 1
    assert error.value.cleanup == native.ConfinedFileReadCleanup("closed", 1, 1, 1)


def test_lost_acquisition_return_stays_unknown(created, monkeypatch):
    original_open = os.open

    def lost(*args, **kwargs):
        fd = original_open(*args, **kwargs)
        _CLOSE(fd)  # test-only disposition; caller cannot infer this knowledge
        raise KeyboardInterrupt("lost open return")

    monkeypatch.setattr(os, "open", lost)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.stage == "postimage_open"
    assert error.value.cleanup.outcome == "unknown"
    assert error.value.cleanup.acquired_count is None


def test_lost_close_return_retains_completed_observation_without_success(
    created, monkeypatch
):
    calls = []

    def lost(fd):
        calls.append(fd)
        _CLOSE(fd)
        raise KeyboardInterrupt("lost close return")

    monkeypatch.setattr(os, "close", lost)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.stage == "cleanup"
    assert error.value.code == "filesystem_postimage_cleanup_unverified"
    assert error.value.observation.content_digest == digest(b"abc")
    assert error.value.cleanup.outcome == "unknown"
    assert error.value.cleanup.closed_count is None
    error.value._original_read_ledger.close_all()
    assert len(calls) == 1


def test_primary_survives_unknown_close(created, monkeypatch):
    def lost(fd):
        _CLOSE(fd)
        raise OSError("lost close")

    monkeypatch.setattr(os, "close", lost)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created, content_digest=digest(b"bad"))
    assert error.value.stage == "postimage_digest"
    assert "bytes_mismatch" in str(error.value.primary)
    assert error.value.cleanup.outcome == "unknown"


def test_cleanup_snapshot_failure_does_not_reclose(created, monkeypatch):
    def fail(*args):
        raise RuntimeError("snapshot unavailable")

    monkeypatch.setattr(native._ReadLedger, "snapshot", fail)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.stage == "cleanup"
    assert error.value.observation is not None
    assert error.value.cleanup.outcome == "unknown"
    assert error.value.cleanup.release_attempted_count == 1
    assert error.value.cleanup.closed_count == 1


def test_mode_change_during_read_refuses(created, monkeypatch):
    root, _ = created
    original = os.read

    def changed(fd, amount):
        value = original(fd, amount)
        (root / "scratch").chmod(0o644)
        return value

    monkeypatch.setattr(os, "read", changed)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.stage == "postimage_stat_after"


def test_leaf_replacement_after_read_is_not_adopted(created, monkeypatch):
    root, _ = created
    original = os.fstat
    calls = 0

    def changed(fd):
        nonlocal calls
        value = original(fd)
        calls += 1
        if calls == 2:
            (root / "scratch").rename(root / "original")
            (root / "scratch").write_bytes(b"abc")
            (root / "scratch").chmod(0o444)
        return value

    monkeypatch.setattr(os, "fstat", changed)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert calls == 2
    assert error.value.stage == "postimage_leaf_correspondence"
    assert (root / "original").read_bytes() == b"abc"
    assert (root / "scratch").read_bytes() == b"abc"


def test_empty_file_single_eof_read(created):
    root, _ = created
    target = root / "scratch"
    target.chmod(0o644)
    target.write_bytes(b"")
    target.chmod(0o444)
    result = verify(
        created, size_bytes=0, content_digest=digest(b""), maximum_read_calls=1
    )
    assert result.observation.size_bytes == 0
    assert result.observation.read_calls == 1


def test_digest_verification_reads_only_bounded_pieces(created, monkeypatch):
    root, _ = created
    target = root / "scratch"
    target.chmod(0o644)
    chunk = b"x" * 65536
    expected = hashlib.sha256()
    with target.open("wb") as stream:
        for _ in range(32):
            stream.write(chunk)
            expected.update(chunk)
    target.chmod(0o444)
    original = os.read
    requests = []

    def read(fd, amount):
        requests.append(amount)
        assert 0 < amount <= 65536
        return original(fd, amount)

    monkeypatch.setattr(os, "read", read)
    result = verify(
        created,
        size_bytes=32 * len(chunk),
        content_digest="sha256:" + expected.hexdigest(),
    )
    assert result.observation.read_calls == len(requests) == 33


@pytest.mark.parametrize("change", ["grow", "shrink", "hardlink"])
def test_mid_read_mutations_fail_without_claiming_seal(created, monkeypatch, change):
    root, _ = created
    original = os.read
    changed = False

    def read(fd, amount):
        nonlocal changed
        if not changed:
            changed = True
            target = root / "scratch"
            if change == "hardlink":
                os.link(target, root / "alias")
            else:
                target.chmod(0o644)
                with target.open("ab" if change == "grow" else "wb") as stream:
                    stream.write(b"d" if change == "grow" else b"a")
                target.chmod(0o444)
        return original(fd, amount)

    monkeypatch.setattr(os, "read", read)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert changed
    assert error.value.observation is None
    assert error.value.cleanup.outcome == "closed"


def test_effective_uid_drift_refuses(created, monkeypatch):
    uid = os.geteuid()
    calls = 0

    def identity():
        nonlocal calls
        calls += 1
        return uid if calls == 1 else uid + 1

    monkeypatch.setattr(os, "geteuid", identity)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.stage == "postimage_stat_after"


def test_wrong_owner_metadata_refuses(created, monkeypatch):
    original = os.fstat

    def owner(fd):
        fields = list(original(fd))
        fields[4] += 1
        return os.stat_result(fields)

    monkeypatch.setattr(os, "fstat", owner)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.stage == "postimage_stat_before"
    assert error.value.cleanup.outcome == "closed"


def test_cleanup_boundary_interruption_finishes_unspent_rights(created, monkeypatch):
    def interrupted(*args):
        raise KeyboardInterrupt("drain interrupted before dispatch")

    monkeypatch.setattr(native._ReadLedger, "close_all", interrupted)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.stage == "cleanup"
    assert error.value.observation is not None
    assert error.value.cleanup.outcome == "unknown"
    assert error.value.cleanup.release_attempted_count == 1
    assert error.value.cleanup.closed_count == 1


@pytest.mark.parametrize(
    "target", ["_FilePostimageObservation", "_FilePostimageVerification"]
)
def test_result_construction_failure_keeps_original_evidence(
    created, monkeypatch, target
):
    failure = MemoryError("result allocation")

    def fail(*args):
        raise failure

    monkeypatch.setattr(native, target, fail)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert error.value.primary is failure
    assert error.value.cleanup == native.ConfinedFileReadCleanup("closed", 1, 1, 1)
    assert error.value.stage == (
        "result" if target == "_FilePostimageVerification" else "postimage_result"
    )
    assert (error.value.observation is not None) == (
        target == "_FilePostimageVerification"
    )


@pytest.mark.parametrize("primitive", ["O_NOFOLLOW", "O_NONBLOCK"])
def test_missing_secure_primitive_refuses_before_io(created, monkeypatch, primitive):
    monkeypatch.delattr(os, primitive)
    with pytest.raises(native._FilePostimageError) as error:
        verify(created)
    assert isinstance(error.value.primary, NotImplementedError)
    assert error.value.cleanup == native.ConfinedFileReadCleanup(
        "not_acquired", 0, 0, 0
    )
