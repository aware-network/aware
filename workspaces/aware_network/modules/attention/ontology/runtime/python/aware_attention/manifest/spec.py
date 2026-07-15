from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AwareAttentionTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareAttentionTomlBuildSpec:
    anchor_path: str | None = None
    sources_dir: str = "."
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True
    frame_mode: str = "vertical"


@dataclass(frozen=True, slots=True)
class AwareAttentionTomlSpec:
    aware_attention: int
    attention: AwareAttentionTomlPackageSpec
    build: AwareAttentionTomlBuildSpec


__all__ = [
    "AwareAttentionTomlBuildSpec",
    "AwareAttentionTomlPackageSpec",
    "AwareAttentionTomlSpec",
]
