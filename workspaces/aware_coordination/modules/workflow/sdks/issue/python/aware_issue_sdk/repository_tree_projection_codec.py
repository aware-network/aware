"""Closed descriptive tree codecs; no IO, provider discovery or authority minting."""

from __future__ import annotations

import json
import re
import types
import unicodedata
from dataclasses import fields
from typing import Literal, NoReturn, get_args, get_origin, get_type_hints

from . import repository_tree_projection_values as values

MAXIMUM_METADATA_BYTES = 8 * 1024 * 1024
MAXIMUM_PATH_BYTES = 1024
MAXIMUM_TRANSITIONS = 8192

_VALUE_TYPES = (
    values.IssueTreeProjectionRequest,
    values.IssueTreeBindingObservation,
    values.IssueTreeAdmissionObservation,
    values.IssueTreeResourceCleanup,
    values.IssueTreeAdmissionCleanup,
)
_HINTS = {record: get_type_hints(record) for record in _VALUE_TYPES}
_ASCII_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_BAD_PATH_COMPONENT = re.compile(r"(?:^|/)\.{0,2}(?:/|$)")
_SCHEMA_IDS = {
    values.IssueTreeProjectionRequest: "aware.issue.tree-projection-request.v1",
    values.IssueTreeBindingObservation: "aware.issue.tree-binding-observation.v1",
    values.IssueTreeAdmissionObservation: "aware.issue.tree-admission-observation.v1",
    values.IssueTreeResourceCleanup: "aware.issue.tree-resource-cleanup.v1",
    values.IssueTreeAdmissionCleanup: "aware.issue.tree-admission-cleanup.v1",
}


class IssueTreeProjectionValueError(ValueError):
    """Malformed descriptive input, before any owner is selected or invoked."""


def _refuse(path: str, reason: str) -> NoReturn:
    raise IssueTreeProjectionValueError(f"{path}: {reason}")


def tree_projection_value_schema_id(value_type: type) -> str:
    for record in _VALUE_TYPES:
        if value_type is record:
            return _SCHEMA_IDS[record]
    _refuse("value_type", "not a descriptive Issue tree value")


def _text(value: str, path: str) -> None:
    # ASCII is already NFC and its character count is its UTF-8 byte count.
    # Keep all exact text predicates; the scan runs in the regex engine rather
    # than allocating a Python generator for every path at every checkpoint.
    if value.isascii():
        if (
            not value
            or value.strip() != value
            or len(value) > MAXIMUM_PATH_BYTES
            or _ASCII_CONTROL.search(value) is not None
        ):
            _refuse(path, "expected bounded exact NFC non-control text")
        return
    try:
        encoded = value.encode("utf-8")
    except UnicodeError as error:
        raise IssueTreeProjectionValueError(f"{path}: invalid UTF-8 text") from error
    if (
        not value
        or value.strip() != value
        or len(encoded) > MAXIMUM_PATH_BYTES
        or unicodedata.normalize("NFC", value) != value
        or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value)
    ):
        _refuse(path, "expected bounded exact NFC non-control text")


def _path(value: str, path: str) -> None:
    _text(value, path)
    if "\\" in value or _BAD_PATH_COMPONENT.search(value) is not None:
        _refuse(path, "expected canonical repository-relative path")


def _digest(value: str, path: str) -> None:
    if (
        len(value) != 71
        or not value.startswith("sha256:")
        or any(char not in "0123456789abcdef" for char in value[7:])
    ):
        _refuse(path, "expected exact sha256-prefixed digest")


