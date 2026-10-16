"""Original owner planning input for a catalog-backed single product.

The factory supplies meaning; the original selected-source issuer supplies
bytes and currentness. Neither a catalog nor declaration inventory is a source.
The caller owns the semantic-input host and original source-context lifetime.
"""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from typing import Any, cast

from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    SemanticPackageCoordinate,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DependencyPlanningInputCodec,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody

from . import direct_epoch_tracking as hooks
from . import direct_host
from .declaration_host import _selected_policy_source
from .selected_participant_calculation import selected_qualified_occurrence


def _owner(host, policy, contribution):
    state = direct_host._state(host)
    record = direct_host._POLICIES.get(policy)
    if record is None or len(record) != 8 or record[0] is not host:
        raise ContractViolation("original selected product policy required")
    epoch = hooks._BINDINGS.get(host)
    if epoch is None or record[6] is not epoch:
        raise ContractViolation("original product planning epoch required")
    original = products.read_selected_provider_product_contribution(contribution)
    selected = record[4]
    _, package, _, declaration = selected_qualified_occurrence(
        record[5].closure,
        record[7],
        (selected.scope_key, selected.module_id, selected.package_id),
    )
    retained = state.product_retention
    if retained is None:
        raise ContractViolation("original product retention required")
    registration, _entry = retained.validate_declared_profile(
        declaration,
        package_kind=package.package_kind,
    )
    if registration is not original.expected.registration:
        raise ContractViolation("planning producer belongs to another selected product")
    declaration, producer = products.read_selected_provider_product_planning_input(
        contribution
    )
    return state, record, epoch, declaration, producer


def read_product_planning_input_declaration(host, policy, contribution):
    """Detached preparation metadata; supplies no source or execution admission."""
    from copy import deepcopy

    with _selected_policy_source(host, policy):
        return deepcopy(_owner(host, policy, contribution)[3])


def register_product_planning_input_producer(host, policy, contribution, *, input_host):
    """Register only the factory producer and original host-owned source methods."""
    if type(input_host) is not inputs.SemanticInputProducerHost:
        raise TypeError("exact semantic-input host required")
    with _selected_policy_source(host, policy):
        state, _, _, declaration, producer = _owner(host, policy, contribution)
        issuer = state.methods["scope"].receiver
        validator = direct_host._capture(issuer, "validate_semantic_input_source")
        reader = direct_host._capture(issuer, "read_semantic_input_sources")
        context = (
            direct_host._capture(issuer, "validate_semantic_input_context")
            if declaration.context_contracts
            else None
        )
        return inputs.register_semantic_input_producer(
            input_host,
            declaration=declaration,
            producer=producer,
            validator=cast(inputs.SemanticInputSourceValidator, issuer),
            validator_entrance=validator.method,
            reader=cast(inputs.SemanticInputSourceReader, issuer),
            reader_entrance=reader.method,
            context_validator_entrance=None if context is None else context.method,
            retain_result=True,
        )


def _registration(host, policy, contribution, input_host, registration):
    state, record, epoch, declaration, producer = _owner(host, policy, contribution)
    input_host._check_process()
    original = inputs._registration_state(input_host, registration)
    issuer = state.methods["scope"].receiver
    if (
        original.declaration is not declaration
        or original.producer is not producer
        or original.validator is not issuer
        or original.reader is not issuer
        or not original.retain_result
    ):
        raise ContractViolation("original product planning registration differs")
    return record, epoch


@dataclass
class _Source:
    host: direct_host.DirectValidationHost
    policy: direct_host.AdmittedRegistryPolicy
    contribution: products.SelectedProviderProductContribution
    input_host: inputs.SemanticInputProducerHost
    registration: inputs.AdmittedSemanticInputProducerRegistration
    expected: inputs.SemanticInputProductionExpectation
    result: SemanticBody
    evidence: tuple
    tree: Any
    record: tuple
    binding: Any
    pid: int
    terminal: bool = False
    active: int = 0

    @property
    def package(self):
        return self.expected.package_identity.package

    def check_locked(self, source, guard):
        if (
            _SOURCES.get(source) is not self
            or self.terminal
            or self.pid != os.getpid()
            or direct_host._POLICIES.get(self.policy) is not self.record
            or hooks._BINDINGS.get(self.host) is not self.binding
            or self.input_host._closed
        ):
            raise ContractViolation("original product planning source retired")
        if inspect.getattr_static(source, "read_dependencies") is not _READ:
            raise ContractViolation("original product planning reader substituted")
        if self.evidence[0] is not self.expected or self.evidence[1] is not self.result:
            raise ContractViolation("original planning evidence substituted")
        self.tree.check(self.evidence)
        # In-place checks only. Full source/producer validation runs outside exclusion.
        products._state(self.contribution)
        registered = self.input_host._registrations.get(self.registration)
        if registered is None or registered.closed or not registered.retain_result:
            raise ContractViolation("original planning input registration retired")
        hooks._original(self.binding, self.host, guard)


_SOURCES = {}
MAX_PRODUCT_PLANNING_SOURCES = 256


