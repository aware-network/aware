from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest

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
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from aware_reactivity.handlers._generated import (
    meta_handlers as reactivity_meta_handlers,
)
from aware_reactivity.stable_ids import (
    stable_action_execution_id,
    stable_action_feedback_id,
    stable_action_id,
    stable_action_intent_id,
    stable_action_config_id,
    stable_condition_id,
    stable_condition_config_attribute_config_id,
    stable_condition_config_class_config_id,
    stable_condition_config_enum_config_id,
    stable_condition_config_enum_option_id,
    stable_condition_config_id,
    stable_condition_config_primitive_config_id,
    stable_condition_config_relationship_config_id,
    stable_event_condition_id,
    stable_event_config_action_config_id,
    stable_event_config_condition_config_id,
    stable_event_config_id,
    stable_event_id,
)

_TESTS_ROOT = Path(__file__).resolve().parent
KERNEL_WORKSPACE_ROOT = _TESTS_ROOT.parents[5]
REACTIVITY_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/reactivity/ontology/structure/aware.toml",
)


ACTION_CLASS_FQN = "aware_reactivity.default.action.Action"
ACTION_CONFIG_CLASS_FQN = "aware_reactivity.default.action.ActionConfig"
ACTION_EXECUTION_CLASS_FQN = "aware_reactivity.default.action.ActionExecution"
ACTION_FEEDBACK_CLASS_FQN = "aware_reactivity.default.action.ActionFeedback"
ACTION_INTENT_CLASS_FQN = "aware_reactivity.default.action.ActionIntent"
CONDITION_CLASS_FQN = "aware_reactivity.default.condition.Condition"
CONDITION_CONFIG_CLASS_FQN = "aware_reactivity.default.condition.ConditionConfig"
CONDITION_CONFIG_ATTRIBUTE_CONFIG_CLASS_FQN = "aware_reactivity.default.condition.ConditionConfigAttributeConfig"
CONDITION_CONFIG_CLASS_CONFIG_CLASS_FQN = "aware_reactivity.default.condition.ConditionConfigClassConfig"
EVENT_CLASS_FQN = "aware_reactivity.default.event.Event"
EVENT_CONFIG_CLASS_FQN = "aware_reactivity.default.event.EventConfig"

_REACTIVITY_META_HANDLERS_ANY: Any = reactivity_meta_handlers
_REACTIVITY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _REACTIVITY_META_HANDLERS_ANY,
)
_REACTIVITY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _REACTIVITY_META_HANDLERS_ANY,
)


