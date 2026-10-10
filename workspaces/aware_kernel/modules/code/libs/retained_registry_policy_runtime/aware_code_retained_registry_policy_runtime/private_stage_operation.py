"""Original-host binding for a private child of one selected public product.

Private and terminal execution are separate tracked calls. The original host
must authenticate the committed product between them; portable plan agreement
is never an execution admission.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from hashlib import sha256
from threading import RLock, current_thread
from typing import Any, cast
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    TerminalStatus,
)
from aware_code_semantic_contract_runtime.private_stage_contract import (
    CodePrivateStagePlanV1,
    PrivateStageEntry,
    PrivateStageRoleContract,
    encode_private_stage_plan,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    _result_tree,
    _ResultTree,
)

from . import direct_host as hosts
from . import selected_catalog_eligibility as eligibility
from .declaration_host import _selected_policy_source
from .direct_epoch_tracking import _BINDINGS, _guard


class _Nominal:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("private-stage uses are Code-issued only")

    def __reduce__(self):
        raise TypeError("private-stage uses cannot be serialized")

    def __copy__(self):
        raise TypeError("private-stage uses cannot be copied")

    def __deepcopy__(self, memo):
        del memo
        raise TypeError("private-stage uses cannot be copied")


class PrivateStageRootUse(_Nominal):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        raise TypeError("private-stage root is sealed")


class PrivateStageChildUse(_Nominal):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        raise TypeError("private-stage child is sealed")


class TerminalStageChildUse(_Nominal):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        raise TypeError("terminal-stage child is sealed")


@dataclass(slots=True)
class _RootState:
    host: hosts.DirectValidationHost
    policy: hosts.AdmittedRegistryPolicy
    contribution: products.SelectedProviderProductContribution
    plan_body: bytes
    private_registration: object
    public_registration: object
    source_handle: object
    source_digest: object
    public_eligibility: eligibility.SelectedProductCatalogEligibility
    epoch: object
    barrier_full: hosts._Entrance
    barrier_locked: hosts._Entrance
    node_full: hosts._Entrance
    node_locked: hosts._Entrance
    pid: int
    status: str = "ready"
    child: PrivateStageChildUse | None = None
    execution_origin: _PrivateExecutionOrigin | None = None
    read_prepare: hosts._Entrance | None = None
    read_spend: hosts._Entrance | None = None
    read_abort: hosts._Entrance | None = None
    private_completion: object = None
    terminal_child: TerminalStageChildUse | None = None
    terminal_origin: _TerminalExecutionOrigin | None = None


@dataclass(slots=True)
class _ChildState:
    root: PrivateStageRootUse
    operation_use: object
    inputs: tuple[PrivateStageRoleContract, ...]
    pid: int
    spent: bool = False


@dataclass(slots=True)
class _ExecutionState:
    child: PrivateStageChildUse | TerminalStageChildUse
    semantic_input: object
    status: str = "issued"
    closure_digest: object = None
    completion: object = None
    selected_admission: object = None
    read_phase: str = "pending"


@dataclass(slots=True)
class _TerminalChildState:
    root: PrivateStageRootUse
    operation_use: object
    admission: object
    product: SemanticBody | None
    product_tree: _ResultTree | None
    thread: object
    spent: bool = False


class _ExecutionContext(_Nominal):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        raise TypeError("private execution context is sealed")


class _PrivateExecutionOrigin(_Nominal):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        raise TypeError("private execution origin is sealed")

    def adopt(self, context):
        root, record, full, locked = _execution_origin(self)
        if type(context) is not _ExecutionContext:
            raise TypeError("exact private execution context required")
        stage = _EXECUTIONS.get(context)
        if stage is None or stage.status != "issued":
            raise ContractViolation("private execution context unavailable")
        child = _CHILDREN.get(cast(PrivateStageChildUse, stage.child))
        if child is None or child.root is not root or child.spent:
            raise ContractViolation("original private child unavailable")
        validate_private_child(cast(PrivateStageChildUse, stage.child))
        _check_declared_input(record, child, stage, full)
        _check_root(root)
        with _guard(record.epoch) as guard:
            eligibility.check_selected_product_catalog_eligibility_locked(
                record.public_eligibility, guard=guard
            )
            if record.node_locked.call(child.operation_use) is not None:
                raise ContractViolation("locked graph-node validator returned a value")
            _check_declared_input(record, child, stage, locked)
            with _LOCK:
                if stage.status != "issued" or child.spent:
                    raise ContractViolation("private child execution replay")
                child.spent = True
                stage.status = "running"
        return stage

    def validate(self, stage, closure):
        root, record, full, locked = _execution_origin(self)
        child = _running_stage(root, record, stage)
        if stage.selected_admission is not None and stage.read_phase != "complete":
            raise ContractViolation("private predecessor port has not completed")
        if type(closure) is not selected.SelectedProviderInvocationClosure:
            raise TypeError("exact private invocation closure required")
        closure.__post_init__()
        if (
            closure.invocation.profile_ref
            != products.read_selected_provider_private_stage_plan(
                record.contribution
            ).stages[0].profile.profile_ref
        ):
            raise ContractViolation("private invocation profile differs")
        digest = closure.invocation.digest
        if stage.closure_digest is not None and stage.closure_digest != digest:
            raise ContractViolation("private invocation changed")
        _check_declared_input(record, child, stage, full)
        _check_root(root)
        with _guard(record.epoch) as guard:
            eligibility.check_selected_product_catalog_eligibility_locked(
                record.public_eligibility, guard=guard
            )
            if record.node_locked.call(child.operation_use) is not None:
                raise ContractViolation("locked graph-node validator returned a value")
            _check_declared_input(record, child, stage, locked)
            stage.closure_digest = digest

    def complete(self, stage, completion):
        root, record, full, locked = _execution_origin(self)
        child = _running_stage(root, record, stage)
        runtime = selected._registration_state(record.private_registration).runtime
        if not runtime.owns_completion(completion):
            raise ContractViolation("private completion is not runtime-owned")
        snapshot = runtime.snapshot_completion(completion)
        plan = products.read_selected_provider_private_stage_plan(record.contribution)
        result = snapshot.result
        candidate = (
            result.current_result if result.status is TerminalStatus.CURRENT
            else result.transition.result
            if result.status is TerminalStatus.DELTA and result.transition is not None
            else None
        )
        if (
            stage.closure_digest is None
            or snapshot.invocation_digest != stage.closure_digest
            or snapshot.profile_digest != plan.stages[0].profile.digest
            or candidate is None
            or candidate.contract != plan.stages[0].terminal.contract
            or candidate.role != plan.stages[0].terminal.role
        ):
            raise ContractViolation("private candidate completion differs from selected use")
        _check_declared_input(record, child, stage, full)
        _check_root(root)
        with _guard(record.epoch) as guard:
            eligibility.check_selected_product_catalog_eligibility_locked(
                record.public_eligibility, guard=guard
            )
            if record.node_locked.call(child.operation_use) is not None:
                raise ContractViolation("locked graph-node validator returned a value")
            _check_declared_input(record, child, stage, locked)
            with _LOCK:
                if stage.status != "running":
                    raise ContractViolation("private execution already terminal")
                stage.completion = completion
                record.private_completion = completion
                stage.status = "completed"
                record.status = "private_completed"

    def fail(self, stage):
        root, record, _full, _locked = _execution_origin(self)
        if type(stage) is not _ExecutionState:
            raise ContractViolation("foreign private execution")
        with _LOCK:
            if stage.status in ("running", "issued"):
                stage.status = "failed"
                record.status = "failed"
                child = _CHILDREN.get(cast(PrivateStageChildUse, stage.child))
                if child is not None and child.root is root:
                    child.spent = True


_ROOTS: WeakKeyDictionary[PrivateStageRootUse, _RootState] = WeakKeyDictionary()
_CHILDREN: WeakKeyDictionary[PrivateStageChildUse, _ChildState] = WeakKeyDictionary()
_BOUND: dict[products.SelectedProviderProductContribution, PrivateStageRootUse] = {}
_ORIGINS: WeakKeyDictionary[_PrivateExecutionOrigin, tuple] = WeakKeyDictionary()
_EXECUTIONS: WeakKeyDictionary[_ExecutionContext, _ExecutionState] = WeakKeyDictionary()
_TERMINALS: WeakKeyDictionary[TerminalStageChildUse, _TerminalChildState] = WeakKeyDictionary()
_TERMINAL_ORIGINS: WeakKeyDictionary[_TerminalExecutionOrigin, PrivateStageRootUse] = WeakKeyDictionary()
_LOCK = RLock()
_BODY_POST = SemanticBody.__dict__["__post_init__"]


def _execution_origin(origin: _PrivateExecutionOrigin) -> tuple:
    if type(origin) is not _PrivateExecutionOrigin:
        raise TypeError("exact private execution origin required")
    association = _ORIGINS.get(origin)
    if association is None or association[1].pid != os.getpid():
        raise ContractViolation("original private execution origin unavailable")
    if association[1].execution_origin is not origin:
        raise ContractViolation("private execution origin changed")
    return association


def _running_stage(root, record, stage) -> _ChildState:
    if type(stage) is not _ExecutionState or stage.status != "running":
        raise ContractViolation("original running private execution required")
    child = _CHILDREN.get(cast(PrivateStageChildUse, stage.child))
    if (
        child is None
        or child.root is not root
        or not child.spent
        or record.child is not stage.child
        or record.status != "private_admitted"
    ):
        raise ContractViolation("private execution child changed")
    return child


def _check_declared_input(record, child, stage, entrance) -> None:
    if entrance.call(child.operation_use, stage.semantic_input) is not None:
        raise ContractViolation("original private input validator returned a value")


def _live_stage(state: hosts._State, stage: PrivateStageEntry) -> object:
    """Match every declared stage coordinate to one original host registration."""
    retained = state.product_retention
    if retained is None:
        raise ContractViolation("original product registration pool unavailable")
    retained.validate()
    matches = []
    for (runtime, registration), entry in zip(
        retained.products, retained.entries, strict=True
    ):
        provider_key, profile, declaration, binding, digest = entry
        if (
            provider_key == stage.provider_key
            and profile.profile_ref == stage.profile.profile_ref
            and profile.version == stage.profile.version
            and profile.digest == stage.profile.digest
        ):
            catalog_entry = retained.resolver.read_profile_binding(
                profile=profile, semantic_provider_key=provider_key
            )
            if (
                catalog_entry.binding_digest != digest
                or binding.implementation != stage.implementation
                or binding.configuration != stage.configuration
                or runtime.profile != profile
                or not any(
                    role.role == stage.terminal.role
                    and role.contract == stage.terminal.contract
                    for role in (declaration.result_role, *declaration.output_roles)
                )
                or not any(
                    product.role == stage.terminal.role
                    and product.contract == stage.terminal.contract
                    for product in catalog_entry.result_product_contracts
                )
                or any(
                    not any(
                        declared.role == item.role
                        and declared.contract == item.contract
                        for declared in profile.inputs
                    )
                    for item in stage.inputs
                )
                or tuple(
                    (item.role, item.contract) for item in stage.inputs
                ) != tuple(
                    (item.role, item.contract) for item in profile.inputs
                )
            ):
                raise ContractViolation("private-stage live profile differs from plan")
            selected.validate_selected_provider_registration(
                runtime,
                registration,
                expected_profile=profile,
                expected_declaration=declaration,
                expected_binding=binding,
            )
            matches.append(registration)
    if len(matches) != 1:
        raise ContractViolation("unique original private-stage registration required")
    return matches[0]


def _check_root(root: PrivateStageRootUse) -> tuple[_RootState, CodePrivateStagePlanV1]:
    if type(root) is not PrivateStageRootUse:
        raise TypeError("exact private-stage root required")
    record = _ROOTS.get(root)
    if record is None or record.pid != os.getpid() or record.status == "closed":
        raise ContractViolation("private-stage root unavailable")
    state = hosts._state(record.host)
    if state.source_rail != "declaration_v3":
        raise ContractViolation("private stage requires original v3 host")
    if _BINDINGS.get(record.host) is not record.epoch:
        raise ContractViolation("private-stage epoch changed")
    for entrance in (
        record.barrier_full, record.barrier_locked,
        record.node_full, record.node_locked,
    ):
        entrance.check()
    plan = products.read_selected_provider_private_stage_plan(record.contribution)
    if encode_private_stage_plan(plan) != record.plan_body:
        raise ContractViolation("private-stage original plan changed")
    public = products.read_selected_provider_product_contribution(record.contribution)
    if public.expected.registration is not record.public_registration:
        raise ContractViolation("private-stage public registration changed")
    if (
        _live_stage(state, plan.stages[0]) is not record.private_registration
        or _live_stage(state, plan.stages[1]) is not record.public_registration
    ):
        raise ContractViolation("private-stage original registrations changed")
    selected._validate_selected_private_stage_predecessor_port(
        record.private_registration
    )
    view = eligibility.read_selected_product_catalog_eligibility(
        record.public_eligibility
    )
    if (
        view.source_identity_digest != record.source_digest
        or view.profile_ref != plan.public_profile.profile_ref
        or view.semantic_provider_key != plan.stages[1].provider_key
        or plan.stages[1].terminal.role not in view.terminal_roles
    ):
        raise ContractViolation("private-stage public selection changed")
    policy_record = hosts._POLICIES.get(record.policy)
    if (
        policy_record is None
        or policy_record[0] is not record.host
        or policy_record[1] is not record.source_handle
    ):
        raise ContractViolation("private-stage selected source changed")
    with _selected_policy_source(record.host, record.policy) as (
        original_state, _closure, admitted, source
    ):
        if (
            original_state is not state
            or len(admitted.grants) != 1
            or source.expectation.source_identity_digest != record.source_digest
        ):
            raise ContractViolation("private-stage selected package changed")
    return record, plan


def bind_private_stage_plan(
    host: hosts.DirectValidationHost,
    policy: hosts.AdmittedRegistryPolicy,
    public_contribution: products.SelectedProviderProductContribution,
) -> PrivateStageRootUse:
    """Bind the owner-produced plan to one selected source and two live products."""
    state = hosts._state(host)
    if state.source_rail != "declaration_v3":
        raise ContractViolation("private stage requires original v3 host")
    with _LOCK:
        if public_contribution in _BOUND:
            raise ContractViolation("private-stage original plan already bound")
    plan = products.read_selected_provider_private_stage_plan(public_contribution)
    public = products.read_selected_provider_product_contribution(public_contribution)
    private_registration = _live_stage(state, plan.stages[0])
    public_registration = _live_stage(state, plan.stages[1])
    selected._validate_selected_private_stage_predecessor_port(
        private_registration
    )
    if public.expected.registration is not public_registration:
        raise ContractViolation("private-stage public owner differs")
    epoch = _BINDINGS.get(host)
    if epoch is None:
        raise ContractViolation("original private-stage epoch required")
    factory = state.methods["factory"].receiver
    entrances = tuple(
        hosts._capture(factory, name)
        for name in (
            "validate_committed_private_product",
            "check_committed_private_product_locked",
            "validate_selected_graph_node_use",
            "check_selected_graph_node_use_locked",
        )
    )
    policy_record = hosts._POLICIES.get(policy)
    if (
        type(policy) is not hosts.AdmittedRegistryPolicy
        or policy_record is None
        or policy_record[0] is not host
        or policy_record[6] is not epoch
    ):
        raise ContractViolation("original selected private-stage policy required")
    with _selected_policy_source(host, policy) as (
        original_state, _closure, admitted, source
    ):
        if original_state is not state or len(admitted.grants) != 1:
            raise ContractViolation("one original selected package required")
        source_digest = source.expectation.source_identity_digest
    public_eligibility = eligibility.issue_selected_product_catalog_eligibility(
        host, policy, public_registration
    )
    view = eligibility.read_selected_product_catalog_eligibility(public_eligibility)
    if (
        view.source_identity_digest != source_digest
        or view.profile_ref != plan.public_profile.profile_ref
        or view.semantic_provider_key != plan.stages[1].provider_key
        or plan.stages[1].terminal.role not in view.terminal_roles
    ):
        raise ContractViolation("private-stage public selection differs")
    root = object.__new__(PrivateStageRootUse)
    with _LOCK:
        _ROOTS[root] = _RootState(
            host, policy, public_contribution, encode_private_stage_plan(plan),
            private_registration, public_registration, policy_record[1],
            source_digest, public_eligibility, epoch,
            entrances[0], entrances[1], entrances[2], entrances[3], os.getpid(),
        )
    try:
        _check_root(root)
        with _guard(epoch) as guard:
            eligibility.check_selected_product_catalog_eligibility_locked(
                public_eligibility, guard=guard
            )
            with _LOCK:
                if public_contribution in _BOUND:
                    raise ContractViolation("private-stage original plan already bound")
                _BOUND[public_contribution] = root
    except BaseException:
        with _LOCK:
            _ROOTS.pop(root, None)
        raise
    return root


def admit_private_child(
    root: PrivateStageRootUse,
    *,
    operation_use: object,
    declared_inputs: tuple[PrivateStageRoleContract, ...],
) -> PrivateStageChildUse:
    """Issue one unspent private child; this does not invoke a provider."""
    record, plan = _check_root(root)
    if record.status != "ready":
        raise ContractViolation("private-stage child already admitted")
    if type(declared_inputs) is not tuple or declared_inputs != plan.stages[0].inputs:
        raise ContractViolation("private child declared inputs differ from owner plan")
    if operation_use is None:
        raise ContractViolation("original graph-node use required")
    if record.node_full.call(operation_use, closure=None) is not None:
        raise ContractViolation("original graph-node validator returned a value")
    _check_root(root)
    with _guard(record.epoch) as guard:
        eligibility.check_selected_product_catalog_eligibility_locked(
            record.public_eligibility, guard=guard
        )
        if record.node_locked.call(operation_use) is not None:
            raise ContractViolation("locked graph-node validator returned a value")
        child = object.__new__(PrivateStageChildUse)
        with _LOCK:
            if _ROOTS.get(root) is not record or record.status != "ready":
                raise ContractViolation("private-stage root changed during admission")
            _CHILDREN[child] = _ChildState(
                root, operation_use, declared_inputs, os.getpid()
            )
            record.child = child
            record.status = "private_admitted"
    return child


def validate_private_child(child: PrivateStageChildUse) -> None:
    """Revalidate the exact unspent child before selected execution consumes it."""
    if type(child) is not PrivateStageChildUse:
        raise TypeError("exact private-stage child required")
    state = _CHILDREN.get(child)
    if state is None or state.pid != os.getpid() or state.spent:
        raise ContractViolation("private-stage child unavailable")
    root, _plan = _check_root(state.root)
    if root.status != "private_admitted" or root.child is not child:
        raise ContractViolation("private-stage child differs from root")
    if root.node_full.call(state.operation_use, closure=None) is not None:
        raise ContractViolation("original graph-node validator returned a value")
    with _guard(root.epoch) as guard:
        eligibility.check_selected_product_catalog_eligibility_locked(
            root.public_eligibility, guard=guard
        )
        if root.node_locked.call(state.operation_use) is not None:
            raise ContractViolation("locked graph-node validator returned a value")


def bind_private_stage_execution(root: PrivateStageRootUse) -> None:
    """Bind the private runtime to the original Code-defined input port.

    Current hosts without these entrances refuse here. A structurally matching
    caller-supplied validator cannot establish this binding.
    """
    record, _plan = _check_root(root)
    if record.status != "ready" or record.execution_origin is not None:
        raise ContractViolation("private execution binding already used")
    state = hosts._state(record.host)
    factory = state.methods["factory"].receiver
    try:
        full = hosts._capture(factory, "validate_private_stage_input_use")
        locked = hosts._capture(factory, "check_private_stage_input_use_locked")
        prepare = hosts._capture(factory, "prepare_private_stage_read_input")
        spend = hosts._capture(factory, "spend_private_stage_read_input_locked")
        abort = hosts._capture(factory, "abort_private_stage_read_input")
    except AttributeError as error:
        raise ContractViolation(
            "original private input-port entrances unavailable"
        ) from error
    registration = selected._registration_state(
        cast(selected.AdmittedSemanticProviderRegistration, record.private_registration)
    )
    runtime = registration.runtime
    if registration.private_stage_predecessor_input is None:
        raise ContractViolation("original predecessor input binding required")
    origin = object.__new__(_PrivateExecutionOrigin)
    _check_root(root)
    with _guard(record.epoch) as guard:
        eligibility.check_selected_product_catalog_eligibility_locked(
            record.public_eligibility, guard=guard
        )
        with _LOCK:
            if record.execution_origin is not None or record.status != "ready":
                raise ContractViolation("private execution binding changed")
            record.execution_origin = origin
            record.read_prepare, record.read_spend, record.read_abort = prepare, spend, abort
            _ORIGINS[origin] = (root, record, full, locked)
        try:
            selected._bind_selected_execution_lifecycle(
                runtime, record.private_registration, origin,
                terminal_mode="runtime_completion",
            )
        except BaseException:
            with _LOCK:
                record.execution_origin = None
                record.read_prepare = record.read_spend = record.read_abort = None
                _ORIGINS.pop(origin, None)
            raise


def execute_private_child(
    child: PrivateStageChildUse, *, semantic_input: object,
) -> object:
    """Spend one child through the original tracked selected-provider runtime.

    The original host validator must authenticate the declared input through
    its owner-local approval; Code never receives that approval or source state.
    This private completion is a candidate, never a committed Meta product.
    """
    validate_private_child(child)
    state = _CHILDREN[child]
    record, _plan = _check_root(state.root)
    if record.execution_origin is None:
        raise ContractViolation("original private execution binding required")
    _execution_origin(record.execution_origin)
    original_operation_use = state.operation_use
    original_abort = record.read_abort
    original_origin = record.execution_origin
    stage = _ExecutionState(child, semantic_input)
    context = object.__new__(_ExecutionContext)
    with _LOCK:
        if state.spent or record.status != "private_admitted":
            raise ContractViolation("private child execution replay")
        _EXECUTIONS[context] = stage
    original_registration = cast(
        selected.AdmittedSemanticProviderRegistration, record.private_registration
    )
    runtime = selected._registration_state(original_registration).runtime
    admission = None
    try:
        admission = selected.issue_selected_provider_execution(
            runtime, original_registration, semantic_input,
            operation_context=context,
        )
        stage.selected_admission = admission
        from .private_predecessor_read import invoke_private_predecessor_port

        invoke_private_predecessor_port(child, semantic_input, admission)
        return selected.execute_selected_provider(runtime, admission)
    except BaseException as error:
        # Terminal Code state first, then every owner cleanup, outside exclusion.
        if admission is not None:
            try:
                selected._abort_selected_provider_execution(runtime, admission)
            except BaseException as cleanup_error:
                error.add_note(f"selected-admission abort: {type(cleanup_error).__name__}")
        if stage.status in ("issued", "running"):
            try:
                original_origin.fail(stage)
            except BaseException as cleanup_error:
                stage.status = record.status = "failed"
                state.spent = True
                error.add_note(f"private execution abort: {type(cleanup_error).__name__}")
        if original_abort is not None:
            try:
                result = original_abort.call(original_operation_use)
                if result is not None:
                    raise ContractViolation("original read abort returned a value")
            except BaseException as cleanup_error:
                error.add_note(f"original owner read abort: {type(cleanup_error).__name__}")
        raise
    finally:
        _EXECUTIONS.pop(context, None)


def _terminal_root(root):
    """Recognize only this process's registered root, without owner dispatch."""
    record = _registered_root_record(root)
    if type(root) is not PrivateStageRootUse:
        if record is not None and record.pid == os.getpid():
            _fail_terminal(root)
        raise TypeError("exact private-stage root required")
    if record is None or record.pid != os.getpid():
        raise ContractViolation("private-stage root unavailable")
    return record


