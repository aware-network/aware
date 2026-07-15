from __future__ import annotations

from pathlib import Path

from aware_experience.package_projection_ownership import (
    resolve_experience_package_projection_ownership_catalog,
)


def _repo_root() -> Path:
    for path in Path(__file__).resolve().parents:
        if (path / "workspaces/aware_kernel/aware.workspace.toml").is_file():
            return path
    raise RuntimeError("Aware repo root not found")


def test_aware_control_program_port_projection_refs_are_experience_owned() -> None:
    repo_root = _repo_root()

    catalog = resolve_experience_package_projection_ownership_catalog(
        workspace_root=repo_root,
        experience_toml_path=(
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "interface"
            / "experiences"
            / "aware_control"
            / "aware.experience.toml"
        ),
    )

    entries = {entry.experience_name: entry for entry in catalog.entries}
    assert catalog.status == "resolved"
    assert catalog.missing_required_projection_refs == []
    assert {
        "interface",
        "window",
    }.issubset(entries)

    expected_port_keys = {
        "interface": "interface_interface_id",
        "window": "window_window_id",
    }
    for experience_name, port_key in expected_port_keys.items():
        assert any(
            consumer.kind == "program_port"
            and consumer.program_name == "EnsureBootInterfaceGraph"
            and consumer.port_key == port_key
            for consumer in entries[experience_name].consumers
        )


def test_identity_default_program_port_projection_refs_are_experience_owned() -> None:
    repo_root = _repo_root()

    catalog = resolve_experience_package_projection_ownership_catalog(
        workspace_root=repo_root,
        experience_toml_path=(
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "identity"
            / "experiences"
            / "aware_identity"
            / "aware.experience.toml"
        ),
    )

    entries = {entry.experience_name: entry for entry in catalog.entries}
    assert catalog.status == "resolved"
    assert catalog.missing_required_projection_refs == []
    assert {
        "actor_role",
        "actor_subscription",
        "event_config_condition_config_scope",
        "identity",
        "organization",
        "role",
        "role_config",
    }.issubset(entries)

    expected_program_ports = {
        "actor_role": {
            "EnsureActorActReactBindingFromBranch_v1",
            "EnsureActorRoleBindingFromBranch_v1",
            "EnsureActorRoleBinding_v1",
        },
        "actor_subscription": {
            "EnsureActorActReactBindingFromBranch_v1",
            "EnsureActorSubscriptionBindingFromBranch_v1",
            "EnsureActorSubscriptionBinding_v1",
        },
        "role": {
            "EnsureActorActReactBindingFromBranch_v1",
            "EnsureActorRoleBindingFromBranch_v1",
            "EnsureActorRoleBinding_v1",
        },
    }
    for experience_name, program_names in expected_program_ports.items():
        actual_program_names = {
            consumer.program_name
            for consumer in entries[experience_name].consumers
            if consumer.kind == "program_port"
        }
        assert program_names.issubset(actual_program_names)
