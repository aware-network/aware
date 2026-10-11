from __future__ import annotations

import asyncio
import copy
import threading
from contextvars import ContextVar
from dataclasses import replace

import pytest
from aware_workspace_fs_adapter.repository_mutation_store import (
    WorkspaceRepositoryMutationStore,
)
from aware_workspace_runtime import repository_mutation as owner
from aware_workspace_runtime.change_evidence import (
    RepositoryBodyAvailability,
    RepositoryMutationKind,
    RepositoryMutationOutcome,
)
from aware_workspace_runtime.change_evidence_codec import (
    repository_authorized_mutation_from_payload,
    repository_authorized_mutation_payload,
)
from test_repository_mutation import _coordinate, _digest, _runtime


async def fixture(tmp_path):
    source = tmp_path / "issue.md"
    source.write_bytes(b"before")
    provider, session, bodies, coordinator = await _runtime(tmp_path)
    request = owner.WorkspaceRepositoryMutationRequest(
        operation_ref="operation:terminal-evidence",
        idempotency_key="attempt:terminal-evidence",
        mutation_kind=RepositoryMutationKind.UPDATE,
        expected_coordinate=_coordinate(session),
        target_path="issue.md",
        expected_exists=True,
        expected_content_digest=_digest(b"before"),
        content=b"after",
    )
    return source, provider, session, bodies, coordinator, request


