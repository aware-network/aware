from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Protocol, cast
from uuid import UUID

from aware_meta.runtime.graph_commit_invocation_backend import (
    MetaGraphCommitInvocationBackend,
)
from aware_meta.runtime.generated_handler_discovery import (
    MetaGraphGeneratedHandlerProviderSet,
    discover_meta_graph_generated_handler_provider_set,
)

if TYPE_CHECKING:
    from aware_meta.runtime.graph_context import MetaGraphRuntimeContext
    from aware_meta.runtime.graph_runtime import MetaGraphRuntime
    from aware_meta.runtime.package_index import MetaRuntimePackageIndexEntry
from aware_meta.runtime.handler_executor.factory import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    build_meta_graph_generated_handler_executor,
)
from aware_meta.runtime.handler_executor.index import (
    MetaGraphImplementationPolicy,
)
from aware_meta.runtime.handler_executor.language_handler import (
    MetaGraphGeneratedLanguageHandlerCallable,
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedLanguageHandlerRegistry,
    MetaGraphGeneratedLanguageHandlerResolver,
    MetaGraphGeneratedInvocationHandlerCallable,
    MetaGraphGeneratedInvocationHandlerRegistry,
    MetaGraphGeneratedInvocationHandlerResolver,
)
from aware_meta.runtime.handler_executor.pre_state import (
    MetaGraphEmptyLaneBootstrapCallable,
    MetaGraphEmptyLaneBootstrapResolver,
    MetaGraphGeneratedConstructorBootstrapRegistry,
    MetaGraphOigMaterializerPreStateProvider,
    MetaGraphPreStateProvider,
)
from aware_meta.runtime.generated_handler_resolver_chain import (
    meta_graph_runtime_invocation_handler_resolver,
    meta_graph_runtime_language_handler_resolver,
)
from aware_meta.runtime.invocation_commits import InvocationLaneCommitter


class MetaGraphGeneratedInvocationHandlerModule(Protocol):
    AWARE_META_GRAPH_INVOCATION_HANDLERS: Mapping[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedInvocationHandlerCallable,
    ]


