from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_experience_ontology.environment.environment_experience_event_node_scope import (
    EnvironmentExperienceEventNodeScope,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_oigi import (
    ProjectionExperienceOIGI,
)
from aware_reactivity.stable_ids import stable_event_config_condition_config_scope_id


class EnvironmentEventNodeScopeLoweringError(ValueError):
    """Raised when trigger node scope cannot lower from declared graph binding truth."""


@dataclass(frozen=True, slots=True)
class LoweredEnvironmentEventNodeScope:
    event_config_condition_config_id: UUID
    projection_experience_node_identity_id: UUID
    object_instance_graph_identity_id: UUID
    object_instance_graph_branch_id: UUID | None
    class_instance_identity_id: UUID
    scope_key: str
    event_config_condition_config_scope_id: UUID


def lower_environment_event_node_scope(
    *,
    profile_config: EnvironmentExperienceProfileConfig,
    node_scope: EnvironmentExperienceEventNodeScope,
) -> LoweredEnvironmentEventNodeScope:
    """Resolve one Environment event node scope through committed graph binding truth."""

    node_identity_id = node_scope.projection_experience_node_identity_id
    branch_id = node_scope.object_instance_graph_branch_id
    matches: list[
        tuple[ProjectionExperienceOIGI, ProjectionExperienceNodeClassIdentity]
    ] = []
    declared_on_profile = False

    for experience_bridge in profile_config.experiences:
        projection_experience = experience_bridge.projection_experience
        if projection_experience is None:
            continue
        declared_node_identity_ids = {
            node_identity.id
            for node in projection_experience.projection_experience_nodes
            for node_identity in node.projection_experience_node_identities
            if node_identity.id is not None
        }
        if node_identity_id not in declared_node_identity_ids:
            continue
        declared_on_profile = True

        for projection_oigi in projection_experience.projection_experience_oigis:
            if branch_id is not None:
                branch = node_scope.object_instance_graph_branch
                if branch is None:
                    raise EnvironmentEventNodeScopeLoweringError(
                        "environment_event_node_scope_branch_membership_unproven"
                    )
                if (
                    branch.object_instance_graph_identity_id
                    != projection_oigi.object_instance_graph_identity_id
                ):
                    continue
            for node_class_identity in projection_oigi.node_class_identities:
                if (
                    node_class_identity.projection_experience_node_identity_id
                    == node_identity_id
                ):
                    matches.append((projection_oigi, node_class_identity))

    if not declared_on_profile:
        raise EnvironmentEventNodeScopeLoweringError(
            "environment_event_node_scope_alias_not_declared"
        )
    if not matches:
        raise EnvironmentEventNodeScopeLoweringError(
            "environment_event_node_scope_node_unbound"
        )
    if len(matches) > 1:
        raise EnvironmentEventNodeScopeLoweringError(
            "environment_event_node_scope_alias_ambiguous"
        )

    projection_oigi, node_class_identity = matches[0]
    scope_key = _reactivity_scope_key(
        object_instance_graph_branch_id=branch_id,
        class_instance_identity_id=node_class_identity.class_instance_identity_id,
    )
    scope_id = stable_event_config_condition_config_scope_id(
        event_config_condition_config_id=node_scope.event_config_condition_config_id,
        object_instance_graph_identity_id=(
            projection_oigi.object_instance_graph_identity_id
        ),
        scope_key=scope_key,
    )
    _assert_existing_scope_matches(
        node_scope=node_scope,
        object_instance_graph_identity_id=projection_oigi.object_instance_graph_identity_id,
        class_instance_identity_id=node_class_identity.class_instance_identity_id,
        object_instance_graph_branch_id=branch_id,
        expected_scope_id=scope_id,
    )
    return LoweredEnvironmentEventNodeScope(
        event_config_condition_config_id=node_scope.event_config_condition_config_id,
        projection_experience_node_identity_id=node_identity_id,
        object_instance_graph_identity_id=projection_oigi.object_instance_graph_identity_id,
        object_instance_graph_branch_id=branch_id,
        class_instance_identity_id=node_class_identity.class_instance_identity_id,
        scope_key=scope_key,
        event_config_condition_config_scope_id=scope_id,
    )


def _reactivity_scope_key(
    *,
    object_instance_graph_branch_id: UUID | None,
    class_instance_identity_id: UUID,
) -> str:
    branch_part = (
        f"branch:{object_instance_graph_branch_id}"
        if object_instance_graph_branch_id is not None
        else "branch:all"
    )
    return f"{branch_part}|class_instance:{class_instance_identity_id}"


def _assert_existing_scope_matches(
    *,
    node_scope: EnvironmentExperienceEventNodeScope,
    object_instance_graph_identity_id: UUID,
    class_instance_identity_id: UUID,
    object_instance_graph_branch_id: UUID | None,
    expected_scope_id: UUID,
) -> None:
    existing_scope = node_scope.event_config_condition_config_scope
    if existing_scope is None:
        if (
            node_scope.event_config_condition_config_scope_id is not None
            and node_scope.event_config_condition_config_scope_id != expected_scope_id
        ):
            raise EnvironmentEventNodeScopeLoweringError(
                "environment_event_node_scope_existing_scope_id_mismatch"
            )
        return
    if existing_scope.id is not None and existing_scope.id != expected_scope_id:
        raise EnvironmentEventNodeScopeLoweringError(
            "environment_event_node_scope_existing_scope_id_mismatch"
        )
    if (
        existing_scope.object_instance_graph_identity_id
        != object_instance_graph_identity_id
    ):
        raise EnvironmentEventNodeScopeLoweringError(
            "environment_event_node_scope_existing_scope_oigi_mismatch"
        )
    if existing_scope.class_instance_identity_id != class_instance_identity_id:
        raise EnvironmentEventNodeScopeLoweringError(
            "environment_event_node_scope_existing_scope_instance_mismatch"
        )
    if (
        existing_scope.object_instance_graph_branch_id
        != object_instance_graph_branch_id
    ):
        raise EnvironmentEventNodeScopeLoweringError(
            "environment_event_node_scope_existing_scope_branch_mismatch"
        )


__all__ = [
    "EnvironmentEventNodeScopeLoweringError",
    "LoweredEnvironmentEventNodeScope",
    "lower_environment_event_node_scope",
]
