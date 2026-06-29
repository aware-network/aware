from __future__ import annotations

import asyncio
from collections.abc import Awaitable
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

from aware_code.types import JsonArray, JsonObject
from aware_meta.runtime import factory as runtime_factory
from aware_meta.runtime.generated_handler_discovery import (
    discover_meta_graph_generated_handler_provider_set,
)
from aware_meta.runtime.generated_impl_delegation import (
    meta_graph_impl_delegating_invocation_handler_resolver,
    meta_graph_impl_delegating_language_handler_resolver,
    resolve_meta_handler_impl,
)
from aware_meta.runtime.generated_handler_resolver_chain import (
    meta_graph_strict_invocation_handler_resolver,
    meta_graph_strict_language_handler_resolver,
)
from aware_meta.graph.instance.builder import build_object_instance_graph
from aware_meta.runtime.handler_executor import (
    MetaGraphBoundArguments,
    MetaGraphEmptyLaneBootstrap,
    MetaGraphFunctionImplementationDescriptor,
    MetaGraphGeneratedConstructorBootstrapRegistry,
    MetaGraphGeneratedInvocationHandlerRegistry,
    MetaGraphGeneratedLanguageHandlerImplementation,
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedLanguageHandlerRegistry,
    MetaGraphImplementationKind,
    MetaGraphLanguageHandlerExecution,
)
from aware_meta.runtime.handler_executor.execution_context import (
    MetaGraphHandlerContext,
    MetaGraphHandlerExecutionContext,
    scoped_meta_graph_handler_execution_context,
)
from aware_meta.runtime.handler_executor.index import MetaGraphImplementationPolicy
from aware_meta.runtime.handler_executor.language_handler import (
    _MetaGraphGeneratedInvocationProvider,
    _scoped_invocation_provider,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.stable_ids import (
    stable_class_config_function_config_id,
    stable_class_relationship_id,
    stable_function_config_id,
    stable_object_config_graph_node_id,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_orm.session.session import Session


def test_generated_meta_handlers_include_class_config_update_config() -> None:
    from aware_meta.handlers._generated.meta_handlers import (
        AWARE_META_GRAPH_HANDLERS,
        AWARE_META_GRAPH_INVOCATION_HANDLERS,
    )

    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_meta.default.class.ClassConfig",
        function_name="update_config",
        is_constructor=False,
        owner_class_fqn="aware_meta.default.class.ClassConfig",
        owner_class_name="ClassConfig",
    )

    assert key in AWARE_META_GRAPH_HANDLERS
    assert key in AWARE_META_GRAPH_INVOCATION_HANDLERS


def test_meta_handwritten_compatibility_overlay_is_not_importable() -> None:
    assert (
        importlib.util.find_spec("aware_meta.runtime.handwritten_invocation_handlers")
        is None
    )


def test_meta_impl_delegation_resolves_relationship_constructor_without_bridge() -> (
    None
):
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_meta.default.class.ClassConfigRelationship",
        function_name="create_via_class_config",
        is_constructor=True,
        owner_class_fqn="aware_meta.default.class.ClassConfigRelationship",
        owner_class_name="ClassConfigRelationship",
    )

    descriptor = _implementation_descriptor_for_key(key)
    impl = resolve_meta_handler_impl(descriptor)
    assert impl is not None
    assert impl.__module__ == (
        "aware_meta.handlers.impl.class_.class_config_relationship"
    )
    assert impl.__name__ == "create_via_class_config"

    source_class_config_id = uuid4()
    target_class_config_id = uuid4()
    relationship_key = "placements"
    expected_relationship_id = stable_class_relationship_id(
        source_class_id=source_class_config_id,
        target_class_id=target_class_config_id,
        relationship_key=relationship_key,
    )
    low_level_resolver = meta_graph_impl_delegating_invocation_handler_resolver(
        None,
    )
    low_level_resolver.resolve_generated_invocation_handler(descriptor)

    resolver = meta_graph_strict_invocation_handler_resolver(None)
    handler = resolver.resolve_generated_invocation_handler(descriptor)
    session = Session(branch_id=uuid4(), skip_db=True)
    execution_context = MetaGraphHandlerExecutionContext(
        session=session,
        ctx=MetaGraphHandlerContext(requester_id=uuid4()),
        function_call=FunctionCall.model_construct(id=uuid4()),
        index=cast(Any, SimpleNamespace()),
    )

    async def _invoke() -> object:
        with scoped_meta_graph_handler_execution_context(execution_context):
            return await cast(
                Awaitable[object],
                handler(
                    cast(Any, SimpleNamespace()),
                    cast(Any, SimpleNamespace()),
                    ClassConfigRelationship,
                    JsonArray(),
                    JsonObject(
                        {
                            "class_config_id": str(source_class_config_id),
                            "target_class_config_id": str(target_class_config_id),
                            "relationship_key": relationship_key,
                            "relationship_type": (
                                ClassConfigRelationshipType.one_to_many.value
                            ),
                        }
                    ),
                ),
            )

    result = asyncio.run(_invoke())
    assert isinstance(result, ClassConfigRelationship)
    assert result.id == expected_relationship_id
    assert result.class_config_id == source_class_config_id
    assert result.target_class_config_id == target_class_config_id
    assert result.relationship_key == relationship_key
    assert result.relationship_type == ClassConfigRelationshipType.one_to_many
    assert result.target_class_config is None


def test_meta_impl_delegation_resolves_package_owned_handler_impl() -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_agent.default.inference.InferenceServiceConfig",
        function_name="build",
        is_constructor=True,
        owner_class_fqn="aware_agent.default.inference.InferenceServiceConfig",
        owner_class_name="InferenceServiceConfig",
    )

    descriptor = _implementation_descriptor_for_key(key)
    impl = resolve_meta_handler_impl(descriptor)

    assert impl is not None
    assert impl.__module__ == (
        "aware_agent.handlers.impl.inference.inference_service_config"
    )
    assert impl.__name__ == "build"


def test_meta_impl_delegation_resolves_package_owned_nested_handler_impl() -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_agent.agent.process.AgentProcessThread",
        function_name="ensure_system_instruction",
        is_constructor=False,
        owner_class_fqn="aware_agent.agent.process.AgentProcessThread",
        owner_class_name="AgentProcessThread",
    )

    descriptor = _implementation_descriptor_for_key(key)
    impl = resolve_meta_handler_impl(descriptor)

    assert impl is not None
    assert impl.__module__ == ("aware_agent.handlers.impl.process.agent_process_thread")
    assert impl.__name__ == "ensure_system_instruction"


