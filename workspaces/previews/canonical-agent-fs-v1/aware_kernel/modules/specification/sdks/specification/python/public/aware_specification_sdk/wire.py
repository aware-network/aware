"""Versioned SDK value encoding; detached data cannot supply provider authority.

CLI presentation is deliberately unchanged. This codec uses typed records for
the two positional carrier shapes which authored schemas cannot express.
"""

import json
from dataclasses import fields, is_dataclass
from enum import StrEnum
from types import UnionType
from typing import Union, get_args, get_origin, get_type_hints

from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationIterationIdentity,
    SpecificationIterationPlan,
    SpecificationPhaseDefinition,
    SpecificationPhaseDependency,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
)
from aware_specification_runtime.values import canonical_json_bytes

from .draft_cleanup import (
    SpecificationDraftCleanupEvidence,
    SpecificationDraftCleanupInvocation,
    SpecificationDraftCleanupLedger,
    SpecificationDraftCleanupRequest,
    SpecificationDraftInputCustodyObservation,
    SpecificationDraftInputResourceObservation,
    SpecificationDraftIssueCleanup,
    SpecificationDraftPhysicalCleanup,
)
from .draft_evidence import (
    SpecificationDraftEvidence,
    SpecificationDraftMemberBinding,
    SpecificationDraftPhysicalEffect,
)
from .operation import (
    SpecificationDraftRequest,
    SpecificationDraftResult,
    SpecificationObservation,
    SpecificationObserveRequest,
    SpecificationOperationError,
)

SPECIFICATION_SDK_VALUE_CONTRACT = "aware.specification.sdk-value.v1"
_CARRIERS = (
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationIterationIdentity,
    SpecificationIterationPlan,
    SpecificationPhaseDefinition,
    SpecificationPhaseDependency,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
    SpecificationObserveRequest,
    SpecificationObservation,
    SpecificationDraftRequest,
    SpecificationDraftResult,
    SpecificationDraftMemberBinding,
    SpecificationDraftPhysicalEffect,
    SpecificationDraftEvidence,
    SpecificationDraftCleanupRequest,
    SpecificationDraftCleanupLedger,
    SpecificationDraftIssueCleanup,
    SpecificationDraftPhysicalCleanup,
    SpecificationDraftCleanupInvocation,
    SpecificationDraftInputResourceObservation,
    SpecificationDraftInputCustodyObservation,
    SpecificationDraftCleanupEvidence,
    SpecificationOperationError,
)
_BY_REF = {"aware_specification_sdk." + kind.__name__: kind for kind in _CARRIERS}
_ERROR_HINTS = {
    "code": str,
    "effect": str,
    "evidence": SpecificationDraftEvidence | None,
    "evidence_diagnostics": tuple[str, ...],
    "cleanup_evidence": SpecificationDraftCleanupEvidence | None,
}


def encode_specification_value(value: object) -> bytes:
    """Encode an allowlisted existing value, never a live provider or handle."""
    try:
        if type(value) not in _CARRIERS:
            raise ValueError("unsupported_sdk_value")
        payload = {
            "contract": SPECIFICATION_SDK_VALUE_CONTRACT,
            "type_ref": "aware_specification_sdk." + type(value).__name__,
            "value": _encode(value),
        }
        return canonical_json_bytes(payload)
    except (AttributeError, RecursionError, TypeError, ValueError) as error:
        raise SpecificationOperationError("invalid_sdk_wire_value") from error


def decode_specification_value(body: bytes) -> object:
    """Decode canonical v1 bytes and reuse original carrier validators.

    No imported type is selected by the caller; derived digests/identities are
    freshly reconstructed and compared. The result is data, not an admission.
    """
    try:
        if type(body) is not bytes:
            raise TypeError("sdk_value_requires_bytes")
        payload = json.loads(body)
        _exact_object(payload, {"contract", "type_ref", "value"})
        if (
            payload["contract"] != SPECIFICATION_SDK_VALUE_CONTRACT
            or canonical_json_bytes(payload) != body
            or type(payload["type_ref"]) is not str
        ):
            raise ValueError("unsupported_sdk_value_encoding")
        kind = _BY_REF[payload["type_ref"]]
        value = _decode(kind, payload["value"])
        if encode_specification_value(value) != body:
            raise ValueError("sdk_value_not_freshly_derived")
        return value
    except (AttributeError, KeyError, RecursionError, TypeError, ValueError) as error:
        raise SpecificationOperationError("invalid_sdk_wire_value") from error


