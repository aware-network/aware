"""Original authority predecessor retention before selected execution.

Workspace owns package-head currentness and the nominal admission.  This module
retains its exact reader and validator entrances without importing Workspace.
Portable predecessor evidence never grants execution authority by itself.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticBodyCodecBinding,
    SemanticContractInvocation,
    SemanticContractRef,
    SemanticValueCoordinate,
    TerminalStatus,
    TypedEmptyCoordinate,
    canonical_json_bytes,
    predecessor_wire,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SemanticDependencyProductInputCodec,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody


@dataclass(frozen=True, slots=True)
class AuthorityPredecessorEvidence:
    """Detached predecessor meaning; the retained nominal handle is authority."""

    disposition: str
    predecessor: TypedEmptyCoordinate | SemanticValueCoordinate
    predecessor_body: SemanticBody | None
    materialization_head_revision: int
    materialization_head_digest: ContentDigest | None

    def __post_init__(self) -> None:
        if self.disposition not in ("genesis", "current"):
            raise ContractViolation("authority predecessor disposition unsupported")
        if (
            type(self.materialization_head_revision) is not int
            or self.materialization_head_revision < 0
        ):
            raise ContractViolation("authority predecessor revision invalid")
        if self.disposition == "genesis":
            if (
                type(self.predecessor) is not TypedEmptyCoordinate
                or self.predecessor_body is not None
                or self.materialization_head_revision != 0
                or self.materialization_head_digest is not None
            ):
                raise ContractViolation("genesis predecessor evidence differs")
            self.predecessor.__post_init__()
            return
        if (
            type(self.predecessor) is not SemanticValueCoordinate
            or type(self.predecessor_body) is not SemanticBody
            or type(self.materialization_head_digest) is not ContentDigest
            or self.materialization_head_revision < 1
        ):
            raise ContractViolation("current predecessor evidence differs")
        self.predecessor.__post_init__()
        self.predecessor_body.__post_init__()
        self.materialization_head_digest.__post_init__()
        if self.predecessor_body.coordinate != self.predecessor:
            raise ContractViolation("predecessor body coordinate differs")


class RetainedAuthorityPredecessor:
    """Nominal Code retention of one original Workspace admission."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("authority predecessor handles are Code-issued")

    def __reduce__(self):
        raise TypeError("authority predecessor handles cannot be serialized")


@dataclass(frozen=True)
class _Entrance:
    receiver: object
    name: str
    descriptor: object
    method: Callable[..., Any]

    @classmethod
    def capture(cls, receiver: object, name: str) -> _Entrance:
        descriptor = inspect.getattr_static(receiver, name)
        method = getattr(receiver, name)
        if (
            not inspect.ismethod(method)
            or method.__self__ is not receiver
            or method.__func__ is not descriptor
        ):
            raise TypeError("original authority predecessor entrance required")
        return cls(receiver, name, descriptor, method)

    def check(self) -> None:
        if inspect.getattr_static(self.receiver, self.name) is not self.descriptor:
            raise ContractViolation("authority predecessor entrance substituted")
        current = getattr(self.receiver, self.name)
        if (
            not inspect.ismethod(current)
            or current.__self__ is not self.receiver
            or current.__func__ is not self.descriptor
        ):
            raise ContractViolation("authority predecessor entrance substituted")

    def call(self, *args, **kwargs):
        self.check()
        result = self.method(*args, **kwargs)
        self.check()
        return result


@dataclass(frozen=True)
class _Record:
    issuer: object
    admission: object
    authority_context: object
    authority_expected: RetainedSemanticAdmissionExpectation
    execution_identity: object
    result_contract: SemanticContractRef
    reader: _Entrance
    validator: _Entrance
    evidence: AuthorityPredecessorEvidence
    pid: int


_PREDECESSORS: WeakKeyDictionary = WeakKeyDictionary()


def _expected(
    authority_expected: RetainedSemanticAdmissionExpectation,
    execution_identity: object,
    result_contract: SemanticContractRef,
) -> None:
    if (
        type(authority_expected) is not RetainedSemanticAdmissionExpectation
        or authority_expected.stage != "authority_derivation"
    ):
        raise TypeError("exact authority-stage expectation required")
    if execution_identity is None:
        raise ContractViolation("fresh authority execution identity required")
    if type(result_contract) is not SemanticContractRef:
        raise TypeError("exact authority result contract required")
    result_contract.__post_init__()


