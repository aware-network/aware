from __future__ import annotations

from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    CodeComposedSemanticMaterializationIntent,
    CodeSemanticMaterializationIntent,
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticDependencyDemand,
    SemanticDependencyDemandSet,
    SemanticDependencyTargetConstraint,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)


def _digest(value: str) -> ContentDigest:
    return ContentDigest.of_bytes(value.encode())


def _package(manifest: str = "manifest-v1") -> SemanticPackageCoordinate:
    return SemanticPackageCoordinate(
        package_ref="package:sdk",
        package_kind="sdk",
        manifest_digest=_digest(manifest),
    )


def _intent() -> CodeSemanticMaterializationIntent:
    return CodeSemanticMaterializationIntent.create(
        operation_kind="materialize",
        requested_semantic_root_refs=("sdk.public",),
        requested_terminal_output_roles=("python_sdk",),
        semantic_configuration_coordinate=SemanticConfigurationCoordinate(
            configuration_ref="sdk.python",
            digest=_digest("configuration"),
        ),
    )


def _constraints() -> tuple[SemanticDependencyTargetConstraint, ...]:
    values = (
        SemanticDependencyTargetConstraint.create(
            constraint_kind="semantic_provider_key",
            constraint_value="aware.api.sdk",
        ),
        SemanticDependencyTargetConstraint.create(
            constraint_kind="package_kind", constraint_value="api"
        ),
        SemanticDependencyTargetConstraint.create(
            constraint_kind="semantic_root_ref", constraint_value="api.public"
        ),
    )
    return tuple(sorted(values, key=lambda item: canonical_json_bytes(item.to_wire())))


def _demand(authored_ref: str = "sdk.api") -> SemanticDependencyDemand:
    result_contract = SemanticContractRef(
        key="aware.api.contract",
        version="1",
        schema_digest=_digest("api-contract"),
    )
    return SemanticDependencyDemand.create(
        consumer_semantic_role="sdk_source",
        authored_dependency_kind="api_package",
        authored_dependency_ref=authored_ref,
        target_constraints=_constraints(),
        required_result_role="api_contract",
        result_product_contract=result_contract,
        target_intent=CodeSemanticMaterializationIntent.create(
            operation_kind="materialize",
            requested_semantic_root_refs=("api.public",),
            requested_terminal_output_roles=("api_contract",),
            semantic_configuration_coordinate=SemanticConfigurationCoordinate(
                configuration_ref="sdk.python",
                digest=_digest("configuration"),
            ),
        ),
        cardinality="required",
    )


def _demand_set(
    package: SemanticPackageCoordinate | None = None,
) -> SemanticDependencyDemandSet:
    return SemanticDependencyDemandSet.create(
        package=package or _package(),
        intent=_intent(),
        profile_ref="sdk.materialization",
        profile_digest=_digest("profile"),
        contract_profile_binding_digest=_digest("profile-binding"),
        planner_implementation_ref="sdk.dependency-planner",
        planner_implementation_digest=_digest("planner"),
        planner_configuration=SemanticConfigurationCoordinate(
            configuration_ref="sdk.dependency-planner",
            digest=_digest("planner-configuration"),
        ),
        demands=(_demand(),),
    )


def test_intent_and_demand_set_bind_complete_semantic_identity() -> None:
    intent = _intent()
    demand_set = _demand_set()

    assert demand_set.package.manifest_digest == _digest("manifest-v1")
    assert demand_set.intent_digest == intent.intent_digest
    assert demand_set.demands[0].consumer_semantic_role == "sdk_source"
    assert demand_set.demands[0].authored_dependency_ref == "sdk.api"
    assert {
        item.constraint_kind for item in demand_set.demands[0].target_constraints
    } == {"package_kind", "semantic_provider_key", "semantic_root_ref"}


def test_authored_dependency_and_package_manifest_change_identity() -> None:
    assert _demand("sdk.api").demand_digest != _demand("sdk.api.v2").demand_digest
    assert (
        _demand_set(_package("manifest-v1")).demand_set_digest
        != _demand_set(_package("manifest-v2")).demand_set_digest
    )