class RetainedProductPlanningDependencySource(direct_host._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("product planning source is sealed")

    def read_dependencies(self, package):
        state = _state(self)
        if type(package) is not SemanticPackageCoordinate or package != state.package:
            raise ContractViolation("original product planning package differs")
        state.active += 1
        try:
            with _selected_policy_source(state.host, state.policy):
                record, epoch = _registration(
                    state.host,
                    state.policy,
                    state.contribution,
                    state.input_host,
                    state.registration,
                )
                if record is not state.record or epoch is not state.binding:
                    raise ContractViolation("original product planning origin changed")
                inputs.validate_registered_semantic_input_result(
                    state.input_host,
                    state.registration,
                    source_admission=state.record[1],
                    expected=state.expected,
                    result=state.result,
                )
                value = _planning_value(state)
                with hooks._guard(state.binding) as guard:
                    state.check_locked(self, guard)
            return value
        except BaseException:
            state.terminal = True
            raise
        finally:
            state.active -= 1


_READ = RetainedProductPlanningDependencySource.read_dependencies


def _state(source):
    if type(source) is not RetainedProductPlanningDependencySource:
        raise TypeError("exact retained product planning source required")
    state = _SOURCES.get(source)
    if state is None or state.terminal or state.pid != os.getpid():
        raise ContractViolation("foreign or terminal product planning source")
    try:
        state.tree.check(state.evidence)
        if (
            state.expected is not state.evidence[0]
            or state.result is not state.evidence[1]
        ):
            raise ContractViolation("original product planning evidence changed")
    except BaseException:
        state.terminal = True
        raise
    if inspect.getattr_static(source, "read_dependencies") is not _READ:
        state.terminal = True
        raise ContractViolation("original product planning reader substituted")
    return state


def _planning_value(state):
    value = DependencyPlanningInputCodec().decode(state.result.canonical_body)
    if (
        value.package != state.package
        or value.source_identity_digest != state.record[4].source_identity_digest
    ):
        raise ContractViolation("owner planning input package/source differs")
    return value


async def execute_product_planning_input(
    host,
    policy,
    contribution,
    *,
    input_host,
    registration,
    expected,
):
    """Execute one original source-backed producer, retaining its exact return.

    The running original epoch obligation spans the awaited owner call. No
    owner call or source I/O runs under exclusion; publication cannot retire
    this epoch during that call. Semantic-input execution enforces single use.
    """
    if type(input_host) is not inputs.SemanticInputProducerHost:
        raise TypeError("exact semantic-input host required")
    if type(expected) is not inputs.SemanticInputProductionExpectation:
        raise TypeError("exact original source expectation required")
    if len(_SOURCES) >= MAX_PRODUCT_PLANNING_SOURCES:
        raise ContractViolation("product planning source retention bound exceeded")
    source = object.__new__(RetainedProductPlanningDependencySource)
    try:
        with _selected_policy_source(host, policy):
            record, epoch = _registration(
                host, policy, contribution, input_host, registration
            )
            if (
                expected.source_identity is not record[1]
                or expected.operation_identity is not epoch.tracker.parent
            ):
                raise ContractViolation(
                    "original selected planning source/parent differs"
                )
            result = await inputs.execute_registered_semantic_input(
                input_host,
                registration,
                source_admission=record[1],
                expected=expected,
            )
            evidence = (expected, result)
            state = _Source(
                host,
                policy,
                contribution,
                input_host,
                registration,
                expected,
                result,
                evidence,
                inputs._result_tree(evidence),
                record,
                epoch,
                os.getpid(),
            )
            _planning_value(state)
            with hooks._guard(epoch) as guard:
                # Cross-host threads share the same bounded Code retention.
                with direct_host._LOCK:
                    if len(_SOURCES) >= MAX_PRODUCT_PLANNING_SOURCES:
                        raise ContractViolation(
                            "product planning source retention bound exceeded"
                        )
                    # Keep custody through uncertain release; close can retry.
                    _SOURCES[source] = state
                state.check_locked(source, guard)
    except BaseException:
        retained = _SOURCES.get(source)
        if retained is not None:
            retained.terminal = True
        raise
    return source


def close_product_planning_sources(host):
    """Drop Code references after confirmed exclusion release; borrow no cleanup."""
    if type(host) is not direct_host.DirectValidationHost:
        raise TypeError("exact original direct host required")
    records = tuple(
        (source, state) for source, state in _SOURCES.items() if state.host is host
    )
    for source, state in records:
        if state.pid != os.getpid():
            raise ContractViolation("product planning cleanup belongs to another process")
        state.terminal = True
        if state.active:
            raise ContractViolation("original product planning read is active")
        released = hooks._GuardRelease()
        try:
            with hooks._guard(state.binding, release_state=released):
                pass
        except ContractViolation:
            # Epoch retirement is not a reason to retain payload forever. The
            # original release must still complete and pass its identity check.
            if not released.confirmed:
                raise
        finally:
            if released.confirmed:
                _SOURCES.pop(source, None)
                # Stale compositions may retain this terminal record. Clear
                # its borrowed payload only after release, with no owner calls.
                for name in (
                    "host",
                    "policy",
                    "contribution",
                    "input_host",
                    "registration",
                    "expected",
                    "result",
                    "tree",
                    "record",
                    "binding",
                    "evidence",
                ):
                    object.__setattr__(state, name, None)
