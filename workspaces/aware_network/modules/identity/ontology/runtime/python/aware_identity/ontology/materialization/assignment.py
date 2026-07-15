from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias, TypeVar
from uuid import UUID

from aware_identity_service_dto.role.assignment import (
    RoleAssignmentBinding,
    RoleAssignmentReceipt,
    RoleAssignmentRequest,
    RoleAssignmentResolveRequest,
    RoleAssignmentResolveResult,
    RoleUnassignmentReceipt,
    RoleUnassignmentRequest,
)
from aware_identity_ontology.actor.actor import Actor
from aware_identity_ontology.actor.actor_role import ActorRole
from aware_identity_ontology.identity.identity import Identity
from aware_identity_ontology.role.role import Role
from aware_identity_ontology.role.role_class_instance import RoleClassInstance
from aware_identity_ontology_orm_models.actor.actor import Actor as ActorReplicaModel
from aware_identity_ontology_orm_models.role.role_config import (
    RoleConfig as RoleConfigReplicaModel,
)
from aware_identity_ontology_orm_models.role.role_config_class_config import (
    RoleConfigClassConfig as RoleConfigClassConfigReplicaModel,
)
from aware_identity_ontology.stable_ids import (
    stable_actor_role_id,
    stable_role_config_id,
    stable_role_config_class_config_id,
    stable_role_class_instance_id,
    stable_role_id,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.materialization.context import MaterializationRuntimeContext
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import (
    reify_oig_root_model,
    reify_oig_target_model,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph as ObjectProjectionGraphModel,
)
from aware_meta_ontology_orm_models.class_.class_instance import (
    ClassInstance as ClassInstanceReplicaModel,
)
from aware_meta_ontology_orm_models.class_.class_instance_identity import (
    ClassInstanceIdentity as ClassInstanceIdentityReplicaModel,
)
from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch as ObjectInstanceGraphBranchReplicaModel,
)
from aware_orm.session.current_session_ctx import set_session
from aware_orm.session.session import Session
from aware_identity.materialization.bootstrap import (
    resolve_actor_identity_binding,
)

_TRoot = TypeVar("_TRoot")


RoleAssignmentMaterializationContext: TypeAlias = MaterializationRuntimeContext


@dataclass(frozen=True, slots=True)
class _ResolvedClassInstanceScope:
    class_instance_identity_id: UUID
    class_config_id: UUID
    object_instance_graph_identity_id: UUID
    role_config_class_config_id: UUID | None


def _normalize_branch_key(raw: str | None) -> str:
    return (raw or "").strip().casefold() or "all"


def _resolve_role_config_id(
    role_config_id: UUID | None, role_config_name: str | None
) -> UUID:
    name_norm = (role_config_name or "").strip()
    if role_config_id is None and not name_norm:
        raise ValueError("role assignment requires role_config_id or role_config_name")
    if role_config_id is not None and not name_norm:
        return role_config_id
    name_id = stable_role_config_id(name=name_norm)
    if role_config_id is not None and role_config_id != name_id:
        raise ValueError(
            "role_config_id does not match role_config_name stable id: "
            f"role_config_id={role_config_id} role_config_name={role_config_name!r} expected={name_id}"
        )
    return name_id


async def _load_replica_model_by_id(
    *,
    session: Session,
    model_type: type[Any],
    row_id: UUID,
    label: str,
) -> Any | None:
    with set_session(session):
        model = await model_type.by_id(row_id)
    if model is None:
        return None
    if getattr(model, "id", None) != row_id:
        raise RuntimeError(
            f"{label} lookup returned mismatched row: expected={row_id} "
            + f"actual={getattr(model, 'id', None)}"
        )
    return model


async def _require_replica_model(
    *,
    session: Session,
    model_type: type[Any],
    row_id: UUID,
    label: str,
) -> None:
    if await _load_replica_model_by_id(
        session=session,
        model_type=model_type,
        row_id=row_id,
        label=label,
    ):
        return
    raise ValueError(f"missing {label}: {row_id}")


def _binding_from_ids(
    *,
    actor_id: UUID,
    role_config_id: UUID,
    role_id: UUID,
    actor_role_id: UUID,
    role_class_instance_id: UUID,
    class_instance_identity_id: UUID,
    role_config_class_config_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_branch_key: str,
    object_instance_graph_branch_id: UUID | None,
) -> RoleAssignmentBinding:
    return RoleAssignmentBinding(
        actor_id=actor_id,
        role_config_id=role_config_id,
        role_id=role_id,
        actor_role_id=actor_role_id,
        role_class_instance_id=role_class_instance_id,
        class_instance_identity_id=class_instance_identity_id,
        role_config_class_config_id=role_config_class_config_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_branch_key=object_instance_graph_branch_key,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
    )