def test_meta_impl_delegation_prefers_package_namespace_deduped_impl() -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_agent.agent.process.AgentProcess",
        function_name="create_thread",
        is_constructor=False,
        owner_class_fqn="aware_agent.agent.process.AgentProcess",
        owner_class_name="AgentProcess",
    )

    descriptor = _implementation_descriptor_for_key(key)
    impl = resolve_meta_handler_impl(descriptor)

    assert impl is not None
    assert impl.__module__ == ("aware_agent.handlers.impl.process.agent_process")
    assert impl.__name__ == "create_thread"


def test_meta_impl_delegation_resolves_relationship_top_level_language_handler() -> (
    None
):
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_meta.default.class.ClassConfig",
        function_name="create_relationship",
        is_constructor=False,
        owner_class_fqn="aware_meta.default.class.ClassConfig",
        owner_class_name="ClassConfig",
    )

    class_config_schema = ClassConfig.get_class_config()
    assert class_config_schema is not None
    class_config_schema_id = class_config_schema.id
    assert class_config_schema_id is not None
    owner_class_config = ClassConfig(
        id=class_config_schema_id,
        class_fqn="aware_meta.default.class.ClassConfig",
        name="ClassConfig",
    )
    function_config = FunctionConfig(
        id=key.function_id or uuid4(),
        owner_key=key.owner_key,
        name=key.function_name,
        kind=FunctionKind.instance,
    )
    owner_class_config.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=owner_class_config.id,
            function_config_id=function_config.id,
            function_config=function_config,
            is_constructor=False,
            is_public=True,
        )
    ]
    descriptor = MetaGraphFunctionImplementationDescriptor(
        kind=MetaGraphImplementationKind.language_handler,
        function_config=function_config,
        owner_class_config=owner_class_config,
        is_constructor=False,
    )
    impl = resolve_meta_handler_impl(descriptor)
    assert impl is not None
    assert impl.__module__ == "aware_meta.handlers.impl.class_.class_config"
    assert impl.__name__ == "create_relationship"

    source_class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware_test.Source",
        name="Source",
    )
    target_class_config_id = uuid4()
    relationship_key = "children"
    expected_relationship_id = stable_class_relationship_id(
        source_class_id=source_class_config.id,
        target_class_id=target_class_config_id,
        relationship_key=relationship_key,
    )
    relationship_schema = ClassConfigRelationship.get_class_config()
    assert relationship_schema is not None
    relationship_schema_id = relationship_schema.id
    assert relationship_schema_id is not None
    relationship_constructor = FunctionConfig(
        id=uuid4(),
        owner_key="aware_meta.default.class.ClassConfigRelationship",
        name="create_via_class_config",
        kind=FunctionKind.class_,
    )
    relationship_owner_class_config = ClassConfig(
        id=relationship_schema_id,
        class_fqn="aware_meta.default.class.ClassConfigRelationship",
        name="ClassConfigRelationship",
        class_config_function_configs=[
            ClassConfigFunctionConfig(
                class_config_id=relationship_schema_id,
                function_config_id=relationship_constructor.id,
                function_config=relationship_constructor,
                is_constructor=True,
                is_public=True,
            )
        ],
    )
    ocg_id = uuid4()
    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                object_config_graph_id=ocg_id,
                type=ObjectConfigGraphNodeType.class_,
                node_key=owner_class_config.class_fqn,
                class_config=owner_class_config,
            )
        ],
        object_projection_graphs=[],
    )
    opg_id = uuid4()
    opg = ObjectProjectionGraph(
        id=opg_id,
        object_config_graph_id=ocg.id,
        language=CodeLanguage.aware,
        name="ClassConfig",
        projection_hash="sha256:test:class-config",
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=owner_class_config.id,
                is_root=True,
                selection=ObjectProjectionGraphNodeSelection.one,
            )
        ],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    ocg.object_projection_graphs = [opg]
    before_oig = build_object_instance_graph(
        root_instance=source_class_config,
        object_config_graph=ocg,
        object_projection_graph=opg,
        key="before",
        name="before",
        description="before",
    )
    pre_state = cast(
        Any,
        SimpleNamespace(
            before_oig=before_oig,
            root_object_id=source_class_config.id,
            target_object_id=source_class_config.id,
            root_class_instance_identity_id=None,
            oig_index=None,
        ),
    )
    runtime_index = SimpleNamespace(
        ocg=ocg,
        class_configs_by_id={
            owner_class_config.id: owner_class_config,
            relationship_owner_class_config.id: relationship_owner_class_config,
        },
        attribute_configs_by_id={},
        relationships_by_id={},
        portal_index=None,
    )
    lane_scope = SimpleNamespace(
        domain_branch_id=uuid4(),
        object_instance_graph_branch_id=None,
        object_instance_graph_id=None,
        object_instance_graph_identity_id=None,
        domain_projection_hash=opg.projection_hash,
    )
    staged_call = SimpleNamespace(
        lane_scope=lane_scope,
        function_call=FunctionCall.model_construct(id=uuid4()),
    )
    request = cast(
        Any,
        SimpleNamespace(
            staged_call=staged_call,
            execution_plan=SimpleNamespace(
                implementation=descriptor,
                index=runtime_index,
                object_projection_graph=opg,
                target_object_id=source_class_config.id,
                staged_call=staged_call,
            ),
            request=SimpleNamespace(
                target_object_id=source_class_config.id,
                call_target=SimpleNamespace(value="opg_instance"),
                actor_id=uuid4(),
            ),
            invoke_function=None,
        ),
    )
    resolver = meta_graph_strict_language_handler_resolver(None)
    handler = resolver.resolve_generated_language_handler(descriptor)
    invocation_resolver = meta_graph_strict_invocation_handler_resolver(None)
    implementation = MetaGraphGeneratedLanguageHandlerImplementation(
        handler=handler,
        invocation_handler_resolver=invocation_resolver,
    )

    async def _invoke() -> MetaGraphLanguageHandlerExecution:
        return await implementation.execute_language_handler(
            request,
            pre_state,
            MetaGraphBoundArguments(
                execution_plan=request.execution_plan,
                positional=JsonArray(),
                keyword=JsonObject(
                    {
                        "target_class_config_id": str(target_class_config_id),
                        "relationship_key": relationship_key,
                        "relationship_type": (
                            ClassConfigRelationshipType.one_to_many.value
                        ),
                    }
                ),
            ),
        )

    execution = asyncio.run(_invoke())
    assert execution.success is True
    assert execution.root_object_id == source_class_config.id
    assert execution.post_oig is not None
    assert source_class_config.class_config_relationships == []
    payload = cast(dict[str, object], execution.payload)
    value = cast(dict[str, object], payload["value"])
    assert value["id"] == str(expected_relationship_id)
    assert value["relationship_key"] == relationship_key
    assert value["target_class_config_id"] == str(target_class_config_id)