async def retained(coordinator, request):
    receipt_ref = owner.repository_mutation_receipt_ref(
        repository_binding_ref=request.expected_coordinate.repository_binding_ref,
        operation_ref=request.operation_ref,
        idempotency_key=request.idempotency_key,
    )
    resolution = await coordinator.resolve_receipts((receipt_ref,))
    assert not resolution.missing_receipt_refs
    assert len(resolution.resolved) == 1
    return resolution.resolved[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("record_then_raise", [False, True])
async def test_body_retention_failure_preserves_known_applied_and_refuses_replay(
    tmp_path, monkeypatch, error_type, record_then_raise
):
    source, _, session, bodies, coordinator, request = await fixture(tmp_path)
    original_record = bodies.record
    original_writer = owner.mutate_confined_file
    writes = []
    records = []

    def write(**kwargs):
        writes.append(kwargs)
        return original_writer(**kwargs)

    def record(value):
        records.append(value)
        if record_then_raise:
            original_record(value)
        raise error_type("injected retention failure")

    monkeypatch.setattr(owner, "mutate_confined_file", write)
    monkeypatch.setattr(bodies, "record", record)
    try:
        result = await coordinator.mutate(request)
        assert source.read_bytes() == b"after"
        assert result.receipt.outcome is RepositoryMutationOutcome.APPLIED
        assert result.receipt.result_content_digest == _digest(b"after")
        assert result.evidence is not None
        assert result.evidence.changed_entries[0].new_body_availability is (
            RepositoryBodyAvailability.UNAVAILABLE
        )
        execution = result.execution_evidence
        assert execution.physical_return_state == "returned"
        assert execution.body_retention_state == "unknown"
        assert not execution.ledger_complete
        assert execution.diagnostics == (f"body_retention:{error_type.__name__}",)
        assert await retained(coordinator, request) is result
        assert await coordinator.mutate(request) is result
        assert len(writes) == len(records) == 1
        assert (
            repository_authorized_mutation_from_payload(
                repository_authorized_mutation_payload(result)
            )
            == result
        )
    finally:
        await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("write_then_raise", [False, True])
async def test_missing_physical_return_is_unknown_even_when_source_matches(
    tmp_path, monkeypatch, error_type, write_then_raise
):
    source, _, session, _, coordinator, request = await fixture(tmp_path)
    original_writer = owner.mutate_confined_file
    writes = []

    def interrupt(**kwargs):
        writes.append(kwargs)
        if write_then_raise:
            original_writer(**kwargs)
        raise error_type("injected unavailable physical return")

    monkeypatch.setattr(owner, "mutate_confined_file", interrupt)
    try:
        result = await coordinator.mutate(request)
        assert source.read_bytes() == (b"after" if write_then_raise else b"before")
        assert result.receipt.outcome is RepositoryMutationOutcome.FAILED
        assert result.receipt.physical_effect is None
        assert result.evidence is None
        assert result.execution_evidence.physical_return_state == "unavailable"
        assert not result.execution_evidence.ledger_complete
        assert await retained(coordinator, request) is result
        assert await coordinator.mutate(request) is result
        assert len(writes) == 1
        assert (
            repository_authorized_mutation_from_payload(
                repository_authorized_mutation_payload(result)
            )
            == result
        )
    finally:
        await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("unavailable_return", [False, True])
async def test_cancellation_settles_worker_before_releasing_original_transaction(
    tmp_path, monkeypatch, unavailable_return
):
    source, _, session, _, coordinator, request = await fixture(tmp_path)
    original_writer = owner.mutate_confined_file
    entered = threading.Event()
    proceed = threading.Event()
    writes = []

    def blocked_write(**kwargs):
        writes.append(kwargs)
        entered.set()
        assert proceed.wait(5), "test did not release worker"
        result = original_writer(**kwargs)
        if unavailable_return:
            raise KeyboardInterrupt("physical return interrupted")
        return result

    monkeypatch.setattr(owner, "mutate_confined_file", blocked_write)
    task = asyncio.create_task(coordinator.mutate(request))
    competitor_entered = asyncio.Event()

    async def competing_effect(snapshot):
        competitor_entered.set()
        return owner.WorkspaceRepositorySerializedEffect(
            value="probe", poll_after=False
        )

    competitor = None
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()  # repeated cancellation cannot abandon the original worker
        competitor = asyncio.create_task(
            session.run_serialized_transition(competing_effect)
        )
        await asyncio.sleep(0)
        assert not task.done()
        assert not competitor_entered.is_set()
        assert source.read_bytes() == b"before"
        proceed.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, 5)
        await asyncio.wait_for(competitor, 5)
        result = await retained(coordinator, request)
        assert source.read_bytes() == b"after"
        assert result.receipt.outcome is RepositoryMutationOutcome.FAILED
        assert not result.execution_evidence.ledger_complete
        assert result.execution_evidence.physical_return_state == (
            "unavailable" if unavailable_return else "returned"
        )
        if unavailable_return:
            assert result.receipt.physical_effect is None
        else:
            assert result.receipt.physical_effect.state == "applied"
        assert await coordinator.mutate(request) is result
        assert len(writes) == 1
    finally:
        proceed.set()
        if not task.done():
            await asyncio.gather(task, return_exceptions=True)
        if competitor is not None:
            await asyncio.gather(competitor, return_exceptions=True)
        await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt, SystemExit])
async def test_observer_interrupt_preserves_original_physical_effect(
    tmp_path, monkeypatch, error_type
):
    source, provider, session, _, coordinator, request = await fixture(tmp_path)

    async def fail(paths):
        raise error_type("observer unavailable")

    monkeypatch.setattr(provider, "observe_paths", fail)
    try:
        result = await coordinator.mutate(request)
        assert source.read_bytes() == b"after"
        assert result.receipt.outcome is RepositoryMutationOutcome.FAILED
        assert result.receipt.error_code == "observer_convergence_failed"
        assert result.receipt.physical_effect.state == "applied"
        assert result.execution_evidence.physical_return_state == "returned"
        assert not result.execution_evidence.ledger_complete
        assert await coordinator.mutate(request) is result
    finally:
        await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("unavailable_return", [False, True])
