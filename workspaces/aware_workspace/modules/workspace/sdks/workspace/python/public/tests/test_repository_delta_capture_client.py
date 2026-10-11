"""Real public capture, original retention and command-local failure evidence."""

import asyncio
import copy
import os
import pickle
import threading

import pytest
from aware_workspace_sdk.repository_delta_capture import (
    WorkspaceRepositoryDeltaCaptureClient as Capture,
)
from aware_workspace_sdk.repository_delta_capture import (
    WorkspaceRepositoryDeltaCaptureRefusal as Refusal,
)
from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionFactory as Retention,
)


def selected(tmp_path, *, root=None, state=None):
    root = root or tmp_path / "metadata"
    root.mkdir(exist_ok=True)
    state = state or tmp_path / "retention"
    retention = Retention.filesystem(state_root=state).allocate_delta_retention()
    client = Capture.filesystem(
        repository_root=root,
        cache_root=tmp_path / "capture-cache",
        retention=retention,
    )
    retention.initialize_delta_retention(
        repository_binding_ref=client.repository_binding_ref
    )
    return root, retention, client


@pytest.mark.asyncio
async def test_real_head_change_has_original_capture_and_retained_bodies(tmp_path):
    root, retention, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"before\n")
    before = await client.prepare_capture(selected_paths=("HEAD",))
    assert before.phase == "prepared" and before.capture.selected_paths == ("HEAD",)
    assert not (root / ".git").exists()
    assert not tuple(root.glob(".aware*"))
    (root / "HEAD").write_bytes(b"after and committed\n")
    after = await client.observe_capture()
    assert len(after.deltas) == 1
    delta = after.deltas[0]
    assert retention.resolve_delta(delta.delta_ref) == delta
    assert retention.resolve_body(delta.old_body_ref) == b"before\n"
    assert retention.resolve_body(delta.new_body_ref) == b"after and committed\n"
    assert delta.before_coordinate.epoch == delta.after_coordinate.epoch
    assert delta.after_coordinate.cursor > delta.before_coordinate.cursor
    assert (await client.observe_capture()).deltas == after.deltas
    detached = client.capture_observation()
    released = await client.release_capture()
    assert released.cleanup_state == "completed" and released.phase == "released"
    assert detached.phase == "prepared" and detached.deltas == after.deltas
    assert retention.observe_retention().phase == "active"
    assert retention.resolve_delta(delta.delta_ref) == delta
    assert await client.release_capture() == released
    with pytest.raises(Refusal, match="capture_not_prepared"):
        await client.observe_capture()


@pytest.mark.asyncio
async def test_create_delete_binary_and_no_change(tmp_path):
    root, retention, client = selected(tmp_path)
    first = await client.prepare_capture(selected_paths=("HEAD",))
    assert first.capture.path_states[0].state.value == "absent"
    assert not (await client.observe_capture()).deltas
    (root / "HEAD").write_bytes(b"\x00\xffbinary")
    created = await client.observe_capture()
    assert created.deltas[-1].kind.value == "create"
    assert retention.resolve_body(created.deltas[-1].new_body_ref) == b"\x00\xffbinary"
    (root / "HEAD").unlink()
    deleted = await client.observe_capture()
    assert deleted.deltas[-1].kind.value == "delete"
    await client.release_capture()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        ".aware/HEAD",
        ".git/HEAD",
        "target/HEAD",
        "a.pyc",
        "../HEAD",
        "e\u0301/HEAD",
        "a\u0080b/HEAD",
    ],
)
async def test_excluded_and_noncanonical_paths_refuse_before_observer(tmp_path, path):
    _, _, client = selected(tmp_path)
    with pytest.raises(Refusal) as failure:
        await client.prepare_capture(selected_paths=(path,))
    assert failure.value.observation.phase == "failed"
    assert failure.value.observation.snapshot is None
    assert not (tmp_path / "capture-cache").exists()
    with pytest.raises(Refusal, match="capture_preparation_spent"):
        await client.prepare_capture(selected_paths=("HEAD",))
    await client.release_capture()


