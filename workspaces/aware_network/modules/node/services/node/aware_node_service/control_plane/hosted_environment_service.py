from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    ConfigureServiceApiDependencyRoutesResponse,
    EnsureReadyResponse,
)
from aware_network_service_dto.comms.models.network import (
    NetworkRequestStatus,
)
from aware_node_service_dto.node.host import BootEnvironmentDescriptor
from aware_node_service_dto.node.host import EnvironmentConfigDescriptor
from aware_node_service_dto.node.host import ProvisionEnvironmentRequest
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)

from aware_node_service.control_plane.environment_config_registry import (
    EnvironmentConfigRecord,
    discover_environment_configs,
)
from aware_node_service.control_plane.environment_host_support import (
    EnvironmentRouteHandler,
    environment_config_discovery_configured,
    _environment_id_for_config,
    _environment_key_for_config,
    _resolve_environment_config_root,
    _select_kernel_environment_config,
)
from aware_node_service.control_plane.environment_provisioning import (
    EnvironmentApiGateway,
    EnvironmentProcessLauncher,
    EnvironmentProvisioningPlan,
    EnvironmentProvisioningPlanner,
    EnvironmentProvisioningRegistry,
    build_environment_process_env,
    workspace_record_updates_from_config as _workspace_record_updates_from_config,
)
from aware_node_service.control_plane.environment_profile_mounts import (
    profile_mount_apply_plans_from_runtime_artifact_refs_json,
)
from aware_node_service.control_plane.environment_registry import (
    HostedEnvironmentRecord,
    environment_registry,
)
from aware_node_service.control_plane.network_environment_association import (
    NetworkNodeEnvironmentAssociationService,
)
from aware_utils.logging import logger


_ENVIRONMENT_PORT_READY_TIMEOUT_S_ENV = "AWARE_NODE_ENVIRONMENT_PORT_READY_TIMEOUT_S"
_ENVIRONMENT_PORT_READY_POLL_INTERVAL_S_ENV = (
    "AWARE_NODE_ENVIRONMENT_PORT_READY_POLL_INTERVAL_S"
)
_ENVIRONMENT_READY_POLL_INTERVAL_S_ENV = "AWARE_NODE_ENVIRONMENT_READY_POLL_INTERVAL_S"
_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_JSON_ENV = (
    "AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_JSON"
)
_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_PATH_ENV = (
    "AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_PATH"
)


@dataclass(frozen=True)
class BootEnvironmentDescriptorReadResult:
    network_status: NetworkRequestStatus
    response_status: str
    network_error: str | None = None
    response_error: str | None = None
    descriptor: BootEnvironmentDescriptor | None = None


def _build_environment_process_env(
    *,
    base_env: dict[str, str],
    node_id: UUID,
    environment_key: str,
    environment_id: UUID,
    environment_port: int | None,
    database_url: str | None,
    persistence_backend: str | None,
) -> dict[str, str]:
    return build_environment_process_env(
        base_env=base_env,
        node_id=node_id,
        environment_key=environment_key,
        environment_id=environment_id,
        environment_port=environment_port,
        database_url=database_url,
        persistence_backend=persistence_backend,
    )


