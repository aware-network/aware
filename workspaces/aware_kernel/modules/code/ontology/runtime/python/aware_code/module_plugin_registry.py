from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from importlib import import_module
from pathlib import Path
import sys
from typing import TYPE_CHECKING, cast

from aware_code.language_service_capability_contract import (
    LanguageServiceModuleCapabilityContract,
    build_language_service_module_capability_contract_from_semantic_contract,
)
from aware_code.language_service_execution_contract import (
    LanguageServiceCapabilityExecutionEntrypoint,
    LanguageServiceModuleCapabilityExecutionContract,
    build_language_service_module_capability_execution_contract_from_semantic_contract,
)
from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor,
    build_language_service_provider_descriptors_from_semantic_contract,
    merge_language_service_provider_descriptors,
)
from aware_code.code_module_contract import CodeModuleContract
from aware_code.module_semantic_contract import (
    AWARE_MODULE_SEMANTIC_CONTRACT_EXPORT_NAME,
    ModuleSemanticContract,
    ModuleSemanticGrammarRuleDescriptor,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor,
    ModuleSemanticMaterializationExecutionContextDescriptor,
    ModuleSemanticMaterializationInputDescriptor,
    ModuleSemanticLanguageMaterializationProfileDescriptor,
    ModuleSemanticMaterializationPackageOutputDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationToolingDescriptor,
    WorkspaceSemanticArtifactLeafOwnershipResolver,
)
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_CAPABILITY,
    SemanticPackageMaterializationExecutionContextRequest,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_code.module_code_package_materialization_contract import (
    AWARE_MODULE_CODE_PACKAGE_MATERIALIZATION_CONTRACT_EXPORT_NAME,
    ModuleCodePackageMaterializationContract,
)
from aware_code.module_plugin import (
    AwareModulePackageContract,
    AwareModulePackageSemanticBindingContract,
    AwareModulePackageSemanticContract,
    AwareModulePackageSemanticContractBinding,
    AwareModulePlugin,
    AwareModulePluginCapabilityPolicy,
    WorkspaceActivation as ModulePluginWorkspaceActivation,
)
from aware_code.module_manifest.loader import (
    AwareModuleTomlError,
    load_aware_module_spec,
)
from aware_utils.logging import logger

if TYPE_CHECKING:
    from aware_code.language.plugin import CodeLanguagePlugin


_AWARE_MODULE_PLUGIN_EXPORT_NAME = "AWARE_MODULE_PLUGIN"
_CODE_MODULE_PLUGIN_KIND = "code.module_plugin"
_SEMANTIC_PROVIDER_CONTRACT = "aware.semantic_provider"


@dataclass(frozen=True, slots=True)
class _AwarePluginBootstrapSpec:
    provider_key: str | None = None
    module_path: str | None = None
    runtime_root: Path | None = None
    capability_contract_module: str | None = None
    capability_execution_module: str | None = None
    semantic_contract_module: str | None = None
    code_package_materialization_contract_module: str | None = None
    packages: tuple[AwareModulePackageContract, ...] = ()
    capability_policy: tuple[AwareModulePluginCapabilityPolicy, ...] = ()
    code_language_plugin_module: str | None = None
    code_language_plugin_export_name: str | None = None
    code_language_plugin_required: bool = True
    meta_language_plugin_module: str | None = None
    meta_language_plugin_export_name: str | None = None
    meta_language_plugin_required: bool = True


@dataclass(frozen=True, slots=True)
class ResolvedLanguageServiceCapabilityProvider:
    descriptor: LanguageServiceProviderDescriptor
    provider: Callable[..., object]


@dataclass(frozen=True, slots=True)
class ResolvedSemanticCapabilityProvider:
    capability: str
    provider_key: str
    semantic_owner: str
    callable_module: str
    callable_name: str
    provider: Callable[..., object]
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResolvedSemanticArtifactLeafOwnershipResolver:
    provider_key: str
    semantic_owner: str
    callable_module: str
    callable_name: str
    resolver: WorkspaceSemanticArtifactLeafOwnershipResolver


@dataclass(frozen=True, slots=True)
class ResolvedSemanticMaterializationExecutionContextResolver:
    provider_key: str
    semantic_owner: str
    context_key: str
    callable_module: str
    callable_name: str
    required: bool
    provider_payload: Mapping[str, object]
    resolver: Callable[
        [SemanticPackageMaterializationExecutionContextRequest],
        object,
    ]


@dataclass(frozen=True, slots=True)
class ResolvedSemanticMaterializationRuntimeContextResolver:
    provider_key: str
    semantic_owner: str
    callable_module: str
    callable_name: str
    required: bool
    provider_payload: Mapping[str, object]
    resolver: Callable[
        [SemanticPackageMaterializationRuntimeContextRequest],
        object,
    ]


_BUILTIN_PLUGIN_BOOTSTRAP_SPECS: tuple[_AwarePluginBootstrapSpec, ...] = (
    _AwarePluginBootstrapSpec(
        provider_key="aware_grammar",
        capability_contract_module="aware_grammar.language_service_capability_metadata",
        capability_execution_module="aware_grammar.language_service_capabilities",
        semantic_contract_module="aware_grammar.semantic_contract",
        code_package_materialization_contract_module="aware_grammar.code_package_materialization_contract",
        capability_policy=(
            AwareModulePluginCapabilityPolicy(
                capability="semantic_tokens",
                workspace_activation="always",
                workspace_fallback=True,
            ),
        ),
        code_language_plugin_module="aware_grammar.code_language_plugin",
        code_language_plugin_export_name="AWARE_CODE_PLUGIN",
        meta_language_plugin_module="aware_grammar.meta_language_plugin",
        meta_language_plugin_export_name="AWARE_META_PLUGIN",
    ),
    _AwarePluginBootstrapSpec(
        provider_key="aware_code",
        capability_contract_module="aware_code.language_service_capability_metadata",
        capability_execution_module="aware_code.language_service_capabilities",
        semantic_contract_module="aware_code.semantic_contract",
        capability_policy=(
            AwareModulePluginCapabilityPolicy(
                capability="semantic_tokens",
                workspace_activation="always",
                workspace_fallback=True,
            ),
        ),
    ),
    _AwarePluginBootstrapSpec(
        code_language_plugin_module="sql_grammar.code_language_plugin",
        code_language_plugin_export_name="SQL_CODE_PLUGIN",
        meta_language_plugin_module="sql_grammar.meta_language_plugin",
        meta_language_plugin_export_name="SQL_META_PLUGIN",
    ),
    _AwarePluginBootstrapSpec(
        code_language_plugin_module="python_grammar.code_language_plugin",
        code_language_plugin_export_name="PYTHON_CODE_PLUGIN",
        meta_language_plugin_module="python_grammar.meta_language_plugin",
        meta_language_plugin_export_name="PYTHON_META_PLUGIN",
    ),
    _AwarePluginBootstrapSpec(
        code_language_plugin_module="dart_grammar.code_language_plugin",
        code_language_plugin_export_name="DART_CODE_PLUGIN",
        code_language_plugin_required=False,
        meta_language_plugin_module="dart_grammar.meta_language_plugin",
        meta_language_plugin_export_name="DART_META_PLUGIN",
        meta_language_plugin_required=False,
    ),
    _AwarePluginBootstrapSpec(
        provider_key="aware_workspace",
        semantic_contract_module="aware_workspace.semantic_contract",
    ),
)


