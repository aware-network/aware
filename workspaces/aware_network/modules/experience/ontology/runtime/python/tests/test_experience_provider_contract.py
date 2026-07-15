from __future__ import annotations

from ._experience_runtime_test_paths import (
    EXPERIENCE_AWARE_ROOT,
    EXPERIENCE_ONTOLOGY_STRUCTURE_ROOT,
)


_EXPERIENCE_ROOT = EXPERIENCE_ONTOLOGY_STRUCTURE_ROOT
_AWARE_ROOT = EXPERIENCE_AWARE_ROOT


def _read(relative_path: str) -> str:
    return (_AWARE_ROOT / relative_path).read_text(encoding="utf-8")


def test_experience_provider_slice_does_not_depend_on_provider_ontology() -> None:
    manifest = (_EXPERIENCE_ROOT / "aware.toml").read_text(encoding="utf-8")

    assert 'package_name = "service-ontology"' not in manifest

    for relative_path in (
        "projection/projection_experience.aware",
        "provider/experience_provider.aware",
        "provider/experience_provider_action_binding.aware",
        "contract/experience_contract_actor_role_grant.aware",
    ):
        assert "aware_service" not in _read(relative_path)
        assert "Service" not in _read(relative_path)
        assert "service" not in _read(relative_path)


def test_projection_experience_owns_public_provider_and_grant_rails() -> None:
    source = _read("projection/projection_experience.aware")

    assert "providers provider.ExperienceProvider[]" in source
    assert (
        "contract_actor_role_grants contract.ExperienceContractActorRoleGrant[]"
        in source
    )
    assert "fn create_provider" in source
    assert "fn create_contract_actor_role_grant" in source


def test_provider_binds_experience_actions_without_provider_operation_truth() -> None:
    provider_source = _read("provider/experience_provider.aware")
    action_source = _read("provider/experience_provider_action_binding.aware")

    assert "action_bindings ExperienceProviderActionBinding[]" in provider_source
    assert "fn bind_action" in provider_source
    assert (
        "experience_invocation_action_config "
        "invocation.ExperienceInvocationActionConfig key"
    ) in action_source
    assert "service_operation_config" not in action_source
    assert "service_contract_config" not in action_source
    assert "operation_config" not in action_source
    assert "contract_config" not in action_source


def test_experience_contract_actor_role_grant_is_actor_config_scoped() -> None:
    source = _read("contract/experience_contract_actor_role_grant.aware")

    assert (
        "actor_config_role_config aware_identity.actor.ActorConfigRoleConfig key"
        in source
    )
    assert "role_config aware_identity.role.RoleConfig key" in source
    assert "grant_key String key" in source
    assert "RoleConfig eligibility" in source
