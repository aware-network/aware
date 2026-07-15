from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    META_SYSTEM_ACTOR_ID,
    MetaGraphCallTarget,
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphInvokeFunctionInput,
    MetaGraphRuntime,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MetaOIGAssertions,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.stable_ids import stable_inline_value_instance_id
from aware_reactivity.handlers._generated import (
    meta_handlers as reactivity_meta_handlers,
)
from aware_reactivity.stable_ids import (
    stable_action_config_id,
    stable_action_execution_id,
    stable_action_feedback_id,
    stable_action_intent_id,
)

_TESTS_ROOT = Path(__file__).resolve().parent
KERNEL_WORKSPACE_ROOT = _TESTS_ROOT.parents[5]

ACTION_PAYLOAD_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/ontology/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/api/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/sdk/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/reactivity/ontology/structure/aware.toml",
)


_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
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


API_CLASS_FQN = "aware_api.api.Api"
API_CAPABILITY_CLASS_FQN = "aware_api.api.ApiCapability"
API_CAPABILITY_ENDPOINT_CLASS_FQN = "aware_api.api.ApiCapabilityEndpoint"
API_CAPABILITY_ENDPOINT_STREAM_CONFIG_CLASS_FQN = (
    "aware_api.api.ApiCapabilityEndpointStreamConfig"
)
ACTION_INTENT_CLASS_FQN = "aware_reactivity.action.ActionIntent"
ACTION_EXECUTION_CLASS_FQN = "aware_reactivity.action.ActionExecution"