def _planned_binding_for_scope(
    *,
    actor_id: UUID,
    role_config_id: UUID,
    resolved_scope: _ResolvedClassInstanceScope,
    object_instance_graph_branch_key: str,
    object_instance_graph_branch_id: UUID | None,
) -> RoleAssignmentBinding:
    if resolved_scope.role_config_class_config_id is None:
        raise RuntimeError(
            "role assignment scope resolution did not produce role_config_class_config_id: "
            + f"role_config_id={role_config_id} class_instance_identity_id={resolved_scope.class_instance_identity_id}"
        )

    role_id = stable_role_id(
        role_config_id=role_config_id,
        object_instance_graph_identity_id=resolved_scope.object_instance_graph_identity_id,
        object_instance_graph_branch_key=object_instance_graph_branch_key,
    )
    actor_role_id = stable_actor_role_id(actor_id=actor_id, role_id=role_id)
    role_class_instance_id = stable_role_class_instance_id(
        role_id=role_id,
        class_instance_identity_id=resolved_scope.class_instance_identity_id,
        role_config_class_config_id=resolved_scope.role_config_class_config_id,
    )
    return _binding_from_ids(
        actor_id=actor_id,
        role_config_id=role_config_id,
        role_id=role_id,
        actor_role_id=actor_role_id,
        role_class_instance_id=role_class_instance_id,
        class_instance_identity_id=resolved_scope.class_instance_identity_id,
        role_config_class_config_id=resolved_scope.role_config_class_config_id,
        object_instance_graph_identity_id=resolved_scope.object_instance_graph_identity_id,
        object_instance_graph_branch_key=object_instance_graph_branch_key,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
    )


def _role_matches(
    role: Role,
    *,
    role_config_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_branch_key: str,
    object_instance_graph_branch_id: UUID | None,
) -> bool:
    return (
        role.role_config_id == role_config_id
        and role.object_instance_graph_identity_id == object_instance_graph_identity_id
        and _normalize_branch_key(role.object_instance_graph_branch_key)
        == object_instance_graph_branch_key
        and role.object_instance_graph_branch_id == object_instance_graph_branch_id
    )


def _actor_role_matches(
    actor_role: ActorRole, *, actor_id: UUID, role_id: UUID
) -> bool:
    return actor_role.actor_id == actor_id and actor_role.role_id == role_id


def _role_class_instance_matches(
    role_class_instance: RoleClassInstance,
    *,
    class_instance_identity_id: UUID,
    role_config_class_config_id: UUID,
) -> bool:
    return (
        role_class_instance.class_instance_identity_id == class_instance_identity_id
        and role_class_instance.role_config_class_config_id
        == role_config_class_config_id
    )


def _find_role_class_instance(
    *,
    role: Role,
    class_instance_identity_id: UUID,
    role_config_class_config_id: UUID,
) -> RoleClassInstance | None:
    for candidate in role.role_class_instances:
        if candidate.class_instance_identity_id != class_instance_identity_id:
            continue
        if candidate.role_config_class_config_id != role_config_class_config_id:
            raise ValueError(
                "role assignment found ambiguous RoleClassInstance policy for the same "
                + "class_instance_identity: "
                + f"role_id={role.id} class_instance_identity_id={class_instance_identity_id} "
                + f"existing_role_config_class_config_id={candidate.role_config_class_config_id} "
                + f"requested_role_config_class_config_id={role_config_class_config_id}"
            )
        return candidate
    return None


def _find_matching_role_class_instances(
    *,
    role: Role,
    class_instance_identity_id: UUID,
    role_config_class_config_id: UUID | None,
) -> tuple[RoleClassInstance, ...]:
    if role_config_class_config_id is not None:
        match = _find_role_class_instance(
            role=role,
            class_instance_identity_id=class_instance_identity_id,
            role_config_class_config_id=role_config_class_config_id,
        )
        return () if match is None else (match,)

    matches = [
        candidate
        for candidate in role.role_class_instances
        if candidate.class_instance_identity_id == class_instance_identity_id
    ]
    if len(matches) <= 1:
        return tuple(matches)
    distinct_policy_ids = {
        candidate.role_config_class_config_id for candidate in matches
    }
    if len(distinct_policy_ids) > 1:
        raise ValueError(
            "role assignment resolution found multiple RoleClassInstance policies for one "
            + f"class_instance_identity_id={class_instance_identity_id} role_id={role.id}"
        )
    return tuple(matches[:1])


