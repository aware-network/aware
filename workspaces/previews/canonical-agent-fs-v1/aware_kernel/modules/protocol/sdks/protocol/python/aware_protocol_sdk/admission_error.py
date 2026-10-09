"""Typed admission refusals with bounded, explicitly unvalidated reports."""

from __future__ import annotations

import json
from dataclasses import fields
from enum import StrEnum
from typing import cast

from aware_protocol_runtime import (
    ProtocolAdmissionOutcomeKind,
    ProtocolAdmissionResult,
    ProtocolAuthorityMode,
    ProtocolBootstrap,
    ProtocolContractError,
    ProtocolIdentity,
    ProtocolManifest,
    ProtocolRecordBinding,
    ProtocolRecordRole,
    ProtocolTarget,
    ProtocolTargetKind,
)

PROTOCOL_TARGET_ADMISSION_ERROR_CONTRACT = "aware.protocol.target-admission-error.v1"


def _report(value: object) -> tuple[dict[str, object] | None, tuple[str, ...]]:
    # Only exact known values are traversed. No provider serializer/property,
    # deepcopy hook, custom iterator or repr is executed for malformed transport.
    from .contracts import ProtocolTargetAdmissionRequest, ProtocolTargetAdmissionResult

    known = (
        ProtocolTargetAdmissionRequest,
        ProtocolTargetAdmissionResult,
        ProtocolAdmissionResult,
        ProtocolManifest,
        ProtocolIdentity,
        ProtocolTarget,
        ProtocolBootstrap,
        ProtocolRecordBinding,
    )
    enums = (
        ProtocolAdmissionOutcomeKind,
        ProtocolAuthorityMode,
        ProtocolTargetKind,
        ProtocolRecordRole,
    )
    known_fields: dict[type[object], tuple[str, ...]] = {
        owner: tuple(field.name for field in fields(owner)) for owner in known
    }
    omissions: list[str] = []
    remaining = 1024

    def copy(item: object, path: str, depth: int = 0) -> object:
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 12:
            omissions.append(path + ":capacity_omitted")
            return None
        if type(item) is int and item.bit_length() > 1024:
            omissions.append(path + ":integer_omitted")
            return None
        if item is None or type(item) in (bool, int):
            return item
        if type(item) is str:
            if len(item) > 4096:
                omissions.append(path + ":text_tail_omitted")
                return item[:4096]
            return item
        if type(item) in enums:
            return cast(StrEnum, item).value
        if type(item) in known:
            result = {}
            for name in known_fields[type(item)]:
                try:
                    child = object.__getattribute__(item, name)
                except AttributeError:
                    omissions.append(path + "." + name + ":absent")
                    continue
                result[name] = copy(child, path + "." + name, depth + 1)
            return result
        if type(item) in (tuple, list):
            sequence = cast(tuple[object, ...] | list[object], item)
            if len(sequence) > 64:
                omissions.append(path + ":items_tail_omitted")
            result_list = []
            for i, child in enumerate(sequence[:64]):
                if remaining <= 0:
                    omissions.append(path + ":capacity_omitted")
                    break
                result_list.append(copy(child, path + f"[{i}]", depth + 1))
            return result_list
        if type(item) is dict:
            result = {}
            for index, (key, child) in enumerate(item.items()):
                if index >= 64 or remaining <= 0:
                    omissions.append(path + ":members_tail_omitted")
                    break
                if type(key) is not str or len(key) > 128:
                    omissions.append(path + ":non_wire_key_omitted")
                    continue
                result[key] = copy(child, path + "." + key, depth + 1)
            return result
        omissions.append(path + ":unsupported_value_omitted")
        return None

    if type(value) is dict:
        allowed = {field.name for field in fields(ProtocolTargetAdmissionResult)} | {
            "contract"
        }
        filtered = {key: value[key] for key in allowed if key in value}
        if len(filtered) != len(value):
            omissions.append("reported_result:unknown_fields_omitted")
        value = filtered
    copied = copy(value, "reported_result")
    return (copied if type(copied) is dict else None), tuple(omissions)


class ProtocolTargetAdmissionError(ProtocolContractError):
    """A refusal is not an accepted admission, effect receipt or retry permit."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        diagnostics: tuple[str, ...] = (),
        provider_invoked: bool = False,
        reported_result: object = None,
    ) -> None:
        if any(
            type(text) is not str or not text or text.strip() != text
            for text in (code, message)
        ):
            raise ProtocolContractError(
                "Admission error code/message must be exact text"
            )
        if type(diagnostics) is not tuple or any(
            type(item) is not str or not item for item in diagnostics
        ):
            raise ProtocolContractError(
                "Admission error diagnostics must be exact strings"
            )
        if type(provider_invoked) is not bool:
            raise ProtocolContractError("provider_invoked must be exact bool")
        report, report_diagnostics = (
            _report(reported_result) if provider_invoked else (None, ())
        )
        self.code = code
        self.message = message
        self.diagnostics = diagnostics
        self.provider_invoked = provider_invoked
        self.effect = "unknown" if provider_invoked else "none"
        self.report_diagnostics = report_diagnostics
        self._report_json = json.dumps(report, allow_nan=False, sort_keys=True)
        super().__init__(message)

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": PROTOCOL_TARGET_ADMISSION_ERROR_CONTRACT,
            "operation_ref": "protocol_sdk.admit_target",
            "code": self.code,
            "message": self.message,
            "diagnostics": list(self.diagnostics),
            "provider_invoked": self.provider_invoked,
            "effect": self.effect,
            "reported_result": json.loads(self._report_json),
            "report_diagnostics": list(self.report_diagnostics),
            "evidence_grade": "unvalidated_provider_report",
            "authorizes_retry": False,
        }
