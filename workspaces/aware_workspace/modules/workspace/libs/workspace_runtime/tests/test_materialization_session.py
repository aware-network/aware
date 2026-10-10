from __future__ import annotations

import copy
import json
import statistics
import tempfile
import time
from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_local_service_runtime import (
    InMemoryLocalOperationalStateStore,
    LocalOperationalStateConflict,
)
from aware_workspace_runtime.materialization_session import (
    WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE,
    WORKSPACE_MATERIALIZATION_SESSION_HEAD_NAMESPACE,
    WorkspaceMaterializationSessionAdmission,
    WorkspaceMaterializationSessionAppendRequest,
    WorkspaceMaterializationSessionAppendRequestV3,
    WorkspaceMaterializationSessionAuthorityGrade,
    WorkspaceMaterializationSessionBaselineGrade,
    WorkspaceMaterializationSessionConflict,
    WorkspaceMaterializationSessionError,
    WorkspaceMaterializationSessionEvent,
    WorkspaceMaterializationSessionEventV3,
    WorkspaceMaterializationSessionGapReason,
    WorkspaceMaterializationSessionJournal,
    WorkspaceMaterializationSessionSourceEvidenceV3,
    admit_workspace_materialization_session_append,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD,
    WorkspacePublishedSemanticCoordinate,
    WorkspaceSemanticMaterializationHead,
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
    WorkspaceSemanticMaterializationHeadV3,
    WorkspaceSemanticMaterializationPublicationError,
    WorkspaceSemanticMaterializationPublicationReceipt,
    WorkspaceSemanticMaterializationPublicationReceiptV3,
    WorkspaceSemanticMaterializationRequestV3,
    WorkspaceStagedSemanticBody,
)


def _digest(marker: str) -> str:
    return "sha256:" + marker * 64


def _semantic_digest(contract: str, payload: object) -> str:
    return ContentDigest.of_bytes(
        canonical_json_bytes({"contract": contract, "value": payload})
    ).value


def _coordinate(
    role: str, marker: str, size: int = 10
) -> WorkspacePublishedSemanticCoordinate:
    return WorkspacePublishedSemanticCoordinate(
        role=role,
        contract_key=f"test.{role}",
        contract_version="1",
        contract_schema_digest=_digest(marker),
        value_ref=f"test-{role}-{marker}",
        body_digest=_digest(marker),
        size_bytes=size,
    )


def _publication(
    marker: str = "a", *, package_ref: str = "aware-dev-sdk", revision: int = 1
) -> WorkspaceSemanticMaterializationPublicationReceipt:
    candidate = _coordinate("result", marker, 100)
    outputs = tuple(
        sorted(
            _coordinate("output", marker, 30_000 + index)
            for index, marker in enumerate("bcdef0")
        )
    )
    bodies = tuple(
        sorted(
            WorkspaceStagedSemanticBody(
                coordinate=item,
                body_ref=(
                    "cas://workspace-semantic-materialization/body/"
                    + item.body_digest[7:]
                ),
            )
            for item in (candidate, *outputs)
        )
    )
    values: dict[str, object] = {
        "package_ref": package_ref,
        "package_kind": "sdk",
        "manifest_digest": _digest("1"),
        "source_authority_ref": "workspace-source:test",
        "source_authority_digest": _digest("2"),
        "request_ref": "cas://workspace-semantic-materialization/request/test",
        "request_digest": _digest("3"),
        "operation_ref": "workspace-operation:materialize",
        "operation_digest": _digest("4"),
        "invocation_digest": _digest("5"),
        "profile_digest": _digest("6"),
        "terminal_status": "delta",
        "result_digest": _digest("7"),
        "result_body_ref": (
            "cas://workspace-semantic-materialization/body/" + "8" * 64
        ),
        "result_body_digest": _digest("8"),
        "result_body_size_bytes": 236_237,
        "candidate": candidate,
        "transition_digest": _digest("9"),
        "effect_digest": _digest("a"),
        "outputs": outputs,
        "semantic_bodies": bodies,
        "output_activation": "staged_not_applied",
    }
    payload = {
        **{
            key: values[key]
            for key in (
                "package_ref",
                "package_kind",
                "manifest_digest",
                "source_authority_ref",
                "source_authority_digest",
                "request_ref",
                "request_digest",
                "operation_ref",
                "operation_digest",
                "invocation_digest",
                "profile_digest",
                "terminal_status",
                "result_digest",
                "result_body_ref",
                "result_body_digest",
                "result_body_size_bytes",
            )
        },
        "candidate": candidate.to_dict(),
        "transition_digest": values["transition_digest"],
        "effect_digest": values["effect_digest"],
        "outputs": [item.to_dict() for item in outputs],
        "semantic_bodies": [item.to_dict() for item in bodies],
        "output_activation": "staged_not_applied",
    }
    head = WorkspaceSemanticMaterializationHead(
        **values,
        head_digest=_semantic_digest(WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD, payload),
    )
    return WorkspaceSemanticMaterializationPublicationReceipt.create(
        head=head,
        observed_result_digest=head.result_digest,
        observed_result_body_ref=head.result_body_ref,
        observed_result_body_digest=head.result_body_digest,
        observed_semantic_bodies=bodies,
        prior_head_revision=revision - 1,
        head_revision=revision,
        head_advanced=True,
    )


