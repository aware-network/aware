# pyright: reportImportCycles=false
"""One original CLI product through the existing graph coordinator/publisher.

Local operational backing is selected by Workspace's fixed FS composition. It
does not install a protected store, grant shared authority or mint RELEASE.
"""

from __future__ import annotations

import inspect
import os
import time
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import get_ident
from typing import Any, cast
from uuid import uuid4

from aware_code_retained_registry_policy_runtime.selected_root_intent import (
    derive_selected_root_intent,
)
from aware_code_semantic_contract_runtime import ContentDigest, ContractViolation
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SemanticDependencyProductInputCodec,
)
from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore

from . import direct_command_composition as composition
from .declaration_product_membership import WorkspaceDeclarationProductCorrespondence
from .direct_cli_product_execution import (
    DirectCLIProductDependencyAdmissions,
    _execution_participant,
    prepare_direct_cli_selected_product_inputs,
    validate_direct_cli_selected_host,
)
from .direct_cli_product_planning import DirectCLIProductGraphPlan
from .direct_cli_selected_host import DirectCLISelectedProduct
from .materialization_graph_coordinator import (
    WorkspaceSemanticMaterializationGraphCoordinator,
    _dispose_workspace_direct_command_graph_execution,
    _issue_workspace_direct_command_graph_execution,
    _WorkspaceSemanticMaterializationGraphHostPorts,
)
from .materialization_graph_host_composition import WorkspaceMaterializationGraphBacking
from .materialization_operation import (
    WorkspaceMaterializeExecutionPlan,
    WorkspaceMaterializeOperation,
    WorkspaceMaterializeOperationRequest,
    _graph_node_admission_state,
    admit_workspace_materialize_execution_input_composition,
    admit_workspace_materialize_operation,
    derive_workspace_materialize_execution_input_closure_digest,
)
from .materialization_session import WorkspaceMaterializationSessionAuthorityGrade
from .semantic_catalog_host import WorkspaceJointCatalogResolvers
from .semantic_dependency_graph import WorkspaceSemanticMaterializationGraphResultV3
from .semantic_dependency_graph_codec import (
    encode_workspace_semantic_materialization_graph_result_v2,
)


@dataclass(frozen=True, slots=True)
class DirectCLIProductPublication:
    wire: bytes
    elapsed_ns: int
    admission_ns: int
    result: WorkspaceSemanticMaterializationGraphResultV3


class _DirectCLIProductGraphScope:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("original command issues graph scope")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("direct graph scope is sealed")

    def __reduce__(self):
        raise TypeError("direct graph scope is nonportable")


@dataclass(slots=True)
class _Scope:
    command: Any
    source: Any
    product: Any
    planned: Any
    backing: Any
    pid: int
    thread: int
    ports: Any = None
    prepared: Any = None
    execution_plan: Any = None
    operation_request: Any = None
    operation: Any = None
    operation_admission: Any = None
    terminal: bool = False
    active_binding: Any = None
    evidence: Any = None


_SCOPES: list[tuple[object, _Scope]] = []
_PID = os.getpid()


def _scope(holder):
    if os.getpid() != _PID:
        raise ContractViolation("direct graph scope belongs to another process")
    state = next((state for original, state in _SCOPES if original is holder), None)
    if type(holder) is not _DirectCLIProductGraphScope:
        if state is not None:
            state.terminal = True
        raise TypeError("original direct graph scope required")
    if (
        state is None
        or state.terminal
        or state.pid != os.getpid()
        or state.thread != get_ident()
    ):
        raise ContractViolation("direct graph scope is terminal or foreign")
    return state


