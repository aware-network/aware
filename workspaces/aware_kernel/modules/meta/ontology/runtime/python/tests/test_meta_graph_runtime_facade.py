from __future__ import annotations

import inspect
from dataclasses import MISSING, fields
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.types import JsonArray, JsonObject
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.stable_ids import stable_lane_id
from aware_meta.runtime import (
    graph_commit_invocation_backend as graph_commit_backend_module,
    MetaGraphAppendReadyChanges,
    MetaGraphCommitInvocationBackend,
    MetaGraphCommitInvocationNotReadyError,
    MetaGraphHandlerExecutionRequest,
    MetaGraphHandlerExecutionResult,
    MetaGraphRuntimeContext,
    MetaGraphRuntimeIndex,
    build_meta_graph_function_target_index,
    build_meta_graph_runtime_context,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor, invoke_instance
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta.runtime.graph_runtime import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvocationBackend,
    MetaGraphInvocationEngine,
    MetaGraphInvokeFunctionInput,
    MetaGraphRuntime,
)
from aware_meta.runtime.commit.required_reactions import (
    RuntimeCommitReactionContext,
    RuntimeCommitReactionReceipt,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph import (
    ObjectConfigGraph,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_constructor import (
    ObjectProjectionGraphConstructor,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.stable_ids import (
    stable_class_instance_identity_id,
    stable_function_call_id,
    stable_function_call_response_id,
    stable_object_config_graph_identity_id,
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
    stable_object_instance_graph_lane_id,
    stable_object_projection_graph_identity_id,
)


def _required_field_names(cls: Any) -> set[str]:
    required: set[str] = set()
    for item in fields(cls):
        if item.default is MISSING and item.default_factory is MISSING:
            required.add(item.name)
    return required


def _meta_commit_index(
    *,
    function_config: object,
    projection_hash: str,
    opg_id: object,
    class_config: object | None = None,
) -> SimpleNamespace:
    class_configs_by_id = {uuid4(): class_config} if class_config is not None else {}
    opg = SimpleNamespace(
        id=opg_id,
        name="Domain",
        projection_hash=projection_hash,
    )
    return SimpleNamespace(
        ocg=SimpleNamespace(
            name="Aware Tests",
            fqn_prefix="aware.tests",
            object_config_graph_identity=None,
            object_config_graph_nodes=[
                SimpleNamespace(
                    type=ObjectConfigGraphNodeType.function,
                    function_config=function_config,
                )
            ],
        ),
        class_configs_by_id=class_configs_by_id,
        opg_by_hash={projection_hash: opg},
        opg_by_id={opg_id: opg},
    )


class MetaLaneDemoModel(ORMModel):
    label: str | None = None


class _RecordingMetaGraphBackend:
    def __init__(self) -> None:
        self.requests: list[MetaGraphInvokeFunctionInput] = []

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphCommitReceipt:
        self.requests.append(request)
        request_count = len(self.requests)
        return MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            payload={"value": f"call-{request_count}"},
            error=None,
            logs=(),
            execution_time_ms=1,
            root_object_id=request.target_object_id or uuid4(),
            graph_hash_pre=f"sha256:pre:{request_count}",
            graph_hash_post=f"sha256:post:{request_count}",
            changes=JsonArray([]),
            function_call_id=uuid4(),
            function_call_response_id=uuid4(),
            commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
        )


def _meta_lane_context() -> tuple[MetaGraphRuntimeContext, UUID, UUID]:
    graph_id = uuid4()
    opg_id = uuid4()
    class_config = ClassConfig(
        class_fqn=(f"{MetaLaneDemoModel.__module__}.{MetaLaneDemoModel.__name__}"),
        name="MetaLaneDemoModel",
    )
    constructor_function = FunctionConfig(
        owner_key="aware.tests.MetaLaneDemoModel",
        name="create",
        kind=FunctionKind.class_,
    )
    instance_function = FunctionConfig(
        owner_key="aware.tests.MetaLaneDemoModel",
        name="rename",
        kind=FunctionKind.instance,
    )
    constructor_link = ClassConfigFunctionConfig(
        class_config_id=class_config.id,
        function_config=constructor_function,
        function_config_id=constructor_function.id,
        is_constructor=True,
    )
    instance_link = ClassConfigFunctionConfig(
        class_config_id=class_config.id,
        function_config=instance_function,
        function_config_id=instance_function.id,
        is_constructor=False,
    )
    class_config.class_config_function_configs = [
        constructor_link,
        instance_link,
    ]
    MetaLaneDemoModel.bind_class_config(class_config)

    opg_node = ObjectProjectionGraphNode(
        object_projection_graph_id=opg_id,
        class_config_id=class_config.id,
        is_root=True,
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        object_config_graph_id=graph_id,
        language=CodeLanguage.aware,
        name="MetaLaneDemo",
        projection_hash="sha256:meta-lane-demo",
        object_projection_graph_nodes=[opg_node],
        object_projection_graph_constructors=[
            ObjectProjectionGraphConstructor(
                object_projection_graph_id=opg_id,
                root_node_id=opg_node.id,
                function_constructor_id=constructor_link.id,
            )
        ],
    )
    graph = ObjectConfigGraph(
        id=graph_id,
        name="Meta Lane Demo",
        hash="sha256:meta-lane-demo-ocg",
        fqn_prefix="aware.tests",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                object_config_graph_id=graph_id,
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_config.class_fqn,
                class_config=class_config,
            )
        ],
        object_projection_graphs=[opg],
    )
    context = build_meta_graph_runtime_context(runtime_graphs=(graph,))
    return context, constructor_function.id, instance_function.id


