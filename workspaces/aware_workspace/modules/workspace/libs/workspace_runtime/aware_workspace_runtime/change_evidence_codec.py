from __future__ import annotations

import base64
import types
from dataclasses import fields, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from functools import cache
from typing import Any, get_args, get_origin, get_type_hints

from .change_evidence import (
    WORKSPACE_REPOSITORY_CHANGE_EVIDENCE_CONTRACT_REF,
    WORKSPACE_REPOSITORY_CHANGE_EVIDENCE_CONTRACT_VERSION,
    WorkspaceRepositoryChangeEvidence,
    WorkspaceRepositoryDiffPage,
    WorkspaceRepositoryDiffRequest,
    WorkspaceRepositoryEvidenceCheckpoint,
    WorkspaceRepositoryExternalEvidenceRef,
    WorkspaceRepositoryMutationReceipt,
)
from .repository_access import RepositoryObservationCoordinate
from .repository_delta import (
    WorkspaceRepositoryContentDelta,
    WorkspaceRepositoryDeltaCapture,
)
from .repository_delta_resolution import WorkspaceRepositoryContentDeltaResolution
from .repository_mutation import (
    WorkspaceRepositoryAuthorizedMutation,
    WorkspaceRepositoryMutationRequest,
    WorkspaceRepositoryTextReplacement,
)

WORKSPACE_REPOSITORY_CHANGE_OPERATION_CONTRACT_REF = (
    "aware.workspace.repository-change-operation.v1"
)
WORKSPACE_REPOSITORY_CHANGE_OPERATION_CONTRACT_VERSION = "1"

_VALUE_TYPES = {
    "change_evidence": WorkspaceRepositoryChangeEvidence,
    "diff_page": WorkspaceRepositoryDiffPage,
    "diff_request": WorkspaceRepositoryDiffRequest,
    "evidence_checkpoint": WorkspaceRepositoryEvidenceCheckpoint,
    "external_evidence": WorkspaceRepositoryExternalEvidenceRef,
    "mutation_receipt": WorkspaceRepositoryMutationReceipt,
    "content_delta": WorkspaceRepositoryContentDelta,
    "delta_capture": WorkspaceRepositoryDeltaCapture,
    "content_delta_resolution": WorkspaceRepositoryContentDeltaResolution,
}
_TYPE_VALUE_KINDS = {value: key for key, value in _VALUE_TYPES.items()}
_ENVELOPE_KEYS = frozenset({"contract_ref", "contract_version", "value_kind", "value"})
_MUTATION_REQUEST_KEYS = frozenset(
    {
        "operation_ref",
        "idempotency_key",
        "mutation_kind",
        "expected_coordinate",
        "target_path",
        "expected_exists",
        "expected_content_digest",
        "content_base64",
        "context_refs",
    }
)
_MUTATION_REQUEST_REPLACEMENT_KEYS = _MUTATION_REQUEST_KEYS | {
    "text_replacements"
}
_AUTHORIZED_MUTATION_KEYS = frozenset({"receipt", "evidence"})


def workspace_repository_value_payload(
    value: WorkspaceRepositoryChangeEvidence
    | WorkspaceRepositoryDiffPage
    | WorkspaceRepositoryDiffRequest
    | WorkspaceRepositoryEvidenceCheckpoint
    | WorkspaceRepositoryExternalEvidenceRef
    | WorkspaceRepositoryMutationReceipt
    | WorkspaceRepositoryContentDelta
    | WorkspaceRepositoryDeltaCapture
    | WorkspaceRepositoryContentDeltaResolution,
) -> dict[str, object]:
    value_kind = _TYPE_VALUE_KINDS.get(type(value))
    if value_kind is None:
        raise TypeError(f"Unsupported repository evidence value: {type(value)!r}")
    return {
        "contract_ref": WORKSPACE_REPOSITORY_CHANGE_EVIDENCE_CONTRACT_REF,
        "contract_version": (
            "2" if type(value) is WorkspaceRepositoryMutationReceipt
            and value.physical_effect is not None
            else WORKSPACE_REPOSITORY_CHANGE_EVIDENCE_CONTRACT_VERSION
        ),
        "value_kind": value_kind,
        "value": _encode(value, type(value)),
    }