def _bind_original_graph_scope_validation(scope_reader, input_reader, dispatch, participant_reader):
    namespace = globals()
    composition_namespace = vars(composition)
    dispatch_namespace = dispatch.__globals__
    descriptor_reader = inspect.getattr_static
    scopes = _SCOPES
    state_kind = _Scope
    entrances = (scope_reader, input_reader, dispatch, participant_reader)
    codes = tuple(value.__code__ for value in entrances)

    def origins():
        if (
            namespace.get("_scope") is not scope_reader
            or namespace.get("_execution_participant") is not participant_reader
            or namespace.get("_SCOPES") is not scopes
            or namespace.get("_Scope") is not state_kind
            or composition_namespace.get("_selected_input_read_record") is not input_reader
            or composition_namespace.get("_original_group_method") is not dispatch
            or dispatch_namespace.get("_original_group_method") is not dispatch
            or any(value.__code__ is not code for value, code in zip(entrances, codes, strict=True))
            or inspect.getattr_static is not descriptor_reader
        ):
            raise ContractViolation("original graph source-window entrance changed")

    def checked_dispatch(*args, **kwargs):
        result = None
        try:
            origins()
            result = dispatch(*args, **kwargs)
            origins()
            return result
        finally:
            args = ()
            kwargs = result = None

    def validate(holder, *, values=None):
        state = command = product = prepared = record = issuer = None
        retained = ()
        binding = pair = intent = required = None
        try:
            state = next((item[1] for item in scopes
                          if type(item) is tuple and len(item) == 2 and item[0] is holder), None)
            origins()
            state = scope_reader(holder)
            origins()
            command, product = state.command, state.product
            prepared = state.prepared
            composition._require_live_direct_workspace_command(command)
            with ExitStack() as stack:
                if prepared is not None:
                    if descriptor_reader(prepared.node, "validate") is not composition._SELECTED_INPUT_READ_VALIDATE:
                        raise ContractViolation("original source-node validator substituted")
                    origins()
                    record = input_reader(prepared.node)
                    origins()
                    if (
                        record.command is not command or record.selected is not state.source
                        or record.host is not product.host.code_host
                    ):
                        raise ContractViolation("original graph source-node association differs")
                    issuer = command.sources.declaration_scope_runtime
                    retained = tuple(
                        checked_dispatch(issuer, "_pre_request_record", record.selected, expected)
                        for expected in record.expectations
                    )
                    if retained and not any(item.grouped_origin is not None for item in retained):
                        stack.enter_context(checked_dispatch(
                            issuer, "_original_semantic_source_window", record.selected,
                            record.expectations[0],
                        ))
                origins()
                validate_direct_cli_selected_host(product)
                command.sources.declaration_scope_runtime.read_selected_package_source(
                    state.source
                )
                intent, required = derive_selected_root_intent(
                    product.host.code_host, product.policy
                )
                bindings = state.planned.plan.graph_execution_binding.ordered_node_bindings
                if state.active_binding is None:
                    (binding,) = bindings
                    root_binding = binding
                else:
                    binding = state.active_binding
                    if not any(binding is item for item in bindings):
                        raise ContractViolation("original graph active binding differs")
                    (root_binding,) = tuple(item for item in bindings if item.package.package_ref == product.package_ref)
                    _, _, runtime_binding = participant_reader(command, state.source, product)
                    if (binding.package != command.sources.declaration_scope_runtime.inspect_inputs(state.source)[0].package
                        or binding.code_match.selected_binding.profile_declaration != runtime_binding.runtime.profile
                        or binding.package_entry != product.host.catalog_pair.workspace.package(binding.package.package_ref)):
                        raise ContractViolation("original active graph participant differs")
                pair = product.host.catalog_pair
                if (
                    pair is not command.catalog_host._result
                    or root_binding.package_entry != pair.workspace.package(product.package_ref)
                    or root_binding.code_intent != intent
                    or root_binding.required_result_products != (required,)
                    or (state.planned.plan.graph.edges and state.planned.demands is None)
                ):
                    raise ContractViolation("original direct graph selection differs")
                if state.prepared is not None:
                    origins()
                    if (
                        descriptor_reader(state.prepared.node, "validate")
                        is not composition._SELECTED_INPUT_READ_VALIDATE
                    ):
                        raise ContractViolation("original source-node validator substituted")
                    composition._SELECTED_INPUT_READ_VALIDATE(state.prepared.node)
                if values is not None and (
                    values.get("plan_result") is not state.planned.plan
                    or values.get("ports") is not state.ports
                    or state.ports.cutover_fence_reader is not None
                ):
                    raise ContractViolation("direct graph admission assembly differs")
                origins()
            origins()
            if scope_reader(holder) is not state or state.prepared is not prepared:
                raise ContractViolation("original graph validation scope changed")
            origins()
            if record is not None and (
                prepared is None or input_reader(prepared.node) is not record
            ):
                raise ContractViolation("original graph source-node association differs")
            origins()
        except BaseException:
            if type(state) is state_kind:
                state.terminal = True
            raise
        finally:
            holder = state = values = command = product = prepared = record = issuer = None
            retained = ()
            binding = root_binding = runtime_binding = pair = intent = required = None

    return validate


