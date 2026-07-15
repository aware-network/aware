from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.graph.instance.projection_readiness import (
    ProjectionReadinessModes,
    ProjectionReadinessRequirement,
    ProjectionReadinessResult,
    ensure_projection_readiness,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex, reify_oig_root_model
from aware_orm.session.session import Session
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_enums import ServiceOperationStatus
from aware_service_ontology.service.service_operation import ServiceOperation
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)
from aware_service_ontology.stable_ids import stable_service_operation_id
from aware_utils.logging import logger

from ._lane_hydration import (
    hydrate_committed_lane_object,
)
from ...materialization.snapshot_commit import commit_service_operation_snapshot
from ...api_ingress.telemetry import (
    await_with_service_api_trace,
    service_api_trace_phase,
)
from ...api_ingress import (
    ResolvedServiceApiDispatch,
    ResolvedServiceApiDispatchCandidate,
    require_single_service_api_dispatch_candidate,
)


@dataclass(frozen=True, slots=True)
class MaterializedServiceOperationBinding:
    service_operation_id: UUID
    service_operation_config_id: UUID
    service_id: UUID
    api_call_id: UUID | None
    api_endpoint_id: UUID | None
    operation_key: str
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceOperationMaterializationResult:
    resolved_dispatch: ResolvedServiceApiDispatch
    candidate: ResolvedServiceApiDispatchCandidate
    binding: MaterializedServiceOperationBinding
    service_operation: ServiceOperation


@dataclass(frozen=True, slots=True)
class ServiceOperationStatusUpdateResult:
    binding: MaterializedServiceOperationBinding
    service_operation: ServiceOperation


def _resolve_canonical_service_config_projection_hash(
    index: MetaGraphRuntimeIndex,
) -> str:
    candidate_hashes = tuple(
        projection_hash
        for projection_hash, opg in index.opg_by_hash.items()
        if (opg.name or "").strip() == "ServiceConfig"
    )
    if not candidate_hashes:
        raise ValueError("Unknown projection 'ServiceConfig'")

    required_class_names = frozenset(
        {
            "ServiceConfig",
            "ServiceConfigApi",
            "ServiceConfigApiProjection",
            "ServiceOperationConfigApiEndpoint",
            "ServiceOperationConfigApiEndpointFunction",
        }
    )
    matches: list[str] = []
    candidate_descriptors: list[str] = []
    for projection_hash in candidate_hashes:
        opg = index.opg_by_hash[projection_hash]
        class_names = frozenset(
            index.class_configs_by_id[node.class_config_id].name
            for node in (cast(Any, opg).object_projection_graph_nodes or ())
        )
        candidate_descriptors.append(f"{projection_hash}:{sorted(class_names)!r}")
        if required_class_names.issubset(class_names):
            matches.append(projection_hash)

    if len(matches) != 1:
        raise ValueError(
            "Expected one canonical Service-owned projection hash for 'ServiceConfig', "
            f"got matches={matches!r}, candidates={candidate_descriptors!r}"
        )
    return matches[0]


