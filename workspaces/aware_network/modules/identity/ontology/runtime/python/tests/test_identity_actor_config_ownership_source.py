from pathlib import Path

from ._paths import IDENTITY_AWARE_ROOT, REPO_ROOT

IDENTITY_AWARE = IDENTITY_AWARE_ROOT
EXPERIENCE_AWARE = (
    REPO_ROOT / "workspaces/aware_network/modules/experience/ontology/structure/aware"
)
ENVIRONMENT_AWARE = (
    REPO_ROOT / "workspaces/aware_network/modules/environment/ontology/structure/aware"
)


def _read(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


def test_identity_owns_actor_config_policy_vocabulary() -> None:
    actor_config_source = _read(IDENTITY_AWARE, "actor/actor_config.aware")
    edge_source = _read(IDENTITY_AWARE, "actor/actor_config_role_config.aware")
    projection_source = _read(IDENTITY_AWARE, "actor_config_projection.aware")

    assert "class ActorConfig" in actor_config_source
    assert "role_configs ActorConfigRoleConfig[]" in actor_config_source
    assert "type ActorType?" in actor_config_source
    assert "fn add_role_config" in actor_config_source
    assert "class ActorConfigRoleConfig" in edge_source
    assert "role_config aware_identity.role.RoleConfig key" in edge_source
    assert "projection ActorConfig" in projection_source
    assert "root actor.ActorConfig" in projection_source
    assert "actor.ActorConfigRoleConfig::role_config RoleConfig" in projection_source


def test_experience_consumes_identity_actor_config_without_local_source() -> None:
    assert not (EXPERIENCE_AWARE / "actor/actor_config.aware").exists()
    assert not (EXPERIENCE_AWARE / "actor/actor_config_role_config.aware").exists()
    assert not (EXPERIENCE_AWARE / "actor_config_projection.aware").exists()

    environment_actor_source = _read(
        EXPERIENCE_AWARE,
        "environment/environment_experience_actor.aware",
    )
    program_actor_source = _read(
        EXPERIENCE_AWARE,
        "program/program_config_actor_config.aware",
    )
    program_role_source = _read(EXPERIENCE_AWARE, "program/program_actor_role.aware")
    contract_grant_source = _read(
        EXPERIENCE_AWARE,
        "contract/experience_contract_actor_role_grant.aware",
    )

    assert (
        "actor_config aware_identity.actor.ActorConfig key" in environment_actor_source
    )
    assert "actor_config aware_identity.actor.ActorConfig" in program_actor_source
    assert (
        "actor_config_role_config aware_identity.actor.ActorConfigRoleConfig key"
        in program_role_source
    )
    assert (
        "actor_config_role_config aware_identity.actor.ActorConfigRoleConfig key"
        in contract_grant_source
    )


def test_environment_profile_consumes_identity_actor_config() -> None:
    profile_config_source = _read(
        ENVIRONMENT_AWARE,
        "environment/environment_profile_config.aware",
    )
    edge_source = _read(
        ENVIRONMENT_AWARE,
        "environment/environment_profile_actor_config.aware",
    )
    projection_source = _read(ENVIRONMENT_AWARE, "environment_profile_projection.aware")

    assert "actor_configs EnvironmentProfileActorConfig[]" in profile_config_source
    assert "fn add_actor_config" in profile_config_source
    assert "actor_config aware_identity.actor.ActorConfig key" in edge_source
    assert "EnvironmentProfileRoleConfig" not in profile_config_source
    assert "EnvironmentProfileRoleConfig" not in projection_source
    assert (
        "environment.EnvironmentProfileActorConfig::actor_config aware_identity.ActorConfig"
        in projection_source
    )
