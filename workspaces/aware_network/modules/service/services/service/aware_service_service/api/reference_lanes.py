from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import inspect
from uuid import UUID

from aware_meta_service.local_sdk import MaterializationLaneContext, MetaSdkLaneStore
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_service_runtime.materialization.service import (
    _hydrate_committed_api_reference_contexts,
    _resolve_committed_api_endpoint_id,
    _resolve_committed_api_graph_projection_id,
)
from aware_service_runtime.runtime_resolution import (
    ServiceProtocolApiReferenceLaneInput,
    service_protocol_api_reference_branch_id,
)
from aware_utils.logging import logger


@dataclass(frozen=True, slots=True)
class ServiceProtocolApiReferenceLaneState:
    state: str
    lane: MaterializationLaneContext
    head_commit_id: UUID | None = None
    error: str | None = None


def api_reference_lane_for_branch_key(
    *,
    lane: MaterializationLaneContext,
    branch_key: str,
) -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=_stable_service_protocol_api_reference_branch_id(branch_key),
        projection_hash=lane.projection_hash,
    )


def api_reference_repair_lane_for_incomplete_state(
    *,
    lane: MaterializationLaneContext,
    reference: ServiceProtocolApiReferenceLaneInput,
    lane_state: ServiceProtocolApiReferenceLaneState,
) -> MaterializationLaneContext:
    head_commit_id = lane_state.head_commit_id
    if head_commit_id is None:
        raise RuntimeError(
            "Service host cannot repair an incomplete service-protocol API reference lane "
            "without a head commit id: "
            f"api={reference.api_name!r} branch_id={lane_state.lane.branch_id}"
        )
    return api_reference_lane_for_branch_key(
        lane=lane,
        branch_key=(
            "service-protocol-api:boot-repair-v1:"
            f"{reference.branch_key}:incomplete-head:{head_commit_id}"
        ),
    )


def remember_service_protocol_api_reference_lane(
    *,
    api_branch_ids_by_name: dict[str, UUID],
    reference: ServiceProtocolApiReferenceLaneInput,
    lane: MaterializationLaneContext,
) -> None:
    existing = api_branch_ids_by_name.get(reference.api_name)
    if existing is not None and existing != lane.branch_id:
        raise RuntimeError(
            "Service host found conflicting service-protocol API refs "
            f"for api={reference.api_name!r}."
        )
    api_branch_ids_by_name[reference.api_name] = lane.branch_id
    api_branch_ids_by_name[reference.api_name.casefold()] = lane.branch_id


async def classify_service_protocol_api_reference_lane(
    *,
    index,
    lane: MaterializationLaneContext,
    reference: ServiceProtocolApiReferenceLaneInput,
    meta_lane_store: MetaSdkLaneStore,
    commit_store: FSCommitStore | None = None,
) -> ServiceProtocolApiReferenceLaneState:
    head = await _materialization_lane_head(lane, meta_lane_store=meta_lane_store)
    head_commit_id = _head_commit_id(head)
    if head_commit_id is None:
        logger.info(
            "Service host classified service-protocol API reference lane as empty "
            "api=%s branch_id=%s",
            reference.api_name,
            lane.branch_id,
        )
        return ServiceProtocolApiReferenceLaneState(state="empty", lane=lane)
    try:
        contains_refs = await api_reference_lane_contains_refs(
            index=index,
            lane=lane,
            api_refs={reference.api_name},
            projection_refs=set(reference.projection_refs),
            endpoint_refs=set(reference.endpoint_refs),
            endpoint_function_refs=set(reference.endpoint_function_refs),
            accessible_graphs=reference.accessible_graphs,
            commit_store=commit_store,
        )
    except RuntimeError as exc:
        logger.warning(
            "Service host classified service-protocol API reference lane as incomplete "
            "after hydration failure api=%s branch_id=%s head_commit_id=%s error=%s",
            reference.api_name,
            lane.branch_id,
            head_commit_id,
            exc,
        )
        return ServiceProtocolApiReferenceLaneState(
            state="incomplete",
            lane=lane,
            head_commit_id=head_commit_id,
            error=str(exc),
        )
    if contains_refs:
        return ServiceProtocolApiReferenceLaneState(
            state="complete",
            lane=lane,
            head_commit_id=head_commit_id,
        )
    return ServiceProtocolApiReferenceLaneState(
        state="incomplete",
        lane=lane,
        head_commit_id=head_commit_id,
        error="committed lane does not contain all expected API/endpoint refs",
    )


