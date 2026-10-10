"""Original demand invocation evidence; not dependency fulfillment or completion.

Requires the coordinated explicit-input dispatch. This isolated implementation
must migrate with that dispatch and its owner callers, never as a fallback rail.
"""

from __future__ import annotations

import inspect
import os
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    AdmittedCodeSemanticContractCatalog,
    CodeSemanticContractCatalogResolver,
    CodeSemanticContractMatch,
    CodeSemanticContractMatchAdmission,
    CodeSemanticPackagePlanningContext,
    _admitted_catalog_state,
    _original_planner_entrance,
)
from aware_code_semantic_contract_runtime.materialization_catalog_codec import (
    encode_code_semantic_contract_match,
    encode_code_semantic_contract_match_admission,
    encode_code_semantic_package_planning_context,
)
from aware_code_semantic_contract_runtime.materialization_planning_codec import (
    decode_semantic_dependency_demand_set,
    encode_semantic_dependency_demand_set,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DependencyPlanningInputCodec,
    RegistryPackageInputCodec,
)

from . import direct_epoch_tracking as hooks
from . import direct_host as hosts
from . import operation_context as contexts
from . import planning_dependency_source as sources
from . import planning_execution as execution


class RetainedDependencyDemandOperation(hosts._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("retained demand operation is sealed")

    def read_demand(self):
        record = _record(self)
        record.validate()
        if record.status != "returned":
            raise ContractViolation("accepted original demand unavailable")
        value = decode_semantic_dependency_demand_set(
            record.result_bytes, **record.demand_context()
        )
        with hooks._guard(record.binding) as guard:
            record.check_locked(guard)
            if record.status != "returned":
                raise ContractViolation("demand changed during read")
        return value


@dataclass
class _Demand:
    source: sources.RetainedPlanningDependencySource
    source_record: tuple
    planning_input_coordinate: SemanticValueCoordinate
    planning_input_bytes: bytes
    source_reader: hosts._Entrance
    host: hosts.DirectValidationHost
    stage: execution._Stage
    binding: hooks._Binding
    catalog: AdmittedCodeSemanticContractCatalog
    resolver: CodeSemanticContractCatalogResolver
    dispatch: hosts._Entrance
    context: CodeSemanticPackagePlanningContext
    context_bytes: bytes
    match: CodeSemanticContractMatch
    match_bytes: bytes
    match_admission: CodeSemanticContractMatchAdmission
    match_admission_bytes: bytes
    planner: object
    planner_entrance: hosts._Entrance
    pid: int
    replay_token: object
    status: str = "reserved"
    result_bytes: bytes | None = None

    def demand_context(self):
        b = self.match.selected_binding
        return {
            "package": self.context.package,
            "intent": self.context.code_intent,
            "profile_ref": b.profile_declaration.profile_ref,
            "profile_digest": b.profile_declaration.digest,
            "contract_profile_binding_digest": b.binding_digest,
            "planner_implementation_ref": b.dependency_planner_implementation.implementation_ref,
            "planner_implementation_digest": b.dependency_planner_implementation.closure_digest,
            "planner_configuration": b.dependency_planner_configuration,
        }

    def check_locked(self, guard):
        if self.pid != os.getpid():
            raise ContractViolation("foreign demand process")
        hooks._original(self.binding, self.host, guard)
        if (
            _BY_CONTEXT.get(self.stage.context) is not self.replay_token
            or sources._SOURCES.get(self.source) is not self.source_record
            or self.stage.status != "returned"
            or self.stage.result_body is not self.source_record[3]
        ):
            raise ContractViolation("original demand lineage unavailable")
        execution._validate_consumed_context(
            self.host, self.stage.context, self.stage.record.reservation
        )
        self.source_reader.check()
        self.dispatch.check()
        self.planner_entrance.check()

    def validate(self):
        contexts._performance_count("code.demand_validation")
        if self in _ACTIVE_VALIDATIONS.get():
            contexts._performance_count("code.demand_validation_nominal")
            self.source_reader.check()
            self.dispatch.check()
            self.planner_entrance.check()
            with hooks._guard(self.binding) as guard:
                self.check_locked(guard)
            return DependencyPlanningInputCodec().decode(self.planning_input_bytes)
        contexts._performance_count("code.demand_validation_complete")
        if (
            inspect.getattr_static(self.source, "read_dependencies")
            is not sources._READ
        ):
            raise ContractViolation("original source reader substituted")
        self.source_reader.check()
        value = self.source_reader.call(self.stage.record.expected.package)
        if (
            DependencyPlanningInputCodec().encode(value) != self.planning_input_bytes
            or self.source_record[3].coordinate != self.planning_input_coordinate
            or self.source_record[3].canonical_body != self.planning_input_bytes
            or encode_code_semantic_package_planning_context(self.context)
            != self.context_bytes
            or encode_code_semantic_contract_match(
                self.match, context=self.context, resolver=self.resolver
            )
            != self.match_bytes
            or encode_code_semantic_contract_match_admission(
                self.match_admission, context=self.context, resolver=self.resolver
            )
            != self.match_admission_bytes
        ):
            raise ContractViolation("original demand input or context changed")
        state = _admitted_catalog_state(self.catalog)
        if (
            state.dependency_planners.get(self.match.selected_entry_digest)
            is not self.planner
            or self.resolver._admission is not self.catalog
            or self.resolver._dependency_planners.get(self.match.selected_entry_digest)
            is not self.planner
        ):
            raise ContractViolation("original demand planner/catalog changed")
        self.planner_entrance.check()
        _original_planner_entrance(state, self.match.selected_entry_digest)
        if self.resolver.resolve(self.context)[0] != self.match:
            raise ContractViolation("original demand catalog match changed")
        with hooks._guard(self.binding) as guard:
            self.check_locked(guard)
        return value


_OPERATIONS = WeakKeyDictionary()
# Values never point back to the weak context key. Keep only a replay tombstone;
# live result handles retain operation evidence, not this replay ledger.
_BY_CONTEXT = WeakKeyDictionary()
_ACTIVE_VALIDATIONS: ContextVar[tuple[_Demand, ...]] = ContextVar(
    "aware_code_active_demand_validations", default=()
)
_READ = RetainedDependencyDemandOperation.read_demand


@contextmanager
def _synchronous_validation_window(record):
    """One complete check on each side of synchronous owner validation.

    The caller establishes the first complete validation before entering. Nested
    original Code callbacks retain nominal lineage and epoch checks. Exiting the
    interval always performs the matching complete validation.
    """

    active = _ACTIVE_VALIDATIONS.get()
    if record in active:
        yield
        return
    token = _ACTIVE_VALIDATIONS.set(active + (record,))
    try:
        yield
    finally:
        _ACTIVE_VALIDATIONS.reset(token)
        record.validate()


@contextmanager
def dependency_resolution_validation_session(operation):
    """Retain exact Code evidence across one synchronous owner resolution.

    The original demand record supplies the host and source context.  Callers
    cannot nominate either value, and the yielded interval carries no portable
    or reusable authority.
    """

    record = _record(operation)
    source_context = record.source_record[1]
    with contexts._synchronous_validation_window(record.host, source_context):
        # Source currentness is already complete on entry. Demand validation
        # retains nominal source callbacks while independently proving the
        # complete demand before and after the synchronous owner operation.
        record.validate()
        with _synchronous_validation_window(record):
            yield


def _record(handle):
    if type(handle) is not RetainedDependencyDemandOperation:
        raise TypeError("exact retained demand operation required")
    record = _OPERATIONS.get(handle)
    if record is None or inspect.getattr_static(handle, "read_demand") is not _READ:
        raise ContractViolation("foreign or substituted demand operation")
    return record


async def execute_retained_dependency_demand(source, *, context):
    """Invoke the original catalog planner once; never accept a caller demand.

    The context is requested meaning only. Package, family and role must agree
    with the original admitted owner input/registry; Code performs catalog match.
    """
    if type(source) is not sources.RetainedPlanningDependencySource:
        raise TypeError("original retained planning source required")
    if type(context) is not CodeSemanticPackagePlanningContext:
        raise TypeError("exact demand planning context required")
    source_record = sources._SOURCES.get(source)
    if source_record is None or source_record[4] != os.getpid():
        raise ContractViolation("foreign retained source/process")
    origin, source_context, stage, _body, _pid = source_record
    host, registration, stages = execution._origin(origin)
    execution._check_stage(host, registration, stages, stage, status="returned")
    registry = RegistryPackageInputCodec().decode(
        stage.record.retained.registry_package.canonical_body
    )
    if (
        context.package != stage.record.expected.package
        or context.package_family != registry.semantic_package_family
        or context.package_role != registry.semantic_contract.role
    ):
        raise ContractViolation("demand context differs from original package/registry")
    context_bytes = encode_code_semantic_package_planning_context(context)
    detached = deepcopy(context)
    catalog = hosts._state(host).expected.catalog
    resolver = CodeSemanticContractCatalogResolver(catalog)
    match, match_admission = resolver.resolve(detached)
    if match.selected_binding.semantic_provider_key != registry.semantic_provider_key:
        raise ContractViolation("demand planner differs from admitted semantic owner")
    planner = _admitted_catalog_state(catalog).dependency_planners.get(
        match.selected_entry_digest
    )
    if planner is None:
        raise ContractViolation("original demand planner unavailable")
    binding = stage.record.reservation.binding
    record = _Demand(
        source,
        source_record,
        deepcopy(source_record[3].coordinate),
        source_record[3].canonical_body,
        hosts._capture(source, "read_dependencies"),
        host,
        stage,
        binding,
        catalog,
        resolver,
        hosts._capture(resolver, "plan_dependencies"),
        detached,
        context_bytes,
        match,
        encode_code_semantic_contract_match(match, context=detached, resolver=resolver),
        match_admission,
        encode_code_semantic_contract_match_admission(
            match_admission, context=detached, resolver=resolver
        ),
        planner,
        hosts._capture(planner, "plan"),
        os.getpid(),
        object(),
    )
    with hooks._guard(binding) as guard:
        hooks._original(binding, host, guard)
        if source_context in _BY_CONTEXT:
            raise ContractViolation("original demand execution replay")
        _BY_CONTEXT[source_context] = record.replay_token
    try:
        planning_input = record.validate()
        with hooks._guard(binding) as guard:
            record.check_locked(guard)
            record.status = "running"
        # The sole canonical dispatch owns detachment and result correspondence.
        result = await record.dispatch.method(
            context=detached, match=match, planning_input=planning_input
        )
        record.validate()
        result_bytes = encode_semantic_dependency_demand_set(
            result, **record.demand_context()
        )
        if encode_code_semantic_package_planning_context(context) != context_bytes:
            raise ContractViolation("caller demand context changed during execution")
        with hooks._guard(binding) as guard:
            record.check_locked(guard)
            if record.status != "running":
                raise ContractViolation("original demand invocation unavailable")
            record.result_bytes = result_bytes
            record.status = "returned"
            handle = object.__new__(RetainedDependencyDemandOperation)
            _OPERATIONS[handle] = record
        return handle
    except BaseException:
        # Source obligation remains active. Cancellation/failure never publishes
        # demand evidence, retires an epoch, or permits retry as fresh execution.
        record.status = "failed"
        raise