def test_meta_graph_invoke_input_does_not_require_orchestration_fields() -> None:
    required = _required_field_names(MetaGraphInvokeFunctionInput)

    assert {"index", "actor_id", "function_id"}.issubset(required)
    assert "orchestration_context" not in required
    assert "environment_id" not in required
    assert "process_id" not in required
    assert "thread_id" not in required


def test_meta_graph_invoke_input_uses_meta_owned_call_target() -> None:
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, object()),
        actor_id=uuid4(),
        function_id=uuid4(),
    )

    assert request.call_target is MetaGraphCallTarget.instance


@pytest.mark.asyncio
async def test_meta_graph_runtime_bound_lane_activates_orm_provider() -> None:
    context, constructor_function_id, instance_function_id = _meta_lane_context()
    backend = _RecordingMetaGraphBackend()
    runtime = MetaGraphRuntime(backend=backend, context=context)
    branch_id = uuid4()
    actor_id = uuid4()

    lane = runtime.bind(
        projection="MetaLaneDemo",
        branch_id=branch_id,
        actor_id=actor_id,
    )

    with lane.activate(commit=True, publish=False):
        constructor_payload = await invoke_constructor(
            orm_class=MetaLaneDemoModel,
            function_name="create",
            payload={"label": "Ada"},
        )
        model = MetaLaneDemoModel(id=uuid4(), label="Ada")
        instance_payload = await invoke_instance(
            orm_model=model,
            function_name="rename",
            payload={"label": "Grace"},
        )

    assert constructor_payload == {"value": "call-1"}
    assert instance_payload == {"value": "call-2"}
    assert lane.branch_id == branch_id
    assert lane.last_commit_id == lane.records[-1].response.commit_id
    assert len(lane.records) == 2

    constructor_request = backend.requests[0]
    assert constructor_request.call_target is MetaGraphCallTarget.opg_constructor
    assert constructor_request.actor_id == actor_id
    assert constructor_request.function_id == constructor_function_id
    assert constructor_request.domain_branch_id == branch_id
    assert constructor_request.domain_projection_hash == "sha256:meta-lane-demo"
    assert constructor_request.kwargs["label"] == "Ada"

    instance_request = backend.requests[1]
    assert instance_request.call_target is MetaGraphCallTarget.instance
    assert instance_request.function_id == instance_function_id
    assert instance_request.target_object_id == model.id
    assert instance_request.domain_branch_id == branch_id
    assert instance_request.domain_projection_hash == "sha256:meta-lane-demo"
    assert instance_request.kwargs["label"] == "Grace"


@pytest.mark.asyncio
async def test_meta_graph_runtime_bound_lane_uses_graph_invocation_target_id() -> None:
    context, _, instance_function_id = _meta_lane_context()
    backend = _RecordingMetaGraphBackend()
    runtime = MetaGraphRuntime(backend=backend, context=context)
    branch_id = uuid4()
    class_instance_id = uuid4()
    model = MetaLaneDemoModel(id=uuid4(), label="Ada")
    model.bind_graph_invocation_target_id(class_instance_id)

    lane = runtime.bind(projection="MetaLaneDemo", branch_id=branch_id)

    with lane.activate(commit=True, publish=False):
        await invoke_instance(
            orm_model=model,
            function_name="rename",
            payload={"label": "Grace"},
        )

    request = backend.requests[0]
    assert request.call_target is MetaGraphCallTarget.instance
    assert request.function_id == instance_function_id
    assert request.target_object_id == class_instance_id
    assert model.id != class_instance_id


def test_meta_graph_lane_facade_has_no_runtime_harness_dependency() -> None:
    source = Path("workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/graph_lane.py").read_text(
        encoding="utf-8"
    )

    assert "aware_runtime" not in source
    assert "RuntimeHarness" not in source
    assert "FunctionCallInvoker" not in source
    assert "getattr(" not in source