def record_service_protocol_api_reference_lane_head(
    *,
    lane_state: ServiceProtocolApiReferenceLaneState,
    reason: str,
) -> None:
    commit_id = lane_state.head_commit_id
    if commit_id is None:
        return
    lane = lane_state.lane
    logger.info(
        "Service host service-protocol API reference lane has committed Meta head "
        "reason=%s api_reference_branch_id=%s projection_hash=%s head_commit_id=%s",
        reason,
        lane.branch_id,
        lane.projection_hash,
        commit_id,
    )


async def api_reference_lane_contains_refs(
    *,
    index,
    lane: MaterializationLaneContext,
    api_refs: set[str],
    projection_refs: set[str],
    endpoint_refs: set[str],
    endpoint_function_refs: set[str],
    accessible_graphs: tuple[ObjectConfigGraph, ...] = (),
    commit_store: FSCommitStore | None = None,
) -> bool:
    if (
        not api_refs
        and not projection_refs
        and not endpoint_refs
        and not endpoint_function_refs
    ):
        return True
    try:
        context = await _hydrate_committed_api_reference_contexts(
            index=index,
            lanes=(lane,),
            accessible_graphs=accessible_graphs,
            commit_store=commit_store,
        )
    except RuntimeError as exc:
        if "requires a committed lane head" in str(exc):
            return False
        raise
    if not all(ref.casefold() in context.apis_by_name for ref in api_refs):
        return False
    for api_ref in api_refs:
        for projection_ref in projection_refs:
            try:
                _resolve_committed_api_graph_projection_id(
                    api_context=context,
                    api_ref=api_ref,
                    projection_ref=projection_ref,
                )
            except RuntimeError as exc:
                if "could not resolve committed Api" in str(exc) or (
                    "could not resolve one committed ApiGraphProjection" in str(exc)
                ):
                    return False
                raise
    for endpoint_ref in endpoint_refs:
        try:
            _resolve_committed_api_endpoint_id(
                api_context=context,
                endpoint_ref=endpoint_ref,
            )
        except RuntimeError as exc:
            if "could not resolve committed" in str(exc):
                return False
            raise
    for endpoint_function_ref in endpoint_function_refs:
        parts = endpoint_function_ref.split(".")
        if len(parts) != 4 or any(not part.strip() for part in parts):
            return False
        endpoint_ref = ".".join(parts[:3])
        function_name = parts[3].strip().casefold()
        try:
            endpoint_id = _resolve_committed_api_endpoint_id(
                api_context=context,
                endpoint_ref=endpoint_ref,
            )
        except RuntimeError as exc:
            if "could not resolve committed" in str(exc):
                return False
            raise
        endpoint = next(
            (
                item
                for item in context.endpoints_by_key.values()
                if item.id == endpoint_id
            ),
            None,
        )
        if endpoint is None:
            return False
        endpoint_functions = endpoint.api_capability_endpoint_functions or ()
        if inspect.isawaitable(endpoint_functions):
            endpoint_functions = await endpoint_functions
        if not any(
            getattr(item, "id", None) is not None
            and str(getattr(item, "name", "") or "").strip().casefold() == function_name
            for item in endpoint_functions
        ):
            return False
    return True


async def _materialization_lane_head(
    lane: MaterializationLaneContext,
    *,
    meta_lane_store: MetaSdkLaneStore,
) -> Mapping[str, object] | None:
    return await meta_lane_store.head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )


def _head_commit_id(head: Mapping[str, object] | None) -> UUID | None:
    if head is None:
        return None
    raw = head.get("commit_id")
    if isinstance(raw, UUID):
        return raw
    if isinstance(raw, str) and raw.strip():
        return UUID(raw)
    return None


def _stable_service_protocol_api_reference_branch_id(branch_key: str) -> UUID:
    return service_protocol_api_reference_branch_id(branch_key)


__all__ = [
    "ServiceProtocolApiReferenceLaneState",
    "api_reference_lane_contains_refs",
    "api_reference_lane_for_branch_key",
    "api_reference_repair_lane_for_incomplete_state",
    "classify_service_protocol_api_reference_lane",
    "record_service_protocol_api_reference_lane_head",
    "remember_service_protocol_api_reference_lane",
]
