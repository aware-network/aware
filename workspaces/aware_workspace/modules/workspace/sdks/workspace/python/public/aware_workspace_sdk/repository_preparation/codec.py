"""Strict evidence codecs. Decoding never constructs a live admission."""

from __future__ import annotations

import json
import math
import re
from dataclasses import fields
from types import UnionType
from typing import Any, Literal, get_args, get_origin, get_type_hints

from .values import (
    RepositoryPreparationEffect,
    RepositoryPreparationErrorEvidence,
    RepositoryPreparationPlanObservation,
    RepositoryPrepareRequest,
    RepositoryPrepareResult,
)

_ROOTS = (
    RepositoryPrepareRequest,
    RepositoryPreparationEffect,
    RepositoryPreparationPlanObservation,
    RepositoryPrepareResult,
    RepositoryPreparationErrorEvidence,
)
type _Value = (
    RepositoryPrepareRequest
    | RepositoryPreparationEffect
    | RepositoryPreparationPlanObservation
    | RepositoryPrepareResult
    | RepositoryPreparationErrorEvidence
)


class RepositoryPreparationValueError(ValueError):
    pass


def _root_type(root: object) -> bool:
    return any(root is declared for declared in _ROOTS)


def _json_value(value: Any) -> Any:
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is list:
        return [_json_value(item) for item in value]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: _json_value(item) for key, item in value.items()}
    raise RepositoryPreparationValueError("json_value_required")


def unvalidated_report(value: Any, *, _seen=None, _depth=0) -> Any:
    """Preserve plain reported data without trusting it or executing repr hooks."""
    seen = set() if _seen is None else _seen
    if _depth >= 32 or id(value) in seen:
        return {
            "unvalidated_unrepresentable": type(value).__name__,
            "reason": "cycle_or_depth_bound",
        }

    def child(item):
        return unvalidated_report(item, _seen=seen | {id(value)}, _depth=_depth + 1)

    if _root_type(type(value)):
        return {item.name: child(getattr(value, item.name)) for item in fields(value)}
    if type(value) in (tuple, list):
        return [child(item) for item in value]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: child(item) for key, item in value.items()}
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        return value if math.isfinite(value) else {"unvalidated_nonfinite": str(value)}
    return {"unvalidated_type": type(value).__name__}


def _convert(annotation: Any, value: Any, *, decode: bool) -> Any:
    origin, arguments = get_origin(annotation), get_args(annotation)
    if origin is UnionType:
        for member in arguments:
            try:
                return _convert(member, value, decode=decode)
            except RepositoryPreparationValueError:
                pass
        raise RepositoryPreparationValueError("union_value_required")
    if annotation is type(None):
        if value is not None:
            raise RepositoryPreparationValueError("null_required")
        return None
    if annotation is object:
        return _json_value(value)
    if origin is Literal:
        if not any(type(value) is type(item) and value == item for item in arguments):
            raise RepositoryPreparationValueError("enum_value_required")
        return value
    if origin is tuple:
        if type(value) is not (list if decode else tuple):
            raise RepositoryPreparationValueError("array_required")
        converted = [_convert(arguments[0], item, decode=decode) for item in value]
        return tuple(converted) if decode else converted
    if _root_type(annotation):
        return (
            repository_preparation_value_from_payload(annotation, value)
            if decode
            else repository_preparation_value_to_payload(
                value, expected_type=annotation
            )
        )
    if annotation in (str, int, bool) and type(value) is annotation:
        return value
    raise RepositoryPreparationValueError("exact_value_type_required")


def _semantic(value: Any) -> None:
    if type(value) is RepositoryPrepareRequest and (
        not value.repository_root or "\x00" in value.repository_root
    ):
        raise RepositoryPreparationValueError("repository_root_required")
    if isinstance(
        value,
        (
            RepositoryPrepareResult,
            RepositoryPreparationErrorEvidence,
        ),
    ):
        result = type(value) is RepositoryPrepareResult
        expected = (
            "aware.repository.prepare-result.v1"
            if result
            else "aware.repository.prepare-error.v1"
        )
        if (
            value.contract != expected
            or value.operation_ref != "repository_sdk.prepare_repository"
        ):
            raise RepositoryPreparationValueError("operation_contract_mismatch")
        if value.authorizes_retry is not False:
            raise RepositoryPreparationValueError("retry_authority_refused")
        if result:
            if value.authority_mode != "filesystem":
                raise RepositoryPreparationValueError("authority_mode_mismatch")
            if value.repository_root != value.request.repository_root:
                raise RepositoryPreparationValueError("repository_root_mismatch")
            if (
                value.head is not None
                and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value.head) is None
            ):
                raise RepositoryPreparationValueError("head_shape_invalid")
            if value.outcome == "refused" and not any(
                item.strip() for item in value.diagnostics
            ):
                raise RepositoryPreparationValueError("refusal_diagnostics_required")
        elif (
            isinstance(value, RepositoryPreparationErrorEvidence)
            and value.evidence_grade != "unvalidated_provider_report"
        ):
            raise RepositoryPreparationValueError("evidence_grade_mismatch")


def repository_preparation_value_to_payload(
    value: Any, *, expected_type: type | None = None
) -> dict[str, Any]:
    if not _root_type(type(value)) or (
        expected_type is not None and type(value) is not expected_type
    ):
        raise RepositoryPreparationValueError("authored_value_required")
    hints = get_type_hints(type(value))
    payload = {
        item.name: _convert(hints[item.name], getattr(value, item.name), decode=False)
        for item in fields(value)
    }
    _semantic(value)
    return payload


def repository_preparation_value_from_payload[T: _Value](
    root: type[T], payload: Any
) -> T:
    if not _root_type(root) or type(payload) is not dict:
        raise RepositoryPreparationValueError("authored_payload_required")
    if set(payload) != {item.name for item in fields(root)}:
        raise RepositoryPreparationValueError("exact_fields_required")
    hints = get_type_hints(root)
    value = root(
        **{
            name: _convert(hints[name], item, decode=True)
            for name, item in payload.items()
        }
    )
    _semantic(value)
    return value


def detached[T: _Value](value: T) -> T:
    return repository_preparation_value_from_payload(
        type(value), repository_preparation_value_to_payload(value)
    )


def repository_preparation_value_to_json(value: Any) -> str:
    return json.dumps(
        repository_preparation_value_to_payload(value),
        sort_keys=True,
        separators=(",", ":"),
    )


def repository_preparation_value_from_json[T: _Value](root: type[T], source: str) -> T:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, item in items:
            if key in result:
                raise RepositoryPreparationValueError("duplicate_json_key")
            result[key] = item
        return result

    def constant(_value: str):
        raise RepositoryPreparationValueError("nonfinite_json_refused")

    return repository_preparation_value_from_payload(
        root, json.loads(source, object_pairs_hook=pairs, parse_constant=constant)
    )