class _Authority:
    operation_ref = "workspace-session-operation:append"
    operation_digest = _digest("d")

    def __init__(
        self,
        request_digest: str,
        *,
        grade: WorkspaceMaterializationSessionAuthorityGrade = (
            WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL
        ),
        permitted: tuple[str, ...] = ("aware-dev-sdk",),
    ) -> None:
        self._request_digest = request_digest
        self._grade = grade
        self._permitted = permitted

    @property
    def authority_grade(self) -> WorkspaceMaterializationSessionAuthorityGrade:
        return self._grade

    def admits(self, request: WorkspaceMaterializationSessionAppendRequest) -> bool:
        return request.request_digest == self._request_digest

    def permitted_package_refs_for(
        self, request: WorkspaceMaterializationSessionAppendRequest
    ) -> tuple[str, ...]:
        assert request.request_digest == self._request_digest
        return self._permitted


def _request(
    publication: WorkspaceSemanticMaterializationPublicationReceipt,
    *,
    expected_revision: int = 0,
    expected_cursor: int = 0,
    predecessor: str | None = None,
    attempt: str = "attempt:one",
) -> WorkspaceMaterializationSessionAppendRequest:
    return WorkspaceMaterializationSessionAppendRequest.create(
        workspace_session_ref="workspace-session:test",
        epoch="session-epoch:test",
        participant_ref="participant:test",
        actor_ref="actor:test",
        workflow_session_ref="workflow-session:test",
        materialization_attempt_ref=attempt,
        branch_baseline_ref="workspace-source-head:test",
        branch_baseline_digest=_digest("e"),
        branch_baseline_grade=(
            WorkspaceMaterializationSessionBaselineGrade.SOURCE_HEAD_LOCAL_OPERATIONAL.value
        ),
        package_ref=publication.head.package_ref,
        profile_digest=publication.head.profile_digest,
        source_authority_ref=publication.head.source_authority_ref,
        source_authority_digest=publication.head.source_authority_digest,
        publication_receipt_digest=publication.receipt_digest,
        expected_session_head_revision=expected_revision,
        expected_cursor=expected_cursor,
        expected_predecessor_event_digest=predecessor,
        operation_ref=_Authority.operation_ref,
        operation_digest=_Authority.operation_digest,
    )


def _admission(
    request: WorkspaceMaterializationSessionAppendRequest,
    *,
    grade: WorkspaceMaterializationSessionAuthorityGrade = (
        WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL
    ),
    permitted: tuple[str, ...] = ("aware-dev-sdk",),
) -> WorkspaceMaterializationSessionAdmission:
    return admit_workspace_materialization_session_append(
        request=request,
        operation_authority=_Authority(
            request.request_digest, grade=grade, permitted=permitted
        ),
    )


def _journal(store=None, publications=()):
    by_package = {
        publication.head.package_ref: (publication.head_revision, publication.head)
        for publication in publications
    }
    return WorkspaceMaterializationSessionJournal(
        state_store=store or InMemoryLocalOperationalStateStore(),
        package_head_resolver=by_package.get,
        replay_limit=2,
        snapshot_package_limit=2,
    )


def _content_digest(marker: str) -> ContentDigest:
    return ContentDigest.of_bytes(marker.encode("utf-8"))