def _validate_fields(record: type, result: dict, path: str) -> None:
    for name in ("expected_issue_source_sha256", "transition_sequence_digest"):
        if name in result:
            _digest(result[name], f"{path}.{name}")
    if (
        "authority_source_digest" in result
        and result["authority_source_digest"] is not None
    ):
        _digest(result["authority_source_digest"], path + ".authority_source_digest")
    for name in ("authority_source_path", "path"):
        if name in result and result[name] is not None:
            _path(result[name], f"{path}.{name}")
    for name in ("effect_paths", "read_guard_paths", "scratch_effect_paths"):
        if name in result:
            collection = result[name]
            if len(collection) != len(set(collection)):
                _refuse(f"{path}.{name}", "duplicate path")
            for member in collection:
                _path(member, f"{path}.{name}")
    if record is values.IssueTreeProjectionRequest:
        if result["operation_ref"] != values.ISSUE_TREE_PROJECTION_OPERATION_REF:
            _refuse(path, "unsupported tree operation purpose")
        if result["profile"] != values.ISSUE_TREE_PROJECTION_PROFILE:
            _refuse(path, "unsupported tree admission profile")
    if (
        record is values.IssueTreeBindingObservation
        and not 0 <= result["transition_count"] <= MAXIMUM_TRANSITIONS
    ):
        _refuse(path, "transition count exceeds complete file/ancestor ceiling")


def _convert(annotation: object, value: object, path: str, *, decode: bool):
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        if value is None and type(None) in args:
            return None
        return _convert(
            next(arg for arg in args if arg is not type(None)),
            value,
            path,
            decode=decode,
        )
    if origin is Literal:
        if not any(type(value) is type(choice) and value == choice for choice in args):
            _refuse(path, "unsupported authored literal")
        return value
    if annotation in (str, int, bool):
        if type(value) is not annotation:
            _refuse(path, "incorrect primitive type")
        if annotation is str:
            _text(value, path)
        if annotation is int and (value < 0 or value.bit_length() > 64):
            _refuse(path, "expected bounded nonnegative integer")
        return value
    if origin is tuple:
        if type(value) is not (list if decode else tuple):
            _refuse(path, "incorrect ordered collection type")
        if len(value) > MAXIMUM_METADATA_BYTES // 2:
            _refuse(path, "collection cannot fit metadata ceiling")
        if args[-1] is not Ellipsis and len(value) != len(args):
            _refuse(path, "incorrect fixed tuple length")
        result = [
            _convert(
                args[0] if args[-1] is Ellipsis else args[index],
                item,
                f"{path}[{index}]",
                decode=decode,
            )
            for index, item in enumerate(value)
        ]
        return tuple(result) if decode else result
    for record in _VALUE_TYPES:
        if annotation is record:
            return _record(record, value, path, decode=decode)
    _refuse(path, "not an authored descriptive type")


def _record(record: type, value: object, path: str, *, decode: bool):
    definitions = fields(record)
    if decode:
        if (
            type(value) is not dict
            or any(type(key) is not str for key in value)
            or set(value) != {field.name for field in definitions}
        ):
            _refuse(path, "expected exactly the authored fields, including nulls")
        source = value
    else:
        if type(value) is not record:
            _refuse(path, "expected the exact SDK descriptive value")
        try:
            source = {field.name: getattr(value, field.name) for field in definitions}
        except AttributeError as error:
            raise IssueTreeProjectionValueError(f"{path}: incomplete value") from error
    result = {
        field.name: _convert(
            _HINTS[record][field.name],
            source[field.name],
            f"{path}.{field.name}",
            decode=decode,
        )
        for field in definitions
    }
    _validate_fields(record, result, path)
    return record(**result) if decode else result


def _wire(payload: dict) -> str:
    source = json.dumps(
        payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    )
    if len(source.encode("utf-8")) > MAXIMUM_METADATA_BYTES:
        _refuse("value", "tree metadata ceiling exceeded")
    return source


def tree_projection_value_to_payload(value: object) -> dict:
    tree_projection_value_schema_id(type(value))
    _payload_budget(value, native=True)
    payload = _record(type(value), value, "value", decode=False)
    _wire(payload)
    return payload


