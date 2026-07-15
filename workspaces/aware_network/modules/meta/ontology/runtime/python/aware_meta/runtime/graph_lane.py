from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol, cast
from uuid import UUID

from pydantic import BaseModel

from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID
from aware_meta.runtime.graph_context import MetaGraphRuntimeContext
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    InvocationProvider,
    reset_invocation_provider,
    set_invocation_provider,
)


@dataclass(slots=True)
class MetaGraphRuntimeLaneBinding:
    projection_hash: str
    branch_id: UUID
    actor_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class MetaGraphRuntimeLaneInvokeRecord:
    call_target: MetaGraphCallTarget
    class_fqn: str
    function_name: str
    function_id: UUID
    object_id: UUID | None
    commit: bool
    publish: bool
    response: MetaGraphCommitReceipt


class MetaGraphRuntimeProtocol(Protocol):
    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionInput,
    ) -> MetaGraphCommitReceipt: ...


def bind_meta_graph_runtime_lane(
    *,
    runtime: MetaGraphRuntimeProtocol,
    context: MetaGraphRuntimeContext,
    projection: str,
    branch_id: UUID,
    actor_id: UUID | None = None,
) -> MetaGraphBoundRuntimeLane:
    projection_hash = _resolve_projection_hash(
        context=context,
        projection=projection,
    )
    return MetaGraphBoundRuntimeLane(
        backend=MetaGraphRuntimeLaneBackend(
            runtime=runtime,
            index=context.index,
        ),
        binding=MetaGraphRuntimeLaneBinding(
            projection_hash=projection_hash,
            branch_id=branch_id,
            actor_id=actor_id,
        ),
    )


@dataclass(slots=True)
class MetaGraphRuntimeLaneBackend:
    runtime: MetaGraphRuntimeProtocol
    index: MetaGraphRuntimeIndex

    async def invoke_constructor(
        self,
        *,
        lane: MetaGraphRuntimeLaneBinding,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, object],
        commit: bool,
        publish: bool,
    ) -> tuple[UUID, MetaGraphCommitReceipt]:
        function_link = _resolve_function_link_for_class(
            orm_class=orm_class,
            function_name=function_name,
        )
        function_id = function_link.function_config.id
        opg = _resolve_constructor_opg(
            index=self.index,
            orm_class=orm_class,
            function_name=function_name,
            active_projection_hash=lane.projection_hash,
        )
        request = MetaGraphInvokeFunctionInput(
            index=self.index,
            actor_id=lane.actor_id or META_SYSTEM_ACTOR_ID,
            function_id=function_id,
            domain_branch_id=lane.branch_id,
            domain_projection_hash=opg.projection_hash,
            call_target=MetaGraphCallTarget.opg_constructor,
            object_projection_graph_id=opg.id,
            args=JsonArray([]),
            kwargs=_jsonify_payload_mapping(payload),
            commit=commit,
            publish=publish,
        )
        return function_id, await self.runtime.invoke_function(request)

    async def invoke_instance(
        self,
        *,
        lane: MetaGraphRuntimeLaneBinding,
        orm_model: ORMModel,
        function_name: str,
        payload: Mapping[str, object],
        commit: bool,
        publish: bool,
    ) -> tuple[UUID, MetaGraphCommitReceipt]:
        source_object_id = orm_model.id
        if not isinstance(source_object_id, UUID):
            raise ValueError(
                "Meta graph instance invocation requires ORM model with UUID id; "
                f"class={type(orm_model).__module__}.{type(orm_model).__name__} "
                f"function={function_name}"
            )
        target_object_id = orm_model.graph_invocation_target_id
        orm_class = type(orm_model)
        function_id = _resolve_function_id_for_class(
            orm_class=orm_class,
            function_name=function_name,
        )
        request = MetaGraphInvokeFunctionInput(
            index=self.index,
            actor_id=lane.actor_id or META_SYSTEM_ACTOR_ID,
            function_id=function_id,
            domain_branch_id=lane.branch_id,
            domain_projection_hash=lane.projection_hash,
            call_target=MetaGraphCallTarget.instance,
            target_object_id=target_object_id,
            args=JsonArray([]),
            kwargs=_jsonify_payload_mapping(payload),
            commit=commit,
            publish=publish,
        )
        return function_id, await self.runtime.invoke_function(request)


