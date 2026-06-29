from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_scope import SemanticScopeResolution


META_SEMANTIC_PROJECTION_MUTATION_SCOPE_CONTRACT_VERSION = (
    "aware.meta.semantic-projection-mutation-scope.v0"
)
META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY = (
    "aware_meta.object_config_graph.projection_mutation_scope"
)
META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY = (
    "semantic_projection_mutation_scopes"
)

_TUPLE_FIELDS = (
    "projection_refs",
    "projection_node_refs",
    "projection_node_key_refs",
    "object_graph_refs",
    "operation_family_refs",
    "semantic_operation_type_refs",
    "function_call_binding_refs",
    "ontology_function_refs",
    "source_binding_refs",
    "generated_materialization_intent_refs",
    "expected_proof_refs",
    "expected_receipt_refs",
)


@dataclass(frozen=True, slots=True)
class MetaSemanticProjectionMutationScopeDescriptor:
    """Meta-owned contract for projection-scoped ontology mutation evidence."""

    scope_key: str
    semantic_owner: str
    projection_name: str
    projection_refs: tuple[str, ...]
    projection_node_refs: tuple[str, ...] = ()
    projection_node_key_refs: tuple[str, ...] = ()
    object_graph_refs: tuple[str, ...] = ()
    operation_family_refs: tuple[str, ...] = ()
    semantic_operation_type_refs: tuple[str, ...] = ()
    function_call_binding_refs: tuple[str, ...] = ()
    ontology_function_refs: tuple[str, ...] = ()
    source_binding_refs: tuple[str, ...] = ()
    generated_materialization_intent_refs: tuple[str, ...] = ()
    expected_proof_refs: tuple[str, ...] = ()
    expected_receipt_refs: tuple[str, ...] = ()
    package_selectors: Mapping[str, str] = field(default_factory=dict)
    provider_payload: Mapping[str, object] = field(default_factory=dict)
    contract_version: str = META_SEMANTIC_PROJECTION_MUTATION_SCOPE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        for field_name in _TUPLE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalized_unique_text(getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "package_selectors",
            _normalized_text_mapping(self.package_selectors),
        )
        object.__setattr__(self, "provider_payload", dict(self.provider_payload))

    def evidence_payload(self) -> dict[str, object]:
        return {
            "scope_kind": "meta_semantic_projection_mutation_scope",
            "contract_version": self.contract_version,
            "scope_key": self.scope_key,
            "semantic_owner": self.semantic_owner,
            "projection_name": self.projection_name,
            "projection_refs": self.projection_refs,
            "projection_node_refs": self.projection_node_refs,
            "projection_node_key_refs": self.projection_node_key_refs,
            "object_graph_refs": self.object_graph_refs,
            "operation_family_refs": self.operation_family_refs,
            "semantic_operation_type_refs": self.semantic_operation_type_refs,
            "function_call_binding_refs": self.function_call_binding_refs,
            "ontology_function_refs": self.ontology_function_refs,
            "source_binding_refs": self.source_binding_refs,
            "generated_materialization_intent_refs": (
                self.generated_materialization_intent_refs
            ),
            "expected_proof_refs": self.expected_proof_refs,
            "expected_receipt_refs": self.expected_receipt_refs,
            "package_selectors": dict(self.package_selectors),
            "provider_payload": dict(self.provider_payload),
        }


def code_package_matches_meta_projection_mutation_scope(
    code_package: CodePackageInfo,
) -> bool:
    return (
        code_package.metadata.get("manifest_kind")
        in {"aware_toml", "aware_ontology_toml"}
        and code_package.metadata.get("package_kind") == "ontology"
    )


def meta_semantic_projection_mutation_scope_resolution(
    *,
    descriptor: MetaSemanticProjectionMutationScopeDescriptor,
    code_package: CodePackageInfo,
    provider_key: str,
    workspace_root: Path,
) -> SemanticScopeResolution:
    payload = descriptor.evidence_payload()
    payload["code_package"] = {
        "name": code_package.name,
        "manifest_kind": code_package.metadata.get("manifest_kind"),
        "package_kind": code_package.metadata.get("package_kind"),
        "fqn_prefix": code_package.metadata.get("fqn_prefix"),
        "root_relative_path": _workspace_relative_path_or_abs(
            path=code_package.root_path,
            workspace_root=workspace_root,
        ),
        "manifest_relative_path": _workspace_relative_path_or_abs(
            path=code_package.manifest_path,
            workspace_root=workspace_root,
        ),
    }
    return SemanticScopeResolution(
        scope_key=descriptor.scope_key,
        provider_key=provider_key,
        payload=payload,
        runtime_value=descriptor,
    )


def _workspace_relative_path_or_abs(*, path: Path, workspace_root: Path) -> str:
    resolved_path = (path if path.is_absolute() else workspace_root / path).resolve()
    resolved_root = workspace_root.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def _normalized_unique_text(values: Sequence[str]) -> tuple[str, ...]:
    normalized: dict[str, None] = {}
    for value in values:
        text = value.strip() if isinstance(value, str) else ""
        if text:
            normalized[text] = None
    return tuple(normalized)


def _normalized_text_mapping(values: Mapping[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in values.items():
        normalized_key = key.strip() if isinstance(key, str) else ""
        normalized_value = value.strip() if isinstance(value, str) else ""
        if normalized_key and normalized_value:
            normalized[normalized_key] = normalized_value
    return normalized


__all__ = [
    "META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY",
    "META_SEMANTIC_PROJECTION_MUTATION_SCOPE_CONTRACT_VERSION",
    "META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY",
    "MetaSemanticProjectionMutationScopeDescriptor",
    "code_package_matches_meta_projection_mutation_scope",
    "meta_semantic_projection_mutation_scope_resolution",
]
