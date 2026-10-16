"""Original physical read/lifetime proofs, not SPEC presentation or installation."""

from __future__ import annotations

import errno
import hashlib
import inspect
import os
import tomllib
from dataclasses import fields, replace
from pathlib import Path

import aware_file_system as facade
import aware_file_system.confined_mutation as owner
import pytest

PORT = owner.observe_confined_file_with_cleanup


@pytest.fixture
def source(tmp_path):
    directory = tmp_path / "parent"
    directory.mkdir()
    (directory / "capture.json").write_bytes(b'{"result":"recorded"}\n')
    return tmp_path, "parent/capture.json"


def _track(monkeypatch):
    original_open, original_close = os.open, os.close
    acquired, releases = [], []

    def opened(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        acquired.append(descriptor)
        return descriptor

    def closed(descriptor):
        releases.append(descriptor)
        return original_close(descriptor)

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "close", closed)
    return acquired, releases


def test_original_facade_reexports_additive_port_and_values():
    for name in (
        "ConfinedFileReadCleanup",
        "ConfinedFileObservationWithCleanup",
        "ConfinedFileObservationError",
        "observe_confined_file_with_cleanup",
    ):
        assert getattr(facade, name) is getattr(owner, name)
        assert name in facade.__all__


def test_original_legacy_observer_signature_is_unchanged():
    signature = inspect.signature(owner.observe_confined_file)
    assert tuple(signature.parameters) == ("root", "path", "maximum_bytes")
    assert all(
        p.kind is inspect.Parameter.KEYWORD_ONLY for p in signature.parameters.values()
    )


def test_cleanup_value_and_result_fields_match_supplier_shapes():
    assert tuple(f.name for f in fields(owner.ConfinedFileReadCleanup)) == (
        "outcome",
        "acquired_count",
        "release_attempted_count",
        "closed_count",
        "diagnostics",
    )
    assert tuple(f.name for f in fields(owner.ConfinedFileObservationWithCleanup)) == (
        "observation",
        "root_locator",
        "path",
        "cleanup",
        "observation_grade",
        "confinement_profile",
    )


def test_exact_read_and_once_only_original_close_returns(source, monkeypatch):
    root, path = source
    legacy = owner.observe_confined_file(root=root, path=path)
    with monkeypatch.context() as patch:
        acquired, releases = _track(patch)
        result = PORT(root=root, path=path)
    assert result.observation == legacy
    assert result.observation.content == (root / path).read_bytes()
    assert (
        result.observation.content_digest
        == "sha256:" + hashlib.sha256(result.observation.content).hexdigest()
    )
    assert releases == acquired[::-1]
    assert result.cleanup == owner.ConfinedFileReadCleanup("closed", 3, 3, 3)
    assert result.root_locator == str(root) and result.path == path
    assert result.observation_grade == "observed_state"
    assert result.confinement_profile == "descriptor_walk_v1"


@pytest.mark.parametrize("path,count", [("parent/missing", 2), ("missing/child", 1)])
def test_known_absence_retains_exact_acquisition_count(source, path, count):
    root, _ = source
    result = PORT(root=root, path=path)
    assert result.observation == owner.ConfinedFileObservation(
        path, owner.ConfinedObservationOutcome.OBSERVED, False
    )
    assert result.cleanup == owner.ConfinedFileReadCleanup(
        "closed", count, count, count
    )


