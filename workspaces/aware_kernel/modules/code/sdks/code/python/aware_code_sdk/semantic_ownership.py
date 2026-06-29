from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol, cast
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CodeSdkSemanticProviderOwnership:
    provider_key: str
    role: str
    contract: str
    module: str
    code_package_surface: str | None
    code_package_surface_by_package_kind: Mapping[str, str] | None
    owned_manifest_kind_count: int


@dataclass(frozen=True, slots=True)
class CodeSdkSemanticArtifactBinding:
    module_id: str | None
    package_name: str
    language: str
    surface: str
    manifest_kind: str
    manifest_relative_path: str
    package_root: str
    sources_root: str
    package_kind: str | None = None
    semantic_contract_provider_key: str | None = None
    semantic_contract_role: str | None = None
    semantic_contract_name: str | None = None
    semantic_contract_module: str | None = None


@dataclass(frozen=True, slots=True)
class CodeSdkSemanticArtifactProduction:
    provider_key: str
    producer_key: str
    producer_kind: str | None = None
    provider_payload: Mapping[str, object] | None = None
    input_code_package_id: UUID | None = None
    input_object_instance_graph_commit_id: UUID | None = None
    input_digest: str | None = None
    output_digest: str | None = None
    emission_payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CodeSdkSemanticArtifactLeafClaim:
    owned: bool
    owner_semantic_package_manifest: str
    ownership_role: str
    artifact_manifest_kind: str
    artifact_package_root: str
    production: CodeSdkSemanticArtifactProduction | None = None


class CodeSdkSemanticOwnershipProvider(Protocol):
    def semantic_provider_ownerships_for_manifest_kind(
        self,
        *,
        manifest_kind: str,
    ) -> tuple[CodeSdkSemanticProviderOwnership, ...]: ...

    def claim_semantic_artifact_leaf(
        self,
        *,
        workspace_root: str,
        owner: CodeSdkSemanticArtifactBinding,
        leaf: CodeSdkSemanticArtifactBinding,
    ) -> CodeSdkSemanticArtifactLeafClaim | None: ...


@dataclass(frozen=True, slots=True)
class ServiceBackedCodeSdkSemanticOwnershipProvider:
    raw_provider: object

    def semantic_provider_ownerships_for_manifest_kind(
        self,
        *,
        manifest_kind: str,
    ) -> tuple[CodeSdkSemanticProviderOwnership, ...]:
        method = getattr(
            self.raw_provider,
            "semantic_provider_ownerships_for_manifest_kind",
            None,
        )
        if not callable(method):
            return ()
        raw_items = cast(Iterable[object], method(manifest_kind=manifest_kind))
        return tuple(
            _semantic_provider_ownership_from_mapping(item)
            for item in raw_items
        )

    def claim_semantic_artifact_leaf(
        self,
        *,
        workspace_root: str,
        owner: CodeSdkSemanticArtifactBinding,
        leaf: CodeSdkSemanticArtifactBinding,
    ) -> CodeSdkSemanticArtifactLeafClaim | None:
        method = getattr(self.raw_provider, "claim_semantic_artifact_leaf", None)
        if not callable(method):
            return None
        raw_claim = method(
            workspace_root=workspace_root,
            owner=_semantic_artifact_binding_payload(owner),
            leaf=_semantic_artifact_binding_payload(leaf),
        )
        if raw_claim is None:
            return None
        return _semantic_artifact_leaf_claim_from_mapping(raw_claim)


def _semantic_provider_ownership_from_mapping(
    value: object,
) -> CodeSdkSemanticProviderOwnership:
    item = _mapping(value)
    return CodeSdkSemanticProviderOwnership(
        provider_key=_required_str(item, "provider_key"),
        role=_required_str(item, "role"),
        contract=_required_str(item, "contract"),
        module=_required_str(item, "module"),
        code_package_surface=_optional_str(item, "code_package_surface"),
        code_package_surface_by_package_kind=_optional_string_mapping(
            item,
            "code_package_surface_by_package_kind",
        ),
        owned_manifest_kind_count=_required_int(
            item,
            "owned_manifest_kind_count",
        ),
    )


