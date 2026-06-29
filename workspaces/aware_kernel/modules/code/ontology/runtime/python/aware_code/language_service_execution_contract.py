from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from aware_code.language_service_provider_descriptor import (
    build_language_service_provider_descriptors_from_semantic_contract,
)
from aware_code.module_semantic_contract import ModuleSemanticContract


@dataclass(frozen=True, slots=True)
class LanguageServiceCapabilityExecutionEntrypoint:
    capability: str
    provider_key: str
    callable_module: str
    callable_name: str


@dataclass(frozen=True, slots=True)
class LanguageServiceModuleCapabilityExecutionContract:
    provider_key: str
    execution_module: str
    execution_entrypoints: tuple[LanguageServiceCapabilityExecutionEntrypoint, ...] = ()

    def execution_entrypoints_for(
        self,
        *,
        capability: str,
    ) -> tuple[LanguageServiceCapabilityExecutionEntrypoint, ...]:
        return tuple(
            item
            for item in self.execution_entrypoints
            if item.capability == capability
        )


def build_language_service_module_capability_execution_contract(
    *,
    provider_key: str,
    execution_module: str,
    execution_entrypoints: Iterable[LanguageServiceCapabilityExecutionEntrypoint],
) -> LanguageServiceModuleCapabilityExecutionContract:
    return LanguageServiceModuleCapabilityExecutionContract(
        provider_key=provider_key.strip(),
        execution_module=execution_module.strip(),
        execution_entrypoints=tuple(execution_entrypoints),
    )


def build_capability_execution_entrypoints_from_semantic_contract(
    contract: ModuleSemanticContract,
    *,
    callable_module: str,
    capability: str | None = None,
) -> tuple[LanguageServiceCapabilityExecutionEntrypoint, ...]:
    execution_policy_by_key = {
        (descriptor.capability, descriptor.semantic_owner): descriptor
        for descriptor in contract.capability_execution_policy
        if capability is None or descriptor.capability == capability
    }
    items: list[LanguageServiceCapabilityExecutionEntrypoint] = []
    seen: set[tuple[str, str]] = set()
    for descriptor in build_language_service_provider_descriptors_from_semantic_contract(
        contract,
        capability=capability,
    ):
        key = (descriptor.capability, descriptor.provider_key)
        if key in seen:
            continue
        seen.add(key)
        execution_policy = execution_policy_by_key.get(
            (descriptor.capability, descriptor.semantic_owner)
        )
        if execution_policy is None:
            raise ValueError(
                f"{contract.provider_key} execution contract missing execution policy "
                f"for {descriptor.capability}:{descriptor.semantic_owner}"
            )
        callable_name = (execution_policy.callable_name or "").strip()
        if not callable_name:
            raise ValueError(
                f"{contract.provider_key} execution contract missing callable name "
                f"for {descriptor.capability}:{descriptor.semantic_owner}"
            )
        items.append(
            LanguageServiceCapabilityExecutionEntrypoint(
                capability=descriptor.capability,
                provider_key=descriptor.provider_key,
                callable_module=execution_policy.callable_module or callable_module,
                callable_name=callable_name,
            )
        )
    return tuple(items)


def build_language_service_module_capability_execution_contract_from_semantic_contract(
    contract: ModuleSemanticContract,
    *,
    execution_module: str,
    callable_module: str,
    capability: str | None = None,
) -> LanguageServiceModuleCapabilityExecutionContract:
    return build_language_service_module_capability_execution_contract(
        provider_key=contract.provider_key,
        execution_module=execution_module,
        execution_entrypoints=build_capability_execution_entrypoints_from_semantic_contract(
            contract,
            callable_module=callable_module,
            capability=capability,
        ),
    )


__all__ = [
    "LanguageServiceCapabilityExecutionEntrypoint",
    "LanguageServiceModuleCapabilityExecutionContract",
    "build_capability_execution_entrypoints_from_semantic_contract",
    "build_language_service_module_capability_execution_contract_from_semantic_contract",
    "build_language_service_module_capability_execution_contract",
]