def _encode(value):
    kind = type(value)
    if kind in _CARRIERS:
        if kind is SpecificationOperationError:
            # Reuse the existing error's structural snapshot validation.
            checked = SpecificationOperationError(
                value.code,
                effect=value.effect,
                evidence=value.evidence,
                evidence_diagnostics=value.evidence_diagnostics,
                cleanup_evidence=value.cleanup_evidence,
            )
            return {name: _encode(getattr(checked, name)) for name in _ERROR_HINTS}
        value.__post_init__()
        result = {}
        for field in fields(value):
            item = getattr(value, field.name)
            if (
                kind is SpecificationDraftCleanupRequest
                and field.name == "ordered_members"
            ):
                result[field.name] = [
                    {
                        "relative_path": path,
                        "content": {"encoding": "hex", "body": body.hex()},
                    }
                    for path, body in item
                ]
            elif kind is SpecificationDraftPhysicalEffect and field.name in {
                "before_identity",
                "after_identity",
            }:
                result[field.name] = (
                    None if item is None else {"device": item[0], "inode": item[1]}
                )
            else:
                result[field.name] = _encode(item)
        return result
    if isinstance(value, StrEnum):
        return value.value
    if kind is tuple:
        return [_encode(item) for item in value]
    if value is None or kind in {str, int, bool}:
        return value
    raise TypeError("unsupported_sdk_value_member")


def _exact_object(value, keys):
    if type(value) is not dict or set(value) != keys:
        raise ValueError("sdk_value_fields_must_be_exact")


def _decode(kind, value):
    if kind in _CARRIERS:
        # Static reflection is restricted to the trusted allowlist, not input.
        member_fields = fields(kind) if is_dataclass(kind) else ()
        hints = (
            _ERROR_HINTS
            if kind is SpecificationOperationError
            else get_type_hints(kind)
        )
        names = (
            set(hints)
            if kind is SpecificationOperationError
            else {field.name for field in member_fields}
        )
        _exact_object(value, names)
        decoded = {}
        for name in names:
            item = value[name]
            if kind is SpecificationDraftCleanupRequest and name == "ordered_members":
                if type(item) is not list:
                    raise TypeError("sdk_members_require_list")
                members = []
                for member in item:
                    _exact_object(member, {"relative_path", "content"})
                    _exact_object(member["content"], {"encoding", "body"})
                    content = member["content"]
                    if content["encoding"] != "hex" or type(content["body"]) is not str:
                        raise ValueError("unsupported_member_byte_encoding")
                    body = bytes.fromhex(content["body"])
                    if body.hex() != content["body"]:
                        raise ValueError("noncanonical_member_bytes")
                    members.append((_decode(str, member["relative_path"]), body))
                decoded[name] = tuple(members)
            elif kind is SpecificationDraftPhysicalEffect and name in {
                "before_identity",
                "after_identity",
            }:
                if item is None:
                    decoded[name] = None
                else:
                    _exact_object(item, {"device", "inode"})
                    decoded[name] = (
                        _decode(int, item["device"]),
                        _decode(int, item["inode"]),
                    )
            else:
                decoded[name] = _decode(hints[name], item)
        if kind is SpecificationOperationError:
            code = decoded.pop("code")
            return kind(code, **decoded)
        return kind(
            **{field.name: decoded[field.name] for field in member_fields if field.init}
        )
    origin = get_origin(kind)
    if origin in {Union, UnionType}:
        choices = get_args(kind)
        if value is None and type(None) in choices:
            return None
        other = tuple(choice for choice in choices if choice is not type(None))
        if len(other) != 1:
            raise TypeError("unsupported_sdk_union")
        return _decode(other[0], value)
    if origin is tuple:
        arguments = get_args(kind)
        if (
            type(value) is not list
            or len(arguments) != 2
            or arguments[1] is not Ellipsis
        ):
            raise TypeError("sdk_sequence_requires_homogeneous_list")
        return tuple(_decode(arguments[0], item) for item in value)
    if isinstance(kind, type) and issubclass(kind, StrEnum):
        return kind(_decode(str, value))
    if kind in {str, int, bool} and type(value) is kind:
        return value
    raise TypeError("invalid_sdk_value_member")