validate_direct_cli_graph_scope = _bind_original_graph_scope_validation(
    _scope, composition._selected_input_read_record, composition._original_group_method, _execution_participant,
)


class _OriginalOperationAuthority:
    def __init__(self, scope):
        self.scope = scope

    @property
    def authority_grade(self):
        _scope(self.scope)
        return WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL

    @property
    def operation_ref(self):
        return _scope(self.scope).operation_request.operation_ref

    @property
    def operation_digest(self):
        return _scope(self.scope).operation_request.operation_digest

    def admits_composition(self, **values):
        validate_direct_cli_graph_scope(self.scope)
        request = _scope(self.scope).operation_request
        return all(value == getattr(request, name) for name, value in values.items())

    def admits(self, request):
        validate_direct_cli_graph_scope(self.scope)
        return request is _scope(self.scope).operation_request

    def permitted_package_refs_for(self, request):
        if not self.admits(request):
            raise ContractViolation("foreign original operation request")
        return (request.package_ref,)


class _OriginalPlanResolver:
    def __init__(self, scope):
        self.scope = scope

    @property
    def implementation_ref(self):
        return "aware.workspace.original-cli-product-plan.v1"

    @property
    def implementation_digest(self):
        return ContentDigest.of_bytes(Path(__file__).read_bytes()).value

    @property
    def profile_ref(self):
        return _scope(self.scope).prepared.closure.invocation.profile_ref

    @property
    def profile_digest(self):
        return _scope(self.scope).prepared.closure.invocation.profile_digest.value

    async def resolve_graph_node(self, admission, *, node_use):
        state = _scope(self.scope)
        if (
            admission is not state.operation_admission
            or node_use.scope is not self.scope
        ):
            raise ContractViolation("original graph plan admission differs")
        node_use.validate()
        return state.execution_plan

    async def resolve(self, admission):
        raise ContractViolation("original graph-node use required")


class _OriginalGraphNodeUse:
    def __init__(self, scope, admission):
        self.scope, self.admission = scope, admission

    def validate(self):
        validate_direct_cli_graph_scope(self.scope)
        state = _scope(self.scope)
        node = _graph_node_admission_state(self.admission)
        if (
            node.operation is not state.operation
            or node.operation_admission is not state.operation_admission
            or node.node_binding.package_entry
            != (state.active_binding or state.planned.plan.graph_execution_binding.ordered_node_bindings[0]).package_entry
        ):
            raise ContractViolation("original graph-node use differs")

    def bind_execution_plan(self, plan):
        self.validate()
        if plan is not _scope(self.scope).execution_plan:
            raise ContractViolation("original node plan differs")


def _selected_input(use, plan):
    if type(use) is not _OriginalGraphNodeUse:
        raise TypeError("original command graph-node use required")
    use.bind_execution_plan(plan)
    state = _scope(use.scope)
    return state.prepared.assembly.semantic_input, state.prepared.node


