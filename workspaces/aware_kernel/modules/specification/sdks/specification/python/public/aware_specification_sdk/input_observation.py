"""Bounded input values and explicit read provider; no source or write authority."""

import hashlib
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Protocol, cast

SPECIFICATION_INPUT_LIMIT = 2 * 1024 * 1024
SPECIFICATION_INPUT_WIRE_LIMIT = SPECIFICATION_INPUT_LIMIT * 2 + 65536
SPECIFICATION_INPUT_OBSERVE_OPERATION_REF = "specification_sdk.observe_draft_input"
SPECIFICATION_INPUT_OBSERVE_PROVIDER_OPERATION_REF = "specification.input.observe"


def _text(value: object, limit: int = 8192) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or "\x00" in value
        or len(value.encode("utf-8")) > limit
    ):
        raise ValueError("invalid_input_text")
    return value


def _body(value: object) -> bytes:
    if type(value) is not str or len(value) > SPECIFICATION_INPUT_LIMIT * 2:
        raise ValueError("invalid_input_bytes")
    body = bytes.fromhex(value)
    if body.hex() != value:
        raise ValueError("noncanonical_input_bytes")
    return body


class SpecificationInputCleanup(StrEnum):
    NOT_ACQUIRED = "not_acquired"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SpecificationInputObservationRequest:
    source_ref: str
    base_ref: str

    def __post_init__(self) -> None:
        _text(self.source_ref)
        _text(self.base_ref)


@dataclass(frozen=True, slots=True)
class SpecificationInputObservationResult:
    request: SpecificationInputObservationRequest
    source_ref: str
    provider_ref: str
    provider_distribution: str
    provider_version: str
    body_hex: str
    byte_count: int
    source_sha256: str
    cleanup: SpecificationInputCleanup = SpecificationInputCleanup.CLOSED
    observation_grade: str = "observed_state"

    def __post_init__(self) -> None:
        if type(self.request) is not SpecificationInputObservationRequest:
            raise ValueError("invalid_input_request")
        object.__setattr__(self, "request", replace(self.request))
        _text(self.source_ref)
        for value in (
            self.provider_ref,
            self.provider_distribution,
            self.provider_version,
        ):
            _text(value, 1024)
        body = _body(self.body_hex)
        if type(self.byte_count) is not int or self.byte_count != len(body):
            raise ValueError("input_byte_count_mismatch")
        if (
            type(self.source_sha256) is not str
            or self.source_sha256 != "sha256:" + hashlib.sha256(body).hexdigest()
        ):
            raise ValueError("input_byte_digest_mismatch")
        if self.cleanup is not SpecificationInputCleanup.CLOSED:
            raise ValueError("input_cleanup_unverified")
        if (
            type(self.observation_grade) is not str
            or self.observation_grade != "observed_state"
        ):
            raise ValueError("invalid_input_observation_grade")

    @property
    def body(self) -> bytes:
        return _body(self.body_hex)


@dataclass(slots=True)
class SpecificationInputObservationError(ValueError):
    code: str
    request: SpecificationInputObservationRequest | None = None
    provider_invoked: bool = False
    cleanup: SpecificationInputCleanup = SpecificationInputCleanup.NOT_ACQUIRED
    effect: str = "none"
    diagnostics: tuple[str, ...] = ()
    source_ref: str | None = None
    observed_body_hex: str | None = None
    reported_result_type: str | None = None

    def __post_init__(self) -> None:
        _text(self.code, 1024)
        if self.request is not None:
            if type(self.request) is not SpecificationInputObservationRequest:
                raise ValueError("invalid_input_error_request")
            self.request = replace(self.request)
        if type(self.provider_invoked) is not bool:
            raise ValueError("invalid_input_invocation")
        if type(self.cleanup) is not SpecificationInputCleanup:
            raise ValueError("invalid_input_cleanup")
        if type(self.effect) is not str or self.effect not in ("none", "unknown"):
            raise ValueError("invalid_input_effect")
        if not self.provider_invoked and (
            self.cleanup is not SpecificationInputCleanup.NOT_ACQUIRED
            or self.effect != "none"
            or self.observed_body_hex is not None
        ):
            raise ValueError("invalid_preinvocation_input_evidence")
        if type(self.diagnostics) is not tuple or len(self.diagnostics) > 16:
            raise ValueError("invalid_input_diagnostics")
        for value in self.diagnostics:
            _text(value, 1024)
        if self.source_ref is not None:
            _text(self.source_ref)
        if self.observed_body_hex is not None:
            _body(self.observed_body_hex)
        if self.reported_result_type is not None:
            _text(self.reported_result_type, 1024)
        ValueError.__init__(self, self.code)


