from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, cast

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.runtime.handler_executor import (
    MetaGraphEmptyLaneBootstrapCallable,
    MetaGraphEmptyLaneBootstrapResolver,
    MetaGraphGeneratedConstructorBootstrapRegistry,
    MetaGraphGeneratedLanguageHandlerCallable,
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedLanguageHandlerRegistry,
    MetaGraphGeneratedLanguageHandlerResolver,
    MetaGraphGeneratedInvocationHandlerCallable,
    MetaGraphGeneratedInvocationHandlerRegistry,
    MetaGraphGeneratedInvocationHandlerResolver,
    MetaGraphRuntimeIndex,
)


_META_RUNTIME_HANDLER_PROVIDER_ROLE = "meta_runtime_handler_provider"
_RUNTIME_HANDLERS_MATERIALIZATION_SOURCE = "runtime_handlers"


@dataclass(frozen=True, slots=True)
class MetaGraphGeneratedHandlerProviderSet:
    """Generated Meta handler provider modules resolved from committed graph truth."""

    provider_module_names: tuple[str, ...]
    handler_resolver: MetaGraphGeneratedLanguageHandlerResolver
    empty_lane_bootstrap_resolver: MetaGraphEmptyLaneBootstrapResolver | None
    invocation_handler_resolver: MetaGraphGeneratedInvocationHandlerResolver | None = (
        None
    )


def discover_meta_graph_generated_handler_provider_set(
    *,
    index: object,
    handler_owner_prefixes: Iterable[str] | None = None,
) -> MetaGraphGeneratedHandlerProviderSet | None:
    """Discover generated Meta handler providers from Python language output truth.

    The provider module suffix comes from the Python code language plugin's
    `meta_runtime_handler_provider` materialization output. Candidate provider
    package roots come from indexed `FunctionConfig.owner_key` prefixes, which
    are committed OCG truth.
    """

    provider_module_suffix = _python_meta_runtime_handler_provider_module()
    if provider_module_suffix is None:
        return None
    if not isinstance(index, MetaGraphRuntimeIndex):
        return None

    modules: list[ModuleType] = []
    module_names: list[str] = []
    seen_module_names: set[str] = set()
    if handler_owner_prefixes is not None:
        provider_roots = _explicit_owner_prefixes(handler_owner_prefixes)
    else:
        runtime_provider_roots = (
            _runtime_handler_provider_import_roots_from_runtime_index(index=index)
        )
        provider_roots = (
            *runtime_provider_roots,
            *(
                owner_prefix
                for owner_prefix in _owner_prefixes_from_runtime_index(index=index)
                if not _owner_prefix_has_explicit_runtime_provider(
                    owner_prefix=owner_prefix,
                    runtime_provider_roots=runtime_provider_roots,
                )
            ),
        )
    for owner_prefix in dict.fromkeys(provider_roots):
        for module_name in _candidate_provider_module_names(
            owner_prefix=owner_prefix,
            provider_module_suffix=provider_module_suffix,
        ):
            if module_name in seen_module_names:
                continue
            module = _try_import_provider_module(module_name)
            if module is None:
                continue
            seen_module_names.add(module_name)
            modules.append(module)
            module_names.append(module_name)
            break

    return build_meta_graph_generated_handler_provider_set(
        modules=tuple(modules),
        provider_module_names=tuple(module_names),
    )