def _build_action_payload_meta_runtime(
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=ACTION_PAYLOAD_PACKAGE_MANIFEST_PATHS,
        workspace_root=KERNEL_WORKSPACE_ROOT,
        aware_root=aware_root,
        handler_modules=(
            _API_META_HANDLER_MODULE,
            _REACTIVITY_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _API_META_BOOTSTRAP_MODULE,
            _REACTIVITY_META_BOOTSTRAP_MODULE,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


def _select_runtime_inline_class_configs(
    runtime_index,
) -> tuple[ClassConfig, ClassConfig]:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    inline_class_configs = [
        class_config
        for class_config in class_configs
        if class_config.value_mode == ClassValueMode.inline_value
    ]
    if len(inline_class_configs) < 2:
        raise AssertionError(
            "Expected two compiled inline_value ClassConfigs for action payload proof"
        )
    return inline_class_configs[0], inline_class_configs[1]


def _projection_hash(runtime_index: MetaGraphRuntimeIndex, projection_name: str) -> str:
    matches = [
        opg.projection_hash
        for opg in runtime_index.opg_by_hash.values()
        if opg.name == projection_name
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected exactly one projection named {projection_name!r}, found {len(matches)}"
        )
    return matches[0]


async def _assertions_for_lane_head(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> MetaOIGAssertions:
    lane_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert lane_head is not None
    opg = runtime_index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=runtime_index.ocg,
        opg=opg,
        commit_id=UUID(str(lane_head["commit_id"])),
        oig_id=UUID(str(lane_head["object_instance_graph_id"])),
        attribute_configs_by_id=runtime_index.attribute_configs_by_id,
        class_configs_by_id=runtime_index.class_configs_by_id,
    )
    return MetaOIGAssertions(
        oig=oig,
        index=runtime_index,
    )


def _uuid_from_payload(payload: object, key: str) -> UUID:
    assert isinstance(payload, dict)
    if "value" in payload:
        value = payload["value"]
        assert isinstance(value, dict)
        payload = value
    return UUID(str(payload[key]))


def _branch_id(value: UUID | None) -> UUID:
    assert value is not None
    return value


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


def _resolve_function_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_fqn: str,
    function_name: str,
) -> UUID:
    matches: list[UUID] = []
    for class_config in index.class_configs_by_id.values():
        if class_config.class_fqn != class_fqn:
            continue
        for edge in class_config.class_config_function_configs:
            function_config = edge.function_config
            if function_config.name == function_name:
                matches.append(function_config.id)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise AssertionError(
            "FunctionConfig not found in Meta graph index: "
            f"class_fqn={class_fqn!r} function_name={function_name!r}"
        )
    raise AssertionError(
        "FunctionConfig is ambiguous in Meta graph index: "
        f"class_fqn={class_fqn!r} function_name={function_name!r} "
        f"matches={matches}"
    )


def _jsonify_value(value: object) -> JsonValue:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return cast(JsonValue, [_jsonify_value(item) for item in value])
    if isinstance(value, list):
        return cast(JsonValue, [_jsonify_value(item) for item in value])
    if isinstance(value, dict):
        return cast(
            JsonValue,
            {str(key): _jsonify_value(item) for key, item in value.items()},
        )
    return cast(JsonValue, value)


async def _invoke_constructor(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    branch_id: UUID | None,
    projection_hash: str,
    class_fqn: str,
    function_name: str,
    kwargs: dict[str, object],
):
    context = runtime.context
    assert context is not None
    opg = context.index.opg_by_hash[projection_hash]
    result = await runtime.invoke_function(
        MetaGraphInvokeFunctionInput(
            index=context.index,
            actor_id=lane.actor_id or META_SYSTEM_ACTOR_ID,
            function_id=_resolve_function_id(
                index=context.index,
                class_fqn=class_fqn,
                function_name=function_name,
            ),
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            call_target=MetaGraphCallTarget.opg_constructor,
            target_object_id=None,
            object_projection_graph_id=opg.id,
            args=JsonArray([]),
            kwargs=JsonObject(
                cast(
                    dict[str, JsonValue],
                    {str(key): _jsonify_value(value) for key, value in kwargs.items()},
                )
            ),
            commit=True,
            publish=False,
        )
    )
    assert result.status == "succeeded", result.error
    assert isinstance(result.payload, dict)
    return result


async def _invoke_instance(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    branch_id: UUID,
    projection_hash: str,
    object_id: UUID,
    class_fqn: str,
    function_name: str,
    kwargs: dict[str, object],
):
    context = runtime.context
    assert context is not None
    result = await runtime.invoke_function(
        MetaGraphInvokeFunctionInput(
            index=context.index,
            actor_id=lane.actor_id or META_SYSTEM_ACTOR_ID,
            function_id=_resolve_function_id(
                index=context.index,
                class_fqn=class_fqn,
                function_name=function_name,
            ),
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            call_target=MetaGraphCallTarget.instance,
            target_object_id=object_id,
            object_projection_graph_id=None,
            args=JsonArray([]),
            kwargs=JsonObject(
                cast(
                    dict[str, JsonValue],
                    {str(key): _jsonify_value(value) for key, value in kwargs.items()},
                )
            ),
            commit=True,
            publish=False,
        )
    )
    assert result.status == "succeeded", result.error
    assert isinstance(result.payload, dict)
    return result


@pytest.mark.asyncio
async def test_action_payload_models_use_committed_api_reactivity_class_configs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import aware_api_ontology  # noqa: F401
    import aware_reactivity_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_action_payload_meta_runtime(
            aware_root=aware_root,
        )
        assert runtime.context is not None
        lane = LaneIds(
            branch_id=uuid4(),
        )
        runtime_index = runtime.context.index
        request_class_config, feedback_class_config = (
            _select_runtime_inline_class_configs(runtime_index)
        )
        api_projection_hash = _projection_hash(runtime_index, "Api")
        action_intent_hash = _projection_hash(runtime_index, "ActionIntent")

        create_api = await _invoke_constructor(
            runtime=runtime,
            lane=lane,
            branch_id=lane.branch_id,
            projection_hash=api_projection_hash,
            class_fqn=API_CLASS_FQN,
            function_name="create",
            kwargs={"name": "a2-proof-api"},
        )
        api_id = _uuid_from_payload(create_api.payload, "id")

        create_capability = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=_branch_id(create_api.domain_branch_id),
            projection_hash=api_projection_hash,
            object_id=api_id,
            class_fqn=API_CLASS_FQN,
            function_name="create_capability",
            kwargs={"name": "door"},
        )
        capability_id = _uuid_from_payload(create_capability.payload, "id")

        create_endpoint = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=_branch_id(create_capability.domain_branch_id),
            projection_hash=api_projection_hash,
            object_id=capability_id,
            class_fqn=API_CAPABILITY_CLASS_FQN,
            function_name="create_endpoint",
            kwargs={
                "name": "lock",
                "request_class_config_id": str(request_class_config.id),
            },
        )
        endpoint_id = _uuid_from_payload(create_endpoint.payload, "id")

        ensure_request_config = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=_branch_id(create_endpoint.domain_branch_id),
            projection_hash=api_projection_hash,
            object_id=endpoint_id,
            class_fqn=API_CAPABILITY_ENDPOINT_CLASS_FQN,
            function_name="ensure_request_config",
            kwargs={"request_class_config_id": str(request_class_config.id)},
        )
        request_config_id = _uuid_from_payload(ensure_request_config.payload, "id")

        create_stream_config = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=_branch_id(ensure_request_config.domain_branch_id),
            projection_hash=api_projection_hash,
            object_id=endpoint_id,
            class_fqn=API_CAPABILITY_ENDPOINT_CLASS_FQN,
            function_name="create_stream_config",
            kwargs={"stream_mode": "server"},
        )
        stream_config_id = _uuid_from_payload(create_stream_config.payload, "id")

        create_event_config = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=_branch_id(create_stream_config.domain_branch_id),
            projection_hash=api_projection_hash,
            object_id=stream_config_id,
            class_fqn=API_CAPABILITY_ENDPOINT_STREAM_CONFIG_CLASS_FQN,
            function_name="create_event_config",
            kwargs={
                "kind": "delta",
                "class_config_id": str(feedback_class_config.id),
            },
        )
        stream_event_config_id = _uuid_from_payload(create_event_config.payload, "id")

        api_assertions = await _assertions_for_lane_head(
            runtime_index=runtime_index,
            branch_id=_branch_id(create_event_config.domain_branch_id),
            projection_hash=api_projection_hash,
        )
        api_assertions.expect_instance(endpoint_id)
        api_assertions.expect_instance(request_config_id)
        api_assertions.expect_instance(stream_config_id)
        api_assertions.expect_instance(stream_event_config_id)
        api_assertions.expect_edge(
            source_id=endpoint_id,
            target_id=request_config_id,
            relationship_name="request_config",
        )
        api_assertions.expect_edge(
            source_id=request_config_id,
            target_id=stream_config_id,
            relationship_name="stream_config",
        )
        api_assertions.expect_edge(
            source_id=stream_config_id,
            target_id=stream_event_config_id,
            relationship_name="api_capability_endpoint_stream_event_configs",
        )
        _expect_uuid_primitive(
            api_assertions,
            instance_id=request_config_id,
            field_name="class_config_id",
            expected=request_class_config.id,
        )
        _expect_uuid_primitive(
            api_assertions,
            instance_id=stream_event_config_id,
            field_name="class_config_id",
            expected=feedback_class_config.id,
        )

        action_config_id = stable_action_config_id(name="a2.door.lock")

        event_id = uuid4()
        actor_subscription_id = uuid4()
        intent_key = f"{actor_subscription_id}:door.lock"
        expected_action_intent_id = stable_action_intent_id(
            event_id=event_id,
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
        expected_intent_payload_model_id = stable_inline_value_instance_id(
            class_config_id=request_class_config.id,
            owner_key=expected_action_intent_id,
        )
        expected_feedback_payload_model_id = stable_inline_value_instance_id(
            class_config_id=feedback_class_config.id,
            owner_key=expected_action_feedback_id,
        )

        create_intent = await _invoke_constructor(
            runtime=runtime,
            lane=lane,
            branch_id=_branch_id(create_event_config.domain_branch_id),
            projection_hash=action_intent_hash,
            class_fqn=ACTION_INTENT_CLASS_FQN,
            function_name="create_via_event",
            kwargs={
                "event_id": str(event_id),
                "config_id": str(action_config_id),
                "intent_key": intent_key,
                "actor_subscription_id": str(actor_subscription_id),
                "action_type": "door.lock",
                "action_payload": {"deprecated": "compatibility-only"},
                "payload_class_config_id": str(request_class_config.id),
            },
        )
        action_intent_id = _uuid_from_payload(create_intent.payload, "id")
        assert action_intent_id == expected_action_intent_id
        assert (
            _uuid_from_payload(create_intent.payload, "payload_model_id")
            == expected_intent_payload_model_id
        )

        start_execution = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=_branch_id(create_intent.domain_branch_id),
            projection_hash=action_intent_hash,
            object_id=action_intent_id,
            class_fqn=ACTION_INTENT_CLASS_FQN,
            function_name="start_execution",
            kwargs={"status": "accepted"},
        )
        action_execution_id = _uuid_from_payload(start_execution.payload, "id")
        assert action_execution_id == expected_action_execution_id

        add_feedback = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=_branch_id(start_execution.domain_branch_id),
            projection_hash=action_intent_hash,
            object_id=action_execution_id,
            class_fqn=ACTION_EXECUTION_CLASS_FQN,
            function_name="add_feedback",
            kwargs={
                "sequence": 1,
                "stage": "execute",
                "status": "accepted",
                "message": "world service accepted typed request",
                "payload": {"deprecated": "compatibility-only"},
                "payload_class_config_id": str(feedback_class_config.id),
            },
        )
        action_feedback_id = _uuid_from_payload(add_feedback.payload, "id")
        assert action_feedback_id == expected_action_feedback_id
        assert (
            _uuid_from_payload(add_feedback.payload, "payload_model_id")
            == expected_feedback_payload_model_id
        )

        action_intent_assertions = await _assertions_for_lane_head(
            runtime_index=runtime_index,
            branch_id=_branch_id(add_feedback.domain_branch_id),
            projection_hash=action_intent_hash,
        )
        action_intent_assertions.expect_root(action_intent_id)
        action_intent_assertions.expect_instance(action_intent_id)
        action_intent_assertions.expect_instance(action_execution_id)
        action_intent_assertions.expect_instance(action_feedback_id)
        action_intent_assertions.expect_instance(expected_intent_payload_model_id)
        action_intent_assertions.expect_instance(expected_feedback_payload_model_id)
        action_intent_assertions.expect_primitive(
            instance_id=action_intent_id,
            field_name="intent_key",
            expected=intent_key,
        )
        action_intent_assertions.expect_edge(
            source_id=action_intent_id,
            target_id=action_execution_id,
            relationship_name="action_executions",
        )
        action_intent_assertions.expect_edge(
            source_id=action_execution_id,
            target_id=action_feedback_id,
            relationship_name="action_feedback",
        )
        action_intent_assertions.expect_edge(
            source_id=action_intent_id,
            target_id=expected_intent_payload_model_id,
            relationship_name="payload_model",
        )
        action_intent_assertions.expect_edge(
            source_id=action_feedback_id,
            target_id=expected_feedback_payload_model_id,
            relationship_name="payload_model",
        )
        _expect_uuid_primitive(
            action_intent_assertions,
            instance_id=expected_intent_payload_model_id,
            field_name="owner_key",
            expected=action_intent_id,
        )
        _expect_uuid_primitive(
            action_intent_assertions,
            instance_id=expected_intent_payload_model_id,
            field_name="class_config_id",
            expected=request_class_config.id,
        )
        _expect_uuid_primitive(
            action_intent_assertions,
            instance_id=expected_feedback_payload_model_id,
            field_name="owner_key",
            expected=action_feedback_id,
        )
        _expect_uuid_primitive(
            action_intent_assertions,
            instance_id=expected_feedback_payload_model_id,
            field_name="class_config_id",
            expected=feedback_class_config.id,
        )
