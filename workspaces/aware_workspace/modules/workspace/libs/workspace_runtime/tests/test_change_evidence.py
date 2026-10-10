from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest
from aware_workspace_runtime import (
    RepositoryBodyAvailability,
    RepositoryChangedEntryKind,
    RepositoryDiffBinaryPolicy,
    RepositoryDiffLineKind,
    RepositoryDiffPageState,
    RepositoryEvidenceCoordinateKind,
    RepositoryEvidencePosture,
    RepositoryEvidenceResolutionState,
    RepositoryMutationKind,
    RepositoryMutationOutcome,
    RepositoryObservationCoordinate,
    RepositoryReportedChangeKind,
    WorkspaceRepositoryChangedEntry,
    WorkspaceRepositoryChangeEvidence,
    WorkspaceRepositoryDiffFile,
    WorkspaceRepositoryDiffHunk,
    WorkspaceRepositoryDiffLine,
    WorkspaceRepositoryDiffPage,
    WorkspaceRepositoryDiffRequest,
    WorkspaceRepositoryEvidenceCheckpoint,
    WorkspaceRepositoryEvidenceCoordinate,
    WorkspaceRepositoryExternalEvidenceRef,
    WorkspaceRepositoryMutationReceipt,
    WorkspaceRepositoryReportedChange,
    repository_change_evidence_ref,
    repository_changed_entry_ref,
    repository_diff_continuation_ref,
    repository_diff_file_ref,
    repository_diff_hunk_ref,
    repository_diff_ref,
    repository_diff_request_ref,
    repository_mutation_receipt_ref,
    validate_repository_change_evidence_advance,
)

BINDING = "workspace-binding:aware"
NOW = datetime(2026, 8, 22, 4, 20, tzinfo=UTC)


def _observation(cursor: int) -> WorkspaceRepositoryEvidenceCoordinate:
    digest = f"snapshot-{cursor}"
    value = RepositoryObservationCoordinate(
        repository_binding_ref=BINDING,
        epoch="observer-epoch-1",
        cursor=cursor,
        snapshot_digest=digest,
        visibility_policy_ref="workspace-source-visibility",
        visibility_policy_version="1",
    )
    return WorkspaceRepositoryEvidenceCoordinate(
        kind=RepositoryEvidenceCoordinateKind.OBSERVATION,
        repository_binding_ref=BINDING,
        state_digest=digest,
        observation=value,
    )


def _revision(name: str) -> WorkspaceRepositoryEvidenceCoordinate:
    return WorkspaceRepositoryEvidenceCoordinate(
        kind=RepositoryEvidenceCoordinateKind.COMMITTED_REVISION,
        repository_binding_ref=BINDING,
        state_digest=f"tree-{name}",
        revision_ref=f"revision:{name}",
    )


def _entry(
    before: WorkspaceRepositoryEvidenceCoordinate,
    after: WorkspaceRepositoryEvidenceCoordinate,
    *,
    posture: RepositoryEvidencePosture,
    kind: RepositoryChangedEntryKind = RepositoryChangedEntryKind.UPDATE,
    old_path: str | None = "src/main.py",
    new_path: str | None = "src/main.py",
    reason: str | None = None,
) -> WorkspaceRepositoryChangedEntry:
    return WorkspaceRepositoryChangedEntry(
        changed_entry_ref=repository_changed_entry_ref(
            repository_binding_ref=BINDING,
            before_coordinate=before,
            after_coordinate=after,
            kind=kind,
            old_path=old_path,
            new_path=new_path,
        ),
        kind=kind,
        posture=posture,
        before_coordinate=before,
        after_coordinate=after,
        old_path=old_path,
        new_path=new_path,
        old_entry_ref=None if old_path is None else "entry:old",
        new_entry_ref=None if new_path is None else "entry:new",
        old_content_digest=None if old_path is None else "content:old",
        new_content_digest=None if new_path is None else "content:new",
        old_size_bytes=None if old_path is None else 10,
        new_size_bytes=None if new_path is None else 12,
        old_body_availability=(
            RepositoryBodyAvailability.UNAVAILABLE
            if old_path is None
            else RepositoryBodyAvailability.AVAILABLE
        ),
        new_body_availability=(
            RepositoryBodyAvailability.UNAVAILABLE
            if new_path is None
            else RepositoryBodyAvailability.AVAILABLE
        ),
        reason=reason,
    )


def _external() -> WorkspaceRepositoryExternalEvidenceRef:
    return WorkspaceRepositoryExternalEvidenceRef(
        evidence_ref="codex:item:file-change:7",
        source_namespace="codex.app-server",
        source_contract_version="2026-08-22",
        observed_at=NOW,
        changes=(
            WorkspaceRepositoryReportedChange(
                path="src/main.py", kind=RepositoryReportedChangeKind.UPDATE
            ),
        ),
        context_refs=("agent-session:1", "issue:42"),
        complete=True,
    )