def _normalize(value: Any, result_contract: SemanticContractRef):
    try:
        evidence = AuthorityPredecessorEvidence(
            disposition=value.disposition,
            predecessor=deepcopy(value.predecessor),
            predecessor_body=deepcopy(value.predecessor_body),
            materialization_head_revision=value.materialization_head_revision,
            materialization_head_digest=deepcopy(value.materialization_head_digest),
        )
    except (AttributeError, TypeError, ValueError) as error:
        raise ContractViolation("authority predecessor evidence malformed") from error
    if evidence.predecessor.contract != result_contract:
        raise ContractViolation("authority predecessor result contract differs")
    return evidence


def _arguments(record: _Record) -> dict[str, object]:
    return {
        "authority_context": record.authority_context,
        "authority_expected": record.authority_expected,
        "execution_identity": record.execution_identity,
        "result_contract": record.result_contract,
    }


def _validate(record: _Record) -> AuthorityPredecessorEvidence:
    if record.pid != os.getpid():
        raise ContractViolation("foreign authority predecessor process")
    record.reader.check()
    record.validator.check()
    kwargs = _arguments(record)
    if record.validator.call(record.admission, **kwargs) is not None:
        raise ContractViolation("authority predecessor validator returned a value")
    evidence = _normalize(
        record.reader.call(record.admission, **kwargs), record.result_contract
    )
    if evidence != record.evidence:
        raise ContractViolation("authority predecessor evidence changed")
    if record.validator.call(record.admission, **kwargs) is not None:
        raise ContractViolation("authority predecessor validator returned a value")
    return evidence


def retain_authority_predecessor(
    issuer: object,
    admission: object,
    *,
    authority_context: object,
    authority_expected: RetainedSemanticAdmissionExpectation,
    execution_identity: object,
    result_contract: SemanticContractRef,
) -> RetainedAuthorityPredecessor:
    """Retain one original Workspace admission; fixed composition supplies issuer."""

    _expected(authority_expected, execution_identity, result_contract)
    reader = _Entrance.capture(issuer, "read_authority_predecessor")
    validator = _Entrance.capture(issuer, "validate_authority_predecessor_admission")
    provisional = _Record(
        issuer,
        admission,
        authority_context,
        authority_expected,
        execution_identity,
        deepcopy(result_contract),
        reader,
        validator,
        _normalize(
            reader.call(
                admission,
                authority_context=authority_context,
                authority_expected=authority_expected,
                execution_identity=execution_identity,
                result_contract=result_contract,
            ),
            result_contract,
        ),
        os.getpid(),
    )
    _validate(provisional)
    handle = object.__new__(RetainedAuthorityPredecessor)
    _PREDECESSORS[handle] = provisional
    return handle


def read_retained_authority_predecessor(
    handle: RetainedAuthorityPredecessor,
) -> AuthorityPredecessorEvidence:
    if type(handle) is not RetainedAuthorityPredecessor:
        raise TypeError("exact retained authority predecessor required")
    record = _PREDECESSORS.get(handle)
    if record is None:
        raise ContractViolation("foreign retained authority predecessor")
    return deepcopy(_validate(record))


@dataclass
class _ExecutionStage:
    context: object
    context_record: Any
    predecessor: RetainedAuthorityPredecessor
    predecessor_evidence: AuthorityPredecessorEvidence
    closure: selected.SelectedProviderInvocationClosure
    execution_identity: object
    status: str = "prepared"
    completion: object = None
    completion_snapshot: object = None


