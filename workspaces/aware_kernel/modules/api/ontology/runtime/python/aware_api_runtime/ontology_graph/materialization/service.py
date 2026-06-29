from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
import inspect
from time import perf_counter
from typing import Any, TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_ontology.api.api_capability_endpoint_stream_enums import (
    ApiCapabilityEndpointStreamEventKind,
    ApiCapabilityEndpointStreamMode,
)
from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_function import (
    ApiCapabilityEndpointFunction,
)
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_capability_endpoint_response_config import (
    ApiCapabilityEndpointResponseConfig,
)
from aware_api_ontology.api.api_capability_endpoint_stream_config import (
    ApiCapabilityEndpointStreamConfig,
)
from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
    ApiCapabilityEndpointStreamEventConfig,
)
from aware_api_ontology.api.api_graph import ApiGraph
from aware_api_ontology.api.api_graph_capability import ApiGraphCapability
from aware_api_ontology.api.api_graph_capability_function import (
    ApiGraphCapabilityFunction,
)
from aware_api_ontology.api.api_graph_function import ApiGraphFunction
from aware_api_ontology.api.api_graph_projection import ApiGraphProjection
from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_function_id,
    stable_api_capability_endpoint_id,
    stable_api_capability_endpoint_request_config_id,
    stable_api_capability_endpoint_response_config_id,
    stable_api_capability_endpoint_stream_config_id,
    stable_api_capability_endpoint_stream_event_config_id,
    stable_api_capability_id,
    stable_api_graph_capability_function_id,
    stable_api_graph_capability_id,
    stable_api_graph_function_id,
    stable_api_graph_id,
    stable_api_graph_projection_id,
    stable_api_id,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)

from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_utils.logging import logger
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_store import CommitActionDescriptor
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta.runtime.commit.identity_lane import (
    ensure_object_instance_graph_identity_lane_head,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.change_collector import ORMChangeSet

from .plan import build_api_ontology_materialization_plan
from .resolution import (
    _collect_accessible_object_config_graphs,
    _normalize_token,
    _resolve_class_config_id,
    _resolve_object_projection_graph,
    _resolve_public_function_config_id_within_graph,
    _resolve_target_object_config_graph,
)
from .specs import (
    APIOntologyMaterializationSpec,
    decode_api_ontology_materialization_step_payload,
    resolve_api_ontology_materialization_specs,
)


@dataclass(frozen=True, slots=True)
class _ApiGraphSnapshotCommitResult:
    api: Api
    commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


_API_GRAPH_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://api/materialization/api-graph-snapshot-commit/v1",
)
_TApiObject = TypeVar("_TApiObject", bound=BaseORMModel)


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


@contextmanager
def _record_optional_phase(
    phase_timings_s: dict[str, float] | None,
    phase_name: str,
) -> Iterator[None]:
    if phase_timings_s is None:
        yield
        return
    started_at = perf_counter()
    logger.info("API graph materialization phase started: %s", phase_name)
    try:
        yield
    finally:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        logger.info(
            "API graph materialization phase finished: %s (%.6fs)",
            phase_name,
            duration_s,
        )


async def materialize_api_graph_ontology(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    extra_accessible_graphs: Sequence[ObjectConfigGraph] = (),
    phase_timings_s: dict[str, float] | None = None,
) -> MaterializationRunReceipt | None:
    with _record_optional_phase(
        phase_timings_s,
        "api_graph.resolve_api_ontology_materialization_specs",
    ):
        specs = resolve_api_ontology_materialization_specs(
            compile_plan_payloads=compile_plan_payloads
        )
    if not specs:
        return None

    with _record_optional_phase(
        phase_timings_s,
        "api_graph.build_api_ontology_materialization_plan",
    ):
        plan = build_api_ontology_materialization_plan(lane=lane, specs=specs)
    with _record_optional_phase(
        phase_timings_s,
        "api_graph.collect_accessible_object_config_graphs",
    ):
        accessible_graphs = _collect_accessible_object_config_graphs(
            index=index,
            extra_graphs=extra_accessible_graphs,
        )

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        with _record_optional_phase(
            phase_timings_s,
            f"api_graph.runner:{step.step_id}.decode_step_payload",
        ):
            spec = decode_api_ontology_materialization_step_payload(step.payload)

        with _record_optional_phase(
            phase_timings_s,
            f"api_graph.runner:{step.step_id}.commit_api_plan_snapshot",
        ):
            snapshot_commit = await _commit_api_plan_snapshot(
                index=index,
                actor_id=actor_id,
                lane=plan.lane,
                spec=spec,
                accessible_graphs=accessible_graphs,
                phase_timings_s=phase_timings_s,
            )

        return MaterializationStepResult(
            details={
                **_build_step_details(spec=spec),
                "commit_strategy": "api_graph_snapshot_commit",
                "object_count": snapshot_commit.object_count,
                "change_count": snapshot_commit.change_count,
            },
            commit_id=snapshot_commit.commit_id,
            head_commit_id=snapshot_commit.object_instance_graph_commit_id,
        )

    with _record_optional_phase(phase_timings_s, "api_graph.executor.run"):
        return await MaterializationExecutor().run(plan=plan, runner=_runner)