def _semantic_artifact_leaf_claim_from_mapping(
    value: object,
) -> CodeSdkSemanticArtifactLeafClaim:
    item = _mapping(value)
    return CodeSdkSemanticArtifactLeafClaim(
        owned=_required_bool(item, "owned"),
        owner_semantic_package_manifest=_required_str(
            item,
            "owner_semantic_package_manifest",
        ),
        ownership_role=_required_str(item, "ownership_role"),
        artifact_manifest_kind=_required_str(item, "artifact_manifest_kind"),
        artifact_package_root=_required_str(item, "artifact_package_root"),
        production=_semantic_artifact_production_from_mapping(item.get("production")),
    )


def _semantic_artifact_production_from_mapping(
    value: object,
) -> CodeSdkSemanticArtifactProduction | None:
    if value is None:
        return None
    item = _mapping(value)
    return CodeSdkSemanticArtifactProduction(
        provider_key=_required_str(item, "provider_key"),
        producer_key=_required_str(item, "producer_key"),
        producer_kind=_optional_str(item, "producer_kind"),
        provider_payload=_optional_object_mapping(item, "provider_payload"),
        input_code_package_id=_optional_uuid(item, "input_code_package_id"),
        input_object_instance_graph_commit_id=_optional_uuid(
            item,
            "input_object_instance_graph_commit_id",
        ),
        input_digest=_optional_str(item, "input_digest"),
        output_digest=_optional_str(item, "output_digest"),
        emission_payload=_optional_object_mapping(item, "emission_payload"),
    )


def _semantic_artifact_binding_payload(
    binding: CodeSdkSemanticArtifactBinding,
) -> dict[str, object]:
    return {
        "module_id": binding.module_id,
        "package_name": binding.package_name,
        "language": binding.language,
        "surface": binding.surface,
        "manifest_kind": binding.manifest_kind,
        "manifest_relative_path": binding.manifest_relative_path,
        "package_root": binding.package_root,
        "sources_root": binding.sources_root,
        "package_kind": binding.package_kind,
        "semantic_contract_provider_key": binding.semantic_contract_provider_key,
        "semantic_contract_role": binding.semantic_contract_role,
        "semantic_contract_name": binding.semantic_contract_name,
        "semantic_contract_module": binding.semantic_contract_module,
    }


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    raise TypeError(f"Expected mapping payload, got {type(value).__name__}.")


def _required_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if isinstance(value, str) and value.strip():
        return value
    raise ValueError(f"semantic ownership payload requires {key!r}.")


def _optional_str(mapping: Mapping[str, object], key: str) -> str | None:
    value = mapping.get(key)
    return value if isinstance(value, str) and value.strip() else None


def _required_int(mapping: Mapping[str, object], key: str) -> int:
    value = mapping.get(key)
    if isinstance(value, int):
        return value
    raise ValueError(f"semantic ownership payload requires integer {key!r}.")


def _required_bool(mapping: Mapping[str, object], key: str) -> bool:
    value = mapping.get(key)
    if isinstance(value, bool):
        return value
    raise ValueError(f"semantic ownership payload requires boolean {key!r}.")


def _optional_uuid(mapping: Mapping[str, object], key: str) -> UUID | None:
    value = mapping.get(key)
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        return UUID(value)
    raise ValueError(f"semantic ownership payload expected UUID for {key!r}.")


def _optional_string_mapping(
    mapping: Mapping[str, object],
    key: str,
) -> Mapping[str, str] | None:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        return None
    result = {
        str(item_key): item_value
        for item_key, item_value in value.items()
        if isinstance(item_value, str)
    }
    return result or None


def _optional_object_mapping(
    mapping: Mapping[str, object],
    key: str,
) -> Mapping[str, object] | None:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        return None
    return {str(item_key): item for item_key, item in value.items()}


__all__ = [
    "CodeSdkSemanticArtifactBinding",
    "CodeSdkSemanticArtifactLeafClaim",
    "CodeSdkSemanticArtifactProduction",
    "CodeSdkSemanticOwnershipProvider",
    "CodeSdkSemanticProviderOwnership",
    "ServiceBackedCodeSdkSemanticOwnershipProvider",
]