@dataclass(slots=True)
class MetaGraphBoundRuntimeLane:
    backend: MetaGraphRuntimeLaneBackend
    binding: MetaGraphRuntimeLaneBinding
    _records: list[MetaGraphRuntimeLaneInvokeRecord] = field(
        default_factory=list,
        init=False,
        repr=False,
    )
    _last_response: MetaGraphCommitReceipt | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _last_commit_id: UUID | None = field(default=None, init=False, repr=False)
    _last_head_commit_id: UUID | None = field(default=None, init=False, repr=False)

    @property
    def branch_id(self) -> UUID:
        return self.binding.branch_id

    @property
    def records(self) -> tuple[MetaGraphRuntimeLaneInvokeRecord, ...]:
        return tuple(self._records)

    @property
    def last_response(self) -> MetaGraphCommitReceipt | None:
        return self._last_response

    @property
    def last_commit_id(self) -> UUID | None:
        return self._last_commit_id

    @property
    def last_head_commit_id(self) -> UUID | None:
        return self._last_head_commit_id

    @contextmanager
    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> Iterator[MetaGraphBoundRuntimeLane]:
        provider = _MetaGraphLaneBoundInvocationProvider(
            lane=self,
            commit=bool(commit),
            publish=bool(publish),
        )
        token = set_invocation_provider(provider)
        try:
            yield self
        finally:
            reset_invocation_provider(token)

    async def invoke_constructor(
        self,
        *,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, object],
        commit: bool = True,
        publish: bool = False,
    ) -> MetaGraphCommitReceipt:
        return await self.invoke_constructor_with_binding(
            binding=self.binding,
            orm_class=orm_class,
            function_name=function_name,
            payload=payload,
            commit=commit,
            publish=publish,
        )

    async def invoke_constructor_with_binding(
        self,
        *,
        binding: MetaGraphRuntimeLaneBinding,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, object],
        commit: bool,
        publish: bool,
    ) -> MetaGraphCommitReceipt:
        function_id, response = await self.backend.invoke_constructor(
            lane=binding,
            orm_class=orm_class,
            function_name=function_name,
            payload=payload,
            commit=commit,
            publish=publish,
        )
        self._record(
            call_target=MetaGraphCallTarget.opg_constructor,
            class_fqn=f"{orm_class.__module__}.{orm_class.__name__}",
            function_name=function_name,
            function_id=function_id,
            object_id=None,
            commit=commit,
            publish=publish,
            response=response,
        )
        self._assert_invoke_succeeded(
            response=response,
            label=f"{orm_class.__module__}.{orm_class.__name__}.{function_name}",
        )
        return response

    async def invoke_instance(
        self,
        *,
        orm_model: ORMModel,
        function_name: str,
        payload: Mapping[str, object],
        commit: bool = True,
        publish: bool = False,
    ) -> MetaGraphCommitReceipt:
        return await self.invoke_instance_with_binding(
            binding=self.binding,
            orm_model=orm_model,
            function_name=function_name,
            payload=payload,
            commit=commit,
            publish=publish,
        )

    async def invoke_instance_with_binding(
        self,
        *,
        binding: MetaGraphRuntimeLaneBinding,
        orm_model: ORMModel,
        function_name: str,
        payload: Mapping[str, object],
        commit: bool,
        publish: bool,
    ) -> MetaGraphCommitReceipt:
        function_id, response = await self.backend.invoke_instance(
            lane=binding,
            orm_model=orm_model,
            function_name=function_name,
            payload=payload,
            commit=commit,
            publish=publish,
        )
        object_id = orm_model.id
        self._record(
            call_target=MetaGraphCallTarget.instance,
            class_fqn=f"{type(orm_model).__module__}.{type(orm_model).__name__}",
            function_name=function_name,
            function_id=function_id,
            object_id=object_id if isinstance(object_id, UUID) else None,
            commit=commit,
            publish=publish,
            response=response,
        )
        self._assert_invoke_succeeded(
            response=response,
            label=f"{type(orm_model).__module__}.{type(orm_model).__name__}.{function_name}",
        )
        return response

    def _record(
        self,
        *,
        call_target: MetaGraphCallTarget,
        class_fqn: str,
        function_name: str,
        function_id: UUID,
        object_id: UUID | None,
        commit: bool,
        publish: bool,
        response: MetaGraphCommitReceipt,
    ) -> None:
        if response.domain_branch_id is not None:
            self.binding.branch_id = response.domain_branch_id
        if response.commit_id is not None:
            self._last_commit_id = response.commit_id
        if response.object_instance_graph_commit_id is not None:
            self._last_head_commit_id = response.object_instance_graph_commit_id
        self._last_response = response
        self._records.append(
            MetaGraphRuntimeLaneInvokeRecord(
                call_target=call_target,
                class_fqn=class_fqn,
                function_name=function_name,
                function_id=function_id,
                object_id=object_id,
                commit=commit,
                publish=publish,
                response=response,
            )
        )

    @staticmethod
    def _assert_invoke_succeeded(
        *,
        response: MetaGraphCommitReceipt,
        label: str,
    ) -> None:
        if response.status == "succeeded":
            return
        if response.error:
            raise RuntimeError(f"{label} failed: {response.error}")
        raise RuntimeError(f"{label} failed")


