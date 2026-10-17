# pyright: reportImportCycles=false
"""Original factory recipe into tracked Code execution under one CLI command.

This joins existing entrances. It neither issues predecessor/genesis authority
nor bypasses the graph host's package publication admission.
"""

from __future__ import annotations

import time
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Any, NamedTuple
from uuid import uuid4

from aware_code_retained_registry_policy_runtime import direct_host, product_execution
from aware_code_retained_registry_policy_runtime import (
    product_execution_inputs as inputs,
)
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    ExecutionCompletion,
    ExecutionPublicationSnapshot,
    SemanticValueCoordinate,
    TerminalStatus,
    selected_provider,
)
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime.product_contribution import (
    read_selected_provider_product_contribution,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
    SemanticInputSourceCoordinate,
)

from . import direct_command_composition as composition
from .declaration_scope_admission import WorkspaceSelectedPackageSource
from .direct_cli_selected_host import (
    DirectCLIProductParticipant,
    DirectCLISelectedProduct,
)


@dataclass(frozen=True, slots=True)
class DirectCLIProductExecution:
    snapshot: ExecutionPublicationSnapshot
    elapsed_ns: int


@dataclass(frozen=True, slots=True)
class PreparedDirectCLIProductInputs:
    node: Any
    assembly: Any
    closure: selected_provider.SelectedProviderInvocationClosure
    elapsed_ns: int


class DirectCLIProductDependencyAdmissions(NamedTuple):
    """Borrowed original admissions, not a new dependency authority or codec."""

    operation: Any
    resolution: Any
    fulfillment: Any
    body: Any


def _bind_contribution_reader(reader):
    namespace, owner_namespace = globals(), vars(products)
    code = reader.__code__

    def read(contribution):
        def check():
            if (
                namespace.get("read_selected_provider_product_contribution") is not reader
                or owner_namespace.get("read_selected_provider_product_contribution") is not reader
                or reader.__code__ is not code
            ):
                raise ContractViolation("original execution contribution reader changed")

        check()
        result = reader(contribution)
        check()
        return result

    return read


_read_original_contribution = _bind_contribution_reader(read_selected_provider_product_contribution)


def _bind_policy_reader(reader):
    namespace, code = vars(direct_host), reader.__code__

    def validate(host, policy):
        def check():
            if namespace.get("validate_admitted_registry_policy") is not reader or reader.__code__ is not code:
                raise ContractViolation("original execution policy reader changed")

        check()
        value = reader(host, policy)
        check()
        return value

    return validate


_read_original_policy = _bind_policy_reader(direct_host.validate_admitted_registry_policy)


def _execution_participant(command, source, product):
    """Choose by original source identity; never accept a requested factory key."""
    if (
        type(product) is not DirectCLISelectedProduct
        or type(source) is not WorkspaceSelectedPackageSource
        or product.host.staged.command is not command
    ):
        raise TypeError("original selected command/product/source required")
    composition._require_live_direct_workspace_command(command)
    validate_direct_cli_selected_host(product)
    participants = product.participants
    if type(participants) is not tuple or not 1 <= len(participants) <= 256:
        raise ContractViolation("original execution participants required")
    matches = []
    for participant in participants:
        if type(participant) is not DirectCLIProductParticipant or len(participant) != 5:
            raise ContractViolation("original execution participant required")
        values = tuple(tuple.__iter__(participant))
        if values[0] is source:
            matches.append(values)
    if len(matches) != 1:
        raise ContractViolation("unique original execution source required")
    selected, key, package_ref, policy, contribution = matches[0]
    if type(key) is not str or type(package_ref) is not str:
        raise ContractViolation("original execution participant coordinates required")
    original = _read_original_contribution(contribution)
    if original.binding.provider_key != key:
        raise ContractViolation("execution contribution differs from participant")
    bindings = tuple(
        binding for binding in product.host.staged.product_runtime_bindings
        if binding.registration is original.expected.registration
    )
    if len(bindings) != 1:
        raise ContractViolation("unique original execution registration required")
    evidence = command.sources.declaration_scope_runtime.inspect_inputs(selected)[0]
    if evidence.package.package_ref != package_ref:
        raise ContractViolation("execution package differs from original source")
    granted = _read_original_policy(product.host.code_host, policy)
    if len(granted.grants) != 1 or granted.grants[0].source_identity_digest != evidence.source_identity_digest:
        raise ContractViolation("execution policy differs from original source")
    return participants, matches[0], bindings[0]