def test_meta_graph_commit_function_target_index_prefers_class_label() -> None:
    function_id = uuid4()
    function_config = FunctionConfig(
        id=function_id,
        owner_key="aware.tests",
        name="attach_lane",
    )
    class_config = SimpleNamespace(
        name="Thread",
        class_config_function_configs=[
            SimpleNamespace(
                function_config_id=function_id,
                function_config=function_config,
            )
        ],
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(object_config_graph_nodes=[]),
        class_configs_by_id={uuid4(): class_config},
    )

    targets_by_id = build_meta_graph_function_target_index(index)

    resolved_target = targets_by_id[function_id]
    assert resolved_target.function_config is function_config
    assert resolved_target.operation_label == "Thread.attach_lane"


def test_meta_graph_commit_function_target_index_uses_function_node_label() -> None:
    function_id = uuid4()
    function_config = SimpleNamespace(id=function_id, name="read")
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_config_graph_nodes=[
                SimpleNamespace(
                    type=ObjectConfigGraphNodeType.function,
                    function_config=function_config,
                )
            ]
        ),
        class_configs_by_id={},
    )

    targets_by_id = build_meta_graph_function_target_index(index)

    resolved_target = targets_by_id[function_id]
    assert resolved_target.function_config is function_config
    assert resolved_target.operation_label == "read"


def test_meta_graph_commit_backend_stages_function_call_from_lane_scope() -> None:
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    opg_id = uuid4()
    call_key = uuid4()
    target_object_id = uuid4()
    function_config = FunctionConfig(
        id=function_id,
        owner_key="aware.tests",
        name="attach_lane",
    )
    class_config = SimpleNamespace(
        name="Thread",
        class_config_function_configs=[
            SimpleNamespace(
                function_config_id=function_id,
                function_config=function_config,
            )
        ],
    )
    index = _meta_commit_index(
        function_config=function_config,
        class_config=class_config,
        projection_hash=projection_hash,
        opg_id=opg_id,
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_key=call_key,
        target_object_id=target_object_id,
        expected_graph_hash_pre="sha256:test:pre",
    )

    staged_call = MetaGraphCommitInvocationBackend().stage_function_call(request)

    ocgi_id = stable_object_config_graph_identity_id(key="aware.tests")
    opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi_id,
        object_projection_graph_id=opg_id,
    )
    oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg_id,
        key=str(branch_id),
    )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi_id,
        object_instance_graph_id=oig_id,
    )
    oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=oigi_id,
        branch_id=branch_id,
    )
    lane_id = stable_lane_id(branch_id=branch_id, lane_hash=projection_hash)
    oig_lane_id = stable_object_instance_graph_lane_id(
        object_instance_graph_branch_id=oigb_id,
        lane_id=lane_id,
    )

    assert staged_call.resolved_target.operation_label == "Thread.attach_lane"
    assert staged_call.lane_scope.domain_branch_id == branch_id
    assert staged_call.lane_scope.domain_projection_hash == projection_hash
    assert staged_call.lane_scope.object_projection_graph_id == opg_id
    assert staged_call.lane_scope.object_instance_graph_id == oig_id
    assert staged_call.lane_scope.object_instance_graph_identity_id == oigi_id
    assert staged_call.lane_scope.object_instance_graph_branch_id == oigb_id
    assert staged_call.lane_scope.lane_id == lane_id
    assert staged_call.lane_scope.object_instance_graph_lane_id == oig_lane_id

    function_call = staged_call.function_call
    assert function_call.id == stable_function_call_id(
        object_instance_graph_lane_id=oig_lane_id,
        function_config_id=function_id,
        call_key=call_key,
    )
    assert function_call.object_instance_graph_lane_id == oig_lane_id
    assert function_call.call_key == call_key
    assert function_call.function_config is function_config
    assert function_call.function_config_id == function_id
    assert function_call.graph_hash_pre == "sha256:test:pre"
    assert function_call.target_class_instance_identity_id == (
        stable_class_instance_identity_id(
            object_instance_graph_identity_id=oigi_id,
            class_instance_id=target_object_id,
        )
    )


def test_meta_graph_commit_backend_stages_function_call_response() -> None:
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    index = _meta_commit_index(
        function_config=FunctionConfig(
            id=function_id,
            owner_key="aware.tests",
            name="read",
        ),
        projection_hash=projection_hash,
        opg_id=uuid4(),
    )
    backend = MetaGraphCommitInvocationBackend()
    staged_call = backend.stage_function_call(
        MetaGraphInvokeFunctionInput(
            index=cast(MetaGraphRuntimeIndex, index),
            actor_id=uuid4(),
            function_id=function_id,
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            call_key=uuid4(),
        )
    )

    response = backend.stage_function_call_response(
        function_call=staged_call.function_call,
        success=False,
        error_message="handler unavailable",
        execution_time_ms=12,
        graph_hash_post="sha256:test:post",
        root_class_instance_identity_id=uuid4(),
    )

    assert response.id == stable_function_call_response_id(
        function_call_id=staged_call.function_call.id
    )
    assert response.function_call_id == staged_call.function_call.id
    assert response.success is False
    assert response.error_message == "handler unavailable"
    assert response.execution_time_ms == 12
    assert response.graph_hash_post == "sha256:test:post"
    assert staged_call.function_call.function_call_response is response