def _tree_projection_value_clone(value: object):
    """Detach an owner observation after one complete, fresh producer check.

    The payload is created and validated here, including the logical budget
    and encoded byte ceiling. It never comes from a caller or previous call.
    Restore only that invocation-local payload, avoiding a second validation
    and JSON serialization of already checked descriptive primitives.
    """
    payload = tree_projection_value_to_payload(value)

    def restore(annotation, member):
        origin, args = get_origin(annotation), get_args(annotation)
        if origin is types.UnionType:
            if member is None:
                return None
            return restore(next(arg for arg in args if arg is not type(None)), member)
        if origin is tuple:
            return tuple(
                restore(args[0] if args[-1] is Ellipsis else args[index], item)
                for index, item in enumerate(member)
            )
        for record in _VALUE_TYPES:
            if annotation is record:
                return record(
                    **{
                        name: restore(hint, member[name])
                        for name, hint in _HINTS[record].items()
                    }
                )
        return member

    return restore(type(value), payload)


def tree_projection_value_from_payload[T](value_type: type[T], payload: object) -> T:
    tree_projection_value_schema_id(value_type)
    _payload_budget(payload)
    result = _record(value_type, payload, "value", decode=True)
    # Check the same encoded byte ceiling in both producer and consumer paths.
    _wire(_record(value_type, result, "value", decode=False))
    return result


def _payload_budget(payload: object, *, native: bool = False) -> None:
    """Bound native/decoded inputs before allocating detached collections."""
    remaining = MAXIMUM_METADATA_BYTES
    active: set[int] = set()

    def charge(size: int) -> None:
        nonlocal remaining
        remaining -= size
        if remaining < 0:
            _refuse("value", "tree metadata ceiling exceeded")

    def visit(value: object, depth: int) -> None:
        if depth > 16:
            _refuse("value", "nested payload limit exceeded")
        if value is None or type(value) in (bool, int, str):
            if type(value) is int and (value < 0 or value.bit_length() > 64):
                _refuse("value", "expected bounded nonnegative integer")
            if type(value) is str:
                _text(value, "value")
            charge(len(json.dumps(value, ensure_ascii=False).encode("utf-8")))
            return
        original_identity = id(value)
        if native and any(type(value) is record for record in _VALUE_TYPES):
            try:
                value = {
                    field.name: getattr(value, field.name)
                    for field in fields(type(value))
                }
            except AttributeError as error:
                raise IssueTreeProjectionValueError(
                    "value: incomplete value"
                ) from error
        allowed = (dict, list, tuple) if native else (dict, list)
        if type(value) not in allowed:
            _refuse("value", "non-JSON or nonfinite payload value")
        identity = original_identity
        if identity in active:
            _refuse("value", "cyclic payload")
        active.add(identity)
        try:
            charge(2 + max(0, len(value) - 1))
            if type(value) is dict:
                for key, member in value.items():
                    if type(key) is not str:
                        _refuse("value", "non-string field name")
                    visit(key, depth + 1)
                    charge(1)
                    visit(member, depth + 1)
            else:
                for member in value:
                    visit(member, depth + 1)
        finally:
            active.remove(identity)

    visit(payload, 0)


def tree_projection_value_to_json(value: object) -> str:
    return _wire(tree_projection_value_to_payload(value))


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _refuse("json", "duplicate field")
        result[key] = value
    return result


def _number(source: str) -> NoReturn:
    _refuse("json", "floating-point and nonfinite values are not authored")


def tree_projection_value_from_json[T](value_type: type[T], source: str) -> T:
    tree_projection_value_schema_id(value_type)
    if type(source) is not str:
        _refuse("json", "expected exact text")
    try:
        if len(source.encode("utf-8")) > MAXIMUM_METADATA_BYTES:
            _refuse("json", "tree metadata ceiling exceeded")
        payload = json.loads(
            source,
            object_pairs_hook=_object,
            parse_constant=_number,
            parse_float=_number,
        )
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, IssueTreeProjectionValueError):
            raise
        raise IssueTreeProjectionValueError("json: malformed input") from error
    return tree_projection_value_from_payload(value_type, payload)


__all__ = (
    "IssueTreeProjectionValueError",
    "tree_projection_value_from_json",
    "tree_projection_value_from_payload",
    "tree_projection_value_schema_id",
    "tree_projection_value_to_json",
    "tree_projection_value_to_payload",
)
