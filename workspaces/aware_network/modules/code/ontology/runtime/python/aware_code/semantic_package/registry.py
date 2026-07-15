from __future__ import annotations

from abc import ABC, abstractmethod

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.module_semantic_contract import ModuleSemanticContract
from aware_code.package_surface import (
    code_package_surface_from_semantic_manifest_descriptor,
)
from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package.schemas import SemanticPackageDescriptor

from aware_utils.logging import logger


class SemanticPackageProvider(ABC):
    """Provider contract for resolving semantic leaf provenance from a code package."""

    @property
    @abstractmethod
    def provider_key(self) -> str:
        """Stable provider key."""

    @abstractmethod
    def resolve(
        self, code_package: CodePackageInfo
    ) -> tuple[SemanticPackageDescriptor, ...]:
        """Return semantic leaf descriptors for the supplied code package."""


class SemanticPackageRegistry:
    """Singleton registry for semantic package provenance providers."""

    _providers: dict[str, SemanticPackageProvider] = {}
    _builtin_bootstrap_attempted: bool = False

    @classmethod
    def register(cls, provider: SemanticPackageProvider) -> None:
        if provider.provider_key not in cls._providers:
            cls._providers[provider.provider_key] = provider

    @classmethod
    def ensure_builtin_providers_registered(cls) -> None:
        if not cls._builtin_bootstrap_attempted:
            cls._builtin_bootstrap_attempted = True
            AwareModulePluginRegistry.ensure_builtin_plugins_registered()
        cls.refresh_from_registered_module_plugins()

    @classmethod
    def refresh_from_registered_module_plugins(cls) -> None:
        for contract in AwareModulePluginRegistry.get_module_semantic_contracts():
            if not _contract_declares_semantic_package_resolution(contract):
                continue
            cls.register(_SemanticContractPackageProvider(contract=contract))
        for plugin in AwareModulePluginRegistry.get_plugins():
            register_function = plugin.register_semantic_package_providers
            if register_function is None:
                continue
            try:
                register_function()
            except Exception as exc:
                logger.warning(
                    "Semantic package provider bootstrap failed for %s: %s",
                    plugin.provider_key,
                    exc,
                )

    @classmethod
    def get(cls, provider_key: str) -> SemanticPackageProvider:
        if provider_key not in cls._providers:
            raise KeyError(
                f"No semantic package provider registered for key: {provider_key}"
            )
        return cls._providers[provider_key]

    @classmethod
    def get_provider_keys(cls) -> tuple[str, ...]:
        return tuple(sorted(cls._providers))

    @classmethod
    def resolve(
        cls, code_package: CodePackageInfo
    ) -> tuple[SemanticPackageDescriptor, ...]:
        if not cls._providers:
            return ()

        descriptors: list[SemanticPackageDescriptor] = []
        seen: set[tuple[str, str, str, str | None, str | None]] = set()
        for provider_key in sorted(cls._providers):
            provider = cls._providers[provider_key]
            try:
                resolved = provider.resolve(code_package)
            except Exception as exc:
                logger.warning(
                    "Semantic package provider failed for code package %s (%s): %s",
                    code_package.name,
                    provider_key,
                    exc,
                )
                continue
            for descriptor in resolved:
                normalized = (
                    descriptor
                    if descriptor.provider_key == provider_key
                    else descriptor.model_copy(update={"provider_key": provider_key})
                )
                key = (
                    normalized.provider_key,
                    normalized.family,
                    normalized.semantic_kind,
                    normalized.package_name,
                    normalized.manifest_relative_path,
                )
                if key in seen:
                    continue
                seen.add(key)
                descriptors.append(normalized)
        return tuple(descriptors)

    @classmethod
    def enrich_code_package(cls, code_package: CodePackageInfo) -> CodePackageInfo:
        semantic_packages = cls.resolve(code_package)
        if not semantic_packages:
            return code_package
        merged = _merge_semantic_packages(
            existing=code_package.semantic_packages,
            incoming=semantic_packages,
        )
        metadata = _metadata_with_semantic_code_package_surface(
            code_package=code_package,
            semantic_packages=merged,
        )
        return code_package.model_copy(
            update={
                "metadata": metadata,
                "semantic_packages": merged,
            },
        )

    @classmethod
    def clear(cls) -> None:
        cls._providers.clear()
        cls._builtin_bootstrap_attempted = False
        logger.info("Cleared all semantic package providers")


def _contract_declares_semantic_package_resolution(
    contract: ModuleSemanticContract,
) -> bool:
    if contract.manifest_resolution:
        return True
    return any(role.owns_manifest_kinds for role in contract.package_roles)


