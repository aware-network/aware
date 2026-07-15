from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.environment.environment_config_ontology_config import EnvironmentConfigOntologyConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_environment_config_ontology_config_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_config(
    environment_config_id: UUID,
    name: str,
    fqn_prefix: str,
    ontology_config_object_instance_graph_commit_id: UUID | None = None,
) -> EnvironmentConfigOntologyConfig:
    """
    Create a deterministic EnvironmentConfig-owned edge to one OntologyConfig.

    Contract:
    - Parent `EnvironmentConfig` scope is injected by propagation.
    - Target OntologyConfig identity is resolved from `(name, fqn_prefix)`.
    - OCG authority remains on `OntologyConfig.object_config_graph`.
    - The optional commit pin lets runtime replay exact ontology config truth
      without reopening source manifests.
    """

    # --- AWARE: LOGIC START build_via_environment_config
    from aware_ontology_ontology.stable_ids import (
        stable_ontology_config_id,
    )  # noqa: WPS433

    normalized_name = (name or "").strip()
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_name:
        raise RuntimeError("EnvironmentConfigOntologyConfig.build_via_environment_config " "requires non-empty name")
    if not normalized_fqn_prefix:
        raise RuntimeError(
            "EnvironmentConfigOntologyConfig.build_via_environment_config " "requires non-empty fqn_prefix"
        )

    association_id = stable_environment_config_ontology_config_id(
        environment_config_id=environment_config_id,
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )
    target_config_id = stable_ontology_config_id(
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )

    session = current_handler_session()
    existing = session.imap_get(EnvironmentConfigOntologyConfig, association_id)
    if existing is not None:
        if (
            existing.environment_config_id != environment_config_id
            or existing.ontology_config_id != target_config_id
            or (existing.name or "").strip() != normalized_name
            or (existing.fqn_prefix or "").strip() != normalized_fqn_prefix
        ):
            raise RuntimeError(
                "EnvironmentConfigOntologyConfig.build_via_environment_config "
                "payload mismatch for existing membership: "
                f"environment_config_ontology_config_id={association_id}"
            )
        if (
            ontology_config_object_instance_graph_commit_id is not None
            and existing.ontology_config_object_instance_graph_commit_id
            not in {None, ontology_config_object_instance_graph_commit_id}
        ):
            raise RuntimeError(
                "EnvironmentConfigOntologyConfig.build_via_environment_config "
                "OntologyConfig commit mismatch for existing membership: "
                f"membership_id={association_id} "
                f"existing={existing.ontology_config_object_instance_graph_commit_id} "
                f"provided={ontology_config_object_instance_graph_commit_id}"
            )
        if ontology_config_object_instance_graph_commit_id is not None:
            existing.ontology_config_object_instance_graph_commit_id = ontology_config_object_instance_graph_commit_id
            existing.ontology_config_object_instance_graph_commit = None
        existing.ontology_config = None
        return existing

    return EnvironmentConfigOntologyConfig(
        id=association_id,
        environment_config_id=environment_config_id,
        ontology_config=None,
        ontology_config_id=target_config_id,
        ontology_config_object_instance_graph_commit=None,
        ontology_config_object_instance_graph_commit_id=(ontology_config_object_instance_graph_commit_id),
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )
    # --- AWARE: LOGIC END build_via_environment_config
