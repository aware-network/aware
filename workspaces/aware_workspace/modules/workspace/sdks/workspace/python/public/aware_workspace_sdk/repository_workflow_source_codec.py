"""Strict, bounded workflow evidence codec. No provider selection or IO."""

from __future__ import annotations

import json
import re
import types
import unicodedata
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

from .repository_workflow_source_values import (
    MAX_WORKFLOW_SOURCE_BYTES,
    MAX_WORKFLOW_SOURCE_FILES,
    MAX_WORKFLOW_SOURCE_METADATA_BYTES,
    WORKFLOW_SOURCE_VALUE_TYPES,
)

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
    for cls in WORKFLOW_SOURCE_VALUE_TYPES
)


class WorkspaceWorkflowSourceValueError(ValueError):
    pass


def _refuse(reason: str) -> NoReturn:
    raise WorkspaceWorkflowSourceValueError(reason)


def _known(value_type: object) -> bool:
    return any(value_type is item for item in WORKFLOW_SOURCE_VALUE_TYPES)


def _convert(annotation: Any, value: Any, *, decode: bool, depth: int = 0) -> Any:
    if depth > 16:
        _refuse("workflow nesting exceeds bound")
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
        if type(value) not in (str, int) or not any(
            type(value) is type(item) and value == item for item in args
        ):
            _refuse("unknown workflow enum")
        return value
    if origin is tuple:
        if type(value) is not (list if decode else tuple):
            _refuse("workflow ordered collection type differs")
        collection = cast(list[Any] | tuple[Any, ...], value)
        if len(collection) > MAX_WORKFLOW_SOURCE_FILES:
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
        if not decode:
            return result
        decoded = object.__new__(annotation)
        for name, descriptor, _ in definitions:
            descriptor.__set__(decoded, result[name])
        return decoded
    _refuse("unsupported workflow descriptive type")


def _wire(payload: Any, *, limit: int = MAX_WORKFLOW_SOURCE_METADATA_BYTES) -> str:
    try:
        text = json.dumps(
            payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
    except (ValueError, RecursionError):
        _refuse("malformed workflow JSON")
    if len(text.encode("utf-8")) > limit:
        _refuse("workflow record exceeds byte bound")
    return text


def repository_workflow_source_value_to_payload(value: object) -> dict[str, Any]:
    if not _known(type(value)):
        _refuse("native bodies and live handles cannot be encoded")
    result = _convert(type(value), value, decode=False)
    _wire(result, limit=MAX_WORKFLOW_SOURCE_METADATA_BYTES)
    _validate(result)
    return result


def repository_workflow_source_value_clone[T](value: T) -> T:
    # This payload is newly constructed by the closed traversal, never borrowed
    # from a caller. Replaying public from_payload would redundantly encode it.
    payload = repository_workflow_source_value_to_payload(value)
    return cast(T, _convert(type(value), payload, decode=True))


def repository_workflow_source_value_from_payload[T](
    value_type: type[T], payload: object
) -> T:
    if not _known(value_type):
        _refuse("unknown source metadata type")
    result = _convert(value_type, payload, decode=True)
    repository_workflow_source_value_to_payload(result)
    return cast(T, result)


def repository_workflow_source_value_to_json(value: object) -> str:
    return _wire(
        repository_workflow_source_value_to_payload(value),
        limit=MAX_WORKFLOW_SOURCE_METADATA_BYTES,
    )


def repository_workflow_source_value_from_json[T](value_type: type[T], text: str) -> T:
    if (
        type(text) is not str
        or len(text.encode("utf-8")) > MAX_WORKFLOW_SOURCE_METADATA_BYTES
    ):
        _refuse("source metadata byte bound exceeded")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                _refuse("duplicate source metadata field")
            result[key] = value
        return result

    try:
        payload = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=lambda _: _refuse("nonfinite source metadata"),
        )
    except (ValueError, RecursionError, UnicodeError) as error:
        raise WorkspaceWorkflowSourceValueError(
            "malformed source metadata JSON"
        ) from error
    return repository_workflow_source_value_from_payload(value_type, payload)


def _validate(payload: dict[str, Any]) -> None:
    for key in ("source_repository_root", "target_repository_root"):
        if key in payload:
            path = payload[key]
            if (
                not path.startswith("/")
                or "\\" in path
                or "\0" in path
                or (
                    path != "/"
                    and any(part in ("", ".", "..") for part in path[1:].split("/"))
                )
            ):
                _refuse("invalid source repository root")
    for key in ("source_path", "output_path"):
        if key in payload:
            path = payload[key]
            if (
                not path
                or len(path.encode()) > 4096
                or "\\" in path
                or "\0" in path
                or unicodedata.normalize("NFC", path) != path
                or any(
                    part in ("", ".", "..") or len(part.encode()) > 255
                    for part in path.split("/")
                )
            ):
                _refuse("invalid source path")
    for key in (
        "content_digest",
        "profile_digest",
        "selection_digest",
        "output_layout_digest",
        "binding_ref",
        "delivery_ref",
        "source_repository_binding_ref",
        "target_repository_binding_ref",
    ):
        if key in payload and not re.fullmatch(r"sha256:[0-9a-f]{64}", payload[key]):
            _refuse("invalid source digest")
    for key in ("source_commit", "expected_target_head"):
        if payload.get(key) is not None and not re.fullmatch(
            r"(?:[0-9a-f]{40}|[0-9a-f]{64})", payload[key]
        ):
            _refuse("invalid source commit")
    if "git_mode" in payload:
        if payload["projected_mode"] != (
            493 if payload["git_mode"] == "100755" else 420
        ):
            _refuse("source mode mapping differs")
        if payload["size_bytes"] > MAX_WORKFLOW_SOURCE_BYTES:
            _refuse("source body exceeds byte bound")
    if "marker_environment" in payload:
        markers = payload["marker_environment"]
        keys = [row["key"] for row in markers]
        if not keys or keys != sorted(set(keys)) or len(keys) > 64:
            _refuse("source marker set differs")
        if any(
            len(payload[key]) != 2
            for key in ("source_root_identity", "target_root_identity")
        ):
            _refuse("source root identity differs")
        if (
            payload["maximum_files"] != MAX_WORKFLOW_SOURCE_FILES
            or payload["maximum_body_bytes"] != MAX_WORKFLOW_SOURCE_BYTES
            or payload["captured_count"] > MAX_WORKFLOW_SOURCE_FILES
            or payload["projected_count"] > MAX_WORKFLOW_SOURCE_FILES
            or payload["captured_bytes"] > MAX_WORKFLOW_SOURCE_BYTES
        ):
            _refuse("source inventory bounds differ")
    if "files" in payload:
        binding = payload["binding"]
        files = payload["files"]
        paths = [row["output_path"] for row in files]
        if paths != sorted(set(paths)) or len(files) != binding["projected_count"]:
            _refuse("source inventory ordering differs")
    for item in payload.values():
        if type(item) is dict:
            _validate(cast(dict[str, Any], item))
        elif type(item) is list:
            for member in cast(list[Any], item):
                if type(member) is dict:
                    _validate(cast(dict[str, Any], member))
