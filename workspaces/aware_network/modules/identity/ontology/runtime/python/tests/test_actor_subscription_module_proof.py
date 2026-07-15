from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_identity.handlers._generated import meta_handlers as identity_meta_handlers
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    ProofCall,
    SourceObjectId,
    run_meta_runtime_proof,
)
from aware_reactivity.handlers._generated import (
    meta_handlers as reactivity_meta_handlers,
)
from ._paths import REPO_ROOT


ACTION_CONFIG_CLASS_FQN = "aware_reactivity.action.ActionConfig"
ACTOR_CLASS_FQN = "aware_identity.actor.Actor"
CONDITION_CONFIG_CLASS_FQN = "aware_reactivity.condition.ConditionConfig"
EVENT_CONFIG_CLASS_FQN = "aware_reactivity.event.EventConfig"
EVENT_CONFIG_CONDITION_CONFIG_SCOPE_CLASS_FQN = (
    "aware_reactivity.event.EventConfigConditionConfigScope"
)
IDENTITY_CLASS_FQN = "aware_identity.identity.Identity"

_IDENTITY_META_HANDLERS_ANY: Any = identity_meta_handlers
_IDENTITY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _IDENTITY_META_HANDLERS_ANY,
)
_IDENTITY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _IDENTITY_META_HANDLERS_ANY,
)
_REACTIVITY_META_HANDLERS_ANY: Any = reactivity_meta_handlers
_REACTIVITY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _REACTIVITY_META_HANDLERS_ANY,
)
_REACTIVITY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _REACTIVITY_META_HANDLERS_ANY,
)


