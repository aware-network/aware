"""Closed non-authorizing governed-command evidence and owner codec joins."""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import MemberDescriptorType
from typing import Literal, cast

from aware_issue_sdk import workspace_setup_admission_codec as ic
from aware_issue_sdk import workspace_setup_admission_values as i
from aware_issue_sdk.workspace_setup_admission_values import (
    IssueWorkspaceSetupCleanup,
    IssueWorkspaceSetupClientCleanup,
    IssueWorkspaceSetupObservation,
    IssueWorkspaceSetupRequest,
    IssueWorkspaceSetupSourcesObservation,
)
from aware_workspace_sdk import architecture_setup_admission_codec as wc
from aware_workspace_sdk import architecture_setup_admission_values as w
from aware_workspace_sdk.architecture_setup_admission_values import (
    ArchitectureSetupRequest,
    WorkspaceAuthorizedSetupResult,
    WorkspaceSetupCleanup,
    WorkspaceSetupClientCleanup,
    WorkspaceSetupPlanObservation,
    WorkspaceSetupPrimaryFailure,
)

CommandContract = Literal["aware.workspace.architecture-setup-a1-command.v1"]

CommandMode = Literal["preview", "apply"]

CommandOperation = Literal[
    "repository", "workspace", "module", "python_package", "package_manager", "locks"
]

CommandStatus = Literal["preview_completed", "apply_completed", "refused", "incomplete"]

OwnerFamily = Literal["issue", "workspace", "filesystem_sequence", "command"]


@dataclass(frozen=True, slots=True)
class WorkspaceSetupA1ClientCleanup:
    issue: IssueWorkspaceSetupClientCleanup | None
    workspace: WorkspaceSetupClientCleanup | None


@dataclass(frozen=True, slots=True)
class WorkspaceSetupA1CommandEvidence:
    contract: CommandContract
    mode: CommandMode
    operation: CommandOperation | None
    command_status: CommandStatus
    completion_verified: bool
    request: WorkspaceSetupA1CommandRequest | None
    review_guards: WorkspaceSetupA1ReviewGuards
    workspace_observation: WorkspaceSetupPlanObservation | None
    issue_sources_observation: IssueWorkspaceSetupSourcesObservation | None
    issue_observation: IssueWorkspaceSetupObservation | None
    workspace_result: WorkspaceAuthorizedSetupResult | None
    primary_failure: WorkspaceSetupPrimaryFailure
    plan_cleanup: WorkspaceSetupCleanup | None
    admission_cleanup: IssueWorkspaceSetupCleanup | None
    client_cleanup: WorkspaceSetupA1ClientCleanup
    unvalidated_reports: tuple[WorkspaceSetupA1UnvalidatedReport, ...]
    diagnostics: tuple[str, ...]
    ledger_complete: bool
    authorizes_retry: Literal[False]


@dataclass(frozen=True, slots=True)
class WorkspaceSetupA1CommandRequest:
    architecture_request: ArchitectureSetupRequest
    issue_request: IssueWorkspaceSetupRequest | None
    repository_root: str
    authority_manifest_locator: str
    issue_ref: str
    execution_ref: str
    client_intent_id: str


@dataclass(frozen=True, slots=True)
class WorkspaceSetupA1ReviewGuards:
    issue_source_sha256: str | None
    authority_manifest_sha256: str | None
    plan_sha256: str | None


@dataclass(frozen=True, slots=True)
class WorkspaceSetupA1UnvalidatedReport:
    owner: OwnerFamily
    expected_wire: str
    stage: str
    code: str