def _float_env(name: str, *, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _host_from_environment_endpoint(endpoint: str | None) -> str:
    if not endpoint:
        return "127.0.0.1"
    parsed = urlparse(endpoint)
    if parsed.hostname:
        return parsed.hostname
    return "127.0.0.1"


def _read_existing_environment_record(
    registry: object,
    *,
    environment_id: UUID,
) -> HostedEnvironmentRecord | None:
    reader = getattr(registry, "get", None)
    if not callable(reader):
        return None
    record = reader(environment_id)
    if record is None or isinstance(record, HostedEnvironmentRecord):
        return record
    return None


def _existing_environment_process_is_live(
    registry: object,
    *,
    record: HostedEnvironmentRecord | None,
) -> bool:
    if record is None:
        return False
    process_reader = getattr(registry, "get_process", None)
    if not callable(process_reader):
        return False
    process = process_reader(record.environment_id)
    if process is None:
        return False
    return getattr(process, "returncode", None) is None


def _runtime_artifact_refs_json_from_env() -> str | None:
    raw_json = (
        os.environ.get(_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_JSON_ENV) or ""
    ).strip()
    if raw_json:
        return raw_json
    raw_path = (
        os.environ.get(_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_PATH_ENV) or ""
    ).strip()
    if not raw_path:
        return None
    return Path(raw_path).expanduser().read_text(encoding="utf-8").strip()


def _profile_mount_environment_handle(plan: EnvironmentProvisioningPlan) -> str:
    resolved_handle = (
        getattr(plan.resolved_config, "environment_handle", None)
        if plan.resolved_config is not None
        else None
    )
    handle = str(resolved_handle or "").strip()
    return handle or plan.environment_key


async def _wait_for_environment_api_port(
    *,
    environment_endpoint: str | None,
    environment_port: int | None,
    timeout_s: float,
) -> None:
    if environment_port is None or timeout_s <= 0:
        return

    host = _host_from_environment_endpoint(environment_endpoint)
    poll_interval_s = max(
        0.05,
        _float_env(_ENVIRONMENT_PORT_READY_POLL_INTERVAL_S_ENV, default=0.25),
    )
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    last_exc: BaseException | None = None
    logger.info(
        "Waiting for Environment API TCP endpoint before ensure_ready "
        "(host=%s port=%s timeout_s=%.2f)",
        host,
        environment_port,
        timeout_s,
    )

    while True:
        remaining_s = deadline - loop.time()
        if remaining_s <= 0:
            break
        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, environment_port),
                timeout=min(1.0, remaining_s),
            )
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
            logger.info(
                "Environment API TCP endpoint reachable " "(host=%s port=%s)",
                host,
                environment_port,
            )
            return
        except (OSError, asyncio.TimeoutError) as exc:
            last_exc = exc
            await asyncio.sleep(min(poll_interval_s, max(0.0, deadline - loop.time())))

    raise RuntimeError(
        "Environment API TCP endpoint did not become reachable before "
        f"ensure_ready (host={host} port={environment_port} "
        f"timeout_s={timeout_s:.2f})"
    ) from last_exc