@pytest.mark.parametrize("kind", ["directory", "symlink", "fifo"])
def test_nonregular_leaf_refuses_without_leaf_acquisition(source, kind):
    root, _ = source
    leaf = root / "parent/other"
    if kind == "directory":
        leaf.mkdir()
    elif kind == "symlink":
        leaf.symlink_to("capture.json")
    else:
        os.mkfifo(leaf)
    result = PORT(root=root, path="parent/other")
    assert result.observation.outcome is owner.ConfinedObservationOutcome.DENIED
    assert result.observation.error_code == "target_is_not_regular_file"
    assert result.cleanup == owner.ConfinedFileReadCleanup("closed", 2, 2, 2)


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/absolute",
        "../capture",
        "parent/../capture",
        "./capture",
        "parent//capture",
        "parent\\capture",
        "control\npath",
        "e\u0301",
        "\ud800",
        "a" * 1025,
        "/".join(["a"] * 65),
        None,
        1,
    ],
)
def test_invalid_saved_path_is_typed_before_open(source, monkeypatch, path):
    root, _ = source

    def forbidden(*args, **kwargs):
        pytest.fail("invalid request acquired a descriptor")

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", forbidden)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    error = failure.value
    assert error.path is None and error.observation is None
    assert error.cleanup == owner.ConfinedFileReadCleanup("not_acquired", 0, 0, 0)
    assert error.__cause__ is not None


@pytest.mark.parametrize("maximum", [0, -1, True, 1.0, 16 * 1024**2 + 1, None])
def test_invalid_exact_integer_byte_bound_is_typed_before_open(
    source, monkeypatch, maximum
):
    root, path = source
    with monkeypatch.context() as patch:
        acquired, _ = _track(patch)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path, maximum_bytes=maximum)
    assert acquired == []
    assert failure.value.cleanup.outcome == "not_acquired"


@pytest.mark.parametrize(
    "kind", ["relative", "parent", "alias", "absent", "file", "text"]
)
def test_explicit_root_validation_never_silently_rebases(source, monkeypatch, kind):
    root, path = source
    if kind == "relative":
        selected = Path("relative")
    elif kind == "parent":
        selected = root / ".." / root.name
    elif kind == "alias":
        selected = root / "alias"
        selected.symlink_to(root, target_is_directory=True)
    elif kind == "absent":
        selected = root / "absent"
    elif kind == "file":
        selected = root / path
    else:
        selected = str(root)
    with monkeypatch.context() as patch:
        acquired, _ = _track(patch)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=selected, path=path)
    assert acquired == []
    assert failure.value.cleanup.outcome == "not_acquired"


def test_original_legacy_root_alias_still_resolves(source):
    root, path = source
    alias = root / "alias"
    alias.symlink_to(root, target_is_directory=True)
    assert (
        owner.observe_confined_file(root=alias, path=path).content
        == (root / path).read_bytes()
    )


@pytest.mark.parametrize("flag", ["O_DIRECTORY", "O_NOFOLLOW"])
def test_unsupported_facilities_refuse_without_open(source, monkeypatch, flag):
    root, path = source
    with monkeypatch.context() as patch:
        acquired, _ = _track(patch)
        patch.delattr(os, flag)
        result = PORT(root=root, path=path)
    assert acquired == []
    assert result.observation.error_code == "secure_descriptor_traversal_unavailable"
    assert result.cleanup.outcome == "not_acquired"


@pytest.mark.parametrize("maximum", [1, 2, 16 * 1024**2])
def test_exact_byte_limits_preserve_bodies(source, maximum):
    root, path = source
    (root / path).write_bytes(b"x" * min(maximum, 3))
    result = PORT(root=root, path=path, maximum_bytes=maximum)
    assert result.observation.content == (root / path).read_bytes()


def test_over_limit_data_is_denied_not_truncated(source):
    root, path = source
    result = PORT(root=root, path=path, maximum_bytes=1)
    assert result.observation.error_code == "target_changed_or_exceeds_byte_bound"
    assert result.observation.content is None
    assert result.cleanup.outcome == "closed"


