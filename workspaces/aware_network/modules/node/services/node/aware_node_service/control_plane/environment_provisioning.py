from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
import os
import socket
import sys
from typing import Any, Protocol, TypedDict, cast
from uuid import UUID, uuid4

from aware_environment_service_dto.environment.environment import (
    ConfigureServiceApiDependencyRoutesRequest,
    ConfigureServiceApiDependencyRoutesResponse,
    EnsureReadyRequest,
    EnsureReadyResponse,
    UpsertEnvironmentProfileRequest,
    UpsertEnvironmentProfileResponse,
)
from aware_network_service_dto.comms.models.network import NetworkAppType
from aware_network.communications.app_config import (
    get_network_app_config as get_app_config,
)
from aware_node_service_dto.node.host import ProvisionEnvironmentRequest
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    service_api_dependency_routes_to_payload,
)
from aware_types import JsonArray, JsonObject

from aware_node_service.acl_mode import lock_node_actor_role_acl_mode
from aware_node_service.control_plane.environment_api_network import (
    build_environment_service_api_client,
)
from aware_node_service.control_plane.environment_profile_mounts import (
    EnvironmentProfileMountApplyPlan,
)
from aware_node_service.control_plane.environment_config_registry import (
    EnvironmentConfigRecord,
    resolve_environment_config_record,
)
from aware_node_service.control_plane.environment_endpoint import (
    resolve_node_environment_publication_endpoint,
)
from aware_node_service.control_plane.environment_host_support import (
    EnvironmentRouteHandler,
    _environment_id_for_config,
    _environment_key_for_config,
    _resolve_environment_config_root,
)
from aware_node_service.control_plane.environment_registry import (
    HostedEnvironmentRecord,
    environment_registry,
)


class _WorkspaceRecordUpdates(TypedDict, total=False):
    outer_wrapper_kind: str
    environment_handle: str | None
    workspace_root: str | None
    workspace_toml_path: str | None
    workspace_id: str | None
    workspace_package_id: str | None
    workspace_build_invocation_id: str | None
    workspace_build_receipt_path: str | None
    workspace_build_latest_path: str | None
    workspace_target_latest_path: str | None
    workspace_target_ref: str | None


@dataclass(frozen=True, slots=True)
class EnvironmentProvisioningPlan:
    provision_mode: str
    resolved_config: EnvironmentConfigRecord | None
    environment_key: str
    environment_id: UUID
    environment_title: str | None
    environment_endpoint: str | None
    environment_port: int | None
    database_url: str | None
    persistence_backend: str | None
    eager_ready: bool


@dataclass(frozen=True, slots=True)
class EnvironmentProcessLaunchResult:
    process: object
    pid: int | None


class _SubprocessFactory(Protocol):
    async def __call__(
        self,
        program: str,
        *args: str,
        env: Mapping[str, str],
    ) -> object: ...


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


_RUNTIME_BASE_ENVIRONMENT_MANIFEST_ENV = "AWARE_RUNTIME_BASE_ENVIRONMENT_MANIFEST"
_RUNTIME_BASE_ENVIRONMENT_MANIFESTS_ENV = "AWARE_RUNTIME_BASE_ENVIRONMENT_MANIFESTS"
_ENVIRONMENT_MANIFEST_ENV = "AWARE_ENVIRONMENT_MANIFEST"
_ENVIRONMENT_HOST_RUNTIME_MANIFEST_PATH_ENV = (
    "AWARE_ENVIRONMENT_HOST_RUNTIME_MANIFEST_PATH"
)
_LOCAL_SOURCE_DB_SCHEMA_REFRESH_ENV = "AWARE_ENVIRONMENT_DB_SCHEMA_LOCAL_SOURCE_REFRESH"
_NODE_RUN_MANIFEST_SOURCE_KIND_ENV = "AWARE_NODE_RUN_MANIFEST_SOURCE_KIND"
_NODE_WORKSPACE_REVISION_ROOT_ENV = "AWARE_NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT"


