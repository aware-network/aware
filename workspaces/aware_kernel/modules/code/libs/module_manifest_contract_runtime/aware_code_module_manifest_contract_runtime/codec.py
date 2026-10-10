"""Strict canonical full-meaning transport; no source or admission authority."""

from __future__ import annotations

import json
import types
from dataclasses import fields, is_dataclass
from typing import cast, get_args, get_origin, get_type_hints

from .models import AwareModuleSpec

CONTRACT = "aware.code.module-manifest-meaning.v1"


class ModuleManifestMeaningError(ValueError):
    """Meaning has a foreign type, field set or noncanonical wire."""


def _convert(value: object, expected: object, *, decode: bool, aware: bool = False):
    if get_origin(expected) is types.UnionType:
        if value is None and type(None) in get_args(expected):
            return None
        for alternative in get_args(expected):
            if alternative is not type(None):
                return _convert(value, alternative, decode=decode)
    if get_origin(expected) is tuple:
        if type(value) is not (list if decode else tuple):
            raise ModuleManifestMeaningError("exact meaning sequence required")
        items = [_convert(v, get_args(expected)[0], decode=decode) for v in value]
        return tuple(items) if decode else items
    if isinstance(expected, type) and is_dataclass(expected):
        schema = get_type_hints(expected)
        if decode:
            if type(value) is not dict or set(value) != set(schema):
                raise ModuleManifestMeaningError("meaning field set differs")
            return expected(**{
                key: _convert(value[key], kind, decode=True,
                              aware=expected is AwareModuleSpec and key == "aware")
                for key, kind in schema.items()
            })
        if type(value) is not expected:
            raise ModuleManifestMeaningError("exact meaning model required")
        return {
            f.name: _convert(getattr(value, f.name), schema[f.name], decode=False,
                             aware=expected is AwareModuleSpec and f.name == "aware")
            for f in fields(expected)
        }
    # Legacy grammar admits bool for aware through isinstance(value, int).
    if type(value) is not expected and not (aware and type(value) is bool):
        raise ModuleManifestMeaningError("meaning scalar type differs")
    return value


def encode_module_manifest_meaning(value: AwareModuleSpec) -> bytes:
    from .v3_models import AwareModuleSpecV3
    if type(value) is AwareModuleSpecV3:
        from .v3_codec import encode_module_manifest_meaning_v3
        return encode_module_manifest_meaning_v3(value)
    from .v2_models import AwareModuleSpecV2
    if type(value) is AwareModuleSpecV2:
        from .v2_codec import encode_module_manifest_meaning_v2
        return encode_module_manifest_meaning_v2(value)
    try:
        return json.dumps(
            {"contract": CONTRACT, "meaning": _convert(value, AwareModuleSpec, decode=False)},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, UnicodeError, RecursionError) as exc:
        raise ModuleManifestMeaningError("invalid module meaning") from exc


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ModuleManifestMeaningError("duplicate meaning key")
        result[key] = value
    return result


def decode_module_manifest_meaning(body: bytes) -> AwareModuleSpec:
    if type(body) is not bytes:
        raise ModuleManifestMeaningError("exact meaning bytes required")
    try:
        raw = json.loads(body.decode("utf-8"), object_pairs_hook=_pairs)
        if type(raw) is dict and raw.get("contract") == "aware.code.module-manifest-meaning.v3":
            from .v3_codec import decode_module_manifest_meaning_v3
            return decode_module_manifest_meaning_v3(body)
        if type(raw) is dict and raw.get("contract") == "aware.code.module-manifest-meaning.v2":
            from .v2_codec import decode_module_manifest_meaning_v2
            return decode_module_manifest_meaning_v2(body)
        if type(raw) is not dict or set(raw) != {"contract", "meaning"} or raw["contract"] != CONTRACT:
            raise ModuleManifestMeaningError("meaning envelope differs")
        value = cast(AwareModuleSpec, _convert(raw["meaning"], AwareModuleSpec, decode=True))
        if encode_module_manifest_meaning(value) != body:
            raise ModuleManifestMeaningError("noncanonical module meaning")
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise ModuleManifestMeaningError(str(exc)) from exc