def test_meta_impl_delegation_resolves_constructor_top_level_language_handler() -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_meta.default.class.ClassConfigRelationship",
        function_name="create_via_class_config",
        is_constructor=True,
        owner_class_fqn="aware_meta.default.class.ClassConfigRelationship",
        owner_class_name="ClassConfigRelationship",
    )

    relationship_schema = ClassConfigRelationship.get_class_config()
    assert relationship_schema is not None
    relationship_schema_id = relationship_schema.id
    assert relationship_schema_id is not None
    owner_class_config = ClassConfig(
        id=relationship_schema_id,
        class_fqn="aware_meta.default.class.ClassConfigRelationship",
        name="ClassConfigRelationship",
    )
    function_config = FunctionConfig(
        id=key.function_id or uuid4(),
        owner_key=key.owner_key,
        name=key.function_name,
        kind=FunctionKind.class_,
    )
    owner_class_config.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=owner_class_config.id,
            function_config_id=function_config.id,
            function_config=function_config,
            is_constructor=True,
            is_public=True,
        )
    ]
    descriptor = MetaGraphFunctionImplementationDescriptor(
        kind=MetaGraphImplementationKind.language_handler,
        function_config=function_config,
        owner_class_config=owner_class_config,
        is_constructor=True,
    )
    impl = resolve_meta_handler_impl(descriptor)
    assert impl is not None
    assert impl.__module__ == (
        "aware_meta.handlers.impl.class_.class_config_relationship"
    )
    assert impl.__name__ == "create_via_class_config"

    source_class_config_id = uuid4()
    target_class_config_id = uuid4()
    relationship_key = "children"
    expected_relationship_id = stable_class_relationship_id(
        source_class_id=source_class_config_id,
        target_class_id=target_class_config_id,
        relationship_key=relationship_key,
    )
    ocg_id = uuid4()
    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test",
        description="test",
        hash="sha256:test",
        fqn_prefix="aware_test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                object_config_graph_id=ocg_id,
                type=ObjectConfigGraphNodeType.class_,
                node_key=owner_class_config.class_fqn,
                class_config=owner_class_config,
            )
        ],
        object_projection_graphs=[],
    )
    opg_id = uuid4()
    opg = ObjectProjectionGraph(
        id=opg_id,
        object_config_graph_id=ocg.id,
        language=CodeLanguage.aware,
        name="ClassConfigRelationship",
        projection_hash="sha256:test:relationship",
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=owner_class_config.id,
                is_root=True,
                selection=ObjectProjectionGraphNodeSelection.one,
            )
        ],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    ocg.object_projection_graphs = [opg]
    before_oig = ObjectInstanceGraph.model_construct(
        id=uuid4(),
        object_projection_graph_id=opg.id,
        root_class_instance_id=None,
        root_class_instance=None,
        class_instances=[],
        class_instance_relationships=[],
        key="before",
        name="before",
        description="before",
        hash="sha256:before",
    )
    runtime_index = SimpleNamespace(
        ocg=ocg,
        class_configs_by_id={owner_class_config.id: owner_class_config},
        attribute_configs_by_id={},
        relationships_by_id={},
        portal_index=None,
    )
    lane_scope = SimpleNamespace(
        domain_branch_id=uuid4(),
        object_instance_graph_branch_id=None,
        object_instance_graph_id=None,
        object_instance_graph_identity_id=None,
        domain_projection_hash=opg.projection_hash,
    )
    staged_call = SimpleNamespace(
        lane_scope=lane_scope,
        function_call=FunctionCall.model_construct(id=uuid4()),
    )
    request = cast(
        Any,
        SimpleNamespace(
            staged_call=staged_call,
            execution_plan=SimpleNamespace(
                implementation=descriptor,
                index=runtime_index,
                object_projection_graph=opg,
                target_object_id=None,
                staged_call=staged_call,
            ),
            request=SimpleNamespace(
                target_object_id=None,
                call_target=SimpleNamespace(value="opg_constructor"),
                actor_id=uuid4(),
            ),
            invoke_function=None,
        ),
    )
    pre_state = cast(
        Any,
        SimpleNamespace(
            execution_plan=request.execution_plan,
            before_oig=before_oig,
            graph_hash_pre=before_oig.hash,
            root_object_id=expected_relationship_id,
            root_class_instance_identity_id=None,
            target_object_id=None,
            oig_index=None,
        ),
    )
    resolver = meta_graph_strict_language_handler_resolver(None)
    handler = resolver.resolve_generated_language_handler(descriptor)
    session = Session(branch_id=uuid4(), skip_db=True)
    execution_context = MetaGraphHandlerExecutionContext(
        session=session,
        ctx=MetaGraphHandlerContext(requester_id=uuid4()),
        function_call=FunctionCall.model_construct(id=uuid4()),
        index=cast(Any, runtime_index),
    )

    async def _invoke() -> MetaGraphLanguageHandlerExecution:
        with scoped_meta_graph_handler_execution_context(execution_context):
            return await handler(
                request,
                pre_state,
                JsonArray(),
                JsonObject(
                    {
                        "class_config_id": str(source_class_config_id),
                        "target_class_config_id": str(target_class_config_id),
                        "relationship_key": relationship_key,
                        "relationship_type": (
                            ClassConfigRelationshipType.one_to_many.value
                        ),
                    }
                ),
            )

    execution = asyncio.run(_invoke())
    assert execution.success is True
    assert execution.root_object_id == expected_relationship_id
    assert execution.post_oig is not None
    payload = cast(dict[str, object], execution.payload)
    value = cast(dict[str, object], payload["value"])
    assert value["id"] == str(expected_relationship_id)
    assert value["class_config_id"] == str(source_class_config_id)
    assert value["target_class_config_id"] == str(target_class_config_id)
    assert value["relationship_key"] == relationship_key


