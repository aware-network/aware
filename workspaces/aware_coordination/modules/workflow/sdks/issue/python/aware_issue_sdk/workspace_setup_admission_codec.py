"""Original Issue A1 codecs; portable values never recover issuer authority."""

from __future__ import annotations

import hashlib
import json
from types import MemberDescriptorType
from typing import Any, cast

from aware_workspace_sdk import architecture_setup_admission_codec as workspace
from aware_workspace_sdk import architecture_setup_admission_values as w

from . import workspace_setup_admission_values as v


class IssueWorkspaceSetupValueError(ValueError):
    pass


_DEFINITIONS = {
    id(cls): (
        cls,
        tuple(
            (name, vars(cls)[name], kind)
            for name, kind in v.ISSUE_SETUP_FIELD_TYPES[cls]
        ),
    )
    for cls in v.ISSUE_SETUP_VALUE_TYPES
}
_NAMES = {cls.__name__: cls for cls in v.ISSUE_SETUP_VALUE_TYPES}
_SCHEMAS = dict(v.ISSUE_SETUP_WIRE_IDS)
_WS_NAMES = {cls.__name__: cls for cls in w.SETUP_VALUE_TYPES}
_GET = MemberDescriptorType.__get__
_SET = MemberDescriptorType.__set__
_NEW = object.__new__


def _fields(cls):
    row = _DEFINITIONS.get(id(cls))
    if row is None or row[0] is not cls:
        raise IssueWorkspaceSetupValueError("original_issue_setup_value_required")
    if any(vars(cls).get(name) is not slot for name, slot, _ in row[1]):
        raise IssueWorkspaceSetupValueError("issue_setup_original_slot_changed")
    return row[1]


def _convert(kind, value, path, decode, depth, budget):
    budget.visit(depth, path)
    if depth > 64:
        raise IssueWorkspaceSetupValueError("issue_setup_depth_limit")
    if kind.startswith("Nullable["):
        if value is None:
            budget.charge(4, path)
        return (
            None
            if value is None
            else _convert(kind[9:-1], value, path, decode, depth + 1, budget)
        )
    if kind.startswith("Array["):
        if type(value) is not (list if decode else tuple) or len(value) > 16384:
            raise IssueWorkspaceSetupValueError("issue_setup_array_limit")
        if path.endswith(".diagnostics") and len(value) > 8:
            raise IssueWorkspaceSetupValueError("issue_setup_diagnostic_limit")
        budget.charge(2 + max(0, len(value) - 1), path)
        result = [
            _convert(kind[6:-1], item, path, decode, depth + 1, budget)
            for item in value
        ]
        return tuple(result) if decode else result
    if kind in _NAMES:
        return _record(_NAMES[kind], value, path, decode, depth + 1, budget)
    if kind in _WS_NAMES:
        return workspace._record(
            _WS_NAMES[kind], value, path, budget, depth + 1, decode
        )
    if kind in v.ISSUE_SETUP_ENUMS:
        if type(value) is not str or value not in v.ISSUE_SETUP_ENUMS[kind]:
            raise IssueWorkspaceSetupValueError("issue_setup_enum_invalid")
        budget.charge(len(json.dumps(value, ensure_ascii=False).encode("utf-8")), path)
        return value
    result = workspace._scalar(kind, value, path)
    budget.charge(
        len(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
        ),
        path,
    )
    return result


def _record(cls, value, path, decode, depth, budget):
    rows = _fields(cls)
    skeleton = {"contract": _SCHEMAS[cls], "value": {name: None for name, _, _ in rows}}
    budget.charge(
        len(
            json.dumps(
                skeleton, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        )
        - 4 * len(rows),
        path,
    )
    if decode:
        if (
            type(value) is not dict
            or any(type(key) is not str for key in value)
            or set(value) != {"contract", "value"}
            or type(value["contract"]) is not str
            or value["contract"] != _SCHEMAS[cls]
        ):
            raise IssueWorkspaceSetupValueError("issue_setup_closed_wrapper_required")
        source = value["value"]
        if (
            type(source) is not dict
            or any(type(key) is not str for key in source)
            or set(source) != {name for name, _, _ in rows}
        ):
            raise IssueWorkspaceSetupValueError("issue_setup_closed_fields_required")
        result = {
            name: _convert(
                kind, source[name], path + "." + name, True, depth + 1, budget
            )
            for name, _, kind in rows
        }
    else:
        if type(value) is not cls:
            raise IssueWorkspaceSetupValueError("original_issue_setup_value_required")
        result = {
            name: _convert(
                kind,
                _GET(slot, value, cls),
                path + "." + name,
                False,
                depth + 1,
                budget,
            )
            for name, slot, kind in rows
        }
    if cls is v.IssueWorkspaceSetupRequest and (
        (result["actor_ref"] is None) != (result["actor_evidence_ref"] is None)
    ):
        raise IssueWorkspaceSetupValueError("issue_setup_actor_metadata_pair_required")
    _fields(cls)
    if decode:
        instance = _NEW(cls)
        for name, slot, _ in rows:
            _SET(slot, instance, result[name])
        return instance
    return {"contract": _SCHEMAS[cls], "value": result}


def issue_setup_value_to_payload(value: object) -> dict[str, Any]:
    _fields(type(value))
    payload: Any = _record(
        type(value), value, type(value).__name__, False, 0, workspace._Budget(4194304)
    )
    _wire(payload)
    return payload


def _wire(payload):
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if len(encoded.encode("utf-8")) > 4194304:
        raise IssueWorkspaceSetupValueError("issue_setup_metadata_limit")
    return encoded


def issue_setup_value_to_json(value: object) -> str:
    return _wire(issue_setup_value_to_payload(value))


def issue_setup_value_digest(value: object) -> str:
    return (
        "sha256:"
        + hashlib.sha256(issue_setup_value_to_json(value).encode()).hexdigest()
    )


def issue_setup_value_from_payload[T](value_type: type[T], payload: object) -> T:
    _fields(value_type)
    value = _record(
        value_type, payload, value_type.__name__, True, 0, workspace._Budget(4194304)
    )
    issue_setup_value_to_payload(value)
    return cast(T, value)


def issue_setup_value_from_json[T](value_type: type[T], source: object) -> T:
    _fields(value_type)
    text = workspace._text(source, "issue_setup_json", 4194304)
    try:
        payload = json.loads(
            text, object_pairs_hook=workspace._pairs, parse_constant=workspace._constant
        )
    except (ValueError, RecursionError) as error:
        raise IssueWorkspaceSetupValueError("issue_setup_json_invalid") from error
    return issue_setup_value_from_payload(value_type, payload)
