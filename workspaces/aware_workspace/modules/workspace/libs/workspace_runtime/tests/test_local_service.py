from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from collections import deque
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from aware_local_service_runtime import (
    InMemoryLocalOperationalStateStore,
    LocalCallRequest,
    LocalCallStatus,
    LocalFailureCode,
    LocalObservationGapReason,
    LocalServiceHost,
    LocalServiceHostState,
)
from aware_workspace_runtime import (
    WORKSPACE_AGENT_INVOCABLE_OPERATION_CATALOG,
    WORKSPACE_AGENT_MUTATE_SOURCE_REQUEST_SCHEMA_DIGEST,
    WORKSPACE_AGENT_MUTATION_PREVIEW_OPERATION_CATALOG,
    WORKSPACE_AGENT_READ_SOURCE_REQUEST_SCHEMA_DIGEST,
    WORKSPACE_AGENT_SNAPSHOT_PAGE_MAX_ENTRIES,
    WORKSPACE_AGENT_SNAPSHOT_PAGE_REQUEST_SCHEMA_DIGEST,
    WORKSPACE_AGENT_SOURCE_MUTATION_MAX_BYTES,
    WORKSPACE_AGENT_SOURCE_READ_MAX_BYTES,
    WORKSPACE_LOCAL_SERVICE_CAPABILITY,
    WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF,
    WORKSPACE_SOURCE_CHANGES_TOPIC,
    FileSystemIndexObservationProvider,
    ObservationChangeKind,
    RepositoryContentDeltaResolutionState,
    RepositoryDiffBinaryPolicy,
    RepositoryEntryKind,
    RepositoryEvidencePosture,
    RepositoryEvidenceResolutionState,
    RepositoryMutationKind,
    RepositoryMutationOutcome,
    RepositoryObservationChange,
    RepositoryProviderObservation,
    RepositoryReportedChangeKind,
    RepositorySnapshotEntry,
    WorkspaceObservationNotStartedError,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryChangeEvidence,
    WorkspaceRepositoryChangeEvidenceResolver,
    WorkspaceRepositoryDeltaResident,
    WorkspaceRepositoryDiffRequest,
    WorkspaceRepositoryExternalEvidenceRef,
    WorkspaceRepositoryLocalServiceParticipant,
    WorkspaceRepositoryMutationCoordinator,
    WorkspaceRepositoryMutationRequest,
    WorkspaceRepositoryObservationSession,
    WorkspaceRepositoryOperationalBodyStore,
    WorkspaceRepositoryOperationalDiffProvider,
    WorkspaceRepositoryReportedChange,
    repository_authorized_mutation_from_payload,
    repository_change_evidence_from_payload,
    repository_change_evidence_payload,
    repository_change_evidence_ref,
    repository_content_delta_resolution_from_payload,
    repository_delta_capture_from_payload,
    repository_diff_page_from_payload,
    repository_diff_request_payload,
    repository_diff_request_ref,
    repository_entry_ref,
    repository_external_evidence_payload,
    repository_mutation_request_payload,
    workspace_agent_invocable_request_schema,
)
from aware_workspace_runtime.change_evidence import (
    WORKSPACE_REPOSITORY_EVIDENCE_GAP_EXACT_TRANSITION_UNAVAILABLE,
    WORKSPACE_REPOSITORY_EVIDENCE_GAP_OBSERVER_BASELINE_UNAVAILABLE,
)
from aware_workspace_runtime.repository_access import (
    WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF,
)
from test_repository_delta_retention_client import retained
from test_repository_mutation import ScanningProvider, _coordinate


class FakeProvider:
    def __init__(self, root_path: Path, initial: RepositoryProviderObservation) -> None:
        self._root_path = root_path.resolve()
        self.initial = initial
        self.polls: deque[RepositoryProviderObservation] = deque()
        self.targeted: deque[RepositoryProviderObservation] = deque()
        self.initialize_calls = 0
        self.poll_calls = 0
        self.observe_paths_calls: list[tuple[str, ...]] = []

    @property
    def root_path(self) -> Path:
        return self._root_path

    async def initialize(self) -> RepositoryProviderObservation:
        self.initialize_calls += 1
        return self.initial

    async def poll(self) -> RepositoryProviderObservation:
        self.poll_calls += 1
        return self.polls.popleft()

    async def observe_paths(
        self, paths: tuple[str, ...]
    ) -> RepositoryProviderObservation:
        self.observe_paths_calls.append(paths)
        return self.targeted.popleft()


class GatedInitializeProvider(FakeProvider):
    def __init__(self, root_path: Path, initial: RepositoryProviderObservation) -> None:
        super().__init__(root_path, initial)
        self.initialize_started = asyncio.Event()
        self.release_initialize = asyncio.Event()

    async def initialize(self) -> RepositoryProviderObservation:
        self.initialize_calls += 1
        self.initialize_started.set()
        await self.release_initialize.wait()
        return self.initial


def test_workspace_agent_catalog_is_exact_bounded_and_schema_bound() -> None:
    catalog = WORKSPACE_AGENT_INVOCABLE_OPERATION_CATALOG
    assert [item.operation_key for item in catalog.operations] == [
        "read_source",
        "snapshot_page",
    ]
    assert all(item.effect_class.value == "read_only" for item in catalog.operations)
    assert all(
        item.approval_kind.value == "not_required" for item in catalog.operations
    )
    assert {item.metadata["recommended_tool_name"] for item in catalog.operations} == {
        "workspace_read_source",
        "workspace_snapshot_page",
    }

    preview = WORKSPACE_AGENT_MUTATION_PREVIEW_OPERATION_CATALOG
    assert [item.operation_key for item in preview.operations] == [
        "mutate_source",
        "read_source",
        "snapshot_page",
    ]
    mutation = preview.operations[0]
    assert mutation.semantic_version == "0.2.0"
    assert mutation.effect_class.value == "authority_bound_mutation"
    assert mutation.approval_kind.value == "authority_receipt"
    assert mutation.idempotency_required is True
    assert mutation.receipt_schema_ref is not None
    assert mutation.result_observation_topics == (WORKSPACE_SOURCE_CHANGES_TOPIC,)
    assert all(
        item.effect_class.value == "read_only" for item in preview.operations[1:]
    )
    assert all(
        item.approval_kind.value == "not_required" for item in preview.operations[1:]
    )
    assert {item.metadata["recommended_tool_name"] for item in preview.operations} == {
        "workspace_read_source",
        "workspace_mutate_source",
        "workspace_snapshot_page",
    }
    assert not {
        "snapshot",
        "health",
        "poll",
        "composition",
        "read_source_chunk",
        "repository_descriptor",
        "repository_children",
        "repository_read_source",
        "acknowledge",
    }.intersection(item.operation_key for item in preview.operations)

    schemas = {
        item.operation_key: workspace_agent_invocable_request_schema(item.operation_key)
        for item in preview.operations
    }
    digests = {
        key: "sha256:"
        + hashlib.sha256(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        for key, value in schemas.items()
    }
    assert digests == {
        "mutate_source": WORKSPACE_AGENT_MUTATE_SOURCE_REQUEST_SCHEMA_DIGEST,
        "read_source": WORKSPACE_AGENT_READ_SOURCE_REQUEST_SCHEMA_DIGEST,
        "snapshot_page": WORKSPACE_AGENT_SNAPSHOT_PAGE_REQUEST_SCHEMA_DIGEST,
    }
    assert schemas["read_source"]["properties"]["max_bytes"]["maximum"] == (  # type: ignore[index]
        WORKSPACE_AGENT_SOURCE_READ_MAX_BYTES
    )
    assert schemas["snapshot_page"]["properties"]["limit"]["maximum"] == (  # type: ignore[index]
        WORKSPACE_AGENT_SNAPSHOT_PAGE_MAX_ENTRIES
    )
    assert schemas["mutate_source"]["properties"]["content"]["maxLength"] >= (  # type: ignore[index]
        WORKSPACE_AGENT_SOURCE_MUTATION_MAX_BYTES
    )
    assert schemas["mutate_source"]["properties"]["text_replacements"] == {  # type: ignore[index]
        "type": "array",
        "minItems": 1,
        "maxItems": 64,
        "items": {
            "type": "object",
            "properties": {
                "old_text": {"type": "string", "minLength": 1},
                "new_text": {"type": "string"},
            },
            "required": ["old_text", "new_text"],
            "additionalProperties": False,
        },
    }
    schemas["read_source"]["required"] = []
    assert workspace_agent_invocable_request_schema("read_source")["required"]
    with pytest.raises(KeyError, match="Unknown Workspace Agent operation"):
        workspace_agent_invocable_request_schema("snapshot")


def _entry(path: str, version: int = 1) -> RepositorySnapshotEntry:
    return RepositorySnapshotEntry(
        path=path,
        size_bytes=version,
        modified_ns=version,
    )


def _disk_entry(root: Path, relative_path: str) -> RepositorySnapshotEntry:
    metadata = (root / relative_path).stat()
    return RepositorySnapshotEntry(
        path=relative_path,
        size_bytes=metadata.st_size,
        modified_ns=metadata.st_mtime_ns,
    )


def _observation(
    entries: tuple[RepositorySnapshotEntry, ...],
    changes: tuple[RepositoryObservationChange, ...] = (),
) -> RepositoryProviderObservation:
    return RepositoryProviderObservation(
        observed_at=datetime.now(UTC), entries=entries, changes=changes
    )


def _create(entry: RepositorySnapshotEntry) -> RepositoryObservationChange:
    return RepositoryObservationChange(
        kind=ObservationChangeKind.CREATE,
        path=entry.path,
        entry=entry,
    )


def _update(entry: RepositorySnapshotEntry) -> RepositoryObservationChange:
    return RepositoryObservationChange(
        kind=ObservationChangeKind.UPDATE,
        path=entry.path,
        entry=entry,
    )


def _session(
    tmp_path: Path,
    provider: FakeProvider,
    *,
    journal_capacity: int = 8,
) -> WorkspaceRepositoryObservationSession:
    return WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
        journal_capacity=journal_capacity,
    )