async def materialize_service_operation(
    *,
    runtime: object,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    resolved_dispatch: ResolvedServiceApiDispatch,
    service_id: UUID,
    operation_key: str,
    status: ServiceOperationStatus = ServiceOperationStatus.queued,
    result_info: str | None = None,
    execution_context: JsonObject | None = None,
    service_config_session: Session | None = None,
    hydrate_committed_operation: bool = True,
    commit: bool = True,
    publish: bool = False,
) -> ServiceOperationMaterializationResult:
    _ = runtime
    _ = publish
    trace_fields = {
        "branch_id": str(target_lane.branch_id),
        "projection_hash": target_lane.projection_hash,
        "service_id": str(service_id),
        "operation_key": operation_key,
        "status": status.value,
        "commit": commit,
    }
    with service_api_trace_phase(
        "service_operation.materialize.resolve_candidate",
        **trace_fields,
    ):
        candidate = require_single_service_api_dispatch_candidate(
            resolved_dispatch=resolved_dispatch,
        )
    api_call_id = resolved_dispatch.dispatch_plan.envelope.api_call_id
    service = await await_with_service_api_trace(
        _hydrate_service_lane_root(
            index=index,
            target_lane=target_lane,
            service_id=service_id,
            error_context="ServiceOperation materialization",
        ),
        phase="service_operation.materialize.hydrate_service_root",
        fields=trace_fields,
    )
    await await_with_service_api_trace(
        _ensure_target_lane_projected_for_db_receipt(
            index=index,
            target_lane=target_lane,
            commit=commit,
            receipt_kind="service_operation",
        ),
        phase="service_operation.materialize.ensure_projection_readiness",
        fields=trace_fields,
    )

    if commit:
        committed = await await_with_service_api_trace(
            commit_service_operation_snapshot(
                index=index,
                actor_id=actor_id,
                branch_id=target_lane.branch_id,
                projection_hash=target_lane.projection_hash,
                service=service,
                service_operation_config_id=candidate.service_operation_config_id,
                operation_key=operation_key,
                api_call_id=api_call_id,
                api_endpoint_id=candidate.service_operation_config_api_endpoint_id,
                status=status,
                result_info=result_info,
                execution_context=execution_context,
            ),
            phase="service_operation.materialize.commit_snapshot",
            fields=trace_fields,
        )
        service_operation = committed.service_operation
        commit_id = committed.commit_id
        head_commit_id = committed.head_commit_id
    else:
        with service_api_trace_phase(
            "service_operation.materialize.build_snapshot",
            **trace_fields,
        ):
            service_operation = _build_service_operation_snapshot(
                service_id=service_id,
                service_operation_config_id=candidate.service_operation_config_id,
                operation_key=operation_key,
                api_call_id=api_call_id,
                api_endpoint_id=candidate.service_operation_config_api_endpoint_id,
                status=status,
                result_info=result_info,
                execution_context=execution_context,
            )
        commit_id = None
        head_commit_id = None

    service_operation_id = service_operation.id
    if service_operation_id is None:
        raise RuntimeError(
            "ServiceOperation materialization must produce service_operation.id"
        )

    if commit and not hydrate_committed_operation:
        with service_api_trace_phase(
            "service_operation.materialize.skip_hydrate_materialized_operation",
            **trace_fields,
        ):
            hydrated_service_operation = service_operation
    else:
        hydrated_service_operation = (
            await await_with_service_api_trace(
                _hydrate_materialized_service_operation(
                    index=index,
                    target_lane=target_lane,
                    service_operation_id=service_operation_id,
                    service_id=service_id,
                    service_operation_config_id=candidate.service_operation_config_id,
                    api_call_id=api_call_id,
                    api_endpoint_id=candidate.service_operation_config_api_endpoint_id,
                    service_config_session=service_config_session,
                ),
                phase="service_operation.materialize.hydrate_materialized_operation",
                fields=trace_fields,
            )
            if commit
            else service_operation
        )
    with service_api_trace_phase(
        "service_operation.materialize.build_result",
        **trace_fields,
    ):
        return ServiceOperationMaterializationResult(
            resolved_dispatch=resolved_dispatch,
            candidate=candidate,
            binding=MaterializedServiceOperationBinding(
                service_operation_id=service_operation_id,
                service_operation_config_id=candidate.service_operation_config_id,
                service_id=service_id,
                api_call_id=api_call_id,
                api_endpoint_id=candidate.service_operation_config_api_endpoint_id,
                operation_key=operation_key,
                commit_id=commit_id,
                head_commit_id=head_commit_id,
                branch_id=target_lane.branch_id,
                projection_hash=target_lane.projection_hash,
            ),
            service_operation=hydrated_service_operation,
        )


