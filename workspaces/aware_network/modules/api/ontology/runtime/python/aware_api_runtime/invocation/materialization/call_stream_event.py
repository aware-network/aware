from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Awaitable, ContextManager, Mapping, Protocol
from uuid import UUID

from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_call_stream_event import ApiCallStreamEvent
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
    ApiCapabilityEndpointStreamEventConfig,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex, reify_oig_root_model
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_orm.registry import ORMModelRegistry

from .context import scoped_api_call_stream_event_materialization_input
from .pydantic_class_config_closure import pydantic_class_configs_by_id_for_ref


class _MetaRuntimeLaneProtocol(Protocol):
    @property
    def last_commit_id(self) -> UUID | None: ...

    @property
    def last_head_commit_id(self) -> UUID | None: ...

    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> ContextManager[object]: ...


class _RuntimeProtocol(Protocol):
    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> _MetaRuntimeLaneProtocol | Awaitable[_MetaRuntimeLaneProtocol]: ...


@dataclass(frozen=True, slots=True)
class MaterializedApiCallStreamEventBinding:
    api_call_stream_event_id: UUID
    api_call_id: UUID
    sequence: int
    api_capability_endpoint_stream_event_config_id: UUID
    event_model_id: UUID
    event_class_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ApiCallStreamEventMaterializationResult:
    binding: MaterializedApiCallStreamEventBinding
    api_call: ApiCall
    api_call_stream_event: ApiCallStreamEvent
    last_commit_id: UUID | None
    last_head_commit_id: UUID | None


