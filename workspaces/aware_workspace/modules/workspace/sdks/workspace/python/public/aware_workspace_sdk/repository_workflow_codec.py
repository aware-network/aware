"""Strict, bounded workflow evidence codec. No provider selection or IO."""

from __future__ import annotations

import json
import types
from dataclasses import fields
from typing import (
    Any,
    Literal,
    NoReturn,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from .repository_workflow_values import (
    WORKFLOW_VALUE_TYPES,
    WorkspaceRepositoryWorkflowAttemptObservation,
    WorkspaceRepositoryWorkflowEvidenceAppendRequest,
)

MAX_WORKFLOW_RECORD_BYTES = 1024 * 1024
MAX_WORKFLOW_RECORDS = 256
MAX_WORKFLOW_ATTEMPT_BYTES = MAX_WORKFLOW_RECORDS * MAX_WORKFLOW_RECORD_BYTES
_DEFINITIONS: tuple[
    tuple[type[Any], tuple[tuple[str, types.MemberDescriptorType, Any], ...]], ...
] = tuple(
    (
        cls,
        tuple(
            (
                field.name,
                cast(types.MemberDescriptorType, vars(cls)[field.name]),
                get_type_hints(cls)[field.name],
            )
            for field in fields(cls)
        ),
    )
    for cls in WORKFLOW_VALUE_TYPES
)


class WorkspaceWorkflowValueError(ValueError):
    pass


def _refuse(reason: str) -> NoReturn:
    raise WorkspaceWorkflowValueError(reason)


def _known(value_type: object) -> bool:
    return any(value_type is item for item in WORKFLOW_VALUE_TYPES)


def _convert(annotation: Any, value: Any, *, decode: bool, depth: int = 0) -> Any:
    if depth > 16:
        _refuse("workflow nesting exceeds bound")
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        if value is None and type(None) in args:
            return None
        return _convert(
            next(x for x in args if x is not type(None)),
            value,
            decode=decode,
            depth=depth + 1,
        )
    if origin is Literal:
        if type(value) is not str or value not in args:
            _refuse("unknown workflow enum")
        return value
    if annotation in (str, int, bool):
        if type(value) is not annotation:
            _refuse("workflow primitive type differs")
        if annotation is str:
            try:
                encoded = cast(str, value).encode("utf-8")
            except UnicodeError:
                _refuse("workflow text must be UTF-8")
            if len(encoded) > 16384:
                _refuse("workflow text exceeds bound")
        elif annotation is int and not 0 <= cast(int, value) <= 2**64:
            _refuse("workflow integer exceeds bound")
        return value
    if origin is tuple:
        if type(value) is not (list if decode else tuple):
            _refuse("workflow ordered collection type differs")
        collection = cast(list[Any] | tuple[Any, ...], value)
        if len(collection) > 256:
            _refuse("workflow ordered collection type or bound differs")
        result = [
            _convert(args[0], item, decode=decode, depth=depth + 1)
            for item in collection
        ]
        return tuple(result) if decode else result
    if _known(annotation):
        definitions = next(items for cls, items in _DEFINITIONS if cls is annotation)
        if any(
            cast(dict[str, object], vars(annotation)).get(name) is not descriptor
            for name, descriptor, _ in definitions
        ):
            _refuse("workflow slot descriptor changed")
        if decode:
            if type(value) is not dict:
                _refuse("workflow record must be an exact object")
            source = cast(dict[str, Any], value)
            if any(type(k) is not str for k in source):
                _refuse("workflow record keys must be exact text")
            if set(source) != {name for name, _, _ in definitions}:
                _refuse("workflow fields differ")
        else:
            if type(value) is not annotation:
                _refuse("original descriptive workflow type required")
            try:
                source = {
                    name: descriptor.__get__(value, annotation)
                    for name, descriptor, _ in definitions
                }
            except AttributeError:
                _refuse("workflow fields missing")
        result = {
            name: _convert(hint, source[name], decode=decode, depth=depth + 1)
            for name, _, hint in definitions
        }
        # Collection-specific limits precede durable/effect dispatch.
        for key, limit in (
            ("artifact_bindings", 64),
            ("request_refs", 16),
            ("result_refs", 16),
            ("error_refs", 16),
            ("owner_observations", 16),
            ("original_evidence_refs", 16),
        ):
            if key in result and len(result[key]) > limit:
                _refuse("workflow evidence group exceeds bound")
        if (
            result.get("dispatch_state") == "not_dispatched"
            and result["effect_state"] != "none"
        ):
            _refuse("undispatched workflow cannot claim an effect")
        for key in (
            "expected_cursor",
            "prior_cursor",
            "observed_cursor",
            "last_verified_cursor",
        ):
            if result.get(key) is not None and result[key] > MAX_WORKFLOW_RECORDS:
                _refuse("workflow cursor exceeds attempt bound")
        if annotation is WorkspaceRepositoryWorkflowEvidenceAppendRequest:
            _wire(source if decode else result)
        if not decode:
            return result
        decoded = object.__new__(annotation)
        for name, descriptor, _ in definitions:
            descriptor.__set__(decoded, result[name])
        return decoded
    _refuse("unsupported workflow descriptive type")


def _wire(payload: Any, *, limit: int = MAX_WORKFLOW_RECORD_BYTES) -> str:
    try:
        text = json.dumps(
            payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
    except (ValueError, RecursionError):
        _refuse("malformed workflow JSON")
    if len(text.encode("utf-8")) > limit:
        _refuse("workflow record exceeds byte bound")
    return text


def _limit(value_type: object) -> int:
    return (
        MAX_WORKFLOW_ATTEMPT_BYTES
        if value_type is WorkspaceRepositoryWorkflowAttemptObservation
        else MAX_WORKFLOW_RECORD_BYTES
    )


def repository_workflow_value_to_payload(value: object) -> dict[str, Any]:
    if not _known(type(value)):
        _refuse("live handles and foreign values are not workflow evidence")
    result = _convert(type(value), value, decode=False)
    _wire(result, limit=_limit(type(value)))
    return result


def repository_workflow_value_from_payload[T](
    value_type: type[T], payload: object
) -> T:
    if not _known(value_type):
        _refuse("live handles and foreign types cannot be decoded")
    result = _convert(value_type, payload, decode=True)
    _wire(repository_workflow_value_to_payload(result), limit=_limit(value_type))
    return cast(T, result)


def repository_workflow_value_to_json(value: object) -> str:
    return _wire(repository_workflow_value_to_payload(value), limit=_limit(type(value)))


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _refuse("duplicate workflow JSON field")
        result[key] = value
    return result


def _number(_: str) -> NoReturn:
    _refuse("workflow floats and nonfinite numbers are forbidden")


def repository_workflow_value_from_json[T](value_type: type[T], text: str) -> T:
    if not _known(value_type):
        _refuse("live handles and foreign types cannot be decoded")
    if type(text) is not str:
        _refuse("workflow JSON requires exact text")
    try:
        if len(text.encode("utf-8")) > _limit(value_type):
            _refuse("workflow record exceeds byte bound")
        payload = json.loads(
            text, object_pairs_hook=_pairs, parse_float=_number, parse_constant=_number
        )
    except (ValueError, RecursionError, UnicodeError) as error:
        if type(error) is WorkspaceWorkflowValueError:
            raise
        _refuse("malformed workflow JSON")
    return repository_workflow_value_from_payload(value_type, payload)


__all__ = (
    "MAX_WORKFLOW_ATTEMPT_BYTES",
    "MAX_WORKFLOW_RECORDS",
    "MAX_WORKFLOW_RECORD_BYTES",
    "WorkspaceWorkflowValueError",
    "repository_workflow_value_from_json",
    "repository_workflow_value_from_payload",
    "repository_workflow_value_to_json",
    "repository_workflow_value_to_payload",
)