def _graph_session_request(
    *,
    marker: str,
    disposition: str,
    expected_revision: int,
    expected_cursor: int,
    predecessor: ContentDigest | None,
) -> WorkspaceMaterializationSessionAppendRequestV3:
    contract = SemanticContractRef("test.result", "1", _content_digest("result-schema"))
    package = SemanticPackageCoordinate(
        "aware-dev-sdk", "sdk", _content_digest("manifest")
    )
    coordinate = SemanticValueCoordinate(
        "result",
        contract,
        f"result:{marker}",
        _content_digest(f"result:{marker}"),
        len(marker),
    )
    publication_request = WorkspaceSemanticMaterializationRequestV3.create(
        package=package,
        result_coordinate=coordinate,
        source_identity_digest=_content_digest(f"source:{marker}"),
        code_intent_digest=_content_digest(f"intent:{marker}"),
        code_match_digest=_content_digest(f"match:{marker}"),
        planning_input_digest=_content_digest(f"planning:{marker}"),
        execution_input_closure_digest=_content_digest(f"closure:{marker}"),
        operation_result_digest=_content_digest(f"operation-result:{marker}"),
        expected_head_revision=0,
    )
    publication_head = WorkspaceSemanticMaterializationHeadV3.create(
        request=publication_request
    )
    publication_receipt = WorkspaceSemanticMaterializationPublicationReceiptV3.create(
        request=publication_request,
        head=publication_head,
        prior_head_revision=0,
        head_revision=1,
        head_advanced=True,
    )
    reread = WorkspaceSemanticMaterializationHeadRereadEvidenceV3.create(
        observation_role=(
            "package_result" if disposition == "executed" else "package_reuse"
        ),
        materialization_head_revision=1,
        head=publication_head,
    )
    source = WorkspaceMaterializationSessionSourceEvidenceV3.create(
        disposition=disposition,
        head_reread_evidence=reread,
        publication_receipt=(
            publication_receipt if disposition == "executed" else None
        ),
    )
    return WorkspaceMaterializationSessionAppendRequestV3.create(
        workspace_session_ref="workspace-session:test",
        epoch="session-epoch:test",
        participant_ref="participant:test",
        actor_ref="actor:test",
        workflow_session_ref="workflow-session:test",
        materialization_attempt_ref=f"attempt:{marker}",
        branch_baseline_ref="workspace-source-head:test",
        branch_baseline_digest=_content_digest("baseline"),
        branch_baseline_grade="source_head_local_operational",
        package_ref="aware-dev-sdk",
        operation_ref=f"workspace-operation:{marker}",
        operation_digest=_content_digest(f"operation:{marker}"),
        source_evidence=source,
        expected_session_head_revision=expected_revision,
        expected_cursor=expected_cursor,
        expected_predecessor_event_digest=predecessor,
    )


def test_genesis_append_and_exact_current_retry_are_visible() -> None:
    publication = _publication()
    request = _request(publication)
    admission = _admission(request)
    journal = _journal(publications=(publication,))

    result = journal.append(admission=admission, publication=publication)
    assert result.receipt.head_advanced is True
    assert result.receipt.head_revision == 1
    assert result.metrics.event_state_cas_count == 1
    assert result.metrics.head_state_cas_count == 1
    assert result.metrics.event_state_read_count == 2
    assert result.metrics.head_state_read_count == 2
    assert result.metrics.event_wire_bytes > 2_000

    repeated = journal.append(admission=admission, publication=publication)
    assert repeated.receipt.head_advanced is False
    assert repeated.receipt.head_revision == 1
    assert repeated.metrics.event_state_cas_count == 0
    assert repeated.metrics.event_state_reuse_count == 1
    assert repeated.metrics.head_state_cas_count == 0

    replay = journal.replay(
        admission=admission,
        requested_epoch=request.epoch,
        after_cursor=0,
        package_refs=(request.package_ref,),
    )
    assert replay.gap is None
    assert replay.events == (result.event,)
    assert replay.snapshot.current_cursor == 1
    assert replay.snapshot.package_heads[0].head_digest == publication.head.head_digest
    assert replay.metrics.event_state_read_count == 1
    assert replay.metrics.package_head_read_count == 1