def _build_reactivity_meta_runtime(
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=REACTIVITY_PACKAGE_MANIFEST_PATHS,
        workspace_root=KERNEL_WORKSPACE_ROOT,
        aware_root=aware_root,
        handler_modules=(_REACTIVITY_META_HANDLER_MODULE,),
        bootstrap_modules=(_REACTIVITY_META_BOOTSTRAP_MODULE,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


def _expect_uuid_primitive(assertions, *, instance_id, field_name, expected) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


def test_reactivity_module_proof_does_not_import_legacy_runtime() -> None:
    source = Path(__file__).read_text(encoding="utf-8")

    assert ("from " + "aware_" + "runtime") not in source
    assert ("import " + "aware_" + "runtime") not in source


@pytest.mark.asyncio
async def test_reactivity_condition_event_and_action_projection_roots_registered(tmp_path: Path, monkeypatch) -> None:
    import aware_reactivity_ontology  # noqa: F401

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs") as aware_root:
        runtime = _build_reactivity_meta_runtime(
            aware_root=aware_root,
        )
        assert runtime.context is not None
        idx = runtime.context.index

        condition_opg = next(opg for opg in idx.ocg.object_projection_graphs if opg.name == "ConditionConfig")
        event_opg = next(opg for opg in idx.ocg.object_projection_graphs if opg.name == "EventConfig")
        action_opg = next(opg for opg in idx.ocg.object_projection_graphs if opg.name == "ActionConfig")
        action_intent_opg = next(opg for opg in idx.ocg.object_projection_graphs if opg.name == "ActionIntent")

        assert any(node.is_root for node in condition_opg.object_projection_graph_nodes)
        assert any(node.is_root for node in event_opg.object_projection_graph_nodes)
        assert any(node.is_root for node in action_opg.object_projection_graph_nodes)
        assert any(node.is_root for node in action_intent_opg.object_projection_graph_nodes)


@pytest.mark.asyncio
async def test_reactivity_event_config_portals_to_condition_and_action_registered(tmp_path: Path, monkeypatch) -> None:
    import aware_reactivity_ontology  # noqa: F401

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs") as aware_root:
        runtime = _build_reactivity_meta_runtime(
            aware_root=aware_root,
        )
        assert runtime.context is not None
        idx = runtime.context.index

        condition_opg = next(opg for opg in idx.ocg.object_projection_graphs if opg.name == "ConditionConfig")
        action_opg = next(opg for opg in idx.ocg.object_projection_graphs if opg.name == "ActionConfig")
        event_opg = next(opg for opg in idx.ocg.object_projection_graphs if opg.name == "EventConfig")

        event_portals = [
            portal for portal in idx.portal_index.portals if portal.source_projection_hash == event_opg.projection_hash
        ]

        assert any(
            portal.reference_field_name == "condition_config"
            and portal.target_projection_hash == condition_opg.projection_hash
            for portal in event_portals
        )
        assert any(
            portal.reference_field_name == "action_config"
            and portal.target_projection_hash == action_opg.projection_hash
            for portal in event_portals
        )


@pytest.mark.asyncio
async def test_reactivity_condition_config_create_module_proof(tmp_path: Path, monkeypatch) -> None:
    import aware_reactivity_ontology  # noqa: F401
    from aware_reactivity_ontology.condition.condition_enums import (
        ConditionLogicStrategy,
    )

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs") as aware_root:
        runtime = _build_reactivity_meta_runtime(
            aware_root=aware_root,
        )
        name = "conversation.message.new"
        description = "Wake agent inference when a new message commit is received."
        expected_condition_config_id = stable_condition_config_id(name=name)

        lane = LaneIds(environment_id=uuid4(), process_id=uuid4(), thread_id=uuid4())
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ConditionConfig",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.default.condition.ConditionConfig",
                    function_name="create",
                    args=[name, description],
                    kwargs={"logic_strategy": ConditionLogicStrategy.all.value},
                    expected_root_object_id=expected_condition_config_id,
                )
            ],
        )

        assertions.expect_root(expected_condition_config_id)
        assertions.expect_instance(expected_condition_config_id)
        assertions.expect_primitive(instance_id=expected_condition_config_id, field_name="name", expected=name)
        assertions.expect_primitive(
            instance_id=expected_condition_config_id,
            field_name="description",
            expected=description,
        )
        assertions.expect_primitive(
            instance_id=expected_condition_config_id,
            field_name="is_enabled",
            expected=True,
        )
        assertions.expect_primitive(
            instance_id=expected_condition_config_id,
            field_name="is_system",
            expected=False,
        )
        assert result.root_object_id == expected_condition_config_id