def validate_direct_cli_selected_host(product: DirectCLISelectedProduct) -> None:
    """Authenticate retained association by identity, then ask the original owner."""
    host = product.host.code_host
    if (
        composition._selected_input_identity_lookup(composition._POLICY_HOSTS, host)
        is not product.host.staged
    ):
        raise ContractViolation("original selected execution host differs")
    direct_host.validate_direct_validation_host(host)


async def prepare_direct_cli_selected_product_inputs(
    command: composition._DirectWorkspaceCommandResources,
    source: WorkspaceSelectedPackageSource,
    product: DirectCLISelectedProduct,
    *,
    retention: ExitStack,
    dependency_admissions: DirectCLIProductDependencyAdmissions | None = None,
) -> PreparedDirectCLIProductInputs:
    """Keep borrowed inputs until the caller has closed its original Code host.

    The caller owns the outer retention stack, which must outlive the selected
    host. Code attachments retire first, then the node and its expectations,
    then the producer host. The detached snapshot supplies no publication grant.
    """
    if type(retention) is not ExitStack:
        raise TypeError("original composition retention stack required")
    if dependency_admissions is not None and type(dependency_admissions) is not DirectCLIProductDependencyAdmissions:
        raise TypeError("original dependency admission tuple required")
    participants, participant, binding = _execution_participant(command, source, product)
    host = product.host.code_host
    _, _, _, policy, contribution = participant
    registration = binding.registration

    def check_participant():
        current, values, current_binding = _execution_participant(command, source, product)
        if (
            current is not participants or current_binding is not binding
            or any(actual is not retained for actual, retained in zip(values, participant, strict=True))
        ):
            raise ContractViolation("original execution participant changed")
    sources = command.sources
    if type(sources) is not composition._DirectWorkspaceDeclarationSources:
        raise TypeError("original declaration sources required")
    issuer = sources.declaration_scope_runtime
    evidence = issuer.inspect_selected_package_evidence(source)
    plan = inputs.enroll_product_execution_inputs(host, policy, contribution)
    if bool(plan.dependency_input_role) != (dependency_admissions is not None):
        raise ContractViolation("complete declared dependency admissions required")
    check_participant()
    inputs.bind_product_execution_input_origin(host, policy, contribution)
    input_host = SemanticInputProducerHost()
    retention.callback(input_host.close)
    node: Any = retention.enter_context(
        composition._command_owned_selected_input_read_session(
            command,
            host=host,
            selected_source=source,
            registration=registration,
        )
    )
    started_ns = time.perf_counter_ns()
    dependency_products = None
    if dependency_admissions is not None:
        operation, resolution, fulfillment, body = tuple(tuple.__iter__(dependency_admissions))
        dependency_products = node.admit_dependency_products(
            operation, resolution, fulfillment, body=body,
        )
        check_participant()
    expectations = []

    def prepare_expected(step):
        rows = []
        for scope, contract in zip(
            step.source_scopes, step.ordinary.source_contracts, strict=True
        ):
            for body in evidence.bodies:
                if not scope.suffixes or body.relative_path.endswith(scope.suffixes):
                    rows.append(
                        SemanticInputSourceCoordinate(
                            body.relative_path,
                            SemanticValueCoordinate(
                                contract.role,
                                contract.contract,
                                body.body_ref,
                                ContentDigest(body.content_digest),
                                body.size_bytes,
                            ),
                        )
                    )
        return node.prepare_source_expectation(
            use_ref="workspace-product-input:" + str(uuid4()),
            stage=step.stage,
            source_coordinates=tuple(
                sorted(rows, key=lambda row: row.relative_path.encode())
            ),
            context_contracts=step.ordinary.context_contracts,
        )

    registrations = inputs.register_product_execution_input_producers(
        host,
        policy,
        contribution,
        input_host=input_host,
    )
    selected_steps = any(step.source_selection_index is not None for step in plan.steps)
    if selected_steps:
        returned = []
        for index, step in enumerate(plan.steps):
            predecessor = step.source_selection_index
            if predecessor is None:
                expectation = prepare_expected(step)
            else:
                expectation = node.prepare_selected_source_expectation(
                    input_host, registrations[predecessor],
                    selection_expected=expectations[predecessor],
                    result=returned[predecessor],
                    use_ref="workspace-product-input:" + str(uuid4()),
                    stage=step.stage,
                    source_contracts=step.ordinary.source_contracts,
                    context_contracts=step.ordinary.context_contracts,
                )
            expectations.append(expectation)
            result = await inputs.execute_product_execution_input_step(
                host, policy, contribution, input_host=input_host,
                registrations=registrations, expectations=tuple(expectations),
                results=tuple(returned),
            )
            check_participant()
            node.retain_source_result(
                input_host, registrations[index], expected=expectation, result=result,
            )
            returned.append(result)
        results = tuple(returned)
    else:
        expectations.extend(prepare_expected(step) for step in plan.steps)
        results = await inputs.execute_product_execution_inputs(
            host, policy, contribution, input_host=input_host,
            registrations=registrations, expectations=tuple(expectations),
        )
    expected = tuple(expectations)
    check_participant()
    invocation_ref = "workspace-product-execution:" + str(uuid4())
    assembled = inputs.assemble_product_execution_inputs(
        host,
        policy,
        contribution,
        input_host=input_host,
        registrations=registrations,
        expectations=expected,
        results=results,
        invocation_ref=invocation_ref,
        idempotency_key=invocation_ref,
        dependency_products=dependency_products,
    )
    check_participant()
    if not selected_steps:
        for original, expectation, result in zip(
            registrations, expected, results, strict=True
        ):
            node.retain_source_result(
                input_host, original, expected=expectation, result=result
            )
    assembly = node.assemble_inputs(
        assembled.semantic_input,
        assembled.input_bodies,
        source_input_roles=assembled.source_input_roles,
        dependency_input_role=plan.dependency_input_role or None,
    )
    product_execution.prepare_selected_input_verification(
        host, node, registration, assembly=assembly
    )
    closure = inputs.read_product_execution_input_closure(
        host,
        policy,
        contribution,
        assembly,
    )
    check_participant()
    return PreparedDirectCLIProductInputs(
        node, assembly, closure, time.perf_counter_ns() - started_ns
    )