def build_environment_process_env(
    *,
    base_env: Mapping[str, str],
    node_id: UUID,
    environment_key: str,
    environment_id: UUID,
    environment_port: int | None,
    database_url: str | None,
    persistence_backend: str | None,
) -> dict[str, str]:
    env = dict(base_env)
    env.pop(_RUNTIME_BASE_ENVIRONMENT_MANIFEST_ENV, None)
    env.pop(_RUNTIME_BASE_ENVIRONMENT_MANIFESTS_ENV, None)
    env.pop(_ENVIRONMENT_MANIFEST_ENV, None)
    env.pop(_ENVIRONMENT_HOST_RUNTIME_MANIFEST_PATH_ENV, None)
    env.pop(_LOCAL_SOURCE_DB_SCHEMA_REFRESH_ENV, None)
    env["AWARE_ENVIRONMENT_KEY"] = environment_key
    env["AWARE_ENVIRONMENT_HOST_SERVICE_API_ROUTE_REGISTRY_ENABLED"] = "true"
    env["AWARE_ENVIRONMENT_HOST_SERVICE_API_ROUTE_REGISTRY_NODE_ID"] = str(node_id)
    env["AWARE_ENVIRONMENT_HOST_SERVICE_API_ROUTE_REGISTRY_ENVIRONMENT_ID"] = str(
        environment_id
    )
    env["AWARE_ENVIRONMENT_EAGER_INDEX"] = "0"
    if (
        env.get(_NODE_RUN_MANIFEST_SOURCE_KIND_ENV) == "node_ontology_manifest"
        and not str(env.get(_NODE_WORKSPACE_REVISION_ROOT_ENV) or "").strip()
    ):
        env[_LOCAL_SOURCE_DB_SCHEMA_REFRESH_ENV] = "1"
    lock_node_actor_role_acl_mode(env=env)
    if environment_port is not None:
        env["AWARE_ENVIRONMENT_PORT"] = str(environment_port)
    if database_url is not None:
        env["DATABASE_URL"] = database_url
        env.setdefault("AWARE_PERSISTENCE_BACKEND", "db")
    if persistence_backend is not None:
        env["AWARE_PERSISTENCE_BACKEND"] = persistence_backend
    return env


def workspace_record_updates_from_config(
    *, config: EnvironmentConfigRecord | None
) -> _WorkspaceRecordUpdates:
    if config is None:
        return {}
    return {
        "outer_wrapper_kind": config.outer_wrapper_kind,
        "environment_handle": config.environment_handle,
        "workspace_root": config.workspace_root,
        "workspace_toml_path": config.workspace_toml_path,
        "workspace_id": config.workspace_id,
        "workspace_package_id": config.workspace_package_id,
        "workspace_build_invocation_id": config.workspace_build_invocation_id,
        "workspace_build_receipt_path": config.workspace_build_receipt_path,
        "workspace_build_latest_path": config.workspace_build_latest_path,
        "workspace_target_latest_path": config.workspace_target_latest_path,
        "workspace_target_ref": config.workspace_target_ref,
    }


class EnvironmentProvisioningPlanner:
    """Resolves a public provisioning request into a deterministic host plan."""

    def __init__(
        self,
        *,
        uuid_factory: Any = uuid4,
        free_port_factory: Any = _find_free_port,
    ) -> None:
        self._uuid_factory = uuid_factory
        self._free_port_factory = free_port_factory

    def plan(
        self,
        *,
        request: ProvisionEnvironmentRequest,
        node_id: UUID,
        provision_mode: str,
    ) -> EnvironmentProvisioningPlan:
        if request.environment_config_id is None:
            raise RuntimeError(
                "ProvisionEnvironmentRequest requires environment_config_id for "
                "Node-hosted Environment provisioning."
            )

        config_root = _resolve_environment_config_root()
        try:
            resolved_config = resolve_environment_config_record(
                aware_root=config_root,
                environment_config_id=request.environment_config_id,
            )
        except KeyError as exc:
            raise RuntimeError(
                "Unknown environment_config_id for provisioning: "
                f"{request.environment_config_id}"
            ) from exc

        environment_port = request.environment_port
        environment_endpoint: str | None = None
        if provision_mode == "subprocess":
            if environment_port is None:
                environment_port = int(self._free_port_factory())
            base_url = os.environ.get(
                "AWARE_NODE_ENVIRONMENT_BASE_URL", "http://127.0.0.1"
            ).rstrip("/")
            environment_endpoint = f"{base_url}:{environment_port}"
        else:
            env_cfg = get_app_config(NetworkAppType.environment.value)
            if environment_port is None:
                environment_port = env_cfg.PORT
            environment_endpoint = resolve_node_environment_publication_endpoint(
                environment_port=environment_port,
                configured_base_url=getattr(env_cfg, "BASE_URL", None),
                configured_full_url=getattr(env_cfg, "full_url", None),
            )

        environment_key = _environment_key_for_config(
            node_id=node_id,
            environment_config_id=request.environment_config_id,
        )
        environment_id = _environment_id_for_config(
            node_id=node_id,
            environment_config_id=request.environment_config_id,
        )

        return EnvironmentProvisioningPlan(
            provision_mode=provision_mode,
            resolved_config=resolved_config,
            environment_key=environment_key,
            environment_id=environment_id,
            environment_title=request.environment_title,
            environment_endpoint=environment_endpoint,
            environment_port=environment_port,
            database_url=request.database_url,
            persistence_backend=request.persistence_backend,
            eager_ready=request.eager_ready,
        )