async def _commit_api_plan_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    spec: APIOntologyMaterializationSpec,
    accessible_graphs: Sequence[ObjectConfigGraph],
    phase_timings_s: dict[str, float] | None = None,
) -> _ApiGraphSnapshotCommitResult:
    opg = index.opg_by_hash.get(lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            "API graph snapshot commit missing projection hash: "
            f"{lane.projection_hash}"
        )

    with _record_optional_phase(
        phase_timings_s,
        f"api_graph.snapshot:{spec.api_name}.build_objects",
    ):
        api, objects_by_id = await _build_api_plan_snapshot_objects(
            index=index,
            spec=spec,
            accessible_graphs=accessible_graphs,
            phase_timings_s=phase_timings_s,
        )

    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(lane.branch_id),
    )
    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=lane.projection_hash,
    )
    if opgi is None:
        raise RuntimeError(
            "API graph snapshot commit missing ObjectProjectionGraphIdentity: "
            f"projection_hash={lane.projection_hash}"
        )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    before_oig = build_rooted_object_instance_graph_base(
        key=str(lane.branch_id),
        name=f"OIG_{lane.branch_id.hex[:8]}",
        description="ROOTED_BASE",
        object_config_graph=index.ocg,
        object_projection_graph=opg,
        root_source_object_id=api.id,
        oig_id=domain_oig_id,
    )
    created_ids = frozenset(objects_by_id)
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=created_ids,
        touched_ids=created_ids,
        deleted_ids=frozenset(),
        objects_by_id=dict(objects_by_id),
        scalar_fields_by_id={},
        list_fields_by_id={},
        scalar_baseline={},
        list_baseline={},
        list_added={},
        list_removed={},
    )
    with _record_optional_phase(
        phase_timings_s,
        f"api_graph.snapshot:{spec.api_name}.build_changes",
    ):
        changes = build_object_instance_graph_changes_from_orm_change_set(
            before_oig=before_oig,
            object_instance_graph_identity_id=oigi_id,
            ocg=index.ocg,
            opg=opg,
            change_set=change_set,
            class_configs_by_id=index.class_configs_by_id,
            relationships_by_id=index.relationships_by_id,
            enum_option_resolver=default_meta_enum_option_resolver,
            class_instance_resolver=None,
            union_selections=None,
        )
    if not changes:
        raise RuntimeError(
            "API graph snapshot commit produced no OIG changes: "
            f"api_name={spec.api_name!r}"
        )
    with _record_optional_phase(
        phase_timings_s,
        f"api_graph.snapshot:{spec.api_name}.materialize_post",
    ):
        after_oig = materialize_meta_oig_post(
            before_oig=before_oig,
            changes=changes,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
    commit_id = _api_graph_snapshot_commit_id(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
        spec=spec,
        graph_hash_post=after_oig.hash,
    )
    author_id = resolve_meta_author_id(actor_id)
    with _record_optional_phase(
        phase_timings_s,
        f"api_graph.snapshot:{spec.api_name}.ensure_oigi_lane_head",
    ):
        await ensure_object_instance_graph_identity_lane_head(
            index=index,
            object_instance_graph_id=domain_oig_id,
            domain_projection_hash=lane.projection_hash,
            author_id=author_id,
            label="Api.materialize_compile_plan",
        )
    committer = FSLaneCommitter()
    with _record_optional_phase(
        phase_timings_s,
        f"api_graph.snapshot:{spec.api_name}.commit_to_lane",
    ):
        commit = await committer.commit(
            branch_id=lane.branch_id,
            projection_hash=lane.projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            before_oig=before_oig,
            root_object_id=api.id,
            changes=changes,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=author_id,
            commit_id=commit_id,
            commit_action=CommitActionDescriptor(
                operation_label="Api.materialize_compile_plan",
                call_target="generated_materialization",
                object_id=api.id,
            ),
        )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "API graph snapshot commit did not append a lane commit: "
            f"api_name={spec.api_name!r}"
        )

    return _ApiGraphSnapshotCommitResult(
        api=api,
        commit_id=commit.commit.id,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        object_count=len(objects_by_id),
        change_count=len(changes),
    )