def _host(
    participant: WorkspaceRepositoryLocalServiceParticipant,
    *,
    binding_key: str,
) -> LocalServiceHost:
    return LocalServiceHost(
        (participant,),
        state_store=InMemoryLocalOperationalStateStore(),
        admission={
            "workspace_repository_binding": {
                "binding_key": binding_key,
                "grant_ref": "workspace-grant-1",
            }
        },
    )


def _request(
    operation: str,
    *,
    payload: dict[str, object] | None = None,
    correlation_id: str = "corr-1",
    idempotency_key: str | None = None,
) -> LocalCallRequest:
    return LocalCallRequest(
        capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
        operation_key=operation,
        correlation_id=correlation_id,
        caller_provenance_kind="local_operator",
        authority_kind="local_uncommitted",
        payload=payload or {},
        idempotency_key=idempotency_key,
    )


@pytest.mark.asyncio
async def test_delta_capture_prepare_and_status_are_neutral_local_service_operations(
    tmp_path: Path,
) -> None:
    source = tmp_path / "selected.txt"
    source.write_bytes(b"before\n")
    before_entry = _disk_entry(tmp_path, "selected.txt")
    provider = FakeProvider(tmp_path, _observation((before_entry,)))
    session = _session(tmp_path, provider)
    store = retained(
        repository_binding_ref=session.binding.binding_key or "",
        state_root=tmp_path / ".state",
    )
    resident = WorkspaceRepositoryDeltaResident(session=session, store=store)
    participant = WorkspaceRepositoryLocalServiceParticipant(
        session,
        delta_resident=resident,
        background=False,
    )
    host = _host(participant, binding_key=session.binding.binding_key or "")
    await host.start()
    try:
        assert participant.descriptor.metadata["repository_change_operations"] == [
            "repository_delta_prepare",
            "repository_delta_status",
            "repository_delta_resolve_evidence",
        ]
        prepared = await host.call(
            _request(
                "repository_delta_prepare",
                payload={
                    "selected_paths": ["selected.txt"],
                    "context_refs": ["issue:one"],
                    "selection_kind": "exact",
                },
            )
        )
        assert prepared.status is LocalCallStatus.SUCCEEDED
        captures = prepared.payload["captures"]
        assert isinstance(captures, list)
        capture = repository_delta_capture_from_payload(captures[0])
        assert capture.selected_paths == ("selected.txt",)
        assert prepared.payload["resident"]["store"]["retained_body_count"] == 1  # type: ignore[index]

        scoped = await host.call(
            _request(
                "repository_delta_prepare",
                payload={
                    "selected_paths": ["missing", "selected.txt"],
                    "context_refs": ["issue:scoped"],
                    "selection_kind": "scope",
                },
                correlation_id="scope-prepare",
            )
        )
        assert scoped.status is LocalCallStatus.SUCCEEDED
        scoped_capture = repository_delta_capture_from_payload(
            scoped.payload["captures"][0]  # type: ignore[index]
        )
        assert scoped_capture.selected_paths == ("missing", "selected.txt")

        source.write_bytes(b"after\n")
        after_entry = _disk_entry(tmp_path, "selected.txt")
        provider.polls.append(_observation((after_entry,), (_update(after_entry),)))
        polled = await host.call(_request("poll", correlation_id="poll-1"))
        assert polled.status is LocalCallStatus.SUCCEEDED

        status = None
        for index in range(100):
            status = await host.call(
                _request(
                    "repository_delta_status",
                    payload={"capture_ref": capture.capture_ref},
                    correlation_id=f"status-{index}",
                )
            )
            if status.payload["resident"]["store"]["retained_delta_count"] == 1:  # type: ignore[index]
                break
            await asyncio.sleep(0.005)
        assert status is not None
        assert status.status is LocalCallStatus.SUCCEEDED
        assert repository_delta_capture_from_payload(status.payload["capture"])  # type: ignore[arg-type]
        assert status.payload["resident"]["capture"]["changed_body_read_count"] == 1  # type: ignore[index]

        reported = WorkspaceRepositoryChangeEvidence(
            evidence_ref=repository_change_evidence_ref(
                repository_binding_ref=session.binding.binding_key or "",
                evidence_key="external:reported",
            ),
            evidence_key="external:reported",
            revision=0,
            repository_binding_ref=session.binding.binding_key or "",
            posture=RepositoryEvidencePosture.PROVIDER_REPORTED,
            resolution_state=RepositoryEvidenceResolutionState.REPORTED,
            observed_at=datetime.now(UTC),
            external_evidence_refs=("reported",),
        )
        resolved = await host.call(
            _request(
                "repository_delta_resolve_evidence",
                payload={
                    "evidence": repository_change_evidence_payload(reported),
                    "context_refs": ["issue:one"],
                },
                correlation_id="resolve-1",
            )
        )
        resolution = repository_content_delta_resolution_from_payload(resolved.payload)
        assert resolution.state is RepositoryContentDeltaResolutionState.INCOMPATIBLE
    finally:
        await host.stop()


@pytest.mark.asyncio
async def test_repository_change_operations_preserve_replay_diff_and_capability(
    tmp_path: Path,
) -> None:
    (tmp_path / "src").mkdir()
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=ScanningProvider(tmp_path),
    )
    body_store = WorkspaceRepositoryOperationalBodyStore()
    coordinator = WorkspaceRepositoryMutationCoordinator(
        session=session,
        body_store=body_store,
    )
    participant = WorkspaceRepositoryLocalServiceParticipant(
        session,
        mutation_coordinator=coordinator,
        diff_provider=WorkspaceRepositoryOperationalDiffProvider(body_store=body_store),
        background=False,
    )
    host = _host(participant, binding_key=session.binding.binding_key or "")
    await host.start()
    try:
        assert participant.descriptor.metadata["repository_change_operations"] == [
            "repository_mutate",
            "repository_mutation_receipts_describe",
            "repository_diff",
        ]
        initialized = await host.call(_request("snapshot", correlation_id="snapshot-1"))
        assert initialized.status is LocalCallStatus.SUCCEEDED
        mutation = WorkspaceRepositoryMutationRequest(
            operation_ref="operation:local-service",
            idempotency_key="submission:local-service",
            mutation_kind=RepositoryMutationKind.CREATE,
            expected_coordinate=_coordinate(session),
            target_path="src/new.txt",
            expected_exists=False,
            expected_content_digest=None,
            content=b"before\nafter\n",
            context_refs=("issue:phase-04",),
        )
        first = await host.call(
            _request(
                "repository_mutate",
                payload=repository_mutation_request_payload(mutation),
                correlation_id="mutation-1",
            )
        )
        repeated = await host.call(
            _request(
                "repository_mutate",
                payload=repository_mutation_request_payload(mutation),
                correlation_id="mutation-2",
            )
        )
        assert first.status is LocalCallStatus.SUCCEEDED
        assert repeated.status is LocalCallStatus.SUCCEEDED
        result = repository_authorized_mutation_from_payload(first.payload)
        assert repository_authorized_mutation_from_payload(repeated.payload) == result
        assert result.receipt.outcome is RepositoryMutationOutcome.APPLIED
        assert result.evidence is not None

        described = await host.call(
            _request(
                "repository_mutation_receipts_describe",
                payload={
                    "mutation_receipt_refs": [
                        result.receipt.mutation_receipt_ref,
                        "mutation:missing",
                    ]
                },
                correlation_id="mutation-describe-1",
            )
        )
        assert described.status is LocalCallStatus.SUCCEEDED
        assert described.payload["repository_binding_ref"] == (
            session.binding.binding_key
        )
        assert described.payload["missing_receipt_refs"] == ["mutation:missing"]
        assert described.payload["store_error"] is None
        described_results = described.payload["resolved"]
        assert isinstance(described_results, list)
        assert repository_authorized_mutation_from_payload(
            described_results[0]
        ) == result

        diff_request = WorkspaceRepositoryDiffRequest(
            request_ref=repository_diff_request_ref(
                evidence_ref=result.evidence.evidence_ref,
                repository_binding_ref=result.evidence.repository_binding_ref,
                baseline=result.evidence.before_coordinate,
                target=result.evidence.after_coordinate,
                changed_entry_ref=None,
                continuation_ref=None,
                maximum_files=1,
                maximum_lines=100,
                maximum_bytes=16 * 1024,
                context_lines=3,
                binary_policy=RepositoryDiffBinaryPolicy.METADATA_ONLY,
            ),
            evidence_ref=result.evidence.evidence_ref,
            repository_binding_ref=result.evidence.repository_binding_ref,
            baseline=result.evidence.before_coordinate,
            target=result.evidence.after_coordinate,
            maximum_files=1,
            maximum_lines=100,
            maximum_bytes=16 * 1024,
        )
        diff = await host.call(
            _request(
                "repository_diff",
                payload=repository_diff_request_payload(diff_request),
                correlation_id="diff-1",
            )
        )
        assert diff.status is LocalCallStatus.SUCCEEDED
        page = repository_diff_page_from_payload(diff.payload)
        assert page.evidence_ref == result.evidence.evidence_ref
        assert page.complete
        assert page.returned_file_count == 1

        malformed = await host.call(
            _request(
                "repository_mutate",
                payload={"provider_operation": "write_file"},
                correlation_id="mutation-invalid",
            )
        )
        assert malformed.status is LocalCallStatus.FAILED
        assert malformed.failure is not None
        assert malformed.failure.code is LocalFailureCode.INVALID_REQUEST

    finally:
        await host.stop()


