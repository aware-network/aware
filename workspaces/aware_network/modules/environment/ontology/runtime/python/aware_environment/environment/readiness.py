from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphGetLaneHeadRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphGetLaneHeadResponse,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphResolveProjectionRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.persistence.readiness import (
    OntologyDatabaseArtifactReceipt,
)
from aware_ontology_service_dto.persistence.readiness import (
    OntologyPersistenceEnsureReadyRequest,
)
from aware_ontology_service_dto.persistence.readiness import (
    OntologyPersistenceEnsureReadyResponse,
)
from aware_environment.branching import stable_environment_thread_branch_id
from aware_environment.stable_ids import (
    stable_boot_process_id,
    stable_boot_thread_id,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentReadinessGraphReceipt,
    EnsureReadyRequest,
    EnsureReadyResponse,
    EnvironmentReadinessPersistenceReceipt,
    EnvironmentReadinessReceipt,
)
from aware_types import JsonArray, JsonObject


@dataclass(frozen=True, slots=True)
class EnvironmentReadinessHostState:
    """Host-owned data needed by Environment readiness planning."""

    manifest_path: str
    environment_title: str | None
    ocg_id: UUID | None
    opg_hashes: tuple[str, ...]
    environment_projection_hash: str | None
    environment_object_projection_graph_id: UUID | None
    environment_constructor_function_id: UUID | None
    persistence_backend: str = "noop"
    database_url_ref: str | None = None
    database_connection_ref: str | None = None
    environment_key: str | None = None


@dataclass(frozen=True, slots=True)
class _EnvironmentGraphAuthorityState:
    projection_hash: str
    object_projection_graph_id: UUID
    constructor_function_id: UUID


@dataclass(frozen=True, slots=True)
class _DatabaseReadinessResult:
    error: str | None
    receipt: EnvironmentReadinessPersistenceReceipt


class EnvironmentHostReadinessPort(Protocol):
    async def resolve_environment_readiness_state(
        self,
        *,
        request: EnsureReadyRequest,
    ) -> EnvironmentReadinessHostState: ...


class StructureArtifactReadinessPort(Protocol):
    async def resolve_environment_database_artifacts(
        self,
        *,
        request: EnsureReadyRequest,
        host_state: EnvironmentReadinessHostState,
    ) -> OntologyDatabaseArtifactReceipt: ...


class MetaGraphReadinessPort(Protocol):
    async def resolve_projection(
        self,
        request: MetaGraphResolveProjectionRequest,
    ) -> MetaGraphResolveProjectionResponse: ...

    async def get_lane_head(
        self,
        request: MetaGraphGetLaneHeadRequest,
    ) -> MetaGraphGetLaneHeadResponse: ...

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse: ...


class OntologyPersistenceReadinessPort(Protocol):
    async def ensure_ready(
        self,
        request: OntologyPersistenceEnsureReadyRequest,
    ) -> OntologyPersistenceEnsureReadyResponse: ...


