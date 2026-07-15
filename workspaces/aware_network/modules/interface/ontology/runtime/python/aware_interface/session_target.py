from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_identity_ontology.identity.identity_enums import IdentityType
from aware_identity_ontology.stable_ids import stable_actor_id
from aware_identity_ontology.stable_ids import stable_identity_id


@dataclass(frozen=True, slots=True)
class InterfaceSessionTarget:
    endpoint: str
    environment_config_id: UUID | None
    actor_id: UUID
    agent_identity_id: UUID | None
    environment_target_reason: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceSessionTargetCoordinates:
    endpoint: str
    environment_config_id: UUID | None
    environment_target_reason: str | None = None


@dataclass(frozen=True, slots=True)
class AgentKeypair:
    label: str
    public_key: str
    private_key: str


def _sanitize_ws_endpoint(value: str) -> str:
    endpoint = value.strip().rstrip("/")
    for suffix in ("/interface/network_node", "/network_node/network_node"):
        if endpoint.endswith(suffix):
            endpoint = endpoint[: -len(suffix)].rstrip("/")
    if endpoint.endswith("/ws"):
        endpoint = endpoint[: -len("/ws")].rstrip("/")
    return endpoint


def _resolve_node_endpoint(*, repository_root: Path | None = None) -> str:
    endpoint = os.getenv("AWARE_NODE_WS_URL")
    if endpoint:
        return _sanitize_ws_endpoint(endpoint)
    base = os.getenv("AWARE_NODE_BASE_URL")
    if base:
        if base.startswith("http://"):
            return _sanitize_ws_endpoint("ws://" + base[len("http://") :])
        if base.startswith("https://"):
            return _sanitize_ws_endpoint("wss://" + base[len("https://") :])
        return _sanitize_ws_endpoint(base)

    repo_root = repository_root
    if repo_root is None:
        repo_env = os.getenv("AWARE_REPO_ROOT") or os.getenv("AWARE_REPOSITORY_ROOT")
        repo_root = Path(repo_env).expanduser() if repo_env else Path.cwd()
    node_cfg_path = repo_root / ".aware" / "network_node.json"
    if node_cfg_path.exists():
        try:
            payload = json.loads(node_cfg_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Invalid node config at {node_cfg_path}: {exc}") from exc
        http_base_url = payload.get("http_base_url") if isinstance(payload, dict) else None
        if isinstance(http_base_url, str) and http_base_url.strip():
            base_url = http_base_url.strip()
            if base_url.startswith("http://"):
                return _sanitize_ws_endpoint("ws://" + base_url[len("http://") :])
            if base_url.startswith("https://"):
                return _sanitize_ws_endpoint("wss://" + base_url[len("https://") :])
            return _sanitize_ws_endpoint(base_url)
    raise RuntimeError(
        "Node endpoint missing. Set AWARE_NODE_WS_URL or AWARE_NODE_BASE_URL "
        "or provide `.aware/network_node.json` with http_base_url."
    )


def _resolve_environment_config_id(*, repository_root: Path | None = None) -> UUID:
    raw = (
        os.getenv("AWARE_ENVIRONMENT_CONFIG_ID")
        or os.getenv("AWARE_ENV_CONFIG_ID")
        or ""
    ).strip()
    if raw:
        return UUID(raw)

    repo_root = repository_root
    if repo_root is None:
        repo_env = os.getenv("AWARE_REPO_ROOT") or os.getenv("AWARE_REPOSITORY_ROOT")
        repo_root = Path(repo_env).expanduser() if repo_env else Path.cwd()

    env_path = repo_root / ".aware" / "environment.json"
    if not env_path.exists():
        raise RuntimeError(
            "Environment config id missing. Set AWARE_ENVIRONMENT_CONFIG_ID "
            "or ensure `.aware/environment.json` exists."
        )
    try:
        payload = json.loads(env_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Invalid environment config at {env_path}: {exc}") from exc
    env_id = payload.get("id") if isinstance(payload, dict) else None
    if not isinstance(env_id, str) or not env_id.strip():
        raise RuntimeError(f"Missing `id` in {env_path}")
    return UUID(env_id)


def _parse_agent_keypairs(payload: Any) -> dict[str, AgentKeypair]:
    if isinstance(payload, list):
        out: dict[str, AgentKeypair] = {}
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("AWARE_AGENT_KEYS_JSON list entries must be objects")
            label = str(item.get("label") or item.get("name") or "").strip()
            public_key = str(
                item.get("public_key") or item.get("publicKey") or ""
            ).strip()
            private_key = str(
                item.get("private_key") or item.get("privateKey") or ""
            ).strip()
            if not label:
                raise ValueError(
                    "AWARE_AGENT_KEYS_JSON entries require a non-empty 'label'"
                )
            if not public_key or not private_key:
                raise ValueError(
                    f"AWARE_AGENT_KEYS_JSON entry {label!r} missing "
                    "public_key/private_key"
                )
            out[label] = AgentKeypair(
                label=label,
                public_key=public_key,
                private_key=private_key,
            )
        return out

    if isinstance(payload, dict):
        if "agents" in payload:
            return _parse_agent_keypairs(payload["agents"])
        out: dict[str, AgentKeypair] = {}
        for label, item in payload.items():
            if not isinstance(item, dict):
                raise ValueError("AWARE_AGENT_KEYS_JSON dict entries must be objects")
            public_key = str(
                item.get("public_key") or item.get("publicKey") or ""
            ).strip()
            private_key = str(
                item.get("private_key") or item.get("privateKey") or ""
            ).strip()
            if not public_key or not private_key:
                raise ValueError(
                    f"AWARE_AGENT_KEYS_JSON entry {label!r} missing "
                    "public_key/private_key"
                )
            key_label = str(label).strip()
            out[key_label] = AgentKeypair(
                label=key_label,
                public_key=public_key,
                private_key=private_key,
            )
        return out

    raise ValueError("AWARE_AGENT_KEYS_JSON must be a list or dict")


def _load_agent_keypairs() -> dict[str, AgentKeypair]:
    raw = os.getenv("AWARE_AGENT_KEYS_JSON")
    keys_file = os.getenv("AWARE_AGENT_KEYS_FILE")
    if (raw is None or not raw.strip()) and keys_file and keys_file.strip():
        raw = Path(keys_file.strip()).read_text(encoding="utf-8")

    if raw is None or not raw.strip():
        public_key = os.getenv("AWARE_AGENT_PUBLIC_KEY", "").strip()
        private_key = os.getenv("AWARE_AGENT_PRIVATE_KEY", "").strip()
        if not public_key or not private_key:
            raise RuntimeError(
                "Agent identity session requires keys. Set either "
                "AWARE_AGENT_KEYS_JSON/AWARE_AGENT_KEYS_FILE or "
                "AWARE_AGENT_PUBLIC_KEY+AWARE_AGENT_PRIVATE_KEY."
            )
        label = os.getenv("AWARE_AGENT_KEY_LABEL", "default").strip() or "default"
        return {
            label: AgentKeypair(
                label=label,
                public_key=public_key,
                private_key=private_key,
            )
        }

    payload = json.loads(raw)
    keypairs = _parse_agent_keypairs(payload)
    if not keypairs:
        raise RuntimeError("AWARE_AGENT_KEYS_JSON resolved to an empty key set")
    return keypairs


def _pick_agent_keypair(*, requested_identity_id: UUID | None) -> tuple[UUID, AgentKeypair]:
    keypairs = _load_agent_keypairs()
    requested = requested_identity_id
    if requested is None:
        raw = os.getenv("AWARE_AGENT_IDENTITY_ID", "").strip()
        if raw:
            requested = UUID(raw)

    by_identity: dict[UUID, AgentKeypair] = {}
    for keypair in keypairs.values():
        _, key_bytes = canonicalize_ed25519_public_key(keypair.public_key)
        identity_id = stable_identity_id(
            public_key=f"ed25519:{key_bytes.hex()}",
            type=IdentityType.agent.value,
        )
        by_identity[identity_id] = keypair

    if requested is not None:
        match = by_identity.get(requested)
        if match is None:
            raise RuntimeError(
                "Requested AWARE_AGENT_IDENTITY_ID does not match any configured "
                "agent public key. "
                f"requested={requested} available={sorted(str(i) for i in by_identity)}"
            )
        return requested, match

    if len(by_identity) == 1:
        identity_id = next(iter(by_identity.keys()))
        return identity_id, by_identity[identity_id]

    label = os.getenv("AWARE_AGENT_KEY_LABEL", "").strip()
    if label and label in keypairs:
        keypair = keypairs[label]
        _, key_bytes = canonicalize_ed25519_public_key(keypair.public_key)
        identity_id = stable_identity_id(
            public_key=f"ed25519:{key_bytes.hex()}",
            type=IdentityType.agent.value,
        )
        return identity_id, keypair

    raise RuntimeError(
        "Multiple agent keys configured. Set AWARE_AGENT_IDENTITY_ID to "
        "disambiguate (or AWARE_AGENT_KEY_LABEL to select by label)."
    )


def resolve_interface_session_target_coordinates(
    *,
    repository_root: Path | None = None,
    endpoint: str | None = None,
    environment_config_id: UUID | None = None,
) -> InterfaceSessionTargetCoordinates:
    resolved_endpoint = (
        endpoint.strip().rstrip("/")
        if endpoint
        else _resolve_node_endpoint(repository_root=repository_root)
    )
    resolved_environment_config_id = environment_config_id
    environment_target_reason: str | None = None
    if resolved_environment_config_id is None:
        try:
            resolved_environment_config_id = _resolve_environment_config_id(
                repository_root=repository_root,
            )
        except RuntimeError as exc:
            if "Environment config id missing" not in str(exc):
                raise
            environment_target_reason = str(exc)
    return InterfaceSessionTargetCoordinates(
        endpoint=resolved_endpoint,
        environment_config_id=resolved_environment_config_id,
        environment_target_reason=environment_target_reason,
    )


def resolve_interface_session_target(
    *,
    repository_root: Path | None = None,
    endpoint: str | None = None,
    environment_config_id: UUID | None = None,
    agent_identity_id: UUID | None = None,
    auth_actor_id: UUID | None = None,
) -> InterfaceSessionTarget:
    coordinates = resolve_interface_session_target_coordinates(
        repository_root=repository_root,
        endpoint=endpoint,
        environment_config_id=environment_config_id,
    )

    if auth_actor_id is not None:
        return InterfaceSessionTarget(
            endpoint=coordinates.endpoint,
            environment_config_id=coordinates.environment_config_id,
            actor_id=auth_actor_id,
            agent_identity_id=None,
            environment_target_reason=coordinates.environment_target_reason,
        )

    resolved_agent_identity_id, _ = _pick_agent_keypair(
        requested_identity_id=agent_identity_id,
    )
    return InterfaceSessionTarget(
        endpoint=coordinates.endpoint,
        environment_config_id=coordinates.environment_config_id,
        actor_id=stable_actor_id(identity_id=resolved_agent_identity_id),
        agent_identity_id=resolved_agent_identity_id,
        environment_target_reason=coordinates.environment_target_reason,
    )


__all__ = [
    "InterfaceSessionTarget",
    "InterfaceSessionTargetCoordinates",
    "resolve_interface_session_target",
    "resolve_interface_session_target_coordinates",
]