def _identity_reactivity_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return tuple(
        repo_root / path
        for path in (
            "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
            "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
            "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        )
    )


def _build_identity_reactivity_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_identity_reactivity_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            _IDENTITY_META_HANDLER_MODULE,
            _REACTIVITY_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _IDENTITY_META_BOOTSTRAP_MODULE,
            _REACTIVITY_META_BOOTSTRAP_MODULE,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


def _lane(
    *,
    actor_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> LaneIds:
    return LaneIds(
        branch_id=branch_id,
        actor_id=actor_id,
    )


async def _commit_reactivity_subscription_config(
    *,
    runtime: MetaGraphRuntime,
    actor_id: UUID,
    condition_name: str,
    event_name: str,
    condition_config_id: UUID,
    action_config_id: UUID,
    event_config_id: UUID,
    event_cfg_cond_cfg_id: UUID,
    event_cfg_action_cfg_id: UUID,
    event_cfg_scope_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_branch_id: UUID,
) -> None:
    action_name = f"{event_name}.execute"
    api_capability_endpoint_id = uuid5(
        NAMESPACE_URL,
        f"aware.identity.actor-subscription.api-endpoint:{action_name}",
    )

    await run_meta_runtime_proof(
        runtime=runtime,
        lane=_lane(
            actor_id=actor_id,
            branch_id=condition_config_id,
        ),
        opg_name="ConditionConfig",
        calls=[
            ProofCall(
                target="constructor",
                class_fqn=CONDITION_CONFIG_CLASS_FQN,
                function_name="create",
                args=[
                    condition_name,
                    "Detect newly appended human conversation messages.",
                ],
                expected_root_object_id=condition_config_id,
            ),
        ],
    )
    await run_meta_runtime_proof(
        runtime=runtime,
        lane=_lane(
            actor_id=actor_id,
            branch_id=action_config_id,
        ),
        opg_name="ActionConfig",
        calls=[
            ProofCall(
                target="constructor",
                class_fqn=ACTION_CONFIG_CLASS_FQN,
                function_name="create",
                args=[
                    action_name,
                    "Execute actor subscription action binding.",
                    api_capability_endpoint_id,
                    "agent.turn.execute",
                ],
                expected_root_object_id=action_config_id,
            )
        ],
    )
    _, event_assertions = await run_meta_runtime_proof(
        runtime=runtime,
        lane=_lane(
            actor_id=actor_id,
            branch_id=event_config_id,
        ),
        opg_name="EventConfig",
        calls=[
            ProofCall(
                target="constructor",
                class_fqn=EVENT_CONFIG_CLASS_FQN,
                function_name="create",
                args=[
                    event_name,
                    "Wake subscribed agents for conversation updates.",
                ],
                expected_root_object_id=event_config_id,
            ),
            ProofCall(
                target="instance",
                class_fqn=EVENT_CONFIG_CLASS_FQN,
                function_name="add_condition_config",
                object_id=SourceObjectId(event_config_id),
                args=[condition_config_id],
            ),
            ProofCall(
                target="instance",
                class_fqn=EVENT_CONFIG_CLASS_FQN,
                function_name="add_action_config",
                object_id=SourceObjectId(event_config_id),
                args=[action_config_id],
            ),
        ],
    )
    event_assertions.expect_instance(event_cfg_cond_cfg_id)
    event_assertions.expect_instance(event_cfg_action_cfg_id)
    event_assertions.expect_edge(
        source_id=event_config_id,
        target_id=event_cfg_cond_cfg_id,
        relationship_name="event_config_condition_configs",
    )
    event_assertions.expect_edge(
        source_id=event_config_id,
        target_id=event_cfg_action_cfg_id,
        relationship_name="event_config_action_configs",
    )

    await run_meta_runtime_proof(
        runtime=runtime,
        lane=_lane(
            actor_id=actor_id,
            branch_id=event_cfg_scope_id,
        ),
        opg_name="EventConfigConditionConfigScope",
        calls=[
            ProofCall(
                target="constructor",
                class_fqn=EVENT_CONFIG_CONDITION_CONFIG_SCOPE_CLASS_FQN,
                function_name="create_via_event_config_condition_config",
                args=[
                    event_cfg_cond_cfg_id,
                    object_instance_graph_identity_id,
                    object_instance_graph_branch_id,
                ],
                expected_root_object_id=event_cfg_scope_id,
            )
        ],
    )


@pytest.mark.asyncio
async def test_actor_subscription_portal_to_reactivity_event_config_registered(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    import aware_reactivity_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_identity_reactivity_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        idx = context.index

        identity_opg = next(
            opg for opg in idx.opg_by_hash.values() if opg.name == "Identity"
        )
        event_config_opg = next(
            opg for opg in idx.opg_by_hash.values() if opg.name == "EventConfig"
        )
        event_config_scope_opg = next(
            opg
            for opg in idx.opg_by_hash.values()
            if opg.name == "EventConfigConditionConfigScope"
        )

        subscription_portals = idx.portal_index.portals_by_source_projection_hash.get(
            identity_opg.projection_hash,
            [],
        )
        assert any(
            portal.reference_field_name == "event_config_condition_config_scope"
            and portal.target_projection_hash == event_config_scope_opg.projection_hash
            for portal in subscription_portals
        )
        assert any(
            portal.reference_field_name == "event_config_action_configs"
            and portal.target_projection_hash == event_config_opg.projection_hash
            for portal in subscription_portals
        )


@pytest.mark.asyncio
async def test_actor_subscription_create_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_identity_ontology  # noqa: F401
    import aware_reactivity_ontology  # noqa: F401
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_actor_subscription_id,
        stable_identity_id,
    )
    from aware_reactivity_ontology.stable_ids import (
        stable_action_config_id,
        stable_condition_config_id,
        stable_event_config_action_config_id,
        stable_event_config_condition_config_id,
        stable_event_config_condition_config_scope_id,
        stable_event_config_id,
    )

    public_key = f"ed25519:{'65' * 32}"
    identity_id = stable_identity_id(public_key=public_key, type="human")
    actor_id = stable_actor_id(identity_id=identity_id, key="default")
    condition_name = "conversation.has.new.user.message"
    event_name = "conversation.agent.wakeup"
    condition_config_id = stable_condition_config_id(name=condition_name)
    event_config_id = stable_event_config_id(name=event_name)
    event_cfg_cond_cfg_id = stable_event_config_condition_config_id(
        event_config_id=event_config_id,
        condition_config_id=condition_config_id,
    )
    action_name = f"{event_name}.execute"
    action_config_id = stable_action_config_id(name=action_name)
    event_cfg_action_cfg_id = stable_event_config_action_config_id(
        event_config_id=event_config_id,
        action_config_id=action_config_id,
    )
    object_instance_graph_identity_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/subscription/oigi",
    )
    object_instance_graph_branch_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/identity/subscription/oigb",
    )
    event_cfg_scope_id = stable_event_config_condition_config_scope_id(
        event_config_condition_config_id=event_cfg_cond_cfg_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
    )
    expected_subscription_id = stable_actor_subscription_id(
        actor_id=actor_id,
        event_config_condition_config_scope_id=event_cfg_scope_id,
        name=event_name,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_identity_reactivity_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=_lane(
                actor_id=actor_id,
                branch_id=identity_id,
            ),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=IDENTITY_CLASS_FQN,
                    function_name="signup",
                    args=[public_key],
                    expected_root_object_id=identity_id,
                ),
            ],
        )
        await _commit_reactivity_subscription_config(
            runtime=runtime,
            actor_id=actor_id,
            condition_name=condition_name,
            event_name=event_name,
            condition_config_id=condition_config_id,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
            event_cfg_cond_cfg_id=event_cfg_cond_cfg_id,
            event_cfg_action_cfg_id=event_cfg_action_cfg_id,
            event_cfg_scope_id=event_cfg_scope_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=_lane(
                actor_id=actor_id,
                branch_id=identity_id,
            ),
            opg_name="Identity",
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=ACTOR_CLASS_FQN,
                    function_name="add_subscription",
                    object_id=SourceObjectId(actor_id),
                    args=[
                        event_cfg_scope_id,
                        event_name,
                    ],
                    kwargs={
                        "priority": 5,
                        "batch_mode": True,
                        "batch_window_ms": 2500,
                        "max_batch_size": 64,
                        "action_type": "agent.turn.execute",
                        "event_config_action_config_ids": [event_cfg_action_cfg_id],
                        "status": "active",
                        "is_enabled": True,
                    },
                )
            ],
        )

        assertions.expect_root(identity_id)
        assertions.expect_instance(expected_subscription_id)
        assertions.expect_edge(source_id=actor_id, target_id=expected_subscription_id)
        assertions.expect_primitive(
            instance_id=expected_subscription_id,
            field_name="name",
            expected=event_name,
        )
        assertions.expect_primitive(
            instance_id=expected_subscription_id,
            field_name="priority",
            expected=5,
        )
        assertions.expect_primitive(
            instance_id=expected_subscription_id,
            field_name="batch_mode",
            expected=True,
        )
        assertions.expect_primitive(
            instance_id=expected_subscription_id,
            field_name="batch_window_ms",
            expected=2500,
        )
        assertions.expect_primitive(
            instance_id=expected_subscription_id,
            field_name="max_batch_size",
            expected=64,
        )
        assertions.expect_primitive(
            instance_id=expected_subscription_id,
            field_name="status",
            expected="active",
        )
        assertions.expect_primitive(
            instance_id=expected_subscription_id,
            field_name="is_enabled",
            expected=True,
        )
        assertions.expect_primitive(
            instance_id=expected_subscription_id,
            field_name="action_type",
            expected="agent.turn.execute",
        )
        assert result.branch_id == identity_id


def test_identity_list_actor_subscriptions_removed_from_generated_surface() -> None:
    import aware_identity_ontology  # noqa: F401
    import aware_reactivity_ontology  # noqa: F401

    generated_function_names = {
        key.function_name
        for key in identity_meta_handlers.AWARE_META_GRAPH_HANDLERS
        if key.owner_class_fqn == IDENTITY_CLASS_FQN
    }

    assert "list_actor_subscriptions" not in generated_function_names