@pytest.mark.asyncio
async def test_reactivity_condition_config_nested_policy_constructors_module_proof(tmp_path: Path, monkeypatch) -> None:
    import aware_reactivity_ontology  # noqa: F401
    from aware_reactivity_ontology.condition.condition_enums import (
        ConditionOperator,
        EnumMatchMode,
        RelationshipEvalMode,
    )

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs") as aware_root:
        runtime = _build_reactivity_meta_runtime(
            aware_root=aware_root,
        )
        assert runtime.context is not None
        idx = runtime.context.index
        condition_config_fqn = "aware_reactivity.default.condition.ConditionConfig"
        condition_class_config_fqn = "aware_reactivity.default.condition.ConditionConfigClassConfig"
        condition_attr_config_fqn = "aware_reactivity.default.condition.ConditionConfigAttributeConfig"

        condition_cfg_cc = next(cc for cc in idx.class_configs_by_id.values() if cc.name == "ConditionConfig")
        condition_class_cfg_cc = next(
            cc for cc in idx.class_configs_by_id.values() if cc.name == "ConditionConfigClassConfig"
        )

        name_attr_cfg = next(
            link.attribute_config
            for link in condition_cfg_cc.class_config_attribute_configs
            if link.attribute_config is not None and link.attribute_config.name == "name"
        )
        logic_attr_cfg = next(
            link.attribute_config
            for link in condition_cfg_cc.class_config_attribute_configs
            if link.attribute_config is not None and link.attribute_config.name == "logic_strategy"
        )

        primitive_config_id = name_attr_cfg.type_descriptor.primitive_config_id
        assert primitive_config_id is not None

        enum_config_id = logic_attr_cfg.type_descriptor.enum_config_id
        assert enum_config_id is not None
        enum_config = logic_attr_cfg.type_descriptor.enum_config
        if enum_config is None:
            enum_config = next(
                (
                    node.enum_config
                    for node in idx.ocg.object_config_graph_nodes
                    if node.enum_config is not None and node.enum_config.id == enum_config_id
                ),
                None,
            )
        assert enum_config is not None
        enum_option_id = enum_config.enum_options[0].id

        class_config_relationship_id = next(
            rel.id
            for rel in condition_cfg_cc.class_config_relationships
            if rel.target_class_config_id == condition_class_cfg_cc.id
        )

        condition_name = "conversation.new.user.message.policy"
        condition_description = "Nested condition policy constructors proof"

        condition_config_id = stable_condition_config_id(name=condition_name)
        condition_class_config_id = stable_condition_config_class_config_id(
            condition_config_id=condition_config_id,
            class_config_id=condition_cfg_cc.id,
        )
        condition_attribute_config_id = stable_condition_config_attribute_config_id(
            condition_config_class_config_id=condition_class_config_id,
            attribute_config_id=name_attr_cfg.id,
            operator=ConditionOperator.equals.value,
            negate=False,
        )
        primitive_policy_id = stable_condition_config_primitive_config_id(
            condition_config_attribute_config_id=condition_attribute_config_id,
            primitive_config_id=primitive_config_id,
        )
        enum_policy_id = stable_condition_config_enum_config_id(
            condition_config_attribute_config_id=condition_attribute_config_id,
            enum_config_id=enum_config_id,
        )
        enum_option_policy_id = stable_condition_config_enum_option_id(
            condition_config_enum_config_id=enum_policy_id,
            enum_option_id=enum_option_id,
        )
        relationship_policy_id = stable_condition_config_relationship_config_id(
            condition_config_attribute_config_id=condition_attribute_config_id,
            class_config_relationship_id=class_config_relationship_id,
        )

        lane = LaneIds(environment_id=uuid4(), process_id=uuid4(), thread_id=uuid4())
        _, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ConditionConfig",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=condition_config_fqn,
                    function_name="create",
                    args=[condition_name, condition_description],
                    expected_root_object_id=condition_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=condition_config_fqn,
                    function_name="add_class_config",
                    object_id=ROOT_OBJECT_ID,
                    args=[condition_cfg_cc.id],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=condition_class_config_fqn,
                    function_name="add_attribute_config",
                    object_id=condition_class_config_id,
                    args=[name_attr_cfg.id, ConditionOperator.equals.value],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=condition_attr_config_fqn,
                    function_name="set_primitive_config",
                    object_id=condition_attribute_config_id,
                    args=[primitive_config_id, "user"],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=condition_attr_config_fqn,
                    function_name="set_enum_config",
                    object_id=condition_attribute_config_id,
                    kwargs={
                        "enum_config_id": enum_config_id,
                        "enum_option_ids": [enum_option_id],
                        "match_mode": EnumMatchMode.any_of.value,
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=condition_attr_config_fqn,
                    function_name="set_relationship_config",
                    object_id=condition_attribute_config_id,
                    kwargs={
                        "class_config_relationship_id": class_config_relationship_id,
                        "eval_mode": RelationshipEvalMode.exists.value,
                    },
                ),
            ],
        )

        assertions.expect_root(condition_config_id)
        assertions.expect_instance(condition_config_id)
        assertions.expect_instance(condition_class_config_id)
        assertions.expect_instance(condition_attribute_config_id)
        assertions.expect_instance(primitive_policy_id)
        assertions.expect_instance(enum_policy_id)
        assertions.expect_instance(enum_option_policy_id)
        assertions.expect_instance(relationship_policy_id)

        assertions.expect_edge(
            source_id=condition_config_id,
            target_id=condition_class_config_id,
            relationship_name="condition_config_class_configs",
        )
        assertions.expect_edge(
            source_id=condition_class_config_id,
            target_id=condition_attribute_config_id,
            relationship_name="condition_config_attribute_configs",
        )
        assertions.expect_edge(
            source_id=condition_attribute_config_id,
            target_id=primitive_policy_id,
            relationship_name="condition_config_primitive_config",
        )
        assertions.expect_edge(
            source_id=condition_attribute_config_id,
            target_id=enum_policy_id,
            relationship_name="condition_config_enum_config",
        )
        assertions.expect_edge(
            source_id=condition_attribute_config_id,
            target_id=relationship_policy_id,
            relationship_name="condition_config_relationship_config",
        )
        assertions.expect_edge(
            source_id=enum_policy_id,
            target_id=enum_option_policy_id,
            relationship_name="condition_config_enum_options",
        )

        assertions.expect_primitive(
            instance_id=condition_attribute_config_id,
            field_name="operator",
            expected=ConditionOperator.equals.value,
        )
        assertions.expect_primitive(
            instance_id=primitive_policy_id,
            field_name="primitive_value",
            expected="user",
        )
        assertions.expect_primitive(
            instance_id=enum_policy_id,
            field_name="match_mode",
            expected=EnumMatchMode.any_of.value,
        )
        assertions.expect_primitive(
            instance_id=relationship_policy_id,
            field_name="eval_mode",
            expected=RelationshipEvalMode.exists.value,
        )