async def materialize_service_operation_status(
    *,
    runtime: object,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    binding: MaterializedServiceOperationBinding,
    status: ServiceOperationStatus,
    result_info: str | None = None,
    service_config_session: Session | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceOperationStatusUpdateResult:
    _ = runtime
    _ = publish
    await _ensure_target_lane_projected_for_db_receipt(
        index=index,
        target_lane=target_lane,
        commit=commit,
        receipt_kind="service_operation_status",
    )

    current_operation = await _hydrate_materialized_service_operation(
        index=index,
        target_lane=target_lane,
        service_operation_id=binding.service_operation_id,
        service_id=binding.service_id,
        service_operation_config_id=binding.service_operation_config_id,
        api_call_id=binding.api_call_id,
        api_endpoint_id=binding.api_endpoint_id,
        service_config_session=service_config_session,
    )
    if commit:
        service = await _hydrate_service_lane_root(
            index=index,
            target_lane=target_lane,
            service_id=binding.service_id,
            error_context="ServiceOperation status materialization",
        )
        committed = await commit_service_operation_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=target_lane.branch_id,
            projection_hash=target_lane.projection_hash,
            service=service,
            service_operation_config_id=binding.service_operation_config_id,
            operation_key=binding.operation_key,
            api_call_id=binding.api_call_id,
            api_endpoint_id=binding.api_endpoint_id,
            status=status,
            result_info=result_info,
            execution_context=current_operation.execution_context,
        )
        commit_id = committed.commit_id
        head_commit_id = committed.head_commit_id
        hydrated_service_operation = await _hydrate_materialized_service_operation(
            index=index,
            target_lane=target_lane,
            service_operation_id=binding.service_operation_id,
            service_id=binding.service_id,
            service_operation_config_id=binding.service_operation_config_id,
            api_call_id=binding.api_call_id,
            api_endpoint_id=binding.api_endpoint_id,
            service_config_session=service_config_session,
        )
    else:
        current_operation.status = status
        current_operation.result_info = result_info
        commit_id = None
        head_commit_id = None
        hydrated_service_operation = current_operation
    return ServiceOperationStatusUpdateResult(
        binding=MaterializedServiceOperationBinding(
            service_operation_id=binding.service_operation_id,
            service_operation_config_id=binding.service_operation_config_id,
            service_id=binding.service_id,
            api_call_id=binding.api_call_id,
            api_endpoint_id=binding.api_endpoint_id,
            operation_key=binding.operation_key,
            commit_id=commit_id,
            head_commit_id=head_commit_id,
            branch_id=target_lane.branch_id,
            projection_hash=target_lane.projection_hash,
        ),
        service_operation=hydrated_service_operation,
    )


def _build_service_operation_snapshot(
    *,
    service_id: UUID,
    service_operation_config_id: UUID,
    operation_key: str,
    api_call_id: UUID | None,
    api_endpoint_id: UUID | None,
    status: ServiceOperationStatus,
    result_info: str | None,
    execution_context: JsonObject | None,
) -> ServiceOperation:
    normalized_operation_key = (operation_key or "").strip()
    if not normalized_operation_key:
        raise RuntimeError("ServiceOperation materialization requires operation_key")
    return ServiceOperation(
        id=stable_service_operation_id(
            service_id=service_id,
            service_operation_config_id=service_operation_config_id,
            operation_key=normalized_operation_key,
        ),
        service_id=service_id,
        api_call_id=api_call_id,
        api_endpoint_id=api_endpoint_id,
        service_operation_config_id=service_operation_config_id,
        operation_key=normalized_operation_key,
        status=status,
        result_info=result_info,
        execution_context=JsonObject(dict(execution_context or {})),
    )


async def _hydrate_service_lane_root(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    service_id: UUID,
    error_context: str,
) -> Service:
    return await hydrate_committed_lane_object(
        index=index,
        target_lane=target_lane,
        orm_class=Service,
        object_id=service_id,
        error_context=error_context,
    )


async def _ensure_target_lane_projected_for_db_receipt(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    commit: bool,
    receipt_kind: str,
) -> ProjectionReadinessResult | None:
    if not commit:
        return None
    backend = (os.getenv("AWARE_PERSISTENCE_BACKEND") or "").strip().lower()
    if backend != "db":
        return await ensure_projection_readiness(
            index=None,
            requirement=ProjectionReadinessRequirement(
                name=f"{receipt_kind}.read_model_receipt",
                branch_id=target_lane.branch_id,
                projection_hash=target_lane.projection_hash,
                mode=ProjectionReadinessModes.OFF,
            ),
        )

    result = await ensure_projection_readiness(
        index=index,
        requirement=ProjectionReadinessRequirement(
            name=f"{receipt_kind}.read_model_receipt",
            branch_id=target_lane.branch_id,
            projection_hash=target_lane.projection_hash,
            mode=ProjectionReadinessModes.REQUIRED_DB,
        ),
    )
    if result.skipped_reason:
        logger.debug(
            "Skipped Service read-model receipt projection readiness "
            "receipt_kind=%s branch_id=%s projection_hash=%s status=%s reason=%s",
            receipt_kind,
            target_lane.branch_id,
            target_lane.projection_hash,
            result.status,
            result.skipped_reason,
        )
        return result
    if result.commits_applied:
        logger.info(
            "Service read-model receipt projection readiness applied committed lane "
            "receipt_kind=%s branch_id=%s projection_hash=%s commits=%s "
            "head_commit_id=%s",
            receipt_kind,
            target_lane.branch_id,
            target_lane.projection_hash,
            result.commits_applied,
            result.head_commit_id,
        )
    return result