def _registered_root_record(root):
    for original, record in _ROOTS.items():
        if original is root:
            return record
    return None


def _remove_terminal(child):
    # Reuse the stored weakref's cached hash. A restamped key must not receive
    # a new hash/equality dispatch while its original family is retired.
    for original in _TERMINALS.keyrefs():
        if original() is child:
            return cast(Any, _TERMINALS).data.pop(original, None)
    return None


def _fail_terminal(root):
    record = _registered_root_record(root)
    if record is None or record.pid != os.getpid():
        return
    with _LOCK:
        record.status = "failed"
        record.private_completion = None
        if record.terminal_child is not None:
            child = _remove_terminal(record.terminal_child)
            if child is not None:
                child.spent = True
                _release_terminal_state(child)
        if record.terminal_origin is not None:
            _TERMINAL_ORIGINS.pop(record.terminal_origin, None)


def _release_terminal_state(state):
    """Release Code's references without closing any borrowed owner resource."""
    state.admission = state.product = state.product_tree = None
    state.operation_use = state.thread = None


def _check_committed(root, record, admission):
    _check_root(root)
    if record.private_completion is None:
        raise ContractViolation("original private completion unavailable")
    if record.barrier_full.call(root, record.private_completion, admission) is not None:
        raise ContractViolation("original committed-product validator returned a value")
    _check_root(root)


