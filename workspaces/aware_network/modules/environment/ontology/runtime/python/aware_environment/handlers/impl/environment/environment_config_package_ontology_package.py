from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.environment.environment_config_package_ontology_package import (
    EnvironmentConfigPackageOntologyPackage,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_environment_ontology.stable_ids import (
    stable_environment_config_package_ontology_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_config_package(
    environment_config_package_id: UUID,
    name: str,
    fqn_prefix: str,
    ontology_package_object_instance_graph_commit_id: UUID | None = None,
) -> EnvironmentConfigPackageOntologyPackage:
    """
    Create a deterministic environment-owned membership edge to one
    Ontology-owned `OntologyPackage`.

    Contract:
    - Parent `EnvironmentConfigPackage` scope is injected by propagation.
    - Target package identity is resolved from `(name, fqn_prefix)`.
    - `ontology_package_object_instance_graph_commit_id` pins the exact
      OntologyPackage semantic package commit when available.
    - Raw OCG package refs are reached through
      `OntologyPackage.object_config_graph_package`, not duplicated here.
    """

    # --- AWARE: LOGIC START build_via_environment_config_package
    from aware_ontology_ontology.stable_ids import (
        stable_ontology_package_id,
    )  # noqa: WPS433

    normalized_name = (name or "").strip()
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_name:
        raise RuntimeError(
            "EnvironmentConfigPackageOntologyPackage.build_via_environment_config_package " "requires non-empty name"
        )
    if not normalized_fqn_prefix:
        raise RuntimeError(
            "EnvironmentConfigPackageOntologyPackage.build_via_environment_config_package "
            "requires non-empty fqn_prefix"
        )

    association_id = stable_environment_config_package_ontology_package_id(
        environment_config_package_id=environment_config_package_id,
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )
    target_package_id = stable_ontology_package_id(
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )

    session = current_handler_session()
    existing = session.imap_get(
        EnvironmentConfigPackageOntologyPackage,
        association_id,
    )
    if existing is not None:
        if (
            existing.environment_config_package_id != environment_config_package_id
            or existing.ontology_package_id != target_package_id
            or (existing.name or "").strip() != normalized_name
            or (existing.fqn_prefix or "").strip() != normalized_fqn_prefix
        ):
            raise RuntimeError(
                "EnvironmentConfigPackageOntologyPackage.build_via_environment_config_package "
                "payload mismatch for existing membership: "
                f"environment_config_package_ontology_package_id={association_id}"
            )
        if (
            ontology_package_object_instance_graph_commit_id is not None
            and existing.ontology_package_object_instance_graph_commit_id
            not in {None, ontology_package_object_instance_graph_commit_id}
        ):
            raise RuntimeError(
                "EnvironmentConfigPackageOntologyPackage.build_via_environment_config_package "
                "OntologyPackage commit mismatch for existing membership: "
                f"membership_id={association_id} "
                f"existing={existing.ontology_package_object_instance_graph_commit_id} "
                f"provided={ontology_package_object_instance_graph_commit_id}"
            )
        if ontology_package_object_instance_graph_commit_id is not None:
            existing.ontology_package_object_instance_graph_commit_id = ontology_package_object_instance_graph_commit_id
            existing.ontology_package_object_instance_graph_commit = None
        existing.ontology_package = None
        return existing

    return EnvironmentConfigPackageOntologyPackage(
        id=association_id,
        environment_config_package_id=environment_config_package_id,
        ontology_package=None,
        ontology_package_id=target_package_id,
        ontology_package_object_instance_graph_commit=None,
        ontology_package_object_instance_graph_commit_id=(ontology_package_object_instance_graph_commit_id),
        name=normalized_name,
        fqn_prefix=normalized_fqn_prefix,
    )
    # --- AWARE: LOGIC END build_via_environment_config_package
