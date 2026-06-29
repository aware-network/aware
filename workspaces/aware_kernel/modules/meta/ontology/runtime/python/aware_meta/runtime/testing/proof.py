from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID, uuid4

from aware_code.types import JsonArray, JsonObject
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID
from aware_meta.runtime.graph_runtime import MetaGraphRuntime
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.runtime.testing import MetaOIGAssertions
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


@dataclass(frozen=True, slots=True)
class LaneIds:
    branch_id: UUID | None = None
    actor_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class RootObjectId:
    pass


ROOT_OBJECT_ID = RootObjectId()


@dataclass(frozen=True, slots=True)
class SourceObjectId:
    value: UUID


@dataclass(frozen=True, slots=True)
class ProofCall:
    target: Literal["constructor", "instance"]
    class_fqn: str
    function_name: str
    args: Sequence[Any] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    object_id: UUID | RootObjectId | SourceObjectId | None = None
    expected_root_object_id: UUID | None = None
    commit: bool = True
    publish: bool = False
    allow_noop_commit: bool = False


@dataclass(frozen=True, slots=True)
class MultiLaneProofCall:
    opg_name: str
    call: ProofCall
    root_class_fqn: str | None = None


@dataclass(frozen=True, slots=True)
class ProofResult:
    projection_hash: str
    opg_name: str
    branch_id: UUID
    root_object_id: UUID | None
    responses: tuple[MetaGraphCommitReceipt, ...]
    commits: tuple[ObjectInstanceGraphCommit, ...]
    head: dict[str, Any]
    oig: ObjectInstanceGraph


@dataclass(slots=True)
class _MultiLaneProofState:
    projection_hash: str
    branch_id: UUID | None
    root_object_id: UUID | None = None
    prev_graph_hash_post: str | None = None
    responses: list[MetaGraphCommitReceipt] = field(default_factory=list)
    commits: list[ObjectInstanceGraphCommit] = field(default_factory=list)


async def run_meta_runtime_proof(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    opg_name: str,
    calls: Sequence[ProofCall],
    projection_hash: str | None = None,
    root_class_fqn: str | None = None,
) -> tuple[ProofResult, MetaOIGAssertions]:
    context = _require_runtime_context(runtime)
    index = context.index
    opg = _resolve_opg(
        index=index,
        opg_name=opg_name,
        projection_hash=projection_hash,
        root_class_fqn=root_class_fqn,
    )
    state = _MultiLaneProofState(
        projection_hash=opg.projection_hash,
        branch_id=lane.branch_id or uuid4(),
    )
    await _run_calls_for_state(
        runtime=runtime,
        index=index,
        lane=lane,
        state=state,
        calls=calls,
    )
    return await _finalize_state(
        index=index,
        opg_name=opg_name,
        state=state,
    )


async def run_multi_lane_meta_runtime_proof(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    calls: Sequence[MultiLaneProofCall],
) -> tuple[dict[str, ProofResult], dict[str, MetaOIGAssertions]]:
    if not calls:
        raise AssertionError("Multi-lane Meta runtime proof requires at least one call")

    context = _require_runtime_context(runtime)
    index = context.index
    lane_states: dict[str, _MultiLaneProofState] = {}
    shared_branch_id = lane.branch_id or uuid4()

    for lane_call in calls:
        opg = _resolve_opg(
            index=index,
            opg_name=lane_call.opg_name,
            root_class_fqn=lane_call.root_class_fqn,
        )
        state = lane_states.get(lane_call.opg_name)
        if state is None:
            state = _MultiLaneProofState(
                projection_hash=opg.projection_hash,
                branch_id=shared_branch_id,
            )
            lane_states[lane_call.opg_name] = state

        await _run_calls_for_state(
            runtime=runtime,
            index=index,
            lane=lane,
            state=state,
            calls=(lane_call.call,),
        )
        if state.branch_id is not None:
            if shared_branch_id is None:
                shared_branch_id = state.branch_id
            elif shared_branch_id != state.branch_id:
                raise AssertionError(
                    "Multi-lane Meta runtime proof branch divergence detected: "
                    f"expected={shared_branch_id} got={state.branch_id} "
                    f"opg={lane_call.opg_name!r}"
                )
            for other in lane_states.values():
                if other.branch_id is None:
                    other.branch_id = shared_branch_id

    results: dict[str, ProofResult] = {}
    assertions_by_opg: dict[str, MetaOIGAssertions] = {}
    for opg_name, state in lane_states.items():
        result, assertions = await _finalize_state(
            index=index,
            opg_name=opg_name,
            state=state,
        )
        results[opg_name] = result
        assertions_by_opg[opg_name] = assertions
    return results, assertions_by_opg


