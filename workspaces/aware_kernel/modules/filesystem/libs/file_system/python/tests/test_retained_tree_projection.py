"""Genuine C physical preparation/read/cleanup, not joined tree execution."""

from __future__ import annotations

import copy
import gc
import os
import pickle
import stat
from pathlib import PurePosixPath

import pytest
from aware_file_system import confined_mutation as physical
from aware_file_system import retained_tree_projection as tree


def pin(path):
    if not path.exists():
        return physical.ConfinedTreeEntryPin(False)
    value = path.stat()
    body = path.read_bytes() if path.is_file() else None
    return tree._entry(value, body)


def request(
    root,
    *,
    path="file",
    kind=physical.ConfinedMutationKind.CREATE,
    content=b"new",
    mode=0o644,
    limits=None,
):
    value = root.stat()
    ancestors = tuple(
        physical.ConfinedTreeAncestorTransition(
            str(parent),
            "preserve" if (root / parent).exists() else "create",
            pin(root / parent),
            None if (root / parent).exists() else 0o755,
        )
        for parent in sorted(
            (parent for parent in PurePosixPath(path).parents if str(parent) != "."),
            key=lambda parent: (len(parent.parts), str(parent)),
        )
    )
    delete = kind is physical.ConfinedMutationKind.DELETE
    row = physical.ConfinedTreeFileTransition(
        path,
        kind,
        pin(root / path),
        None if delete else content,
        None if delete else physical._content_digest(content),
        None if delete else len(content),
        None if delete else mode,
    )
    return physical.ConfinedTreeProjectionRequest(
        "test-request",
        (value.st_dev, value.st_ino),
        (row,),
        ancestors,
        limits or physical.ConfinedTreeLimits(),
    )


def snapshot(root):
    return {
        str(path.relative_to(root)): (
            stat.S_IMODE(path.stat().st_mode),
            path.read_bytes() if path.is_file() else None,
        )
        for path in root.rglob("*")
    }


@pytest.mark.parametrize("kind", tuple(physical.ConfinedMutationKind))
def test_original_preparation_has_exact_pins_and_no_target_effects(tmp_path, kind):
    if kind is not physical.ConfinedMutationKind.CREATE:
        (tmp_path / "file").write_bytes(b"before")
        (tmp_path / "file").chmod(0o640)
    original = snapshot(tmp_path)
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path, kind=kind)
    )
    observed = handle.observe_preparation()
    assert observed.root_identity == (tmp_path.stat().st_dev, tmp_path.stat().st_ino)
    assert observed.request_ref == "test-request"
    assert observed.transition_order == ((0, "file", kind.name),)
    assert dict(observed.read_pins)["file"] == pin(tmp_path / "file")
    assert handle.observe_effects().effects == ()
    assert handle.observe_effects().completed_prefix == 0
    assert len(observed.scratch_effects) == (
        0 if kind is physical.ConfinedMutationKind.DELETE else 4
    )
    assert all(not (tmp_path / row.path).exists() for row in observed.scratch_effects)
    handle.validate_current()
    assert snapshot(tmp_path) == original
    cleanup = handle.release()
    assert cleanup.cleanup_state == "completed" and cleanup.ledger_complete
    assert all(row.ownership == "released" for row in cleanup.resources)
    assert handle.release() == cleanup
    assert handle.observe_preparation() == observed
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.validate_current()
    assert snapshot(tmp_path) == original


def test_bodyless_and_directory_only_requests_have_genuine_original_custody(tmp_path):
    value = tmp_path.stat()
    root_identity = value.st_dev, value.st_ino
    rows = (
        physical.ConfinedTreeAncestorTransition(
            "new", "create", physical.ConfinedTreeEntryPin(False), 0o755
        ),
        physical.ConfinedTreeAncestorTransition(
            "new/child", "create", physical.ConfinedTreeEntryPin(False), 0o755
        ),
    )
    native = physical.ConfinedTreeProjectionRequest(
        "directory-only", root_identity, (), rows
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    observation = handle.observe_preparation()
    assert observation.transition_order == (
        (0, "new", "directory_create"),
        (1, "new/child", "directory_create"),
    )
    assert observation.scratch_effects == ()
    assert dict(observation.read_pins) == {row.path: row.before for row in rows}
    handle.validate_current()
    assert not (tmp_path / "new").exists()
    handle.release()


@pytest.mark.parametrize("same_mode", (True, False))
def test_current_and_mode_only_prepare_no_replacement_scratch(tmp_path, same_mode):
    (tmp_path / "file").write_bytes(b"same")
    (tmp_path / "file").chmod(0o644)
    handle = tree.retain_confined_tree_projection(
        root=tmp_path,
        request=request(
            tmp_path,
            kind=physical.ConfinedMutationKind.UPDATE,
            content=b"same",
            mode=0o644 if same_mode else 0o755,
        ),
    )
    assert handle.observe_preparation().scratch_effects == ()
    assert (tmp_path / "file").read_bytes() == b"same"
    assert stat.S_IMODE((tmp_path / "file").stat().st_mode) == 0o644
    handle.release()


def test_complete_scratch_order_is_bound_before_any_creation(tmp_path):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path, path="new/child/file", mode=0o755)
    )
    observed = handle.observe_preparation()
    assert observed.transition_order == (
        (0, "new", "directory_create"),
        (1, "new/child", "directory_create"),
        (2, "new/child/file", "CREATE"),
    )
    scratch = observed.scratch_effects
    assert tuple(row.kind for row in scratch) == ("create", "mode", "sync", "unlink")
    assert tuple(row.requested_mode for row in scratch) == (0o600, 0o755, None, None)
    assert all(row.ordinal == 2 and row.role == "replacement_body" for row in scratch)
    assert len({row.path for row in scratch}) == 1
    assert scratch[0].path.startswith("new/child/.aware-tree-")
    assert not any(tmp_path.iterdir())
    handle.validate_current()
    handle.release()


@pytest.mark.parametrize("mutation", ("bytes", "mode", "replacement", "scratch"))
def test_freshness_refusal_retires_and_restoration_cannot_revive(tmp_path, mutation):
    target = tmp_path / "file"
    target.write_bytes(b"before")
    handle = tree.retain_confined_tree_projection(
        root=tmp_path,
        request=request(tmp_path, kind=physical.ConfinedMutationKind.UPDATE),
    )
    if mutation == "bytes":
        target.write_bytes(b"changed")
    elif mutation == "mode":
        target.chmod(0o755)
    elif mutation == "replacement":
        other = tmp_path / "other"
        other.write_bytes(b"before")
        other.replace(target)
    else:
        scratch = tmp_path / handle.observe_preparation().scratch_effects[0].path
        scratch.write_bytes(b"foreign")
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.validate_current()
    assert caught.value.cleanup.cleanup_state == "completed"
    assert caught.value.observation.effects == ()
    target.write_bytes(b"before")
    target.chmod(0o644)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal, match="terminal"):
        handle.validate_current()
    if mutation == "scratch":
        assert scratch.read_bytes() == b"foreign"


@pytest.mark.parametrize("effect", ("finish", "validate_consumed_current"))
def test_premature_completion_entrances_cannot_claim_success_or_change_tree(
    tmp_path, effect
):
    native = request(tmp_path)
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    with pytest.raises(
        tree.RetainedPhysicalTreeProjectionRefusal, match="incomplete|required"
    ):
        getattr(handle, effect)()
    assert not (tmp_path / "file").exists()
    assert handle.observe_effects().effects == ()
    handle.release()


@pytest.mark.parametrize("operation", (copy.copy, copy.deepcopy, pickle.dumps))
def test_constructor_copy_pickle_and_forged_handles_refuse(tmp_path, operation):
    with pytest.raises(TypeError):
        tree.RetainedPhysicalTreeProjection()
    forged = object.__new__(tree.RetainedPhysicalTreeProjection)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal, match="not_issued"):
        forged.observe_preparation()
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    with pytest.raises(TypeError):
        operation(handle)
    handle.validate_current()
    handle.release()


@pytest.mark.parametrize("components", (64, 65, 128))
def test_deep_paths_use_constant_live_descriptors_not_depth_limit(tmp_path, components):
    path = "/".join(["a"] * components)
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    native = request(
        tmp_path,
        path=path,
        limits=physical.ConfinedTreeLimits(maximum_live_descriptors=3),
    )
    if components == 128:
        # The path is canonical; its complete sequence of preserved-ancestor
        # checks needs over 8192 actual cleanup records. Refuse that conjunctive
        # lifecycle budget before effects, not via a new component-depth bound.
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
            tree.retain_confined_tree_projection(root=tmp_path, request=native)
        assert caught.value.code == "tree_cleanup_resource_capacity_exceeded"
        assert caught.value.observation.effects == ()
        assert not target.exists()
        return
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    state = tree._HANDLES[handle]
    assert state.ledger.peak_live <= 3
    handle.validate_current()
    assert state.ledger.peak_live <= 3
    assert not target.exists()
    handle.release()