def build_meta_graph_generated_handler_provider_set(
    *,
    modules: Iterable[object],
    provider_module_names: Iterable[str] = (),
) -> MetaGraphGeneratedHandlerProviderSet | None:
    """Build combined generated-handler and bootstrap registries."""

    module_tuple = tuple(modules)
    if not module_tuple:
        return None

    handlers_by_key: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedLanguageHandlerCallable,
    ] = {}
    invocation_handlers_by_key: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedInvocationHandlerCallable,
    ] = {}
    bootstraps_by_key: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphEmptyLaneBootstrapCallable,
    ] = {}
    resolved_names = tuple(provider_module_names)

    for module in module_tuple:
        handlers = _module_handlers(module)
        invocation_handlers = _module_invocation_handlers(module)
        bootstraps = _module_bootstraps(module)
        if not handlers and not invocation_handlers and not bootstraps:
            continue
        for key, handler in handlers.items():
            if key in handlers_by_key:
                raise ValueError(
                    "Duplicate Meta generated language handler key: "
                    f"{key.describe()}"
                )
            handlers_by_key[key] = handler
        for key, handler in invocation_handlers.items():
            if key in invocation_handlers_by_key:
                raise ValueError(
                    "Duplicate Meta generated invocation handler key: "
                    f"{key.describe()}"
                )
            invocation_handlers_by_key[key] = handler
        for key, bootstrap in bootstraps.items():
            if key in bootstraps_by_key:
                raise ValueError(
                    "Duplicate Meta generated constructor bootstrap key: "
                    f"{key.describe()}"
                )
            bootstraps_by_key[key] = bootstrap

    if not handlers_by_key:
        return None

    return MetaGraphGeneratedHandlerProviderSet(
        provider_module_names=resolved_names,
        handler_resolver=MetaGraphGeneratedLanguageHandlerRegistry(
            handlers_by_key=handlers_by_key,
        ),
        invocation_handler_resolver=(
            MetaGraphGeneratedInvocationHandlerRegistry(
                handlers_by_key=invocation_handlers_by_key,
            )
            if invocation_handlers_by_key
            else None
        ),
        empty_lane_bootstrap_resolver=(
            MetaGraphGeneratedConstructorBootstrapRegistry(
                bootstraps_by_key=bootstraps_by_key,
            )
            if bootstraps_by_key
            else None
        ),
    )


def _explicit_owner_prefixes(
    handler_owner_prefixes: Iterable[str],
) -> tuple[str, ...]:
    prefixes: list[str] = []
    seen: set[str] = set()
    for raw_prefix in handler_owner_prefixes:
        prefix = str(raw_prefix).strip()
        if not prefix:
            continue
        if not _is_import_root(prefix):
            raise ValueError(
                "Meta generated handler owner prefix must be an import root: "
                f"{raw_prefix!r}."
            )
        if prefix in seen:
            continue
        prefixes.append(prefix)
        seen.add(prefix)
    return tuple(prefixes)


def _owner_prefixes_from_runtime_index(
    *,
    index: MetaGraphRuntimeIndex,
) -> tuple[str, ...]:
    prefixes: set[str] = set()
    for class_config in index.class_configs_by_id.values():
        for edge in class_config.class_config_function_configs:
            function_config = edge.function_config
            owner_prefix = _owner_prefix_from_owner_key(function_config.owner_key)
            if owner_prefix is not None:
                prefixes.add(owner_prefix)
    return tuple(sorted(prefixes))


def _runtime_handler_provider_import_roots_from_runtime_index(
    *,
    index: MetaGraphRuntimeIndex,
) -> tuple[str, ...]:
    roots = getattr(index, "runtime_handler_provider_import_roots", ())
    if isinstance(roots, str):
        roots = (roots,)
    if not isinstance(roots, Iterable):
        return ()
    resolved_roots: list[str] = []
    seen: set[str] = set()
    for raw_root in roots:
        root = str(raw_root).strip()
        if not root or root in seen or not _is_import_root(root):
            continue
        seen.add(root)
        resolved_roots.append(root)
    return tuple(resolved_roots)


def _owner_prefix_has_explicit_runtime_provider(
    *,
    owner_prefix: str,
    runtime_provider_roots: Iterable[str],
) -> bool:
    prefix = str(owner_prefix).strip()
    if not prefix:
        return False
    covered_roots = {prefix}
    if not prefix.endswith("_runtime"):
        covered_roots.add(f"{prefix}_runtime")
    return any(str(root).strip() in covered_roots for root in runtime_provider_roots)


