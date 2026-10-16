"""Real retained legacy-writer sequence, ordinals and cleanup; no Issue mocks."""

import copy
import hashlib
import json
import os
import stat
from dataclasses import fields, replace
from pathlib import Path

import pytest
from aware_file_system import confined_mutation as n
from aware_file_system import retained_file_sequence as s


def sequence(root, requests, **caps):
    return s.retain_confined_file_sequence(
        root=root,
        requests=tuple(requests),
        limits=s.ConfinedSequenceLimits(**(s._LIMIT_CAPS | caps)),
        confinement_profile=n.ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
    )


def create(path="libs/example/data", content=b"42"):
    return n.ConfinedFileMutationRequest(
        n.ConfinedMutationKind.CREATE, path, False, None, content, maximum_bytes=1048576
    )


def finish(handle):
    binding = s.observe_confined_file_sequence(handle).binding
    for step in binding.ordered_steps:
        s.verify_confined_file_sequence(handle, expected_binding=binding)
        result = s.execute_next_confined_file_step(
            handle, expected_ordinal=step.ordinal
        )
        assert result.step_ordinal == step.ordinal
    return s.observe_confined_file_sequence(handle)


@pytest.mark.parametrize("umask", (0o022, 0o077))
def test_genuine_create_update_complete_modes_and_no_before_spend_effects(
    tmp_path, umask
):
    target = tmp_path / "existing"
    target.write_bytes(b"old")
    target.chmod(0o664)
    update = n.ConfinedFileMutationRequest(
        n.ConfinedMutationKind.UPDATE,
        "existing",
        True,
        "sha256:" + hashlib.sha256(b"old").hexdigest(),
        b"new",
        maximum_bytes=1048576,
    )
    previous = os.umask(umask)
    try:
        handle = sequence(tmp_path, (create(), update))
        assert not (tmp_path / "libs").exists()
        assert target.read_bytes() == b"old"
        original = s.observe_confined_file_sequence(handle).binding
        view = finish(handle)
        assert view.phase == "completed" and view.ledger_complete
        assert view.binding is original
        assert (
            target.read_bytes() == b"new"
            and stat.S_IMODE(target.stat().st_mode) == 0o664
        )
        assert (tmp_path / "libs/example/data").read_bytes() == b"42"
        assert stat.S_IMODE((tmp_path / "libs").stat().st_mode) == (0o777 & ~umask)
        cleanup = s.release_confined_file_sequence(handle)
        assert (
            cleanup.release == "confirmed"
            and cleanup.ledger_complete
            and not cleanup.scratch_residue
        )
        assert s.release_confined_file_sequence(handle) is cleanup
        assert all(row.ownership == "released" for row in cleanup.resources)
    finally:
        os.umask(previous)


def test_replay_and_binding_replacement_refuse_without_forward_effect(tmp_path):
    handle = sequence(tmp_path, (create(),))
    s.execute_next_confined_file_step(handle, expected_ordinal=0)
    with pytest.raises(s.ConfinedSequenceRefusal):
        s.execute_next_confined_file_step(handle, expected_ordinal=0)
    assert not (tmp_path / "libs/example/data").exists()
    cleanup = s.release_confined_file_sequence(handle)
    assert cleanup.release == "confirmed" and (tmp_path / "libs").is_dir()
    handle = sequence(tmp_path, (create("other/data"),))
    with pytest.raises(s.ConfinedSequenceRefusal):
        s.verify_confined_file_sequence(
            handle,
            expected_binding=replace(
                s.observe_confined_file_sequence(handle).binding,
                preparation_ref="foreign:1",
            ),
        )
    assert not (tmp_path / "other").exists()
    assert s.release_confined_file_sequence(handle).release == "confirmed"