def _evidence(
    posture: RepositoryEvidencePosture,
) -> WorkspaceRepositoryChangeEvidence:
    before: WorkspaceRepositoryEvidenceCoordinate | None = _observation(4)
    after: WorkspaceRepositoryEvidenceCoordinate | None = _observation(5)
    external_refs: tuple[str, ...] = ()
    mutation_refs: tuple[str, ...] = ()
    revision_refs: tuple[str, ...] = ()
    reason: str | None = None
    if posture is RepositoryEvidencePosture.PROVIDER_REPORTED:
        before = after = None
        external_refs = (_external().evidence_ref,)
    elif posture is RepositoryEvidencePosture.PROVIDER_CORRELATED:
        external_refs = (_external().evidence_ref,)
    elif posture is RepositoryEvidencePosture.WORKSPACE_AUTHORIZED:
        mutation_refs = ("workspace-repository-mutation-receipt:sha256:receipt",)
    elif posture is RepositoryEvidencePosture.COMMITTED_REVISION:
        before, after = _revision("before"), _revision("after")
        revision_refs = ("revision:after",)
    elif posture is RepositoryEvidencePosture.AMBIGUOUS:
        external_refs = (_external().evidence_ref,)
        reason = "two observation batches overlap the provider interval"
    elif posture is RepositoryEvidencePosture.GAP:
        before = after = None
        external_refs = (_external().evidence_ref,)
        reason = "observer replay retention was exceeded"
    entries = (
        ()
        if before is None or after is None
        else (
            _entry(
                before,
                after,
                posture=posture,
                reason=reason
                if posture is RepositoryEvidencePosture.AMBIGUOUS
                else None,
            ),
        )
    )
    expected_state = {
        RepositoryEvidencePosture.PROVIDER_REPORTED: RepositoryEvidenceResolutionState.REPORTED,
        RepositoryEvidencePosture.AMBIGUOUS: RepositoryEvidenceResolutionState.AMBIGUOUS,
        RepositoryEvidencePosture.GAP: RepositoryEvidenceResolutionState.GAP,
    }.get(posture, RepositoryEvidenceResolutionState.RESOLVED)
    return WorkspaceRepositoryChangeEvidence(
        evidence_ref=repository_change_evidence_ref(
            repository_binding_ref=BINDING, evidence_key="provider-item-7"
        ),
        evidence_key="provider-item-7",
        revision=0,
        repository_binding_ref=BINDING,
        posture=posture,
        resolution_state=expected_state,
        observed_at=NOW,
        before_coordinate=before,
        after_coordinate=after,
        changed_entries=entries,
        external_evidence_refs=external_refs,
        mutation_receipt_refs=mutation_refs,
        committed_revision_refs=revision_refs,
        reason=reason,
    )


@pytest.mark.parametrize("posture", list(RepositoryEvidencePosture))
def test_all_evidence_postures_have_honest_provenance(
    posture: RepositoryEvidencePosture,
) -> None:
    value = _evidence(posture)
    assert value.posture is posture


def test_provider_evidence_is_opaque_bounded_and_never_authorized() -> None:
    value = _external()
    assert value.posture is RepositoryEvidencePosture.PROVIDER_REPORTED
    assert value.context_refs == ("agent-session:1", "issue:42")
    with pytest.raises(ValueError, match="provider_reported"):
        WorkspaceRepositoryExternalEvidenceRef(
            **{
                **{
                    field: getattr(value, field) for field in value.__dataclass_fields__
                },
                "posture": RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
            }
        )


@pytest.mark.parametrize(
    ("kind", "old_path", "new_path"),
    [
        (RepositoryChangedEntryKind.CREATE, None, "new.txt"),
        (RepositoryChangedEntryKind.UPDATE, "same.txt", "same.txt"),
        (RepositoryChangedEntryKind.DELETE, "old.txt", None),
        (RepositoryChangedEntryKind.RENAME, "old.txt", "new.txt"),
        (RepositoryChangedEntryKind.BINARY, "image.png", "image.png"),
    ],
)
def test_changed_entry_shapes_are_explicit(
    kind: RepositoryChangedEntryKind,
    old_path: str | None,
    new_path: str | None,
) -> None:
    value = _entry(
        _observation(1),
        _observation(2),
        posture=RepositoryEvidencePosture.WORKSPACE_OBSERVED,
        kind=kind,
        old_path=old_path,
        new_path=new_path,
    )
    assert value.kind is kind