async def _build_api_plan_snapshot_objects(
    *,
    index: MetaGraphRuntimeIndex,
    spec: APIOntologyMaterializationSpec,
    accessible_graphs: Sequence[ObjectConfigGraph],
    phase_timings_s: dict[str, float] | None = None,
) -> tuple[Api, dict[UUID, BaseORMModel]]:
    prefix = f"api_graph.snapshot:{spec.api_name}"
    objects_by_id: dict[UUID, BaseORMModel] = {}
    api_name = spec.api_name.strip()
    if not api_name:
        raise RuntimeError(
            "API graph snapshot materialization requires non-empty api_name"
        )
    api = _remember_api_object(
        objects_by_id,
        Api(
            id=stable_api_id(name=api_name),
            name=api_name,
            description=spec.plan.api.description,
        ),
    )

    capability_by_name: dict[str, ApiCapability] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_capabilities"):
        for row in spec.plan.capabilities:
            capability = _remember_api_object(
                objects_by_id,
                ApiCapability(
                    id=stable_api_capability_id(api_id=api.id, name=row.name),
                    api_id=api.id,
                    name=row.name,
                    description=row.description,
                ),
            )
            _append_unique(api.api_capabilities, capability)
            capability_by_name[row.name] = capability

    with _record_optional_phase(phase_timings_s, f"{prefix}.index_endpoint_rows"):
        request_row_by_endpoint: dict[tuple[str, str], Any] = {
            (row.capability_name, row.endpoint_name): row
            for row in spec.plan.capability_endpoint_request_configs
        }
        response_row_by_endpoint: dict[tuple[str, str], Any] = {
            (row.capability_name, row.endpoint_name): row
            for row in spec.plan.capability_endpoint_response_configs
        }
        stream_row_by_endpoint: dict[tuple[str, str], Any] = {
            (row.capability_name, row.endpoint_name): row
            for row in spec.plan.capability_endpoint_stream_configs
        }
        stream_event_rows_by_endpoint: dict[tuple[str, str], list[Any]] = {}
        for row in spec.plan.capability_endpoint_stream_event_configs:
            stream_event_rows_by_endpoint.setdefault(
                (row.capability_name, row.endpoint_name),
                [],
            ).append(row)

    endpoint_by_key: dict[tuple[str, str], ApiCapabilityEndpoint] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_endpoints"):
        for row in spec.plan.capability_endpoints:
            endpoint_key = (row.capability_name, row.name)
            endpoint_prefix = f"{prefix}.endpoint:{row.capability_name}.{row.name}"
            request_row = request_row_by_endpoint.get(endpoint_key)
            if request_row is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: endpoint is missing request config "
                    + f"(capability={row.capability_name!r}, endpoint={row.name!r})"
                )

            capability = capability_by_name.get(row.capability_name)
            if capability is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: endpoint references unknown capability "
                    + f"(capability={row.capability_name!r}, endpoint={row.name!r})"
                )

            with _record_optional_phase(
                phase_timings_s,
                f"{endpoint_prefix}.resolve_request_class_config_id",
            ):
                request_class_config_id = _resolve_class_config_id(
                    index=index,
                    accessible_graphs=accessible_graphs,
                    class_ref=request_row.class_ref,
                    class_config_id=request_row.class_config_id,
                )
            endpoint = _remember_api_object(
                objects_by_id,
                ApiCapabilityEndpoint(
                    id=stable_api_capability_endpoint_id(
                        api_capability_id=capability.id,
                        name=row.name,
                    ),
                    api_capability_id=capability.id,
                    name=row.name,
                    description=row.description,
                ),
            )
            request_config = _remember_api_object(
                objects_by_id,
                ApiCapabilityEndpointRequestConfig(
                    id=stable_api_capability_endpoint_request_config_id(
                        api_capability_endpoint_id=endpoint.id,
                        class_config_id=request_class_config_id,
                    ),
                    api_capability_endpoint_id=endpoint.id,
                    class_config_id=request_class_config_id,
                    description=request_row.description,
                ),
            )
            endpoint.request_config = request_config
            _append_unique(capability.api_capability_endpoints, endpoint)

            response_row = response_row_by_endpoint.get(endpoint_key)
            if response_row is not None:
                with _record_optional_phase(
                    phase_timings_s,
                    f"{endpoint_prefix}.resolve_response_class_config_id",
                ):
                    response_class_config_id = _resolve_class_config_id(
                        index=index,
                        accessible_graphs=accessible_graphs,
                        class_ref=response_row.class_ref,
                        class_config_id=response_row.class_config_id,
                    )
                response_config = _remember_api_object(
                    objects_by_id,
                    ApiCapabilityEndpointResponseConfig(
                        id=stable_api_capability_endpoint_response_config_id(
                            api_capability_endpoint_request_config_id=request_config.id,
                            class_config_id=response_class_config_id,
                        ),
                        api_capability_endpoint_request_config_id=request_config.id,
                        class_config_id=response_class_config_id,
                        description=response_row.description,
                    ),
                )
                request_config.response_config = response_config

            stream_row = stream_row_by_endpoint.get(endpoint_key)
            if stream_row is not None:
                stream_mode = _resolve_stream_mode(stream_row.stream_mode)
                stream_config = _remember_api_object(
                    objects_by_id,
                    ApiCapabilityEndpointStreamConfig(
                        id=stable_api_capability_endpoint_stream_config_id(
                            api_capability_endpoint_request_config_id=request_config.id,
                            stream_mode=stream_mode.value,
                        ),
                        api_capability_endpoint_request_config_id=request_config.id,
                        stream_mode=stream_mode,
                        description=stream_row.description,
                    ),
                )
                request_config.stream_config = stream_config
                for event_row in stream_event_rows_by_endpoint.get(endpoint_key, ()):
                    with _record_optional_phase(
                        phase_timings_s,
                        f"{endpoint_prefix}.resolve_event_class_config_id",
                    ):
                        event_class_config_id = _resolve_class_config_id(
                            index=index,
                            accessible_graphs=accessible_graphs,
                            class_ref=event_row.class_ref,
                            class_config_id=event_row.class_config_id,
                        )
                    event_kind = _resolve_stream_event_kind(event_row.kind)
                    event_config = _remember_api_object(
                        objects_by_id,
                        ApiCapabilityEndpointStreamEventConfig(
                            id=stable_api_capability_endpoint_stream_event_config_id(
                                api_capability_endpoint_stream_config_id=stream_config.id,
                                class_config_id=event_class_config_id,
                                kind=event_kind.value,
                            ),
                            api_capability_endpoint_stream_config_id=stream_config.id,
                            kind=event_kind,
                            class_config_id=event_class_config_id,
                            description=event_row.description,
                        ),
                    )
                    _append_unique(
                        stream_config.api_capability_endpoint_stream_event_configs,
                        event_config,
                    )

            endpoint_by_key[endpoint_key] = endpoint

    with _record_optional_phase(phase_timings_s, f"{prefix}.index_graph_rows"):
        graph_function_targets_by_graph_target: dict[str, list[str]] = {}
        for row in spec.plan.graph_functions:
            graph_function_targets_by_graph_target.setdefault(
                row.graph_target,
                [],
            ).append(row.target)

        graph_projection_specs_by_graph_target: dict[str, list[str]] = {}
        for row in spec.plan.graph_projections:
            graph_projection_specs_by_graph_target.setdefault(
                row.graph_target,
                [],
            ).append(row.target)

    target_graph_by_key: dict[str, ObjectConfigGraph] = {}
    api_graph_by_target: dict[str, ApiGraph] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_api_graphs"):
        for row in spec.plan.graphs:
            target_graph = _resolve_target_object_config_graph(
                index=index,
                accessible_graphs=accessible_graphs,
                target=row.target,
                function_targets=tuple(
                    graph_function_targets_by_graph_target.get(row.target, ())
                ),
                projection_specs=tuple(
                    graph_projection_specs_by_graph_target.get(row.target, ())
                ),
            )
            api_graph = _remember_api_object(
                objects_by_id,
                ApiGraph(
                    id=stable_api_graph_id(
                        api_id=api.id,
                        object_config_graph_id=target_graph.id,
                    ),
                    api_id=api.id,
                    object_config_graph_id=target_graph.id,
                    description=row.description,
                ),
            )
            _append_unique(api.api_graphs, api_graph)
            target_graph_by_key[row.target] = target_graph
            api_graph_by_target[row.target] = api_graph

    graph_function_by_key: dict[tuple[str, str], ApiGraphFunction] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_graph_functions"):
        for row in spec.plan.graph_functions:
            api_graph = api_graph_by_target.get(row.graph_target)
            target_graph = target_graph_by_key.get(row.graph_target)
            if api_graph is None or target_graph is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: graph function references unknown graph "
                    + f"(graph_target={row.graph_target!r}, target={row.target!r})"
                )
            class_config_function_config_id = (
                _resolve_public_function_config_id_within_graph(
                    target_graph=target_graph,
                    function_target=row.target,
                )
            )
            graph_function = _remember_api_object(
                objects_by_id,
                ApiGraphFunction(
                    id=stable_api_graph_function_id(
                        api_graph_id=api_graph.id,
                        class_config_function_config_id=class_config_function_config_id,
                    ),
                    api_graph_id=api_graph.id,
                    class_config_function_config_id=class_config_function_config_id,
                    description=getattr(row, "description", None),
                ),
            )
            _append_unique(api_graph.api_graph_functions, graph_function)
            graph_function_by_key[(row.graph_target, row.target)] = graph_function

    graph_projection_by_key: dict[tuple[str, str], ApiGraphProjection] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_graph_projections"):
        for row in spec.plan.graph_projections:
            api_graph = api_graph_by_target.get(row.graph_target)
            target_graph = target_graph_by_key.get(row.graph_target)
            if api_graph is None or target_graph is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: graph projection references unknown graph "
                    + f"(graph_target={row.graph_target!r}, projection_target={row.target!r})"
                )
            object_projection_graph = _resolve_object_projection_graph(
                index=index,
                target_graph=target_graph,
                projection_target=row.target,
                accessible_graphs=accessible_graphs,
            )
            graph_projection = _remember_api_object(
                objects_by_id,
                ApiGraphProjection(
                    id=stable_api_graph_projection_id(
                        api_graph_id=api_graph.id,
                        object_projection_graph_id=object_projection_graph.id,
                    ),
                    api_graph_id=api_graph.id,
                    object_projection_graph_id=object_projection_graph.id,
                    description=row.description,
                ),
            )
            _append_unique(api_graph.api_graph_projections, graph_projection)
            graph_projection_key = (row.graph_target, row.target)
            existing_projection = graph_projection_by_key.get(graph_projection_key)
            if (
                existing_projection is not None
                and existing_projection.id != graph_projection.id
            ):
                raise RuntimeError(
                    "Invalid api ontology materialization plan: duplicate graph projection rows resolved "
                    + "to different API graph projection objects "
                    + f"(graph_target={row.graph_target!r}, projection_target={row.target!r})"
                )
            graph_projection_by_key[graph_projection_key] = graph_projection

    graph_capability_by_key: dict[tuple[str, str], ApiGraphCapability] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_graph_capabilities"):
        for row in spec.plan.graph_capabilities:
            api_graph = api_graph_by_target.get(row.graph_target)
            capability = capability_by_name.get(row.capability_name)
            if api_graph is None or capability is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: graph capability references unknown api rail "
                    + f"(graph_target={row.graph_target!r}, capability={row.capability_name!r})"
                )
            graph_capability = _remember_api_object(
                objects_by_id,
                ApiGraphCapability(
                    id=stable_api_graph_capability_id(
                        api_graph_id=api_graph.id,
                        api_capability_id=capability.id,
                    ),
                    api_graph_id=api_graph.id,
                    api_capability_id=capability.id,
                    api_capability=capability,
                    description=row.description,
                ),
            )
            _append_unique(api_graph.api_graph_capabilities, graph_capability)
            graph_capability_by_key[(row.graph_target, row.capability_name)] = (
                graph_capability
            )

    graph_capability_function_by_key: dict[
        tuple[str, str, str],
        ApiGraphCapabilityFunction,
    ] = {}
    with _record_optional_phase(
        phase_timings_s,
        f"{prefix}.create_graph_capability_functions",
    ):
        for row in spec.plan.graph_capability_functions:
            graph_capability = graph_capability_by_key.get(
                (row.graph_target, row.capability_name)
            )
            graph_function = graph_function_by_key.get((row.graph_target, row.target))
            if graph_capability is None or graph_function is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: graph capability function "
                    + "references unknown graph rail "
                    + f"(graph_target={row.graph_target!r}, capability={row.capability_name!r}, "
                    + f"name={row.name!r}, target={row.target!r})"
                )
            graph_capability_function = _remember_api_object(
                objects_by_id,
                ApiGraphCapabilityFunction(
                    id=stable_api_graph_capability_function_id(
                        api_graph_capability_id=graph_capability.id,
                        api_graph_function_id=graph_function.id,
                        name=row.name,
                    ),
                    api_graph_capability_id=graph_capability.id,
                    name=row.name,
                    api_graph_function_id=graph_function.id,
                    api_graph_function=graph_function,
                    description=getattr(row, "description", None),
                ),
            )
            _append_unique(
                graph_capability.api_graph_capability_functions,
                graph_capability_function,
            )
            graph_capability_function_by_key[
                (row.graph_target, row.capability_name, row.name)
            ] = graph_capability_function

    endpoint_function_by_key: dict[
        tuple[str, str, str, str, str],
        ApiCapabilityEndpointFunction,
    ] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_endpoint_functions"):
        for row in spec.plan.capability_endpoint_functions:
            endpoint = endpoint_by_key.get((row.capability_name, row.endpoint_name))
            graph_capability_function = graph_capability_function_by_key.get(
                (
                    row.graph_target,
                    row.capability_name,
                    row.graph_capability_function_name,
                )
            )
            if endpoint is None or graph_capability_function is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: endpoint function references unknown endpoint or graph "
                    + f"(capability={row.capability_name!r}, endpoint={row.endpoint_name!r}, "
                    + f"graph_target={row.graph_target!r}, graph_function={row.graph_capability_function_name!r})"
                )
            endpoint_function = _remember_api_object(
                objects_by_id,
                ApiCapabilityEndpointFunction(
                    id=stable_api_capability_endpoint_function_id(
                        api_capability_endpoint_id=endpoint.id,
                        api_graph_capability_function_id=graph_capability_function.id,
                        name=row.name,
                    ),
                    api_capability_endpoint_id=endpoint.id,
                    name=row.name,
                    api_graph_capability_function_id=graph_capability_function.id,
                    api_graph_capability_function=graph_capability_function,
                    description=getattr(row, "description", None),
                ),
            )
            _append_unique(
                endpoint.api_capability_endpoint_functions,
                endpoint_function,
            )
            endpoint_function_by_key[
                (
                    row.capability_name,
                    row.endpoint_name,
                    row.name,
                    row.graph_target,
                    row.graph_capability_function_name,
                )
            ] = endpoint_function

    return api, objects_by_id


