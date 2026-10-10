"""Original Code source composition; fixture parent, no bootstrap qualification."""

import copy
from dataclasses import replace
from typing import Any, cast

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as host
from aware_code_retained_registry_policy_runtime.planning_dependency_source import (
    RetainedPlanningDependencySource,
    retained_planning_dependency_source,
)
from aware_code_retained_registry_policy_runtime.planning_source_composition import (
    compose_retained_planning_sources,
    validate_composed_retained_planning_source,
)
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyPlanningInput,
)
from test_planning_dependency_source import run
from test_planning_execution import setup


def source_fixture(
    monkeypatch,
) -> tuple[Any, SemanticDependencyPlanningInput, RetainedPlanningDependencySource]:
    values, _, origin, context, closure = setup(monkeypatch)
    result = cast(SemanticDependencyPlanningInput, run(values, context, closure))
    source = retained_planning_dependency_source(origin, context)
    return values, result, source


def test_original_source_handoff_and_missing_package(monkeypatch):
    values, original, source = source_fixture(monkeypatch)
    try:
        composed = compose_retained_planning_sources((source,))
        assert (
            validate_composed_retained_planning_source(
                values[1], composed, (original.package,)
            )
            is None
        )
        value = composed.read_dependencies(original.package)
        assert value == original and value is not original
        with pytest.raises(ContractViolation, match="unavailable"):
            composed.read_dependencies(replace(original.package, package_ref="missing"))
        with pytest.raises(TypeError):
            copy.copy(composed)
        with pytest.raises(ContractViolation, match="foreign"):
            object.__new__(type(composed)).read_dependencies(original.package)
        host.close_direct_validation_host(values[1])
        with pytest.raises(ContractViolation):
            composed.read_dependencies(original.package)
    finally:
        host.close_direct_validation_host(values[1])


@pytest.mark.parametrize("kind", ["duplicate", "substitution", "fork", "mutation"])
def test_original_source_rejection(monkeypatch, kind):
    import os

    values, original, source = source_fixture(monkeypatch)
    try:
        if kind == "duplicate":
            with pytest.raises(ContractViolation, match="duplicate"):
                compose_retained_planning_sources((source, source))
            return
        composed = compose_retained_planning_sources((source,))
        if kind == "substitution":
            object.__setattr__(source, "read_dependencies", lambda package: original)
        elif kind == "fork":
            pid = os.getpid()
            monkeypatch.setattr(os, "getpid", lambda: pid + 1)
        else:
            object.__setattr__(
                original,
                "source_identity_digest",
                type(original.source_identity_digest).of_bytes(b"changed"),
            )
        with pytest.raises(ContractViolation):
            composed.read_dependencies(original.package)
    finally:
        monkeypatch.undo()
        host.close_direct_validation_host(values[1])


def test_portable_or_protocol_inputs_are_not_originals():
    class Fake:
        def read_dependencies(self, package):
            raise AssertionError("must not call foreign reader")

    with pytest.raises(TypeError):
        compose_retained_planning_sources((Fake(),))
    with pytest.raises(ContractViolation):
        compose_retained_planning_sources(())


def test_original_sources_from_foreign_parents_do_not_compose(monkeypatch):
    first, _, source1 = source_fixture(monkeypatch)
    second = None
    try:
        second, _, source2 = source_fixture(monkeypatch)
        with pytest.raises(ContractViolation, match="different parent/epoch/catalog"):
            compose_retained_planning_sources((source1, source2))
    finally:
        if second is not None:
            host.close_direct_validation_host(second[1])
        host.close_direct_validation_host(first[1])


def test_revoked_original_context_invalidates_composition(monkeypatch):
    from aware_code_retained_registry_policy_runtime import (
        operation_context as contexts,
    )
    from aware_code_retained_registry_policy_runtime import (
        planning_dependency_source as sources,
    )

    values, original, source = source_fixture(monkeypatch)
    try:
        composed = compose_retained_planning_sources((source,))
        _, context, stage, _, _ = sources._SOURCES[source]
        with pytest.raises(ContractViolation, match="expectation differs"):
            contexts.source_planning_context_validator(
                values[1]
            ).validate_retained_semantic_operation_context(
                context,
                expected=replace(stage.record.expected, operation_identity=object()),
            )
        with pytest.raises(ContractViolation, match="lineage changed"):
            composed.read_dependencies(original.package)
    finally:
        host.close_direct_validation_host(values[1])


def test_composed_source_requires_exact_host_and_complete_package_closure(monkeypatch):
    first, original, source = source_fixture(monkeypatch)
    second = None
    try:
        composed = compose_retained_planning_sources((source,))
        second, _, _ = source_fixture(monkeypatch)
        with pytest.raises(ContractViolation, match="another direct host"):
            validate_composed_retained_planning_source(
                second[1], composed, (original.package,)
            )
        with pytest.raises(ContractViolation, match="1..4096"):
            validate_composed_retained_planning_source(first[1], composed, ())
        extra = replace(original.package, package_ref="zz-extra")
        with pytest.raises(ContractViolation, match="package closure differs"):
            validate_composed_retained_planning_source(
                first[1], composed, (original.package, extra)
            )
    finally:
        if second is not None:
            host.close_direct_validation_host(second[1])
        host.close_direct_validation_host(first[1])


def test_composed_source_host_validation_rejects_operation_change_and_replay(
    monkeypatch,
):
    from aware_code_retained_registry_policy_runtime import (
        planning_source_composition as compositions,
    )

    values, original, source = source_fixture(monkeypatch)
    composed = compose_retained_planning_sources((source,))
    try:
        state = compositions._COMPOSITIONS[composed]
        member = state.members[0]
        object.__setattr__(
            member.retained[2].record.expected,
            "operation_identity",
            object(),
        )
        with pytest.raises(ContractViolation, match="operation identity changed"):
            validate_composed_retained_planning_source(
                values[1], composed, (original.package,)
            )
    finally:
        host.close_direct_validation_host(values[1])

    with pytest.raises(ContractViolation, match="foreign or closed host"):
        validate_composed_retained_planning_source(
            values[1], composed, (original.package,)
        )
