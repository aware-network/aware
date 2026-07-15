from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar, cast
from uuid import UUID

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex, reify_oig_root_model
from aware_orm.models.orm_model import ORMModel

from ...api_ingress.telemetry import (
    await_with_service_api_trace,
    service_api_trace_phase,
)

TModel = TypeVar("TModel", bound=ORMModel)


class ServiceRuntimeLaneBinding(Protocol):
    projection_hash: str


class ServiceBoundRuntimeLane(Protocol):
    binding: ServiceRuntimeLaneBinding

    @property
    def branch_id(self) -> UUID | None: ...

    @property
    def last_commit_id(self) -> UUID | None: ...

    @property
    def last_head_commit_id(self) -> UUID | None: ...

    def activate(self, **kwargs: object) -> Any: ...


@dataclass(frozen=True, slots=True)
class _MetaServiceRuntimeLaneAdapter:
    lane: Any

    @property
    def binding(self) -> ServiceRuntimeLaneBinding:
        return cast(ServiceRuntimeLaneBinding, self.lane.binding)

    @property
    def branch_id(self) -> UUID | None:
        return cast(UUID | None, self.lane.branch_id)

    @property
    def last_commit_id(self) -> UUID | None:
        return cast(UUID | None, self.lane.last_commit_id)

    @property
    def last_head_commit_id(self) -> UUID | None:
        return cast(UUID | None, self.lane.last_head_commit_id)

    def activate(self, **kwargs: object) -> AbstractContextManager[object]:
        return cast(
            AbstractContextManager[object],
            self.lane.activate(
                commit=bool(kwargs.get("commit", True)),
                publish=bool(kwargs.get("publish", False)),
            ),
        )


def bind_service_runtime_lane(
    *,
    runtime: object,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection: str,
    actor_id: UUID | None,
) -> ServiceBoundRuntimeLane:
    meta_bind = getattr(runtime, "bind", None)
    if not callable(meta_bind):
        raise RuntimeError(
            "Service runtime lane binding requires a Meta-native runtime.bind(...); "
            "legacy runtime harness fallback is retired."
        )
    return cast(
        ServiceBoundRuntimeLane,
        _MetaServiceRuntimeLaneAdapter(
            lane=meta_bind(
                projection=projection,
                branch_id=branch_id,
                actor_id=actor_id,
            ),
        ),
    )


def resolve_committed_target_lane(
    *,
    target_lane: MaterializationLaneContext,
    runtime_lane: ServiceBoundRuntimeLane,
) -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=runtime_lane.branch_id or target_lane.branch_id,
        projection_hash=runtime_lane.binding.projection_hash,
    )


async def hydrate_committed_lane_object(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    orm_class: type[TModel],
    object_id: UUID,
    error_context: str,
) -> TModel:
    trace_fields = {
        "branch_id": str(target_lane.branch_id),
        "projection_hash": target_lane.projection_hash,
        "orm_class": orm_class.__name__,
        "object_id": str(object_id),
        "error_context": error_context,
    }
    target_head = await await_with_service_api_trace(
        FSCommitStore().head(
            branch_id=target_lane.branch_id,
            projection_hash=target_lane.projection_hash,
        ),
        phase="service_lane_hydration.head_lookup",
        fields=trace_fields,
    )
    if target_head is None or not target_head.get("commit_id"):
        raise RuntimeError(
            f"{error_context} requires a committed lane head for post-hydration."
        )

    with service_api_trace_phase(
        "service_lane_hydration.resolve_projection",
        **trace_fields,
    ):
        opg = index.opg_by_hash.get(target_lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} could not resolve projection hash {target_lane.projection_hash!r}."
        )

    target_oig, _ = await await_with_service_api_trace(
        CachedLaneMaterializer().get(
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
        ),
        phase="service_lane_hydration.materializer_get",
        fields=trace_fields,
    )

    with service_api_trace_phase("service_lane_hydration.reify_root", **trace_fields):
        hydrated = reify_oig_root_model(
            index=index,
            opg=opg,
            oig=target_oig,
            model_type=orm_class,
            root_id=object_id,
            branch_id=target_lane.branch_id,
        )
    if hydrated is None:
        raise RuntimeError(
            f"{error_context} could not resolve committed object {orm_class.__name__}({object_id})."
        )
    return hydrated


__all__ = [
    "ServiceBoundRuntimeLane",
    "bind_service_runtime_lane",
    "hydrate_committed_lane_object",
    "resolve_committed_target_lane",
]
