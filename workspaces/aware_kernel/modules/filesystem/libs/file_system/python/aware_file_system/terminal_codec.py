"""Closed, detached terminal evidence over the original FileSystem validators.

No IO, handle enrollment, resource cleanup or retry is performed. These payload
APIs do not parse JSON or serialize Python causes/contexts/tracebacks. The outer
owner must retain those separately or report incomplete capture, never omit them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from typing import Literal, overload

from . import confined_mutation as read
from . import private_directory as owner
from . import retained_file_sequence as sequence

_READ_TYPES = (
    read.ConfinedFileObservation,
    read.ConfinedFileReadCleanup,
    read.ConfinedFileObservationWithCleanup,
)
_VALUE_TYPES = sequence._VALUE_TYPES + _READ_TYPES
_SCHEMA = "aware.file-system.terminal-error-evidence.v1"


def terminal_value_to_payload(value: object) -> dict[str, object]:
    """Validate an exact original sequence/read root and return its owner payload."""
    try:
        return owner._owner_to_payload(value, _VALUE_TYPES)
    finally:
        del value


def terminal_value_from_payload[T](value_type: type[T], source: object) -> T:
    """Decode against an explicit closed type, without IO or live enrollment."""
    try:
        return owner._owner_from_payload(value_type, source, _VALUE_TYPES)
    finally:
        del value_type, source


@dataclass(frozen=True, slots=True)
class TerminalErrorEvidence:
    schema: Literal["aware.file-system.terminal-error-evidence.v1"]
    family: Literal["sequence", "private", "read"]
    code: str
    stage: str | None
    cause_kind: str | None
    root_locator: str | None
    path: str | None
    observation: read.ConfinedFileObservation | None
    cleanup: read.ConfinedFileReadCleanup | None
    provider_evidence: (
        sequence.ConfinedSequenceRefusalEvidence
        | owner.PrivateDirectoryRefusalEvidence
        | None
    )


class TerminalCodecError(ValueError):
    def __init__(self, cause, *, original_input):
        super().__init__(str(cause))
        self.original_cause = cause
        self.original_input = original_input
        self.authorizes_retry = False
        self.grants_authority = False
        self.interruption = isinstance(cause, (KeyboardInterrupt, SystemExit)) or (
            type(cause) is owner.PrivateDirectoryRefusal
            and type(cause.evidence) is owner.PrivateDirectoryRefusalEvidence
            and cause.evidence.primary_failure.interruption is True
        )


_ORIGINAL_ERRORS = (
    (sequence, "ConfinedSequenceRefusal", sequence.ConfinedSequenceRefusal),
    (owner, "PrivateDirectoryRefusal", owner.PrivateDirectoryRefusal),
    (read, "ConfinedFileObservationError", read.ConfinedFileObservationError),
)
_ERROR_INITS = tuple(
    (cls, cls.__init__, cls.__init__.__code__) for _, _, cls in _ORIGINAL_ERRORS
)
_EVIDENCE_TYPE = TerminalErrorEvidence
_EVIDENCE_INIT = (_EVIDENCE_TYPE.__init__, _EVIDENCE_TYPE.__init__.__code__)
_EVIDENCE_SLOTS = tuple(
    (item.name, vars(_EVIDENCE_TYPE)[item.name]) for item in fields(_EVIDENCE_TYPE)
)
_EVIDENCE_METHODS = (_EVIDENCE_TYPE.__new__, _EVIDENCE_TYPE.__getattribute__)


def _authenticate():
    if any(getattr(module, name) is not cls for module, name, cls in _ORIGINAL_ERRORS):
        raise ValueError("original_provider_error_types_changed")
    if any(
        cls.__init__ is not init or init.__code__ is not code
        for cls, init, code in _ERROR_INITS
    ):
        raise ValueError("original_provider_error_constructor_changed")
    if (
        TerminalErrorEvidence is not _EVIDENCE_TYPE
        or _EVIDENCE_TYPE.__init__ is not _EVIDENCE_INIT[0]
        or _EVIDENCE_INIT[0].__code__ is not _EVIDENCE_INIT[1]
        or _EVIDENCE_TYPE.__new__ is not _EVIDENCE_METHODS[0]
        or _EVIDENCE_TYPE.__getattribute__ is not _EVIDENCE_METHODS[1]
        or any(
            vars(_EVIDENCE_TYPE).get(name) is not slot for name, slot in _EVIDENCE_SLOTS
        )
    ):
        raise ValueError("original_terminal_evidence_constructor_changed")


def _capture_fields(error):
    _authenticate()
    if type(error) is sequence.ConfinedSequenceRefusal:
        family, allowed = "sequence", {"code", "evidence"}
    elif type(error) is owner.PrivateDirectoryRefusal:
        family, allowed = "private", {"code", "evidence"}
    elif type(error) is read.ConfinedFileObservationError:
        family = "read"
        allowed = {
            "code",
            "stage",
            "cause_kind",
            "root_locator",
            "path",
            "observation",
            "cleanup",
            "_original_read_ledger",
        }
    else:
        raise ValueError("original_supported_filesystem_error_required")
    if (
        set(vars(error)) - allowed
        or type(error.args) is not tuple
        or error.args != (error.code,)
    ):
        raise ValueError("unsupported_error_fields_require_separate_capture")
    if type(error) is read.ConfinedFileObservationError:
        return TerminalErrorEvidence(
            _SCHEMA,
            family,
            error.code,
            error.stage,
            error.cause_kind,
            error.root_locator,
            error.path,
            error.observation,
            error.cleanup,
            None,
        )
    if (
        type(error) is sequence.ConfinedSequenceRefusal
        or type(error) is owner.PrivateDirectoryRefusal
    ):
        return TerminalErrorEvidence(
            _SCHEMA,
            family,
            error.code,
            None,
            None,
            None,
            None,
            None,
            None,
            error.evidence,
        )
    raise ValueError("original_supported_filesystem_error_required")


@overload
def _convert_error(value, *, decode: Literal[True]) -> TerminalErrorEvidence: ...


@overload
def _convert_error(value, *, decode: Literal[False]) -> dict[str, object]: ...


def _convert_error(value, *, decode):
    _authenticate()
    names = tuple(name for name, _ in _EVIDENCE_SLOTS)
    if decode:
        if (
            type(value) is not dict
            or any(type(key) is not str for key in value)
            or set(value) != set(names)
        ):
            raise ValueError("exact_terminal_error_fields_required")
        data = dict(value)
    else:
        if type(value) is not TerminalErrorEvidence:
            raise ValueError("original_terminal_error_evidence_required")
        data = {name: getattr(value, name) for name in names}
    if (
        type(data["schema"]) is not str
        or data["schema"] != _SCHEMA
        or type(data["family"]) is not str
        or data["family"] not in {"sequence", "private", "read"}
    ):
        raise ValueError("terminal_error_schema_or_family_invalid")
    text = owner._owner_helper(read, "_read_text")
    text(data["code"], 1024)
    if data["family"] == "read":
        text(data["stage"], 1024)
        text(data["cause_kind"], 1024)
        if data["root_locator"] is not None:
            owner._owner_helper(read, "_read_root")(data["root_locator"])
        if data["path"] is not None:
            owner._owner_helper(read, "_saved_read_path")(data["path"])
        if data["provider_evidence"] is not None or data["cleanup"] is None:
            raise ValueError("read_error_cleanup_and_absent_provider_required")
        nested = {
            "observation": read.ConfinedFileObservation,
            "cleanup": read.ConfinedFileReadCleanup,
        }
    else:
        if any(
            data[name] is not None
            for name in (
                "stage",
                "cause_kind",
                "root_locator",
                "path",
                "observation",
                "cleanup",
            )
        ):
            raise ValueError("foreign_read_fields_in_provider_error")
        nested = {
            "provider_evidence": sequence.ConfinedSequenceRefusalEvidence
            if data["family"] == "sequence"
            else owner.PrivateDirectoryRefusalEvidence
        }
        if data["family"] == "private" and data["provider_evidence"] is None:
            raise ValueError("original_private_refusal_evidence_required")
    # One original owner budget spans metadata and all nested carriers. It must
    # not reset for observation/cleanup or split a large error into fresh budgets.
    budget = owner._Budget()
    skeleton = dict(data)
    for name in nested:
        skeleton[name] = None
    budget.charge(
        len(
            json.dumps(
                skeleton,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        )
        - 4 * sum(data[name] is not None for name in nested),
        "private",
    )
    converted = dict(data)
    for name, expected in nested.items():
        if data[name] is not None:
            converted[name] = (
                owner._owner_from_payload(
                    expected, data[name], (expected,), _budget=budget
                )
                if decode
                else owner._owner_to_payload(data[name], (expected,), _budget=budget)
            )
    actual = converted if decode else data
    if data["family"] != "read":
        evidence = actual["provider_evidence"]
        if evidence is not None and evidence.code != data["code"]:
            raise ValueError("provider_error_code_correlation_failed")
    elif (
        actual["observation"] is not None and actual["observation"].path != data["path"]
    ):
        raise ValueError("read_error_path_correlation_failed")
    return TerminalErrorEvidence(**converted) if decode else converted


def capture_terminal_error(error: BaseException) -> TerminalErrorEvidence:
    """Capture original public provider fields; causes remain an outer-owner input.

    The private live read ledger is never serialized, inspected or disposed.
    Unrecognized public attributes/args refuse rather than silently disappear.
    """
    try:
        value = _capture_fields(error)
        _convert_error(value, decode=False)
        return value
    except BaseException as cause:
        raise TerminalCodecError(cause, original_input=error) from cause


def terminal_error_to_payload(value) -> dict[str, object]:
    try:
        return _convert_error(
            value if type(value) is TerminalErrorEvidence else _capture_fields(value),
            decode=False,
        )
    except BaseException as cause:
        raise TerminalCodecError(cause, original_input=value) from cause


def terminal_error_from_payload(source) -> TerminalErrorEvidence:
    try:
        return _convert_error(source, decode=True)
    except BaseException as cause:
        raise TerminalCodecError(cause, original_input=source) from cause


__all__ = [
    "TerminalCodecError",
    "TerminalErrorEvidence",
    "capture_terminal_error",
    "terminal_error_from_payload",
    "terminal_error_to_payload",
    "terminal_value_from_payload",
    "terminal_value_to_payload",
]
