"""Both stages through qualified host and actual selected-provider registrations."""

import pytest
import test_stage_context_derivation as paired_fixture
import test_stage_policy_binding as policy_fixture
from aware_code_retained_registry_policy_runtime.operation_derivation import (
    _derive_stage,
)
from aware_code_retained_registry_policy_runtime.stage_policy_binding import (
    validate_stage_policy_occurrence,
)
from aware_code_semantic_contract_runtime import selected_provider
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    PackageContextInputCodec,
)
from test_direct_epoch_tracking import Owner
from test_qualified_host import upgrade


@pytest.fixture
def paired(monkeypatch):
    monkeypatch.setattr(policy_fixture, "StageOwner", Owner)
    upgrade(monkeypatch, stages_only=True, provider_key="stage_retention_test")
    generator = paired_fixture.paired.__wrapped__(monkeypatch)
    try:
        yield next(generator)
    finally:
        generator.close()


@pytest.mark.parametrize("stage", ["source_planning", "authority_derivation"])
def test_qualified_stage_uses_original_imported_registration(paired, stage):
    owner, host, policy, proposed, providers = paired
    selected, request = proposed(stage)
    operation = object()
    result = _derive_stage(
        host, policy, selected.registration, request, operation, stage=stage
    )
    assert result.runtime is selected.runtime
    assert result.selected_provider_registration is selected.registration
    assert result.operation_identity is operation
    assert result.stage == stage
    assert all(p.calls == 0 for p in providers)
    assert not owner.source.active
    # Includes one imported provider edge, so the lookup cannot be local-only.
    assert len(owner.source.closure.edges) == 1


def test_qualified_authority_policy_preserves_both_live_stages(paired):
    owner, host, policy, proposed, _ = paired
    _, request = proposed("authority_derivation")
    source = (
        PackageContextInputCodec()
        .decode(request.package_context.canonical_body)
        .source_identity_digest
    )
    validate_stage_policy_occurrence(host, policy, source)
    assert not owner.source.active


def test_qualified_authority_rejects_planning_registration(paired):
    _, host, policy, proposed, _ = paired
    selected, _ = proposed("source_planning")
    _, request = proposed("authority_derivation")
    with pytest.raises(ContractViolation, match="original stage registration"):
        _derive_stage(
            host,
            policy,
            selected.registration,
            request,
            object(),
            stage="authority_derivation",
        )


def test_qualified_revoked_authority_registration_rejects(paired):
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


@pytest.mark.parametrize("stage", ["source_planning", "authority_derivation"])
def test_changed_profile_body_rejects_both_stages(paired, stage):
    from dataclasses import replace

    from aware_code_semantic_contract_runtime.contracts import ContentDigest

    owner, host, policy, proposed, providers = paired
    selected, request = proposed(stage)
    closure = owner.source.closure
    association = closure.profile_associations[0]
    raw = association.manifest.body + b"\n# changed retained profile bytes\n"
    association = replace(
        association,
        manifest=replace(
            association.manifest, body=raw, content_digest=ContentDigest.of_bytes(raw)
        ),
    )
    owner.source.closure = replace(closure, profile_associations=(association,))
    with pytest.raises(ContractViolation):
        _derive_stage(
            host, policy, selected.registration, request, object(), stage=stage
        )
    assert all(p.calls == 0 for p in providers)
    assert not owner.source.active


def test_qualified_authority_refuses_planning_profile_input(paired):
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
