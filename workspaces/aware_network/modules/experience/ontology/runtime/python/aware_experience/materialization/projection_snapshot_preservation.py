from __future__ import annotations

from uuid import UUID

from aware_experience.materialization.snapshot_commit import (
    ExperienceProjectionBranchSnapshot,
    ExperienceProjectionNodeSnapshot,
    ExperienceProjectionNodeClassIdentitySnapshot,
    ExperienceProjectionOIGISnapshot,
    ExperienceProjectionViewInvocationActionSnapshot,
    ExperienceProjectionViewSnapshot,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience_branch import (
    ProjectionExperienceBranch,
)
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_oigi import (
    ProjectionExperienceOIGI,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience_view_state_provider import (
    ProjectionExperienceViewStateProvider,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
from aware_orm.session.session import Session


def preserve_projection_branch_snapshots_from_session(
    *,
    projection_session: Session,
    projection_experience_id: UUID,
) -> tuple[ExperienceProjectionBranchSnapshot, ...]:
    branches: list[ExperienceProjectionBranchSnapshot] = []
    for obj in projection_session.imap_all_objects():
        if not isinstance(obj, ProjectionExperienceBranch):
            continue
        if getattr(obj, "projection_experience_id", None) != projection_experience_id:
            continue
        name = (obj.name or "").strip()
        if name:
            branches.append(ExperienceProjectionBranchSnapshot(name=name))
    return tuple(sorted(branches, key=lambda item: item.name.casefold()))


def preserve_projection_view_snapshots_from_session(
    *,
    projection_session: Session,
    projection_experience_id: UUID,
) -> tuple[ExperienceProjectionViewSnapshot, ...]:
    views: list[ProjectionExperienceView] = []
    providers_by_view_id: dict[UUID, ProjectionExperienceViewStateProvider] = {}
    action_configs_by_id: dict[UUID, ExperienceInvocationActionConfig] = {}
    view_action_bindings_by_view_id: dict[
        UUID, list[ProjectionExperienceViewInvocationActionConfig]
    ] = {}

    for obj in projection_session.imap_all_objects():
        if isinstance(obj, ProjectionExperienceView):
            if (
                getattr(obj, "projection_experience_id", None)
                == projection_experience_id
            ):
                views.append(obj)
        elif isinstance(obj, ProjectionExperienceViewStateProvider):
            view_id = getattr(obj, "projection_experience_view_id", None)
            if isinstance(view_id, UUID):
                providers_by_view_id[view_id] = obj
        elif isinstance(obj, ExperienceInvocationActionConfig):
            if (
                getattr(obj, "projection_experience_id", None)
                == projection_experience_id
            ):
                obj_id = getattr(obj, "id", None)
                if isinstance(obj_id, UUID):
                    action_configs_by_id[obj_id] = obj
        elif isinstance(obj, ProjectionExperienceViewInvocationActionConfig):
            view_id = getattr(obj, "projection_experience_view_id", None)
            if isinstance(view_id, UUID):
                view_action_bindings_by_view_id.setdefault(view_id, []).append(obj)

    snapshots: list[ExperienceProjectionViewSnapshot] = []
    for view in views:
        view_id = getattr(view, "id", None)
        api_view_id = getattr(view, "api_view_id", None)
        name = (view.name or "").strip()
        if (
            not isinstance(view_id, UUID)
            or not isinstance(api_view_id, UUID)
            or not name
        ):
            continue

        provider = providers_by_view_id.get(view_id)
        relationship_providers = tuple(getattr(view, "state_providers", ()) or ())
        if provider is None and relationship_providers:
            provider = relationship_providers[0]

        invocation_actions: list[ExperienceProjectionViewInvocationActionSnapshot] = []
        relationship_bindings = tuple(
            getattr(view, "invocation_action_configs", ()) or ()
        )
        bindings = (
            tuple(view_action_bindings_by_view_id.get(view_id, ()))
            or relationship_bindings
        )
        for binding in bindings:
            action_config = getattr(
                binding, "experience_invocation_action_config", None
            )
            if action_config is None:
                action_config_id = getattr(
                    binding, "experience_invocation_action_config_id", None
                )
                if isinstance(action_config_id, UUID):
                    action_config = action_configs_by_id.get(action_config_id)
            if not isinstance(action_config, ExperienceInvocationActionConfig):
                continue
            api_view_capability_endpoint = getattr(
                binding, "api_view_capability_endpoint", None
            )
            api_capability_endpoint_id = (
                getattr(
                    api_view_capability_endpoint, "api_capability_endpoint_id", None
                )
                or action_config.api_capability_endpoint_id
            )
            if api_capability_endpoint_id is None:
                continue
            invocation_actions.append(
                ExperienceProjectionViewInvocationActionSnapshot(
                    api_view_capability_endpoint_id=(
                        binding.api_view_capability_endpoint_id
                    ),
                    action_key=binding.action_key,
                    sdk_operation_api_view_capability_endpoint_id=(
                        binding.sdk_operation_api_view_capability_endpoint_id
                    ),
                    api_capability_endpoint_id=api_capability_endpoint_id,
                    sdk_operation_id=action_config.sdk_operation_id,
                    label=binding.label,
                    receipt_policy=binding.receipt_policy,
                    confirmation_policy=binding.confirmation_policy,
                    optimistic_policy=binding.optimistic_policy,
                )
            )

        snapshots.append(
            ExperienceProjectionViewSnapshot(
                api_view_id=api_view_id,
                name=name,
                state_provider_ref=(
                    None if provider is None else provider.provider_ref
                ),
                provider_kind=(
                    "runtime_callable" if provider is None else provider.provider_kind
                ),
                purity="pure_read" if provider is None else provider.purity,
                invocation_actions=tuple(
                    sorted(
                        invocation_actions,
                        key=lambda item: item.action_key.casefold(),
                    )
                ),
            )
        )

    return tuple(sorted(snapshots, key=lambda item: item.name.casefold()))


def preserve_projection_node_snapshots_from_session(
    *,
    projection_session: Session,
    projection_experience_id: UUID,
) -> tuple[ExperienceProjectionNodeSnapshot, ...]:
    nodes: list[ProjectionExperienceNode] = []
    identity_keys_by_node_id: dict[UUID, set[str]] = {}

    for obj in projection_session.imap_all_objects():
        if isinstance(obj, ProjectionExperienceNode):
            if (
                getattr(obj, "projection_experience_id", None)
                != projection_experience_id
            ):
                continue
            nodes.append(obj)
            obj_id = getattr(obj, "id", None)
            if isinstance(obj_id, UUID):
                bucket = identity_keys_by_node_id.setdefault(obj_id, set())
                for identity in (
                    getattr(obj, "projection_experience_node_identities", ()) or ()
                ):
                    key = (getattr(identity, "key", "") or "").strip()
                    if key:
                        bucket.add(key)
        elif isinstance(obj, ProjectionExperienceNodeIdentity):
            node_id = getattr(obj, "projection_experience_node_id", None)
            key = (obj.key or "").strip()
            if isinstance(node_id, UUID) and key:
                identity_keys_by_node_id.setdefault(node_id, set()).add(key)

    snapshots: list[ExperienceProjectionNodeSnapshot] = []
    for node in nodes:
        node_id = getattr(node, "id", None)
        object_projection_graph_node_id = getattr(
            node, "object_projection_graph_node_id", None
        )
        key = (node.key or "").strip()
        if (
            not isinstance(node_id, UUID)
            or not isinstance(object_projection_graph_node_id, UUID)
            or not key
        ):
            continue
        snapshots.append(
            ExperienceProjectionNodeSnapshot(
                object_projection_graph_node_id=object_projection_graph_node_id,
                key=key,
                identity_keys=tuple(
                    sorted(identity_keys_by_node_id.get(node_id, set()))
                ),
            )
        )

    return tuple(sorted(snapshots, key=lambda item: item.key.casefold()))


def preserve_projection_oigi_snapshots_from_session(
    *,
    projection_session: Session,
    projection_experience_id: UUID,
) -> tuple[ExperienceProjectionOIGISnapshot, ...]:
    oigis: list[ProjectionExperienceOIGI] = []
    node_class_identities_by_oigi_id: dict[
        UUID, dict[UUID, ProjectionExperienceNodeClassIdentity]
    ] = {}
    class_instance_identities_by_id: dict[UUID, ClassInstanceIdentity] = {}
    class_instances_by_id: dict[UUID, ClassInstance] = {}

    for obj in projection_session.imap_all_objects():
        if isinstance(obj, ProjectionExperienceOIGI):
            if getattr(obj, "projection_experience_id", None) != projection_experience_id:
                continue
            oigis.append(obj)
            oigi_id = getattr(obj, "id", None)
            if isinstance(oigi_id, UUID):
                bucket = node_class_identities_by_oigi_id.setdefault(oigi_id, {})
                for node_class_identity in (
                    getattr(obj, "node_class_identities", ()) or ()
                ):
                    node_class_identity_id = getattr(node_class_identity, "id", None)
                    if isinstance(node_class_identity_id, UUID):
                        bucket[node_class_identity_id] = node_class_identity
        elif isinstance(obj, ProjectionExperienceNodeClassIdentity):
            oigi_id = getattr(obj, "projection_experience_oigi_id", None)
            node_class_identity_id = getattr(obj, "id", None)
            if isinstance(oigi_id, UUID) and isinstance(
                node_class_identity_id, UUID
            ):
                node_class_identities_by_oigi_id.setdefault(oigi_id, {})[
                    node_class_identity_id
                ] = obj
        elif isinstance(obj, ClassInstanceIdentity):
            obj_id = getattr(obj, "id", None)
            if isinstance(obj_id, UUID):
                class_instance_identities_by_id[obj_id] = obj
        elif isinstance(obj, ClassInstance):
            obj_id = getattr(obj, "id", None)
            if isinstance(obj_id, UUID):
                class_instances_by_id[obj_id] = obj

    snapshots: list[ExperienceProjectionOIGISnapshot] = []
    for oigi in sorted(
        oigis,
        key=lambda item: (
            (getattr(item, "key", None) or "").casefold(),
            str(getattr(item, "object_instance_graph_identity_id", "")),
            str(getattr(item, "id", "")),
        ),
    ):
        oigi_id = getattr(oigi, "id", None)
        object_instance_graph_identity_id = getattr(
            oigi, "object_instance_graph_identity_id", None
        )
        if not isinstance(oigi_id, UUID) or not isinstance(
            object_instance_graph_identity_id, UUID
        ):
            continue

        node_class_identity_snapshots: list[
            ExperienceProjectionNodeClassIdentitySnapshot
        ] = []
        object_instance_graph_ids: set[UUID] = set()
        for node_class_identity in sorted(
            node_class_identities_by_oigi_id.get(oigi_id, {}).values(),
            key=lambda item: (
                (getattr(item, "key", None) or "").casefold(),
                str(getattr(item, "projection_experience_node_identity_id", "")),
                str(getattr(item, "class_instance_identity_id", "")),
            ),
        ):
            projection_node_identity_id = getattr(
                node_class_identity, "projection_experience_node_identity_id", None
            )
            class_instance_identity_id = getattr(
                node_class_identity, "class_instance_identity_id", None
            )
            key = (getattr(node_class_identity, "key", "") or "").strip()
            if (
                not isinstance(projection_node_identity_id, UUID)
                or not isinstance(class_instance_identity_id, UUID)
                or not key
            ):
                continue

            class_instance_identity = getattr(
                node_class_identity, "class_instance_identity", None
            ) or class_instance_identities_by_id.get(class_instance_identity_id)
            if not isinstance(class_instance_identity, ClassInstanceIdentity):
                raise RuntimeError(
                    "ProjectionExperience OIGI preservation requires "
                    + "ClassInstanceIdentity for node-class identity "
                    + f"{getattr(node_class_identity, 'id', None)}"
                )

            class_instance = getattr(
                class_instance_identity, "class_instance", None
            )
            class_instance_id = getattr(
                class_instance_identity, "class_instance_id", None
            )
            if class_instance is None and isinstance(class_instance_id, UUID):
                class_instance = class_instances_by_id.get(class_instance_id)
            if not isinstance(class_instance, ClassInstance):
                raise RuntimeError(
                    "ProjectionExperience OIGI preservation requires "
                    + "ClassInstance for ClassInstanceIdentity "
                    + f"{class_instance_identity_id}"
                )

            class_config_id = getattr(class_instance, "class_config_id", None)
            source_object_id = getattr(class_instance, "source_object_id", None)
            object_instance_graph_id = getattr(
                class_instance, "object_instance_graph_id", None
            )
            if (
                not isinstance(class_config_id, UUID)
                or not isinstance(source_object_id, UUID)
                or not isinstance(object_instance_graph_id, UUID)
            ):
                raise RuntimeError(
                    "ProjectionExperience OIGI preservation found incomplete "
                    + f"ClassInstance {getattr(class_instance, 'id', None)}"
                )
            object_instance_graph_ids.add(object_instance_graph_id)
            node_class_identity_snapshots.append(
                ExperienceProjectionNodeClassIdentitySnapshot(
                    projection_experience_node_identity_id=(
                        projection_node_identity_id
                    ),
                    class_config_id=class_config_id,
                    source_object_id=source_object_id,
                    key=key,
                )
            )

        if not node_class_identity_snapshots:
            continue
        if len(object_instance_graph_ids) != 1:
            raise RuntimeError(
                "ProjectionExperience OIGI preservation expected exactly one "
                + "ObjectInstanceGraph id, got "
                + ", ".join(str(item) for item in sorted(object_instance_graph_ids))
            )
        snapshots.append(
            ExperienceProjectionOIGISnapshot(
                object_instance_graph_id=next(iter(object_instance_graph_ids)),
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                key=(getattr(oigi, "key", None) or "").strip() or None,
                node_class_identities=tuple(node_class_identity_snapshots),
            )
        )

    return tuple(snapshots)


def merge_projection_node_snapshots(
    *snapshot_groups: tuple[ExperienceProjectionNodeSnapshot, ...],
) -> tuple[ExperienceProjectionNodeSnapshot, ...]:
    merged_by_key: dict[tuple[UUID, str], ExperienceProjectionNodeSnapshot] = {}
    for snapshots in snapshot_groups:
        for snapshot in snapshots:
            key = (
                snapshot.object_projection_graph_node_id,
                (snapshot.key or "").strip().casefold(),
            )
            merged_by_key[key] = snapshot
    return tuple(
        sorted(
            merged_by_key.values(),
            key=lambda item: (
                item.key.casefold(),
                str(item.object_projection_graph_node_id),
            ),
        )
    )