def workspace_repository_value_from_payload(
    payload: object,
) -> (
    WorkspaceRepositoryChangeEvidence
    | WorkspaceRepositoryDiffPage
    | WorkspaceRepositoryDiffRequest
    | WorkspaceRepositoryEvidenceCheckpoint
    | WorkspaceRepositoryExternalEvidenceRef
    | WorkspaceRepositoryMutationReceipt
    | WorkspaceRepositoryContentDelta
    | WorkspaceRepositoryDeltaCapture
    | WorkspaceRepositoryContentDeltaResolution
):
    envelope = _mapping(payload, "repository evidence envelope")
    _exact_keys(envelope, _ENVELOPE_KEYS, "repository evidence envelope")
    if envelope["contract_ref"] != WORKSPACE_REPOSITORY_CHANGE_EVIDENCE_CONTRACT_REF:
        raise ValueError("Repository evidence contract ref is unsupported")
    if (
        envelope["contract_version"] != WORKSPACE_REPOSITORY_CHANGE_EVIDENCE_CONTRACT_VERSION
        and not (envelope["contract_version"] == "2" and envelope["value_kind"] == "mutation_receipt")
    ):
        raise ValueError("Repository evidence contract version is unsupported")
    value_kind = _string(envelope["value_kind"], "value_kind")
    value_type = _VALUE_TYPES.get(value_kind)
    if value_type is None:
        raise ValueError(f"Repository evidence value kind is unsupported: {value_kind}")
    if value_type is WorkspaceRepositoryMutationReceipt:
        receipt = _mapping(envelope["value"], "mutation_receipt")
        has_effect = receipt.get("physical_effect") is not None
        if has_effect != (envelope["contract_version"] == "2"):
            raise ValueError("Physical effect receipt requires version 2")
    return _decode(envelope["value"], value_type, value_kind)


def repository_external_evidence_payload(
    value: WorkspaceRepositoryExternalEvidenceRef,
) -> dict[str, object]:
    return workspace_repository_value_payload(value)


def repository_external_evidence_from_payload(
    payload: object,
) -> WorkspaceRepositoryExternalEvidenceRef:
    return _expected(payload, WorkspaceRepositoryExternalEvidenceRef)


def repository_change_evidence_payload(
    value: WorkspaceRepositoryChangeEvidence,
) -> dict[str, object]:
    return workspace_repository_value_payload(value)


def repository_change_evidence_from_payload(
    payload: object,
) -> WorkspaceRepositoryChangeEvidence:
    return _expected(payload, WorkspaceRepositoryChangeEvidence)


def repository_mutation_receipt_payload(
    value: WorkspaceRepositoryMutationReceipt,
) -> dict[str, object]:
    return workspace_repository_value_payload(value)


def repository_mutation_receipt_from_payload(
    payload: object,
) -> WorkspaceRepositoryMutationReceipt:
    return _expected(payload, WorkspaceRepositoryMutationReceipt)


def repository_diff_request_payload(
    value: WorkspaceRepositoryDiffRequest,
) -> dict[str, object]:
    return workspace_repository_value_payload(value)


def repository_diff_request_from_payload(
    payload: object,
) -> WorkspaceRepositoryDiffRequest:
    return _expected(payload, WorkspaceRepositoryDiffRequest)


def repository_diff_page_payload(
    value: WorkspaceRepositoryDiffPage,
) -> dict[str, object]:
    return workspace_repository_value_payload(value)


def repository_diff_page_from_payload(
    payload: object,
) -> WorkspaceRepositoryDiffPage:
    return _expected(payload, WorkspaceRepositoryDiffPage)


def repository_evidence_checkpoint_payload(
    value: WorkspaceRepositoryEvidenceCheckpoint,
) -> dict[str, object]:
    return workspace_repository_value_payload(value)


def repository_evidence_checkpoint_from_payload(
    payload: object,
) -> WorkspaceRepositoryEvidenceCheckpoint:
    return _expected(payload, WorkspaceRepositoryEvidenceCheckpoint)