def build_meta_graph_runtime_for_aware_package_manifests(
    *,
    package_manifest_paths: Iterable[Path],
    workspace_root: Path | None = None,
    aware_root: Path | None = None,
    composition_context_id: UUID | None = None,
    composite_name: str = "Aware Package Graph Runtime Context",
    handler_modules: Iterable[MetaGraphGeneratedLanguageHandlerModule] = (),
    bootstrap_modules: Iterable[MetaGraphGeneratedConstructorBootstrapModule] = (),
    handler_resolver: MetaGraphGeneratedLanguageHandlerResolver | None = None,
    invocation_handler_resolver: (
        MetaGraphGeneratedInvocationHandlerResolver | None
    ) = None,
    empty_lane_bootstrap_resolver: MetaGraphEmptyLaneBootstrapResolver | None = None,
    implementation_policy: MetaGraphImplementationPolicy | None = None,
    strict_package_graph_cache: bool = False,
    package_entries_by_manifest_path: (
        Mapping[
            Path,
            MetaRuntimePackageIndexEntry,
        ]
        | None
    ) = None,
    package_cache_owner_roots_by_manifest_path: Mapping[Path, Path] | None = None,
    source_analysis_allowed_manifest_paths: Iterable[Path] = (),
    package_graph_cache_request_signature: str | None = None,
    handler_owner_prefixes: Iterable[str] | None = None,
    load_source_graph_payloads: bool = True,
) -> MetaGraphRuntime:
    """Build a Meta-owned graph runtime from package OCG truth.

    This is the ergonomic production/proof entrypoint. It owns the context,
    executor, backend, and runtime composition while leaving lane activation as
    the explicit consumer boundary.
    """

    from aware_meta.runtime.graph_context import (  # noqa: WPS433
        build_meta_graph_runtime_context_for_aware_package_manifests,
    )
    from aware_meta.runtime.graph_runtime import MetaGraphRuntime  # noqa: WPS433

    resolved_handler_modules = tuple(handler_modules)
    resolved_bootstrap_modules = tuple(bootstrap_modules)
    if handler_resolver is not None and resolved_handler_modules:
        raise ValueError("Pass handler_resolver or handler_modules, not both.")
    if invocation_handler_resolver is not None and resolved_handler_modules:
        raise ValueError(
            "Pass invocation_handler_resolver or handler_modules, not both."
        )
    if empty_lane_bootstrap_resolver is not None and resolved_bootstrap_modules:
        raise ValueError(
            "Pass empty_lane_bootstrap_resolver or bootstrap_modules, not both."
        )

    phase_timings_s: dict[str, float] = {}
    total_started_at = perf_counter()
    phase_started_at = perf_counter()
    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=package_manifest_paths,
        workspace_root=workspace_root,
        composition_context_id=composition_context_id,
        composite_name=composite_name,
        strict_package_graph_cache=strict_package_graph_cache,
        package_entries_by_manifest_path=package_entries_by_manifest_path,
        package_cache_owner_roots_by_manifest_path=(
            package_cache_owner_roots_by_manifest_path
        ),
        source_analysis_allowed_manifest_paths=source_analysis_allowed_manifest_paths,
        package_graph_cache_request_signature=package_graph_cache_request_signature,
        load_source_graph_payloads=load_source_graph_payloads,
    )
    _record_meta_runtime_factory_phase_timing(
        phase_timings_s=phase_timings_s,
        phase_name="runtime_factory_build_graph_context_s",
        started_at=phase_started_at,
    )
    phase_started_at = perf_counter()
    discovered_provider_set = _discover_generated_handler_provider_set(
        context_index=context.index,
        handler_modules=resolved_handler_modules,
        bootstrap_modules=resolved_bootstrap_modules,
        handler_resolver=handler_resolver,
        invocation_handler_resolver=invocation_handler_resolver,
        empty_lane_bootstrap_resolver=empty_lane_bootstrap_resolver,
        handler_owner_prefixes=handler_owner_prefixes,
    )
    _record_meta_runtime_factory_phase_timing(
        phase_timings_s=phase_timings_s,
        phase_name="runtime_factory_discover_generated_handler_provider_set_s",
        started_at=phase_started_at,
    )
    phase_started_at = perf_counter()
    resolved_handler_resolver = (
        handler_resolver
        if handler_resolver is not None
        else (
            discovered_provider_set.handler_resolver
            if discovered_provider_set is not None
            else _generated_language_handler_registry(resolved_handler_modules)
        )
    )
    resolved_bootstrap_resolver = (
        empty_lane_bootstrap_resolver
        if empty_lane_bootstrap_resolver is not None
        else (
            discovered_provider_set.empty_lane_bootstrap_resolver
            if discovered_provider_set is not None
            else _generated_constructor_bootstrap_registry(resolved_bootstrap_modules)
        )
    )
    resolved_invocation_handler_resolver = (
        invocation_handler_resolver
        if invocation_handler_resolver is not None
        else (
            discovered_provider_set.invocation_handler_resolver
            if discovered_provider_set is not None
            else _generated_invocation_handler_registry(resolved_handler_modules)
        )
    )
    resolved_handler_resolver = meta_graph_runtime_language_handler_resolver(
        resolved_handler_resolver,
    )
    resolved_invocation_handler_resolver = (
        meta_graph_runtime_invocation_handler_resolver(
            resolved_invocation_handler_resolver,
        )
    )
    _record_meta_runtime_factory_phase_timing(
        phase_timings_s=phase_timings_s,
        phase_name="runtime_factory_resolve_handler_resolvers_s",
        started_at=phase_started_at,
    )
    phase_started_at = perf_counter()
    runtime_storage_root = aware_root if aware_root is not None else workspace_root
    pre_state_provider = _workspace_root_pre_state_provider(
        workspace_root=runtime_storage_root,
        empty_lane_bootstrap_resolver=resolved_bootstrap_resolver,
    )
    _record_meta_runtime_factory_phase_timing(
        phase_timings_s=phase_timings_s,
        phase_name="runtime_factory_build_pre_state_provider_s",
        started_at=phase_started_at,
    )
    phase_started_at = perf_counter()
    handler_executor = build_meta_graph_generated_handler_executor(
        handler_resolver=resolved_handler_resolver,
        invocation_handler_resolver=resolved_invocation_handler_resolver,
        pre_state_provider=pre_state_provider,
        empty_lane_bootstrap_resolver=resolved_bootstrap_resolver,
    )
    _record_meta_runtime_factory_phase_timing(
        phase_timings_s=phase_timings_s,
        phase_name="runtime_factory_build_handler_executor_s",
        started_at=phase_started_at,
    )
    phase_started_at = perf_counter()
    lane_committer = _workspace_root_lane_committer(
        workspace_root=runtime_storage_root,
    )
    _record_meta_runtime_factory_phase_timing(
        phase_timings_s=phase_timings_s,
        phase_name="runtime_factory_build_lane_committer_s",
        started_at=phase_started_at,
    )
    _record_meta_runtime_factory_phase_timing(
        phase_timings_s=phase_timings_s,
        phase_name="runtime_factory_total_s",
        started_at=total_started_at,
    )
    context = _context_with_runtime_factory_phase_timings(
        context=context,
        phase_timings_s=phase_timings_s,
    )
    return MetaGraphRuntime(
        backend=MetaGraphCommitInvocationBackend(
            handler_executor=handler_executor,
            lane_committer=lane_committer,
            implementation_policy=(
                implementation_policy or context.implementation_policy
            ),
        ),
        context=context,
    )