def _remember_api_object(
    objects_by_id: dict[UUID, BaseORMModel],
    obj: _TApiObject,
) -> _TApiObject:
    if obj.id is None:
        raise RuntimeError(
            "API graph snapshot materialization attempted to stage an object "
            f"without a stable id: {type(obj).__name__}"
        )
    existing = objects_by_id.get(obj.id)
    if existing is not None:
        return cast(_TApiObject, existing)
    objects_by_id[obj.id] = obj
    return obj


def _append_unique(items: list[_TApiObject], obj: _TApiObject) -> None:
    if all(item.id != obj.id for item in items):
        items.append(obj)


def _api_graph_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    spec: APIOntologyMaterializationSpec,
    graph_hash_post: str,
) -> UUID:
    return uuid5(
        _API_GRAPH_SNAPSHOT_COMMIT_NAMESPACE,
        "aware:api_graph_snapshot_commit:"
        + f"{branch_id}:{projection_hash}:{spec.api_name}:{spec.source_path}:{graph_hash_post}",
    )


async def _materialize_api_plan(
    *,
    index: MetaGraphRuntimeIndex,
    spec: APIOntologyMaterializationSpec,
    accessible_graphs: Sequence[ObjectConfigGraph],
    phase_timings_s: dict[str, float] | None = None,
) -> None:
    prefix = f"api_graph.plan:{spec.api_name}"
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_api"):
        api = await Api.create(
            name=spec.api_name, description=spec.plan.api.description
        )

    capability_by_name: dict[str, Any] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_capabilities"):
        for row in spec.plan.capabilities:
            capability = await api.create_capability(
                name=row.name, description=row.description
            )
            capability_by_name[row.name] = capability

    with _record_optional_phase(phase_timings_s, f"{prefix}.index_endpoint_rows"):
        request_row_by_endpoint: dict[tuple[str, str], Any] = {
            (row.capability_name, row.endpoint_name): row
            for row in spec.plan.capability_endpoint_request_configs
        }
        response_row_by_endpoint: dict[tuple[str, str], Any] = {
            (row.capability_name, row.endpoint_name): row
            for row in spec.plan.capability_endpoint_response_configs
        }
        stream_row_by_endpoint: dict[tuple[str, str], Any] = {
            (row.capability_name, row.endpoint_name): row
            for row in spec.plan.capability_endpoint_stream_configs
        }
        stream_event_rows_by_endpoint: dict[tuple[str, str], list[Any]] = {}
        for row in spec.plan.capability_endpoint_stream_event_configs:
            stream_event_rows_by_endpoint.setdefault(
                (row.capability_name, row.endpoint_name), []
            ).append(row)

    endpoint_by_key: dict[tuple[str, str], Any] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_endpoints"):
        for row in spec.plan.capability_endpoints:
            endpoint_key = (row.capability_name, row.name)
            endpoint_prefix = f"{prefix}.endpoint:{row.capability_name}.{row.name}"
            request_row = request_row_by_endpoint.get(endpoint_key)
            if request_row is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: endpoint is missing request config "
                    + f"(capability={row.capability_name!r}, endpoint={row.name!r})"
                )

            capability = capability_by_name.get(row.capability_name)
            if capability is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: endpoint references unknown capability "
                    + f"(capability={row.capability_name!r}, endpoint={row.name!r})"
                )

            with _record_optional_phase(
                phase_timings_s,
                f"{endpoint_prefix}.resolve_request_class_config_id",
            ):
                request_class_config_id = _resolve_class_config_id(
                    index=index,
                    accessible_graphs=accessible_graphs,
                    class_ref=request_row.class_ref,
                    class_config_id=request_row.class_config_id,
                )
            with _record_optional_phase(
                phase_timings_s,
                f"{endpoint_prefix}.create_endpoint",
            ):
                endpoint = await capability.create_endpoint(
                    name=row.name,
                    request_class_config_id=request_class_config_id,
                    description=row.description,
                )
            with _record_optional_phase(
                phase_timings_s,
                f"{endpoint_prefix}.resolve_existing_request_config",
            ):
                request_config = await _resolve_existing_request_config(
                    endpoint=endpoint,
                    request_class_config_id=request_class_config_id,
                    endpoint_name=row.name,
                    description=request_row.description,
                )

            response_row = response_row_by_endpoint.get(endpoint_key)
            if response_row is not None:
                with _record_optional_phase(
                    phase_timings_s,
                    f"{endpoint_prefix}.resolve_response_class_config_id",
                ):
                    response_class_config_id = _resolve_class_config_id(
                        index=index,
                        accessible_graphs=accessible_graphs,
                        class_ref=response_row.class_ref,
                        class_config_id=response_row.class_config_id,
                    )
                with _record_optional_phase(
                    phase_timings_s,
                    f"{endpoint_prefix}.create_response_config",
                ):
                    _ = await request_config.create_response_config(
                        class_config_id=response_class_config_id,
                        description=response_row.description,
                    )

            stream_row = stream_row_by_endpoint.get(endpoint_key)
            if stream_row is not None:
                with _record_optional_phase(
                    phase_timings_s,
                    f"{endpoint_prefix}.create_stream_config",
                ):
                    stream_config = await request_config.create_stream_config(
                        stream_mode=_resolve_stream_mode(stream_row.stream_mode),
                        description=stream_row.description,
                    )
                for event_row in stream_event_rows_by_endpoint.get(endpoint_key, ()):
                    with _record_optional_phase(
                        phase_timings_s,
                        f"{endpoint_prefix}.resolve_event_class_config_id",
                    ):
                        event_class_config_id = _resolve_class_config_id(
                            index=index,
                            accessible_graphs=accessible_graphs,
                            class_ref=event_row.class_ref,
                            class_config_id=event_row.class_config_id,
                        )
                    with _record_optional_phase(
                        phase_timings_s,
                        f"{endpoint_prefix}.create_event_config",
                    ):
                        _ = await stream_config.create_event_config(
                            kind=_resolve_stream_event_kind(event_row.kind),
                            class_config_id=event_class_config_id,
                            description=event_row.description,
                        )

            endpoint_by_key[endpoint_key] = endpoint

    with _record_optional_phase(phase_timings_s, f"{prefix}.index_graph_rows"):
        graph_function_targets_by_graph_target: dict[str, list[str]] = {}
        for row in spec.plan.graph_functions:
            graph_function_targets_by_graph_target.setdefault(
                row.graph_target, []
            ).append(row.target)

        graph_projection_specs_by_graph_target: dict[str, list[str]] = {}
        for row in spec.plan.graph_projections:
            graph_projection_specs_by_graph_target.setdefault(
                row.graph_target, []
            ).append(row.target)

    target_graph_by_key: dict[str, ObjectConfigGraph] = {}
    api_graph_by_target: dict[str, Any] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_api_graphs"):
        for row in spec.plan.graphs:
            target_graph = _resolve_target_object_config_graph(
                index=index,
                accessible_graphs=accessible_graphs,
                target=row.target,
                function_targets=tuple(
                    graph_function_targets_by_graph_target.get(row.target, ())
                ),
                projection_specs=tuple(
                    graph_projection_specs_by_graph_target.get(row.target, ())
                ),
            )
            api_graph = await api.create_api_graph(
                object_config_graph_id=target_graph.id,
                description=row.description,
            )
            target_graph_by_key[row.target] = target_graph
            api_graph_by_target[row.target] = api_graph

    graph_function_by_key: dict[tuple[str, str], Any] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_graph_functions"):
        for row in spec.plan.graph_functions:
            api_graph = api_graph_by_target.get(row.graph_target)
            target_graph = target_graph_by_key.get(row.graph_target)
            if api_graph is None or target_graph is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: graph function references unknown graph "
                    + f"(graph_target={row.graph_target!r}, target={row.target!r})"
                )
            class_config_function_config_id = (
                _resolve_public_function_config_id_within_graph(
                    target_graph=target_graph,
                    function_target=row.target,
                )
            )
            graph_function = await api_graph.create_graph_function(
                class_config_function_config_id=class_config_function_config_id
            )
            graph_function_by_key[(row.graph_target, row.target)] = graph_function

    graph_projection_by_key: dict[tuple[str, str], Any] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_graph_projections"):
        for row in spec.plan.graph_projections:
            api_graph = api_graph_by_target.get(row.graph_target)
            target_graph = target_graph_by_key.get(row.graph_target)
            if api_graph is None or target_graph is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: graph projection references unknown graph "
                    + f"(graph_target={row.graph_target!r}, projection_target={row.target!r})"
                )
            object_projection_graph = _resolve_object_projection_graph(
                index=index,
                target_graph=target_graph,
                projection_target=row.target,
                accessible_graphs=accessible_graphs,
            )
            graph_projection = await api_graph.create_graph_projection(
                object_projection_graph_id=object_projection_graph.id,
                description=row.description,
            )
            graph_projection_key = (row.graph_target, row.target)
            existing_projection = graph_projection_by_key.get(graph_projection_key)
            if (
                existing_projection is not None
                and existing_projection.id != graph_projection.id
            ):
                raise RuntimeError(
                    "Invalid api ontology materialization plan: duplicate graph projection rows resolved "
                    + "to different API graph projection objects "
                    + f"(graph_target={row.graph_target!r}, projection_target={row.target!r})"
                )
            graph_projection_by_key[graph_projection_key] = graph_projection

    graph_capability_by_key: dict[tuple[str, str], Any] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_graph_capabilities"):
        for row in spec.plan.graph_capabilities:
            api_graph = api_graph_by_target.get(row.graph_target)
            capability = capability_by_name.get(row.capability_name)
            if api_graph is None or capability is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: graph capability references unknown api rail "
                    + f"(graph_target={row.graph_target!r}, capability={row.capability_name!r})"
                )
            graph_capability = await api_graph.create_graph_capability(
                api_capability_id=capability.id,
                description=row.description,
            )
            graph_capability_by_key[(row.graph_target, row.capability_name)] = (
                graph_capability
            )

    graph_capability_function_by_key: dict[tuple[str, str, str], Any] = {}
    with _record_optional_phase(
        phase_timings_s,
        f"{prefix}.create_graph_capability_functions",
    ):
        for row in spec.plan.graph_capability_functions:
            graph_capability = graph_capability_by_key.get(
                (row.graph_target, row.capability_name)
            )
            graph_function = graph_function_by_key.get((row.graph_target, row.target))
            if graph_capability is None or graph_function is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: graph capability function "
                    + "references unknown graph rail "
                    + f"(graph_target={row.graph_target!r}, capability={row.capability_name!r}, "
                    + f"name={row.name!r}, target={row.target!r})"
                )
            graph_capability_function = await graph_capability.create_function(
                name=row.name,
                api_graph_function_id=graph_function.id,
            )
            graph_capability_function_by_key[
                (row.graph_target, row.capability_name, row.name)
            ] = graph_capability_function

    endpoint_function_by_key: dict[tuple[str, str, str, str, str], Any] = {}
    with _record_optional_phase(phase_timings_s, f"{prefix}.create_endpoint_functions"):
        for row in spec.plan.capability_endpoint_functions:
            endpoint = endpoint_by_key.get((row.capability_name, row.endpoint_name))
            graph_capability_function = graph_capability_function_by_key.get(
                (
                    row.graph_target,
                    row.capability_name,
                    row.graph_capability_function_name,
                )
            )
            if endpoint is None or graph_capability_function is None:
                raise RuntimeError(
                    "Invalid api ontology materialization plan: endpoint function references unknown endpoint or graph "
                    + f"(capability={row.capability_name!r}, endpoint={row.endpoint_name!r}, "
                    + f"graph_target={row.graph_target!r}, graph_function={row.graph_capability_function_name!r})"
                )
            endpoint_function = await endpoint.create_function(
                name=row.name,
                api_graph_capability_function_id=graph_capability_function.id,
            )
            endpoint_function_by_key[
                (
                    row.capability_name,
                    row.endpoint_name,
                    row.name,
                    row.graph_target,
                    row.graph_capability_function_name,
                )
            ] = endpoint_function


