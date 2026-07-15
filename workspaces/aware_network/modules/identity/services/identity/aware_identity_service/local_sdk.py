from __future__ import annotations

"""Service-owned local Identity SDK helpers for monorepo execution identity."""

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_identity_ontology_dto.stable_ids import (
    stable_actor_id as _stable_actor_id,
)
from aware_identity_ontology_dto.stable_ids import (
    stable_identity_id as _stable_identity_id,
)
from aware_identity_ontology_dto.stable_ids import (
    stable_identity_profile_id as _stable_identity_profile_id,
)
from aware_identity_service_dto.identity.models import IdentityAdmissionReceipt
from aware_identity_service_dto.identity.admission import (
    IdentitySignupViaProfileRequest,
)
from aware_identity_service_dto.profile.requests import IdentityType

from aware_identity_sdk.client import (
    DEFAULT_IDENTITY_SDK_SOURCE,
    IdentityAdmission,
    IdentityAdmissionProfile,
    IdentityGateSnapshot,
    IdentitySdkClient,
    IdentitySdkError,
)


LOCAL_IDENTITY_STATE_VERSION = 1
LOCAL_IDENTITY_NAMESPACE = "monorepo"
LOCAL_IDENTITY_PROVIDER_KEY = "codex"
LOCAL_IDENTITY_ACTOR_KEY = "default"
LOCAL_IDENTITY_COUNTRY_CODE = "US"
LOCAL_IDENTITY_LANGUAGE_CODE = "en"


@dataclass(frozen=True, slots=True)
class LocalIdentityExecutionIdentity:
    provider_key: str
    provider_session_id: str
    execution_id: str

    def to_payload(self) -> dict[str, str]:
        return {
            "provider_key": self.provider_key,
            "provider_session_id": self.provider_session_id,
            "execution_id": self.execution_id,
        }


@dataclass(frozen=True, slots=True)
class LocalIdentityAdmissionResult:
    execution_identity: LocalIdentityExecutionIdentity
    identity_key: str
    actor_key: str
    public_key: str
    admission: IdentityAdmission
    gate: IdentityGateSnapshot
    state_path: Path | None = None

    @property
    def owner_execution_id(self) -> str:
        return self.execution_identity.execution_id

    @property
    def identity_id(self) -> UUID | None:
        return self.admission.identity_id

    @property
    def actor_id(self) -> UUID | None:
        return self.admission.actor_id

    @property
    def identity_profile_id(self) -> UUID | None:
        return self.admission.identity_profile_id

    @property
    def public_handle(self) -> str | None:
        return self.admission.public_handle

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": "local_identity_ready",
            "execution_identity": self.execution_identity.to_payload(),
            "identity_key": self.identity_key,
            "actor_key": self.actor_key,
            "public_key": self.public_key,
            "identity_id": _optional_str(self.identity_id),
            "actor_id": _optional_str(self.actor_id),
            "identity_profile_id": _optional_str(self.identity_profile_id),
            "public_handle": self.public_handle,
            "identity_type": self.admission.identity_type.value,
            "gate": {
                "status": self.gate.status.value,
                "crossed": self.gate.crossed,
                "identity_id": _optional_str(self.gate.identity_id),
                "expected_actor_id": _optional_str(self.gate.expected_actor_id),
                "authenticated_actor_id": _optional_str(
                    self.gate.authenticated_actor_id
                ),
                "reason": self.gate.reason,
            },
            "receipt": self.admission.receipt.model_dump(mode="json"),
            "state_path": str(self.state_path) if self.state_path is not None else None,
        }


def resolve_local_identity_execution_identity(
    *,
    provider_key: str = LOCAL_IDENTITY_PROVIDER_KEY,
    provider_session_id: str | None = None,
    env: Mapping[str, str] | None = None,
) -> LocalIdentityExecutionIdentity:
    normalized_provider = _normalize_provider_key(provider_key)
    resolved_session_id = provider_session_id
    source_env = env if env is not None else os.environ
    if not resolved_session_id and normalized_provider == "codex":
        resolved_session_id = source_env.get("CODEX_THREAD_ID")
    if not resolved_session_id:
        raise IdentitySdkError(
            "Local Identity resolution requires a provider session id. "
            "For Codex, set CODEX_THREAD_ID or pass provider_session_id."
        )
    raw_session_id = _strip_provider_prefix(
        provider_key=normalized_provider,
        provider_session_id=resolved_session_id,
    )
    return LocalIdentityExecutionIdentity(
        provider_key=normalized_provider,
        provider_session_id=raw_session_id,
        execution_id=f"{normalized_provider}-{raw_session_id}",
    )