def test_demand_set_uses_unique_digest_order() -> None:
    demands = tuple(
        sorted(
            (_demand("sdk.api"), _demand("sdk.other")),
            key=lambda item: item.demand_digest.value,
        )
    )
    value = SemanticDependencyDemandSet.create(
        package=_package(),
        intent=_intent(),
        profile_ref="sdk.materialization",
        profile_digest=_digest("profile"),
        contract_profile_binding_digest=_digest("profile-binding"),
        planner_implementation_ref="sdk.dependency-planner",
        planner_implementation_digest=_digest("planner"),
        planner_configuration=SemanticConfigurationCoordinate(
            configuration_ref="sdk.dependency-planner",
            digest=_digest("planner-configuration"),
        ),
        demands=demands,
    )
    assert value.demands == demands

    with pytest.raises(ContractViolation, match="demand-digest ordered"):
        SemanticDependencyDemandSet.create(
            package=_package(),
            intent=_intent(),
            profile_ref="sdk.materialization",
            profile_digest=_digest("profile"),
            contract_profile_binding_digest=_digest("profile-binding"),
            planner_implementation_ref="sdk.dependency-planner",
            planner_implementation_digest=_digest("planner"),
            planner_configuration=SemanticConfigurationCoordinate(
                configuration_ref="sdk.dependency-planner",
                digest=_digest("planner-configuration"),
            ),
            demands=tuple(reversed(demands)),
        )


def test_constraints_reject_unknown_duplicate_and_noncanonical_values() -> None:
    with pytest.raises(ContractViolation, match="kind unsupported"):
        SemanticDependencyTargetConstraint.create(
            constraint_kind="implementation_ref", constraint_value="forbidden"
        )

    duplicate = (
        SemanticDependencyTargetConstraint.create(
            constraint_kind="package_kind", constraint_value="api"
        ),
        SemanticDependencyTargetConstraint.create(
            constraint_kind="package_kind", constraint_value="service"
        ),
    )
    duplicate = tuple(
        sorted(duplicate, key=lambda item: canonical_json_bytes(item.to_wire()))
    )
    with pytest.raises(ContractViolation, match="singleton"):
        SemanticDependencyDemand.create(
            consumer_semantic_role="sdk_source",
            authored_dependency_kind="api_package",
            authored_dependency_ref="sdk.api",
            target_constraints=duplicate,
            required_result_role="api_contract",
            result_product_contract=SemanticContractRef(
                key="aware.api.contract",
                version="1",
                schema_digest=_digest("contract"),
            ),
            target_intent=CodeSemanticMaterializationIntent.create(
                operation_kind="materialize",
                requested_semantic_root_refs=("api.public",),
                requested_terminal_output_roles=("api_contract",),
                semantic_configuration_coordinate=None,
            ),
            cardinality="required",
        )

    reversed_constraints = tuple(reversed(_constraints()))
    with pytest.raises(ContractViolation, match="canonical-byte ordered"):
        SemanticDependencyDemand.create(
            consumer_semantic_role="sdk_source",
            authored_dependency_kind="api_package",
            authored_dependency_ref="sdk.api",
            target_constraints=reversed_constraints,
            required_result_role="api_contract",
            result_product_contract=SemanticContractRef(
                key="aware.api.contract",
                version="1",
                schema_digest=_digest("contract"),
            ),
            target_intent=CodeSemanticMaterializationIntent.create(
                operation_kind="materialize",
                requested_semantic_root_refs=("api.public",),
                requested_terminal_output_roles=("api_contract",),
                semantic_configuration_coordinate=None,
            ),
            cardinality="required",
        )


def test_restamped_nested_and_outer_digests_fail() -> None:
    constraint = _constraints()[0]
    with pytest.raises(ContractViolation, match="constraint digest"):
        replace(constraint, constraint_digest=_digest("forged"))

    demand_set = _demand_set()
    with pytest.raises(ContractViolation, match="demand set digest"):
        replace(demand_set, demand_set_digest=_digest("forged"))


def test_foreign_nested_types_fail_before_foreign_wire_method() -> None:
    calls: list[str] = []

    class ForeignConstraint(SemanticDependencyTargetConstraint):
        def to_wire(self) -> dict[str, object]:
            calls.append("foreign")
            return super().to_wire()

    exact = _constraints()[0]
    foreign = ForeignConstraint(
        constraint_kind=exact.constraint_kind,
        constraint_value=exact.constraint_value,
        constraint_digest=exact.constraint_digest,
    )
    with pytest.raises(TypeError, match="exact SemanticDependencyTargetConstraint"):
        SemanticDependencyDemand.create(
            consumer_semantic_role="sdk_source",
            authored_dependency_kind="api_package",
            authored_dependency_ref="sdk.api",
            target_constraints=(foreign,),
            required_result_role="api_contract",
            result_product_contract=SemanticContractRef(
                key="aware.api.contract",
                version="1",
                schema_digest=_digest("contract"),
            ),
            target_intent=CodeSemanticMaterializationIntent.create(
                operation_kind="materialize",
                requested_semantic_root_refs=("api.public",),
                requested_terminal_output_roles=("api_contract",),
                semantic_configuration_coordinate=None,
            ),
            cardinality="required",
        )
    assert calls == []