def test_failed_acquisition_and_low_metadata_leave_no_target_effects(tmp_path):
    native = request(
        tmp_path, limits=physical.ConfinedTreeLimits(maximum_live_descriptors=1)
    )
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        tree.retain_confined_tree_projection(root=tmp_path, request=native)
    assert caught.value.cleanup.cleanup_state == "completed"
    assert caught.value.observation.effects == ()
    assert not any(tmp_path.iterdir())
    native = request(
        tmp_path, limits=physical.ConfinedTreeLimits(maximum_metadata_bytes=64)
    )
    with pytest.raises(
        tree.RetainedPhysicalTreeProjectionRefusal, match="metadata"
    ) as caught:
        tree.retain_confined_tree_projection(root=tmp_path, request=native)
    assert caught.value.cleanup.resources == ()


def test_read_interruption_releases_original_descriptors_and_preserves_evidence(
    tmp_path, monkeypatch
):
    (tmp_path / "file").write_bytes(b"before")
    native = request(tmp_path, kind=physical.ConfinedMutationKind.UPDATE)
    monkeypatch.setattr(
        os, "read", lambda *args: (_ for _ in ()).throw(KeyboardInterrupt())
    )
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        tree.retain_confined_tree_projection(root=tmp_path, request=native)
    assert caught.value.cleanup.cleanup_state == "completed"
    assert caught.value.observation.effects == ()
    assert isinstance(caught.value.__cause__, KeyboardInterrupt)


def test_unknown_close_is_reported_and_never_retried(tmp_path, monkeypatch):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._HANDLES[handle]
    original = os.close
    calls = []

    def interrupted(fd):
        calls.append(fd)
        original(fd)
        raise KeyboardInterrupt()

    monkeypatch.setattr(os, "close", interrupted)
    for _ in range(2):
        with pytest.raises(
            tree.RetainedPhysicalTreeProjectionRefusal, match="cleanup_unknown"
        ) as caught:
            handle.release()
        assert not caught.value.cleanup.ledger_complete
    assert calls == [state.ledger.history[0].record.descriptor]
    assert state.request is None


def test_unknown_walk_close_stops_all_further_acquisition(tmp_path, monkeypatch):
    (tmp_path / "parent").mkdir()
    native = request(tmp_path, path="parent/file")
    original_open, original_close = os.open, os.close
    uncertain = False

    def opened(*args, **kwargs):
        assert not uncertain, "continued acquisition after unknown disposal"
        return original_open(*args, **kwargs)

    def closed(descriptor):
        nonlocal uncertain
        original_close(descriptor)
        if not uncertain:
            uncertain = True
            raise KeyboardInterrupt()

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "close", closed)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        tree.retain_confined_tree_projection(root=tmp_path, request=native)
    assert caught.value.cleanup.cleanup_state == "unknown"
    assert not caught.value.cleanup.ledger_complete
    assert not (tmp_path / "parent/file").exists()


@pytest.mark.parametrize("kind", ("symlink", "fifo", "hardlink"))
def test_non_regular_or_linked_target_refuses_without_effects(tmp_path, kind):
    target = tmp_path / "file"
    native = request(tmp_path)
    if kind == "symlink":
        other = tmp_path / "other"
        other.write_bytes(b"foreign")
        target.symlink_to(other)
    elif kind == "fifo":
        os.mkfifo(target)
    else:
        other = tmp_path / "other"
        other.write_bytes(b"foreign")
        os.link(other, target)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        tree.retain_confined_tree_projection(root=tmp_path, request=native)
    assert target.exists()


def test_gc_and_worker_validation_preserve_original_lifetime(tmp_path):
    import concurrent.futures

    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._HANDLES[handle]
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(handle.validate_current).result()
    root_descriptor = state.root_fd
    del handle
    gc.collect()
    with pytest.raises(OSError):
        os.fstat(root_descriptor)
    assert state.request is None


def test_process_rejection_happens_before_inherited_lock_and_io(tmp_path, monkeypatch):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._HANDLES[handle]

    class Forbidden:
        def __enter__(self):
            raise AssertionError("foreign inherited lock")

    old = state.lock
    state.lock = Forbidden()
    with monkeypatch.context() as patch:
        patch.setattr(os, "getpid", lambda: state.pid + 1)
        with pytest.raises(
            tree.RetainedPhysicalTreeProjectionRefusal, match="foreign_process"
        ):
            handle.validate_current()
    state.lock = old
    handle.validate_current()
    handle.release()


def execute_all(handle):
    rows = []
    for _ in handle.observe_preparation().transition_order:
        rows.append(handle.apply_next_transition())
        handle.validate_current()
    final = handle.finish()
    handle.validate_consumed_current()
    return rows, final


@pytest.mark.parametrize("kind", tuple(physical.ConfinedMutationKind))
@pytest.mark.parametrize("mode", (0o644, 0o755))
def test_genuine_file_transition_finish_and_consumed_postimage(tmp_path, kind, mode):
    if kind is not physical.ConfinedMutationKind.CREATE:
        (tmp_path / "file").write_bytes(b"before")
        (tmp_path / "file").chmod(0o640)
    native = request(tmp_path, kind=kind, mode=mode)
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    rows, final = execute_all(handle)
    assert len(rows) == final.completed_prefix == 1
    assert rows[0].effect_state is physical.ConfinedMutationEffectState.APPLIED
    assert rows[0].completion_state == "complete"
    assert rows[0].convergence_state == "matched"
    assert final.phase == "consumed" and final.ledger_complete
    if kind is physical.ConfinedMutationKind.DELETE:
        assert not (tmp_path / "file").exists()
        assert not rows[0].after.exists
    else:
        assert (tmp_path / "file").read_bytes() == b"new"
        assert stat.S_IMODE((tmp_path / "file").stat().st_mode) == mode
        assert rows[0].after == pin(tmp_path / "file")
    assert not final.residual_scratch
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal, match="terminal"):
        handle.apply_next_transition()
    original = handle.observe_effects().effects
    handle.release()
    assert handle.observe_effects().effects == original
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.validate_consumed_current()


@pytest.mark.parametrize("mask", (0o022, 0o077, 0o777))
def test_nested_directory_modes_are_exact_independent_of_umask(tmp_path, mask):
    native = request(tmp_path, path="a/b/file", mode=0o755)
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    prior = os.umask(mask)
    try:
        rows, final = execute_all(handle)
    finally:
        os.umask(prior)
    assert len(rows) == final.completed_prefix == 3
    assert all(
        stat.S_IMODE((tmp_path / path).stat().st_mode) == 0o755
        for path in ("a", "a/b", "a/b/file")
    )
    assert rows[0].kind == rows[1].kind == "directory_create"
    assert rows[2].kind == "CREATE"
    assert tree._HANDLES[handle].ledger.peak_live <= 64
    handle.release()


@pytest.mark.parametrize("change_mode", (False, True))
def test_current_and_mode_only_keep_inode_and_have_no_byte_publication(
    tmp_path, change_mode
):
    target = tmp_path / "file"
    target.write_bytes(b"new")
    target.chmod(0o644)
    inode = target.stat().st_ino
    handle = tree.retain_confined_tree_projection(
        root=tmp_path,
        request=request(
            tmp_path,
            kind=physical.ConfinedMutationKind.UPDATE,
            mode=0o755 if change_mode else 0o644,
        ),
    )
    rows, _ = execute_all(handle)
    assert target.stat().st_ino == inode and target.read_bytes() == b"new"
    assert not any(
        row.kind in ("file_create", "file_replace", "scratch_create")
        for row in rows[0].effects
    )
    assert rows[0].effect_state is (
        physical.ConfinedMutationEffectState.APPLIED
        if change_mode
        else physical.ConfinedMutationEffectState.NONE
    )
    handle.release()


@pytest.mark.parametrize("boundary", ("finish", "consumed"))
def test_postimage_drift_refuses_without_replaying_known_effects(tmp_path, boundary):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    handle.apply_next_transition()
    if boundary == "consumed":
        handle.finish()
    (tmp_path / "file").write_bytes(b"foreign postimage")
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        getattr(
            handle, "finish" if boundary == "finish" else "validate_consumed_current"
        )()
    assert caught.value.observation.completed_prefix == 1
    assert any(
        row.kind == "file_create"
        and row.state is physical.ConfinedMutationEffectState.APPLIED
        for row in caught.value.observation.effects
    )
    assert (tmp_path / "file").read_bytes() == b"foreign postimage"
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.apply_next_transition()