def build_local_identity_api_client(
    *,
    repo_root: str | Path | None = None,
    provider_key: str = LOCAL_IDENTITY_PROVIDER_KEY,
    provider_session_id: str | None = None,
    identity_key: str | None = None,
    actor_key: str = LOCAL_IDENTITY_ACTOR_KEY,
    state_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> "LocalIdentityApiClient":
    execution_identity = resolve_local_identity_execution_identity(
        provider_key=provider_key,
        provider_session_id=provider_session_id,
        env=env,
    )
    return LocalIdentityApiClient(
        repo_root=_resolve_repo_root(repo_root),
        execution_identity=execution_identity,
        identity_key=_resolve_identity_key(
            identity_key=identity_key,
            execution_identity=execution_identity,
        ),
        actor_key=_normalize_key(actor_key, default=LOCAL_IDENTITY_ACTOR_KEY),
        state_path=Path(state_path) if state_path is not None else None,
    )


async def ensure_local_identity_admission(
    *,
    repo_root: str | Path | None = None,
    provider_key: str = LOCAL_IDENTITY_PROVIDER_KEY,
    provider_session_id: str | None = None,
    identity_key: str | None = None,
    actor_key: str = LOCAL_IDENTITY_ACTOR_KEY,
    identity_type: IdentityType | str = IdentityType.agent,
    public_key: str | None = None,
    public_handle: str | None = None,
    display_name: str | None = None,
    full_name: str | None = None,
    country_code: str = LOCAL_IDENTITY_COUNTRY_CODE,
    language_code: str = LOCAL_IDENTITY_LANGUAGE_CODE,
    bio: str | None = None,
    state_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> LocalIdentityAdmissionResult:
    api_client = build_local_identity_api_client(
        repo_root=repo_root,
        provider_key=provider_key,
        provider_session_id=provider_session_id,
        identity_key=identity_key,
        actor_key=actor_key,
        state_path=state_path,
        env=env,
    )
    resolved_type = _coerce_identity_type(identity_type)
    resolved_public_key = public_key or _local_public_key(
        namespace=LOCAL_IDENTITY_NAMESPACE,
        identity_key=api_client.identity_key,
    )
    profile = IdentityAdmissionProfile(
        display_name=display_name or _display_name(api_client.identity_key),
        public_handle=public_handle or _public_handle(api_client.identity_key),
        full_name=full_name or _display_name(api_client.identity_key),
        country_code=country_code,
        language_code=language_code,
        bio=bio,
    )
    sdk = IdentitySdkClient(api_client)
    admission = await sdk.admit_identity_via_profile(
        public_key=resolved_public_key,
        profile=profile,
        identity_type=resolved_type,
        source=DEFAULT_IDENTITY_SDK_SOURCE,
    )
    gate = sdk.build_gate_snapshot(
        admission=admission,
        authenticated_actor_id=admission.actor_id,
    )
    return LocalIdentityAdmissionResult(
        execution_identity=api_client.execution_identity,
        identity_key=api_client.identity_key,
        actor_key=api_client.actor_key,
        public_key=resolved_public_key,
        admission=admission,
        gate=gate,
        state_path=api_client.state_path,
    )


class LocalIdentityApiClient:
    def __init__(
        self,
        *,
        repo_root: Path,
        execution_identity: LocalIdentityExecutionIdentity,
        identity_key: str,
        actor_key: str,
        state_path: Path | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.execution_identity = execution_identity
        self.identity_key = identity_key
        self.actor_key = actor_key
        self.state_path = state_path or (
            repo_root / ".aware" / "identity" / "local_identity" / "state.json"
        )
        self.identity = _LocalIdentityNamespace(self)

    def signup_via_profile(
        self,
        request: IdentitySignupViaProfileRequest,
    ) -> IdentityAdmissionReceipt:
        identity_type = request.create_profile_request.identity_type
        identity_id = stable_identity_id(
            public_key=request.public_key,
            identity_type=identity_type,
        )
        receipt = IdentityAdmissionReceipt(
            identity_id=identity_id,
            actor_id=stable_actor_id(identity_id=identity_id, key=self.actor_key),
            identity_profile_id=stable_identity_profile_id(
                public_handle=request.create_profile_request.public_handle,
            ),
            public_handle=request.create_profile_request.public_handle,
            info="local Identity admission ensured",
        )
        self._write_state(request=request, receipt=receipt)
        return receipt

    def _write_state(
        self,
        *,
        request: IdentitySignupViaProfileRequest,
        receipt: IdentityAdmissionReceipt,
    ) -> None:
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": LOCAL_IDENTITY_STATE_VERSION,
            "updated_at": _now_utc(),
            "repo_root": str(self.repo_root),
            "execution_identity": self.execution_identity.to_payload(),
            "identity_key": self.identity_key,
            "actor_key": self.actor_key,
            "request": request.model_dump(mode="json"),
            "receipt": receipt.model_dump(mode="json"),
        }
        self.state_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


class _LocalIdentityNamespace:
    def __init__(self, client: LocalIdentityApiClient) -> None:
        self.signup_via_profile = _LocalSignupViaProfile(client)


class _LocalSignupViaProfile:
    def __init__(self, client: LocalIdentityApiClient) -> None:
        self._client = client

    async def signup_via_profile(
        self,
        request: IdentitySignupViaProfileRequest,
    ) -> IdentityAdmissionReceipt:
        return self._client.signup_via_profile(request)


def stable_identity_id(*, public_key: str, identity_type: IdentityType | str) -> UUID:
    return _stable_identity_id(
        public_key=public_key,
        type=_coerce_identity_type(identity_type).value,
    )


def stable_actor_id(*, identity_id: UUID, key: str = LOCAL_IDENTITY_ACTOR_KEY) -> UUID:
    return _stable_actor_id(identity_id=identity_id, key=key)


def stable_identity_profile_id(*, public_handle: str) -> UUID:
    return _stable_identity_profile_id(public_handle=public_handle)


def _coerce_identity_type(identity_type: IdentityType | str) -> IdentityType:
    if isinstance(identity_type, IdentityType):
        return identity_type
    try:
        return IdentityType(identity_type)
    except ValueError as exc:
        valid_values = ", ".join(member.value for member in IdentityType)
        raise IdentitySdkError(
            f"Unknown IdentityType {identity_type!r}; expected one of: {valid_values}."
        ) from exc


def _resolve_repo_root(repo_root: str | Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "aware.workspace.toml").exists() or (
            candidate / ".git"
        ).exists():
            return candidate
    return current


def _resolve_identity_key(
    *,
    identity_key: str | None,
    execution_identity: LocalIdentityExecutionIdentity,
) -> str:
    if identity_key is not None and identity_key.strip():
        return _normalize_key(identity_key, default=execution_identity.execution_id)
    return execution_identity.execution_id


def _normalize_provider_key(value: str) -> str:
    normalized = "_".join(value.strip().lower().replace("-", "_").split())
    if not normalized:
        raise IdentitySdkError("provider_key is required.")
    return normalized


def _normalize_key(value: str, *, default: str) -> str:
    normalized = "_".join(value.strip().casefold().split())
    return normalized or default


def _strip_provider_prefix(*, provider_key: str, provider_session_id: str) -> str:
    normalized = provider_session_id.strip()
    prefix = f"{provider_key}-"
    if normalized.startswith(prefix):
        return normalized[len(prefix) :]
    return normalized


def _local_public_key(*, namespace: str, identity_key: str) -> str:
    return f"aware-local://{namespace}/identity/{identity_key}"


def _public_handle(identity_key: str) -> str:
    cleaned = []
    for char in identity_key.casefold():
        if char.isalnum():
            cleaned.append(char)
        elif char in {"-", "_", ".", "/"}:
            cleaned.append("-")
    handle = "".join(cleaned).strip("-")
    if not handle:
        handle = str(uuid5(NAMESPACE_URL, identity_key))
    return f"local-{handle}"[:80]


def _display_name(identity_key: str) -> str:
    return identity_key.replace("_", " ").replace("-", " ").strip() or "Local Identity"


def _now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = [
    "LOCAL_IDENTITY_ACTOR_KEY",
    "LOCAL_IDENTITY_COUNTRY_CODE",
    "LOCAL_IDENTITY_LANGUAGE_CODE",
    "LOCAL_IDENTITY_NAMESPACE",
    "LOCAL_IDENTITY_PROVIDER_KEY",
    "LOCAL_IDENTITY_STATE_VERSION",
    "LocalIdentityAdmissionResult",
    "LocalIdentityApiClient",
    "LocalIdentityExecutionIdentity",
    "build_local_identity_api_client",
    "ensure_local_identity_admission",
    "resolve_local_identity_execution_identity",
    "stable_actor_id",
    "stable_identity_id",
    "stable_identity_profile_id",
]