def _check_committed_locked(root, record, admission, operation_use, guard):
    eligibility.check_selected_product_catalog_eligibility_locked(
        record.public_eligibility, guard=guard
    )
    if record.node_locked.call(operation_use) is not None:
        raise ContractViolation("locked graph-node validator returned a value")
    if record.barrier_locked.call(root, record.private_completion, admission) is not None:
        raise ContractViolation("locked committed-product validator returned a value")


def admit_terminal_child(
    root: PrivateStageRootUse, *, operation_use: object,
    private_completion: object, admitted_committed_product: object,
    committed_product_body: SemanticBody,
) -> TerminalStageChildUse:
    """Authenticate an original admission and its detached committed input.

    Workspace verifies its nominal admission and causal private completion.
    Its original node validator must bind the complete invocation to that
    admission. The separately supplied body is portable input, never approval.
    Neither nominal admission nor owner handles enter the semantic provider.
    """
    record = _terminal_root(root)
    try:
        record, plan = _check_root(root)
        if record.status != "private_completed":
            raise ContractViolation("private completion must precede terminal admission")
        if private_completion is not record.private_completion:
            raise ContractViolation("terminal admission requires exact private completion")
        with _LOCK:
            if record.status != "private_completed":
                raise ContractViolation("terminal admission replay")
            record.status = "barrier_checking"
        if record.child is None:
            raise ContractViolation("original private child unavailable")
        private = _CHILDREN.get(record.child)
        if private is None or operation_use is not private.operation_use:
            raise ContractViolation("terminal node differs from original private node")
        if type(committed_product_body) is not SemanticBody:
            raise TypeError("exact committed SemanticBody required")
        if type.__getattribute__(SemanticBody, "__dict__").get("__post_init__") is not _BODY_POST:
            raise ContractViolation("original committed body validator changed")
        tree = _result_tree(committed_product_body)
        tree.check(committed_product_body)
        data = _body_data(tree)
        contract = plan.barrier.committed_product.contract
        if (data[0] != plan.barrier.committed_product.role
                or data[1:4] != (contract.key, contract.version, contract.schema_digest.value)):
            raise ContractViolation("committed product binding differs from barrier")
        if data[5] != "sha256:" + sha256(data[7]).hexdigest() or data[6] != len(data[7]):
            raise ContractViolation("committed body digest or size differs from coordinate")
        _check_committed(root, record, admitted_committed_product)
        if record.node_full.call(operation_use, closure=None) is not None:
            raise ContractViolation("original graph-node validator returned a value")
        tree.check(committed_product_body)
        runtime = selected._registration_state(cast(
            selected.AdmittedSemanticProviderRegistration, record.public_registration
        )).runtime
        child = object.__new__(TerminalStageChildUse)
        origin = object.__new__(_TerminalExecutionOrigin)
        with _guard(record.epoch) as guard:
            _check_committed_locked(
                root, record, admitted_committed_product, operation_use, guard
            )
            tree.check(committed_product_body)
            with _LOCK:
                if (record.status != "barrier_checking"
                        or record.private_completion is not private_completion):
                    raise ContractViolation("terminal admission changed or replayed")
                _TERMINALS[child] = _TerminalChildState(
                    root, operation_use, admitted_committed_product,
                    committed_product_body, tree, current_thread()
                )
                record.terminal_child, record.terminal_origin = child, origin
                record.status = "terminal_admitted"
                _TERMINAL_ORIGINS[origin] = root
            selected._bind_selected_execution_lifecycle(
                runtime, record.public_registration, origin,
                terminal_mode="runtime_completion",
            )
        return child
    except BaseException:
        _fail_terminal(root)
        raise
    finally:
        # A retained rejection traceback must not become another admission or
        # source-buffer retention rail. Never clear the foreign owner's frame.
        record = private = tree = runtime = None
        private_completion = admitted_committed_product = operation_use = None
        del committed_product_body