@pytest.mark.asyncio
async def test_meta_graph_commit_backend_stages_instance_commit_action() -> None:
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    target_object_id = uuid4()
    index = _meta_commit_index(
        function_config=FunctionConfig(
            id=function_id,
            owner_key="aware.tests",
            name="mutate",
        ),
        projection_hash=projection_hash,
        opg_id=uuid4(),
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_target=MetaGraphCallTarget.instance,
        target_object_id=target_object_id,
        call_key=uuid4(),
    )
    backend = MetaGraphCommitInvocationBackend(
        handler_executor=_RecordingMetaGraphHandlerExecutor(
            result=MetaGraphHandlerExecutionResult(
                success=True,
                graph_hash_post="sha256:test:post",
            )
        )
    )
    staged_call = backend.stage_function_call(request)
    staged_result = await backend.execute_staged_function_call(
        request=request,
        staged_call=staged_call,
    )

    staged_action = backend.stage_commit_action(staged_result)

    action = staged_action.action
    assert staged_action.staged_result is staged_result
    assert action.operation_label == "mutate"
    assert action.call_target == MetaGraphCallTarget.instance.value
    assert action.function_id == function_id
    assert action.object_id == target_object_id
    assert (
        action.class_instance_identity_id
        == staged_call.function_call.target_class_instance_identity_id
    )


@pytest.mark.asyncio
async def test_meta_graph_commit_backend_stages_constructor_commit_action() -> None:
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    root_object_id = uuid4()
    root_identity_id = uuid4()
    index = _meta_commit_index(
        function_config=FunctionConfig(
            id=function_id,
            owner_key="aware.tests",
            name="create",
        ),
        projection_hash=projection_hash,
        opg_id=uuid4(),
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_target=MetaGraphCallTarget.opg_constructor,
        call_key=uuid4(),
    )
    backend = MetaGraphCommitInvocationBackend(
        handler_executor=_RecordingMetaGraphHandlerExecutor(
            result=MetaGraphHandlerExecutionResult(
                success=True,
                graph_hash_post="sha256:test:post",
                root_object_id=root_object_id,
                root_class_instance_identity_id=root_identity_id,
            )
        )
    )
    staged_call = backend.stage_function_call(request)
    staged_result = await backend.execute_staged_function_call(
        request=request,
        staged_call=staged_call,
    )

    action = backend.stage_commit_action(staged_result).action

    assert action.operation_label == "create"
    assert action.call_target == MetaGraphCallTarget.opg_constructor.value
    assert action.function_id == function_id
    assert action.object_id == root_object_id
    assert action.class_instance_identity_id == root_identity_id


@pytest.mark.asyncio
async def test_meta_graph_commit_backend_executes_handler_port_and_stages_response() -> (
    None
):
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    root_identity_id = uuid4()
    index = _meta_commit_index(
        function_config=FunctionConfig(
            id=function_id,
            owner_key="aware.tests",
            name="mutate",
        ),
        projection_hash=projection_hash,
        opg_id=uuid4(),
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_key=uuid4(),
    )
    executor = _RecordingMetaGraphHandlerExecutor(
        result=MetaGraphHandlerExecutionResult(
            success=True,
            payload=JsonObject({"ok": True}),
            execution_time_ms=17,
            graph_hash_post="sha256:test:post",
            root_object_id=uuid4(),
            root_class_instance_identity_id=root_identity_id,
        )
    )
    backend = MetaGraphCommitInvocationBackend(handler_executor=executor)
    staged_call = backend.stage_function_call(request)

    staged_result = await backend.execute_staged_function_call(
        request=request,
        staged_call=staged_call,
    )

    assert executor.calls == [
        MetaGraphHandlerExecutionRequest(
            request=request,
            staged_call=staged_call,
            execution_plan=backend.build_execution_plan(
                request=request,
                staged_call=staged_call,
            ),
            invoke_function=backend.invoke_function,
        )
    ]
    assert staged_result.staged_call is staged_call
    assert staged_result.execution_result is executor.result
    response = staged_result.function_call_response
    assert response.id == stable_function_call_response_id(
        function_call_id=staged_call.function_call.id
    )
    assert response.success is True
    assert response.execution_time_ms == 17
    assert response.graph_hash_post == "sha256:test:post"
    assert response.root_class_instance_identity_id == root_identity_id
    assert staged_call.function_call.function_call_response is response