def repository_delta_capture_payload(
    value: WorkspaceRepositoryDeltaCapture,
) -> dict[str, object]:
    return workspace_repository_value_payload(value)


def repository_delta_capture_from_payload(
    payload: object,
) -> WorkspaceRepositoryDeltaCapture:
    return _expected(payload, WorkspaceRepositoryDeltaCapture)


def repository_content_delta_payload(
    value: WorkspaceRepositoryContentDelta,
) -> dict[str, object]:
    return workspace_repository_value_payload(value)


def repository_content_delta_from_payload(
    payload: object,
) -> WorkspaceRepositoryContentDelta:
    return _expected(payload, WorkspaceRepositoryContentDelta)


def repository_content_delta_resolution_payload(
    value: WorkspaceRepositoryContentDeltaResolution,
) -> dict[str, object]:
    return workspace_repository_value_payload(value)


def repository_content_delta_resolution_from_payload(
    payload: object,
) -> WorkspaceRepositoryContentDeltaResolution:
    return _expected(payload, WorkspaceRepositoryContentDeltaResolution)


def repository_mutation_request_payload(
    value: WorkspaceRepositoryMutationRequest,
) -> dict[str, object]:
    request_value: dict[str, object] = {
            "operation_ref": value.operation_ref,
            "idempotency_key": value.idempotency_key,
            "mutation_kind": value.mutation_kind.value,
            "expected_coordinate": _encode(
                value.expected_coordinate,
                type(value.expected_coordinate),
            ),
            "target_path": value.target_path,
            "expected_exists": value.expected_exists,
            "expected_content_digest": value.expected_content_digest,
            "content_base64": (
                None
                if value.content is None
                else base64.b64encode(value.content).decode("ascii")
            ),
            "context_refs": list(value.context_refs),
    }
    if value.text_replacements:
        request_value["text_replacements"] = [
            {
                "old_text": replacement.old_text,
                "new_text": replacement.new_text,
            }
            for replacement in value.text_replacements
        ]
    return _operation_payload("mutation_request", request_value)


def repository_mutation_request_from_payload(
    payload: object,
) -> WorkspaceRepositoryMutationRequest:
    value = _operation_value(payload, "mutation_request")
    if frozenset(value) not in {
        _MUTATION_REQUEST_KEYS,
        _MUTATION_REQUEST_REPLACEMENT_KEYS,
    }:
        _exact_keys(value, _MUTATION_REQUEST_KEYS, "mutation_request")
    encoded_content = value["content_base64"]
    if encoded_content is None:
        content = None
    else:
        raw = _string(encoded_content, "mutation_request.content_base64")
        try:
            content = base64.b64decode(raw, validate=True)
        except ValueError as error:
            raise ValueError(
                "mutation_request.content_base64 must be canonical base64"
            ) from error
        if base64.b64encode(content).decode("ascii") != raw:
            raise ValueError("mutation_request.content_base64 must be canonical base64")
    raw_replacements = value.get("text_replacements", [])
    if not isinstance(raw_replacements, list):
        raise TypeError("mutation_request.text_replacements must be a list")
    replacements: list[WorkspaceRepositoryTextReplacement] = []
    for index, raw_replacement in enumerate(raw_replacements):
        if not isinstance(raw_replacement, dict) or set(raw_replacement) != {
            "old_text",
            "new_text",
        }:
            raise ValueError(
                "mutation_request.text_replacements entries are invalid"
            )
        replacements.append(
            WorkspaceRepositoryTextReplacement(
                old_text=_string(
                    raw_replacement["old_text"],
                    f"mutation_request.text_replacements[{index}].old_text",
                ),
                new_text=_string(
                    raw_replacement["new_text"],
                    f"mutation_request.text_replacements[{index}].new_text",
                ),
            )
        )
    return WorkspaceRepositoryMutationRequest(
        operation_ref=_string(value["operation_ref"], "mutation_request.operation_ref"),
        idempotency_key=_string(
            value["idempotency_key"], "mutation_request.idempotency_key"
        ),
        mutation_kind=_decode(
            value["mutation_kind"],
            get_type_hints(WorkspaceRepositoryMutationRequest)["mutation_kind"],
            "mutation_request.mutation_kind",
        ),
        expected_coordinate=_decode(
            value["expected_coordinate"],
            get_type_hints(WorkspaceRepositoryMutationRequest)["expected_coordinate"],
            "mutation_request.expected_coordinate",
        ),
        target_path=_string(value["target_path"], "mutation_request.target_path"),
        expected_exists=_decode(
            value["expected_exists"], bool, "mutation_request.expected_exists"
        ),
        expected_content_digest=_decode(
            value["expected_content_digest"],
            str | None,
            "mutation_request.expected_content_digest",
        ),
        content=content,
        text_replacements=tuple(replacements),
        context_refs=_decode(
            value["context_refs"], tuple[str, ...], "mutation_request.context_refs"
        ),
    )


