from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

from aware_identity_ontology.stable_ids import stable_auth_token_registry_id
from aware_meta_service.local_sdk import (
    LocalMetaLaneStore,
    build_local_meta_runtime_index_snapshot,
    build_local_meta_lane_store,
)
from aware_environment.environment_config.manifest.schema.environment_manifest import (
    EnvironmentManifest,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
import msgpack


class AptTokenValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AptTokenClaims:
    token_id: UUID
    actor_id: UUID
    public_key: str
    scopes: list[str]
    context_environment_id: UUID
    context_process_id: UUID
    context_thread_id: UUID
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class TokenAuthorityManifest:
    path: Path
    runtime_manifest_path: Path | None
    commit_store_root_path: Path | None
    token_registry_id: UUID | None = None
    auth_token_projection_hash: str | None = None


TOKEN_AUTHORITY_MANIFEST_VERSION = "aware.node.token_authority.v1"
_APT_TOKEN_RE = re.compile(
    r"^aware_apt_(?P<token_id>[0-9a-fA-F-]{36})\.(?P<secret>[A-Za-z0-9_-]+)$"
)


def load_token_authority_manifest(path: str | Path) -> TokenAuthorityManifest:
    manifest_path = Path(path).expanduser().resolve()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(
            "Token authority manifest could not be read: " + manifest_path.as_posix()
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            "Token authority manifest must be a JSON object: "
            + manifest_path.as_posix()
        )
    version = str(payload.get("version") or "").strip()
    if version != TOKEN_AUTHORITY_MANIFEST_VERSION:
        raise ValueError(
            "Unsupported token authority manifest version "
            f"{version!r}; expected {TOKEN_AUTHORITY_MANIFEST_VERSION!r}."
        )
    runtime_manifest_path = _json_optional_path(
        payload,
        "runtime_manifest_path",
        base_dir=manifest_path.parent,
    )
    commit_store_root_path = _json_optional_path(
        payload,
        "commit_store_root_path",
        base_dir=manifest_path.parent,
    )
    return TokenAuthorityManifest(
        path=manifest_path,
        runtime_manifest_path=runtime_manifest_path,
        commit_store_root_path=commit_store_root_path,
        token_registry_id=_json_optional_uuid(payload, "token_registry_id"),
        auth_token_projection_hash=_json_optional_text(
            payload,
            "auth_token_projection_hash",
        ),
    )


def _json_optional_text(payload: dict[object, object], key: str) -> str | None:
    value = payload.get(key)
    text = str(value or "").strip() if value is not None else ""
    return text or None


def _json_optional_path(
    payload: dict[object, object],
    key: str,
    *,
    base_dir: Path,
) -> Path | None:
    text = _json_optional_text(payload, key)
    if text is None:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _json_optional_uuid(payload: dict[object, object], key: str) -> UUID | None:
    text = _json_optional_text(payload, key)
    if text is None:
        return None
    try:
        return UUID(text)
    except Exception as exc:
        raise ValueError(
            f"Token authority manifest field {key!r} must be a UUID."
        ) from exc


def _b64url_decode(value: str) -> bytes:
    raw = value.strip()
    padding = "=" * (-len(raw) % 4)
    try:
        return base64.urlsafe_b64decode(raw + padding)
    except Exception as exc:
        raise AptTokenValidationError("Invalid token secret encoding") from exc


def _parse_dt(value: object) -> datetime | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    # Accept Z suffix.
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _graph_catalog(graph_context: object) -> object:
    catalog = getattr(graph_context, "index", None)
    if catalog is not None:
        return catalog
    return graph_context


class AptTokenValidator:
    """Resolve and validate commit-backed APT tokens.

    Notes:
    - Uses local Meta SDK storage helpers, because token validation happens
      before an identity session exists.
    """

    def __init__(
        self,
        *,
        manifest_path: str | None = None,
        token_authority_manifest_path: str | Path | None = None,
    ) -> None:
        authority_manifest = (
            load_token_authority_manifest(token_authority_manifest_path)
            if token_authority_manifest_path
            else None
        )
        resolved_manifest_path = (
            authority_manifest.runtime_manifest_path
            if authority_manifest is not None
            and authority_manifest.runtime_manifest_path is not None
            else manifest_path
        )
        commit_store_root_path = (
            authority_manifest.commit_store_root_path
            if authority_manifest is not None
            else None
        )

        self._runtime_manifest_path = resolved_manifest_path
        self._token_registry_id = (
            authority_manifest.token_registry_id
            if authority_manifest is not None
            and authority_manifest.token_registry_id is not None
            else stable_auth_token_registry_id()
        )
        self._auth_token_projection_hash = (
            authority_manifest.auth_token_projection_hash
            if authority_manifest is not None
            else None
        )
        self._lane_store: LocalMetaLaneStore = build_local_meta_lane_store(
            root_dir=commit_store_root_path,
        )

        self._resolve_lock = asyncio.Lock()
        self._resolved = False

        self._index = None
        self._opg = None
        self._projection_hash: str | None = None
        self._token_class_config_id: UUID | None = None
        self._token_attr_name_by_id: dict[UUID, str] = {}
        self._enum_option_value_by_id: dict[UUID, str] = {}

    async def validate_apt_token(self, token: str) -> AptTokenClaims:
        token_id, secret_bytes = self._parse_token(token)
        secret_sha256 = hashlib.sha256(secret_bytes).hexdigest()

        attrs = await self._load_token_attrs(token_id=token_id)
        if attrs is None:
            raise AptTokenValidationError("Unknown token")

        token_type = str(attrs.get("token_type") or "").strip().lower()
        if token_type != "apt":
            raise AptTokenValidationError("Invalid token type")

        expected_sha256 = str(attrs.get("sha256") or "").strip().lower()
        if not expected_sha256 or expected_sha256 != secret_sha256:
            raise AptTokenValidationError("Invalid token secret")

        revoked_at = attrs.get("revoked_at")
        if revoked_at is not None and str(revoked_at).strip():
            raise AptTokenValidationError("Token revoked")

        expires_at = _parse_dt(attrs.get("expires_at"))
        if expires_at is not None and datetime.now(timezone.utc) >= expires_at:
            raise AptTokenValidationError("Token expired")

        actor_id_raw = attrs.get("actor_id")
        public_key = str(attrs.get("public_key") or "").strip()
        if not actor_id_raw or not public_key:
            raise AptTokenValidationError("Malformed token record")

        ctx_env_raw = attrs.get("context_environment_id")
        ctx_proc_raw = attrs.get("context_process_id")
        ctx_thread_raw = attrs.get("context_thread_id")
        if not ctx_env_raw or not ctx_proc_raw or not ctx_thread_raw:
            raise AptTokenValidationError(
                "Malformed token record (missing context binding)"
            )

        scopes_raw = attrs.get("scopes")
        scopes: list[str]
        if isinstance(scopes_raw, list):
            scopes = [str(s).strip() for s in scopes_raw if str(s).strip()]
        else:
            scopes = []

        return AptTokenClaims(
            token_id=token_id,
            actor_id=UUID(str(actor_id_raw)),
            public_key=public_key,
            scopes=scopes,
            context_environment_id=UUID(str(ctx_env_raw)),
            context_process_id=UUID(str(ctx_proc_raw)),
            context_thread_id=UUID(str(ctx_thread_raw)),
            expires_at=expires_at,
        )

    @classmethod
    def _parse_token(cls, token: str) -> tuple[UUID, bytes]:
        raw = (token or "").strip()
        m = _APT_TOKEN_RE.match(raw)
        if not m:
            raise AptTokenValidationError(
                "Invalid token format (expected aware_apt_<uuid>.<secret>)"
            )
        try:
            token_id = UUID(m.group("token_id"))
        except Exception as exc:
            raise AptTokenValidationError("Invalid token id") from exc
        secret_b64url = m.group("secret")
        secret_bytes = _b64url_decode(secret_b64url)
        if len(secret_bytes) < 16:
            raise AptTokenValidationError("Token secret too short")
        return token_id, secret_bytes

    async def _ensure_resolved(self) -> None:
        if self._resolved:
            return

        async with self._resolve_lock:
            if self._resolved:
                return

            graph_context = _load_token_graph_context_from_runtime_manifest(
                runtime_manifest_path=_required_token_runtime_manifest_path(
                    self._runtime_manifest_path
                ),
                auth_token_projection_hash=self._auth_token_projection_hash,
            )
            index = _graph_catalog(graph_context)

            opg = next(
                (
                    candidate
                    for candidate in index.opg_by_hash.values()
                    if candidate.name == "AuthToken"
                ),
                None,
            )
            if opg is None:
                available = sorted({c.name for c in index.opg_by_hash.values()})
                raise RuntimeError(
                    "auth_token projection not found in graph context "
                    f"(available={available})"
                )

            token_node = next(
                (
                    node
                    for node in opg.object_projection_graph_nodes
                    if not node.is_root
                    and index.class_configs_by_id.get(node.class_config_id) is not None
                    and index.class_configs_by_id[node.class_config_id].name
                    == "AuthToken"
                ),
                None,
            )
            if token_node is None:
                raise RuntimeError("auth_token projection missing AuthToken node")

            token_cc = index.class_configs_by_id[token_node.class_config_id]
            token_attr_name_by_id = {
                link.attribute_config.id: link.attribute_config.name
                for link in token_cc.class_config_attribute_configs
            }

            self._index = index
            self._opg = opg
            self._projection_hash = opg.projection_hash
            self._token_class_config_id = token_cc.id
            self._token_attr_name_by_id = token_attr_name_by_id
            self._enum_option_value_by_id = self._build_enum_option_value_index(index)
            self._resolved = True

    @staticmethod
    def _build_enum_option_value_index(index: object) -> dict[UUID, str]:
        out: dict[UUID, str] = {}
        ocg = index.ocg
        for node in ocg.object_config_graph_nodes:
            enum_config = node.enum_config
            if enum_config is None:
                continue
            for option in enum_config.enum_options:
                opt_id = option.id
                value = option.value
                if opt_id is None or value is None:
                    continue
                out[opt_id] = str(value)
        return out

    async def _load_token_attrs(self, *, token_id: UUID) -> dict[str, object] | None:
        await self._ensure_resolved()
        assert self._projection_hash is not None
        assert self._token_class_config_id is not None
        assert self._index is not None
        assert self._opg is not None

        snapshot = await self._lane_store.materialize_head(
            branch_id=self._token_registry_id,
            projection_hash=self._projection_hash,
            ocg=self._index.ocg,
            opg=self._opg,
            class_configs_by_id=self._index.class_configs_by_id,
            attribute_configs_by_id=self._index.attribute_configs_by_id,
        )
        if snapshot is None:
            return None
        oig, _ = snapshot

        for ci in oig.class_instances:
            if ci.class_config_id != self._token_class_config_id:
                continue
            source_object_id = getattr(ci, "source_object_id", None)
            if ci.id != token_id and source_object_id != token_id:
                continue

            attrs: dict[str, object] = {}
            for attr in ci.attributes:
                name = self._token_attr_name_by_id.get(attr.attribute_config_id)
                if not name:
                    continue
                attrs[name] = self._decode_attribute_value(attr.value_root)
            return attrs
        return None

    def _decode_attribute_value(
        self, value_root: AttributeValue
    ) -> object:  # noqa: ANN001
        kind = value_root.type_descriptor.kind
        if kind == AttributeTypeDescriptorKind.primitive:
            raw = value_root.primitive_value
            if isinstance(raw, dict) and "value" in raw:
                return raw["value"]
            return raw
        if kind == AttributeTypeDescriptorKind.enum:
            if value_root.enum_option is not None:
                return value_root.enum_option.value
            enum_option_id = value_root.enum_option_id
            if enum_option_id is not None:
                return self._enum_option_value_by_id.get(enum_option_id)
            return None
        if kind == AttributeTypeDescriptorKind.union:
            links = list(value_root.child_links or [])
            if not links:
                return None
            links.sort(key=lambda l: (l.position or 0, l.identity_key or ""))
            # Prefer a non-null decoded value when possible (optional unions).
            for link in links:
                decoded = self._decode_attribute_value(link.child)
                if decoded is not None:
                    return decoded
            return self._decode_attribute_value(links[0].child)
        if kind == AttributeTypeDescriptorKind.class_:
            if (
                value_root.class_instance is not None
                and value_root.class_instance.id is not None
            ):
                return str(value_root.class_instance.id)
            return (
                str(value_root.class_instance_id)
                if value_root.class_instance_id
                else None
            )
        if kind == AttributeTypeDescriptorKind.collection:
            links = list(value_root.child_links or [])
            elements = [
                link
                for link in links
                if link.role
                in {
                    AttributeTypeDescriptorRole.element,
                    AttributeTypeDescriptorRole.member,
                }
            ]
            elements.sort(key=lambda l: (l.position or 0, l.identity_key or ""))
            return [self._decode_attribute_value(link.child) for link in elements]

        return None


def _required_token_runtime_manifest_path(
    runtime_manifest_path: str | Path | None,
) -> Path:
    text = str(runtime_manifest_path or "").strip()
    if not text:
        raise RuntimeError(
            "APT token validation requires a materialized runtime manifest from "
            "the token authority manifest or AWARE_ENVIRONMENT_MANIFEST; source "
            "package-manifest fallback is disabled."
        )
    return Path(text).expanduser().resolve()


def _load_token_graph_context_from_runtime_manifest(
    *,
    runtime_manifest_path: Path,
    auth_token_projection_hash: str | None,
) -> object:
    manifest = EnvironmentManifest.model_validate_json(
        runtime_manifest_path.read_text(encoding="utf-8")
    )
    ocg = _load_ocg_snapshot_from_runtime_manifest(
        runtime_manifest_path=runtime_manifest_path,
        manifest=manifest,
    )
    projection_hash = _resolve_auth_token_projection_hash_from_manifest(
        manifest=manifest,
        auth_token_projection_hash=auth_token_projection_hash,
    )
    if projection_hash and not any(
        opg.projection_hash == projection_hash
        for opg in tuple(ocg.object_projection_graphs or ())
    ):
        opg = _load_opg_from_runtime_manifest(
            runtime_manifest_path=runtime_manifest_path,
            manifest=manifest,
            projection_hash=projection_hash,
        )
        ocg = ocg.model_copy(
            update={
                "object_projection_graphs": tuple(ocg.object_projection_graphs or ())
                + (opg,)
            }
        )
    return build_local_meta_runtime_index_snapshot(ocg=ocg)


def _load_ocg_snapshot_from_runtime_manifest(
    *,
    runtime_manifest_path: Path,
    manifest: EnvironmentManifest,
) -> ObjectConfigGraph:
    snapshot_path = _resolve_runtime_artifact_path(
        runtime_manifest_path=runtime_manifest_path,
        artifact_path=manifest.ocg.snapshot,
    )
    payload = msgpack.unpackb(snapshot_path.read_bytes(), raw=False)
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            "Token validation runtime OCG snapshot must contain a mapping payload "
            f"(manifest={runtime_manifest_path}, snapshot={snapshot_path})"
        )
    return ObjectConfigGraph.model_validate(payload)


