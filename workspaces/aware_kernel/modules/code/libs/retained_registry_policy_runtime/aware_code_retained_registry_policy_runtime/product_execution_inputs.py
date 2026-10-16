"""Fixed-host intake of original source-backed product execution inputs.

Factory recipes supply all owner functions and opaque contracts. The caller
owns source expectations, input hosts, node associations and prior-head proof.
No owner module discovery, source parsing, graph or publication occurs here.
"""

from __future__ import annotations

from typing import Any, cast

from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.product_execution_input_plan import (
    ProductExecutionInputAssemblyInput,
)
from aware_code_semantic_contract_runtime.selected_input_verification import (
    SelectedInputSourceResult,
    SelectedInputVerificationAssembly,
)

from . import direct_epoch_tracking as hooks
from . import direct_host
from .declaration_host import _selected_policy_source
from .selected_participant_calculation import selected_qualified_occurrence


def _owner(host, policy, contribution):
    state = direct_host._state(host)
    record = direct_host._POLICIES.get(policy)
    if record is None or len(record) != 8 or record[0] is not host:
        raise ContractViolation("original execution-input selected policy required")
    epoch = hooks._BINDINGS.get(host)
    if epoch is None or record[6] is not epoch:
        raise ContractViolation("original execution-input epoch required")
    original = products.read_selected_provider_product_contribution(contribution)
    expected = record[4]
    _, package, _, declaration = selected_qualified_occurrence(
        record[5].closure,
        record[7],
        (expected.scope_key, expected.module_id, expected.package_id),
    )
    if state.product_retention is None:
        raise ContractViolation("original product retention required")
    registration, _ = state.product_retention.validate_declared_profile(
        declaration,
        package_kind=package.package_kind,
    )
    if registration is not original.expected.registration:
        raise ContractViolation("execution inputs belong to another selected product")
    return state, record, epoch, registration


def enroll_product_execution_inputs(host, policy, contribution):
    """Invoke the original factory recipe producer once, outside exclusion."""
    with _selected_policy_source(host, policy):
        _owner(host, policy, contribution)
        plan = products.produce_selected_provider_product_execution_inputs(contribution)
        _owner(host, policy, contribution)
        return plan


def read_product_execution_inputs(host, policy, contribution):
    with _selected_policy_source(host, policy):
        _owner(host, policy, contribution)
        return products.read_selected_provider_product_execution_inputs(contribution)


def register_product_execution_input_producers(
    host, policy, contribution, *, input_host
):
    """Register factory functions against the exact host-owned source methods."""
    if type(input_host) is not inputs.SemanticInputProducerHost:
        raise TypeError("exact semantic-input host required")
    with _selected_policy_source(host, policy):
        state, _, _, _ = _owner(host, policy, contribution)
        plan = products.read_selected_provider_product_execution_inputs(contribution)
        issuer = state.methods["scope"].receiver
        validator = direct_host._capture(issuer, "validate_semantic_input_source")
        reader = direct_host._capture(issuer, "read_semantic_input_sources")
        registrations = []
        try:
            for step in plan.steps:
                context = (
                    direct_host._capture(issuer, "validate_semantic_input_context")
                    if step.ordinary.context_contracts
                    else None
                )
                kwargs: dict[str, Any] = {
                    "producer": step.producer,
                    "validator": cast(inputs.SemanticInputSourceValidator, issuer),
                    "validator_entrance": validator.method,
                    "reader": cast(inputs.SemanticInputSourceReader, issuer),
                    "reader_entrance": reader.method,
                    "context_validator_entrance": None
                    if context is None
                    else context.method,
                    "retain_result": True,
                }
                if (
                    type(step.declaration)
                    is inputs.SemanticInputJoinedProducerDeclaration
                ):
                    registration = inputs.register_joined_semantic_input_producer(
                        input_host, declaration=step.declaration, **kwargs
                    )
                else:
                    registration = inputs.register_semantic_input_producer(
                        input_host, declaration=step.ordinary, **kwargs
                    )
                registrations.append(registration)
            products.read_selected_provider_product_execution_inputs(contribution)
            return tuple(registrations)
        except BaseException:
            # Retire only registrations made by this entrance, not the host.
            for registration in registrations:
                inputs.close_semantic_input_producer_registration(
                    input_host, registration
                )
            raise