def _merge_semantic_packages(
    *,
    existing: tuple[SemanticPackageDescriptor, ...],
    incoming: tuple[SemanticPackageDescriptor, ...],
) -> tuple[SemanticPackageDescriptor, ...]:
    if not existing:
        return incoming
    seen = {
        (
            descriptor.provider_key,
            descriptor.family,
            descriptor.semantic_kind,
            descriptor.package_name,
            descriptor.manifest_relative_path,
        )
        for descriptor in existing
    }
    merged = list(existing)
    for descriptor in incoming:
        key = (
            descriptor.provider_key,
            descriptor.family,
            descriptor.semantic_kind,
            descriptor.package_name,
            descriptor.manifest_relative_path,
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(descriptor)
    return tuple(merged)


def _metadata_with_semantic_code_package_surface(
    *,
    code_package: CodePackageInfo,
    semantic_packages: tuple[SemanticPackageDescriptor, ...],
) -> dict[str, object]:
    metadata = dict(code_package.metadata)
    if metadata.get("code_package_surface") is not None:
        return metadata

    manifest_kind = _optional_text(metadata.get("manifest_kind"))
    if manifest_kind is None:
        return metadata

    package_kind = _optional_text(metadata.get("package_kind"))
    surfaces: set[str] = set()
    for descriptor in semantic_packages:
        contract = AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
            descriptor.provider_key
        )
        if contract is None:
            continue
        for manifest_descriptor in contract.manifest_resolution_for(
            manifest_kind=manifest_kind,
        ):
            if (
                manifest_descriptor.semantic_package_family is not None
                and manifest_descriptor.semantic_package_family != descriptor.family
            ):
                continue
            if (
                manifest_descriptor.semantic_package_kind is not None
                and manifest_descriptor.semantic_package_kind
                != descriptor.semantic_kind
            ):
                continue
            surface = code_package_surface_from_semantic_manifest_descriptor(
                manifest_descriptor,
                package_kind=package_kind,
            )
            if surface is not None:
                surfaces.add(surface)

    if not surfaces:
        return metadata
    if len(surfaces) > 1:
        raise ValueError(
            "Semantic package providers resolved conflicting code_package_surface "
            f"values for {code_package.name}: {tuple(sorted(surfaces))}"
        )
    metadata["code_package_surface"] = next(iter(surfaces))
    return metadata


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


class _SemanticContractPackageProvider(SemanticPackageProvider):
    """Semantic package provider synthesized from a module semantic contract."""

    def __init__(self, *, contract: ModuleSemanticContract) -> None:
        self._contract = contract

    @property
    def provider_key(self) -> str:
        return self._contract.provider_key

    def resolve(
        self, code_package: CodePackageInfo
    ) -> tuple[SemanticPackageDescriptor, ...]:
        manifest_kind = _optional_text(code_package.metadata.get("manifest_kind"))
        if manifest_kind is None:
            return ()
        package_kind = _optional_text(code_package.metadata.get("package_kind"))
        descriptors: list[SemanticPackageDescriptor] = []
        for manifest_descriptor in self._contract.manifest_resolution_for(
            manifest_kind=manifest_kind,
        ):
            family = _optional_text(manifest_descriptor.semantic_package_family)
            semantic_kind = _optional_text(manifest_descriptor.semantic_package_kind)
            if family is None or semantic_kind is None:
                continue
            metadata = _semantic_package_metadata_from_contract(
                code_package=code_package,
                package_kind=package_kind,
                manifest_descriptor=manifest_descriptor,
            )
            descriptors.append(
                SemanticPackageDescriptor(
                    provider_key=self.provider_key,
                    family=family,
                    semantic_kind=semantic_kind,
                    package_name=code_package.name,
                    manifest_relative_path=code_package.manifest_path.as_posix(),
                    metadata=metadata,
                    semantic_scope_keys=self._contract.semantic_scope_keys,
                    capability_participation=(self._contract.capability_participation),
                    capability_profiles=self._contract.capability_profiles,
                    capability_bundles=self._contract.capability_bundles,
                )
            )
        return tuple(descriptors)


def _semantic_package_metadata_from_contract(
    *,
    code_package: CodePackageInfo,
    package_kind: str | None,
    manifest_descriptor: object,
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    for key in getattr(manifest_descriptor, "copy_code_package_metadata_keys", ()):
        if key in code_package.metadata:
            metadata[key] = code_package.metadata[key]

    surface = code_package_surface_from_semantic_manifest_descriptor(
        manifest_descriptor,
        package_kind=package_kind,
    )
    if surface is not None:
        metadata["code_package_surface"] = surface
    _put_optional(
        metadata,
        "package_kind",
        package_kind,
    )
    _put_optional(
        metadata,
        "workspace_materialization_primary",
        getattr(manifest_descriptor, "workspace_materialization_primary", None),
    )
    _put_optional(
        metadata,
        "workspace_materialization_order",
        getattr(manifest_descriptor, "workspace_materialization_order", None),
    )
    _put_optional(
        metadata,
        "workspace_materialization_branch",
        getattr(manifest_descriptor, "workspace_materialization_branch", None),
    )
    _put_optional(
        metadata,
        "workspace_materialization_commit",
        getattr(manifest_descriptor, "workspace_materialization_commit", None),
    )
    _put_optional(
        metadata,
        "semantic_projection_name",
        getattr(manifest_descriptor, "semantic_projection_name", None),
    )
    _put_optional(
        metadata,
        "semantic_root_kind",
        getattr(manifest_descriptor, "semantic_root_kind", None),
    )
    semantic_package_metadata = getattr(
        manifest_descriptor,
        "semantic_package_metadata",
        None,
    )
    if semantic_package_metadata is not None:
        metadata.update(dict(semantic_package_metadata))
    return metadata


def _put_optional(
    metadata: dict[str, object],
    key: str,
    value: object,
) -> None:
    if value is not None:
        metadata[key] = value


__all__ = [
    "SemanticPackageProvider",
    "SemanticPackageRegistry",
]