class SpecificationInputObservationProvider(Protocol):
    def observe_draft_input(
        self, request: SpecificationInputObservationRequest
    ) -> SpecificationInputObservationResult: ...


@dataclass(frozen=True, slots=True)
class SpecificationInputObservationClient:
    provider: SpecificationInputObservationProvider

    def observe_draft_input(
        self, request: SpecificationInputObservationRequest
    ) -> SpecificationInputObservationResult:
        try:
            if type(request) is not SpecificationInputObservationRequest:
                raise ValueError("invalid_input_request")
            original = replace(request)
        except BaseException as error:
            raise SpecificationInputObservationError("input_request_invalid") from error
        try:
            prepared = replace(original)
        except BaseException as error:
            raise SpecificationInputObservationError(
                "input_request_invalid", request=original
            ) from error
        try:
            value = self.provider.observe_draft_input(prepared)
        except SpecificationInputObservationError as error:
            try:
                checked = replace(error)
                if checked.request != original or not checked.provider_invoked:
                    raise ValueError("uncorrelated_input_error")
            except BaseException as invalid:
                raise _unknown(original, error) from invalid
            raise checked from error
        except BaseException as error:
            raise _unknown(original, error) from error
        try:
            if type(value) is not SpecificationInputObservationResult:
                raise ValueError("invalid_input_result")
            checked = replace(value)
            if checked.request != original:
                raise ValueError("uncorrelated_input_result")
        except BaseException as error:
            raise _unknown(original, value) from error
        return checked


def _unknown(
    request: SpecificationInputObservationRequest, value: object
) -> SpecificationInputObservationError:
    try:
        name = (type(value).__module__ + "." + type(value).__name__).encode("utf-8")
        report_type = name[:1024].decode("utf-8", errors="ignore")
    except BaseException:  # noqa: BLE001 - malformed report metadata cannot hide original refusal
        report_type = "unavailable"
    return SpecificationInputObservationError(
        "input_provider_report_invalid",
        request=request,
        provider_invoked=True,
        cleanup=SpecificationInputCleanup.UNKNOWN,
        effect="unknown",
        diagnostics=("provider_report_unvalidated",),
        reported_result_type=report_type,
    )


def encode_specification_input_value(
    value: SpecificationInputObservationRequest
    | SpecificationInputObservationResult
    | SpecificationInputObservationError,
) -> bytes:
    from .wire import encode_specification_value

    if type(value) not in _INPUT_VALUES:
        raise SpecificationInputObservationError("invalid_input_wire_value")
    try:
        body = encode_specification_value(value)
    except ValueError as error:
        raise SpecificationInputObservationError("invalid_input_wire_value") from error
    if len(body) > SPECIFICATION_INPUT_WIRE_LIMIT:
        raise SpecificationInputObservationError("input_wire_limit_exceeded")
    return body


def decode_specification_input_value(
    body: bytes,
) -> (
    SpecificationInputObservationRequest
    | SpecificationInputObservationResult
    | SpecificationInputObservationError
):
    from .wire import decode_specification_value

    if type(body) is not bytes or len(body) > SPECIFICATION_INPUT_WIRE_LIMIT:
        raise SpecificationInputObservationError("input_wire_limit_exceeded")
    try:
        value = decode_specification_value(body)
    except ValueError as error:
        raise SpecificationInputObservationError("invalid_input_wire_value") from error
    if type(value) not in _INPUT_VALUES:
        raise SpecificationInputObservationError("invalid_input_wire_value")
    return cast(
        SpecificationInputObservationRequest
        | SpecificationInputObservationResult
        | SpecificationInputObservationError,
        value,
    )


_INPUT_VALUES = (
    SpecificationInputObservationRequest,
    SpecificationInputObservationResult,
    SpecificationInputObservationError,
)