class _AuthorityExecutionOrigin:
    """Original Code lifecycle bound to one authority registration."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("authority execution origin is sealed")

    def adopt(self, context):
        contexts, hooks, epochs = _runtime_modules()
        host, registration, stages = _execution_origin(self)
        prepared = _PREPARED.get(context)
        record = contexts._CONTEXTS.get(context)
        if (
            prepared is None
            or record is None
            or prepared.context_record is not record
            or record.host is not host
            or record.registration is not registration
            or prepared.status != "prepared"
        ):
            raise ContractViolation("original prepared authority operation required")
        contexts._validate(record, read_products=True, rederive=True)
        evidence = read_retained_authority_predecessor(prepared.predecessor)
        if evidence != prepared.predecessor_evidence:
            raise ContractViolation("authority predecessor changed before adoption")
        binding = record.demand.binding
        with hooks._guard(binding) as guard:
            contexts._identity(record, guard)
            tracker = epochs._state(binding.participant)
            with tracker.lock:
                use = tracker.uses.get(record.use)
                if use is None or use.status != "pending":
                    raise ContractViolation("authority reservation unavailable")
            binding.participant._start_epoch_use(guard, record.use)
            prepared.status = "running"
            stages[context] = prepared
        return prepared

    def validate(self, stage, closure):
        host, registration, stages = _execution_origin(self)
        _validate_execution_stage(
            host,
            registration,
            stages,
            stage,
            validate_context=True,
        )
        if (
            type(closure) is not selected.SelectedProviderInvocationClosure
            or closure != stage.closure
        ):
            raise ContractViolation("selected authority closure differs")
        closure.__post_init__()

    def complete(self, stage, completion):
        contexts, hooks, _epochs = _runtime_modules()
        host, registration, stages = _execution_origin(self)
        _validate_execution_stage(host, registration, stages, stage)
        record = stage.context_record
        runtime = record.expected.runtime
        if not runtime.owns_completion(completion):
            raise ContractViolation("original authority runtime completion required")
        snapshot = runtime.snapshot_completion(completion)
        result = snapshot.result
        predecessor = stage.predecessor_evidence.predecessor
        if (
            snapshot.invocation_digest != stage.closure.invocation.digest
            or snapshot.profile_digest != record.expected.profile.digest
            or result.status not in (TerminalStatus.CURRENT, TerminalStatus.DELTA)
        ):
            raise ContractViolation("authority completion invocation/profile differs")
        if result.status is TerminalStatus.CURRENT:
            if (
                stage.predecessor_evidence.disposition != "current"
                or result.current_result != predecessor
                or result.transition is not None
            ):
                raise ContractViolation("CURRENT authority completion differs")
        elif (
            result.transition is None
            or result.transition.predecessor != predecessor
            or result.transition.result.contract
            != record.expected.provider_declaration.result_role.contract
        ):
            raise ContractViolation("DELTA authority completion differs")
        contexts._validate(record, read_products=True, rederive=True)
        if (
            read_retained_authority_predecessor(stage.predecessor)
            != stage.predecessor_evidence
        ):
            raise ContractViolation("authority predecessor changed after execution")
        with hooks._guard(record.demand.binding) as guard:
            contexts._identity(record, guard)
            if stages.get(stage.context) is not stage or stage.status != "running":
                raise ContractViolation("authority stage changed before retention")
            if not runtime.owns_completion(completion):
                raise ContractViolation("authority completion revoked before retention")
            stage.completion = completion
            stage.completion_snapshot = snapshot
            stage.status = "completed"

    def fail(self, stage):
        _contexts, hooks, _epochs = _runtime_modules()
        _host, _registration, stages = _execution_origin(self)
        if type(stage) is not _ExecutionStage or stages.get(stage.context) is not stage:
            raise ContractViolation("foreign authority execution stage")
        record = stage.context_record
        with hooks._guard(record.demand.binding) as guard:
            if stage.status == "uncertain":
                return
            record.demand.binding.participant._mark_epoch_use_uncertain(
                guard, record.use
            )
            stage.status = "uncertain"


_EXECUTION_ORIGINS: WeakKeyDictionary = WeakKeyDictionary()
_PREPARED: WeakKeyDictionary = WeakKeyDictionary()


def _runtime_modules():
    from . import authority_operation_context as contexts
    from . import direct_epoch_tracking as hooks
    from . import epoch_participation as epochs

    return contexts, hooks, epochs


def _execution_origin(origin):
    if type(origin) is not _AuthorityExecutionOrigin:
        raise TypeError("exact authority execution origin required")
    value = _EXECUTION_ORIGINS.get(origin)
    if value is None or value[3] != os.getpid():
        raise ContractViolation("foreign authority execution origin/process")
    return value[:3]


def _validate_execution_stage(
    host, registration, stages, stage, *, validate_context=True
):
    contexts, hooks, epochs = _runtime_modules()
    if type(stage) is not _ExecutionStage or stages.get(stage.context) is not stage:
        raise ContractViolation("foreign authority execution stage")
    record = contexts._CONTEXTS.get(stage.context)
    if (
        record is not stage.context_record
        or record.host is not host
        or record.registration is not registration
        or stage.status != "running"
    ):
        raise ContractViolation("authority execution stage unavailable")
    if validate_context:
        contexts._validate(record)
        if (
            read_retained_authority_predecessor(stage.predecessor)
            != stage.predecessor_evidence
        ):
            raise ContractViolation("authority predecessor changed during execution")
    binding = record.demand.binding
    with hooks._guard(binding) as guard:
        contexts._identity(record, guard)
        tracker = epochs._state(binding.participant)
        with tracker.lock:
            use = tracker.uses.get(record.use)
            if use is None or use.status != "running":
                raise ContractViolation("original running authority use unavailable")


def bind_authority_execution_origin(host, registration):
    """Bind the exact authority registration before any selected execution."""

    contexts, hooks, _epochs = _runtime_modules()
    state = contexts.hosts._state(host)
    registration_state = selected._registration_state(registration)
    if state.stage_retention is None:
        raise ContractViolation("original authority stage retention required")
    matches = [
        (runtime, original)
        for name, runtime, original in state.stage_retention.stages
        if name == "authority_derivation"
    ]
    if not any(
        runtime is registration_state.runtime and original is registration
        for runtime, original in matches
    ) or sum(original is registration for _, original in matches) != 1:
        raise ContractViolation("original authority registration required")
    origin = object.__new__(_AuthorityExecutionOrigin)
    binding = hooks._BINDINGS.get(host)
    if binding is None:
        raise ContractViolation("original epoch host required")
    with hooks._guard(binding) as guard:
        hooks._original(binding, host, guard)
        _EXECUTION_ORIGINS[origin] = (host, registration, {}, os.getpid())
        try:
            selected._bind_selected_execution_lifecycle(
                registration_state.runtime,
                registration,
                origin,
                terminal_mode="runtime_completion",
            )
        except BaseException:
            _EXECUTION_ORIGINS.pop(origin, None)
            raise
    return origin


def _requested_output_roles(context_record):
    runtime = context_record.expected.runtime
    intent = context_record.demand.context.code_intent
    intent.__post_init__()
    roles = intent.requested_terminal_output_roles
    declared_roles = runtime.profile.terminal_output_roles
    result_role = runtime.profile.terminal_result_role
    if any(role not in declared_roles and role != result_role for role in roles):
        raise ContractViolation("authority intent requests undeclared terminal output")
    required = context_record.demand.context.required_result_products
    if tuple(item.role for item in required) != roles:
        raise ContractViolation("authority intent/result roles differ")
    output_contracts = {
        role.role: role.contract for provider in runtime.profile.providers
        for role in (*provider.output_roles, provider.result_role)
    }
    if any(output_contracts.get(item.role) != item.contract for item in required):
        raise ContractViolation("authority result contract differs from profile")
    # The terminal result is emitted by the provider protocol itself; only
    # supplementary output roles belong in the invocation's output request.
    return tuple(role for role in roles if role != result_role)


def _authority_input_bodies(profile, request_bodies, planning_body, owner_outputs, product_body):
    profile_inputs = {item.role: item.contract for item in profile.inputs}
    owner_inputs = tuple(
        body for body in owner_outputs if body.coordinate.role in profile_inputs
    )
    bodies = tuple(
        sorted(
            (*request_bodies, planning_body, *owner_inputs, product_body),
            key=lambda body: body.coordinate.role,
        )
    )
    roles = tuple(body.coordinate.role for body in bodies)
    if (
        len(set(roles)) != len(roles)
        or set(roles) != set(profile_inputs)
        or any(
            body.coordinate.contract != profile_inputs[body.coordinate.role]
            for body in bodies
        )
    ):
        raise ContractViolation("original authority input closure incomplete")
    return bodies


def _invocation(context_record, evidence, bodies):
    expected = context_record.expected
    runtime = expected.runtime
    roles = _requested_output_roles(context_record)
    products = SemanticDependencyProductInputCodec().decode(
        next(
            body.canonical_body
            for body in bodies
            if body.coordinate.role == "semantic_dependencies"
        )
    )
    dependencies = tuple(
        sorted(
            {item.coordinate for item in products.products},
            key=lambda item: canonical_json_bytes(item.to_wire()),
        )
    )
    codecs = tuple(
        SemanticBodyCodecBinding(contract, implementation)
        for contract, implementation in sorted(
            runtime._codec_implementations.items(),
            key=lambda item: canonical_json_bytes(item[0].to_wire()),
        )
    )
    identity = ContentDigest.of_bytes(
        canonical_json_bytes(
            {
                "inputs": [body.coordinate.to_wire() for body in bodies],
                "predecessor": predecessor_wire(evidence.predecessor),
                "profile": expected.profile.digest.to_wire(),
            }
        )
    ).value.removeprefix("sha256:")
    return SemanticContractInvocation(
        invocation_ref=f"authority-{identity}",
        idempotency_key=f"authority-{identity}",
        profile_ref=expected.profile.profile_ref,
        profile_digest=expected.profile.digest,
        target_package=expected.package,
        operation_kind="materialize",
        inputs=tuple(body.coordinate for body in bodies),
        predecessor=evidence.predecessor,
        dependencies=dependencies,
        body_codec_bindings=codecs,
        provider_bindings=(expected.binding,),
        requested_output_roles=roles,
    )


def prepare_authority_execution(
    context,
    predecessor: RetainedAuthorityPredecessor,
) -> selected.SelectedProviderInvocationClosure:
    """Assemble one exact closure from original retained Code/Workspace lineage."""

    contexts, hooks, _epochs = _runtime_modules()
    record = contexts._CONTEXTS.get(context)
    if record is None:
        raise ContractViolation("original authority context required")
    contexts._validate(record)
    evidence = read_retained_authority_predecessor(predecessor)
    predecessor_record = _PREDECESSORS.get(predecessor)
    if (
        predecessor_record is None
        or predecessor_record.authority_context is not context
    ):
        raise ContractViolation("authority predecessor belongs to another context")
    contexts._same_expected(predecessor_record.authority_expected, record.expected)
    from .operation_derivation import _bodies
    from .planning_completion import retained_planning_output_body

    planning_body = record.stage.result_body
    product_body = SemanticBody(
        deepcopy(record.product_coordinate), record.product_wire
    )
    lifecycle = selected._registration_state(
        record.stage.record.registration
    ).execution_lifecycle
    if lifecycle is None or record.completion_snapshot is None:
        raise ContractViolation("original planning completion outputs required")
    owner_outputs = tuple(
        retained_planning_output_body(
            lifecycle.origin, record.stage.context, output.output
        )
        for output in record.completion_snapshot.result.outputs
    )
    bodies = _authority_input_bodies(
        record.expected.profile,
        _bodies(record.request),
        planning_body,
        owner_outputs,
        product_body,
    )
    closure = selected.SelectedProviderInvocationClosure(
        _invocation(record, evidence, bodies),
        bodies,
        predecessor_body=evidence.predecessor_body,
    )
    stage = _ExecutionStage(
        context,
        record,
        predecessor,
        evidence,
        closure,
        predecessor_record.execution_identity,
    )
    with hooks._guard(record.demand.binding) as guard:
        contexts._identity(record, guard)
        if context in _PREPARED:
            raise ContractViolation("authority execution preparation replay")
        _PREPARED[context] = stage
    return closure


def read_authority_completion(context):
    """Return the original runtime-owned completion after selected execution."""

    contexts, hooks, _epochs = _runtime_modules()
    stage = _PREPARED.get(context)
    record = contexts._CONTEXTS.get(context)
    if (
        stage is None
        or record is not stage.context_record
        or stage.status != "completed"
        or not record.expected.runtime.owns_completion(stage.completion)
        or record.expected.runtime.snapshot_completion(stage.completion)
        != stage.completion_snapshot
    ):
        raise ContractViolation("original authority completion unavailable")
    contexts._validate(record)
    if (
        read_retained_authority_predecessor(stage.predecessor)
        != stage.predecessor_evidence
    ):
        raise ContractViolation("authority predecessor changed after completion")
    with hooks._guard(record.demand.binding) as guard:
        contexts._identity(record, guard)
        if _PREPARED.get(context) is not stage:
            raise ContractViolation("authority completion association changed")
    return stage.completion
