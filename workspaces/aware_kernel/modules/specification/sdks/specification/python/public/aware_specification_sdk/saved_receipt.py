"""Guarded saved transport presentation; never an operation replay or admission."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import asdict, dataclass, fields, replace
from enum import StrEnum
from pathlib import PurePosixPath
from types import UnionType
from typing import Any, Never, Protocol, Union, get_args, get_origin, get_type_hints

from aware_specification_runtime import (
    decode_specification_snapshot,
    resolve_iteration_identity,
)

from .draft_cleanup import (
    SpecificationDraftCleanupEvidence,
    SpecificationDraftCleanupInvocation,
    SpecificationDraftCleanupLedger,
    SpecificationDraftCleanupRequest,
    SpecificationDraftInputCustodyObservation,
    SpecificationDraftInputResourceObservation,
    SpecificationDraftIssueCleanup,
    SpecificationDraftPhysicalCleanup,
    snapshot_draft_cleanup,
)
from .draft_evidence import (
    SpecificationDraftEvidence,
    SpecificationDraftMemberBinding,
    SpecificationDraftPhysicalEffect,
    snapshot_draft_evidence,
)
from .input_observation import (
    SpecificationInputObservationError,
    SpecificationInputObservationRequest,
)
from .operation import SpecificationObservation

SPECIFICATION_SAVED_RECEIPT_OPERATION_REF = "specification_sdk.present_draft_receipt"
SPECIFICATION_SAVED_RECEIPT_PROVIDER_OPERATION_REF = "specification.receipt.present"
SPECIFICATION_SAVED_RECEIPT_INPUT_PROFILE = "specification.cli043-draft-transport.v1"
SPECIFICATION_SAVED_RECEIPT_SOURCE_LIMIT = 16 * 1024**2
SPECIFICATION_SAVED_RECEIPT_REQUEST_LIMIT = 64 * 1024
SPECIFICATION_SAVED_RECEIPT_WIRE_LIMIT = 192 * 1024**2
_REQUEST_CONTRACT = "specification.saved-receipt.request.v1"
_RESULT_CONTRACT = "specification.saved-receipt.result.v1"
_ERROR_CONTRACT = "specification.saved-receipt.error.v1"
_WIRE_CONTRACT = "aware.specification.saved-receipt-value.v1"
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")


class SpecificationSavedReceiptValueError(ValueError):
    """Invalid detached value or transport, with its original cause retained."""


class SpecificationSavedReceiptView(StrEnum):
    SUMMARY = "summary"
    FULL = "full"


class SpecificationSavedReceiptCleanup(StrEnum):
    NOT_ACQUIRED = "not_acquired"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class SpecificationSavedReceiptEvidenceGrade(StrEnum):
    LOCAL_NOT_OBSERVED = "local_not_observed"
    PROVIDER_OBSERVATION = "provider_observation"
    UNVALIDATED_PROVIDER_REPORT = "unvalidated_provider_report"


def _fail(code: str) -> Never:
    raise SpecificationSavedReceiptValueError(code)


def _text(value, limit=1024, *, empty=False):
    if type(value) is not str or (not empty and not value):
        _fail("receipt_text_invalid")
    try:
        if len(value.encode("utf-8")) > limit:
            _fail("receipt_text_limit")
    except UnicodeError as error:
        raise SpecificationSavedReceiptValueError("receipt_utf8_invalid") from error
    return value


def _choice(value, choices):
    if type(value) is not str and not isinstance(value, StrEnum):
        _fail("receipt_choice_invalid")
    if value not in choices:
        _fail("receipt_choice_invalid")


def _integer(value: object, maximum: int, *, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        _fail("receipt_integer_invalid")
    return value


def _digest(value):
    if type(value) is not str or _SHA.fullmatch(value) is None:
        _fail("receipt_digest_invalid")


def _coordinate(value, *, absolute):
    _text(value, 4096 if absolute else 1024)
    path = PurePosixPath(value)
    if (
        path.is_absolute() != absolute
        or str(path) != value
        or "\\" in value
        or value.startswith("//")
        or any(part in {"", ".", ".."} for part in value.split("/")[absolute:])
        or unicodedata.normalize("NFC", value) != value
        or any(ord(c) < 32 or 0x7F <= ord(c) <= 0x9F for c in value)
        or (not absolute and len(path.parts) > 64)
    ) and not (absolute and value == "/"):
        _fail("receipt_coordinate_invalid")


def _diagnostics(value):
    if type(value) is not tuple or len(value) > 16:
        _fail("receipt_diagnostics_invalid")
    for item in value:
        _text(item)


def _exact(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        _fail("receipt_fields_invalid")


def _hash(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _json_body(value):
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise SpecificationSavedReceiptValueError("receipt_json_invalid") from error


def _json_shape(value, *, depth_limit=32, string_limit=1024**2):
    pending = [(value, 0)]
    nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if nodes > 262144:
            _fail("receipt_json_node_limit")
        kind = type(item)
        if kind in (dict, list):
            depth += 1
            if depth > depth_limit:
                _fail("receipt_json_depth_limit")
            if kind is dict:
                for key, child in item.items():
                    _text(key, 1024**2, empty=True)
                    nodes += 1
                    pending.append((child, depth))
            else:
                pending.extend((child, depth) for child in item)
        elif kind is str:
            _text(item, string_limit, empty=True)
        elif kind is int:
            _integer(item, 2**63 - 1, minimum=-(2**63))
        elif kind is float:
            if not math.isfinite(item):
                _fail("receipt_json_nonfinite")
        elif item is not None and kind is not bool:
            _fail("receipt_json_type_invalid")
    if nodes > 262144:
        _fail("receipt_json_node_limit")


def _json_parse(body, limit, *, depth_limit=32, string_limit=1024**2):
    if type(body) is not bytes or len(body) > limit:
        _fail("receipt_wire_limit")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail("receipt_json_duplicate_key")
            result[key] = value
        return result

    def constant(_):
        _fail("receipt_json_nonfinite")

    try:
        text = body.decode("utf-8")
        # Bound nesting before entering the standard decoder's recursion.
        depth = 0
        quoted = escaped = False
        for character in text:
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quoted = False
            elif character == '"':
                quoted = True
            elif character in "[{":
                depth += 1
                if depth > depth_limit:
                    _fail("receipt_json_depth_limit")
            elif character in "]}":
                depth -= 1
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
        _json_shape(value, depth_limit=depth_limit, string_limit=string_limit)
        return value
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, SpecificationSavedReceiptValueError):
            raise
        raise SpecificationSavedReceiptValueError("receipt_json_invalid") from error


def _hex(value, maximum=SPECIFICATION_SAVED_RECEIPT_SOURCE_LIMIT):
    if type(value) is not str or len(value) > maximum * 2:
        _fail("receipt_body_hex_invalid")
    try:
        body = bytes.fromhex(value)
    except (ValueError, UnicodeError) as error:
        raise SpecificationSavedReceiptValueError("receipt_body_hex_invalid") from error
    if body.hex() != value:
        _fail("receipt_body_hex_noncanonical")
    return body


@dataclass(frozen=True, slots=True)
class SpecificationSavedReceiptRequest:
    base_ref: str
    source_ref: str
    expected_source_sha256: str
    view: SpecificationSavedReceiptView = SpecificationSavedReceiptView.SUMMARY
    input_profile: str = SPECIFICATION_SAVED_RECEIPT_INPUT_PROFILE
    contract: str = _REQUEST_CONTRACT

    def __post_init__(self):
        _coordinate(self.base_ref, absolute=True)
        _coordinate(self.source_ref, absolute=False)
        _digest(self.expected_source_sha256)
        _choice(self.view, {"summary", "full"})
        if (
            type(self.input_profile) is not str
            or self.input_profile != SPECIFICATION_SAVED_RECEIPT_INPUT_PROFILE
        ):
            _fail("receipt_input_profile_unsupported")
        if type(self.contract) is not str or self.contract != _REQUEST_CONTRACT:
            _fail("receipt_request_contract_invalid")
        object.__setattr__(self, "view", SpecificationSavedReceiptView(self.view))


@dataclass(frozen=True, slots=True)
class SpecificationSavedReceiptReadCleanup:
    outcome: SpecificationSavedReceiptCleanup
    acquired_count: int | None
    release_attempted_count: int | None
    closed_count: int | None
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self):
        _choice(self.outcome, {"not_acquired", "closed", "unknown"})
        counts = (self.acquired_count, self.release_attempted_count, self.closed_count)
        for count in counts:
            if count is not None:
                _integer(count, 65)
        _diagnostics(self.diagnostics)
        a, attempted, closed = counts
        if (a is not None and attempted is not None and attempted > a) or (
            attempted is not None and closed is not None and closed > attempted
        ):
            _fail("receipt_cleanup_counts_inconsistent")
        if self.outcome == "not_acquired" and (counts != (0, 0, 0) or self.diagnostics):
            _fail("receipt_cleanup_not_acquired_invalid")
        if self.outcome == "closed" and (
            a is None or a == 0 or counts != (a,) * 3 or self.diagnostics
        ):
            _fail("receipt_cleanup_closed_invalid")
        if (
            self.outcome == "unknown"
            and not self.diagnostics
            and (
                counts == (0, 0, 0) or (a is not None and a > 0 and counts == (a,) * 3)
            )
        ):
            _fail("receipt_cleanup_unknown_invalid")
        object.__setattr__(
            self, "outcome", SpecificationSavedReceiptCleanup(self.outcome)
        )


@dataclass(frozen=True, slots=True)
class SpecificationSavedReceiptSource:
    base_ref: str
    source_ref: str
    source_sha256: str
    byte_count: int
    cleanup: SpecificationSavedReceiptReadCleanup
    observation_grade: str = "observed_state"
    confinement_profile: str = "descriptor_walk_v1"

    def __post_init__(self):
        _coordinate(self.base_ref, absolute=True)
        _coordinate(self.source_ref, absolute=False)
        _digest(self.source_sha256)
        _integer(self.byte_count, SPECIFICATION_SAVED_RECEIPT_SOURCE_LIMIT)
        if type(self.cleanup) is not SpecificationSavedReceiptReadCleanup:
            _fail("receipt_cleanup_type_invalid")
        object.__setattr__(self, "cleanup", replace(self.cleanup))
        if self.cleanup.outcome == "not_acquired":
            _fail("receipt_source_without_acquisition")
        if (
            self.observation_grade != "observed_state"
            or type(self.observation_grade) is not str
        ):
            _fail("receipt_observation_grade_invalid")
        if (
            self.confinement_profile != "descriptor_walk_v1"
            or type(self.confinement_profile) is not str
        ):
            _fail("receipt_confinement_profile_invalid")


@dataclass(frozen=True, slots=True)
class SpecificationSavedReceiptOmission:
    pointer: str
    kind: str
    item_count: int
    encoded_byte_count: int
    encoded_sha256: str
    effect_none_count: int | None
    effect_applied_count: int | None
    effect_unknown_count: int | None
    durability_confirmed_count: int | None
    durability_unconfirmed_count: int | None
    encoding: str = "sorted-ascii-json-compact.v1"
    availability: str = "guarded_source_read"

    def __post_init__(self):
        _text(self.pointer, 512)
        if self.pointer not in _OMISSION_POINTERS:
            _fail("receipt_omission_pointer_invalid")
        _choice(self.kind, {"array", "object"})
        _integer(self.item_count, 262144)
        _integer(self.encoded_byte_count, SPECIFICATION_SAVED_RECEIPT_WIRE_LIMIT)
        _digest(self.encoded_sha256)
        counts = (
            self.effect_none_count,
            self.effect_applied_count,
            self.effect_unknown_count,
            self.durability_confirmed_count,
            self.durability_unconfirmed_count,
        )
        if self.pointer.endswith("/effects"):
            confirmed = tuple(_integer(count, self.item_count) for count in counts)
            if (
                sum(confirmed[:3]) != self.item_count
                or sum(confirmed[3:]) != self.item_count
            ):
                _fail("receipt_omission_counts_inconsistent")
        elif counts != (None,) * 5:
            _fail("receipt_non_effect_counts_invalid")
        if (
            self.encoding != "sorted-ascii-json-compact.v1"
            or self.availability != "guarded_source_read"
        ):
            _fail("receipt_omission_access_invalid")


_NONAUTHORITY = {
    "capture_grade": "captured_transport_not_authenticated",
    "currentness": "not_revalidated",
    "operation_invoked": False,
    "authority_restored": False,
    "authorizes_retry": False,
}


def _fixed(value, names):
    for name, expected in names.items():
        actual = getattr(value, name)
        if type(actual) is not type(expected) or actual != expected:
            _fail("receipt_non_authority_flags_invalid")


@dataclass(frozen=True, slots=True)
class SpecificationSavedReceiptResult:
    request: SpecificationSavedReceiptRequest
    provider_ref: str
    provider_distribution: str
    provider_version: str
    source: SpecificationSavedReceiptSource
    record: dict[str, object] | None
    full_body_hex: str
    omissions: tuple[SpecificationSavedReceiptOmission, ...] = ()
    presentation_outcome: str = "presented"
    capture_grade: str = "captured_transport_not_authenticated"
    currentness: str = "not_revalidated"
    operation_invoked: bool = False
    authority_restored: bool = False
    authorizes_retry: bool = False
    next_action: str = "review_saved_evidence"
    contract: str = _RESULT_CONTRACT

    def __post_init__(self):
        if (
            type(self.request) is not SpecificationSavedReceiptRequest
            or type(self.source) is not SpecificationSavedReceiptSource
        ):
            _fail("receipt_result_binding_invalid")
        object.__setattr__(self, "request", replace(self.request))
        object.__setattr__(self, "source", replace(self.source))
        for item in (
            self.provider_ref,
            self.provider_distribution,
            self.provider_version,
        ):
            _text(item)
        _fixed(
            self,
            {
                **_NONAUTHORITY,
                "presentation_outcome": "presented",
                "next_action": "review_saved_evidence",
                "contract": _RESULT_CONTRACT,
            },
        )
        body = _hex(self.full_body_hex)
        if (
            self.source.source_sha256 != _hash(body)
            or self.source.source_sha256 != self.request.expected_source_sha256
            or self.source.byte_count != len(body)
            or (self.source.base_ref, self.source.source_ref)
            != (self.request.base_ref, self.request.source_ref)
            or self.source.cleanup.outcome != "closed"
        ):
            _fail("receipt_source_correlation_failed")
        packet = decode_saved_draft_capture(
            body, input_profile=self.request.input_profile
        )
        if (
            type(self.omissions) is not tuple
            or len(self.omissions) > 10
            or any(
                type(x) is not SpecificationSavedReceiptOmission for x in self.omissions
            )
        ):
            _fail("receipt_omissions_invalid")
        omissions = tuple(replace(item) for item in self.omissions)
        if self.request.view == "summary":
            _json_shape(self.record)
            record, expected_omissions = _summary(packet)
            if (
                _json_body(self.record) != _json_body(record)
                or omissions != expected_omissions
            ):
                _fail("receipt_summary_correlation_failed")
            object.__setattr__(self, "record", record)
        elif self.record is not None or omissions:
            _fail("receipt_full_view_invalid")
        object.__setattr__(self, "omissions", omissions)


@dataclass(frozen=True, slots=True)
class SpecificationSavedReceiptErrorEvidence:
    code: str
    message: str
    request: SpecificationSavedReceiptRequest | None = None
    provider_invoked: bool = False
    cleanup: SpecificationSavedReceiptCleanup = (
        SpecificationSavedReceiptCleanup.NOT_ACQUIRED
    )
    effect: str = "none"
    observed_source: SpecificationSavedReceiptSource | None = None
    diagnostics: tuple[str, ...] = ()
    reported_result: (
        dict[str, object] | list[object] | str | int | float | bool | None
    ) = None
    reported_result_type: str | None = None
    report_diagnostics: tuple[str, ...] = ()
    evidence_grade: SpecificationSavedReceiptEvidenceGrade = (
        SpecificationSavedReceiptEvidenceGrade.LOCAL_NOT_OBSERVED
    )
    currentness: str = "not_revalidated"
    operation_invoked: bool = False
    authority_restored: bool = False
    authorizes_retry: bool = False
    contract: str = _ERROR_CONTRACT

    def __post_init__(self):
        _text(self.code)
        _text(self.message)
        if self.request is not None:
            if type(self.request) is not SpecificationSavedReceiptRequest:
                _fail("receipt_error_request_invalid")
            object.__setattr__(self, "request", replace(self.request))
        if type(self.provider_invoked) is not bool:
            _fail("receipt_error_invocation_invalid")
        _choice(self.cleanup, {"not_acquired", "closed", "unknown"})
        _choice(self.effect, {"none", "unknown"})
        _choice(
            self.evidence_grade,
            {
                "local_not_observed",
                "provider_observation",
                "unvalidated_provider_report",
            },
        )
        _fixed(self, {k: v for k, v in _NONAUTHORITY.items() if k != "capture_grade"})
        _fixed(self, {"contract": _ERROR_CONTRACT})
        for sequence in (self.diagnostics, self.report_diagnostics):
            _diagnostics(sequence)
        if self.reported_result_type is not None:
            _text(self.reported_result_type)
        if self.observed_source is not None:
            if type(self.observed_source) is not SpecificationSavedReceiptSource:
                _fail("receipt_error_observation_invalid")
            object.__setattr__(self, "observed_source", replace(self.observed_source))
            if (
                self.request is None
                or (self.observed_source.base_ref, self.observed_source.source_ref)
                != (self.request.base_ref, self.request.source_ref)
                or self.observed_source.cleanup.outcome != self.cleanup
            ):
                _fail("receipt_error_observation_correlation_failed")
        if not self.provider_invoked:
            if (
                self.evidence_grade != "local_not_observed"
                or self.cleanup != "not_acquired"
                or self.effect != "none"
                or any(
                    v is not None
                    for v in (
                        self.observed_source,
                        self.reported_result,
                        self.reported_result_type,
                    )
                )
                or self.report_diagnostics
            ):
                _fail("receipt_local_error_evidence_invalid")
        elif self.evidence_grade == "local_not_observed":
            _fail("receipt_provider_error_grade_invalid")
        if self.evidence_grade == "unvalidated_provider_report" and (
            not self.provider_invoked
            or self.cleanup != "unknown"
            or self.effect != "unknown"
            or self.observed_source is not None
        ):
            _fail("receipt_unvalidated_report_evidence_invalid")
        if self.evidence_grade == "provider_observation" and (
            self.reported_result is not None
            or self.reported_result_type is not None
            or self.report_diagnostics
        ):
            _fail("receipt_provider_observation_evidence_invalid")
        if self.reported_result is not None:
            _json_shape(self.reported_result)
            raw = _json_body(self.reported_result)
            if len(raw) > SPECIFICATION_SAVED_RECEIPT_WIRE_LIMIT:
                _fail("receipt_report_limit")
            object.__setattr__(self, "reported_result", json.loads(raw))
        object.__setattr__(
            self, "cleanup", SpecificationSavedReceiptCleanup(self.cleanup)
        )
        object.__setattr__(
            self,
            "evidence_grade",
            SpecificationSavedReceiptEvidenceGrade(self.evidence_grade),
        )


class SpecificationSavedReceiptError(ValueError):
    def __init__(self, evidence: SpecificationSavedReceiptErrorEvidence):
        if type(evidence) is not SpecificationSavedReceiptErrorEvidence:
            _fail("receipt_error_evidence_invalid")
        self.evidence = replace(evidence)
        self.code = self.evidence.code
        super().__init__(self.code)


class SpecificationSavedReceiptProvider(Protocol):
    def present_draft_receipt(
        self, request: SpecificationSavedReceiptRequest
    ) -> SpecificationSavedReceiptResult: ...


class SpecificationSavedReceiptClient:
    def __init__(self, provider: SpecificationSavedReceiptProvider):
        self._provider = provider

    def present_draft_receipt(
        self, request: SpecificationSavedReceiptRequest
    ) -> SpecificationSavedReceiptResult:
        try:
            if type(request) is not SpecificationSavedReceiptRequest:
                _fail("receipt_request_type_invalid")
            original = replace(request)
        except BaseException as error:
            raise SpecificationSavedReceiptError(
                SpecificationSavedReceiptErrorEvidence(
                    "receipt_request_invalid",
                    "Saved receipt request validation failed before invocation.",
                )
            ) from error
        try:
            prepared = replace(original)
        except BaseException as error:
            raise SpecificationSavedReceiptError(
                SpecificationSavedReceiptErrorEvidence(
                    "receipt_request_invalid",
                    "Dispatch preparation failed before invocation.",
                    request=original,
                )
            ) from error
        try:
            value = self._provider.present_draft_receipt(prepared)
        except SpecificationSavedReceiptError as error:
            report = error
            try:
                # Read an untrusted exception carrier once, inside protection.
                report = error.evidence
                checked = replace(report)
                if checked.request != original or not checked.provider_invoked:
                    _fail("receipt_provider_error_uncorrelated")
            except BaseException:  # noqa: BLE001 - malformed/interrupted carriers cannot mask the provider refusal
                refusal = _unknown(original, report)
                refusal.add_note(
                    "Provider error carrier validation failed; original provider cause retained."
                )
                raise refusal from error
            raise SpecificationSavedReceiptError(checked) from error
        except BaseException as error:
            raise _unknown(original, error) from error
        try:
            if type(value) is not SpecificationSavedReceiptResult:
                _fail("receipt_result_type_invalid")
            checked = replace(value)
            if checked.request != original:
                _fail("receipt_provider_result_uncorrelated")
        except BaseException as error:
            raise _unknown(original, value) from error
        return checked


def _unknown(request, value):
    report = None
    faults = []
    try:
        name = type(value).__module__ + "." + type(value).__name__
        name = name.encode("utf-8")[:1024].decode("utf-8", errors="ignore")
    except BaseException:  # noqa: BLE001 - reporting metadata cannot hide the original refusal
        name = "unavailable"
    try:
        raw = asdict(value) if type(value) in _SAVED_VALUES else value
        body = _json_body(raw)
        if len(body) > SPECIFICATION_SAVED_RECEIPT_WIRE_LIMIT:
            _fail("receipt_report_limit")
        report = json.loads(body)
        _json_shape(report)
    except BaseException:  # noqa: BLE001 - unavailable report bytes remain explicitly unvalidated
        report = None
        faults.append("provider_report_not_transportable")
    return SpecificationSavedReceiptError(
        SpecificationSavedReceiptErrorEvidence(
            "receipt_provider_report_invalid",
            "Provider report is unvalidated; no successful read or retry is established.",
            request=request,
            provider_invoked=True,
            cleanup=SpecificationSavedReceiptCleanup.UNKNOWN,
            effect="unknown",
            diagnostics=("provider_report_unvalidated",),
            reported_result=report,
            reported_result_type=name,
            report_diagnostics=tuple(faults),
            evidence_grade=SpecificationSavedReceiptEvidenceGrade.UNVALIDATED_PROVIDER_REPORT,
        )
    )


_DOMAIN_VALUES = (
    SpecificationDraftCleanupEvidence,
    SpecificationDraftCleanupInvocation,
    SpecificationDraftCleanupLedger,
    SpecificationDraftCleanupRequest,
    SpecificationDraftInputCustodyObservation,
    SpecificationDraftInputResourceObservation,
    SpecificationDraftIssueCleanup,
    SpecificationDraftPhysicalCleanup,
    SpecificationDraftEvidence,
    SpecificationDraftMemberBinding,
    SpecificationDraftPhysicalEffect,
    SpecificationInputObservationError,
    SpecificationInputObservationRequest,
)


def _domain_transport(kind: Any, value: Any) -> Any:
    """Map the pinned CLI transport into the original public constructors."""
    if kind in _DOMAIN_VALUES:
        names = {f.name for f in fields(kind)}
        _exact(value, names)
        hints = get_type_hints(kind)
        result = {}
        for name in names:
            item = value[name]
            if kind is SpecificationDraftPhysicalEffect and name in {
                "before_identity",
                "after_identity",
            }:
                if item is not None:
                    if type(item) is not list or len(item) != 2:
                        _fail("receipt_effect_identity_invalid")
                    for number in item:
                        _integer(number, 2**63 - 1)
                    item = (item[0], item[1])
                result[name] = item
            elif kind is SpecificationDraftCleanupRequest and name == "ordered_members":
                if type(item) is not list:
                    _fail("receipt_ordered_members_invalid")
                members = []
                for member in item:
                    if type(member) is not list or len(member) != 2:
                        _fail("receipt_ordered_member_invalid")
                    _text(member[0], 1024)
                    _exact(member[1], {"encoding", "body"})
                    if member[1]["encoding"] != "hex":
                        _fail("receipt_ordered_member_encoding_invalid")
                    _hex(member[1]["body"], 2 * 1024**2)
                    members.append((member[0], _hex(member[1]["body"], 2 * 1024**2)))
                result[name] = tuple(members)
            else:
                result[name] = _domain_transport(hints[name], item)
        return kind(**result)
    origin = get_origin(kind)
    if origin in (Union, UnionType):
        options = get_args(kind)
        if value is None and type(None) in options:
            return None
        nonnull = [item for item in options if item is not type(None)]
        if len(nonnull) != 1:
            _fail("receipt_domain_union_invalid")
        return _domain_transport(nonnull[0], value)
    if origin is tuple:
        args = get_args(kind)
        if type(value) is not list or len(args) != 2 or args[1] is not Ellipsis:
            _fail("receipt_domain_sequence_invalid")
        return tuple(_domain_transport(args[0], item) for item in value)
    if isinstance(kind, type) and issubclass(kind, StrEnum):
        if type(value) is not str:
            _fail("receipt_domain_enum_invalid")
        return kind(value)
    if kind in (str, int, bool) and type(value) is kind:
        return value
    _fail("receipt_domain_value_invalid")


def _domain_value(kind: Any, value: Any) -> Any:
    decoded = _domain_transport(kind, value)
    if kind is SpecificationDraftCleanupEvidence:
        return snapshot_draft_cleanup(decoded)
    if kind is SpecificationDraftEvidence:
        return snapshot_draft_evidence(decoded)
    return decoded


def _legacy_cleanup(raw):
    _exact(
        raw,
        {
            "root_locator",
            "target_path",
            "scratch_path",
            "attempted",
            "outcome",
            "evidence",
        },
    )
    ledger = raw["evidence"]
    _exact(
        ledger,
        {
            "package_outcome",
            "effects",
            "residual_scratch_paths",
            "cleanup_diagnostics",
            "durability_confirmed",
        },
    )
    if type(ledger["effects"]) is not list:
        _fail("receipt_legacy_effects_invalid")
    adapted_effects = []
    for effect in ledger["effects"]:
        _exact(
            effect,
            {
                "path",
                "kind",
                "state",
                "durability_confirmed",
                "mode",
                "before_digest",
                "after_digest",
                "after_identity",
            },
        )
        adapted_effects.append({**effect, "before_identity": None})
    # Validator-only absent arguments never enter the preserved raw record.
    adapted = {
        **raw,
        "evidence": {**ledger, "effects": adapted_effects, "ledger_complete": None},
    }
    return _domain_value(SpecificationDraftPhysicalCleanup, adapted)


def _issue_custody(raw):
    """Map the original Issue transport, never guess between producer schemas."""
    _exact(
        raw, {item.name for item in fields(SpecificationDraftInputCustodyObservation)}
    )
    ledger = raw["physical_evidence"]
    if ledger is None:
        return _domain_value(SpecificationDraftInputCustodyObservation, raw)
    _exact(
        ledger,
        {
            "package_outcome",
            "effects",
            "residual_scratch_paths",
            "cleanup_diagnostics",
            "durability_confirmed",
            "ledger_complete",
        },
    )
    if (
        type(ledger["ledger_complete"]) is not bool
        or type(ledger["effects"]) is not list
    ):
        _fail("receipt_issue_ledger_invalid")
    effects = []
    for effect in ledger["effects"]:
        _exact(
            effect,
            {
                "path",
                "kind",
                "state",
                "durability_confirmed",
                "mode",
                "before_digest",
                "after_digest",
                "after_identity",
            },
        )
        effects.append({**effect, "before_identity": None})
    # Only the constructor argument gains unknown identity, not captured data.
    adapted = {**raw, "physical_evidence": {**ledger, "effects": effects}}
    return _domain_value(SpecificationDraftInputCustodyObservation, adapted)


def _record_observation(raw):
    _exact(
        raw,
        {
            "snapshot",
            "source_digest",
            "source_context_digest",
            "provider_ref",
            "authority_mode",
            "observation_grade",
            "iterations",
            "work_authority",
            "phase_acceptance",
        },
    )
    if (
        raw["work_authority"] is not False
        or raw["phase_acceptance"] is not False
        or type(raw["iterations"]) is not list
    ):
        _fail("receipt_observation_authority_invalid")
    snapshot = decode_specification_snapshot(_json_body(raw["snapshot"]))
    identities = []
    for item in raw["iterations"]:
        _exact(item, {"iteration_ref", "plan_revision", "plan_digest"})
        identity = resolve_iteration_identity(snapshot, item["iteration_ref"])
        if (
            type(item["plan_revision"]) is not int
            or identity.plan.plan_revision != item["plan_revision"]
            or identity.plan_digest != item["plan_digest"]
        ):
            _fail("receipt_iteration_correlation_failed")
        identities.append(identity)
    return SpecificationObservation(
        snapshot,
        raw["source_digest"],
        raw["provider_ref"],
        raw["authority_mode"],
        raw["observation_grade"],
        raw["source_context_digest"],
        tuple(identities),
    )


_REQUIRED = {
    "effect",
    "consumer_completion_verified",
    "retained_capability_exported",
    "cleanup_evidence",
    "input_custody",
    "caller_cleanup",
    "cleanup_diagnostics",
    "protocol_owner_completion",
}
_OPTIONAL = {
    "operation_outcome",
    "error",
    "authoring_intent_ref",
    "input_sha256",
    "snapshot_digest",
    "created_paths",
    "members",
    "evidence",
    "observation",
    "evidence_diagnostics",
    "primary_diagnostics",
    "input_observation",
    "input_observation_error",
    "input_guidance",
}
_OMISSION_POINTERS = (
    "/members",
    "/evidence/members",
    "/evidence/effects",
    "/observation/snapshot",
    "/cleanup_evidence/issue_disposition/evidence/effects",
    "/cleanup_evidence/physical_observation/evidence/effects",
    "/cleanup_evidence/input_custody/physical_evidence/effects",
    "/input_custody/physical_evidence/effects",
    "/caller_cleanup/physical_observation/evidence/effects",
    "/cleanup_evidence/issue_disposition/request/ordered_members",
)


def _record_texts(value):
    if type(value) is not list:
        _fail("receipt_record_texts_invalid")
    for text in value:
        _text(text, 1024**2)


def _validate_packet(packet):
    if type(packet) is not dict:
        _fail("receipt_capture_requires_object")
    if set(packet) == {
        "effect",
        "consumer_completion_verified",
        "retained_capability_exported",
        "error",
        "detail",
    }:
        if (
            packet["effect"] != "none"
            or packet["consumer_completion_verified"] is not False
            or packet["retained_capability_exported"] is not False
            or packet["error"] != "governed_draft_integration_unavailable"
            or packet["detail"] not in {"ImportError", "AttributeError"}
        ):
            _fail("receipt_supplier_unavailable_invalid")
        return
    if not _REQUIRED <= set(packet) or set(packet) - (_REQUIRED | _OPTIONAL):
        _fail("receipt_packet_fields_invalid")
    _choice(packet["effect"], {"none", "published", "unknown"})
    _choice(
        packet["protocol_owner_completion"],
        {"not_attempted", "completed", "incomplete", "unknown"},
    )
    if (
        type(packet["consumer_completion_verified"]) is not bool
        or packet["retained_capability_exported"] is not False
    ):
        _fail("receipt_packet_boolean_invalid")
    for key in ("cleanup_diagnostics", "evidence_diagnostics", "primary_diagnostics"):
        if key in packet:
            _record_texts(packet[key])
    for key in ("error", "authoring_intent_ref"):
        if key in packet:
            _text(packet[key], 1024**2)
    for key in ("input_sha256", "snapshot_digest"):
        if key in packet:
            _digest(packet[key])
    if "operation_outcome" in packet:
        _choice(packet["operation_outcome"], {"previewed", "published"})
    if "created_paths" in packet:
        _record_texts(packet["created_paths"])
        for path in packet["created_paths"]:
            _coordinate(path, absolute=False)
    members = None
    if "members" in packet:
        if type(packet["members"]) is not list:
            _fail("receipt_members_invalid")
        members = []
        for item in packet["members"]:
            _exact(item, {"path", "bytes", "sha256"})
            members.append(
                _domain_value(
                    SpecificationDraftMemberBinding,
                    {
                        "relative_path": item["path"],
                        "byte_count": item["bytes"],
                        "source_sha256": item["sha256"],
                    },
                )
            )
        paths = [item.relative_path for item in members]
        if paths != sorted(set(paths)):
            _fail("receipt_members_order_invalid")
    decoded = {}
    for key, kind in (
        ("cleanup_evidence", SpecificationDraftCleanupEvidence),
        ("evidence", SpecificationDraftEvidence),
        ("input_observation_error", SpecificationInputObservationError),
    ):
        if key == "input_observation_error" and key in packet and packet[key] is None:
            _fail("receipt_input_error_null_invalid")
        if key in packet and packet[key] is not None:
            decoded[key] = _domain_value(kind, packet[key])
    if packet["input_custody"] is not None:
        decoded["input_custody"] = _issue_custody(packet["input_custody"])
    if (
        "evidence" in decoded
        and members is not None
        and tuple(members) != decoded["evidence"].members
    ):
        _fail("receipt_member_evidence_mismatch")
    cleanup = decoded.get("cleanup_evidence")
    custody = decoded.get("input_custody")
    if (
        cleanup is not None
        and cleanup.input_custody is not None
        and custody is not None
    ):
        names = ("attempt_ref", "client_intent_id", "execution_ref", "context_ref")
        if any(
            getattr(cleanup.input_custody, name) != getattr(custody, name)
            for name in names
        ):
            _fail("receipt_custody_correlation_failed")
    coordinates = []
    evidence = decoded.get("evidence")
    if evidence is not None:
        coordinates.append(
            {
                name: getattr(evidence, name)
                for name in (
                    "attempt_ref",
                    "client_intent_id",
                    "execution_ref",
                )
            }
        )
    if cleanup is not None:
        coordinates.append({"attempt_ref": cleanup.attempt_ref})
        if cleanup.input_custody is not None:
            coordinates.append(
                {
                    name: getattr(cleanup.input_custody, name)
                    for name in (
                        "attempt_ref",
                        "client_intent_id",
                        "execution_ref",
                        "context_ref",
                    )
                }
            )
        if cleanup.issue_disposition is not None:
            disposition = cleanup.issue_disposition
            coordinates.append(
                {
                    "execution_ref": disposition.execution_ref,
                    "client_intent_id": disposition.request.client_intent_id,
                }
            )
    if custody is not None:
        coordinates.append(
            {
                name: getattr(custody, name)
                for name in (
                    "attempt_ref",
                    "client_intent_id",
                    "execution_ref",
                    "context_ref",
                )
            }
        )
    # Missing/null coordinates stay unknown. Present known coordinates must join;
    # the stricter original two-custody comparison above also preserves nulls.
    for name in ("attempt_ref", "client_intent_id", "execution_ref", "context_ref"):
        known = {item[name] for item in coordinates if item.get(name) is not None}
        if len(known) > 1:
            _fail("receipt_carrier_correlation_failed")
    caller = packet["caller_cleanup"]
    if type(caller) is not dict or set(caller) - {
        "custody",
        "physical",
        "protocol",
        "physical_observation",
    }:
        _fail("receipt_caller_cleanup_invalid")
    legacy_observation = None
    for key, value in caller.items():
        if key == "physical_observation":
            legacy_observation = _legacy_cleanup(value)
        else:
            _exact(
                value,
                {"invocation_state"}
                if key == "custody"
                else {"invocation_state", "owner_completion"},
            )
            _choice(value["invocation_state"], {"invoked", "returned", "raised"})
            if key != "custody" and value["owner_completion"] != "unknown":
                _fail("receipt_caller_completion_invalid")
    ledgers = [decoded.get("evidence")]
    if custody is not None:
        ledgers.append(custody.physical_evidence)
    if cleanup is not None:
        for observation in (cleanup.issue_disposition, cleanup.physical_observation):
            if observation is not None:
                ledgers.append(observation.evidence)
        if cleanup.input_custody is not None:
            ledgers.append(cleanup.input_custody.physical_evidence)
    if legacy_observation is not None:
        ledgers.append(legacy_observation.evidence)
    if packet["effect"] != "published" and any(
        ledger is not None and ledger.package_outcome == "published"
        for ledger in ledgers
    ):
        _fail("receipt_known_publication_contradicted")
    if "observation" in packet:
        _record_observation(packet["observation"])
    if "input_observation" in packet:
        value = packet["input_observation"]
        _exact(
            value,
            {
                "source_ref",
                "base_ref",
                "source_sha256",
                "byte_count",
                "cleanup",
                "observation_grade",
            },
        )
        _text(value["source_ref"], 8192)
        _text(value["base_ref"], 8192)
        _digest(value["source_sha256"])
        _integer(value["byte_count"], 2 * 1024**2)
        if (
            value["cleanup"] != "closed"
            or value["observation_grade"] != "observed_state"
        ):
            _fail("receipt_input_observation_invalid")
        if (
            "input_sha256" in packet
            and value["source_sha256"] != packet["input_sha256"]
        ):
            _fail("receipt_input_digest_mismatch")
    if "input_guidance" in packet:
        value = packet["input_guidance"]
        _exact(value, {"argument", "path_base", "reason", "next_action"})
        for item in value.values():
            _text(item, 1024**2)
        if (
            value["argument"] != "--snapshot-json"
            or value["path_base"] != "invocation_directory_or_absolute"
        ):
            _fail("receipt_input_guidance_invalid")
    outcome = packet.get("operation_outcome")
    if outcome == "published":
        if (
            not {"created_paths", "authoring_intent_ref", "evidence"} <= set(packet)
            or packet["evidence"] is None
            or not packet["created_paths"]
            or packet["effect"] != "published"
        ):
            _fail("receipt_published_record_incomplete")
        if "error" not in packet and "observation" not in packet:
            _fail("receipt_published_observation_missing")
    if outcome == "previewed" and packet["effect"] != "none":
        _fail("receipt_preview_effect_inconsistent")
    if packet["consumer_completion_verified"] and (
        outcome is None or "error" in packet
    ):
        _fail("receipt_completion_claim_inconsistent")


def decode_saved_draft_capture(
    body: bytes, *, input_profile=SPECIFICATION_SAVED_RECEIPT_INPUT_PROFILE
) -> dict[str, object]:
    """Validate the whole closed historical transport through original owners."""
    try:
        if (
            type(input_profile) is not str
            or input_profile != SPECIFICATION_SAVED_RECEIPT_INPUT_PROFILE
        ):
            _fail("receipt_input_profile_unsupported")
        packet = _json_parse(body, SPECIFICATION_SAVED_RECEIPT_SOURCE_LIMIT)
        _validate_packet(packet)
        return packet
    except Exception as error:
        if isinstance(error, SpecificationSavedReceiptValueError):
            raise
        raise SpecificationSavedReceiptValueError("receipt_capture_invalid") from error


def _summary(packet):
    # Build from the raw validated shape, never from adapted legacy constructors.
    record = json.loads(_json_body(packet))
    omissions = []
    for pointer in sorted(_OMISSION_POINTERS):
        parts = pointer.split("/")[1:]
        parent = record
        for part in parts[:-1]:
            if type(parent) is not dict or part not in parent:
                parent = None
                break
            parent = parent[part]
        if (
            type(parent) is not dict
            or parts[-1] not in parent
            or parent[parts[-1]] is None
        ):
            continue
        collection = parent[parts[-1]]
        if type(collection) not in (dict, list):
            _fail("receipt_omission_collection_invalid")
        body = _json_body(collection)
        counts = (None,) * 5
        if pointer.endswith("/effects"):
            counts = tuple(
                sum(item["state"] == state for item in collection)
                for state in ("none", "applied", "unknown")
            ) + (
                sum(item["durability_confirmed"] is True for item in collection),
                sum(item["durability_confirmed"] is False for item in collection),
            )
        omissions.append(
            SpecificationSavedReceiptOmission(
                pointer,
                "object" if type(collection) is dict else "array",
                len(collection),
                len(body),
                _hash(body),
                counts[0],
                counts[1],
                counts[2],
                counts[3],
                counts[4],
            )
        )
        parent[parts[-1]] = {"omitted": True, "pointer": pointer}
    return record, tuple(omissions)


def present_saved_draft_capture(
    request: SpecificationSavedReceiptRequest,
    body: bytes,
    *,
    provider_ref: str,
    provider_distribution: str,
    provider_version: str,
    cleanup: SpecificationSavedReceiptReadCleanup,
) -> SpecificationSavedReceiptResult:
    """Data-only composition for an explicitly selected original read provider."""
    original = replace(request)
    packet = decode_saved_draft_capture(body, input_profile=original.input_profile)
    source = SpecificationSavedReceiptSource(
        original.base_ref,
        original.source_ref,
        _hash(body),
        len(body),
        cleanup,
    )
    record, omissions = _summary(packet) if original.view == "summary" else (None, ())
    return SpecificationSavedReceiptResult(
        original,
        provider_ref,
        provider_distribution,
        provider_version,
        source,
        record,
        body.hex(),
        omissions,
    )


_SAVED_VALUES = (
    SpecificationSavedReceiptRequest,
    SpecificationSavedReceiptReadCleanup,
    SpecificationSavedReceiptSource,
    SpecificationSavedReceiptOmission,
    SpecificationSavedReceiptResult,
    SpecificationSavedReceiptErrorEvidence,
)
_SAVED_BY_REF = {
    "aware_specification_sdk." + cls.__name__: cls for cls in _SAVED_VALUES
}


def _saved_decode(kind: Any, raw: Any) -> Any:
    if kind in _SAVED_VALUES:
        _exact(raw, {f.name for f in fields(kind)})
        hints = get_type_hints(kind)
        return kind(
            **{name: _saved_decode(hints[name], value) for name, value in raw.items()}
        )
    origin = get_origin(kind)
    if origin in (UnionType, Union):
        options = get_args(kind)
        if raw is None and type(None) in options:
            return None
        if len(options) > 2:
            _json_shape(raw)
            return raw
        return _saved_decode(next(v for v in options if v is not type(None)), raw)
    if origin is tuple:
        if type(raw) is not list:
            _fail("receipt_wire_sequence_invalid")
        return tuple(_saved_decode(get_args(kind)[0], item) for item in raw)
    if isinstance(kind, type) and issubclass(kind, StrEnum):
        if type(raw) is not str:
            _fail("receipt_wire_enum_invalid")
        return kind(raw)
    if kind is dict or origin is dict:
        if type(raw) is not dict:
            _fail("receipt_wire_object_invalid")
        return raw
    if kind in (str, int, bool) and type(raw) is kind:
        return raw
    _fail("receipt_wire_type_invalid")


def encode_specification_saved_receipt_value(value) -> bytes:
    try:
        if type(value) not in _SAVED_VALUES:
            _fail("receipt_wire_value_invalid")
        checked = replace(value)
        body = _json_body(
            {
                "contract": _WIRE_CONTRACT,
                "type_ref": "aware_specification_sdk." + type(value).__name__,
                "value": asdict(checked),
            }
        )
        limit = (
            SPECIFICATION_SAVED_RECEIPT_REQUEST_LIMIT
            if type(value) is SpecificationSavedReceiptRequest
            else SPECIFICATION_SAVED_RECEIPT_WIRE_LIMIT
        )
        if len(body) > limit:
            _fail("receipt_wire_limit")
        return body
    except Exception as error:
        if isinstance(error, SpecificationSavedReceiptValueError):
            raise
        raise SpecificationSavedReceiptValueError(
            "receipt_wire_value_invalid"
        ) from error


def decode_specification_saved_receipt_value(body: bytes):
    try:
        # Raw hex can exceed the captured profile's individual-string bound.
        payload = _json_parse_saved_wire(body)
        _exact(payload, {"contract", "type_ref", "value"})
        if (
            payload["contract"] != _WIRE_CONTRACT
            or type(payload["type_ref"]) is not str
            or payload["type_ref"] not in _SAVED_BY_REF
        ):
            _fail("receipt_wire_contract_invalid")
        kind = _SAVED_BY_REF[payload["type_ref"]]
        if (
            kind is SpecificationSavedReceiptRequest
            and len(body) > SPECIFICATION_SAVED_RECEIPT_REQUEST_LIMIT
        ):
            _fail("receipt_wire_limit")
        value = _saved_decode(kind, payload["value"])
        if encode_specification_saved_receipt_value(value) != body:
            _fail("receipt_wire_noncanonical")
        return value
    except Exception as error:
        if isinstance(error, SpecificationSavedReceiptValueError):
            raise
        raise SpecificationSavedReceiptValueError(
            "receipt_wire_value_invalid"
        ) from error


def _json_parse_saved_wire(body):
    value = _json_parse(
        body,
        SPECIFICATION_SAVED_RECEIPT_WIRE_LIMIT,
        depth_limit=40,
        string_limit=SPECIFICATION_SAVED_RECEIPT_SOURCE_LIMIT * 2,
    )
    if type(value) is dict and type(value.get("value")) is dict:
        record = value["value"]
        if "full_body_hex" in record:
            _hex(record["full_body_hex"])
            # Temporary mask for structural accounting, not returned evidence.
            masked = {**value, "value": {**record, "full_body_hex": ""}}
        else:
            masked = value
    else:
        masked = value
    _json_shape(masked, depth_limit=40)
    return value