async def _resolve_class_instance_scope(
    *,
    session: Session,
    class_instance_identity_id: UUID,
    role_config_id: UUID | None = None,
) -> _ResolvedClassInstanceScope:
    class_instance_identity = await _load_replica_model_by_id(
        session=session,
        model_type=ClassInstanceIdentityReplicaModel,
        row_id=class_instance_identity_id,
        label="class_instance_identity_id",
    )
    if class_instance_identity is None:
        raise ValueError(
            f"missing class_instance_identity_id: {class_instance_identity_id}"
        )

    class_instance_id = class_instance_identity.class_instance_id
    if class_instance_id is None:
        raise RuntimeError(
            "class_instance_identity row is missing class_instance_id: "
            + str(class_instance_identity_id)
        )
    class_instance = await _load_replica_model_by_id(
        session=session,
        model_type=ClassInstanceReplicaModel,
        row_id=class_instance_id,
        label="class_instance",
    )
    if class_instance is None:
        raise ValueError(
            f"missing class_instance for class_instance_identity_id: {class_instance_identity_id}"
        )

    resolved_class_config_id = class_instance.class_config_id
    resolved_object_instance_graph_identity_id = (
        class_instance_identity.object_instance_graph_identity_id
    )
    resolved_role_config_class_config_id: UUID | None = None
    if role_config_id is not None:
        resolved_role_config_class_config_id = stable_role_config_class_config_id(
            role_config_id=role_config_id,
            class_config_id=resolved_class_config_id,
        )
        await _require_replica_model(
            session=session,
            model_type=RoleConfigClassConfigReplicaModel,
            row_id=resolved_role_config_class_config_id,
            label="role_config_class_config_id",
        )

    return _ResolvedClassInstanceScope(
        class_instance_identity_id=class_instance_identity_id,
        class_config_id=resolved_class_config_id,
        object_instance_graph_identity_id=resolved_object_instance_graph_identity_id,
        role_config_class_config_id=resolved_role_config_class_config_id,
    )


async def _actor_roles_for_role(
    *,
    context: RoleAssignmentMaterializationContext,
    role_id: UUID,
) -> tuple[ActorRole, ...]:
    commit_store = FSCommitStore()
    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    actor_roles: list[ActorRole] = []
    async for identity_branch_id, _ in commit_store.iter_lane_heads_by_projection(
        projection_hash=identity_opg.projection_hash
    ):
        materialized = await _materialize_projection_lane_oig(
            context=context,
            branch_id=identity_branch_id,
            projection_name="Identity",
        )
        if materialized is None:
            continue
        opg, oig = materialized
        for actor_role in _reify_oig_models_by_type(
            context=context,
            opg=opg,
            oig=oig,
            branch_id=identity_branch_id,
            model_type=ActorRole,
        ):
            if actor_role.role_id == role_id:
                actor_roles.append(actor_role)
    return tuple(actor_roles)


async def _resolve_actor_role_by_id(
    *,
    context: RoleAssignmentMaterializationContext,
    actor_role_id: UUID,
) -> ActorRole | None:
    commit_store = FSCommitStore()
    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    async for identity_branch_id, _ in commit_store.iter_lane_heads_by_projection(
        projection_hash=identity_opg.projection_hash
    ):
        materialized = await _materialize_projection_lane_oig(
            context=context,
            branch_id=identity_branch_id,
            projection_name="Identity",
        )
        if materialized is None:
            continue
        opg, oig = materialized
        actor_role = _reify_oig_model_by_source_id(
            context=context,
            opg=opg,
            oig=oig,
            branch_id=identity_branch_id,
            model_type=ActorRole,
            root_id=actor_role_id,
        )
        if actor_role is not None:
            return actor_role
    return None