def test_meta_impl_delegation_resolves_function_config_create_with_strict_invocation_provider() -> (
    None
):
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_meta.default.class.ClassConfig",
        function_name="create_function_config",
        is_constructor=False,
        owner_class_fqn="aware_meta.default.class.ClassConfig",
        owner_class_name="ClassConfig",
    )

    class_config_schema = ClassConfig.get_class_config()
    assert class_config_schema is not None
    class_config_schema_id = class_config_schema.id
    assert class_config_schema_id is not None
    owner_class_config = ClassConfig(
        id=class_config_schema_id,
        class_fqn="aware_meta.default.class.ClassConfig",
        name="ClassConfig",
    )
    function_config = FunctionConfig(
        id=key.function_id or uuid4(),
        owner_key=key.owner_key,
        name=key.function_name,
        kind=FunctionKind.instance,
    )
    owner_class_config.class_config_function_configs = [
        ClassConfigFunctionConfig(
            class_config_id=owner_class_config.id,
            function_config_id=function_config.id,
            function_config=function_config,
            is_constructor=False,
            is_public=True,
        )
    ]
    descriptor = MetaGraphFunctionImplementationDescriptor(
        kind=MetaGraphImplementationKind.language_handler,
        function_config=function_config,
        owner_class_config=owner_class_config,
        is_constructor=False,
    )
    impl = resolve_meta_handler_impl(descriptor)
    assert impl is not None
    assert impl.__module__ == "aware_meta.handlers.impl.class_.class_config"
    assert impl.__name__ == "create_function_config"

    source_class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware_test.Source",
        name="Source",
    )
    new_function_name = "create_scene"
    expected_function_id = stable_function_config_id(
        owner_key=source_class_config.class_fqn,
        name=new_function_name,
        kind=FunctionKind.instance.value,
    )
    expected_membership_id = stable_class_config_function_config_id(
        class_config_id=source_class_config.id,
        function_config_id=expected_function_id,
    )
    function_membership_schema = ClassConfigFunctionConfig.get_class_config()
    assert function_membership_schema is not None
    function_membership_schema_id = function_membership_schema.id
    assert function_membership_schema_id is not None
    function_membership_constructor = FunctionConfig(
        id=uuid4(),
        owner_key="aware_meta.default.class.ClassConfigFunctionConfig",
        name="create_via_class_config",
        kind=FunctionKind.class_,
    )
    function_membership_owner_class_config = ClassConfig(
        id=function_membership_schema_id,
        class_fqn="aware_meta.default.class.ClassConfigFunctionConfig",
        name="ClassConfigFunctionConfig",
        class_config_function_configs=[
            ClassConfigFunctionConfig(
                class_config_id=function_membership_schema_id,
                function_config_id=function_membership_constructor.id,
                function_config=function_membership_constructor,
                is_constructor=True,
                is_public=True,
            )
        ],
    )
    function_config_schema = FunctionConfig.get_class_config()
    assert function_config_schema is not None
    function_config_schema_id = function_config_schema.id
    assert function_config_schema_id is not None
    function_config_owner_class_config = ClassConfig(
        id=function_config_schema_id,
        class_fqn="aware_meta.default.function.FunctionConfig",
        name="FunctionConfig",
    )
    runtime_index = SimpleNamespace(
        ocg=SimpleNamespace(),
        class_configs_by_id={
            owner_class_config.id: owner_class_config,
            function_membership_owner_class_config.id: (
                function_membership_owner_class_config
            ),
            function_config_owner_class_config.id: function_config_owner_class_config,
        },
        attribute_configs_by_id={},
        relationships_by_id={},
        portal_index=None,
    )
    request = cast(
        Any,
        SimpleNamespace(
            execution_plan=SimpleNamespace(
                implementation=descriptor,
                index=runtime_index,
            ),
        ),
    )
    pre_state = cast(Any, SimpleNamespace())
    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(source_class_config)
    execution_context = MetaGraphHandlerExecutionContext(
        session=session,
        ctx=MetaGraphHandlerContext(requester_id=uuid4()),
        function_call=FunctionCall.model_construct(id=uuid4()),
        index=cast(Any, runtime_index),
    )
    invocation_resolver = meta_graph_strict_invocation_handler_resolver(None)
    invocation_provider = _MetaGraphGeneratedInvocationProvider(
        request=request,
        pre_state=pre_state,
        handler_resolver=invocation_resolver,
    )
    handler = invocation_resolver.resolve_generated_invocation_handler(descriptor)

    async def _invoke() -> object:
        with (
            scoped_meta_graph_handler_execution_context(execution_context),
            _scoped_invocation_provider(invocation_provider),
        ):
            return await cast(
                Awaitable[object],
                handler(
                    request,
                    pre_state,
                    source_class_config,
                    JsonArray(),
                    JsonObject(
                        {
                            "name": new_function_name,
                            "description": "Create a scene.",
                            "verb": "create",
                            "is_async": True,
                            "kind": FunctionKind.instance.value,
                            "is_public": True,
                            "is_constructor": False,
                            "position": 4,
                        }
                    ),
                ),
            )

    result = asyncio.run(_invoke())
    assert isinstance(result, FunctionConfig)
    assert result.id == expected_function_id
    assert result.name == new_function_name
    assert result.owner_key == source_class_config.class_fqn
    assert result.description == "Create a scene."
    assert len(source_class_config.class_config_function_configs) == 1
    edge = source_class_config.class_config_function_configs[0]
    assert edge.id == expected_membership_id
    assert edge.class_config_id == source_class_config.id
    assert edge.function_config_id == expected_function_id
    assert edge.function_config is result
    assert edge.position == 4