async def _run_calls_for_state(
    *,
    runtime: MetaGraphRuntime,
    index: MetaGraphRuntimeIndex,
    lane: LaneIds,
    state: _MultiLaneProofState,
    calls: Sequence[ProofCall],
) -> None:
    store = FSCommitStore()
    for call in calls:
        response = await _invoke_call(
            runtime=runtime,
            index=index,
            lane=lane,
            state=state,
            call=call,
        )
        if response.status != "succeeded":
            raise AssertionError(_invoke_failure_text(response))
        state.responses.append(response)

        if call.expected_root_object_id is not None:
            assert response.root_object_id == call.expected_root_object_id

        if response.domain_branch_id is not None:
            state.branch_id = response.domain_branch_id
        if state.root_object_id is None and response.root_object_id is not None:
            state.root_object_id = response.root_object_id

        if not call.commit:
            continue
        if response.commit_id is None:
            if not call.allow_noop_commit:
                raise AssertionError(
                    "Meta runtime proof expected a commit_id for write call, "
                    "but function returned no-op commit"
                )
            continue
        assert response.graph_hash_post
        if state.prev_graph_hash_post is not None:
            assert response.graph_hash_pre == state.prev_graph_hash_post
        state.prev_graph_hash_post = response.graph_hash_post

        if state.branch_id is None:
            raise AssertionError("Meta runtime proof missing branch_id after commit")
        head = await store.head(
            branch_id=state.branch_id,
            projection_hash=state.projection_hash,
        )
        assert head and head.get("commit_id") == str(response.commit_id)
        commit = await store.get_commit(
            branch_id=state.branch_id,
            projection_hash=state.projection_hash,
            commit_id=response.commit_id,
        )
        assert commit is not None
        state.commits.append(commit)


async def _invoke_call(
    *,
    runtime: MetaGraphRuntime,
    index: MetaGraphRuntimeIndex,
    lane: LaneIds,
    state: _MultiLaneProofState,
    call: ProofCall,
) -> MetaGraphCommitReceipt:
    function_config = _resolve_function_config(
        index=index,
        class_fqn=call.class_fqn,
        function_name=call.function_name,
    )
    target_object_id: UUID | None = None
    call_target = MetaGraphCallTarget.opg_constructor
    object_projection_graph_id: UUID | None = index.opg_by_hash[
        state.projection_hash
    ].id

    if call.target == "instance":
        call_target = MetaGraphCallTarget.instance
        object_projection_graph_id = None
        if call.object_id is None:
            raise AssertionError(
                "Instance call requires object_id; pass an explicit UUID, "
                "ROOT_OBJECT_ID, or SourceObjectId."
            )
        if isinstance(call.object_id, RootObjectId):
            target_object_id = await _resolve_lane_root_class_instance_id(
                index=index,
                branch_id=state.branch_id,
                projection_hash=state.projection_hash,
            )
        elif isinstance(call.object_id, SourceObjectId):
            target_object_id = await _resolve_lane_class_instance_id_for_source_object(
                index=index,
                branch_id=state.branch_id,
                projection_hash=state.projection_hash,
                source_object_id=call.object_id.value,
            )
        else:
            target_object_id = call.object_id

    return await runtime.invoke_function(
        MetaGraphInvokeFunctionInput(
            index=index,
            actor_id=lane.actor_id or META_SYSTEM_ACTOR_ID,
            function_id=function_config.id,
            domain_branch_id=state.branch_id,
            domain_projection_hash=state.projection_hash,
            call_target=call_target,
            target_object_id=target_object_id,
            object_projection_graph_id=object_projection_graph_id,
            args=JsonArray([_jsonify_value(value) for value in call.args]),
            kwargs=JsonObject(
                {str(key): _jsonify_value(value) for key, value in call.kwargs.items()}
            ),
            commit=call.commit,
            publish=call.publish,
        )
    )


