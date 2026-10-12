"""Real local persistence, races and crash outcomes; no supplier authority."""

from __future__ import annotations

import json
import multiprocessing
import os
from dataclasses import replace

import pytest
from aware_workspace_fs_adapter import repository_workflow_evidence as physical
from aware_workspace_sdk.repository_workflow_codec import (
    repository_workflow_value_to_payload,
)
from aware_workspace_sdk.repository_workflow_values import (
    WorkspaceRepositoryWorkflowEvidenceAppendRequest,
    WorkspaceRepositoryWorkflowPlanObservation,
    WorkspaceRepositoryWorkflowStageObservation,
)


def plan():
    return WorkspaceRepositoryWorkflowPlanObservation(
        "binding",
        "source",
        "target",
        "a" * 40,
        "portable",
        "sha256:" + "b" * 64,
        "selection",
        "refs/heads/main",
        None,
        (
            WorkspaceRepositoryWorkflowStageObservation(
                "source_capture", "available", ()
            ),
        ),
        (),
    )


def event(snapshot, *, invocation="invoke:1", **changes):
    value = WorkspaceRepositoryWorkflowEvidenceAppendRequest(
        snapshot.plan.binding_ref,
        snapshot.cursor,
        snapshot.digest,
        "qualification",
        invocation,
        (),
        (),
        (),
        (),
        "caller_reported",
        "not_dispatched",
        "none",
        "not_attempted",
        False,
        (),
    )
    return replace(value, **changes)


@pytest.fixture
def store(tmp_path):
    root = tmp_path / "state"
    backend = physical.FilesystemWorkflowEvidence(root)
    assert not root.exists()
    snapshot = backend.open(plan(), "attempt:1")
    return root, backend, snapshot


def observe(backend):
    return backend.observe("source", "target", "attempt:1", "binding")


def test_original_append_identical_replay_and_fresh_read(store):
    root, backend, snapshot = store
    request = event(snapshot)
    first = backend.append("source", "target", "attempt:1", request)
    assert first[0] == 1 and first[2:] == ("persisted", "completed")
    assert backend.append("source", "target", "attempt:1", request) == first
    fresh = observe(physical.FilesystemWorkflowEvidence(root))
    assert (
        fresh.cursor == 1
        and fresh.records == (request,)
        and fresh.integrity == "verified"
    )
    assert list(root.rglob(".pending-*")) == []


def test_changed_replay_or_chain_refuses_without_replacing_bytes(store):
    root, backend, snapshot = store
    request = event(snapshot)
    backend.append("source", "target", "attempt:1", request)
    before = {p.name: p.read_bytes() for p in root.rglob("*.json")}
    for changed in (
        replace(request, invocation_ref="changed"),
        replace(request, expected_previous_digest="other"),
        replace(request, expected_cursor=2),
    ):
        with pytest.raises(physical.WorkflowEvidenceError, match="evidence_conflict"):
            backend.append("source", "target", "attempt:1", changed)
    assert before == {p.name: p.read_bytes() for p in root.rglob("*.json")}


def test_owner_observed_claim_is_not_supplied_by_public_values(store):
    _, backend, snapshot = store
    with pytest.raises(physical.WorkflowEvidenceError, match="supplier_unavailable"):
        backend.append(
            "source",
            "target",
            "attempt:1",
            event(snapshot, evidence_grade="owner_observed"),
        )
    assert observe(backend).cursor == 0


@pytest.mark.parametrize(
    "damage", ("malformed", "duplicate", "noncanonical", "gap", "chain")
)
def test_corrupt_history_refuses_without_repair(store, damage):
    root, backend, snapshot = store
    backend.append("source", "target", "attempt:1", event(snapshot))
    record = next(root.rglob("000001.json"))
    if damage == "malformed":
        record.write_bytes(b"{")
    elif damage == "duplicate":
        record.write_bytes(b'{"body":{},"body":{},"previous_digest":"x"}')
    elif damage == "noncanonical":
        record.write_text(json.dumps(json.loads(record.read_bytes()), indent=2))
    elif damage == "gap":
        record.rename(record.with_name("000002.json"))
    else:
        value = json.loads(record.read_bytes())
        value["previous_digest"] = "changed"
        record.write_bytes(physical._wire(value))
    before = {p.name: p.read_bytes() for p in root.rglob("*.json")}
    with pytest.raises(physical.WorkflowEvidenceError, match="evidence_corrupt"):
        observe(backend)
    assert before == {p.name: p.read_bytes() for p in root.rglob("*.json")}