@pytest.mark.asyncio
async def test_reactivity_event_config_add_condition_config_module_proof(tmp_path: Path, monkeypatch) -> None:
    import aware_reactivity_ontology  # noqa: F401

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs") as aware_root:
        runtime = _build_reactivity_meta_runtime(
            aware_root=aware_root,
        )
        event_name = "agent.turn.requested"
        event_description = "Canonical agent wake-up semantic event."
        event_config_id = stable_event_config_id(name=event_name)
        condition_config_id = uuid5(NAMESPACE_URL, "aware://tests/reactivity/condition-config")
        expected_binding_id = stable_event_config_condition_config_id(
            event_config_id=event_config_id,
            condition_config_id=condition_config_id,
        )

        lane = LaneIds(environment_id=uuid4(), process_id=uuid4(), thread_id=uuid4())
        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="EventConfig",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.default.event.EventConfig",
                    function_name="create",
                    args=[event_name, event_description],
                    expected_root_object_id=event_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn="aware_reactivity.default.event.EventConfig",
                    function_name="add_condition_config",
                    object_id=ROOT_OBJECT_ID,
                    args=[condition_config_id],
                    kwargs={
                        "execution_order": 10,
                        "priority": 3,
                        "cache_result": True,
                        "cache_ttl_seconds": 120,
                    },
                ),
            ],
        )

        assertions.expect_root(event_config_id)
        assertions.expect_instance(event_config_id)
        assertions.expect_primitive(instance_id=event_config_id, field_name="name", expected=event_name)
        assertions.expect_primitive(
            instance_id=event_config_id,
            field_name="description",
            expected=event_description,
        )

        assertions.expect_instance(expected_binding_id)
        assertions.expect_edge(source_id=event_config_id, target_id=expected_binding_id)
        assertions.expect_primitive(
            instance_id=expected_binding_id,
            field_name="execution_order",
            expected=10,
        )
        assertions.expect_primitive(instance_id=expected_binding_id, field_name="priority", expected=3)
        assertions.expect_primitive(instance_id=expected_binding_id, field_name="cache_result", expected=True)
        assertions.expect_primitive(
            instance_id=expected_binding_id,
            field_name="cache_ttl_seconds",
            expected=120,
        )
        assert result.root_object_id == event_config_id


