from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, cast

from aware_code.module_plugin import AwareModulePlugin
from aware_code.module_semantic_contract import ModuleSemanticContract


WorkspaceActivation = Literal["always", "owner"]


@dataclass(frozen=True, slots=True)
class LanguageServiceProviderDescriptor:
    capability: str
    provider_key: str
    semantic_owner: str
    module_provider_key: str | None = None
    required_semantic_scope_keys: tuple[str, ...] = ()
    priority: int = 100
    applies_when: str = "always"
    workspace_activation: WorkspaceActivation = "owner"


def build_language_service_provider_descriptors_from_semantic_contract(
    contract: ModuleSemanticContract,
    *,
    plugin: AwareModulePlugin | None = None,
    capability: str | None = None,
) -> tuple[LanguageServiceProviderDescriptor, ...]:
    participation_by_key = {
        (descriptor.capability, descriptor.semantic_owner): descriptor
        for descriptor in contract.capability_participation
        if capability is None or descriptor.capability == capability
    }
    execution_policy_by_key = {
        (descriptor.capability, descriptor.semantic_owner): descriptor
        for descriptor in contract.capability_execution_policy
        if capability is None or descriptor.capability == capability
    }
    unknown_execution_policy_keys = tuple(
        sorted(set(execution_policy_by_key) - set(participation_by_key))
    )
    if unknown_execution_policy_keys:
        rendered = ", ".join(
            f"{capability_name}:{semantic_owner}"
            for capability_name, semantic_owner in unknown_execution_policy_keys
        )
        raise ValueError(
            f"{contract.provider_key} semantic contract defines execution policy without "
            f"capability participation for: {rendered}"
        )

    module_provider_key = (
        plugin.provider_key if plugin is not None else contract.provider_key
    ).strip()
    workspace_activation_by_capability = (
        {
            policy.capability: policy.workspace_activation
            for policy in plugin.capability_policy
        }
        if plugin is not None
        else {}
    )

    descriptors: list[LanguageServiceProviderDescriptor] = []
    for participation in contract.capability_participation:
        if capability is not None and participation.capability != capability:
            continue
        execution_policy = execution_policy_by_key.get(
            (participation.capability, participation.semantic_owner)
        )
        descriptors.append(
            LanguageServiceProviderDescriptor(
                capability=participation.capability,
                provider_key=participation.semantic_owner,
                semantic_owner=participation.semantic_owner,
                module_provider_key=module_provider_key or None,
                required_semantic_scope_keys=(
                    execution_policy.required_semantic_scope_keys
                    if execution_policy is not None
                    else ()
                ),
                priority=execution_policy.priority if execution_policy is not None else 100,
                applies_when=(
                    execution_policy.applies_when if execution_policy is not None else "always"
                ),
                workspace_activation=cast(
                    WorkspaceActivation,
                    workspace_activation_by_capability.get(
                        participation.capability,
                        "owner",
                    ),
                ),
            )
        )
    return tuple(
        sorted(
            descriptors,
            key=lambda item: (
                item.capability,
                item.priority,
                item.provider_key,
                item.semantic_owner,
            ),
        )
    )


def merge_language_service_provider_descriptors(
    *,
    capability: str,
    provider_descriptors: Iterable[LanguageServiceProviderDescriptor],
    registered_descriptors: Iterable[LanguageServiceProviderDescriptor] = (),
) -> tuple[LanguageServiceProviderDescriptor, ...]:
    descriptors: list[LanguageServiceProviderDescriptor] = []
    seen: set[tuple[str, str]] = set()

    for descriptor in provider_descriptors:
        if descriptor.capability != capability:
            continue
        key = (descriptor.capability, descriptor.provider_key)
        if key in seen:
            continue
        seen.add(key)
        descriptors.append(descriptor)

    for descriptor in registered_descriptors:
        if descriptor.capability != capability:
            continue
        key = (descriptor.capability, descriptor.provider_key)
        if key in seen:
            continue
        seen.add(key)
        descriptors.append(descriptor)

    return tuple(
        sorted(
            descriptors,
            key=lambda item: (
                item.priority,
                item.provider_key,
                item.semantic_owner,
            ),
        )
    )


__all__ = [
    "LanguageServiceProviderDescriptor",
    "WorkspaceActivation",
    "build_language_service_provider_descriptors_from_semantic_contract",
    "merge_language_service_provider_descriptors",
]