def test_pending_tail_retains_prefix_and_blocks_blind_retry(store):
    root, backend, snapshot = store
    backend.append("source", "target", "attempt:1", event(snapshot))
    directory = next(root.iterdir())
    (directory / ".pending-crash").write_bytes(b"{")
    result = observe(backend)
    assert (
        result.cursor == 1
        and result.integrity == "incomplete"
        and result.cleanup == "incomplete"
    )
    with pytest.raises(
        physical.WorkflowEvidenceError, match="evidence_persistence_unknown"
    ):
        backend.append(
            "source", "target", "attempt:1", event(result, invocation="next")
        )
    assert (directory / ".pending-crash").read_bytes() == b"{"


@pytest.mark.parametrize("point", ("write", "link", "fsync"))
def test_unknown_write_does_not_discard_or_retry_candidate(store, monkeypatch, point):
    root, backend, snapshot = store

    def fail(*args, **kwargs):
        raise OSError("simulated uncertain write")

    monkeypatch.setattr(physical.os, point, fail)
    with pytest.raises(physical.WorkflowEvidenceError) as caught:
        backend.append(
            "source",
            "target",
            "attempt:1",
            event(snapshot, dispatch_state="returned", effect_state="applied"),
        )
    assert (
        caught.value.persistence == "unknown"
        and caught.value.code == "evidence_persistence_unknown"
    )
    assert list(root.rglob(".pending-*"))


def test_known_durable_record_survives_cleanup_failure(store, monkeypatch):
    root, backend, snapshot = store
    original = physical.os.unlink

    def fail_pending(*args, **kwargs):
        if str(args[0]).startswith(".pending-"):
            raise OSError("cleanup unavailable")
        return original(*args, **kwargs)

    monkeypatch.setattr(physical.os, "unlink", fail_pending)
    result = backend.append(
        "source",
        "target",
        "attempt:1",
        event(snapshot, dispatch_state="returned", effect_state="applied"),
    )
    assert result[2:] == ("persisted", "incomplete")
    history = observe(backend)
    assert history.cursor == 1 and history.records[0].effect_state == "applied"
    assert history.integrity == "incomplete" and list(root.rglob(".pending-*"))


@pytest.mark.parametrize("kind", ("root", "attempt", "header", "lock"))
def test_symlink_substitution_refuses_without_following_foreign_file(
    store, tmp_path, kind
):
    root, backend, _ = store
    target = tmp_path / "foreign"
    if kind in ("root", "attempt"):
        target.mkdir()
        victim = root if kind == "root" else next(root.iterdir())
        victim.rename(victim.with_name(victim.name + "-original"))
        victim.symlink_to(target, target_is_directory=True)
    else:
        target.write_text("foreign")
        victim = next(root.rglob("header.json" if kind == "header" else "lock"))
        victim.unlink()
        victim.symlink_to(target)
    with pytest.raises(physical.WorkflowEvidenceError):
        observe(backend)
    assert (
        not list(target.iterdir())
        if target.is_dir()
        else target.read_text() == "foreign"
    )


def test_missing_observation_creates_no_state(tmp_path):
    root = tmp_path / "absent"
    with pytest.raises(physical.WorkflowEvidenceError):
        observe(physical.FilesystemWorkflowEvidence(root))
    assert not root.exists()