def test_meta_impl_delegation_resolves_function_config_delete_with_strict_invocation_provider() -> (
    None
):
    from aware_meta.handlers._generated.meta_handlers import (
        AWARE_META_GRAPH_HANDLERS,
        AWARE_META_GRAPH_INVOCATION_HANDLERS,
    )

    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_meta.default.class.ClassConfig",
        function_name="remove_function_config",
        is_constructor=False,
        owner_class_fqn="aware_meta.default.class.ClassConfig",
        owner_class_name="ClassConfig",
    )
    function_config = FunctionConfig(
        id=key.function_id or uuid4(),
        owner_key=key.owner_key,
        name=key.function_name,
        kind=FunctionKind.instance,
    )
    owner_class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware_meta.default.class.ClassConfig",
        name="ClassConfig",
    )
    descriptor = MetaGraphFunctionImplementationDescriptor(
        kind=MetaGraphImplementationKind.language_handler,
        function_config=function_config,
        owner_class_config=owner_class_config,
        is_constructor=False,
    )

    assert key in AWARE_META_GRAPH_HANDLERS
    assert key in AWARE_META_GRAPH_INVOCATION_HANDLERS
    impl = resolve_meta_handler_impl(descriptor)
    assert impl is not None
    assert impl.__module__ == "aware_meta.handlers.impl.class_.class_config"
    assert impl.__name__ == "remove_function_config"

    source_class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware_test.Source",
        name="Source",
    )
    removed_function_name = "remove_scene"
    retained_function_name = "keep_scene"
    removed_function_id = stable_function_config_id(
        owner_key=source_class_config.class_fqn,
        name=removed_function_name,
        kind=FunctionKind.instance.value,
    )
    retained_function_id = stable_function_config_id(
        owner_key=source_class_config.class_fqn,
        name=retained_function_name,
        kind=FunctionKind.instance.value,
    )
    removed_function = FunctionConfig(
        id=removed_function_id,
        owner_key=source_class_config.class_fqn,
        name=removed_function_name,
        kind=FunctionKind.instance,
    )
    retained_function = FunctionConfig(
        id=retained_function_id,
        owner_key=source_class_config.class_fqn,
        name=retained_function_name,
        kind=FunctionKind.instance,
    )
    removed_edge = ClassConfigFunctionConfig(
        id=stable_class_config_function_config_id(
            class_config_id=source_class_config.id,
            function_config_id=removed_function_id,
        ),
        class_config_id=source_class_config.id,
        function_config_id=removed_function_id,
        function_config=removed_function,
        is_public=True,
        is_constructor=False,
        position=0,
    )
    retained_edge = ClassConfigFunctionConfig(
        id=stable_class_config_function_config_id(
            class_config_id=source_class_config.id,
            function_config_id=retained_function_id,
        ),
        class_config_id=source_class_config.id,
        function_config_id=retained_function_id,
        function_config=retained_function,
        is_public=True,
        is_constructor=False,
        position=1,
    )
    source_class_config.class_config_function_configs = [
        removed_edge,
        retained_edge,
    ]

    resolver = meta_graph_strict_invocation_handler_resolver(None)
    handler = resolver.resolve_generated_invocation_handler(descriptor)

    async def _invoke() -> object:
        return await cast(
            Awaitable[object],
            handler(
                cast(Any, SimpleNamespace()),
                cast(Any, SimpleNamespace()),
                source_class_config,
                JsonArray(),
                JsonObject(
                    {
                        "name": removed_function_name,
                        "function_config_id": str(removed_function_id),
                    }
                ),
            ),
        )

    result = asyncio.run(_invoke())
    assert result is None
    assert source_class_config.class_config_function_configs == [retained_edge]
    assert retained_edge.function_config is retained_function


def test_meta_generated_handlers_include_class_config_attribute_lifecycle_stubs() -> (
    None
):
    from aware_meta.handlers._generated.meta_handlers import (
        AWARE_META_GRAPH_HANDLERS,
        AWARE_META_GRAPH_INVOCATION_HANDLERS,
    )

    for key in (
        MetaGraphGeneratedLanguageHandlerKey(
            owner_key="aware_meta.default.class.ClassConfig",
            function_name="create_primitive_attribute_config",
            is_constructor=False,
            owner_class_fqn="aware_meta.default.class.ClassConfig",
            owner_class_name="ClassConfig",
        ),
        MetaGraphGeneratedLanguageHandlerKey(
            owner_key="aware_meta.default.class.ClassConfigAttributeConfig",
            function_name="create_primitive_via_class_config",
            is_constructor=True,
            owner_class_fqn="aware_meta.default.class.ClassConfigAttributeConfig",
            owner_class_name="ClassConfigAttributeConfig",
        ),
        MetaGraphGeneratedLanguageHandlerKey(
            owner_key="aware_meta.default.class.ClassConfig",
            function_name="remove_attribute_config",
            is_constructor=False,
            owner_class_fqn="aware_meta.default.class.ClassConfig",
            owner_class_name="ClassConfig",
        ),
    ):
        assert key in AWARE_META_GRAPH_HANDLERS
        assert key in AWARE_META_GRAPH_INVOCATION_HANDLERS


def test_generated_handler_discovery_uses_python_meta_handler_provider_descriptor() -> (
    None
):
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_test_meta.default.foo.Foo",
        function_name="build",
        is_constructor=True,
        owner_class_fqn="aware_test_meta_ontology.foo.foo.Foo",
        owner_class_name="Foo",
    )

    def _handler(*args: object, **kwargs: object) -> MetaGraphLanguageHandlerExecution:
        _ = (args, kwargs)
        return MetaGraphLanguageHandlerExecution(success=True)

    def _bootstrap(request: object) -> object:
        _ = request
        return MetaGraphEmptyLaneBootstrap(root_object_id=uuid4())

    def _invocation(*args: object, **kwargs: object) -> object:
        _ = (args, kwargs)
        return {"ok": True}

    installed = _install_generated_handler_module(
        module_name="aware_test_meta.handlers._generated.meta_handlers",
        handlers={key: _handler},
        invocation_handlers={key: _invocation},
        bootstraps={key: _bootstrap},
    )
    try:
        provider_set = discover_meta_graph_generated_handler_provider_set(
            index=_runtime_index_for_owner_key(key.owner_key),
        )
    finally:
        for module_name in installed:
            sys.modules.pop(module_name, None)

    assert provider_set is not None
    assert provider_set.provider_module_names == (
        "aware_test_meta.handlers._generated.meta_handlers",
    )

    descriptor = _implementation_descriptor_for_key(key)
    assert (
        provider_set.handler_resolver.resolve_generated_language_handler(
            descriptor,
        )
        is _handler
    )
    invocation_resolver = cast(
        MetaGraphGeneratedInvocationHandlerRegistry,
        provider_set.invocation_handler_resolver,
    )
    assert invocation_resolver is not None
    assert (
        invocation_resolver.resolve_generated_invocation_handler(descriptor)
        is _invocation
    )
    bootstrap_resolver = cast(
        MetaGraphGeneratedConstructorBootstrapRegistry,
        provider_set.empty_lane_bootstrap_resolver,
    )
    assert bootstrap_resolver is not None
    assert key in bootstrap_resolver.bootstraps_by_key

    semantic_descriptor = _implementation_descriptor_for_key(
        key,
        owner_class_fqn="aware_test_meta.default.foo.Foo",
    )
    assert (
        provider_set.handler_resolver.resolve_generated_language_handler(
            semantic_descriptor,
        )
        is _handler
    )
    bootstrap = bootstrap_resolver.resolve_empty_lane_bootstrap(
        cast(
            Any,
            SimpleNamespace(
                execution_plan=SimpleNamespace(implementation=semantic_descriptor),
            ),
        )
    )
    assert bootstrap is not None


