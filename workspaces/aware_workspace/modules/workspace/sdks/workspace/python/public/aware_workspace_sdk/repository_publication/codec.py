"""Strict, detached codecs for the authored publication value slice only.

No provider lookup, authority reconstruction, Issue policy or physical IO.
Required fields stay required; explicit null and unknown states are preserved.
"""

from __future__ import annotations

import json
import types
import unicodedata
from dataclasses import fields
from typing import Literal, get_args, get_origin, get_type_hints

from .ports import PUBLICATION_PORT_VALUE_TYPES
from .values import PUBLICATION_VALUE_TYPES

_VALUE_TYPES = PUBLICATION_VALUE_TYPES + PUBLICATION_PORT_VALUE_TYPES


class WorkspacePublicationValueError(ValueError):
    """Malformed value; this refusal reports no operational effects."""


def _refuse(path: str, reason: str):
    raise WorkspacePublicationValueError(f"{path}: {reason}")


def _paths(value: tuple[str, ...], path: str) -> None:
    if value != tuple(sorted(set(value))):
        _refuse(path, "paths must be unique and sorted")
    for item in value:
        if (
            not item
            or item.startswith("/")
            or "\\" in item
            or any(part in ("", ".", "..") for part in item.split("/"))
            or unicodedata.normalize("NFC", item) != item
            or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in item)
        ):
            _refuse(path, "noncanonical repository path")


def _record(annotation: type, value: object, path: str, *, decode: bool):
    definitions = fields(annotation)
    if decode:
        if type(value) is not dict or set(value) != {
            field.name for field in definitions
        }:
            _refuse(path, "expected exactly the authored fields")
        source = value
    else:
        if type(value) is not annotation:
            _refuse(path, "expected the original SDK value type")
        source = {field.name: getattr(value, field.name) for field in definitions}
    hints = get_type_hints(annotation)
    result = {
        field.name: _convert(
            hints[field.name], source[field.name], f"{path}.{field.name}", decode=decode
        )
        for field in definitions
    }
    if "target_paths" in result:
        _paths(tuple(result["target_paths"]), f"{path}.target_paths")
    return annotation(**result) if decode else result


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
            except UnicodeError:
                _refuse(path, "string is not UTF-8 encodable")
        return value
    if annotation == tuple[int, int]:
        if decode:
            if type(value) is not dict or set(value) != {"device", "inode"}:
                _refuse(path, "expected exact file identity fields")
            return (
                _convert(int, value["device"], path + ".device", decode=True),
                _convert(int, value["inode"], path + ".inode", decode=True),
            )
        if type(value) is not tuple or len(value) != 2:
            _refuse(path, "expected device/inode tuple")
        return {
            "device": _convert(int, value[0], path + ".device", decode=False),
            "inode": _convert(int, value[1], path + ".inode", decode=False),
        }
    if annotation == list[list[str]]:
        if type(value) is not list:
            _refuse(path, "expected ordered command list")
        result = []
        for index, command in enumerate(value):
            item_path = f"{path}[{index}]"
            if decode:
                if type(command) is not dict or set(command) != {"arguments"}:
                    _refuse(item_path, "expected exact command fields")
                result.append(
                    _convert(
                        list[str],
                        command["arguments"],
                        item_path + ".arguments",
                        decode=True,
                    )
                )
            else:
                result.append(
                    {
                        "arguments": _convert(
                            list[str], command, item_path + ".arguments", decode=False
                        )
                    }
                )
        return result
    if origin in (tuple, list):
        expected = list if decode or origin is list else tuple
        if type(value) is not expected:
            _refuse(path, "incorrect ordered collection type")
        items = [
            _convert(arguments[0], item, f"{path}[{index}]", decode=decode)
            for index, item in enumerate(value)
        ]
        return tuple(items) if decode and origin is tuple else items
    if any(annotation is item for item in _VALUE_TYPES):
        return _record(annotation, value, path, decode=decode)
    _refuse(path, "unsupported value type")


def repository_publication_value_to_payload(value: object) -> dict[str, object]:
    """Validate and encode one known SDK value, detaching every collection."""
    if not any(type(value) is item for item in _VALUE_TYPES):
        _refuse("value", "not a publication value; handles cannot be encoded")
    return _record(type(value), value, "value", decode=False)


def repository_publication_value_from_payload[T](
    value_type: type[T], payload: object
) -> T:
    """Decode only a selected original SDK type; values never restore authority."""
    if not any(value_type is item for item in _VALUE_TYPES):
        _refuse("value_type", "not a publication value; handles cannot be decoded")
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


def repository_publication_value_to_json(value: object) -> str:
    return json.dumps(
        repository_publication_value_to_payload(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )


def repository_publication_value_from_json[T](value_type: type[T], source: str) -> T:
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
        if isinstance(error, WorkspacePublicationValueError):
            raise
        raise WorkspacePublicationValueError("json: malformed input") from error
    return repository_publication_value_from_payload(value_type, payload)