@pytest.mark.asyncio
async def test_external_evidence_is_terminal_gap_before_observer_initialization(
    tmp_path: Path,
) -> None:
    observed_at = datetime.now(UTC)
    provider = GatedInitializeProvider(
        tmp_path,
        RepositoryProviderObservation(observed_at=observed_at, entries=()),
    )
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="local-development",
    )
    participant = WorkspaceRepositoryLocalServiceParticipant(
        session,
        evidence_resolver=resolver,
        background=True,
    )
    host = _host(participant, binding_key=session.binding.binding_key or "")
    external = WorkspaceRepositoryExternalEvidenceRef(
        evidence_ref="agent-edit:before-initialization",
        source_namespace="aware.agent.runtime-edit-observation.v1",
        source_contract_version="1",
        observed_at=observed_at,
        changes=(
            WorkspaceRepositoryReportedChange(
                path="lib/new.dart",
                kind=RepositoryReportedChangeKind.CREATE,
            ),
        ),
        context_refs=("aware.agent.work-correlation:work:one",),
        correlation_started_at=observed_at - timedelta(seconds=1),
        correlation_ended_at=observed_at + timedelta(seconds=1),
    )
    await host.start()
    try:
        await asyncio.wait_for(provider.initialize_started.wait(), timeout=1)
        assert not session.observation_initialized
        result = await host.call(
            _request(
                "repository_correlate_external",
                correlation_id="correlate-before-initialization",
                payload={
                    "external_evidence": repository_external_evidence_payload(external),
                    "wait_timeout_milliseconds": 0,
                },
            )
        )
        assert result.status is LocalCallStatus.SUCCEEDED
        evidence = repository_change_evidence_from_payload(result.payload)
        assert evidence.posture is RepositoryEvidencePosture.GAP
        assert evidence.resolution_state.value == "gap"
        assert (
            evidence.reason
            == WORKSPACE_REPOSITORY_EVIDENCE_GAP_OBSERVER_BASELINE_UNAVAILABLE
        )
        assert evidence.changed_entries == ()
        assert evidence.before_coordinate is None
        assert evidence.after_coordinate is None
        assert not session.observation_initialized
        assert provider.initialize_calls == 1
        assert provider.poll_calls == 0
    finally:
        provider.release_initialize.set()
        await host.stop()


@pytest.mark.asyncio
async def test_external_evidence_observed_during_initialization_is_terminal_gap_after_baseline(
    tmp_path: Path,
) -> None:
    external_observed_at = datetime.now(UTC)
    baseline_observed_at = external_observed_at + timedelta(seconds=1)
    provider = GatedInitializeProvider(
        tmp_path,
        RepositoryProviderObservation(observed_at=baseline_observed_at, entries=()),
    )
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="local-development",
    )
    participant = WorkspaceRepositoryLocalServiceParticipant(
        session,
        evidence_resolver=resolver,
        background=True,
    )
    host = _host(participant, binding_key=session.binding.binding_key or "")
    external = WorkspaceRepositoryExternalEvidenceRef(
        evidence_ref="agent-edit:delayed-prebaseline-delivery",
        source_namespace="aware.agent.runtime-edit-observation.v1",
        source_contract_version="1",
        observed_at=external_observed_at,
        changes=(
            WorkspaceRepositoryReportedChange(
                path="lib/new.dart",
                kind=RepositoryReportedChangeKind.CREATE,
            ),
        ),
        context_refs=("aware.agent.work-correlation:work:one",),
        correlation_started_at=external_observed_at - timedelta(seconds=1),
        correlation_ended_at=external_observed_at + timedelta(seconds=1),
    )
    await host.start()
    try:
        await asyncio.wait_for(provider.initialize_started.wait(), timeout=1)
        provider.release_initialize.set()
        for _ in range(100):
            if session.observation_initialized:
                break
            await asyncio.sleep(0)
        assert session.observation_initialized
        assert session.baseline_observed_at == baseline_observed_at

        result = await host.call(
            _request(
                "repository_correlate_external",
                correlation_id="correlate-delayed-prebaseline-delivery",
                payload={
                    "external_evidence": repository_external_evidence_payload(external),
                    "wait_timeout_milliseconds": 0,
                },
            )
        )

        assert result.status is LocalCallStatus.SUCCEEDED
        evidence = repository_change_evidence_from_payload(result.payload)
        assert evidence.posture is RepositoryEvidencePosture.GAP
        assert evidence.resolution_state.value == "gap"
        assert (
            evidence.reason
            == WORKSPACE_REPOSITORY_EVIDENCE_GAP_OBSERVER_BASELINE_UNAVAILABLE
        )
        assert evidence.changed_entries == ()
        assert evidence.before_coordinate is None
        assert evidence.after_coordinate is None
        assert provider.poll_calls == 0
    finally:
        provider.release_initialize.set()
        await host.stop()


@pytest.mark.asyncio
async def test_background_participant_initializes_without_first_request(
    tmp_path: Path,
) -> None:
    observed_at = datetime.now(UTC)
    provider = GatedInitializeProvider(
        tmp_path,
        RepositoryProviderObservation(observed_at=observed_at, entries=()),
    )
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    participant = WorkspaceRepositoryLocalServiceParticipant(
        session,
        background=True,
    )
    host = _host(participant, binding_key=session.binding.binding_key or "")

    await host.start()
    try:
        await asyncio.wait_for(provider.initialize_started.wait(), timeout=1)
        assert not session.observation_initialized
        provider.release_initialize.set()
        for _ in range(100):
            if session.observation_initialized:
                break
            await asyncio.sleep(0)
        assert session.observation_initialized
        assert provider.initialize_calls == 1
    finally:
        provider.release_initialize.set()
        await host.stop()


@pytest.mark.asyncio
async def test_repository_readiness_does_not_wait_for_held_initialization(
    tmp_path: Path,
) -> None:
    observed_at = datetime.now(UTC)
    provider = GatedInitializeProvider(
        tmp_path,
        RepositoryProviderObservation(
            observed_at=observed_at,
            entries=(RepositorySnapshotEntry("README.md", 7, 42),),
        ),
    )
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    participant = WorkspaceRepositoryLocalServiceParticipant(
        session,
        background=True,
    )
    host = _host(participant, binding_key=session.binding.binding_key or "")
    readiness_payload = {
        "preparation_ref": "repository-preparation:opaque",
        "workspace_grant_ref": "workspace-grant:opaque",
        "repository_grant_ref": "repository-grant:opaque",
        "display_name": "aware",
        "display_path": "aware",
    }

    await host.start()
    try:
        await asyncio.wait_for(provider.initialize_started.wait(), timeout=1)
        preparing = await asyncio.wait_for(
            host.call(_request("repository_prepare", payload=readiness_payload)),
            timeout=0.1,
        )
        observed = await asyncio.wait_for(
            host.call(
                _request(
                    "repository_access_readiness",
                    payload=readiness_payload,
                    correlation_id="observe-during-prepare",
                )
            ),
            timeout=0.1,
        )

        assert preparing.status is LocalCallStatus.SUCCEEDED
        assert preparing.payload["state"] == "initializing"
        assert preparing.payload["revision"] == 0
        assert preparing.payload["descriptor"] is None
        assert observed.status is LocalCallStatus.SUCCEEDED
        assert observed.payload["state"] == "initializing"
        assert provider.initialize_calls == 1

        provider.release_initialize.set()
        for _ in range(100):
            ready = await host.call(
                _request(
                    "repository_access_readiness",
                    payload=readiness_payload,
                    correlation_id="observe-ready",
                )
            )
            if ready.payload["state"] == "ready":
                break
            await asyncio.sleep(0)

        assert ready.payload["revision"] == 1
        assert ready.payload["failure_code"] is None
        descriptor = ready.payload["descriptor"]
        assert descriptor["grant_ref"] == "repository-grant:opaque"
        assert descriptor["observed_source_entry_count"] == 1
        assert "entries" not in descriptor
    finally:
        provider.release_initialize.set()
        await host.stop()