async def ensure_role_assignment(
    *,
    session: Session,
    request: RoleAssignmentRequest,
    context: RoleAssignmentMaterializationContext | None = None,
) -> RoleAssignmentReceipt:
    role_config_id = _resolve_role_config_id(
        request.role_config_id, request.role_config_name
    )
    branch_key = _normalize_branch_key(request.object_instance_graph_branch_key)
    resolved_context = _require_role_assignment_context(context)

    await _require_replica_model(
        session=session,
        model_type=ActorReplicaModel,
        row_id=request.actor_id,
        label="actor_id",
    )
    await _require_replica_model(
        session=session,
        model_type=RoleConfigReplicaModel,
        row_id=role_config_id,
        label="role_config_id",
    )
    if request.object_instance_graph_branch_id is not None:
        await _require_replica_model(
            session=session,
            model_type=ObjectInstanceGraphBranchReplicaModel,
            row_id=request.object_instance_graph_branch_id,
            label="object_instance_graph_branch_id",
        )

    resolved_scope = await _resolve_class_instance_scope(
        session=session,
        class_instance_identity_id=request.class_instance_identity_id,
        role_config_id=role_config_id,
    )
    if resolved_scope.role_config_class_config_id is None:
        raise RuntimeError(
            "role assignment scope resolution did not produce role_config_class_config_id: "
            + f"role_config_id={role_config_id} class_instance_identity_id={request.class_instance_identity_id}"
        )

    role_id = stable_role_id(
        role_config_id=role_config_id,
        object_instance_graph_identity_id=resolved_scope.object_instance_graph_identity_id,
        object_instance_graph_branch_key=branch_key,
    )
    actor_role_id = stable_actor_role_id(actor_id=request.actor_id, role_id=role_id)

    role = await _materialize_lane_root(
        context=resolved_context,
        root_id=role_id,
        projection_name="Role",
        root_type=Role,
    )
    role_created = role is None
    if role is None or not _role_matches(
        role,
        role_config_id=role_config_id,
        object_instance_graph_identity_id=resolved_scope.object_instance_graph_identity_id,
        object_instance_graph_branch_key=branch_key,
        object_instance_graph_branch_id=request.object_instance_graph_branch_id,
    ):
        role_lane = resolved_context.bind_lane(
            projection="Role",
            branch_id=role_id,
        )
        with role_lane.activate(commit=True, publish=False):
            await Role.create(
                role_config_id=role_config_id,
                object_instance_graph_identity_id=resolved_scope.object_instance_graph_identity_id,
                object_instance_graph_branch_key=branch_key,
                object_instance_graph_branch_id=request.object_instance_graph_branch_id,
            )
        role = await _materialize_lane_root(
            context=resolved_context,
            root_id=role_id,
            projection_name="Role",
            root_type=Role,
        )
    if role is None:
        raise RuntimeError(
            "Role assignment materialization did not hydrate Role lane root: "
            + f"role_id={role_id}"
        )

    role_class_instance = _find_role_class_instance(
        role=role,
        class_instance_identity_id=resolved_scope.class_instance_identity_id,
        role_config_class_config_id=resolved_scope.role_config_class_config_id,
    )
    role_class_instance_created = role_class_instance is None
    if role_class_instance is None:
        role_lane = resolved_context.bind_lane(
            projection="Role",
            branch_id=role_id,
        )
        with role_lane.activate(commit=True, publish=False):
            await role.add_class_instance(
                class_instance_identity_id=resolved_scope.class_instance_identity_id,
                role_config_class_config_id=resolved_scope.role_config_class_config_id,
            )
        role = await _materialize_lane_root(
            context=resolved_context,
            root_id=role_id,
            projection_name="Role",
            root_type=Role,
        )
        if role is None:
            raise RuntimeError(
                "Role assignment materialization lost Role after RoleClassInstance write: "
                + f"role_id={role_id}"
            )
        role_class_instance = _find_role_class_instance(
            role=role,
            class_instance_identity_id=resolved_scope.class_instance_identity_id,
            role_config_class_config_id=resolved_scope.role_config_class_config_id,
        )
    if role_class_instance is None:
        raise RuntimeError(
            "Role assignment materialization did not hydrate RoleClassInstance: "
            + f"role_id={role_id} class_instance_identity_id={resolved_scope.class_instance_identity_id}"
        )

    actor_role = await _resolve_actor_role_by_id(
        context=resolved_context,
        actor_role_id=actor_role_id,
    )
    actor_role_created = actor_role is None
    if actor_role is None or not _actor_role_matches(
        actor_role, actor_id=request.actor_id, role_id=role.id
    ):
        await _add_actor_role_on_identity_lane(
            context=resolved_context,
            session=session,
            actor_id=request.actor_id,
            role_id=role.id,
        )
        actor_role = await _resolve_actor_role_by_id(
            context=resolved_context,
            actor_role_id=actor_role_id,
        )
    if actor_role is None:
        raise RuntimeError(
            "Role assignment materialization did not hydrate ActorRole lane root: "
            + f"actor_role_id={actor_role_id}"
        )

    binding = _binding_from_ids(
        actor_id=request.actor_id,
        role_config_id=role_config_id,
        role_id=role.id,
        actor_role_id=actor_role.id,
        role_class_instance_id=role_class_instance.id,
        class_instance_identity_id=role_class_instance.class_instance_identity_id,
        role_config_class_config_id=role_class_instance.role_config_class_config_id,
        object_instance_graph_identity_id=resolved_scope.object_instance_graph_identity_id,
        object_instance_graph_branch_key=branch_key,
        object_instance_graph_branch_id=request.object_instance_graph_branch_id,
    )
    return RoleAssignmentReceipt(
        request_id=request.request_id,
        binding=binding,
        role_created=role_created,
        actor_role_created=actor_role_created,
        role_class_instance_created=role_class_instance_created,
    )


