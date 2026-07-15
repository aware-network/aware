from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast
from uuid import UUID

from pydantic import BaseModel

from aware_meta.manifest.loader import load_aware_toml_spec
from aware_ontology.manifest.loader import load_aware_ontology_toml_spec
from aware_meta_service.api_service_protocol import (
    build_aware_meta_service_protocol_handler,
)
from aware_meta.runtime.read_model_provider import (
    read_workspace_meta_runtime_read_model,
)
from aware_meta_service_dto.graph.config.package_compile import (
    MetaObjectConfigGraphPackageEnsureRequest,
)
from aware_meta_service_dto.graph.instance.commit_event import (
    MetaCommitSubscriptionRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphGetLaneHeadRequest,
    MetaGraphGetObjectInstanceGraphCommitRequest,
    MetaGraphInvokeFunctionRequest,
    MetaGraphResolveProjectionRequest,
)
from aware_meta_service_dto.persistence.database_readiness import (
    MetaDatabaseArtifactRef,
    MetaDatabaseArtifactReceipt,
    MetaPersistenceEnsureDatabaseReadyRequest,
)
from aware_ontology.semantic_runtime_catalog import (
    resolve_ontology_runtime_artifact_set_payload,
)
from aware_ontology_service_dto.graph.config.package_compile import (
    OntologyObjectConfigGraphPackageEnsureRequest,
    OntologyObjectConfigGraphPackageEnsureResponse,
)
from aware_ontology_service_dto.graph.instance.commit_event import (
    OntologyCommitEventEnvelope,
    OntologyCommitSubscriptionRequest,
    OntologyCommitSubscriptionResponse,
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
from aware_ontology_service_dto.persistence.readiness import (
    OntologyDatabaseArtifactRef,
    OntologyDatabaseArtifactReceipt,
    OntologyPersistenceEnsureReadyRequest,
    OntologyPersistenceEnsureReadyResponse,
)
from aware_ontology_service_dto.runtime.artifact_set import (
    OntologyRuntimeArtifactSetResolveRequest,
    OntologyRuntimeArtifactSetResolveResponse,
)
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
)


@dataclass(frozen=True, slots=True)
class _OntologyManifestResolution:
    ontology_manifest_path: str
    source_manifest_path: str


class _MetaGraphCapability(Protocol):
    async def get_lane_head(self, request: MetaGraphGetLaneHeadRequest) -> object: ...

    async def get_object_instance_graph_commit(
        self,
        request: MetaGraphGetObjectInstanceGraphCommitRequest,
    ) -> object: ...

    async def invoke_function(
        self,
        request: MetaGraphInvokeFunctionRequest,
    ) -> object: ...

    async def resolve_projection(
        self,
        request: MetaGraphResolveProjectionRequest,
    ) -> object: ...


class _MetaPackageCapability(Protocol):
    async def ensure_object_config_graph_package(
        self,
        request: MetaObjectConfigGraphPackageEnsureRequest,
    ) -> object: ...


class _MetaPersistenceCapability(Protocol):
    async def ensure_database_ready(
        self,
        request: MetaPersistenceEnsureDatabaseReadyRequest,
    ) -> object: ...


class _MetaCommitCapability(Protocol):
    async def subscribe(self, request: MetaCommitSubscriptionRequest) -> object: ...

    def stream_subscribe(
        self,
        request: MetaCommitSubscriptionRequest,
    ) -> AsyncIterator[object]: ...


class _MetaApiProtocol(Protocol):
    graph: _MetaGraphCapability
    package: _MetaPackageCapability
    persistence: _MetaPersistenceCapability
    commit: _MetaCommitCapability


class _MetaHandlerProtocol(Protocol):
    meta: _MetaApiProtocol


def build_aware_ontology_service_protocol_handler(
    *,
    meta_handler: object | None = None,
) -> object:
    return _AwareOntologyServiceProtocolHandler(meta_handler=meta_handler)


def _model_payload(value: object) -> dict[str, object]:
    if isinstance(value, BaseModel):
        return dict(cast(dict[str, object], value.model_dump(mode="python")))
    if isinstance(value, dict):
        return dict(cast(dict[str, object], value))
    raise TypeError(f"Expected pydantic-compatible payload, got {type(value).__name__}")


