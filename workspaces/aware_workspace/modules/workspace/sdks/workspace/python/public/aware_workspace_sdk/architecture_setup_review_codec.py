"""Closed, bounded codecs for durable review data; decoded records grant no rights."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
from collections.abc import Callable
from types import MemberDescriptorType
from typing import Any, NoReturn, cast

from . import architecture_setup_review_values as v

MAX_RECORD_BYTES = 1_048_576
MAX_RECORD_DEPTH = 32
MAX_RECORD_NODES = 32_768
_GET = MemberDescriptorType.__get__
_SET = MemberDescriptorType.__set__
_NEW = object.__new__
# Capture the authored classes/slots once. Do not infer a type from a payload name.
_DEFS = {
    id(cls): (cls, tuple((key, vars(cls)[key], kind) for key, kind in rows))
    for cls, rows in v.REVIEW_FIELD_TYPES.items()
}
_NAMES = {cls.__name__: cls for cls in v.REVIEW_FIELD_TYPES}
_WIRES = dict(v.REVIEW_SCHEMA_IDS)
_ENUMS = dict(v.REVIEW_ENUMS)
_SCALARS: dict[str, dict[str, Any]] = {
    key: dict(value) for key, value in v.REVIEW_SCALARS.items()
}
_PRIVATE = frozenset(
    (
        "PrivateDirectoryBinding",
        "PrivateRootObservation",
        "PrivateDirectoryObservation",
        "PrivateSequenceBinding",
        "PrivateSequenceObservation",
        "PrivateSequenceStepResult",
        "PrivateSequenceCleanup",
        "PrivateDirectoryCleanup",
        "PrivateFileReadResult",
        "PrivateReadFailure",
        "PrivateDirectoryRefusalEvidence",
    )
)


class SetupReviewValueError(ValueError):
    """A malformed detached record, never a physical or admission outcome."""


def _refuse(reason) -> NoReturn:
    raise SetupReviewValueError(reason)


def _rows(cls):
    pair = _DEFS.get(id(cls))
    if pair is None or pair[0] is not cls or _WIRES.get(cls) is None:
        _refuse("serializable_original_review_type_required")
    if any(vars(cls).get(key) is not slot for key, slot, _ in pair[1]):
        _refuse("original_review_slot_changed")
    return pair[1]


def _wire(value):
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise SetupReviewValueError("invalid_review_json") from error


class _Budget:
    def __init__(self):
        self.wire_bytes = 0
        self.nodes = 0
        self.ceiling = MAX_RECORD_BYTES
        self.resources = 0

    def charge(self, count, path="review"):
        self.wire_bytes += count
        if self.wire_bytes > self.ceiling:
            _refuse("review_encoded_byte_limit")

    def visit(self, depth, path="review"):
        self.nodes += 1
        if depth > MAX_RECORD_DEPTH or self.nodes > MAX_RECORD_NODES:
            _refuse("review_structure_limit")


def _tree(value, budget, depth):
    """Charge each owner-codec occurrence, including repeated nested bytes."""
    budget.visit(depth)
    if type(value) is dict:
        if any(type(k) is not str for k in value):
            _refuse("exact_json_keys_required")
        budget.charge(2 + max(0, len(value) - 1))
        for k, item in value.items():
            budget.charge(len(_wire(k)) + 1)
            _tree(item, budget, depth + 1)
    elif type(value) is list:
        if len(value) > 16_384:
            _refuse("review_array_limit")
        budget.charge(2 + max(0, len(value) - 1))
        for item in value:
            _tree(item, budget, depth + 1)
    elif value is None or type(value) in (bool, int, str):
        budget.charge(len(_wire(value)))
    else:
        _refuse("exact_json_scalar_required")


def _scalar(kind, value):
    if kind in _ENUMS:
        if type(value) is not str or value not in _ENUMS[kind]:
            _refuse("review_enum_invalid")
        return value
    if kind == "False":
        if value is not False:
            _refuse("review_never_authorizes_retry")
        return False
    spec = _SCALARS.get(kind)
    if spec is None:
        _refuse("unknown_review_scalar")
    if spec["kind"] == "integer":
        if type(value) is not int or not spec["minimum"] <= value <= spec["maximum"]:
            _refuse("review_integer_limit")
    elif spec["kind"] == "boolean":
        if type(value) is not bool:
            _refuse("exact_boolean_required")
    elif spec["kind"] == "string":
        if type(value) is not str:
            _refuse("exact_string_required")
        try:
            n = len(value.encode("utf-8"))
        except UnicodeError as error:
            raise SetupReviewValueError("invalid_utf8") from error
        if not spec.get("minimum_bytes", 0) <= n <= spec["maximum_bytes"]:
            _refuse("review_string_limit")
        if "pattern" in spec and re.fullmatch(spec["pattern"], value) is None:
            _refuse("review_digest_invalid")
        if kind in ("RootPath", "RelativePath"):
            absolute = kind == "RootPath"
            parts = value.split("/")[1:] if absolute else value.split("/")
            if (
                value.startswith("/") != absolute
                or "\\" in value
                or any(c in value for c in ("\x00", "\r", "\n"))
                or (value != "/" and any(p in ("", ".", "..") for p in parts))
                or (not absolute and len(parts) > 64)
            ):
                _refuse("canonical_review_path_required")
    else:
        # RawBytes belongs to an in-process view, never a metadata envelope.
        _refuse("nonwire_scalar")
    return value


def _external(kind, value, decode, budget, depth):
    if kind.startswith("Original"):
        from aware_issue_sdk import operation as op
        from aware_issue_sdk import operation_codec as oc
        from aware_issue_sdk import workspace_setup_admission_codec as ic
        from aware_issue_sdk import workspace_setup_admission_values as iv

        from . import architecture_setup_admission_codec as wc
        from . import architecture_setup_admission_values as wv
        from . import architecture_setup_command_values as cv

        command = {
            "OriginalReviewRequest": cv.WorkspaceSetupA1CommandRequest,
            "OriginalReviewGuards": cv.WorkspaceSetupA1ReviewGuards,
        }
        own = {
            "OriginalArchitectureRequest": wv.ArchitectureSetupRequest,
            "OriginalWorkspaceClientCleanup": wv.WorkspaceSetupClientCleanup,
        }
        if kind in command:
            return cv._record(command[kind], value, decode, depth, budget)
        if kind in own:
            return wc._record(own[kind], value, "review", budget, depth, decode)
        if kind in ("OriginalIssueClientCleanup", "OriginalIssueSourcesObservation"):
            return ic._record(
                iv.IssueWorkspaceSetupClientCleanup
                if kind == "OriginalIssueClientCleanup"
                else iv.IssueWorkspaceSetupSourcesObservation,
                value,
                "review",
                decode,
                depth,
                budget,
            )
        table: dict[
            str,
            tuple[type, Callable[[Any], dict[str, object]], Callable[[object], object]],
        ] = {
            "OriginalIssueReadResult": (
                op.IssueReadProjectionResolveResult,
                oc.encode_issue_result,
                lambda x: oc.decode_issue_result(
                    op.ISSUE_RESOLVE_READ_PROJECTION_PROVIDER_OPERATION_REF, x
                ),
            ),
            "OriginalScopeRequest": (
                op.IssueBindScopePathsRequest,
                oc.encode_issue_request,
                lambda x: oc.decode_issue_request(
                    op.ISSUE_BIND_SCOPE_PROVIDER_OPERATION_REF, x
                ),
            ),
        }
        if kind not in table:
            _refuse("nonwire_owner_type")
        cls, encode, inverse = table[kind]
        if decode:
            _tree(value, budget, depth)
            result = inverse(value)
            if type(result) is not cls:
                _refuse("wrong_owner_type")
            return result
        if type(value) is not cls:
            _refuse("original_owner_type_required")
        result = encode(value)
        _tree(result, budget, depth)
        return result
    if kind in _PRIVATE:
        # No physical algorithm is selected or invoked by decoding data.
        try:
            physical = importlib.import_module("aware_file_system.private_directory")
        except ModuleNotFoundError as error:
            raise SetupReviewValueError("private_owner_codec_unavailable") from error
        cls = getattr(physical, kind)
        if decode:
            _tree(value, budget, depth)
            return physical.private_directory_value_from_payload(cls, value)
        if type(value) is not cls:
            _refuse("original_private_value_required")
        result = physical.private_directory_value_to_payload(value)
        _tree(result, budget, depth)
        return result
    _refuse("unknown_review_owner")


def _convert(kind, value, decode, budget, depth):
    budget.visit(depth)
    if kind.startswith("Nullable["):
        if value is None:
            budget.charge(4)
            return None
        return _convert(kind[9:-1], value, decode, budget, depth + 1)
    if kind.startswith("Array["):
        inner, cap = kind[6:-1].rsplit(",", 1)
        if type(value) is not (list if decode else tuple) or len(value) > int(cap):
            _refuse("review_array_limit")
        budget.charge(2 + max(0, len(value) - 1))
        items = [_convert(inner, item, decode, budget, depth + 1) for item in value]
        return tuple(items) if decode else items
    if kind in _NAMES:
        return _record(_NAMES[kind], value, decode, budget, depth + 1)
    if kind.startswith("Original") or kind in _PRIVATE:
        return _external(kind, value, decode, budget, depth + 1)
    result = _scalar(kind, value)
    budget.charge(len(_wire(result)))
    return result


def _invariants(cls, data, decode):
    def fields(item, item_cls):
        return (
            {key: _GET(slot, item, item_cls) for key, slot, _ in _rows(item_cls)}
            if decode
            else item["value"]
        )

    if cls is v.SetupActionAdmissionRequest:
        review = fields(data["review_ref"], v.SetupEvidenceRef)
        intent = fields(data["intent_ref"], v.SetupEvidenceRef)
        if (
            review["record_contract"] != _WIRES[v.SetupReviewRecord]
            or intent["record_contract"] != _WIRES[v.SetupDispatchIntent]
            or review["target"] != data["target"]
            or intent["target"] != data["target"]
            or review["evidence_root"] != intent["evidence_root"]
            or review["root_identity"] != intent["root_identity"]
        ):
            _refuse("action_observation_reference_context_mismatch")
    if cls is v.SetupCaptureDescriptor:
        rows = [fields(x, v.SetupChunkDescriptor) for x in data["chunks"]]
        if (
            not rows
            or [r["ordinal"] for r in rows] != list(range(len(rows)))
            or sum(r["byte_count"] for r in rows) != data["byte_count"]
            or len({r["locator"] for r in rows}) != len(rows)
        ):
            _refuse("contiguous_exact_capture_required")
    if cls is v.SetupScopeOutcomeRecord:
        unknown = data["outcome_kind"] == "unknown"
        if unknown != (data["unknown"] is not None) or unknown == (
            data["capture"] is not None
        ):
            _refuse("complete_scope_outcome_alternative_required")
    if cls is v.SetupRefusalRecord:
        reference = fields(data["review_ref"], v.SetupEvidenceRef)
        request = fields(data["request"], v.SetupReviewRequest)
        attempt = hashlib.sha256(
            b"aware.setup-review.attempt.v1\0"
            + request["execution_ref"].encode("utf-8")
            + b"\0"
            + request["client_intent_id"].encode("utf-8")
        ).hexdigest()
        if (
            reference["record_contract"] != _WIRES[v.SetupReviewRecord]
            or reference["target"] != request["target"]
            or reference["attempt_ref"] != attempt
            or data["phase"]
            not in ("read_review", "record_review_decision", "apply_reviewed")
            or (data["observed_sources"] is None)
            != (data["code"] == "review_issue_changed")
        ):
            _refuse("original_refusal_context_required")
        scope, apply, inputs = (
            data[key] for key in ("scope_decision", "apply_decision", "inputs_ref")
        )
        if (
            data["phase"] == "read_review"
            and any(x is not None for x in (scope, apply, inputs))
            or data["phase"] == "record_review_decision"
            and ((scope is None) == (apply is None) or inputs is not None)
            or data["phase"] == "apply_reviewed"
            and (scope is not None or apply is None or inputs is None)
        ):
            _refuse("original_refusal_call_required")
        for decision, decision_type in (
            (scope, v.SetupScopeDecision),
            (apply, v.SetupApplyDecision),
        ):
            if (
                decision is not None
                and fields(decision, decision_type)["review"] != data["review_ref"]
            ):
                _refuse("original_refusal_call_required")
        if (
            inputs is not None
            and fields(inputs, v.SetupEvidenceRef)["record_contract"]
            != _WIRES[v.SetupApplyInputRecord]
        ):
            _refuse("original_refusal_call_required")
    for key in ("existing_scope", "physical_scope", "final_files", "scope_paths"):
        if key in data and len(set(data[key])) != len(data[key]):
            _refuse("duplicate_review_path")


def _record(cls, value, decode, budget, depth):
    rows = _rows(cls)
    budget.visit(depth)
    skeleton = {"contract": _WIRES[cls], "value": {k: None for k, _, _ in rows}}
    budget.charge(len(_wire(skeleton)) - 4 * len(rows))
    if decode:
        if (
            type(value) is not dict
            or set(value) != {"contract", "value"}
            or any(type(k) is not str for k in value)
            or type(value["contract"]) is not str
            or value["contract"] != _WIRES[cls]
        ):
            _refuse("closed_review_wrapper_required")
        raw = value["value"]
        if (
            type(raw) is not dict
            or any(type(k) is not str for k in raw)
            or set(raw) != {key for key, _, _ in rows}
        ):
            _refuse("closed_review_fields_required")
    else:
        if type(value) is not cls:
            _refuse("original_review_type_required")
        raw = {key: _GET(slot, value, cls) for key, slot, _ in rows}
    data = {
        key: _convert(kind, raw[key], decode, budget, depth + 1)
        for key, _, kind in rows
    }
    _invariants(cls, data, decode)
    rows = _rows(cls)
    if decode:
        instance = _NEW(cls)
        for key, slot, _ in rows:
            _SET(slot, instance, data[key])
        return instance
    return {"contract": _WIRES[cls], "value": data}


def review_value_to_payload(value: object) -> dict[str, object]:
    budget = _Budget()
    result = _record(type(value), value, False, budget, 0)
    if len(_wire(result)) != budget.wire_bytes:
        _refuse("review_wire_accounting_mismatch")
    return cast(dict[str, object], result)


def review_value_to_json(value: object) -> str:
    return _wire(review_value_to_payload(value)).decode("utf-8")


def review_value_digest(value: object) -> str:
    return (
        "sha256:"
        + hashlib.sha256(review_value_to_json(value).encode("utf-8")).hexdigest()
    )


def review_value_from_payload[T](value_type: type[T], payload: object) -> T:
    result = _record(value_type, payload, True, _Budget(), 0)
    review_value_to_payload(result)
    return cast(T, result)


def _pairs(rows):
    result = {}
    for key, value in rows:
        if key in result:
            _refuse("duplicate_review_key")
        result[key] = value
    return result


def _number(value):
    _refuse("review_integer_json_required")


def review_value_from_json[T](value_type: type[T], source: object) -> T:
    _rows(value_type)
    if type(source) is not str:
        _refuse("review_json_text_required")
    if len(source) > MAX_RECORD_BYTES:
        _refuse("review_encoded_byte_limit")
    try:
        source_bytes = len(source.encode("utf-8"))
    except UnicodeError as error:
        raise SetupReviewValueError("invalid_utf8") from error
    if len(source) > MAX_RECORD_BYTES or source_bytes > MAX_RECORD_BYTES:
        _refuse("review_encoded_byte_limit")
    try:
        payload = json.loads(
            source,
            object_pairs_hook=_pairs,
            parse_float=_number,
            parse_constant=_number,
        )
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, SetupReviewValueError):
            raise
        raise SetupReviewValueError("invalid_review_json") from error
    return review_value_from_payload(value_type, payload)
