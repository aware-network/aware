from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import TypeAlias, TypeVar, cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionBridgeConfig,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionEnsureReceipt,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionEnsureRequest,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionResolveRequest,
)
from aware_identity_service_dto.actor.subscription import (
    ActorSubscriptionResolveResult,
)
from aware_identity_ontology.actor.actor import Actor
from aware_identity_ontology.actor.actor_subscription import ActorSubscription
from aware_identity_ontology.actor.actor_subscription_enums import (
    SubscriptionAddressingPolicy,
    SubscriptionFilterMode,
    SubscriptionStatus,
)
from aware_identity_ontology.identity.identity import Identity
from aware_identity_ontology.stable_ids import stable_actor_subscription_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.materialization.context import MaterializationRuntimeContext
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_meta.runtime.oig_value_decoder import decode_oig_attribute_value
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph as ObjectProjectionGraphModel,
)
from aware_identity.materialization.bootstrap import (
    resolve_actor_identity_binding,
)

_EnumT = TypeVar("_EnumT", bound=Enum)

ActorSubscriptionMaterializationContext: TypeAlias = MaterializationRuntimeContext


async def ensure_actor_subscription(
    *,
    request: ActorSubscriptionEnsureRequest,
    context: ActorSubscriptionMaterializationContext | None = None,
) -> ActorSubscriptionEnsureReceipt:
    resolved_context = _require_actor_subscription_context(context)
    subscription_id = stable_actor_subscription_id(
        actor_id=request.actor_id,
        event_config_condition_config_scope_id=request.event_config_condition_config_scope_id,
        name=request.name,
    )
    commits = FSCommitStore()

    await _require_lane_head(
        commits=commits,
        context=resolved_context,
        projection_name="EventConfigConditionConfigScope",
        branch_id=request.event_config_condition_config_scope_id,
        label="event_config_condition_config_scope_id",
    )
    subscription_created = (
        await _resolve_subscription_by_id(
            context=resolved_context,
            subscription_id=subscription_id,
        )
        is None
    )

    if subscription_created:
        await _add_actor_subscription_on_identity_lane(
            context=resolved_context,
            request=request,
        )

    subscription = await _resolve_subscription_by_id(
        context=resolved_context,
        subscription_id=subscription_id,
    )
    if subscription is None:
        raise RuntimeError(
            "Actor subscription materialization did not expose bridge config: "
            + f"actor_subscription_id={subscription_id}"
        )
    return ActorSubscriptionEnsureReceipt(
        request_id=request.request_id,
        subscription=subscription,
        subscription_created=subscription_created,
        info="identity actor-subscription ensured",
    )


async def resolve_actor_subscriptions(
    *,
    request: ActorSubscriptionResolveRequest,
    context: ActorSubscriptionMaterializationContext | None = None,
) -> ActorSubscriptionResolveResult:
    resolved_context = _require_actor_subscription_context(context)
    subscriptions = await _list_subscriptions(context=resolved_context)
    filtered = [
        subscription
        for subscription in subscriptions
        if _subscription_matches(subscription=subscription, request=request)
    ]
    filtered.sort(
        key=lambda subscription: (-subscription.priority, str(subscription.id))
    )
    return ActorSubscriptionResolveResult(
        request_id=request.request_id,
        subscriptions=filtered,
        info="identity actor-subscriptions resolved",
    )


async def actor_subscription_bridge_config(
    *,
    context: ActorSubscriptionMaterializationContext,
    subscription: ActorSubscription,
) -> ActorSubscriptionBridgeConfig | None:
    return await _subscription_bridge_config(context=context, subscription=subscription)


async def _resolve_subscription_by_id(
    *,
    context: ActorSubscriptionMaterializationContext,
    subscription_id: UUID,
) -> ActorSubscriptionBridgeConfig | None:
    subscriptions = await _list_subscriptions(context=context)
    return next(
        (
            subscription
            for subscription in subscriptions
            if subscription.id == subscription_id
        ),
        None,
    )