class AwareModulePluginRegistry:
    """Singleton registry for module-owned Workspace/LSP execution plugins."""

    _plugins: dict[str, AwareModulePlugin] = {}
    _language_service_capability_contracts: dict[
        str, LanguageServiceModuleCapabilityContract | None
    ] = {}
    _language_service_capability_execution_contracts: dict[
        str, LanguageServiceModuleCapabilityExecutionContract | None
    ] = {}
    _module_semantic_contracts: dict[str, ModuleSemanticContract | None] = {}
    _module_code_package_materialization_contracts: dict[
        str, ModuleCodePackageMaterializationContract | None
    ] = {}
    _code_module_contracts: dict[str, CodeModuleContract | None] = {}
    _language_service_provider_descriptors: dict[
        str, tuple[LanguageServiceProviderDescriptor, ...]
    ] = {}
    _language_service_capability_providers: dict[
        tuple[str, str], Callable[..., object] | None
    ] = {}
    _semantic_capability_providers: dict[
        tuple[str, str, str | None], ResolvedSemanticCapabilityProvider | None
    ] = {}
    _builtin_code_language_plugins: tuple["CodeLanguagePlugin[object]", ...] | None = (
        None
    )
    _builtin_meta_language_plugins: tuple[object, ...] | None = None
    _builtin_bootstrap_attempted: bool = False

    @classmethod
    def register(
        cls,
        plugin: AwareModulePlugin,
        *,
        replace_existing: bool = False,
    ) -> None:
        existing = cls._plugins.get(plugin.provider_key)
        if existing is None:
            cls._plugins[plugin.provider_key] = plugin
            return
        if not replace_existing or _plugin_bootstrap_equivalent(existing, plugin):
            return
        cls._plugins[plugin.provider_key] = plugin
        cls._invalidate_provider_cache(provider_key=plugin.provider_key)

    @classmethod
    def ensure_builtin_plugins_registered(cls) -> None:
        if cls._builtin_bootstrap_attempted:
            return
        cls._builtin_bootstrap_attempted = True
        for spec in _BUILTIN_PLUGIN_BOOTSTRAP_SPECS:
            cls._register_plugin_bootstrap_spec(spec)

    @classmethod
    def ensure_module_plugins_registered_from_repo_root(
        cls,
        *,
        repo_root: Path,
        replace_existing: bool = False,
    ) -> None:
        resolved_repo_root = repo_root.expanduser().resolve()
        for spec in _BUILTIN_PLUGIN_BOOTSTRAP_SPECS:
            cls._register_plugin_bootstrap_spec(
                spec,
                replace_existing=replace_existing,
            )
        for spec in _module_plugin_bootstrap_specs_from_manifests(
            repo_root=resolved_repo_root,
        ):
            cls._register_plugin_bootstrap_spec(
                spec,
                replace_existing=replace_existing,
            )

    @classmethod
    def ensure_module_plugins_registered_from_module_roots(
        cls,
        *,
        module_roots: Iterable[Path],
        replace_existing: bool = False,
    ) -> None:
        for spec in _BUILTIN_PLUGIN_BOOTSTRAP_SPECS:
            cls._register_plugin_bootstrap_spec(
                spec,
                replace_existing=replace_existing,
            )
        seen: set[str] = set()
        for module_root in tuple(module_roots):
            spec = _module_plugin_bootstrap_spec_from_manifest(
                module_root=module_root.expanduser().resolve(),
            )
            if spec is None:
                continue
            spec_key = (spec.provider_key or "").strip() or (
                spec.module_path or ""
            ).strip()
            if not spec_key or spec_key in seen:
                continue
            seen.add(spec_key)
            cls._register_plugin_bootstrap_spec(
                spec,
                replace_existing=replace_existing,
            )

    @classmethod
    def get(cls, provider_key: str) -> AwareModulePlugin:
        if provider_key not in cls._plugins:
            raise KeyError(f"No module plugin registered for key: {provider_key}")
        return cls._plugins[provider_key]

    @classmethod
    def get_plugins(cls) -> tuple[AwareModulePlugin, ...]:
        return tuple(cls._plugins.values())

    @classmethod
    def get_provider_keys(cls) -> tuple[str, ...]:
        return tuple(cls._plugins)

    @classmethod
    def clear(cls) -> None:
        cls._plugins.clear()
        cls._language_service_capability_contracts.clear()
        cls._language_service_capability_execution_contracts.clear()
        cls._module_semantic_contracts.clear()
        cls._module_code_package_materialization_contracts.clear()
        cls._code_module_contracts.clear()
        cls._language_service_provider_descriptors.clear()
        cls._language_service_capability_providers.clear()
        cls._semantic_capability_providers.clear()
        cls._builtin_code_language_plugins = None
        cls._builtin_meta_language_plugins = None
        cls._builtin_bootstrap_attempted = False
        logger.info("Cleared all module plugins")

    @classmethod
    def _invalidate_provider_cache(cls, *, provider_key: str) -> None:
        cls._language_service_capability_contracts.pop(provider_key, None)
        cls._language_service_capability_execution_contracts.pop(provider_key, None)
        cls._module_semantic_contracts.pop(provider_key, None)
        cls._module_code_package_materialization_contracts.pop(provider_key, None)
        cls._code_module_contracts.pop(provider_key, None)
        cls._language_service_provider_descriptors.pop(provider_key, None)
        for cache_key in tuple(cls._language_service_capability_providers):
            if len(cache_key) >= 2 and cache_key[1] == provider_key:
                cls._language_service_capability_providers.pop(cache_key, None)
        for cache_key in tuple(cls._semantic_capability_providers):
            if len(cache_key) >= 2 and cache_key[1] == provider_key:
                cls._semantic_capability_providers.pop(cache_key, None)

    @classmethod
    def get_builtin_code_language_plugins(
        cls,
    ) -> tuple["CodeLanguagePlugin[object]", ...]:
        cached = cls._builtin_code_language_plugins
        if cached is not None:
            return cached

        plugins = tuple(
            cast("CodeLanguagePlugin[object]", plugin)
            for spec in _BUILTIN_PLUGIN_BOOTSTRAP_SPECS
            for plugin in (
                _load_optional_export(
                    module_path=spec.code_language_plugin_module,
                    export_name=spec.code_language_plugin_export_name,
                    required=spec.code_language_plugin_required,
                ),
            )
            if plugin is not None
        )
        cls._builtin_code_language_plugins = plugins
        return plugins

    @classmethod
    def get_builtin_meta_language_plugins(cls) -> tuple[object, ...]:
        cached = cls._builtin_meta_language_plugins
        if cached is not None:
            return cached

        plugins = tuple(
            cast(object, plugin)
            for spec in _BUILTIN_PLUGIN_BOOTSTRAP_SPECS
            for plugin in (
                _load_optional_export(
                    module_path=spec.meta_language_plugin_module,
                    export_name=spec.meta_language_plugin_export_name,
                    required=spec.meta_language_plugin_required,
                ),
            )
            if plugin is not None
        )
        cls._builtin_meta_language_plugins = plugins
        return plugins

    @classmethod
    def capability_contract_module_for_provider_key(
        cls,
        provider_key: str,
    ) -> str | None:
        plugin = cls._plugins.get(provider_key)
        if plugin is None:
            return None
        capability_contract_module = (plugin.capability_contract_module or "").strip()
        return capability_contract_module or None

    @classmethod
    def semantic_contract_module_for_provider_key(
        cls,
        provider_key: str,
    ) -> str | None:
        plugin = cls._plugins.get(provider_key)
        if plugin is None:
            return None
        semantic_contract_module = (plugin.semantic_contract_module or "").strip()
        return semantic_contract_module or None

    @classmethod
    def code_package_materialization_contract_module_for_provider_key(
        cls,
        provider_key: str,
    ) -> str | None:
        plugin = cls._plugins.get(provider_key)
        if plugin is None:
            return None
        materialization_contract_module = (
            plugin.code_package_materialization_contract_module or ""
        ).strip()
        return materialization_contract_module or None

    @classmethod
    def capability_execution_module_for_provider_key(
        cls,
        provider_key: str,
    ) -> str | None:
        plugin = cls._plugins.get(provider_key)
        if plugin is None:
            return None
        capability_execution_module = (plugin.capability_execution_module or "").strip()
        return capability_execution_module or None

    @classmethod
    def workspace_fallback_provider_keys_for_capability(
        cls,
        *,
        capability: str,
    ) -> tuple[str, ...]:
        cls.ensure_builtin_plugins_registered()
        provider_keys = {
            plugin.provider_key
            for plugin in cls._plugins.values()
            if any(
                policy.capability == capability and policy.workspace_fallback
                for policy in plugin.capability_policy
            )
        }
        return tuple(sorted(provider_keys))

    @classmethod
    def get_capability_execution_module_paths(cls) -> tuple[str, ...]:
        modules = {
            plugin.capability_execution_module.strip()
            for plugin in cls._plugins.values()
            if plugin.capability_execution_module is not None
            and plugin.capability_execution_module.strip()
        }
        return tuple(sorted(modules))

    @classmethod
    def get_capability_contract_module_paths(cls) -> tuple[str, ...]:
        modules = {
            plugin.capability_contract_module.strip()
            for plugin in cls._plugins.values()
            if plugin.capability_contract_module is not None
            and plugin.capability_contract_module.strip()
        }
        return tuple(sorted(modules))

    @classmethod
    def get_semantic_contract_module_paths(cls) -> tuple[str, ...]:
        modules = {
            plugin.semantic_contract_module.strip()
            for plugin in cls._plugins.values()
            if plugin.semantic_contract_module is not None
            and plugin.semantic_contract_module.strip()
        }
        return tuple(sorted(modules))

    @classmethod
    def get_code_package_materialization_contract_module_paths(cls) -> tuple[str, ...]:
        modules = {
            plugin.code_package_materialization_contract_module.strip()
            for plugin in cls._plugins.values()
            if plugin.code_package_materialization_contract_module is not None
            and plugin.code_package_materialization_contract_module.strip()
        }
        return tuple(sorted(modules))

    @classmethod
    def language_service_capability_contract_for_provider_key(
        cls,
        provider_key: str,
    ) -> LanguageServiceModuleCapabilityContract | None:
        cls.ensure_builtin_plugins_registered()
        cached = cls._language_service_capability_contracts.get(provider_key)
        if (
            cached is not None
            or provider_key in cls._language_service_capability_contracts
        ):
            return cached

        capability_contract_module = cls.capability_contract_module_for_provider_key(
            provider_key
        )
        if capability_contract_module is None:
            cls._language_service_capability_contracts[provider_key] = None
            return None

        semantic_contract = cls.module_semantic_contract_for_provider_key(provider_key)
        if semantic_contract is None:
            cls._language_service_capability_contracts[provider_key] = None
            return None

        try:
            import_module(capability_contract_module)
        except ModuleNotFoundError:
            cls._language_service_capability_contracts[provider_key] = None
            return None

        try:
            contract = build_language_service_module_capability_contract_from_semantic_contract(
                semantic_contract,
                contract_module=capability_contract_module,
                plugin=cls._plugins.get(provider_key),
            )
        except ValueError as exc:
            logger.warning(
                "Aware module capability contract could not be synthesized for %s in %s: %s",
                provider_key,
                capability_contract_module,
                exc,
            )
            cls._language_service_capability_contracts[provider_key] = None
            return None

        normalized = _normalize_capability_contract(
            contract=contract,
            provider_key=provider_key,
            capability_contract_module=capability_contract_module,
        )
        cls._language_service_capability_contracts[provider_key] = normalized
        return normalized

    @classmethod
    def language_service_capability_execution_contract_for_provider_key(
        cls,
        provider_key: str,
    ) -> LanguageServiceModuleCapabilityExecutionContract | None:
        cls.ensure_builtin_plugins_registered()
        cached = cls._language_service_capability_execution_contracts.get(provider_key)
        if (
            cached is not None
            or provider_key in cls._language_service_capability_execution_contracts
        ):
            return cached

        capability_execution_module = cls.capability_execution_module_for_provider_key(
            provider_key
        )
        if capability_execution_module is None:
            cls._language_service_capability_execution_contracts[provider_key] = None
            return None

        semantic_contract = cls.module_semantic_contract_for_provider_key(provider_key)
        if semantic_contract is None:
            cls._language_service_capability_execution_contracts[provider_key] = None
            return None

        try:
            import_module(capability_execution_module)
        except ModuleNotFoundError:
            cls._language_service_capability_execution_contracts[provider_key] = None
            return None

        try:
            contract = build_language_service_module_capability_execution_contract_from_semantic_contract(
                semantic_contract,
                execution_module=capability_execution_module,
                callable_module=capability_execution_module,
            )
        except ValueError as exc:
            logger.warning(
                "Aware module capability execution contract could not be synthesized for %s in %s: %s",
                provider_key,
                capability_execution_module,
                exc,
            )
            cls._language_service_capability_execution_contracts[provider_key] = None
            return None

        normalized = _normalize_capability_execution_contract(
            contract=contract,
            provider_key=provider_key,
            capability_execution_module=capability_execution_module,
        )
        cls._language_service_capability_execution_contracts[provider_key] = normalized
        return normalized

    @classmethod
    def module_semantic_contract_for_provider_key(
        cls,
        provider_key: str,
    ) -> ModuleSemanticContract | None:
        cls.ensure_builtin_plugins_registered()
        cached = cls._module_semantic_contracts.get(provider_key)
        if cached is not None or provider_key in cls._module_semantic_contracts:
            return cached

        semantic_contract_module = cls.semantic_contract_module_for_provider_key(
            provider_key
        )
        if semantic_contract_module is None:
            cls._module_semantic_contracts[provider_key] = None
            return None

        try:
            module = import_module(semantic_contract_module)
        except ModuleNotFoundError:
            cls._module_semantic_contracts[provider_key] = None
            return None

        contract = getattr(
            module,
            AWARE_MODULE_SEMANTIC_CONTRACT_EXPORT_NAME,
            None,
        )
        if not isinstance(contract, ModuleSemanticContract):
            logger.warning(
                "Aware module semantic contract missing contract %s in %s",
                AWARE_MODULE_SEMANTIC_CONTRACT_EXPORT_NAME,
                semantic_contract_module,
            )
            cls._module_semantic_contracts[provider_key] = None
            return None

        normalized = _normalize_module_semantic_contract(
            contract=contract,
            provider_key=provider_key,
        )
        cls._module_semantic_contracts[provider_key] = normalized
        return normalized

    @classmethod
    def get_module_semantic_contracts(
        cls,
        *,
        provider_keys: Iterable[str] | None = None,
    ) -> tuple[ModuleSemanticContract, ...]:
        cls.ensure_builtin_plugins_registered()
        selected_provider_keys = (
            tuple(provider_keys)
            if provider_keys is not None
            else cls.get_provider_keys()
        )
        contracts = [
            contract
            for provider_key in selected_provider_keys
            for contract in (
                cls.module_semantic_contract_for_provider_key(provider_key),
            )
            if contract is not None
        ]
        return tuple(sorted(contracts, key=lambda item: item.provider_key))

    @classmethod
    def module_code_package_materialization_contract_for_provider_key(
        cls,
        provider_key: str,
    ) -> ModuleCodePackageMaterializationContract | None:
        cls.ensure_builtin_plugins_registered()
        cached = cls._module_code_package_materialization_contracts.get(provider_key)
        if (
            cached is not None
            or provider_key in cls._module_code_package_materialization_contracts
        ):
            return cached

        contract_module = (
            cls.code_package_materialization_contract_module_for_provider_key(
                provider_key
            )
        )
        if contract_module is None:
            cls._module_code_package_materialization_contracts[provider_key] = None
            return None

        try:
            module = import_module(contract_module)
        except ModuleNotFoundError:
            cls._module_code_package_materialization_contracts[provider_key] = None
            return None

        contract = getattr(
            module,
            AWARE_MODULE_CODE_PACKAGE_MATERIALIZATION_CONTRACT_EXPORT_NAME,
            None,
        )
        if not isinstance(contract, ModuleCodePackageMaterializationContract):
            logger.warning(
                "Aware module code-package materialization contract missing contract %s in %s",
                AWARE_MODULE_CODE_PACKAGE_MATERIALIZATION_CONTRACT_EXPORT_NAME,
                contract_module,
            )
            cls._module_code_package_materialization_contracts[provider_key] = None
            return None

        normalized = _normalize_module_code_package_materialization_contract(
            contract=contract,
            provider_key=provider_key,
        )
        cls._module_code_package_materialization_contracts[provider_key] = normalized
        return normalized

    @classmethod
    def get_module_code_package_materialization_contracts(
        cls,
        *,
        provider_keys: Iterable[str] | None = None,
    ) -> tuple[ModuleCodePackageMaterializationContract, ...]:
        cls.ensure_builtin_plugins_registered()
        selected_provider_keys = (
            tuple(provider_keys)
            if provider_keys is not None
            else cls.get_provider_keys()
        )
        contracts = [
            contract
            for provider_key in selected_provider_keys
            for contract in (
                cls.module_code_package_materialization_contract_for_provider_key(
                    provider_key
                ),
            )
            if contract is not None
        ]
        return tuple(sorted(contracts, key=lambda item: item.provider_key))

    @classmethod
    def code_module_contract_for_provider_key(
        cls,
        provider_key: str,
    ) -> CodeModuleContract | None:
        cls.ensure_builtin_plugins_registered()
        cached = cls._code_module_contracts.get(provider_key)
        if cached is not None or provider_key in cls._code_module_contracts:
            return cached

        plugin = cls._plugins.get(provider_key)
        if plugin is None:
            cls._code_module_contracts[provider_key] = None
            return None

        semantic_contract = cls.module_semantic_contract_for_provider_key(provider_key)
        packages = _validate_package_semantic_contracts(
            provider_key=provider_key,
            packages=plugin.packages,
            semantic_contract=semantic_contract,
        )
        contract = CodeModuleContract(
            provider_key=provider_key,
            capability_contract_module=cls.capability_contract_module_for_provider_key(
                provider_key
            ),
            capability_execution_module=cls.capability_execution_module_for_provider_key(
                provider_key
            ),
            semantic_contract_module=cls.semantic_contract_module_for_provider_key(
                provider_key
            ),
            code_package_materialization_contract_module=(
                cls.code_package_materialization_contract_module_for_provider_key(
                    provider_key
                )
            ),
            packages=packages,
            capability_policy=plugin.capability_policy,
            language_service_capability_contract=(
                cls.language_service_capability_contract_for_provider_key(provider_key)
            ),
            language_service_capability_execution_contract=(
                cls.language_service_capability_execution_contract_for_provider_key(
                    provider_key
                )
            ),
            semantic_contract=semantic_contract,
            code_package_materialization_contract=(
                cls.module_code_package_materialization_contract_for_provider_key(
                    provider_key
                )
            ),
            language_service_provider_descriptors=(
                cls.language_service_provider_descriptors_for_provider_key(provider_key)
            ),
        )
        cls._code_module_contracts[provider_key] = contract
        return contract

    @classmethod
    def get_code_module_contracts(
        cls,
        *,
        provider_keys: Iterable[str] | None = None,
    ) -> tuple[CodeModuleContract, ...]:
        cls.ensure_builtin_plugins_registered()
        selected_provider_keys = (
            tuple(provider_keys)
            if provider_keys is not None
            else cls.get_provider_keys()
        )
        contracts = [
            contract
            for provider_key in selected_provider_keys
            for contract in (cls.code_module_contract_for_provider_key(provider_key),)
            if contract is not None
        ]
        return tuple(sorted(contracts, key=lambda item: item.provider_key))

    @classmethod
    def language_service_provider_descriptors_for_provider_key(
        cls,
        provider_key: str,
    ) -> tuple[LanguageServiceProviderDescriptor, ...]:
        cls.ensure_builtin_plugins_registered()
        if provider_key in cls._language_service_provider_descriptors:
            return cls._language_service_provider_descriptors[provider_key]

        contract = cls.module_semantic_contract_for_provider_key(provider_key)
        if contract is None:
            cls._language_service_provider_descriptors[provider_key] = ()
            return ()

        descriptors = (
            build_language_service_provider_descriptors_from_semantic_contract(
                contract,
                plugin=cls._plugins.get(provider_key),
            )
        )
        cls._language_service_provider_descriptors[provider_key] = descriptors
        return descriptors

    @classmethod
    def get_language_service_provider_descriptors(
        cls,
        *,
        provider_keys: Iterable[str] | None = None,
    ) -> tuple[LanguageServiceProviderDescriptor, ...]:
        cls.ensure_builtin_plugins_registered()
        selected_provider_keys = (
            tuple(provider_keys)
            if provider_keys is not None
            else cls.get_provider_keys()
        )
        descriptors = [
            descriptor
            for provider_key in selected_provider_keys
            for descriptor in cls.language_service_provider_descriptors_for_provider_key(
                provider_key
            )
        ]
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

    @classmethod
    def get_language_service_capability_contracts(
        cls,
        *,
        provider_keys: Iterable[str] | None = None,
    ) -> tuple[LanguageServiceModuleCapabilityContract, ...]:
        cls.ensure_builtin_plugins_registered()
        selected_provider_keys = (
            tuple(provider_keys)
            if provider_keys is not None
            else cls.get_provider_keys()
        )
        contracts = [
            contract
            for provider_key in selected_provider_keys
            for contract in (
                cls.language_service_capability_contract_for_provider_key(provider_key),
            )
            if contract is not None
        ]
        return tuple(sorted(contracts, key=lambda item: item.provider_key))

    @classmethod
    def get_language_service_capability_execution_contracts(
        cls,
        *,
        provider_keys: Iterable[str] | None = None,
    ) -> tuple[LanguageServiceModuleCapabilityExecutionContract, ...]:
        cls.ensure_builtin_plugins_registered()
        selected_provider_keys = (
            tuple(provider_keys)
            if provider_keys is not None
            else cls.get_provider_keys()
        )
        contracts = [
            contract
            for provider_key in selected_provider_keys
            for contract in (
                cls.language_service_capability_execution_contract_for_provider_key(
                    provider_key
                ),
            )
            if contract is not None
        ]
        return tuple(sorted(contracts, key=lambda item: item.provider_key))

    @classmethod
    def get_language_service_capability_execution_provider_keys(
        cls,
        *,
        capability: str,
        module_provider_keys: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        contracts = cls.get_language_service_capability_execution_contracts(
            provider_keys=module_provider_keys
        )
        provider_keys = {
            entrypoint.provider_key
            for contract in contracts
            for entrypoint in contract.execution_entrypoints_for(capability=capability)
        }
        return tuple(sorted(provider_keys))

    @classmethod
    def get_language_service_capability_available_provider_keys(
        cls,
        *,
        capability: str,
        module_provider_keys: Iterable[str] | None = None,
        overlay_provider_keys: Iterable[str] = (),
    ) -> tuple[str, ...]:
        contract_provider_keys = (
            cls.get_language_service_capability_execution_provider_keys(
                capability=capability,
                module_provider_keys=module_provider_keys,
            )
        )
        return tuple(
            sorted(
                {
                    provider_key
                    for provider_key in (
                        *overlay_provider_keys,
                        *contract_provider_keys,
                    )
                    if isinstance(provider_key, str) and provider_key.strip()
                }
            )
        )

    @classmethod
    def language_service_capability_execution_entrypoint(
        cls,
        *,
        capability: str,
        provider_key: str,
        module_provider_keys: Iterable[str] | None = None,
    ) -> LanguageServiceCapabilityExecutionEntrypoint | None:
        contracts = cls.get_language_service_capability_execution_contracts(
            provider_keys=module_provider_keys
        )
        for contract in contracts:
            for entrypoint in contract.execution_entrypoints_for(capability=capability):
                if entrypoint.provider_key == provider_key:
                    return entrypoint
        return None

    @classmethod
    def resolve_semantic_capability_provider(
        cls,
        *,
        provider_key: str,
        capability: str,
        semantic_owner: str | None = None,
    ) -> ResolvedSemanticCapabilityProvider | None:
        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        normalized_capability = capability.strip()
        normalized_semantic_owner = (
            semantic_owner.strip()
            if isinstance(semantic_owner, str) and semantic_owner.strip()
            else None
        )
        if not normalized_provider_key or not normalized_capability:
            return None

        cache_key = (
            normalized_capability,
            normalized_provider_key,
            normalized_semantic_owner,
        )
        cached = cls._semantic_capability_providers.get(cache_key)
        if cached is not None or cache_key in cls._semantic_capability_providers:
            return cached

        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key
        )
        if contract is None:
            cls._semantic_capability_providers[cache_key] = None
            return None

        participation_descriptors = contract.capability_participation_for(
            capability=normalized_capability
        )
        participation_keys = {
            (descriptor.capability, descriptor.semantic_owner)
            for descriptor in participation_descriptors
        }
        participation_metadata_by_key = {
            (descriptor.capability, descriptor.semantic_owner): dict(
                descriptor.metadata
            )
            for descriptor in participation_descriptors
        }
        candidate_semantic_owners = _semantic_owner_query_candidates_for_capability(
            contract=contract,
            requested_semantic_owner=normalized_semantic_owner,
            capability=normalized_capability,
        )
        candidate_semantic_owner_set = (
            None
            if candidate_semantic_owners == (None,)
            else frozenset(
                owner for owner in candidate_semantic_owners if owner is not None
            )
        )
        execution_policies = tuple(
            sorted(
                (
                    policy
                    for policy in contract.capability_execution_policy_for(
                        capability=normalized_capability
                    )
                    if (
                        policy.capability,
                        policy.semantic_owner,
                    )
                    in participation_keys
                    and (
                        candidate_semantic_owner_set is None
                        or policy.semantic_owner in candidate_semantic_owner_set
                    )
                ),
                key=lambda item: (item.priority, item.semantic_owner),
            )
        )
        if not execution_policies:
            cls._semantic_capability_providers[cache_key] = None
            return None

        semantic_contract_module = cls.semantic_contract_module_for_provider_key(
            normalized_provider_key
        )
        for policy in execution_policies:
            callable_module = (
                policy.callable_module or semantic_contract_module or ""
            ).strip()
            callable_name = (policy.callable_name or "").strip()
            if not callable_module or not callable_name:
                continue
            try:
                module = import_module(callable_module)
            except ModuleNotFoundError:
                continue
            provider = getattr(module, callable_name, None)
            if not callable(provider):
                logger.warning(
                    "Aware semantic capability execution entrypoint is not callable for %s:%s at %s.%s",
                    normalized_capability,
                    policy.semantic_owner,
                    callable_module,
                    callable_name,
                )
                continue
            resolved = ResolvedSemanticCapabilityProvider(
                capability=normalized_capability,
                provider_key=normalized_provider_key,
                semantic_owner=policy.semantic_owner,
                callable_module=callable_module,
                callable_name=callable_name,
                provider=provider,
                metadata=participation_metadata_by_key.get(
                    (policy.capability, policy.semantic_owner),
                    {},
                ),
            )
            cls._semantic_capability_providers[cache_key] = resolved
            return resolved

        cls._semantic_capability_providers[cache_key] = None
        return None

    @classmethod
    def resolve_semantic_artifact_leaf_ownership_resolvers(
        cls,
        *,
        provider_key: str,
        semantic_owner: str,
        owner_manifest_kind: str,
        artifact_manifest_kind: str,
    ) -> tuple[ResolvedSemanticArtifactLeafOwnershipResolver, ...]:
        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        normalized_semantic_owner = semantic_owner.strip()
        normalized_owner_manifest_kind = owner_manifest_kind.strip()
        normalized_artifact_manifest_kind = artifact_manifest_kind.strip()
        if (
            not normalized_provider_key
            or not normalized_semantic_owner
            or not normalized_owner_manifest_kind
            or not normalized_artifact_manifest_kind
        ):
            return ()

        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key
        )
        if contract is None:
            return ()

        resolved: list[ResolvedSemanticArtifactLeafOwnershipResolver] = []
        for descriptor in contract.artifact_leaf_ownership_for(
            semantic_owner=normalized_semantic_owner,
            owner_manifest_kind=normalized_owner_manifest_kind,
            artifact_manifest_kind=normalized_artifact_manifest_kind,
        ):
            callable_module = descriptor.callable_module.strip()
            callable_name = descriptor.callable_name.strip()
            if not callable_module or not callable_name:
                continue
            try:
                module = import_module(callable_module)
            except ModuleNotFoundError:
                continue
            resolver = getattr(module, callable_name, None)
            if not callable(resolver):
                logger.warning(
                    "Aware semantic artifact ownership resolver is not callable for %s:%s at %s.%s",
                    normalized_provider_key,
                    descriptor.semantic_owner,
                    callable_module,
                    callable_name,
                )
                continue
            resolved.append(
                ResolvedSemanticArtifactLeafOwnershipResolver(
                    provider_key=normalized_provider_key,
                    semantic_owner=descriptor.semantic_owner,
                    callable_module=callable_module,
                    callable_name=callable_name,
                    resolver=cast(
                        WorkspaceSemanticArtifactLeafOwnershipResolver,
                        resolver,
                    ),
                )
            )
        return tuple(resolved)

    @classmethod
    def semantic_materialization_artifact_outputs_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
        producer_key: str | None = None,
        output_key: str | None = None,
        artifact_family: str | None = None,
        required_for: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationArtifactOutputDescriptor, ...]:
        """Resolve provider-declared semantic materialization artifact outputs."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return tuple(
            descriptor
            for owner in _semantic_owner_query_candidates_for_capability(
                contract=contract,
                requested_semantic_owner=semantic_owner,
                capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            )
            for descriptor in contract.materialization_artifact_outputs_for(
                semantic_owner=owner,
                producer_key=producer_key,
                output_key=output_key,
                artifact_family=artifact_family,
                required_for=required_for,
            )
        )

    @classmethod
    def semantic_materialization_inputs_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
        input_key: str | None = None,
        input_kind: str | None = None,
        artifact_family: str | None = None,
        package_family: str | None = None,
        semantic_kind: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationInputDescriptor, ...]:
        """Resolve provider-declared semantic materialization inputs."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return tuple(
            descriptor
            for owner in _semantic_owner_query_candidates_for_capability(
                contract=contract,
                requested_semantic_owner=semantic_owner,
                capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            )
            for descriptor in contract.materialization_inputs_for(
                semantic_owner=owner,
                input_key=input_key,
                input_kind=input_kind,
                artifact_family=artifact_family,
                package_family=package_family,
                semantic_kind=semantic_kind,
            )
        )

    @classmethod
    def semantic_materialization_code_package_delta_outputs_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
        producer_key: str | None = None,
        output_key: str | None = None,
        authority_kind: str | None = None,
        required_for: str | None = None,
    ) -> tuple[
        ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor,
        ...,
    ]:
        """Resolve provider-declared semantic CodePackageDelta outputs."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return tuple(
            descriptor
            for owner in _semantic_owner_query_candidates_for_capability(
                contract=contract,
                requested_semantic_owner=semantic_owner,
                capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            )
            for descriptor in contract.materialization_code_package_delta_outputs_for(
                semantic_owner=owner,
                producer_key=producer_key,
                output_key=output_key,
                authority_kind=authority_kind,
                required_for=required_for,
            )
        )

    @classmethod
    def semantic_materialization_package_outputs_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
        producer_key: str | None = None,
        output_key: str | None = None,
        target_provider_key: str | None = None,
        target_input_key: str | None = None,
        required_for: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationPackageOutputDescriptor, ...]:
        """Resolve provider-declared semantic package materialization outputs."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return tuple(
            descriptor
            for owner in _semantic_owner_query_candidates_for_capability(
                contract=contract,
                requested_semantic_owner=semantic_owner,
                capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            )
            for descriptor in contract.materialization_package_outputs_for(
                semantic_owner=owner,
                producer_key=producer_key,
                output_key=output_key,
                target_provider_key=target_provider_key,
                target_input_key=target_input_key,
                required_for=required_for,
            )
        )

    @classmethod
    def semantic_materialization_runtime_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationRuntimeDescriptor, ...]:
        """Resolve provider-declared runtime requirements for materialization."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return tuple(
            descriptor
            for owner in _semantic_owner_query_candidates_for_capability(
                contract=contract,
                requested_semantic_owner=semantic_owner,
                capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            )
            for descriptor in contract.materialization_runtime_for(
                semantic_owner=owner,
            )
        )

    @classmethod
    def semantic_materialization_runtime_context_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationRuntimeContextDescriptor, ...]:
        """Resolve provider-declared runtime context resolvers."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return tuple(
            descriptor
            for owner in _semantic_owner_query_candidates_for_capability(
                contract=contract,
                requested_semantic_owner=semantic_owner,
                capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            )
            for descriptor in contract.materialization_runtime_context_for(
                semantic_owner=owner,
            )
        )

    @classmethod
    def semantic_materialization_tooling_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
        tooling_key: str | None = None,
        required_for: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationToolingDescriptor, ...]:
        """Resolve provider-declared tooling requirements."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return tuple(
            descriptor
            for owner in _semantic_owner_query_candidates_for_capability(
                contract=contract,
                requested_semantic_owner=semantic_owner,
                capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            )
            for descriptor in contract.materialization_tooling_for(
                semantic_owner=owner,
                tooling_key=tooling_key,
                required_for=required_for,
            )
        )

    @classmethod
    def semantic_materialization_language_profiles_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
        profile_key: str | None = None,
        producer_key: str | None = None,
        artifact_family: str | None = None,
        required_for: str | None = None,
    ) -> tuple[ModuleSemanticLanguageMaterializationProfileDescriptor, ...]:
        """Resolve provider-declared language materialization profile policy."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return tuple(
            descriptor
            for owner in _semantic_owner_query_candidates_for_capability(
                contract=contract,
                requested_semantic_owner=semantic_owner,
                capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            )
            for descriptor in contract.materialization_language_profiles_for(
                semantic_owner=owner,
                profile_key=profile_key,
                producer_key=producer_key,
                artifact_family=artifact_family,
                required_for=required_for,
            )
        )

    @classmethod
    def semantic_grammar_rule_declarations_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
        rule_name: str | None = None,
        grammar_backend: str | None = None,
        language: str | None = None,
    ) -> tuple[ModuleSemanticGrammarRuleDescriptor, ...]:
        """Resolve provider-declared grammar rule structure."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return contract.grammar_rule_declarations_for(
            semantic_owner=semantic_owner,
            rule_name=rule_name,
            grammar_backend=grammar_backend,
            language=language,
        )

    @classmethod
    def resolve_semantic_materialization_runtime_context_resolvers(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
    ) -> tuple[ResolvedSemanticMaterializationRuntimeContextResolver, ...]:
        """Resolve provider-owned runtime context resolver callables."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()

        resolved: list[ResolvedSemanticMaterializationRuntimeContextResolver] = []
        for descriptor in cls.semantic_materialization_runtime_context_for_provider_key(
            provider_key=normalized_provider_key,
            semantic_owner=semantic_owner,
        ):
            callable_module = descriptor.callable_module.strip()
            callable_name = descriptor.callable_name.strip()
            if not callable_module or not callable_name:
                continue
            try:
                module = import_module(callable_module)
            except ModuleNotFoundError:
                continue
            resolver = getattr(module, callable_name, None)
            if not callable(resolver):
                logger.warning(
                    "Aware semantic materialization runtime context resolver is not callable for %s:%s at %s.%s",
                    normalized_provider_key,
                    descriptor.semantic_owner,
                    callable_module,
                    callable_name,
                )
                continue
            resolved.append(
                ResolvedSemanticMaterializationRuntimeContextResolver(
                    provider_key=normalized_provider_key,
                    semantic_owner=descriptor.semantic_owner,
                    callable_module=callable_module,
                    callable_name=callable_name,
                    required=descriptor.required,
                    provider_payload=dict(descriptor.provider_payload or {}),
                    resolver=cast(
                        Callable[
                            [SemanticPackageMaterializationRuntimeContextRequest],
                            object,
                        ],
                        resolver,
                    ),
                )
            )
        return tuple(resolved)

    @classmethod
    def semantic_materialization_execution_context_for_provider_key(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
        context_key: str | None = None,
    ) -> tuple[ModuleSemanticMaterializationExecutionContextDescriptor, ...]:
        """Resolve provider-declared materialization execution contexts."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()
        contract = cls.module_semantic_contract_for_provider_key(
            normalized_provider_key,
        )
        if contract is None:
            return ()
        return tuple(
            descriptor
            for owner in _semantic_owner_query_candidates_for_capability(
                contract=contract,
                requested_semantic_owner=semantic_owner,
                capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            )
            for descriptor in contract.materialization_execution_context_for(
                semantic_owner=owner,
                context_key=context_key,
            )
        )

    @classmethod
    def resolve_semantic_materialization_execution_context_resolvers(
        cls,
        *,
        provider_key: str,
        semantic_owner: str | None = None,
        context_key: str | None = None,
    ) -> tuple[ResolvedSemanticMaterializationExecutionContextResolver, ...]:
        """Resolve provider-owned execution context resolver callables."""

        cls.ensure_builtin_plugins_registered()
        normalized_provider_key = provider_key.strip()
        if not normalized_provider_key:
            return ()

        resolved: list[ResolvedSemanticMaterializationExecutionContextResolver] = []
        for (
            descriptor
        ) in cls.semantic_materialization_execution_context_for_provider_key(
            provider_key=normalized_provider_key,
            semantic_owner=semantic_owner,
            context_key=context_key,
        ):
            callable_module = descriptor.callable_module.strip()
            callable_name = descriptor.callable_name.strip()
            if not callable_module or not callable_name:
                continue
            try:
                module = import_module(callable_module)
            except ModuleNotFoundError:
                continue
            resolver = getattr(module, callable_name, None)
            if not callable(resolver):
                logger.warning(
                    "Aware semantic materialization context resolver is not callable for %s:%s:%s at %s.%s",
                    normalized_provider_key,
                    descriptor.semantic_owner,
                    descriptor.context_key,
                    callable_module,
                    callable_name,
                )
                continue
            resolved.append(
                ResolvedSemanticMaterializationExecutionContextResolver(
                    provider_key=normalized_provider_key,
                    semantic_owner=descriptor.semantic_owner,
                    context_key=descriptor.context_key,
                    callable_module=callable_module,
                    callable_name=callable_name,
                    required=descriptor.required,
                    provider_payload=dict(descriptor.provider_payload or {}),
                    resolver=cast(
                        Callable[
                            [SemanticPackageMaterializationExecutionContextRequest],
                            object,
                        ],
                        resolver,
                    ),
                )
            )
        return tuple(resolved)

    @classmethod
    def language_service_capability_provider(
        cls,
        *,
        capability: str,
        provider_key: str,
    ) -> Callable[..., object] | None:
        cls.ensure_builtin_plugins_registered()
        cache_key = (capability, provider_key)
        cached = cls._language_service_capability_providers.get(cache_key)
        if (
            cached is not None
            or cache_key in cls._language_service_capability_providers
        ):
            return cached

        entrypoint = cls.language_service_capability_execution_entrypoint(
            capability=capability,
            provider_key=provider_key,
        )
        if entrypoint is None:
            cls._language_service_capability_providers[cache_key] = None
            return None

        try:
            module = import_module(entrypoint.callable_module)
        except ModuleNotFoundError:
            cls._language_service_capability_providers[cache_key] = None
            return None

        provider = getattr(module, entrypoint.callable_name, None)
        if not callable(provider):
            logger.warning(
                "Aware module capability execution entrypoint is not callable for %s:%s at %s.%s",
                capability,
                provider_key,
                entrypoint.callable_module,
                entrypoint.callable_name,
            )
            cls._language_service_capability_providers[cache_key] = None
            return None

        cls._language_service_capability_providers[cache_key] = provider
        return provider

    @classmethod
    def resolve_language_service_capability_providers(
        cls,
        *,
        capability: str,
        provider_keys: Iterable[str],
        overlay_providers: Mapping[str, Callable[..., object]] | None = None,
    ) -> tuple[tuple[str, Callable[..., object]], ...]:
        selected_overlay_providers = dict(overlay_providers or {})
        seen_provider_keys: set[str] = set()
        providers: list[tuple[str, Callable[..., object]]] = []

        for raw_provider_key in provider_keys:
            provider_key = (
                raw_provider_key.strip() if isinstance(raw_provider_key, str) else ""
            )
            if not provider_key or provider_key in seen_provider_keys:
                continue
            seen_provider_keys.add(provider_key)

            provider = selected_overlay_providers.get(provider_key)
            if provider is None:
                provider = cls.language_service_capability_provider(
                    capability=capability,
                    provider_key=provider_key,
                )
            if not callable(provider):
                continue
            providers.append((provider_key, provider))

        return tuple(providers)

    @classmethod
    def resolve_language_service_capability_execution_providers(
        cls,
        *,
        capability: str,
        provider_keys: Iterable[str] | None = None,
        module_provider_keys: Iterable[str] | None = None,
        overlay_descriptors: Iterable[LanguageServiceProviderDescriptor] = (),
        overlay_providers: Mapping[str, Callable[..., object]] | None = None,
        descriptor_filter: (
            Callable[[LanguageServiceProviderDescriptor], bool] | None
        ) = None,
    ) -> tuple[ResolvedLanguageServiceCapabilityProvider, ...]:
        merged_descriptors = merge_language_service_provider_descriptors(
            capability=capability,
            provider_descriptors=cls.get_language_service_provider_descriptors(
                provider_keys=module_provider_keys
            ),
            registered_descriptors=overlay_descriptors,
        )
        descriptor_by_provider_key = {
            descriptor.provider_key: descriptor for descriptor in merged_descriptors
        }
        selected_provider_keys = (
            tuple(
                provider_key.strip()
                for provider_key in provider_keys
                if isinstance(provider_key, str) and provider_key.strip()
            )
            if provider_keys is not None
            else tuple(descriptor.provider_key for descriptor in merged_descriptors)
        )

        resolved_providers = cls.resolve_language_service_capability_providers(
            capability=capability,
            provider_keys=selected_provider_keys,
            overlay_providers=overlay_providers,
        )
        resolved: list[ResolvedLanguageServiceCapabilityProvider] = []
        for provider_key, provider in resolved_providers:
            descriptor = descriptor_by_provider_key.get(provider_key)
            if descriptor is None:
                continue
            if descriptor_filter is not None and not descriptor_filter(descriptor):
                continue
            resolved.append(
                ResolvedLanguageServiceCapabilityProvider(
                    descriptor=descriptor,
                    provider=provider,
                )
            )
        return tuple(resolved)

    @classmethod
    def _register_plugin_export(
        cls,
        *,
        module_path: str,
        plugin_export_name: str,
        capability_contract_module: str | None = None,
        capability_execution_module: str | None = None,
        semantic_contract_module: str | None = None,
        code_package_materialization_contract_module: str | None = None,
        packages: tuple[AwareModulePackageContract, ...] = (),
        replace_existing: bool = False,
    ) -> None:
        try:
            module = import_module(module_path)
        except ModuleNotFoundError:
            return
        plugin = getattr(module, plugin_export_name, None)
        if not isinstance(plugin, AwareModulePlugin):
            logger.warning(
                "Aware module plugin bootstrap missing plugin %s in %s",
                plugin_export_name,
                module_path,
            )
            return
        if (
            capability_contract_module
            or capability_execution_module
            or semantic_contract_module
            or code_package_materialization_contract_module
            or packages
        ):
            plugin = replace(
                plugin,
                capability_contract_module=(
                    capability_contract_module or plugin.capability_contract_module
                ),
                capability_execution_module=(
                    capability_execution_module or plugin.capability_execution_module
                ),
                semantic_contract_module=(
                    semantic_contract_module or plugin.semantic_contract_module
                ),
                code_package_materialization_contract_module=(
                    code_package_materialization_contract_module
                    or plugin.code_package_materialization_contract_module
                ),
                packages=packages or plugin.packages,
            )
        cls.register(plugin, replace_existing=replace_existing)

    @classmethod
    def _register_plugin_bootstrap_spec(
        cls,
        spec: _AwarePluginBootstrapSpec,
        *,
        replace_existing: bool = False,
    ) -> None:
        _ensure_runtime_root_on_sys_path(spec.runtime_root)
        module_path = (spec.module_path or "").strip()
        if module_path:
            cls._register_plugin_export(
                module_path=module_path,
                plugin_export_name=_AWARE_MODULE_PLUGIN_EXPORT_NAME,
                capability_contract_module=spec.capability_contract_module,
                capability_execution_module=spec.capability_execution_module,
                semantic_contract_module=spec.semantic_contract_module,
                code_package_materialization_contract_module=(
                    spec.code_package_materialization_contract_module
                ),
                packages=spec.packages,
                replace_existing=replace_existing,
            )
            return

        provider_key = (spec.provider_key or "").strip()
        if not provider_key:
            return

        cls.register(
            AwareModulePlugin(
                provider_key=provider_key,
                capability_contract_module=spec.capability_contract_module,
                capability_execution_module=spec.capability_execution_module,
                semantic_contract_module=spec.semantic_contract_module,
                code_package_materialization_contract_module=(
                    spec.code_package_materialization_contract_module
                ),
                packages=spec.packages,
                capability_policy=spec.capability_policy,
                register_semantic_package_providers=None,
                register_semantic_scope_providers=_combined_registration_hook(
                    hooks=(
                        _registration_hook_from_semantic_contract_modules(
                            module_paths=_semantic_provider_contract_modules(
                                packages=spec.packages,
                            ),
                            function_name="register_semantic_scope_providers",
                            sibling_module_name="semantic_scope",
                        ),
                    ),
                ),
            ),
            replace_existing=replace_existing,
        )


def _module_plugin_bootstrap_specs_from_manifests(
    *,
    repo_root: Path,
) -> tuple[_AwarePluginBootstrapSpec, ...]:
    repo_root = repo_root.expanduser().resolve()
    modules_root = (repo_root / "modules").resolve()
    if not modules_root.exists():
        return ()

    specs: list[_AwarePluginBootstrapSpec] = []
    seen: set[str] = set()
    for module_root in sorted(path for path in modules_root.iterdir() if path.is_dir()):
        spec = _module_plugin_bootstrap_spec_from_manifest(module_root=module_root)
        if spec is None:
            continue
        spec_key = (spec.provider_key or "").strip() or (spec.module_path or "").strip()
        if not spec_key or spec_key in seen:
            continue
        seen.add(spec_key)
        specs.append(spec)
    return tuple(specs)


def _module_plugin_bootstrap_spec_from_manifest(
    *,
    module_root: Path,
) -> _AwarePluginBootstrapSpec | None:
    module_toml = module_root / "aware.module.toml"
    if not module_toml.exists():
        return None

    try:
        module_spec = load_aware_module_spec(toml_path=module_toml)
    except AwareModuleTomlError as exc:
        logger.warning(
            "Aware module plugin bootstrap skipped invalid module manifest %s: %s",
            module_toml,
            exc,
        )
        return None

    for plugin in module_spec.plugins:
        if plugin.kind != _CODE_MODULE_PLUGIN_KIND or not plugin.required:
            continue
        module_path = (plugin.module or "").strip() or None
        provider_key = (plugin.provider_key or "").strip() or None
        capability_contract_module = (
            plugin.capability_contract_module or ""
        ).strip() or None
        capability_execution_module = (
            plugin.capability_execution_module or ""
        ).strip() or None
        semantic_contract_module = (
            plugin.semantic_contract_module or ""
        ).strip() or None
        code_package_materialization_contract_module = (
            plugin.code_package_materialization_contract_module or ""
        ).strip() or None
        capability_policy = tuple(
            AwareModulePluginCapabilityPolicy(
                capability=policy.capability,
                workspace_activation=cast(
                    ModulePluginWorkspaceActivation,
                    policy.workspace_activation,
                ),
                workspace_fallback=policy.workspace_fallback,
            )
            for policy in plugin.capability_policy
        )
        packages = tuple(
            AwareModulePackageContract(
                id=package.id,
                kind=package.kind,
                manifest=package.manifest,
                visibility=package.visibility,
                semantic_contract=(
                    AwareModulePackageSemanticContract(
                        role=package.semantic_contract.role,
                        contract=package.semantic_contract.contract,
                        provider_key=package.semantic_contract.provider_key,
                        module=package.semantic_contract.module,
                        owns_manifest_kinds=package.semantic_contract.owns_manifest_kinds,
                        capabilities=package.semantic_contract.capabilities,
                        bindings=tuple(
                            AwareModulePackageSemanticContractBinding(
                                capability=binding.capability,
                                module=binding.module,
                                callable=binding.callable,
                            )
                            for binding in package.semantic_contract.bindings
                        ),
                    )
                    if package.semantic_contract is not None
                    else None
                ),
                semantic_bindings=tuple(
                    AwareModulePackageSemanticBindingContract(
                        role=binding.role,
                        contract=binding.contract,
                        binding_module=binding.binding_module,
                        capabilities=binding.capabilities,
                        callable_name=binding.callable_name,
                    )
                    for binding in package.semantic_bindings
                ),
                mirrors_ontology=package.mirrors_ontology,
            )
            for package in module_spec.packages
        )
        semantic_contract_module = semantic_contract_module or (
            _semantic_contract_module_from_provider_packages(
                packages=packages,
                provider_key=provider_key,
            )
        )
        if module_path or provider_key:
            return _AwarePluginBootstrapSpec(
                provider_key=provider_key,
                module_path=module_path,
                runtime_root=(module_root / module_spec.runtime_root).resolve(),
                capability_contract_module=capability_contract_module,
                capability_execution_module=capability_execution_module,
                semantic_contract_module=semantic_contract_module,
                code_package_materialization_contract_module=(
                    code_package_materialization_contract_module
                ),
                packages=packages,
                capability_policy=capability_policy,
            )
    return None


def _ensure_runtime_root_on_sys_path(runtime_root: Path | None) -> None:
    if runtime_root is None or not runtime_root.is_dir():
        return
    runtime_root_text = runtime_root.as_posix()
    if runtime_root_text not in sys.path:
        sys.path.insert(0, runtime_root_text)


def _plugin_bootstrap_equivalent(
    existing: AwareModulePlugin,
    candidate: AwareModulePlugin,
) -> bool:
    return (
        existing.provider_key == candidate.provider_key
        and existing.capability_contract_module == candidate.capability_contract_module
        and existing.capability_execution_module
        == candidate.capability_execution_module
        and existing.semantic_contract_module == candidate.semantic_contract_module
        and existing.code_package_materialization_contract_module
        == candidate.code_package_materialization_contract_module
        and existing.packages == candidate.packages
        and existing.capability_policy == candidate.capability_policy
    )


def _normalize_capability_contract(
    *,
    contract: LanguageServiceModuleCapabilityContract,
    provider_key: str,
    capability_contract_module: str,
) -> LanguageServiceModuleCapabilityContract:
    if (
        contract.provider_key == provider_key
        and contract.contract_module == capability_contract_module
    ):
        return contract

    return replace(
        contract,
        provider_key=provider_key,
        contract_module=capability_contract_module,
    )


def _normalize_capability_execution_contract(
    *,
    contract: LanguageServiceModuleCapabilityExecutionContract,
    provider_key: str,
    capability_execution_module: str,
) -> LanguageServiceModuleCapabilityExecutionContract:
    if (
        contract.provider_key == provider_key
        and contract.execution_module == capability_execution_module
    ):
        return contract
    return replace(
        contract,
        provider_key=provider_key,
        execution_module=capability_execution_module,
    )


def _normalize_module_semantic_contract(
    *,
    contract: ModuleSemanticContract,
    provider_key: str,
) -> ModuleSemanticContract:
    if contract.provider_key == provider_key:
        return contract
    return replace(contract, provider_key=provider_key)


def _semantic_owner_query_candidates_for_capability(
    *,
    contract: ModuleSemanticContract,
    requested_semantic_owner: str | None,
    capability: str,
) -> tuple[str | None, ...]:
    normalized_semantic_owner = _optional_text(requested_semantic_owner)
    if normalized_semantic_owner is None:
        return (None,)
    candidates: list[str | None] = [normalized_semantic_owner]
    package_role = contract.package_role_for(role=normalized_semantic_owner)
    if package_role is None:
        return tuple(candidates)
    if capability not in package_role.capabilities:
        return tuple(candidates)
    for participation in contract.capability_participation_for(
        capability=capability,
    ):
        semantic_owner = _optional_text(participation.semantic_owner)
        if semantic_owner is not None and semantic_owner not in candidates:
            candidates.append(semantic_owner)
    return tuple(candidates)


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _validate_package_semantic_contracts(
    *,
    provider_key: str,
    packages: tuple[AwareModulePackageContract, ...],
    semantic_contract: ModuleSemanticContract | None,
) -> tuple[AwareModulePackageContract, ...]:
    for package in packages:
        package_contract = package.semantic_contract
        if package_contract is None:
            continue
        if package_contract.provider_key != provider_key:
            raise ValueError(
                f"Package {package.id!r} semantic_contract provider_key "
                f"{package_contract.provider_key!r} does not match module plugin "
                f"provider_key {provider_key!r}"
            )
        if semantic_contract is None:
            raise ValueError(
                f"Package {package.id!r} declares semantic_contract role "
                f"{package_contract.role!r}, but provider {provider_key!r} has no "
                "loaded ModuleSemanticContract"
            )
        package_role = semantic_contract.package_role_for(
            role=package_contract.role,
        )
        if package_role is None:
            raise ValueError(
                f"Package {package.id!r} declares semantic_contract role "
                f"{package_contract.role!r}, but provider {provider_key!r} "
                "does not declare that package role"
            )
        if package_role.contract != package_contract.contract:
            raise ValueError(
                f"Package {package.id!r} semantic_contract role "
                f"{package_contract.role!r} uses contract "
                f"{package_contract.contract!r}, expected {package_role.contract!r}"
            )
        if (
            package_role.package_kind is not None
            and package_role.package_kind != package.kind
        ):
            raise ValueError(
                f"Package {package.id!r} semantic_contract role "
                f"{package_contract.role!r} applies to package kind "
                f"{package.kind!r}, expected {package_role.package_kind!r}"
            )
        allowed_capabilities = frozenset(package_role.capabilities)
        for capability in package_contract.capabilities:
            if capability not in allowed_capabilities:
                raise ValueError(
                    f"Package {package.id!r} semantic_contract role "
                    f"{package_contract.role!r} capability "
                    f"{capability!r} is not allowed by the module "
                    "semantic contract"
                )
        for binding in package_contract.bindings:
            if binding.capability not in allowed_capabilities:
                raise ValueError(
                    f"Package {package.id!r} semantic_contract role "
                    f"{package_contract.role!r} binding capability "
                    f"{binding.capability!r} is not allowed by the module "
                    "semantic contract"
                )
        allowed_manifest_kinds = frozenset(package_role.owns_manifest_kinds)
        for manifest_kind in package_contract.owns_manifest_kinds:
            if manifest_kind not in allowed_manifest_kinds:
                raise ValueError(
                    f"Package {package.id!r} semantic_contract role "
                    f"{package_contract.role!r} manifest kind "
                    f"{manifest_kind!r} is not allowed by the module "
                    "semantic contract"
                )
    return packages


def _normalize_module_code_package_materialization_contract(
    *,
    contract: ModuleCodePackageMaterializationContract,
    provider_key: str,
) -> ModuleCodePackageMaterializationContract:
    if contract.provider_key == provider_key:
        return contract
    return replace(contract, provider_key=provider_key)


def _load_optional_export(
    *,
    module_path: str | None,
    export_name: str | None,
    required: bool,
) -> object | None:
    normalized_module_path = (module_path or "").strip()
    normalized_export_name = (export_name or "").strip()
    if not normalized_module_path or not normalized_export_name:
        return None

    try:
        module = import_module(normalized_module_path)
    except ModuleNotFoundError:
        if required:
            raise
        return None

    export = getattr(module, normalized_export_name, None)
    if export is not None:
        return export
    if required:
        raise AttributeError(
            f"{normalized_module_path}.{normalized_export_name} is not available"
        )
    return None


def _semantic_provider_contract_modules(
    *,
    packages: tuple[AwareModulePackageContract, ...],
) -> tuple[str, ...]:
    modules: list[str] = []
    seen: set[str] = set()
    for package in packages:
        semantic_contract = package.semantic_contract
        if semantic_contract is None:
            continue
        if semantic_contract.contract != _SEMANTIC_PROVIDER_CONTRACT:
            continue
        normalized_module_path = semantic_contract.module.strip()
        if not normalized_module_path or normalized_module_path in seen:
            continue
        seen.add(normalized_module_path)
        modules.append(normalized_module_path)
    return tuple(modules)


def _semantic_contract_module_from_provider_packages(
    *,
    packages: tuple[AwareModulePackageContract, ...],
    provider_key: str | None,
) -> str | None:
    provider = (provider_key or "").strip()
    if not provider:
        return None
    modules = tuple(
        semantic_contract.module
        for package in packages
        for semantic_contract in (package.semantic_contract,)
        if semantic_contract is not None
        and semantic_contract.contract == _SEMANTIC_PROVIDER_CONTRACT
        and semantic_contract.provider_key == provider
    )
    deduped = tuple(
        dict.fromkeys(module.strip() for module in modules if module.strip())
    )
    if len(deduped) > 1:
        raise ValueError(
            f"Provider {provider!r} declares multiple semantic provider modules: "
            f"{deduped!r}"
        )
    return deduped[0] if deduped else None


def _registration_hook_from_module(
    *,
    module_path: str | None,
    function_name: str,
) -> Callable[[], None] | None:
    return _registration_hook_from_modules(
        module_paths=(module_path,),
        function_name=function_name,
    )


def _registration_hook_from_modules(
    *,
    module_paths: Iterable[str | None],
    function_name: str,
) -> Callable[[], None] | None:
    normalized_module_paths: list[str] = []
    seen: set[str] = set()
    for module_path in module_paths:
        normalized_module_path = (module_path or "").strip()
        if not normalized_module_path or normalized_module_path in seen:
            continue
        seen.add(normalized_module_path)
        normalized_module_paths.append(normalized_module_path)
    if not normalized_module_paths:
        return None

    def _register() -> None:
        for normalized_module_path in normalized_module_paths:
            module = import_module(normalized_module_path)
            register_function = getattr(module, function_name, None)
            if not callable(register_function):
                raise AttributeError(
                    f"{normalized_module_path}.{function_name} is not callable"
                )
            register_function()

    return _register


def _registration_hook_from_semantic_contract_modules(
    *,
    module_paths: Iterable[str | None],
    function_name: str,
    sibling_module_name: str,
) -> Callable[[], None] | None:
    normalized_module_paths: list[str] = []
    seen: set[str] = set()
    for module_path in module_paths:
        normalized_module_path = (module_path or "").strip()
        if not normalized_module_path or normalized_module_path in seen:
            continue
        seen.add(normalized_module_path)
        normalized_module_paths.append(normalized_module_path)
    if not normalized_module_paths:
        return None

    def _register() -> None:
        for normalized_module_path in normalized_module_paths:
            module = import_module(normalized_module_path)
            register_function = getattr(module, function_name, None)
            if callable(register_function):
                register_function()
                continue

            package_root, _sep, _leaf = normalized_module_path.rpartition(".")
            if not package_root:
                raise AttributeError(
                    f"{normalized_module_path}.{function_name} is not callable"
                )
            sibling_module_path = f"{package_root}.{sibling_module_name}"
            sibling_module = import_module(sibling_module_path)
            sibling_register_function = getattr(sibling_module, function_name, None)
            if not callable(sibling_register_function):
                raise AttributeError(
                    f"{sibling_module_path}.{function_name} is not callable"
                )
            sibling_register_function()

    return _register


def _combined_registration_hook(
    *,
    hooks: Iterable[Callable[[], None] | None],
) -> Callable[[], None] | None:
    normalized_hooks = tuple(hook for hook in hooks if hook is not None)
    if not normalized_hooks:
        return None

    def _register() -> None:
        for hook in normalized_hooks:
            hook()

    return _register


__all__ = [
    "AwareModulePluginRegistry",
    "ResolvedSemanticArtifactLeafOwnershipResolver",
    "ResolvedSemanticCapabilityProvider",
]