@pytest.mark.asyncio
async def test_meta_graph_commit_backend_appends_domain_commit_and_returns_receipt() -> (
    None
):
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    call_key = uuid4()
    root_object_id = uuid4()
    index = _meta_commit_index(
        function_config=FunctionConfig(
            id=function_id,
            owner_key="aware.tests",
            name="mutate",
        ),
        projection_hash=projection_hash,
        opg_id=uuid4(),
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_key=call_key,
        expected_graph_hash_pre="sha256:test:pre",
    )
    staged_call = MetaGraphCommitInvocationBackend().stage_function_call(request)
    lane_scope = staged_call.lane_scope
    before_oig = ObjectInstanceGraph.model_construct(
        id=lane_scope.object_instance_graph_id
    )
    domain_commit_id = uuid4()
    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=(
            lane_scope.object_instance_graph_identity_id
        ),
        commit_id=domain_commit_id,
    )
    domain_commit = ObjectInstanceGraphCommit.model_construct(
        id=object_instance_graph_commit_id,
        commit=Commit.model_construct(id=domain_commit_id),
        object_instance_graph_identity_id=(
            lane_scope.object_instance_graph_identity_id
        ),
        object_instance_graph_id=lane_scope.object_instance_graph_id,
        root_source_object_id=root_object_id,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        object_instance_graph_changes=[],
    )
    executor = _RecordingMetaGraphHandlerExecutor(
        result=MetaGraphHandlerExecutionResult(
            success=True,
            payload=JsonObject({"ok": True}),
            execution_time_ms=3,
            graph_hash_pre="sha256:test:pre",
            graph_hash_post="sha256:test:post",
            root_object_id=root_object_id,
            before_oig=before_oig,
        )
    )
    committer = _RecordingInvocationLaneCommitter(commit=domain_commit)
    reaction_runner = _RecordingRequiredReactionRunner()
    backend = MetaGraphCommitInvocationBackend(
        handler_executor=executor,
        lane_committer=committer,
        required_reaction_runner=reaction_runner.run,
    )

    receipt = await backend.invoke_function(request)

    assert len(committer.calls) == 1
    committed = committer.calls[0]
    assert committed.branch_id == branch_id
    assert committed.projection_hash == projection_hash
    assert committed.object_instance_graph_identity_id == (
        lane_scope.object_instance_graph_identity_id
    )
    assert committed.object_instance_graph_id == lane_scope.object_instance_graph_id
    assert committed.before_oig is before_oig
    assert committed.root_object_id == root_object_id
    assert committed.changes == []
    assert committed.graph_hash_pre == "sha256:test:pre"
    assert committed.graph_hash_post == "sha256:test:post"
    assert committed.author_id == request.actor_id
    assert committed.commit_action.operation_label == "mutate"
    assert committed.commit_action.call_target == MetaGraphCallTarget.instance.value
    assert committed.commit_action.function_id == function_id
    assert len(reaction_runner.contexts) == 1
    reaction_context = reaction_runner.contexts[0]
    assert reaction_context.index is index
    assert reaction_context.actor_id == request.actor_id
    assert reaction_context.domain_branch_id == branch_id
    assert reaction_context.domain_projection_hash == projection_hash
    assert reaction_context.domain_commit is domain_commit
    assert reaction_context.perf_ms == {"append_ms": 4}

    response = executor.calls[0].staged_call.function_call.function_call_response
    assert response is not None
    assert len(response.function_call_response_commits) == 1
    assert (
        response.function_call_response_commits[0].object_instance_graph_commit_id
        == object_instance_graph_commit_id
    )
    assert receipt.status == "succeeded"
    assert receipt.payload == JsonObject({"ok": True})
    assert receipt.execution_time_ms == 3
    assert receipt.root_object_id == root_object_id
    assert receipt.graph_hash_pre == "sha256:test:pre"
    assert receipt.graph_hash_post == "sha256:test:post"
    assert receipt.changes == JsonArray()
    assert receipt.logs == ("aware_meta.test_required_reaction:succeeded",)
    assert receipt.function_call_id == response.function_call_id
    assert receipt.function_call_response_id == response.id
    assert receipt.commit_id == domain_commit_id
    assert receipt.object_instance_graph_commit_id == object_instance_graph_commit_id
    assert receipt.commit_action is not None
    assert receipt.commit_action.operation_label == "mutate"
    assert receipt.commit_action.call_target == MetaGraphCallTarget.instance.value
    assert receipt.commit_action.function_id == function_id


