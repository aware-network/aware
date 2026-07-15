from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from aware_api_ontology.stable_ids import (
    stable_api_call_id,
    stable_api_call_stream_event_id,
)
from aware_api_runtime.handlers._generated import (
    meta_handlers as api_meta_handlers,
)
from aware_code.types import JsonArray, JsonObject
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

REACTIVITY_API_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/api/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/reactivity/ontology/structure/aware.toml",
)

API_CLASS_FQN = "aware_api.api.Api"
API_CAPABILITY_CLASS_FQN = "aware_api.api.ApiCapability"
API_CAPABILITY_ENDPOINT_CLASS_FQN = "aware_api.api.ApiCapabilityEndpoint"
API_CAPABILITY_ENDPOINT_STREAM_CONFIG_CLASS_FQN = (
    "aware_api.api.ApiCapabilityEndpointStreamConfig"
)
API_CALL_CLASS_FQN = "aware_api.api.ApiCall"
ACTION_CONFIG_CLASS_FQN = "aware_reactivity.action.ActionConfig"
ACTION_INTENT_CLASS_FQN = "aware_reactivity.action.ActionIntent"
ACTION_EXECUTION_CLASS_FQN = "aware_reactivity.action.ActionExecution"

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


def _build_runtime(*, aware_root: Path) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=REACTIVITY_API_PACKAGE_MANIFEST_PATHS,
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


def _projection_hash(runtime_index: MetaGraphRuntimeIndex, projection_name: str) -> str:
    matches = [
        opg.projection_hash
        for opg in runtime_index.opg_by_hash.values()
        if opg.name == projection_name
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one projection named {projection_name!r}, found {len(matches)}"
        )
    return matches[0]


def _select_inline_class_configs(
    runtime_index: MetaGraphRuntimeIndex,
) -> tuple[ClassConfig, ClassConfig]:
    inline_configs = [
        class_config
        for class_config in sorted(
            runtime_index.class_configs_by_id.values(),
            key=lambda item: ((item.class_fqn or ""), str(item.id)),
        )
        if class_config.value_mode == ClassValueMode.inline_value
    ]
    if len(inline_configs) < 2:
        raise AssertionError("Expected at least two inline ClassConfigs")
    return inline_configs[0], inline_configs[1]


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
    raise AssertionError(
        f"Expected one function {class_fqn}.{function_name}, found {len(matches)}"
    )


def _jsonify_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify_value(item) for key, item in value.items()}
    return value


async def _invoke_constructor(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    branch_id: UUID,
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
                {key: _jsonify_value(value) for key, value in kwargs.items()}
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
                {key: _jsonify_value(value) for key, value in kwargs.items()}
            ),
            commit=True,
            publish=False,
        )
    )
    assert result.status == "succeeded", result.error
    assert isinstance(result.payload, dict)
    return result


def _uuid_from_payload(payload: object, key: str) -> UUID:
    assert isinstance(payload, dict)
    if "value" in payload:
        value = payload["value"]
        assert isinstance(value, dict)
        payload = value
    return UUID(str(payload[key]))


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
    return MetaOIGAssertions(oig=oig, index=runtime_index)


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


