"""Stage derivation over original Code resources; fixture bootstrap, no admission."""

from dataclasses import fields, replace

import pytest
import test_operation_context as planning
import test_stage_policy_binding as policy_fixture
import test_stage_runtime_retention as stage_fixture
from aware_code_retained_registry_policy_runtime import direct_host as hosts
from aware_code_retained_registry_policy_runtime import operation_context as contexts
from aware_code_retained_registry_policy_runtime.operation_derivation import (
    _derive_stage,
)
from aware_code_semantic_contract_runtime import selected_provider
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    RegistryPackageInputCodec,
    retained_projection_body,
)


@pytest.fixture
def paired(monkeypatch):
    original_binding = stage_fixture._binding

    def full_binding(*, provider_key, profile_ref):
        base = original_binding(provider_key=provider_key, profile_ref=profile_ref)
        profile = planning.planning_profile()
        profile = replace(
            profile,
            profile_ref=profile_ref,
            providers=tuple(
                replace(p, provider_key=provider_key) for p in profile.providers
            ),
            steps=tuple(replace(s, provider_key=provider_key) for s in profile.steps),
        )
        values = {
            f.name: getattr(base, f.name)
            for f in fields(base)
            if f.name != "binding_digest"
        }
        values["profile_declaration"] = profile
        return CodeSemanticMaterializationProfileBinding.create(**values)

    monkeypatch.setattr(stage_fixture, "_binding", full_binding)
    case = stage_fixture.case.__wrapped__()
    generator = policy_fixture.joined.__wrapped__(case)
    owner, host, policy, _, _ = next(generator)
    baseline = planning.setup()
    request = baseline[-1]
    hosts.close_direct_validation_host(baseline[1])
    registry = RegistryPackageInputCodec().decode(
        request.registry_package.canonical_body
    )
    registry = replace(
        registry,
        semantic_provider_key="stage_retention_test",
        binding=stage_fixture._BINDING,
        semantic_contract=replace(
            registry.semantic_contract, provider_key="stage_retention_test"
        ),
    )

    def proposed(stage):
        original = next(
            s for s in owner.expected.stage_runtime_bindings if s.stage == stage
        )
        profile = original.runtime.profile
        value = replace(
            registry,
            profile_ref=profile.profile_ref,
            profile_version=profile.version,
            profile_digest=profile.digest,
            binding=stage_fixture._BINDING,
        )
        return original, replace(
            request, registry_package=retained_projection_body(value)
        )

    try:
        yield owner, host, policy, proposed, case[2]
    finally:
        generator.close()
        for stage in owner.expected.stage_runtime_bindings:
            try:
                selected_provider.close_selected_provider_registration(
                    stage.runtime, stage.registration
                )
            except ContractViolation as exc:
                if str(exc) != "provider registration is closed":
                    raise


@pytest.mark.parametrize("stage", ["source_planning", "authority_derivation"])
def test_exact_stage_derivation_preserves_identity_without_admission(paired, stage):
    owner, host, policy, proposed, providers = paired
    selected, request = proposed(stage)
    operation = object()
    expected = _derive_stage(
        host, policy, selected.registration, request, operation, stage=stage
    )
    assert expected.runtime is selected.runtime
    assert expected.selected_provider_registration is selected.registration
    assert expected.generation_identity is owner.expected.epoch_identity
    assert expected.operation_identity is operation
    assert expected.stage == stage
    assert all(p.calls == 0 for p in providers)
    with pytest.raises(TypeError):
        contexts.source_planning_expectation(host, expected)


def test_planning_registration_cannot_stand_in_for_authority(paired):
    _, host, policy, proposed, _ = paired
    planning_stage, _ = proposed("source_planning")
    _, request = proposed("authority_derivation")
    with pytest.raises(ContractViolation, match="original stage registration"):
        _derive_stage(
            host,
            policy,
            planning_stage.registration,
            request,
            object(),
            stage="authority_derivation",
        )


def test_planning_registry_cannot_be_restamped_as_authority(paired):
    _, host, policy, proposed, _ = paired
    selected, _ = proposed("authority_derivation")
    _, request = proposed("source_planning")
    with pytest.raises(ContractViolation, match="registry request differs"):
        _derive_stage(
            host,
            policy,
            selected.registration,
            request,
            object(),
            stage="authority_derivation",
        )


def test_closed_authority_registration_refuses(paired):
    _, host, policy, proposed, _ = paired
    selected, request = proposed("authority_derivation")
    selected_provider.close_selected_provider_registration(
        selected.runtime, selected.registration
    )
    with pytest.raises(ContractViolation):
        _derive_stage(
            host,
            policy,
            selected.registration,
            request,
            object(),
            stage="authority_derivation",
        )


def test_source_only_host_has_no_authority_derivation():
    _, host, policy, _, registration, request = planning.setup()
    try:
        with pytest.raises(
            ContractViolation, match="authority stage retention required"
        ):
            _derive_stage(
                host,
                policy,
                registration,
                request,
                object(),
                stage="authority_derivation",
            )
    finally:
        hosts.close_direct_validation_host(host)
