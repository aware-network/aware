"""Invocation-bound read grants; owner meaning and read state stay owner-local."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock, Thread, current_thread
from typing import cast
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.private_stage_contract import (
    PrivateStageRoleContract,
)
from aware_code_semantic_contract_runtime.runtime import (
    AdmittedSemanticValue,
    BoundSemanticInput,
    ProviderStepInvocation,
    SemanticBody,
    SemanticContractRuntime,
)

from . import private_stage_operation as stages


class PrivatePredecessorReadGrant(stages._Nominal):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        raise TypeError("private predecessor grant is sealed")


@dataclass(slots=True)
class _Read:
    root: stages.PrivateStageRootUse
    record: stages._RootState
    child: stages._ChildState
    stage: stages._ExecutionState
    context: stages._ExecutionContext
    admission: selected.SelectedSemanticProviderExecutionAdmission
    execution: selected._ExecutionState
    registration: selected._RegistrationState
    runtime: SemanticContractRuntime
    host_state: stages.hosts._State
    binding: PrivateStageRoleContract
    body: SemanticBody
    child_handle: stages.PrivateStageChildUse
    operation_use: object
    semantic_input: object
    root_identities: tuple[object, ...]
    step_identities: tuple[object, ...]
    thread: Thread
    pid: int
    port_active: bool = False
    status: str = "issued"


_GRANTS: WeakKeyDictionary[PrivatePredecessorReadGrant, _Read] = WeakKeyDictionary()
_LOCK = RLock()


def _root_identities(record: stages._RootState) -> tuple[object, ...]:
    return (
        record.host, record.policy, record.contribution, record.private_registration,
        record.public_registration, record.source_handle, record.epoch,
        record.execution_origin, record.read_prepare, record.read_spend, record.read_abort,
    )


def _step_identities(step: ProviderStepInvocation) -> tuple[object, ...]:
    """Keep every node of the existing selected-step identity guard alive."""
    if type(step) is not ProviderStepInvocation:
        raise ContractViolation("exact selected step required")
    inputs = object.__getattribute__(step, "inputs")
    if type(inputs) is not tuple:
        raise ContractViolation("exact selected input tuple required")
    nodes = [
        step, object.__getattribute__(step, "invocation"),
        object.__getattribute__(step, "step"),
        object.__getattribute__(step, "declaration"),
        object.__getattribute__(step, "binding"), inputs,
        object.__getattribute__(step, "predecessor"),
        object.__getattribute__(step, "dependencies"),
    ]
    for item in inputs:
        if type(item) is not BoundSemanticInput:
            raise ContractViolation("exact selected input required")
        admitted = object.__getattribute__(item, "admitted")
        if type(admitted) is not AdmittedSemanticValue:
            raise ContractViolation("exact admitted selected value required")
        nodes.extend((item, admitted, object.__getattribute__(admitted, "_coordinate")))
    return tuple(nodes)


def _check(read: _Read) -> None:
    """Code data only: no Workspace guard or semantic-owner call here."""
    if (
        read.pid != os.getpid()
        or current_thread() is not read.thread
        or not read.thread.is_alive()
        or stages._ROOTS.get(read.root) is not read.record
        or any(a is not b for a, b in zip(
            _root_identities(read.record), read.root_identities, strict=True
        ))
        or read.record.status != "private_admitted"
        or read.stage.child is not read.child_handle
        or stages._CHILDREN.get(read.stage.child) is not read.child
        or read.child.root is not read.root
        or read.child.operation_use is not read.operation_use
        or read.stage.semantic_input is not read.semantic_input
        or read.record.child is not read.stage.child
        or not read.child.spent
        or read.stage.status != "running"
        or stages._EXECUTIONS.get(read.context) is not read.stage
        or read.stage.selected_admission is not read.admission
        or stages._BINDINGS.get(read.record.host) is not read.record.epoch
        or stages.hosts._HOSTS.get(read.record.host) is not read.host_state
        or read.host_state.closed
    ):
        raise ContractViolation("original predecessor grant execution expired or changed")
    execution, registration, binding, body = selected._private_predecessor_execution_input(
        read.runtime, read.admission
    )
    if (
        execution is not read.execution
        or registration is not read.registration
        or execution.lifecycle_use is not read.stage
        or execution.semantic_input is not read.semantic_input
        or execution.closure.invocation.digest != read.stage.closure_digest
        or binding is not read.binding
        or body is not read.body
        or any(a is not b for a, b in zip(
            _step_identities(execution.step_invocation), read.step_identities, strict=True
        ))
    ):
        raise ContractViolation("original predecessor grant invocation changed")


def verify_and_spend_private_predecessor_grant(
    grant: PrivatePredecessorReadGrant,
    original_provider: object,
    claim_role: str,
    claim_body: bytes,
) -> None:
    """Called by the original registered port immediately before its read.

    Only declared input identity/bytes are checked. This function does not
    decode owner claim meaning, invoke an owner, or reacquire parent exclusion.
    """
    if type(grant) is not PrivatePredecessorReadGrant:
        raise TypeError("exact Code private predecessor grant required")
    read = _GRANTS.get(grant)
    if read is None:
        raise ContractViolation("private predecessor grant unavailable")
    try:
        # Process/thread checks precede the potentially inherited lock.
        _check(read)
        with _LOCK:
            if (
                read.status != "issued"
                or not read.port_active
                or verify_and_spend_private_predecessor_grant is not _ORIGINAL_VERIFIER
                or original_provider is not read.registration.provider
                or type(claim_role) is not str
                or claim_role != read.binding.role
                or type(claim_body) is not bytes
                or claim_body != read.body.canonical_body
            ):
                raise ContractViolation("private predecessor grant replay or input substitution")
            read.status = "spent"
    except BaseException:
        read.status = "failed"
        read.stage.read_phase = "failed"
        read.record.status = "failed"
        raise


_ORIGINAL_VERIFIER = verify_and_spend_private_predecessor_grant


def spend_private_predecessor_grant_for_invocation(
    use: selected.SelectedInvocationUse,
    grant: PrivatePredecessorReadGrant,
    provider: object,
    claim_role: str,
    claim_body: bytes,
) -> None:
    """Join exact original invocation attribution to the sole existing spend.

    No owner claim is decoded and no approval, owner handle or store is returned.
    """
    if type(grant) is not PrivatePredecessorReadGrant:
        raise TypeError("exact Code private predecessor grant required")
    read = _GRANTS.get(grant)
    if read is None:
        raise ContractViolation("private predecessor grant unavailable")
    try:
        if selected._require_observed_invocation is not _ORIGINAL_INVOCATION_VERIFIER:
            raise ContractViolation("original Code invocation verifier substituted")
        observed = _ORIGINAL_INVOCATION_VERIFIER(use, provider)
        if (
            observed.admission is not read.admission
            or observed.execution is not read.execution
            or observed.registration is not read.registration
            or observed.runtime is not read.runtime
            or observed.execution.semantic_input is not read.semantic_input
            or observed.execution.observed_use is not use
            or observed.phase != "associated"
            or not read.port_active
            or verify_and_spend_private_predecessor_grant is not _ORIGINAL_VERIFIER
        ):
            raise ContractViolation("private predecessor grant belongs to another invocation")
        _ORIGINAL_VERIFIER(grant, provider, claim_role, claim_body)
    except BaseException:
        read.status = "failed"
        read.stage.read_phase = "failed"
        read.record.status = "failed"
        raise


_ORIGINAL_INVOCATION_VERIFIER = selected._require_observed_invocation


def invoke_private_predecessor_port(
    child_use: stages.PrivateStageChildUse,
    semantic_input: object,
    original_selected_admission: selected.SelectedSemanticProviderExecutionAdmission,
) -> None:
    """Prepare/spend through the original host, then call its selected owner port.

    This is an execution-internal entrance: the caller cannot supply an issuer,
    preparation, claim, grant, callback or registration.
    """
    if type(child_use) is not stages.PrivateStageChildUse:
        raise TypeError("exact private child required")
    child = stages._CHILDREN.get(child_use)
    if child is None:
        raise ContractViolation("original running private child unavailable")
    record, _plan = stages._check_root(child.root)
    original_registration = selected._registration_state(
        cast(selected.AdmittedSemanticProviderRegistration, record.private_registration)
    )
    runtime = original_registration.runtime
    execution, registration, binding, body = selected._private_predecessor_execution_input(
        runtime, original_selected_admission
    )
    stage = execution.lifecycle_use
    if type(stage) is not stages._ExecutionState:
        raise ContractViolation("original private execution context required")
    if (
        registration is not original_registration
        or stage.child is not child_use
        or stage.semantic_input is not semantic_input
        or execution.semantic_input is not semantic_input
        or stage.selected_admission is not original_selected_admission
        or stage.read_phase != "pending"
    ):
        raise ContractViolation("private read belongs to another selected invocation")
    stages._running_stage(child.root, record, stage)
    contexts = tuple(key for key, value in stages._EXECUTIONS.items() if value is stage)
    if len(contexts) != 1:
        raise ContractViolation("unique original private context required")
    if record.read_prepare is None or record.read_spend is None or record.read_abort is None:
        raise ContractViolation("original private read issuer entrances unavailable")
    if record.execution_origin is None:
        raise ContractViolation("original private execution origin unavailable")
    read = _Read(
        child.root, record, child, stage, contexts[0], original_selected_admission,
        execution, registration, runtime, stages.hosts._state(record.host), binding,
        body, child_use, child.operation_use, semantic_input, _root_identities(record),
        _step_identities(execution.step_invocation), current_thread(), os.getpid(),
    )
    stage.read_phase = "preparing"  # One attempt even if preparation fails.
    grant = None
    try:
        _check(read)
        root, _record, full, locked = stages._execution_origin(record.execution_origin)
        if root is not child.root:
            raise ContractViolation("original private execution origin differs")
        stages._check_declared_input(record, child, stage, full)
        if record.read_prepare.call(child.operation_use, semantic_input) is not None:
            raise ContractViolation("original read preparation must return None")
        stages._check_root(child.root)
        _check(read)
        with stages._guard(record.epoch) as guard:
            stages.eligibility.check_selected_product_catalog_eligibility_locked(
                record.public_eligibility, guard=guard
            )
            if record.node_locked.call(child.operation_use) is not None:
                raise ContractViolation("locked graph-node validator returned a value")
            stages._check_declared_input(record, child, stage, locked)
            _check(read)
            if record.read_spend.call(child.operation_use, semantic_input, guard) is not None:
                raise ContractViolation("original read spend must return None")
            _check(read)
        # No grant exists until the original once-only spend succeeds and the
        # parent guard has been released. Only its original port sees the grant.
        _check(read)
        if verify_and_spend_private_predecessor_grant is not _ORIGINAL_VERIFIER:
            raise ContractViolation("original Code read verifier substituted")
        grant = object.__new__(PrivatePredecessorReadGrant)
        _GRANTS[grant] = read
        read.port_active = True
        stage.read_phase = "port"
        port = cast(Callable[[str, bytes, object], object], registration.private_stage_predecessor_port)
        result = port(
            binding.role, body.canonical_body, grant
        )
        read.port_active = False
        if result is not None or read.status != "spent":
            raise ContractViolation("original predecessor port must spend once and return None")
        _check(read)
        stage.read_phase = "complete"
        read.status = "completed"
    except BaseException:
        read.status = "failed"
        stage.read_phase = "failed"
        raise
    finally:
        read.port_active = False
        if grant is not None:
            _GRANTS.pop(grant, None)


__all__ = [
    "PrivatePredecessorReadGrant",
    "invoke_private_predecessor_port",
    "spend_private_predecessor_grant_for_invocation",
    "verify_and_spend_private_predecessor_grant",
]
