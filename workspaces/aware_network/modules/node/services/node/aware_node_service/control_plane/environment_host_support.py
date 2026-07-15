from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol, Sequence
from uuid import UUID

from aware_network_service_dto.comms.models.network import NetworkOperation
from aware_environment.environment.identity import (
    environment_id_for_config,
    environment_key_for_config,
)
from aware_node_service.control_plane.environment_config_registry import (
    EnvironmentConfigRecord,
)

_LOCAL_ENVIRONMENT_CONFIG_INPUT_ENABLED_ENV = (
    "AWARE_NODE_LOCAL_ENVIRONMENT_CONFIG_INPUT_ENABLED"
)


class EnvironmentRouteHandler(Protocol):
    async def __call__(
        self,
        network_op: NetworkOperation,
        *,
        timeout_s: float | None = None,
    ) -> NetworkOperation | None: ...


def _resolve_environment_config_root() -> Path:
    """Resolve where the node should discover environment config manifests from.

    `AWARE_ROOT` is a persistence root (PV). Environment config discovery should use
    explicit deployment config input, not repo/cwd discovery.
    """

    raw = os.environ.get("AWARE_NODE_ENVIRONMENT_CONFIG_ROOT")
    if raw is not None and raw.strip():
        return Path(raw).expanduser().resolve()
    if _environment_config_inputs_are_absolute():
        return Path("/")
    raise RuntimeError(
        "Environment config discovery requires AWARE_NODE_ENVIRONMENT_CONFIG_ROOT "
        "or absolute AWARE_NODE_ENVIRONMENT_CONFIG_MANIFESTS/"
        "AWARE_NODE_ENVIRONMENT_CONFIG_MANIFEST_GLOBS. "
        "Repo/cwd fallback is disabled for Node deploy readiness."
    )


def _environment_config_inputs_are_absolute() -> bool:
    for env_name in (
        "AWARE_NODE_ENVIRONMENT_CONFIG_MANIFESTS",
        "AWARE_NODE_ENVIRONMENT_CONFIG_MANIFEST_GLOBS",
    ):
        raw = os.environ.get(env_name)
        if raw is None or not raw.strip():
            continue
        values = [item.strip() for item in raw.split(",") if item.strip()]
        if values and all(Path(value).expanduser().is_absolute() for value in values):
            return True
    return False


def environment_config_discovery_configured() -> bool:
    raw = os.environ.get(_LOCAL_ENVIRONMENT_CONFIG_INPUT_ENABLED_ENV)
    if raw is None:
        return False
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise RuntimeError(
        f"{_LOCAL_ENVIRONMENT_CONFIG_INPUT_ENABLED_ENV} must be a boolean value."
    )


def _environment_id_for_config(*, node_id: UUID, environment_config_id: UUID) -> UUID:
    """Deterministic environment_id for config-only provisioning."""

    return environment_id_for_config(
        node_id=node_id,
        environment_config_id=environment_config_id,
    )


def _environment_key_for_config(*, node_id: UUID, environment_config_id: UUID) -> str:
    """Deterministic Environment Environment key for config-only provisioning."""

    return environment_key_for_config(
        node_id=node_id,
        environment_config_id=environment_config_id,
    )


def _select_kernel_environment_config(
    configs: Sequence[EnvironmentConfigRecord],
) -> EnvironmentConfigRecord:
    kernel_cfg_raw = (
        os.environ.get("AWARE_NODE_KERNEL_ENVIRONMENT_CONFIG_ID") or ""
    ).strip()
    kernel_cfg_id: UUID | None = None
    if kernel_cfg_raw:
        kernel_cfg_id = UUID(kernel_cfg_raw)

    if kernel_cfg_id is not None:
        kernel_cfg = next(
            (c for c in configs if c.environment_config_id == kernel_cfg_id), None
        )
        if kernel_cfg is None:
            raise RuntimeError(
                "AWARE_NODE_KERNEL_ENVIRONMENT_CONFIG_ID does not match any discovered config "
                f"(kernel={kernel_cfg_id} discovered={[str(c.environment_config_id) for c in configs]})"
            )
        return kernel_cfg

    if len(configs) == 1:
        return configs[0]

    raise RuntimeError(
        "Multiple environment configs discovered; set AWARE_NODE_KERNEL_ENVIRONMENT_CONFIG_ID "
        f"(discovered={[str(c.environment_config_id) for c in configs]})"
    )


__all__ = [
    "EnvironmentRouteHandler",
    "_environment_id_for_config",
    "_environment_key_for_config",
    "environment_config_discovery_configured",
    "_resolve_environment_config_root",
    "_select_kernel_environment_config",
]