async def _list_subscriptions(
    *,
    context: ActorSubscriptionMaterializationContext,
) -> list[ActorSubscriptionBridgeConfig]:
    commit_store = FSCommitStore()
    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    subscriptions: list[ActorSubscriptionBridgeConfig] = []
    async for identity_branch_id, _ in commit_store.iter_lane_heads_by_projection(
        projection_hash=identity_opg.projection_hash,
    ):
        oig = await _materialize_identity_lane_oig(
            context=context,
            branch_id=identity_branch_id,
        )
        if oig is None:
            continue
        for obj in _actor_subscriptions_from_identity_oig(context=context, oig=oig):
            bridge = await _subscription_bridge_config(
                context=context,
                subscription=obj,
            )
            if bridge is not None:
                subscriptions.append(bridge)
    return subscriptions


async def _add_actor_subscription_on_identity_lane(
    *,
    context: ActorSubscriptionMaterializationContext,
    request: ActorSubscriptionEnsureRequest,
) -> None:
    identity_branch_id, identity = await _materialize_identity_for_actor(
        context=context,
        actor_id=request.actor_id,
    )
    lane = context.bind_lane(
        projection="Identity",
        branch_id=identity_branch_id,
    )
    with lane.activate(commit=True, publish=False):
        actor = await identity.ensure_actor()
        if actor.id != request.actor_id:
            raise ValueError(
                "ActorSubscription ensure resolved a different actor from the identity lane: "
                f"expected_actor_id={request.actor_id} got_actor_id={actor.id} "
                f"identity_id={identity.id}"
            )
        await actor.add_subscription(
            event_config_condition_config_scope_id=request.event_config_condition_config_scope_id,
            name=request.name,
            description=request.description,
            action_type=request.action_type,
            event_config_action_config_ids=list(
                request.event_config_action_config_ids or []
            ),
            addressing_policy=_coerce_enum(
                SubscriptionAddressingPolicy,
                request.addressing_policy,
                default=SubscriptionAddressingPolicy.any,
                label="addressing_policy",
            ),
            is_enabled=request.is_enabled,
            status=_coerce_enum(
                SubscriptionStatus,
                request.status,
                default=SubscriptionStatus.active,
                label="status",
            ),
            filter_mode=_coerce_enum(
                SubscriptionFilterMode,
                request.filter_mode,
                default=SubscriptionFilterMode.all_instances,
                label="filter_mode",
            ),
            filter_config=_coerce_filter_config(request.filter_config),
            priority=request.priority,
            batch_mode=request.batch_mode,
            batch_window_ms=request.batch_window_ms,
            max_batch_size=request.max_batch_size,
            require_read_access=request.require_read_access,
            check_ownership=request.check_ownership,
            rate_limit_per_minute=request.rate_limit_per_minute,
            rate_limit_per_hour=request.rate_limit_per_hour,
        )


async def _subscription_bridge_config(
    *,
    context: ActorSubscriptionMaterializationContext,
    subscription: ActorSubscription,
) -> ActorSubscriptionBridgeConfig | None:
    scope_values = await _event_config_condition_config_scope_values(
        context=context,
        scope_id=subscription.event_config_condition_config_scope_id,
    )
    if scope_values is None:
        return None

    action_config_ids = [
        action_config.id
        for action_config in subscription.event_config_action_configs
        if action_config.id is not None
    ]
    return ActorSubscriptionBridgeConfig(
        id=subscription.id,
        actor_id=subscription.actor_id,
        event_config_condition_config_scope_id=subscription.event_config_condition_config_scope_id,
        event_config_condition_config_id=scope_values[
            "event_config_condition_config_id"
        ],
        object_instance_graph_identity_id=scope_values[
            "object_instance_graph_identity_id"
        ],
        object_instance_graph_branch_id=scope_values["object_instance_graph_branch_id"],
        name=subscription.name,
        action_type=subscription.action_type,
        event_config_action_config_ids=action_config_ids,
        addressing_policy=str(
            getattr(
                subscription.addressing_policy, "value", subscription.addressing_policy
            )
        ),
        is_enabled=subscription.is_enabled,
        status=str(getattr(subscription.status, "value", subscription.status)),
        priority=subscription.priority,
        filter_config=subscription.filter_config,
    )


def _event_config_condition_config_scope_type():
    from aware_reactivity_ontology.event.event_config_condition_config_scope import (
        EventConfigConditionConfigScope,
    )

    return EventConfigConditionConfigScope