def repository_authorized_mutation_payload(
    value: WorkspaceRepositoryAuthorizedMutation,
) -> dict[str, object]:
    return _operation_payload(
        "authorized_mutation",
        {
            "receipt": repository_mutation_receipt_payload(value.receipt),
            "evidence": (
                None
                if value.evidence is None
                else repository_change_evidence_payload(value.evidence)
            ),
        },
    )


def repository_authorized_mutation_from_payload(
    payload: object,
) -> WorkspaceRepositoryAuthorizedMutation:
    value = _operation_value(payload, "authorized_mutation")
    _exact_keys(value, _AUTHORIZED_MUTATION_KEYS, "authorized_mutation")
    evidence_payload = value["evidence"]
    return WorkspaceRepositoryAuthorizedMutation(
        receipt=repository_mutation_receipt_from_payload(value["receipt"]),
        evidence=(
            None
            if evidence_payload is None
            else repository_change_evidence_from_payload(evidence_payload)
        ),
    )


def _operation_payload(value_kind: str, value: dict[str, object]) -> dict[str, object]:
    return {
        "contract_ref": WORKSPACE_REPOSITORY_CHANGE_OPERATION_CONTRACT_REF,
        "contract_version": WORKSPACE_REPOSITORY_CHANGE_OPERATION_CONTRACT_VERSION,
        "value_kind": value_kind,
        "value": value,
    }


def _operation_value(payload: object, expected_kind: str) -> dict[str, object]:
    envelope = _mapping(payload, "repository change operation envelope")
    _exact_keys(envelope, _ENVELOPE_KEYS, "repository change operation envelope")
    if envelope["contract_ref"] != WORKSPACE_REPOSITORY_CHANGE_OPERATION_CONTRACT_REF:
        raise ValueError("Repository change operation contract ref is unsupported")
    if (
        envelope["contract_version"]
        != WORKSPACE_REPOSITORY_CHANGE_OPERATION_CONTRACT_VERSION
    ):
        raise ValueError("Repository change operation contract version is unsupported")
    value_kind = _string(envelope["value_kind"], "value_kind")
    if value_kind != expected_kind:
        raise ValueError(f"Expected repository change operation kind {expected_kind}")
    return _mapping(envelope["value"], expected_kind)


def _expected(payload: object, expected_type: type[Any]) -> Any:
    value = workspace_repository_value_from_payload(payload)
    if type(value) is not expected_type:
        expected_kind = _TYPE_VALUE_KINDS[expected_type]
        raise ValueError(f"Expected repository evidence value kind {expected_kind}")
    return value


def _encode(value: Any, annotation: Any) -> object:
    if value is None:
        return None
    origin = get_origin(annotation)
    if origin in (types.UnionType, getattr(types, "UnionType", object)):
        return _encode_union(value, annotation)
    if origin is tuple:
        item_type = get_args(annotation)[0]
        return [_encode(item, item_type) for item in value]
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return value.value
    if annotation is datetime:
        return _timestamp(value)
    if is_dataclass(annotation):
        hints = _type_hints(annotation)
        return {
            field.name: _encode(getattr(value, field.name), hints[field.name])
            for field in fields(annotation)
            if not (annotation is WorkspaceRepositoryMutationReceipt and field.name == "physical_effect" and value.physical_effect is None)
        }
    if annotation in (str, int, bool):
        return value
    raise TypeError(f"Unsupported repository evidence annotation: {annotation!r}")


