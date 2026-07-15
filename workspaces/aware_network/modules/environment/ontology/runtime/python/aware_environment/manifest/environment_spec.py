"""Environment spec models for `aware.environment.toml` (strict, deterministic)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AwareEnvironmentBuildSpec:
    """Environment-owned source discovery for profile/session topology."""

    sources_dir: str = "aware"
    include_paths: tuple[str, ...] = ("**/*.aware",)
    exclude_paths: tuple[str, ...] = ()
    force_fresh_scan: bool = True


@dataclass(frozen=True, slots=True)
class AwareEnvironmentDescriptorSpec:
    """High-level environment config descriptor (build-time)."""

    handle: str
    environment_config_id: str | None = None
    title: str | None = None
    canonical_language: str = "aware"


@dataclass(frozen=True, slots=True)
class AwareEnvironmentSpec:
    aware: int
    environment: AwareEnvironmentDescriptorSpec
    build: AwareEnvironmentBuildSpec | None = None
    modules: tuple[str, ...] = ()
    ontologies: tuple[str, ...] = ()
    base_environment_manifest_paths: tuple[str, ...] = ()


__all__ = [
    "AwareEnvironmentBuildSpec",
    "AwareEnvironmentDescriptorSpec",
    "AwareEnvironmentSpec",
]
