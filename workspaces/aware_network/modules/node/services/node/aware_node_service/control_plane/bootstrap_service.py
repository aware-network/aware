from __future__ import annotations

import os
from uuid import UUID

from aware_network_service_dto.comms.models.network import NetworkAppType
from aware_network.communications.app_config import (
    get_network_app_config as get_app_config,
)
from aware_utils.logging import logger

from aware_node_service.control_plane.actor_authority import (
    resolve_node_system_actor_id,
)
from aware_node_service.control_plane.environment_host_support import (
    EnvironmentRouteHandler,
    _select_kernel_environment_config,
)
from aware_node_service.control_plane.environment_endpoint import (
    resolve_node_environment_publication_endpoint,
)
from aware_node_service.control_plane.hosted_environment_service import (
    NetworkNodeHostedEnvironmentService,
)
from aware_node_service.control_plane.topology_bootstrap_service import (
    NetworkNodeTopologyBootstrapService,
)


def _system_actor_id() -> UUID:
    return resolve_node_system_actor_id()


def _has_local_environment_config_runtime_input(
    hosted_environment_service: object,
) -> bool:
    has_runtime_input = getattr(
        hosted_environment_service,
        "has_local_environment_config_runtime_input",
        None,
    )
    if not callable(has_runtime_input):
        return False
    return bool(has_runtime_input())


class NetworkNodeBootstrapService:
    def __init__(
        self,
        *,
        route_to_environment_service: EnvironmentRouteHandler,
        hosted_environment_service: NetworkNodeHostedEnvironmentService | None = None,
        topology_bootstrap_service: NetworkNodeTopologyBootstrapService | None = None,
    ):
        self._hosted_environment_service = hosted_environment_service or (
            NetworkNodeHostedEnvironmentService(
                route_to_environment_service=route_to_environment_service
            )
        )
        self._topology_bootstrap_service = topology_bootstrap_service or (
            NetworkNodeTopologyBootstrapService(
                route_to_environment_service=route_to_environment_service
            )
        )

    async def bootstrap_kernel_environment(self) -> None:
        """Ensure the kernel environment is registered and ready on node boot."""

        boot_raw = (os.environ.get("AWARE_NODE_BOOT_KERNEL") or "1").strip().lower()
        if boot_raw in {"0", "false", "no"}:
            logger.info("Kernel boot disabled (AWARE_NODE_BOOT_KERNEL=%s)", boot_raw)
            return

        from aware_network.network.node.manager import network_node_manager

        node_id = network_node_manager.hosted_node_id
        if not _has_local_environment_config_runtime_input(
            self._hosted_environment_service
        ):
            logger.info(
                "No local EnvironmentConfig runtime input; skipping kernel boot"
            )
            return

        configs = self._hosted_environment_service.discover_environment_config_records()
        if not configs:
            logger.warning(
                "No environment configs discovered; skipping kernel boot (env=AWARE_NODE_ENVIRONMENT_CONFIG_MANIFESTS)"
            )
            return

        kernel_cfg = _select_kernel_environment_config(configs)

        env_cfg = get_app_config(NetworkAppType.environment.value)
        provision_mode = (
            os.environ.get("AWARE_NODE_PROVISION_MODE", "register_only").strip().lower()
        )
        if provision_mode == "subprocess":
            from aware_node_service_dto.node.host import ProvisionEnvironmentRequest

            logger.info(
                "Provisioning kernel environment subprocess "
                "(environment_config_id=%s environment_port=%s)",
                kernel_cfg.environment_config_id,
                env_cfg.PORT,
            )
            record = await self._hosted_environment_service.provision_environment(
                request=ProvisionEnvironmentRequest(
                    actor_id=_system_actor_id(),
                    node_id=node_id,
                    environment_config_id=kernel_cfg.environment_config_id,
                    environment_title=kernel_cfg.title,
                    environment_port=env_cfg.PORT,
                    eager_ready=True,
                ),
                node_id=node_id,
            )
            if record.status != "ready":
                raise RuntimeError(
                    "Kernel environment subprocess provisioning failed: "
                    f"{record.error or record.status}"
                )
            if record.process_id is None or record.thread_id is None:
                raise RuntimeError(
                    "Kernel environment subprocess provisioning returned ready "
                    "without process/thread ids."
                )
            logger.info(
                "Kernel environment boot complete (environment_id=%s process_id=%s thread_id=%s branch_id=%s)",
                record.environment_id,
                record.process_id,
                record.thread_id,
                record.branch_id,
            )
            try:
                await self._topology_bootstrap_service.bootstrap_network_topology(
                    actor_id=_system_actor_id(),
                    environment_id=record.environment_id,
                    process_id=record.process_id,
                    thread_id=record.thread_id,
                )
            except Exception as exc:
                logger.warning("Network topology bootstrap failed: %s", exc)
            return

        record = self._hosted_environment_service.register_environment_from_config(
            node_id=node_id,
            config=kernel_cfg,
            environment_endpoint=resolve_node_environment_publication_endpoint(
                environment_port=env_cfg.PORT,
                configured_base_url=getattr(env_cfg, "BASE_URL", None),
                configured_full_url=getattr(env_cfg, "full_url", None),
            ),
            environment_port=env_cfg.PORT,
        )

        if record.status == "ready":
            logger.info(
                "Kernel environment registry says ready; verifying via ensure_ready "
                "(environment_id=%s environment_config_id=%s)",
                record.environment_id,
                record.environment_config_id,
            )

        ready_timeout_s = float(
            os.environ.get("AWARE_NODE_KERNEL_READY_TIMEOUT_S", "120.0")
        )
        logger.info(
            "Bootstrapping kernel environment (environment_id=%s environment_config_id=%s timeout_s=%s)",
            record.environment_id,
            record.environment_config_id,
            ready_timeout_s,
        )
        ensure_ready = await self._hosted_environment_service.ensure_environment_ready(
            actor_id=_system_actor_id(),
            environment_id=record.environment_id,
            node_id=node_id,
            timeout_s=ready_timeout_s,
        )
        record = (
            self._hosted_environment_service.record_environment_ensure_ready_result(
                environment_id=record.environment_id,
                ensure_ready=ensure_ready,
            )
        )
        if ensure_ready.status != "ready":
            raise RuntimeError(f"Kernel ensure_ready failed: {record.error}")
        logger.info(
            "Kernel environment boot complete (environment_id=%s process_id=%s thread_id=%s branch_id=%s)",
            record.environment_id,
            ensure_ready.process_id,
            ensure_ready.thread_id,
            ensure_ready.branch_id,
        )

        try:
            await self._topology_bootstrap_service.bootstrap_network_topology(
                actor_id=_system_actor_id(),
                environment_id=record.environment_id,
                process_id=ensure_ready.process_id,
                thread_id=ensure_ready.thread_id,
            )
        except Exception as exc:
            logger.warning("Network topology bootstrap failed: %s", exc)


__all__ = ["NetworkNodeBootstrapService"]
