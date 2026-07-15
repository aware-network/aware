from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.environment.environment_config_package import EnvironmentConfigPackage
from aware_environment_ontology.environment.environment_config_package_dependency import (
    EnvironmentConfigPackageDependency,
)
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
    stable_environment_config_id,
    stable_environment_config_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build(
    handle: str, environment_config_id: UUID, environment_config_object_instance_graph_commit_id: UUID | None = None
) -> EnvironmentConfigPackage:
    """
    Create the canonical environment-owned semantic aggregate package.

    Contract:
    - Identity is keyed by the environment `handle`.
    - `EnvironmentConfigPackage` is the package/public root over an existing
      canonical `EnvironmentConfig` portal target.
    - `environment_config_id` must point at the canonical EnvironmentConfig
      stable id for the same handle.
    - `environment_config_object_instance_graph_commit_id` pins the historical
      ObjectInstanceGraphCommit for the semantic EnvironmentConfig root so
      WorkspaceRevision consumers can replay exact environment truth without
      resolving branch head.
    - Repository/layout ownership remains outside this aggregate package.
    - ObjectConfigGraph resolution is only reachable through
      EnvironmentConfig -> OntologyConfig and OntologyPackage ->
      OntologyConfig.
    """

    # --- AWARE: LOGIC START build
    normalized_handle = (handle or "").strip()
    if not normalized_handle:
        raise RuntimeError("EnvironmentConfigPackage.build requires non-empty handle")

    package_id = stable_environment_config_package_id(handle=normalized_handle)
    expected_environment_config_id = stable_environment_config_id(
        handle=normalized_handle,
    )
    if environment_config_id != expected_environment_config_id:
        raise RuntimeError(
            "EnvironmentConfigPackage.build environment_config_id does not match the canonical "
            f"EnvironmentConfig stable id for handle={normalized_handle!r}: "
            f"provided={environment_config_id} expected={expected_environment_config_id}"
        )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None
    if session is not None:
        existing = session.imap_get(EnvironmentConfigPackage, package_id)
        if existing is not None:
            if (
                existing.environment_config_id != expected_environment_config_id
                or (existing.handle or "").strip() != normalized_handle
            ):
                raise RuntimeError(
                    "EnvironmentConfigPackage.build payload mismatch for existing package: "
                    f"environment_config_package_id={package_id}"
                )
            existing_commit_id = existing.environment_config_object_instance_graph_commit_id
            if environment_config_object_instance_graph_commit_id is not None:
                if existing_commit_id is None:
                    existing.environment_config_object_instance_graph_commit_id = (
                        environment_config_object_instance_graph_commit_id
                    )
                    existing.environment_config_object_instance_graph_commit = None
                elif existing_commit_id != environment_config_object_instance_graph_commit_id:
                    raise RuntimeError(
                        "EnvironmentConfigPackage.build "
                        "environment_config_object_instance_graph_commit_id mismatch "
                        "for existing package: "
                        f"environment_config_package_id={package_id} "
                        f"existing={existing_commit_id} "
                        f"provided={environment_config_object_instance_graph_commit_id}"
                    )
            return existing

    return EnvironmentConfigPackage.model_construct(
        id=package_id,
        handle=normalized_handle,
        environment_config_id=expected_environment_config_id,
        environment_config_object_instance_graph_commit=None,
        environment_config_object_instance_graph_commit_id=(environment_config_object_instance_graph_commit_id),
        ontology_packages=[],
        dependencies=[],
    )
    # --- AWARE: LOGIC END build


async def attach_ontology_package(
    environment_config_package: EnvironmentConfigPackage,
    name: str,
    fqn_prefix: str,
    ontology_package_object_instance_graph_commit_id: UUID | None = None,
) -> EnvironmentConfigPackageOntologyPackage:
    """
    Attach one Ontology-owned package under this environment aggregate.

    Contract:
    - Parent `EnvironmentConfigPackage` scope is injected by propagation.
    - Target ontology package identity is resolved deterministically from
      `(name, fqn_prefix)`.
    - The optional OIG commit pin is exact ontology package replay truth.
    - This is the semantic ownership rail. Raw `ObjectConfigGraphPackage`
      membership is not owned by EnvironmentConfigPackage.
    """

    # --- AWARE: LOGIC START attach_ontology_package
    created = await EnvironmentConfigPackageOntologyPackage.build_via_environment_config_package(
        environment_config_package_id=environment_config_package.id,
        name=name,
        fqn_prefix=fqn_prefix,
        ontology_package_object_instance_graph_commit_id=(ontology_package_object_instance_graph_commit_id),
    )
    for existing in environment_config_package.ontology_packages:
        if existing.id == created.id:
            return existing
    environment_config_package.ontology_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_ontology_package


async def attach_dependency(
    environment_config_package: EnvironmentConfigPackage,
    dependency_role: str,
    dependency_index: int,
    target_handle: str,
    target_environment_config_package_id: UUID,
    target_environment_config_package_object_instance_graph_commit_id: UUID,
) -> EnvironmentConfigPackageDependency:
    """
    Attach one direct EnvironmentConfigPackage dependency.

    Contract:
    - Parent `EnvironmentConfigPackage` scope is injected by propagation.
    - `dependency_role` is usually `base`; the class remains generic so
      kernel is not hard-coded into the ontology.
    - `dependency_index` preserves authored composition order.
    - Target package identity and OIG commit are pinned so WorkspaceRevision
      consumers can replay composition without reopening source manifests.
    """

    # --- AWARE: LOGIC START attach_dependency
    created = await EnvironmentConfigPackageDependency.build_via_environment_config_package(
        environment_config_package_id=environment_config_package.id,
        dependency_role=dependency_role,
        dependency_index=dependency_index,
        target_handle=target_handle,
        target_environment_config_package_id=target_environment_config_package_id,
        target_environment_config_package_object_instance_graph_commit_id=(
            target_environment_config_package_object_instance_graph_commit_id
        ),
    )
    for existing in environment_config_package.dependencies:
        if existing.id == created.id:
            return existing
    environment_config_package.dependencies.append(created)
    return created
    # --- AWARE: LOGIC END attach_dependency
