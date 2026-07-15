from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

from aware_code.types import JsonArray, JsonObject
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
    summarize_commit_perf_events,
)
from aware_meta.graph.instance.commit.perf_trace import JsonObject as TraceJsonObject
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphBoundArguments,
    MetaGraphFunctionImplementationDescriptor,
    MetaGraphImplementationKind,
    MetaGraphPreState,
)
from aware_meta.runtime.handler_executor.language_handler import (
    MetaGraphGeneratedInvocationHandlerCallable,
    MetaGraphGeneratedLanguageHandlerImplementation,
    MetaGraphLanguageHandlerExecution,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor, invoke_instance


@pytest.mark.asyncio
async def test_generated_handler_body_traces_nested_instance_invocation() -> None:
    target_class, target, handler_request, pre_state = _handler_fixture(
        nested_function_name="mutate_child",
        is_constructor=False,
    )
    resolver = _RecordingInvocationResolver()

    async def _handler(
        request: Any,
        pre_state: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        _ = request, pre_state, positional, keyword
        await invoke_instance(
            orm_model=target,
            function_name="mutate_child",
            payload={"value": "updated"},
        )
        return MetaGraphLanguageHandlerExecution(success=True)

    trace_summary, trace_events = await _execute_with_trace(
        handler_request=handler_request,
        pre_state=pre_state,
        resolver=resolver,
        handler=_handler,
    )

    assert resolver.invocation_kinds == [False]
    assert target_class.get_class_config() is not None
    assert _generated_invocation_span_names() <= set(trace_summary)
    assert _metadata_values(trace_events, "invocation_kind") == {"instance"}
    assert _metadata_values(trace_events, "nested_function_name") == {"mutate_child"}


@pytest.mark.asyncio
async def test_generated_handler_body_traces_nested_constructor_invocation() -> None:
    target_class, _, handler_request, pre_state = _handler_fixture(
        nested_function_name="create_child",
        is_constructor=True,
    )
    resolver = _RecordingInvocationResolver()

    async def _handler(
        request: Any,
        pre_state: MetaGraphPreState,
        positional: JsonArray,
        keyword: JsonObject,
    ) -> MetaGraphLanguageHandlerExecution:
        _ = request, pre_state, positional, keyword
        await invoke_constructor(
            orm_class=target_class,
            function_name="create_child",
            payload={"value": "created"},
        )
        return MetaGraphLanguageHandlerExecution(success=True)

    trace_summary, trace_events = await _execute_with_trace(
        handler_request=handler_request,
        pre_state=pre_state,
        resolver=resolver,
        handler=_handler,
    )

    assert resolver.invocation_kinds == [True]
    assert _generated_invocation_span_names() <= set(trace_summary)
    assert _metadata_values(trace_events, "invocation_kind") == {"constructor"}
    assert _metadata_values(trace_events, "nested_function_name") == {"create_child"}


class _RecordingInvocationResolver:
    def __init__(self) -> None:
        self.invocation_kinds: list[bool] = []

    def resolve_generated_invocation_handler(
        self,
        descriptor: MetaGraphFunctionImplementationDescriptor,
    ) -> MetaGraphGeneratedInvocationHandlerCallable:
        self.invocation_kinds.append(descriptor.is_constructor)

        async def _nested_handler(
            request: Any,
            pre_state: MetaGraphPreState,
            target: ORMModel | type[ORMModel],
            positional: JsonArray,
            keyword: JsonObject,
        ) -> object:
            _ = request, pre_state, target, positional, keyword
            return JsonObject({"value": "ok"})

        return _nested_handler


async def _execute_with_trace(
    *,
    handler_request: Any,
    pre_state: MetaGraphPreState,
    resolver: _RecordingInvocationResolver,
    handler: Any,
) -> tuple[dict[str, dict[str, float | int]], tuple[TraceJsonObject, ...]]:
    implementation = MetaGraphGeneratedLanguageHandlerImplementation(
        handler=handler,
        invocation_handler_resolver=resolver,
    )
    recorder = CommitPerfTraceRecorder(
        default_category="meta.runtime.handler_execution",
    )
    with active_commit_perf_trace(recorder):
        await implementation.execute_language_handler(
            request=handler_request,
            pre_state=pre_state,
            bound_arguments=MetaGraphBoundArguments(
                execution_plan=handler_request.execution_plan,
                positional=JsonArray(),
                keyword=JsonObject(),
            ),
        )
    events = recorder.snapshot_json()
    return summarize_commit_perf_events(events), events


def _handler_fixture(
    *,
    nested_function_name: str,
    is_constructor: bool,
) -> tuple[type[ORMModel], ORMModel, Any, MetaGraphPreState]:
    class _SyntheticGeneratedInvocationModel(ORMModel):
        pass

    nested_function = FunctionConfig.model_construct(
        id=uuid4(),
        owner_key="aware.tests.SyntheticGeneratedInvocation",
        name=nested_function_name,
    )
    class_config_id = uuid4()
    class_config = ClassConfig.model_construct(
        id=class_config_id,
        name="SyntheticGeneratedInvocation",
        class_fqn="aware.tests.SyntheticGeneratedInvocation",
        class_config_attribute_configs=[],
        class_config_function_configs=[
            ClassConfigFunctionConfig.model_construct(
                id=uuid4(),
                class_config_id=class_config_id,
                function_config_id=nested_function.id,
                function_config=nested_function,
                is_constructor=is_constructor,
            )
        ],
        class_config_relationships=[],
    )
    _SyntheticGeneratedInvocationModel.bind_class_config(cast(Any, class_config))
    target = _SyntheticGeneratedInvocationModel(id=uuid4())
    handler_request = _handler_request(class_config=class_config)
    pre_state = _pre_state(handler_request=handler_request)
    return _SyntheticGeneratedInvocationModel, target, handler_request, pre_state


def _handler_request(*, class_config: ClassConfig) -> Any:
    top_function = FunctionConfig.model_construct(
        id=uuid4(),
        owner_key="aware.tests.SyntheticGeneratedInvocation",
        name="top_level",
    )
    lane_scope = SimpleNamespace(
        domain_branch_id=uuid4(),
        domain_projection_hash="sha256:test:domain",
        object_projection_graph_id=uuid4(),
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=uuid4(),
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_branch_id=uuid4(),
    )
    execution_plan = SimpleNamespace(
        implementation=SimpleNamespace(
            kind=MetaGraphImplementationKind.language_handler,
            function_config=top_function,
            owner_class_config=class_config,
            is_constructor=False,
        ),
        index=SimpleNamespace(
            class_configs_by_id={class_config.id: class_config},
            portal_index=SimpleNamespace(),
        ),
    )
    return SimpleNamespace(
        request=SimpleNamespace(
            actor_id=uuid4(),
            call_target=SimpleNamespace(value="opg_constructor"),
            domain_projection_hash=lane_scope.domain_projection_hash,
        ),
        staged_call=SimpleNamespace(
            lane_scope=lane_scope,
            function_call=SimpleNamespace(id=uuid4()),
            resolved_target=SimpleNamespace(
                operation_label="SyntheticGeneratedInvocation.top_level",
            ),
        ),
        execution_plan=execution_plan,
        invoke_function=None,
    )


def _pre_state(*, handler_request: Any) -> MetaGraphPreState:
    before_oig = ObjectInstanceGraph.model_construct(
        id=handler_request.staged_call.lane_scope.object_instance_graph_id,
        hash="sha256:test:pre",
        class_instances=[],
        class_instance_relationships=[],
    )
    return MetaGraphPreState(
        execution_plan=handler_request.execution_plan,
        before_oig=before_oig,
        graph_hash_pre="sha256:test:pre",
    )


def _generated_invocation_span_names() -> set[str]:
    return {
        "handler_execution.generated_invocation.resolve_descriptor",
        "handler_execution.generated_invocation.resolve_handler",
        "handler_execution.generated_invocation.build_keyword_payload",
        "handler_execution.generated_invocation.call_handler",
        "handler_execution.generated_invocation.await_handler",
    }


def _metadata_values(
    trace_events: tuple[TraceJsonObject, ...],
    key: str,
) -> set[object]:
    values: set[object] = set()
    for event in trace_events:
        if event.get("phase") not in _generated_invocation_span_names():
            continue
        metadata = event.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        value = metadata.get(key)
        if value is not None:
            values.add(value)
    return values