@pytest.mark.asyncio
async def test_gitignored_absent_target_is_not_known_absent(tmp_path):
    root, _, client = selected(tmp_path)
    (root / ".gitignore").write_text("HEAD\n")
    with pytest.raises(Refusal) as failure:
        await client.prepare_capture(selected_paths=("HEAD",))
    assert "capture_path_excluded" in str(failure.value.__cause__)
    assert failure.value.observation.capture is None
    await client.release_capture()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo"])
async def test_nonregular_selected_sources_refuse_without_body_read(tmp_path, kind):
    root, _, client = selected(tmp_path)
    if kind == "symlink":
        (root / "HEAD").symlink_to(tmp_path / "elsewhere")
    elif kind == "directory":
        (root / "HEAD").mkdir()
    else:
        os.mkfifo(root / "HEAD")
    with pytest.raises(Refusal) as failure:
        await client.prepare_capture(selected_paths=("HEAD",))
    assert failure.value.observation.snapshot is None
    await client.release_capture()


@pytest.mark.parametrize(
    "mode", ["construct", "forge", "subclass", "copy", "deepcopy", "pickle"]
)
def test_original_client_cannot_be_reconstructed(tmp_path, mode):
    _, _, client = selected(tmp_path)
    if mode == "construct":
        with pytest.raises(TypeError):
            Capture()
    elif mode == "forge":
        with pytest.raises(Refusal, match="not_issued"):
            object.__new__(Capture).capture_observation()
    elif mode == "subclass":

        class Foreign(Capture):
            pass

        with pytest.raises(Refusal, match="not_issued"):
            object.__new__(Foreign).capture_observation()
    else:
        with pytest.raises(TypeError):
            {"copy": copy.copy, "deepcopy": copy.deepcopy, "pickle": pickle.dumps}[
                mode
            ](client)


def test_no_caller_snapshot_batch_or_provider_entrance(tmp_path):
    import inspect

    _, _, client = selected(tmp_path)
    assert tuple(inspect.signature(client.observe_capture).parameters) == ()
    assert tuple(inspect.signature(client.prepare_capture).parameters) == (
        "selected_paths",
        "policy",
        "context_refs",
    )
    with pytest.raises(TypeError):
        client.observe_capture(batch=object())


@pytest.mark.asyncio
async def test_actual_retention_location_must_not_overlap_source(tmp_path):
    _, _, client = selected(tmp_path, state=tmp_path / "metadata" / "state")
    with pytest.raises(Refusal) as failure:
        await client.prepare_capture(selected_paths=("HEAD",))
    assert failure.value.observation.phase == "failed"
    assert failure.value.observation.snapshot is None
    await client.release_capture()


@pytest.mark.asyncio
async def test_borrowed_retention_release_retires_capture_and_preserves_evidence(
    tmp_path,
):
    root, retention, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"before")
    await client.prepare_capture(selected_paths=("HEAD",))
    (root / "HEAD").write_bytes(b"new persisted state")
    known = await client.observe_capture()
    retention.release_retention()
    with pytest.raises(Refusal) as failure:
        await client.observe_capture()
    assert failure.value.observation.deltas == known.deltas
    assert not failure.value.observation.ledger_complete
    await client.release_capture()


@pytest.mark.asyncio
async def test_root_substitution_is_terminal_without_touching_replacement(tmp_path):
    root, _, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"old")
    await client.prepare_capture(selected_paths=("HEAD",))
    root.rename(tmp_path / "original")
    root.mkdir()
    (root / "HEAD").write_bytes(b"foreign")
    with pytest.raises(Refusal):
        await client.observe_capture()
    assert (root / "HEAD").read_bytes() == b"foreign"
    root.rename(tmp_path / "replacement")
    (tmp_path / "original").rename(root)
    with pytest.raises(Refusal, match="capture_not_prepared"):
        await client.observe_capture()
    await client.release_capture()


