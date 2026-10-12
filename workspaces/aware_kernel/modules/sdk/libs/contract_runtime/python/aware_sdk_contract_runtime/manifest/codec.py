"""Strict canonical portable codec for complete SDK manifest meaning.

The codec carries parsed meaning only. It does not authenticate source bytes or
issue package membership, currentness, or publication authority.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from types import UnionType
from typing import Any, get_args, get_origin, get_type_hints

from .model import AwareSdkTomlSpec, validate_sdk_manifest_version

_MAX_BODY = 8_388_608
_TAG_V1 = "aware.sdk.manifest.meaning.v1"
_TAG_PROFILED = "aware.sdk.manifest.meaning.profiled.v1"


class SdkManifestMeaningCodecError(ValueError):
    """A meaning body is malformed or noncanonical."""


def _shape(value: object, expected: Any) -> object:
    origin = get_origin(expected)
    if origin is UnionType:
        if value is None and type(None) in get_args(expected):
            return None
        options = [item for item in get_args(expected) if item is not type(None)]
        if len(options) != 1:
            raise SdkManifestMeaningCodecError("unsupported union field")
        return _shape(value, options[0])
    if origin is list:
        if type(value) is not list:
            raise SdkManifestMeaningCodecError("manifest list field differs")
        (member,) = get_args(expected)
        return [_shape(item, member) for item in value]
    if expected in (str, int, bool):
        if type(value) is not expected:
            raise SdkManifestMeaningCodecError("manifest scalar field differs")
        return value
    if isinstance(expected, type) and issubclass(expected, Enum):
        if type(value) is expected:
            return value.value
        if type(value) is not str:
            raise SdkManifestMeaningCodecError("manifest enum field differs")
        try:
            return expected(value).value
        except ValueError as error:
            raise SdkManifestMeaningCodecError("manifest enum field differs") from error
    if not isinstance(expected, type) or not is_dataclass(expected):
        raise SdkManifestMeaningCodecError("unsupported manifest field")
    names = {field.name for field in fields(expected)}
    if type(value) is expected:
        source = {name: getattr(value, name) for name in names}
    elif type(value) is dict and set(value) == names:
        source = value
    else:
        raise SdkManifestMeaningCodecError("manifest model fields differ")
    hints = get_type_hints(expected)
    return {
        field.name: _shape(source[field.name], hints[field.name])
        for field in fields(expected)
    }


def _construct(value: object, expected: Any) -> object:
    origin = get_origin(expected)
    if origin is UnionType:
        if value is None and type(None) in get_args(expected):
            return None
        options = [item for item in get_args(expected) if item is not type(None)]
        if len(options) != 1:
            raise SdkManifestMeaningCodecError("unsupported union field")
        return _construct(value, options[0])
    if origin is list:
        if type(value) is not list:
            raise SdkManifestMeaningCodecError("manifest list field differs")
        (member,) = get_args(expected)
        return [_construct(item, member) for item in value]
    if expected in (str, int, bool):
        if type(value) is not expected:
            raise SdkManifestMeaningCodecError("manifest scalar field differs")
        return value
    if isinstance(expected, type) and issubclass(expected, Enum):
        if type(value) is not str:
            raise SdkManifestMeaningCodecError("manifest enum field differs")
        try:
            return expected(value)
        except ValueError as error:
            raise SdkManifestMeaningCodecError("manifest enum field differs") from error
    if not isinstance(expected, type) or not is_dataclass(expected):
        raise SdkManifestMeaningCodecError("unsupported manifest field")
    names = {field.name for field in fields(expected)}
    if type(value) is not dict or set(value) != names:
        raise SdkManifestMeaningCodecError("manifest model fields differ")
    hints = get_type_hints(expected)
    return expected(
        **{
            field.name: _construct(value[field.name], hints[field.name])
            for field in fields(expected)
        }
    )


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise SdkManifestMeaningCodecError("duplicate manifest JSON key")
        result[key] = value
    return result


def encode_sdk_manifest_meaning(value: AwareSdkTomlSpec) -> bytes:
    if type(value) is not AwareSdkTomlSpec:
        raise TypeError("exact SDK manifest meaning required")
    try:
        validate_sdk_manifest_version(value)
    except ValueError as error:
        raise SdkManifestMeaningCodecError(str(error)) from error
    meaning = _shape(value, AwareSdkTomlSpec)
    assert type(meaning) is dict
    tag = _TAG_PROFILED if value.generation_profiles else _TAG_V1
    if not value.generation_profiles:
        # Preserve every historical unprofiled wire byte, not just its meaning.
        del meaning["generation_profiles"]
    body = json.dumps(
        {"format": tag, "meaning": meaning},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    if len(body) > _MAX_BODY:
        raise SdkManifestMeaningCodecError("manifest meaning exceeds bound")
    return body


def decode_sdk_manifest_meaning(body: bytes) -> AwareSdkTomlSpec:
    if type(body) is not bytes or not 0 < len(body) <= _MAX_BODY:
        raise SdkManifestMeaningCodecError("bounded exact manifest bytes required")
    try:
        raw = json.loads(body.decode("utf-8"), object_pairs_hook=_pairs)
    except SdkManifestMeaningCodecError:
        raise
    except (UnicodeError, ValueError) as error:
        raise SdkManifestMeaningCodecError("invalid manifest meaning JSON") from error
    if (
        type(raw) is not dict
        or set(raw) != {"format", "meaning"}
        or raw["format"] not in (_TAG_V1, _TAG_PROFILED)
    ):
        raise SdkManifestMeaningCodecError("manifest meaning envelope differs")
    meaning = raw["meaning"]
    if type(meaning) is not dict or "definition" in meaning:
        raise SdkManifestMeaningCodecError("manifest meaning fields differ")
    if raw["format"] == _TAG_V1:
        if "generation_profiles" in meaning:
            raise SdkManifestMeaningCodecError("legacy meaning cannot carry profiles")
        meaning = {**meaning, "generation_profiles": []}
    elif (
        type(meaning.get("generation_profiles")) is not list
        or not meaning["generation_profiles"]
    ):
        raise SdkManifestMeaningCodecError(
            "profiled meaning requires generation profiles"
        )
    value = _construct(meaning, AwareSdkTomlSpec)
    if (
        type(value) is not AwareSdkTomlSpec
        or encode_sdk_manifest_meaning(value) != body
    ):
        raise SdkManifestMeaningCodecError("manifest meaning is not canonical")
    return value


__all__ = [
    "SdkManifestMeaningCodecError",
    "decode_sdk_manifest_meaning",
    "encode_sdk_manifest_meaning",
]
