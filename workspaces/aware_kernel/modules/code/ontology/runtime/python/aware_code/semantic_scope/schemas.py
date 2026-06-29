from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TypeAlias


SemanticScopePayloadObject: TypeAlias = Mapping[str, "SemanticScopePayloadValue"]
SemanticScopePayloadValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | Sequence["SemanticScopePayloadValue"]
    | SemanticScopePayloadObject
)


@dataclass(frozen=True, slots=True)
class SemanticScopeMaterializationDependency:
    """Provider-owned dependency ref required by materialization scope closure."""

    package_name: str
    provider_key: str | None = None
    semantic_owner: str | None = None
    manifest_kind: str | None = None
    dependency_kind: str = "semantic_package"
    required_state: str = "materialized"
    semantic_package_family: str | None = None
    semantic_package_kind: str | None = None
    semantic_package_name: str | None = None
    source_refs: tuple[str, ...] = ()
    reason: str | None = None
    metadata: SemanticScopePayloadObject = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticScopeResolution:
    """Module-owned semantic scope resolved for one code package."""

    scope_key: str
    provider_key: str
    payload: SemanticScopePayloadObject
    materialization_dependencies: tuple[
        SemanticScopeMaterializationDependency,
        ...,
    ] = ()
    runtime_value: object | None = None


__all__ = [
    "SemanticScopeMaterializationDependency",
    "SemanticScopePayloadObject",
    "SemanticScopePayloadValue",
    "SemanticScopeResolution",
]