@pytest.mark.asyncio
async def test_reactivity_event_config_add_action_config_module_proof(tmp_path: Path, monkeypatch) -> None:
    import aware_reactivity_ontology  # noqa: F401

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs") as aware_root:
        runtime = _build_reactivity_meta_runtime(
            aware_root=aware_root,
        )
        action_name = "agent.execute.turn"
        action_description = "Dispatch an agent runtime turn execution request."
        action_type = "agent.turn.execute"
        action_config_id = stable_action_config_id(name=action_name)

        event_name = "agent.turn.requested"
        event_description = "Canonical agent wake-up semantic event."
        event_config_id = stable_event_config_id(name=event_name)
        expected_binding_id = stable_event_config_action_config_id(
            event_config_id=event_config_id,
            action_config_id=action_config_id,
        )

        lane = LaneIds(environment_id=uuid4(), process_id=uuid4(), thread_id=uuid4())
        _, action_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ActionConfig",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.default.action.ActionConfig",
                    function_name="create",
                    args=[action_name, action_description, action_type],
                    expected_root_object_id=action_config_id,
                )
            ],
        )
        action_assertions.expect_root(action_config_id)
        action_assertions.expect_instance(action_config_id)
        action_assertions.expect_primitive(instance_id=action_config_id, field_name="name", expected=action_name)
        action_assertions.expect_primitive(
            instance_id=action_config_id,
            field_name="action_type",
            expected=action_type,
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="EventConfig",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.default.event.EventConfig",
                    function_name="create",
                    args=[event_name, event_description],
                    expected_root_object_id=event_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn="aware_reactivity.default.event.EventConfig",
                    function_name="add_action_config",
                    object_id=ROOT_OBJECT_ID,
                    args=[action_config_id],
                    kwargs={
                        "execution_order": 5,
                        "priority": 2,
                        "continue_on_fail": False,
                    },
                ),
            ],
        )

        assertions.expect_root(event_config_id)
        assertions.expect_instance(event_config_id)
        assertions.expect_instance(expected_binding_id)
        assertions.expect_edge(source_id=event_config_id, target_id=expected_binding_id)
        assertions.expect_primitive(
            instance_id=expected_binding_id,
            field_name="execution_order",
            expected=5,
        )
        assertions.expect_primitive(instance_id=expected_binding_id, field_name="priority", expected=2)
        assertions.expect_primitive(
            instance_id=expected_binding_id,
            field_name="continue_on_fail",
            expected=False,
        )
        assert result.root_object_id == event_config_id