def contender(root, body, queue):
    from pathlib import Path

    from aware_workspace_sdk.repository_workflow_codec import (
        repository_workflow_value_from_payload,
    )

    backend = physical.FilesystemWorkflowEvidence(Path(root))
    request = repository_workflow_value_from_payload(
        WorkspaceRepositoryWorkflowEvidenceAppendRequest, body
    )
    try:
        backend.append("source", "target", "attempt:1", request)
        queue.put("persisted")
    except physical.WorkflowEvidenceError as error:
        queue.put(error.code)


def test_four_real_processes_share_one_cas_position(store):
    root, backend, snapshot = store
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    children = [
        context.Process(
            target=contender,
            args=(
                str(root),
                repository_workflow_value_to_payload(
                    event(snapshot, invocation=f"race:{i}")
                ),
                queue,
            ),
        )
        for i in range(4)
    ]
    for child in children:
        child.start()
    for child in children:
        child.join(10)
        assert child.exitcode == 0
    outcomes = [queue.get(timeout=2) for _ in children]
    queue.close()
    queue.join_thread()
    assert outcomes.count("persisted") == 1 and outcomes.count("evidence_conflict") == 3
    assert observe(backend).cursor == 1


def crash_writer(root, payload):
    from pathlib import Path

    from aware_workspace_sdk.repository_workflow_codec import (
        repository_workflow_value_from_payload,
    )

    backend = physical.FilesystemWorkflowEvidence(Path(root))
    request = repository_workflow_value_from_payload(
        WorkspaceRepositoryWorkflowEvidenceAppendRequest, payload
    )
    original = physical.os.link

    def crash_after_link(*args, **kwargs):
        original(*args, **kwargs)
        os._exit(73)

    physical.os.link = crash_after_link
    backend.append("source", "target", "attempt:1", request)


def test_real_crash_after_link_returns_descriptive_prefix_and_uncertainty(store):
    root, backend, snapshot = store
    context = multiprocessing.get_context("spawn")
    child = context.Process(
        target=crash_writer,
        args=(str(root), repository_workflow_value_to_payload(event(snapshot))),
    )
    child.start()
    child.join(10)
    assert child.exitcode == 73
    result = observe(backend)
    assert result.cursor == 1 and result.integrity == "incomplete"
    with pytest.raises(
        physical.WorkflowEvidenceError, match="evidence_persistence_unknown"
    ):
        backend.append("source", "target", "attempt:1", event(snapshot))


def test_full_record_ceiling_is_not_evicted(store):
    _, backend, snapshot = store
    for i in range(256):
        backend.append(
            "source", "target", "attempt:1", event(snapshot, invocation=f"record:{i}")
        )
        snapshot = observe(backend)
    assert snapshot.cursor == 256
    with pytest.raises(physical.WorkflowEvidenceError, match="evidence_conflict"):
        backend.append(
            "source", "target", "attempt:1", event(snapshot, invocation="over-limit")
        )
    assert observe(backend).cursor == 256


def test_missing_header_with_existing_records_is_not_repaired(store):
    root, backend, snapshot = store
    backend.append("source", "target", "attempt:1", event(snapshot))
    header = next(root.rglob("header.json"))
    header.unlink()
    with pytest.raises(physical.WorkflowEvidenceError, match="evidence_corrupt"):
        backend.open(plan(), "attempt:1")
    assert not header.exists() and next(root.rglob("000001.json")).exists()


def test_missing_lock_is_not_recreated_by_observation(store):
    root, backend, _ = store
    lock = next(root.rglob("lock"))
    lock.unlink()
    with pytest.raises(physical.WorkflowEvidenceError):
        observe(backend)
    assert not lock.exists()


def test_total_attempt_byte_limit_prevents_new_record_without_eviction(
    store, monkeypatch
):
    root, backend, snapshot = store
    monkeypatch.setattr(physical, "MAX_WORKFLOW_ATTEMPT_BYTES", snapshot.size_bytes + 1)
    with pytest.raises(physical.WorkflowEvidenceError, match="evidence_conflict"):
        backend.append("source", "target", "attempt:1", event(snapshot))
    assert not list(root.rglob("000001.json"))
    assert observe(backend).cursor == 0


