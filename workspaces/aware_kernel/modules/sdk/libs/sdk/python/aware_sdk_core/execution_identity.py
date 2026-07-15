from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


DEFAULT_PROVIDER_KEY = "codex"
DEFAULT_EXECUTION_ROLE = "worker"
CODEX_THREAD_ID_ENV = "CODEX_THREAD_ID"


class ProviderExecutionIdentityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderExecutionIdentity:
    provider_key: str
    provider_session_id: str
    execution_id: str
    role: str = DEFAULT_EXECUTION_ROLE

    def to_payload(self) -> dict[str, str]:
        return {
            "provider_key": self.provider_key,
            "provider_session_id": self.provider_session_id,
            "execution_id": self.execution_id,
            "role": self.role,
        }


def resolve_provider_execution_identity(
    *,
    provider_key: str | None = DEFAULT_PROVIDER_KEY,
    provider_session_id: str | None = None,
    role: str = DEFAULT_EXECUTION_ROLE,
    env: Mapping[str, str] | None = None,
) -> ProviderExecutionIdentity:
    normalized_provider = normalize_provider_key(provider_key or DEFAULT_PROVIDER_KEY)
    normalized_role = normalize_execution_role(role)
    resolved_session_id = provider_session_id
    source_env = env if env is not None else os.environ
    if not resolved_session_id and normalized_provider == "codex":
        resolved_session_id = source_env.get(CODEX_THREAD_ID_ENV)
    if not resolved_session_id:
        raise ProviderExecutionIdentityError(
            "Provider execution identity requires a provider session id. "
            f"For Codex, set {CODEX_THREAD_ID_ENV} or pass provider_session_id."
        )
    raw_session_id = strip_provider_prefix(
        provider_key=normalized_provider,
        provider_session_id=resolved_session_id,
    )
    if not raw_session_id:
        raise ProviderExecutionIdentityError(
            "Provider execution identity requires a non-empty provider session id."
        )
    execution_id = f"{normalized_provider}-{raw_session_id}"
    return ProviderExecutionIdentity(
        provider_key=normalized_provider,
        provider_session_id=raw_session_id,
        execution_id=execution_id,
        role=normalized_role,
    )


def try_resolve_provider_execution_identity(
    *,
    provider_key: str | None = DEFAULT_PROVIDER_KEY,
    provider_session_id: str | None = None,
    role: str = DEFAULT_EXECUTION_ROLE,
    env: Mapping[str, str] | None = None,
) -> ProviderExecutionIdentity | None:
    try:
        return resolve_provider_execution_identity(
            provider_key=provider_key,
            provider_session_id=provider_session_id,
            role=role,
            env=env,
        )
    except ProviderExecutionIdentityError:
        return None


def local_sdk_actor_ref(identity: ProviderExecutionIdentity) -> str:
    return identity.execution_id


def normalize_provider_key(value: str) -> str:
    normalized = "_".join(value.strip().lower().replace("-", "_").split())
    if not normalized:
        raise ProviderExecutionIdentityError("provider_key is required.")
    return normalized


def normalize_execution_role(value: str) -> str:
    normalized = "_".join(value.strip().lower().replace("-", "_").split())
    if not normalized:
        raise ProviderExecutionIdentityError("role is required.")
    return normalized


def strip_provider_prefix(*, provider_key: str, provider_session_id: str) -> str:
    normalized = provider_session_id.strip()
    prefix = f"{provider_key}-"
    if normalized.startswith(prefix):
        return normalized[len(prefix) :]
    return normalized


__all__ = [
    "CODEX_THREAD_ID_ENV",
    "DEFAULT_EXECUTION_ROLE",
    "DEFAULT_PROVIDER_KEY",
    "ProviderExecutionIdentity",
    "ProviderExecutionIdentityError",
    "local_sdk_actor_ref",
    "normalize_execution_role",
    "normalize_provider_key",
    "resolve_provider_execution_identity",
    "strip_provider_prefix",
    "try_resolve_provider_execution_identity",
]