def test_successor_chain_and_gap_results_are_exact() -> None:
    first_publication = _publication("a", revision=1)
    second_publication = _publication("f", revision=2)
    third_publication = _publication("0", revision=3)
    journal = _journal(publications=(third_publication,))

    first_request = _request(first_publication)
    first_admission = _admission(first_request)
    first = journal.append(admission=first_admission, publication=first_publication)
    second_request = _request(
        second_publication,
        expected_revision=1,
        expected_cursor=1,
        predecessor=first.event.event_digest,
        attempt="attempt:two",
    )
    second_admission = _admission(second_request)
    second = journal.append(admission=second_admission, publication=second_publication)
    third_request = _request(
        third_publication,
        expected_revision=2,
        expected_cursor=2,
        predecessor=second.event.event_digest,
        attempt="attempt:three",
    )
    third_admission = _admission(third_request)
    third = journal.append(admission=third_admission, publication=third_publication)

    contiguous = journal.replay(
        admission=third_admission,
        requested_epoch=third_request.epoch,
        after_cursor=1,
        package_refs=(third_request.package_ref,),
    )
    assert [event.cursor for event in contiguous.events] == [2, 3]
    assert contiguous.gap is None

    retained = journal.replay(
        admission=third_admission,
        requested_epoch=third_request.epoch,
        after_cursor=0,
        package_refs=(),
    )
    assert retained.events == ()
    assert retained.gap is not None
    assert (
        retained.gap.reason
        is WorkspaceMaterializationSessionGapReason.RETENTION_EXCEEDED
    )

    ahead = journal.replay(
        admission=third_admission,
        requested_epoch=third_request.epoch,
        after_cursor=4,
        package_refs=(),
    )
    assert ahead.gap is not None
    assert ahead.gap.reason is WorkspaceMaterializationSessionGapReason.CURSOR_AHEAD

    epoch = journal.replay(
        admission=third_admission,
        requested_epoch="session-epoch:foreign",
        after_cursor=3,
        package_refs=(),
    )
    assert epoch.gap is not None
    assert epoch.gap.reason is WorkspaceMaterializationSessionGapReason.EPOCH_MISMATCH
    assert third.head.cursor == 3


class _FailHeadOnceStore:
    def __init__(self) -> None:
        self.inner = InMemoryLocalOperationalStateStore()
        self.failed = False

    def read(self, namespace, key, *, include_deleted=False):
        return self.inner.read(namespace, key, include_deleted=include_deleted)

    def compare_and_set(self, namespace, key, **kwargs):
        if (
            namespace == WORKSPACE_MATERIALIZATION_SESSION_HEAD_NAMESPACE
            and not self.failed
        ):
            self.failed = True
            raise LocalOperationalStateConflict("injected head loss")
        return self.inner.compare_and_set(namespace, key, **kwargs)

    def delete(self, namespace, key, **kwargs):
        return self.inner.delete(namespace, key, **kwargs)


def test_interrupted_head_cas_reuses_exact_staged_event() -> None:
    publication = _publication()
    request = _request(publication)
    admission = _admission(request)
    store = _FailHeadOnceStore()
    journal = _journal(store=store, publications=(publication,))

    with pytest.raises(WorkspaceMaterializationSessionConflict, match="head CAS lost"):
        journal.append(admission=admission, publication=publication)
    assert (
        store.inner.read(
            WORKSPACE_MATERIALIZATION_SESSION_HEAD_NAMESPACE,
            request.workspace_session_ref,
        )
        is None
    )
    assert (
        store.inner.read(
            WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE,
            WorkspaceMaterializationSessionEvent.create(
                admission=admission, publication=publication
            ).event_digest,
        )
        is not None
    )

    recovered = journal.append(admission=admission, publication=publication)
    assert recovered.metrics.event_state_reuse_count == 1
    assert recovered.metrics.head_state_cas_count == 1
    assert recovered.receipt.head_advanced is True