async def materialize_api_call_stream_event(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    api_call_id: UUID,
    sequence: int,
    api_capability_endpoint_stream_event_config_id: UUID,
    api_source_lane: MaterializationLaneContext | None = None,
    api_call_hint: ApiCall | None = None,
    event_values: Mapping[str, object] | None = None,
    event_class_config: ClassConfig | None = None,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ApiCallStreamEventMaterializationResult:
    """Materialize one API-owned typed stream-event receipt under an ApiCall."""

    hydrated_api_call = api_call_hint
    if hydrated_api_call is not None and hydrated_api_call.id != api_call_id:
        raise RuntimeError(
            "ApiCallStreamEvent materialization received mismatched ApiCall hint: "
            f"api_call_id={api_call_id} hint_api_call_id={hydrated_api_call.id}"
        )
    if hydrated_api_call is None:
        hydrated_api_call = await _hydrate_materialized_api_call(
            index=index,
            target_lane=target_lane,
            api_call_id=api_call_id,
        )

    endpoint, stream_event_config, resolved_event_class_config = (
        await _resolve_committed_api_call_stream_event_contract(
            index=index,
            target_lane=target_lane,
            api_source_lane=api_source_lane or target_lane,
            api_call=hydrated_api_call,
            api_capability_endpoint_stream_event_config_id=(
                api_capability_endpoint_stream_event_config_id
            ),
            event_class_config_hint=event_class_config,
        )
    )
    runtime_lane = await _resolve_runtime_lane(
        runtime=runtime,
        lane=target_lane,
        actor_id=actor_id,
    )
    with runtime_lane.activate(commit=commit, publish=publish):
        with scoped_api_call_stream_event_materialization_input(
            event_values=event_values,
            event_class_config=resolved_event_class_config,
            event_class_configs_by_id=_event_class_configs_by_id_for_materialization(
                index=index,
                event_class_config=resolved_event_class_config,
            ),
            api_call=hydrated_api_call,
            api_capability_endpoint=endpoint,
            stream_event_config=stream_event_config,
        ):
            api_call_stream_event = await hydrated_api_call.record_stream_event(
                sequence=sequence,
                api_capability_endpoint_stream_event_config_id=(
                    api_capability_endpoint_stream_event_config_id
                ),
                description=description,
            )

    stream_event_id = api_call_stream_event.id
    event_model_id = api_call_stream_event.event_model_id
    event_class_config_id = resolved_event_class_config.id
    if stream_event_id is None:
        raise RuntimeError(
            "ApiCallStreamEvent materialization must produce api_call_stream_event.id"
        )
    if event_model_id is None:
        raise RuntimeError(
            "ApiCallStreamEvent materialization must produce event_model_id"
        )
    if event_class_config_id is None:
        raise RuntimeError(
            "ApiCallStreamEvent materialization requires event ClassConfig id"
        )

    return ApiCallStreamEventMaterializationResult(
        binding=MaterializedApiCallStreamEventBinding(
            api_call_stream_event_id=stream_event_id,
            api_call_id=api_call_id,
            sequence=sequence,
            api_capability_endpoint_stream_event_config_id=api_capability_endpoint_stream_event_config_id,
            event_model_id=event_model_id,
            event_class_config_id=event_class_config_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=target_lane.branch_id,
            projection_hash=target_lane.projection_hash,
        ),
        api_call=hydrated_api_call,
        api_call_stream_event=api_call_stream_event,
        last_commit_id=runtime_lane.last_commit_id,
        last_head_commit_id=runtime_lane.last_head_commit_id,
    )


async def _resolve_runtime_lane(
    *,
    runtime: _RuntimeProtocol,
    lane: MaterializationLaneContext,
    actor_id: UUID | None,
) -> _MetaRuntimeLaneProtocol:
    runtime_lane = runtime.bind(
        projection=lane.projection_hash,
        branch_id=lane.branch_id,
        actor_id=actor_id,
    )
    if inspect.isawaitable(runtime_lane):
        runtime_lane = await runtime_lane
    return runtime_lane


async def _resolve_committed_api_call_stream_event_contract(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    api_source_lane: MaterializationLaneContext,
    api_call: ApiCall,
    api_capability_endpoint_stream_event_config_id: UUID,
    event_class_config_hint: ClassConfig | None,
) -> tuple[
    ApiCapabilityEndpoint,
    ApiCapabilityEndpointStreamEventConfig,
    ClassConfig,
]:
    _ = target_lane
    endpoint = await _hydrate_api_endpoint(
        index=index,
        branch_id=api_source_lane.branch_id,
        api_capability_endpoint_id=api_call.api_capability_endpoint_id,
    )
    if endpoint is None:
        raise RuntimeError(
            "ApiCallStreamEvent materialization requires committed "
            "ApiCapabilityEndpoint in the API lane: "
            f"api_call_id={api_call.id} "
            f"api_capability_endpoint_id={api_call.api_capability_endpoint_id}"
        )

    request_config = endpoint.request_config
    if inspect.isawaitable(request_config):
        request_config = await request_config
    if request_config is None:
        raise RuntimeError(
            "ApiCallStreamEvent materialization requires committed endpoint "
            "request_config: "
            f"api_call_id={api_call.id} endpoint_id={endpoint.id}"
        )
    stream_config = request_config.stream_config
    if inspect.isawaitable(stream_config):
        stream_config = await stream_config
    if stream_config is None or stream_config.id is None:
        raise RuntimeError(
            "ApiCallStreamEvent materialization requires committed endpoint "
            "stream_config: "
            f"api_call_id={api_call.id} endpoint_id={endpoint.id}"
        )

    event_configs = stream_config.api_capability_endpoint_stream_event_configs
    if inspect.isawaitable(event_configs):
        event_configs = await event_configs
    stream_event_config = None
    for candidate in event_configs or ():
        if (
            isinstance(candidate, ApiCapabilityEndpointStreamEventConfig)
            and candidate.id == api_capability_endpoint_stream_event_config_id
        ):
            stream_event_config = candidate
            break
    if stream_event_config is None:
        raise RuntimeError(
            "ApiCallStreamEvent materialization rejected stream event config outside "
            "this call's endpoint stream contract: "
            f"api_call_id={api_call.id} endpoint_id={endpoint.id} "
            "api_capability_endpoint_stream_event_config_id="
            f"{api_capability_endpoint_stream_event_config_id}"
        )

    event_class_config = await _resolve_stream_event_class_config(
        index=index,
        stream_event_config=stream_event_config,
        event_class_config_hint=event_class_config_hint,
    )
    return endpoint, stream_event_config, event_class_config


async def _resolve_stream_event_class_config(
    *,
    index: MetaGraphRuntimeIndex,
    stream_event_config: ApiCapabilityEndpointStreamEventConfig,
    event_class_config_hint: ClassConfig | None,
) -> ClassConfig:
    if event_class_config_hint is not None:
        if event_class_config_hint.id != stream_event_config.class_config_id:
            raise RuntimeError(
                "ApiCallStreamEvent materialization received mismatched event "
                "ClassConfig hint: "
                f"expected_class_config_id={stream_event_config.class_config_id} "
                f"got_class_config_id={event_class_config_hint.id}"
            )
        return event_class_config_hint

    event_class_config = stream_event_config.class_config
    if inspect.isawaitable(event_class_config):
        event_class_config = await event_class_config
    if event_class_config is None:
        event_class_config = index.class_configs_by_id.get(
            stream_event_config.class_config_id
        )
    if event_class_config is None:
        orm_class = ORMModelRegistry.get_class_by_class_config_id(
            stream_event_config.class_config_id
        )
        if orm_class is not None:
            event_class_config = orm_class.get_class_config()
    if event_class_config is None or event_class_config.id is None:
        raise RuntimeError(
            "ApiCallStreamEvent materialization requires stream event "
            "config.class_config to resolve through the API projection portal: "
            "api_capability_endpoint_stream_event_config_id="
            f"{stream_event_config.id} "
            f"class_config_id={stream_event_config.class_config_id}"
        )
    if event_class_config.id != stream_event_config.class_config_id:
        raise RuntimeError(
            "ApiCallStreamEvent materialization resolved mismatched stream event "
            "ClassConfig: "
            f"expected_class_config_id={stream_event_config.class_config_id} "
            f"got_class_config_id={event_class_config.id}"
        )
    return event_class_config


def _event_class_configs_by_id_for_materialization(
    *,
    index: MetaGraphRuntimeIndex,
    event_class_config: ClassConfig | None,
) -> dict[UUID, ClassConfig]:
    event_class_fqn = (
        (event_class_config.class_fqn or "").strip()
        if event_class_config is not None
        else ""
    )
    return pydantic_class_configs_by_id_for_ref(
        base_class_configs_by_id=index.class_configs_by_id,
        root_class_config=event_class_config,
        class_ref=event_class_fqn,
    )


def _resolve_canonical_api_projection_hash(index: MetaGraphRuntimeIndex) -> str:
    candidate_hashes = tuple(
        projection_hash
        for projection_hash, opg in index.opg_by_hash.items()
        if (opg.name or "").strip() == "Api"
    )
    if len(candidate_hashes) != 1:
        raise ValueError(
            f"Expected one canonical projection 'Api', got {candidate_hashes!r}"
        )
    return candidate_hashes[0]


async def _hydrate_api_endpoint(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    api_capability_endpoint_id: UUID,
) -> ApiCapabilityEndpoint | None:
    api_projection_hash = _resolve_canonical_api_projection_hash(index)
    api_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=api_projection_hash,
    )
    if api_head is None or not api_head.get("commit_id"):
        return None

    api_opg = index.opg_by_hash.get(api_projection_hash)
    if api_opg is None:
        return None

    api_oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=api_opg,
        commit_id=UUID(str(api_head["commit_id"])),
        oig_id=(
            UUID(str(api_head["object_instance_graph_id"]))
            if api_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_root_model(
        index=index,
        opg=api_opg,
        oig=api_oig,
        model_type=ApiCapabilityEndpoint,
        root_id=api_capability_endpoint_id,
        branch_id=branch_id,
    )


async def _hydrate_materialized_api_call(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    api_call_id: UUID,
) -> ApiCall:
    target_head = await FSCommitStore().head(
        branch_id=target_lane.branch_id,
        projection_hash=target_lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        raise RuntimeError(
            "ApiCallStreamEvent materialization requires a committed api_call lane "
            "head for post-hydration."
        )

    opg = index.opg_by_hash.get(target_lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            "Unknown target projection hash for ApiCallStreamEvent post-hydration: "
            f"{target_lane.projection_hash}"
        )

    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=target_lane.branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(target_head["commit_id"])),
        oig_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )

    hydrated_api_call = reify_oig_root_model(
        index=index,
        opg=opg,
        oig=target_oig,
        model_type=ApiCall,
        root_id=api_call_id,
        branch_id=target_lane.branch_id,
    )

    if hydrated_api_call is None:
        raise RuntimeError(
            "ApiCallStreamEvent post-hydration could not resolve committed ApiCall "
            "from the api_call lane: "
            f"api_call_id={api_call_id}"
        )
    return hydrated_api_call


__all__ = [
    "ApiCallStreamEventMaterializationResult",
    "MaterializedApiCallStreamEventBinding",
    "materialize_api_call_stream_event",
]
