from __future__ import annotations

import json
from typing import TypedDict

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
    decode_code_semantic_materialization_intent,
    decode_semantic_dependency_demand_set,
    encode_code_semantic_materialization_intent,
    encode_code_composed_semantic_materialization_intent,
    encode_semantic_dependency_demand_set,
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
        semantic_configuration_coordinate=None,
    )


def _demand_set(
    package: SemanticPackageCoordinate | None = None,
) -> SemanticDependencyDemandSet:
    provider = SemanticDependencyTargetConstraint.create(
        constraint_kind="semantic_provider_key", constraint_value="aware.api.sdk"
    )
    result_contract = SemanticContractRef(
        key="aware.api.contract",
        version="1",
        schema_digest=_digest("contract"),
    )
    demand = SemanticDependencyDemand.create(
        consumer_semantic_role="sdk_source",
        authored_dependency_kind="api_package",
        authored_dependency_ref="sdk.api",
        target_constraints=(provider,),
        required_result_role="api_contract",
        result_product_contract=result_contract,
        target_intent=CodeSemanticMaterializationIntent.create(
            operation_kind="materialize",
            requested_semantic_root_refs=("api.public",),
            requested_terminal_output_roles=("api_contract",),
            semantic_configuration_coordinate=None,
        ),
        cardinality="required",
    )
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
        demands=(demand,),
    )


class _DemandContext(TypedDict):
    package: SemanticPackageCoordinate
    intent: CodeSemanticMaterializationIntent
    profile_ref: str
    profile_digest: ContentDigest
    contract_profile_binding_digest: ContentDigest
    planner_implementation_ref: str
    planner_implementation_digest: ContentDigest
    planner_configuration: SemanticConfigurationCoordinate


def _context(package: SemanticPackageCoordinate | None = None) -> _DemandContext:
    return {
        "package": package or _package(),
        "intent": _intent(),
        "profile_ref": "sdk.materialization",
        "profile_digest": _digest("profile"),
        "contract_profile_binding_digest": _digest("profile-binding"),
        "planner_implementation_ref": "sdk.dependency-planner",
        "planner_implementation_digest": _digest("planner"),
        "planner_configuration": SemanticConfigurationCoordinate(
            configuration_ref="sdk.dependency-planner",
            digest=_digest("planner-configuration"),
        ),
    }


def test_intent_and_contextual_demand_set_round_trip_byte_exact() -> None:
    intent = _intent()
    intent_wire = encode_code_semantic_materialization_intent(intent)
    assert decode_code_semantic_materialization_intent(intent_wire) == intent

    value = _demand_set()
    context = _context()
    wire = encode_semantic_dependency_demand_set(value, **context)  # type: ignore[arg-type]
    assert (
        decode_semantic_dependency_demand_set(
            wire,
            **context,  # type: ignore[arg-type]
        )
        == value
    )


def test_cross_package_and_manifest_context_substitution_fail() -> None:
    value = _demand_set()
    context = _context()

    for foreign in (
        SemanticPackageCoordinate(
            package_ref="package:other",
            package_kind="sdk",
            manifest_digest=_digest("manifest-v1"),
        ),
        _package("manifest-v2"),
    ):
        foreign_context: _DemandContext = {**context, "package": foreign}
        with pytest.raises(ContractViolation, match="planning context"):
            encode_semantic_dependency_demand_set(
                value,
                **foreign_context,  # type: ignore[arg-type]
            )

        wire = encode_semantic_dependency_demand_set(
            value,
            **context,  # type: ignore[arg-type]
        )
        with pytest.raises(ContractViolation, match="planning context"):
            decode_semantic_dependency_demand_set(
                wire,
                **foreign_context,  # type: ignore[arg-type]
            )


def test_provider_and_authored_identity_substitution_fail_with_retained_digest() -> (
    None
):
    value = _demand_set()
    context = _context()
    wire = encode_semantic_dependency_demand_set(
        value,
        **context,  # type: ignore[arg-type]
    )
    payload = json.loads(wire)
    constraint = payload["demands"][0]["target_constraints"][0]
    constraint["constraint_value"] = "unknown.provider"
    poisoned = canonical_json_bytes(payload)
    with pytest.raises(ContractViolation):
        decode_semantic_dependency_demand_set(
            poisoned,
            **context,  # type: ignore[arg-type]
        )

    payload = json.loads(wire)
    payload["demands"][0]["authored_dependency_ref"] = "sdk.other"
    poisoned = canonical_json_bytes(payload)
    with pytest.raises(ContractViolation):
        decode_semantic_dependency_demand_set(
            poisoned,
            **context,  # type: ignore[arg-type]
        )


def test_noncanonical_and_unknown_constraint_wire_fail() -> None:
    context = _context()
    wire = encode_semantic_dependency_demand_set(
        _demand_set(),
        **context,  # type: ignore[arg-type]
    )
    with pytest.raises(ContractViolation, match="not canonical"):
        decode_semantic_dependency_demand_set(
            wire + b"\n",
            **context,  # type: ignore[arg-type]
        )

    payload = json.loads(wire)
    payload["demands"][0]["target_constraints"][0]["constraint_kind"] = (
        "implementation_ref"
    )
    with pytest.raises(ContractViolation, match="kind unsupported"):
        decode_semantic_dependency_demand_set(
            canonical_json_bytes(payload),
            **context,  # type: ignore[arg-type]
        )


def test_decode_rejects_wrong_exact_scalar_types() -> None:
    wire = encode_code_semantic_materialization_intent(_intent())
    payload = json.loads(wire)
    payload["operation_kind"] = True
    with pytest.raises(TypeError, match="token text"):
        decode_code_semantic_materialization_intent(canonical_json_bytes(payload))


def test_composed_encoder_preflights_before_foreign_nested_equality() -> None:
    calls: list[str] = []

    class ForeignIntent(CodeSemanticMaterializationIntent):
        def __eq__(self, other: object) -> bool:
            del other
            calls.append("foreign-equality")
            return False

    demands = _demand_set().demands
    target = SemanticPackageCoordinate(
        package_ref="package:api",
        package_kind="api",
        manifest_digest=_digest("api-manifest"),
    )
    expected = CodeComposedSemanticMaterializationIntent.create(
        target_package=target, demands=demands
    )
    intent = expected.composed_intent
    foreign_intent = ForeignIntent(
        operation_kind=intent.operation_kind,
        requested_semantic_root_refs=intent.requested_semantic_root_refs,
        requested_terminal_output_roles=intent.requested_terminal_output_roles,
        semantic_configuration_coordinate=intent.semantic_configuration_coordinate,
        intent_digest=intent.intent_digest,
    )
    poisoned = object.__new__(CodeComposedSemanticMaterializationIntent)
    for name, value in (
        ("target_package", expected.target_package),
        ("contributing_demand_digests", expected.contributing_demand_digests),
        ("contributing_intent_digests", expected.contributing_intent_digests),
        ("composed_intent", foreign_intent),
        ("required_result_products", expected.required_result_products),
        ("composition_digest", expected.composition_digest),
    ):
        object.__setattr__(poisoned, name, value)
    with pytest.raises(TypeError, match="composition intent must be exact"):
        encode_code_composed_semantic_materialization_intent(
            poisoned, target_package=target, demands=demands
        )
    assert calls == []