async def _hydrate_materialized_service_operation(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    service_operation_id: UUID,
    service_id: UUID,
    service_operation_config_id: UUID,
    api_call_id: UUID | None,
    api_endpoint_id: UUID | None,
    service_config_session: Session | None = None,
) -> ServiceOperation:
    target_head = await FSCommitStore().head(
        branch_id=target_lane.branch_id,
        projection_hash=target_lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        raise RuntimeError(
            "ServiceOperation materialization requires a committed service lane head "
            "for post-hydration."
        )

    opg = index.opg_by_hash.get(target_lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            "Unknown target projection hash for ServiceOperation post-hydration: "
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

    hydrated_service_operation = reify_oig_root_model(
        index=index,
        opg=opg,
        oig=target_oig,
        model_type=ServiceOperation,
        root_id=service_operation_id,
        branch_id=target_lane.branch_id,
    )
    if hydrated_service_operation is None:
        raise RuntimeError(
            "ServiceOperation post-hydration could not resolve the committed receipt from the "
            "service lane: "
            f"service_operation_id={service_operation_id}"
        )
    if hydrated_service_operation.service_id != service_id:
        raise RuntimeError(
            "ServiceOperation post-hydration resolved mismatched service binding: "
            f"service_operation_id={service_operation_id} expected_service_id={service_id} "
            f"got_service_id={hydrated_service_operation.service_id}"
        )
    if hydrated_service_operation.service_operation_config is None:
        service_operation_config = _session_object(
            service_config_session,
            ServiceOperationConfig,
            service_operation_config_id,
        )
        if service_operation_config is not None:
            hydrated_service_operation.service_operation_config = (
                service_operation_config
            )
        else:
            service_operation_config = await _hydrate_service_config_lane_object(
                index=index,
                reference_lane=target_lane,
                orm_class=ServiceOperationConfig,
                object_id=service_operation_config_id,
                error_context="ServiceOperation post-hydration",
            )
            if service_operation_config is not None:
                hydrated_service_operation.service_operation_config = (
                    service_operation_config
                )
    if hydrated_service_operation.api_endpoint is None and api_endpoint_id is not None:
        api_endpoint = _session_object(
            service_config_session,
            ServiceOperationConfigApiEndpoint,
            api_endpoint_id,
        )
        if api_endpoint is not None:
            hydrated_service_operation.api_endpoint = api_endpoint
        else:
            api_endpoint = await _hydrate_service_config_lane_object(
                index=index,
                reference_lane=target_lane,
                orm_class=ServiceOperationConfigApiEndpoint,
                object_id=api_endpoint_id,
                error_context="ServiceOperation post-hydration",
            )
            if api_endpoint is not None:
                hydrated_service_operation.api_endpoint = api_endpoint
    return hydrated_service_operation


def _session_object(
    session: Session | None,
    orm_class: type[ServiceOperationConfig] | type[ServiceOperationConfigApiEndpoint],
    object_id: UUID,
) -> ServiceOperationConfig | ServiceOperationConfigApiEndpoint | None:
    if session is None:
        return None
    value = session.imap_get(orm_class, object_id)
    if value is None:
        return None
    return cast(ServiceOperationConfig | ServiceOperationConfigApiEndpoint, value)


async def _hydrate_service_config_lane_object(
    *,
    index: MetaGraphRuntimeIndex,
    reference_lane: MaterializationLaneContext,
    orm_class: type[ServiceOperationConfig] | type[ServiceOperationConfigApiEndpoint],
    object_id: UUID,
    error_context: str,
) -> ServiceOperationConfig | ServiceOperationConfigApiEndpoint | None:
    service_config_projection_hash = _resolve_canonical_service_config_projection_hash(
        index
    )
    service_config_head = await FSCommitStore().head(
        branch_id=reference_lane.branch_id,
        projection_hash=service_config_projection_hash,
    )
    if service_config_head is None or not service_config_head.get("commit_id"):
        return None

    service_config_opg = index.opg_by_hash.get(service_config_projection_hash)
    if service_config_opg is None:
        return None

    return await hydrate_committed_lane_object(
        index=index,
        target_lane=MaterializationLaneContext(
            branch_id=reference_lane.branch_id,
            projection_hash=service_config_projection_hash,
        ),
        orm_class=orm_class,
        object_id=object_id,
        error_context=error_context,
    )


__all__ = [
    "MaterializedServiceOperationBinding",
    "ServiceOperationMaterializationResult",
    "ServiceOperationStatusUpdateResult",
    "materialize_service_operation",
    "materialize_service_operation_status",
]