@pytest.mark.asyncio
async def test_post_retention_return_failure_preserves_canonical_delta(
    tmp_path, monkeypatch
):
    from aware_workspace_sdk.repository_delta_retention import (
        WorkspaceRepositoryDeltaRetentionClient,
    )

    root, retention, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"before")
    await client.prepare_capture(selected_paths=("HEAD",))
    (root / "HEAD").write_bytes(b"known changed")
    original = WorkspaceRepositoryDeltaRetentionClient.record_delta

    def unavailable_return(self, delta):
        original(self, delta)
        raise OSError("delta persisted; return lost")

    with monkeypatch.context() as patch:
        patch.setattr(
            WorkspaceRepositoryDeltaRetentionClient, "record_delta", unavailable_return
        )
        with pytest.raises(Refusal) as failure:
            await client.observe_capture()
    evidence = failure.value.observation
    assert len(evidence.deltas) == 1 and not evidence.ledger_complete
    assert retention.resolve_body(evidence.deltas[0].new_body_ref) == b"known changed"
    with pytest.raises(Refusal, match="capture_not_prepared"):
        await client.observe_capture()
    await client.release_capture()


@pytest.mark.asyncio
async def test_known_delta_survives_later_unavailable_recapture(tmp_path, monkeypatch):
    from aware_workspace_runtime.observation import (
        WorkspaceRepositoryObservationSession,
    )
    from aware_workspace_sdk.repository_delta_retention import (
        WorkspaceRepositoryDeltaRetentionClient,
    )

    root, _, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"before")
    await client.prepare_capture(selected_paths=("HEAD",))
    (root / "HEAD").write_bytes(b"changed")
    known = await client.observe_capture()

    async def unavailable(*args):
        raise OSError("poll unavailable")

    def no_recapture(*args):
        raise OSError("retention observation unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(
            WorkspaceRepositoryObservationSession, "observe_paths_once", unavailable
        )
        patch.setattr(
            WorkspaceRepositoryDeltaRetentionClient, "retained_captures", no_recapture
        )
        with pytest.raises(Refusal) as failure:
            await client.observe_capture()
    assert failure.value.observation.deltas == known.deltas
    assert not failure.value.observation.ledger_complete
    await client.release_capture()


@pytest.mark.asyncio
async def test_concurrent_prepare_only_one_original_capture(tmp_path):
    _, retention, client = selected(tmp_path)
    results = await asyncio.gather(
        client.prepare_capture(selected_paths=("HEAD",)),
        client.prepare_capture(selected_paths=("HEAD",)),
        return_exceptions=True,
    )
    assert sum(isinstance(x, Refusal) for x in results) == 1
    assert len(retention.retained_captures()) == 1
    await client.release_capture()


@pytest.mark.asyncio
async def test_cancellation_settles_capture_worker_before_release(
    tmp_path, monkeypatch
):
    from aware_workspace_runtime.repository_delta_capture import (
        WorkspaceRepositoryDeltaCaptureCoordinator,
    )

    root, retention, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"old")
    await client.prepare_capture(selected_paths=("HEAD",))
    (root / "HEAD").write_bytes(b"changed and retained")
    started, finish = threading.Event(), threading.Event()
    original = WorkspaceRepositoryDeltaCaptureCoordinator.observe

    def delayed(self, batch):
        started.set()
        assert finish.wait(10)
        return original(self, batch)

    with monkeypatch.context() as patch:
        patch.setattr(WorkspaceRepositoryDeltaCaptureCoordinator, "observe", delayed)
        task = asyncio.create_task(client.observe_capture())
        assert await asyncio.to_thread(started.wait, 10)
        task.cancel()
        release = asyncio.create_task(client.release_capture())
        await asyncio.sleep(0)
        assert not release.done()
        finish.set()
        with pytest.raises(Refusal) as failure:
            await task
        released = await release
    assert isinstance(failure.value.__cause__, asyncio.CancelledError)
    assert len(failure.value.observation.deltas) == 1
    assert len(retention.retained_deltas()) == 1
    assert released.cleanup_state == "completed"


