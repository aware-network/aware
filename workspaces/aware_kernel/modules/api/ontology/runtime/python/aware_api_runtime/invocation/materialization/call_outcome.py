from __future__ import annotations

from dataclasses import dataclass
import inspect
import os
from typing import Awaitable, ContextManager, Mapping, Protocol
from uuid import UUID

from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
from aware_api_ontology.api.api_call_outcome import ApiCallOutcome
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
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
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_orm.registry import ORMModelRegistry
from aware_utils.pydantic.class_config_registry import (
    get_registered_class_config_payload,
    iter_pydantic_package_class_config_payloads,
    register_pydantic_package_class_configs,
)
from aware_utils.logging import logger

from .context import (
    api_receipt_payload_summary,
    scoped_api_call_outcome_materialization_input,
    should_use_compact_api_receipt_payload,
)
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
class MaterializedApiCallOutcomeBinding:
    api_call_outcome_id: UUID
    api_call_id: UUID
    response_model_id: UUID | None
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ApiCallOutcomeMaterializationResult:
    binding: MaterializedApiCallOutcomeBinding
    api_call: ApiCall
    api_call_outcome: ApiCallOutcome
    last_commit_id: UUID | None
    last_head_commit_id: UUID | None


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


async def materialize_api_call_outcome(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    api_call_id: UUID,
    api_source_lane: MaterializationLaneContext | None = None,
    api_call_hint: ApiCall | None = None,
    status: ApiCallOutcomeStatus = ApiCallOutcomeStatus.succeeded,
    error: str | None = None,
    response_payload: Mapping[str, object] | None = None,
    response_class_config: ClassConfig | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ApiCallOutcomeMaterializationResult:
    hydrated_api_call = api_call_hint
    if hydrated_api_call is not None and hydrated_api_call.id != api_call_id:
        raise RuntimeError(
            "ApiCallOutcome materialization received mismatched ApiCall hint: "
            f"api_call_id={api_call_id} hint_api_call_id={hydrated_api_call.id}"
        )
    if hydrated_api_call is None:
        hydrated_api_call = await _hydrate_materialized_api_call(
            index=index,
            target_lane=target_lane,
            api_call_id=api_call_id,
        )
    resolved_response_class_config = response_class_config
    if resolved_response_class_config is None:
        _, resolved_response_class_config = (
            await _resolve_committed_api_call_response_contract(
                index=index,
                target_lane=target_lane,
                api_source_lane=api_source_lane or target_lane,
                api_call_id=api_call_id,
            )
        )
    runtime_lane = await _resolve_runtime_lane(
        runtime=runtime,
        lane=target_lane,
        actor_id=actor_id,
    )
    await _ensure_api_call_lane_projected_for_db_outcome_receipt(
        index=index,
        target_lane=target_lane,
        commit=commit,
        api_call_hint=hydrated_api_call if api_call_hint is not None else None,
    )
    use_compact_receipt_payload = should_use_compact_api_receipt_payload(
        payload=response_payload,
        commit=commit,
    )
    if use_compact_receipt_payload:
        summary = api_receipt_payload_summary(response_payload)
        logger.info(
            "ApiCallOutcome materialization selected compact response payload receipt "
            f"api_call_id={api_call_id} status={status.value!r} "
            f"field_count={summary['field_count']} "
            f"container_field_count={summary['container_field_count']} "
            f"nested_container_count={summary['nested_container_count']}"
        )

    with runtime_lane.activate(commit=commit, publish=publish):
        with scoped_api_call_outcome_materialization_input(
            response_payload=(
                None if use_compact_receipt_payload else response_payload
            ),
            response_class_config=resolved_response_class_config,
            response_class_configs_by_id=(
                None
                if use_compact_receipt_payload
                else _response_class_configs_by_id_for_materialization(
                    index=index,
                    response_class_config=resolved_response_class_config,
                )
            ),
            api_call=hydrated_api_call,
        ):
            api_call_outcome = await hydrated_api_call.create_outcome(
                status=status,
                error=error,
            )

    outcome_id = api_call_outcome.id
    if outcome_id is None:
        raise RuntimeError(
            "ApiCallOutcome materialization must produce api_call_outcome.id"
        )

    return ApiCallOutcomeMaterializationResult(
        binding=MaterializedApiCallOutcomeBinding(
            api_call_outcome_id=outcome_id,
            api_call_id=api_call_id,
            response_model_id=api_call_outcome.response_model_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=target_lane.branch_id,
            projection_hash=target_lane.projection_hash,
        ),
        api_call=hydrated_api_call,
        api_call_outcome=api_call_outcome,
        last_commit_id=runtime_lane.last_commit_id,
        last_head_commit_id=runtime_lane.last_head_commit_id,
    )


async def _ensure_api_call_lane_projected_for_db_outcome_receipt(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    commit: bool,
    api_call_hint: ApiCall | None = None,
) -> ProjectionReadinessResult | None:
    if not commit:
        return None
    backend = (os.getenv("AWARE_PERSISTENCE_BACKEND") or "").strip().lower()
    if backend != "db":
        return await ensure_projection_readiness(
            index=None,
            requirement=ProjectionReadinessRequirement(
                name="api_call_outcome.read_model_receipt",
                branch_id=target_lane.branch_id,
                projection_hash=target_lane.projection_hash,
                mode=ProjectionReadinessModes.OFF,
            ),
        )
    if api_call_hint is not None:
        return await ensure_projection_readiness(
            index=None,
            requirement=ProjectionReadinessRequirement(
                name="api_call_outcome.read_model_receipt",
                branch_id=target_lane.branch_id,
                projection_hash=target_lane.projection_hash,
                mode=ProjectionReadinessModes.OFF,
            ),
        )

    result = await ensure_projection_readiness(
        index=index,
        requirement=ProjectionReadinessRequirement(
            name="api_call_outcome.read_model_receipt",
            branch_id=target_lane.branch_id,
            projection_hash=target_lane.projection_hash,
            mode=ProjectionReadinessModes.REQUIRED_DB,
        ),
    )
    if result.skipped_reason:
        logger.debug(
            "Skipped ApiCallOutcome read-model receipt projection readiness "
            "branch_id=%s projection_hash=%s status=%s reason=%s",
            target_lane.branch_id,
            target_lane.projection_hash,
            result.status,
            result.skipped_reason,
        )
        return result
    if result.commits_applied:
        logger.info(
            "ApiCallOutcome read-model receipt projection readiness applied "
            "committed lane "
            "branch_id=%s projection_hash=%s commits=%s head_commit_id=%s",
            target_lane.branch_id,
            target_lane.projection_hash,
            result.commits_applied,
            result.head_commit_id,
        )
    return result


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


async def _resolve_committed_api_call_response_contract(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    api_source_lane: MaterializationLaneContext,
    api_call_id: UUID,
) -> tuple[ApiCall, ClassConfig | None]:
    hydrated_api_call = await _hydrate_materialized_api_call(
        index=index,
        target_lane=target_lane,
        api_call_id=api_call_id,
    )
    endpoint = await _hydrate_api_endpoint(
        index=index,
        branch_id=api_source_lane.branch_id,
        api_capability_endpoint_id=hydrated_api_call.api_capability_endpoint_id,
    )
    if endpoint is None:
        raise RuntimeError(
            "ApiCallOutcome materialization requires committed ApiCapabilityEndpoint in the api lane: "
            f"api_call_id={api_call_id} api_capability_endpoint_id={hydrated_api_call.api_capability_endpoint_id}"
        )

    request_config = endpoint.request_config
    if inspect.isawaitable(request_config):
        request_config = await request_config
    if request_config is None:
        raise RuntimeError(
            "ApiCallOutcome materialization requires committed ApiCapabilityEndpoint.request_config in the "
            "api_call lane: "
            f"api_call_id={api_call_id}"
        )

    response_config = request_config.response_config
    if inspect.isawaitable(response_config):
        response_config = await response_config
    if response_config is None:
        return hydrated_api_call, None

    response_class_config = response_config.class_config
    if inspect.isawaitable(response_class_config):
        response_class_config = await response_class_config
    registered_response_class_config = (
        _resolve_registered_pydantic_response_class_config(
            response_class_config_id=response_config.class_config_id,
            response_class_config_hint=response_class_config,
        )
    )
    if registered_response_class_config is not None:
        response_class_config = registered_response_class_config
    if response_class_config is None:
        response_class_config = index.class_configs_by_id.get(
            response_config.class_config_id
        )
    if response_class_config is None:
        orm_class = ORMModelRegistry.get_class_by_class_config_id(
            response_config.class_config_id
        )
        if orm_class is not None:
            response_class_config = orm_class.get_class_config()
    registered_response_class_config = (
        _resolve_registered_pydantic_response_class_config(
            response_class_config_id=response_config.class_config_id,
            response_class_config_hint=response_class_config,
        )
    )
    if registered_response_class_config is not None:
        response_class_config = registered_response_class_config
    if response_class_config is None:
        payload = get_registered_class_config_payload(
            class_config_id=str(response_config.class_config_id)
        )
        if payload is not None:
            response_class_config = ClassConfig.model_validate(payload)
    if response_class_config is None or response_class_config.id is None:
        raise RuntimeError(
            "ApiCallOutcome materialization requires response_config.class_config to resolve through the "
            "api_call projection portal before response-model materialization: "
            f"api_call_id={api_call_id} response_class_config_id={response_config.class_config_id}"
        )
    if response_class_config.id != response_config.class_config_id:
        raise RuntimeError(
            "ApiCallOutcome materialization resolved mismatched endpoint response contract: "
            f"api_call_id={api_call_id} expected_response_class_config_id={response_config.class_config_id} "
            f"got_response_class_config_id={response_class_config.id}"
        )
    return hydrated_api_call, response_class_config


def _resolve_registered_pydantic_response_class_config(
    *,
    response_class_config_id: UUID,
    response_class_config_hint: ClassConfig | None,
) -> ClassConfig | None:
    response_class_fqn = (
        (response_class_config_hint.class_fqn or "").strip()
        if response_class_config_hint is not None
        else ""
    )
    package_prefix = response_class_fqn.split(".", 1)[0].strip()
    if package_prefix:
        register_pydantic_package_class_configs(package_prefix=package_prefix)
        for entry in iter_pydantic_package_class_config_payloads(
            package_prefix=package_prefix,
        ):
            response_class_config = ClassConfig.model_validate(entry.payload)
            if response_class_config.id != response_class_config_id:
                continue
            return response_class_config

    payload = get_registered_class_config_payload(
        class_config_id=str(response_class_config_id)
    )
    if payload is None:
        return None
    response_class_config = ClassConfig.model_validate(payload)
    if response_class_config.id != response_class_config_id:
        return None
    return response_class_config


def _response_class_configs_by_id_for_materialization(
    *,
    index: MetaGraphRuntimeIndex,
    response_class_config: ClassConfig | None,
) -> dict[UUID, ClassConfig]:
    response_class_fqn = (
        (response_class_config.class_fqn or "").strip()
        if response_class_config is not None
        else ""
    )
    return pydantic_class_configs_by_id_for_ref(
        base_class_configs_by_id=index.class_configs_by_id,
        root_class_config=response_class_config,
        class_ref=response_class_fqn,
    )


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
            "ApiCallOutcome materialization requires a committed api_call lane head for post-hydration."
        )

    opg = index.opg_by_hash.get(target_lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            "Unknown target projection hash for ApiCallOutcome post-hydration: "
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
            "ApiCallOutcome post-hydration could not resolve the committed ApiCall from the api_call lane: "
            f"api_call_id={api_call_id}"
        )
    return hydrated_api_call


__all__ = [
    "ApiCallOutcomeMaterializationResult",
    "MaterializedApiCallOutcomeBinding",
    "materialize_api_call_outcome",
]
