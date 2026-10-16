# pyright: reportImportCycles=false
"""Original factory recipe into tracked Code execution under one CLI command.

This joins existing entrances. It neither issues predecessor/genesis authority
nor bypasses the graph host's package publication admission.
"""

from __future__ import annotations

import time
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Any
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
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
    SemanticInputSourceCoordinate,
)

from . import direct_command_composition as composition
from .declaration_scope_admission import WorkspaceSelectedPackageSource
from .direct_cli_selected_host import DirectCLISelectedProduct


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
) -> PreparedDirectCLIProductInputs:
    """Keep borrowed inputs until the caller has closed its original Code host.

    The caller owns the outer retention stack, which must outlive the selected
    host. Code attachments retire first, then the node and its expectations,
    then the producer host. The detached snapshot supplies no publication grant.
    """
    if type(retention) is not ExitStack:
        raise TypeError("original composition retention stack required")
    if (
        type(product) is not DirectCLISelectedProduct
        or product.host.staged.command is not command
    ):
        raise TypeError("original selected command/product required")
    composition._require_live_direct_workspace_command(command)
    validate_direct_cli_selected_host(product)
    host = product.host.code_host
    (contribution,) = product.host.staged.product_contributions
    (binding,) = product.host.staged.product_runtime_bindings
    registration = binding.registration
    sources = command.sources
    if type(sources) is not composition._DirectWorkspaceDeclarationSources:
        raise TypeError("original declaration sources required")
    issuer = sources.declaration_scope_runtime
    evidence = issuer.inspect_selected_package_evidence(source)
    plan = inputs.enroll_product_execution_inputs(host, product.policy, contribution)
    inputs.bind_product_execution_input_origin(host, product.policy, contribution)
    input_host = SemanticInputProducerHost()
    retention.callback(input_host.close)
    node = retention.enter_context(
        composition._command_owned_selected_input_read_session(
            command,
            host=host,
            selected_source=source,
            registration=registration,
        )
    )
    started_ns = time.perf_counter_ns()
    expectations = []
    for step in plan.steps:
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
        expectations.append(
            node.prepare_source_expectation(
                use_ref="workspace-product-input:" + str(uuid4()),
                stage=step.stage,
                source_coordinates=tuple(
                    sorted(rows, key=lambda row: row.relative_path.encode())
                ),
                context_contracts=step.ordinary.context_contracts,
            )
        )
    expected = tuple(expectations)
    registrations = inputs.register_product_execution_input_producers(
        host,
        product.policy,
        contribution,
        input_host=input_host,
    )
    results = await inputs.execute_product_execution_inputs(
        host,
        product.policy,
        contribution,
        input_host=input_host,
        registrations=registrations,
        expectations=expected,
    )
    invocation_ref = "workspace-product-execution:" + str(uuid4())
    assembled = inputs.assemble_product_execution_inputs(
        host,
        product.policy,
        contribution,
        input_host=input_host,
        registrations=registrations,
        expectations=expected,
        results=results,
        invocation_ref=invocation_ref,
        idempotency_key=invocation_ref,
    )
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
    )
    product_execution.prepare_selected_input_verification(
        host, node, registration, assembly=assembly
    )
    closure = inputs.read_product_execution_input_closure(
        host,
        product.policy,
        contribution,
        assembly,
    )
    return PreparedDirectCLIProductInputs(
        node, assembly, closure, time.perf_counter_ns() - started_ns
    )


async def execute_direct_cli_selected_product(
    command: composition._DirectWorkspaceCommandResources,
    source: WorkspaceSelectedPackageSource,
    product: DirectCLISelectedProduct,
    *,
    retention: ExitStack,
) -> DirectCLIProductExecution:
    """Diagnostic tracked completion; publication uses the prepared-input join."""
    prepared = await prepare_direct_cli_selected_product_inputs(
        command,
        source,
        product,
        retention=retention,
    )
    (binding,) = product.host.staged.product_runtime_bindings
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
    composition._require_live_direct_workspace_command(command)
    return DirectCLIProductExecution(
        snapshot, prepared.elapsed_ns + time.perf_counter_ns() - started_ns
    )
