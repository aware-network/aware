"""Portable projections close source planning inputs without issuing authority."""

import json
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    CodePortableSemanticContract,
    CodeSemanticDeclarationTarget,
    CodeSemanticDeclarationTargetInventory,
    CodeSemanticPackageContextInput,
    CodeSemanticRegistryPackageInput,
    ContentDigest,
    ContractViolation,
    DeclarationTargetInventoryCodec,
    DependencyPlanningInputCodec,
    PackageContextInputCodec,
    ProviderExecutionBinding,
    RegistryPackageInputCodec,
    SemanticConfigurationCoordinate,
    SemanticDependencyTargetConstraint,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    retained_projection_body,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
    SemanticDependencyTarget,
)

D = ContentDigest.of_bytes(b"earlier observation")
P = SemanticPackageCoordinate("package:home-environment@0.1", "environment", D)
T = SemanticDependencyTarget(
    SemanticPackageCoordinate("package:home-ontology@1", "ontology", D),
    ("ontology:home",),
)
B = ProviderExecutionBinding(
    "environment",
    SemanticImplementationCoordinate("impl:environment", D),
    SemanticConfigurationCoordinate("config:environment", D),
)


def registry():
    return CodeSemanticRegistryPackageInput(
        "aware_environment_toml",
        "aware.environment.toml",
        "environment",
        "environment",
        "environment_config_package",
        CodePortableSemanticContract(
            "environment", "environment", "environment", "contract:environment"
        ),
        ("aware",),
        "environment",
        "home",
        ("environment:home",),
        "profile:environment",
        "1",
        D,
        B,
    )


def context():
    return CodeSemanticPackageContextInput(
        P, D, "aware.environment.toml", "home", "0.1", None, None, None
    )


def inventory():
    return CodeSemanticDeclarationTargetInventory(
        P, D, (CodeSemanticDeclarationTarget("module", "home", (T,)),)
    )


def planning():
    return SemanticDependencyPlanningInput(
        P, D, (SemanticAuthoredDependency("module", "home", (T,)),)
    )


CASES = [
    (registry, RegistryPackageInputCodec),
    (context, PackageContextInputCodec),
    (inventory, DeclarationTargetInventoryCodec),
    (planning, DependencyPlanningInputCodec),
]


@pytest.mark.parametrize("factory,codec_type", CASES)
def test_roundtrip_exact_contract_and_body(factory, codec_type):
    value, codec = factory(), codec_type()
    wire = codec.encode(value)
    assert codec.decode(wire) == value
    assert codec.encode(codec.decode(wire)) == wire
    body = retained_projection_body(value)
    assert body.coordinate.contract == codec.contract
    assert body.canonical_body == wire
    assert "issuer" not in json.loads(wire)
    for bad in (
        wire + b"\n",
        b"\xef\xbb\xbf" + wire,
        wire.replace(b"{", b'{"root":"/tmp",', 1),
        wire.replace(b'"contract":', b'"contract":"duplicate","contract":', 1),
    ):
        with pytest.raises((ValueError, TypeError)):
            codec.decode(bad)
    with pytest.raises((ValueError, TypeError)):
        codec.encode({})
    with pytest.raises((ValueError, TypeError)):
        codec.decode(b" " * 8_388_609)


def test_provider_profile_and_explicit_context_fields():
    with pytest.raises(ContractViolation):
        replace(registry(), semantic_provider_key="other")
    with pytest.raises((ValueError, TypeError)):
        replace(registry(), profile_digest=D.value)
    with pytest.raises((ValueError, TypeError)):
        replace(registry(), manifest_filename="sub/aware.environment.toml")
    with pytest.raises((ValueError, TypeError)):
        replace(context(), manifest_relative_path="../aware.environment.toml")
    for field, value in (
        ("semantic_version", True),
        ("semantic_version", "bad/version"),
        ("code_package_name", "bad/name"),
        ("config_id", "invented"),
    ):
        with pytest.raises((ValueError, TypeError)):
            replace(context(), **{field: value})
    # These values are portable, so mismatching independent source contexts can exist.
    assert (
        replace(
            context(), source_identity_digest=ContentDigest.of_bytes(b"other")
        ).source_identity_digest
        != D
    )


def test_inventory_available_choices_and_exact_targets():
    extra = CodeSemanticDeclarationTarget("module", "other", (T,))
    inv = replace(inventory(), entries=inventory().entries + (extra,))
    assert len(inv.entries) == 2
    assert len(planning().dependencies) == 1
    with pytest.raises((ValueError, TypeError)):
        replace(inv, entries=(extra, inv.entries[0]))
    with pytest.raises((ValueError, TypeError)):
        replace(inv, entries=(extra, extra))
    with pytest.raises((ValueError, TypeError)):
        replace(inv.entries[0], targets=(T, T))
    constraint = SemanticDependencyTargetConstraint.create(
        constraint_kind="package_kind", constraint_value="ontology"
    )
    dep = replace(planning().dependencies[0], target_constraints=(constraint,))
    plan = replace(planning(), dependencies=(dep,))
    codec = DependencyPlanningInputCodec()
    assert codec.decode(codec.encode(plan)) == plan


def test_text_tuple_and_nested_bounds():
    with pytest.raises((ValueError, TypeError)):
        replace(registry(), profile_ref="x" * 4097)
    with pytest.raises((ValueError, TypeError)):
        replace(
            registry(),
            binding=replace(
                B, implementation=SemanticImplementationCoordinate("x" * 4097, D)
            ),
        )
    with pytest.raises((ValueError, TypeError)):
        replace(inventory(), entries=inventory().entries * 16385)
    with pytest.raises((ValueError, TypeError)):
        replace(
            inventory().entries[0],
            target_constraints=(
                SemanticDependencyTargetConstraint.create(
                    constraint_kind="package_kind", constraint_value="ontology"
                ),
            )
            * 16385,
        )
    assert replace(context(), config_key="x" * 4096).config_key == "x" * 4096


@pytest.mark.parametrize("factory,codec_type", CASES)
def test_mutation_revalidated_at_encode(factory, codec_type):
    value = factory()
    field = (
        "source_identity_digest"
        if hasattr(value, "source_identity_digest")
        else "profile_digest"
    )
    object.__setattr__(value, field, "forged")
    with pytest.raises((ValueError, TypeError, AttributeError)):
        codec_type().encode(value)