def _actor_id(explicit_actor_id: UUID | None) -> UUID:
    if explicit_actor_id is not None:
        return explicit_actor_id
    host_context = current_service_api_host_context()
    actor_id = (
        host_context.operation_context.actor_id if host_context is not None else None
    )
    if actor_id is None:
        raise RuntimeError(
            "Ontology graph invocation requires actor_id or active Service API host context."
        )
    return actor_id


def _meta_invoke_request(
    request: OntologyGraphInvokeFunctionRequest,
) -> MetaGraphInvokeFunctionRequest:
    payload = _model_payload(request)
    payload["actor_id"] = _actor_id(request.actor_id)
    payload["call_target"] = request.call_target.value
    return MetaGraphInvokeFunctionRequest.model_validate(payload)


def _ontology_commit_event_from_meta(
    event: object | None,
) -> OntologyCommitEventEnvelope | None:
    if event is None:
        return None
    payload = _model_payload(event)
    payload["event_family"] = "ontology.oig_commit"
    payload["ontology_authority_id"] = payload.pop(
        "meta_authority_id",
        "aware_ontology",
    )
    payload["required_reactions"] = payload.pop("required_meta_reactions", [])
    _normalize_commit_action_payload(payload)
    return OntologyCommitEventEnvelope.model_validate(payload)


def _normalize_commit_action_payload(payload: dict[str, object]) -> None:
    commit_action = payload.get("commit_action")
    if commit_action is None:
        return
    if isinstance(commit_action, BaseModel):
        action_payload = _model_payload(commit_action)
    elif isinstance(commit_action, dict):
        action_payload = dict(cast(dict[str, object], commit_action))
    else:
        return

    call_target = action_payload.get("call_target")
    if call_target is not None:
        raw_call_target = getattr(call_target, "value", call_target)
        action_payload["call_target"] = OntologyGraphFunctionCallTarget(
            raw_call_target
        ).value
    payload["commit_action"] = action_payload


def _ontology_payload_from_meta_response(response: object) -> dict[str, object]:
    payload = _model_payload(response)
    payload["required_reactions"] = payload.pop("required_meta_reactions", [])
    payload["commit_event"] = _ontology_commit_event_from_meta(
        payload.get("commit_event")
    )
    return payload


def _meta_commit_subscription_request(
    request: OntologyCommitSubscriptionRequest,
) -> MetaCommitSubscriptionRequest:
    payload = _model_payload(request)
    return MetaCommitSubscriptionRequest.model_validate(payload)


def _meta_package_ensure_request(
    request: OntologyObjectConfigGraphPackageEnsureRequest,
) -> tuple[
    MetaObjectConfigGraphPackageEnsureRequest, _OntologyManifestResolution | None
]:
    payload = _model_payload(request)
    resolution = _resolve_ontology_manifest_request(request)
    if resolution is not None:
        payload["aware_toml_path"] = resolution.source_manifest_path
    return MetaObjectConfigGraphPackageEnsureRequest.model_validate(payload), resolution


def _resolve_ontology_manifest_request(
    request: OntologyObjectConfigGraphPackageEnsureRequest,
) -> _OntologyManifestResolution | None:
    workspace_root = _resolve_workspace_root(request.workspace_root)
    ontology_manifest_path = _resolve_request_path(
        workspace_root=workspace_root,
        value=request.aware_toml_path,
    )
    if ontology_manifest_path.name != "aware.ontology.toml":
        return None

    ontology_spec = load_aware_ontology_toml_spec(toml_path=ontology_manifest_path)
    source_manifest_path = (
        ontology_manifest_path.parent / ontology_spec.ontology.source_manifest
    ).resolve()
    if not source_manifest_path.is_file():
        raise FileNotFoundError(
            "aware.ontology.toml source_manifest was not found: "
            f"{ontology_spec.ontology.source_manifest!r}"
        )

    source_spec = load_aware_toml_spec(toml_path=source_manifest_path)
    if source_spec.package.package_name != ontology_spec.ontology.package_name:
        raise RuntimeError(
            "aware.ontology.toml package_name does not match source aware.toml: "
            f"ontology={ontology_spec.ontology.package_name!r} "
            f"source={source_spec.package.package_name!r}"
        )
    if source_spec.package.fqn_prefix != ontology_spec.ontology.fqn_prefix:
        raise RuntimeError(
            "aware.ontology.toml fqn_prefix does not match source aware.toml: "
            f"ontology={ontology_spec.ontology.fqn_prefix!r} "
            f"source={source_spec.package.fqn_prefix!r}"
        )

    return _OntologyManifestResolution(
        ontology_manifest_path=_path_for_request(
            path=ontology_manifest_path,
            workspace_root=workspace_root,
        ),
        source_manifest_path=_path_for_request(
            path=source_manifest_path,
            workspace_root=workspace_root,
        ),
    )