def _terminal_state(child):
    if type(child) is not TerminalStageChildUse:
        # A restamped registered child is terminal. Never invoke its hash,
        # equality or attribute behavior to find its original family.
        for original, original_state in _TERMINALS.items():
            if original is child:
                _fail_terminal(original_state.root)
                break
        raise TypeError("exact terminal-stage child required")
    state = _TERMINALS.get(child)
    if state is None:
        raise ContractViolation("terminal-stage child unavailable")
    record = _terminal_root(state.root)
    if (current_thread() is not state.thread or record.terminal_child is not child
            or record.status not in ("terminal_admitted", "terminal_running", "terminal_completing")):
        raise ContractViolation("original terminal-stage use unavailable")
    return state, record


def _body_data(tree: _ResultTree) -> tuple[str, str, str, str, str, str, int, bytes]:
    """Read scalar leaves already captured through original slot descriptors."""
    coordinate = tree.children[0].children
    contract = coordinate[1].children
    values = (coordinate[0].original, contract[0].original, contract[1].original,
            contract[2].children[0].original, coordinate[2].original,
            coordinate[3].children[0].original, coordinate[4].original,
            tree.children[1].original)
    if any(type(value) is not kind for value, kind in zip(
        values, (str, str, str, str, str, str, int, bytes), strict=True
    )):
        raise ContractViolation("committed body scalar types differ")
    return cast(tuple[str, str, str, str, str, str, int, bytes], values)


