from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from aware_code.module_plugin import AwareModulePlugin
from aware_code.language_service_provider_descriptor import (
    WorkspaceActivation,
    build_language_service_provider_descriptors_from_semantic_contract,
)
from aware_code.module_semantic_contract import ModuleSemanticContract
from aware_code.semantic_package.schemas import CapabilityParticipationDescriptor


ModulePluginWorkspaceActivation = WorkspaceActivation


@dataclass(frozen=True, slots=True)
class LanguageServiceCapabilityMetadata:
    capability: str
    semantic_owner: str
    provider_key: str | None = None
    required_semantic_scope_keys: tuple[str, ...] = ()
    priority: int = 100
    applies_when: str = "always"
    workspace_activation: ModulePluginWorkspaceActivation = "owner"
    default_enabled: bool = True

    @property
    def resolved_provider_key(self) -> str:
        provider_key = (self.provider_key or "").strip()
        return provider_key or self.semantic_owner


@dataclass(frozen=True, slots=True)
class LanguageServiceModuleCapabilityContract:
    provider_key: str
    contract_module: str
    capability_metadata: tuple[LanguageServiceCapabilityMetadata, ...]

    def capability_metadata_for(
        self,
        *,
        capability: str,
    ) -> tuple[LanguageServiceCapabilityMetadata, ...]:
        return tuple(
            item
            for item in self.capability_metadata
            if item.capability == capability
        )


def build_language_service_module_capability_contract(
    *,
    provider_key: str,
    contract_module: str,
    capability_metadata: Iterable[LanguageServiceCapabilityMetadata],
) -> LanguageServiceModuleCapabilityContract:
    return LanguageServiceModuleCapabilityContract(
        provider_key=provider_key.strip(),
        contract_module=contract_module.strip(),
        capability_metadata=tuple(capability_metadata),
    )


def build_language_service_capability_metadata_from_semantic_contract(
    contract: ModuleSemanticContract,
    *,
    plugin: AwareModulePlugin | None = None,
    capability: str | None = None,
) -> tuple[LanguageServiceCapabilityMetadata, ...]:
    participation_by_key = {
        (descriptor.capability, descriptor.semantic_owner): descriptor
        for descriptor in contract.capability_participation
        if capability is None or descriptor.capability == capability
    }

    metadata: list[LanguageServiceCapabilityMetadata] = []
    for descriptor in build_language_service_provider_descriptors_from_semantic_contract(
        contract,
        plugin=plugin,
        capability=capability,
    ):
        participation = participation_by_key[(descriptor.capability, descriptor.semantic_owner)]
        metadata.append(
            LanguageServiceCapabilityMetadata(
                capability=descriptor.capability,
                semantic_owner=descriptor.semantic_owner,
                provider_key=(
                    descriptor.provider_key
                    if descriptor.provider_key != descriptor.semantic_owner
                    else None
                ),
                required_semantic_scope_keys=descriptor.required_semantic_scope_keys,
                priority=descriptor.priority,
                applies_when=descriptor.applies_when,
                workspace_activation=descriptor.workspace_activation,
                default_enabled=bool(participation.default_enabled),
            )
        )
    return tuple(
        sorted(
            metadata,
            key=lambda item: (
                item.capability,
                item.priority,
                item.resolved_provider_key,
                item.semantic_owner,
            ),
        )
    )


def build_language_service_module_capability_contract_from_semantic_contract(
    contract: ModuleSemanticContract,
    *,
    contract_module: str,
    plugin: AwareModulePlugin | None = None,
    capability: str | None = None,
) -> LanguageServiceModuleCapabilityContract:
    return build_language_service_module_capability_contract(
        provider_key=contract.provider_key,
        contract_module=contract_module,
        capability_metadata=build_language_service_capability_metadata_from_semantic_contract(
            contract,
            plugin=plugin,
            capability=capability,
        ),
    )


def build_capability_participation_descriptors(
    metadata: Iterable[LanguageServiceCapabilityMetadata],
    *,
    capability: str | None = None,
) -> tuple[CapabilityParticipationDescriptor, ...]:
    items: list[CapabilityParticipationDescriptor] = []
    seen: set[tuple[str, str]] = set()
    for descriptor in metadata:
        if capability is not None and descriptor.capability != capability:
            continue
        key = (descriptor.capability, descriptor.semantic_owner)
        if key in seen:
            continue
        seen.add(key)
        items.append(
            CapabilityParticipationDescriptor(
                capability=descriptor.capability,
                semantic_owner=descriptor.semantic_owner,
                default_enabled=descriptor.default_enabled,
            )
        )
    return tuple(items)


__all__ = [
    "build_language_service_capability_metadata_from_semantic_contract",
    "build_language_service_module_capability_contract_from_semantic_contract",
    "LanguageServiceCapabilityMetadata",
    "LanguageServiceModuleCapabilityContract",
    "ModulePluginWorkspaceActivation",
    "build_language_service_module_capability_contract",
    "build_capability_participation_descriptors",
]