@pytest.mark.asyncio
async def test_meta_graph_commit_backend_ensures_oigi_head_before_instance_domain_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    oigi_projection_hash = "sha256:test:oigi"
    root_object_id = uuid4()
    events: list[str] = []
    index = _meta_commit_index(
        function_config=FunctionConfig(
            id=function_id,
            owner_key="aware.tests",
            name="mutate",
        ),
        projection_hash=projection_hash,
        opg_id=uuid4(),
    )
    index.ocg.object_projection_graphs = [
        SimpleNamespace(
            name="ObjectInstanceGraphIdentity",
            projection_hash=oigi_projection_hash,
        )
    ]
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_key=uuid4(),
        expected_graph_hash_pre="sha256:test:pre",
    )
    staged_call = MetaGraphCommitInvocationBackend().stage_function_call(request)
    lane_scope = staged_call.lane_scope
    before_oig = ObjectInstanceGraph.model_construct(
        id=lane_scope.object_instance_graph_id
    )
    domain_commit_id = uuid4()
    domain_commit = ObjectInstanceGraphCommit.model_construct(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=(
                lane_scope.object_instance_graph_identity_id
            ),
            commit_id=domain_commit_id,
        ),
        commit=Commit.model_construct(id=domain_commit_id),
        object_instance_graph_identity_id=(
            lane_scope.object_instance_graph_identity_id
        ),
        object_instance_graph_id=lane_scope.object_instance_graph_id,
        root_source_object_id=root_object_id,
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        object_instance_graph_changes=[],
    )

    async def _ensure_oigi_head(**kwargs: object) -> None:
        events.append("ensure_oigi_head")
        assert kwargs["index"] is index
        assert kwargs["object_instance_graph_id"] == lane_scope.object_instance_graph_id
        assert kwargs["domain_projection_hash"] == projection_hash
        assert kwargs["author_id"] == request.actor_id
        assert kwargs["label"] == "mutate"
        assert kwargs["perf_metric_prefix"] == "domain_commit_oigi_lane_ensure"
        perf_ms = kwargs["perf_ms"]
        assert isinstance(perf_ms, dict)
        perf_ms["domain_commit_oigi_lane_ensure_total_ms"] = 1

    class _EventCommitter(_RecordingInvocationLaneCommitter):
        async def commit(
            self,
            **kwargs: object,
        ) -> ObjectInstanceGraphCommit | None:
            events.append("commit")
            return await super().commit(**kwargs)

    class _EventReactionRunner(_RecordingRequiredReactionRunner):
        async def run(
            self,
            context: RuntimeCommitReactionContext,
        ) -> tuple[RuntimeCommitReactionReceipt, ...]:
            events.append("reaction")
            return await super().run(context)

    monkeypatch.setattr(
        graph_commit_backend_module,
        "ensure_object_instance_graph_identity_lane_head",
        _ensure_oigi_head,
    )
    executor = _RecordingMetaGraphHandlerExecutor(
        result=MetaGraphHandlerExecutionResult(
            success=True,
            graph_hash_pre="sha256:test:pre",
            graph_hash_post="sha256:test:post",
            root_object_id=root_object_id,
            before_oig=before_oig,
        )
    )
    reaction_runner = _EventReactionRunner()
    backend = MetaGraphCommitInvocationBackend(
        handler_executor=executor,
        lane_committer=_EventCommitter(commit=domain_commit),
        required_reaction_runner=reaction_runner.run,
    )

    receipt = await backend.invoke_function(request)

    assert receipt.status == "succeeded"
    assert events == ["ensure_oigi_head", "commit", "reaction"]
    assert reaction_runner.contexts[0].perf_ms == {
        "domain_commit_oigi_lane_ensure_total_ms": 1,
        "append_ms": 4,
    }


