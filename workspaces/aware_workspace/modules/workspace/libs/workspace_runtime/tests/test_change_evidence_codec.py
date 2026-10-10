from __future__ import annotations

import copy
import json

import pytest
from aware_workspace_runtime import (
    RepositoryEvidencePosture,
    RepositoryMutationKind,
    RepositoryMutationOutcome,
    WorkspaceRepositoryAuthorizedMutation,
    WorkspaceRepositoryEvidenceCheckpoint,
    WorkspaceRepositoryMutationReceipt,
    WorkspaceRepositoryMutationRequest,
    repository_authorized_mutation_from_payload,
    repository_authorized_mutation_payload,
    repository_change_evidence_from_payload,
    repository_content_delta_from_payload,
    repository_delta_capture_from_payload,
    repository_diff_page_from_payload,
    repository_diff_request_from_payload,
    repository_evidence_checkpoint_from_payload,
    repository_external_evidence_from_payload,
    repository_mutation_receipt_from_payload,
    repository_mutation_receipt_ref,
    repository_mutation_request_from_payload,
    repository_mutation_request_payload,
    workspace_repository_value_from_payload,
    workspace_repository_value_payload,
)
from test_change_evidence import (
    BINDING,
    NOW,
    _diff_values,
    _evidence,
    _external,
    _observation,
)
from test_repository_delta import capture, content_delta


def _mutation_receipt() -> WorkspaceRepositoryMutationReceipt:
    return WorkspaceRepositoryMutationReceipt(
        mutation_receipt_ref=repository_mutation_receipt_ref(
            repository_binding_ref=BINDING,
            operation_ref="operation:codec",
            idempotency_key="request:codec",
        ),
        repository_binding_ref=BINDING,
        operation_ref="operation:codec",
        idempotency_key="request:codec",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_observation(5),
        target_path="new.txt",
        expected_exists=False,
        expected_content_digest=None,
        outcome=RepositoryMutationOutcome.APPLIED,
        context_refs=("opaque:caller",),
        result_coordinate=_observation(6),
        result_entry_ref="entry:new",
        result_content_digest="content:new",
        result_size_bytes=8,
        request_body_evidence_ref="body:request",
        result_body_evidence_ref="body:result",
        delta_evidence_ref="delta:create",
    )


def _checkpoint() -> WorkspaceRepositoryEvidenceCheckpoint:
    return WorkspaceRepositoryEvidenceCheckpoint(
        consumer_key="coordination-issue-reader",
        repository_binding_ref=BINDING,
        observer_epoch="observer-epoch-1",
        accepted_cursor=6,
        evidence_revision=4,
        projection_digest="projection:4",
        accepted_at=NOW,
    )


@pytest.mark.parametrize(
    ("value", "decoder"),
    [
        (
            _evidence(RepositoryEvidencePosture.PROVIDER_CORRELATED),
            repository_change_evidence_from_payload,
        ),
        (_external(), repository_external_evidence_from_payload),
        (_mutation_receipt(), repository_mutation_receipt_from_payload),
        (_diff_values()[0], repository_diff_request_from_payload),
        (_diff_values()[1], repository_diff_page_from_payload),
        (_checkpoint(), repository_evidence_checkpoint_from_payload),
        (capture(), repository_delta_capture_from_payload),
        (content_delta(capture()), repository_content_delta_from_payload),
    ],
)
def test_every_top_level_value_round_trips_through_json(
    value: object, decoder: object
) -> None:
    payload = workspace_repository_value_payload(value)  # type: ignore[arg-type]
    transported = json.loads(json.dumps(payload))
    assert decoder(transported) == value  # type: ignore[operator]
    assert workspace_repository_value_from_payload(transported) == value


@pytest.mark.parametrize(
    ("field", "replacement", "match"),
    [
        ("contract_ref", "wrong-contract", "contract ref"),
        ("contract_version", "99", "contract version"),
        ("value_kind", "unknown", "value kind"),
    ],
)
def test_envelope_rejects_unknown_contract_and_kind(
    field: str, replacement: str, match: str
) -> None:
    payload = workspace_repository_value_payload(_external())
    payload[field] = replacement
    with pytest.raises(ValueError, match=match):
        workspace_repository_value_from_payload(payload)


def test_codec_rejects_missing_unknown_and_wrong_typed_fields() -> None:
    payload = workspace_repository_value_payload(_external())
    missing = copy.deepcopy(payload)
    del missing["value"]["observed_at"]  # type: ignore[index]
    with pytest.raises(ValueError, match="missing: observed_at"):
        workspace_repository_value_from_payload(missing)

    unknown = copy.deepcopy(payload)
    unknown["value"]["provider_payload"] = {"trusted": True}  # type: ignore[index]
    with pytest.raises(ValueError, match="unknown: provider_payload"):
        workspace_repository_value_from_payload(unknown)

    wrong_type = copy.deepcopy(payload)
    wrong_type["value"]["complete"] = 1  # type: ignore[index]
    with pytest.raises(ValueError, match="must be a boolean"):
        workspace_repository_value_from_payload(wrong_type)


