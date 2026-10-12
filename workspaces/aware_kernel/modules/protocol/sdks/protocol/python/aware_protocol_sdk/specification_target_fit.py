"""Bounded read-only target-fit data and explicitly selected provider client.

Values are observations, never authority. This module imports no FS provider.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Protocol, cast

PROTOCOL_SPECIFICATION_TARGET_FIT_OPERATION_REF = (
    "protocol_sdk.observe_specification_target_fit"
)
PROTOCOL_SPECIFICATION_TARGET_FIT_PROVIDER_OPERATION_REF = (
    "protocol.specification.target_fit.observe"
)
PROTOCOL_SPECIFICATION_TARGET_FIT_PROVIDER_REF = (
    "aware_protocol_fs_adapter.specification_target_fit.v1"
)
PROTOCOL_SPECIFICATION_TARGET_FIT_DISTRIBUTION = "aware-protocol-fs-adapter"
PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_WIRE_BYTES = 131072
PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_REPORT_BYTES = 16384
PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_SOURCE_BYTES = 1048576
_REQUEST = "aware.protocol.specification-target-fit-request.v1"
_RESULT = "aware.protocol.specification-target-fit-result.v1"
_ERROR = "aware.protocol.specification-target-fit-error.v1"


class ProtocolSpecificationTargetFitOutcome(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"


class ProtocolSpecificationTargetFitCleanup(StrEnum):
    NOT_ACQUIRED = "not_acquired"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class ProtocolSpecificationTargetFitEffect(StrEnum):
    NONE = "none"
    UNKNOWN = "unknown"


class ProtocolSpecificationTargetFitEvidenceGrade(StrEnum):
    LOCAL_NOT_OBSERVED = "local_not_observed"
    PROVIDER_OBSERVATION = "provider_observation"
    UNVALIDATED_PROVIDER_REPORT = "unvalidated_provider_report"


class ProtocolSpecificationTargetFitValueError(ValueError):
    """Invalid data; never an operation admission or retry instruction."""


def _require(condition: bool, code: str = "target_fit_value_invalid") -> None:
    if not condition:
        raise ProtocolSpecificationTargetFitValueError(code)


def _utf8(value: str) -> bytes:
    """Translate invalid Unicode at every direct codec/report entry."""
    try:
        return value.encode("utf-8", "strict")
    except UnicodeError as error:
        raise ProtocolSpecificationTargetFitValueError(
            "target_fit_utf8_invalid"
        ) from error


def _text(value: object, limit: int = 1024) -> None:
    if type(value) is not str:
        raise ProtocolSpecificationTargetFitValueError("target_fit_text_invalid")
    try:
        body = value.encode("utf-8", "strict")
    except UnicodeError as error:
        raise ProtocolSpecificationTargetFitValueError(
            "target_fit_text_invalid"
        ) from error
    _require(bool(body) and len(body) <= limit and value == value.strip())
    _require(not any(ord(c) < 32 or ord(c) == 127 for c in value))


def _digest(value: object) -> None:
    _require(
        type(value) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None
    )


def _diagnostics(value: object) -> None:
    if type(value) is not tuple or len(value) > 16:
        raise ProtocolSpecificationTargetFitValueError("target_fit_diagnostics_invalid")
    for item in value:
        _text(item)


def _encoded(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8", "strict")
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise ProtocolSpecificationTargetFitValueError(
            "target_fit_json_invalid"
        ) from error


@dataclass(frozen=True, slots=True)
class _FrozenReport:
    body: str


def _json_tree(value: object, *, frozen: bool = False) -> object:
    """Only exact builtin/our immutable JSON containers; no user hooks."""
    count = 0
    if type(value) is _FrozenReport:
        body = object.__getattribute__(value, "body")
        _require(type(body) is str)
        _require(len(_utf8(body)) <= PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_REPORT_BYTES)
        value = json.loads(body)

    def visit(item: object, depth: int) -> object:
        nonlocal count
        count += 1
        _require(count <= 512 and depth <= 8, "target_fit_report_capacity")
        kind = type(item)
        if item is None or kind in (bool, int):
            return item
        if type(item) is float:
            _require(math.isfinite(item))
            return item
        if type(item) is str:
            _require(
                len(_utf8(item)) <= PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_REPORT_BYTES
            )
            return item
        if type(item) is dict:
            _require(len(item) <= 512)
            result = {}
            for key, child in item.items():
                _require(type(key) is str)
                _require(
                    len(_utf8(key))
                    <= PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_REPORT_BYTES
                )
                count += 1
                result[key] = visit(child, depth + 1)
            return result
        if kind in (list, tuple):
            children = cast(list[object] | tuple[object, ...], item)
            _require(len(children) <= 512)
            return [visit(child, depth + 1) for child in children]
        raise ProtocolSpecificationTargetFitValueError("target_fit_report_type_invalid")

    result = visit(value, 0)
    body = _encoded(result)
    _require(
        len(body) <= PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_REPORT_BYTES,
        "target_fit_report_capacity",
    )
    return _FrozenReport(body.decode("utf-8")) if frozen else result


@dataclass(frozen=True, slots=True)
class ProtocolSpecificationTargetFitRequest:
    repository_root: str
    protocol_manifest_locator: str
    supplied_spec_manifest_locator: str
    expected_manifest_sha256: str
    contract: str = _REQUEST

    def __post_init__(self) -> None:
        _text(self.repository_root, 4096)
        _text(self.protocol_manifest_locator, 4096)
        _text(self.supplied_spec_manifest_locator)
        _digest(self.expected_manifest_sha256)
        _require(type(self.contract) is str and self.contract == _REQUEST)

    def to_wire(self) -> dict[str, object]:
        return protocol_specification_target_fit_value_to_payload(self)


@dataclass(frozen=True, slots=True)
class ProtocolSpecificationTargetFitResult:
    request: ProtocolSpecificationTargetFitRequest
    provider_ref: str
    provider_distribution: str
    provider_version: str
    source_sha256: str
    configured_root: str
    path_template: str
    expected_shape: str
    fit: ProtocolSpecificationTargetFitOutcome
    reason: str
    diagnostics: tuple[str, ...] = ()
    matched_spec_key: str | None = None
    cleanup: ProtocolSpecificationTargetFitCleanup = (
        ProtocolSpecificationTargetFitCleanup.CLOSED
    )
    observation_grade: str = "observed_state"
    scope: str = "binding_layout_only"
    effect: ProtocolSpecificationTargetFitEffect = (
        ProtocolSpecificationTargetFitEffect.NONE
    )
    authorizes_retry: bool = False
    operation_ref: str = PROTOCOL_SPECIFICATION_TARGET_FIT_OPERATION_REF
    contract: str = _RESULT

    def __post_init__(self) -> None:
        _require(type(self.request) is ProtocolSpecificationTargetFitRequest)
        self.request.__post_init__()
        for value in (
            self.provider_ref,
            self.provider_distribution,
            self.provider_version,
            self.configured_root,
            self.path_template,
            self.reason,
        ):
            _text(value)
        _require(self.provider_ref == PROTOCOL_SPECIFICATION_TARGET_FIT_PROVIDER_REF)
        _require(
            self.provider_distribution == PROTOCOL_SPECIFICATION_TARGET_FIT_DISTRIBUTION
        )
        _text(self.expected_shape, 2048)
        _digest(self.source_sha256)
        _require(self.source_sha256 == self.request.expected_manifest_sha256)
        _require(type(self.fit) is ProtocolSpecificationTargetFitOutcome)
        _diagnostics(self.diagnostics)
        if self.fit is ProtocolSpecificationTargetFitOutcome.MATCH:
            _text(self.matched_spec_key)
        else:
            _require(self.matched_spec_key is None and bool(self.diagnostics))
        _require(
            type(self.cleanup) is ProtocolSpecificationTargetFitCleanup
            and self.cleanup is ProtocolSpecificationTargetFitCleanup.CLOSED
        )
        _require(
            type(self.effect) is ProtocolSpecificationTargetFitEffect
            and self.effect is ProtocolSpecificationTargetFitEffect.NONE
        )
        _require(
            type(self.observation_grade) is str
            and self.observation_grade == "observed_state"
        )
        _require(type(self.scope) is str and self.scope == "binding_layout_only")
        _fixed(self, _RESULT)

    def to_wire(self) -> dict[str, object]:
        return protocol_specification_target_fit_value_to_payload(self)


@dataclass(frozen=True, slots=True)
class ProtocolSpecificationTargetFitErrorEvidence:
    code: str
    message: str
    request: ProtocolSpecificationTargetFitRequest | None = None
    provider_invoked: bool = False
    cleanup: ProtocolSpecificationTargetFitCleanup = (
        ProtocolSpecificationTargetFitCleanup.NOT_ACQUIRED
    )
    effect: ProtocolSpecificationTargetFitEffect = (
        ProtocolSpecificationTargetFitEffect.NONE
    )
    observed_source_sha256: str | None = None
    configured_root: str | None = None
    path_template: str | None = None
    expected_shape: str | None = None
    observed_fit: ProtocolSpecificationTargetFitOutcome | None = None
    diagnostics: tuple[str, ...] = ()
    reported_result: object | None = None
    report_diagnostics: tuple[str, ...] = ()
    evidence_grade: ProtocolSpecificationTargetFitEvidenceGrade = (
        ProtocolSpecificationTargetFitEvidenceGrade.LOCAL_NOT_OBSERVED
    )
    authorizes_retry: bool = False
    operation_ref: str = PROTOCOL_SPECIFICATION_TARGET_FIT_OPERATION_REF
    contract: str = _ERROR

    def __post_init__(self) -> None:
        _text(self.code)
        _text(self.message)
        if self.request is not None:
            _require(type(self.request) is ProtocolSpecificationTargetFitRequest)
            self.request.__post_init__()
        _require(type(self.provider_invoked) is bool)
        _require(type(self.cleanup) is ProtocolSpecificationTargetFitCleanup)
        _require(type(self.effect) is ProtocolSpecificationTargetFitEffect)
        _require(
            type(self.evidence_grade) is ProtocolSpecificationTargetFitEvidenceGrade
        )
        if self.observed_source_sha256 is not None:
            _digest(self.observed_source_sha256)
        for value in (self.configured_root, self.path_template):
            if value is not None:
                _text(value)
        if self.expected_shape is not None:
            _text(self.expected_shape, 2048)
        _require(
            self.observed_fit is None
            or type(self.observed_fit) is ProtocolSpecificationTargetFitOutcome
        )
        _diagnostics(self.diagnostics)
        _diagnostics(self.report_diagnostics)
        if not self.provider_invoked:
            _require(
                self.evidence_grade
                is ProtocolSpecificationTargetFitEvidenceGrade.LOCAL_NOT_OBSERVED
            )
            _require(
                self.cleanup is ProtocolSpecificationTargetFitCleanup.NOT_ACQUIRED
                and self.effect is ProtocolSpecificationTargetFitEffect.NONE
            )
            _require(
                all(
                    value is None
                    for value in (
                        self.observed_source_sha256,
                        self.configured_root,
                        self.path_template,
                        self.expected_shape,
                        self.observed_fit,
                        self.reported_result,
                    )
                )
            )
            _require(not self.report_diagnostics)
        else:
            _require(
                self.evidence_grade
                is not ProtocolSpecificationTargetFitEvidenceGrade.LOCAL_NOT_OBSERVED
            )
            if (
                self.evidence_grade
                is ProtocolSpecificationTargetFitEvidenceGrade.PROVIDER_OBSERVATION
            ):
                _require(self.reported_result is None and not self.report_diagnostics)
            else:
                _require(
                    self.cleanup is ProtocolSpecificationTargetFitCleanup.UNKNOWN
                    and self.effect is ProtocolSpecificationTargetFitEffect.UNKNOWN
                )
        if self.reported_result is not None:
            object.__setattr__(
                self, "reported_result", _json_tree(self.reported_result, frozen=True)
            )
        _fixed(self, _ERROR)

    def to_wire(self) -> dict[str, object]:
        return protocol_specification_target_fit_value_to_payload(self)


def _fixed(
    value: ProtocolSpecificationTargetFitResult
    | ProtocolSpecificationTargetFitErrorEvidence,
    contract: str,
) -> None:
    _require(type(value.authorizes_retry) is bool and not value.authorizes_retry)
    _require(
        type(value.operation_ref) is str
        and value.operation_ref == PROTOCOL_SPECIFICATION_TARGET_FIT_OPERATION_REF
    )
    _require(type(value.contract) is str and value.contract == contract)


_ROOTS = (
    ProtocolSpecificationTargetFitRequest,
    ProtocolSpecificationTargetFitResult,
    ProtocolSpecificationTargetFitErrorEvidence,
)
_Value = (
    ProtocolSpecificationTargetFitRequest
    | ProtocolSpecificationTargetFitResult
    | ProtocolSpecificationTargetFitErrorEvidence
)
_ENUM_FIELDS = {
    "fit": ProtocolSpecificationTargetFitOutcome,
    "observed_fit": ProtocolSpecificationTargetFitOutcome,
    "cleanup": ProtocolSpecificationTargetFitCleanup,
    "effect": ProtocolSpecificationTargetFitEffect,
    "evidence_grade": ProtocolSpecificationTargetFitEvidenceGrade,
}


def protocol_specification_target_fit_value_to_payload(
    value: object,
) -> dict[str, object]:
    _require(any(type(value) is root for root in _ROOTS))
    value = cast(_Value, value)
    value.__post_init__()
    result = {}
    for field in fields(type(value)):
        item = object.__getattribute__(value, field.name)
        if field.name == "request" and item is not None:
            item = protocol_specification_target_fit_value_to_payload(item)
        elif type(item) in tuple(_ENUM_FIELDS.values()):
            item = cast(StrEnum, item).value
        elif field.name in ("diagnostics", "report_diagnostics"):
            item = list(cast(tuple[str, ...], item))
        elif field.name == "reported_result" and item is not None:
            item = _json_tree(item)
        result[field.name] = item
    _require(
        len(_encoded(result)) <= PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_WIRE_BYTES,
        "target_fit_wire_capacity",
    )
    return result


def protocol_specification_target_fit_value_from_payload[
    T: (
        ProtocolSpecificationTargetFitRequest,
        ProtocolSpecificationTargetFitResult,
        ProtocolSpecificationTargetFitErrorEvidence,
    )
](expected_type: type[T], payload: object) -> T:
    _require(any(expected_type is root for root in _ROOTS) and type(payload) is dict)
    payload = cast(dict[str, object], payload)
    _require(all(type(key) is str for key in payload))
    _require(set(payload) == {field.name for field in fields(expected_type)})
    values = dict(payload)
    for name, item in values.items():
        if name == "request" and item is not None:
            values[name] = protocol_specification_target_fit_value_from_payload(
                ProtocolSpecificationTargetFitRequest, item
            )
        elif name in _ENUM_FIELDS and item is not None:
            _require(type(item) is str)
            try:
                values[name] = _ENUM_FIELDS[name](item)
            except ValueError as error:
                raise ProtocolSpecificationTargetFitValueError(
                    "target_fit_enum_invalid"
                ) from error
        elif name in ("diagnostics", "report_diagnostics"):
            _require(type(item) is list)
            values[name] = tuple(cast(list[object], item))
    try:
        value = cast(Callable[..., T], expected_type)(**values)
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise ProtocolSpecificationTargetFitValueError(
            "target_fit_payload_invalid"
        ) from error
    protocol_specification_target_fit_value_to_payload(value)
    return value


def protocol_specification_target_fit_value_to_json(value: object) -> str:
    return _encoded(protocol_specification_target_fit_value_to_payload(value)).decode(
        "utf-8"
    )


def protocol_specification_target_fit_value_from_json[
    T: (
        ProtocolSpecificationTargetFitRequest,
        ProtocolSpecificationTargetFitResult,
        ProtocolSpecificationTargetFitErrorEvidence,
    )
](expected_type: type[T], body: str) -> T:
    _require(type(body) is str)
    _require(
        len(_utf8(body)) <= PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_WIRE_BYTES,
        "target_fit_wire_capacity",
    )

    def pairs(items):
        result = {}
        for key, item in items:
            _require(key not in result, "target_fit_json_duplicate")
            result[key] = item
        return result

    def constant(_):
        raise ProtocolSpecificationTargetFitValueError("target_fit_json_constant")

    try:
        payload = json.loads(body, object_pairs_hook=pairs, parse_constant=constant)
        return protocol_specification_target_fit_value_from_payload(
            expected_type, payload
        )
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise ProtocolSpecificationTargetFitValueError(
            "target_fit_json_invalid"
        ) from error


def _detached[
    T: (
        ProtocolSpecificationTargetFitRequest,
        ProtocolSpecificationTargetFitResult,
        ProtocolSpecificationTargetFitErrorEvidence,
    )
](value: T) -> T:
    return protocol_specification_target_fit_value_from_payload(
        type(value), protocol_specification_target_fit_value_to_payload(value)
    )


class ProtocolSpecificationTargetFitError(RuntimeError):
    """Validated immutable operation evidence, distinct from admission errors."""

    def __init__(self, evidence: ProtocolSpecificationTargetFitErrorEvidence):
        _require(type(evidence) is ProtocolSpecificationTargetFitErrorEvidence)
        self._evidence = _detached(evidence)
        super().__init__(self._evidence.code)

    @property
    def evidence(self):
        return self._evidence

    @property
    def code(self):
        return self._evidence.code

    @property
    def diagnostics(self):
        return self._evidence.diagnostics

    @property
    def provider_invoked(self):
        return self._evidence.provider_invoked

    @property
    def cleanup(self):
        return self._evidence.cleanup

    @property
    def effect(self):
        return self._evidence.effect

    def to_wire(self):
        return self._evidence.to_wire()


class ProtocolSpecificationTargetFitProvider(Protocol):
    def observe_specification_target_fit(
        self, request: ProtocolSpecificationTargetFitRequest
    ) -> ProtocolSpecificationTargetFitResult: ...


def _unvalidated(value: object) -> tuple[object | None, tuple[str, ...]]:
    try:
        if any(type(value) is root for root in _ROOTS):
            report = {}
            for field in fields(type(cast(_Value, value))):
                item = object.__getattribute__(value, field.name)
                if any(type(item) is root for root in _ROOTS):
                    item = protocol_specification_target_fit_value_to_payload(item)
                elif type(item) in tuple(_ENUM_FIELDS.values()):
                    item = cast(StrEnum, item).value
                report[field.name] = item
            value = report
        return _json_tree(value), ()
    except BaseException:  # noqa: BLE001 -- report capture must preserve interruption/refusal
        return None, ("target_fit_unvalidated_report_omitted",)


class ProtocolSpecificationTargetFitClient:
    def __init__(self, provider: ProtocolSpecificationTargetFitProvider):
        self._provider = provider

    def observe(
        self, request: ProtocolSpecificationTargetFitRequest
    ) -> ProtocolSpecificationTargetFitResult:
        invocation = None
        try:
            _require(type(request) is ProtocolSpecificationTargetFitRequest)
            invocation = _detached(request)
            dispatch = _detached(invocation)
            method = self._provider.observe_specification_target_fit
            _require(callable(method))
        except BaseException as error:
            raise ProtocolSpecificationTargetFitError(
                ProtocolSpecificationTargetFitErrorEvidence(
                    code="target_fit_dispatch_preparation_failed",
                    message="Target-fit observation was not dispatched.",
                    request=invocation,
                    diagnostics=(f"local_failure:{type(error).__name__}",),
                )
            ) from error
        reported = None
        try:
            reported = method(dispatch)
            value = _detached(reported)
            _require(
                type(value) is ProtocolSpecificationTargetFitResult
                and value.request == invocation
                and _detached(request) == invocation,
                "target_fit_result_correlation_failed",
            )
            return cast(ProtocolSpecificationTargetFitResult, value)
        except ProtocolSpecificationTargetFitError as error:
            reported = None
            try:
                _require(type(error) is ProtocolSpecificationTargetFitError)
                reported = object.__getattribute__(error, "_evidence")
                evidence = _detached(
                    cast(ProtocolSpecificationTargetFitErrorEvidence, reported)
                )
                _require(
                    evidence.provider_invoked
                    and evidence.request == invocation
                    and _detached(request) == invocation
                )
            except BaseException as validation_error:  # noqa: BLE001 -- malformed error must remain a typed refusal
                cause = validation_error
            else:
                raise ProtocolSpecificationTargetFitError(evidence) from error
        except BaseException as error:  # noqa: BLE001 -- preserve interruptions after dispatch
            cause = error
        report, diagnostics = _unvalidated(reported)
        raise ProtocolSpecificationTargetFitError(
            ProtocolSpecificationTargetFitErrorEvidence(
                code="target_fit_provider_return_unverified",
                message="Provider observation could not be validated; do not infer effects or retry.",
                request=invocation,
                provider_invoked=True,
                cleanup=ProtocolSpecificationTargetFitCleanup.UNKNOWN,
                effect=ProtocolSpecificationTargetFitEffect.UNKNOWN,
                reported_result=report,
                report_diagnostics=diagnostics,
                evidence_grade=ProtocolSpecificationTargetFitEvidenceGrade.UNVALIDATED_PROVIDER_REPORT,
            )
        ) from cause


__all__ = [
    "PROTOCOL_SPECIFICATION_TARGET_FIT_DISTRIBUTION",
    "PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_REPORT_BYTES",
    "PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_SOURCE_BYTES",
    "PROTOCOL_SPECIFICATION_TARGET_FIT_MAX_WIRE_BYTES",
    "PROTOCOL_SPECIFICATION_TARGET_FIT_OPERATION_REF",
    "PROTOCOL_SPECIFICATION_TARGET_FIT_PROVIDER_OPERATION_REF",
    "PROTOCOL_SPECIFICATION_TARGET_FIT_PROVIDER_REF",
    "ProtocolSpecificationTargetFitCleanup",
    "ProtocolSpecificationTargetFitClient",
    "ProtocolSpecificationTargetFitEffect",
    "ProtocolSpecificationTargetFitError",
    "ProtocolSpecificationTargetFitErrorEvidence",
    "ProtocolSpecificationTargetFitEvidenceGrade",
    "ProtocolSpecificationTargetFitOutcome",
    "ProtocolSpecificationTargetFitProvider",
    "ProtocolSpecificationTargetFitRequest",
    "ProtocolSpecificationTargetFitResult",
    "ProtocolSpecificationTargetFitValueError",
    "protocol_specification_target_fit_value_from_json",
    "protocol_specification_target_fit_value_from_payload",
    "protocol_specification_target_fit_value_to_json",
    "protocol_specification_target_fit_value_to_payload",
]
