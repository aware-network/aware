from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast
from uuid import uuid5, NAMESPACE_URL

from aware_attention.handlers._generated import meta_handlers as attention_meta_handlers
from aware_code.handlers._generated import meta_handlers as code_meta_handlers
from aware_identity.handlers._generated import meta_handlers as identity_meta_handlers
from aware_interface.handlers._generated import meta_handlers as interface_meta_handlers
from aware_interface.semantic_contract import (
    INTERFACE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
)
from aware_environment.handlers._generated import (
    meta_handlers as environment_meta_handlers,
)
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphCommitInvocationBackend,
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedInvocationHandlerRegistry,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphOigMaterializerPreStateProvider,
    MetaGraphRuntime,
    build_meta_graph_generated_constructor_bootstrap_registry,
    build_meta_graph_generated_handler_executor,
    build_meta_graph_generated_language_handler_registry,
)
from aware_meta.runtime.graph_context import (
    build_meta_graph_runtime_context_for_workspace_required_projections,
)

_GENERATED_META_HANDLER_MODULES: tuple[Any, ...] = (
    code_meta_handlers,
    attention_meta_handlers,
    identity_meta_handlers,
    environment_meta_handlers,
    interface_meta_handlers,
)


def _merge_generated_meta_maps(attribute_name: str) -> Mapping[Any, Any]:
    merged: dict[Any, Any] = {}
    for module in _GENERATED_META_HANDLER_MODULES:
        source = getattr(module, attribute_name, None)
        if isinstance(source, Mapping):
            merged.update(source)
    return merged


class _MergedGeneratedMetaHandlers:
    AWARE_META_GRAPH_HANDLERS = _merge_generated_meta_maps(
        "AWARE_META_GRAPH_HANDLERS",
    )
    AWARE_META_GRAPH_INVOCATION_HANDLERS = _merge_generated_meta_maps(
        "AWARE_META_GRAPH_INVOCATION_HANDLERS",
    )
    AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS = _merge_generated_meta_maps(
        "AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS",
    )


_INTERFACE_META_HANDLERS_ANY: Any = _MergedGeneratedMetaHandlers
_INTERFACE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _INTERFACE_META_HANDLERS_ANY,
)
_INTERFACE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _INTERFACE_META_HANDLERS_ANY,
)


@contextmanager
def isolated_meta_aware_root(
    root: Path,
    *,
    persistence_backend: str = "fs",
) -> Iterator[Path]:
    resolved = root.expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    (resolved / ".aware").mkdir(parents=True, exist_ok=True)
    previous = {
        "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
        "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
    }
    os.environ["AWARE_ROOT"] = str(resolved)
    os.environ["AWARE_PERSISTENCE_BACKEND"] = persistence_backend
    os.environ.pop("DATABASE_URL", None)
    try:
        yield resolved
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def build_interface_meta_runtime(repo_root: Path, *, workspace_root: Path):
    policy = MetaGraphImplementationPolicy(
        default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
    )
    context = build_meta_graph_runtime_context_for_workspace_required_projections(
        repo_root=repo_root,
        required_projection_names=(),
        required_package_names=INTERFACE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
        aware_root=workspace_root,
        composition_context_id=uuid5(
            NAMESPACE_URL,
            "aware://tests/interface/provider-owned-meta-runtime",
        ),
        composite_name="Interface Provider-Owned Meta Runtime",
    )
    bootstrap_resolver = build_meta_graph_generated_constructor_bootstrap_registry(
        module=_INTERFACE_META_BOOTSTRAP_MODULE,
    )
    handler_executor = build_meta_graph_generated_handler_executor(
        handler_resolver=build_meta_graph_generated_language_handler_registry(
            module=_INTERFACE_META_HANDLER_MODULE,
        ),
        invocation_handler_resolver=MetaGraphGeneratedInvocationHandlerRegistry(
            handlers_by_key=_MergedGeneratedMetaHandlers.AWARE_META_GRAPH_INVOCATION_HANDLERS,
        ),
        pre_state_provider=MetaGraphOigMaterializerPreStateProvider(
            materializer=OIGMaterializer(
                commits=FSCommitStore(root_dir=workspace_root),
                snaps=FSSnapshotStore(root_dir=workspace_root),
            ),
            empty_lane_bootstrap_resolver=bootstrap_resolver,
        ),
        empty_lane_bootstrap_resolver=bootstrap_resolver,
    )
    runtime = MetaGraphRuntime(
        backend=MetaGraphCommitInvocationBackend(
            handler_executor=handler_executor,
            lane_committer=FSLaneCommitter(
                store=FSCommitStore(root_dir=workspace_root),
            ),
            implementation_policy=policy,
        ),
        context=context,
    )
    assert runtime.context is not None
    return runtime
