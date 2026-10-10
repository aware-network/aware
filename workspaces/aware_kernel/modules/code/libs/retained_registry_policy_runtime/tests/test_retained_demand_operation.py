"""Original source-stage/demand lineage with an explicitly fixture-owned parent."""

import asyncio
import copy
import gc
import weakref
from dataclasses import fields

import pytest
import test_operation_context as fixtures
from aware_code_retained_registry_policy_runtime import direct_host as host
from aware_code_retained_registry_policy_runtime import operation_context as contexts
from aware_code_retained_registry_policy_runtime import (
    retained_demand_operation as demand,
)
from aware_code_retained_registry_policy_runtime.planning_dependency_source import (
    retained_planning_dependency_source,
)
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
    CodeSemanticPackagePlanningContext,
)
from test_direct_epoch_tracking import clearance
from test_explicit_dependency_planning import Planner
from test_materialization_catalog import _context
from test_planning_dependency_source import run
from test_planning_execution import setup


def fixture(monkeypatch):
    planner = Planner()
    original = fixtures._execution_closure

    def executables(catalog):
        providers, planners = original(catalog)
        return providers, tuple((i, c, planner) for i, c, _ in planners)

    with monkeypatch.context() as patch:
        patch.setattr(fixtures, "_execution_closure", executables)
        values, tracker, origin, context, closure = setup(patch)
    result = run(values, context, closure)
    source = retained_planning_dependency_source(origin, context)
    catalog = CodeSemanticContractCatalogResolver(values[0].expected.catalog).catalog
    authority = next(
        b for b in catalog.entries if b.profile_declaration.profile_ref == "authority"
    )
    base = _context(authority)
    kwargs = {
        f.name: getattr(base, f.name)
        for f in fields(base)
        if f.name != "context_digest"
    }
    kwargs["package"] = result.package
    graph_context = CodeSemanticPackagePlanningContext.create(**kwargs)
    return values, tracker, source, graph_context, planner, result


def execute(source, context):
    return asyncio.run(
        demand.execute_retained_dependency_demand(source, context=context)
    )


def test_original_demand_retains_exact_input_and_rejects_replay(monkeypatch):
    values, tracker, source, context, planner, original = fixture(monkeypatch)
    try:
        handle = execute(source, context)
        assert handle.read_demand().package == original.package
        record = demand._OPERATIONS[handle]
        assert (
            record.source_record[3].coordinate.digest
            == record.stage.result_body.coordinate.digest
        )
        assert planner.received == original and planner.received is not original
        assert planner.calls == 1
        with pytest.raises(ContractViolation, match="replay"):
            execute(source, context)
        assert planner.calls == 1
        assert handle.read_demand() == handle.read_demand()
        with pytest.raises(TypeError):
            copy.copy(handle)
        with pytest.raises(ContractViolation, match="active"):
            clearance(values[0], tracker)
        host.close_direct_validation_host(values[1])
        with pytest.raises(ContractViolation):
            handle.read_demand()
        retained = weakref.ref(record)
        del record, handle
        gc.collect()
        assert retained() is None  # Replay tombstone must not retain closed resources.
    finally:
        host.close_direct_validation_host(values[1])


def test_resolution_session_coalesces_original_code_callbacks(monkeypatch):
    values, _, source, context, _, _ = fixture(monkeypatch)
    operation = execute(source, context)
    record = demand._OPERATIONS[operation]
    source_context = record.source_record[1]
    source_record = contexts._CONTEXTS[source_context]

    class Probe:
        def __init__(self):
            self.counts = {}

        def record(self, *, kind, name, amount=1, **_fields):
            if kind == "counter":
                self.counts[name] = self.counts.get(name, 0) + amount

    probe = Probe()
    token = contexts.set_performance_probe(probe)
    try:
        with demand.dependency_resolution_validation_session(operation):
            contexts.source_planning_context_validator(
                values[1]
            ).validate_retained_semantic_operation_context(
                source_context, expected=source_record.expected
            )
            assert operation.read_demand() == operation.read_demand()
    finally:
        contexts.reset_performance_probe(token)
        host.close_direct_validation_host(values[1])

    # The source-context window brackets demand prevalidation and owner contact.
    # Demand validation remains complete while its source callbacks are nominal.
    assert probe.counts["code.source_context_validation_complete"] == 2
    assert probe.counts["code.source_context_validation_nominal"] == 5
    assert probe.counts["code.demand_validation_complete"] == 2
    assert probe.counts["code.demand_validation_nominal"] == 2


def test_resolution_session_rejects_foreign_operation_and_host_close(monkeypatch):
    with (
        pytest.raises(TypeError, match="exact retained demand"),
        demand.dependency_resolution_validation_session(object()),
    ):
        pass

    values, _, source, context, _, _ = fixture(monkeypatch)
    operation = execute(source, context)
    try:
        with (
            pytest.raises(ContractViolation),
            demand.dependency_resolution_validation_session(operation),
        ):
            host.close_direct_validation_host(values[1])
    finally:
        host.close_direct_validation_host(values[1])


@pytest.mark.parametrize("change", ["source", "planner", "close", "cancel"])
def test_failure_across_await_never_publishes_demand(monkeypatch, change):
    values, _, source, context, planner, original = fixture(monkeypatch)
    before = len(demand._OPERATIONS)

    def mutate(value):
        if change == "source":
            object.__setattr__(
                original,
                "source_identity_digest",
                type(original.source_identity_digest).of_bytes(b"changed"),
            )
        elif change == "planner":
            planner.plan = lambda **kw: None
        elif change == "close":
            host.close_direct_validation_host(values[1])
        else:
            raise asyncio.CancelledError()

    planner.hook = mutate
    try:
        with pytest.raises((ContractViolation, asyncio.CancelledError)):
            execute(source, context)
        assert len(demand._OPERATIONS) == before
        assert demand.sources._SOURCES[source][1] in demand._BY_CONTEXT
        if change == "cancel":
            with pytest.raises(ContractViolation, match="replay"):
                execute(source, context)
            assert planner.calls == 1
    finally:
        host.close_direct_validation_host(values[1])


def test_portable_source_is_not_original():
    with pytest.raises(TypeError, match="original retained"):
        execute(object(), object())


def test_bound_source_reader_substitution_is_not_origin_validation(monkeypatch):
    from types import MethodType

    values, _, source, context, planner, original = fixture(monkeypatch)
    calls = []

    def replacement(self, package):
        calls.append(package)
        return original

    source.read_dependencies = MethodType(replacement, source)
    try:
        with pytest.raises(ContractViolation, match="source reader substituted"):
            execute(source, context)
        assert calls == [] and planner.calls == 0
    finally:
        host.close_direct_validation_host(values[1])