async def _event_config_condition_config_scope_values(
    *,
    context: ActorSubscriptionMaterializationContext,
    scope_id: UUID,
) -> dict[str, UUID | None] | None:
    opg = _resolve_opg_by_name(
        context.index,
        name="EventConfigConditionConfigScope",
    )
    scope_type = _event_config_condition_config_scope_type()
    class_config = scope_type.get_class_config()
    if class_config is None or class_config.id is None:
        return None
    async for branch_id, _ in FSCommitStore().iter_lane_heads_by_projection(
        projection_hash=opg.projection_hash,
    ):
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=context.index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=context.index.attribute_configs_by_id,
            class_configs_by_id=context.index.class_configs_by_id,
        )
        for class_instance in oig.class_instances:
            if class_instance.class_config_id != class_config.id:
                continue
            if (
                class_instance.id != scope_id
                and class_instance.source_object_id != scope_id
            ):
                continue
            values = _class_instance_values(
                context=context, class_instance=class_instance
            )
            return {
                "event_config_condition_config_id": _coerce_required_uuid(
                    values.get("event_config_condition_config_id"),
                    label="event_config_condition_config_id",
                ),
                "object_instance_graph_identity_id": _coerce_required_uuid(
                    values.get("object_instance_graph_identity_id"),
                    label="object_instance_graph_identity_id",
                ),
                "object_instance_graph_branch_id": _coerce_uuid(
                    values.get("object_instance_graph_branch_id")
                ),
            }
    return None


async def _materialize_identity_for_actor(
    *,
    context: ActorSubscriptionMaterializationContext,
    actor_id: UUID,
) -> tuple[UUID, Identity]:
    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    binding = await resolve_actor_identity_binding(
        index=context.index,
        actor_id=actor_id,
        identity_projection_hash=identity_opg.projection_hash,
    )
    if binding is None:
        raise ValueError(f"missing identity lane for actor_id: {actor_id}")

    identity = await _materialize_lane_root(
        context=context,
        root_id=binding.identity_branch_id,
        projection_name="Identity",
        root_type=Identity,
    )
    if identity is None:
        raise ValueError(
            "identity lane could not be materialized for actor write: "
            f"actor_id={actor_id} identity_branch_id={binding.identity_branch_id}"
        )
    if identity.id != binding.identity_id:
        raise ValueError(
            "identity binding mismatch for actor write: "
            f"actor_id={actor_id} binding_identity_id={binding.identity_id} "
            f"lane_identity_id={identity.id}"
        )
    return binding.identity_branch_id, identity


async def _materialize_lane_root(
    *,
    context: ActorSubscriptionMaterializationContext,
    root_id: UUID,
    projection_name: str,
    root_type: type,
):
    opg = _resolve_opg_by_name(context.index, name=projection_name)
    head = await FSCommitStore().head(
        branch_id=root_id,
        projection_hash=opg.projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    oig, _ = await OIGMaterializer().get(
        branch_id=root_id,
        ocg=context.index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=context.index.attribute_configs_by_id,
        class_configs_by_id=context.index.class_configs_by_id,
    )
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
    context: ActorSubscriptionMaterializationContext,
    root_id: UUID,
    projection_name: str,
    root_type: type,
):
    opg = _resolve_opg_by_name(context.index, name=projection_name)
    class_config = root_type.get_class_config()
    if class_config is None or class_config.id is None:
        return None
    async for branch_id, _ in FSCommitStore().iter_lane_heads_by_projection(
        projection_hash=opg.projection_hash,
    ):
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=context.index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=context.index.attribute_configs_by_id,
            class_configs_by_id=context.index.class_configs_by_id,
        )
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
        root = reify_oig_root_model(
            index=context.index,
            opg=opg,
            oig=oig,
            model_type=root_type,
            root_id=root_id,
            branch_id=branch_id,
        )
        if root is not None:
            return root
    return None


async def _materialize_identity_lane_oig(
    *,
    context: ActorSubscriptionMaterializationContext,
    branch_id: UUID,
) -> ObjectInstanceGraph | None:
    identity_opg = _resolve_opg_by_name(context.index, name="Identity")
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=identity_opg.projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=context.index.ocg,
        opg=identity_opg,
        commit_id=None,
        attribute_configs_by_id=context.index.attribute_configs_by_id,
        class_configs_by_id=context.index.class_configs_by_id,
    )
    return oig