def test_authority_publication_and_state_substitutions_fail_closed() -> None:
    publication = _publication()
    request = _request(publication)
    admission = _admission(request)
    journal = _journal(publications=(publication,))

    forged = object.__new__(WorkspaceMaterializationSessionAdmission)
    with pytest.raises(WorkspaceMaterializationSessionError, match="not registered"):
        journal.append(admission=forged, publication=publication)

    substituted = _publication()
    object.__setattr__(substituted, "receipt_digest", _digest("f"))
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="receipt digest mismatched",
    ):
        journal.append(admission=admission, publication=substituted)

    shared = _admission(
        request,
        grade=WorkspaceMaterializationSessionAuthorityGrade.WORKSPACE_AUTHORIZED_SHARED,
    )
    local = journal.append(admission=admission, publication=publication)
    with pytest.raises(WorkspaceMaterializationSessionConflict):
        journal.append(admission=shared, publication=publication)
    assert local.event.authority_grade == "local_operational"

    with pytest.raises(WorkspaceMaterializationSessionError, match="not admitted"):
        journal.replay(
            admission=admission,
            requested_epoch=request.epoch,
            after_cursor=1,
            package_refs=("foreign-package",),
        )


def test_stale_revision_cursor_and_predecessor_conflicts_are_distinct() -> None:
    first_publication = _publication("a", revision=1)
    second_publication = _publication("b", revision=2)
    journal = _journal(publications=(second_publication,))
    first_request = _request(first_publication)
    first = journal.append(
        admission=_admission(first_request), publication=first_publication
    )

    stale_revision = _request(second_publication, attempt="attempt:stale-revision")
    with pytest.raises(
        WorkspaceMaterializationSessionConflict,
        match="head revision is stale",
    ):
        journal.append(
            admission=_admission(stale_revision), publication=second_publication
        )

    stale_cursor = _request(
        second_publication,
        expected_revision=1,
        expected_cursor=2,
        predecessor=first.event.event_digest,
        attempt="attempt:stale-cursor",
    )
    with pytest.raises(
        WorkspaceMaterializationSessionConflict,
        match="cursor or predecessor differs",
    ):
        journal.append(
            admission=_admission(stale_cursor), publication=second_publication
        )

    stale_predecessor = _request(
        second_publication,
        expected_revision=1,
        expected_cursor=1,
        predecessor=_digest("f"),
        attempt="attempt:stale-predecessor",
    )
    with pytest.raises(
        WorkspaceMaterializationSessionConflict,
        match="cursor or predecessor differs",
    ):
        journal.append(
            admission=_admission(stale_predecessor), publication=second_publication
        )


def test_request_admission_and_event_construction_poisons_fail_before_effects() -> None:
    publication = _publication()

    class _ForeignRequest(WorkspaceMaterializationSessionAppendRequest):
        pass

    request = _request(publication)
    foreign = _ForeignRequest(
        **{field: getattr(request, field) for field in request.__dataclass_fields__}
    )
    with pytest.raises(TypeError, match="exact session append request"):
        admit_workspace_materialization_session_append(
            request=foreign,
            operation_authority=_Authority(foreign.request_digest),
        )

    forged = object.__new__(WorkspaceMaterializationSessionAdmission)
    with pytest.raises(WorkspaceMaterializationSessionError, match="not registered"):
        forged._assert_intact()
    with pytest.raises(TypeError, match="not serializable"):
        copy.copy(_admission(request))

    for field, poison in (
        ("participant_ref", "participant:foreign"),
        ("actor_ref", "actor:foreign"),
        ("workflow_session_ref", "workflow-session:foreign"),
        ("materialization_attempt_ref", "attempt:foreign"),
        ("package_ref", "foreign-package"),
        ("profile_digest", _digest("f")),
        ("source_authority_ref", "workspace-source:foreign"),
        ("source_authority_digest", _digest("f")),
    ):
        candidate = _request(publication)
        admission = _admission(candidate)
        object.__setattr__(candidate, field, poison)
        with pytest.raises(
            WorkspaceMaterializationSessionError,
            match="append request digest mismatched",
        ):
            _journal(publications=(publication,)).append(
                admission=admission, publication=publication
            )

    admission = _admission(request)
    event = WorkspaceMaterializationSessionEvent.create(
        admission=admission, publication=publication
    )
    object.__setattr__(event, "actor_ref", "actor:foreign")
    with pytest.raises(
        WorkspaceMaterializationSessionError,
        match="session event digest mismatched",
    ):
        event.to_json_bytes()