def test_rename_requires_distinct_paths_and_deterministic_ref() -> None:
    before, after = _observation(1), _observation(2)
    with pytest.raises(ValueError, match="distinct"):
        _entry(
            before,
            after,
            posture=RepositoryEvidencePosture.WORKSPACE_OBSERVED,
            kind=RepositoryChangedEntryKind.RENAME,
            old_path="same.txt",
            new_path="same.txt",
        )
    valid = _entry(
        before,
        after,
        posture=RepositoryEvidencePosture.WORKSPACE_OBSERVED,
    )
    with pytest.raises(ValueError, match="deterministic"):
        WorkspaceRepositoryChangedEntry(
            **{
                **{
                    field: getattr(valid, field) for field in valid.__dataclass_fields__
                },
                "changed_entry_ref": "tampered",
            }
        )


def test_provider_correlation_cannot_claim_authorization() -> None:
    correlated = _evidence(RepositoryEvidencePosture.PROVIDER_CORRELATED)
    with pytest.raises(ValueError, match="mutation receipt"):
        WorkspaceRepositoryChangeEvidence(
            **{
                **{
                    field: getattr(correlated, field)
                    for field in correlated.__dataclass_fields__
                },
                "posture": RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
                "resolution_state": RepositoryEvidenceResolutionState.RESOLVED,
                "changed_entries": tuple(
                    _entry(
                        item.before_coordinate,
                        item.after_coordinate,
                        posture=RepositoryEvidencePosture.WORKSPACE_AUTHORIZED,
                    )
                    for item in correlated.changed_entries
                ),
            }
        )


def test_evidence_advance_is_monotonic_and_retains_provenance() -> None:
    reported = _evidence(RepositoryEvidencePosture.PROVIDER_REPORTED)
    correlated = replace(
        _evidence(RepositoryEvidencePosture.PROVIDER_CORRELATED),
        revision=1,
        resolved_at=NOW,
    )
    validate_repository_change_evidence_advance(reported, correlated)

    downgraded = replace(reported, revision=2)
    with pytest.raises(ValueError, match="downgrade"):
        validate_repository_change_evidence_advance(correlated, downgraded)

    skipped = replace(correlated, revision=3)
    with pytest.raises(ValueError, match="exactly one"):
        validate_repository_change_evidence_advance(reported, skipped)

    authorized = replace(
        _evidence(RepositoryEvidencePosture.WORKSPACE_AUTHORIZED),
        external_evidence_refs=(_external().evidence_ref,),
    )
    committed_without_external = replace(
        _evidence(RepositoryEvidencePosture.COMMITTED_REVISION),
        revision=1,
        mutation_receipt_refs=authorized.mutation_receipt_refs,
    )
    with pytest.raises(ValueError, match="erase provenance"):
        validate_repository_change_evidence_advance(
            authorized, committed_without_external
        )


def test_mutation_receipt_enforces_cas_and_result_posture() -> None:
    expected, result = _observation(9), _observation(10)
    receipt_ref = repository_mutation_receipt_ref(
        repository_binding_ref=BINDING,
        operation_ref="operation:1",
        idempotency_key="request:1",
    )
    applied = WorkspaceRepositoryMutationReceipt(
        mutation_receipt_ref=receipt_ref,
        repository_binding_ref=BINDING,
        operation_ref="operation:1",
        idempotency_key="request:1",
        mutation_kind=RepositoryMutationKind.UPDATE,
        expected_coordinate=expected,
        target_path="src/main.py",
        expected_exists=True,
        expected_content_digest="content:old",
        outcome=RepositoryMutationOutcome.APPLIED,
        context_refs=("agent-session:1",),
        result_coordinate=result,
        result_entry_ref="entry:new",
        result_content_digest="content:new",
        result_size_bytes=12,
        request_body_evidence_ref="body:request",
        result_body_evidence_ref="body:result",
        delta_evidence_ref="delta:1",
    )
    assert applied.outcome is RepositoryMutationOutcome.APPLIED
    with pytest.raises(ValueError, match="requires error_code"):
        WorkspaceRepositoryMutationReceipt(
            **{
                **{
                    field: getattr(applied, field)
                    for field in applied.__dataclass_fields__
                },
                "outcome": RepositoryMutationOutcome.CONFLICT,
                "result_coordinate": None,
                "result_entry_ref": None,
                "result_content_digest": None,
                "result_size_bytes": None,
                "result_body_evidence_ref": None,
                "delta_evidence_ref": None,
            }
        )


