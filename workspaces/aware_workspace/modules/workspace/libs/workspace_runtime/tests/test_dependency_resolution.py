"""Selection laws with fixture owner evidence and the real Code matcher."""

from contextlib import contextmanager
from dataclasses import replace
from threading import RLock
from types import SimpleNamespace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticDependencyDemand,
    SemanticDependencyTargetConstraint,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyTarget,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    _issue_code_semantic_contract_catalog,
    _revoke_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.target_context_interfaces import (
    TargetContextFields,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime.dependency_resolution import (
    _WorkspaceDependencyResolutionRuntime,
)
from test_materialization_catalog import (
    _binding,
    _catalog,
    _context,
    _execution_closure,
)


@pytest.mark.parametrize(
    "mode",
    [
        "unique",
        "required_absent",
        "optional_absent",
        "ambiguous",
        "unsupported",
        "undeclared",
    ],
)
def test_resolution_cardinality(mode):
    binding = _binding()
    context = _context(binding)
    catalog = _catalog(binding)
    providers, planners = _execution_closure(catalog)
    admitted = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=providers,
        dependency_planner_bindings=planners,
        host_liveness=lambda: True,
    )
    inventory = object()
    packages = (context.package,)
    if mode == "ambiguous":
        packages += (replace(context.package, package_ref="package:second"),)
    handles = {p.package_ref: object() for p in packages}

    class Issuer:
        _contexts = {inventory: object()}

        def select_dependency_target_admission(self, *, inventory_admission, expected):
            assert inventory_admission is inventory
            return handles[expected.target_package.package_ref]

    class TargetOrigin:
        def issue(self, source, inventory_admission, target, **kwargs):
            assert inventory_admission is inventory
            return target

        def read(self, admission, **kwargs):
            assert admission in handles.values()
            return TargetContextFields(
                context.package_family, context.package_role, context.manifest_contract
            )

        def issue_source(self, source, inventory_admission, target, **kwargs):
            assert inventory_admission is inventory
            return target

        def read_source(self, admission, **kwargs):
            assert admission in handles.values()
            return TargetContextFields(
                context.package_family, context.package_role, context.manifest_contract
            )

    product = context.required_result_products[0]
    contract = product.contract
    if "absent" in mode:
        contract = replace(contract, version="unsupported")
    constraints = (
        (
            SemanticDependencyTargetConstraint.create(
                constraint_kind="module_ref", constraint_value="module:test"
            ),
        )
        if mode == "unsupported"
        else ()
    )
    demand = SemanticDependencyDemand.create(
        consumer_semantic_role="source",
        authored_dependency_kind="module",
        authored_dependency_ref="foreign" if mode == "undeclared" else "target",
        target_constraints=constraints,
        required_result_role=product.role,
        result_product_contract=contract,
        target_intent=context.code_intent,
        cardinality="optional" if mode == "optional_absent" else "required",
    )
    declaration = SimpleNamespace(
        target_constraints=constraints,
        targets=tuple(
            SemanticDependencyTarget(
                p, context.code_intent.requested_semantic_root_refs
            )
            for p in packages
        ),
    )
    record = SimpleNamespace(
        targets=tuple(
            SimpleNamespace(
                context=SimpleNamespace(
                    package=p,
                    source_identity_digest=ContentDigest.of_bytes(
                        p.package_ref.encode()
                    ),
                )
            )
            for p in packages
        )
    )
    expected = SimpleNamespace(
        source_planning=object(), demand_set=SimpleNamespace(demands=(demand,))
    )
    runtime = _WorkspaceDependencyResolutionRuntime(Issuer(), TargetOrigin(), admitted)
    # Only isolate selection policy. This bypass is a unit fixture, not an
    # admitted original demand, inventory or production construction entrance.
    runtime._inventory = lambda *args: (record, {("module", "target"): declaration})
    try:
        if mode in ("required_absent", "ambiguous", "unsupported", "undeclared"):
            with pytest.raises(SourceObservationUnavailable):
                runtime._resolve(object(), inventory, expected)
        else:
            result = runtime._resolve(object(), inventory, expected)
            assert len(result) == (0 if mode == "optional_absent" else 1)
            assert not runtime.records  # Selection alone issues no handle.
    finally:
        _revoke_code_semantic_contract_catalog(admitted)


def test_empty_fulfillment_refuses_nonempty_resolution():
    from aware_workspace_runtime.dependency_fulfillment import (
        _WorkspaceEmptyDependencyFulfillmentRuntime,
    )

    resolution, expected = object(), object()

    class Resolutions:
        records = {resolution: SimpleNamespace(targets=(object(),))}
        calls = 0

        def validate(self, admission, supplied):
            assert admission is resolution and supplied is expected
            self.calls += 1

    resolutions = Resolutions()
    runtime = _WorkspaceEmptyDependencyFulfillmentRuntime(resolutions)
    with pytest.raises(SourceObservationUnavailable):
        runtime.issue(resolution, expected)
    assert resolutions.calls == 1
    assert not runtime.records and not runtime.issued