async def execute_direct_cli_selected_product(
    command: composition._DirectWorkspaceCommandResources,
    source: WorkspaceSelectedPackageSource,
    product: DirectCLISelectedProduct,
    *,
    retention: ExitStack,
    dependency_admissions: DirectCLIProductDependencyAdmissions | None = None,
) -> DirectCLIProductExecution:
    """Diagnostic tracked completion; publication uses the prepared-input join."""
    prepared = await prepare_direct_cli_selected_product_inputs(
        command,
        source,
        product,
        retention=retention,
        dependency_admissions=dependency_admissions,
    )
    participants, participant, binding = _execution_participant(command, source, product)
    runtime, registration = binding.runtime, binding.registration
    node, assembly = prepared.node, prepared.assembly
    started_ns = time.perf_counter_ns()
    admission = selected_provider.issue_selected_provider_execution(
        runtime,
        registration,
        assembly.semantic_input,
        operation_context=node,
    )
    completion = selected_provider.execute_selected_provider(runtime, admission)
    if type(completion) is not ExecutionCompletion or not runtime.owns_completion(
        completion
    ):
        raise ContractViolation("original runtime-owned product completion required")
    node.validate()
    snapshot = runtime.snapshot_completion(completion)
    snapshot.__post_init__()
    if snapshot.result.status not in {TerminalStatus.DELTA, TerminalStatus.CURRENT}:
        raise ContractViolation("selected product did not complete successfully")
    current, values, current_binding = _execution_participant(command, source, product)
    if (
        current is not participants or current_binding is not binding
        or any(actual is not retained for actual, retained in zip(values, participant, strict=True))
        or snapshot.invocation_digest != prepared.closure.invocation.digest
    ):
        raise ContractViolation("completed execution participant changed")
    composition._require_live_direct_workspace_command(command)
    return DirectCLIProductExecution(
        snapshot, prepared.elapsed_ns + time.perf_counter_ns() - started_ns
    )