@dataclass(slots=True)
class _MetaGraphLaneBoundInvocationProvider(InvocationProvider):
    lane: MetaGraphBoundRuntimeLane
    commit: bool
    publish: bool

    async def invoke_instance(
        self,
        *,
        orm_model: ORMModel,
        function_name: str,
        payload: Mapping[str, object],
    ) -> object:
        target_projection_hash = _resolve_instance_projection_hash(
            index=self.lane.backend.index,
            active_projection_hash=self.lane.binding.projection_hash,
            orm_model=orm_model,
        )
        response = await self.lane.invoke_instance_with_binding(
            binding=_retarget_lane_binding(
                binding=self.lane.binding,
                projection_hash=target_projection_hash,
            ),
            orm_model=orm_model,
            function_name=function_name,
            payload={str(key): value for key, value in dict(payload).items()},
            commit=self.commit,
            publish=self.publish,
        )
        return cast(object, response.payload)

    async def invoke_constructor(
        self,
        *,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, object],
    ) -> object:
        target_projection_hash = _resolve_constructor_projection_hash(
            index=self.lane.backend.index,
            active_projection_hash=self.lane.binding.projection_hash,
            orm_class=orm_class,
            function_name=function_name,
        )
        response = await self.lane.invoke_constructor_with_binding(
            binding=_retarget_lane_binding(
                binding=self.lane.binding,
                projection_hash=target_projection_hash,
            ),
            orm_class=orm_class,
            function_name=function_name,
            payload={str(key): value for key, value in dict(payload).items()},
            commit=self.commit,
            publish=self.publish,
        )
        return cast(object, response.payload)


def _resolve_projection_hash(
    *,
    context: MetaGraphRuntimeContext,
    projection: str,
) -> str:
    token = str(projection or "").strip()
    if not token:
        raise ValueError("projection is required")
    if token in context.index.opg_by_hash:
        return token
    return context.projection_hash_for_name(token)


def _resolve_function_id_for_class(
    *,
    orm_class: type[ORMModel],
    function_name: str,
) -> UUID:
    return _resolve_function_link_for_class(
        orm_class=orm_class,
        function_name=function_name,
    ).function_config.id


def _resolve_function_link_for_class(
    *,
    orm_class: type[ORMModel],
    function_name: str,
) -> ClassConfigFunctionConfig:
    class_config = orm_class.get_class_config()
    if class_config is None:
        raise RuntimeError(
            "ORM class missing ClassConfig binding: "
            f"{orm_class.__module__}.{orm_class.__name__}"
        )
    for edge in class_config.class_config_function_configs:
        function_config = edge.function_config
        if function_config.name == function_name:
            return edge
    raise RuntimeError(
        "FunctionConfig not found on ClassConfig: "
        f"class={orm_class.__module__}.{orm_class.__name__} "
        f"class_config_id={class_config.id} function_name={function_name!r}"
    )


def _lookup_opgs_for_class(
    *,
    index: MetaGraphRuntimeIndex,
    class_config_id: UUID,
) -> tuple[ObjectProjectionGraph, ...]:
    opgs: list[ObjectProjectionGraph] = []
    for opg in index.opg_by_id.values():
        for node in opg.object_projection_graph_nodes:
            if node.class_config_id == class_config_id:
                opgs.append(opg)
                break
    return tuple(opgs)


def _resolve_constructor_opg(
    *,
    index: MetaGraphRuntimeIndex,
    active_projection_hash: str,
    orm_class: type[ORMModel],
    function_name: str,
) -> ObjectProjectionGraph:
    projection_hash = _resolve_constructor_projection_hash(
        index=index,
        active_projection_hash=active_projection_hash,
        orm_class=orm_class,
        function_name=function_name,
    )
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Resolved constructor projection hash is missing from Meta graph index: "
            f"{projection_hash!r}"
        )
    return opg