def test_event_stage_collision_and_wire_substitution_fail_closed() -> None:
    publication = _publication()
    request = _request(publication)
    admission = _admission(request)
    event = WorkspaceMaterializationSessionEvent.create(
        admission=admission, publication=publication
    )
    store = InMemoryLocalOperationalStateStore()
    substituted_wire = canonical_json_bytes({"substituted": True})
    store.compare_and_set(
        WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE,
        event.event_digest,
        expected_revision=0,
        value={
            "wire": substituted_wire.decode("utf-8"),
            "wire_digest": ContentDigest.of_bytes(substituted_wire).value,
        },
    )
    journal = _journal(store=store, publications=(publication,))
    with pytest.raises(
        WorkspaceMaterializationSessionConflict,
        match="digest collided with different wire",
    ):
        journal.append(admission=admission, publication=publication)
    assert journal.read_head(request.workspace_session_ref) is None


def test_snapshot_page_is_bounded_ordered_and_directly_counted() -> None:
    first = _publication("a", package_ref="aware-api", revision=1)
    second = _publication("b", package_ref="aware-dev-sdk", revision=1)
    request = _request(second)
    admission = _admission(
        request,
        permitted=("aware-api", "aware-dev-sdk", "aware-ontology"),
    )
    journal = _journal(publications=(first, second))
    appended = journal.append(admission=admission, publication=second)
    replay = journal.replay(
        admission=admission,
        requested_epoch=request.epoch,
        after_cursor=appended.event.cursor,
        package_refs=("aware-api", "aware-dev-sdk"),
    )
    assert tuple(item.package_ref for item in replay.snapshot.package_heads) == (
        "aware-api",
        "aware-dev-sdk",
    )
    assert replay.metrics.package_head_read_count == 2
    assert replay.metrics.requested_package_count == 2
    assert replay.metrics.event_state_read_count == 0

    with pytest.raises(
        WorkspaceMaterializationSessionError,
        match="not canonical",
    ):
        journal.replay(
            admission=admission,
            requested_epoch=request.epoch,
            after_cursor=1,
            package_refs=("aware-dev-sdk", "aware-api"),
        )
    with pytest.raises(
        WorkspaceMaterializationSessionError,
        match="exceeds limit",
    ):
        journal.replay(
            admission=admission,
            requested_epoch=request.epoch,
            after_cursor=1,
            package_refs=("aware-api", "aware-dev-sdk", "aware-ontology"),
        )


def test_request_and_event_codecs_reject_boolean_integer_substitution() -> None:
    publication = _publication()
    request = _request(publication)
    assert (
        WorkspaceMaterializationSessionAppendRequest.from_json_bytes(
            request.to_json_bytes()
        )
        == request
    )
    payload = json.loads(request.to_json_bytes())
    payload["expected_cursor"] = True
    with pytest.raises(WorkspaceMaterializationSessionError, match="integer type"):
        WorkspaceMaterializationSessionAppendRequest.from_json_bytes(
            canonical_json_bytes(payload)
        )

    admission = _admission(request)
    event = WorkspaceMaterializationSessionEvent.create(
        admission=admission, publication=publication
    )
    assert (
        WorkspaceMaterializationSessionEvent.from_json_bytes(event.to_json_bytes())
        == event
    )
    event_payload = json.loads(event.to_json_bytes())
    event_payload["cursor"] = True
    with pytest.raises(WorkspaceMaterializationSessionError, match="integer type"):
        WorkspaceMaterializationSessionEvent.from_json_bytes(
            canonical_json_bytes(event_payload)
        )


