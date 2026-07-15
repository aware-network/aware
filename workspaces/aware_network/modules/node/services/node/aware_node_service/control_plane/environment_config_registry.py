from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable
from uuid import UUID

from aware_environment.environment_config.manifest.schema.environment_manifest import (
    EnvironmentManifest,
)


@dataclass(frozen=True)
class EnvironmentConfigRecord:
    """A provisionable environment config (template/map) discovered by the node."""

    environment_config_id: UUID
    title: str | None
    canonical_language: str | None
    bundle_manifest_path: str
    ocg_hash: str | None
    opg_hashes: tuple[str, ...]
    environment_handle: str | None = None
    outer_wrapper_kind: str = "environment"
    workspace_root: str | None = None
    workspace_toml_path: str | None = None
    workspace_id: str | None = None
    workspace_package_id: str | None = None
    workspace_build_invocation_id: str | None = None
    workspace_build_receipt_path: str | None = None
    workspace_build_latest_path: str | None = None
    workspace_target_latest_path: str | None = None
    workspace_target_ref: str | None = None


def _split_csv(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _default_manifest_globs() -> list[str]:
    return []


def discover_environment_config_manifests(
    *, aware_root: Path, globs: Iterable[str]
) -> list[Path]:
    manifests: list[Path] = []
    for pattern in globs:
        p = Path(pattern)
        if p.is_absolute():
            manifests.extend(Path("/").glob(str(p).lstrip("/")))
        else:
            manifests.extend(aware_root.glob(pattern))
    dedup: dict[str, Path] = {}
    for path in manifests:
        if path.exists():
            dedup[str(path.resolve())] = path
    return sorted(dedup.values(), key=lambda p: str(p))


def discover_environment_configs(*, aware_root: Path) -> list[EnvironmentConfigRecord]:
    """Discover provisionable environment configs by scanning runtime bundle manifests."""

    explicit_paths = _split_csv(
        os.environ.get("AWARE_NODE_ENVIRONMENT_CONFIG_MANIFESTS")
    )
    strict = bool(explicit_paths)

    if explicit_paths:
        manifest_paths = [Path(p) for p in explicit_paths]
    else:
        globs = _split_csv(
            os.environ.get("AWARE_NODE_ENVIRONMENT_CONFIG_MANIFEST_GLOBS")
        )
        if not globs:
            globs = _default_manifest_globs()
        manifest_paths = discover_environment_config_manifests(
            aware_root=aware_root, globs=globs
        )

    records: list[EnvironmentConfigRecord] = []
    seen: set[UUID] = set()
    for manifest_path in manifest_paths:
        try:
            raw = manifest_path.read_text(encoding="utf-8")
            manifest = EnvironmentManifest.model_validate_json(raw)
            config_id = UUID(manifest.environment.id)
            title = manifest.environment.title
            canonical_language = manifest.environment.canonical_language
            ocg_hash = manifest.ocg.hash
            opg_hashes = tuple(
                entry.projection_hash for entry in manifest.opg_index.entries
            )
            if config_id in seen:
                continue
            seen.add(config_id)
            records.append(
                EnvironmentConfigRecord(
                    environment_config_id=config_id,
                    title=title,
                    canonical_language=canonical_language,
                    bundle_manifest_path=str(manifest_path),
                    ocg_hash=ocg_hash,
                    opg_hashes=opg_hashes,
                )
            )
        except Exception:
            if strict:
                raise
            continue

    records.sort(key=lambda r: (r.title or "", str(r.environment_config_id)))
    return records


def resolve_manifest_path(*, aware_root: Path, environment_config_id: UUID) -> str:
    return resolve_environment_config_record(
        aware_root=aware_root,
        environment_config_id=environment_config_id,
    ).bundle_manifest_path


def resolve_environment_config_record(
    *, aware_root: Path, environment_config_id: UUID
) -> EnvironmentConfigRecord:
    configs = discover_environment_configs(aware_root=aware_root)
    for cfg in configs:
        if cfg.environment_config_id == environment_config_id:
            return cfg
    raise KeyError(environment_config_id)


__all__ = [
    "EnvironmentConfigRecord",
    "discover_environment_configs",
    "resolve_environment_config_record",
    "resolve_manifest_path",
]