def _actor_subscriptions_from_identity_oig(
    *,
    context: ActorSubscriptionMaterializationContext,
    oig: ObjectInstanceGraph,
) -> list[ActorSubscription]:
    class_config = ActorSubscription.get_class_config()
    if class_config is None or class_config.id is None:
        raise RuntimeError("ActorSubscription ORM class missing ClassConfig binding")
    subscription_class_config_id = class_config.id
    subscriptions: list[ActorSubscription] = []
    for class_instance in oig.class_instances:
        if class_instance.class_config_id != subscription_class_config_id:
            continue
        values = _class_instance_values(context=context, class_instance=class_instance)
        subscription_id = (
            _coerce_uuid(values.get("id"))
            or class_instance.source_object_id
            or class_instance.id
        )
        actor_id = _coerce_uuid(
            values.get("actor_id")
        ) or _actor_id_for_subscription_from_identity_oig(
            oig=oig,
            subscription_class_instance_id=class_instance.id,
        )
        if actor_id is None:
            raise ValueError("ActorSubscription OIG row missing actor_id")
        scope_id = _coerce_required_uuid(
            values.get("event_config_condition_config_scope_id"),
            label="event_config_condition_config_scope_id",
        )
        name = str(values.get("name") or "").strip()
        if subscription_id is None or not name:
            continue
        action_config_ids = _event_config_action_config_ids_from_identity_oig(
            context=context,
            oig=oig,
            subscription_class_instance_id=class_instance.id,
        )
        subscriptions.append(
            ActorSubscription.model_construct(
                id=subscription_id,
                actor_id=actor_id,
                event_config_condition_config_scope_id=scope_id,
                name=name,
                description=values.get("description"),
                action_type=values.get("action_type"),
                event_config_action_configs=[
                    _event_config_action_config_type().model_construct(
                        id=action_config_id
                    )
                    for action_config_id in action_config_ids
                ],
                addressing_policy=values.get("addressing_policy") or "any",
                is_enabled=bool(values.get("is_enabled", True)),
                status=values.get("status") or "active",
                filter_mode=values.get("filter_mode") or "all_instances",
                filter_config=values.get("filter_config"),
                priority=_coerce_int(values.get("priority"), default=0),
                batch_mode=bool(values.get("batch_mode", False)),
                batch_window_ms=_coerce_int(
                    values.get("batch_window_ms"), default=1000
                ),
                max_batch_size=_coerce_int(values.get("max_batch_size"), default=100),
                require_read_access=bool(values.get("require_read_access", True)),
                check_ownership=bool(values.get("check_ownership", True)),
                rate_limit_per_minute=_coerce_optional_int(
                    values.get("rate_limit_per_minute")
                ),
                rate_limit_per_hour=_coerce_optional_int(
                    values.get("rate_limit_per_hour")
                ),
            )
        )
    return subscriptions


def _class_instance_values(
    *,
    context: ActorSubscriptionMaterializationContext,
    class_instance: object,
) -> dict[str, object]:
    values: dict[str, object] = {}
    for attribute in list(getattr(class_instance, "attributes", []) or []):
        attr_id = getattr(attribute, "attribute_config_id", None)
        attr_config = context.index.attribute_configs_by_id.get(attr_id)
        name = str(getattr(attr_config, "name", "") or "").strip()
        if not name:
            continue
        values[name] = decode_oig_attribute_value(
            getattr(attribute, "value_root", None),
            class_configs_by_id=context.index.class_configs_by_id,
        )
    return values


def _event_config_action_config_ids_from_identity_oig(
    *,
    context: ActorSubscriptionMaterializationContext,
    oig: ObjectInstanceGraph,
    subscription_class_instance_id: UUID | None,
) -> list[UUID]:
    if subscription_class_instance_id is None:
        return []
    target_type = _event_config_action_config_type()
    target_class_config = target_type.get_class_config()
    if target_class_config is None or target_class_config.id is None:
        return []
    class_instance_by_id = {ci.id: ci for ci in oig.class_instances}
    action_config_ids: list[UUID] = []
    for relationship in oig.class_instance_relationships:
        if relationship.source_class_instance_id != subscription_class_instance_id:
            continue
        target = class_instance_by_id.get(relationship.target_class_instance_id)
        if target is None or target.class_config_id != target_class_config.id:
            continue
        action_config_id = target.source_object_id or target.id
        if action_config_id is not None:
            action_config_ids.append(action_config_id)
    return sorted(set(action_config_ids), key=str)