def test_generated_handler_discovery_accepts_explicit_owner_prefixes() -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_workspace_perf_test.default.workspace.Workspace",
        function_name="append_materialization",
        is_constructor=False,
        owner_class_fqn="aware_workspace_perf_test.workspace.workspace.Workspace",
        owner_class_name="Workspace",
    )

    def _handler(*args: object, **kwargs: object) -> MetaGraphLanguageHandlerExecution:
        _ = (args, kwargs)
        return MetaGraphLanguageHandlerExecution(success=True)

    installed = _install_generated_handler_module(
        module_name="aware_workspace_perf_test.handlers._generated.meta_handlers",
        handlers={key: _handler},
        invocation_handlers={},
        bootstraps={},
    )
    try:
        provider_set = discover_meta_graph_generated_handler_provider_set(
            index=_runtime_index_for_owner_key("aware_unrelated.default.foo.Foo"),
            handler_owner_prefixes=("aware_workspace_perf_test",),
        )
    finally:
        for module_name in installed:
            sys.modules.pop(module_name, None)

    assert provider_set is not None
    assert provider_set.provider_module_names == (
        "aware_workspace_perf_test.handlers._generated.meta_handlers",
    )
    assert (
        provider_set.handler_resolver.resolve_generated_language_handler(
            _implementation_descriptor_for_key(key),
        )
        is _handler
    )


def test_generated_handler_discovery_tries_runtime_import_root() -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_api_test.default.api.ApiCall",
        function_name="create_via_api_capability_endpoint",
        is_constructor=True,
        owner_class_fqn="aware_api_test.default.api.ApiCall",
        owner_class_name="ApiCall",
    )

    def _handler(*args: object, **kwargs: object) -> MetaGraphLanguageHandlerExecution:
        _ = (args, kwargs)
        return MetaGraphLanguageHandlerExecution(success=True)

    def _bootstrap(request: object) -> object:
        _ = request
        return MetaGraphEmptyLaneBootstrap(root_object_id=uuid4())

    installed = _install_generated_handler_module(
        module_name="aware_api_test_runtime.handlers._generated.meta_handlers",
        handlers={key: _handler},
        invocation_handlers={},
        bootstraps={key: _bootstrap},
    )
    try:
        provider_set = discover_meta_graph_generated_handler_provider_set(
            index=_runtime_index_for_owner_key(key.owner_key),
        )
    finally:
        for module_name in installed:
            sys.modules.pop(module_name, None)

    assert provider_set is not None
    assert provider_set.provider_module_names == (
        "aware_api_test_runtime.handlers._generated.meta_handlers",
    )
    descriptor = _implementation_descriptor_for_key(key)
    assert (
        provider_set.handler_resolver.resolve_generated_language_handler(
            descriptor,
        )
        is _handler
    )
    bootstrap_resolver = cast(
        MetaGraphGeneratedConstructorBootstrapRegistry,
        provider_set.empty_lane_bootstrap_resolver,
    )
    assert bootstrap_resolver is not None
    assert (
        bootstrap_resolver.resolve_empty_lane_bootstrap(
            cast(
                Any,
                SimpleNamespace(
                    execution_plan=SimpleNamespace(implementation=descriptor),
                ),
            )
        )
        is not None
    )


def test_generated_handler_discovery_prefers_index_runtime_provider_roots() -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_service_api_test.default.api.ApiCall",
        function_name="create_via_api_capability_endpoint",
        is_constructor=True,
        owner_class_fqn="aware_service_api_test.default.api.ApiCall",
        owner_class_name="ApiCall",
    )

    def _handler(*args: object, **kwargs: object) -> MetaGraphLanguageHandlerExecution:
        _ = (args, kwargs)
        return MetaGraphLanguageHandlerExecution(success=True)

    runtime_index = _runtime_index_for_owner_key(key.owner_key)
    cast(Any, runtime_index).runtime_handler_provider_import_roots = (
        "aware_service_api_test_provider",
    )

    installed = _install_generated_handler_module(
        module_name="aware_service_api_test_provider.handlers._generated.meta_handlers",
        handlers={key: _handler},
        invocation_handlers={},
        bootstraps={},
    )
    try:
        provider_set = discover_meta_graph_generated_handler_provider_set(
            index=runtime_index,
        )
    finally:
        for module_name in installed:
            sys.modules.pop(module_name, None)

    assert provider_set is not None
    assert provider_set.provider_module_names == (
        "aware_service_api_test_provider.handlers._generated.meta_handlers",
    )


def test_generated_handler_discovery_dedupes_runtime_provider_module_names() -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_api.default.api.Api",
        function_name="build",
        is_constructor=True,
        owner_class_fqn="aware_api.default.api.Api",
        owner_class_name="Api",
    )

    def _handler(*args: object, **kwargs: object) -> MetaGraphLanguageHandlerExecution:
        _ = (args, kwargs)
        return MetaGraphLanguageHandlerExecution(success=True)

    runtime_index = _runtime_index_for_owner_key(key.owner_key)
    cast(Any, runtime_index).runtime_handler_provider_import_roots = (
        "aware_api_runtime",
    )

    installed = _install_generated_handler_module(
        module_name="aware_api_runtime.handlers._generated.meta_handlers",
        handlers={key: _handler},
        invocation_handlers={},
        bootstraps={},
    )
    try:
        provider_set = discover_meta_graph_generated_handler_provider_set(
            index=runtime_index,
        )
    finally:
        for module_name in installed:
            sys.modules.pop(module_name, None)

    assert provider_set is not None
    assert provider_set.provider_module_names == (
        "aware_api_runtime.handlers._generated.meta_handlers",
    )