async def unassign_role(
    *,
    session: Session,
    request: RoleUnassignmentRequest,
    context: RoleAssignmentMaterializationContext | None = None,
) -> RoleUnassignmentReceipt:
    role_config_id = _resolve_role_config_id(
        request.role_config_id, request.role_config_name
    )
    branch_key = _normalize_branch_key(request.object_instance_graph_branch_key)
    resolved_context = _require_role_assignment_context(context)

    await _require_replica_model(
        session=session,
        model_type=ActorReplicaModel,
        row_id=request.actor_id,
        label="actor_id",
    )
    await _require_replica_model(
        session=session,
        model_type=RoleConfigReplicaModel,
        row_id=role_config_id,
        label="role_config_id",
    )
    if request.object_instance_graph_branch_id is not None:
        await _require_replica_model(
            session=session,
            model_type=ObjectInstanceGraphBranchReplicaModel,
            row_id=request.object_instance_graph_branch_id,
            label="object_instance_graph_branch_id",
        )

    resolved_scope = await _resolve_class_instance_scope(
        session=session,
        class_instance_identity_id=request.class_instance_identity_id,
        role_config_id=role_config_id,
    )
    planned_binding = _planned_binding_for_scope(
        actor_id=request.actor_id,
        role_config_id=role_config_id,
        resolved_scope=resolved_scope,
        object_instance_graph_branch_key=branch_key,
        object_instance_graph_branch_id=request.object_instance_graph_branch_id,
    )

    role = await _materialize_lane_root(
        context=resolved_context,
        root_id=planned_binding.role_id,
        projection_name="Role",
        root_type=Role,
    )
    if role is None or not _role_matches(
        role,
        role_config_id=role_config_id,
        object_instance_graph_identity_id=resolved_scope.object_instance_graph_identity_id,
        object_instance_graph_branch_key=branch_key,
        object_instance_graph_branch_id=request.object_instance_graph_branch_id,
    ):
        return RoleUnassignmentReceipt(
            request_id=request.request_id,
            binding=planned_binding,
            actor_role_removed=False,
            role_class_instance_removed=False,
            role_removed=False,
        )

    role_class_instance = _find_role_class_instance(
        role=role,
        class_instance_identity_id=resolved_scope.class_instance_identity_id,
        role_config_class_config_id=planned_binding.role_config_class_config_id,
    )
    if role_class_instance is None:
        return RoleUnassignmentReceipt(
            request_id=request.request_id,
            binding=planned_binding,
            actor_role_removed=False,
            role_class_instance_removed=False,
            role_removed=False,
        )

    actor_role = await _resolve_actor_role_by_id(
        context=resolved_context,
        actor_role_id=planned_binding.actor_role_id,
    )
    if actor_role is None or not _actor_role_matches(
        actor_role,
        actor_id=request.actor_id,
        role_id=role.id,
    ):
        return RoleUnassignmentReceipt(
            request_id=request.request_id,
            binding=planned_binding,
            actor_role_removed=False,
            role_class_instance_removed=False,
            role_removed=False,
        )

    if len(role.role_class_instances) > 1:
        raise ValueError(
            "role unassignment refuses ambiguous multi-class-instance role envelope: "
            + f"role_id={role.id} actor_id={request.actor_id} "
            + f"class_instance_identity_id={resolved_scope.class_instance_identity_id} "
            + f"role_class_instance_count={len(role.role_class_instances)}"
        )

    actor_roles_for_role = await _actor_roles_for_role(
        context=resolved_context,
        role_id=role.id,
    )
    if not any(existing.id == actor_role.id for existing in actor_roles_for_role):
        raise RuntimeError(
            "Role unassignment materialization could not confirm ActorRole membership "
            + f"for actor_role_id={actor_role.id} role_id={role.id}"
        )

    identity_branch_id = await _resolve_identity_branch_id_for_actor(
        context=resolved_context,
        session=session,
        actor_id=request.actor_id,
    )
    identity = await _materialize_lane_root(
        context=resolved_context,
        root_id=identity_branch_id,
        projection_name="Identity",
        root_type=Identity,
    )
    if identity is None:
        raise ValueError(
            "identity lane could not be materialized for role unassignment: "
            f"actor_id={request.actor_id} identity_branch_id={identity_branch_id}"
        )
    actor_role_lane = resolved_context.bind_lane(
        projection="Identity",
        branch_id=identity_branch_id,
    )
    with actor_role_lane.activate(commit=True, publish=False):
        ensured_actor = await identity.ensure_actor()
        if ensured_actor.id != request.actor_id:
            raise ValueError(
                "Role unassignment resolved a different actor from the identity lane: "
                f"expected_actor_id={request.actor_id} got_actor_id={ensured_actor.id} "
                f"identity_id={identity.id}"
            )
    actor = await _materialize_projection_lane_root_by_source_id(
        context=resolved_context,
        root_id=request.actor_id,
        projection_name="Identity",
        root_type=Actor,
    )
    if actor is None:
        raise RuntimeError(
            "Role unassignment could not rehydrate Actor target from Identity lane: "
            f"actor_id={request.actor_id} identity_branch_id={identity_branch_id}"
        )
    with actor_role_lane.activate(commit=True, publish=False):
        await actor.remove_role(role_id=role.id)

    role_class_instance_removed = False
    role_removed = False
    if len(actor_roles_for_role) == 1:
        role_lane = resolved_context.bind_lane(
            projection="Role",
            branch_id=role.id,
        )
        with role_lane.activate(commit=True, publish=False):
            await role.remove_class_instance(
                class_instance_identity_id=resolved_scope.class_instance_identity_id,
                role_config_class_config_id=planned_binding.role_config_class_config_id,
            )
            await role.delete()
        role_class_instance_removed = True
        role_removed = True

    return RoleUnassignmentReceipt(
        request_id=request.request_id,
        binding=planned_binding,
        actor_role_removed=True,
        role_class_instance_removed=role_class_instance_removed,
        role_removed=role_removed,
    )