def _actor_id_for_subscription_from_identity_oig(
    *,
    oig: ObjectInstanceGraph,
    subscription_class_instance_id: UUID | None,
) -> UUID | None:
    if subscription_class_instance_id is None:
        return None
    actor_class_config = Actor.get_class_config()
    if actor_class_config is None or actor_class_config.id is None:
        return None
    class_instance_by_id = {ci.id: ci for ci in oig.class_instances}
    for relationship in oig.class_instance_relationships:
        if relationship.target_class_instance_id != subscription_class_instance_id:
            continue
        source = class_instance_by_id.get(relationship.source_class_instance_id)
        if source is None or source.class_config_id != actor_class_config.id:
            continue
        return source.source_object_id or source.id
    return None


def _event_config_action_config_type():
    from aware_reactivity_ontology.event.event_config_action_config import (
        EventConfigActionConfig,
    )

    return EventConfigActionConfig


def _coerce_required_uuid(value: object, *, label: str) -> UUID:
    resolved = _coerce_uuid(value)
    if resolved is None:
        raise ValueError(f"ActorSubscription OIG row missing {label}")
    return resolved


def _coerce_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    return None


def _coerce_optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _coerce_int(value, default=0)


def _coerce_int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip():
        return int(value)
    return default


def _subscription_matches(
    *,
    subscription: ActorSubscriptionBridgeConfig,
    request: ActorSubscriptionResolveRequest,
) -> bool:
    if request.actor_id is not None and subscription.actor_id != request.actor_id:
        return False
    if (
        request.event_config_condition_config_id is not None
        and subscription.event_config_condition_config_id
        != request.event_config_condition_config_id
    ):
        return False
    if (
        request.object_instance_graph_identity_id is not None
        and subscription.object_instance_graph_identity_id
        != request.object_instance_graph_identity_id
    ):
        return False
    if (
        request.object_instance_graph_branch_id is not None
        and subscription.object_instance_graph_branch_id
        != request.object_instance_graph_branch_id
    ):
        return False
    if not request.include_disabled and not subscription.is_enabled:
        return False
    if not request.include_inactive and subscription.status != "active":
        return False
    return True


async def _require_lane_head(
    *,
    commits: FSCommitStore,
    context: ActorSubscriptionMaterializationContext,
    projection_name: str,
    branch_id: UUID,
    label: str,
) -> None:
    if await _lane_head_exists(
        commits=commits,
        context=context,
        projection_name=projection_name,
        branch_id=branch_id,
    ):
        return
    raise ValueError(f"missing {label}: {branch_id}")


async def _lane_head_exists(
    *,
    commits: FSCommitStore,
    context: ActorSubscriptionMaterializationContext,
    projection_name: str,
    branch_id: UUID,
) -> bool:
    opg = _resolve_opg_by_name(context.index, name=projection_name)
    head = await commits.head(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
    )
    return head is not None and head.get("commit_id") is not None


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


def _coerce_enum(
    enum_cls: type[_EnumT],
    value: str | None,
    *,
    default: _EnumT,
    label: str,
) -> _EnumT:
    token = (value or default.value).strip()
    for member in enum_cls:
        if token == member.value or token == member.name:
            return member
    allowed = ", ".join(member.value for member in enum_cls)
    raise ValueError(
        f"invalid actor subscription {label}: {token!r} (allowed={allowed})"
    )


def _coerce_filter_config(value: object) -> JsonObject | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("actor subscription filter_config must be a JSON object")
    if not all(isinstance(key, str) for key in value.keys()):
        raise ValueError("actor subscription filter_config keys must be strings")
    return cast(JsonObject, dict(value))


def _require_actor_subscription_context(
    context: ActorSubscriptionMaterializationContext | None,
) -> ActorSubscriptionMaterializationContext:
    if context is None:
        raise ValueError("ActorSubscription materialization context is required.")
    return context


__all__ = [
    "ActorSubscriptionMaterializationContext",
    "actor_subscription_bridge_config",
    "ensure_actor_subscription",
    "resolve_actor_subscriptions",
]