def test_sqlite_restart_and_real_envelope_performance(tmp_path: Path) -> None:
    sqlite = pytest.importorskip("aware_local_service_state_sqlite")
    publication = _publication()
    request = _request(publication)
    admission = _admission(request)
    database = tmp_path / "session.sqlite3"
    first = _journal(
        store=sqlite.SqliteLocalOperationalStateStore(database),
        publications=(publication,),
    )
    result = first.append(admission=admission, publication=publication)
    reconstructed = _journal(
        store=sqlite.SqliteLocalOperationalStateStore(database),
        publications=(publication,),
    )
    replay = reconstructed.replay(
        admission=admission,
        requested_epoch=request.epoch,
        after_cursor=0,
        package_refs=(request.package_ref,),
    )
    assert replay.events == (result.event,)

    append_ms: list[float] = []
    replay_ms: list[float] = []
    for index in range(30):
        with tempfile.TemporaryDirectory(
            prefix="aware-session-performance-"
        ) as location:
            store = sqlite.SqliteLocalOperationalStateStore(
                Path(location) / "state.sqlite3"
            )
            sample = _journal(store=store, publications=(publication,))
            started = time.perf_counter_ns()
            appended = sample.append(admission=admission, publication=publication)
            append_ms.append((time.perf_counter_ns() - started) / 1_000_000)
            replay_started = time.perf_counter_ns()
            observed = sample.replay(
                admission=admission,
                requested_epoch=request.epoch,
                after_cursor=0,
                package_refs=(request.package_ref,),
            )
            replay_ms.append((time.perf_counter_ns() - replay_started) / 1_000_000)
            assert observed.events == (appended.event,)
            assert appended.metrics.event_state_cas_count == 1
            assert appended.metrics.head_state_cas_count == 1
    append_sorted = sorted(append_ms)
    replay_sorted = sorted(replay_ms)
    assert statistics.median(append_ms) < 10.0
    assert append_sorted[int(0.95 * 29)] < 25.0
    assert statistics.median(replay_ms) < 5.0
    assert replay_sorted[int(0.95 * 29)] < 5.0


def test_dormant_graph_v2_append_retry_restart_and_replay() -> None:
    store = InMemoryLocalOperationalStateStore()
    journal = _journal(store=store)
    first_request = _graph_session_request(
        marker="one",
        disposition="executed",
        expected_revision=0,
        expected_cursor=0,
        predecessor=None,
    )
    first = journal._append_graph_v2(request=first_request)
    retry = journal._append_graph_v2(request=first_request)
    assert retry.receipt == first.receipt
    assert retry.metrics.head_state_cas_count == 0
    assert retry.metrics.event_state_reuse_count == 1

    second_request = _graph_session_request(
        marker="two",
        disposition="reused",
        expected_revision=1,
        expected_cursor=1,
        predecessor=first.event.event_digest,
    )
    second = journal._append_graph_v2(request=second_request)
    assert second.receipt.head_revision == 2
    assert second.event.disposition == "reused"
    assert second.event.publication_receipt_digest is None

    reconstructed = _journal(store=store)
    replay = reconstructed._replay_graph_v2_events(
        workspace_session_ref="workspace-session:test",
        epoch="session-epoch:test",
        after_cursor=0,
    )
    assert replay == (first.event, second.event)
    assert all(
        type(event) is WorkspaceMaterializationSessionEventV3 for event in replay
    )


def test_graph_v2_succeeds_v1_and_v1_after_v2_fails_before_event_stage() -> None:
    first_publication = _publication("a", revision=1)
    later_publication = _publication("b", revision=2)
    store = InMemoryLocalOperationalStateStore()
    journal = _journal(store=store, publications=(first_publication, later_publication))
    first_request = _request(first_publication)
    first = journal.append(
        admission=_admission(first_request), publication=first_publication
    )
    graph_request = _graph_session_request(
        marker="graph",
        disposition="executed",
        expected_revision=1,
        expected_cursor=1,
        predecessor=ContentDigest(first.event.event_digest),
    )
    graph = journal._append_graph_v2(request=graph_request)
    replay = journal._replay_graph_v2_events(
        workspace_session_ref="workspace-session:test",
        epoch="session-epoch:test",
        after_cursor=0,
    )
    assert replay == (first.event, graph.event)
    assert type(replay[0]) is WorkspaceMaterializationSessionEvent
    assert type(replay[1]) is WorkspaceMaterializationSessionEventV3

    downgrade_request = _request(
        later_publication,
        expected_revision=2,
        expected_cursor=2,
        predecessor=graph.event.event_digest.value,
        attempt="attempt:downgrade",
    )
    downgrade_admission = _admission(downgrade_request)
    downgrade_event = WorkspaceMaterializationSessionEvent.create(
        admission=downgrade_admission, publication=later_publication
    )
    with pytest.raises(
        WorkspaceMaterializationSessionError,
        match="wire fields differ",
    ):
        journal.append(admission=downgrade_admission, publication=later_publication)
    assert (
        store.read(
            WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE,
            downgrade_event.event_digest,
        )
        is None
    )