class NetworkNodeHostedEnvironmentService:
    def __init__(
        self,
        *,
        route_to_environment_service: EnvironmentRouteHandler,
        provisioning_planner: EnvironmentProvisioningPlanner | None = None,
        provisioning_registry: EnvironmentProvisioningRegistry | None = None,
        process_launcher: EnvironmentProcessLauncher | None = None,
        environment_api: EnvironmentApiGateway | None = None,
        network_association: NetworkNodeEnvironmentAssociationService | None = None,
    ) -> None:
        self._provisioning_planner = (
            provisioning_planner or EnvironmentProvisioningPlanner()
        )
        self._provisioning_registry = (
            provisioning_registry or EnvironmentProvisioningRegistry()
        )
        self._process_launcher = process_launcher or EnvironmentProcessLauncher()
        self._environment_api = environment_api or EnvironmentApiGateway(
            route_to_environment_service=route_to_environment_service
        )
        self._network_association = (
            network_association
            or NetworkNodeEnvironmentAssociationService(
                route_to_environment_service=route_to_environment_service
            )
        )

    def has_local_environment_config_runtime_input(self) -> bool:
        return environment_config_discovery_configured()

    def has_configured_environment_discovery(self) -> bool:
        return self.has_local_environment_config_runtime_input()

    def discover_environment_config_records(self) -> list[EnvironmentConfigRecord]:
        config_root = _resolve_environment_config_root()
        return discover_environment_configs(aware_root=config_root)

    def list_environment_config_descriptors(self) -> list[EnvironmentConfigDescriptor]:
        return [
            EnvironmentConfigDescriptor(
                environment_config_id=cfg.environment_config_id,
                title=cfg.title,
                canonical_language=cfg.canonical_language,
                ocg_hash=cfg.ocg_hash,
                opg_hashes=list(cfg.opg_hashes),
                outer_wrapper_kind=cfg.outer_wrapper_kind,
                environment_handle=cfg.environment_handle,
                workspace_target_ref=cfg.workspace_target_ref,
            )
            for cfg in self.discover_environment_config_records()
        ]

    def read_boot_environment_descriptor(
        self, *, node_id: UUID
    ) -> BootEnvironmentDescriptorReadResult:
        configs = self.discover_environment_config_records()
        if not configs:
            error = "No environment configs discovered"
            return BootEnvironmentDescriptorReadResult(
                network_status=NetworkRequestStatus.failed,
                response_status="failed",
                network_error=error,
                response_error=error,
            )

        try:
            kernel_cfg = _select_kernel_environment_config(configs)
        except RuntimeError as exc:
            error = str(exc)
            return BootEnvironmentDescriptorReadResult(
                network_status=NetworkRequestStatus.failed,
                response_status="failed",
                network_error=error,
                response_error=error,
            )

        environment_id = _environment_id_for_config(
            node_id=node_id,
            environment_config_id=kernel_cfg.environment_config_id,
        )
        record = environment_registry.get(environment_id)
        if record is None:
            return BootEnvironmentDescriptorReadResult(
                network_status=NetworkRequestStatus.succeeded,
                response_status="not_found",
                response_error="Boot environment is not registered on this node",
            )

        descriptor = BootEnvironmentDescriptor(
            kernel_environment_config_id=kernel_cfg.environment_config_id,
            boot_environment_id=environment_id,
            kernel_environment_config_title=kernel_cfg.title,
            boot_environment_title=record.environment_title or kernel_cfg.title,
            process_id=record.process_id,
            thread_id=record.thread_id,
            branch_id=record.branch_id,
            opg_hashes=list(record.opg_hashes),
        )
        return BootEnvironmentDescriptorReadResult(
            network_status=NetworkRequestStatus.succeeded,
            response_status=record.status,
            response_error=record.error,
            descriptor=descriptor,
        )

    def read_environment_record(
        self, environment_id: UUID
    ) -> HostedEnvironmentRecord | None:
        return environment_registry.get(environment_id)

    def register_environment_from_config(
        self,
        *,
        node_id: UUID,
        config: EnvironmentConfigRecord,
        environment_endpoint: str | None,
        environment_port: int | None,
    ) -> HostedEnvironmentRecord:
        environment_id = _environment_id_for_config(
            node_id=node_id,
            environment_config_id=config.environment_config_id,
        )
        environment_key = _environment_key_for_config(
            node_id=node_id,
            environment_config_id=config.environment_config_id,
        )

        existing = environment_registry.get(environment_id)
        if existing is None:
            return environment_registry.register(
                environment_id=environment_id,
                environment_config_id=config.environment_config_id,
                environment_config_title=config.title,
                environment_key=environment_key,
                environment_title=config.title,
                environment_endpoint=environment_endpoint,
                environment_port=environment_port,
                ocg_hash=config.ocg_hash,
                opg_hashes=tuple(config.opg_hashes),
                status="registered",
                **_workspace_record_updates_from_config(config=config),
            )

        next_status = existing.status if existing.status == "ready" else "registered"
        return environment_registry.register(
            environment_title=config.title,
            status=next_status,
            error=None if next_status == "registered" else existing.error,
            environment_id=environment_id,
            environment_config_id=config.environment_config_id,
            environment_config_title=config.title,
            environment_key=environment_key,
            environment_endpoint=environment_endpoint,
            environment_port=environment_port,
            ocg_hash=config.ocg_hash,
            opg_hashes=tuple(config.opg_hashes),
            process_id=existing.process_id,
            thread_id=existing.thread_id,
            branch_id=existing.branch_id,
            readiness_receipt=existing.readiness_receipt,
            network_node_environment_receipt=existing.network_node_environment_receipt,
            pid=existing.pid,
            **_workspace_record_updates_from_config(config=config),
        )

    def record_environment_ensure_ready_result(
        self,
        *,
        environment_id: UUID,
        ensure_ready: EnsureReadyResponse,
    ) -> HostedEnvironmentRecord:
        return self._provisioning_registry.record_readiness(
            environment_id=environment_id,
            ensure_ready=ensure_ready,
        )

    async def provision_environment(
        self,
        *,
        request: ProvisionEnvironmentRequest,
        node_id: UUID,
    ) -> HostedEnvironmentRecord:
        provision_mode = (
            os.environ.get("AWARE_NODE_PROVISION_MODE", "register_only").strip().lower()
        )
        plan = self._provisioning_planner.plan(
            request=request,
            node_id=node_id,
            provision_mode=provision_mode,
        )
        runtime_artifact_refs_json = _runtime_artifact_refs_json_from_env()
        existing_record = _read_existing_environment_record(
            self._provisioning_registry,
            environment_id=plan.environment_id,
        )
        reuse_existing_process = (
            provision_mode == "subprocess"
            and _existing_environment_process_is_live(
                self._provisioning_registry,
                record=existing_record,
            )
        )
        if reuse_existing_process:
            logger.info(
                "Reusing live hosted Environment process for provision request "
                "(environment_id=%s endpoint=%s pid=%s)",
                existing_record.environment_id if existing_record is not None else None,
                (
                    existing_record.environment_endpoint
                    if existing_record is not None
                    else None
                ),
                existing_record.pid if existing_record is not None else None,
            )
            record = existing_record
        else:
            record = self._provisioning_registry.register_or_update(
                plan=plan,
                runtime_artifact_refs_json=runtime_artifact_refs_json,
            )

        if provision_mode == "subprocess" and not reuse_existing_process:
            launch_result = await self._process_launcher.launch(
                plan=plan,
                node_id=node_id,
                base_env=os.environ,
            )
            record = self._provisioning_registry.mark_starting(
                environment_id=record.environment_id,
                process=launch_result.process,
                pid=launch_result.pid,
            )

        if plan.eager_ready:
            try:
                ready_timeout_s = float(
                    os.environ.get("AWARE_NODE_ENVIRONMENT_READY_TIMEOUT_S", "60.0")
                )
                if provision_mode == "subprocess":
                    await _wait_for_environment_api_port(
                        environment_endpoint=record.environment_endpoint,
                        environment_port=record.environment_port,
                        timeout_s=_float_env(
                            _ENVIRONMENT_PORT_READY_TIMEOUT_S_ENV,
                            default=ready_timeout_s,
                        ),
                    )
                ensure_ready = await self._ensure_environment_ready_until_ready(
                    actor_id=request.actor_id,
                    environment_id=record.environment_id,
                    node_id=node_id,
                    timeout_s=ready_timeout_s,
                )
                record = self.record_environment_ensure_ready_result(
                    environment_id=record.environment_id,
                    ensure_ready=ensure_ready,
                )
                if record.status == "ready":
                    profile_mounts = (
                        profile_mount_apply_plans_from_runtime_artifact_refs_json(
                            artifact_refs_json=runtime_artifact_refs_json,
                            environment_handle=_profile_mount_environment_handle(plan),
                        )
                    )
                    if profile_mounts:
                        await self._environment_api.apply_environment_profile_mounts(
                            actor_id=request.actor_id,
                            environment_id=record.environment_id,
                            node_id=node_id,
                            process_id=record.process_id,
                            thread_id=record.thread_id,
                            branch_id=record.branch_id,
                            projection_hash=ensure_ready.projection_hash,
                            mounts=profile_mounts,
                            timeout_s=ready_timeout_s,
                        )
                    record_network_receipt = (
                        self._provisioning_registry.record_network_node_environment_receipt
                    )
                    assoc_receipt = (
                        await self._network_association.ensure_node_environment(
                            actor_id=request.actor_id,
                            environment_id=record.environment_id,
                            node_id=node_id,
                            process_id=record.process_id,
                            thread_id=record.thread_id,
                        )
                    )
                    record = record_network_receipt(
                        environment_id=record.environment_id,
                        receipt=assoc_receipt,
                    )
            except Exception as exc:
                record = self._provisioning_registry.mark_failed(
                    environment_id=record.environment_id,
                    error=str(exc),
                )

        return record

    async def _ensure_environment_ready_until_ready(
        self,
        *,
        actor_id: UUID | None,
        environment_id: UUID,
        node_id: UUID,
        timeout_s: float,
    ) -> EnsureReadyResponse:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(timeout_s, 0.0)
        poll_interval_s = _float_env(
            _ENVIRONMENT_READY_POLL_INTERVAL_S_ENV,
            default=1.0,
        )
        attempt = 0
        while True:
            attempt += 1
            response = await self.ensure_environment_ready(
                actor_id=actor_id,
                environment_id=environment_id,
                node_id=node_id,
                timeout_s=timeout_s,
            )
            if str(response.status).strip().lower() == "ready":
                return response
            remaining_s = deadline - loop.time()
            if remaining_s <= 0:
                return response
            sleep_s = min(max(poll_interval_s, 0.0), remaining_s)
            logger.info(
                "Hosted Environment ensure_ready not ready; retrying "
                "(environment_id=%s status=%s error=%s attempt=%s sleep_s=%.2f)",
                environment_id,
                response.status,
                response.error,
                attempt,
                sleep_s,
            )
            await asyncio.sleep(sleep_s)

    async def configure_service_api_dependency_routes(
        self,
        *,
        environment_id: UUID,
        node_id: UUID,
        routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
        timeout_s: float,
    ) -> ConfigureServiceApiDependencyRoutesResponse:
        record = environment_registry.get(environment_id)
        if record is None:
            raise RuntimeError(
                "Cannot configure service API dependency routes for unknown "
                f"environment_id={environment_id}"
            )
        return await self._environment_api.configure_service_api_dependency_routes(
            environment_id=environment_id,
            node_id=node_id,
            process_id=record.process_id,
            thread_id=record.thread_id,
            branch_id=record.branch_id,
            routes=routes,
            timeout_s=timeout_s,
        )

    async def ensure_environment_ready(
        self,
        *,
        actor_id: UUID | None,
        environment_id: UUID,
        node_id: UUID,
        timeout_s: float,
    ) -> EnsureReadyResponse:
        return await self._environment_api.ensure_ready(
            actor_id=actor_id,
            environment_id=environment_id,
            node_id=node_id,
            timeout_s=timeout_s,
        )


__all__ = [
    "BootEnvironmentDescriptorReadResult",
    "NetworkNodeHostedEnvironmentService",
]
