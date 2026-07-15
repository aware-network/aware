from __future__ import annotations

from uuid import UUID

from aware_environment_ontology.stable_ids import stable_environment_id


def environment_key_for_config(
    *,
    node_id: UUID,
    environment_config_id: UUID,
) -> str:
    """Canonical territory key for node-hosted config provisioning."""

    return f"node:{node_id}:environment_config:{environment_config_id}"


def environment_key_from_provision_seed(*, seed: UUID) -> str:
    """Canonical territory key for ad hoc bundle provisioning."""

    return f"provisioned:{seed}"


def environment_id_for_key(*, environment_key: str) -> UUID:
    """Resolve the Environment Environment object id from its territory key."""

    return stable_environment_id(key=environment_key)


def environment_id_for_config(
    *,
    node_id: UUID,
    environment_config_id: UUID,
) -> UUID:
    return environment_id_for_key(
        environment_key=environment_key_for_config(
            node_id=node_id,
            environment_config_id=environment_config_id,
        )
    )


__all__ = [
    "environment_id_for_config",
    "environment_id_for_key",
    "environment_key_for_config",
    "environment_key_from_provision_seed",
]