def _workspace_root_pre_state_provider(
    *,
    workspace_root: Path | None,
    empty_lane_bootstrap_resolver: MetaGraphEmptyLaneBootstrapResolver | None,
) -> MetaGraphPreStateProvider | None:
    if workspace_root is None:
        return None

    from aware_meta.graph.instance.commit.fs_store import (  # noqa: WPS433
        FSCommitStore,
        FSSnapshotStore,
    )
    from aware_meta.graph.instance.commit.materializer import (  # noqa: WPS433
        OIGMaterializer,
    )

    return MetaGraphOigMaterializerPreStateProvider(
        materializer=OIGMaterializer(
            commits=FSCommitStore(root_dir=workspace_root),
            snaps=FSSnapshotStore(root_dir=workspace_root),
        ),
        empty_lane_bootstrap_resolver=empty_lane_bootstrap_resolver,
    )


def _workspace_root_lane_committer(
    *, workspace_root: Path | None
) -> InvocationLaneCommitter | None:
    if workspace_root is None:
        return None

    from aware_meta.graph.instance.commit.committer import (  # noqa: WPS433
        FSLaneCommitter,
    )
    from aware_meta.graph.instance.commit.fs_store import FSCommitStore  # noqa: WPS433

    return FSLaneCommitter(store=FSCommitStore(root_dir=workspace_root))


def _discover_generated_handler_provider_set(
    *,
    context_index: object,
    handler_modules: tuple[MetaGraphGeneratedLanguageHandlerModule, ...],
    bootstrap_modules: tuple[MetaGraphGeneratedConstructorBootstrapModule, ...],
    handler_resolver: MetaGraphGeneratedLanguageHandlerResolver | None,
    invocation_handler_resolver: MetaGraphGeneratedInvocationHandlerResolver | None,
    empty_lane_bootstrap_resolver: MetaGraphEmptyLaneBootstrapResolver | None,
    handler_owner_prefixes: Iterable[str] | None,
) -> MetaGraphGeneratedHandlerProviderSet | None:
    if (
        handler_modules
        or bootstrap_modules
        or handler_resolver is not None
        or invocation_handler_resolver is not None
        or empty_lane_bootstrap_resolver is not None
    ):
        return None
    return discover_meta_graph_generated_handler_provider_set(
        index=context_index,
        handler_owner_prefixes=handler_owner_prefixes,
    )