async def _resolve_existing_request_config(
    *,
    endpoint: Any,
    request_class_config_id: UUID,
    endpoint_name: str,
    description: str | None,
) -> Any:
    existing = endpoint.request_config
    if inspect.isawaitable(existing):
        existing = await existing
    if existing is None:
        logger.info(
            "ApiCapabilityEndpoint.create_endpoint returned an endpoint without hydrated request_config; "
            "ensuring request-config through endpoint rail (endpoint=%r)",
            endpoint_name,
        )
        existing = await endpoint.ensure_request_config(
            request_class_config_id=request_class_config_id,
            description=description,
        )
    if existing.class_config_id != request_class_config_id:
        raise RuntimeError(
            "ApiCapabilityEndpoint.create_endpoint returned a mismatched request_config "
            + f"(endpoint={endpoint_name!r}, expected_class_config_id={request_class_config_id}, "
            + f"got_class_config_id={existing.class_config_id})"
        )
    return existing


def _resolve_stream_mode(stream_mode: str) -> ApiCapabilityEndpointStreamMode:
    try:
        return ApiCapabilityEndpointStreamMode((_normalize_token(stream_mode)))
    except ValueError as exc:
        raise RuntimeError(f"Invalid api ontology stream mode {stream_mode!r}") from exc


def _resolve_stream_event_kind(kind: str) -> ApiCapabilityEndpointStreamEventKind:
    try:
        return ApiCapabilityEndpointStreamEventKind((_normalize_token(kind)))
    except ValueError as exc:
        raise RuntimeError(f"Invalid api ontology stream event kind {kind!r}") from exc


def _build_step_details(*, spec: APIOntologyMaterializationSpec) -> dict[str, object]:
    plan = spec.plan
    return {
        "api_name": spec.api_name,
        "source_path": spec.source_path,
        "capability_count": len(plan.capabilities),
        "endpoint_count": len(plan.capability_endpoints),
        "request_config_count": len(plan.capability_endpoint_request_configs),
        "response_config_count": len(plan.capability_endpoint_response_configs),
        "stream_config_count": len(plan.capability_endpoint_stream_configs),
        "stream_event_config_count": len(plan.capability_endpoint_stream_event_configs),
        "endpoint_function_count": len(plan.capability_endpoint_functions),
        "graph_count": len(plan.graphs),
        "graph_function_count": len(plan.graph_functions),
        "graph_projection_count": len(plan.graph_projections),
        "graph_capability_count": len(plan.graph_capabilities),
        "graph_capability_function_count": len(plan.graph_capability_functions),
    }


__all__ = [
    "materialize_api_graph_ontology",
]