async def test_original_metadata_index_round_trips_terminal_results(
    tmp_path, monkeypatch, unavailable_return
):
    _, _, session, bodies, _, request = await fixture(tmp_path)
    binding_ref = session.binding.binding_key
    state_root = tmp_path / "state"
    index = WorkspaceRepositoryMutationStore(
        repository_binding_ref=binding_ref, state_root=state_root
    )
    coordinator = owner.WorkspaceRepositoryMutationCoordinator(
        session=session, body_store=bodies, result_store=index
    )
    if unavailable_return:
        original = owner.mutate_confined_file

        def write_then_interrupt(**kwargs):
            original(**kwargs)
            raise KeyboardInterrupt("missing physical return")

        monkeypatch.setattr(owner, "mutate_confined_file", write_then_interrupt)
    try:
        result = await coordinator.mutate(request)
        reopened = WorkspaceRepositoryMutationStore(
            repository_binding_ref=binding_ref, state_root=state_root
        )
        successor = owner.WorkspaceRepositoryMutationCoordinator(
            session=session, body_store=bodies, result_store=reopened
        )
        assert await successor.mutate(request) == result
        assert await retained(successor, request) == result
    finally:
        await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt, SystemExit])
async def test_metadata_failure_preserves_result_and_blocks_new_attempts(
    tmp_path, error_type
):
    source, _, session, bodies, _, request = await fixture(tmp_path)

    class UnavailableIndex:
        def resolve(self, receipt_ref):
            return None

        def record(self, *, fingerprint, result):
            raise error_type("metadata unavailable")

    coordinator = owner.WorkspaceRepositoryMutationCoordinator(
        session=session, body_store=bodies, result_store=UnavailableIndex()
    )
    try:
        result = await coordinator.mutate(request)
        assert source.read_bytes() == b"after"
        assert result.receipt.outcome is RepositoryMutationOutcome.APPLIED
        # Execution evidence and receipt-index persistence are separate. An
        # interrupted persist may already have saved this exact immutable result.
        assert result.execution_evidence.ledger_complete
        assert coordinator.result_store_error == (
            f"{error_type.__name__}: metadata unavailable"
        )
        assert await retained(coordinator, request) is result
        assert await coordinator.mutate(request) is result
        with pytest.raises(RuntimeError, match="metadata store is unavailable"):
            await coordinator.mutate(
                replace(request, idempotency_key="another-attempt")
            )
    finally:
        await session.stop()


@pytest.mark.asyncio
async def test_legacy_codec_stays_version_one_and_successor_is_detached(tmp_path):
    _, _, session, _, coordinator, request = await fixture(tmp_path)
    try:
        result = await coordinator.mutate(request)
        assert result.execution_evidence.body_retention_state == "retained"
        assert result.execution_evidence.ledger_complete
        successor = repository_authorized_mutation_payload(result)
        assert successor["contract_version"] == "2"
        historical = replace(result, execution_evidence=None)
        legacy = repository_authorized_mutation_payload(historical)
        assert legacy["contract_version"] == "1"
        assert set(legacy["value"]) == {"receipt", "evidence"}
        assert repository_authorized_mutation_from_payload(legacy) == historical
        restored = repository_authorized_mutation_from_payload(successor)
        successor["value"]["execution_evidence"]["diagnostics"].append("changed")
        assert restored.execution_evidence.diagnostics == ()
    finally:
        await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("physical_return_state", "none"),
        ("physical_return_state", None),
        ("body_retention_state", "complete"),
        ("ledger_complete", 1),
        ("diagnostics", [None]),
        ("diagnostics", "not-an-array"),
        ("diagnostics", [" "]),
    ],
)
async def test_successor_codec_refuses_malformed_execution_evidence(
    tmp_path, field, bad_value
):
    _, _, session, _, coordinator, request = await fixture(tmp_path)
    try:
        result = await coordinator.mutate(request)
        payload = repository_authorized_mutation_payload(result)
        payload["value"]["execution_evidence"][field] = bad_value
        with pytest.raises((ValueError, TypeError)):
            repository_authorized_mutation_from_payload(payload)
    finally:
        await session.stop()