@pytest.mark.asyncio
async def test_repository_external_evidence_correlation_is_strict_and_neutral(
    tmp_path: Path,
) -> None:
    started = datetime.now(UTC) - timedelta(seconds=5)
    provider = FakeProvider(
        tmp_path,
        RepositoryProviderObservation(observed_at=started, entries=()),
    )
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    resolver = WorkspaceRepositoryChangeEvidenceResolver(
        session=session,
        consumer_key="local-development",
    )
    participant = WorkspaceRepositoryLocalServiceParticipant(
        session,
        evidence_resolver=resolver,
        background=False,
    )
    host = _host(participant, binding_key=session.binding.binding_key or "")
    await host.start()
    try:
        assert participant.descriptor.metadata["repository_change_operations"] == [
            "repository_correlate_external",
            "repository_observe_paths",
        ]
        created = RepositorySnapshotEntry(
            path="lib/new.dart",
            size_bytes=3,
            modified_ns=1,
            content_digest="sha256:new",
        )
        provider.polls.append(
            RepositoryProviderObservation(
                observed_at=started + timedelta(seconds=1),
                entries=(created,),
                changes=(
                    RepositoryObservationChange(
                        kind=ObservationChangeKind.CREATE,
                        path=created.path,
                        entry=created,
                    ),
                ),
            )
        )
        polled = await host.call(_request("poll", correlation_id="poll-evidence"))
        assert polled.status is LocalCallStatus.SUCCEEDED
        external = WorkspaceRepositoryExternalEvidenceRef(
            evidence_ref="agent-edit:one",
            source_namespace="aware.agent.runtime-edit-observation.v1",
            source_contract_version="1",
            observed_at=started + timedelta(seconds=2),
            changes=(
                WorkspaceRepositoryReportedChange(
                    path="lib/new.dart",
                    kind=RepositoryReportedChangeKind.CREATE,
                ),
            ),
            context_refs=("aware.agent.work-correlation:work:one",),
            correlation_started_at=started,
            correlation_ended_at=started + timedelta(seconds=3),
        )
        result = await host.call(
            _request(
                "repository_correlate_external",
                correlation_id="correlate-evidence",
                payload={
                    "external_evidence": repository_external_evidence_payload(external),
                    "wait_timeout_milliseconds": 0,
                },
            )
        )
        assert result.status is LocalCallStatus.SUCCEEDED
        evidence = repository_change_evidence_from_payload(result.payload)
        assert evidence.posture is RepositoryEvidencePosture.PROVIDER_CORRELATED
        assert evidence.external_evidence_refs == (external.evidence_ref,)

        malformed = await host.call(
            _request(
                "repository_correlate_external",
                correlation_id="correlate-malformed",
                payload={
                    "external_evidence": {"provider": "codex"},
                    "wait_timeout_milliseconds": 0,
                },
            )
        )
        assert malformed.status is LocalCallStatus.FAILED
        assert malformed.failure is not None
        assert malformed.failure.code is LocalFailureCode.INVALID_REQUEST

        unmatched = WorkspaceRepositoryExternalEvidenceRef(
            evidence_ref="agent-edit:unmatched",
            source_namespace="aware.agent.runtime-edit-observation.v1",
            source_contract_version="1",
            observed_at=started + timedelta(seconds=2),
            changes=(
                WorkspaceRepositoryReportedChange(
                    path="lib/other.dart",
                    kind=RepositoryReportedChangeKind.UPDATE,
                ),
            ),
            correlation_started_at=started,
            correlation_ended_at=started + timedelta(seconds=3),
        )
        completed = await host.call(
            _request(
                "repository_correlate_external",
                correlation_id="correlate-completed-unmatched",
                payload={
                    "external_evidence": repository_external_evidence_payload(
                        unmatched
                    ),
                    "wait_timeout_milliseconds": 0,
                    "observation_completed": True,
                },
            )
        )
        completed_evidence = repository_change_evidence_from_payload(completed.payload)
        assert completed_evidence.posture is RepositoryEvidencePosture.GAP
        assert (
            completed_evidence.reason
            == WORKSPACE_REPOSITORY_EVIDENCE_GAP_EXACT_TRANSITION_UNAVAILABLE
        )
    finally:
        await host.stop()


@pytest.mark.asyncio
async def test_restart_checkpoint_correlates_edit_during_host_startup(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    source = repository / "lib" / "main.dart"
    source.parent.mkdir()
    source.write_text("void main() {}\n", encoding="utf-8")
    cache_dir = tmp_path / "source-index"
    binding = WorkspaceRepositoryBinding(repository)

    first_session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FileSystemIndexObservationProvider(
            binding=binding,
            cache_dir=cache_dir,
        ),
    )
    await first_session.start(background=False)
    await first_session.stop()

    source.write_text("void main() => print('aware');\n", encoding="utf-8")
    provider_observed_at = datetime.now(UTC)
    restarted_session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=FileSystemIndexObservationProvider(
            binding=binding,
            cache_dir=cache_dir,
        ),
    )
    participant = WorkspaceRepositoryLocalServiceParticipant(
        restarted_session,
        evidence_resolver=WorkspaceRepositoryChangeEvidenceResolver(
            session=restarted_session,
            consumer_key="restart-proof",
        ),
        background=False,
    )
    host = _host(participant, binding_key=binding.binding_key or "")
    await host.start()
    try:
        initialized = await host.call(
            _request("snapshot", correlation_id="restart-snapshot")
        )
        assert initialized.status is LocalCallStatus.SUCCEEDED
        snapshot = restarted_session.current_snapshot
        assert snapshot.cursor == 1
        external = WorkspaceRepositoryExternalEvidenceRef(
            evidence_ref="agent-edit:during-restart",
            source_namespace="aware.agent.runtime-edit-observation.v1",
            source_contract_version="1",
            observed_at=provider_observed_at,
            changes=(
                WorkspaceRepositoryReportedChange(
                    path="lib/main.dart",
                    kind=RepositoryReportedChangeKind.UPDATE,
                ),
            ),
            correlation_started_at=provider_observed_at - timedelta(seconds=5),
            correlation_ended_at=provider_observed_at + timedelta(seconds=5),
        )
        correlated = await host.call(
            _request(
                "repository_correlate_external",
                correlation_id="correlate-during-restart",
                payload={
                    "external_evidence": repository_external_evidence_payload(external),
                    "wait_timeout_milliseconds": 0,
                },
            )
        )
        evidence = repository_change_evidence_from_payload(correlated.payload)
        assert evidence.posture is RepositoryEvidencePosture.PROVIDER_CORRELATED
        assert [item.new_path for item in evidence.changed_entries] == ["lib/main.dart"]
    finally:
        await host.stop()


@pytest.mark.asyncio
async def test_repository_change_operations_fail_closed_when_not_mounted(
    tmp_path: Path,
) -> None:
    provider = ScanningProvider(tmp_path)
    session = WorkspaceRepositoryObservationSession(
        binding=WorkspaceRepositoryBinding(tmp_path),
        provider=provider,
    )
    participant = WorkspaceRepositoryLocalServiceParticipant(
        session,
        background=False,
    )
    host = _host(participant, binding_key=session.binding.binding_key or "")
    await host.start()
    try:
        assert participant.descriptor.metadata["repository_change_operations"] == []
        result = await host.call(_request("repository_diff", payload={"bad": True}))
        assert result.status is LocalCallStatus.FAILED
        assert result.failure is not None
        assert result.failure.code is LocalFailureCode.DEPENDENCY_UNAVAILABLE
    finally:
        await host.stop()


def _read_payload(
    session: WorkspaceRepositoryObservationSession,
    path: str,
    *,
    encoding: str = "utf-8",
    **overrides: object,
) -> dict[str, object]:
    try:
        snapshot = session.current_snapshot
        epoch = snapshot.epoch
        cursor = snapshot.cursor
        snapshot_digest = snapshot.snapshot_digest
    except RuntimeError:
        provider = session.provider
        assert isinstance(provider, FakeProvider)
        epoch = session.epoch
        cursor = 0
        snapshot_digest = provider.initial.snapshot_digest
    payload: dict[str, object] = {
        "path": path,
        "expected_epoch": epoch,
        "expected_cursor": cursor,
        "expected_snapshot_digest": snapshot_digest,
        "encoding": encoding,
    }
    payload.update(overrides)
    return payload


def _chunk_payload(
    session: WorkspaceRepositoryObservationSession,
    path: str,
    *,
    offset: int = 0,
    chunk_index: int = 0,
    expected_content_digest: str | None = None,
    **overrides: object,
) -> dict[str, object]:
    try:
        snapshot = session.current_snapshot
        binding_key = snapshot.binding_key
        epoch = snapshot.epoch
        cursor = snapshot.cursor
        snapshot_digest = snapshot.snapshot_digest
    except RuntimeError:
        provider = session.provider
        assert isinstance(provider, FakeProvider)
        binding_key = session.binding.binding_key
        epoch = session.epoch
        cursor = 0
        snapshot_digest = provider.initial.snapshot_digest
    payload: dict[str, object] = {
        "path": path,
        "expected_binding_key": binding_key,
        "expected_epoch": epoch,
        "expected_cursor": cursor,
        "expected_snapshot_digest": snapshot_digest,
        "expected_content_digest": expected_content_digest,
        "offset_bytes": offset,
        "chunk_index": chunk_index,
        "chunk_size_bytes": 128 * 1024,
        "max_document_bytes": 1024 * 1024,
    }
    payload.update(overrides)
    return payload


