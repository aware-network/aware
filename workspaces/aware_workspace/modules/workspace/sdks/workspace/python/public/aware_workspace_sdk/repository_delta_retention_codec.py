"""Strict, detached codecs for the two descriptive retention roots only.

No owner selection, runtime imports, capability reconstruction or physical IO.
Required nulls, finite vocabularies and exact authored field order are retained.
"""

from __future__ import annotations

import json
import types
from dataclasses import fields
from typing import Literal, get_args, get_origin, get_type_hints

from .repository_delta_retention_values import (
    WorkspaceRepositoryDeltaRetentionObservation,
    WorkspaceRepositoryDeltaRetentionRefusalEvidence,
)

_VALUE_TYPES = (
    WorkspaceRepositoryDeltaRetentionObservation,
    WorkspaceRepositoryDeltaRetentionRefusalEvidence,
)


class WorkspaceDeltaRetentionValueError(ValueError):
    """Malformed descriptive data; no owner operation is dispatched."""


def _refuse(path: str, reason: str):
    raise WorkspaceDeltaRetentionValueError(f"{path}: {reason}")


def _known(value_type: object) -> bool:
    return any(value_type is item for item in _VALUE_TYPES)


def _record(value_type: type, value: object, path: str, *, decode: bool):
    definitions = fields(value_type)
    if decode:
        if (
            type(value) is not dict
            or any(type(key) is not str for key in value)
            or set(value) != {field.name for field in definitions}
        ):
            _refuse(path, "expected exactly the authored fields")
        source = value
    else:
        if type(value) is not value_type:
            _refuse(path, "expected the original SDK evidence type")
        try:
            source = {field.name: getattr(value, field.name) for field in definitions}
        except AttributeError as error:
            raise WorkspaceDeltaRetentionValueError(
                f"{path}: missing authored evidence fields"
            ) from error
    hints = get_type_hints(value_type)
    result = {
        field.name: _convert(
            hints[field.name], source[field.name], f"{path}.{field.name}", decode=decode
        )
        for field in definitions
    }
    return value_type(**result) if decode else result


def _convert(annotation: object, value: object, path: str, *, decode: bool):
    origin, arguments = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        if value is None and type(None) in arguments:
            return None
        selected = next(item for item in arguments if item is not type(None))
        return _convert(selected, value, path, decode=decode)
    if origin is Literal:
        if type(value) is not str or value not in arguments:
            _refuse(path, "unrecognized authored enum value")
        return value
    if annotation in (str, int):
        if type(value) is not annotation:
            _refuse(path, "incorrect primitive type")
        if annotation is str:
            try:
                value.encode("utf-8")
            except UnicodeError as error:
                raise WorkspaceDeltaRetentionValueError(
                    f"{path}: string is not UTF-8 encodable"
                ) from error
        return value
    if origin is tuple:
        if type(value) is not (list if decode else tuple):
            _refuse(path, "incorrect ordered collection type")
        items = [
            _convert(arguments[0], item, f"{path}[{index}]", decode=decode)
            for index, item in enumerate(value)
        ]
        return tuple(items) if decode else items
    if _known(annotation):
        return _record(annotation, value, path, decode=decode)
    _refuse(path, "unsupported evidence type")


def repository_delta_retention_value_to_payload(value: object) -> dict[str, object]:
    """Validate a known original value and detach its ordered collections."""
    if not _known(type(value)):
        _refuse("value", "not retention evidence; handles cannot be encoded")
    return _record(type(value), value, "value", decode=False)


def repository_delta_retention_value_from_payload[T](
    value_type: type[T], payload: object
) -> T:
    """Decode only an original descriptive type, never a live client or owner."""
    if not _known(value_type):
        _refuse("value_type", "not retention evidence; handles cannot be decoded")
    return _record(value_type, payload, "value", decode=True)


def _json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            _refuse("json", "duplicate field")
        result[key] = value
    return result


def _json_number(value: str):
    _refuse("json", "floating-point or nonfinite numbers are not authored values")


def repository_delta_retention_value_to_json(value: object) -> str:
    payload = repository_delta_retention_value_to_payload(value)
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (ValueError, RecursionError) as error:
        raise WorkspaceDeltaRetentionValueError(
            "json: evidence cannot be serialized"
        ) from error


def repository_delta_retention_value_from_json[T](
    value_type: type[T], source: str
) -> T:
    if not _known(value_type):
        _refuse("value_type", "not retention evidence; handles cannot be decoded")
    if type(source) is not str:
        _refuse("json", "expected text")
    try:
        payload = json.loads(
            source,
            object_pairs_hook=_json_object,
            parse_constant=_json_number,
            parse_float=_json_number,
        )
    except (ValueError, RecursionError) as error:
        if isinstance(error, WorkspaceDeltaRetentionValueError):
            raise
        raise WorkspaceDeltaRetentionValueError("json: malformed input") from error
    return repository_delta_retention_value_from_payload(value_type, payload)


__all__ = (
    "WorkspaceDeltaRetentionValueError",
    "repository_delta_retention_value_from_json",
    "repository_delta_retention_value_from_payload",
    "repository_delta_retention_value_to_json",
    "repository_delta_retention_value_to_payload",
)