async def _finalize_state(
    *,
    index: MetaGraphRuntimeIndex,
    opg_name: str,
    state: _MultiLaneProofState,
) -> tuple[ProofResult, MetaOIGAssertions]:
    if state.branch_id is None:
        raise AssertionError("Meta runtime proof requires a committed branch_id")
    store = FSCommitStore()
    head = await store.head(
        branch_id=state.branch_id,
        projection_hash=state.projection_hash,
    )
    assert head and "object_instance_graph_id" in head
    final_commit_id = _final_commit_id(state=state, head=head)
    opg = index.opg_by_hash[state.projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=state.branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=final_commit_id,
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    if state.prev_graph_hash_post is not None:
        assert oig.hash == state.prev_graph_hash_post

    result = ProofResult(
        projection_hash=state.projection_hash,
        opg_name=opg_name,
        branch_id=state.branch_id,
        root_object_id=state.root_object_id,
        responses=tuple(state.responses),
        commits=tuple(state.commits),
        head=head,
        oig=oig,
    )
    return result, MetaOIGAssertions(oig=oig, index=index)


def _require_runtime_context(runtime: MetaGraphRuntime):
    context = runtime.context
    if context is None:
        raise ValueError("Meta runtime proof requires a runtime context.")
    return context


def _resolve_opg(
    *,
    index: MetaGraphRuntimeIndex,
    opg_name: str,
    projection_hash: str | None = None,
    root_class_fqn: str | None = None,
) -> ObjectProjectionGraph:
    if projection_hash is not None:
        opg = index.opg_by_hash.get(projection_hash)
        if opg is None:
            raise AssertionError(
                f"Projection hash {projection_hash!r} not found in Meta index"
            )
        if opg.name != opg_name:
            raise AssertionError(
                f"Projection hash {projection_hash!r} resolved to OPG "
                f"{opg.name!r}, expected {opg_name!r}"
            )
        return opg

    matches = [
        opg for opg in index.opg_by_hash.values() if (opg.name or "") == opg_name
    ]
    if root_class_fqn is not None:
        matches = [
            opg
            for opg in matches
            if _resolve_opg_root_class_fqn(index=index, opg=opg) == root_class_fqn
        ]
    if len(matches) != 1:
        if root_class_fqn is None:
            raise AssertionError(
                f"Expected exactly one OPG named {opg_name!r}, found {len(matches)}"
            )
        raise AssertionError(
            f"Expected exactly one OPG named {opg_name!r} with root class "
            f"{root_class_fqn!r}, found {len(matches)}"
        )
    return matches[0]


def _resolve_opg_root_class_fqn(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph,
) -> str:
    roots = [node for node in opg.object_projection_graph_nodes if node.is_root]
    if len(roots) != 1:
        raise AssertionError(
            f"Expected exactly one root node for OPG {opg.name!r}, found {len(roots)}"
        )
    class_config = index.class_configs_by_id.get(roots[0].class_config_id)
    if class_config is None:
        raise AssertionError(
            f"Meta index is missing ClassConfig {roots[0].class_config_id} "
            f"for OPG {opg.name!r}"
        )
    return class_config.class_fqn


def _resolve_function_config(
    *,
    index: MetaGraphRuntimeIndex,
    class_fqn: str,
    function_name: str,
) -> FunctionConfig:
    matches: list[FunctionConfig] = []
    for class_config in index.class_configs_by_id.values():
        if class_config.class_fqn != class_fqn:
            continue
        for edge in class_config.class_config_function_configs:
            function_config = edge.function_config
            if function_config.name == function_name:
                matches.append(function_config)
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
        f"matches={[item.id for item in matches]}"
    )


async def _resolve_lane_root_class_instance_id(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID | None,
    projection_hash: str,
) -> UUID:
    if branch_id is None:
        raise AssertionError("ROOT_OBJECT_ID requires an active branch_id")
    oig = await _materialize_lane_head(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    root_id = oig.root_class_instance_id
    if root_id is None:
        raise AssertionError(
            "Materialized lane is missing root_class_instance_id: "
            f"branch_id={branch_id} projection_hash={projection_hash}"
        )
    return root_id


async def _resolve_lane_class_instance_id_for_source_object(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID | None,
    projection_hash: str,
    source_object_id: UUID,
) -> UUID:
    if branch_id is None:
        raise AssertionError("SourceObjectId requires an active branch_id")
    oig = await _materialize_lane_head(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    for instance in oig.class_instances:
        if instance.source_object_id != source_object_id:
            continue
        if instance.id is None:
            break
        return instance.id
    raise AssertionError(
        "SourceObjectId could not resolve to a class-instance id in the "
        "materialized lane: "
        f"source_object_id={source_object_id} "
        f"branch_id={branch_id} projection_hash={projection_hash}"
    )


async def _materialize_lane_head(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> ObjectInstanceGraph:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if (
        not head
        or not head.get("commit_id")
        or not head.get("object_instance_graph_id")
    ):
        raise AssertionError(
            "Meta runtime proof requires a committed lane head: "
            f"branch_id={branch_id} projection_hash={projection_hash}"
        )
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return oig


def _final_commit_id(
    *,
    state: _MultiLaneProofState,
    head: Mapping[str, object],
) -> UUID:
    for response in reversed(state.responses):
        if response.commit_id is not None:
            return response.commit_id
    if head.get("commit_id"):
        return UUID(str(head["commit_id"]))
    raise AssertionError("Meta runtime proof requires a final commit_id")


def _invoke_failure_text(response: MetaGraphCommitReceipt) -> str:
    summary = response.error or f"invoke failed with status={response.status}"
    if not response.logs:
        return summary
    return "\n".join([summary, *response.logs])


def _jsonify_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, list):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify_value(item) for key, item in value.items()}
    return value


__all__ = [
    "LaneIds",
    "MultiLaneProofCall",
    "ProofCall",
    "ProofResult",
    "ROOT_OBJECT_ID",
    "RootObjectId",
    "SourceObjectId",
    "run_meta_runtime_proof",
    "run_multi_lane_meta_runtime_proof",
]
