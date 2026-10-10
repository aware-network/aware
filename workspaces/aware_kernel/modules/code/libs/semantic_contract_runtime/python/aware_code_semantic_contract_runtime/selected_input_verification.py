"""Shared input correspondence and original selected-invocation verification.

Composition values never grant authority. Providers receive SelectedInvocationUse
and call the two verification/cleanup entrances; they must not receive borrowed
source/product assembly references or nominate a validator.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass

from .contracts import ContractViolation
from .runtime import SemanticBody
from .selected_provider import _clear_input_rejection_frames
from .semantic_input_producer import (
    AdmittedSemanticInputProducerRegistration,
    SemanticInputProducerHost,
    SemanticInputProductionExpectation,
    _check_result_slots,
    _result_tree,
)

MAX_SELECTED_INPUT_SOURCE_RESULTS = 32
MAX_SELECTED_INPUT_BYTES = 8_388_608
MAX_SELECTED_INPUT_RETAINED_BODY_BYTES = 33_554_432
MAX_SELECTED_INPUT_SOURCES = 512


def _body_bytes(value: SemanticBody) -> int:
    if type(value) is not SemanticBody:
        raise TypeError("exact selected input body required")
    _check_result_slots(SemanticBody)
    if type(value.canonical_body) is not bytes:
        raise TypeError("exact selected input bytes required")
    if len(value.canonical_body) > MAX_SELECTED_INPUT_BYTES:
        raise ContractViolation("selected input body byte bound exceeded")
    return len(value.canonical_body)


def _body(value: SemanticBody) -> None:
    _body_bytes(value)
    _result_tree(value).check(value)
    value.__post_init__()


def _index(value: int, length: int) -> int:
    if type(value) is not int or not 0 <= value < length:
        raise ContractViolation("selected input original body index differs")
    return value


@dataclass(frozen=True, slots=True)
class SelectedInputSourceResult:
    host: SemanticInputProducerHost
    registration: AdmittedSemanticInputProducerRegistration
    source_admission: object
    expected: SemanticInputProductionExpectation
    result: SemanticBody

    def __post_init__(self) -> None:
        if type(self.host) is not SemanticInputProducerHost:
            raise TypeError("exact source producer host required")
        if type(self.registration) is not AdmittedSemanticInputProducerRegistration:
            raise TypeError("exact source producer registration required")
        if type(self.expected) is not SemanticInputProductionExpectation:
            raise TypeError("exact source production expectation required")
        _result_tree(self.expected).check(self.expected)
        self.expected.__post_init__()
        if self.expected.source_identity is not self.source_admission:
            raise ContractViolation("source expectation admission differs")
        _body(self.result)


@dataclass(frozen=True, slots=True)
class SelectedInputVerificationAssembly:
    semantic_input: object
    input_bodies: tuple[SemanticBody, ...]
    source_results: tuple[SelectedInputSourceResult, ...]
    _: KW_ONLY
    source_input_roles: tuple[tuple[str, int], ...] = ()
    context_input_roles: tuple[tuple[str, int, int], ...] = ()
    dependency_products: object | None = None
    dependency_input_role: str | None = None

    def __post_init__(self) -> None:
        if (
            type(self.input_bodies) is not tuple
            or type(self.source_results) is not tuple
        ):
            raise TypeError("exact selected input/source tuples required")
        if (
            not self.input_bodies
            or len(self.input_bodies) > MAX_SELECTED_INPUT_SOURCE_RESULTS
            or len(self.source_results) > MAX_SELECTED_INPUT_SOURCE_RESULTS
        ):
            raise ContractViolation("selected input/source count exceeds bound")
        bodies: dict[str, SemanticBody] = {}
        total = sum(_body_bytes(body) for body in self.input_bodies)
        if total > MAX_SELECTED_INPUT_BYTES:
            raise ContractViolation("complete selected input byte bound exceeded")
        retained = total
        for body in self.input_bodies:
            _body(body)
            role = body.coordinate.role
            if role in bodies:
                raise ContractViolation("selected input role is duplicate")
            bodies[role] = body
        seen_results: list[SemanticBody] = []
        for original in self.source_results:
            if type(original) is not SelectedInputSourceResult:
                raise TypeError("exact original source result binding required")
            original.__post_init__()
            if any(body is original.result for body in seen_results):
                raise ContractViolation("original source result is duplicate")
            seen_results.append(original.result)
            expected = original.expected
            size = sum(
                item.coordinate.size_bytes for item in expected.source_coordinates
            )
            size += sum(len(body.canonical_body) for body in expected.context_bodies)
            if (
                len(expected.source_coordinates) > MAX_SELECTED_INPUT_SOURCES
                or size > MAX_SELECTED_INPUT_BYTES
            ):
                raise ContractViolation("original source input bound exceeded")
            retained += size + len(original.result.canonical_body)
        if retained > MAX_SELECTED_INPUT_RETAINED_BODY_BYTES:
            raise ContractViolation("retained selected input byte bound exceeded")
        if (
            type(self.source_input_roles) is not tuple
            or type(self.context_input_roles) is not tuple
        ):
            raise TypeError("exact selected input role tuples required")
        used: set[str] = set()

        def join(role: str, original: SemanticBody) -> None:
            if type(role) is not str or role not in bodies or role in used:
                raise ContractViolation("selected input role partition differs")
            if bodies[role] is not original:
                raise ContractViolation("selected input body is not original")
            used.add(role)

        for row in self.source_input_roles:
            if type(row) is not tuple or len(row) != 2:
                raise TypeError("exact source role/index pair required")
            role, index = row
            original = self.source_results[_index(index, len(self.source_results))]
            join(role, original.result)
        for row in self.context_input_roles:
            if type(row) is not tuple or len(row) != 3:
                raise TypeError("exact context role/source/index triple required")
            role, index, context_index = row
            original = self.source_results[_index(index, len(self.source_results))]
            contexts = original.expected.context_bodies
            join(role, contexts[_index(context_index, len(contexts))])
        if self.dependency_products is None:
            if self.dependency_input_role is not None:
                raise ContractViolation("dependency role lacks original products")
        else:
            role = self.dependency_input_role
            if type(role) is not str or role not in bodies or role in used:
                raise ContractViolation("dependency input role differs")
            # Policy composition authenticates the admission and reread. This
            # shared value cannot appoint or invoke a reader, or decode it.
            used.add(role)
        if used != set(bodies):
            raise ContractViolation("complete selected input partition required")


def validate_selected_invocation_inputs(use: object, provider: object) -> None:
    """Fresh original-input checks for this exact selected invocation.

    Successful completion proves execution, not later input currentness. This
    entrance reuses the lifecycle bound by authenticated Code composition.
    """
    try:
        from .selected_provider import _selected_invocation_inputs

        _selected_invocation_inputs(use, provider)
    except BaseException as error:
        provider = use = None
        _clear_input_rejection_frames(error, __file__)
        raise


def release_selected_invocation_input_verification(use: object, provider: object) -> None:
    """Release delivery-owned references; borrowed issuer resources are untouched.

    Composition also retires independently on failure, registration, host and
    epoch closure. This entrance does not require source/product currentness.
    """
    try:
        from .selected_provider import _selected_invocation_inputs

        _selected_invocation_inputs(use, provider, release=True)
    except BaseException as error:
        provider = use = None
        _clear_input_rejection_frames(error, __file__)
        raise