def _resolve_workspace_root(value: str | None) -> Path:
    if value is not None and value.strip():
        return Path(value).expanduser().resolve()
    host_context = current_service_api_host_context()
    if host_context is not None and host_context.workspace_root is not None:
        return host_context.workspace_root.expanduser().resolve()
    raise RuntimeError(
        "Ontology service API request requires workspace_root or a hosted "
        "Service API workspace_root context."
    )


def _resolve_request_path(*, workspace_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    return path.resolve()


def _path_for_request(*, path: Path, workspace_root: Path) -> str:
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError:
        return path.as_posix()


def _ontology_package_failed_response(
    *,
    request: OntologyObjectConfigGraphPackageEnsureRequest,
    error: str,
) -> OntologyObjectConfigGraphPackageEnsureResponse:
    return OntologyObjectConfigGraphPackageEnsureResponse(
        status="failed",
        actor_id=request.actor_id,
        workspace_root=request.workspace_root,
        aware_toml_path=request.aware_toml_path,
        error=error,
    )


def _ontology_package_response_from_meta(
    *,
    request: OntologyObjectConfigGraphPackageEnsureRequest,
    response: object,
    resolution: _OntologyManifestResolution | None,
) -> OntologyObjectConfigGraphPackageEnsureResponse:
    payload = _model_payload(response)
    if resolution is not None:
        payload["aware_toml_path"] = resolution.ontology_manifest_path
        telemetry = dict(cast(dict[str, object], payload.get("telemetry") or {}))
        telemetry["ontology_manifest_path"] = resolution.ontology_manifest_path
        telemetry["resolved_source_manifest_path"] = resolution.source_manifest_path
        payload["telemetry"] = telemetry
    return OntologyObjectConfigGraphPackageEnsureResponse.model_validate(payload)


def _ontology_failed_response(
    *,
    request: OntologyGraphInvokeFunctionRequest,
    error: str,
) -> OntologyGraphInvokeFunctionResponse:
    return OntologyGraphInvokeFunctionResponse(
        status="failed",
        actor_id=request.actor_id,
        domain_branch_id=request.domain_branch_id,
        domain_projection_hash=request.domain_projection_hash,
        error=error,
    )


def _ontology_persistence_failed_response(
    *,
    request: OntologyPersistenceEnsureReadyRequest,
    error: str,
) -> OntologyPersistenceEnsureReadyResponse:
    receipt = request.database_artifact_receipt
    return OntologyPersistenceEnsureReadyResponse(
        status="failed",
        error=(
            "Ontology persistence readiness requires an Ontology-native "
            f"database artifact receipt: {error}"
        ),
        actor_id=request.actor_id,
        ontology_package_id=receipt.ontology_package_id,
        ocg_id=receipt.ocg_id,
        ocg_hash=receipt.ocg_hash,
        db_schema_hash=receipt.db_schema_hash,
        sql_root_count=len(receipt.sql_roots),
    )


def _ontology_persistence_boot_failed_response(
    *,
    request: OntologyPersistenceEnsureReadyRequest,
    error: str,
) -> OntologyPersistenceEnsureReadyResponse:
    receipt = request.database_artifact_receipt
    return OntologyPersistenceEnsureReadyResponse(
        status="failed",
        error=f"Ontology persistence readiness failed during Meta DB boot: {error}",
        actor_id=request.actor_id,
        ontology_package_id=receipt.ontology_package_id,
        ocg_id=receipt.ocg_id,
        ocg_hash=receipt.ocg_hash,
        db_schema_hash=receipt.db_schema_hash,
        sql_root_count=len(receipt.sql_roots),
    )


def _required_uuid(value: UUID | None, field_name: str) -> UUID:
    if value is None:
        raise RuntimeError(f"receipt.{field_name} is required.")
    return value


def _required_text(value: str | None, field_name: str) -> str:
    if value is None or not value.strip():
        raise RuntimeError(f"receipt.{field_name} is required.")
    return value


def _required_ontology_ref(
    value: OntologyDatabaseArtifactRef | None,
    field_name: str,
) -> OntologyDatabaseArtifactRef:
    if value is None:
        raise RuntimeError(f"receipt.{field_name} is required.")
    if not value.path.strip():
        raise RuntimeError(f"receipt.{field_name}.path is required.")
    if not value.hash.strip():
        raise RuntimeError(f"receipt.{field_name}.hash is required.")
    return value


def _meta_artifact_ref_from_ontology(
    value: OntologyDatabaseArtifactRef | None,
) -> MetaDatabaseArtifactRef | None:
    if value is None:
        return None
    return MetaDatabaseArtifactRef(path=value.path, hash=value.hash)


def _required_meta_artifact_ref_from_ontology(
    value: OntologyDatabaseArtifactRef | None,
    field_name: str,
) -> MetaDatabaseArtifactRef:
    return MetaDatabaseArtifactRef.model_validate(
        _model_payload(_required_ontology_ref(value, field_name))
    )


def _meta_database_receipt_from_ontology(
    receipt: OntologyDatabaseArtifactReceipt,
) -> MetaDatabaseArtifactReceipt:
    ontology_package_id = _required_uuid(
        receipt.ontology_package_id,
        "ontology_package_id",
    )
    return MetaDatabaseArtifactReceipt(
        meta_package_id=ontology_package_id,
        meta_manifest_ref=_required_meta_artifact_ref_from_ontology(
            receipt.ontology_manifest_ref,
            "ontology_manifest_ref",
        ),
        ocg_id=_required_uuid(receipt.ocg_id, "ocg_id"),
        ocg_hash=_required_text(receipt.ocg_hash, "ocg_hash"),
        ocg_head_commit_id=receipt.ocg_head_commit_id,
        ocg_lane_branch_id=receipt.ocg_lane_branch_id,
        ocg_lane_projection_hash=receipt.ocg_lane_projection_hash,
        db_schema_registry_ref=_required_meta_artifact_ref_from_ontology(
            receipt.db_schema_registry_ref,
            "db_schema_registry_ref",
        ),
        db_schema_hash=_required_text(receipt.db_schema_hash, "db_schema_hash"),
        db_backend_target=receipt.db_backend_target,
        db_package_kind=receipt.db_package_kind,
        sql_roots=list(receipt.sql_roots),
        meta_lock_ref=_meta_artifact_ref_from_ontology(
            receipt.ontology_lock_ref
        ),
        ocg_lane_index_ref=_meta_artifact_ref_from_ontology(receipt.ocg_lane_index_ref),
    )


class _OntologyGraphCapabilityHandler:
    def __init__(self, *, meta_handler: _MetaHandlerProtocol) -> None:
        self._meta_handler: _MetaHandlerProtocol = meta_handler

    async def get_lane_head(
        self,
        request: OntologyGraphGetLaneHeadRequest,
    ) -> OntologyGraphGetLaneHeadResponse:
        meta_response = await self._meta_handler.meta.graph.get_lane_head(
            MetaGraphGetLaneHeadRequest.model_validate(_model_payload(request))
        )
        return OntologyGraphGetLaneHeadResponse.model_validate(
            _model_payload(meta_response)
        )

    async def get_object_instance_graph_commit(
        self,
        request: OntologyGraphGetObjectInstanceGraphCommitRequest,
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse:
        meta_response = (
            await self._meta_handler.meta.graph.get_object_instance_graph_commit(
                MetaGraphGetObjectInstanceGraphCommitRequest.model_validate(
                    _model_payload(request)
                )
            )
        )
        return OntologyGraphGetObjectInstanceGraphCommitResponse.model_validate(
            _model_payload(meta_response)
        )

    async def invoke_function(
        self,
        request: OntologyGraphInvokeFunctionRequest,
    ) -> OntologyGraphInvokeFunctionResponse:
        try:
            meta_request = _meta_invoke_request(request)
            meta_response = await self._meta_handler.meta.graph.invoke_function(
                meta_request
            )
            return OntologyGraphInvokeFunctionResponse.model_validate(
                _ontology_payload_from_meta_response(meta_response)
            )
        except Exception as exc:
            return _ontology_failed_response(request=request, error=str(exc))

    async def resolve_projection(
        self,
        request: OntologyGraphResolveProjectionRequest,
    ) -> OntologyGraphResolveProjectionResponse:
        meta_response = await self._meta_handler.meta.graph.resolve_projection(
            MetaGraphResolveProjectionRequest.model_validate(_model_payload(request))
        )
        return OntologyGraphResolveProjectionResponse.model_validate(
            _model_payload(meta_response)
        )


class _OntologyPackageCapabilityHandler:
    def __init__(self, *, meta_handler: _MetaHandlerProtocol) -> None:
        self._meta_handler: _MetaHandlerProtocol = meta_handler

    async def ensure_object_config_graph_package(
        self,
        request: OntologyObjectConfigGraphPackageEnsureRequest,
    ) -> OntologyObjectConfigGraphPackageEnsureResponse:
        try:
            meta_request, resolution = _meta_package_ensure_request(request)
            meta_response = await self._meta_handler.meta.package.ensure_object_config_graph_package(
                meta_request
            )
            return _ontology_package_response_from_meta(
                request=request,
                response=meta_response,
                resolution=resolution,
            )
        except Exception as exc:
            return _ontology_package_failed_response(
                request=request,
                error=str(exc),
            )


class _OntologyPersistenceCapabilityHandler:
    def __init__(self, *, meta_handler: _MetaHandlerProtocol) -> None:
        self._meta_handler: _MetaHandlerProtocol = meta_handler

    async def ensure_ready(
        self,
        request: OntologyPersistenceEnsureReadyRequest,
    ) -> OntologyPersistenceEnsureReadyResponse:
        try:
            meta_request = MetaPersistenceEnsureDatabaseReadyRequest(
                actor_id=request.actor_id,
                database_artifact_receipt=(
                    _meta_database_receipt_from_ontology(
                        request.database_artifact_receipt,
                    )
                ),
                database_url_ref=request.database_url_ref,
                boot_policy=request.boot_policy,
            )
        except Exception as exc:
            return _ontology_persistence_failed_response(
                request=request,
                error=str(exc),
            )
        try:
            meta_response = (
                await self._meta_handler.meta.persistence.ensure_database_ready(
                    meta_request
                )
            )
        except Exception as exc:
            return _ontology_persistence_boot_failed_response(
                request=request,
                error=str(exc),
            )
        payload = _model_payload(meta_response)
        payload["ontology_package_id"] = (
            request.database_artifact_receipt.ontology_package_id
        )
        return OntologyPersistenceEnsureReadyResponse.model_validate(payload)


class _OntologyCommitCapabilityHandler:
    def __init__(self, *, meta_handler: _MetaHandlerProtocol) -> None:
        self._meta_handler: _MetaHandlerProtocol = meta_handler

    async def subscribe(
        self,
        request: OntologyCommitSubscriptionRequest,
    ) -> OntologyCommitSubscriptionResponse:
        meta_response = await self._meta_handler.meta.commit.subscribe(
            _meta_commit_subscription_request(request)
        )
        return OntologyCommitSubscriptionResponse.model_validate(
            _model_payload(meta_response)
        )

    async def stream_subscribe(
        self,
        request: OntologyCommitSubscriptionRequest,
    ) -> AsyncIterator[OntologyCommitEventEnvelope]:
        meta_request = _meta_commit_subscription_request(request)
        async for event in self._meta_handler.meta.commit.stream_subscribe(
            meta_request
        ):
            ontology_event = _ontology_commit_event_from_meta(event)
            if ontology_event is not None:
                yield ontology_event


def _ontology_runtime_artifact_set_failed_response(
    *,
    request: OntologyRuntimeArtifactSetResolveRequest,
    error: str,
) -> OntologyRuntimeArtifactSetResolveResponse:
    return OntologyRuntimeArtifactSetResolveResponse(
        status="failed",
        error=f"Ontology runtime artifact-set resolution failed: {error}",
        actor_id=request.actor_id,
        package_name=request.package_name,
        fqn_prefix=request.fqn_prefix,
        evidence={
            "activation_allowed": False,
            "activation_policy": "workspace_revision_or_service_lifecycle_required",
        },
    )


class _OntologyRuntimeCapabilityHandler:
    async def resolve_runtime_artifact_set(
        self,
        request: OntologyRuntimeArtifactSetResolveRequest,
    ) -> OntologyRuntimeArtifactSetResolveResponse:
        try:
            artifact_set_payload = resolve_ontology_runtime_artifact_set_payload(
                source_payload=request.source_payload,
                package_name=request.package_name,
                fqn_prefix=request.fqn_prefix,
                artifact_set_id=request.artifact_set_id,
                workspace_revision_id=request.workspace_revision_id,
                materialization_ref=request.materialization_ref,
                include_artifacts=request.include_artifacts,
            )
        except Exception as exc:
            return _ontology_runtime_artifact_set_failed_response(
                request=request,
                error=str(exc),
            )
        return OntologyRuntimeArtifactSetResolveResponse.model_validate(
            {
                "status": "resolved",
                "actor_id": request.actor_id,
                "package_name": artifact_set_payload.get("package_name"),
                "fqn_prefix": artifact_set_payload.get("fqn_prefix"),
                "artifact_set": artifact_set_payload,
                "evidence": {
                    "source": (
                        "source_payload"
                        if request.source_payload is not None
                        else "explicit_coordinates"
                    ),
                    "activation_allowed": False,
                    "activation_policy": artifact_set_payload.get("activation_policy"),
                },
            }
        )


@dataclass(frozen=True, slots=True)
class _OntologyApiProtocolHandler:
    graph: _OntologyGraphCapabilityHandler
    package: _OntologyPackageCapabilityHandler
    persistence: _OntologyPersistenceCapabilityHandler
    commit: _OntologyCommitCapabilityHandler
    runtime: _OntologyRuntimeCapabilityHandler


class _AwareOntologyServiceProtocolHandler:
    def __init__(self, *, meta_handler: object | None = None) -> None:
        resolved_meta_handler = cast(
            _MetaHandlerProtocol,
            meta_handler
            or build_aware_meta_service_protocol_handler(
                graph_context_provider=_ontology_authority_graph_context,
            ),
        )
        self.ontology: _OntologyApiProtocolHandler = _OntologyApiProtocolHandler(
            graph=_OntologyGraphCapabilityHandler(meta_handler=resolved_meta_handler),
            package=_OntologyPackageCapabilityHandler(
                meta_handler=resolved_meta_handler,
            ),
            persistence=_OntologyPersistenceCapabilityHandler(
                meta_handler=resolved_meta_handler,
            ),
            commit=_OntologyCommitCapabilityHandler(
                meta_handler=resolved_meta_handler,
            ),
            runtime=_OntologyRuntimeCapabilityHandler(),
        )


async def _ontology_authority_graph_context() -> object:
    host_context = current_service_api_host_context()
    if host_context is None:
        raise RuntimeError(
            "Ontology graph execution requires an active Service API host context."
        )
    package_names = tuple(
        name.strip()
        for name in host_context.ontology_authority_package_names
        if name.strip()
    )
    if package_names:
        authority_root = host_context.ontology_authority_root
        if authority_root is None:
            source_kind = str(host_context.ontology_authority_source_kind or "").strip()
            source_context = f" source_kind={source_kind!r}" if source_kind else ""
            raise RuntimeError(
                "Ontology graph execution requires an explicit ontology authority "
                "root or artifact root when ontology authority package names are "
                f"configured:{source_context} package_names={package_names!r}."
            )
        root = authority_root.expanduser().resolve()
        read_model = read_workspace_meta_runtime_read_model(
            repo_root=root,
            aware_root=root,
            required_projection_names=(),
            required_package_names=package_names,
            composite_name="Ontology Service Authority Runtime",
        )
        return read_model.context
    if host_context.materialization is not None:
        return host_context.materialization.graph_context
    if host_context.graph_context_provider is not None:
        return await host_context.graph_context_provider.resolve_graph_context()
    raise RuntimeError(
        "Ontology graph execution requires ontology authority package names or "
        "a Service graph context provider."
    )
