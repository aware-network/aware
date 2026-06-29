from __future__ import annotations

from collections.abc import Iterable
from abc import ABC, abstractmethod
from pathlib import Path

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_scope.schemas import SemanticScopeResolution

from aware_utils.logging import logger


class SemanticScopeProvider(ABC):
    """Provider contract for module-owned semantic scopes resolved from code-package truth."""

    @property
    @abstractmethod
    def provider_key(self) -> str:
        """Stable provider key."""

    @property
    @abstractmethod
    def scope_keys(self) -> tuple[str, ...]:
        """Semantic scope keys this provider may resolve."""

    @abstractmethod
    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        """Return semantic-scope resolutions for the supplied code package."""


class SemanticScopeRegistry:
    """Singleton registry for module-owned semantic-scope providers."""

    _providers: dict[str, SemanticScopeProvider] = {}
    _builtin_bootstrap_attempted: bool = False

    @classmethod
    def register(cls, provider: SemanticScopeProvider) -> None:
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
        for plugin in AwareModulePluginRegistry.get_plugins():
            semantic_contract = (
                AwareModulePluginRegistry.module_semantic_contract_for_provider_key(
                    plugin.provider_key
                )
            )
            if semantic_contract is None or not semantic_contract.semantic_scope_keys:
                continue
            register_function = plugin.register_semantic_scope_providers
            if register_function is None:
                continue
            try:
                register_function()
            except Exception as exc:
                logger.warning(
                    "Semantic scope provider bootstrap failed for %s: %s",
                    plugin.provider_key,
                    exc,
                )

    @classmethod
    def get(cls, provider_key: str) -> SemanticScopeProvider:
        if provider_key not in cls._providers:
            raise KeyError(
                f"No semantic scope provider registered for key: {provider_key}"
            )
        return cls._providers[provider_key]

    @classmethod
    def get_provider_keys(cls) -> tuple[str, ...]:
        return tuple(sorted(cls._providers))

    @classmethod
    def resolve(
        cls,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
        provider_keys: Iterable[str] | None = None,
        scope_keys: Iterable[str] | None = None,
    ) -> tuple[SemanticScopeResolution, ...]:
        cls.ensure_builtin_providers_registered()
        if not cls._providers:
            return ()
        allowed_provider_keys = _normalize_scope_keys(provider_keys)
        if allowed_provider_keys is not None and not allowed_provider_keys:
            return ()
        allowed_scope_keys = _normalize_scope_keys(scope_keys)
        if allowed_scope_keys is not None and not allowed_scope_keys:
            return ()

        resolutions: list[SemanticScopeResolution] = []
        seen: set[tuple[str, str]] = set()
        for provider_key in sorted(cls._providers):
            if (
                allowed_provider_keys is not None
                and provider_key not in allowed_provider_keys
            ):
                continue
            provider = cls._providers[provider_key]
            if allowed_scope_keys is not None and not allowed_scope_keys.intersection(
                provider.scope_keys
            ):
                continue
            try:
                resolved = provider.resolve(
                    code_package,
                    workspace_root=workspace_root,
                )
            except Exception as exc:
                logger.warning(
                    "Semantic scope provider failed for code package %s (%s): %s",
                    code_package.name,
                    provider_key,
                    exc,
                )
                continue
            for resolution in resolved:
                if (
                    allowed_scope_keys is not None
                    and resolution.scope_key not in allowed_scope_keys
                ):
                    continue
                normalized = (
                    resolution
                    if resolution.provider_key == provider_key
                    else SemanticScopeResolution(
                        scope_key=resolution.scope_key,
                        provider_key=provider_key,
                        payload=resolution.payload,
                        materialization_dependencies=(
                            resolution.materialization_dependencies
                        ),
                        runtime_value=resolution.runtime_value,
                    )
                )
                key = (normalized.provider_key, normalized.scope_key)
                if key in seen:
                    continue
                seen.add(key)
                resolutions.append(normalized)
        return tuple(
            sorted(
                resolutions,
                key=lambda item: (item.scope_key, item.provider_key),
            )
        )

    @classmethod
    def clear(cls) -> None:
        cls._providers.clear()
        cls._builtin_bootstrap_attempted = False
        logger.info("Cleared all semantic scope providers")


def _normalize_scope_keys(scope_keys: Iterable[str] | None) -> frozenset[str] | None:
    if scope_keys is None:
        return None
    return frozenset(
        scope_key.strip()
        for scope_key in scope_keys
        if isinstance(scope_key, str) and scope_key.strip()
    )


__all__ = [
    "SemanticScopeProvider",
    "SemanticScopeRegistry",
]
