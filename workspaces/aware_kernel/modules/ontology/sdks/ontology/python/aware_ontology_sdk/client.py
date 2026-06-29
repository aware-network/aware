from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from aware_ontology_service_dto.graph.config.package_compile import (
    OntologyObjectConfigGraphPackageDependencyRef,
    OntologyObjectConfigGraphPackageEnsureRequest,
    OntologyObjectConfigGraphPackageEnsureResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetLaneHeadRequest,
    OntologyGraphGetLaneHeadResponse,
    OntologyGraphGetObjectInstanceGraphCommitRequest,
    OntologyGraphGetObjectInstanceGraphCommitResponse,
    OntologyGraphInvokeFunctionRequest,
    OntologyGraphInvokeFunctionResponse,
    OntologyGraphResolveProjectionRequest,
    OntologyGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call_target import (
    OntologyGraphFunctionCallTarget,
)
from aware_ontology_service_dto.graph.instance.commit_event import (
    OntologyCommitEventEnvelope,
    OntologyCommitSubscriptionRequest,
    OntologyCommitSubscriptionResponse,
)
from aware_ontology_service_dto.persistence.readiness import (
    OntologyDatabaseArtifactReceipt,
    OntologyPersistenceEnsureReadyRequest,
    OntologyPersistenceEnsureReadyResponse,
)
from aware_ontology_service_dto.runtime.artifact_set import (
    OntologyMaterializedSemanticRootRef,
    OntologyRuntimeArtifactSet,
    OntologyRuntimeArtifactSetResolveRequest,
    OntologyRuntimeArtifactSetResolveResponse,
)
from aware_types import JsonArray, JsonObject, JsonValue

OntologyGraphCallTarget = Literal["instance", "opg_constructor"]


class OntologySdkError(RuntimeError):
    pass


class _OntologyGraphCapabilityClient(Protocol):
    async def get_lane_head(
        self,
        request: OntologyGraphGetLaneHeadRequest,
    ) -> OntologyGraphGetLaneHeadResponse: ...

    async def get_object_instance_graph_commit(
        self,
        request: OntologyGraphGetObjectInstanceGraphCommitRequest,
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse: ...

    async def invoke_function(
        self,
        request: OntologyGraphInvokeFunctionRequest,
    ) -> OntologyGraphInvokeFunctionResponse: ...

    async def resolve_projection(
        self,
        request: OntologyGraphResolveProjectionRequest,
    ) -> OntologyGraphResolveProjectionResponse: ...


class _OntologyPackageCapabilityClient(Protocol):
    async def ensure_object_config_graph_package(
        self,
        request: OntologyObjectConfigGraphPackageEnsureRequest,
    ) -> OntologyObjectConfigGraphPackageEnsureResponse: ...


class _OntologyPersistenceCapabilityClient(Protocol):
    async def ensure_ready(
        self,
        request: OntologyPersistenceEnsureReadyRequest,
    ) -> OntologyPersistenceEnsureReadyResponse: ...


class _OntologyCommitCapabilityClient(Protocol):
    async def subscribe(
        self,
        request: OntologyCommitSubscriptionRequest,
    ) -> OntologyCommitSubscriptionResponse: ...

    def stream_subscribe(
        self,
        request: OntologyCommitSubscriptionRequest,
    ) -> AsyncIterator[OntologyCommitEventEnvelope]: ...


class _OntologyRuntimeCapabilityClient(Protocol):
    async def resolve_runtime_artifact_set(
        self,
        request: OntologyRuntimeArtifactSetResolveRequest,
    ) -> OntologyRuntimeArtifactSetResolveResponse: ...


class _OntologyApiNamespaceClient(Protocol):
    @property
    def graph(self) -> _OntologyGraphCapabilityClient: ...

    @property
    def package(self) -> _OntologyPackageCapabilityClient: ...

    @property
    def persistence(self) -> _OntologyPersistenceCapabilityClient: ...

    @property
    def commit(self) -> _OntologyCommitCapabilityClient: ...

    @property
    def runtime(self) -> _OntologyRuntimeCapabilityClient: ...


class OntologyGeneratedApiClient(Protocol):
    @property
    def ontology(self) -> _OntologyApiNamespaceClient: ...


@dataclass(frozen=True, slots=True)
class OntologySdkClient:
    api_client: OntologyGeneratedApiClient

    async def ensure_object_config_graph_package(
        self,
        *,
        aware_toml_path: str,
        actor_id: UUID | None = None,
        workspace_root: str | None = None,
        parent_branch_id: UUID | None = None,
        package_branch_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        object_config_graph_package_id: UUID | None = None,
        dependency_refs: Sequence[OntologyObjectConfigGraphPackageDependencyRef] = (),
        include_object_config_graph: bool = False,
        collect_telemetry: bool = True,
    ) -> OntologyObjectConfigGraphPackageEnsureResponse:
        response = (
            await self.api_client.ontology.package.ensure_object_config_graph_package(
                OntologyObjectConfigGraphPackageEnsureRequest(
                    actor_id=actor_id,
                    workspace_root=workspace_root,
                    aware_toml_path=aware_toml_path,
                    parent_branch_id=parent_branch_id,
                    package_branch_id=package_branch_id,
                    source_code_package_id=source_code_package_id,
                    object_config_graph_package_id=object_config_graph_package_id,
                    dependency_refs=list(dependency_refs),
                    include_object_config_graph=include_object_config_graph,
                    collect_telemetry=collect_telemetry,
                )
            )
        )
        _raise_if_failed(response.status, response.error, operation="ensure_package")
        return response

    async def ensure_ready(
        self,
        *,
        database_artifact_receipt: OntologyDatabaseArtifactReceipt,
        actor_id: UUID | None = None,
        database_url_ref: str | None = None,
        boot_policy: str = "migrate",
    ) -> OntologyPersistenceEnsureReadyResponse:
        response = await self.api_client.ontology.persistence.ensure_ready(
            OntologyPersistenceEnsureReadyRequest(
                actor_id=actor_id,
                database_artifact_receipt=database_artifact_receipt,
                database_url_ref=database_url_ref,
                boot_policy=boot_policy,
            )
        )
        _raise_if_failed(response.status, response.error, operation="ensure_ready")
        return response

    async def resolve_runtime_artifact_set(
        self,
        *,
        actor_id: UUID | None = None,
        package_name: str | None = None,
        fqn_prefix: str | None = None,
        artifact_set_id: str | None = None,
        workspace_revision_id: str | None = None,
        materialization_ref: str | None = None,
        include_artifacts: bool = True,
        source_payload: Mapping[str, JsonValue] | None = None,
    ) -> OntologyRuntimeArtifactSetResolveResponse:
        response = await self.api_client.ontology.runtime.resolve_runtime_artifact_set(
            OntologyRuntimeArtifactSetResolveRequest(
                actor_id=actor_id,
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                artifact_set_id=artifact_set_id,
                workspace_revision_id=workspace_revision_id,
                materialization_ref=materialization_ref,
                include_artifacts=include_artifacts,
                source_payload=(
                    JsonObject(dict(source_payload or {}))
                    if source_payload is not None
                    else None
                ),
            )
        )
        _raise_if_failed(
            response.status,
            response.error,
            operation="resolve_runtime_artifact_set",
        )
        return response

    def materialized_semantic_roots(
        self,
        artifact_set: OntologyRuntimeArtifactSet | None,
    ) -> tuple[OntologyMaterializedSemanticRootRef, ...]:
        if artifact_set is None:
            return ()
        return tuple(artifact_set.materialized_semantic_roots)

    def find_materialized_semantic_root(
        self,
        artifact_set: OntologyRuntimeArtifactSet | None,
        *,
        semantic_root_kind: str | None = None,
        semantic_projection_name: str | None = None,
    ) -> OntologyMaterializedSemanticRootRef | None:
        for root in self.materialized_semantic_roots(artifact_set):
            if (
                semantic_root_kind is not None
                and root.semantic_root_kind != semantic_root_kind
            ):
                continue
            if (
                semantic_projection_name is not None
                and root.semantic_projection_name != semantic_projection_name
            ):
                continue
            return root
        return None

    async def get_lane_head(
        self,
        *,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        actor_id: UUID | None = None,
    ) -> OntologyGraphGetLaneHeadResponse:
        response = await self.api_client.ontology.graph.get_lane_head(
            OntologyGraphGetLaneHeadRequest(
                actor_id=actor_id,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
            )
        )
        _raise_if_failed(response.status, response.error, operation="get_lane_head")
        return response

    async def get_object_instance_graph_commit(
        self,
        *,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        domain_commit_id: UUID,
        actor_id: UUID | None = None,
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse:
        response = (
            await self.api_client.ontology.graph.get_object_instance_graph_commit(
                OntologyGraphGetObjectInstanceGraphCommitRequest(
                    actor_id=actor_id,
                    domain_branch_id=domain_branch_id,
                    domain_projection_hash=domain_projection_hash,
                    domain_commit_id=domain_commit_id,
                )
            )
        )
        _raise_if_failed(
            response.status,
            response.error,
            operation="get_object_instance_graph_commit",
        )
        return response

    async def resolve_projection(
        self,
        *,
        actor_id: UUID | None = None,
        projection_name: str | None = None,
        projection_hash: str | None = None,
        object_projection_graph_id: UUID | None = None,
        include_available: bool = False,
    ) -> OntologyGraphResolveProjectionResponse:
        response = await self.api_client.ontology.graph.resolve_projection(
            OntologyGraphResolveProjectionRequest(
                actor_id=actor_id,
                projection_name=projection_name,
                projection_hash=projection_hash,
                object_projection_graph_id=object_projection_graph_id,
                include_available=include_available,
            )
        )
        _raise_if_failed(
            response.status,
            response.error,
            operation="resolve_projection",
        )
        return response

    async def invoke_function(
        self,
        *,
        function_id: UUID,
        actor_id: UUID | None = None,
        domain_branch_id: UUID | None = None,
        domain_projection_hash: str | None = None,
        call_target: OntologyGraphCallTarget | OntologyGraphFunctionCallTarget = (
            "instance"
        ),
        target_object_id: UUID | None = None,
        object_projection_graph_id: UUID | None = None,
        args: Sequence[JsonValue] = (),
        kwargs: Mapping[str, JsonValue] | None = None,
        expected_graph_hash_pre: str | None = None,
        expected_head_commit_id: UUID | None = None,
        commit: bool = True,
        publish: bool = False,
    ) -> OntologyGraphInvokeFunctionResponse:
        response = await self.api_client.ontology.graph.invoke_function(
            OntologyGraphInvokeFunctionRequest(
                actor_id=actor_id,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
                call_target=_call_target(call_target),
                target_object_id=target_object_id,
                object_projection_graph_id=object_projection_graph_id,
                function_id=function_id,
                args=JsonArray(list(args)),
                kwargs=JsonObject(dict(kwargs or {})),
                expected_graph_hash_pre=expected_graph_hash_pre,
                expected_head_commit_id=expected_head_commit_id,
                commit=commit,
                publish=publish,
            )
        )
        _raise_if_failed(response.status, response.error, operation="invoke_function")
        return response

    async def subscribe_commits(
        self,
        *,
        subscriber_id: str,
        event_families: Sequence[str] = (),
        branch_filters: Sequence[UUID] = (),
        projection_hash_filters: Sequence[str] = (),
        object_instance_graph_identity_filters: Sequence[UUID] = (),
        package_filters: Sequence[str] = (),
        include_artifact_refs: bool = True,
        resume_after_event_id: UUID | None = None,
    ) -> OntologyCommitSubscriptionResponse:
        response = await self.api_client.ontology.commit.subscribe(
            _commit_subscription_request(
                subscriber_id=subscriber_id,
                event_families=event_families,
                branch_filters=branch_filters,
                projection_hash_filters=projection_hash_filters,
                object_instance_graph_identity_filters=(
                    object_instance_graph_identity_filters
                ),
                package_filters=package_filters,
                include_artifact_refs=include_artifact_refs,
                resume_after_event_id=resume_after_event_id,
            )
        )
        _raise_if_failed(
            "succeeded" if response.accepted else "failed",
            response.error,
            operation="subscribe_commits",
        )
        return response

    def stream_commits(
        self,
        *,
        subscriber_id: str,
        event_families: Sequence[str] = (),
        branch_filters: Sequence[UUID] = (),
        projection_hash_filters: Sequence[str] = (),
        object_instance_graph_identity_filters: Sequence[UUID] = (),
        package_filters: Sequence[str] = (),
        include_artifact_refs: bool = True,
        resume_after_event_id: UUID | None = None,
    ) -> AsyncIterator[OntologyCommitEventEnvelope]:
        return self.api_client.ontology.commit.stream_subscribe(
            _commit_subscription_request(
                subscriber_id=subscriber_id,
                event_families=event_families,
                branch_filters=branch_filters,
                projection_hash_filters=projection_hash_filters,
                object_instance_graph_identity_filters=(
                    object_instance_graph_identity_filters
                ),
                package_filters=package_filters,
                include_artifact_refs=include_artifact_refs,
                resume_after_event_id=resume_after_event_id,
            )
        )


def _call_target(
    value: OntologyGraphCallTarget | OntologyGraphFunctionCallTarget,
) -> OntologyGraphFunctionCallTarget:
    if isinstance(value, OntologyGraphFunctionCallTarget):
        return value
    try:
        return OntologyGraphFunctionCallTarget(value)
    except ValueError as exc:
        raise OntologySdkError(f"Unsupported Ontology call target: {value!r}") from exc


def _raise_if_failed(
    status: str,
    error: str | None,
    *,
    operation: str,
) -> None:
    if status.strip().lower() in {"ok", "ready", "succeeded", "available", "resolved"}:
        return
    raise OntologySdkError(
        f"Ontology SDK operation failed: operation={operation!r} "
        f"status={status!r} error={error!r}"
    )


def _commit_subscription_request(
    *,
    subscriber_id: str,
    event_families: Sequence[str],
    branch_filters: Sequence[UUID],
    projection_hash_filters: Sequence[str],
    object_instance_graph_identity_filters: Sequence[UUID],
    package_filters: Sequence[str],
    include_artifact_refs: bool,
    resume_after_event_id: UUID | None,
) -> OntologyCommitSubscriptionRequest:
    return OntologyCommitSubscriptionRequest(
        subscriber_id=subscriber_id,
        event_families=list(event_families),
        branch_filters=list(branch_filters),
        projection_hash_filters=list(projection_hash_filters),
        object_instance_graph_identity_filters=list(
            object_instance_graph_identity_filters
        ),
        package_filters=list(package_filters),
        include_artifact_refs=include_artifact_refs,
        resume_after_event_id=resume_after_event_id,
    )