@pytest.mark.asyncio
async def test_release_failure_is_unknown_and_never_replayed(tmp_path, monkeypatch):
    from aware_workspace_runtime.observation import (
        WorkspaceRepositoryObservationSession,
    )

    _, retention, client = selected(tmp_path)
    await client.prepare_capture(selected_paths=("HEAD",))
    original = WorkspaceRepositoryObservationSession.stop
    calls = []

    async def failed_stop(self):
        calls.append(self)
        await original(self)
        raise OSError("cleanup return unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(WorkspaceRepositoryObservationSession, "stop", failed_stop)
        with pytest.raises(Refusal, match="capture_release_incomplete") as failure:
            await client.release_capture()
        second = await client.release_capture()
    assert len(calls) == 1 and second.cleanup_state == "unknown"
    assert failure.value.observation.cleanup_state == "unknown"
    assert retention.observe_retention().phase == "active"


def test_foreign_process_cannot_observe_release_or_restore_client(
    tmp_path, monkeypatch
):
    _, _, client = selected(tmp_path)
    original_pid = os.getpid()
    monkeypatch.setattr(os, "getpid", lambda: original_pid + 1)
    with pytest.raises(Refusal, match="capture_process_mismatch"):
        client.capture_observation()


@pytest.mark.asyncio
async def test_missing_initialization_is_terminal(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    retention = Retention.filesystem(
        state_root=tmp_path / "state"
    ).allocate_delta_retention()
    client = Capture.filesystem(
        repository_root=root, cache_root=tmp_path / "cache", retention=retention
    )
    with pytest.raises(Refusal) as failure:
        await client.prepare_capture(selected_paths=("HEAD",))
    assert failure.value.observation.snapshot is None
    assert not (tmp_path / "cache").exists()
    retention.initialize_delta_retention(
        repository_binding_ref=client.repository_binding_ref
    )
    with pytest.raises(Refusal, match="capture_preparation_spent"):
        await client.prepare_capture(selected_paths=("HEAD",))
    await client.release_capture()


@pytest.mark.asyncio
async def test_regressing_original_snapshot_preserves_last_valid_history(
    tmp_path, monkeypatch
):
    from aware_workspace_runtime.observation import (
        WorkspaceRepositoryObservationSession,
    )

    root, _, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"old")
    before = await client.prepare_capture(selected_paths=("HEAD",))
    (root / "HEAD").write_bytes(b"new longer")
    known = await client.observe_capture()
    with monkeypatch.context() as patch:
        patch.setattr(
            WorkspaceRepositoryObservationSession,
            "current_snapshot",
            property(lambda self: before.snapshot),
        )
        with pytest.raises(Refusal) as failure:
            await client.observe_capture()
    assert failure.value.observation.snapshot == known.snapshot
    assert failure.value.observation.deltas == known.deltas
    assert not failure.value.observation.ledger_complete
    await client.release_capture()


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["prepare", "observe"])
@pytest.mark.parametrize("interruption", [OSError, KeyboardInterrupt, SystemExit])
async def test_original_retention_returns_lost_after_persistence(
    tmp_path, monkeypatch, stage, interruption
):
    from aware_workspace_sdk.repository_delta_retention import (
        WorkspaceRepositoryDeltaRetentionClient,
    )

    root, retention, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"old")
    if stage == "observe":
        await client.prepare_capture(selected_paths=("HEAD",))
        (root / "HEAD").write_bytes(b"new persisted body")
    method = "record_capture" if stage == "prepare" else "record_delta"
    original = getattr(WorkspaceRepositoryDeltaRetentionClient, method)

    def unavailable(self, value):
        original(self, value)
        raise interruption("original return lost")

    with monkeypatch.context() as patch:
        patch.setattr(WorkspaceRepositoryDeltaRetentionClient, method, unavailable)
        with pytest.raises(Refusal) as failure:
            if stage == "prepare":
                await client.prepare_capture(selected_paths=("HEAD",))
            else:
                await client.observe_capture()
    assert isinstance(failure.value.__cause__, interruption)
    assert failure.value.observation.capture is not None
    assert failure.value.observation.phase == "failed"
    assert not failure.value.observation.ledger_complete
    if stage == "observe":
        assert failure.value.observation.deltas == retention.retained_deltas()
    await client.release_capture()