def _diff_values() -> tuple[
    WorkspaceRepositoryDiffRequest, WorkspaceRepositoryDiffPage
]:
    evidence = _evidence(RepositoryEvidencePosture.WORKSPACE_OBSERVED)
    assert evidence.before_coordinate is not None
    assert evidence.after_coordinate is not None
    diff_ref = repository_diff_ref(
        repository_binding_ref=BINDING,
        evidence_ref=evidence.evidence_ref,
        baseline=evidence.before_coordinate,
        target=evidence.after_coordinate,
    )
    file_ref = repository_diff_file_ref(
        diff_ref=diff_ref,
        kind=RepositoryChangedEntryKind.UPDATE,
        old_path="src/main.py",
        new_path="src/main.py",
    )
    hunk_ref = repository_diff_hunk_ref(
        file_ref=file_ref,
        hunk_index=0,
        old_start=1,
        old_count=2,
        new_start=1,
        new_count=2,
    )
    hunk = WorkspaceRepositoryDiffHunk(
        hunk_ref=hunk_ref,
        hunk_index=0,
        old_start=1,
        old_count=2,
        new_start=1,
        new_count=2,
        lines=(
            WorkspaceRepositoryDiffLine(
                kind=RepositoryDiffLineKind.CONTEXT,
                text="same",
                old_line_number=1,
                new_line_number=1,
            ),
            WorkspaceRepositoryDiffLine(
                kind=RepositoryDiffLineKind.DELETION,
                text="old",
                old_line_number=2,
            ),
            WorkspaceRepositoryDiffLine(
                kind=RepositoryDiffLineKind.ADDITION,
                text="new",
                new_line_number=2,
            ),
        ),
    )
    file = WorkspaceRepositoryDiffFile(
        file_ref=file_ref,
        kind=RepositoryChangedEntryKind.UPDATE,
        old_path="src/main.py",
        new_path="src/main.py",
        old_content_digest="content:old",
        new_content_digest="content:new",
        binary=False,
        hunks=(hunk,),
        changed_entry_ref=evidence.changed_entries[0].changed_entry_ref,
    )
    request = WorkspaceRepositoryDiffRequest(
        request_ref=repository_diff_request_ref(
            evidence_ref=evidence.evidence_ref,
            repository_binding_ref=BINDING,
            baseline=evidence.before_coordinate,
            target=evidence.after_coordinate,
            changed_entry_ref=None,
            continuation_ref=None,
            maximum_files=20,
            maximum_lines=2000,
            maximum_bytes=100_000,
            context_lines=3,
            binary_policy=RepositoryDiffBinaryPolicy.METADATA_ONLY,
        ),
        evidence_ref=evidence.evidence_ref,
        repository_binding_ref=BINDING,
        baseline=evidence.before_coordinate,
        target=evidence.after_coordinate,
        maximum_files=20,
        maximum_lines=2000,
        maximum_bytes=100_000,
    )
    page = WorkspaceRepositoryDiffPage(
        diff_ref=diff_ref,
        evidence_ref=evidence.evidence_ref,
        repository_binding_ref=BINDING,
        posture=RepositoryEvidencePosture.WORKSPACE_OBSERVED,
        state=RepositoryDiffPageState.AVAILABLE,
        baseline=evidence.before_coordinate,
        target=evidence.after_coordinate,
        files=(file,),
        returned_file_count=1,
        total_file_count=1,
        complete=True,
    )
    return request, page


def test_diff_values_require_exact_coordinates_ranges_budgets_and_refs() -> None:
    request, page = _diff_values()
    assert request.maximum_files == 20
    assert page.files[0].hunks[0].old_count == 2
    with pytest.raises(ValueError, match="line counts"):
        WorkspaceRepositoryDiffHunk(
            **{
                **{
                    field: getattr(page.files[0].hunks[0], field)
                    for field in page.files[0].hunks[0].__dataclass_fields__
                },
                "old_count": 7,
            }
        )
    with pytest.raises(ValueError, match="positive and bounded"):
        WorkspaceRepositoryDiffRequest(
            **{
                **{
                    field: getattr(request, field)
                    for field in request.__dataclass_fields__
                },
                "maximum_files": 0,
            }
        )
    with pytest.raises(ValueError, match="not authoritative enough"):
        WorkspaceRepositoryDiffPage(
            **{
                **{field: getattr(page, field) for field in page.__dataclass_fields__},
                "posture": RepositoryEvidencePosture.PROVIDER_REPORTED,
            }
        )


def test_diff_continuation_and_checkpoint_are_stable_immutable_values() -> None:
    _, page = _diff_values()
    continuation = repository_diff_continuation_ref(
        diff_ref=page.diff_ref,
        last_file_ref=page.files[0].file_ref,
        page_index=1,
    )
    assert continuation == repository_diff_continuation_ref(
        diff_ref=page.diff_ref,
        last_file_ref=page.files[0].file_ref,
        page_index=1,
    )
    checkpoint = WorkspaceRepositoryEvidenceCheckpoint(
        consumer_key="agent-activity-projection",
        repository_binding_ref=BINDING,
        observer_epoch="observer-epoch-1",
        accepted_cursor=5,
        evidence_revision=2,
        projection_digest="projection:2",
        accepted_at=NOW,
    )
    with pytest.raises(FrozenInstanceError):
        checkpoint.accepted_cursor = 6  # type: ignore[misc]