def _snapshot_page_continuation(
    page: dict[str, object],
    *,
    after_path: object,
    limit: object = 128,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "after_path": after_path,
        "limit": limit,
        "expected_binding_key": page["binding_key"],
        "expected_epoch": page["epoch"],
        "expected_cursor": page["cursor"],
        "expected_snapshot_digest": page["snapshot_digest"],
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_host_starts_exactly_one_injected_workspace_observer(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation((_entry("README.md"),)))
    session = _session(tmp_path, provider)
    participant = WorkspaceRepositoryLocalServiceParticipant(session, background=False)
    host = _host(participant, binding_key=str(session.binding.binding_key))
    first = await host.start()
    second = await host.start()
    assert first.state is second.state is LocalServiceHostState.READY
    assert provider.initialize_calls == 0
    await host.call(_request("snapshot"))
    assert provider.initialize_calls == 1
    assert host.dependency_order == (WORKSPACE_LOCAL_SERVICE_CAPABILITY,)
    assert (
        host.invocable_operation_catalog.catalog_digest
        == WORKSPACE_AGENT_MUTATION_PREVIEW_OPERATION_CATALOG.catalog_digest
    )
    assert participant.descriptor.metadata["background_observation"] is False
    assert (
        participant.descriptor.metadata["background_poll_policy"] == "cost_governed_v1"
    )
    assert participant.descriptor.metadata["background_poll_maximum_duty_cycle"] == 0.10
    await host.stop()


@pytest.mark.asyncio
async def test_mismatched_admission_fails_before_provider_initialization(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    session = _session(tmp_path, provider)
    participant = WorkspaceRepositoryLocalServiceParticipant(session, background=False)
    snapshot = await _host(participant, binding_key="wrong").start()
    assert snapshot.state is LocalServiceHostState.FAILED
    assert provider.initialize_calls == 0


def test_source_read_budget_cannot_exceed_json_safe_contract(tmp_path: Path) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    session = _session(tmp_path, provider)
    with pytest.raises(ValueError, match="JSON-safe"):
        WorkspaceRepositoryLocalServiceParticipant(
            session,
            source_read_max_bytes=1024 * 1024,
        )


@pytest.mark.asyncio
async def test_snapshot_health_and_strict_invalid_operations(tmp_path: Path) -> None:
    entry = _entry("docs/one.md")
    provider = FakeProvider(tmp_path, _observation((entry,)))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    snapshot = await host.call(_request("snapshot"))
    assert snapshot.status is LocalCallStatus.SUCCEEDED
    assert snapshot.payload["authority_kind"] == "local_uncommitted"
    assert snapshot.payload["entries"] == [
        {
            "path": "docs/one.md",
            "size_bytes": 1,
            "modified_ns": 1,
            "content_digest": None,
        }
    ]
    health = await host.call(_request("health", correlation_id="health"))
    assert health.payload["files_tracked"] == 1
    invalid = await host.call(_request("unknown", correlation_id="invalid"))
    assert invalid.status is LocalCallStatus.FAILED
    assert invalid.failure is not None
    wrong_authority = LocalCallRequest(
        capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
        operation_key="snapshot",
        correlation_id="canonical",
        caller_provenance_kind="service_adapter",
        authority_kind="canonical_service",
    )
    rejected = await host.call(wrong_authority)
    assert rejected.status is LocalCallStatus.FAILED


@pytest.mark.asyncio
async def test_poll_and_many_replays_share_one_cursor_writer(tmp_path: Path) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    created = _entry("docs/created.md")
    provider.polls.append(_observation((created,), (_create(created),)))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    poll = await host.call(_request("poll", idempotency_key="poll-1"))
    assert poll.status is LocalCallStatus.SUCCEEDED
    assert poll.payload["changed"] is True
    assert provider.poll_calls == 1

    replays = await asyncio.gather(
        *(
            host.replay_observations(
                capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
                topic_key=WORKSPACE_SOURCE_CHANGES_TOPIC,
                requested_epoch=session.epoch,
                after_cursor=0,
            )
            for _ in range(64)
        )
    )
    assert all(replay.current_cursor == 1 for replay in replays)
    assert all(replay.envelopes[0].cursor == 1 for replay in replays)
    assert all(
        replay.envelopes[0].payload["changes"][0]["path"]  # type: ignore[index]
        == "docs/created.md"
        for replay in replays
    )
    assert provider.poll_calls == 1


@pytest.mark.asyncio
async def test_exact_path_observation_is_a_bounded_local_service_operation(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    created = _entry("docs/created.md")
    provider.targeted.append(_observation((created,), (_create(created),)))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()

    observed = await host.call(
        _request(
            "repository_observe_paths",
            payload={"selected_paths": ["docs/created.md"]},
        )
    )

    assert observed.status is LocalCallStatus.SUCCEEDED
    assert observed.payload["changed"] is True
    assert observed.payload["batch"]["changes"][0]["path"] == "docs/created.md"  # type: ignore[index]
    assert provider.observe_paths_calls == [("docs/created.md",)]
    assert provider.poll_calls == 0

    invalid = await host.call(
        _request(
            "repository_observe_paths",
            payload={"selected_paths": ["../outside"]},
            correlation_id="invalid-exact-path",
        )
    )
    assert invalid.status is LocalCallStatus.FAILED
    assert invalid.failure is not None
    assert invalid.failure.code is LocalFailureCode.INVALID_REQUEST


@pytest.mark.asyncio
async def test_retention_gap_contains_current_workspace_reset_snapshot(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    first = _entry("one.md", 1)
    second = _entry("one.md", 2)
    provider.polls.extend(
        [
            _observation((first,), (_create(first),)),
            _observation((second,), (_update(second),)),
        ]
    )
    session = _session(tmp_path, provider, journal_capacity=1)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    await host.call(_request("poll", idempotency_key="poll-1"))
    await host.call(_request("poll", idempotency_key="poll-2"))
    replay = await host.replay_observations(
        capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
        topic_key=WORKSPACE_SOURCE_CHANGES_TOPIC,
        requested_epoch=session.epoch,
        after_cursor=0,
    )
    assert replay.gap is not None
    assert replay.gap.reason is LocalObservationGapReason.RETENTION_EXCEEDED
    assert replay.gap.reset_snapshot.cursor == 2
    entries = replay.gap.reset_snapshot.payload["entries"]
    assert entries[0]["modified_ns"] == 2  # type: ignore[index]


@pytest.mark.asyncio
async def test_acknowledgement_retains_independent_workspace_checkpoint(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    result = await host.call(
        _request(
            "acknowledge",
            payload={
                "consumer_key": "issue.resolver",
                "epoch": session.epoch,
                "cursor": 0,
                "projection_digest": "sha256:projection",
            },
        )
    )
    assert result.status is LocalCallStatus.SUCCEEDED
    assert session.checkpoint_for("issue.resolver") is not None
    assert result.participant_receipt["authority_kind"] == "local_uncommitted"  # type: ignore[index]


@pytest.mark.asyncio
async def test_read_source_returns_exact_snapshot_bound_utf8_content(
    tmp_path: Path,
) -> None:
    source = tmp_path / "docs" / "issue.md"
    source.parent.mkdir()
    content = "# Issue\n\nStatus: Open\n"
    source.write_text(content)
    provider = FakeProvider(
        tmp_path, _observation((_disk_entry(tmp_path, "docs/issue.md"),))
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()

    result = await host.call(
        _request("read_source", payload=_read_payload(session, "docs/issue.md"))
    )

    assert result.status is LocalCallStatus.SUCCEEDED
    assert result.payload["content"] == content
    assert result.payload["encoding"] == "utf-8"
    assert result.payload["content_digest"] == (
        f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"
    )
    assert result.payload["snapshot_digest"] == session.current_snapshot.snapshot_digest
    assert result.participant_receipt is not None
    assert result.participant_receipt["authority_kind"] == "local_uncommitted"


@pytest.mark.asyncio
async def test_read_source_supports_binary_base64(tmp_path: Path) -> None:
    content = b"\x00\xffaware\x80"
    (tmp_path / "artifact.bin").write_bytes(content)
    provider = FakeProvider(
        tmp_path, _observation((_disk_entry(tmp_path, "artifact.bin"),))
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()

    result = await host.call(
        _request(
            "read_source",
            payload=_read_payload(session, "artifact.bin", encoding="base64"),
        )
    )

    assert result.status is LocalCallStatus.SUCCEEDED
    assert result.payload["content"] == base64.b64encode(content).decode("ascii")


@pytest.mark.asyncio
async def test_read_source_maximum_utf8_payload_remains_json_safe(
    tmp_path: Path,
) -> None:
    content = b"\x00" * (128 * 1024)
    (tmp_path / "bounded.txt").write_bytes(content)
    provider = FakeProvider(
        tmp_path,
        _observation((_disk_entry(tmp_path, "bounded.txt"),)),
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    result = await host.call(
        _request(
            "read_source",
            payload=_read_payload(session, "bounded.txt"),
        )
    )
    assert result.status is LocalCallStatus.SUCCEEDED
    assert len(result.payload["content"]) == len(content)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_chunked_source_read_binds_exact_document_and_never_widens_chunk(
    tmp_path: Path,
) -> None:
    content = ("shared-world-å\n" * 30_000).encode("utf-8")
    source = tmp_path / "large.aware"
    source.write_bytes(content)
    provider = FakeProvider(
        tmp_path, _observation((_disk_entry(tmp_path, "large.aware"),))
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()

    observed: list[bytes] = []
    expected_digest: str | None = None
    offset = 0
    index = 0
    while True:
        result = await host.call(
            _request(
                "read_source_chunk",
                payload=_chunk_payload(
                    session,
                    "large.aware",
                    offset=offset,
                    chunk_index=index,
                    expected_content_digest=expected_digest,
                ),
                correlation_id=f"chunk-{index}",
            )
        )
        assert result.status is LocalCallStatus.SUCCEEDED
        chunk = base64.b64decode(result.payload["content"], validate=True)  # type: ignore[arg-type]
        assert len(chunk) <= 128 * 1024
        assert result.payload["binding_key"] == session.current_snapshot.binding_key
        assert result.payload["chunk_index"] == index
        assert result.payload["offset_bytes"] == offset
        expected_digest = str(result.payload["content_digest"])
        observed.append(chunk)
        offset = int(result.payload["next_offset_bytes"])
        if result.payload["complete"] is True:
            break
        index += 1

    assert b"".join(observed) == content
    assert expected_digest == f"sha256:{hashlib.sha256(content).hexdigest()}"


@pytest.mark.asyncio
async def test_chunked_source_read_fails_closed_on_mid_read_source_drift(
    tmp_path: Path,
) -> None:
    source = tmp_path / "large.aware"
    source.write_bytes(b"a" * (256 * 1024))
    provider = FakeProvider(
        tmp_path, _observation((_disk_entry(tmp_path, "large.aware"),))
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    first = await host.call(
        _request(
            "read_source_chunk",
            payload=_chunk_payload(session, "large.aware"),
        )
    )
    source.write_bytes(b"b" * (256 * 1024))
    second = await host.call(
        _request(
            "read_source_chunk",
            payload=_chunk_payload(
                session,
                "large.aware",
                offset=128 * 1024,
                chunk_index=1,
                expected_content_digest=str(first.payload["content_digest"]),
            ),
            correlation_id="chunk-2",
        )
    )
    assert second.status is LocalCallStatus.FAILED
    assert second.failure is not None
    assert second.failure.code is LocalFailureCode.CONFLICT
    assert second.failure.retryable is True


@pytest.mark.asyncio
async def test_chunked_source_read_rejects_document_above_dev_ceiling(
    tmp_path: Path,
) -> None:
    source = tmp_path / "too-large.aware"
    source.write_bytes(b"x" * (1024 * 1024 + 1))
    provider = FakeProvider(
        tmp_path, _observation((_disk_entry(tmp_path, "too-large.aware"),))
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    result = await host.call(
        _request(
            "read_source_chunk",
            payload=_chunk_payload(session, "too-large.aware"),
        )
    )
    assert result.status is LocalCallStatus.FAILED
    assert result.failure is not None
    assert result.failure.code is LocalFailureCode.INVALID_REQUEST


@pytest.mark.asyncio
@pytest.mark.parametrize("maximum_document", [4 * 1024 * 1024, 4 * 1024 * 1024 + 1])
async def test_chunked_source_read_rejects_above_new_document_or_request_ceiling(
    tmp_path: Path, maximum_document: int,
) -> None:
    source = tmp_path / "too-large.aware"
    source.write_bytes(b"x" * (4 * 1024 * 1024 + 1))
    provider = FakeProvider(tmp_path, _observation((_disk_entry(tmp_path, source.name),)))
    session = _session(tmp_path, provider)
    host = _host(WorkspaceRepositoryLocalServiceParticipant(session, background=False),
                 binding_key=str(session.binding.binding_key))
    await host.start()
    try:
        result = await host.call(_request("read_source_chunk", payload=_chunk_payload(
            session, source.name, max_document_bytes=maximum_document,
        )))
        assert result.status is LocalCallStatus.FAILED
        assert result.failure is not None
        assert result.failure.code is LocalFailureCode.INVALID_REQUEST
    finally:
        await host.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("expected_epoch", "stale-epoch"),
        ("expected_cursor", 99),
        ("expected_snapshot_digest", "sha256:" + "0" * 64),
    ],
)
async def test_read_source_rejects_stale_snapshot_coordinates(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    (tmp_path / "issue.md").write_text("issue")
    provider = FakeProvider(
        tmp_path, _observation((_disk_entry(tmp_path, "issue.md"),))
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    result = await host.call(
        _request(
            "read_source",
            payload=_read_payload(session, "issue.md", **{field: value}),
        )
    )
    assert result.status is LocalCallStatus.FAILED
    assert result.failure is not None
    assert result.failure.code is LocalFailureCode.CONFLICT
    assert result.failure.retryable is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path", ["../outside.md", "/tmp/outside.md", "docs\\issue.md", "docs/../issue.md"]
)
async def test_read_source_rejects_noncanonical_or_escaping_paths(
    tmp_path: Path,
    path: str,
) -> None:
    provider = FakeProvider(tmp_path, _observation(()))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    result = await host.call(
        _request("read_source", payload=_read_payload(session, path))
    )
    assert result.status is LocalCallStatus.FAILED
    assert result.failure is not None
    assert result.failure.code is LocalFailureCode.INVALID_REQUEST


@pytest.mark.asyncio
async def test_read_source_rejects_symlink_components(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (outside / "secret.md").write_text("secret")
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    provider = FakeProvider(
        tmp_path,
        _observation((_disk_entry(tmp_path, "linked/secret.md"),)),
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    result = await host.call(
        _request("read_source", payload=_read_payload(session, "linked/secret.md"))
    )
    assert result.status is LocalCallStatus.FAILED
    assert result.failure is not None
    assert result.failure.code is LocalFailureCode.CONFLICT


@pytest.mark.asyncio
async def test_read_source_rejects_deleted_replaced_and_oversized_sources(
    tmp_path: Path,
) -> None:
    source = tmp_path / "issue.md"
    source.write_text("five!")
    entry = _disk_entry(tmp_path, "issue.md")
    provider = FakeProvider(tmp_path, _observation((entry,)))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(
            session, background=False, source_read_max_bytes=4
        ),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    oversized = await host.call(
        _request("read_source", payload=_read_payload(session, "issue.md"))
    )
    assert oversized.failure is not None
    assert oversized.failure.code is LocalFailureCode.INVALID_REQUEST

    await host.stop()
    source.unlink()
    stale_provider = FakeProvider(tmp_path, _observation((entry,)))
    stale_session = _session(tmp_path, stale_provider)
    stale_host = _host(
        WorkspaceRepositoryLocalServiceParticipant(stale_session, background=False),
        binding_key=str(stale_session.binding.binding_key),
    )
    await stale_host.start()
    deleted = await stale_host.call(
        _request(
            "read_source",
            payload=_read_payload(stale_session, "issue.md", max_bytes=100),
            correlation_id="deleted",
        )
    )
    assert deleted.failure is not None
    assert deleted.failure.code is LocalFailureCode.CONFLICT
    assert deleted.failure.retryable is True

    source.write_text("replacement is longer")
    replaced = await stale_host.call(
        _request(
            "read_source",
            payload=_read_payload(stale_session, "issue.md", max_bytes=100),
            correlation_id="replaced",
        )
    )
    assert replaced.failure is not None
    assert replaced.failure.code is LocalFailureCode.CONFLICT


@pytest.mark.asyncio
async def test_snapshot_pages_reconstruct_inventory_above_json_item_budget(
    tmp_path: Path,
) -> None:
    entries = tuple(_entry(f"docs/source-{index:04d}.aware") for index in range(3000))
    provider = FakeProvider(tmp_path, _observation(entries))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()

    legacy = await host.call(_request("snapshot"))
    assert legacy.status is LocalCallStatus.FAILED
    assert legacy.failure is not None
    assert legacy.failure.code is LocalFailureCode.PROVIDER_FAILURE

    expected_paths = [entry.path for entry in entries]
    observed_paths: list[str] = []
    page_count = 0
    request_payload: dict[str, object] = {"after_path": None, "limit": 128}
    while True:
        result = await host.call(
            _request(
                "snapshot_page",
                payload=request_payload,
                correlation_id=f"page-{page_count}",
            )
        )
        assert result.status is LocalCallStatus.SUCCEEDED
        page = dict(result.payload)
        assert page["entry_count"] == len(entries)
        assert isinstance(page["entries"], list)
        assert page["returned_count"] == len(page["entries"])
        assert len(page["entries"]) <= 128
        observed_paths.extend(str(item["path"]) for item in page["entries"])
        page_count += 1
        if page["complete"] is True:
            assert page["next_after_path"] is None
            break
        assert page["next_after_path"] == observed_paths[-1]
        request_payload = _snapshot_page_continuation(
            page,
            after_path=page["next_after_path"],
        )

    assert page_count == 24
    assert observed_paths == expected_paths
    await host.stop()


@pytest.mark.asyncio
async def test_snapshot_page_continuation_fails_closed(
    tmp_path: Path,
) -> None:
    entries = (_entry("a.aware"), _entry("b.aware"), _entry("c.aware"))
    provider = FakeProvider(tmp_path, _observation(entries))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    first = await host.call(
        _request("snapshot_page", payload={"after_path": None, "limit": 1})
    )
    assert first.status is LocalCallStatus.SUCCEEDED
    page = dict(first.payload)

    invalid_payloads = (
        {"after_path": "a.aware", "limit": 1},
        {"after_path": None, "limit": 129},
        {
            "after_path": "a.aware",
            "limit": 1,
            "expected_epoch": page["epoch"],
        },
        _snapshot_page_continuation(page, after_path="missing.aware", limit=1),
    )
    for index, payload in enumerate(invalid_payloads):
        result = await host.call(
            _request(
                "snapshot_page",
                payload=payload,
                correlation_id=f"invalid-page-{index}",
            )
        )
        assert result.status is LocalCallStatus.FAILED
        assert result.failure is not None
        assert result.failure.code is LocalFailureCode.INVALID_REQUEST

    stale = await host.call(
        _request(
            "snapshot_page",
            payload=_snapshot_page_continuation(
                page,
                after_path="a.aware",
                limit=1,
                expected_snapshot_digest="sha256:stale",
            ),
            correlation_id="stale-page",
        )
    )
    assert stale.status is LocalCallStatus.FAILED
    assert stale.failure is not None
    assert stale.failure.code is LocalFailureCode.CONFLICT
    assert stale.failure.retryable is True
    await host.stop()


@pytest.mark.asyncio
async def test_snapshot_page_continuation_retains_exact_snapshot_during_advance(
    tmp_path: Path,
) -> None:
    entries = (_entry("a.aware"), _entry("b.aware"), _entry("c.aware"))
    provider = FakeProvider(tmp_path, _observation(entries))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    first_result = await host.call(
        _request("snapshot_page", payload={"after_path": None, "limit": 1})
    )
    assert first_result.status is LocalCallStatus.SUCCEEDED
    first = dict(first_result.payload)

    created = _entry("d.aware")
    provider.polls.append(_observation((*entries, created), (_create(created),)))
    advanced = await host.call(_request("poll"))
    assert advanced.status is LocalCallStatus.SUCCEEDED
    assert session.current_snapshot.cursor == 1

    second_result = await host.call(
        _request(
            "snapshot_page",
            payload=_snapshot_page_continuation(
                first,
                after_path="a.aware",
                limit=1,
            ),
        )
    )
    assert second_result.status is LocalCallStatus.SUCCEEDED
    second = dict(second_result.payload)
    assert second["entries"] == [
        {
            "path": "b.aware",
            "size_bytes": 1,
            "modified_ns": 1,
            "content_digest": None,
        }
    ]
    assert second["cursor"] == first["cursor"] == 0

    final_result = await host.call(
        _request(
            "snapshot_page",
            payload=_snapshot_page_continuation(
                first,
                after_path="b.aware",
                limit=1,
            ),
        )
    )
    assert final_result.status is LocalCallStatus.SUCCEEDED
    assert final_result.payload["complete"] is True
    assert [item["path"] for item in final_result.payload["entries"]] == ["c.aware"]

    released = await host.call(
        _request(
            "snapshot_page",
            payload=_snapshot_page_continuation(
                first,
                after_path="a.aware",
                limit=1,
            ),
        )
    )
    assert released.status is LocalCallStatus.FAILED
    assert released.failure is not None
    assert released.failure.code is LocalFailureCode.CONFLICT
    await host.stop()


@pytest.mark.asyncio
async def test_snapshot_page_totalizes_untransportable_entry_path(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(tmp_path, _observation((_entry("a" * 16_385),)))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()

    result = await host.call(
        _request("snapshot_page", payload={"after_path": None, "limit": 1})
    )

    assert result.status is LocalCallStatus.FAILED
    assert result.failure is not None
    assert result.failure.code is LocalFailureCode.PROVIDER_FAILURE
    await host.stop()


@pytest.mark.asyncio
async def test_read_source_rejects_invalid_utf8_and_detects_in_read_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "issue.md"
    source.write_bytes(b"\xff")
    provider = FakeProvider(
        tmp_path, _observation((_disk_entry(tmp_path, "issue.md"),))
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    invalid_utf8 = await host.call(
        _request("read_source", payload=_read_payload(session, "issue.md"))
    )
    assert invalid_utf8.failure is not None
    assert invalid_utf8.failure.code is LocalFailureCode.INVALID_REQUEST

    original_read = __import__("os").read
    mutated = False

    def mutate_then_read(descriptor: int, count: int) -> bytes:
        nonlocal mutated
        if not mutated:
            mutated = True
            source.write_bytes(b"changed during read")
        return original_read(descriptor, count)

    monkeypatch.setattr(
        "aware_workspace_runtime.local_service.os.read", mutate_then_read
    )
    raced = await host.call(
        _request(
            "read_source",
            payload=_read_payload(session, "issue.md", encoding="base64"),
            correlation_id="race",
        )
    )
    assert raced.failure is not None
    assert raced.failure.code is LocalFailureCode.CONFLICT
    assert raced.failure.retryable is True


@pytest.mark.asyncio
async def test_many_source_readers_do_not_poll_or_advance_workspace_cursor(
    tmp_path: Path,
) -> None:
    (tmp_path / "issue.md").write_text("shared")
    provider = FakeProvider(
        tmp_path, _observation((_disk_entry(tmp_path, "issue.md"),))
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    results = await asyncio.gather(
        *(
            host.call(
                _request(
                    "read_source",
                    payload=_read_payload(session, "issue.md"),
                    correlation_id=f"read-{index}",
                )
            )
            for index in range(64)
        )
    )
    assert all(result.status is LocalCallStatus.SUCCEEDED for result in results)
    assert session.current_snapshot.cursor == 0
    assert provider.initialize_calls == 1
    assert provider.poll_calls == 0


@pytest.mark.asyncio
async def test_repository_descriptor_children_and_exact_read_share_one_observer(
    tmp_path: Path,
) -> None:
    source = tmp_path / "src" / "main.py"
    source.parent.mkdir()
    source.write_text("print('aware')\n")
    readme = tmp_path / "README.md"
    readme.write_text("# Neutral repository\n")
    provider = FakeProvider(
        tmp_path,
        _observation(
            (_disk_entry(tmp_path, "README.md"), _disk_entry(tmp_path, "src/main.py"))
        ),
    )
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()

    descriptor = await host.call(_request("repository_descriptor"))
    assert descriptor.status is LocalCallStatus.SUCCEEDED
    assert (
        descriptor.payload["contract_ref"] == WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF
    )
    assert "entries" not in descriptor.payload
    coordinate = descriptor.payload["coordinate"]
    children = await host.call(
        _request(
            "repository_children",
            payload={
                "parent_path": "",
                "continuation_ref": None,
                "limit": 10,
                "expected_binding_key": coordinate["repository_binding_ref"],
                "expected_epoch": coordinate["epoch"],
                "expected_cursor": coordinate["cursor"],
                "expected_snapshot_digest": coordinate["snapshot_digest"],
            },
            correlation_id="children",
        )
    )
    assert [value["name"] for value in children.payload["entries"]] == [
        "src",
        "README.md",
    ]
    read_entry_ref = repository_entry_ref(
        binding_ref=str(session.binding.binding_key),
        snapshot_digest=str(coordinate["snapshot_digest"]),
        path="README.md",
        kind=RepositoryEntryKind.REGULAR_FILE,
    )
    read = await host.call(
        _request(
            "repository_read_source",
            payload={
                "entry_ref": read_entry_ref,
                "path": "README.md",
                "expected_binding_key": coordinate["repository_binding_ref"],
                "expected_epoch": coordinate["epoch"],
                "expected_cursor": coordinate["cursor"],
                "expected_snapshot_digest": coordinate["snapshot_digest"],
                "encoding": "utf-8",
                "max_bytes": 4096,
            },
            correlation_id="read-repository-source",
        )
    )
    assert read.status is LocalCallStatus.SUCCEEDED
    assert read.payload["entry_ref"] == read_entry_ref
    assert read.payload["content"] == "# Neutral repository\n"
    assert read.payload["content_classification"] == "text"
    assert provider.initialize_calls == 1
    assert provider.poll_calls == 0
    await host.stop()


@pytest.mark.asyncio
async def test_repository_path_search_is_exact_bounded_and_tree_identical(
    tmp_path: Path,
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Search\n")
    guide = tmp_path / "docs" / "guide.md"
    guide.parent.mkdir()
    guide.write_text("# Guide\n")
    provider = FakeProvider(
        tmp_path,
        _observation(
            (_disk_entry(tmp_path, "README.md"), _disk_entry(tmp_path, "docs/guide.md"))
        ),
    )
    session = _session(tmp_path, provider)
    participant = WorkspaceRepositoryLocalServiceParticipant(
        session,
        background=False,
    )
    host = _host(participant, binding_key=str(session.binding.binding_key))
    await host.start()

    descriptor = await host.call(_request("repository_descriptor"))
    coordinate = descriptor.payload["coordinate"]
    result = await host.call(
        _request(
            "repository_search_paths",
            payload={
                "query_ref": "repository-query:local-service",
                "query": "guide",
                "continuation_ref": None,
                "maximum_results": 20,
                "maximum_examined": 1000,
                "expected_binding_key": coordinate["repository_binding_ref"],
                "expected_epoch": coordinate["epoch"],
                "expected_cursor": coordinate["cursor"],
                "expected_snapshot_digest": coordinate["snapshot_digest"],
                "expected_visibility_policy_ref": coordinate["visibility_policy_ref"],
                "expected_visibility_policy_version": coordinate[
                    "visibility_policy_version"
                ],
            },
            correlation_id="search-paths",
        )
    )

    assert result.status is LocalCallStatus.SUCCEEDED
    assert (
        result.payload["contract_ref"] == WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF
    )
    assert result.payload["query_ref"] == "repository-query:local-service"
    assert result.payload["examined_count"] == 2
    assert result.payload["returned_count"] == 1
    match = result.payload["matches"][0]
    assert match["entry"]["path"] == "docs/guide.md"
    assert match["entry"]["entry_ref"] == repository_entry_ref(
        binding_ref=str(session.binding.binding_key),
        snapshot_digest=str(coordinate["snapshot_digest"]),
        path="docs/guide.md",
        kind=RepositoryEntryKind.REGULAR_FILE,
    )
    assert provider.initialize_calls == 1
    assert provider.poll_calls == 0
    assert (
        participant.descriptor.metadata["repository_path_search_contract_ref"]
        == WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF
    )
    await host.stop()


@pytest.mark.asyncio
async def test_repository_path_search_fails_closed_on_stale_coordinate(
    tmp_path: Path,
) -> None:
    source = tmp_path / "README.md"
    source.write_text("before")
    first = _disk_entry(tmp_path, "README.md")
    provider = FakeProvider(tmp_path, _observation((first,)))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    descriptor = await host.call(_request("repository_descriptor"))
    coordinate = descriptor.payload["coordinate"]
    source.write_text("after")
    next_entry = _disk_entry(tmp_path, "README.md")
    provider.polls.append(_observation((next_entry,), (_update(next_entry),)))
    await host.call(_request("poll", correlation_id="advance-search"))

    stale = await host.call(
        _request(
            "repository_search_paths",
            payload={
                "query_ref": "repository-query:stale",
                "query": "readme",
                "continuation_ref": None,
                "maximum_results": 20,
                "maximum_examined": 1000,
                "expected_binding_key": coordinate["repository_binding_ref"],
                "expected_epoch": coordinate["epoch"],
                "expected_cursor": coordinate["cursor"],
                "expected_snapshot_digest": coordinate["snapshot_digest"],
                "expected_visibility_policy_ref": coordinate["visibility_policy_ref"],
                "expected_visibility_policy_version": coordinate[
                    "visibility_policy_version"
                ],
            },
            correlation_id="stale-search",
        )
    )

    assert stale.failure is not None
    assert stale.failure.code is LocalFailureCode.CONFLICT
    assert stale.failure.retryable is True
    await host.stop()


@pytest.mark.asyncio
async def test_repository_catalog_and_read_fail_stale_without_mixing_coordinates(
    tmp_path: Path,
) -> None:
    source = tmp_path / "README.md"
    source.write_text("before")
    first = _disk_entry(tmp_path, "README.md")
    provider = FakeProvider(tmp_path, _observation((first,)))
    session = _session(tmp_path, provider)
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(session.binding.binding_key),
    )
    await host.start()
    descriptor = await host.call(_request("repository_descriptor"))
    coordinate = descriptor.payload["coordinate"]
    source.write_text("after")
    next_entry = _disk_entry(tmp_path, "README.md")
    provider.polls.append(_observation((next_entry,), (_update(next_entry),)))
    await host.call(_request("poll", correlation_id="advance"))

    stale_payload = {
        "parent_path": "",
        "continuation_ref": None,
        "limit": 10,
        "expected_binding_key": coordinate["repository_binding_ref"],
        "expected_epoch": coordinate["epoch"],
        "expected_cursor": coordinate["cursor"],
        "expected_snapshot_digest": coordinate["snapshot_digest"],
    }
    stale_children = await host.call(
        _request("repository_children", payload=stale_payload, correlation_id="stale")
    )
    assert stale_children.failure is not None
    assert stale_children.failure.code is LocalFailureCode.CONFLICT
    assert stale_children.failure.retryable is True

    stale_ref = repository_entry_ref(
        binding_ref=str(coordinate["repository_binding_ref"]),
        snapshot_digest=str(coordinate["snapshot_digest"]),
        path="README.md",
        kind=RepositoryEntryKind.REGULAR_FILE,
    )
    stale_read = await host.call(
        _request(
            "repository_read_source",
            payload={
                "entry_ref": stale_ref,
                "path": "README.md",
                "expected_binding_key": coordinate["repository_binding_ref"],
                "expected_epoch": coordinate["epoch"],
                "expected_cursor": coordinate["cursor"],
                "expected_snapshot_digest": coordinate["snapshot_digest"],
                "encoding": "utf-8",
                "max_bytes": 1024,
            },
            correlation_id="stale-read",
        )
    )
    assert stale_read.failure is not None
    assert stale_read.failure.code is LocalFailureCode.CONFLICT
    assert stale_read.failure.retryable is True
    await host.stop()


@pytest.mark.asyncio
async def test_bounded_query_bootstraps_without_full_index_and_reads_exact_source(
    tmp_path: Path,
) -> None:
    issue = tmp_path / "docs/issues/2026/08/21/fb-2026-08-21-query.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("# Issue: Query\n")
    (issue.parent / ".gitignore").write_text("ignored.md\n")
    (issue.parent / "ignored.md").write_text("# Ignored\n")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    for index in range(100):
        (unrelated / f"{index}.txt").write_text("unrelated")
    binding = WorkspaceRepositoryBinding(tmp_path)
    provider = FileSystemIndexObservationProvider(
        binding=binding,
        cache_dir=tmp_path.parent / f"{tmp_path.name}-query-cache",
    )
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=provider,
    )
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(binding.binding_key),
    )

    await host.start()

    assert session.authority_admitted
    assert provider.index.scanner._session_cache is None
    with pytest.raises(WorkspaceObservationNotStartedError):
        _ = session.current_snapshot

    query_payload = {
        "query_ref": "coordination-test.v1",
        "prefixes": ["docs/issues"],
        "maximum_depth": 4,
        "maximum_entries": 1000,
        "maximum_examined": 2000,
        "suffixes": [".md"],
        "after_path": None,
        "limit": 128,
    }
    first = await host.call(_request("repository_query", payload=query_payload))
    assert first.status is LocalCallStatus.SUCCEEDED
    assert [entry["path"] for entry in first.payload["entries"]] == [
        "docs/issues/2026/08/21/fb-2026-08-21-query.md"
    ]
    assert provider.index.scanner._session_cache is None
    same = await host.call(
        _request(
            "repository_query",
            payload=query_payload,
            correlation_id="query-unchanged",
        )
    )
    assert same.payload["cursor"] == first.payload["cursor"]
    assert same.payload["snapshot_digest"] == first.payload["snapshot_digest"]
    assert same.payload["changed_paths"] == []

    read_payload = {
        "query_ref": first.payload["query_ref"],
        "path": "docs/issues/2026/08/21/fb-2026-08-21-query.md",
        "expected_epoch": first.payload["epoch"],
        "expected_cursor": first.payload["cursor"],
        "expected_query_digest": first.payload["query_digest"],
        "expected_snapshot_digest": first.payload["snapshot_digest"],
    }
    read = await host.call(
        _request("repository_query_read_source", payload=read_payload)
    )
    assert read.status is LocalCallStatus.SUCCEEDED
    assert read.payload["content"] == "# Issue: Query\n"

    issue.write_text("# Issue: Query changed\n")
    changed = await host.call(
        _request(
            "repository_query",
            payload=query_payload,
            correlation_id="query-changed",
        )
    )
    assert changed.payload["cursor"] == first.payload["cursor"] + 1
    assert changed.payload["changed_paths"] == [
        "docs/issues/2026/08/21/fb-2026-08-21-query.md"
    ]
    stale = await host.call(
        _request(
            "repository_query_read_source",
            payload=read_payload,
            correlation_id="query-stale-read",
        )
    )
    assert stale.failure is not None
    assert stale.failure.code is LocalFailureCode.CONFLICT
    await host.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("document_bytes", [256 * 1024, 1024 * 1024 + 1, 4 * 1024 * 1024, 4 * 1024 * 1024 + 1])
async def test_bounded_query_reads_large_exact_source_in_digest_stable_chunks(
    tmp_path: Path, document_bytes: int,
) -> None:
    issue = tmp_path / "docs/issues/2026/08/21/fb-2026-08-21-large.md"
    issue.parent.mkdir(parents=True)
    header = b"# Issue: Large\n"
    content = header + b"x" * (document_bytes - len(header))
    issue.write_bytes(content)
    binding = WorkspaceRepositoryBinding(tmp_path)
    provider = FileSystemIndexObservationProvider(
        binding=binding,
        cache_dir=tmp_path.parent / f"{tmp_path.name}-query-chunk-cache",
    )
    session = WorkspaceRepositoryObservationSession(
        binding=binding,
        provider=provider,
    )
    host = _host(
        WorkspaceRepositoryLocalServiceParticipant(session, background=False),
        binding_key=str(binding.binding_key),
    )
    await host.start()
    query = await host.call(
        _request(
            "repository_query",
            payload={
                "query_ref": "coordination-large-test.v1",
                "prefixes": ["docs/issues"],
                "maximum_depth": 4,
                "maximum_entries": 1000,
                "maximum_examined": 2000,
                "suffixes": [".md"],
                "after_path": None,
                "limit": 128,
            },
        )
    )
    assert query.status is LocalCallStatus.SUCCEEDED

    observed: list[bytes] = []
    expected_digest: str | None = None
    offset = 0
    index = 0
    while True:
        result = await host.call(
            _request(
                "repository_query_read_source_chunk",
                payload={
                    "query_ref": query.payload["query_ref"],
                    "path": "docs/issues/2026/08/21/fb-2026-08-21-large.md",
                    "expected_binding_key": query.payload["binding_key"],
                    "expected_epoch": query.payload["epoch"],
                    "expected_cursor": query.payload["cursor"],
                    "expected_query_digest": query.payload["query_digest"],
                    "expected_snapshot_digest": query.payload["snapshot_digest"],
                    "expected_content_digest": expected_digest,
                    "offset_bytes": offset,
                    "chunk_index": index,
                    "chunk_size_bytes": 128 * 1024,
                    "max_document_bytes": 4 * 1024 * 1024,
                },
                correlation_id=f"query-chunk-{index}",
            )
        )
        if document_bytes > 4 * 1024 * 1024:
            assert result.status is LocalCallStatus.FAILED
            assert result.failure is not None
            assert result.failure.code is LocalFailureCode.INVALID_REQUEST
            await host.stop()
            return
        assert result.status is LocalCallStatus.SUCCEEDED
        encoded = result.payload["content"]
        observed.append(base64.b64decode(encoded, validate=True))  # type: ignore[arg-type]
        expected_digest = str(result.payload["content_digest"])
        offset = int(result.payload["next_offset_bytes"])
        if result.payload["complete"] is True:
            break
        index += 1

    assert b"".join(observed) == content
    assert expected_digest == f"sha256:{hashlib.sha256(content).hexdigest()}"
    await host.stop()


@pytest.mark.asyncio
async def test_large_query_chunk_read_rejects_mid_read_source_movement(tmp_path: Path) -> None:
    path = "docs/issues/2026/08/21/fb-2026-08-21-moving.md"
    source = tmp_path / path
    source.parent.mkdir(parents=True)
    source.write_bytes(b"a" * (2 * 1024 * 1024))
    binding = WorkspaceRepositoryBinding(tmp_path)
    provider = FileSystemIndexObservationProvider(
        binding=binding, cache_dir=tmp_path.parent / f"{tmp_path.name}-moving-cache",
    )
    host = _host(WorkspaceRepositoryLocalServiceParticipant(
        WorkspaceRepositoryObservationSession(binding=binding, provider=provider), background=False,
    ), binding_key=str(binding.binding_key))
    await host.start()
    try:
        query = await host.call(_request("repository_query", payload={
            "query_ref": "moving-large.v1", "prefixes": ["docs/issues"],
            "maximum_depth": 4, "maximum_entries": 1000, "maximum_examined": 2000,
            "suffixes": [".md"], "after_path": None, "limit": 128,
        }))
        assert query.status is LocalCallStatus.SUCCEEDED
        payload: dict[str, object] = {
            "query_ref": query.payload["query_ref"], "path": path,
            "expected_binding_key": query.payload["binding_key"],
            "expected_epoch": query.payload["epoch"], "expected_cursor": query.payload["cursor"],
            "expected_query_digest": query.payload["query_digest"],
            "expected_snapshot_digest": query.payload["snapshot_digest"],
            "expected_content_digest": None, "offset_bytes": 0, "chunk_index": 0,
            "chunk_size_bytes": 128 * 1024, "max_document_bytes": 4 * 1024 * 1024,
        }
        first = await host.call(_request("repository_query_read_source_chunk", payload=payload))
        assert first.status is LocalCallStatus.SUCCEEDED
        source.write_bytes(b"b" * (2 * 1024 * 1024))
        second = await host.call(_request("repository_query_read_source_chunk", payload={
            **payload, "expected_content_digest": first.payload["content_digest"],
            "offset_bytes": 128 * 1024, "chunk_index": 1,
        }, correlation_id="changed-large"))
        assert second.status is LocalCallStatus.FAILED
        assert second.failure is not None
        assert second.failure.code is LocalFailureCode.CONFLICT
        assert second.failure.retryable
    finally:
        await host.stop()