def test_demand_set_rejects_foreign_intent_before_foreign_validation() -> None:
    calls: list[str] = []

    class ForeignIntent(CodeSemanticMaterializationIntent):
        def __post_init__(self) -> None:
            calls.append("foreign")

    exact = _intent()
    foreign = ForeignIntent(
        operation_kind=exact.operation_kind,
        requested_semantic_root_refs=exact.requested_semantic_root_refs,
        requested_terminal_output_roles=exact.requested_terminal_output_roles,
        semantic_configuration_coordinate=exact.semantic_configuration_coordinate,
        intent_digest=exact.intent_digest,
    )
    calls.clear()

    with pytest.raises(TypeError, match="exact CodeSemanticMaterializationIntent"):
        SemanticDependencyDemandSet.create(
            package=_package(),
            intent=foreign,
            profile_ref="sdk.materialization",
            profile_digest=_digest("profile"),
            contract_profile_binding_digest=_digest("profile-binding"),
            planner_implementation_ref="sdk.dependency-planner",
            planner_implementation_digest=_digest("planner"),
            planner_configuration=SemanticConfigurationCoordinate(
                configuration_ref="sdk.dependency-planner",
                digest=_digest("planner-configuration"),
            ),
            demands=(_demand(),),
        )
    assert calls == []


def test_target_intent_fan_in_is_code_owned_and_contract_exact() -> None:
    first = _demand("sdk.api")
    second_contract = SemanticContractRef(
        key="aware.api.docs", version="1", schema_digest=_digest("docs-contract")
    )
    second = SemanticDependencyDemand.create(
        consumer_semantic_role="sdk_docs",
        authored_dependency_kind="api_package",
        authored_dependency_ref="sdk.api.docs",
        target_constraints=_constraints(),
        required_result_role="api_docs",
        result_product_contract=second_contract,
        target_intent=CodeSemanticMaterializationIntent.create(
            operation_kind="materialize",
            requested_semantic_root_refs=("api.docs",),
            requested_terminal_output_roles=("api_docs",),
            semantic_configuration_coordinate=first.target_intent.semantic_configuration_coordinate,
        ),
        cardinality="required",
    )
    demands = tuple(sorted((first, second), key=lambda item: item.demand_digest.value))
    result = CodeComposedSemanticMaterializationIntent.create(
        target_package=SemanticPackageCoordinate(
            package_ref="package:api",
            package_kind="api",
            manifest_digest=_digest("api-manifest"),
        ),
        demands=demands,
    )
    assert result.composed_intent.requested_semantic_root_refs == (
        "api.docs",
        "api.public",
    )
    assert result.composed_intent.requested_terminal_output_roles == (
        "api_contract",
        "api_docs",
    )
    assert tuple(item.role for item in result.required_result_products) == (
        "api_contract",
        "api_docs",
    )


def test_target_intent_fan_in_rejects_same_role_different_contract() -> None:
    first = _demand("sdk.api")
    foreign_contract = SemanticContractRef(
        key="aware.api.contract.v2",
        version="2",
        schema_digest=_digest("api-contract-v2"),
    )
    second = SemanticDependencyDemand.create(
        consumer_semantic_role="sdk_source",
        authored_dependency_kind="api_package",
        authored_dependency_ref="sdk.api.v2",
        target_constraints=_constraints(),
        required_result_role="api_contract",
        result_product_contract=foreign_contract,
        target_intent=CodeSemanticMaterializationIntent.create(
            operation_kind="materialize",
            requested_semantic_root_refs=("api.v2",),
            requested_terminal_output_roles=("api_contract",),
            semantic_configuration_coordinate=first.target_intent.semantic_configuration_coordinate,
        ),
        cardinality="required",
    )
    demands = tuple(sorted((first, second), key=lambda item: item.demand_digest.value))
    with pytest.raises(ContractViolation, match="result contract conflict"):
        CodeComposedSemanticMaterializationIntent.create(
            target_package=SemanticPackageCoordinate(
                package_ref="package:api",
                package_kind="api",
                manifest_digest=_digest("api-manifest"),
            ),
            demands=demands,
        )