@pytest.mark.parametrize("point", [0, 1, 2])
@pytest.mark.parametrize("kind", [OSError, KeyboardInterrupt, SystemExit])
def test_missing_open_return_never_claims_zero_acquisition(
    source, monkeypatch, point, kind
):
    root, path = source
    real_open, real_close = os.open, os.close
    acquired, released, lost = [], [], []
    calls = 0
    original_error = kind("missing original open return")

    def opened(*args, **kwargs):
        nonlocal calls
        index = calls
        calls += 1
        fd = real_open(*args, **kwargs)
        if index == point:
            lost.append(fd)
            raise original_error
        acquired.append(fd)
        return fd

    def closed(fd):
        released.append(fd)
        return real_close(fd)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(os, "open", opened)
            patch.setattr(os, "close", closed)
            with pytest.raises(owner.ConfinedFileObservationError) as failure:
                PORT(root=root, path=path)
        error = failure.value
        assert error.__cause__ is original_error
        assert error.stage == ("root_open", "parent_open", "leaf_open")[point]
        assert error.cleanup.outcome == "unknown"
        assert error.cleanup.acquired_count is None
        assert released == acquired[::-1]
        assert not set(lost) & set(released)
        assert error.observation is None
    finally:
        # Fault injector retained this fd; the product never observed its id.
        # Test-only disposal is not product cleanup evidence or recovery.
        for fd in lost:
            real_close(fd)


def test_acquisition_slot_exists_before_the_original_open_dispatch(source, monkeypatch):
    root, path = source

    def allocation():
        raise MemoryError("slot unavailable before open")

    with monkeypatch.context() as patch:
        acquired, _ = _track(patch)
        patch.setattr(owner, "_ReadResource", allocation)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    assert acquired == []
    assert failure.value.cleanup.outcome == "not_acquired"
    assert isinstance(failure.value.__cause__, MemoryError)


def test_returned_descriptor_survives_interrupted_attachment(source, monkeypatch):
    root, path = source
    original_set = owner._ReadResource.__setattr__
    interrupted = False

    def attachment(value, name, body):
        nonlocal interrupted
        if name == "descriptor" and type(body) is int and not interrupted:
            interrupted = True
            raise KeyboardInterrupt("attachment interrupted")
        return original_set(value, name, body)

    with monkeypatch.context() as patch:
        acquired, released = _track(patch)
        patch.setattr(owner._ReadResource, "__setattr__", attachment)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    assert acquired == released and len(acquired) == 1
    assert failure.value.cleanup == owner.ConfinedFileReadCleanup("closed", 1, 1, 1)
    assert isinstance(failure.value.__cause__, KeyboardInterrupt)