class EnvironmentReadinessService:
    """Environment-owned Environment admission state machine."""

    def __init__(
        self,
        *,
        host: EnvironmentHostReadinessPort,
        meta_graph: MetaGraphReadinessPort,
        structure_artifacts: StructureArtifactReadinessPort | None = None,
        ontology_persistence: OntologyPersistenceReadinessPort | None = None,
    ) -> None:
        self._host = host
        self._meta_graph = meta_graph
        self._structure_artifacts = structure_artifacts
        self._ontology_persistence = ontology_persistence

    async def ensure_ready(
        self,
        *,
        request: EnsureReadyRequest,
        actor_id: UUID,
    ) -> EnsureReadyResponse:
        boot_process_id = stable_boot_process_id(environment_id=request.environment_id)
        boot_thread_id = stable_boot_thread_id(environment_id=request.environment_id)
        boot_branch_id = stable_environment_thread_branch_id(
            environment_id=request.environment_id,
            thread_id=boot_thread_id,
        )
        request = request.model_copy(update={"actor_id": actor_id})

        try:
            host_state = await self._host.resolve_environment_readiness_state(
                request=request,
            )
            validation_error = self._validate_host_state(host_state)
            if validation_error is not None:
                return self._response(
                    request=request,
                    host_state=host_state,
                    boot_process_id=boot_process_id,
                    boot_thread_id=boot_thread_id,
                    boot_branch_id=boot_branch_id,
                    status="failed",
                    error=validation_error,
                )

            db_result = await self._ensure_database_ready_if_required(
                request=request,
                actor_id=actor_id,
                host_state=host_state,
            )
            if db_result.error is not None:
                return self._response(
                    request=request,
                    host_state=host_state,
                    boot_process_id=boot_process_id,
                    boot_thread_id=boot_thread_id,
                    boot_branch_id=boot_branch_id,
                    status="failed",
                    error=db_result.error,
                    persistence_receipt=db_result.receipt,
                    graph_status="not_started",
                )

            graph_authority, graph_authority_error = (
                await self._resolve_graph_authority_state(
                    actor_id=actor_id,
                    host_state=host_state,
                )
            )
            if graph_authority_error is not None or graph_authority is None:
                return self._response(
                    request=request,
                    host_state=host_state,
                    boot_process_id=boot_process_id,
                    boot_thread_id=boot_thread_id,
                    boot_branch_id=boot_branch_id,
                    status="failed",
                    error=(
                        graph_authority_error
                        or "Environment graph authority resolution failed."
                    ),
                    persistence_receipt=db_result.receipt,
                    graph_status="failed",
                )

            head = await self._read_lane_head(
                actor_id=actor_id,
                boot_branch_id=boot_branch_id,
                projection_hash=graph_authority.projection_hash,
            )
            if head.status == "failed":
                return self._response(
                    request=request,
                    host_state=host_state,
                    boot_process_id=boot_process_id,
                    boot_thread_id=boot_thread_id,
                    boot_branch_id=boot_branch_id,
                    status="failed",
                    error=head.error or "Failed to read Environment lane head.",
                    persistence_receipt=db_result.receipt,
                    graph_status="failed",
                    lane_head=head,
                    graph_authority=graph_authority,
                )
            if _lane_head_has_commit(head):
                return self._response(
                    request=request,
                    host_state=host_state,
                    boot_process_id=boot_process_id,
                    boot_thread_id=boot_thread_id,
                    boot_branch_id=boot_branch_id,
                    status="ready",
                    persistence_receipt=db_result.receipt,
                    graph_status="ready",
                    lane_head=head,
                    graph_authority=graph_authority,
                )

            invoke_response = await self._meta_graph.invoke_function(
                self._genesis_request(
                    request=request,
                    actor_id=actor_id,
                    host_state=host_state,
                    boot_process_id=boot_process_id,
                    boot_thread_id=boot_thread_id,
                    boot_branch_id=boot_branch_id,
                    graph_authority=graph_authority,
                )
            )
            if invoke_response.status == "succeeded" and (
                invoke_response.domain_commit_id is not None
                or invoke_response.object_instance_graph_commit_id is not None
            ):
                return self._response(
                    request=request,
                    host_state=host_state,
                    boot_process_id=boot_process_id,
                    boot_thread_id=boot_thread_id,
                    boot_branch_id=boot_branch_id,
                    status="ready",
                    persistence_receipt=db_result.receipt,
                    graph_status="ready",
                    lane_head=head,
                    invoke_response=invoke_response,
                    graph_authority=graph_authority,
                )

            race_head = await self._read_lane_head(
                actor_id=actor_id,
                boot_branch_id=boot_branch_id,
                projection_hash=graph_authority.projection_hash,
            )
            if _lane_head_has_commit(race_head):
                return self._response(
                    request=request,
                    host_state=host_state,
                    boot_process_id=boot_process_id,
                    boot_thread_id=boot_thread_id,
                    boot_branch_id=boot_branch_id,
                    status="ready",
                    persistence_receipt=db_result.receipt,
                    graph_status="ready",
                    lane_head=race_head,
                    invoke_response=invoke_response,
                    graph_authority=graph_authority,
                )

            return self._response(
                request=request,
                host_state=host_state,
                boot_process_id=boot_process_id,
                boot_thread_id=boot_thread_id,
                boot_branch_id=boot_branch_id,
                status="failed",
                error=invoke_response.error or "Environment genesis failed.",
                persistence_receipt=db_result.receipt,
                graph_status="failed",
                lane_head=head,
                invoke_response=invoke_response,
                graph_authority=graph_authority,
            )
        except Exception as exc:
            return EnsureReadyResponse(
                actor_id=request.actor_id or actor_id,
                environment_id=request.environment_id,
                process_id=boot_process_id,
                thread_id=boot_thread_id,
                branch_id=boot_branch_id,
                status="failed",
                error=_exception_message(exc),
                readiness_receipt=EnvironmentReadinessReceipt(
                    status="failed",
                    actor_id=request.actor_id or actor_id,
                    environment_id=request.environment_id,
                    process_id=boot_process_id,
                    thread_id=boot_thread_id,
                    branch_id=boot_branch_id,
                ),
            )

    def _validate_host_state(
        self,
        host_state: EnvironmentReadinessHostState,
    ) -> str | None:
        if host_state.environment_constructor_function_id is None:
            return "Environment OPG constructor not available in hosted config"
        return None

    async def _resolve_graph_authority_state(
        self,
        *,
        actor_id: UUID,
        host_state: EnvironmentReadinessHostState,
    ) -> tuple[_EnvironmentGraphAuthorityState | None, str | None]:
        constructor_function_id = host_state.environment_constructor_function_id
        if constructor_function_id is None:
            return None, "Environment OPG constructor not available in hosted config"
        response = await self._meta_graph.resolve_projection(
            MetaGraphResolveProjectionRequest(
                actor_id=actor_id,
                projection_name="Environment",
            )
        )
        if response.status != "succeeded":
            return (
                None,
                response.error
                or "Environment projection was not resolved by graph authority.",
            )
        projection_hash = (response.projection_hash or "").strip()
        if not projection_hash:
            return None, "Graph authority did not return Environment projection_hash."
        object_projection_graph_id = response.object_projection_graph_id
        if object_projection_graph_id is None:
            return (
                None,
                "Graph authority did not return Environment ObjectProjectionGraph id.",
            )
        return (
            _EnvironmentGraphAuthorityState(
                projection_hash=projection_hash,
                object_projection_graph_id=object_projection_graph_id,
                constructor_function_id=constructor_function_id,
            ),
            None,
        )

    async def _ensure_database_ready_if_required(
        self,
        *,
        request: EnsureReadyRequest,
        actor_id: UUID,
        host_state: EnvironmentReadinessHostState,
    ) -> _DatabaseReadinessResult:
        backend = host_state.persistence_backend.strip().casefold()
        if backend not in {"db", "postgres", "postgresql"}:
            return _DatabaseReadinessResult(
                error=None,
                receipt=EnvironmentReadinessPersistenceReceipt(
                    status="skipped",
                    backend=backend or "noop",
                    database_url_ref=host_state.database_url_ref,
                ),
            )
        if self._structure_artifacts is None:
            return _DatabaseReadinessResult(
                error=(
                    "Environment DB readiness requires a configured Structure "
                    "artifact resolver."
                ),
                receipt=EnvironmentReadinessPersistenceReceipt(
                    status="failed",
                    backend=backend,
                    database_url_ref=host_state.database_url_ref,
                ),
            )
        if self._ontology_persistence is None:
            return _DatabaseReadinessResult(
                error=(
                    "Environment DB readiness requires a configured Ontology "
                    "persistence API route."
                ),
                receipt=EnvironmentReadinessPersistenceReceipt(
                    status="failed",
                    backend=backend,
                    database_url_ref=host_state.database_url_ref,
                ),
            )
        receipt = (
            await self._structure_artifacts.resolve_environment_database_artifacts(
                request=request,
                host_state=host_state,
            )
        )
        response = await self._ontology_persistence.ensure_ready(
            OntologyPersistenceEnsureReadyRequest(
                actor_id=actor_id,
                database_artifact_receipt=receipt,
                database_url_ref=(
                    host_state.database_connection_ref or host_state.database_url_ref
                ),
                boot_policy="migrate",
            )
        )
        readiness_receipt = EnvironmentReadinessPersistenceReceipt(
            status=response.status,
            backend=backend,
            database_url_ref=host_state.database_url_ref,
            environment_config_id=receipt.ontology_package_id,
            ocg_id=response.ocg_id,
            ocg_hash=response.ocg_hash,
            db_schema_hash=response.db_schema_hash,
            db_schema_registry_hash=response.db_schema_registry_hash,
            marker_ocg_hash=response.marker_ocg_hash,
            marker_head_commit_id=response.marker_head_commit_id,
            installed=response.installed,
            migrated=response.migrated,
            sql_root_count=response.sql_root_count,
            step_count=response.step_count,
        )
        if response.status == "succeeded":
            return _DatabaseReadinessResult(error=None, receipt=readiness_receipt)
        return _DatabaseReadinessResult(
            error=response.error or "Ontology DB readiness failed.",
            receipt=readiness_receipt,
        )

    async def _read_lane_head(
        self,
        *,
        actor_id: UUID,
        boot_branch_id: UUID,
        projection_hash: str,
    ) -> MetaGraphGetLaneHeadResponse:
        return await self._meta_graph.get_lane_head(
            MetaGraphGetLaneHeadRequest(
                actor_id=actor_id,
                domain_branch_id=boot_branch_id,
                domain_projection_hash=projection_hash,
            )
        )

    def _genesis_request(
        self,
        *,
        request: EnsureReadyRequest,
        actor_id: UUID,
        host_state: EnvironmentReadinessHostState,
        boot_process_id: UUID,
        boot_thread_id: UUID,
        boot_branch_id: UUID,
        graph_authority: _EnvironmentGraphAuthorityState,
    ) -> MetaGraphInvokeFunctionRequest:
        environment_key = (host_state.environment_key or "").strip() or str(
            request.environment_id
        )
        return MetaGraphInvokeFunctionRequest(
            actor_id=actor_id,
            domain_branch_id=boot_branch_id,
            domain_projection_hash=graph_authority.projection_hash,
            call_target=MetaGraphFunctionCallTarget.opg_constructor,
            object_projection_graph_id=graph_authority.object_projection_graph_id,
            function_id=graph_authority.constructor_function_id,
            args=JsonArray(),
            kwargs=JsonObject(
                {
                    "key": environment_key,
                    "title": host_state.environment_title or "Aware Environment",
                    "description": None,
                }
            ),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        )

    def _response(
        self,
        *,
        request: EnsureReadyRequest,
        host_state: EnvironmentReadinessHostState,
        boot_process_id: UUID,
        boot_thread_id: UUID,
        boot_branch_id: UUID,
        status: str,
        error: str | None = None,
        persistence_receipt: EnvironmentReadinessPersistenceReceipt | None = None,
        graph_status: str = "failed",
        lane_head: MetaGraphGetLaneHeadResponse | None = None,
        invoke_response: MetaGraphInvokeFunctionResponse | None = None,
        graph_authority: _EnvironmentGraphAuthorityState | None = None,
    ) -> EnsureReadyResponse:
        graph_receipt = self._graph_receipt(
            host_state=host_state,
            boot_branch_id=boot_branch_id,
            status=graph_status,
            lane_head=lane_head,
            invoke_response=invoke_response,
            graph_authority=graph_authority,
        )
        projection_hash = _readiness_projection_hash(
            host_state=host_state,
            graph_authority=graph_authority,
        )
        readiness_receipt = EnvironmentReadinessReceipt(
            status=status,
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            environment_title=host_state.environment_title,
            environment_manifest_path=host_state.manifest_path,
            process_id=boot_process_id,
            thread_id=boot_thread_id,
            branch_id=boot_branch_id,
            projection_hash=projection_hash,
            ocg_id=host_state.ocg_id,
            opg_hashes=list(host_state.opg_hashes),
            graph=graph_receipt,
            persistence=(
                persistence_receipt
                or EnvironmentReadinessPersistenceReceipt(
                    status="not_checked",
                    backend=host_state.persistence_backend.strip().casefold() or "noop",
                    database_url_ref=host_state.database_url_ref,
                )
            ),
        )
        return EnsureReadyResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=boot_process_id,
            thread_id=boot_thread_id,
            branch_id=boot_branch_id,
            projection_hash=projection_hash,
            status=status,
            error=error,
            bundle_manifest_path=host_state.manifest_path,
            ocg_id=host_state.ocg_id,
            opg_hashes=list(host_state.opg_hashes),
            readiness_receipt=readiness_receipt,
        )

    def _graph_receipt(
        self,
        *,
        host_state: EnvironmentReadinessHostState,
        boot_branch_id: UUID,
        status: str,
        lane_head: MetaGraphGetLaneHeadResponse | None = None,
        invoke_response: MetaGraphInvokeFunctionResponse | None = None,
        graph_authority: _EnvironmentGraphAuthorityState | None = None,
    ) -> EnvironmentReadinessGraphReceipt:
        graph_hash_post = (
            invoke_response.graph_hash_post
            if invoke_response is not None
            and invoke_response.graph_hash_post is not None
            else (lane_head.graph_hash_post if lane_head is not None else None)
        )
        root_object_id = (
            invoke_response.root_object_id
            if invoke_response is not None
            and invoke_response.root_object_id is not None
            else (lane_head.root_object_id if lane_head is not None else None)
        )
        projection_hash = _readiness_projection_hash(
            host_state=host_state,
            graph_authority=graph_authority,
        )
        object_projection_graph_id = (
            graph_authority.object_projection_graph_id
            if graph_authority is not None
            else host_state.environment_object_projection_graph_id
        )
        constructor_function_id = (
            graph_authority.constructor_function_id
            if graph_authority is not None
            else host_state.environment_constructor_function_id
        )
        return EnvironmentReadinessGraphReceipt(
            status=status,
            lane_head_status=lane_head.status if lane_head is not None else None,
            genesis_status=(
                invoke_response.status if invoke_response is not None else None
            ),
            branch_id=boot_branch_id,
            projection_hash=projection_hash,
            object_projection_graph_id=object_projection_graph_id,
            constructor_function_id=constructor_function_id,
            lane_head_commit_id=(
                lane_head.domain_commit_id if lane_head is not None else None
            ),
            domain_commit_id=(
                invoke_response.domain_commit_id
                if invoke_response is not None
                else None
            ),
            object_instance_graph_commit_id=(
                invoke_response.object_instance_graph_commit_id
                if invoke_response is not None
                else None
            ),
            object_instance_graph_id=(
                lane_head.object_instance_graph_id if lane_head is not None else None
            ),
            root_object_id=root_object_id,
            graph_hash_post=graph_hash_post,
            function_call_id=(
                invoke_response.function_call_id
                if invoke_response is not None
                else None
            ),
            function_call_response_id=(
                invoke_response.function_call_response_id
                if invoke_response is not None
                else None
            ),
        )


def _lane_head_has_commit(response: MetaGraphGetLaneHeadResponse) -> bool:
    return response.status == "succeeded" and response.domain_commit_id is not None


def _readiness_projection_hash(
    *,
    host_state: EnvironmentReadinessHostState,
    graph_authority: _EnvironmentGraphAuthorityState | None,
) -> str | None:
    if graph_authority is not None:
        return graph_authority.projection_hash
    return host_state.environment_projection_hash


def _exception_message(exc: Exception) -> str:
    message = str(exc).strip()
    return message or exc.__class__.__name__


__all__ = [
    "EnvironmentHostReadinessPort",
    "EnvironmentReadinessHostState",
    "EnvironmentReadinessService",
    "MetaGraphReadinessPort",
    "OntologyPersistenceReadinessPort",
    "StructureArtifactReadinessPort",
]