@pytest.mark.asyncio
async def test_reactivity_links_action_lifecycle_to_committed_api_receipts(
    tmp_path: Path,
) -> None:
    import aware_api_ontology  # noqa: F401
    import aware_reactivity_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_runtime(aware_root=aware_root)
        context = runtime.context
        assert context is not None
        runtime_index = context.index
        request_class_config, stream_class_config = _select_inline_class_configs(
            runtime_index
        )
        assert request_class_config.id is not None
        assert stream_class_config.id is not None

        api_projection_hash = _projection_hash(runtime_index, "Api")
        action_config_projection_hash = _projection_hash(runtime_index, "ActionConfig")
        action_intent_projection_hash = _projection_hash(runtime_index, "ActionIntent")
        api_call_projection_hash = _projection_hash(runtime_index, "ApiCall")

        lane = LaneIds(branch_id=uuid4())
        branch_id = lane.branch_id
        assert branch_id is not None

        create_api = await _invoke_constructor(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            class_fqn=API_CLASS_FQN,
            function_name="create",
            kwargs={"name": "r2a-proof-api"},
        )
        api_id = _uuid_from_payload(create_api.payload, "id")
        create_capability = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
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
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            object_id=capability_id,
            class_fqn=API_CAPABILITY_CLASS_FQN,
            function_name="create_endpoint",
            kwargs={
                "name": "open",
                "request_class_config_id": request_class_config.id,
            },
        )
        endpoint_id = _uuid_from_payload(create_endpoint.payload, "id")
        create_stream_config = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            object_id=endpoint_id,
            class_fqn=API_CAPABILITY_ENDPOINT_CLASS_FQN,
            function_name="create_stream_config",
            kwargs={"stream_mode": "server"},
        )
        stream_config_id = _uuid_from_payload(create_stream_config.payload, "id")
        create_stream_event_config = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            object_id=stream_config_id,
            class_fqn=API_CAPABILITY_ENDPOINT_STREAM_CONFIG_CLASS_FQN,
            function_name="create_event_config",
            kwargs={
                "kind": "delta",
                "class_config_id": stream_class_config.id,
            },
        )
        stream_event_config_id = _uuid_from_payload(
            create_stream_event_config.payload,
            "id",
        )
        call_key = uuid4()
        create_call = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            object_id=endpoint_id,
            class_fqn=API_CAPABILITY_ENDPOINT_CLASS_FQN,
            function_name="create_call",
            kwargs={"call_key": call_key},
        )
        api_call_id = _uuid_from_payload(create_call.payload, "id")
        assert api_call_id == stable_api_call_id(
            api_capability_endpoint_id=endpoint_id,
            call_key=call_key,
        )
        record_stream_event = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            object_id=api_call_id,
            class_fqn=API_CALL_CLASS_FQN,
            function_name="record_stream_event",
            kwargs={
                "sequence": 1,
                "api_capability_endpoint_stream_event_config_id": (
                    stream_event_config_id
                ),
            },
        )
        stream_event_id = _uuid_from_payload(record_stream_event.payload, "id")
        assert stream_event_id == stable_api_call_stream_event_id(
            api_call_id=api_call_id,
            sequence=1,
        )

        api_assertions = await _assertions_for_lane_head(
            runtime_index=runtime_index,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        for instance_id in (
            endpoint_id,
            stream_event_config_id,
            api_call_id,
            stream_event_id,
        ):
            api_assertions.expect_instance(instance_id)
        api_assertions.expect_edge(
            source_id=endpoint_id,
            target_id=api_call_id,
            relationship_name="api_calls",
        )
        api_assertions.expect_edge(
            source_id=api_call_id,
            target_id=stream_event_id,
            relationship_name="stream_events",
        )
        _expect_uuid_primitive(
            api_assertions,
            instance_id=stream_event_id,
            field_name="api_capability_endpoint_stream_event_config_id",
            expected=stream_event_config_id,
        )

        action_name = "r2a.door.open"
        action_config_id = stable_action_config_id(name=action_name)
        create_action_config = await _invoke_constructor(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=action_config_projection_hash,
            class_fqn=ACTION_CONFIG_CLASS_FQN,
            function_name="create",
            kwargs={
                "name": action_name,
                "description": "Open the door through the world service.",
                "api_capability_endpoint_id": endpoint_id,
                "action_type": "door.open",
            },
        )
        assert (
            _uuid_from_payload(create_action_config.payload, "id") == action_config_id
        )

        action_config_assertions = await _assertions_for_lane_head(
            runtime_index=runtime_index,
            branch_id=branch_id,
            projection_hash=action_config_projection_hash,
        )
        action_config_assertions.expect_root(action_config_id)
        action_config_assertions.expect_instance(action_config_id)
        _expect_uuid_primitive(
            action_config_assertions,
            instance_id=action_config_id,
            field_name="api_capability_endpoint_id",
            expected=endpoint_id,
        )

        event_id = uuid4()
        intent_key = "r2a:door.open"
        expected_intent_id = stable_action_intent_id(
            event_id=event_id,
            config_id=action_config_id,
            intent_key=intent_key,
        )
        expected_execution_id = stable_action_execution_id(
            action_intent_id=expected_intent_id,
            execution_key="primary",
        )
        expected_feedback_id = stable_action_feedback_id(
            action_execution_id=expected_execution_id,
            sequence=1,
        )
        create_intent = await _invoke_constructor(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=action_intent_projection_hash,
            class_fqn=ACTION_INTENT_CLASS_FQN,
            function_name="create_via_event",
            kwargs={
                "event_id": event_id,
                "config_id": action_config_id,
                "intent_key": intent_key,
                "action_type": "door.open",
            },
        )
        assert _uuid_from_payload(create_intent.payload, "id") == expected_intent_id
        start_execution = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=action_intent_projection_hash,
            object_id=expected_intent_id,
            class_fqn=ACTION_INTENT_CLASS_FQN,
            function_name="start_execution",
            kwargs={
                "status": "accepted",
                "api_call_id": api_call_id,
            },
        )
        assert (
            _uuid_from_payload(start_execution.payload, "id") == expected_execution_id
        )
        add_feedback = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            branch_id=branch_id,
            projection_hash=action_intent_projection_hash,
            object_id=expected_execution_id,
            class_fqn=ACTION_EXECUTION_CLASS_FQN,
            function_name="add_feedback",
            kwargs={
                "sequence": 1,
                "stage": "execute",
                "status": "accepted",
                "message": "API stream receipt recorded.",
                "api_call_stream_event_id": stream_event_id,
            },
        )
        assert _uuid_from_payload(add_feedback.payload, "id") == expected_feedback_id

        action_intent_assertions = await _assertions_for_lane_head(
            runtime_index=runtime_index,
            branch_id=branch_id,
            projection_hash=action_intent_projection_hash,
        )
        action_intent_assertions.expect_root(expected_intent_id)
        for instance_id in (
            expected_intent_id,
            expected_execution_id,
            expected_feedback_id,
        ):
            action_intent_assertions.expect_instance(instance_id)
        action_intent_assertions.expect_edge(
            source_id=expected_intent_id,
            target_id=expected_execution_id,
            relationship_name="action_executions",
        )
        action_intent_assertions.expect_edge(
            source_id=expected_execution_id,
            target_id=expected_feedback_id,
            relationship_name="action_feedback",
        )
        _expect_uuid_primitive(
            action_intent_assertions,
            instance_id=expected_execution_id,
            field_name="api_call_id",
            expected=api_call_id,
        )
        _expect_uuid_primitive(
            action_intent_assertions,
            instance_id=expected_feedback_id,
            field_name="api_call_stream_event_id",
            expected=stream_event_id,
        )

        action_config_portals = [
            portal
            for portal in runtime_index.portal_index.portals
            if portal.source_projection_hash == action_config_projection_hash
        ]
        action_intent_portals = [
            portal
            for portal in runtime_index.portal_index.portals
            if portal.source_projection_hash == action_intent_projection_hash
        ]
        assert any(
            portal.reference_field_name == "api_capability_endpoint"
            and portal.target_projection_hash == api_projection_hash
            for portal in action_config_portals
        )
        assert any(
            portal.reference_field_name == "api_call"
            and portal.target_projection_hash == api_projection_hash
            for portal in action_intent_portals
        )
        assert any(
            portal.reference_field_name == "api_call_stream_event"
            and portal.target_projection_hash == api_call_projection_hash
            for portal in action_intent_portals
        )