def _body_content(body):
    tree = _result_tree(body)
    tree.check(body)
    return _body_data(tree)[1:]


def _check_terminal_product(state: _TerminalChildState):
    if state.product_tree is None or state.product is None:
        raise ContractViolation("terminal committed input already released")
    state.product_tree.check(state.product)


def _check_terminal(child, *, closure=None):
    state, record = _terminal_state(child)
    root = state.root
    if type.__getattribute__(SemanticBody, "__dict__").get("__post_init__") is not _BODY_POST:
        raise ContractViolation("original committed body validator changed")
    _check_terminal_product(state)
    _check_committed(root, record, state.admission)
    _record, plan = _check_root(root)
    if closure is not None:
        if type(closure) is not selected.SelectedProviderInvocationClosure:
            raise TypeError("exact terminal invocation closure required")
        tree = _result_tree(closure.input_bodies)
        tree.check(closure.input_bodies)
        closure.__post_init__()
        if (closure.invocation.profile_ref != plan.stages[1].profile.profile_ref
                or tuple((b.coordinate.role, b.coordinate.contract)
                         for b in closure.input_bodies)
                != tuple((i.role, i.contract) for i in plan.stages[1].inputs)):
            raise ContractViolation("terminal invocation inputs differ from owner plan")
        matches = tuple(b for b in closure.input_bodies
                        if b.coordinate.role == plan.barrier.consumer_input_role)
        if len(matches) != 1 or _body_content(matches[0]) != _body_content(state.product):
            raise ContractViolation("terminal invocation lost exact committed product")
    if record.node_full.call(state.operation_use, closure=closure) is not None:
        raise ContractViolation("original graph-node validator returned a value")
    with _guard(record.epoch) as guard:
        _check_committed_locked(root, record, state.admission, state.operation_use, guard)
        _check_terminal_product(state)
        _terminal_state(child)
    return state, record


