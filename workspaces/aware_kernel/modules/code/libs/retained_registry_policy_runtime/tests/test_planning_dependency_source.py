"""Original selected-return dependency source, without Workspace admission claims."""

import copy
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as host
from aware_code_retained_registry_policy_runtime import planning_execution as execution
from aware_code_retained_registry_policy_runtime.planning_dependency_source import (
    retained_planning_dependency_source,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyTarget,
)
from test_direct_epoch_tracking import clearance
from test_planning_execution import setup


def run(values, context, closure):
    admission = selected.issue_selected_provider_execution(
        values[0].expected.runtime, values[4], closure, operation_context=context
    )
    return selected.execute_selected_provider(values[0].expected.runtime, admission)


def test_existing_dependency_source_returns_detached_exact_planning(monkeypatch):
    values, tracker, origin, context, closure = setup(monkeypatch)
    result = run(values, context, closure)
    source = retained_planning_dependency_source(origin, context)
    first = source.read_dependencies(result.package)
    second = source.read_dependencies(result.package)
    assert first == result == second
    assert first is not result and first is not second
    with pytest.raises(ContractViolation, match="active"):
        clearance(values[0], tracker)
    with pytest.raises(TypeError):
        copy.copy(source)
    host.close_direct_validation_host(values[1])
    with pytest.raises(ContractViolation):
        source.read_dependencies(result.package)


def test_no_source_before_original_selected_return(monkeypatch):
    values, _, origin, context, _ = setup(monkeypatch)
    with pytest.raises(ContractViolation, match="returned planning"):
        retained_planning_dependency_source(origin, context)
    host.close_direct_validation_host(values[1])


@pytest.mark.parametrize("change", ["package", "source", "untyped", "target"])
def test_bad_original_return_never_becomes_planning_source(monkeypatch, change):
    values, _, origin, context, closure = setup(monkeypatch)
    result = values[3].result
    if change == "package":
        result = replace(result, package=replace(result.package, package_ref="foreign"))
    elif change == "source":
        result = replace(
            result, source_identity_digest=ContentDigest.of_bytes(b"foreign")
        )
    elif change == "target":
        result = replace(
            result,
            dependencies=(
                SemanticAuthoredDependency(
                    "module",
                    "foreign",
                    (SemanticDependencyTarget(result.package, ("home",)),),
                ),
            ),
        )
    else:
        result = object()
    values[3].result = result
    with pytest.raises((ContractViolation, TypeError)):
        run(values, context, closure)
    assert execution._ORIGINS[origin][2][context].status == "uncertain"
    with pytest.raises(ContractViolation):
        retained_planning_dependency_source(origin, context)
    host.close_direct_validation_host(values[1])


def test_mutation_after_return_cannot_be_admitted(monkeypatch):
    values, _, origin, context, closure = setup(monkeypatch)
    result = run(values, context, closure)
    object.__setattr__(
        result, "source_identity_digest", ContentDigest.of_bytes(b"changed")
    )
    with pytest.raises(ContractViolation):
        retained_planning_dependency_source(origin, context)
    host.close_direct_validation_host(values[1])


def test_detached_result_mutation_does_not_change_original_source(monkeypatch):
    values, _, origin, context, closure = setup(monkeypatch)
    result = run(values, context, closure)
    source = retained_planning_dependency_source(origin, context)
    detached = source.read_dependencies(result.package)
    object.__setattr__(detached, "dependencies", ())
    object.__setattr__(
        detached, "source_identity_digest", ContentDigest.of_bytes(b"changed")
    )
    assert source.read_dependencies(result.package) == result
    with pytest.raises(ContractViolation, match="package differs"):
        source.read_dependencies(replace(result.package, package_ref="foreign"))
    host.close_direct_validation_host(values[1])


def test_original_reader_substitution_rejects(monkeypatch):
    values, _, origin, context, closure = setup(monkeypatch)
    result = run(values, context, closure)
    source = retained_planning_dependency_source(origin, context)
    original = source.read_dependencies
    source.read_dependencies = lambda package: result
    with pytest.raises(ContractViolation, match="substituted"):
        original(result.package)
    host.close_direct_validation_host(values[1])


def test_typed_value_cannot_replace_selected_result_contract(monkeypatch):
    values, _, origin, context, closure = setup(monkeypatch, declare_result=False)
    with pytest.raises(ContractViolation, match="does not declare planning result"):
        run(values, context, closure)
    with pytest.raises(ContractViolation):
        retained_planning_dependency_source(origin, context)
    host.close_direct_validation_host(values[1])


@pytest.mark.parametrize("substitute_root", [False, True])
def test_selected_targets_must_match_retained_inventory(monkeypatch, substitute_root):
    import test_operation_context as fixtures
    from aware_code_semantic_contract_runtime.retained_input_projections import (
        CodeSemanticDeclarationTarget,
        CodeSemanticDeclarationTargetInventory,
    )

    original = fixtures.retained_projection_body
    entries = []

    def with_inventory(value):
        if type(value) is CodeSemanticDeclarationTargetInventory:
            entry = CodeSemanticDeclarationTarget(
                "module",
                "selected",
                (SemanticDependencyTarget(value.package, ("home",)),),
            )
            entries.append(entry)
            value = replace(value, entries=(entry,))
        return original(value)

    with monkeypatch.context() as patch:
        patch.setattr(fixtures, "retained_projection_body", with_inventory)
        values, _, origin, context, closure = setup(patch)
    entry = entries[0]
    dependency = SemanticAuthoredDependency(
        entry.dependency_kind,
        entry.dependency_ref,
        entry.targets,
        entry.target_constraints,
    )
    if substitute_root:
        dependency = replace(
            dependency,
            targets=(replace(entry.targets[0], semantic_root_refs=("foreign",)),),
        )
    values[3].result = replace(values[3].result, dependencies=(dependency,))
    if substitute_root:
        with pytest.raises(ContractViolation, match="retained inventory"):
            run(values, context, closure)
    else:
        result = run(values, context, closure)
        source = retained_planning_dependency_source(origin, context)
        assert source.read_dependencies(result.package).dependencies == (dependency,)
    host.close_direct_validation_host(values[1])
