# pyright: reportImportCycles=false
"""Original factory recipe into tracked Code execution under one CLI command.

This joins existing entrances. It neither issues predecessor/genesis authority
nor bypasses the graph host's package publication admission.
"""

from __future__ import annotations

import inspect
import os
import time
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from types import CellType, FunctionType
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
from aware_code_semantic_contract_runtime.product_input_context import (
    close_product_input_contexts,
)
from aware_code_semantic_contract_runtime.selected_input_verification import (
    SelectedInputSourceResult,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProducerHost,
    SemanticInputSourceCoordinate,
)
from aware_code_semantic_contract_runtime.source_selection import (
    decode_source_selection,
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
    execution_context: product_execution.SelectedProductExecutionInputContext


@dataclass(frozen=True, slots=True)
class PreparedDirectCLIProductInputs:
    node: Any
    assembly: Any
    closure: selected_provider.SelectedProviderInvocationClosure
    elapsed_ns: int
    execution_context: product_execution.SelectedProductExecutionInputContext


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




def validate_direct_cli_selected_host(product: DirectCLISelectedProduct) -> None:
    """Authenticate retained association by identity, then ask the original owner."""
    host = product.host.code_host
    if (
        composition._selected_input_identity_lookup(composition._POLICY_HOSTS, host)
        is not product.host.staged
    ):
        raise ContractViolation("original selected execution host differs")
    direct_host.validate_direct_validation_host(host)


def _bind_execution_participant():
    namespace = globals()
    source_kind = composition.WorkspaceDeclarationScopeRuntime
    descriptor = inspect.getattr_static
    scope = descriptor(source_kind, "selected_source_validation_scope")
    dispatch = composition._original_group_method
    policy_read = _read_original_policy
    contribution_read = _read_original_contribution
    require_command = composition._require_live_direct_workspace_command
    validate_host = validate_direct_cli_selected_host
    close_host = direct_host.close_direct_validation_host
    make_context, function_kind, cell_kind = contextmanager, FunctionType, CellType
    lookup = composition._selected_input_identity_lookup
    registry = composition._POLICY_HOSTS
    pid_reader, process_id = os.getpid, os.getpid()
    templates = tuple((fn.__code__, fn.__globals__, fn.__name__, fn.__defaults__,
                       None if fn.__kwdefaults__ is None else tuple(fn.__kwdefaults__.items()),
                       None if fn.__closure__ is None else tuple(cell.cell_contents for cell in fn.__closure__))
                      for fn in (scope, dispatch, policy_read, close_host, lookup))
    witnesses = tuple((fn, fn.__code__, fn.__closure__, tuple(cell.cell_contents for cell in fn.__closure__ or ()))
                      for fn in (scope, dispatch, policy_read, contribution_read, require_command, validate_host, close_host, lookup))

    def origins():
        if (inspect.getattr_static is not descriptor
            or descriptor(source_kind, "selected_source_validation_scope") is not scope
            or composition._original_group_method is not dispatch
            or composition._selected_input_identity_lookup is not lookup
            or composition._POLICY_HOSTS is not registry
            or namespace.get("_read_original_policy") is not policy_read
            or namespace.get("_read_original_contribution") is not contribution_read
            or namespace.get("validate_direct_cli_selected_host") is not validate_host
            or composition._require_live_direct_workspace_command is not require_command
            or direct_host.close_direct_validation_host is not close_host
            or any(fn.__code__ is not code or fn.__closure__ is not cells
                   or any(cell.cell_contents is not value for cell, value in zip(cells or (), values, strict=True))
                   for fn, code, cells, values in witnesses)):
            raise ContractViolation("original participant validation entrance changed")

    def _execution_participant(command, source, product):
        """Check the original participant under one closed source bracket."""
        original_close: Any
        authenticated = False
        shared_check = False
        host = functions = fn = scoped = original_dispatch = original_policy = original_close = original_lookup = None
        participants = participant = values = matches = selected = policy = contribution = None
        original = bindings = resources = issuer = declaration = manager = evidence = granted = None
        code = owner = name = defaults = keywords = cells = key = package_ref = None
        try:
            if pid_reader() != process_id:
                raise ContractViolation("original participant belongs to another process")
            if (type(product) is not DirectCLISelectedProduct
                or type(source) is not WorkspaceSelectedPackageSource
                or product.host.staged.command is not command):
                raise TypeError("original selected command/product/source required")
            host = product.host.code_host
            # Native frames are fixed before any command/source callback.
            functions = []
            for code, owner, name, defaults, keywords, cells in templates:
                fn = function_kind(code, owner, name, defaults,
                    None if cells is None else tuple(cell_kind(value) for value in cells))
                fn.__kwdefaults__ = None if keywords is None else dict(keywords)
                functions.append(fn)
            scoped, original_dispatch, original_policy, original_close, original_lookup = functions
            # The original scope calls the same retained dispatcher from a
            # closure cell. Freeze that native call too, so a code restamp
            # between the last guard and generator entry cannot execute it.
            code, owner, name, defaults, keywords, cells = templates[0]
            scoped = function_kind(code, owner, name, defaults,
                None if cells is None else tuple(cell_kind(original_dispatch if value is dispatch else value)
                                                for value in cells))
            scoped.__kwdefaults__ = None if keywords is None else dict(keywords)
            if original_lookup(registry, host) is not product.host.staged:
                raise ContractViolation("original selected execution host differs")
            authenticated = True
            shared_check = True
            origins()
            require_command(command)
            origins()
            validate_host(product)
            origins()
            shared_check = False
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
            origins()
            original = contribution_read(contribution)
            origins()
            if original.binding.provider_key != key:
                raise ContractViolation("execution contribution differs from participant")
            bindings = tuple(binding for binding in product.host.staged.product_runtime_bindings
                             if binding.registration is original.expected.registration)
            if len(bindings) != 1:
                raise ContractViolation("unique original execution registration required")
            resources = command.sources
            issuer = resources.declaration_scope_runtime
            declaration = resources.declaration_scope
            manager = make_context(scoped)(issuer, declaration, selected)
            with manager:
                origins()
                evidence = original_dispatch(issuer, "inspect_inputs", selected)[0]
                origins()
                if evidence.package.package_ref != package_ref:
                    raise ContractViolation("execution package differs from original source")
                granted = original_policy(host, policy)
                origins()
                if len(granted.grants) != 1 or granted.grants[0].source_identity_digest != evidence.source_identity_digest:
                    raise ContractViolation("execution policy differs from original source")
            origins()
            if (command.sources is not resources
                or resources.declaration_scope_runtime is not issuer
                or resources.declaration_scope is not declaration
                or product.host.code_host is not host):
                raise ContractViolation("original participant source association changed")
            require_command(command)
            origins()
            return participants, matches[0], bindings[0]
        except BaseException:
            if authenticated:
                if shared_check:
                    original_close(host)
                else:
                    try:
                        origins()
                    except BaseException:  # noqa: BLE001 - quarantine only independently established shared corruption.
                        # Shared executable corruption is independently
                        # established, not inferred from B's refusal label.
                        original_close(host)
            raise
        finally:
            command = source = product = host = functions = fn = None
            scoped = original_dispatch = original_policy = original_close = original_lookup = None
            participants = participant = values = matches = selected = policy = contribution = None
            original = bindings = resources = issuer = declaration = manager = evidence = granted = None
            code = owner = name = defaults = keywords = cells = key = package_ref = None

    return _execution_participant


_execution_participant = _bind_execution_participant()
del _bind_execution_participant


def _bind_direct_cli_product_execution_origins(command, product, participating_sources: tuple[Any, ...]) -> None:
    if type(participating_sources) is not tuple or not participating_sources:
        raise ContractViolation("original participating sources required")
    registrations = []
    seen_sources = []
    for source in participating_sources:
        if any(source is value for value in seen_sources):
            raise ContractViolation("duplicate participating source")
        seen_sources.append(source)
        _, participant, binding = _execution_participant(command, source, product)
        _, _, _, policy, contribution = participant
        inputs.enroll_product_execution_inputs(product.host.code_host, policy, contribution)
        existing = next((row for row in registrations if row[0] is binding.registration), None)
        if existing is None:
            registrations.append((binding.registration, policy, contribution, 1))
        else:
            if existing[2] is not contribution:
                raise ContractViolation("registration has another original contribution")
            index = registrations.index(existing)
            registrations[index] = (*existing[:3], existing[3] + 1)
    if any(row[3] > 32 for row in registrations):
        raise ContractViolation("per-registration product context bound exceeded")
    for _, policy, contribution, _ in registrations:
        inputs.bind_product_execution_input_origin(product.host.code_host, policy, contribution)


async def _prepare_direct_cli_source_results(
    command: composition._DirectWorkspaceCommandResources,
    source: WorkspaceSelectedPackageSource,
    product: DirectCLISelectedProduct,
    *,
    retention: ExitStack,
    dependency_admissions: DirectCLIProductDependencyAdmissions | None = None,
    planning: bool = False,
):
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
    if planning and plan.planning_source_selection_index is None:
        raise ContractViolation("original planning source-selection recipe unavailable")
    if not planning and bool(plan.dependency_input_role) != (dependency_admissions is not None):
        raise ContractViolation("complete declared dependency admissions required")
    check_participant()
    if not planning:
        inputs._require_product_execution_input_origin(host, policy, contribution)
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
    returned = []

    def prepare_expected(index):
        step = plan.steps[index]
        rows = []
        predecessor = step.source_selection_index
        if predecessor is None:
            for scope, contract in zip(step.source_scopes, step.ordinary.source_contracts, strict=True):
                for body in evidence.bodies:
                    if (body.relative_path == evidence.manifest_relative_path
                        if scope.package_manifest_only else
                        not scope.suffixes or body.relative_path.endswith(scope.suffixes)):
                        rows.append(SemanticInputSourceCoordinate(body.relative_path,
                            SemanticValueCoordinate(contract.role, contract.contract, body.body_ref,
                                ContentDigest(body.content_digest), body.size_bytes)))
        else:
            selection = decode_source_selection(returned[predecessor].canonical_body)
            candidates = {body.relative_path: body for body in evidence.bodies}
            for item in selection.sources:
                body = candidates[item.relative_path]
                rows.append(SemanticInputSourceCoordinate(item.relative_path,
                    SemanticValueCoordinate(item.role, item.contract, body.body_ref,
                        ContentDigest(body.content_digest), body.size_bytes)))
        coordinates = tuple(sorted(rows, key=lambda row: row.relative_path.encode()))
        receipts = inputs.prepare_product_input_contexts(host, policy, contribution,
            step_index=index, source_coordinates=coordinates,
            source_results=tuple(SelectedInputSourceResult(input_host, registrations[i], source,
                expectations[i], result) for i, result in enumerate(returned)))
        kwargs = {}
        if receipts:
            declarations = {item.role: item.contract for item in step.ordinary.context_contracts}
            bindings = tuple(row for row in plan.input_context_bindings if row[0] == index)
            kwargs["context_receipts"] = tuple((row[1], declarations[row[1]], receipt)
                for row, receipt in zip(bindings, receipts, strict=True))
        common = dict(use_ref="workspace-product-input:" + str(uuid4()), stage=step.stage,
                      context_contracts=step.ordinary.context_contracts, **kwargs)
        try:
            if predecessor is None:
                expectation = node.prepare_source_expectation(source_coordinates=coordinates, **common)
            else:
                expectation = node.prepare_selected_source_expectation(input_host, registrations[predecessor],
                    selection_expected=expectations[predecessor], result=returned[predecessor],
                    source_contracts=step.ordinary.source_contracts, **common)
            if receipts:
                inputs.bind_product_input_contexts(host, policy, contribution,
                                                   receipts=receipts, expected=expectation)
        except BaseException:
            close_product_input_contexts(receipts)
            raise
        return expectation

    registrations = inputs.register_product_execution_input_producers(
        host,
        policy,
        contribution,
        input_host=input_host,
    )
    if planning:
        assert plan.planning_source_selection_index is not None
        count = plan.planning_source_selection_index + 1
    else:
        count = len(plan.steps)
    steps = plan.steps[:count]
    prefix_count = next((index for index, step in enumerate(steps)
                         if step.source_selection_index is not None), len(steps))
    prefix_count = min(prefix_count, next((index for index, _, _ in plan.input_context_bindings
                                         if index < count), len(steps)))
    expectations.extend(prepare_expected(index) for index in range(prefix_count))
    prefix = await inputs.execute_product_execution_inputs(
        host, policy, contribution, input_host=input_host,
        registrations=registrations, expectations=tuple(expectations),
    )
    returned = list(prefix)
    for index, result in enumerate(prefix):
        node.retain_source_result(input_host, registrations[index],
                                  expected=expectations[index], result=result)
    if prefix_count < len(steps):
        for index in range(prefix_count, len(steps)):
            expectation = prepare_expected(index)
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
    expected = tuple(expectations)
    check_participant()
    return plan, input_host, node, registration, registrations, expected, results, dependency_products, started_ns


async def prepare_direct_cli_selected_planning_source(command, source, product, *, retention):
    """Use the owner's same source chain without assembly or semantic execution."""
    from aware_code_retained_registry_policy_runtime import (
        product_planning_source as planning,
    )

    plan, input_host, node, _, registrations, expected, results, _, _ = (
        await _prepare_direct_cli_source_results(command, source, product,
                                                retention=retention, planning=True)
    )
    _, participant, _ = _execution_participant(command, source, product)
    _, _, _, policy, contribution = participant
    declaration = planning.read_product_planning_input_declaration(product.host.code_host, policy, contribution)
    index = plan.planning_source_selection_index
    assert index is not None
    planning_expected = node.prepare_selected_source_expectation(
        input_host, registrations[index], selection_expected=expected[index], result=results[index],
        use_ref="workspace-product-planning:" + str(uuid4()), stage="source_planning",
        source_contracts=declaration.source_contracts, context_contracts=declaration.context_contracts,
    )
    node.retain_source_evidence(retention)
    return input_host, planning_expected


async def prepare_direct_cli_selected_product_inputs(
    command, source, product, *, retention,
    dependency_admissions: DirectCLIProductDependencyAdmissions | None = None,
) -> PreparedDirectCLIProductInputs:
    plan, input_host, node, _registration, registrations, expected, results, dependency_products, started_ns = (
        await _prepare_direct_cli_source_results(command, source, product, retention=retention,
                                                dependency_admissions=dependency_admissions)
    )
    _, participant, _ = _execution_participant(command, source, product)
    host = product.host.code_host
    _, _, _, policy, contribution = participant
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
    _execution_participant(command, source, product)
    assembly = node.assemble_inputs(
        assembled.semantic_input,
        assembled.input_bodies,
        source_input_roles=assembled.source_input_roles,
        dependency_input_role=plan.dependency_input_role or None,
    )
    execution_context = inputs.prepare_product_execution_input_verification(
        host, policy, contribution, node, assembly=assembly)
    closure = inputs.read_product_execution_input_closure(
        host,
        policy,
        contribution,
        assembly,
    )
    _execution_participant(command, source, product)
    return PreparedDirectCLIProductInputs(
        node, assembly, closure, time.perf_counter_ns() - started_ns, execution_context
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
    _bind_direct_cli_product_execution_origins(command, product, (source,))
    prepared = await prepare_direct_cli_selected_product_inputs(
        command,
        source,
        product,
        retention=retention,
        dependency_admissions=dependency_admissions,
    )
    retention.callback(inputs.close_product_execution_input_context, product.host.code_host, prepared.execution_context)
    participants, participant, binding = _execution_participant(command, source, product)
    runtime, registration = binding.runtime, binding.registration
    node, assembly = prepared.node, prepared.assembly
    started_ns = time.perf_counter_ns()
    admission = selected_provider.issue_selected_provider_execution(
        runtime,
        registration,
        assembly.semantic_input,
        operation_context=prepared.execution_context,
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
        snapshot, prepared.elapsed_ns + time.perf_counter_ns() - started_ns, prepared.execution_context
    )