def _check_expected(record, epoch, selected_binding, plan, expectations):
    if type(expectations) is not tuple or len(expectations) != len(plan.steps):
        raise ContractViolation("complete ordered input expectations required")
    package = None
    for step, expected in zip(plan.steps, expectations, strict=True):
        if type(expected) is not inputs.SemanticInputProductionExpectation:
            raise TypeError("exact original input expectation required")
        inputs._result_tree(expected).check(expected)
        expected.__post_init__()
        if (
            expected.source_identity is not record[1]
            or expected.operation_identity is not epoch.tracker.parent
            or expected.stage != step.stage
        ):
            raise ContractViolation("original input source/parent/stage differs")
        if package is None:
            package = expected.package_identity
        elif (
            expected.package_identity != package
            or expected.operation_ref != expectations[0].operation_ref
        ):
            raise ContractViolation("input package/operation differs")
        wanted = []
        for scope, contract in zip(
            step.source_scopes, step.ordinary.source_contracts, strict=True
        ):
            for candidate in selected_binding.candidates.candidates:
                if not scope.suffixes or candidate.relative_path.endswith(
                    scope.suffixes
                ):
                    wanted.append(
                        (
                            candidate.relative_path,
                            contract.role,
                            contract.contract,
                            candidate.content_digest,
                        )
                    )
        wanted.sort(key=lambda row: row[0].encode())
        if len({row[0] for row in wanted}) != len(wanted):
            raise ContractViolation("input source scopes overlap")
        actual = tuple(
            (
                source.relative_path,
                source.coordinate.role,
                source.coordinate.contract,
                source.coordinate.digest,
            )
            for source in expected.source_coordinates
        )
        if actual != tuple(wanted) or not actual:
            raise ContractViolation("input source selection is incomplete or foreign")


def _registrations(state, plan, input_host, registrations):
    if type(input_host) is not inputs.SemanticInputProducerHost:
        raise TypeError("exact semantic-input host required")
    if type(registrations) is not tuple or len(registrations) != len(plan.steps):
        raise ContractViolation("complete ordered input registrations required")
    input_host._check_process()
    issuer = state.methods["scope"].receiver
    for step, registration in zip(plan.steps, registrations, strict=True):
        read = (
            inputs._joined_registration_state
            if type(step.declaration) is inputs.SemanticInputJoinedProducerDeclaration
            else inputs._registration_state
        )
        registered = read(input_host, registration)
        if (
            registered.declaration is not step.declaration
            or registered.producer is not step.producer
            or registered.validator is not issuer
            or registered.reader is not issuer
            or registered.retain_result is not True
        ):
            raise ContractViolation("original execution-input registration differs")


async def execute_product_execution_inputs(
    host,
    policy,
    contribution,
    *,
    input_host,
    registrations,
    expectations,
):
    """Open the original join before dispatch; preserve each exact result body."""
    with _selected_policy_source(host, policy) as (_, _, _, source):
        state, record, epoch, _ = _owner(host, policy, contribution)
        plan = products.read_selected_provider_product_execution_inputs(contribution)
        _registrations(state, plan, input_host, registrations)
        _check_expected(record, epoch, source, plan, expectations)
        final = plan.steps[-1]
        join = None
        if type(final.declaration) is inputs.SemanticInputJoinedProducerDeclaration:
            join = inputs.open_semantic_input_role_join(
                input_host,
                joined_registration=registrations[-1],
                joined_expected=expectations[-1],
                source_admission=record[1],
                predecessors=tuple(
                    inputs.SemanticInputRoleJoinPredecessor(registration, expected)
                    for registration, expected in zip(
                        registrations[:-1], expectations[:-1], strict=True
                    )
                ),
            )
        results = []
        try:
            for step, registration, expected in zip(
                plan.steps, registrations, expectations, strict=True
            ):
                if (
                    type(step.declaration)
                    is inputs.SemanticInputJoinedProducerDeclaration
                ):
                    assert join is not None
                    result = await inputs.execute_registered_joined_semantic_input(
                        input_host,
                        registration,
                        role_join=join,
                        source_admission=record[1],
                        expected=expected,
                    )
                else:
                    result = await inputs.execute_registered_semantic_input(
                        input_host,
                        registration,
                        source_admission=record[1],
                        expected=expected,
                    )
                products.read_selected_provider_product_execution_inputs(contribution)
                results.append(result)
        except BaseException:
            if join is not None:
                inputs.close_semantic_input_role_join(input_host, join)
            raise
        return tuple(results)