def test_input_and_ancestor_mutation_terminally_refuse_and_restoration_cannot_revive(
    tmp_path,
):
    (tmp_path / "libs").mkdir()
    handle = sequence(tmp_path, (create("libs/data"),))
    original = (tmp_path / "libs").stat().st_mode
    (tmp_path / "libs").chmod(0o700)
    with pytest.raises(s.ConfinedSequenceRefusal):
        finish(handle)
    (tmp_path / "libs").chmod(stat.S_IMODE(original))
    with pytest.raises(s.ConfinedSequenceRefusal):
        finish(handle)
    assert not (tmp_path / "libs/data").exists()
    assert s.release_confined_file_sequence(handle).release == "confirmed"


def test_partial_cleanup_removes_only_original_scratch_preserving_published_prefix(
    tmp_path,
):
    handle = sequence(tmp_path, (create("one"), create("two")))
    binding = s.observe_confined_file_sequence(handle).binding
    for step in binding.ordered_steps:
        if step.file_ordinal == 1 and step.kind == "scratch_sync":
            break
        s.execute_next_confined_file_step(handle, expected_ordinal=step.ordinal)
    cleanup = s.release_confined_file_sequence(handle)
    assert (tmp_path / "one").read_bytes() == b"42"
    assert not (tmp_path / "two").exists()
    assert not tuple(tmp_path.glob(".aware-cas-*"))
    assert cleanup.release == "confirmed" and cleanup.ledger_complete


@pytest.mark.parametrize("field", tuple(s._LIMIT_CAPS))
@pytest.mark.parametrize("value", (0, True, []))
def test_scalar_limits_refuse_before_preparation_io(tmp_path, field, value):
    with pytest.raises(s.ConfinedSequenceRefusal):
        sequence(tmp_path, (create(),), **{field: value})
    assert list(tmp_path.iterdir()) == []


def test_capacity_reservation_refuses_before_any_namespace_effect(tmp_path):
    with pytest.raises(s.ConfinedSequenceRefusal):
        sequence(tmp_path, (create(),), physical_step_count=1)
    assert list(tmp_path.iterdir()) == []


def test_original_writer_and_native_dispatch_substitution_refuse_zero_foreign_calls(
    tmp_path, monkeypatch
):
    handle = sequence(tmp_path, (create(),))
    binding = s.observe_confined_file_sequence(handle).binding
    calls = []
    monkeypatch.setattr(
        n, "_confined_file_writer_steps", lambda **_: calls.append("foreign")
    )
    with pytest.raises(s.ConfinedSequenceRefusal):
        s.verify_confined_file_sequence(handle, expected_binding=binding)
    assert calls == [] and list(tmp_path.iterdir()) == []
    assert s.release_confined_file_sequence(handle).release == "confirmed"


def test_opaque_sequence_cannot_be_copied_forged_or_decoded(tmp_path):
    handle = sequence(tmp_path, (create(),))
    with pytest.raises(TypeError):
        copy.copy(handle)
    with pytest.raises(s.ConfinedSequenceRefusal):
        s.observe_confined_file_sequence(object.__new__(s.RetainedConfinedFileSequence))
    assert s.release_confined_file_sequence(handle).release == "confirmed"


def test_exact_native_member_plan_and_schema_fields_match_frozen_intake():
    root = next(
        p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
    )
    freeze = json.loads(
        (
            root / "docs/reports/workspace-setup-a1-supplier-inputs-20261012.json"
        ).read_text()
    )["joined_freeze"]
    for cls in s._VALUE_TYPES:
        assert [f.name for f in fields(cls)] == freeze["schemas"][cls.__name__]
        assert s._WIRE_IDS[cls] == freeze["wire_ids"][cls.__name__]