@pytest.mark.parametrize("failed_role", ("lock", "directory", "root", "parent", "all"))
@pytest.mark.parametrize("after_release", (False, True))
def test_descriptor_cleanup_attempts_all_releases_and_preserves_durable_append(
    store, monkeypatch, failed_role, after_release
):
    root, backend, snapshot = store
    directory = next(path for path in root.iterdir() if path.is_dir())
    paths = {
        str(directory / "lock"): "lock",
        str(directory): "directory",
        str(root): "root",
        str(root.parent): "parent",
    }
    original = physical.os.close
    releases = []
    unreleased = []
    causes = []

    def fail_release(descriptor):
        role = paths.get(os.readlink(f"/proc/self/fd/{descriptor}"))
        if role is None:
            return original(descriptor)
        releases.append(role)
        if role == failed_role or failed_role == "all":
            if after_release:
                original(descriptor)
            else:
                unreleased.append(descriptor)
            error = OSError("release fault: " + role)
            causes.append(error)
            raise error
        return original(descriptor)

    monkeypatch.setattr(physical.os, "close", fail_release)
    try:
        with pytest.raises(physical.WorkflowEvidenceError) as caught:
            backend.append("source", "target", "attempt:1", event(snapshot))
        assert releases == ["lock", "directory", "root", "parent"]
        assert caught.value.persistence == "persisted"
        assert caught.value.cleanup == "unknown"
        assert caught.value.__cause__ is causes[0]
        (reference,) = caught.value.evidence_refs
        body = (directory / "000001.json").read_bytes()
        assert reference.sha256 == physical._digest(body)
        assert reference.size_bytes == len(body)
        assert len(list(directory.glob("000001.json"))) == 1
    finally:
        monkeypatch.setattr(physical.os, "close", original)
        for descriptor in unreleased:
            original(descriptor)
    assert observe(backend).cursor == 1


@pytest.mark.parametrize("failure", ("refusal", "interrupt"))
def test_cleanup_failure_preserves_primary_failure_and_attempts_remaining_releases(
    store, monkeypatch, failure
):
    root, backend, snapshot = store
    directory = next(path for path in root.iterdir() if path.is_dir())
    paths = [str(directory / "lock"), str(directory), str(root), str(root.parent)]
    original = physical.os.close
    released = []
    primary = (
        physical.WorkflowEvidenceError("evidence_conflict")
        if failure == "refusal"
        else KeyboardInterrupt("primary interruption")
    )

    def fail_snapshot(*args, **kwargs):
        raise primary

    def fail_close(descriptor):
        path = os.readlink(f"/proc/self/fd/{descriptor}")
        original(descriptor)
        if path in paths:
            released.append(path)
        if path == paths[0]:
            raise OSError("secondary cleanup error")

    monkeypatch.setattr(backend, "_snapshot", fail_snapshot)
    monkeypatch.setattr(physical.os, "close", fail_close)
    with pytest.raises(type(primary)) as caught:
        backend.append("source", "target", "attempt:1", event(snapshot))
    assert caught.value is primary
    assert released == paths
    assert not list(directory.glob("000001.json"))
    if failure == "refusal":
        assert primary.cleanup == "unknown" and primary.persistence == "not_written"
    else:
        assert "Workflow descriptor cleanup is unknown" in primary.__notes__


def test_cleanup_refusal_after_open_retains_original_header(store, monkeypatch):
    root, backend, _ = store
    original = physical.os.close

    def fail_close(descriptor):
        path = os.readlink(f"/proc/self/fd/{descriptor}")
        original(descriptor)
        if path.endswith("/lock"):
            raise OSError("late open release failure")

    monkeypatch.setattr(physical.os, "close", fail_close)
    with pytest.raises(physical.WorkflowEvidenceError) as caught:
        backend.open(plan(), "attempt:1")
    assert caught.value.persistence == "persisted"
    assert caught.value.cleanup == "unknown"
    (reference,) = caught.value.evidence_refs
    (header,) = root.rglob("header.json")
    assert reference.sha256 == physical._digest(header.read_bytes())
