"""Strict detached codecs for the ordinary filesystem Service subset.

These values are presentation and intent data, never original owner handles.
"""

from __future__ import annotations

import json
from dataclasses import MISSING, fields, is_dataclass
from enum import StrEnum
from types import UnionType
from typing import Any, cast, get_args, get_origin, get_type_hints

from aware_issue_runtime import IssueReadProjection

from . import operation as op

MAX_REQUEST_BYTES = 65_536
MAX_RESULT_BYTES = 786_432
REQUEST_TYPES: dict[str, type[Any]] = {
    op.ISSUE_RESOLVE_READ_PROJECTION_PROVIDER_OPERATION_REF: op.IssueReadProjectionResolveRequest,
    op.ISSUE_ENSURE_SNAPSHOT_PROVIDER_OPERATION_REF: op.IssueEnsureSnapshotRequest,
    op.ISSUE_START_PROGRESS_PROVIDER_OPERATION_REF: op.IssueStartProgressRequest,
    op.ISSUE_BLOCK_PROVIDER_OPERATION_REF: op.IssueBlockRequest,
    op.ISSUE_RESUME_PROVIDER_OPERATION_REF: op.IssueResumeRequest,
    op.ISSUE_SET_OWNER_PROVIDER_OPERATION_REF: op.IssueSetOwnerRequest,
    op.ISSUE_BIND_SCOPE_PROVIDER_OPERATION_REF: op.IssueBindScopePathsRequest,
    op.ISSUE_APPEND_UPDATE_PROVIDER_OPERATION_REF: op.IssueAppendUpdateRequest,
    op.ISSUE_APPEND_EVIDENCE_PROVIDER_OPERATION_REF: op.IssueAppendEvidenceRequest,
}


def _bounded(value, maximum):
    nodes = 0

    def visit(item, depth):
        nonlocal nodes
        nodes += 1
        if depth > 32 or nodes > 8192:
            raise ValueError("Issue wire structure exceeds bounds")
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str:
                    raise ValueError("JSON keys must be strings")
                visit(key, depth + 1)
                visit(child, depth + 1)
        elif type(item) is list:
            if len(item) > 4096:
                raise ValueError("Issue array exceeds bounds")
            for child in item:
                visit(child, depth + 1)
        elif type(item) is str:
            if len(item.encode("utf-8")) > 262144:
                raise ValueError("Issue string exceeds bounds")
        elif item is not None and type(item) not in (bool, int):
            raise ValueError("Unsupported Issue JSON value")

    visit(value, 0)
    if (
        len(
            json.dumps(
                value, ensure_ascii=False, separators=(",", ":"), allow_nan=False
            ).encode()
        )
        > maximum
    ):
        raise ValueError("Issue wire byte limit exceeded")
    return value


def _keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError("Issue wire has missing or extra fields")
    return value


def _typed(annotation: Any, value: Any) -> Any:
    origin = get_origin(annotation)
    if origin is UnionType:
        for choice in get_args(annotation):
            try:
                return _typed(choice, value)
            except (ValueError, TypeError):
                pass
        raise ValueError("Invalid optional Issue value")
    if origin is tuple:
        if type(value) is not list:
            raise ValueError("Tuple wire value must be an array")
        return tuple(_typed(get_args(annotation)[0], item) for item in value)
    if annotation is type(None):
        if value is not None:
            raise ValueError("Expected null")
        return None
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        if type(value) is not str:
            raise ValueError("Enum must be a string")
        return annotation(value)
    if is_dataclass(annotation):
        return _record(annotation, value)
    if type(value) is not annotation:
        raise ValueError("Issue field type mismatch")
    return value


def _record(cls: Any, value: Any, *, overrides: dict[str, Any] | None = None) -> Any:
    if type(value) is not dict:
        raise ValueError("Issue record must be an object")
    declared = {field.name: field for field in fields(cls)}
    if set(value) - set(declared):
        raise ValueError("Unknown Issue record field")
    hints = get_type_hints(cls)
    for name, field in declared.items():
        if (
            name not in value
            and field.default is MISSING
            and field.default_factory is MISSING
        ):
            raise ValueError("Missing Issue record field")
    arguments = {
        name: _typed(hints[name], item)
        for name, item in value.items()
        if overrides is None or name not in overrides
    }
    if overrides is not None:
        arguments.update(overrides)
    return cls(**arguments)