@pytest.mark.parametrize("point", [0, 1, 2])
@pytest.mark.parametrize("kind", [OSError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("when", ["before", "after"])
def test_each_close_is_spent_once_and_other_resources_still_close(
    source, monkeypatch, point, kind, when
):
    root, path = source
    real_open, real_close = os.open, os.close
    acquired, released, withheld = [], [], []
    original_error = kind("missing original close return")

    def opened(*args, **kwargs):
        fd = real_open(*args, **kwargs)
        acquired.append(fd)
        return fd

    def closed(fd):
        index = len(released)
        released.append(fd)
        if index == point and when == "before":
            withheld.append(fd)
            raise original_error
        real_close(fd)
        if index == point:
            raise original_error

    try:
        with monkeypatch.context() as patch:
            patch.setattr(os, "open", opened)
            patch.setattr(os, "close", closed)
            with pytest.raises(owner.ConfinedFileObservationError) as failure:
                PORT(root=root, path=path)
        error = failure.value
        assert error.__cause__ is original_error
        assert error.stage == "cleanup"
        assert error.cleanup.outcome == "unknown"
        assert (
            error.cleanup.acquired_count == error.cleanup.release_attempted_count == 3
        )
        assert error.cleanup.closed_count is None
        assert released == acquired[::-1]
        assert len(released) == len(set(released))
        assert error.observation.content == (root / path).read_bytes()
    finally:
        # Explicit injector-owned disposal only when the injected close did
        # not reach the kernel. Never retry a missing-return product close.
        for fd in withheld:
            real_close(fd)


@pytest.mark.parametrize(
    "stage",
    [
        "leaf_stat",
        "leaf_stat_before",
        "read",
        "leaf_stat_after",
        "digest",
        "observation",
        "result",
    ],
)
@pytest.mark.parametrize("kind", [OSError, KeyboardInterrupt])
def test_primary_failure_at_original_read_and_return_boundaries_retains_cleanup(
    source, monkeypatch, stage, kind
):
    root, path = source
    original_error = kind("primary boundary failure")
    real_stat, real_fstat = os.stat, os.fstat
    fstats = 0

    def path_stat(*args, **kwargs):
        if kwargs.get("dir_fd") is not None:
            raise original_error
        return real_stat(*args, **kwargs)

    def descriptor_stat(*args, **kwargs):
        nonlocal fstats
        fstats += 1
        if fstats == (1 if stage == "leaf_stat_before" else 2):
            raise original_error
        return real_fstat(*args, **kwargs)

    def read(*args, **kwargs):
        raise original_error

    def digest(*args, **kwargs):
        raise original_error

    def construct(*args, **kwargs):
        raise original_error

    with monkeypatch.context() as patch:
        acquired, released = _track(patch)
        if stage == "leaf_stat":
            patch.setattr(os, "stat", path_stat)
        elif stage in {"leaf_stat_before", "leaf_stat_after"}:
            patch.setattr(os, "fstat", descriptor_stat)
        elif stage == "read":
            patch.setattr(os, "read", read)
        elif stage == "digest":
            patch.setattr(owner, "_content_digest", digest)
        elif stage == "observation":
            patch.setattr(owner.ConfinedFileObservation, "__post_init__", construct)
        else:
            patch.setattr(
                owner.ConfinedFileObservationWithCleanup, "__post_init__", construct
            )
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    error = failure.value
    assert error.__cause__ is original_error
    assert error.stage == stage
    assert released == acquired[::-1]
    assert error.cleanup.outcome == "closed"
    assert error.cleanup.closed_count == len(acquired)
    if stage == "result":
        assert error.observation.content == (root / path).read_bytes()
    else:
        assert error.observation is None


def test_primary_read_error_wins_over_secondary_close_interruptions(
    source, monkeypatch
):
    root, path = source
    real_close = os.close
    primary = OSError("original read failure")

    def read(*args, **kwargs):
        raise primary

    def close(fd):
        real_close(fd)
        raise KeyboardInterrupt("secondary close interruption")

    with monkeypatch.context() as patch:
        patch.setattr(os, "read", read)
        patch.setattr(os, "close", close)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    assert failure.value.__cause__ is primary
    assert failure.value.stage == "read"
    assert failure.value.cleanup.outcome == "unknown"
    assert len(failure.value.cleanup.diagnostics) == 3


def test_sixty_four_components_use_original_sixty_five_resources(tmp_path, monkeypatch):
    components = ["d"] * 63
    leaf = tmp_path.joinpath(*components, "capture")
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(b"capture")
    with monkeypatch.context() as patch:
        acquired, releases = _track(patch)
        result = PORT(root=tmp_path, path="/".join([*components, "capture"]))
    assert releases == acquired[::-1]
    assert result.cleanup == owner.ConfinedFileReadCleanup("closed", 65, 65, 65)


def test_many_close_failures_have_bounded_incomplete_diagnostics(tmp_path, monkeypatch):
    leaf = tmp_path.joinpath(*(["d"] * 18), "capture")
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(b"capture")
    real_close = os.close
    attempts = []

    def close(fd):
        attempts.append(fd)
        real_close(fd)
        raise OSError("missing close acknowledgement")

    with monkeypatch.context() as patch:
        patch.setattr(os, "close", close)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=tmp_path, path=str(leaf.relative_to(tmp_path)))
    assert len(attempts) == len(set(attempts)) == 20
    cleanup = failure.value.cleanup
    assert cleanup.outcome == "unknown"
    assert len(cleanup.diagnostics) == 16
    assert cleanup.diagnostics[-1] == "cleanup_diagnostics_incomplete"


def test_fifo_substitution_between_original_stat_and_open_never_blocks(
    source, monkeypatch
):
    root, path = source
    real_open = os.open
    flags_seen = []

    def opened(name, flags, *args, **kwargs):
        if str(name) == "capture.json":
            (root / path).unlink()
            os.mkfifo(root / path)
            flags_seen.append(flags)
        return real_open(name, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", opened)
        result = PORT(root=root, path=path)
    assert flags_seen[0] & os.O_NONBLOCK
    assert result.observation.error_code == "target_changed_or_exceeds_byte_bound"
    assert result.cleanup.outcome == "closed"


def test_original_post_read_stat_refuses_changed_bytes(source, monkeypatch):
    root, path = source
    real_read = os.read
    changed = False

    def read(fd, count):
        nonlocal changed
        data = real_read(fd, count)
        if not changed:
            changed = True
            with (root / path).open("ab") as stream:
                stream.write(b"changed")
        return data

    with monkeypatch.context() as patch:
        patch.setattr(os, "read", read)
        result = PORT(root=root, path=path)
    assert result.observation.error_code == "target_changed_or_exceeds_byte_bound"
    assert result.cleanup.outcome == "closed"


def test_reader_has_no_namespace_or_write_dispatch(source, monkeypatch):
    root, path = source
    before = (root / path).read_bytes()

    def forbidden(*args, **kwargs):
        pytest.fail("read dispatched a namespace write")

    with monkeypatch.context() as patch:
        for name in (
            "write",
            "mkdir",
            "unlink",
            "replace",
            "rename",
            "link",
            "chmod",
            "fsync",
        ):
            patch.setattr(os, name, forbidden)
        result = PORT(root=root, path=path)
    assert result.observation.content == before == (root / path).read_bytes()


@pytest.mark.parametrize(
    "changes",
    [
        {
            "outcome": "closed",
            "acquired_count": 0,
            "release_attempted_count": 0,
            "closed_count": 0,
        },
        {"outcome": "closed", "closed_count": None},
        {"outcome": "closed", "closed_count": 2},
        {"outcome": "closed", "diagnostics": ("unknown",)},
        {"outcome": "not_acquired"},
        {"acquired_count": True},
        {"closed_count": 66},
        {"closed_count": -1},
        {"diagnostics": ("x" * 1025,)},
        {"diagnostics": ("\ud800",)},
        {"outcome": "unknown"},
    ],
)
def test_invalid_cleanup_combinations_refuse(changes):
    value = owner.ConfinedFileReadCleanup("closed", 3, 3, 3)
    with pytest.raises((ValueError, UnicodeError)):
        replace(value, **changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"path": "other"},
        {"root_locator": "relative"},
        {"confinement_profile": "continuous_root_v1"},
        {"observation_grade": "authenticated"},
        {"cleanup": owner.ConfinedFileReadCleanup("unknown", 3, 3, None, ("unknown",))},
    ],
)
def test_invalid_or_unknown_result_knowledge_cannot_be_success(source, changes):
    root, path = source
    value = PORT(root=root, path=path)
    with pytest.raises(ValueError):
        replace(value, **changes)