class EnvironmentProvisioningRegistry:
    """Owns local Node registry mutations for provisioning."""

    def get(self, environment_id: UUID) -> HostedEnvironmentRecord | None:
        return environment_registry.get(environment_id)

    def get_process(self, environment_id: UUID) -> object | None:
        return environment_registry.get_process(environment_id)

    def register_or_update(
        self,
        *,
        plan: EnvironmentProvisioningPlan,
        runtime_artifact_refs_json: str | None = None,
    ) -> HostedEnvironmentRecord:
        if plan.resolved_config is None:
            raise RuntimeError(
                "Node Environment registry requires resolved environment config "
                "metadata; bundle-manifest-only provisioning is retired."
            )
        config = plan.resolved_config
        record = environment_registry.get(plan.environment_id)
        workspace_updates = workspace_record_updates_from_config(config=config)
        if record is None:
            return environment_registry.register(
                environment_id=plan.environment_id,
                environment_config_id=config.environment_config_id,
                environment_config_title=config.title,
                environment_key=plan.environment_key,
                environment_title=plan.environment_title,
                environment_endpoint=plan.environment_endpoint,
                environment_port=plan.environment_port,
                ocg_hash=config.ocg_hash,
                opg_hashes=tuple(config.opg_hashes),
                status="registered",
                runtime_artifact_refs_json=runtime_artifact_refs_json,
                **workspace_updates,
            )
        return environment_registry.update(
            plan.environment_id,
            environment_key=plan.environment_key,
            environment_title=plan.environment_title,
            environment_endpoint=plan.environment_endpoint,
            environment_port=plan.environment_port,
            environment_config_id=config.environment_config_id,
            environment_config_title=config.title,
            ocg_hash=config.ocg_hash,
            opg_hashes=tuple(config.opg_hashes),
            runtime_artifact_refs_json=runtime_artifact_refs_json,
            error=None,
            **workspace_updates,
        )

    def mark_starting(
        self,
        *,
        environment_id: UUID,
        process: object,
        pid: int | None,
    ) -> HostedEnvironmentRecord:
        environment_registry.set_process(environment_id, process)
        return environment_registry.update(
            environment_id,
            pid=pid,
            status="starting",
        )

    def record_readiness(
        self,
        *,
        environment_id: UUID,
        ensure_ready: EnsureReadyResponse,
    ) -> HostedEnvironmentRecord:
        return environment_registry.update(
            environment_id,
            status="ready" if ensure_ready.status == "ready" else "failed",
            error=ensure_ready.error,
            process_id=ensure_ready.process_id,
            thread_id=ensure_ready.thread_id,
            branch_id=ensure_ready.branch_id,
            readiness_receipt=_readiness_receipt_payload(ensure_ready),
        )

    def record_network_node_environment_receipt(
        self,
        *,
        environment_id: UUID,
        receipt: JsonObject,
    ) -> HostedEnvironmentRecord:
        return environment_registry.update(
            environment_id,
            network_node_environment_receipt=dict(receipt),
        )

    def mark_failed(
        self,
        *,
        environment_id: UUID,
        error: str,
    ) -> HostedEnvironmentRecord:
        return environment_registry.update(
            environment_id,
            status="failed",
            error=error,
        )


def _readiness_receipt_payload(
    ensure_ready: EnsureReadyResponse,
) -> JsonObject | None:
    receipt = getattr(ensure_ready, "readiness_receipt", None)
    if receipt is None:
        return None
    if hasattr(receipt, "model_dump"):
        payload = receipt.model_dump(mode="json", exclude_none=True)
    elif isinstance(receipt, dict):
        payload = receipt
    else:
        return None
    if not isinstance(payload, dict):
        return None
    return JsonObject(cast(Any, payload))


class EnvironmentProcessLauncher:
    """Starts local Environment processes without owning provisioning policy."""

    def __init__(
        self,
        *,
        subprocess_factory: _SubprocessFactory = asyncio.create_subprocess_exec,
    ) -> None:
        self._subprocess_factory = subprocess_factory

    async def launch(
        self,
        *,
        plan: EnvironmentProvisioningPlan,
        node_id: UUID,
        base_env: Mapping[str, str] | None = None,
    ) -> EnvironmentProcessLaunchResult:
        process = await self._subprocess_factory(
            sys.executable,
            "-m",
            "aware_environment_service.app",
            env=build_environment_process_env(
                base_env=base_env or os.environ,
                node_id=node_id,
                environment_key=plan.environment_key,
                environment_id=plan.environment_id,
                environment_port=plan.environment_port,
                database_url=plan.database_url,
                persistence_backend=plan.persistence_backend,
            ),
        )
        return EnvironmentProcessLaunchResult(
            process=process,
            pid=getattr(process, "pid", None),
        )