@pytest.mark.asyncio
async def test_meta_graph_commit_backend_uses_append_ready_changes_for_append_request() -> (
    None
):
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    target_object_id = uuid4()
    index = _meta_commit_index(
        function_config=FunctionConfig(
            id=function_id,
            owner_key="aware.tests",
            name="mutate",
        ),
        projection_hash=projection_hash,
        opg_id=uuid4(),
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_key=uuid4(),
        target_object_id=target_object_id,
    )
    backend = MetaGraphCommitInvocationBackend()
    staged_call = backend.stage_function_call(request)
    execution_plan = backend.build_execution_plan(
        request=request,
        staged_call=staged_call,
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=staged_call.lane_scope.object_instance_graph_id
    )
    append_ready = MetaGraphAppendReadyChanges(
        execution_plan=execution_plan,
        before_oig=before_oig,
        changes=(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        root_object_id=target_object_id,
    )
    executor = _RecordingMetaGraphHandlerExecutor(
        result=MetaGraphHandlerExecutionResult(
            success=True,
            append_ready_changes=append_ready,
        )
    )
    backend = MetaGraphCommitInvocationBackend(handler_executor=executor)

    staged_result = await backend.execute_staged_function_call(
        request=request,
        staged_call=staged_call,
    )
    staged_action = backend.stage_commit_action(staged_result)
    append_request = backend.build_domain_commit_append_request(staged_action)

    assert append_request.before_oig is before_oig
    assert append_request.changes == ()
    assert append_request.graph_hash_pre == "sha256:test:pre"
    assert append_request.graph_hash_post == "sha256:test:post"
    assert append_request.root_object_id == target_object_id


@pytest.mark.asyncio
async def test_meta_graph_commit_backend_fails_before_append_without_commit_inputs() -> (
    None
):
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    call_key = uuid4()
    index = _meta_commit_index(
        function_config=FunctionConfig(
            id=function_id,
            owner_key="aware.tests",
            name="mutate",
        ),
        projection_hash=projection_hash,
        opg_id=uuid4(),
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_key=call_key,
    )
    executor = _RecordingMetaGraphHandlerExecutor(
        result=MetaGraphHandlerExecutionResult(
            success=True,
            execution_time_ms=1,
            graph_hash_post="sha256:test:post",
        )
    )
    runtime = MetaGraphRuntime(
        backend=MetaGraphCommitInvocationBackend(handler_executor=executor)
    )

    with pytest.raises(MetaGraphCommitInvocationNotReadyError) as exc_info:
        await runtime.invoke_function(request)

    message = str(exc_info.value)
    assert "OIG commit append requires handler result before_oig" in message
    assert "function_call_id=" in message
    assert "function_call_response_id=" in message
    assert "commit_action=mutate" in message
    assert len(executor.calls) == 1


def test_meta_graph_facade_and_engine_do_not_expose_legacy_request_adapter() -> None:
    assert not hasattr(MetaGraphRuntime, "_to_legacy_request")
    assert not hasattr(MetaGraphInvocationEngine, "_to_legacy_request")


def test_meta_graph_facade_and_engine_do_not_expose_legacy_constructor_knobs() -> None:
    for runtime_type in (MetaGraphRuntime, MetaGraphInvocationEngine):
        params = inspect.signature(runtime_type).parameters
        assert "legacy_invoker" not in params
        assert "manifest_path" not in params


def test_meta_graph_runtime_requires_explicit_invocation_authority() -> None:
    with pytest.raises(ValueError, match="backend or invocation_engine"):
        MetaGraphRuntime()


def test_meta_graph_facade_and_engine_do_not_import_environment_dtos() -> None:
    runtime_root = Path(__file__).parents[1] / "aware_meta" / "runtime"
    for path in [
        runtime_root / "graph_runtime.py",
        runtime_root / "invocation_engine.py",
    ]:
        source = path.read_text()
        assert "aware_environment_api.comms.models.environment" not in source
        assert "InvokeFunctionRequest" not in source
        assert "InvokeFunctionResponse" not in source
        assert "LegacyFunctionCallInvocationBackend" not in source
        assert "get" "attr(" not in source


@pytest.mark.asyncio
async def test_meta_graph_runtime_delegates_to_invocation_engine() -> None:
    engine = _RecordingInvocationEngine()
    runtime = MetaGraphRuntime(
        invocation_engine=cast(MetaGraphInvocationEngine, engine)
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, object()),
        actor_id=uuid4(),
        function_id=uuid4(),
    )

    receipt = await runtime.invoke_function(request)

    assert engine.calls == [request]
    assert receipt is engine.receipt


@pytest.mark.asyncio
async def test_meta_graph_invocation_engine_accepts_native_backend_without_orchestration_context() -> (
    None
):
    backend = _RecordingInvocationBackend()
    engine = MetaGraphInvocationEngine(
        backend=cast(MetaGraphInvocationBackend, backend)
    )
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, object()),
        actor_id=uuid4(),
        function_id=uuid4(),
    )

    receipt = await engine.invoke_function(request)

    assert backend.calls == [request]
    assert receipt is backend.receipt


@pytest.mark.asyncio
async def test_meta_graph_runtime_accepts_native_backend_without_orchestration_context() -> (
    None
):
    backend = _RecordingInvocationBackend()
    runtime = MetaGraphRuntime(backend=cast(MetaGraphInvocationBackend, backend))
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, object()),
        actor_id=uuid4(),
        function_id=uuid4(),
    )

    receipt = await runtime.invoke_function(request)

    assert backend.calls == [request]
    assert receipt is backend.receipt


@pytest.mark.asyncio
async def test_meta_graph_commit_invocation_backend_fails_closed() -> None:
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:domain"
    call_key = uuid4()
    function_config = FunctionConfig(
        id=function_id,
        owner_key="aware.tests",
        name="attach_lane",
    )
    class_config = SimpleNamespace(
        name="Thread",
        class_config_function_configs=[
            SimpleNamespace(
                function_config_id=function_id,
                function_config=function_config,
            )
        ],
    )
    index = _meta_commit_index(
        function_config=function_config,
        class_config=class_config,
        projection_hash=projection_hash,
        opg_id=uuid4(),
    )
    runtime = MetaGraphRuntime(backend=MetaGraphCommitInvocationBackend())
    request = MetaGraphInvokeFunctionInput(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=uuid4(),
        function_id=function_id,
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_key=call_key,
    )

    with pytest.raises(MetaGraphCommitInvocationNotReadyError) as exc_info:
        await runtime.invoke_function(request)

    message = str(exc_info.value)
    assert "FunctionCall -> FunctionCallResponse -> OIG Commit" in message
    assert "Resolved function target=Thread.attach_lane" in message
    assert "function_call_id=" in message
    assert "not wired yet" in message