def test_empty_fulfillment_retains_exact_body_and_resolution():
    import copy

    from aware_code_semantic_contract_runtime import SemanticDependencyDemandSet
    from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
        RetainedDependencyFulfillmentExpectation,
    )
    from aware_code_semantic_contract_runtime.dependency_input_codec import (
        decode_dependency_product_input,
    )
    from aware_code_semantic_contract_runtime.dependency_inputs import (
        SemanticDependencyPlanningInput,
    )
    from aware_workspace_runtime.dependency_fulfillment import (
        _WorkspaceEmptyDependencyFulfillmentRuntime,
    )

    binding = _binding()
    context = _context(binding)
    planning = SemanticDependencyPlanningInput(
        context.package, ContentDigest.of_bytes(b"source"), ()
    )
    demands = SemanticDependencyDemandSet.create(
        package=context.package,
        intent=context.code_intent,
        profile_ref=binding.profile_declaration.profile_ref,
        profile_digest=binding.profile_declaration.digest,
        contract_profile_binding_digest=binding.binding_digest,
        planner_implementation_ref=binding.dependency_planner_implementation.implementation_ref,
        planner_implementation_digest=binding.dependency_planner_implementation.closure_digest,
        planner_configuration=binding.dependency_planner_configuration,
        demands=(),
    )
    expected = SimpleNamespace(
        planning_input=planning, demand_set=demands, planning_context=context
    )
    resolution = object()

    class Resolutions:
        records = {resolution: SimpleNamespace(targets=(), expected=expected)}
        live = True

        def validate(self, handle, value):
            from aware_workspace_runtime.observed_semantic_issuers import _unavailable

            if not self.live or handle is not resolution or value is not expected:
                _unavailable("fixture_resolution_unavailable")

    resolutions = Resolutions()
    runtime = _WorkspaceEmptyDependencyFulfillmentRuntime(resolutions)
    handle = runtime.issue(resolution, expected)
    body = runtime.read(handle, resolution, expected)
    products = decode_dependency_product_input(body.canonical_body)
    assert products.products == ()
    check = RetainedDependencyFulfillmentExpectation(
        expected, body.coordinate, products
    )
    runtime.validate(handle, resolution, check)
    with pytest.raises(TypeError):
        copy.copy(handle)
    with pytest.raises(SourceObservationUnavailable):
        runtime.issue(resolution, expected)
    with pytest.raises(SourceObservationUnavailable):
        runtime.read(handle, object(), expected)
    with pytest.raises(SourceObservationUnavailable):
        runtime.validate(
            handle,
            resolution,
            replace(
                check,
                dependency_products_coordinate=replace(
                    body.coordinate, value_ref="foreign"
                ),
            ),
        )
    resolutions.live = False
    with pytest.raises(SourceObservationUnavailable):
        runtime.read(handle, resolution, expected)
    runtime.close()
    assert not runtime.records


def test_fixed_empty_product_caller_uses_original_code_session(monkeypatch):
    from aware_code_retained_registry_policy_runtime import (
        retained_demand_operation as demand_runtime,
    )
    from aware_workspace_runtime.semantic_issuer_factory import (
        WorkspaceSourcePlanningSemanticIssuerRuntime,
    )

    operation, inventory, expected = object(), object(), object()
    resolution, fulfillment, body = object(), object(), object()
    events = []

    @contextmanager
    def session(value):
        assert value is operation
        events.append("session_enter")
        try:
            yield
        finally:
            events.append("session_exit")

    issuer = object.__new__(WorkspaceSourcePlanningSemanticIssuerRuntime)
    issuer._lock = RLock()
    monkeypatch.setattr(
        WorkspaceSourcePlanningSemanticIssuerRuntime,
        "issue_dependency_resolution",
        lambda self, value, **kwargs: (events.append("resolution"), resolution)[1],
    )
    monkeypatch.setattr(
        WorkspaceSourcePlanningSemanticIssuerRuntime,
        "issue_empty_dependency_fulfillment",
        lambda self, value, **kwargs: (events.append("fulfillment"), fulfillment)[1],
    )
    monkeypatch.setattr(
        WorkspaceSourcePlanningSemanticIssuerRuntime,
        "read_dependency_products",
        lambda self, value, **kwargs: (events.append("read"), body)[1],
    )
    monkeypatch.setattr(
        demand_runtime, "dependency_resolution_validation_session", session
    )

    assert issuer.issue_empty_dependency_products(
        operation, inventory_admission=inventory, expected=expected
    ) == (resolution, fulfillment, body)
    assert events == [
        "session_enter",
        "resolution",
        "fulfillment",
        "read",
        "session_exit",
    ]