def _owner_prefix_from_owner_key(owner_key: str) -> str | None:
    prefix, separator, _rest = owner_key.strip().partition(".default.")
    if not separator or not _is_import_root(prefix):
        return None
    return prefix


def _candidate_provider_module_names(
    *,
    owner_prefix: str,
    provider_module_suffix: str,
) -> tuple[str, ...]:
    roots = [owner_prefix]
    if not owner_prefix.endswith("_runtime"):
        roots.append(f"{owner_prefix}_runtime")
    return tuple(
        dict.fromkeys(
            f"{root}.{provider_module_suffix}"
            for root in roots
            if _is_import_root(root)
        )
    )


def _python_meta_runtime_handler_provider_module() -> str | None:
    _ensure_python_code_plugin_registered()
    if not CodeLanguagePluginRegistry.has_language(CodeLanguage.python):
        return None
    plugin = CodeLanguagePluginRegistry.get(CodeLanguage.python)
    for descriptor in plugin.materialization_artifact_outputs:
        if descriptor.artifact_role != _META_RUNTIME_HANDLER_PROVIDER_ROLE:
            continue
        if (
            _RUNTIME_HANDLERS_MATERIALIZATION_SOURCE
            not in descriptor.materialization_sources
        ):
            continue
        provider_payload = descriptor.provider_payload or {}
        provider_module = provider_payload.get("provider_module")
        if not isinstance(provider_module, str):
            continue
        provider_module = provider_module.strip()
        if provider_module:
            return provider_module
    return None


def _ensure_python_code_plugin_registered() -> None:
    if CodeLanguagePluginRegistry.has_language(CodeLanguage.python):
        return
    for plugin in AwareModulePluginRegistry.get_builtin_code_language_plugins():
        CodeLanguagePluginRegistry.register(plugin)


def _try_import_provider_module(module_name: str) -> ModuleType | None:
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        missing_name = exc.name or ""
        if module_name == missing_name or module_name.startswith(missing_name + "."):
            return None
        raise
    return module


def _module_handlers(
    module: object,
) -> Mapping[
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedLanguageHandlerCallable,
]:
    try:
        handlers = cast(Any, module).AWARE_META_GRAPH_HANDLERS
    except AttributeError:
        return {}
    if not isinstance(handlers, Mapping):
        return {}
    return cast(
        Mapping[
            MetaGraphGeneratedLanguageHandlerKey,
            MetaGraphGeneratedLanguageHandlerCallable,
        ],
        handlers,
    )


def _module_invocation_handlers(
    module: object,
) -> Mapping[
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedInvocationHandlerCallable,
]:
    try:
        handlers = cast(Any, module).AWARE_META_GRAPH_INVOCATION_HANDLERS
    except AttributeError:
        return {}
    if not isinstance(handlers, Mapping):
        return {}
    return cast(
        Mapping[
            MetaGraphGeneratedLanguageHandlerKey,
            MetaGraphGeneratedInvocationHandlerCallable,
        ],
        handlers,
    )


def _module_bootstraps(
    module: object,
) -> Mapping[
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphEmptyLaneBootstrapCallable,
]:
    try:
        bootstraps = cast(Any, module).AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS
    except AttributeError:
        return {}
    if not isinstance(bootstraps, Mapping):
        return {}
    return cast(
        Mapping[
            MetaGraphGeneratedLanguageHandlerKey,
            MetaGraphEmptyLaneBootstrapCallable,
        ],
        bootstraps,
    )


def _is_import_root(value: str) -> bool:
    parts = value.split(".")
    return bool(parts) and all(part.isidentifier() for part in parts)


__all__ = [
    "MetaGraphGeneratedHandlerProviderSet",
    "build_meta_graph_generated_handler_provider_set",
    "discover_meta_graph_generated_handler_provider_set",
]