@pytest.mark.asyncio
async def test_meta_graph_commit_invocation_backend_rejects_unknown_function() -> None:
    function_id = uuid4()
    runtime = MetaGraphRuntime(backend=MetaGraphCommitInvocationBackend())
    request = MetaGraphInvokeFunctionInput(
        index=cast(
            MetaGraphRuntimeIndex,
            SimpleNamespace(
                ocg=SimpleNamespace(object_config_graph_nodes=[]),
                class_configs_by_id={},
            ),
        ),
        actor_id=uuid4(),
        function_id=function_id,
    )

    with pytest.raises(ValueError, match=f"FunctionConfig not found.*{function_id}"):
        await runtime.invoke_function(request)


def test_meta_graph_commit_invocation_backend_has_no_legacy_runtime_imports() -> None:
    source = (
        Path(__file__).parents[1]
        / "aware_meta"
        / "runtime"
        / "graph_commit_invocation_backend.py"
    ).read_text()

    forbidden = [
        "aware_environment_api.comms.models.environment",
        "aware_runtime",
        "FunctionCallInvoker",
        "RuntimeHarness",
        "InvokeFunctionRequest",
        "InvokeFunctionResponse",
        "InvokeFunctionCallTarget",
        "get" "attr(",
    ]
    for token in forbidden:
        assert token not in source


class _RecordingInvocationEngine:
    def __init__(self) -> None:
        self.calls: list[MetaGraphInvokeFunctionInput] = []
        self.receipt = MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=None,
            domain_branch_id=None,
            domain_projection_hash=None,
            payload=None,
            error=None,
            logs=(),
            execution_time_ms=None,
            root_object_id=None,
            graph_hash_pre=None,
            graph_hash_post=None,
            changes=JsonArray(),
            function_call_id=None,
            function_call_response_id=None,
            commit_id=None,
            object_instance_graph_commit_id=None,
        )

    async def invoke_function(
        self, request: MetaGraphInvokeFunctionInput
    ) -> MetaGraphCommitReceipt:
        self.calls.append(request)
        return self.receipt


class _RecordingMetaGraphHandlerExecutor:
    def __init__(self, *, result: MetaGraphHandlerExecutionResult) -> None:
        self.calls: list[MetaGraphHandlerExecutionRequest] = []
        self.result = result

    async def execute_function(
        self,
        request: MetaGraphHandlerExecutionRequest,
    ) -> MetaGraphHandlerExecutionResult:
        self.calls.append(request)
        return self.result


class _RecordingInvocationLaneCommitter:
    def __init__(self, *, commit: ObjectInstanceGraphCommit | None) -> None:
        self.commit_result = commit
        self.calls: list[SimpleNamespace] = []

    async def commit(
        self,
        **kwargs: object,
    ) -> ObjectInstanceGraphCommit | None:
        self.calls.append(SimpleNamespace(**kwargs))
        return self.commit_result

    def last_commit_perf_profile_snapshot(self) -> dict[str, int]:
        return {"append_ms": 4}


class _RecordingRequiredReactionRunner:
    def __init__(self) -> None:
        self.contexts: list[RuntimeCommitReactionContext] = []

    async def run(
        self,
        context: RuntimeCommitReactionContext,
    ) -> tuple[RuntimeCommitReactionReceipt, ...]:
        self.contexts.append(context)
        return (
            RuntimeCommitReactionReceipt(
                provider_key="aware_meta",
                reaction_key="test_required_reaction",
                status="succeeded",
            ),
        )


class _RecordingInvocationBackend:
    def __init__(self) -> None:
        self.calls: list[MetaGraphInvokeFunctionInput] = []
        self.receipt = MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=None,
            domain_branch_id=None,
            domain_projection_hash=None,
            payload=JsonObject({"native": True}),
            error=None,
            logs=(),
            execution_time_ms=None,
            root_object_id=None,
            graph_hash_pre=None,
            graph_hash_post=None,
            changes=JsonArray(),
            function_call_id=None,
            function_call_response_id=None,
            commit_id=None,
            object_instance_graph_commit_id=None,
        )

    async def invoke_function(
        self, request: MetaGraphInvokeFunctionInput
    ) -> MetaGraphCommitReceipt:
        self.calls.append(request)
        return self.receipt