def test_unknown_replace_return_never_becomes_success_from_matching_bytes(
    tmp_path, monkeypatch
):
    target = tmp_path / "file"
    target.write_bytes(b"before")
    handle = tree.retain_confined_tree_projection(
        root=tmp_path,
        request=request(tmp_path, kind=physical.ConfinedMutationKind.UPDATE),
    )
    original = os.replace

    def lost_return(*args, **kwargs):
        original(*args, **kwargs)
        raise KeyboardInterrupt("replace return unavailable")

    monkeypatch.setattr(os, "replace", lost_return)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.apply_next_transition()
    assert target.read_bytes() == b"new"
    assert (
        caught.value.transition.effect_state
        is physical.ConfinedMutationEffectState.UNKNOWN
    )
    assert caught.value.observation.completed_prefix == 0
    assert not caught.value.observation.ledger_complete
    assert "file" not in dict(caught.value.observation.final_entries)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.finish()


def test_applied_file_survives_directory_sync_failure(tmp_path, monkeypatch):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    original = os.fsync

    def failed(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("sync unavailable")
        return original(fd)

    monkeypatch.setattr(os, "fsync", failed)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.apply_next_transition()
    assert (tmp_path / "file").read_bytes() == b"new"
    assert (
        caught.value.transition.effect_state
        is physical.ConfinedMutationEffectState.APPLIED
    )
    assert not caught.value.transition.durability_confirmed
    assert any(
        row.kind == "directory_sync"
        and row.state is physical.ConfinedMutationEffectState.UNKNOWN
        for row in caught.value.observation.effects
    )
    assert caught.value.observation.completed_prefix == 0


def test_create_race_preserves_competing_target_and_cleans_only_original_scratch(
    tmp_path, monkeypatch
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    original = os.link

    def competed(*args, **kwargs):
        (tmp_path / "file").write_bytes(b"foreign")
        return original(*args, **kwargs)

    monkeypatch.setattr(os, "link", competed)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.apply_next_transition()
    assert (tmp_path / "file").read_bytes() == b"foreign"
    assert (
        caught.value.transition.effect_state
        is physical.ConfinedMutationEffectState.NONE
    )
    assert not any(path.name.startswith(".aware-tree-") for path in tmp_path.iterdir())


def test_release_waits_for_original_worker_and_reentrant_release_refuses(
    tmp_path, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    original = os.link
    entered, proceed = Event(), Event()

    def delayed(*args, **kwargs):
        with pytest.raises(
            tree.RetainedPhysicalTreeProjectionRefusal, match="in_progress"
        ):
            handle.release()
        entered.set()
        assert proceed.wait(2)
        return original(*args, **kwargs)

    monkeypatch.setattr(os, "link", delayed)
    with ThreadPoolExecutor(max_workers=2) as workers:
        applied = workers.submit(handle.apply_next_transition)
        assert entered.wait(2)
        cleanup = workers.submit(handle.release)
        assert not cleanup.done()
        proceed.set()
        assert applied.result().completion_state == "complete"
        assert cleanup.result().cleanup_state == "completed"
    assert (tmp_path / "file").read_bytes() == b"new"


def test_partial_prefix_survives_stale_suffix_and_no_ordinal_can_replay(tmp_path):
    first = request(tmp_path, path="a").files[0]
    second = request(tmp_path, path="b").files[0]
    native = physical.ConfinedTreeProjectionRequest(
        "two", (tmp_path.stat().st_dev, tmp_path.stat().st_ino), (first, second), ()
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    one = handle.apply_next_transition()
    (tmp_path / "b").write_bytes(b"competing suffix")
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.apply_next_transition()
    assert (
        one.completion_state == "complete" and (tmp_path / "a").read_bytes() == b"new"
    )
    assert caught.value.observation.completed_prefix == 1
    assert caught.value.observation.pending_ordinal == 1
    assert caught.value.transition.ordinal == 1
    assert (tmp_path / "b").read_bytes() == b"competing suffix"
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.apply_next_transition()


def test_final_return_failure_is_typed_with_known_publication_and_spent_ordinal(
    tmp_path, monkeypatch
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )

    def unavailable(*args, **kwargs):
        raise OSError("result construction unavailable")

    monkeypatch.setattr(tree, "_transition", unavailable)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.apply_next_transition()
    assert (tmp_path / "file").read_bytes() == b"new"
    assert caught.value.observation.completed_prefix == 1
    assert any(
        row.kind == "file_create"
        and row.state is physical.ConfinedMutationEffectState.APPLIED
        for row in caught.value.observation.effects
    )
    assert not caught.value.observation.ledger_complete
    assert "tree_transition_return_unavailable" in caught.value.observation.diagnostics
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.apply_next_transition()


def test_failed_directory_mode_keeps_created_prefix_without_completing_ordinal(
    tmp_path, monkeypatch
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path, path="d/file")
    )
    original = os.chmod

    def denied(path, mode, *args, **kwargs):
        if str(path).startswith("/proc/self/fd/"):
            raise PermissionError("requested mode denied")
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(os, "chmod", denied)
    prior = os.umask(0o077)
    try:
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
            handle.apply_next_transition()
    finally:
        os.umask(prior)
    assert (tmp_path / "d").is_dir() and not (tmp_path / "d/file").exists()
    assert caught.value.observation.completed_prefix == 0
    assert (
        caught.value.transition.effect_state
        is physical.ConfinedMutationEffectState.UNKNOWN
    )
    assert any(
        row.kind == "directory_create"
        and row.state is physical.ConfinedMutationEffectState.APPLIED
        and row.after_mode == 0o700
        for row in caught.value.observation.effects
    )


def test_real_scratch_close_interruption_never_retries_and_prevents_publication(
    tmp_path, monkeypatch
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    original = os.close
    closed = []

    def interrupted(fd):
        is_scratch = not stat.S_ISDIR(os.fstat(fd).st_mode)
        original(fd)
        if is_scratch:
            closed.append(fd)
            raise KeyboardInterrupt("scratch close return lost")

    monkeypatch.setattr(os, "close", interrupted)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.apply_next_transition()
    assert len(closed) == 1 and not (tmp_path / "file").exists()
    assert caught.value.cleanup.cleanup_state == "unknown"
    assert any(
        row.kind == "descriptor_release"
        and row.state is physical.ConfinedMutationEffectState.UNKNOWN
        for row in caught.value.observation.effects
    )
    assert handle.observe_effects().completed_prefix == 0


def test_foreign_relocated_scratch_is_preserved_with_unknown_cleanup(
    tmp_path, monkeypatch
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    scratch = tmp_path / handle.observe_preparation().scratch_effects[0].path

    def relocated(*args, **kwargs):
        scratch.rename(tmp_path / "relocated-owned-scratch")
        scratch.write_bytes(b"foreign occupant")
        raise OSError("publication unavailable")

    monkeypatch.setattr(os, "link", relocated)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.apply_next_transition()
    assert scratch.read_bytes() == b"foreign occupant"
    assert (tmp_path / "relocated-owned-scratch").read_bytes() == b"new"
    assert caught.value.cleanup.cleanup_state == "unknown"
    assert str(scratch.relative_to(tmp_path)) in caught.value.cleanup.residual_scratch


def test_execution_evidence_quota_refuses_before_any_transition_effect(tmp_path):
    limit = physical.ConfinedTreeLimits(maximum_metadata_bytes=12000)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        tree.retain_confined_tree_projection(
            root=tmp_path, request=request(tmp_path, limits=limit)
        )
    assert not (tmp_path / "file").exists() and caught.value.observation.effects == ()


def test_required_1000_transition_8mib_sample_prepares_without_effects(tmp_path):
    total = 8 * 1024 * 1024
    base, remainder = divmod(total, 1000)
    bodies = (b"x" * base, b"x" * (base + 1))
    rows = tuple(
        physical.ConfinedTreeFileTransition(
            f"f{i:04d}",
            physical.ConfinedMutationKind.CREATE,
            physical.ConfinedTreeEntryPin(False),
            bodies[i < remainder],
            physical._content_digest(bodies[i < remainder]),
            len(bodies[i < remainder]),
            0o644,
        )
        for i in range(1000)
    )
    value = tmp_path.stat()
    original = physical.ConfinedTreeProjectionRequest(
        "required-qualification-sample", (value.st_dev, value.st_ino), rows, ()
    )
    assert sum(row.size_bytes for row in rows) == total
    assert original.limits.maximum_metadata_bytes == 8 * 1024 * 1024
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=original)
    try:
        prepared = handle.observe_preparation()
        assert len(prepared.transition_order) == 1000
        assert len(prepared.scratch_effects) == 4000
        assert handle.observe_effects().effects == ()
        assert snapshot(tmp_path) == {}
        state = tree._issued(handle)
        assert 0 < state.execution_reserve < original.limits.maximum_metadata_bytes
        tree._metadata_check(state)
    finally:
        assert handle.release().cleanup_state == "completed"


@pytest.mark.parametrize("kind", tuple(physical.ConfinedMutationKind))
def test_reserved_native_slots_bound_real_effects_and_cleanup(tmp_path, kind):
    if kind is not physical.ConfinedMutationKind.CREATE:
        (tmp_path / "file").write_bytes(b"before")
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path, kind=kind)
    )
    state = tree._issued(handle)
    reserved = state.execution_reserve
    original_size = tree._effect_slot_capacity("file", 0)
    result = handle.apply_next_transition()
    from dataclasses import asdict

    assert len(tree._wire([asdict(row) for row in result.effects])) < reserved
    for row in result.effects:
        assert len(tree._wire(asdict(row))) < tree._effect_slot_capacity(row.path, 0)
    assert original_size > len(tree._wire({"path": "file"}))
    handle.finish()
    tree._metadata_check(state)
    handle.release()


def test_effect_slot_reservation_counts_json_escaping_and_unknown_fields():
    ordinary = tree._effect_slot_capacity("a" * 20, 0)
    escaped = tree._effect_slot_capacity('"' * 20, 8191)
    assert escaped - ordinary == 23  # escaped quotes plus ordinal digits


def test_reserved_slots_cover_uncertain_unlink_and_once_only_scratch_cleanup(
    tmp_path, monkeypatch
):
    from dataclasses import asdict

    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._issued(handle)
    reserved = state.execution_reserve
    original = os.unlink
    calls = []

    def uncertain_once(path, **kwargs):
        calls.append(path)
        if len(calls) == 1:
            raise KeyboardInterrupt("scratch unlink return unavailable")
        return original(path, **kwargs)

    monkeypatch.setattr(os, "unlink", uncertain_once)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.apply_next_transition()
    observed = caught.value.observation
    assert len(observed.effects) == 8
    assert len(tree._wire([asdict(row) for row in observed.effects])) < reserved
    assert (tmp_path / "file").read_bytes() == b"new"
    assert len(calls) == 2
    assert len(tuple(tmp_path.iterdir())) == 1
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.apply_next_transition()


def test_reduced_ceiling_still_refuses_reserved_sequence_before_effects(
    tmp_path, monkeypatch
):
    original = tree._reserve_execution

    def reduced_ceiling(state):
        original(state)
        from dataclasses import replace

        state.ledger.limits = replace(
            state.ledger.limits,
            maximum_metadata_bytes=state.execution_reserve
            + state.ledger.metadata_reserved
            - 1,
        )
        tree._metadata_check(state)

    monkeypatch.setattr(tree, "_reserve_execution", reduced_ceiling)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        tree.retain_confined_tree_projection(root=tmp_path, request=request(tmp_path))
    assert caught.value.code == "tree_metadata_capacity_exceeded"
    assert caught.value.observation.effects == ()
    assert snapshot(tmp_path) == {}


def test_next_check_is_intrinsic_non_spending_and_local_to_the_original_ordinal(
    tmp_path,
):
    from dataclasses import replace

    first = request(tmp_path)
    rows = (replace(first.files[0], path="a"), replace(first.files[0], path="b"))
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=replace(first, files=rows)
    )
    (tmp_path / "b").write_bytes(b"foreign later leaf")
    handle.validate_next_current()
    state = tree._issued(handle)
    assert state.next_ordinal == 0
    assert handle.observe_effects().effects == ()
    assert handle.apply_next_transition().ordinal == 0
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.validate_next_current()
    assert caught.value.observation.completed_prefix == 1
    assert (tmp_path / "a").read_bytes() == b"new"
    assert (tmp_path / "b").read_bytes() == b"foreign later leaf"
    (tmp_path / "b").unlink()
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.apply_next_transition()


def test_full_validator_still_detects_drift_at_an_unselected_later_leaf(tmp_path):
    from dataclasses import replace

    native = request(tmp_path)
    native = replace(
        native,
        files=(replace(native.files[0], path="a"), replace(native.files[0], path="b")),
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    (tmp_path / "b").write_bytes(b"foreign")
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.validate_current()
    assert not (tmp_path / "a").exists()


def test_next_check_does_not_certify_earlier_postimages_or_replace_full_finish(
    tmp_path,
):
    from dataclasses import replace

    native = request(tmp_path)
    native = replace(
        native,
        files=(replace(native.files[0], path="a"), replace(native.files[0], path="b")),
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    handle.validate_next_current()
    handle.apply_next_transition()
    (tmp_path / "a").write_bytes(b"changed earlier result")
    handle.validate_next_current()
    handle.apply_next_transition()
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.finish()
    assert caught.value.observation.completed_prefix == 2
    assert (tmp_path / "a").read_bytes() == b"changed earlier result"
    assert (tmp_path / "b").read_bytes() == b"new"


@pytest.mark.parametrize("change", ("root_mode", "ancestor_mode", "scratch"))
def test_next_guard_drift_retires_the_original_without_effects(tmp_path, change):
    if change == "ancestor_mode":
        (tmp_path / "parent").mkdir()
    native = request(
        tmp_path, path="parent/file" if change == "ancestor_mode" else "file"
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    if change == "root_mode":
        original = tmp_path.stat().st_mode & 0o777
        tmp_path.chmod(0o700 if original != 0o700 else 0o750)
    elif change == "ancestor_mode":
        (tmp_path / "parent").chmod(0o700)
    else:
        scratch = handle.observe_preparation().scratch_effects[0].path
        (tmp_path / scratch).write_bytes(b"competing scratch")
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.validate_next_current()
    assert caught.value.observation.effects == ()
    assert caught.value.observation.phase == "released"
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.validate_next_current()


def test_borrowed_root_is_one_original_acquisition_with_one_actual_close(
    tmp_path, monkeypatch
):
    opened, closed = [], []
    original_open, original_close = os.open, os.close

    def opening(path, *args, **kwargs):
        if path == tmp_path:
            opened.append(path)
        return original_open(path, *args, **kwargs)

    def closing(fd):
        closed.append(fd)
        return original_close(fd)

    monkeypatch.setattr(os, "open", opening)
    monkeypatch.setattr(os, "close", closing)
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._issued(handle)
    descriptor = state.root_fd
    for _ in range(10):
        handle.validate_current()
        handle.validate_next_current()
    assert len(opened) == 1 and closed == []
    assert len(state.ledger.history) == 1
    assert state.ledger.root_borrows == 0
    assert handle.release().cleanup_state == "completed"
    assert closed == [descriptor]
    assert handle.release().cleanup_state == "completed"
    assert closed == [descriptor]


@pytest.mark.parametrize("boundary", ("consumed", "released", "finished_ordinals"))
def test_next_currentness_cannot_renew_a_terminal_or_spent_sequence(tmp_path, boundary):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    handle.apply_next_transition()
    if boundary != "finished_ordinals":
        handle.finish()
    if boundary == "released":
        handle.release()
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.validate_next_current()
    assert (tmp_path / "file").read_bytes() == b"new"
    handle.release()


def test_required_native_ordinal_lifecycle_keeps_all_actual_custody_and_finishes(
    tmp_path,
):
    total = 8 * 1024 * 1024
    base, remainder = divmod(total, 1000)
    bodies = (b"x" * base, b"x" * (base + 1))
    rows = tuple(
        physical.ConfinedTreeFileTransition(
            f"f{i:04d}",
            physical.ConfinedMutationKind.CREATE,
            physical.ConfinedTreeEntryPin(False),
            bodies[i < remainder],
            physical._content_digest(bodies[i < remainder]),
            len(bodies[i < remainder]),
            0o644,
        )
        for i in range(1000)
    )
    value = tmp_path.stat()
    native = physical.ConfinedTreeProjectionRequest(
        "required-qualification-sample", (value.st_dev, value.st_ino), rows, ()
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    try:
        state = tree._issued(handle)
        for _ in range(5):
            handle.validate_current()
        initial_refs = {
            row.resource_ref for row in state.ledger.resource_observations()
        }
        for ordinal in range(1000):
            handle.validate_next_current()
            assert handle.apply_next_transition().ordinal == ordinal
        assert handle.finish().completed_prefix == 1000
        for _ in range(2):
            handle.validate_consumed_current()
        assert initial_refs <= {
            row.resource_ref for row in state.ledger.resource_observations()
        }
        assert len(tuple(tmp_path.iterdir())) == 1000
        assert state.ledger.peak_live <= native.limits.maximum_live_descriptors
    finally:
        handle.release()


def test_cached_resource_snapshots_are_lossless_and_detached_from_later_release(
    tmp_path,
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._issued(handle)
    before = state.ledger.resource_observations()
    assert before is state.ledger.resource_observations()
    handle.apply_next_transition()
    after = state.ledger.resource_observations()
    assert {row.resource_ref for row in before} < {row.resource_ref for row in after}
    assert len(after) == len(state.ledger.history)
    assert before[0].ownership == "owned"
    assert handle.release().cleanup_state == "completed"
    released = state.ledger.resource_observations()
    assert before[0].ownership == "owned"
    assert released[0].ownership == "released"
    assert {row.resource_ref for row in released} == {
        slot.ref for slot in state.ledger.history
    }


def test_lifecycle_budget_bounds_complete_native_serialized_evidence(tmp_path):
    from dataclasses import asdict

    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._issued(handle)

    def check():
        actual = len(
            tree._wire(
                {
                    "request": tree._request_descriptor(state.request),
                    "preparation": asdict(state.preparation),
                    "effects": asdict(handle.observe_effects()),
                    "cleanup": asdict(tree._cleanup(state)),
                    "last_transition": asdict(state.last_transition)
                    if state.last_transition
                    else None,
                }
            )
        )
        bound = (
            state.ledger.metadata_other
            + state.ledger.request_metadata
            + 2
            * (state.ledger.resource_reserved + state.ledger.future_resource_reserved)
        )
        assert actual < bound <= state.ledger.limits.maximum_metadata_bytes

    check()
    handle.validate_current()
    handle.validate_next_current()
    handle.apply_next_transition()
    check()
    handle.finish()
    handle.validate_consumed_current()
    check()
    handle.release()


def test_lost_root_borrow_return_drains_original_once_and_preserves_uncertainty(
    tmp_path, monkeypatch
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._issued(handle)
    original_open, original_close = state.ledger.open, os.close
    closes = []
    failed = False

    def opened(path, *args, **kwargs):
        nonlocal failed
        fd = original_open(path, *args, **kwargs)
        if path == tmp_path and not failed:
            failed = True
            raise KeyboardInterrupt("borrow return unavailable")
        return fd

    def closed(fd):
        closes.append(fd)
        return original_close(fd)

    monkeypatch.setattr(state.ledger, "open", opened)
    monkeypatch.setattr(os, "close", closed)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.validate_next_current()
    assert caught.value.observation.effects == ()
    assert caught.value.cleanup.cleanup_state == "unknown"
    assert "tree_root_borrow_unsettled" in caught.value.cleanup.diagnostics
    assert closes == [state.ledger.history[0].record.descriptor]
    assert state.ledger.root_borrows == 0
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
        handle.release()
    assert len(closes) == 1


def test_snapshot_failure_after_real_acquisition_keeps_cleanup_custody(
    tmp_path, monkeypatch
):
    (tmp_path / "file").write_bytes(b"before")
    handle = tree.retain_confined_tree_projection(
        root=tmp_path,
        request=request(tmp_path, kind=physical.ConfinedMutationKind.UPDATE),
    )
    state = tree._issued(handle)
    original = state.ledger.refresh
    failed = False
    before_fds = len(tuple((tmp_path.__class__("/proc/self/fd")).iterdir()))

    def refresh(slot):
        nonlocal failed
        if slot.state == "owned" and not failed:
            failed = True
            raise OSError("snapshot return unavailable")
        return original(slot)

    monkeypatch.setattr(state.ledger, "refresh", refresh)
    with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
        handle.validate_next_current()
    assert caught.value.observation.effects == ()
    assert caught.value.cleanup.cleanup_state == "completed"
    assert all(row.ownership == "released" for row in caught.value.cleanup.resources)
    assert len(tuple((tmp_path.__class__("/proc/self/fd")).iterdir())) == before_fds - 1
    assert (tmp_path / "file").read_bytes() == b"before"


def test_forecast_exact_frozen_shapes_and_original_writer_conservation():
    import ast
    import json
    import subprocess
    from dataclasses import fields
    from pathlib import Path

    root = next(p for p in Path(__file__).parents if (p / "aware.repo.toml").exists())
    inputs = json.loads(
        (
            root
            / "docs/reports/filesystem-tree-capacity-forecast-implementation-inputs-20261013.json"
        ).read_text()
    )
    current = ast.parse(Path(tree.__file__).read_text())
    classes = {
        node.name: node for node in current.body if isinstance(node, ast.ClassDef)
    }
    for name, shape in inputs["shapes"].items():
        declared = {
            node.target.id: ast.unparse(node.annotation)
            for node in classes[name].body
            if isinstance(node, ast.AnnAssign)
        }
        assert declared == shape
        assert tuple(declared) == tuple(f.name for f in fields(getattr(tree, name)))
        assert getattr(tree, name).__dataclass_params__.frozen
    original = ast.parse(
        subprocess.check_output(
            ["git", "show", inputs["captured_head"] + ":" + inputs["pins"][0]["path"]],
            text=True,
        )
    )
    for name in (
        "_TreeLedger",
        "_TreeWriteIO",
        "_apply_file",
        "_apply_directory",
        "_read_entry",
        "_dispatch",
        "_adopt_target",
        "_cleanup_scratch",
    ):
        assert ast.dump(
            next(n for n in current.body if getattr(n, "name", None) == name)
        ) == ast.dump(
            next(n for n in original.body if getattr(n, "name", None) == name)
        )


@pytest.mark.parametrize("kind", tuple(physical.ConfinedMutationKind))
def test_forecast_no_io_no_capacity_renewal_and_exact_original_correlation(
    tmp_path, monkeypatch, kind
):
    from dataclasses import asdict

    if kind is not physical.ConfinedMutationKind.CREATE:
        (tmp_path / "file").write_bytes(b"before")
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path, kind=kind)
    )
    state = tree._issued(handle)
    before = (
        len(state.ledger.history),
        state.ledger.resource_reserved,
        state.ledger.future_resource_reserved,
        state.ledger.future_resource_rows,
    )
    original = handle.observe_preparation()

    def forbidden(*_a, **_k):
        pytest.fail("forecast must not perform IO or disposal")

    try:
        with monkeypatch.context() as patch:
            for name in (
                "open",
                "close",
                "stat",
                "fstat",
                "read",
                "write",
                "fsync",
                "unlink",
                "mkdir",
                "chmod",
                "replace",
            ):
                patch.setattr(os, name, forbidden)
            first = handle.observe_capacity_forecast()
            assert first == handle.observe_capacity_forecast()
            assert first.forecast_wire_bytes == len(tree._wire(asdict(first)))
        assert (
            len(state.ledger.history),
            state.ledger.resource_reserved,
            state.ledger.future_resource_reserved,
            state.ledger.future_resource_rows,
        ) == before
        assert first.preparation_ref == original.preparation_ref
        assert first.request_digest == original.request_digest
        assert first.transition_order == original.transition_order
        assert first.schedule.full_validation_calls_remaining == 1
        assert first.observed_acquisition_rows == before[0]
        assert first.observed_scratch_rows == 0 and first.remaining_scratch_rows == len(
            state.scratch_paths
        )
        assert handle.observe_effects().effects == ()
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
            tree.RetainedPhysicalTreeProjection.observe_capacity_forecast(first)
    finally:
        handle.release()


def test_forecast_spends_only_pre_reserved_full_read_and_never_rearms_it(tmp_path):
    (tmp_path / "file").write_bytes(b"before")
    handle = tree.retain_confined_tree_projection(
        root=tmp_path,
        request=request(tmp_path, kind=physical.ConfinedMutationKind.UPDATE),
    )
    state = tree._issued(handle)
    try:
        handle.validate_current()  # Before the final observation point: observed cost.
        forecast = handle.observe_capacity_forecast()
        future = state.ledger.future_resource_rows
        history = len(state.ledger.history)
        handle.validate_current()  # The reserved post-observation full check.
        assert len(state.ledger.history) == history + 1
        assert state.ledger.future_resource_rows == future - 1
        assert state.operation_revision > forecast.forecast_revision
        with pytest.raises(
            tree.RetainedPhysicalTreeProjectionRefusal, match="forecast_unavailable"
        ):
            handle.observe_capacity_forecast()
        assert state.phase == "prepared" and state.root_fd in state.ledger.active
        assert handle.observe_effects().effects == ()
    finally:
        handle.release()


@pytest.mark.parametrize("kind", tuple(physical.ConfinedMutationKind))
@pytest.mark.parametrize("nested", (False, True))
def test_forecast_bounds_genuine_complete_encoding_and_resource_history(
    tmp_path, kind, nested
):
    from dataclasses import asdict

    path = 'é"dir/file' if nested else "file"
    if nested:
        (tmp_path / 'é"dir').mkdir()
    if kind is not physical.ConfinedMutationKind.CREATE:
        (tmp_path / path).write_bytes(b"before")
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path, path=path, kind=kind)
    )
    state = tree._issued(handle)
    forecast = handle.observe_capacity_forecast()

    def check(prefix):
        bound = forecast.prefixes[prefix]
        cleanup = tree._cleanup(state)
        effects = handle.observe_effects()
        assert len(state.ledger.history) <= bound.maximum_acquisition_history_rows
        assert (
            len(cleanup.resources)
            <= bound.maximum_acquisition_history_rows
            + bound.maximum_scratch_history_rows
        )
        assert (
            len(tree._wire(asdict(cleanup)))
            <= bound.maximum_cleanup_wire_bytes + bound.release_extra_wire_bytes
        )
        assert len(effects.effects) <= bound.maximum_effect_rows
        assert (
            len(tree._wire([asdict(row) for row in effects.effects]))
            <= bound.maximum_effect_wire_bytes
        )
        assert (
            len(
                tree._wire([(path, asdict(pin)) for path, pin in effects.final_entries])
            )
            <= bound.maximum_postimage_wire_bytes
        )
        if state.last_transition is not None:
            assert (
                len(tree._wire(asdict(state.last_transition)))
                <= bound.maximum_latest_return_wire_bytes
            )
        for row in cleanup.resources:
            assert (
                len(tree._wire(asdict(row)))
                <= forecast.encoding.maximum_resource_record_bytes
            )
        for row in effects.effects:
            assert (
                len(tree._wire(asdict(row)))
                <= forecast.encoding.maximum_effect_record_bytes
            )

    try:
        check(0)
        handle.validate_current()
        check(0)
        while state.next_ordinal < len(forecast.transition_order):
            handle.validate_next_current()
            handle.apply_next_transition()
            check(state.completed_prefix)
        handle.finish()
        handle.validate_consumed_current()
        handle.validate_consumed_current()
        check(state.completed_prefix)
        handle.release()
        check(state.completed_prefix)
    finally:
        handle.release()


@pytest.mark.parametrize("reason", ("busy", "uncertain", "phase", "guard"))
def test_forecast_rejection_never_disposes_original_custody(
    tmp_path, monkeypatch, reason
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._issued(handle)
    try:
        with monkeypatch.context() as patch:
            if reason == "busy":
                patch.setattr(state, "busy", True)
            elif reason == "uncertain":
                patch.setattr(state.ledger, "context_unknown", True)
            elif reason == "phase":
                patch.setattr(state, "phase", "active")
            else:
                patch.setattr(state, "next_guard_ordinal", 0)
            with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
                handle.observe_capacity_forecast()
            assert state.root_fd in state.ledger.active
            assert not state.ledger.active[state.root_fd].attempted
        assert (
            handle.observe_capacity_forecast().preparation_ref
            == handle.observe_preparation().preparation_ref
        )
    finally:
        handle.release()


@pytest.mark.parametrize("replacement", ("handle", "schema", "constructor"))
def test_forecast_substitution_refuses_without_execution_or_disposal(
    tmp_path, monkeypatch, replacement
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._issued(handle)
    observe = tree.RetainedPhysicalTreeProjection.observe_capacity_forecast
    calls = []

    def foreign(*_a, **_k):
        calls.append(True)
        pytest.fail("foreign behavior must not execute")

    try:
        with monkeypatch.context() as patch:
            if replacement == "handle":
                patch.setattr(
                    tree.RetainedPhysicalTreeProjection, "validate_current", foreign
                )
            elif replacement == "schema":
                patch.setattr(tree, "ConfinedTreeCapacitySchedule", foreign)
            else:
                patch.setattr(tree.ConfinedTreeCapacitySchedule, "__init__", foreign)
            with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
                observe(handle)
            assert calls == [] and state.root_fd in state.ledger.active
        assert (
            observe(handle).preparation_ref
            == handle.observe_preparation().preparation_ref
        )
    finally:
        handle.release()


def test_forecast_fork_refuses_before_inherited_lock_and_preserves_parent(
    tmp_path, monkeypatch
):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._issued(handle)

    class ForbiddenLock:
        def __enter__(self):
            pytest.fail("foreign process must not enter inherited lock")

        def __exit__(self, *_args):
            return False

    try:
        with monkeypatch.context() as patch:
            patch.setattr(state, "pid", state.pid + 1)
            patch.setattr(state, "lock", ForbiddenLock())
            with pytest.raises(
                tree.RetainedPhysicalTreeProjectionRefusal, match="foreign_process"
            ):
                handle.observe_capacity_forecast()
            assert state.root_fd in state.ledger.active
        assert (
            handle.observe_capacity_forecast().root_identity
            == handle.observe_preparation().root_identity
        )
    finally:
        handle.release()


@pytest.mark.parametrize(
    "field",
    (
        "forecast_wire_bytes",
        "observed_acquisition_rows",
        "forecast_revision",
        "remaining_acquisition_rows",
    ),
)
@pytest.mark.parametrize("value", (True, -1, 2**64, 1.0))
def test_forecast_strict_integer_and_complete_wire_refusals(tmp_path, field, value):
    from dataclasses import replace

    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    try:
        forecast = handle.observe_capacity_forecast()
        with pytest.raises(ValueError):
            replace(forecast, **{field: value})
        with pytest.raises(ValueError):
            replace(forecast, forecast_wire_bytes=forecast.forecast_wire_bytes + 1)
    finally:
        handle.release()


@pytest.mark.parametrize("prefix", (0, 1, 2))
@pytest.mark.parametrize("failure", ("write", "lost_link", "close"))
def test_forecast_bounds_real_terminal_failure_and_known_prefix(
    tmp_path, monkeypatch, prefix, failure
):
    from dataclasses import asdict

    root = tmp_path.stat()
    native = physical.ConfinedTreeProjectionRequest(
        "request:prefix-failure",
        (root.st_dev, root.st_ino),
        tuple(
            physical.ConfinedTreeFileTransition(
                f"file-{i}",
                physical.ConfinedMutationKind.CREATE,
                physical.ConfinedTreeEntryPin(False),
                b"new",
                physical._content_digest(b"new"),
                3,
                0o644,
            )
            for i in range(3)
        ),
        (),
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    state = tree._issued(handle)
    forecast = handle.observe_capacity_forecast()
    handle.validate_current()
    for _ in range(prefix):
        handle.validate_next_current()
        handle.apply_next_transition()
    original_link, original_close = os.link, os.close
    failed = False

    def write(*_args):
        raise OSError("injected original write refusal")

    def link(*args, **kwargs):
        original_link(*args, **kwargs)
        raise KeyboardInterrupt("original link return unavailable")

    def close(fd):
        nonlocal failed
        if fd != state.root_fd and not failed:
            failed = True
            original_close(fd)
            raise KeyboardInterrupt("original close return unavailable")
        original_close(fd)

    try:
        handle.validate_next_current()
        with monkeypatch.context() as patch:
            patch.setattr(
                os,
                "write"
                if failure == "write"
                else "link"
                if failure == "lost_link"
                else "close",
                write
                if failure == "write"
                else link
                if failure == "lost_link"
                else close,
            )
            with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
                handle.apply_next_transition()
        bound = forecast.prefixes[prefix]
        refusal = caught.value
        assert (
            len(state.ledger.history)
            <= bound.maximum_acquisition_history_rows
            + bound.terminal_extra_acquisition_rows
        )
        assert (
            len(tree._wire(asdict(refusal.cleanup)))
            <= bound.maximum_cleanup_wire_bytes
            + bound.terminal_extra_wire_bytes
            + bound.release_extra_wire_bytes
        )
        assert len(refusal.observation.effects) <= bound.maximum_effect_rows + 16
        assert (
            len(tree._wire([asdict(row) for row in refusal.observation.effects]))
            <= bound.maximum_effect_wire_bytes + bound.terminal_extra_wire_bytes
        )
        assert refusal.observation.completed_prefix == prefix
        assert all(
            (tmp_path / f"file-{i}").read_bytes() == b"new" for i in range(prefix)
        )
        if failure == "lost_link":
            assert (tmp_path / f"file-{prefix}").read_bytes() == b"new"
            assert any(
                row.state is physical.ConfinedMutationEffectState.UNKNOWN
                for row in refusal.observation.effects
            )
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
            handle.observe_capacity_forecast()
    finally:
        try:
            handle.release()
        except tree.RetainedPhysicalTreeProjectionRefusal:
            pass  # Original unknown disposal remains unknown; never retry a close.


def test_forecast_full_native_required_sample_keeps_history_and_bounds_every_prefix(
    tmp_path,
):
    root = tmp_path.stat()
    total = 8 * 1024 * 1024
    bodies = tuple(b"x" * (total // 1000 + (i < total % 1000)) for i in range(1000))
    native = physical.ConfinedTreeProjectionRequest(
        "request:forecast-required",
        (root.st_dev, root.st_ino),
        tuple(
            physical.ConfinedTreeFileTransition(
                f"file-{i:04}",
                physical.ConfinedMutationKind.CREATE,
                physical.ConfinedTreeEntryPin(False),
                body,
                physical._content_digest(body),
                len(body),
                0o644,
            )
            for i, body in enumerate(bodies)
        ),
        (),
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    state = tree._issued(handle)
    try:
        for _ in range(5):
            handle.validate_current()
        forecast = handle.observe_capacity_forecast()
        assert len(forecast.prefixes) == 1001
        assert forecast.forecast_wire_bytes < native.limits.maximum_metadata_bytes
        handle.validate_current()
        for ordinal in range(1000):
            handle.validate_next_current()
            handle.apply_next_transition()
            assert (
                len(state.ledger.history)
                <= forecast.prefixes[ordinal + 1].maximum_acquisition_history_rows
            )
        handle.finish()
        handle.validate_consumed_current()
        handle.validate_consumed_current()
        handle.release()
        assert len(state.ledger.history) == 5001
        assert (
            len(state.ledger.history)
            <= forecast.prefixes[-1].maximum_acquisition_history_rows
        )
        assert (
            len(handle.observe_effects().effects)
            <= forecast.prefixes[-1].maximum_effect_rows
        )
        assert (
            sum((tmp_path / f"file-{i:04}").stat().st_size for i in range(1000))
            == total
        )
    finally:
        handle.release()


@pytest.mark.parametrize("limit", (3, 4))
def test_forecast_lower_live_limit_is_checked_before_dispatch_without_disposal(
    tmp_path, limit
):
    (tmp_path / "parent").mkdir()
    handle = tree.retain_confined_tree_projection(
        root=tmp_path,
        request=request(
            tmp_path,
            path="parent/file",
            limits=physical.ConfinedTreeLimits(maximum_live_descriptors=limit),
        ),
    )
    state = tree._issued(handle)
    try:
        if limit == 3:
            with pytest.raises(
                tree.RetainedPhysicalTreeProjectionRefusal, match="descriptor_capacity"
            ):
                handle.observe_capacity_forecast()
        else:
            assert (
                handle.observe_capacity_forecast().schedule.transition_calls_remaining
                == 2
            )
        assert state.root_fd in state.ledger.active and state.effects == []
        assert not (tmp_path / "parent/file").exists()
    finally:
        handle.release()


def test_forecast_is_not_currentness_and_stale_inputs_still_terminally_refuse(tmp_path):
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    try:
        forecast = handle.observe_capacity_forecast()
        (tmp_path / "file").write_bytes(b"foreign")
        assert handle.observe_capacity_forecast() == forecast
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
            handle.validate_current()
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
            handle.observe_capacity_forecast()
        assert (tmp_path / "file").read_bytes() == b"foreign"
    finally:
        handle.release()


def test_forecast_empty_sequence_still_reserves_finish_and_release(tmp_path):
    from dataclasses import asdict

    root = tmp_path.stat()
    native = physical.ConfinedTreeProjectionRequest(
        "empty", (root.st_dev, root.st_ino), (), ()
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    try:
        forecast = handle.observe_capacity_forecast()
        assert forecast.schedule.transition_calls_remaining == 0
        assert len(forecast.prefixes) == 1
        assert (
            len(tree._wire(asdict(tree._cleanup(tree._issued(handle)))))
            <= forecast.prefixes[0].maximum_cleanup_wire_bytes
        )
        handle.validate_current()
        handle.finish()
        handle.validate_consumed_current()
        handle.validate_consumed_current()
        handle.release()
    finally:
        handle.release()


@pytest.mark.parametrize("case", ("directories", "preserve", "mode", "unchanged"))
def test_forecast_bodyless_ancestor_and_mode_sequences_preserve_complete_bounds(
    tmp_path, case
):
    from dataclasses import asdict

    if case in ("mode", "unchanged"):
        (tmp_path / "file").write_bytes(b"same")
        (tmp_path / "file").chmod(0o644)
        native = request(
            tmp_path,
            kind=physical.ConfinedMutationKind.UPDATE,
            content=b"same",
            mode=0o755 if case == "mode" else 0o644,
        )
    else:
        paths = ('é"parent', 'é"parent/child')
        if case == "preserve":
            (tmp_path / paths[-1]).mkdir(parents=True)
        root = tmp_path.stat()
        native = physical.ConfinedTreeProjectionRequest(
            "request:bodyless-forecast",
            (root.st_dev, root.st_ino),
            (),
            tuple(
                physical.ConfinedTreeAncestorTransition(
                    path,
                    "create" if case == "directories" else "preserve",
                    pin(tmp_path / path),
                    0o755 if case == "directories" else None,
                )
                for path in paths
            ),
        )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    state = tree._issued(handle)
    try:
        handle.validate_current()
        forecast = handle.observe_capacity_forecast()
        assert forecast.remaining_scratch_rows == 0
        handle.validate_current()
        for ordinal in range(len(forecast.transition_order)):
            handle.validate_next_current()
            result = handle.apply_next_transition()
            bound = forecast.prefixes[ordinal + 1]
            assert len(state.ledger.history) <= bound.maximum_acquisition_history_rows
            assert (
                len(tree._wire(asdict(result)))
                <= bound.maximum_latest_return_wire_bytes
            )
            assert (
                len(result.effects)
                <= forecast.encoding.maximum_subeffects_per_transition
            )
        handle.finish()
        handle.validate_consumed_current()
        handle.validate_consumed_current()
        cleanup = handle.release()
        bound = forecast.prefixes[-1]
        assert len(state.ledger.history) <= bound.maximum_acquisition_history_rows
        assert (
            len(tree._wire(asdict(cleanup)))
            <= bound.maximum_cleanup_wire_bytes + bound.release_extra_wire_bytes
        )
        assert (
            len(tree._wire([asdict(row) for row in handle.observe_effects().effects]))
            <= bound.maximum_effect_wire_bytes
        )
        if case == "directories":
            assert all(
                stat.S_IMODE((tmp_path / path).stat().st_mode) == 0o755
                for path in paths
            )
    finally:
        handle.release()


@pytest.mark.parametrize("boundary", ("finish", "consumed"))
@pytest.mark.parametrize("error_type", (OSError, KeyboardInterrupt))
def test_forecast_late_capture_failure_retains_known_effects_and_bounded_cleanup(
    tmp_path, monkeypatch, boundary, error_type
):
    from dataclasses import asdict

    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    state = tree._issued(handle)
    forecast = handle.observe_capacity_forecast()
    handle.validate_current()
    handle.validate_next_current()
    handle.apply_next_transition()
    if boundary == "consumed":
        handle.finish()

    def unavailable(*_args, **_kwargs):
        raise error_type("original final capture unavailable")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(tree, "_capture", unavailable)
            with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
                (
                    handle.finish
                    if boundary == "finish"
                    else handle.validate_consumed_current
                )()
        assert (tmp_path / "file").read_bytes() == b"new"
        assert caught.value.observation.completed_prefix == 1
        assert caught.value.observation.effects
        bound = forecast.prefixes[-1]
        assert (
            len(tree._wire(asdict(caught.value.cleanup)))
            <= bound.maximum_cleanup_wire_bytes
            + bound.terminal_extra_wire_bytes
            + bound.release_extra_wire_bytes
        )
        assert (
            len(state.ledger.history)
            <= bound.maximum_acquisition_history_rows
            + bound.terminal_extra_acquisition_rows
        )
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
            handle.observe_capacity_forecast()
    finally:
        handle.release()


@pytest.mark.parametrize("delta", (0, -1))
def test_forecast_original_metadata_exact_boundary_and_one_under(tmp_path, delta):
    from dataclasses import replace

    # Measure the original compiler's reservation, not a caller estimator.
    native = request(tmp_path)
    # The limit itself is encoded: stabilize its decimal width before equality.
    for _ in range(4):
        control = tree.retain_confined_tree_projection(root=tmp_path, request=native)
        state = tree._issued(control)
        required = (
            state.ledger.metadata_other
            + state.ledger.request_metadata
            + 2
            * (state.ledger.resource_reserved + state.ledger.future_resource_reserved)
        )
        control.release()
        if native.limits.maximum_metadata_bytes == required:
            break
        native = replace(
            native, limits=replace(native.limits, maximum_metadata_bytes=required)
        )
    else:
        pytest.fail("original reservation did not stabilize")
    native = replace(
        native, limits=replace(native.limits, maximum_metadata_bytes=required + delta)
    )
    if delta:
        with pytest.raises(
            tree.RetainedPhysicalTreeProjectionRefusal, match="metadata_capacity"
        ) as caught:
            tree.retain_confined_tree_projection(root=tmp_path, request=native)
        assert caught.value.cleanup.cleanup_state == "completed"
        assert not (tmp_path / "file").exists()
    else:
        handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
        try:
            forecast = handle.observe_capacity_forecast()
            assert forecast.forecast_wire_bytes < required
            handle.validate_current()
            handle.validate_next_current()
            handle.apply_next_transition()
            handle.finish()
            handle.validate_consumed_current()
            handle.validate_consumed_current()
            handle.release()
        finally:
            handle.release()


@pytest.mark.parametrize("damage", ("prefix", "order", "rows", "scratch", "schedule"))
def test_forecast_malformed_dimensions_refuse_before_wire_consideration(
    tmp_path, damage
):
    from dataclasses import replace

    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path)
    )
    try:
        forecast = handle.observe_capacity_forecast()
        values = {}
        if damage == "prefix":
            values["prefixes"] = forecast.prefixes[:-1]
        elif damage == "order":
            values["transition_order"] = ((1, "file", "CREATE"),)
        elif damage == "rows":
            values["remaining_acquisition_rows"] = 0
        elif damage == "scratch":
            values["remaining_scratch_rows"] = 0
        else:
            with pytest.raises(ValueError):
                replace(forecast.schedule, transition_calls_remaining=True)
            return
        with pytest.raises(ValueError):
            replace(forecast, **values)
        assert handle.observe_capacity_forecast() == forecast
    finally:
        handle.release()


@pytest.mark.parametrize("length", (1, 70))
def test_forecast_escaped_unicode_path_bounds_distinct_resource_records(
    tmp_path, length
):
    from dataclasses import asdict

    path = "/".join(('é"' * length,) * 3) + "/file"
    handle = tree.retain_confined_tree_projection(
        root=tmp_path, request=request(tmp_path, path=path)
    )
    state = tree._issued(handle)
    records = set()
    try:
        forecast = handle.observe_capacity_forecast()

        def record(prefix):
            cleanup = tree._cleanup(state)
            records.update(tree._wire(asdict(row)) for row in cleanup.resources)
            bound = forecast.prefixes[prefix]
            assert len(records) <= bound.maximum_resource_variant_rows
            assert (
                len(tree._wire(asdict(cleanup)))
                <= bound.maximum_cleanup_wire_bytes + bound.release_extra_wire_bytes
            )
            assert all(
                len(tree._wire(asdict(row)))
                <= forecast.encoding.maximum_resource_record_bytes
                for row in cleanup.resources
            )

        record(0)
        handle.validate_current()
        record(0)
        for ordinal in range(len(forecast.transition_order)):
            handle.validate_next_current()
            handle.apply_next_transition()
            record(ordinal + 1)
        handle.finish()
        handle.validate_consumed_current()
        handle.validate_consumed_current()
        handle.release()
        record(len(forecast.transition_order))
        assert (tmp_path / path).read_bytes() == b"new"
    finally:
        handle.release()


@pytest.mark.parametrize("error_type", (OSError, KeyboardInterrupt))
def test_forecast_bounds_snapshot_failure_after_known_descriptor_close(
    tmp_path, monkeypatch, error_type
):
    from dataclasses import asdict

    (tmp_path / "file").write_bytes(b"before")
    handle = tree.retain_confined_tree_projection(
        root=tmp_path,
        request=request(tmp_path, kind=physical.ConfinedMutationKind.UPDATE),
    )
    state = tree._issued(handle)
    forecast = handle.observe_capacity_forecast()
    handle.validate_current()
    original = state.ledger.refresh
    failed = False

    def unavailable(slot):
        nonlocal failed
        if slot.state == "released" and not failed:
            failed = True
            raise error_type("original close snapshot unavailable")
        return original(slot)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(state.ledger, "refresh", unavailable)
            with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
                handle.validate_next_current()
        assert failed
        bound = forecast.prefixes[0]
        assert (
            len(tree._wire(asdict(caught.value.cleanup)))
            <= bound.maximum_cleanup_wire_bytes
            + bound.terminal_extra_wire_bytes
            + bound.release_extra_wire_bytes
        )
        assert all(
            row.ownership == "released" for row in caught.value.cleanup.resources
        )
        assert (tmp_path / "file").read_bytes() == b"before"
        assert not state.effects
    finally:
        handle.release()


@pytest.mark.parametrize("boundary", ("control", "refresh", "allocation"))
@pytest.mark.parametrize("error_type", (OSError, KeyboardInterrupt))
def test_snapshot_failure_after_known_close_preserves_disposal_and_old_snapshots(
    tmp_path, monkeypatch, boundary, error_type
):
    (tmp_path / "file").write_bytes(b"before")
    handle = tree.retain_confined_tree_projection(
        root=tmp_path,
        request=request(tmp_path, kind=physical.ConfinedMutationKind.UPDATE),
    )
    state = tree._issued(handle)
    initial_rows = len(state.ledger.history)
    original_refresh = state.ledger.refresh
    original_snapshot = tree.ConfinedTreeResourceCleanup
    original_close = os.close
    failed_slots, old_snapshots, closes = [], [], []

    def closed(fd):
        closes.append(fd)
        return original_close(fd)

    def refresh(slot):
        if slot.index >= initial_rows and slot.state == "owned":
            original_refresh(slot)
            old_snapshots.append(state.ledger.resource_observations())
            return
        if (
            slot.index >= initial_rows
            and slot.attempted
            and slot.state == "released"
            and not failed_slots
        ):
            failed_slots.append(slot)
            if boundary == "refresh":
                raise error_type("close snapshot unavailable")
        return original_refresh(slot)

    def snapshot(*args):
        if boundary == "allocation" and failed_slots and args[0] == failed_slots[0].ref:
            monkeypatch.setattr(tree, "ConfinedTreeResourceCleanup", original_snapshot)
            raise error_type("close snapshot unavailable")
        return original_snapshot(*args)

    monkeypatch.setattr(os, "close", closed)
    monkeypatch.setattr(state.ledger, "refresh", refresh)
    monkeypatch.setattr(tree, "ConfinedTreeResourceCleanup", snapshot)
    if boundary == "control":
        handle.validate_next_current()
        cleanup = handle.release()
    else:
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
            handle.validate_next_current()
        assert type(caught.value.__cause__) is error_type
        cleanup = caught.value.cleanup
        assert caught.value.observation.effects == ()
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
            handle.apply_next_transition()
    assert len(failed_slots) == 1
    slot = failed_slots[0]
    current = next(row for row in cleanup.resources if row.resource_ref == slot.ref)
    previous = next(row for row in old_snapshots[0] if row.resource_ref == slot.ref)
    assert current.ownership == "released"
    assert current.cleanup_attempted
    assert current.cleanup_state == "completed"
    assert previous.ownership == "owned"
    assert not previous.cleanup_attempted
    assert previous.cleanup_state == "not_attempted"
    assert closes.count(slot.record.descriptor) == 1
    before = tuple(closes)
    handle.release()
    assert tuple(closes) == before
    assert not state.ledger.invalid_snapshots
    assert (tmp_path / "file").read_bytes() == b"before"


def test_successful_forecast_keeps_terminal_scratch_cleanup_separate(
    tmp_path, monkeypatch
):
    from dataclasses import asdict, replace

    original = request(tmp_path)
    native = replace(
        original,
        files=tuple(replace(original.files[0], path=f"file-{i}") for i in range(3)),
    )
    handle = tree.retain_confined_tree_projection(root=tmp_path, request=native)
    state = tree._issued(handle)
    forecast = handle.observe_capacity_forecast()
    allocator = state.execution_reserve
    assert tuple(p.maximum_effect_rows for p in forecast.prefixes) == (0, 7, 14, 21)
    handle.validate_current()
    for _ in range(2):
        handle.validate_next_current()
        handle.apply_next_transition()
    assert len(handle.observe_effects().effects) == 14
    assert state.execution_reserve == allocator
    original_unlink = os.unlink
    failed = False

    def unlink(*args, **kwargs):
        nonlocal failed
        if not failed and str(args[0]).startswith(".aware-tree-"):
            failed = True
            raise OSError("original scratch unlink failed")
        return original_unlink(*args, **kwargs)

    try:
        handle.validate_next_current()
        with monkeypatch.context() as patch:
            patch.setattr(os, "unlink", unlink)
            with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal) as caught:
                handle.apply_next_transition()
        observation = caught.value.observation
        bound = forecast.prefixes[2]
        assert observation.completed_prefix == 2
        assert len(observation.effects) <= bound.maximum_effect_rows + 16
        assert len(tree._wire([asdict(r) for r in observation.effects])) <= (
            bound.maximum_effect_wire_bytes + bound.terminal_extra_wire_bytes
        )
        assert (tmp_path / "file-2").read_bytes() == original.files[0].content
        with pytest.raises(tree.RetainedPhysicalTreeProjectionRefusal):
            handle.apply_next_transition()
    finally:
        try:
            handle.release()
        except tree.RetainedPhysicalTreeProjectionRefusal as release_error:
            assert release_error.cleanup.cleanup_state == "unknown"
            assert not release_error.cleanup.ledger_complete