def test_generated_handler_discovery_prefers_explicit_runtime_provider_over_owner_fallback() -> (
    None
):
    duplicate_key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_service.default.service.Service",
        function_name="create_operation",
        is_constructor=False,
        owner_class_fqn="aware_service.default.service.Service",
        owner_class_name="Service",
    )
    runtime_only_key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_service.default.service.ServicePackage",
        function_name="attach_ontology_package",
        is_constructor=False,
        owner_class_fqn="aware_service.default.service.ServicePackage",
        owner_class_name="ServicePackage",
    )

    def _base_handler(
        *args: object, **kwargs: object
    ) -> MetaGraphLanguageHandlerExecution:
        _ = (args, kwargs)
        return MetaGraphLanguageHandlerExecution(success=True)

    def _runtime_handler(
        *args: object, **kwargs: object
    ) -> MetaGraphLanguageHandlerExecution:
        _ = (args, kwargs)
        return MetaGraphLanguageHandlerExecution(success=True)

    runtime_index = _runtime_index_for_owner_key(duplicate_key.owner_key)
    cast(Any, runtime_index).runtime_handler_provider_import_roots = (
        "aware_service_runtime",
    )

    installed = (
        *_install_generated_handler_module(
            module_name="aware_service.handlers._generated.meta_handlers",
            handlers={duplicate_key: _base_handler},
            invocation_handlers={},
            bootstraps={},
        ),
        *_install_generated_handler_module(
            module_name="aware_service_runtime.handlers._generated.meta_handlers",
            handlers={
                duplicate_key: _runtime_handler,
                runtime_only_key: _runtime_handler,
            },
            invocation_handlers={},
            bootstraps={},
        ),
    )
    try:
        provider_set = discover_meta_graph_generated_handler_provider_set(
            index=runtime_index,
        )
    finally:
        for module_name in installed:
            sys.modules.pop(module_name, None)

    assert provider_set is not None
    assert provider_set.provider_module_names == (
        "aware_service_runtime.handlers._generated.meta_handlers",
    )
    assert (
        provider_set.handler_resolver.resolve_generated_language_handler(
            _implementation_descriptor_for_key(duplicate_key)
        )
        is _runtime_handler
    )
    assert (
        provider_set.handler_resolver.resolve_generated_language_handler(
            _implementation_descriptor_for_key(runtime_only_key)
        )
        is _runtime_handler
    )


def test_runtime_factory_discovers_generated_provider_set_from_index(
    monkeypatch,
    tmp_path: Path,
) -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_test_meta.default.foo.Foo",
        function_name="build",
        is_constructor=True,
        owner_class_fqn="aware_test_meta_ontology.foo.foo.Foo",
        owner_class_name="Foo",
    )

    def _handler(*args: object, **kwargs: object) -> MetaGraphLanguageHandlerExecution:
        _ = (args, kwargs)
        return MetaGraphLanguageHandlerExecution(success=True)

    def _bootstrap(request: object) -> object:
        _ = request
        return MetaGraphEmptyLaneBootstrap(root_object_id=uuid4())

    def _invocation(*args: object, **kwargs: object) -> object:
        _ = (args, kwargs)
        return {"ok": True}

    captured: dict[str, object] = {}

    def _fake_context(**kwargs: object) -> object:
        _ = kwargs
        return SimpleNamespace(
            index=_runtime_index_for_owner_key(key.owner_key),
            implementation_policy=MetaGraphImplementationPolicy(),
        )

    def _capture_handler_executor(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(
        "aware_meta.runtime.graph_context."
        "build_meta_graph_runtime_context_for_aware_package_manifests",
        _fake_context,
    )
    monkeypatch.setattr(
        runtime_factory,
        "build_meta_graph_generated_handler_executor",
        _capture_handler_executor,
    )

    installed = _install_generated_handler_module(
        module_name="aware_test_meta.handlers._generated.meta_handlers",
        handlers={key: _handler},
        invocation_handlers={key: _invocation},
        bootstraps={key: _bootstrap},
    )
    try:
        runtime_factory.build_meta_graph_runtime_for_aware_package_manifests(
            package_manifest_paths=(tmp_path / "aware.toml",),
        )
    finally:
        for module_name in installed:
            sys.modules.pop(module_name, None)

    descriptor = _implementation_descriptor_for_key(key)
    handler_resolver = cast(
        Any,
        captured["handler_resolver"],
    )
    assert handler_resolver.resolve_generated_language_handler(descriptor) is _handler
    invocation_resolver = cast(
        Any,
        captured["invocation_handler_resolver"],
    )
    assert (
        invocation_resolver.resolve_generated_invocation_handler(descriptor)
        is _invocation
    )
    bootstrap_resolver = cast(
        Any,
        captured["empty_lane_bootstrap_resolver"],
    )
    bootstrap = bootstrap_resolver.resolve_empty_lane_bootstrap(
        cast(
            Any,
            SimpleNamespace(
                execution_plan=SimpleNamespace(implementation=descriptor),
            ),
        )
    )
    assert bootstrap is not None


def test_runtime_factory_prefers_authored_impl_delegation_over_delegate_resolver(
    monkeypatch,
    tmp_path: Path,
) -> None:
    key = MetaGraphGeneratedLanguageHandlerKey(
        owner_key="aware_meta.default.function.FunctionImplInstructionSet",
        function_name="update_assignment",
        is_constructor=False,
        owner_class_fqn="aware_meta.default.function.FunctionImplInstructionSet",
        owner_class_name="FunctionImplInstructionSet",
    )

    def _delegate_language(*args: object, **kwargs: object) -> object:
        _ = args, kwargs
        return {"wrong": "language"}

    def _delegate_invocation(*args: object, **kwargs: object) -> object:
        _ = args, kwargs
        return {"wrong": "invocation"}

    delegate_language_resolver = MetaGraphGeneratedLanguageHandlerRegistry(
        handlers_by_key={key: _delegate_language},
    )
    delegate_resolver = MetaGraphGeneratedInvocationHandlerRegistry(
        handlers_by_key={key: _delegate_invocation},
    )
    captured: dict[str, object] = {}

    def _fake_context(**kwargs: object) -> object:
        _ = kwargs
        return SimpleNamespace(
            index=_runtime_index_for_owner_key(key.owner_key),
            implementation_policy=MetaGraphImplementationPolicy(),
        )

    def _capture_handler_executor(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(
        "aware_meta.runtime.graph_context."
        "build_meta_graph_runtime_context_for_aware_package_manifests",
        _fake_context,
    )
    monkeypatch.setattr(
        runtime_factory,
        "build_meta_graph_generated_handler_executor",
        _capture_handler_executor,
    )

    runtime_factory.build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=(tmp_path / "aware.toml",),
        handler_resolver=delegate_language_resolver,
        invocation_handler_resolver=delegate_resolver,
    )

    descriptor = _implementation_descriptor_for_key(key)
    impl = resolve_meta_handler_impl(descriptor)
    assert impl is not None
    language_resolver = cast(
        Any,
        captured["handler_resolver"],
    )
    language_handler = language_resolver.resolve_generated_language_handler(descriptor)
    assert language_handler is not _delegate_language
    assert "handwritten_invocation_handlers" not in language_handler.__module__
    invocation_resolver = cast(
        Any,
        captured["invocation_handler_resolver"],
    )
    handler = invocation_resolver.resolve_generated_invocation_handler(descriptor)
    assert handler is not _delegate_invocation
    assert "handwritten_invocation_handlers" not in handler.__module__


@pytest.mark.asyncio
async def test_ocg_delete_node_handler_removes_matching_graph_node_only() -> None:
    from aware_meta.handlers.impl.config.object_config_graph import (  # noqa: WPS433
        delete_node,
    )

    graph_id = uuid4()
    enum_fqn = "aware_demo.home.RoomState"
    enum_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=graph_id,
        type=ObjectConfigGraphNodeType.enum.value,
        node_key=enum_fqn,
    )
    class_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=graph_id,
        type=ObjectConfigGraphNodeType.class_.value,
        node_key="aware_demo.home.Room",
    )
    enum_node = ObjectConfigGraphNode(
        id=enum_node_id,
        object_config_graph_id=graph_id,
        type=ObjectConfigGraphNodeType.enum,
        node_key=enum_fqn,
    )
    class_node = ObjectConfigGraphNode(
        id=class_node_id,
        object_config_graph_id=graph_id,
        type=ObjectConfigGraphNodeType.class_,
        node_key="aware_demo.home.Room",
    )
    graph = ObjectConfigGraph(
        id=graph_id,
        name="aware_demo",
        hash="sha256:demo",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[enum_node, class_node],
    )

    result = await delete_node(
        object_config_graph=graph,
        type=ObjectConfigGraphNodeType.enum,
        node_key=enum_fqn,
        object_config_graph_node_id=enum_node_id,
    )

    assert result is None
    assert [node.id for node in graph.object_config_graph_nodes] == [class_node_id]