def _projection(value):
    _keys(
        value,
        (
            "schema_version",
            "issue_ref",
            "identity",
            "content",
            "activity",
            "evidence",
            "resolution",
            "additional_sections",
            "source",
            "revision",
        ),
    )
    identity = _keys(
        value["identity"],
        (
            "title",
            "slug",
            "tag",
            "status",
            "priority",
            "owner_ref",
            "goal_ref",
            "captured",
            "source_description",
        ),
    )
    content = _keys(
        value["content"],
        ("problem_items", "goal_items", "acceptance_items", "ownership_scope"),
    )
    source = _keys(
        value["source"],
        ("path", "digest", "raw_markdown", "observed_at", "time_authority"),
    )
    revision = _keys(
        value["revision"],
        ("projection_revision", "lane_head_commit_id", "function_call_id"),
    )
    if value["schema_version"] != op.ISSUE_PROJECTION_SCHEMA_VERSION:
        raise ValueError("Projection schema mismatch")
    op._sha256(source["digest"], "projection source digest")
    if (
        source["raw_markdown"] is not None
        or revision["projection_revision"] != source["digest"]
    ):
        raise ValueError("Detached projection source/revision mismatch")
    flattened = {
        **identity,
        **content,
        "schema_version": value["schema_version"],
        "issue_ref": value["issue_ref"],
        "activities": value["activity"],
        "evidence": value["evidence"],
        "resolution": value["resolution"],
        "additional_sections": value["additional_sections"],
        "source_path": source["path"],
        "source_digest": source["digest"],
        "raw_markdown": "",
        "observed_at": source["observed_at"],
        "observation_time_authority": source["time_authority"],
        "lane_head_commit_id": revision["lane_head_commit_id"],
        "function_call_id": revision["function_call_id"],
    }
    result = _record(IssueReadProjection, flattened)
    if result.to_payload(include_raw_markdown=False) != value:
        raise ValueError("Projection codec did not conserve values")
    return result


def encode_issue_request(request: op._RequestValue) -> dict[str, object]:
    if type(request) not in REQUEST_TYPES.values():
        raise ValueError("Unsupported Issue request")
    return _bounded(request.to_wire(), MAX_REQUEST_BYTES)


def decode_issue_request(operation_key: str, value: object) -> op._RequestValue:
    _bounded(value, MAX_REQUEST_BYTES)
    cls = REQUEST_TYPES.get(operation_key)
    if cls is None or type(value) is not dict:
        raise ValueError("Unsupported Issue operation")
    wire = dict(value)
    if cls is op.IssueReadProjectionResolveRequest:
        if (
            wire.pop("contract", None)
            != op.ISSUE_READ_PROJECTION_RESOLVE_REQUEST_CONTRACT
        ):
            raise ValueError("Read contract mismatch")
    elif wire.pop("operation_ref", None) != cls.operation_ref:
        raise ValueError("Operation mismatch")
    result = _record(cls, wire)
    if encode_issue_request(result) != value:
        raise ValueError("Request codec did not conserve values")
    return cast(op._RequestValue, result)


def encode_issue_result(
    result: op.IssueReadProjectionResolveResult | op.IssueMutationResult,
) -> dict[str, object]:
    if type(result) not in (
        op.IssueReadProjectionResolveResult,
        op.IssueMutationResult,
    ):
        raise ValueError("Unsupported Issue result")
    return _bounded(result.to_wire(), MAX_RESULT_BYTES)


def decode_issue_result(
    operation_key: str, value: object
) -> op.IssueReadProjectionResolveResult | op.IssueMutationResult:
    _bounded(value, MAX_RESULT_BYTES)
    if operation_key not in REQUEST_TYPES or type(value) is not dict:
        raise ValueError("Unsupported Issue result operation")
    wire = dict(value)
    read = REQUEST_TYPES[operation_key] is op.IssueReadProjectionResolveRequest
    cls = op.IssueReadProjectionResolveResult if read else op.IssueMutationResult
    contract = (
        op.ISSUE_READ_PROJECTION_RESOLVE_RESULT_CONTRACT
        if read
        else op.ISSUE_MUTATION_RESULT_CONTRACT
    )
    if (
        wire.pop("contract", None) != contract
        or wire.pop("projection_ref", None) != op.ISSUE_PROJECTION_SCHEMA_VERSION
    ):
        raise ValueError("Result contract mismatch")
    expected = (
        op.ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF
        if read
        else REQUEST_TYPES[operation_key].operation_ref
    )
    if wire.get("operation_ref") != expected:
        raise ValueError("Result operation mismatch")
    projection = wire.pop("projection", None)
    # Parse primitive fields first; never accept a caller-authored dataclass.
    parsed = _projection(projection) if projection is not None else None
    result = _record(
        cls, {**wire, "projection": None}, overrides={"projection": parsed}
    )
    if encode_issue_result(result) != value:
        raise ValueError("Result codec did not conserve values")
    if (
        type(result) is op.IssueMutationResult
        and result.projection is not None
        and result.source_sha256_after != result.projection.source_digest
    ):
        raise ValueError("Mutation source/projection digest mismatch")
    return cast(op.IssueReadProjectionResolveResult | op.IssueMutationResult, result)
