from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from typing import cast
from uuid import UUID, uuid4

import pytest

from ._environment_runtime_test_paths import (
    ENVIRONMENT_RUNTIME_ROOT,
    REPO_ROOT,
)

_REPO_ROOT = REPO_ROOT
for _path in (
    _REPO_ROOT / "apis" / "meta" / "python" / "aware_meta_service_api",
    _REPO_ROOT / "apis" / "ontology" / "python" / "aware_ontology_service_dto",
    ENVIRONMENT_RUNTIME_ROOT,
    _REPO_ROOT / "modules" / "history" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "history" / "runtime",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_meta_service_dto.graph.instance.function_call_target import (  # noqa: E402
    MetaGraphFunctionCallTarget,
)
from aware_meta_service_dto.graph.instance.function_call import (  # noqa: E402
    MetaGraphGetLaneHeadRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (  # noqa: E402
    MetaGraphGetLaneHeadResponse,
)
from aware_meta_service_dto.graph.instance.function_call import (  # noqa: E402
    MetaGraphInvokeFunctionRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (  # noqa: E402
    MetaGraphInvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call import (  # noqa: E402
    MetaGraphResolveProjectionRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (  # noqa: E402
    MetaGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.persistence.readiness import (  # noqa: E402
    OntologyDatabaseArtifactRef,
    OntologyDatabaseArtifactReceipt,
    OntologyPersistenceEnsureReadyRequest,
    OntologyPersistenceEnsureReadyResponse,
)
from aware_environment.branching import (  # noqa: E402
    stable_environment_thread_branch_id,
)
from aware_environment.environment.readiness import (  # noqa: E402
    EnvironmentReadinessHostState,
    EnvironmentReadinessService,
)
from aware_environment.stable_ids import (  # noqa: E402
    stable_boot_thread_id,
)
from aware_environment_service_dto.environment.environment import (  # noqa: E402
    EnsureReadyRequest,
)


@dataclass(slots=True)
class _FakeHost:
    state: EnvironmentReadinessHostState

    async def resolve_environment_readiness_state(
        self,
        *,
        request: EnsureReadyRequest,
    ) -> EnvironmentReadinessHostState:
        _ = request
        return self.state


class _FakeMetaGraph:
    def __init__(
        self,
        *,
        lane_heads: list[MetaGraphGetLaneHeadResponse],
        invoke_response: MetaGraphInvokeFunctionResponse | None = None,
        resolve_response: MetaGraphResolveProjectionResponse | None = None,
        order: list[str] | None = None,
    ) -> None:
        self.lane_heads = lane_heads
        self.invoke_response = invoke_response
        self.resolve_response = resolve_response
        self.order = order
        self.resolve_requests: list[MetaGraphResolveProjectionRequest] = []
        self.head_requests: list[MetaGraphGetLaneHeadRequest] = []
        self.invoke_requests: list[MetaGraphInvokeFunctionRequest] = []

    async def resolve_projection(
        self,
        request: MetaGraphResolveProjectionRequest,
    ) -> MetaGraphResolveProjectionResponse:
        if self.order is not None:
            self.order.append("resolve")
        self.resolve_requests.append(request)
        if self.resolve_response is not None:
            return self.resolve_response
        return MetaGraphResolveProjectionResponse(
            status="succeeded",
            actor_id=request.actor_id,
            projection_name=request.projection_name,
            projection_hash="environment.projection",
            object_projection_graph_id=uuid4(),
        )

    async def get_lane_head(
        self,
        request: MetaGraphGetLaneHeadRequest,
    ) -> MetaGraphGetLaneHeadResponse:
        if self.order is not None:
            self.order.append("head")
        self.head_requests.append(request)
        if self.lane_heads:
            return self.lane_heads.pop(0)
        return MetaGraphGetLaneHeadResponse(
            status="empty",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
        )

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        if self.order is not None:
            self.order.append("invoke")
        self.invoke_requests.append(request)
        if self.invoke_response is None:
            raise AssertionError("unexpected invoke_function")
        return self.invoke_response


class _FakeStructureArtifacts:
    def __init__(
        self,
        *,
        receipt: OntologyDatabaseArtifactReceipt,
        order: list[str] | None = None,
    ) -> None:
        self.receipt = receipt
        self.order = order
        self.requests: list[EnsureReadyRequest] = []
        self.host_states: list[EnvironmentReadinessHostState] = []

    async def resolve_environment_database_artifacts(
        self,
        *,
        request: EnsureReadyRequest,
        host_state: EnvironmentReadinessHostState,
    ) -> OntologyDatabaseArtifactReceipt:
        if self.order is not None:
            self.order.append("structure")
        self.requests.append(request)
        self.host_states.append(host_state)
        return self.receipt


class _FakeOntologyPersistence:
    def __init__(
        self,
        *,
        response: OntologyPersistenceEnsureReadyResponse,
        order: list[str] | None = None,
    ) -> None:
        self.response = response
        self.order = order
        self.requests: list[OntologyPersistenceEnsureReadyRequest] = []

    async def ensure_ready(
        self,
        request: OntologyPersistenceEnsureReadyRequest,
    ) -> OntologyPersistenceEnsureReadyResponse:
        if self.order is not None:
            self.order.append("persistence")
        self.requests.append(request)
        return self.response


class _TimeoutMetaGraph:
    async def resolve_projection(
        self,
        request: MetaGraphResolveProjectionRequest,
    ) -> MetaGraphResolveProjectionResponse:
        return MetaGraphResolveProjectionResponse(
            status="succeeded",
            actor_id=request.actor_id,
            projection_name=request.projection_name,
            projection_hash="environment.projection",
            object_projection_graph_id=uuid4(),
        )

    async def get_lane_head(
        self,
        request: MetaGraphGetLaneHeadRequest,
    ) -> MetaGraphGetLaneHeadResponse:
        _ = request
        raise asyncio.TimeoutError()

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        _ = request
        raise AssertionError("unexpected invoke_function")


def _host_state(
    *,
    projection_hash: str = "environment.projection",
    opg_id: UUID | None = None,
    function_id: UUID | None = None,
    persistence_backend: str = "noop",
    database_url_ref: str | None = None,
    database_connection_ref: str | None = None,
    environment_key: str | None = None,
) -> EnvironmentReadinessHostState:
    return EnvironmentReadinessHostState(
        manifest_path="/tmp/environment.manifest.json",
        environment_title="Kernel",
        ocg_id=uuid4(),
        opg_hashes=("environment.projection", "process.projection"),
        environment_projection_hash=projection_hash,
        environment_object_projection_graph_id=opg_id or uuid4(),
        environment_constructor_function_id=function_id or uuid4(),
        persistence_backend=persistence_backend,
        database_url_ref=database_url_ref,
        database_connection_ref=database_connection_ref,
        environment_key=environment_key,
    )


def _resolve_response(
    host_state: EnvironmentReadinessHostState,
    *,
    projection_hash: str | None = None,
) -> MetaGraphResolveProjectionResponse:
    return MetaGraphResolveProjectionResponse(
        status="succeeded",
        projection_name="Environment",
        projection_hash=projection_hash or host_state.environment_projection_hash,
        object_projection_graph_id=host_state.environment_object_projection_graph_id,
    )


def _database_artifact_ref(path: str) -> OntologyDatabaseArtifactRef:
    return OntologyDatabaseArtifactRef(path=path, hash="sha256:artifact")


def _database_artifact_receipt(
    *,
    environment_id: UUID,
) -> OntologyDatabaseArtifactReceipt:
    ontology_package_id = uuid4()
    return OntologyDatabaseArtifactReceipt(
        environment_id=environment_id,
        ontology_package_id=ontology_package_id,
        ontology_manifest_ref=_database_artifact_ref(
            "/tmp/environment.manifest.json",
        ),
        ocg_id=uuid4(),
        ocg_hash="sha256:ocg",
        ocg_head_commit_id=uuid4(),
        ocg_lane_branch_id=ontology_package_id,
        ocg_lane_projection_hash="sha256:ocg-projection",
        db_schema_registry_ref=_database_artifact_ref(
            "/tmp/db.schema.registry.json",
        ),
        db_schema_hash="sha256:schema",
        db_backend_target="postgres",
        db_package_kind="ontology",
        sql_roots=["/tmp/sql"],
    )


def _boot_branch_id(environment_id: UUID) -> UUID:
    boot_thread_id = stable_boot_thread_id(environment_id=environment_id)
    return stable_environment_thread_branch_id(
        environment_id=environment_id,
        thread_id=boot_thread_id,
    )


@pytest.mark.asyncio
async def test_environment_readiness_existing_lane_head_skips_constructor() -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    branch_id = _boot_branch_id(environment_id)
    host_state = _host_state()
    lane_commit_id = uuid4()
    meta_graph = _FakeMetaGraph(
        lane_heads=[
            MetaGraphGetLaneHeadResponse(
                status="succeeded",
                actor_id=actor_id,
                domain_branch_id=branch_id,
                domain_projection_hash=cast(
                    str, host_state.environment_projection_hash
                ),
                domain_commit_id=lane_commit_id,
                graph_hash_post="post",
            )
        ],
        resolve_response=_resolve_response(host_state),
    )
    service = EnvironmentReadinessService(
        host=_FakeHost(host_state),
        meta_graph=meta_graph,
    )

    response = await service.ensure_ready(
        request=EnsureReadyRequest(environment_id=environment_id),
        actor_id=actor_id,
    )

    assert response.status == "ready"
    assert response.actor_id == actor_id
    assert response.branch_id == branch_id
    assert response.projection_hash == host_state.environment_projection_hash
    assert response.ocg_id == host_state.ocg_id
    assert response.opg_hashes == list(host_state.opg_hashes)
    receipt = response.readiness_receipt
    assert receipt is not None
    assert receipt.status == "ready"
    assert receipt.actor_id == actor_id
    assert receipt.environment_id == environment_id
    assert receipt.environment_title == "Kernel"
    assert receipt.environment_manifest_path == "/tmp/environment.manifest.json"
    assert receipt.process_id == response.process_id
    assert receipt.thread_id == response.thread_id
    assert receipt.branch_id == branch_id
    assert receipt.projection_hash == host_state.environment_projection_hash
    assert receipt.ocg_id == host_state.ocg_id
    assert receipt.opg_hashes == list(host_state.opg_hashes)
    assert receipt.persistence is not None
    assert receipt.persistence.status == "skipped"
    assert receipt.persistence.backend == "noop"
    assert receipt.graph is not None
    assert receipt.graph.status == "ready"
    assert receipt.graph.lane_head_status == "succeeded"
    assert receipt.graph.genesis_status is None
    assert receipt.graph.branch_id == branch_id
    assert receipt.graph.projection_hash == host_state.environment_projection_hash
    assert receipt.graph.object_projection_graph_id == (
        host_state.environment_object_projection_graph_id
    )
    assert receipt.graph.constructor_function_id == (
        host_state.environment_constructor_function_id
    )
    assert receipt.graph.lane_head_commit_id == lane_commit_id
    assert receipt.graph.graph_hash_post == "post"
    assert len(meta_graph.resolve_requests) == 1
    assert meta_graph.resolve_requests[0].projection_name == "Environment"
    assert len(meta_graph.head_requests) == 1
    assert meta_graph.invoke_requests == []


@pytest.mark.asyncio
async def test_environment_readiness_missing_lane_invokes_meta_constructor() -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    branch_id = _boot_branch_id(environment_id)
    opg_id = uuid4()
    function_id = uuid4()
    host_state = _host_state(opg_id=opg_id, function_id=function_id)
    domain_commit_id = uuid4()
    oig_commit_id = uuid4()
    root_object_id = uuid4()
    meta_graph = _FakeMetaGraph(
        lane_heads=[
            MetaGraphGetLaneHeadResponse(
                status="empty",
                actor_id=actor_id,
                domain_branch_id=branch_id,
                domain_projection_hash=cast(
                    str, host_state.environment_projection_hash
                ),
            )
        ],
        invoke_response=MetaGraphInvokeFunctionResponse(
            status="succeeded",
            actor_id=actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=host_state.environment_projection_hash,
            domain_commit_id=domain_commit_id,
            object_instance_graph_commit_id=oig_commit_id,
            root_object_id=root_object_id,
        ),
        resolve_response=_resolve_response(host_state),
    )
    service = EnvironmentReadinessService(
        host=_FakeHost(host_state),
        meta_graph=meta_graph,
    )

    response = await service.ensure_ready(
        request=EnsureReadyRequest(environment_id=environment_id),
        actor_id=actor_id,
    )

    assert response.status == "ready"
    assert len(meta_graph.invoke_requests) == 1
    invoke_request = meta_graph.invoke_requests[0]
    assert invoke_request.actor_id == actor_id
    assert invoke_request.domain_branch_id == branch_id
    assert invoke_request.domain_projection_hash == "environment.projection"
    assert invoke_request.call_target is MetaGraphFunctionCallTarget.opg_constructor
    assert invoke_request.object_projection_graph_id == opg_id
    assert invoke_request.function_id == function_id
    assert invoke_request.commit is True
    assert invoke_request.publish is False
    assert not hasattr(invoke_request, "orchestration_context")
    assert invoke_request.kwargs["key"] == str(environment_id)
    assert invoke_request.kwargs["title"] == "Kernel"
    assert "environment_experience_profile_id" not in invoke_request.kwargs
    receipt = response.readiness_receipt
    assert receipt is not None
    assert receipt.graph is not None
    assert receipt.graph.status == "ready"
    assert receipt.graph.lane_head_status == "empty"
    assert receipt.graph.genesis_status == "succeeded"
    assert receipt.graph.branch_id == branch_id
    assert receipt.graph.object_projection_graph_id == opg_id
    assert receipt.graph.constructor_function_id == function_id
    assert receipt.graph.domain_commit_id == domain_commit_id
    assert receipt.graph.object_instance_graph_commit_id == oig_commit_id
    assert receipt.graph.root_object_id == root_object_id


@pytest.mark.asyncio
async def test_environment_readiness_uses_authority_projection_hash() -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    branch_id = _boot_branch_id(environment_id)
    opg_id = uuid4()
    function_id = uuid4()
    host_state = _host_state(
        projection_hash="host.generated.environment.projection",
        opg_id=opg_id,
        function_id=function_id,
    )
    authority_projection_hash = "authority.meta.environment.projection"
    meta_graph = _FakeMetaGraph(
        lane_heads=[
            MetaGraphGetLaneHeadResponse(
                status="empty",
                actor_id=actor_id,
                domain_branch_id=branch_id,
                domain_projection_hash=authority_projection_hash,
            )
        ],
        invoke_response=MetaGraphInvokeFunctionResponse(
            status="succeeded",
            actor_id=actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=authority_projection_hash,
            domain_commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
            root_object_id=uuid4(),
        ),
        resolve_response=_resolve_response(
            host_state,
            projection_hash=authority_projection_hash,
        ),
    )
    service = EnvironmentReadinessService(
        host=_FakeHost(host_state),
        meta_graph=meta_graph,
    )

    response = await service.ensure_ready(
        request=EnsureReadyRequest(environment_id=environment_id),
        actor_id=actor_id,
    )

    assert response.status == "ready"
    assert response.projection_hash == authority_projection_hash
    assert meta_graph.resolve_requests[0].projection_name == "Environment"
    assert (
        meta_graph.head_requests[0].domain_projection_hash == authority_projection_hash
    )
    invoke_request = meta_graph.invoke_requests[0]
    assert invoke_request.domain_projection_hash == authority_projection_hash
    assert invoke_request.object_projection_graph_id == opg_id
    assert invoke_request.function_id == function_id
    receipt = response.readiness_receipt
    assert receipt is not None
    assert receipt.projection_hash == authority_projection_hash
    assert receipt.graph is not None
    assert receipt.graph.projection_hash == authority_projection_hash
    assert receipt.graph.object_projection_graph_id == opg_id


@pytest.mark.asyncio
async def test_environment_readiness_uses_host_environment_key_for_genesis() -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    environment_key = "node:kernel:environment_config:primary"
    branch_id = _boot_branch_id(environment_id)
    host_state = _host_state(environment_key=environment_key)
    meta_graph = _FakeMetaGraph(
        lane_heads=[
            MetaGraphGetLaneHeadResponse(
                status="empty",
                actor_id=actor_id,
                domain_branch_id=branch_id,
                domain_projection_hash=cast(
                    str, host_state.environment_projection_hash
                ),
            )
        ],
        invoke_response=MetaGraphInvokeFunctionResponse(
            status="succeeded",
            actor_id=actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=host_state.environment_projection_hash,
            domain_commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
            root_object_id=uuid4(),
        ),
        resolve_response=_resolve_response(host_state),
    )
    service = EnvironmentReadinessService(
        host=_FakeHost(host_state),
        meta_graph=meta_graph,
    )

    response = await service.ensure_ready(
        request=EnsureReadyRequest(environment_id=environment_id),
        actor_id=actor_id,
    )

    assert response.status == "ready"
    assert len(meta_graph.invoke_requests) == 1
    invoke_request = meta_graph.invoke_requests[0]
    assert invoke_request.kwargs["key"] == environment_key


@pytest.mark.asyncio
async def test_environment_readiness_failed_invoke_accepts_race_head() -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    branch_id = _boot_branch_id(environment_id)
    host_state = _host_state()
    meta_graph = _FakeMetaGraph(
        lane_heads=[
            MetaGraphGetLaneHeadResponse(
                status="empty",
                actor_id=actor_id,
                domain_branch_id=branch_id,
                domain_projection_hash=cast(
                    str, host_state.environment_projection_hash
                ),
            ),
            MetaGraphGetLaneHeadResponse(
                status="succeeded",
                actor_id=actor_id,
                domain_branch_id=branch_id,
                domain_projection_hash=cast(
                    str, host_state.environment_projection_hash
                ),
                domain_commit_id=uuid4(),
            ),
        ],
        invoke_response=MetaGraphInvokeFunctionResponse(
            status="failed",
            actor_id=actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=host_state.environment_projection_hash,
            error="duplicate root",
        ),
        resolve_response=_resolve_response(host_state),
    )
    service = EnvironmentReadinessService(
        host=_FakeHost(host_state),
        meta_graph=meta_graph,
    )

    response = await service.ensure_ready(
        request=EnsureReadyRequest(environment_id=environment_id),
        actor_id=actor_id,
    )

    assert response.status == "ready"
    assert len(meta_graph.head_requests) == 2
    assert len(meta_graph.invoke_requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("database_connection_ref", "expected_persistence_database_url_ref"),
    (
        (None, "env:DATABASE_URL"),
        (
            "postgresql://aware:aware_password@localhost:5432/aware_consumer",
            "postgresql://aware:aware_password@localhost:5432/aware_consumer",
        ),
    ),
)
async def test_environment_readiness_db_gate_runs_before_lane_head(
    database_connection_ref: str | None,
    expected_persistence_database_url_ref: str,
) -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    branch_id = _boot_branch_id(environment_id)
    order: list[str] = []
    host_state = _host_state(
        persistence_backend="db",
        database_url_ref="env:DATABASE_URL",
        database_connection_ref=database_connection_ref,
    )
    receipt = _database_artifact_receipt(environment_id=environment_id)
    registry_ref = receipt.db_schema_registry_ref
    assert registry_ref is not None
    structure_artifacts = _FakeStructureArtifacts(receipt=receipt, order=order)
    ontology_persistence = _FakeOntologyPersistence(
        order=order,
        response=OntologyPersistenceEnsureReadyResponse(
            status="succeeded",
            actor_id=actor_id,
            environment_id=environment_id,
            ontology_package_id=receipt.ontology_package_id,
            ocg_id=receipt.ocg_id,
            ocg_hash=receipt.ocg_hash,
            db_schema_hash=receipt.db_schema_hash,
            db_schema_registry_hash=registry_ref.hash,
            marker_ocg_hash=receipt.ocg_hash,
            marker_head_commit_id=uuid4(),
            installed=True,
            migrated=True,
            sql_root_count=len(receipt.sql_roots),
            step_count=2,
        ),
    )
    meta_graph = _FakeMetaGraph(
        order=order,
        lane_heads=[
            MetaGraphGetLaneHeadResponse(
                status="empty",
                actor_id=actor_id,
                domain_branch_id=branch_id,
                domain_projection_hash=cast(
                    str, host_state.environment_projection_hash
                ),
            )
        ],
        invoke_response=MetaGraphInvokeFunctionResponse(
            status="succeeded",
            actor_id=actor_id,
            domain_branch_id=branch_id,
            domain_projection_hash=host_state.environment_projection_hash,
            domain_commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
        ),
        resolve_response=_resolve_response(host_state),
    )
    service = EnvironmentReadinessService(
        host=_FakeHost(host_state),
        meta_graph=meta_graph,
        structure_artifacts=structure_artifacts,
        ontology_persistence=ontology_persistence,
    )

    response = await service.ensure_ready(
        request=EnsureReadyRequest(environment_id=environment_id),
        actor_id=actor_id,
    )

    assert response.status == "ready"
    assert order == ["structure", "persistence", "resolve", "head", "invoke"]
    assert structure_artifacts.requests[0].environment_id == environment_id
    assert structure_artifacts.host_states == [host_state]
    persistence_request = ontology_persistence.requests[0]
    assert persistence_request.actor_id == actor_id
    assert persistence_request.database_artifact_receipt == receipt
    assert persistence_request.database_url_ref == expected_persistence_database_url_ref
    assert persistence_request.boot_policy == "migrate"
    ready_receipt = response.readiness_receipt
    assert ready_receipt is not None
    assert ready_receipt.persistence is not None
    assert ready_receipt.persistence.status == "succeeded"
    assert ready_receipt.persistence.backend == "db"
    assert ready_receipt.persistence.database_url_ref == "env:DATABASE_URL"
    assert (
        ready_receipt.persistence.environment_config_id == receipt.ontology_package_id
    )
    assert ready_receipt.persistence.ocg_id == receipt.ocg_id
    assert ready_receipt.persistence.ocg_hash == receipt.ocg_hash
    assert ready_receipt.persistence.db_schema_hash == receipt.db_schema_hash
    assert ready_receipt.persistence.db_schema_registry_hash == registry_ref.hash
    assert ready_receipt.persistence.marker_ocg_hash == receipt.ocg_hash
    assert ready_receipt.persistence.installed is True
    assert ready_receipt.persistence.migrated is True
    assert ready_receipt.persistence.sql_root_count == len(receipt.sql_roots)
    assert ready_receipt.persistence.step_count == 2
    assert ready_receipt.graph is not None
    assert ready_receipt.graph.status == "ready"
    assert ready_receipt.graph.genesis_status == "succeeded"


@pytest.mark.asyncio
async def test_environment_readiness_db_gate_failure_stops_before_lane_head() -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    order: list[str] = []
    host_state = _host_state(
        persistence_backend="postgres",
        database_url_ref="env:DATABASE_URL",
    )
    receipt = _database_artifact_receipt(environment_id=environment_id)
    structure_artifacts = _FakeStructureArtifacts(receipt=receipt, order=order)
    ontology_persistence = _FakeOntologyPersistence(
        order=order,
        response=OntologyPersistenceEnsureReadyResponse(
            status="failed",
            actor_id=actor_id,
            environment_id=environment_id,
            ontology_package_id=receipt.ontology_package_id,
            error="db down",
        ),
    )
    meta_graph = _FakeMetaGraph(
        lane_heads=[],
        resolve_response=_resolve_response(host_state),
        order=order,
    )
    service = EnvironmentReadinessService(
        host=_FakeHost(host_state),
        meta_graph=meta_graph,
        structure_artifacts=structure_artifacts,
        ontology_persistence=ontology_persistence,
    )

    response = await service.ensure_ready(
        request=EnsureReadyRequest(environment_id=environment_id),
        actor_id=actor_id,
    )

    assert response.status == "failed"
    assert response.error == "db down"
    receipt = response.readiness_receipt
    assert receipt is not None
    assert receipt.status == "failed"
    assert receipt.persistence is not None
    assert receipt.persistence.status == "failed"
    assert receipt.graph is not None
    assert receipt.graph.status == "not_started"
    assert order == ["structure", "persistence"]
    assert meta_graph.head_requests == []
    assert meta_graph.invoke_requests == []


@pytest.mark.asyncio
async def test_environment_readiness_requires_constructor() -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    host_state = _host_state(function_id=uuid4())
    host_state = EnvironmentReadinessHostState(
        manifest_path=host_state.manifest_path,
        environment_title=host_state.environment_title,
        ocg_id=host_state.ocg_id,
        opg_hashes=host_state.opg_hashes,
        environment_projection_hash=host_state.environment_projection_hash,
        environment_object_projection_graph_id=(
            host_state.environment_object_projection_graph_id
        ),
        environment_constructor_function_id=None,
    )
    meta_graph = _FakeMetaGraph(
        lane_heads=[],
        resolve_response=_resolve_response(host_state),
    )
    service = EnvironmentReadinessService(
        host=_FakeHost(host_state),
        meta_graph=meta_graph,
    )

    response = await service.ensure_ready(
        request=EnsureReadyRequest(environment_id=environment_id),
        actor_id=actor_id,
    )

    assert response.status == "failed"
    assert response.error is not None
    assert "constructor" in response.error
    receipt = response.readiness_receipt
    assert receipt is not None
    assert receipt.status == "failed"
    assert receipt.persistence is not None
    assert receipt.persistence.status == "not_checked"
    assert receipt.graph is not None
    assert receipt.graph.status == "failed"
    assert meta_graph.head_requests == []
    assert meta_graph.invoke_requests == []


@pytest.mark.asyncio
async def test_environment_readiness_reports_timeout_exception_name() -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    service = EnvironmentReadinessService(
        host=_FakeHost(_host_state()),
        meta_graph=_TimeoutMetaGraph(),
    )

    response = await service.ensure_ready(
        request=EnsureReadyRequest(environment_id=environment_id),
        actor_id=actor_id,
    )

    assert response.status == "failed"
    assert response.error == "TimeoutError"
    assert response.readiness_receipt is not None
    assert response.readiness_receipt.status == "failed"