def _terminal_execution_root(origin):
    if type(origin) is not _TerminalExecutionOrigin:
        raise TypeError("exact terminal execution origin required")
    root = _TERMINAL_ORIGINS.get(origin)
    if root is None:
        raise ContractViolation("original terminal execution origin unavailable")
    record = _terminal_root(root)
    if record.terminal_origin is not origin:
        raise ContractViolation("terminal execution origin changed")
    return root


class _TerminalExecutionOrigin(_Nominal):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        raise TypeError("terminal execution origin is sealed")

    def adopt(self, context):
        root = _terminal_execution_root(self)
        if type(context) is not _ExecutionContext:
            raise TypeError("exact terminal execution context required")
        stage = _EXECUTIONS.get(context)
        if stage is None or stage.status != "issued":
            raise ContractViolation("terminal execution context unavailable")
        state, record = _check_terminal(stage.child)
        with _LOCK:
            if state.root is not root or state.spent or record.status != "terminal_admitted":
                raise ContractViolation("terminal child execution replay")
            state.spent = True
            stage.status = "running"
            record.status = "terminal_running"
        return stage

    def validate(self, stage, closure):
        root = _terminal_execution_root(self)
        if type(stage) is not _ExecutionState or stage.status != "running":
            raise ContractViolation("original running terminal execution required")
        state, _record = _check_terminal(stage.child, closure=closure)
        if state.root is not root or not state.spent:
            raise ContractViolation("original terminal child changed")
        digest = closure.invocation.digest
        if stage.closure_digest is not None and stage.closure_digest != digest:
            raise ContractViolation("terminal invocation changed")
        stage.closure_digest = digest

    def complete(self, stage, completion):
        root = _terminal_execution_root(self)
        if type(stage) is not _ExecutionState or stage.status != "running":
            raise ContractViolation("original running terminal execution required")
        state, record = _check_terminal(stage.child)
        if state.root is not root or not state.spent:
            raise ContractViolation("original terminal child changed")
        runtime = selected._registration_state(cast(
            selected.AdmittedSemanticProviderRegistration, record.public_registration
        )).runtime
        if not runtime.owns_completion(completion):
            raise ContractViolation("terminal completion is not runtime-owned")
        snapshot = runtime.snapshot_completion(completion)
        _record, plan = _check_root(root)
        result = snapshot.result
        coordinate = (result.current_result if result.status is TerminalStatus.CURRENT
                      else result.transition.result
                      if result.status is TerminalStatus.DELTA and result.transition is not None
                      else None)
        if (stage.closure_digest is None or snapshot.invocation_digest != stage.closure_digest
                or snapshot.profile_digest != plan.stages[1].profile.digest
                or coordinate is None or coordinate.role != plan.stages[1].terminal.role
                or coordinate.contract != plan.stages[1].terminal.contract):
            raise ContractViolation("terminal completion differs from selected use")
        with _guard(record.epoch) as guard:
            _check_committed_locked(root, record, state.admission, state.operation_use, guard)
            _check_terminal_product(state)
            with _LOCK:
                if stage.status != "running" or record.status != "terminal_running":
                    raise ContractViolation("terminal execution already completed")
                stage.completion, stage.status = completion, "completed"
                record.status = "terminal_completing"

    def fail(self, stage):
        root = _terminal_execution_root(self)
        if type(stage) is not _ExecutionState:
            raise ContractViolation("foreign terminal execution")
        state = _TERMINALS.get(cast(TerminalStageChildUse, stage.child))
        if state is None or state.root is not root:
            raise ContractViolation("foreign terminal execution")
        stage.status = "failed"
        _fail_terminal(root)