def fail_original_io_fstat(monkeypatch, kind):
    """Inject a native observation fault; acquisition/cleanup remain actual IO."""
    import errno
    import sys

    original = os.fstat
    opened = []

    def fail(descriptor):
        caller = sys._getframe(1)
        if (
            caller.f_code is s._SequenceIO.open.__code__
            and caller.f_locals["resource"]["kind"] == kind
        ):
            opened.append(descriptor)
            raise OSError(errno.EIO, "injected original descriptor observation failure")
        return original(descriptor)

    # This controlled test syscall table is not a public provider or an issuer.
    monkeypatch.setitem(s._OS, "fstat", fail)
    monkeypatch.setattr(os, "fstat", fail)
    return opened, original


@pytest.mark.parametrize(
    "kind", ("root_descriptor", "directory_descriptor", "scratch_descriptor")
)
def test_fstat_failure_closes_actual_descriptor_including_partial_construction(
    tmp_path, monkeypatch, kind
):
    import errno

    opened, original_fstat = fail_original_io_fstat(monkeypatch, kind)
    handle = None
    if kind == "root_descriptor":
        with pytest.raises(s.ConfinedSequenceRefusal) as caught:
            sequence(tmp_path, (create(),))
        cleanup = caught.value.evidence.cleanup
        assert cleanup.binding is None
    else:
        handle = sequence(tmp_path, (create(),))
        with pytest.raises(s.ConfinedSequenceRefusal):
            finish(handle)
        cleanup = s.release_confined_file_sequence(handle)
    assert len(opened) == 1
    with pytest.raises(OSError) as closed:
        original_fstat(opened[0])
    assert closed.value.errno == errno.EBADF
    assert all(
        row.ownership == "released" and row.release_outcome == "confirmed"
        for row in cleanup.resources
    )
    assert not (tmp_path / "libs/example/data").exists()
    if kind == "scratch_descriptor":
        scratch = tuple(tmp_path.rglob(".aware-cas-*"))
        assert len(scratch) == 1
        assert cleanup.scratch_residue == (scratch[0].relative_to(tmp_path).as_posix(),)
        assert cleanup.release == "unknown" and not cleanup.ledger_complete
    else:
        assert cleanup.release == "confirmed" and cleanup.ledger_complete
        assert not cleanup.scratch_residue
    if handle is not None:
        assert s.release_confined_file_sequence(handle) is cleanup


@pytest.mark.parametrize("lose_return", (False, True))
def test_failed_unlink_keeps_residue_and_spent_attempt_without_retry(
    tmp_path, monkeypatch, lose_return
):
    import errno

    handle = sequence(tmp_path, (create("target"),))
    binding = s.observe_confined_file_sequence(handle).binding
    calls = []
    original = os.unlink

    def fail(name, **kwargs):
        calls.append(name)
        if lose_return:
            original(name, **kwargs)
        raise PermissionError(errno.EACCES, "injected original unlink failure")

    monkeypatch.setitem(s._OS, "unlink", fail)
    monkeypatch.setattr(os, "unlink", fail)
    for step in binding.ordered_steps:
        if step.kind == "scratch_unlink":
            break
        s.execute_next_confined_file_step(handle, expected_ordinal=step.ordinal)
    scratch = tmp_path / binding.files[0].scratch_path
    assert scratch.is_file() and (tmp_path / "target").read_bytes() == b"42"
    with pytest.raises(s.ConfinedSequenceRefusal):
        s.execute_next_confined_file_step(handle, expected_ordinal=step.ordinal)
    assert len(calls) == 1
    assert scratch.exists() is (not lose_return)
    observation = s.observe_confined_file_sequence(handle)
    assert observation.scratch_residue == (binding.files[0].scratch_path,)
    assert not observation.ledger_complete
    cleanup = s.release_confined_file_sequence(handle)
    assert cleanup.release == "unknown" and not cleanup.ledger_complete
    assert cleanup.scratch_residue == (binding.files[0].scratch_path,)
    assert len(calls) == 1 and (tmp_path / "target").read_bytes() == b"42"
    assert scratch.exists() is (not lose_return)
    assert s.release_confined_file_sequence(handle) is cleanup
    assert len(calls) == 1