def _encode_union(value: Any, annotation: Any) -> object:
    candidates = tuple(item for item in get_args(annotation) if item is not type(None))
    for candidate in candidates:
        if _matches(value, candidate):
            return _encode(value, candidate)
    raise TypeError(f"Value does not match repository evidence union: {annotation!r}")


def _decode(payload: object, annotation: Any, field_name: str) -> Any:
    origin = get_origin(annotation)
    if origin in (types.UnionType, getattr(types, "UnionType", object)):
        if payload is None and type(None) in get_args(annotation):
            return None
        candidates = tuple(
            item for item in get_args(annotation) if item is not type(None)
        )
        if len(candidates) != 1:
            raise TypeError(f"Unsupported repository evidence union: {annotation!r}")
        return _decode(payload, candidates[0], field_name)
    if origin is tuple:
        if not isinstance(payload, list):
            raise ValueError(f"{field_name} must be an array")
        item_type = get_args(annotation)[0]
        return tuple(
            _decode(item, item_type, f"{field_name}[{index}]")
            for index, item in enumerate(payload)
        )
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        raw = _string(payload, field_name)
        try:
            return annotation(raw)
        except ValueError as error:
            raise ValueError(f"{field_name} has an unsupported value: {raw}") from error
    if annotation is datetime:
        return _datetime(payload, field_name)
    if is_dataclass(annotation):
        mapping = _mapping(payload, field_name)
        if annotation is WorkspaceRepositoryMutationReceipt and "physical_effect" not in mapping:
            mapping = {**mapping, "physical_effect": None}
        hints = _type_hints(annotation)
        expected_keys = frozenset(field.name for field in fields(annotation))
        _exact_keys(mapping, expected_keys, field_name)
        return annotation(
            **{
                field.name: _decode(
                    mapping[field.name], hints[field.name], f"{field_name}.{field.name}"
                )
                for field in fields(annotation)
            }
        )
    if annotation is str:
        return _string(payload, field_name)
    if annotation is int:
        if type(payload) is not int:
            raise ValueError(f"{field_name} must be an integer")
        return payload
    if annotation is bool:
        if type(payload) is not bool:
            raise ValueError(f"{field_name} must be a boolean")
        return payload
    raise TypeError(f"Unsupported repository evidence annotation: {annotation!r}")


def _matches(value: Any, annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is tuple:
        return isinstance(value, tuple)
    return isinstance(value, annotation)


@cache
def _type_hints(value_type: type[Any]) -> dict[str, Any]:
    if value_type is RepositoryObservationCoordinate:
        return get_type_hints(RepositoryObservationCoordinate)
    return get_type_hints(value_type)


def _timestamp(value: datetime) -> str:
    return (
        value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )


def _datetime(payload: object, field_name: str) -> datetime:
    raw = _string(payload, field_name)
    if not raw.endswith("Z"):
        raise ValueError(f"{field_name} must be a canonical UTC timestamp")
    try:
        value = datetime.fromisoformat(f"{raw[:-1]}+00:00")
    except ValueError as error:
        raise ValueError(f"{field_name} must be a canonical UTC timestamp") from error
    if _timestamp(value) != raw:
        raise ValueError(f"{field_name} must be a canonical UTC timestamp")
    return value


def _mapping(payload: object, field_name: str) -> dict[str, object]:
    if not isinstance(payload, dict) or any(
        not isinstance(key, str) for key in payload
    ):
        raise ValueError(f"{field_name} must be an object with string keys")
    return payload


def _exact_keys(
    payload: dict[str, object], expected: frozenset[str], field_name: str
) -> None:
    actual = frozenset(payload)
    if actual != expected:
        missing = ", ".join(sorted(expected - actual)) or "none"
        unknown = ", ".join(sorted(actual - expected)) or "none"
        raise ValueError(
            f"{field_name} fields differ; missing: {missing}; unknown: {unknown}"
        )


def _string(payload: object, field_name: str) -> str:
    if not isinstance(payload, str):
        raise TypeError(f"{field_name} must be a string")
    return payload
