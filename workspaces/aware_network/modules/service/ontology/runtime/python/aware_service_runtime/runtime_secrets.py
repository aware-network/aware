from __future__ import annotations

import os
from pathlib import Path

from aware_utils.secrets import resolve_secret, use_secrets_dir

from aware_service_runtime.manifest.spec import AwareServiceTomlRuntimeSpec


class ServiceRuntimeSecretError(RuntimeError):
    pass


def configure_service_runtime_secrets(
    runtime: AwareServiceTomlRuntimeSpec,
) -> Path | None:
    secrets_dir: str | None = None
    env_name = (runtime.secrets_dir_env or "").strip()
    if env_name:
        secrets_dir = (os.getenv(env_name) or "").strip() or None
    if secrets_dir is None:
        secrets_dir = (runtime.canonical_secrets_dir or "").strip() or None
    if secrets_dir is None:
        return None

    resolved = Path(secrets_dir).expanduser().resolve()
    use_secrets_dir(resolved)
    return resolved


def resolve_service_runtime_value(name: str) -> str | None:
    normalized_name = name.strip()
    if not normalized_name:
        raise ServiceRuntimeSecretError("Service runtime value name is required")
    return resolve_secret(normalized_name)


def require_service_runtime_value(name: str) -> str:
    normalized_name = name.strip()
    value = resolve_service_runtime_value(normalized_name)
    if value is None:
        raise ServiceRuntimeSecretError(
            f"Required Service runtime value is unavailable: {normalized_name}"
        )
    return value


def require_service_runtime_secret(name: str) -> str:
    return require_service_runtime_value(name)


__all__ = [
    "ServiceRuntimeSecretError",
    "configure_service_runtime_secrets",
    "require_service_runtime_secret",
    "require_service_runtime_value",
    "resolve_service_runtime_value",
]