_TYPES = (
    WorkspaceSetupA1ClientCleanup,
    WorkspaceSetupA1CommandEvidence,
    WorkspaceSetupA1CommandRequest,
    WorkspaceSetupA1ReviewGuards,
    WorkspaceSetupA1UnvalidatedReport,
)
_WIRE_IDS = {
    WorkspaceSetupA1ClientCleanup: "aware.workspace.setup-a1-command-client-cleanup.v1",
    WorkspaceSetupA1CommandEvidence: "aware.workspace.architecture-setup-a1-command.v1",
    WorkspaceSetupA1CommandRequest: "aware.workspace.setup-a1-command-request.v1",
    WorkspaceSetupA1ReviewGuards: "aware.workspace.setup-a1-review-guards.v1",
    WorkspaceSetupA1UnvalidatedReport: "aware.workspace.setup-a1-unvalidated-report.v1",
}
_FIELD_TYPES = {
    WorkspaceSetupA1ClientCleanup: (
        ("issue", "Nullable[IssueWorkspaceSetupClientCleanup]"),
        ("workspace", "Nullable[WorkspaceSetupClientCleanup]"),
    ),
    WorkspaceSetupA1CommandEvidence: (
        ("contract", "CommandContract"),
        ("mode", "CommandMode"),
        ("operation", "Nullable[CommandOperation]"),
        ("command_status", "CommandStatus"),
        ("completion_verified", "Bool"),
        ("request", "Nullable[WorkspaceSetupA1CommandRequest]"),
        ("review_guards", "WorkspaceSetupA1ReviewGuards"),
        ("workspace_observation", "Nullable[WorkspaceSetupPlanObservation]"),
        (
            "issue_sources_observation",
            "Nullable[IssueWorkspaceSetupSourcesObservation]",
        ),
        ("issue_observation", "Nullable[IssueWorkspaceSetupObservation]"),
        ("workspace_result", "Nullable[WorkspaceAuthorizedSetupResult]"),
        ("primary_failure", "WorkspaceSetupPrimaryFailure"),
        ("plan_cleanup", "Nullable[WorkspaceSetupCleanup]"),
        ("admission_cleanup", "Nullable[IssueWorkspaceSetupCleanup]"),
        ("client_cleanup", "WorkspaceSetupA1ClientCleanup"),
        ("unvalidated_reports", "Array[WorkspaceSetupA1UnvalidatedReport]"),
        ("diagnostics", "Array[Diagnostic]"),
        ("ledger_complete", "Bool"),
        ("authorizes_retry", "False"),
    ),
    WorkspaceSetupA1CommandRequest: (
        ("architecture_request", "ArchitectureSetupRequest"),
        ("issue_request", "Nullable[IssueWorkspaceSetupRequest]"),
        ("repository_root", "RootPath"),
        ("authority_manifest_locator", "RelativePath"),
        ("issue_ref", "RelativePath"),
        ("execution_ref", "Ref"),
        ("client_intent_id", "Ref"),
    ),
    WorkspaceSetupA1ReviewGuards: (
        ("issue_source_sha256", "Nullable[Digest]"),
        ("authority_manifest_sha256", "Nullable[Digest]"),
        ("plan_sha256", "Nullable[Digest]"),
    ),
    WorkspaceSetupA1UnvalidatedReport: (
        ("owner", "OwnerFamily"),
        ("expected_wire", "Ref"),
        ("stage", "Code"),
        ("code", "Code"),
    ),
}
_ENUMS = {
    "CommandContract": ["aware.workspace.architecture-setup-a1-command.v1"],
    "CommandMode": ["preview", "apply"],
    "CommandOperation": [
        "repository",
        "workspace",
        "module",
        "python_package",
        "package_manager",
        "locks",
    ],
    "CommandStatus": ["preview_completed", "apply_completed", "refused", "incomplete"],
    "OwnerFamily": ["issue", "workspace", "filesystem_sequence", "command"],
}
_GROUPS = {
    "all_cleanup": ["plan_cleanup", "admission_cleanup", "client_cleanup"],
    "envelope": [
        "contract",
        "mode",
        "operation",
        "command_status",
        "completion_verified",
        "primary_failure",
        "diagnostics",
        "ledger_complete",
        "authorizes_retry",
    ],
    "issue_admission_observation": ["issue_observation"],
    "request_review_and_observations": [
        "request",
        "review_guards",
        "workspace_observation",
        "issue_sources_observation",
    ],
    "unvalidated_report_descriptions": ["unvalidated_reports"],
    "workspace_result": ["workspace_result"],
}
_GROUP_LIMITS = {
    "all_cleanup": 8388608,
    "issue_admission_observation": 4194304,
    "request_review_and_observations": 2097152,
    "unvalidated_report_descriptions": 262144,
    "workspace_result": 8388608,
}

_DEFS = {
    id(cls): (
        cls,
        tuple((field, vars(cls)[field], kind) for field, kind in _FIELD_TYPES[cls]),
    )
    for cls in _TYPES
}
_NAMES = {cls.__name__: cls for cls in _TYPES}
_WS = {cls.__name__: cls for cls in w.SETUP_VALUE_TYPES}
_IS = {cls.__name__: cls for cls in i.ISSUE_SETUP_VALUE_TYPES}
_GET = MemberDescriptorType.__get__
_SET = MemberDescriptorType.__set__


class WorkspaceSetupCommandValueError(ValueError):
    pass


def _rows(cls):
    pair = _DEFS.get(id(cls))
    if pair is None or pair[0] is not cls:
        raise WorkspaceSetupCommandValueError("closed_command_value_required")
    if any(vars(cls).get(name) is not slot for name, slot, _ in pair[1]):
        raise WorkspaceSetupCommandValueError("command_original_slot_changed")
    return pair[1]