async def publish_direct_cli_selected_product(
    command, source, product, planned, *, retention: ExitStack
):
    """Execute original participants through the sole graph coordinator."""
    if type(product) is not DirectCLISelectedProduct or type(planned) is not DirectCLIProductGraphPlan:
        raise TypeError("original direct product/plan required")
    if type(retention) is not ExitStack or product.host.staged.command is not command:
        raise ContractViolation("original command publication retention required")
    bindings = planned.plan.graph_execution_binding.ordered_node_bindings
    if not bindings or len(bindings) > 256:
        raise ContractViolation("bounded original graph required")
    if (len(bindings) != 1 or planned.plan.graph.edges) and planned.demands is None:
        raise ContractViolation("original retained graph demands required")
    if any(node.head_observation.state != "missing" for node in planned.plan.graph.nodes):
        raise ContractViolation("original direct predecessor admission unavailable")
    if planned.demands is not None:
        planned.demands.check()
    started_ns = time.perf_counter_ns()
    validate_direct_cli_selected_host(product)
    evidence = command.sources.declaration_scope_runtime.inspect_selected_package_evidence(source)
    root = composition._direct_workspace_cli_state_root(command.sources.observation_runtime._session.binding.root_path) / "materialization"
    backing = WorkspaceMaterializationGraphBacking(state_root=root,
        repository_binding_ref=evidence.repository_binding_ref,
        state_store=SqliteLocalOperationalStateStore(root / "heads.sqlite3"))
    for binding in bindings:
        if backing.publisher._state_store.read(backing.publisher._state_namespace, binding.package.package_ref,
            include_deleted=True) is not None:
            raise ContractViolation("original direct package head moved after planning")
    holder = object.__new__(_DirectCLIProductGraphScope)
    root_binding, = tuple(item for item in bindings if item.package.package_ref == product.package_ref)
    state = _Scope(command, source, product, planned, backing, os.getpid(), get_ident(),
        active_binding=root_binding if planned.demands is not None else None, evidence=evidence)
    _SCOPES.append((holder, state))
    node_retention = ExitStack()
    retention.callback(node_retention.close)
    admission = None
    failed = False
    session_ref = "workspace-cli-session:" + str(uuid4())
    epoch = "workspace-cli-epoch:" + str(uuid4())
    op_ref = "workspace-cli-materialize:" + str(uuid4())
    op_digest = ContentDigest.of_bytes((op_ref + planned.plan.graph.graph_digest.value).encode())
    issuer = command.sources.declaration_scope_runtime
    try:
        validate_direct_cli_graph_scope(holder)
        if planned.demands is not None:
            from .declaration_product_membership import (
                read_declaration_product_correspondence_package,
            )
            pair = product.host.catalog_pair
            if type(pair) is not WorkspaceJointCatalogResolvers:
                raise TypeError("original paired graph catalog required")
            if any(type(item) is not WorkspaceDeclarationProductCorrespondence for item in pair.source_correspondences):
                raise TypeError("original declaration product correspondences required")
            correspondences = cast(tuple[WorkspaceDeclarationProductCorrespondence, ...], pair.source_correspondences)
            source_pairs = tuple((item, pair.workspace.package(
                read_declaration_product_correspondence_package(item).package_ref)) for item in correspondences)
            issuer._bind_original_dependency_product_publisher(backing.publisher, source_correspondences=source_pairs)

        async def prepare(preparation):
            try:
                command, product, planned, backing, evidence = state.command, state.product, state.planned, state.backing, state.evidence
                validate_direct_cli_graph_scope(holder)
                node_retention.close()
                state.prepared = None
                state.operation = state.operation_admission = state.execution_plan = state.operation_request = None
                binding, = tuple(item for item in bindings if item == preparation.node_execution_binding)
                participant, = tuple(item for item in product.participants if item.package_ref == binding.package.package_ref)
                state.source = participant.source
                state.active_binding = binding if planned.demands is not None else None
                _, _, runtime_binding = _execution_participant(command, state.source, product)
                validate_direct_cli_graph_scope(holder)
                dependencies = None
                if planned.demands is not None:
                    operation = planned.demands.operation(binding)
                    expected = issuer._dependency_validator[0].expectation(operation)
                    inventory = issuer.issue_product_dependency_inventory(operation, expected=expected)
                    resolution = issuer.issue_dependency_resolution(operation, inventory_admission=inventory, expected=expected)
                    original_fulfillment = issuer.issue_dependency_fulfillment(resolution, expected=expected)
                    original_body = issuer.read_dependency_products(original_fulfillment, resolution_admission=resolution, expected=expected)
                    original_value = SemanticDependencyProductInputCodec().decode(original_body.canonical_body)
                    original_rows = {(item.demand_digest, item.body.coordinate): item for item in original_value.products}
                    if len(preparation.ordered_dependency_bodies) != len(preparation.ordered_fulfilled_products):
                        raise ContractViolation("original graph dependency occurrence count differs")
                    portable_rows = {(item.target_resolution.demand_digest, item.consumed_body_coordinate): (item, body)
                        for item, body in zip(preparation.ordered_fulfilled_products,
                            preparation.ordered_dependency_bodies, strict=True)}
                    if (len(original_rows) != len(original_value.products)
                        or len(portable_rows) != len(preparation.ordered_fulfilled_products)
                        or set(original_rows) != set(portable_rows)):
                        raise ContractViolation("original node fulfillment differs from graph products")
                    for key, original in original_rows.items():
                        portable, body = portable_rows[key]
                        if (original.coordinate.package != portable.head_h2_reread_evidence.head.package
                            or original.provenance_digest != portable.head_h1_reread_evidence_digest):
                            raise ContractViolation("original graph supplier differs")
                        if body != original.body:
                            raise ContractViolation("original graph dependency body differs")
                    consumes_products = any(item.contract == SemanticDependencyProductInputCodec.contract
                        for item in runtime_binding.runtime.profile.inputs)
                    if original_rows and not consumes_products:
                        raise ContractViolation("original product dependencies require declared recipe input")
                    if consumes_products:
                        dependencies = DirectCLIProductDependencyAdmissions(operation, resolution, original_fulfillment, original_body)
                elif preparation.ordered_dependency_bodies or preparation.ordered_fulfilled_products:
                    raise ContractViolation("original graph dependency admissions unavailable")
                state.prepared = await prepare_direct_cli_selected_product_inputs(command, state.source, product,
                    retention=node_retention, dependency_admissions=dependencies)
                resolver = _OriginalPlanResolver(holder)
                invocation = state.prepared.closure.invocation
                state.execution_plan = WorkspaceMaterializeExecutionPlan.create(
                    source_authority_ref=binding.package_entry.source_authority_ref,
                    source_authority_digest=binding.package_entry.source_authority_digest.value,
                    operation_ref=op_ref, operation_digest=op_digest.value, invocation=invocation,
                    input_bodies=state.prepared.closure.input_bodies)
                closure_digest = derive_workspace_materialize_execution_input_closure_digest(state.execution_plan.input_bodies)
                state.operation_request = WorkspaceMaterializeOperationRequest.create(
                    workspace_session_ref=session_ref, epoch=epoch, participant_ref="workspace-cli-local",
                    actor_ref="workspace-cli-local", workflow_session_ref="workspace-cli-local",
                    materialization_attempt_ref=op_ref, branch_baseline_ref=evidence.repository_binding_ref,
                    branch_baseline_digest=evidence.source_identity_digest, branch_baseline_grade="source_head_local_operational",
                    package_ref=binding.package.package_ref, package_kind=binding.package.package_kind,
                    manifest_digest=binding.package.manifest_digest.value,
                    source_authority_ref=binding.package_entry.source_authority_ref,
                    source_authority_digest=binding.package_entry.source_authority_digest.value,
                    operation_ref=op_ref, operation_digest=op_digest.value, profile_ref=invocation.profile_ref,
                    profile_digest=invocation.profile_digest.value, plan_resolver_ref=resolver.implementation_ref,
                    plan_resolver_digest=resolver.implementation_digest, execution_input_closure_digest=closure_digest,
                    expected_materialization_head_revision=preparation.expected_package_head_revision,
                    expected_session_head_revision=preparation.expected_session_head_revision,
                    expected_session_cursor=preparation.expected_session_cursor,
                    expected_predecessor_event_digest=(None if preparation.expected_predecessor_event_digest is None
                        else preparation.expected_predecessor_event_digest.value))
                authority = _OriginalOperationAuthority(holder)
                input_admission = admit_workspace_materialize_execution_input_composition(
                    package_ref=binding.package.package_ref, package_kind=binding.package.package_kind,
                    manifest_digest=binding.package.manifest_digest.value,
                    source_authority_ref=binding.package_entry.source_authority_ref,
                    source_authority_digest=binding.package_entry.source_authority_digest.value,
                    operation_ref=op_ref, operation_digest=op_digest.value, profile_ref=invocation.profile_ref,
                    profile_digest=invocation.profile_digest.value, plan_resolver_ref=resolver.implementation_ref,
                    plan_resolver_digest=resolver.implementation_digest, input_bodies=state.execution_plan.input_bodies,
                    composition_authority=authority)
                state.operation_admission = admit_workspace_materialize_operation(request=state.operation_request,
                    operation_authority=authority, execution_input_admission=input_admission)

                @contextmanager
                def node_use(original):
                    use = _OriginalGraphNodeUse(holder, original)
                    use.validate()
                    yield use
                    use.validate()

                node_backing = WorkspaceMaterializationGraphBacking(state_root=root,
                    repository_binding_ref=evidence.repository_binding_ref, runtime=runtime_binding.runtime,
                    state_store=backing.publisher._state_store)
                state.operation = WorkspaceMaterializeOperation(runtime=runtime_binding.runtime, plan_resolver=resolver,
                    publisher=node_backing.publisher, session_journal=backing.session_journal,
                    graph_product_registration=runtime_binding.registration, graph_node_use=node_use,
                    graph_selected_input=_selected_input)
                return state.operation, state.operation_admission
            finally:
                preparation = command = product = planned = backing = evidence = None
                binding = participant = runtime_binding = dependencies = None
                operation = expected = inventory = resolution = original_fulfillment = original_body = None
                original_value = original_rows = portable_rows = key = original = portable = body = None
                consumes_products = resolver = invocation = closure_digest = authority = input_admission = None
                node_backing = None
                node_use = None  # pyright: ignore[reportAssignmentType]

        state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
            head_reader=lambda package, role: state.backing.publisher._read_graph_v2_head(package, observation_role=role),
            body_reader=backing.read_dependency_body, operation_preparer=prepare, session_journal=backing.session_journal)
        admitted_ns = time.perf_counter_ns()
        admission = _issue_workspace_direct_command_graph_execution(scope=holder, plan_result=planned.plan,
            workspace_session_ref=session_ref, epoch=epoch, participant_ref="workspace-cli-local", actor_ref="workspace-cli-local",
            workflow_session_ref="workspace-cli-local", materialization_attempt_ref=op_ref,
            branch_baseline_ref=evidence.repository_binding_ref, branch_baseline_digest=ContentDigest(evidence.source_identity_digest),
            branch_baseline_grade="source_head_local_operational", operation_ref=op_ref, operation_digest=op_digest,
            authority_grade=WorkspaceMaterializationSessionAuthorityGrade.LOCAL_OPERATIONAL,
            expected_session_head_revision=0, expected_session_cursor=0, expected_predecessor_event_digest=None, ports=state.ports)
        admission_ns = time.perf_counter_ns() - admitted_ns
        result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(admission, owner=holder)
        wire = encode_workspace_semantic_materialization_graph_result_v2(result, plan_result=planned.plan)
        return DirectCLIProductPublication(wire, time.perf_counter_ns() - started_ns, admission_ns, result)
    except BaseException:
        failed = True
        raise
    finally:
        try:
            if admission is not None:
                _dispose_workspace_direct_command_graph_execution(admission, scope=holder)
        except BaseException:
            if not failed:
                raise
        finally:
            try:
                node_retention.close()
            except BaseException:
                if not failed:
                    raise
            finally:
                state.terminal = True
                _SCOPES[:] = [(original, record) for original, record in _SCOPES if original is not holder]
                state.command = state.source = state.product = state.planned = None
                state.backing = state.ports = state.prepared = state.execution_plan = state.active_binding = None
                state.evidence = None
                state.operation_request = state.operation = state.operation_admission = None
                command = source = product = planned = backing = None
                retention = None  # pyright: ignore[reportAssignmentType]
                evidence = None
                result = admission = holder = None