async def resolve_role_assignments(
    *,
    request: RoleAssignmentResolveRequest,
    session: Session | None = None,
    context: RoleAssignmentMaterializationContext | None = None,
) -> RoleAssignmentResolveResult:
    branch_key = _normalize_branch_key(request.object_instance_graph_branch_key)
    role_config_id: UUID | None = None
    if request.role_config_id is not None or request.role_config_name is not None:
        role_config_id = _resolve_role_config_id(
            request.role_config_id, request.role_config_name
        )

    if session is None:
        raise ValueError(
            "resolve_role_assignments requires session to derive class-instance scope"
        )
    resolved_context = _require_role_assignment_context(context)

    resolved_scope = await _resolve_class_instance_scope(
        session=session,
        class_instance_identity_id=request.class_instance_identity_id,
        role_config_id=role_config_id,
    )

    commit_store = FSCommitStore()
    role_opg = _resolve_opg_by_name(resolved_context.index, name="Role")

    actor_roles_by_role_id: dict[UUID, list[ActorRole]] = {}
    if request.actor_id is None:
        actor_roles_by_role_id = await _actor_roles_by_role_id(context=resolved_context)

    bindings = []
    async for role_branch_id, _ in commit_store.iter_lane_heads_by_projection(
        projection_hash=role_opg.projection_hash
    ):
        role = await _materialize_lane_root(
            context=resolved_context,
            root_id=role_branch_id,
            projection_name="Role",
            root_type=Role,
        )
        if role is None:
            continue
        if not _role_matches(
            role,
            role_config_id=(
                role.role_config_id if role_config_id is None else role_config_id
            ),
            object_instance_graph_identity_id=resolved_scope.object_instance_graph_identity_id,
            object_instance_graph_branch_key=branch_key,
            object_instance_graph_branch_id=request.object_instance_graph_branch_id,
        ):
            continue
        if role_config_id is not None and role.role_config_id != role_config_id:
            continue

        role_class_instances = _find_matching_role_class_instances(
            role=role,
            class_instance_identity_id=resolved_scope.class_instance_identity_id,
            role_config_class_config_id=resolved_scope.role_config_class_config_id,
        )
        if not role_class_instances:
            continue

        resolved_actor_roles: tuple[ActorRole, ...]
        if request.actor_id is not None:
            actor_role_id = stable_actor_role_id(
                actor_id=request.actor_id, role_id=role.id
            )
            actor_role = await _resolve_actor_role_by_id(
                context=resolved_context,
                actor_role_id=actor_role_id,
            )
            if actor_role is None or not _actor_role_matches(
                actor_role, actor_id=request.actor_id, role_id=role.id
            ):
                continue
            resolved_actor_roles = (actor_role,)
        else:
            resolved_actor_roles = tuple(actor_roles_by_role_id.get(role.id, ()))
            if not resolved_actor_roles:
                continue

        for role_class_instance in role_class_instances:
            for actor_role in resolved_actor_roles:
                if not _actor_role_matches(
                    actor_role, actor_id=actor_role.actor_id, role_id=role.id
                ):
                    continue
                bindings.append(
                    _binding_from_ids(
                        actor_id=actor_role.actor_id,
                        role_config_id=role.role_config_id,
                        role_id=role.id,
                        actor_role_id=actor_role.id,
                        role_class_instance_id=role_class_instance.id,
                        class_instance_identity_id=resolved_scope.class_instance_identity_id,
                        role_config_class_config_id=role_class_instance.role_config_class_config_id,
                        object_instance_graph_identity_id=resolved_scope.object_instance_graph_identity_id,
                        object_instance_graph_branch_key=branch_key,
                        object_instance_graph_branch_id=role.object_instance_graph_branch_id,
                    )
                )
    bindings.sort(
        key=lambda binding: (
            str(binding.actor_id),
            str(binding.role_config_id),
            str(binding.actor_role_id),
        )
    )
    return RoleAssignmentResolveResult(
        request_id=request.request_id,
        bindings=bindings,
    )