def execute_terminal_child(child: TerminalStageChildUse, *, semantic_input: object) -> object:
    """Spend one terminal child through the same original selected executor."""
    state, record = _terminal_state(child)
    root = state.root
    try:
        if state.spent:
            raise ContractViolation("terminal child execution replay")
        origin = record.terminal_origin
        if origin is None:
            raise ContractViolation("original terminal execution binding required")
        stage = _ExecutionState(child, semantic_input)
        context = object.__new__(_ExecutionContext)
        _EXECUTIONS[context] = stage
        registration = cast(selected.AdmittedSemanticProviderRegistration, record.public_registration)
        runtime = selected._registration_state(registration).runtime
        admission = None
        try:
            admission = selected.issue_selected_provider_execution(
                runtime, registration, semantic_input, operation_context=context
            )
            completion = selected.execute_selected_provider(runtime, admission)
            if stage.status != "completed" or stage.completion is not completion:
                raise ContractViolation("original terminal completion unavailable")
            # Final selected-owner observation may itself fail or revoke the
            # command. Do not release the barrier until the actual return is
            # freshly checked; provisional completion is insufficient.
            _check_terminal(child)
            with _guard(record.epoch) as guard:
                _check_committed_locked(root, record, state.admission, state.operation_use, guard)
                _check_terminal_product(state)
                with _LOCK:
                    if record.status != "terminal_completing":
                        raise ContractViolation("terminal success changed before return")
                    record.status = "terminal_completed"
                    record.private_completion = None
                    _TERMINALS.pop(child, None)
                    _release_terminal_state(state)
            return completion
        except BaseException as error:
            _fail_terminal(root)
            if admission is not None:
                try:
                    selected._abort_selected_provider_execution(runtime, admission)
                except BaseException as cleanup_error:  # noqa: BLE001 - preserve primary failure
                    error.add_note(f"terminal admission abort: {type(cleanup_error).__name__}")
            raise
        finally:
            _EXECUTIONS.pop(context, None)
            stage.semantic_input = stage.completion = None
    except BaseException:
        _fail_terminal(root)
        raise
    finally:
        record = state = semantic_input = None