def _resolve_constructor_projection_hash(
    *,
    index: MetaGraphRuntimeIndex,
    active_projection_hash: str,
    orm_class: type[ORMModel],
    function_name: str,
) -> str:
    class_config = orm_class.get_class_config()
    if class_config is None:
        raise RuntimeError(
            "ORM class missing ClassConfig binding: "
            f"{orm_class.__module__}.{orm_class.__name__}"
        )

    function_link = _resolve_function_link_for_class(
        orm_class=orm_class,
        function_name=function_name,
    )
    candidates = tuple(
        opg
        for opg in _lookup_opgs_for_class(
            index=index,
            class_config_id=class_config.id,
        )
        if any(
            constructor.function_constructor_id == function_link.id
            for constructor in opg.object_projection_graph_constructors
        )
    )
    if not candidates:
        raise RuntimeError(
            "No ObjectProjectionGraph constructor owns the requested ORM facade call: "
            f"class={orm_class.__module__}.{orm_class.__name__} "
            f"function={function_name!r} class_config_id={class_config.id}"
        )
    if len(candidates) == 1:
        return candidates[0].projection_hash

    candidate_hashes = sorted({opg.projection_hash for opg in candidates})
    raise RuntimeError(
        "Ambiguous ObjectProjectionGraph constructor ownership for ORM facade call: "
        f"class={orm_class.__module__}.{orm_class.__name__} "
        f"function={function_name!r} class_config_id={class_config.id} "
        f"active_projection_hash={active_projection_hash!r} "
        f"candidate_projection_hashes={candidate_hashes}"
    )


def _resolve_instance_projection_hash(
    *,
    index: MetaGraphRuntimeIndex,
    active_projection_hash: str,
    orm_model: ORMModel,
) -> str:
    orm_class = type(orm_model)
    class_config = orm_class.get_class_config()
    if class_config is None:
        raise RuntimeError(
            "ORM class missing ClassConfig binding: "
            f"{orm_class.__module__}.{orm_class.__name__}"
        )

    candidates = _lookup_opgs_for_class(
        index=index,
        class_config_id=class_config.id,
    )
    if not candidates:
        raise RuntimeError(
            "No ObjectProjectionGraph membership found for ORM facade instance call: "
            f"class={orm_class.__module__}.{orm_class.__name__} "
            f"class_config_id={class_config.id}"
        )

    candidate_hashes = sorted({opg.projection_hash for opg in candidates})
    if active_projection_hash in candidate_hashes:
        return active_projection_hash
    if len(candidate_hashes) == 1:
        return candidate_hashes[0]

    raise RuntimeError(
        "Ambiguous ObjectProjectionGraph membership for ORM facade instance call "
        "without projection provenance: "
        f"class={orm_class.__module__}.{orm_class.__name__} "
        f"class_config_id={class_config.id} "
        f"active_projection_hash={active_projection_hash!r} "
        f"candidate_projection_hashes={candidate_hashes}"
    )


def _retarget_lane_binding(
    *,
    binding: MetaGraphRuntimeLaneBinding,
    projection_hash: str,
) -> MetaGraphRuntimeLaneBinding:
    return MetaGraphRuntimeLaneBinding(
        projection_hash=projection_hash,
        branch_id=binding.branch_id,
        actor_id=binding.actor_id,
    )


def _jsonify_payload_mapping(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(
        {str(key): _jsonify_payload(value) for key, value in dict(payload).items()}
    )


def _jsonify_payload(payload: object) -> JsonValue:
    if payload is None or isinstance(payload, (str, int, float, bool)):
        return cast(JsonValue, payload)
    if isinstance(payload, Enum):
        return _jsonify_payload(payload.value)
    if isinstance(payload, UUID):
        return str(payload)
    if isinstance(payload, Path):
        return str(payload)
    if isinstance(payload, (list, tuple, set)):
        sequence = cast(list[object] | tuple[object, ...] | set[object], payload)
        return [_jsonify_payload(value) for value in sequence]
    if isinstance(payload, Mapping):
        mapping = cast(Mapping[object, object], payload)
        return {str(key): _jsonify_payload(value) for key, value in mapping.items()}
    if isinstance(payload, BaseModel):
        dumped = payload.model_dump(mode="json", exclude_none=True)
        return _jsonify_payload(dumped)
    return str(payload)


__all__ = [
    "MetaGraphBoundRuntimeLane",
    "MetaGraphRuntimeLaneBackend",
    "MetaGraphRuntimeLaneBinding",
    "MetaGraphRuntimeLaneInvokeRecord",
    "MetaGraphRuntimeProtocol",
    "bind_meta_graph_runtime_lane",
]