async def _add_actor_role_on_identity_lane(
    *,
    context: RoleAssignmentMaterializationContext,
    session: Session,
    actor_id: UUID,
    role_id: UUID,
) -> None:
    identity_branch_id = await _resolve_identity_branch_id_for_actor(
        context=context,
        session=session,
        actor_id=actor_id,
    )
    identity = await _materialize_lane_root(
        context=context,
        root_id=identity_branch_id,
        projection_name="Identity",
        root_type=Identity,
    )
    if identity is None:
        raise ValueError(
            "identity lane could not be materialized for role assignment: "
            f"actor_id={actor_id} identity_branch_id={identity_branch_id}"
        )

    identity_lane = context.bind_lane(
        projection="Identity",
        branch_id=identity_branch_id,
    )
    with identity_lane.activate(commit=True, publish=False):
        ensured_actor = await identity.ensure_actor()
        if ensured_actor.id != actor_id:
            raise ValueError(
                "Role assignment resolved a different actor from the identity lane: "
                f"expected_actor_id={actor_id} got_actor_id={ensured_actor.id} "
                f"identity_id={identity.id}"
            )
    actor = await _materialize_projection_lane_root_by_source_id(
        context=context,
        root_id=actor_id,
        projection_name="Identity",
        root_type=Actor,
    )
    if actor is None:
        raise RuntimeError(
            "Role assignment could not rehydrate Actor target from Identity lane: "
            f"actor_id={actor_id} identity_branch_id={identity_branch_id}"
        )
    with identity_lane.activate(commit=True, publish=False):
        await actor.add_role(role_id=role_id)


async def _actor_roles_by_role_id(
    *,
    context: RoleAssignmentMaterializationContext,
) -> dict[UUID, list[ActorRole]]:
    commit_store = FSCommitStore()
    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    actor_roles_by_role_id: dict[UUID, list[ActorRole]] = {}
    async for identity_branch_id, _ in commit_store.iter_lane_heads_by_projection(
        projection_hash=identity_opg.projection_hash
    ):
        materialized = await _materialize_projection_lane_oig(
            context=context,
            branch_id=identity_branch_id,
            projection_name="Identity",
        )
        if materialized is None:
            continue
        opg, oig = materialized
        for actor_role in _reify_oig_models_by_type(
            context=context,
            opg=opg,
            oig=oig,
            branch_id=identity_branch_id,
            model_type=ActorRole,
        ):
            actor_roles_by_role_id.setdefault(actor_role.role_id, []).append(actor_role)
    return actor_roles_by_role_id


async def _resolve_identity_branch_id_for_actor(
    *,
    context: RoleAssignmentMaterializationContext,
    session: Session,
    actor_id: UUID,
) -> UUID:
    actor_replica = await _load_replica_model_by_id(
        session=session,
        model_type=ActorReplicaModel,
        row_id=actor_id,
        label="actor_id",
    )
    if actor_replica is not None and actor_replica.identity_id is not None:
        return actor_replica.identity_id

    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    binding = await resolve_actor_identity_binding(
        index=context.index,
        actor_id=actor_id,
        identity_projection_hash=identity_opg.projection_hash,
    )
    if binding is None:
        raise ValueError(f"missing identity lane for actor_id: {actor_id}")
    return binding.identity_branch_id


async def _materialize_lane_root(
    *,
    context: RoleAssignmentMaterializationContext,
    root_id: UUID,
    projection_name: str,
    root_type: type[_TRoot],
) -> _TRoot | None:
    materialized = await _materialize_projection_lane_oig(
        context=context,
        branch_id=root_id,
        projection_name=projection_name,
    )
    if materialized is None:
        return None
    opg, oig = materialized
    root = reify_oig_root_model(
        index=context.index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=root_id,
    )
    if root is not None:
        return root
    return await _materialize_projection_lane_root_by_source_id(
        context=context,
        root_id=root_id,
        projection_name=projection_name,
        root_type=root_type,
    )