@pytest.mark.asyncio
async def test_successor_codec_rejects_downgrade_and_missing_fields(tmp_path):
    _, _, session, _, coordinator, request = await fixture(tmp_path)
    try:
        result = await coordinator.mutate(request)
        payload = repository_authorized_mutation_payload(result)
        downgrade = copy.deepcopy(payload)
        downgrade["contract_version"] = "1"
        with pytest.raises(ValueError):
            repository_authorized_mutation_from_payload(downgrade)
        payload["value"].pop("execution_evidence")
        with pytest.raises(ValueError):
            repository_authorized_mutation_from_payload(payload)
    finally:
        await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("phase", ["physical", "observer", "bodies", "metadata"])
async def test_cancelled_error_at_each_owner_retains_terminal_result(
    tmp_path, monkeypatch, phase
):
    source, provider, session, bodies, coordinator, request = await fixture(tmp_path)

    def interrupted(*args, **kwargs):
        raise asyncio.CancelledError("owner interrupted")

    if phase == "physical":
        original = owner.mutate_confined_file

        def unavailable(**kwargs):
            original(**kwargs)
            interrupted()

        monkeypatch.setattr(owner, "mutate_confined_file", unavailable)
    elif phase == "observer":

        async def unavailable_observation(paths):
            interrupted()

        monkeypatch.setattr(provider, "observe_paths", unavailable_observation)
    elif phase == "bodies":
        monkeypatch.setattr(bodies, "record", interrupted)
    else:

        class CancelledIndex:
            def resolve(self, receipt_ref):
                return None

            record = staticmethod(interrupted)

        coordinator = owner.WorkspaceRepositoryMutationCoordinator(
            session=session, body_store=bodies, result_store=CancelledIndex()
        )
    try:
        with pytest.raises(asyncio.CancelledError):
            await coordinator.mutate(request)
        result = await retained(coordinator, request)
        assert source.read_bytes() == b"after"
        assert await coordinator.mutate(request) is result
        if phase in {"bodies", "metadata"}:
            assert result.receipt.outcome is RepositoryMutationOutcome.APPLIED
        else:
            assert result.receipt.outcome is RepositoryMutationOutcome.FAILED
        assert result.execution_evidence.physical_return_state == (
            "unavailable" if phase == "physical" else "returned"
        )
        if phase == "metadata":
            assert coordinator.result_store_error is not None
        else:
            assert not result.execution_evidence.ledger_complete
    finally:
        await session.stop()


@pytest.mark.asyncio
async def test_executor_preserves_original_context_propagation(tmp_path, monkeypatch):
    _, _, session, _, coordinator, request = await fixture(tmp_path)
    value = ContextVar("mutation-test-context")
    token = value.set("original-context")
    original = owner.mutate_confined_file
    seen = []

    def write(**kwargs):
        seen.append(value.get())
        return original(**kwargs)

    monkeypatch.setattr(owner, "mutate_confined_file", write)
    try:
        result = await coordinator.mutate(request)
        assert result.receipt.outcome is RepositoryMutationOutcome.APPLIED
        assert seen == ["original-context"]
    finally:
        value.reset(token)
        await session.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "evidence",
    [
        {
            "physical_return_state": "unavailable",
            "body_retention_state": "not_attempted",
            "ledger_complete": False,
            "diagnostics": [],
        },
        {
            "physical_return_state": "not_dispatched",
            "body_retention_state": "retained",
            "ledger_complete": True,
            "diagnostics": [],
        },
        {
            "physical_return_state": "returned",
            "body_retention_state": "unknown",
            "ledger_complete": True,
            "diagnostics": [],
        },
    ],
)
async def test_codec_rejects_contradictory_applied_execution(tmp_path, evidence):
    _, _, session, _, coordinator, request = await fixture(tmp_path)
    try:
        result = await coordinator.mutate(request)
        payload = repository_authorized_mutation_payload(result)
        payload["value"]["execution_evidence"] = evidence
        with pytest.raises(ValueError):
            repository_authorized_mutation_from_payload(payload)
    finally:
        await session.stop()