class EnvironmentApiGateway:
    """Generated Environment API boundary used by Node control-plane code."""

    def __init__(
        self,
        *,
        route_to_environment_service: EnvironmentRouteHandler,
    ) -> None:
        self._route_to_environment_service = route_to_environment_service

    async def configure_service_api_dependency_routes(
        self,
        *,
        environment_id: UUID,
        node_id: UUID,
        process_id: UUID | None,
        thread_id: UUID | None,
        branch_id: UUID | None,
        routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
        timeout_s: float,
    ) -> ConfigureServiceApiDependencyRoutesResponse:
        request = ConfigureServiceApiDependencyRoutesRequest(
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=None,
            routes=cast(
                JsonArray,
                service_api_dependency_routes_to_payload(routes),
            ),
        )
        client = build_environment_service_api_client(
            route_to_environment_service=self._route_to_environment_service,
            environment_id=environment_id,
            node_id=node_id,
            actor_id=None,
            default_timeout_s=timeout_s,
        )
        env_response = await client.environment.service_routes.configure_service_api_dependency_routes(
            request
        )
        if env_response.status != "succeeded":
            raise RuntimeError(
                "ConfigureServiceApiDependencyRoutes failed: "
                f"{env_response.error or 'unknown error'}"
            )
        return env_response

    async def apply_environment_profile_mounts(
        self,
        *,
        actor_id: UUID | None,
        environment_id: UUID,
        node_id: UUID,
        process_id: UUID | None,
        thread_id: UUID | None,
        branch_id: UUID | None,
        projection_hash: str | None,
        mounts: tuple[EnvironmentProfileMountApplyPlan, ...],
        timeout_s: float,
    ) -> tuple[UpsertEnvironmentProfileResponse, ...]:
        if not mounts:
            return ()
        client = build_environment_service_api_client(
            route_to_environment_service=self._route_to_environment_service,
            environment_id=environment_id,
            node_id=node_id,
            actor_id=actor_id,
            default_timeout_s=timeout_s,
        )
        responses: list[UpsertEnvironmentProfileResponse] = []
        for mount in mounts:
            response = await client.environment.profile.upsert_environment_profile(
                UpsertEnvironmentProfileRequest(
                    actor_id=actor_id,
                    environment_id=environment_id,
                    process_id=process_id,
                    thread_id=thread_id,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    profile={
                        "key": mount.profile_key,
                        "title": mount.profile_key,
                        "description": (
                            "Node-mounted EnvironmentProfilePackage "
                            f"{mount.package_name}"
                        ),
                        "process_configs": [],
                    },
                    validate_only=False,
                )
            )
            if response.status != "succeeded":
                raise RuntimeError(
                    "UpsertEnvironmentProfile failed for Node profile mount "
                    f"{mount.mount_key!r}: {response.error or response.status}"
                )
            responses.append(response)
        return tuple(responses)

    async def ensure_ready(
        self,
        *,
        actor_id: UUID | None,
        environment_id: UUID,
        node_id: UUID,
        timeout_s: float,
    ) -> EnsureReadyResponse:
        deadline = asyncio.get_running_loop().time() + timeout_s
        last_exc: Exception | None = None
        while asyncio.get_running_loop().time() < deadline:
            try:
                request = EnsureReadyRequest(
                    actor_id=actor_id,
                    environment_id=environment_id,
                    process_id=None,
                    thread_id=None,
                    branch_id=None,
                    projection_hash=None,
                )
                remaining_s = max(1.0, deadline - asyncio.get_running_loop().time())
                client = build_environment_service_api_client(
                    route_to_environment_service=self._route_to_environment_service,
                    environment_id=environment_id,
                    node_id=node_id,
                    actor_id=actor_id,
                    default_timeout_s=remaining_s,
                )
                return await client.environment.ready.ensure_ready(request)
            except Exception as exc:
                last_exc = exc
                await asyncio.sleep(0.25)
        raise RuntimeError(
            f"Environment did not become ready within {timeout_s}s: {last_exc}"
        )


__all__ = [
    "EnvironmentApiGateway",
    "EnvironmentProcessLaunchResult",
    "EnvironmentProcessLauncher",
    "EnvironmentProvisioningPlan",
    "EnvironmentProvisioningPlanner",
    "EnvironmentProvisioningRegistry",
    "build_environment_process_env",
    "workspace_record_updates_from_config",
]