def test_graph_v2_event_context_poison_fails_after_restart() -> None:
    store = InMemoryLocalOperationalStateStore()
    journal = _journal(store=store)
    request = _graph_session_request(
        marker="poison",
        disposition="executed",
        expected_revision=0,
        expected_cursor=0,
        predecessor=None,
    )
    result = journal._append_graph_v2(request=request)
    record = store.read(
        WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE,
        result.event.event_digest.value,
    )
    assert record is not None and record.value is not None
    poisoned = json.loads(json.dumps(record.value))
    context = poisoned["context"]
    assert type(context) is dict
    source = context["source_evidence"]
    assert type(source) is dict
    source["disposition"] = "reused"
    store.compare_and_set(
        WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE,
        result.event.event_digest.value,
        expected_revision=1,
        value=poisoned,
    )
    with pytest.raises(WorkspaceMaterializationSessionError):
        _journal(store=store)._replay_graph_v2_events(
            workspace_session_ref="workspace-session:test",
            epoch="session-epoch:test",
            after_cursor=0,
        )


def test_graph_v2_in_memory_append_visibility_gate() -> None:
    journal = _journal()
    predecessor: ContentDigest | None = None
    samples: list[int] = []
    for index in range(100):
        request = _graph_session_request(
            marker=f"performance-{index}",
            disposition="reused",
            expected_revision=index,
            expected_cursor=index,
            predecessor=predecessor,
        )
        started = time.perf_counter_ns()
        result = journal._append_graph_v2(request=request)
        samples.append(time.perf_counter_ns() - started)
        predecessor = result.event.event_digest
        assert result.metrics.event_state_read_count == 2
        assert result.metrics.head_state_read_count == 2
    # C2 records the complete strict persistence cost. The C3 coordinator gate
    # separately excludes durable journal latency and remains <100 ms/100 nodes.
    assert statistics.median(samples) < 250_000_000
    assert max(samples) < 500_000_000


def test_graph_v2_sqlite_restart_replays_mixed_history(tmp_path: Path) -> None:
    sqlite = pytest.importorskip("aware_local_service_state_sqlite")
    first_publication = _publication("a", revision=1)
    database = tmp_path / "graph-v2-session.sqlite3"
    first = _journal(
        store=sqlite.SqliteLocalOperationalStateStore(database),
        publications=(first_publication,),
    )
    v1_request = _request(first_publication)
    v1 = first.append(admission=_admission(v1_request), publication=first_publication)
    v2_request = _graph_session_request(
        marker="sqlite",
        disposition="executed",
        expected_revision=1,
        expected_cursor=1,
        predecessor=ContentDigest(v1.event.event_digest),
    )
    v2 = first._append_graph_v2(request=v2_request)
    reconstructed = _journal(
        store=sqlite.SqliteLocalOperationalStateStore(database),
        publications=(first_publication,),
    )
    assert reconstructed._replay_graph_v2_events(
        workspace_session_ref="workspace-session:test",
        epoch="session-epoch:test",
        after_cursor=0,
    ) == (v1.event, v2.event)


@pytest.mark.parametrize("field", ("source_evidence", "append_request", "head_reread_evidence", "publication_receipt"))
def test_v3_session_rejects_v2_nested_contract_after_restart(field: str) -> None:
    store = InMemoryLocalOperationalStateStore()
    result = _journal(store=store)._append_graph_v2(request=_graph_session_request(
        marker="versions", disposition="executed", expected_revision=0,
        expected_cursor=0, predecessor=None,
    ))
    record = store.read(WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE, result.event.event_digest.value)
    assert record is not None and record.value is not None
    value = json.loads(json.dumps(record.value))
    original = value["context"][field]["contract"]
    assert original.endswith(".v3")
    value["context"][field]["contract"] = original[:-1] + "2"
    store.compare_and_set(WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE,
        result.event.event_digest.value, expected_revision=record.revision, value=value)
    with pytest.raises((WorkspaceMaterializationSessionError, WorkspaceSemanticMaterializationPublicationError)):
        _journal(store=store)._replay_graph_v2_events(
            workspace_session_ref="workspace-session:test", epoch="session-epoch:test", after_cursor=0)
    assert store.read(WORKSPACE_MATERIALIZATION_SESSION_EVENT_NAMESPACE,
        result.event.event_digest.value).revision == record.revision + 1