def _record_meta_runtime_factory_phase_timing(
    *,
    phase_timings_s: dict[str, float],
    phase_name: str,
    started_at: float,
) -> None:
    phase_timings_s[phase_name] = round(
        float(phase_timings_s.get(phase_name, 0.0))
        + max(perf_counter() - started_at, 0.0),
        6,
    )


def _context_with_runtime_factory_phase_timings(
    *,
    context: MetaGraphRuntimeContext,
    phase_timings_s: Mapping[str, float],
) -> MetaGraphRuntimeContext:
    try:
        existing_timings = object.__getattribute__(context, "phase_timings_s") or {}
    except AttributeError:
        existing_timings = {}
    merged_timings = {
        **dict(existing_timings),
        **dict(sorted(phase_timings_s.items())),
    }
    try:
        return cast(
            "MetaGraphRuntimeContext",
            replace(context, phase_timings_s=merged_timings),
        )
    except TypeError:
        setattr(context, "phase_timings_s", merged_timings)
        return cast("MetaGraphRuntimeContext", context)


def _generated_language_handler_registry(
    modules: tuple[MetaGraphGeneratedLanguageHandlerModule, ...],
) -> MetaGraphGeneratedLanguageHandlerRegistry:
    handlers_by_key: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedLanguageHandlerCallable,
    ] = {}
    for module in modules:
        for key, handler in module.AWARE_META_GRAPH_HANDLERS.items():
            if key in handlers_by_key:
                raise ValueError(
                    "Duplicate Meta generated language handler key: "
                    f"{key.describe()}"
                )
            handlers_by_key[key] = handler
    return MetaGraphGeneratedLanguageHandlerRegistry(
        handlers_by_key=handlers_by_key,
    )


def _generated_constructor_bootstrap_registry(
    modules: tuple[MetaGraphGeneratedConstructorBootstrapModule, ...],
) -> MetaGraphGeneratedConstructorBootstrapRegistry:
    bootstraps_by_key: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphEmptyLaneBootstrapCallable,
    ] = {}
    for module in modules:
        for key, bootstrap in module.AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS.items():
            if key in bootstraps_by_key:
                raise ValueError(
                    "Duplicate Meta generated constructor bootstrap key: "
                    f"{key.describe()}"
                )
            bootstraps_by_key[key] = bootstrap
    return MetaGraphGeneratedConstructorBootstrapRegistry(
        bootstraps_by_key=bootstraps_by_key,
    )


def _generated_invocation_handler_registry(
    modules: tuple[MetaGraphGeneratedLanguageHandlerModule, ...],
) -> MetaGraphGeneratedInvocationHandlerRegistry | None:
    handlers_by_key: dict[
        MetaGraphGeneratedLanguageHandlerKey,
        MetaGraphGeneratedInvocationHandlerCallable,
    ] = {}
    for module in modules:
        try:
            invocation_handlers = cast(
                MetaGraphGeneratedInvocationHandlerModule,
                cast(object, module),
            ).AWARE_META_GRAPH_INVOCATION_HANDLERS
        except AttributeError:
            continue
        for key, handler in invocation_handlers.items():
            if key in handlers_by_key:
                raise ValueError(
                    "Duplicate Meta generated invocation handler key: "
                    f"{key.describe()}"
                )
            handlers_by_key[key] = handler
    if not handlers_by_key:
        return None
    return MetaGraphGeneratedInvocationHandlerRegistry(
        handlers_by_key=handlers_by_key,
    )


__all__ = ["build_meta_graph_runtime_for_aware_package_manifests"]