async def _materialize_projection_lane_root_by_source_id(
    *,
    context: RoleAssignmentMaterializationContext,
    root_id: UUID,
    projection_name: str,
    root_type: type[_TRoot],
) -> _TRoot | None:
    opg = _resolve_opg_by_name(context.index, name=projection_name)
    class_config = root_type.get_class_config()
    if class_config is None or class_config.id is None:
        return None
    async for branch_id, _ in FSCommitStore().iter_lane_heads_by_projection(
        projection_hash=opg.projection_hash,
    ):
        materialized = await _materialize_projection_lane_oig(
            context=context,
            branch_id=branch_id,
            projection_name=projection_name,
        )
        if materialized is None:
            continue
        _opg, oig = materialized
        target_instance_id: UUID | None = None
        for class_instance in oig.class_instances:
            if class_instance.class_config_id != class_config.id:
                continue
            if (
                class_instance.id == root_id
                or class_instance.source_object_id == root_id
            ):
                target_instance_id = class_instance.id
                break
        if target_instance_id is None:
            continue
        root = reify_oig_target_model(
            index=context.index,
            opg=opg,
            oig=oig,
            model_type=root_type,
            target_class_instance_id=target_instance_id,
            branch_id=branch_id,
        )
        if root is not None:
            return root
    return None


async def _materialize_projection_lane_oig(
    *,
    context: RoleAssignmentMaterializationContext,
    branch_id: UUID,
    projection_name: str,
) -> tuple[ObjectProjectionGraphModel, ObjectInstanceGraph] | None:
    opg = _resolve_opg_by_name(context.index, name=projection_name)
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=context.index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=context.index.attribute_configs_by_id,
        class_configs_by_id=context.index.class_configs_by_id,
    )
    return opg, oig


def _reify_oig_model_by_source_id(
    *,
    context: RoleAssignmentMaterializationContext,
    opg: ObjectProjectionGraphModel,
    oig: ObjectInstanceGraph,
    branch_id: UUID,
    model_type: type[_TRoot],
    root_id: UUID,
) -> _TRoot | None:
    class_config = model_type.get_class_config()
    if class_config is None or class_config.id is None:
        return None
    for class_instance in oig.class_instances:
        if class_instance.class_config_id != class_config.id:
            continue
        if class_instance.id != root_id and class_instance.source_object_id != root_id:
            continue
        return reify_oig_target_model(
            index=context.index,
            opg=opg,
            oig=oig,
            model_type=model_type,
            target_class_instance_id=class_instance.id,
            branch_id=branch_id,
        )
    return None


def _reify_oig_models_by_type(
    *,
    context: RoleAssignmentMaterializationContext,
    opg: ObjectProjectionGraphModel,
    oig: ObjectInstanceGraph,
    branch_id: UUID,
    model_type: type[_TRoot],
) -> list[_TRoot]:
    class_config = model_type.get_class_config()
    if class_config is None or class_config.id is None:
        return []
    models: list[_TRoot] = []
    for class_instance in oig.class_instances:
        if class_instance.class_config_id != class_config.id:
            continue
        model = reify_oig_target_model(
            index=context.index,
            opg=opg,
            oig=oig,
            model_type=model_type,
            target_class_instance_id=class_instance.id,
            branch_id=branch_id,
        )
        if model is not None:
            models.append(model)
    return models


def _resolve_opg_by_name(
    index: MetaGraphRuntimeIndex,
    *,
    name: str,
) -> ObjectProjectionGraphModel:
    norm = name.strip().casefold()
    matches = [
        opg
        for opg in index.opg_by_hash.values()
        if str(opg.name or "").strip().casefold() == norm
    ]
    if not matches:
        available = sorted(
            {
                str(opg.name or "").strip()
                for opg in index.opg_by_hash.values()
                if str(opg.name or "").strip()
            }
        )
        raise RuntimeError(f"OPG not found: name={name!r} (available={available})")
    if len(matches) > 1:
        raise RuntimeError(f"Duplicate OPG name={name!r} (count={len(matches)})")
    return matches[0]


def _require_role_assignment_context(
    context: RoleAssignmentMaterializationContext | None,
) -> RoleAssignmentMaterializationContext:
    if context is None:
        raise ValueError("RoleAssignment materialization context is required.")
    return context


__all__ = [
    "RoleAssignmentMaterializationContext",
    "ensure_role_assignment",
    "resolve_role_assignments",
    "unassign_role",
]