def _load_opg_from_runtime_manifest(
    *,
    runtime_manifest_path: Path,
    manifest: EnvironmentManifest,
    projection_hash: str,
) -> ObjectProjectionGraph:
    entry = next(
        (
            candidate
            for candidate in manifest.opg_index.entries
            if candidate.projection_hash == projection_hash
        ),
        None,
    )
    if entry is None:
        raise RuntimeError(
            "Token validation runtime manifest does not contain AuthToken OPG "
            f"projection_hash={projection_hash}"
        )
    opg_path = _resolve_runtime_artifact_path(
        runtime_manifest_path=runtime_manifest_path,
        artifact_path=entry.file,
    )
    payload = json.loads(opg_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            "Token validation runtime OPG artifact must contain a mapping payload "
            f"(manifest={runtime_manifest_path}, opg={opg_path})"
        )
    return ObjectProjectionGraph.model_validate(payload)


def _resolve_auth_token_projection_hash_from_manifest(
    *,
    manifest: EnvironmentManifest,
    auth_token_projection_hash: str | None,
) -> str | None:
    expected_hash = str(auth_token_projection_hash or "").strip()
    if expected_hash:
        if not any(
            entry.projection_hash == expected_hash
            for entry in manifest.opg_index.entries
        ):
            raise RuntimeError(
                "Token authority manifest references AuthToken projection hash "
                "that is not present in the runtime manifest: "
                f"{expected_hash}"
            )
        return expected_hash
    entry = next(
        (
            candidate
            for candidate in manifest.opg_index.entries
            if candidate.model.rsplit(".", 1)[-1] == "AuthToken"
        ),
        None,
    )
    return entry.projection_hash if entry is not None else None


def _resolve_runtime_artifact_path(
    *,
    runtime_manifest_path: Path,
    artifact_path: str,
) -> Path:
    path = Path(artifact_path).expanduser()
    if not path.is_absolute():
        path = runtime_manifest_path.parent / path
    return path.resolve()


__all__ = [
    "AptTokenClaims",
    "AptTokenValidationError",
    "AptTokenValidator",
]