def assemble_product_execution_inputs(
    host,
    policy,
    contribution,
    *,
    input_host,
    registrations,
    expectations,
    results,
    invocation_ref,
    idempotency_key,
    predecessor_body=None,
):
    """Validate original results around the factory assembler; issue no node use."""
    with _selected_policy_source(host, policy) as (_, _, _, source):
        state, record, epoch, selected_registration = _owner(host, policy, contribution)
        plan = products.read_selected_provider_product_execution_inputs(contribution)
        _registrations(state, plan, input_host, registrations)
        _check_expected(record, epoch, source, plan, expectations)
        if type(results) is not tuple or len(results) != len(plan.steps):
            raise ContractViolation("complete original result tuple required")
        originals = tuple(
            SelectedInputSourceResult(
                input_host, registration, record[1], expected, result
            )
            for registration, expected, result in zip(
                registrations, expectations, results, strict=True
            )
        )

        def validate():
            for original in originals:
                inputs.validate_registered_semantic_input_result(
                    input_host,
                    original.registration,
                    source_admission=record[1],
                    expected=original.expected,
                    result=original.result,
                )
            products.read_selected_provider_product_execution_inputs(contribution)

        validate()
        bodies = tuple(results[index] for index in plan.input_result_indices)
        value = ProductExecutionInputAssemblyInput(
            expectations[0].package_identity.package,
            invocation_ref,
            idempotency_key,
            bodies,
            predecessor_body,
        )
        value.__post_init__()
        semantic_input = plan.assembler(value)
        validate()
        registered = selected._registration_state(selected_registration)
        closure = registered.input_closure_entrance(semantic_input)
        if type(closure) is not selected.SelectedProviderInvocationClosure:
            raise TypeError("exact original selected closure required")
        closure.__post_init__()
        if (
            len(closure.input_bodies) != len(bodies)
            or any(
                actual is not original
                for actual, original in zip(closure.input_bodies, bodies, strict=True)
            )
            or closure.invocation.target_package != value.package
            or closure.invocation.invocation_ref != invocation_ref
            or closure.invocation.idempotency_key != idempotency_key
            or closure.predecessor_body is not predecessor_body
        ):
            raise ContractViolation(
                "assembler changed original input/prior correspondence"
            )
        validate()
        roles = tuple(
            (body.coordinate.role, index)
            for body, index in zip(bodies, plan.input_result_indices, strict=True)
        )
        return SelectedInputVerificationAssembly(
            semantic_input, closure.input_bodies, originals, source_input_roles=roles
        )


def bind_product_execution_input_origin(host, policy, contribution):
    """Factory-recipe-qualified input validation for ordinary graph products.

    A semantic owner's optional observation hook is not required or fabricated.
    Original factory node validators and runtime-owned completion remain required.
    """
    from .product_execution import _bind_selected_input_verification_origin

    with _selected_policy_source(host, policy):
        _, _, _, registration = _owner(host, policy, contribution)
        products.read_selected_provider_product_execution_inputs(contribution)
        return _bind_selected_input_verification_origin(
            host, registration, execution_inputs=(policy, contribution)
        )


def read_product_execution_input_closure(host, policy, contribution, assembly):
    """Read through the original adapter; opaque owner inputs stay opaque.

    This is an existing-closure projection, not an execution or publication
    grant. Original source results and recipe are checked on both sides.
    """
    try:
        validate_execution_input_assembly(host, policy, contribution, assembly)
        with _selected_policy_source(host, policy):
            _, _, _, registration = _owner(host, policy, contribution)
            registered = selected._registration_state(registration)
            closure = registered.input_closure_entrance(assembly.semantic_input)
            if type(closure) is not selected.SelectedProviderInvocationClosure:
                raise TypeError("exact selected product closure required")
            closure.__post_init__()
            if closure.input_bodies is not assembly.input_bodies:
                raise ContractViolation("original product input tuple differs")
            validate_execution_input_assembly(host, policy, contribution, assembly)
            return closure
    finally:
        host = policy = contribution = assembly = registration = registered = closure = None


def validate_execution_input_assembly(host, policy, contribution, assembly):
    """Before/after execution: bind the live recipe to complete original results."""
    if type(assembly) is not SelectedInputVerificationAssembly:
        raise TypeError("exact original verification assembly required")
    with _selected_policy_source(host, policy) as (_, _, _, source):
        state, record, epoch, _ = _owner(host, policy, contribution)
        plan = products.read_selected_provider_product_execution_inputs(contribution)
        if (
            len(assembly.source_results) != len(plan.steps)
            or not assembly.source_results
        ):
            raise ContractViolation("complete recipe source-result closure required")
        input_host = assembly.source_results[0].host
        registrations = tuple(x.registration for x in assembly.source_results)
        expected = tuple(x.expected for x in assembly.source_results)
        _registrations(state, plan, input_host, registrations)
        _check_expected(record, epoch, source, plan, expected)
        if any(
            x.host is not input_host or x.source_admission is not record[1]
            for x in assembly.source_results
        ):
            raise ContractViolation("execution input original source/host differs")
        roles = tuple(
            (plan.steps[i].ordinary.result_role, i) for i in plan.input_result_indices
        )
        if (
            assembly.source_input_roles != roles
            or assembly.context_input_roles
            or assembly.dependency_products is not None
        ):
            raise ContractViolation("execution input complete role partition differs")
        assembly.__post_init__()
        for original in assembly.source_results:
            inputs.validate_registered_semantic_input_result(
                input_host,
                original.registration,
                source_admission=record[1],
                expected=original.expected,
                result=original.result,
            )