def _convert(kind, value, decode, depth, budget):
    budget.visit(depth, "command")
    if depth > 64:
        raise WorkspaceSetupCommandValueError("command_depth_limit")
    if kind.startswith("Nullable["):
        if value is None:
            budget.charge(4, "command")
            return None
        return _convert(kind[9:-1], value, decode, depth + 1, budget)
    if kind.startswith("Array["):
        if type(value) is not (list if decode else tuple) or len(value) > 16384:
            raise WorkspaceSetupCommandValueError("command_array_limit")
        budget.charge(2 + max(0, len(value) - 1), "command")
        result = [
            _convert(kind[6:-1], child, decode, depth + 1, budget) for child in value
        ]
        return tuple(result) if decode else result
    if kind in _NAMES:
        return _record(_NAMES[kind], value, decode, depth + 1, budget)
    if kind in _WS:
        return wc._record(_WS[kind], value, "command", budget, depth + 1, decode)
    if kind in _IS:
        return ic._record(_IS[kind], value, "command", decode, depth + 1, budget)
    if kind in _ENUMS:
        if type(value) is not str or value not in _ENUMS[kind]:
            raise WorkspaceSetupCommandValueError("command_enum_invalid")
        budget.charge(
            len(json.dumps(value, ensure_ascii=False).encode("utf-8")), "command"
        )
        return value
    if kind == "False":
        if value is not False:
            raise WorkspaceSetupCommandValueError("command_never_authorizes_retry")
        budget.charge(5, "command")
        return False
    result = wc._scalar(kind, value, "command")
    budget.charge(
        len(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
        ),
        "command",
    )
    return result


def _record(cls, value, decode, depth, budget):
    rows = _rows(cls)
    flat = cls is WorkspaceSetupA1CommandEvidence
    skeleton = {name: None for name, _, _ in rows}
    if not flat:
        skeleton = {"contract": _WIRE_IDS[cls], "value": skeleton}
    budget.charge(
        len(
            json.dumps(
                skeleton, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        )
        - 4 * len(rows),
        "command",
    )
    if decode:
        if type(value) is not dict or any(type(key) is not str for key in value):
            raise WorkspaceSetupCommandValueError("closed_command_payload_required")
        source = value
        if not flat:
            if (
                set(value) != {"contract", "value"}
                or type(value["contract"]) is not str
                or value["contract"] != _WIRE_IDS[cls]
            ):
                raise WorkspaceSetupCommandValueError("closed_command_wrapper_required")
            source = value["value"]
        if (
            type(source) is not dict
            or any(type(key) is not str for key in source)
            or set(source) != {name for name, _, _ in rows}
        ):
            raise WorkspaceSetupCommandValueError("closed_command_fields_required")
        raw = {name: source[name] for name, _, _ in rows}
    else:
        if type(value) is not cls:
            raise WorkspaceSetupCommandValueError("original_command_value_required")
        raw = {name: _GET(slot, value, cls) for name, slot, _ in rows}
    fields = {}
    used = dict.fromkeys(_GROUP_LIMITS, 0)
    for name, _, kind in rows:
        group = (
            next(
                (
                    key
                    for key, members in _GROUPS.items()
                    if key != "envelope" and name in members
                ),
                None,
            )
            if flat
            else None
        )
        before, original_ceiling = budget.wire_bytes, budget.ceiling
        if group is not None:
            budget.ceiling = min(
                original_ceiling, before + _GROUP_LIMITS[group] - used[group]
            )
        fields[name] = _convert(kind, raw[name], decode, depth + 1, budget)
        if group is not None:
            used[group] += budget.wire_bytes - before
        budget.ceiling = original_ceiling
    _rows(cls)
    if decode:
        instance = object.__new__(cls)
        for name, slot, _ in rows:
            _SET(slot, instance, fields[name])
        return instance
    return fields if flat else {"contract": _WIRE_IDS[cls], "value": fields}


def command_value_to_payload(value):
    _rows(type(value))
    payload = _record(type(value), value, False, 0, wc._Budget(33554432))
    if type(value) is WorkspaceSetupA1CommandEvidence:
        if len(payload["diagnostics"]) > 8 or len(payload["unvalidated_reports"]) > 32:
            raise WorkspaceSetupCommandValueError("command_report_count_limit")
        for group, fields in _GROUPS.items():
            if group == "envelope":
                continue
            size = len(
                json.dumps(
                    {key: payload[key] for key in fields},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            if size > _GROUP_LIMITS[group]:
                raise WorkspaceSetupCommandValueError(
                    "command_component_budget_exceeded"
                )
    if (
        len(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        )
        > 33554432
    ):
        raise WorkspaceSetupCommandValueError("command_total_budget_exceeded")
    return payload


def command_value_to_json(value):
    return json.dumps(
        command_value_to_payload(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def command_value_from_payload[T](value_type: type[T], payload: object) -> T:
    _rows(value_type)
    value = _record(value_type, payload, True, 0, wc._Budget(33554432))
    command_value_to_payload(value)
    return cast(T, value)


def command_value_from_json[T](value_type: type[T], source: object) -> T:
    _rows(value_type)
    text = wc._text(source, "command", 33554432)
    return command_value_from_payload(
        value_type,
        json.loads(text, object_pairs_hook=wc._pairs, parse_constant=wc._constant),
    )
