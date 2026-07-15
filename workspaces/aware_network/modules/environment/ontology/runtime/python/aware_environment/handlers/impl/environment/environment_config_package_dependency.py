from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.environment.environment_config_package_dependency import (
    EnvironmentConfigPackageDependency,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_environment_ontology.stable_ids import (
    stable_environment_config_package_dependency_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_config_package(
    environment_config_package_id: UUID,
    dependency_role: str,
    dependency_index: int,
    target_handle: str,
    target_environment_config_package_id: UUID,
    target_environment_config_package_object_instance_graph_commit_id: UUID,
) -> EnvironmentConfigPackageDependency:
    """
    Create one deterministic environment package dependency edge.

    Contract:
    - Parent EnvironmentConfigPackage scope is injected by propagation.
    - `target_handle` mirrors the target package handle for readable
      receipts and deterministic root selection.
    - `target_environment_config_package_object_instance_graph_commit_id`
      is required; dependency resolution must be commit-pinned.
    """

    # --- AWARE: LOGIC START build_via_environment_config_package
    normalized_role = (dependency_role or "").strip()
    normalized_target_handle = (target_handle or "").strip()
    if not normalized_role:
        raise RuntimeError(
            "EnvironmentConfigPackageDependency.build_via_environment_config_package " "requires dependency_role"
        )
    if dependency_index < 0:
        raise RuntimeError(
            "EnvironmentConfigPackageDependency.build_via_environment_config_package "
            "requires non-negative dependency_index"
        )
    if not normalized_target_handle:
        raise RuntimeError(
            "EnvironmentConfigPackageDependency.build_via_environment_config_package " "requires target_handle"
        )

    dependency_id = stable_environment_config_package_dependency_id(
        environment_config_package_id=environment_config_package_id,
        dependency_role=normalized_role,
        dependency_index=dependency_index,
        target_handle=normalized_target_handle,
        target_environment_config_package_id=target_environment_config_package_id,
        target_environment_config_package_object_instance_graph_commit_id=(
            target_environment_config_package_object_instance_graph_commit_id
        ),
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentConfigPackageDependency, dependency_id)
    if existing is not None:
        expected = {
            "environment_config_package_id": environment_config_package_id,
            "target_environment_config_package_id": (target_environment_config_package_id),
            "target_environment_config_package_object_instance_graph_commit_id": (
                target_environment_config_package_object_instance_graph_commit_id
            ),
            "dependency_role": normalized_role,
            "dependency_index": dependency_index,
            "target_handle": normalized_target_handle,
        }
        for field_name, expected_value in expected.items():
            if getattr(existing, field_name) != expected_value:
                raise RuntimeError(
                    "EnvironmentConfigPackageDependency existing payload mismatch: "
                    f"dependency_id={dependency_id} field={field_name}"
                )
        return existing

    return EnvironmentConfigPackageDependency(
        id=dependency_id,
        environment_config_package_id=environment_config_package_id,
        target_environment_config_package=None,
        target_environment_config_package_id=target_environment_config_package_id,
        target_environment_config_package_object_instance_graph_commit=None,
        target_environment_config_package_object_instance_graph_commit_id=(
            target_environment_config_package_object_instance_graph_commit_id
        ),
        dependency_role=normalized_role,
        dependency_index=dependency_index,
        target_handle=normalized_target_handle,
    )
    # --- AWARE: LOGIC END build_via_environment_config_package
