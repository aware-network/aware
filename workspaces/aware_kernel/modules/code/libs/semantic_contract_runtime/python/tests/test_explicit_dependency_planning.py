import asyncio
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticContractCatalogResolver,
    ContractViolation,
    SemanticDependencyDemandSet,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyPlanningInput,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    _issue_code_semantic_contract_catalog,
)
from test_materialization_catalog import (
    _binding,
    _catalog,
    _context,
    _digest,
    _execution_closure,
)


class Planner:
    def __init__(self):
        self.calls = 0
        self.hook = None
        self.received = None

    async def plan(self, *, package, intent, selected_match, planning_input):
        self.calls += 1
        self.received = planning_input
        await asyncio.sleep(0)
        if self.hook:
            self.hook(planning_input)
        b = selected_match.selected_binding
        return SemanticDependencyDemandSet.create(
            package=package,
            intent=intent,
            profile_ref=b.profile_declaration.profile_ref,
            profile_digest=b.profile_declaration.digest,
            contract_profile_binding_digest=b.binding_digest,
            planner_implementation_ref=b.dependency_planner_implementation.implementation_ref,
            planner_implementation_digest=b.dependency_planner_implementation.closure_digest,
            planner_configuration=b.dependency_planner_configuration,
            demands=(),
        )


def fixture():
    binding = _binding()
    catalog = _catalog(binding)
    providers, planners = _execution_closure(catalog)
    planner = Planner()
    live = [True]
    admission = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=providers,
        dependency_planner_bindings=tuple((i, c, planner) for i, c, _ in planners),
        host_liveness=lambda: live[0],
    )
    resolver = CodeSemanticContractCatalogResolver(admission)
    context = _context(binding)
    match, _ = resolver.resolve(context)
    value = SemanticDependencyPlanningInput(context.package, _digest("source"), ())
    return resolver, context, match, value, planner, live


def run(resolver, context, match, value):
    return asyncio.run(
        resolver.plan_dependencies(context=context, match=match, planning_input=value)
    )


def test_explicit_input_is_detached_and_delivered():
    r, c, m, v, p, _ = fixture()
    assert run(r, c, m, v).package == c.package
    assert p.received == v and p.received is not v and p.calls == 1


def test_missing_input_has_no_fallback():
    r, c, m, _, p, _ = fixture()
    with pytest.raises(TypeError):
        asyncio.run(r.plan_dependencies(context=c, match=m))
    assert p.calls == 0


def test_wrong_package_refuses_before_planner():
    r, c, m, v, p, _ = fixture()
    v = replace(v, package=replace(v.package, package_ref="foreign"))
    with pytest.raises(ContractViolation, match="package differs"):
        run(r, c, m, v)
    assert p.calls == 0


@pytest.mark.parametrize("target", ["caller", "supplied", "entrance", "lifetime"])
def test_changes_across_await_reject(target):
    r, c, m, v, p, live = fixture()

    def mutate(supplied):
        if target in ("caller", "supplied"):
            object.__setattr__(
                v if target == "caller" else supplied,
                "source_identity_digest",
                _digest("changed"),
            )
        elif target == "entrance":
            p.plan = lambda **kw: None
        else:
            live[0] = False

    p.hook = mutate
    with pytest.raises(ContractViolation):
        run(r, c, m, v)


def test_bound_method_replacement_before_invocation_is_not_admitted():
    from types import MethodType

    r, c, m, v, p, _ = fixture()
    calls = []

    async def replacement(self, **kwargs):
        calls.append(kwargs)
        raise AssertionError("replacement must never run")

    p.plan = MethodType(replacement, p)
    with pytest.raises(ContractViolation, match="entrance substituted"):
        run(r, c, m, v)
    assert calls == [] and p.calls == 0