def test_codec_revalidates_derived_refs_and_provenance_after_transport() -> None:
    evidence = _evidence(RepositoryEvidencePosture.WORKSPACE_OBSERVED)
    payload = workspace_repository_value_payload(evidence)
    tampered = copy.deepcopy(payload)
    tampered["value"]["evidence_ref"] = "tampered"  # type: ignore[index]
    with pytest.raises(ValueError, match="not deterministic"):
        workspace_repository_value_from_payload(tampered)

    posture = copy.deepcopy(payload)
    posture["value"]["posture"] = "workspace_authorized"  # type: ignore[index]
    posture["value"]["changed_entries"][0]["posture"] = "workspace_authorized"  # type: ignore[index]
    with pytest.raises(ValueError, match="mutation receipt"):
        workspace_repository_value_from_payload(posture)


def test_codec_preserves_opaque_context_ref_order_without_interpretation() -> None:
    payload = workspace_repository_value_payload(_external())
    restored = repository_external_evidence_from_payload(
        json.loads(json.dumps(payload))
    )
    assert restored.context_refs == ("agent-session:1", "issue:42")


def test_specific_decoder_rejects_a_different_valid_value_kind() -> None:
    payload = workspace_repository_value_payload(_checkpoint())
    with pytest.raises(ValueError, match="Expected repository evidence value kind"):
        repository_diff_page_from_payload(payload)


def test_mutation_operation_request_and_result_are_strict_and_lossless() -> None:
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:transport",
        idempotency_key="request:transport",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_observation(5),
        target_path="src/new.txt",
        expected_exists=False,
        expected_content_digest=None,
        content=b"hello\x00aware",
        context_refs=("issue:42",),
    )
    request_payload = json.loads(
        json.dumps(repository_mutation_request_payload(request))
    )
    assert repository_mutation_request_from_payload(request_payload) == request

    failed_receipt = WorkspaceRepositoryMutationReceipt(
        mutation_receipt_ref=repository_mutation_receipt_ref(
            repository_binding_ref=BINDING,
            operation_ref="operation:transport",
            idempotency_key="request:transport",
        ),
        repository_binding_ref=BINDING,
        operation_ref="operation:transport",
        idempotency_key="request:transport",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_observation(5),
        target_path="src/new.txt",
        expected_exists=False,
        expected_content_digest=None,
        outcome=RepositoryMutationOutcome.CONFLICT,
        context_refs=("issue:42",),
        error_code="snapshot_existence_mismatch",
    )
    result = WorkspaceRepositoryAuthorizedMutation(failed_receipt, None)
    result_payload = json.loads(
        json.dumps(repository_authorized_mutation_payload(result))
    )
    assert repository_authorized_mutation_from_payload(result_payload) == result


def test_mutation_operation_codec_preserves_exact_text_replacements() -> None:
    from aware_workspace_runtime import WorkspaceRepositoryTextReplacement

    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:replace",
        idempotency_key="request:replace",
        mutation_kind=RepositoryMutationKind.UPDATE,
        expected_coordinate=_observation(6),
        target_path="src/existing.txt",
        expected_exists=True,
        expected_content_digest="sha256:" + "a" * 64,
        text_replacements=(
            WorkspaceRepositoryTextReplacement(
                old_text="before",
                new_text="after",
            ),
        ),
        context_refs=("work-context:42",),
    )

    payload = json.loads(json.dumps(repository_mutation_request_payload(request)))

    assert payload["value"]["text_replacements"] == [  # type: ignore[index]
        {"old_text": "before", "new_text": "after"}
    ]
    assert repository_mutation_request_from_payload(payload) == request


def test_mutation_operation_codec_rejects_noncanonical_content_and_tampering() -> None:
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:transport",
        idempotency_key="request:transport",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_observation(5),
        target_path="new.txt",
        expected_exists=False,
        expected_content_digest=None,
        content=b"aware",
    )
    payload = repository_mutation_request_payload(request)
    invalid_content = copy.deepcopy(payload)
    invalid_content["value"]["content_base64"] = "not base64"  # type: ignore[index]
    with pytest.raises(ValueError, match="canonical base64"):
        repository_mutation_request_from_payload(invalid_content)

    unknown = copy.deepcopy(payload)
    unknown["value"]["provider"] = "filesystem"  # type: ignore[index]
    with pytest.raises(ValueError, match="unknown: provider"):
        repository_mutation_request_from_payload(unknown)