@pytest.mark.asyncio
async def test_reactivity_runtime_evidence_constructors_module_proof(tmp_path: Path, monkeypatch) -> None:
    import aware_reactivity_ontology  # noqa: F401

    from aware_reactivity_ontology.action.action_enums import (
        ActionExecutionStatus,
        ActionFeedbackStage,
        ActionFeedbackStatus,
    )
    from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
    from aware_meta_ontology.stable_ids import (
        stable_object_instance_graph_commit_id,
        stable_object_instance_graph_id,
        stable_object_instance_graph_identity_id,
    )

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs") as aware_root:
        runtime = _build_reactivity_meta_runtime(
            aware_root=aware_root,
        )
        assert runtime.context is not None
        idx = runtime.context.index

        lane = LaneIds(environment_id=uuid4(), process_id=uuid4(), thread_id=uuid4())
        activation_id = uuid5(NAMESPACE_URL, "aware://tests/reactivity/runtime-evidence/activation")
        trigger_commit_id = uuid5(NAMESPACE_URL, "aware://tests/reactivity/runtime-evidence/commit")
        trigger_branch_id = uuid5(NAMESPACE_URL, "aware://tests/reactivity/runtime-evidence/branch")
        trigger_opg = next(opg for opg in idx.ocg.object_projection_graphs if opg.name == "Condition")
        _ocgi, trigger_opgi = resolve_meta_graph_ocgi_opgi(
            index=idx,
            projection_hash=trigger_opg.projection_hash,
        )
        assert trigger_opgi is not None
        trigger_oig_id = stable_object_instance_graph_id(
            object_projection_graph_id=trigger_opg.id,
            key=f"reactivity-runtime-evidence:{trigger_branch_id}",
        )
        trigger_oigi_id = stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=trigger_opgi.id,
            object_instance_graph_id=trigger_oig_id,
        )
        trigger_oig_commit_id = stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=trigger_oigi_id,
            commit_id=trigger_commit_id,
        )
        condition_config_id = uuid5(NAMESPACE_URL, "aware://tests/reactivity/runtime-evidence/condition-config")
        event_config_id = uuid5(NAMESPACE_URL, "aware://tests/reactivity/runtime-evidence/event-config")
        event_config_condition_config_id = uuid5(
            NAMESPACE_URL,
            "aware://tests/reactivity/runtime-evidence/event-config-condition-config",
        )
        action_config_id = uuid5(NAMESPACE_URL, "aware://tests/reactivity/runtime-evidence/action-config")
        actor_subscription_id = uuid5(
            NAMESPACE_URL,
            "aware://tests/reactivity/runtime-evidence/actor-subscription",
        )
        intent_key = f"{actor_subscription_id}:agent.turn.execute"
        actor_id = uuid5(NAMESPACE_URL, "aware://tests/reactivity/runtime-evidence/actor")
        target_actor_id = uuid5(NAMESPACE_URL, "aware://tests/reactivity/runtime-evidence/target-actor")

        expected_condition_id = stable_condition_id(
            config_id=condition_config_id,
            activation_id=activation_id,
        )
        expected_event_id = stable_event_id(
            config_id=event_config_id,
            activation_id=activation_id,
        )
        expected_event_condition_id = stable_event_condition_id(
            condition_id=expected_condition_id,
            config_id=event_config_condition_config_id,
            event_id=expected_event_id,
        )
        expected_action_id = stable_action_id(
            event_id=expected_event_id,
            config_id=action_config_id,
        )
        expected_action_intent_id = stable_action_intent_id(
            event_id=expected_event_id,
            config_id=action_config_id,
            intent_key=intent_key,
        )
        expected_action_execution_id = stable_action_execution_id(
            action_intent_id=expected_action_intent_id,
            execution_key="primary",
        )
        expected_action_feedback_id = stable_action_feedback_id(
            action_execution_id=expected_action_execution_id,
            sequence=1,
        )
        _, condition_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Condition",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.default.condition.Condition",
                    function_name="create",
                    args=[
                        condition_config_id,
                        activation_id,
                        trigger_oig_commit_id,
                    ],
                    expected_root_object_id=expected_condition_id,
                )
            ],
        )
        condition_assertions.expect_instance(expected_condition_id)
        _expect_uuid_primitive(
            condition_assertions,
            instance_id=expected_condition_id,
            field_name="trigger_object_instance_graph_commit_id",
            expected=trigger_oig_commit_id,
        )

        event_lane = LaneIds(
            environment_id=lane.environment_id,
            process_id=lane.process_id,
            thread_id=lane.thread_id,
            branch_id=uuid5(
                NAMESPACE_URL,
                "aware://tests/reactivity/runtime-evidence/event-branch",
            ),
        )
        event_result, event_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=event_lane,
            opg_name="Event",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.default.event.Event",
                    function_name="create",
                    args=[
                        event_config_id,
                        activation_id,
                        "agent.turn.requested",
                        "actor_subscription",
                    ],
                    expected_root_object_id=expected_event_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn="aware_reactivity.default.event.Event",
                    function_name="add_event_condition",
                    object_id=expected_event_id,
                    args=[
                        expected_condition_id,
                        event_config_condition_config_id,
                    ],
                ),
            ],
        )
        event_assertions.expect_instance(expected_event_id)
        event_assertions.expect_instance(expected_event_condition_id)
        event_assertions.expect_primitive(
            instance_id=expected_event_id,
            field_name="event_type",
            expected="agent.turn.requested",
        )

        action_lane = LaneIds(
            environment_id=event_lane.environment_id,
            process_id=event_lane.process_id,
            thread_id=event_lane.thread_id,
            branch_id=event_result.branch_id,
        )
        action_result, action_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=action_lane,
            opg_name="Action",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.default.action.Action",
                    function_name="create_via_event",
                    args=[
                        expected_event_id,
                        action_config_id,
                    ],
                    expected_root_object_id=expected_action_id,
                )
            ],
        )
        action_assertions.expect_instance(expected_action_id)
        action_assertions.expect_primitive(
            instance_id=expected_action_id,
            field_name="status",
            expected="requested",
        )

        action_intent_lane = LaneIds(
            environment_id=action_lane.environment_id,
            process_id=action_lane.process_id,
            thread_id=action_lane.thread_id,
            branch_id=action_result.branch_id,
        )
        action_intent_result, action_intent_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=action_intent_lane,
            opg_name="ActionIntent",
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn="aware_reactivity.default.action.ActionIntent",
                    function_name="create_via_event",
                    args=[
                        expected_event_id,
                        action_config_id,
                        intent_key,
                    ],
                    kwargs={
                        "action_type": "agent.turn.execute",
                        "actor_id": actor_id,
                        "target_actor_id": target_actor_id,
                        "actor_subscription_id": actor_subscription_id,
                        "action_payload": {"goal": "confirm_restaurant_reservation"},
                        "subscription_filter_config": {"branch_lane": "conversation"},
                        "priority": 9,
                    },
                    expected_root_object_id=expected_action_intent_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn="aware_reactivity.default.action.ActionIntent",
                    function_name="start_execution",
                    object_id=expected_action_intent_id,
                    kwargs={
                        "execution_key": "primary",
                        "status": ActionExecutionStatus.accepted.value,
                        "execution_context": {"executor": "agent"},
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn="aware_reactivity.default.action.ActionExecution",
                    function_name="add_feedback",
                    object_id=expected_action_execution_id,
                    args=[
                        1,
                        ActionFeedbackStage.dispatch.value,
                        ActionFeedbackStatus.accepted.value,
                    ],
                    kwargs={
                        "created_at_unix_ms": 1_775_923_200_000,
                        "message": "agent runtime accepted action intent",
                        "payload": {"executor_ref": "agent-runtime"},
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn="aware_reactivity.default.action.ActionExecution",
                    function_name="set_status",
                    object_id=expected_action_execution_id,
                    kwargs={
                        "status": ActionExecutionStatus.running.value,
                        "result_info": "agent run scheduled",
                    },
                ),
            ],
        )
        action_intent_assertions.expect_root(expected_action_intent_id)
        action_intent_assertions.expect_instance(expected_action_intent_id)
        action_intent_assertions.expect_instance(expected_action_execution_id)
        action_intent_assertions.expect_instance(expected_action_feedback_id)
        action_intent_assertions.expect_edge(
            source_id=expected_action_intent_id,
            target_id=expected_action_execution_id,
            relationship_name="action_executions",
        )
        action_intent_assertions.expect_edge(
            source_id=expected_action_execution_id,
            target_id=expected_action_feedback_id,
            relationship_name="action_feedback",
        )
        action_intent_assertions.expect_primitive(
            instance_id=expected_action_intent_id,
            field_name="action_type",
            expected="agent.turn.execute",
        )
        action_intent_assertions.expect_primitive(
            instance_id=expected_action_intent_id,
            field_name="intent_key",
            expected=intent_key,
        )
        action_intent_assertions.expect_primitive(
            instance_id=expected_action_execution_id,
            field_name="status",
            expected="running",
        )
        action_intent_assertions.expect_primitive(
            instance_id=expected_action_execution_id,
            field_name="result_info",
            expected="agent run scheduled",
        )
        action_intent_assertions.expect_primitive(
            instance_id=expected_action_feedback_id,
            field_name="stage",
            expected="dispatch",
        )
        action_intent_assertions.expect_primitive(
            instance_id=expected_action_feedback_id,
            field_name="status",
            expected="accepted",
        )

        idx = runtime.context.index
        event_portals = [
            portal
            for portal in idx.portal_index.portals
            if portal.source_projection_hash == event_result.projection_hash
        ]
        assert any(
            portal.reference_field_name == "actions" and portal.target_projection_hash == action_result.projection_hash
            for portal in event_portals
        )
        assert any(
            portal.reference_field_name == "action_intents"
            and portal.target_projection_hash == action_intent_result.projection_hash
            for portal in event_portals
        )


@pytest.mark.asyncio
async def test_reactivity_evidence_writer_requires_receipt_object_instance_graph_id() -> None:
    from aware_meta.receipts.notifications import (
        LaneCommitReceiptNotification,
    )
    from aware_reactivity.evidence import LaneReactivityEvidenceWriter
    from aware_reactivity_service_dto.reactivity.event_condition_binding_resolution import (
        EventConditionBindingResolution,
    )

    writer = LaneReactivityEvidenceWriter(invoker=object())  # type: ignore[arg-type]
    binding = EventConditionBindingResolution(
        id=uuid4(),
        event_config_id=uuid4(),
        condition_config_id=uuid4(),
        is_enabled=True,
        continue_on_fail=False,
        is_required=True,
        action_bindings=[],
    )
    receipt = LaneCommitReceiptNotification(
        environment_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:test",
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )

    with pytest.raises(ValueError, match="object_instance_graph_id"):
        await writer.persist_for_binding(
            receipt=receipt,
            activation_id=uuid4(),
            event_type="agent.turn.requested",
            source="test",
            actor_subscription_id=None,
            target_actor_id=None,
            binding=binding,
        )