def test_runtime_factory_roots_functioncall_oig_stores_under_workspace_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    def _fake_context(**kwargs: object) -> object:
        _ = kwargs
        return SimpleNamespace(
            index=_runtime_index_for_owner_key("aware_test_meta.default.foo.Foo"),
            implementation_policy=MetaGraphImplementationPolicy(),
        )

    monkeypatch.setattr(
        "aware_meta.runtime.graph_context."
        "build_meta_graph_runtime_context_for_aware_package_manifests",
        _fake_context,
    )

    runtime = runtime_factory.build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=(tmp_path / "aware.toml",),
        workspace_root=workspace_root,
    )

    engine = cast(Any, runtime)._invocation_engine
    backend = engine._backend
    executor = backend._handler_executor
    pre_state_provider = executor.pre_state_materializer.provider
    assert pre_state_provider.materializer.commits.aware_root == (
        workspace_root.resolve()
    )
    assert pre_state_provider.materializer.snaps.aware_root == (
        workspace_root.resolve()
    )
    assert backend._lane_committer._store.aware_root == workspace_root.resolve()


def _runtime_index_for_owner_key(owner_key: str) -> object:
    function_config = FunctionConfig(
        id=uuid4(),
        owner_key=owner_key,
        name="build",
        kind=FunctionKind.class_,
    )
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware_test_meta_ontology.foo.foo.Foo",
        name="Foo",
        class_config_function_configs=[
            ClassConfigFunctionConfig(
                id=uuid4(),
                class_config_id=uuid4(),
                function_config_id=function_config.id,
                function_config=function_config,
                is_constructor=True,
            )
        ],
    )
    return SimpleNamespace(
        ocg=SimpleNamespace(),
        class_configs_by_id={class_config.id: class_config},
        attribute_configs_by_id={},
        relationships_by_id={},
        opg_by_id={},
        opg_by_hash={},
        portal_index=SimpleNamespace(),
    )


def _implementation_descriptor_for_key(
    key: MetaGraphGeneratedLanguageHandlerKey,
    *,
    owner_class_fqn: str | None = None,
) -> MetaGraphFunctionImplementationDescriptor:
    function_config = FunctionConfig(
        id=key.function_id or uuid4(),
        owner_key=key.owner_key,
        name=key.function_name,
        kind=FunctionKind.class_,
    )
    owner_class_config = ClassConfig(
        id=uuid4(),
        class_fqn=(
            owner_class_fqn
            or key.owner_class_fqn
            or "aware_test_meta_ontology.foo.foo.Foo"
        ),
        name=key.owner_class_name or "Foo",
    )
    return MetaGraphFunctionImplementationDescriptor(
        kind=MetaGraphImplementationKind.language_handler,
        function_config=function_config,
        owner_class_config=owner_class_config,
        is_constructor=key.is_constructor,
    )


def _install_generated_handler_module(
    *,
    module_name: str,
    handlers: dict[MetaGraphGeneratedLanguageHandlerKey, object],
    bootstraps: dict[MetaGraphGeneratedLanguageHandlerKey, object],
    invocation_handlers: (
        dict[MetaGraphGeneratedLanguageHandlerKey, object] | None
    ) = None,
) -> tuple[str, ...]:
    parts = module_name.split(".")
    installed: list[str] = []
    for index in range(1, len(parts) + 1):
        name = ".".join(parts[:index])
        module = sys.modules.get(name)
        if module is None:
            module = ModuleType(name)
            if index < len(parts):
                module.__path__ = []  # type: ignore[attr-defined]
            sys.modules[name] = module
            installed.append(name)
    provider_module = sys.modules[module_name]
    cast(Any, provider_module).AWARE_META_GRAPH_HANDLERS = handlers
    cast(Any, provider_module).AWARE_META_GRAPH_INVOCATION_HANDLERS = (
        invocation_handlers or {}
    )
    cast(Any, provider_module).AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS = bootstraps
    return tuple(reversed(installed))
