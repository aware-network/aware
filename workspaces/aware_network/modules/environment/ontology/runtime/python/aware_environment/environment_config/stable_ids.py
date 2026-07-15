"""Bootstrap stable-id helpers for Environment-owned EnvironmentConfig.

Canonical formulas are generated from Environment `.aware` sources. These
fallbacks cover the short window before `environment-ontology` is regenerated
after EnvironmentConfig moves out of Structure.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

try:
    from aware_environment_ontology.stable_ids import (  # type: ignore[import-not-found]
        NS_ENVIRONMENT,
    )
except ImportError:  # pragma: no cover - bootstrap before environment materialize.
    NS_ENVIRONMENT = uuid5(NAMESPACE_URL, "aware://environment/v1")

try:
    from aware_environment_ontology.stable_ids import (  # type: ignore[import-not-found]
        stable_environment_config_id,
    )
except ImportError:  # pragma: no cover - bootstrap before environment materialize.

    def stable_environment_config_id(*, handle: str) -> UUID:
        handle_norm = (handle or "").casefold().strip()
        return uuid5(NS_ENVIRONMENT, f"aware:environment_config:{handle_norm}")


try:
    from aware_environment_ontology.stable_ids import (  # type: ignore[import-not-found]
        stable_environment_config_ontology_config_id,
    )
except ImportError:  # pragma: no cover - bootstrap before environment materialize.

    def stable_environment_config_ontology_config_id(
        *, environment_config_id: UUID, name: str, fqn_prefix: str
    ) -> UUID:
        name_norm = (name or "").casefold().strip()
        fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
        return uuid5(
            NS_ENVIRONMENT,
            "aware:environment_config_ontology_config:"
            f"{environment_config_id}:{name_norm}:{fqn_prefix_norm}",
        )


try:
    from aware_environment_ontology.stable_ids import (  # type: ignore[import-not-found]
        stable_environment_config_package_id,
    )
except ImportError:  # pragma: no cover - bootstrap before environment materialize.

    def stable_environment_config_package_id(*, handle: str) -> UUID:
        handle_norm = (handle or "").casefold().strip()
        return uuid5(
            NS_ENVIRONMENT,
            f"aware:environment_config_package:{handle_norm}",
        )


try:
    from aware_environment_ontology.stable_ids import (  # type: ignore[import-not-found]
        stable_environment_config_package_dependency_id,
    )
except ImportError:  # pragma: no cover - bootstrap before environment materialize.

    def stable_environment_config_package_dependency_id(
        *,
        environment_config_package_id: UUID,
        dependency_role: str,
        dependency_index: int,
        target_handle: str,
        target_environment_config_package_id: UUID,
        target_environment_config_package_object_instance_graph_commit_id: UUID,
    ) -> UUID:
        dependency_role_norm = (dependency_role or "").casefold().strip()
        target_handle_norm = (target_handle or "").casefold().strip()
        return uuid5(
            NS_ENVIRONMENT,
            "aware:environment_config_package_dependency:"
            f"{environment_config_package_id}:{dependency_role_norm}:"
            f"{dependency_index}:{target_handle_norm}:"
            f"{target_environment_config_package_id}:"
            f"{target_environment_config_package_object_instance_graph_commit_id}",
        )


try:
    from aware_environment_ontology.stable_ids import (  # type: ignore[import-not-found]
        stable_environment_config_package_ontology_package_id,
    )
except ImportError:  # pragma: no cover - bootstrap before environment materialize.

    def stable_environment_config_package_ontology_package_id(
        *, environment_config_package_id: UUID, name: str, fqn_prefix: str
    ) -> UUID:
        name_norm = (name or "").casefold().strip()
        fqn_prefix_norm = (fqn_prefix or "").casefold().strip()
        return uuid5(
            NS_ENVIRONMENT,
            "aware:environment_config_package_ontology_package:"
            f"{environment_config_package_id}:{name_norm}:{fqn_prefix_norm}",
        )


__all__ = [
    "NS_ENVIRONMENT",
    "stable_environment_config_id",
    "stable_environment_config_ontology_config_id",
    "stable_environment_config_package_id",
    "stable_environment_config_package_dependency_id",
    "stable_environment_config_package_ontology_package_id",
]