def close_private_stage_plan(root: PrivateStageRootUse) -> None:
    """Revoke any unspent child; parent closure also invalidates every read."""
    if type(root) is not PrivateStageRootUse:
        raise TypeError("exact private-stage root required")
    record = _ROOTS.get(root)
    if record is None or record.pid != os.getpid():
        raise ContractViolation("private-stage root unavailable")
    with _LOCK:
        record.status = "closed"
        if record.child is not None:
            child = _CHILDREN.pop(record.child, None)
            if child is not None:
                child.spent = True
        if _BOUND.get(record.contribution) is root:
            del _BOUND[record.contribution]
        if record.execution_origin is not None:
            _ORIGINS.pop(record.execution_origin, None)
        if record.terminal_origin is not None:
            _TERMINAL_ORIGINS.pop(record.terminal_origin, None)
        if record.terminal_child is not None:
            terminal = _remove_terminal(record.terminal_child)
            if terminal is not None:
                _release_terminal_state(terminal)
        record.private_completion = None
        _ROOTS.pop(root, None)


__all__ = [
    "PrivateStageChildUse",
    "PrivateStageRootUse",
    "TerminalStageChildUse",
    "admit_private_child",
    "admit_terminal_child",
    "bind_private_stage_execution",
    "bind_private_stage_plan",
    "close_private_stage_plan",
    "execute_private_child",
    "execute_terminal_child",
    "validate_private_child",
]
