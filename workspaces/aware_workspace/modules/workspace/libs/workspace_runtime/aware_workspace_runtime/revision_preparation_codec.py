"""Strict canonical JSON primitives for Workspace revision preparation."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Never, cast


class WorkspaceRevisionPreparationContractError(ValueError):
    """Raised when revision-preparation authority is malformed or mismatched."""


def _reject_number(_value: str) -> Never:
    raise WorkspaceRevisionPreparationContractError(
        "revision preparation JSON contains an unsupported number"
    )


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if type(key) is not str:
            raise TypeError("revision preparation JSON key must be exact str")
        if key in result:
            raise WorkspaceRevisionPreparationContractError(
                "revision preparation JSON contains a duplicate key"
            )
        result[key] = value
    return result


def validate_revision_preparation_json(value: object, path: str = "wire") -> object:
    """Return a recursively copied exact JSON value, excluding floats."""

    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is list:
        return [
            validate_revision_preparation_json(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if type(value) is dict:
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f"{path} key must be exact str")
            result[key] = validate_revision_preparation_json(item, f"{path}.{key}")
        return result
    raise TypeError(f"{path} contains unsupported exact type {type(value).__name__}")


def canonical_revision_preparation_json_bytes(value: object) -> bytes:
    admitted = validate_revision_preparation_json(value)
    return json.dumps(
        admitted,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def decode_revision_preparation_json_object(value: bytes) -> dict[str, object]:
    if type(value) is not bytes or not value:
        raise TypeError("revision preparation canonical body must be exact bytes")
    try:
        decoded = json.loads(
            value.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise WorkspaceRevisionPreparationContractError(
            "revision preparation body is not strict JSON"
        ) from error
    if type(decoded) is not dict:
        raise WorkspaceRevisionPreparationContractError(
            "revision preparation body must be an object"
        )
    result = cast(dict[str, object], decoded)
    if canonical_revision_preparation_json_bytes(result) != value:
        raise WorkspaceRevisionPreparationContractError(
            "revision preparation body is not canonical"
        )
    return result


def require_exact_keys(
    value: object, expected: frozenset[str], path: str
) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{path} must be exact dict")
    result = cast(dict[object, object], value)
    if any(type(key) is not str for key in result):
        raise TypeError(f"{path} keys must be exact str")
    if frozenset(cast(dict[str, object], result)) != expected:
        raise WorkspaceRevisionPreparationContractError(f"{path} fields are not exact")
    return cast(dict[str, object], result)


def _measure_revision_preparation_encoding(
    operation: Callable[[], bytes],
) -> tuple[bytes, int]:
    """Run one encoder and count every byte emitted by that runtime operation."""

    body = operation()
    if type(body) is not bytes:
        raise TypeError("measured revision preparation body must be exact bytes")
    bytes_encoded = 0
    for _byte in body:
        bytes_encoded += 1
    return body, bytes_encoded


def _measure_revision_preparation_decoding[T](
    body: bytes, operation: Callable[[bytes], T]
) -> tuple[T, int]:
    """Run one decoder and count every byte supplied to that runtime operation."""

    if type(body) is not bytes:
        raise TypeError("measured revision preparation body must be exact bytes")
    bytes_decoded = 0
    for _byte in body:
        bytes_decoded += 1
    return operation(body), bytes_decoded


__all__ = [
    "WorkspaceRevisionPreparationContractError",
    "canonical_revision_preparation_json_bytes",
    "decode_revision_preparation_json_object",
    "require_exact_keys",
    "validate_revision_preparation_json",
]
