"""Strict detached codecs for descriptive source projection values only.

No provider resolution, admission reconstruction, operational policy or IO.
Required nulls and uncertainty remain data, not proof or cleanup permission.
"""

from __future__ import annotations

import json
import types
from dataclasses import fields
from typing import Literal, get_args, get_origin, get_type_hints

from .repository_source_projection_values import SOURCE_PROJECTION_VALUE_TYPES


class WorkspaceSourceProjectionValueError(ValueError):
    """Malformed descriptive evidence; no owner operation was dispatched."""


def _refuse(path: str, reason: str):
    raise WorkspaceSourceProjectionValueError(f"{path}: {reason}")


def _known(value_type: object) -> bool:
    return any(value_type is item for item in SOURCE_PROJECTION_VALUE_TYPES)


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
            _refuse(path, "expected the original descriptive SDK type")
        try:
            source = {field.name: getattr(value, field.name) for field in definitions}
        except AttributeError as error:
            raise WorkspaceSourceProjectionValueError(
                f"{path}: missing authored fields"
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
    if annotation in (str, int, bool):
        if type(value) is not annotation:
            _refuse(path, "incorrect primitive type")
        if annotation is str:
            try:
                value.encode("utf-8")
            except UnicodeError as error:
                raise WorkspaceSourceProjectionValueError(
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
    _refuse(path, "unsupported descriptive type")


def repository_source_projection_value_to_payload(value: object) -> dict[str, object]:
    """Validate original descriptive types and detach every collection."""
    if not _known(type(value)):
        _refuse("value", "not source projection evidence; handles cannot be encoded")
    return _record(type(value), value, "value", decode=False)


def repository_source_projection_value_from_payload[T](
    value_type: type[T], payload: object
) -> T:
    """Decode descriptive evidence only; never reconstruct an original handle."""
    if not _known(value_type):
        _refuse(
            "value_type", "not source projection evidence; handles cannot be decoded"
        )
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


def repository_source_projection_value_to_json(value: object) -> str:
    payload = repository_source_projection_value_to_payload(value)
    try:
        return json.dumps(
            payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
    except (ValueError, RecursionError) as error:
        raise WorkspaceSourceProjectionValueError("json: malformed evidence") from error


def repository_source_projection_value_from_json[T](
    value_type: type[T], source: str
) -> T:
    if not _known(value_type):
        _refuse(
            "value_type", "not source projection evidence; handles cannot be decoded"
        )
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
        if isinstance(error, WorkspaceSourceProjectionValueError):
            raise
        raise WorkspaceSourceProjectionValueError("json: malformed input") from error
    return repository_source_projection_value_from_payload(value_type, payload)


__all__ = (
    "WorkspaceSourceProjectionValueError",
    "repository_source_projection_value_from_json",
    "repository_source_projection_value_from_payload",
    "repository_source_projection_value_to_json",
    "repository_source_projection_value_to_payload",
)
