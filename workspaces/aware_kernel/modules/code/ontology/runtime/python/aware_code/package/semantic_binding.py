"""CodePackage semantic binding execution resolver."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import sys
from types import ModuleType
from typing import Protocol

from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor,
    WorkspaceActivation,
)


_PACKAGE_SEMANTIC_BINDING_CAPABILITY_FUNCTIONS: dict[str, str] = {
    "diagnostics": "diagnostics",
    "semantic_analysis": "semantic_analysis",
    "semantic_tokens": "semantic_tokens",
}


class PackageSemanticBindingDeclaration(Protocol):
    @property
    def role(self) -> str: ...

    @property
    def contract(self) -> str: ...

    @property
    def binding_module(self) -> str | None: ...

    @property
    def capabilities(self) -> tuple[str, ...]: ...

    @property
    def callable_name(self) -> str | None: ...


class PackageSemanticContractBindingDeclaration(Protocol):
    @property
    def capability(self) -> str: ...

    @property
    def module(self) -> str: ...

    @property
    def callable(self) -> str: ...


class PackageSemanticContractDeclaration(Protocol):
    @property
    def role(self) -> str: ...

    @property
    def contract(self) -> str: ...

    @property
    def provider_key(self) -> str: ...

    @property
    def module(self) -> str: ...

    @property
    def bindings(self) -> tuple[PackageSemanticContractBindingDeclaration, ...]: ...


@dataclass(frozen=True, slots=True)
class ResolvedPackageSemanticBindingProvider:
    capability: str
    provider_key: str
    semantic_owner: str
    contract: str
    binding_module: str
    callable_name: str
    module_runtime_root: Path
    provider: Callable[..., object]


def package_semantic_binding_callable_name(*, capability: str) -> str | None:
    return _PACKAGE_SEMANTIC_BINDING_CAPABILITY_FUNCTIONS.get(capability)


def package_semantic_contract_provider_descriptors(
    *,
    capability: str,
    semantic_contract: PackageSemanticContractDeclaration | None,
    priority: int = 25,
    workspace_activation: WorkspaceActivation = "owner",
) -> tuple[LanguageServiceProviderDescriptor, ...]:
    if (
        semantic_contract is None
        or package_semantic_binding_callable_name(capability=capability) is None
    ):
        return ()

    module_provider_key = semantic_contract.provider_key.strip() or None
    return tuple(
        sorted(
            (
                LanguageServiceProviderDescriptor(
                    capability=capability,
                    provider_key=semantic_contract.role,
                    semantic_owner=semantic_contract.role,
                    module_provider_key=module_provider_key,
                    priority=priority,
                    workspace_activation=workspace_activation,
                )
                for binding in semantic_contract.bindings
                if binding.capability == capability
                and binding.module.strip()
                and binding.callable.strip()
            ),
            key=lambda item: (
                item.priority,
                item.provider_key,
                item.semantic_owner,
            ),
        )
    )


def package_semantic_binding_provider_descriptors(
    *,
    capability: str,
    module_provider_key: str,
    semantic_bindings: Iterable[PackageSemanticBindingDeclaration],
    priority: int = 25,
    workspace_activation: WorkspaceActivation = "owner",
) -> tuple[LanguageServiceProviderDescriptor, ...]:
    if package_semantic_binding_callable_name(capability=capability) is None:
        return ()

    normalized_module_provider_key = module_provider_key.strip() or None
    return tuple(
        sorted(
            (
                LanguageServiceProviderDescriptor(
                    capability=capability,
                    provider_key=binding.role,
                    semantic_owner=binding.role,
                    module_provider_key=normalized_module_provider_key,
                    priority=priority,
                    workspace_activation=workspace_activation,
                )
                for binding in semantic_bindings
                if binding.binding_module is not None
                and capability in binding.capabilities
            ),
            key=lambda item: (
                item.priority,
                item.provider_key,
                item.semantic_owner,
            ),
        )
    )


def resolve_package_semantic_contract_providers(
    *,
    capability: str,
    workspace_root: Path,
    module_root_relative_path: str,
    semantic_contract: PackageSemanticContractDeclaration | None,
    provider_keys: Iterable[str],
) -> tuple[ResolvedPackageSemanticBindingProvider, ...]:
    if (
        semantic_contract is None
        or package_semantic_binding_callable_name(capability=capability) is None
    ):
        return ()

    selected_provider_keys = _normalize_provider_keys(provider_keys)
    if not selected_provider_keys or semantic_contract.role not in selected_provider_keys:
        return ()

    module_runtime_root = (
        workspace_root.resolve()
        / module_root_relative_path
        / "runtime"
    ).resolve()
    resolved: list[ResolvedPackageSemanticBindingProvider] = []
    for binding in semantic_contract.bindings:
        if binding.capability != capability:
            continue
        module = _import_binding_module(
            module_name=binding.module,
            module_runtime_root=module_runtime_root,
        )
        if module is None:
            continue
        provider = getattr(module, binding.callable, None)
        if not callable(provider):
            continue
        resolved.append(
            ResolvedPackageSemanticBindingProvider(
                capability=capability,
                provider_key=semantic_contract.role,
                semantic_owner=semantic_contract.role,
                contract=semantic_contract.contract,
                binding_module=binding.module,
                callable_name=binding.callable,
                module_runtime_root=module_runtime_root,
                provider=provider,
            )
        )
    return tuple(resolved)


def resolve_package_semantic_binding_providers(
    *,
    capability: str,
    workspace_root: Path,
    module_root_relative_path: str,
    semantic_bindings: Iterable[PackageSemanticBindingDeclaration],
    provider_keys: Iterable[str],
) -> tuple[ResolvedPackageSemanticBindingProvider, ...]:
    callable_name = package_semantic_binding_callable_name(capability=capability)
    if callable_name is None:
        return ()

    selected_provider_keys = _normalize_provider_keys(provider_keys)
    if not selected_provider_keys:
        return ()

    module_runtime_root = (
        workspace_root.resolve()
        / module_root_relative_path
        / "runtime"
    ).resolve()
    resolved: list[ResolvedPackageSemanticBindingProvider] = []
    for binding in semantic_bindings:
        if (
            binding.role not in selected_provider_keys
            or binding.binding_module is None
            or capability not in binding.capabilities
        ):
            continue
        binding_callable_name = getattr(binding, "callable_name", None) or callable_name
        module = _import_binding_module(
            module_name=binding.binding_module,
            module_runtime_root=module_runtime_root,
        )
        if module is None:
            continue
        provider = getattr(module, binding_callable_name, None)
        if not callable(provider):
            continue
        resolved.append(
            ResolvedPackageSemanticBindingProvider(
                capability=capability,
                provider_key=binding.role,
                semantic_owner=binding.role,
                contract=binding.contract,
                binding_module=binding.binding_module,
                callable_name=binding_callable_name,
                module_runtime_root=module_runtime_root,
                provider=provider,
            )
        )
    return tuple(resolved)


def package_semantic_contract_provider_map(
    *,
    capability: str,
    workspace_root: Path,
    module_root_relative_path: str,
    semantic_contract: PackageSemanticContractDeclaration | None,
    provider_keys: Iterable[str],
) -> dict[str, Callable[..., object]]:
    return {
        resolved.provider_key: resolved.provider
        for resolved in resolve_package_semantic_contract_providers(
            capability=capability,
            workspace_root=workspace_root,
            module_root_relative_path=module_root_relative_path,
            semantic_contract=semantic_contract,
            provider_keys=provider_keys,
        )
    }


def package_semantic_binding_provider_map(
    *,
    capability: str,
    workspace_root: Path,
    module_root_relative_path: str,
    semantic_bindings: Iterable[PackageSemanticBindingDeclaration],
    provider_keys: Iterable[str],
) -> dict[str, Callable[..., object]]:
    return {
        resolved.provider_key: resolved.provider
        for resolved in resolve_package_semantic_binding_providers(
            capability=capability,
            workspace_root=workspace_root,
            module_root_relative_path=module_root_relative_path,
            semantic_bindings=semantic_bindings,
            provider_keys=provider_keys,
        )
    }


def _normalize_provider_keys(values: Iterable[str]) -> frozenset[str]:
    return frozenset(
        value.strip()
        for value in values
        if isinstance(value, str) and value.strip()
    )


def _import_binding_module(
    *,
    module_name: str,
    module_runtime_root: Path,
) -> ModuleType | None:
    module = _import_optional_module(module_name)
    if module is not None:
        return module

    if not module_runtime_root.is_dir():
        return None

    runtime_root_text = module_runtime_root.as_posix()
    inserted = False
    if runtime_root_text not in sys.path:
        sys.path.insert(0, runtime_root_text)
        inserted = True
    try:
        return _import_optional_module(module_name)
    finally:
        if inserted:
            try:
                sys.path.remove(runtime_root_text)
            except ValueError:
                pass


def _import_optional_module(module_name: str) -> ModuleType | None:
    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        missing_name = exc.name or ""
        if missing_name and not module_name.startswith(missing_name):
            raise
        return None
