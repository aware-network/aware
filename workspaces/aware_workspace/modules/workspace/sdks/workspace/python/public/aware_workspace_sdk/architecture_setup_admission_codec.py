"""Strict Workspace A1 metadata codecs; decoding never recreates a live owner."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from types import MappingProxyType, MemberDescriptorType
from typing import Any, NoReturn, cast

from . import architecture_setup_admission_values as v

MAX_WIRE_BYTES = 32 * 1024 * 1024
MAX_ARRAY_ITEMS = 16384
MAX_DEPTH = 64
MAX_NODES = 1048576
_GET = MemberDescriptorType.__get__
_SET = MemberDescriptorType.__set__
_NEW = object.__new__
_FIELDS = tuple(
    (cls, tuple((name, vars(cls)[name], kind) for name, kind in rows))
    for cls, rows in v.SETUP_FIELD_TYPES.items()
)
_TYPES = MappingProxyType({cls.__name__: cls for cls in v.SETUP_VALUE_TYPES})
_SCHEMAS = MappingProxyType(dict(v.SETUP_SCHEMA_IDS))
_ENUMS = MappingProxyType(dict(v.SETUP_ENUMS))
_CAPS = MappingProxyType(dict(v.WORKSPACE_SETUP_LIMIT_CAPS))
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_CODE = re.compile(r"[A-Za-z0-9_.:-]{1,256}\Z")


class WorkspaceSetupValueError(ValueError):
    """A bounded metadata refusal, with no execution or retry authority."""


def _refuse(path: str, code: str) -> NoReturn:
    raise WorkspaceSetupValueError(f"{path}:{code}")


def _definitions(cls: type):
    for original, rows in _FIELDS:
        if cls is original:
            for name, descriptor, _ in rows:
                if vars(original).get(name) is not descriptor:
                    _refuse(original.__name__, "original_slot_changed")
            return rows
    _refuse("type", "closed_workspace_value_required")


def _text(value: object, path: str, maximum: int) -> str:
    if type(value) is not str:
        _refuse(path, "exact_string_required")
    text = cast(str, value)
    # Refuse before encoding an unbounded caller-owned string.
    if len(text) > maximum:
        _refuse(path, "string_limit")
    try:
        length = len(text.encode("utf-8", "strict"))
    except UnicodeError:
        _refuse(path, "invalid_utf8")
    if length > maximum:
        _refuse(path, "string_limit")
    return text


def _location(value: object, path: str, *, absolute: bool, maximum: int) -> str:
    text = _text(value, path, maximum)
    if (
        not text
        or unicodedata.normalize("NFC", text) != text
        or any(ord(c) < 32 or ord(c) == 127 or c in "\\*?[]" for c in text)
        or text.startswith("/") != absolute
    ):
        _refuse(path, "canonical_path_required")
    parts = text[1:].split("/") if absolute else text.split("/")
    if absolute and text == "/":
        return text
    if any(p in ("", ".", "..") for p in parts):
        _refuse(path, "canonical_path_required")
    if not absolute and len(parts) > 64:
        _refuse(path, "path_component_limit")
    return text


def _scalar(kind: str, value: object, path: str):
    if kind in ("U64", "I64"):
        if type(value) is not int:
            _refuse(path, "exact_integer_required")
        low, high = (0, 2**64 - 1) if kind == "U64" else (-(2**63), 2**63 - 1)
        if not low <= cast(int, value) <= high:
            _refuse(path, "integer_range")
        return value
    if kind == "Bool":
        if type(value) is not bool:
            _refuse(path, "exact_boolean_required")
        return value
    if kind == "Identity":
        raise AssertionError("identity_is_not_scalar")
    if kind in _ENUMS:
        text = _text(value, path, 256)
        if text not in _ENUMS[kind]:
            _refuse(path, "unsupported_enum")
        return text
    if kind == "Digest":
        text = _text(value, path, 71)
        if _DIGEST.fullmatch(text) is None:
            _refuse(path, "sha256_digest_required")
        return text
    if kind == "RelativePath":
        return _location(value, path, absolute=False, maximum=1024)
    if kind == "RootPath":
        return _location(value, path, absolute=True, maximum=4096)
    if kind == "ResourcePath":
        text = _text(value, path, 4096)
        return _location(text, path, absolute=text.startswith("/"), maximum=4096)
    if kind == "Ref":
        text = _text(value, path, 512)
        if (
            not text.strip()
            or text.strip() != text
            or unicodedata.normalize("NFC", text) != text
            or any(ord(c) < 32 or ord(c) == 127 for c in text)
        ):
            _refuse(path, "canonical_ref_required")
        return text
    if kind == "Code":
        text = _text(value, path, 256)
        if _CODE.fullmatch(text) is None:
            _refuse(path, "symbolic_code_required")
        return text
    if kind in ("Diagnostic", "RequestText"):
        return _text(value, path, 256 if kind == "Diagnostic" else 8192)
    _refuse(path, "unknown_frozen_type")


class _Budget:
    def __init__(self, ceiling: int):
        self.nodes = 0
        self.resources = 0
        self.wire_bytes = 0
        self.ceiling = ceiling

    def charge(self, count: int, path: str):
        self.wire_bytes += count
        if self.wire_bytes > self.ceiling:
            _refuse(path, "encoded_byte_limit")

    def visit(self, depth: int, path: str):
        self.nodes += 1
        if depth > MAX_DEPTH or self.nodes > MAX_NODES:
            _refuse(path, "metadata_structure_limit")


def _convert(
    kind: str, value: object, path: str, budget: _Budget, depth: int, decode: bool
):
    budget.visit(depth, path)
    if kind.startswith("Nullable["):
        if value is None:
            budget.charge(4, path)
            return None
        return _convert(kind[9:-1], value, path, budget, depth + 1, decode)
    if kind.startswith("Array[") or kind == "Identity":
        expected = list if decode else tuple
        if type(value) is not expected:
            _refuse(path, "exact_array_required")
        items = cast(list[object] | tuple[object, ...], value)
        field_cap = {
            "diagnostics": 8,
            "dependencies": 256,
            "input_bindings": 4096,
            "ancestor_guards": 4096,
            "file_transitions": 1024,
            "ordered_effects": 12288,
        }.get(path.rsplit(".", 1)[-1], MAX_ARRAY_ITEMS)
        if len(items) > field_cap:
            _refuse(path, "array_limit")
        if kind == "Identity" and len(items) != 2:
            _refuse(path, "two_item_identity_required")
        inner = "U64" if kind == "Identity" else kind[6:-1]
        budget.charge(2 + max(0, len(items) - 1), path)
        result = [
            _convert(inner, item, f"{path}[{index}]", budget, depth + 1, decode)
            for index, item in enumerate(items)
        ]
        return tuple(result) if decode else result
    cls = _TYPES.get(kind)
    if cls is not None:
        return _record(cls, value, path, budget, depth + 1, decode)
    result = _scalar(kind, value, path)
    budget.charge(
        len(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
        ),
        path,
    )
    return result


def _invariants(cls: type, data: dict[str, Any], path: str, *, decode: bool):
    name = cls.__name__
    if name in ("WorkspaceSetupFileObservation", "WorkspaceSetupDirectoryObservation"):
        known = tuple(k for k in data if k != "state")
        if data["state"] == "not_observed" and any(data[k] is not None for k in known):
            _refuse(path, "invented_observation")
        if data["state"] == "observed":
            if data["exists"] is None:
                _refuse(path, "observed_existence_required")
            rest = tuple(k for k in known if k != "exists")
            if data["exists"] is False and any(data[k] is not None for k in rest):
                _refuse(path, "absence_has_no_identity")
            if data["exists"] is True and any(data[k] is None for k in rest):
                _refuse(path, "complete_present_observation_required")
        if data["mode"] is not None and data["mode"] > 0o177777:
            _refuse(path, "mode_range")
    elif name == "WorkspaceSetupPrimaryFailure":
        if data["state"] == "none" and (
            any(
                data[k] is not None
                for k in ("owner_ref", "stage", "code", "cause_type")
            )
            or data["interruption"]
        ):
            _refuse(path, "invented_primary_failure")
    elif name == "WorkspaceSetupLimits":
        for field, ceiling in _CAPS.items():
            if not 0 < data[field] <= ceiling:
                _refuse(path + "." + field, "frozen_limit_exceeded")
    elif name == "WorkspaceSetupScratchPolicy":
        if data["simultaneous_live_scratch"] != 1:
            _refuse(path, "one_live_scratch_required")
    if "diagnostics" in data and len(data["diagnostics"]) > 8:
        _refuse(path, "diagnostic_count_limit")
    if name == "ArchitectureSetupRequest" and len(data["dependencies"]) > 256:
        _refuse(path, "dependency_count_limit")
    if name in ("WorkspaceSetupPhysicalStep", "WorkspaceSetupPhysicalEffect"):
        for key in ("requested_mode", "observed_mode"):
            if key in data and data[key] is not None and data[key] > 0o7777:
                _refuse(path + "." + key, "permission_mode_range")
    if name == "WorkspaceSetupFileTransition":
        if data["candidate_size_bytes"] > _CAPS["file_bytes"]:
            _refuse(path, "file_byte_limit")
        if data["scratch_path"] == data["path"]:
            _refuse(path, "scratch_target_collision")
    if name == "WorkspaceSetupPlanBinding":
        # Native input was projected into wrappers; decoded input holds original
        # closed value instances. This helper only unwraps validated own values.
        def own_fields(value):
            if not decode:
                return value["value"]
            return {
                key: _GET(slot, value, type(value))
                for key, slot, _ in _definitions(type(value))
            }

        limits = own_fields(data["limits"])
        for field, cap in (
            ("input_bindings", "input_files"),
            ("file_transitions", "file_transitions"),
            ("ancestor_guards", "ancestor_guards"),
            ("ordered_effects", "physical_step_count"),
        ):
            if len(data[field]) > limits[cap]:
                _refuse(path + "." + field, "plan_count_limit")
        for field, ordinal in (
            ("file_transitions", "file_ordinal"),
            ("ordered_effects", "ordinal"),
        ):
            if [own_fields(row)[ordinal] for row in data[field]] != list(
                range(len(data[field]))
            ):
                _refuse(path + "." + field, "ordered_ordinals_required")
        for field in ("input_bindings", "file_transitions", "ancestor_guards"):
            paths = [own_fields(row)["path"] for row in data[field]]
            if len(set(paths)) != len(paths):
                _refuse(path + "." + field, "duplicate_plan_path")


def _record(
    cls: type, value: object, path: str, budget: _Budget, depth: int, decode: bool
) -> Any:
    budget.visit(depth, path)
    rows = _definitions(cls)
    # Charge wrappers, exact field names and punctuation before constructing a
    # record. Every repeated nested occurrence receives its own byte charge.
    envelope = {"contract": _SCHEMAS[cls], "value": {}}
    fixed_bytes = len(
        json.dumps(
            envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    )
    fixed_bytes += sum(len(json.dumps(key).encode("utf-8")) + 1 for key, _, _ in rows)
    budget.charge(fixed_bytes + max(0, len(rows) - 1), path)
    if cls is v.WorkspaceSetupResourceEvidence:
        budget.resources += 1
        if budget.resources > MAX_ARRAY_ITEMS:
            _refuse(path, "aggregate_resource_limit")
    if decode:
        if type(value) is not dict:
            _refuse(path, "exact_record_wrapper_required")
        wrapper = cast(dict[str, Any], value)
        if any(type(key) is not str for key in wrapper) or set(wrapper) != {
            "contract",
            "value",
        }:
            _refuse(path, "closed_record_wrapper_required")
        if type(wrapper["contract"]) is not str or wrapper["contract"] != _SCHEMAS[cls]:
            _refuse(path, "wrong_record_contract")
        source = wrapper["value"]
        if type(source) is not dict:
            _refuse(path, "exact_record_fields_required")
        if any(type(key) is not str for key in source) or set(source) != {
            key for key, _, _ in rows
        }:
            _refuse(path, "closed_record_fields_required")
        data = {
            key: _convert(kind, source[key], path + "." + key, budget, depth + 1, True)
            for key, _, kind in rows
        }
        _invariants(cls, data, path, decode=True)
        # Nested returns must not replace a constructor or member descriptor.
        rows = _definitions(cls)
        result = _NEW(cls)
        for key, slot, _ in rows:
            _SET(slot, result, data[key])
        return result
    if type(value) is not cls:
        _refuse(path, "original_value_type_required")
    data = {
        key: _convert(
            kind, _GET(slot, value, cls), path + "." + key, budget, depth + 1, False
        )
        for key, slot, kind in rows
    }
    _definitions(cls)
    _invariants(cls, data, path, decode=False)
    return {"contract": _SCHEMAS[cls], "value": data}


def _ceiling(cls: type) -> int:
    if cls is v.ArchitectureSetupRequest:
        return 65536
    if cls is v.WorkspaceSetupPlanBinding:
        return 2097152
    if cls is v.WorkspaceSetupPlanObservation:
        return 2097152
    if cls in (
        v.WorkspaceAuthorizedSetupResult,
        v.WorkspaceSetupCleanup,
        v.WorkspaceSetupClientCleanup,
    ):
        return 8388608
    return MAX_WIRE_BYTES


def _wire(payload: dict[str, Any], cls: type) -> str:
    text = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if len(text.encode("utf-8")) > _ceiling(cls):
        _refuse(cls.__name__, "encoded_byte_limit")
    return text


def setup_value_to_payload(value: object) -> dict[str, Any]:
    cls = type(value)
    _definitions(cls)
    budget = _Budget(_ceiling(cls))
    payload = _record(cls, value, cls.__name__, budget, 0, False)
    if len(_wire(payload, cls).encode("utf-8")) != budget.wire_bytes:
        _refuse(cls.__name__, "wire_accounting_mismatch")
    return payload


def setup_value_to_json(value: object) -> str:
    return _wire(setup_value_to_payload(value), type(value))


def setup_value_digest(value: object) -> str:
    return (
        "sha256:"
        + hashlib.sha256(setup_value_to_json(value).encode("utf-8")).hexdigest()
    )


def setup_value_from_payload[T](value_type: type[T], payload: object) -> T:
    _definitions(value_type)
    result = _record(
        value_type, payload, value_type.__name__, _Budget(_ceiling(value_type)), 0, True
    )
    # Re-encoding checks exact owner byte limits as well as repeated nested values.
    setup_value_to_payload(result)
    return cast(T, result)


def _pairs(rows: list[tuple[str, object]]) -> dict[str, Any]:
    result = {}
    for key, value in rows:
        if key in result:
            _refuse("json", "duplicate_key")
        result[key] = value
    return result


def _constant(_: str) -> NoReturn:
    _refuse("json", "nonfinite_number")


def setup_value_from_json[T](value_type: type[T], source: object) -> T:
    _definitions(value_type)
    text = _text(source, "json", _ceiling(value_type))
    if text.startswith("\ufeff"):
        _refuse("json", "bom_forbidden")
    try:
        payload = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, RecursionError) as error:
        if isinstance(error, WorkspaceSetupValueError):
            raise
        _refuse("json", "invalid_json")
    return setup_value_from_payload(value_type, payload)
