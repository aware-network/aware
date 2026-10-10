"""Code registry and three-admission source join over original host resources.

No Workspace imports or issuers. This source join is not selected execution
admission, dependency-product authority, or installed application qualification.
"""

import inspect
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from weakref import WeakKeyDictionary, ref

from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    RegistryPackageInputCodec,
)

from . import authority_operation_context as authority
from . import direct_host as direct
from . import operation_context as contexts


class CodeRegistryPackageAdmission(direct._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("registry admission is sealed")


class AdmittedRetainedSemanticInputs(direct._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("retained input join is sealed")


@dataclass
class _OriginState:
    host: object
    issuer: object
    methods: dict
    resources: tuple
    pid: int
    registries: WeakKeyDictionary = field(default_factory=WeakKeyDictionary)
    joins: WeakKeyDictionary = field(default_factory=WeakKeyDictionary)
    issued: set = field(default_factory=set)
    joined: set = field(default_factory=set)
    by_context: dict = field(default_factory=dict)
    consumed: dict = field(default_factory=dict)

    def check(self):
        if self.pid != os.getpid():
            raise ContractViolation("retained admission process changed")
        host_state = direct._state(self.host)
        for method in self.methods.values():
            method.check()
        for name, resource, descriptor in self.resources:
            if (
                inspect.getattr_static(self.issuer, name) is not descriptor
                or getattr(self.issuer, name) is not resource
            ):
                raise ContractViolation("original issuer resource substituted")
        return host_state


_ORIGINS = WeakKeyDictionary()
_INSTALLED = WeakKeyDictionary()


def _state(origin):
    if type(origin) is not RetainedInputAdmissionOrigin:
        raise TypeError("exact retained admission origin required")
    state = _ORIGINS.get(origin)
    if state is None:
        raise ContractViolation("foreign retained admission origin")
    for name, method in _METHODS.items():
        if inspect.getattr_static(origin, name) is not method:
            raise ContractViolation("original Code admission method substituted")
    state.check()
    return state


@contextmanager
def _publication(state):
    host_state = state.check()
    methods = host_state.methods
    methods["acquire"].check()
    guard = methods["acquire"].method(host_state.lifetime, expected=host_state.expected)
    try:
        methods["acquire"].check()
        methods["guard"].call(
            guard, lifetime=host_state.lifetime, expected=host_state.expected
        )
        state.check()
        yield
    finally:
        methods["release"].method(guard)
        methods["release"].check()


def _context_record(context):
    """Exact nominal stage dispatch; expected values never select a stage."""
    if type(context) is contexts.SourcePlanningOperationContext:
        return contexts._CONTEXTS.get(context)
    if type(context) is authority.AuthorityOperationContext:
        return authority._CONTEXTS.get(context)
    raise TypeError("exact original planning or authority context required")


def _expectation(host, context):
    record = _context_record(context)
    if record is None or record.host is not host:
        raise ContractViolation("original semantic context unavailable")
    if type(context) is contexts.SourcePlanningOperationContext:
        return contexts.source_planning_expectation(host, context)
    return authority.authority_operation_expectation(host, context)


@contextmanager
def _owner_context_window(context):
    """Keep owner callbacks inside one Code before/after validation boundary.

    Workspace validators intentionally call the original Code validator while
    checking their own evidence.  Once Code has completed the outer validation,
    those synchronous callbacks need nominal lineage checks, not another full
    source derivation.  The caller always performs a fresh full validation after
    the owner entrance returns.
    """
    if type(context) is contexts.SourcePlanningOperationContext:
        active = contexts._ACTIVE_CONTEXT_VALIDATIONS.get()
        if context in active:
            yield
            return
        token = contexts._ACTIVE_CONTEXT_VALIDATIONS.set(active + (context,))
        try:
            yield
        finally:
            contexts._ACTIVE_CONTEXT_VALIDATIONS.reset(token)
        return
    if type(context) is authority.AuthorityOperationContext:
        record = authority._CONTEXTS.get(context)
        if record is None:
            raise ContractViolation("original authority context unavailable")
        active = authority._ACTIVE_VALIDATIONS.get()
        if any(value[0] is record for value in active):
            yield
            return
        token = authority._ACTIVE_VALIDATIONS.set(
            active + ((record, False, False),)
        )
        try:
            yield
        finally:
            authority._ACTIVE_VALIDATIONS.reset(token)
        return
    raise TypeError("exact original planning or authority context required")


def _validate_package(state, context, package, *, postvalidate=True):
    contexts._performance_count("code.registry_package_validation")
    with contexts._performance_phase("code.registry_package_expected_context"):
        expected = _expectation(state.host, context)
    record = _context_record(context)
    if record is None or record.host is not state.host:
        raise ContractViolation("original planning context unavailable")
    with contexts._performance_phase("code.registry_package_body_decode"):
        retained = (
            record.retained
            if type(context) is contexts.SourcePlanningOperationContext
            else record.request
        )
        registry = RegistryPackageInputCodec().decode(
            retained.registry_package.canonical_body
        )
    # The original assignment entrance validates this exact package-context
    # handle before comparing namespace and complete roots (owning invariant).
    # Retain Code's independent context checks on both sides of that owner call.
    with (
        contexts._performance_phase("code.registry_package_workspace_assignment"),
        _owner_context_window(context),
    ):
        if (
            state.methods["assignments"].call(
                package,
                expected=expected,
                namespace=registry.fqn_prefix,
                owned_roots=registry.owned_semantic_root_refs,
            )
            is not None
        ):
            raise ContractViolation("original Workspace validator returned non-None")
    # Workspace checks assignment evidence; Code's original context rederivation
    # independently checks selected registration and policy namespace entitlement.
    if postvalidate:
        with contexts._performance_phase("code.registry_package_post_expectation"):
            contexts._equal(expected, _expectation(state.host, context))
    with contexts._performance_phase("code.registry_package_origin_check"):
        state.check()
    return record, expected


def _validated_registry(state, admission, *, expected=None, postvalidate=True):
    if type(admission) is not CodeRegistryPackageAdmission:
        raise TypeError("exact registry admission required")
    retained = state.registries.get(admission)
    if retained is None:
        raise ContractViolation("foreign registry admission")
    context, package, record = retained
    if expected is not None:
        contexts._equal(expected, record.expected)
    current, observed = _validate_package(
        state, context, package, postvalidate=postvalidate
    )
    if current is not record or state.registries.get(admission) is not retained:
        raise ContractViolation("original registry context changed")
    return observed


class RetainedInputAdmissionOrigin(direct._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("retained admission origin is sealed")

    def issue_registry_package_admission(self, context, package_admission):
        contexts._performance_count("code.registry_package_issue")
        state = _state(self)
        record, _ = _validate_package(state, context, package_admission)
        admission = object.__new__(CodeRegistryPackageAdmission)
        try:
            with _publication(state), direct._LOCK:
                if (
                    context in state.issued
                    or len(state.issued) >= 128
                    or _context_record(context) is not record
                ):
                    raise ContractViolation(
                        "registry issuance replay, capacity or revoked context"
                    )
                state.issued.add(context)
                state.registries[admission] = (context, package_admission, record)
        except BaseException:
            state.registries.pop(admission, None)
            raise
        return admission

    def validate_registry_package_admission(self, admission, *, expected):
        contexts._performance_count("code.registry_package_validation")
        if type(expected) is not RetainedSemanticAdmissionExpectation:
            raise TypeError("exact retained semantic expectation required")
        state = _state(self)
        _validated_registry(state, admission, expected=expected)

    def join(self, context, registry_admission, package_admission, inventory_admission):
        contexts._performance_count("code.three_admission_join")
        state = _state(self)
        with _owner_context_window(context):
            expected = _validated_registry(
                state, registry_admission, postvalidate=False
            )
            record = state.registries[registry_admission]
            if record[0] is not context or record[1] is not package_admission:
                raise ContractViolation("three-admission context/package substitution")
            if (
                state.methods["inventory"].call(
                    inventory_admission, expected=expected
                )
                is not None
            ):
                raise ContractViolation("original inventory validator returned non-None")
        contexts._equal(expected, _expectation(state.host, context))
        result = object.__new__(AdmittedRetainedSemanticInputs)
        try:
            with _publication(state), direct._LOCK:
                if context in state.joined or _context_record(context) is not record[2]:
                    raise ContractViolation("retained join replay or context revoked")
                state.joined.add(context)
                state.by_context[context] = result
                state.joins[result] = (
                    context,
                    registry_admission,
                    package_admission,
                    inventory_admission,
                )
        except BaseException:
            if state.by_context.get(context) is result:
                state.by_context.pop(context, None)
            state.joins.pop(result, None)
            raise
        return result

    def validate(self, admission):
        contexts._performance_count("code.join_validation")
        state = _state(self)
        if type(admission) is not AdmittedRetainedSemanticInputs:
            raise TypeError("exact retained input admission required")
        joined = state.joins.get(admission)
        if joined is None:
            raise ContractViolation("foreign retained input admission")
        context, registry, package, inventory = joined
        with _owner_context_window(context):
            expected = _validated_registry(state, registry, postvalidate=False)
            if (
                state.registries[registry][0] is not context
                or state.registries[registry][1] is not package
            ):
                raise ContractViolation("original joined handles changed")
            if state.methods["inventory"].call(inventory, expected=expected) is not None:
                raise ContractViolation("original inventory validator returned non-None")
        contexts._equal(expected, _expectation(state.host, context))
        state.check()


_METHODS = {
    name: inspect.getattr_static(RetainedInputAdmissionOrigin, name)
    for name in (
        "issue_registry_package_admission",
        "validate_registry_package_admission",
        "join",
        "validate",
    )
}


def assemble_retained_input_admission_origin(host):
    """Fixed Code composition: resolve only resources retained in original host."""
    host_state = direct._state(host)
    resources = {r.role: r.resource for r in host_state.expected.resources}
    if host_state.source_rail == "declaration_v3":
        # The same original Workspace issuer already retained by the host must
        # issue package/context and inventory admissions for its selected
        # package. A legacy whole-root semantic issuer is unavailable here.
        issuer = resources["declaration_scope_runtime"]
        if (
            host_state.methods["read"].receiver is not issuer
            or host_state.methods["selected_read"].receiver is not issuer
        ):
            raise ContractViolation("original declaration issuer differs")
        bound_resources = ()
    else:
        issuer = resources["semantic_issuer"]
        bound_resources = tuple(
            (name, resources[name], inspect.getattr_static(issuer, name))
            for name in ("observation_runtime", "membership_runtime")
        )
    try:
        methods = {
            key: direct._capture(issuer, name)
            for key, name in (
                ("package", "validate_package_context_admission"),
                ("inventory", "validate_declaration_inventory_admission"),
                ("assignments", "validate_occurrence_assignments"),
            )
        }
    except AttributeError as exc:
        raise ContractViolation("original semantic issuer entrance unavailable") from exc
    state = _OriginState(host, issuer, methods, bound_resources, os.getpid())
    state.check()
    origin = object.__new__(RetainedInputAdmissionOrigin)
    with _publication(state), direct._LOCK:
        if host in _INSTALLED:
            raise ContractViolation("retained admission origin replay")
        _INSTALLED[host] = ref(origin)
        _ORIGINS[origin] = state
    return origin


def _consume_for_planning(host, context, stage):
    """Original planning adoption only; no caller-selected origin or validator."""
    origin = _INSTALLED.get(host, lambda: None)()
    state = _state(origin)
    admission = state.by_context.get(context)
    if admission is None:
        raise ContractViolation("original three-admission join required")
    origin.validate(admission)
    with _publication(state), direct._LOCK:
        if (
            context in state.consumed
            or state.by_context.get(context) is not admission
            or contexts._CONTEXTS.get(context) is not stage.record
            or stage.context is not context
            or stage.status != "adopting"
        ):
            raise ContractViolation("source join consumption replay or substitution")
        state.consumed[context] = (admission, ref(stage))
    return origin, admission


def _validate_consumption_identity(origin, admission, context, stage):
    """No source callbacks: safe inside original epoch exclusion."""
    state = _state(origin)
    value = state.consumed.get(context)
    if (
        value is None
        or value[0] is not admission
        or value[1]() is not stage
        or state.by_context.get(context) is not admission
        or state.joins.get(admission, (None,))[0] is not context
    ):
        raise ContractViolation("original consumed source join unavailable")