def test_retained_native_store_not_factory_label_determines_separation(tmp_path):
    from aware_workspace_fs_adapter.repository_delta_store import (
        WorkspaceRepositoryDeltaStore,
    )

    _, retention, first = selected(tmp_path)
    root = tmp_path / "metadata"
    original = WorkspaceRepositoryDeltaStore(
        repository_binding_ref=first.repository_binding_ref,
        state_root=root / "hidden-state",
    )
    borrowed = Retention.filesystem(
        state_root=tmp_path / "unrelated-factory-label"
    ).retain_delta_retention(
        original,
        expected_binding_ref=first.repository_binding_ref,
    )
    with pytest.raises(Refusal, match="retention_capture_roots_overlap"):
        Capture.filesystem(
            repository_root=root, cache_root=tmp_path / "cache-two", retention=borrowed
        )
    assert retention.observe_retention().phase == "active"


def test_public_capture_import_is_lazy_without_physical_or_foreign_owners():
    import subprocess
    import sys

    code = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("aware_workspace_runtime", "aware_workspace_fs_adapter", "aware_ontology", "aware_issue", "aware_meta")):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Block())
from aware_workspace_sdk.repository_delta_capture import WorkspaceRepositoryDeltaCaptureClient
assert WorkspaceRepositoryDeltaCaptureClient
"""
    subprocess.run(
        [sys.executable, "-B", "-c", code], check=True, capture_output=True, text=True
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("paths,limit", [(("HEAD", "HEAD"), 2), (("HEAD", "other"), 1)])
async def test_selection_limits_refuse_before_observation(tmp_path, paths, limit):
    from aware_workspace_runtime.repository_delta import (
        WorkspaceRepositoryDeltaCapturePolicy,
    )

    _, _, client = selected(tmp_path)
    with pytest.raises(Refusal) as failure:
        await client.prepare_capture(
            selected_paths=paths,
            policy=WorkspaceRepositoryDeltaCapturePolicy(maximum_selected_files=limit),
        )
    assert failure.value.observation.snapshot is None
    assert not (tmp_path / "capture-cache").exists()
    await client.release_capture()


@pytest.mark.asyncio
async def test_overbudget_preimage_retains_original_partial_capture(tmp_path):
    from aware_workspace_runtime.repository_delta import (
        WorkspaceRepositoryDeltaCapturePolicy,
    )

    root, retention, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"too large for this admitted capture")
    with pytest.raises(Refusal) as failure:
        await client.prepare_capture(
            selected_paths=("HEAD",),
            policy=WorkspaceRepositoryDeltaCapturePolicy(maximum_body_bytes=4),
        )
    known = failure.value.observation
    assert known.capture.path_states[0].state.value == "over_budget"
    assert retention.resolve_capture(known.capture.capture_ref) == known.capture
    assert not known.ledger_complete
    assert (root / "HEAD").read_bytes() == b"too large for this admitted capture"
    await client.release_capture()


@pytest.mark.asyncio
async def test_unselected_writes_do_not_become_selected_effects(tmp_path):
    root, _, client = selected(tmp_path)
    (root / "HEAD").write_bytes(b"same")
    await client.prepare_capture(selected_paths=("HEAD",))
    (root / "unrelated").write_bytes(b"another owner")
    assert not (await client.observe_capture()).deltas
    await client.release_capture()
