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
from typing import Any
from uuid import uuid4

from aware_code_retained_registry_policy_runtime.selected_root_intent import (
    derive_selected_root_intent,
)
from aware_code_semantic_contract_runtime import ContentDigest, ContractViolation
from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore

from . import direct_command_composition as composition
from .direct_cli_product_execution import (
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


def validate_direct_cli_graph_scope(holder, *, values=None):
    """Current original command/source checks, never a portable proof verdict."""
    state = _scope(holder)
    try:
        command, product = state.command, state.product
        composition._require_live_direct_workspace_command(command)
        validate_direct_cli_selected_host(product)
        command.sources.declaration_scope_runtime.read_selected_package_source(
            state.source
        )
        intent, required = derive_selected_root_intent(
            product.host.code_host, product.policy
        )
        (binding,) = state.planned.plan.graph_execution_binding.ordered_node_bindings
        pair = product.host.catalog_pair
        if (
            pair is not command.catalog_host._result
            or binding.package_entry != pair.workspace.package(product.package_ref)
            or binding.code_intent != intent
            or binding.required_result_products != (required,)
            or state.planned.plan.graph.edges
        ):
            raise ContractViolation("original direct graph selection differs")
        if state.prepared is not None:
            if (
                inspect.getattr_static(state.prepared.node, "validate")
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
    except BaseException:
        state.terminal = True
        raise
    finally:
        holder = state = values = command = product = binding = pair = intent = (
            required
        ) = None


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
            != state.planned.plan.graph_execution_binding.ordered_node_bindings[
                0
            ].package_entry
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
    """One selected source-backed node, ordinary local store, existing graph rail."""
    if (
        type(product) is not DirectCLISelectedProduct
        or type(planned) is not DirectCLIProductGraphPlan
    ):
        raise TypeError("original direct product/plan required")
    if (
        product.host.staged.command is not command
        or len(planned.plan.graph.nodes) != 1
        or planned.plan.graph.edges
    ):
        raise ContractViolation("complete original one-node direct graph required")
    started_ns = time.perf_counter_ns()
    validate_direct_cli_selected_host(product)
    (binding,) = planned.plan.graph_execution_binding.ordered_node_bindings
    (node,) = planned.plan.graph.nodes
    if node.head_observation.state != "missing":
        raise ContractViolation("original direct predecessor admission unavailable")
    (runtime_binding,) = product.host.staged.product_runtime_bindings
    evidence = (
        command.sources.declaration_scope_runtime.inspect_selected_package_evidence(
            source
        )
    )
    root = (
        composition._direct_workspace_cli_state_root(
            command.sources.observation_runtime._session.binding.root_path
        )
        / "materialization"
    )
    backing = WorkspaceMaterializationGraphBacking(
        state_root=root,
        repository_binding_ref=evidence.repository_binding_ref,
        runtime=runtime_binding.runtime,
        state_store=SqliteLocalOperationalStateStore(root / "heads.sqlite3"),
    )
    # Original primary local state observation. No historical/Meta genesis claim.
    if (
        backing.publisher._state_store.read(
            backing.publisher._state_namespace,
            binding.package.package_ref,
            include_deleted=True,
        )
        is not None
    ):
        raise ContractViolation("original direct package head moved after planning")
    holder = object.__new__(_DirectCLIProductGraphScope)
    state = _Scope(command, source, product, planned, backing, os.getpid(), get_ident())
    _SCOPES.append((holder, state))
    admission = None
    failed = False
    try:
        validate_direct_cli_graph_scope(holder)
        state.prepared = await prepare_direct_cli_selected_product_inputs(
            command, source, product, retention=retention
        )
        resolver = _OriginalPlanResolver(holder)
        invocation = state.prepared.closure.invocation
        op_ref = "workspace-cli-materialize:" + str(uuid4())
        op_digest = ContentDigest.of_bytes(
            (op_ref + planned.plan.graph.graph_digest.value).encode()
        )
        state.execution_plan = WorkspaceMaterializeExecutionPlan.create(
            source_authority_ref=binding.package_entry.source_authority_ref,
            source_authority_digest=binding.package_entry.source_authority_digest.value,
            operation_ref=op_ref,
            operation_digest=op_digest.value,
            invocation=invocation,
            input_bodies=state.prepared.closure.input_bodies,
        )
        closure_digest = derive_workspace_materialize_execution_input_closure_digest(
            state.execution_plan.input_bodies
        )
        session_ref = "workspace-cli-session:" + str(uuid4())
        state.operation_request = WorkspaceMaterializeOperationRequest.create(
            workspace_session_ref=session_ref,
            epoch="workspace-cli-epoch:" + str(uuid4()),
            participant_ref="workspace-cli-local",
            actor_ref="workspace-cli-local",
            workflow_session_ref="workspace-cli-local",
            materialization_attempt_ref=op_ref,
            branch_baseline_ref=evidence.repository_binding_ref,
            branch_baseline_digest=evidence.source_identity_digest,
            branch_baseline_grade="source_head_local_operational",
            package_ref=binding.package.package_ref,
            package_kind=binding.package.package_kind,
            manifest_digest=binding.package.manifest_digest.value,
            source_authority_ref=binding.package_entry.source_authority_ref,
            source_authority_digest=binding.package_entry.source_authority_digest.value,
            operation_ref=op_ref,
            operation_digest=op_digest.value,
            profile_ref=invocation.profile_ref,
            profile_digest=invocation.profile_digest.value,
            plan_resolver_ref=resolver.implementation_ref,
            plan_resolver_digest=resolver.implementation_digest,
            execution_input_closure_digest=closure_digest,
            expected_materialization_head_revision=0,
            expected_session_head_revision=0,
            expected_session_cursor=0,
            expected_predecessor_event_digest=None,
        )
        authority = _OriginalOperationAuthority(holder)
        input_admission = admit_workspace_materialize_execution_input_composition(
            package_ref=binding.package.package_ref,
            package_kind=binding.package.package_kind,
            manifest_digest=binding.package.manifest_digest.value,
            source_authority_ref=binding.package_entry.source_authority_ref,
            source_authority_digest=binding.package_entry.source_authority_digest.value,
            operation_ref=op_ref,
            operation_digest=op_digest.value,
            profile_ref=invocation.profile_ref,
            profile_digest=invocation.profile_digest.value,
            plan_resolver_ref=resolver.implementation_ref,
            plan_resolver_digest=resolver.implementation_digest,
            input_bodies=state.execution_plan.input_bodies,
            composition_authority=authority,
        )
        state.operation_admission = admit_workspace_materialize_operation(
            request=state.operation_request,
            operation_authority=authority,
            execution_input_admission=input_admission,
        )

        @contextmanager
        def node_use(original):
            use = _OriginalGraphNodeUse(holder, original)
            use.validate()
            yield use
            use.validate()

        state.operation = WorkspaceMaterializeOperation(
            runtime=runtime_binding.runtime,
            plan_resolver=resolver,
            publisher=backing.publisher,
            session_journal=backing.session_journal,
            graph_product_registration=runtime_binding.registration,
            graph_node_use=node_use,
            graph_selected_input=_selected_input,
        )

        async def prepare(preparation):
            validate_direct_cli_graph_scope(holder)
            if (
                preparation.node_execution_binding != binding
                or preparation.ordered_dependency_bodies
                or preparation.ordered_fulfilled_products
            ):
                raise ContractViolation("original graph-node preparation differs")
            return state.operation, state.operation_admission

        state.ports = _WorkspaceSemanticMaterializationGraphHostPorts(
            head_reader=lambda package, role: state.backing.publisher._read_graph_v2_head(
                package, observation_role=role
            ),
            body_reader=backing.read_dependency_body,
            operation_preparer=prepare,
            session_journal=backing.session_journal,
        )
        request = state.operation_request
        admitted_ns = time.perf_counter_ns()
        admission = _issue_workspace_direct_command_graph_execution(
            scope=holder,
            plan_result=planned.plan,
            workspace_session_ref=session_ref,
            epoch=request.epoch,
            participant_ref=request.participant_ref,
            actor_ref=request.actor_ref,
            workflow_session_ref=request.workflow_session_ref,
            materialization_attempt_ref=request.materialization_attempt_ref,
            branch_baseline_ref=request.branch_baseline_ref,
            branch_baseline_digest=ContentDigest(request.branch_baseline_digest),
            branch_baseline_grade=request.branch_baseline_grade,
            operation_ref=op_ref,
            operation_digest=op_digest,
            authority_grade=authority.authority_grade,
            expected_session_head_revision=0,
            expected_session_cursor=0,
            expected_predecessor_event_digest=None,
            ports=state.ports,
        )
        admission_ns = time.perf_counter_ns() - admitted_ns
        result = await WorkspaceSemanticMaterializationGraphCoordinator().execute(
            admission, owner=holder
        )
        wire = encode_workspace_semantic_materialization_graph_result_v2(
            result, plan_result=planned.plan
        )
        return DirectCLIProductPublication(
            wire, time.perf_counter_ns() - started_ns, admission_ns, result
        )
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
            state.terminal = True
            _SCOPES[:] = [
                (original, record) for original, record in _SCOPES if original is not holder
            ]
            state.command = state.source = state.product = state.planned = None
            state.backing = state.ports = state.prepared = state.execution_plan = None
            state.operation_request = state.operation = state.operation_admission = None
            command = source = product = planned = backing = None
            retention = None  # pyright: ignore[reportAssignmentType] - release traceback custody
            runtime_binding = evidence = resolver = invocation = authority = None
            request = result = admission = holder = None