@pytest.mark.parametrize("point", [0, 1, 2])
def test_definite_posix_open_refusal_keeps_known_prior_cleanup(
    source, monkeypatch, point
):
    root, path = source
    real_open = os.open
    count = 0
    primary = PermissionError(errno.EACCES, "denied original open")

    def open_source(*args, **kwargs):
        nonlocal count
        index = count
        count += 1
        if index == point:
            raise primary
        return real_open(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", open_source)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    error = failure.value
    assert error.__cause__ is primary
    assert error.cleanup == owner.ConfinedFileReadCleanup(
        "not_acquired" if point == 0 else "closed", point, point, point
    )


@pytest.mark.parametrize("field", ["spent", "closed"])
def test_cleanup_accounting_interruption_cannot_skip_other_original_resources(
    source, monkeypatch, field
):
    root, path = source
    resource_set = owner._ReadResource.__setattr__
    ledger_set = owner._ReadLedger.__setattr__
    original_close = os.close
    withheld = []
    original_error = KeyboardInterrupt("cleanup accounting interrupted")
    interrupted = False

    def resource_assignment(value, name, body):
        nonlocal interrupted
        if field == "spent" and name == "spent" and body is True and not interrupted:
            interrupted = True
            withheld.append(value.descriptor)
            raise original_error
        return resource_set(value, name, body)

    def ledger_assignment(value, name, body):
        nonlocal interrupted
        if field == "closed" and name == "closed" and body == 1 and not interrupted:
            interrupted = True
            raise original_error
        return ledger_set(value, name, body)

    try:
        with monkeypatch.context() as patch:
            acquired, released = _track(patch)
            patch.setattr(owner._ReadResource, "__setattr__", resource_assignment)
            patch.setattr(owner._ReadLedger, "__setattr__", ledger_assignment)
            with pytest.raises(owner.ConfinedFileObservationError) as failure:
                PORT(root=root, path=path)
        error = failure.value
        assert error.__cause__ is original_error
        assert error.cleanup.outcome == "unknown"
        assert error.cleanup.closed_count is None
        assert error.observation.content == (root / path).read_bytes()
        if field == "spent":
            assert error.cleanup.release_attempted_count is None
            assert released == acquired[-2::-1]
        else:
            assert released == acquired[::-1]
    finally:
        for descriptor in withheld:
            original_close(descriptor)


def test_untrusted_exception_name_cannot_break_typed_cleanup_error(source, monkeypatch):
    root, path = source
    error_type = type("Bad\nNameÉ", (RuntimeError,), {})
    original_error = error_type("primary")
    original_close = os.close

    def close(fd):
        original_close(fd)
        raise original_error

    with monkeypatch.context() as patch:
        patch.setattr(os, "close", close)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    assert failure.value.__cause__ is original_error
    assert failure.value.cause_kind == "Bad_Name_"
    assert failure.value.cleanup.outcome == "unknown"


@pytest.mark.parametrize("primary_read_failure", [False, True])
def test_cleanup_boundary_failure_is_typed_without_repeating_disposal(
    source, monkeypatch, primary_read_failure
):
    root, path = source
    original_drain = owner._ReadLedger.close_all
    primary = OSError("read failure")
    secondary = KeyboardInterrupt("cleanup return unavailable")
    calls = []

    def drain(ledger):
        calls.append(ledger)
        original_drain(ledger)
        raise secondary

    def read(*args, **kwargs):
        raise primary

    with monkeypatch.context() as patch:
        acquired, released = _track(patch)
        patch.setattr(owner._ReadLedger, "close_all", drain)
        if primary_read_failure:
            patch.setattr(os, "read", read)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    error = failure.value
    assert len(calls) == 1 and released == acquired[::-1]
    assert error.cleanup.outcome == "unknown"
    assert (
        error.cleanup.acquired_count
        == error.cleanup.release_attempted_count
        == error.cleanup.closed_count
        == 3
    )
    assert error.__cause__ is (primary if primary_read_failure else secondary)
    if primary_read_failure:
        assert error.observation is None
    else:
        assert error.observation.content == (root / path).read_bytes()


@pytest.mark.parametrize("primary_read_failure", [False, True])
@pytest.mark.parametrize("parents_closed", [0, 1, 2])
def test_interrupted_drain_finishes_only_known_unspent_resources(
    source, monkeypatch, primary_read_failure, parents_closed
):
    root, path = source
    real_close = os.close
    primary = OSError("original read failure")
    interruption = KeyboardInterrupt("original drain interrupted")
    calls = []
    acquired, released = [], []

    def drain(ledger):
        calls.append(ledger)
        remaining = [
            item
            for item in reversed(ledger.resources)
            if item.descriptor is not None and not item.spent
        ]
        for resource in remaining[:parents_closed]:
            ledger.close(resource.descriptor)
        raise interruption

    def read(*args, **kwargs):
        raise primary

    try:
        with monkeypatch.context() as patch:
            acquired, released = _track(patch)
            patch.setattr(owner._ReadLedger, "close_all", drain)
            if primary_read_failure:
                patch.setattr(os, "read", read)
            with pytest.raises(owner.ConfinedFileObservationError) as failure:
                PORT(root=root, path=path)
        error = failure.value
        assert len(calls) == 1
        assert len(acquired) == 3 and released == acquired[::-1]
        for descriptor in acquired:
            with pytest.raises(OSError, match="Bad file descriptor"):
                os.fstat(descriptor)
        assert error.__cause__ is (primary if primary_read_failure else interruption)
        assert error.cleanup == owner.ConfinedFileReadCleanup(
            "unknown", 3, 3, 3, ("cleanup_boundary_unknown:KeyboardInterrupt",)
        )
        if primary_read_failure:
            assert error.observation is None
        else:
            assert error.observation.content == (root / path).read_bytes()
    finally:
        # Dispose predecessor leaks only in failing controls, not as product proof.
        for descriptor in acquired:
            if descriptor not in released:
                real_close(descriptor)


@pytest.mark.parametrize("primary_read_failure", [False, True])
@pytest.mark.parametrize("snapshot_returned", [False, True])
def test_cleanup_snapshot_failure_is_typed_and_keeps_primary_without_redrain(
    source, monkeypatch, primary_read_failure, snapshot_returned
):
    root, path = source
    original_snapshot = owner._ReadLedger.snapshot
    original_drain = owner._ReadLedger.close_all
    primary = OSError("original read failure")
    interruption = KeyboardInterrupt("cleanup snapshot unavailable")
    snapshots, drains = [], []

    def snapshot(ledger):
        snapshots.append(ledger)
        if snapshot_returned:
            original_snapshot(ledger)
        raise interruption

    def drain(ledger):
        drains.append(ledger)
        original_drain(ledger)

    def read(*args, **kwargs):
        raise primary

    with monkeypatch.context() as patch:
        acquired, released = _track(patch)
        patch.setattr(owner._ReadLedger, "snapshot", snapshot)
        patch.setattr(owner._ReadLedger, "close_all", drain)
        if primary_read_failure:
            patch.setattr(os, "read", read)
        with pytest.raises(BaseException) as failure:
            PORT(root=root, path=path)
    error = failure.value
    assert isinstance(error, owner.ConfinedFileObservationError)
    assert len(snapshots) == len(drains) == 1
    assert len(acquired) == 3 and released == acquired[::-1]
    assert error.__cause__ is (primary if primary_read_failure else interruption)
    assert error.cleanup.outcome == "unknown"
    assert (
        error.cleanup.acquired_count
        == error.cleanup.release_attempted_count
        == error.cleanup.closed_count
        == 3
    )
    assert "cleanup_snapshot_unknown:KeyboardInterrupt" in error.cleanup.diagnostics
    if primary_read_failure:
        assert error.observation is None and error.stage == "read"
    else:
        assert error.observation.content == (root / path).read_bytes()
        assert error.code == "filesystem_read_cleanup_unverified"


@pytest.mark.parametrize("primary_read_failure", [False, True])
@pytest.mark.parametrize("parents_closed", [0, 1])
def test_original_drain_iterator_interruption_continues_unspent_custody(
    source, monkeypatch, primary_read_failure, parents_closed
):
    root, path = source
    original_open = owner._ReadLedger.open
    real_close = os.close
    primary = OSError("original read failure")
    interruption = KeyboardInterrupt("original drain iteration interrupted")
    acquired, released = [], []

    class InterruptedResources(list):
        interrupted = False

        def __reversed__(self):
            for index, resource in enumerate(super().__reversed__()):
                if index == parents_closed + 1 and not self.interrupted:
                    self.interrupted = True
                    raise interruption
                yield resource

    def opened(ledger, *args, **kwargs):
        descriptor = original_open(ledger, *args, **kwargs)
        if len(ledger.resources) == 3:
            ledger.resources = InterruptedResources(ledger.resources)
        return descriptor

    def read(*args, **kwargs):
        raise primary

    try:
        with monkeypatch.context() as patch:
            acquired, released = _track(patch)
            patch.setattr(owner._ReadLedger, "open", opened)
            if primary_read_failure:
                patch.setattr(os, "read", read)
            with pytest.raises(owner.ConfinedFileObservationError) as failure:
                PORT(root=root, path=path)
        assert released == acquired[::-1] and len(acquired) == 3
        assert failure.value.__cause__ is (
            primary if primary_read_failure else interruption
        )
        assert failure.value.cleanup == owner.ConfinedFileReadCleanup(
            "unknown", 3, 3, 3, ("cleanup_boundary_unknown:KeyboardInterrupt",)
        )
    finally:
        for descriptor in acquired:
            if descriptor not in released:
                real_close(descriptor)


@pytest.mark.parametrize("primary_read_failure", [False, True])
def test_unavailable_cleanup_accounting_keeps_typed_unknown_not_zero(
    source, monkeypatch, primary_read_failure
):
    root, path = source
    primary = OSError("original read failure")
    interruption = KeyboardInterrupt("cleanup accounting unavailable")
    calls = []

    def snapshot_value(ledger):
        calls.append(ledger)
        raise interruption

    def read(*args, **kwargs):
        raise primary

    with monkeypatch.context() as patch:
        acquired, released = _track(patch)
        patch.setattr(owner._ReadLedger, "snapshot_value", snapshot_value)
        if primary_read_failure:
            patch.setattr(os, "read", read)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    error = failure.value
    assert len(calls) == 2 and released == acquired[::-1]
    assert error.__cause__ is (primary if primary_read_failure else interruption)
    assert error.cleanup == owner.ConfinedFileReadCleanup(
        "unknown",
        None,
        None,
        None,
        (
            "cleanup_snapshot_unknown:KeyboardInterrupt",
            "cleanup_accounting_unknown:KeyboardInterrupt",
        ),
    )


@pytest.mark.parametrize("primary_read_failure", [False, True])
def test_snapshot_failure_cannot_upgrade_uncertain_close_or_replace_primary(
    source, monkeypatch, primary_read_failure
):
    root, path = source
    primary = OSError("original read failure")
    close_failure = OSError("original close acknowledgement unavailable")
    snapshot_failure = KeyboardInterrupt("cleanup snapshot unavailable")
    real_close = os.close
    released = []

    def close(descriptor):
        released.append(descriptor)
        real_close(descriptor)
        if len(released) == 1:
            raise close_failure

    def snapshot(ledger):
        raise snapshot_failure

    def read(*args, **kwargs):
        raise primary

    with monkeypatch.context() as patch:
        acquired, _ = _track(patch)
        patch.setattr(os, "close", close)
        patch.setattr(owner._ReadLedger, "snapshot", snapshot)
        if primary_read_failure:
            patch.setattr(os, "read", read)
        with pytest.raises(owner.ConfinedFileObservationError) as failure:
            PORT(root=root, path=path)
    assert released == acquired[::-1] and len(acquired) == 3
    error = failure.value
    assert error.__cause__ is (primary if primary_read_failure else close_failure)
    assert error.cleanup == owner.ConfinedFileReadCleanup(
        "unknown",
        3,
        3,
        None,
        ("close_unknown:OSError", "cleanup_snapshot_unknown:KeyboardInterrupt"),
    )


def test_caller_path_subclass_is_snapshotted_once_not_reinterpreted(source):
    root, path = source
    calls = []

    class ChangingPath(type(root)):
        def __str__(self):
            calls.append(None)
            return str(root) if len(calls) == 1 else "relative-replacement"

    result = PORT(root=ChangingPath(root), path=path)
    assert len(calls) == 1
    assert result.root_locator == str(root)
    assert result.observation.content == (root / path).read_bytes()


def test_source_metadata_target_has_no_new_default_dependencies():
    metadata = Path(__file__).parents[1] / "pyproject.toml"
    project = tomllib.loads(metadata.read_text())["project"]
    assert project["version"] == "0.3.6"
    assert project["dependencies"] == [
        "pyyaml>=6.0.2,<7.0.0",
        "msgpack>=1.1.1,<2.0.0",
        "pathspec>=1.1.1,<2.0.0",
        "pydantic>=2.8.2,<3.0.0",
    ]
