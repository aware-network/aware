"""Tracked selected graph-product execution on the original direct host.

The fixed Workspace origin authenticates each node use and its source. Code
retains only its original method entrances and the selected registration; it
does not interpret graph or owner semantics.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from threading import current_thread
from weakref import WeakKeyDictionary, ref

from aware_code_semantic_contract_runtime import selected_input_verification as inputs
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    _result_tree,
    original_result_verification_work_scope,
)

from . import dependency_admission_origin as products
from . import direct_epoch_tracking as hooks
from . import direct_host as hosts


@dataclass
class _NodeUse:
    source: object
    epoch_use: object
    status: str = "running"
    invocation_digest: object = None


class _ProductExecutionOrigin(hosts._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("product execution origin is sealed")

    def adopt(self, source):
        record = _origin(self)
        _check_source(record, source)
        binding = record[4]
        with hooks._guard(binding) as guard:
            _check_locked(record, source, guard)
            if source in record[2]:
                raise ContractViolation("graph-product node use replay")
            use = binding.participant._begin_epoch_use(
                guard, binding.epoch, expected=binding.expected
            )
            try:
                binding.participant._start_epoch_use(guard, use)
                stage = _NodeUse(source, use)
                record[2][source] = stage
            except BaseException:
                binding.participant._abandon_unstarted_epoch_use(guard, use)
                raise
        return stage

    def validate(self, stage, closure):
        record = _origin(self)
        _check_stage(record, stage, closure=closure)

    def complete(self, stage, completion):
        record = _origin(self)
        _check_stage(record, stage)
        runtime = selected._registration_state(record[1]).runtime
        if not runtime.owns_completion(completion):
            raise ContractViolation("graph-product completion is not runtime-owned")
        snapshot = runtime.snapshot_completion(completion)
        if (
            stage.invocation_digest is None
            or snapshot.invocation_digest != stage.invocation_digest
            or snapshot.profile_digest != runtime.profile.digest
        ):
            raise ContractViolation("graph-product completion differs from node use")
        binding = record[4]
        with hooks._guard(binding) as guard:
            _check_locked(record, stage.source, guard)
            if stage.status != "running":
                raise ContractViolation("graph-product node use is terminal")
            binding.participant._finish_epoch_use(guard, stage.epoch_use)
            stage.status = "completed"

    def fail(self, stage):
        record = _origin(self)
        if type(stage) is not _NodeUse or record[2].get(stage.source) is not stage:
            raise ContractViolation("foreign graph-product node use")
        binding = record[4]
        with hooks._guard(binding) as guard:
            if stage.status == "uncertain":
                return
            if stage.status != "running":
                raise ContractViolation("graph-product node use is terminal")
            binding.participant._mark_epoch_use_uncertain(guard, stage.epoch_use)
            stage.status = "uncertain"


_ORIGINS: WeakKeyDictionary = WeakKeyDictionary()


def _origin(origin):
    if type(origin) is not _ProductExecutionOrigin:
        raise TypeError("exact graph-product execution origin required")
    record = _ORIGINS.get(origin)
    if record is None or record[5] != os.getpid():
        raise ContractViolation("foreign graph-product execution origin")
    return record


def _check_source(record, source, *, closure=None):
    retained = record[4].state.product_retention
    if retained is None:
        raise ContractViolation("original graph-product retention unavailable")
    retained.validate()
    if record[3][0].call(source, closure=closure) is not None:
        raise ContractViolation("original graph-node validator returned a value")


def _check_locked(record, source, guard):
    host, registration, _, entrances, binding, _ = record
    hooks._original(binding, host, guard)
    state = binding.state
    retained = state.product_retention
    if retained is None:
        raise ContractViolation("original graph-product retention unavailable")
    retained.check_identities()
    if sum(original is registration for _, original in retained.products) != 1:
        raise ContractViolation("original graph-product registration differs")
    if entrances[1].call(source) is not None:
        raise ContractViolation("locked graph-node verifier returned a value")


def _check_stage(record, stage, *, closure=None):
    if (
        type(stage) is not _NodeUse
        or record[2].get(stage.source) is not stage
        or stage.status != "running"
    ):
        raise ContractViolation("original running graph-product node use required")
    _check_source(record, stage.source, closure=closure)
    binding = record[4]
    with hooks._guard(binding) as guard:
        _check_locked(record, stage.source, guard)
        tracker = binding.participant
        from . import epoch_participation as epochs

        use = epochs._state(tracker).uses.get(stage.epoch_use)
        if use is None or use.status != "running" or stage.status != "running":
            raise ContractViolation("graph-product epoch use unavailable")
        if closure is not None:
            if type(closure) is not selected.SelectedProviderInvocationClosure:
                raise TypeError("exact selected graph-product closure required")
            closure.__post_init__()
            digest = closure.invocation.digest
            if stage.invocation_digest is not None and stage.invocation_digest != digest:
                raise ContractViolation("graph-product invocation changed")
            stage.invocation_digest = digest


def bind_product_execution_origin(host, registration):
    """Fixed-host only: retain the original Workspace node verifier methods.

    The composition factory was authenticated by the original bootstrap. Its
    full verifier runs outside exclusion; its identity check runs under the
    already-held parent guard. Neither method is supplied per node.
    """
    state = hosts._state(host)
    retained = state.product_retention
    if retained is None:
        raise ContractViolation("original graph-product retention required")
    retained.validate()
    original = selected._registration_state(registration)
    if sum(
        runtime is original.runtime and candidate is registration
        for runtime, candidate in retained.products
    ) != 1:
        raise ContractViolation("original graph-product registration required")
    binding = hooks._BINDINGS.get(host)
    if binding is None or binding.state is not state:
        raise ContractViolation("original graph-product epoch host required")
    factory = state.methods["factory"].receiver
    entrances = (
        hosts._capture(factory, "validate_selected_graph_node_use"),
        hosts._capture(factory, "check_selected_graph_node_use_locked"),
    )
    origin = object.__new__(_ProductExecutionOrigin)
    with hooks._guard(binding) as guard:
        hooks._original(binding, host, guard)
        retained.check_identities()
        _ORIGINS[origin] = (host, registration, {}, entrances, binding, os.getpid())
        try:
            selected._bind_selected_execution_lifecycle(
                original.runtime, registration, origin,
                terminal_mode="runtime_completion",
            )
        except BaseException:
            _ORIGINS.pop(origin, None)
            raise
    return origin


# Optional input reads use the same selected executor and epoch ledger, but have
# their own original factory entrances. They do not replace a graph binding.
_ASSEMBLY_KIND = inputs.SelectedInputVerificationAssembly
_SOURCE_KIND = inputs.SelectedInputSourceResult
_ASSEMBLY_POST = _ASSEMBLY_KIND.__post_init__
_SOURCE_POST = _SOURCE_KIND.__post_init__
_ASSEMBLY_FIELDS = (
    "semantic_input", "input_bodies", "source_results", "source_input_roles",
    "context_input_roles", "dependency_products", "dependency_input_role",
)
_SOURCE_FIELDS = ("host", "registration", "source_admission", "expected", "result")
_ASSEMBLY_SLOTS = tuple(inputs.SelectedInputVerificationAssembly.__dict__[name]
                        for name in _ASSEMBLY_FIELDS)
_SOURCE_SLOTS = tuple(inputs.SelectedInputSourceResult.__dict__[name]
                      for name in _SOURCE_FIELDS)


def _assembly_slots():
    if (inputs.SelectedInputVerificationAssembly is not _ASSEMBLY_KIND
            or inputs.SelectedInputSourceResult is not _SOURCE_KIND
            or type.__getattribute__(_ASSEMBLY_KIND, "__dict__").get("__post_init__") is not _ASSEMBLY_POST
            or type.__getattribute__(_SOURCE_KIND, "__dict__").get("__post_init__") is not _SOURCE_POST):
        raise ContractViolation("selected input assembly class/method changed")
    for kind, names, slots in (
        (inputs.SelectedInputVerificationAssembly, _ASSEMBLY_FIELDS, _ASSEMBLY_SLOTS),
        (inputs.SelectedInputSourceResult, _SOURCE_FIELDS, _SOURCE_SLOTS),
    ):
        namespace = type.__getattribute__(kind, "__dict__")
        if any(namespace.get(name) is not slot
               for name, slot in zip(names, slots, strict=True)):
            raise ContractViolation("selected input assembly slot changed")


@dataclass(frozen=True, slots=True)
class _AssemblyRetention:
    assembly: object
    fields: tuple
    sources: tuple
    trees: tuple

    def check(self):
        _assembly_slots()
        if type(self.assembly) is not inputs.SelectedInputVerificationAssembly:
            raise ContractViolation("selected input assembly type changed")
        if any(slot.__get__(self.assembly) is not original
               for slot, original in zip(_ASSEMBLY_SLOTS, self.fields, strict=True)):
            raise ContractViolation("selected input assembly identity changed")
        for source, fields in self.sources:
            if type(source) is not inputs.SelectedInputSourceResult:
                raise ContractViolation("selected input source type changed")
            if any(slot.__get__(source) is not original
                   for slot, original in zip(_SOURCE_SLOTS, fields, strict=True)):
                raise ContractViolation("selected input source identity changed")
        for tree in self.trees:
            tree.check(tree.original)
        _assembly_slots()


def _retain_assembly(assembly):
    try:
        _assembly_slots()
        if type(assembly) is not inputs.SelectedInputVerificationAssembly:
            raise TypeError("exact selected input assembly required")
        _ASSEMBLY_POST(assembly)
        fields = tuple(slot.__get__(assembly) for slot in _ASSEMBLY_SLOTS)
        sources = tuple((source, tuple(slot.__get__(source) for slot in _SOURCE_SLOTS))
                        for source in assembly.source_results)
        trees = tuple(_result_tree(value) for value in (
            assembly.input_bodies, assembly.source_input_roles, assembly.context_input_roles,
            *(value for source in assembly.source_results
              for value in (source.expected, source.result)),
        ))
        retained = _AssemblyRetention(assembly, fields, sources, trees)
        retained.check()
        return retained
    except BaseException as error:
        assembly = fields = retained = sources = trees = None
        inputs._clear_input_rejection_frames(error, __file__)
        raise


@dataclass(slots=True)
class _InputUse:
    source_ref: object
    source: object
    retained: object
    epoch_use: object = None
    status: str = "prepared"
    closure: object = None
    closure_tree: object = None
    admission: object = None
    completion: object = None
    checkpoints: int = 0
    product_reader: object = None


@dataclass(slots=True)
class _InputOriginRecord:
    host: object
    registration: object
    binding: object
    entrances: tuple
    entrance_codes: tuple
    thread: object
    pid: int
    uses: dict
    retired: bool = False
    exclusion_pending: bool = False


_READ_ORIGINS: WeakKeyDictionary = WeakKeyDictionary()


def _read_origin(origin, *, cleanup=False):
    if type(origin) is not _SelectedInputExecutionOrigin:
        raise TypeError("exact selected input origin required")
    record = _READ_ORIGINS.get(origin)
    if record is None or record.pid != os.getpid():
        raise ContractViolation("original selected input origin unavailable")
    if not cleanup and (record.retired or current_thread() is not record.thread
                        or not record.thread.is_alive()):
        raise ContractViolation("selected input origin retired or wrong thread")
    return record


def _read_entrance(record, index, *args, **kwargs):
    try:
        entrance = record.entrances[index]
        function, code = record.entrance_codes[index]
        if (entrance.method.__func__ is not function
                or object.__getattribute__(function, "__code__") is not code):
            raise ContractViolation("selected input original method code changed")
        result = entrance.call(*args, **kwargs)
        if object.__getattribute__(function, "__code__") is not code:
            raise ContractViolation("selected input original method code changed")
        return result
    except BaseException as error:
        args = code = entrance = function = index = kwargs = record = result = None
        inputs._clear_input_rejection_frames(error, __file__)
        raise


def _input_use(record, stage):
    if type(stage) is not _InputUse or not any(stage is item for item in record.uses.values()):
        raise ContractViolation("original selected input use required")
    return stage


@contextmanager
def _input_guard(record):
    if record.exclusion_pending:
        raise ContractViolation("selected input exclusion release is unconfirmed")
    # Conservatively retain custody even if acquisition itself fails. Only a
    # successful original release, or explicit outside-exclusion composition
    # cleanup, can discharge this flag. No retry reacquires an uncertain guard.
    record.exclusion_pending = True
    release = hooks._GuardRelease()
    try:
        with hooks._guard(record.binding, release_state=release) as guard:
            yield guard
    finally:
        if release.confirmed:
            record.exclusion_pending = False


def _dispose_input_data(record, stage):
    if not record.exclusion_pending:
        _release_input_data(stage)


def _release_input_data(stage):
    # Called outside parent exclusion; dropping borrowed references can invoke
    # finalizers. The weak source tombstone prevents replay without owning it.
    stage.source = stage.retained = stage.closure = stage.closure_tree = None
    stage.admission = stage.completion = stage.product_reader = None


def _read_locked(record, stage, guard):
    binding = record.binding
    if hooks._BINDINGS.get(record.host) is not binding or record.retired:
        raise ContractViolation("selected input epoch retired")
    hooks._original(binding, record.host, guard)
    retained = binding.state.product_retention
    if retained is None:
        raise ContractViolation("original product retention unavailable")
    retained.check_identities()
    if sum(candidate is record.registration for _, candidate in retained.products) != 1:
        raise ContractViolation("selected input registration changed")
    if _read_entrance(record, 1, stage.source) is not None:
        raise ContractViolation("locked selected input validator returned a value")


def _body_signature(body):
    # Both bodies have already passed closed Code traversal. Compare scalar
    # leaves explicitly; no coordinate equality or owner behavior is invoked.
    c = body.coordinate
    return (c.role, c.contract.key, c.contract.version, c.contract.schema_digest.value,
            c.value_ref, c.digest.value, c.size_bytes, body.canonical_body)


def _read_full(record, stage, *, closure=None):
    try:
        _input_use(record, stage)
        if (record.exclusion_pending or record.retired or record.pid != os.getpid()
                or current_thread() is not record.thread or not record.thread.is_alive()
                or hooks._BINDINGS.get(record.host) is not record.binding
                or hosts._HOSTS.get(record.host) is not record.binding.state
                or record.binding.state.closed):
            stage.status = "retired"
            _dispose_input_data(record, stage)
            raise ContractViolation("selected input host/thread/epoch unavailable")
        if stage.status not in ("prepared", "running", "completed"):
            raise ContractViolation("selected input use is terminal")
        if stage.checkpoints >= 32:
            stage.status = "retired"
            _dispose_input_data(record, stage)
            raise ContractViolation("selected input checkpoint bound exceeded")
        stage.checkpoints += 1
        retained = stage.retained
        try:
            retained.check()
            assembly = retained.assembly
            if closure is not None:
                if type(closure) is not selected.SelectedProviderInvocationClosure:
                    raise ContractViolation("exact selected input closure required")
                if closure.input_bodies is not assembly.input_bodies:
                    raise ContractViolation("selected input closure body tuple differs")
                if stage.closure is not None and closure is not stage.closure:
                    raise ContractViolation("selected input closure substituted")
            original = record.binding.state.product_retention
            if original is None:
                raise ContractViolation("selected input product retention unavailable")
            original.validate()
            with original_result_verification_work_scope():
                if _read_entrance(record, 0, stage.source, assembly=assembly, closure=closure) is not None:
                    raise ContractViolation("selected input validator returned a value")
                if assembly.dependency_products is not None:
                    original_products = products._product_record(assembly.dependency_products)
                    product_origin = products._ORIGINS.get(original_products.origin)
                    if product_origin is None or product_origin.host is not record.host:
                        raise ContractViolation("selected dependency product host differs")
                    if stage.product_reader is None:
                        stage.product_reader = hosts._capture(assembly.dependency_products, "read_products")
                    body = stage.product_reader.call()
                    if type(body) is not inputs.SemanticBody:
                        raise ContractViolation("selected product reader returned a foreign body")
                    inputs._body(body)
                    target = next(body for body in assembly.input_bodies
                                  if body.coordinate.role == assembly.dependency_input_role)
                    if _body_signature(body) != _body_signature(target):
                        raise ContractViolation("selected dependency input body differs")
            retained.check()
            with _input_guard(record) as guard:
                _read_locked(record, stage, guard)
            retained.check()
        except BaseException:
            stage.status = "retired"
            _dispose_input_data(record, stage)
            # Withheld exceptions must not keep this delivery's borrowed body set.
            retained = assembly = original = body = target = original_products = product_origin = None
            raise
    except BaseException as error:
        assembly = body = closure = guard = original = original_products = product_origin = record = retained = stage = target = None
        inputs._clear_input_rejection_frames(error, __file__)
        raise


class _SelectedInputExecutionOrigin(hosts._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("selected input execution origin is sealed")

    def adopt(self, source, semantic_input):
        try:
            record = _read_origin(self)
            stage = record.uses.get(id(source))
            if stage is None or stage.source is not source or stage.status != "prepared":
                raise ContractViolation("original prepared selected input use required once")
            if stage.retained.assembly.semantic_input is not semantic_input:
                stage.status = "retired"
                _dispose_input_data(record, stage)
                raise ContractViolation("selected input semantic input differs")
            try:
                _read_full(record, stage)
                with _input_guard(record) as guard:
                    _read_locked(record, stage, guard)
                    stage.epoch_use = record.binding.participant._begin_epoch_use(
                        guard, record.binding.epoch, expected=record.binding.expected)
                    try:
                        record.binding.participant._start_epoch_use(guard, stage.epoch_use)
                        stage.status = "running"
                    except BaseException:
                        record.binding.participant._abandon_unstarted_epoch_use(guard, stage.epoch_use)
                        stage.status = "retired"
                        raise
            except BaseException:
                stage.status = "retired"
                _dispose_input_data(record, stage)
                raise
            return stage
        except BaseException as error:
            guard = record = self = semantic_input = source = stage = None  # noqa: PLW0642 - release rejection-frame custody
            inputs._clear_input_rejection_frames(error, __file__)
            raise

    def validate(self, stage, closure):
        try:
            record = _read_origin(self)
            _input_use(record, stage)
            if stage.status != "running":
                raise ContractViolation("running selected input use required")
            _read_full(record, stage, closure=closure)
            if stage.closure is None:
                stage.closure = closure
                stage.closure_tree = _result_tree(closure.input_bodies)
            stage.closure_tree.check(closure.input_bodies)
        except BaseException as error:
            closure = record = self = stage = None  # noqa: PLW0642 - release rejection-frame custody
            inputs._clear_input_rejection_frames(error, __file__)
            raise

    def complete(self, stage, completion):
        try:
            record = _read_origin(self)
            _input_use(record, stage)
            if stage.status != "running":
                raise ContractViolation("running selected input completion required")
            _read_full(record, stage, closure=stage.closure)
            runtime = selected._registration_state(record.registration).runtime
            if not runtime.owns_completion(completion):
                raise ContractViolation("selected input completion is not runtime-owned")
            snapshot = runtime.snapshot_completion(completion)
            if (snapshot.invocation_digest != stage.closure.invocation.digest
                    or snapshot.profile_digest != runtime.profile.digest):
                raise ContractViolation("selected input completion differs")
            with _input_guard(record) as guard:
                _read_locked(record, stage, guard)
                record.binding.participant._finish_epoch_use(guard, stage.epoch_use)
                stage.completion = completion
                stage.status = "completed"
        except BaseException as error:
            completion = guard = record = runtime = self = snapshot = stage = None  # noqa: PLW0642 - release rejection-frame custody
            inputs._clear_input_rejection_frames(error, __file__)
            raise

    def verify_inputs(self, stage, evidence):
        try:
            record = _read_origin(self)
            _input_use(record, stage)
            if (evidence.registration is not record.registration
                    or stage.retained is None
                    or evidence.semantic_input is not stage.retained.assembly.semantic_input
                    or evidence.closure is not stage.closure
                    or (stage.admission is not None and evidence.admission is not stage.admission)):
                raise ContractViolation("selected input invocation association differs")
            if evidence.terminal_success:
                if stage.status != "completed" or evidence.completion is not stage.completion:
                    raise ContractViolation("original successful selected completion required")
            elif stage.status != "running":
                raise ContractViolation("original active selected input use required")
            stage.admission = evidence.admission
            _read_full(record, stage, closure=stage.closure)
            stage.closure_tree.check(evidence.closure.input_bodies)
        except BaseException as error:
            evidence = record = self = stage = None  # noqa: PLW0642 - release rejection-frame custody
            inputs._clear_input_rejection_frames(error, __file__)
            raise

    def release_inputs(self, stage, evidence):
        try:
            record = _read_origin(self, cleanup=True)
            _input_use(record, stage)
            if evidence.registration is not record.registration:
                raise ContractViolation("selected input cleanup registration differs")
            stage.status = "released"
            _dispose_input_data(record, stage)
        except BaseException as error:
            evidence = record = self = stage = None  # noqa: PLW0642 - release rejection-frame custody
            inputs._clear_input_rejection_frames(error, __file__)
            raise

    def retire_inputs(self):
        try:
            if self not in _READ_ORIGINS:
                return  # Host/epoch disposal already removed every reference.
            record = _read_origin(self, cleanup=True)
            # Registration closure can occur under exclusion. Only revoke here;
            # the host's disposal runs after the original guard is released.
            record.retired = True
            for stage in record.uses.values():
                stage.status = "retired"
        except BaseException as error:
            record = self = stage = None  # noqa: PLW0642 - release rejection-frame custody
            inputs._clear_input_rejection_frames(error, __file__)
            raise

    def fail(self, stage):
        try:
            record = _read_origin(self, cleanup=True)
            _input_use(record, stage)
            try:
                if (not record.exclusion_pending and stage.epoch_use is not None
                        and hooks._BINDINGS.get(record.host) is record.binding):
                    with _input_guard(record) as guard:
                        from . import epoch_participation as epochs
                        current = epochs._state(record.binding.participant).uses.get(stage.epoch_use)
                        if current is not None and current.status == "running":
                            record.binding.participant._mark_epoch_use_uncertain(guard, stage.epoch_use)
            finally:
                stage.status = "failed"
                _dispose_input_data(record, stage)
        except BaseException as error:
            current = guard = record = self = stage = None  # noqa: PLW0642 - release rejection-frame custody
            inputs._clear_input_rejection_frames(error, __file__)
            raise


def bind_selected_input_verification_origin(host, registration):
    """Authenticate the fixed factory and capture its two original entrances."""
    try:
        state = hosts._state(host)
        binding = hooks._BINDINGS.get(host)
        retained = state.product_retention
        if binding is None or binding.state is not state or retained is None:
            raise ContractViolation("original selected input host required")
        retained.validate()
        original = selected._registration_state(registration)
        if original.selected_invocation_observer is None:
            raise ContractViolation("original selected input observer required")
        if sum(runtime is original.runtime and candidate is registration
               for runtime, candidate in retained.products) != 1:
            raise ContractViolation("original selected input registration required")
        factory = state.methods["factory"].receiver
        entrances = (hosts._capture(factory, "validate_selected_input_node_use"),
                     hosts._capture(factory, "check_selected_input_node_use_locked"))
        origin = object.__new__(_SelectedInputExecutionOrigin)
        codes = tuple((entrance.method.__func__, entrance.method.__func__.__code__)
                      for entrance in entrances)
        record = _InputOriginRecord(host, registration, binding, entrances, codes,
                                    current_thread(), os.getpid(), {})
        with hooks._guard(binding) as guard:
            hooks._original(binding, host, guard)
            retained.check_identities()
            _READ_ORIGINS[origin] = record
            try:
                selected._bind_selected_execution_lifecycle(
                    original.runtime, registration, origin,
                    terminal_mode="runtime_completion", input_verification=True)
            except BaseException:
                _READ_ORIGINS.pop(origin, None)
                raise
        return origin
    except BaseException as error:
        binding = codes = entrances = factory = guard = host = origin = original = record = registration = retained = state = None
        inputs._clear_input_rejection_frames(error, __file__)
        raise


def prepare_selected_input_verification(host, operation_context, registration, *, assembly):
    """Fixed composition only; caller values cannot appoint the factory validator."""
    try:
        record = next((record for record in _READ_ORIGINS.values()
                       if record.host is host and record.registration is registration), None)
        if record is None or record.retired or record.pid != os.getpid():
            raise ContractViolation("selected input origin was not bound")
        if current_thread() is not record.thread or not record.thread.is_alive():
            raise ContractViolation("selected input preparation thread changed")
        if len(record.uses) >= 32:
            raise ContractViolation("selected input retained-use bound exceeded")
        key = id(operation_context)
        previous = record.uses.get(key)
        if previous is not None and previous.source_ref() is operation_context:
            raise ContractViolation("selected input preparation replay")
        retained = _retain_assembly(assembly)
        stage = _InputUse(ref(operation_context), operation_context, retained)
        record.uses[key] = stage
        _read_full(record, stage)
    except BaseException as error:
        assembly = host = key = operation_context = previous = record = registration = retained = stage = None
        inputs._clear_input_rejection_frames(error, __file__)
        raise


def _selected_input_exclusion_pending(host):
    return any(record.host is host and record.exclusion_pending
               for record in _READ_ORIGINS.values())


def _retire_selected_input_host(host, binding=None, *, exclusion_pending=False):
    """Guard-held Code retirement only, without dropping owned references."""
    for record in _READ_ORIGINS.values():
        if record.host is host and (binding is None or record.binding is binding):
            record.retired = True
            if exclusion_pending:
                record.exclusion_pending = True
            for stage in record.uses.values():
                stage.status = "retired"


def _dispose_retired_selected_inputs(host):
    """After exclusion: release only delivery references, never borrowed issuers."""
    for origin, record in tuple(_READ_ORIGINS.items()):
        if record.host is host and record.retired:
            record.exclusion_pending = False  # Caller confirms outside exclusion.
            for stage in record.uses.values():
                _release_input_data(stage)
            _READ_ORIGINS.pop(origin, None)
