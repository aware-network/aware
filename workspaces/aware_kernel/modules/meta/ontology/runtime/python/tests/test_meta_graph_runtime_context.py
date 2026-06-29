from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS,
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY,
    SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
    SemanticPackageMaterializationExecutionContextRequest,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_code.semantic_function_call_execution import (
    SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY,
)
from aware_meta.semantic_contract import (
    AWARE_META_SEMANTIC_CONTRACT,
    META_GRAPH_RUNTIME_CONTEXT_KEY,
    META_OBJECT_CONFIG_GRAPH_OWNER,
)
from aware_meta.runtime import (
    MetaGraphRuntimeContext,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_context,
    build_meta_graph_runtime_index_snapshot,
    find_meta_graph_projection_hash_by_name,
)
import aware_meta.runtime.graph_context as graph_context_module
from aware_meta.runtime.graph_context import (
    _clear_meta_graph_runtime_index_snapshot_cache,
    _clear_meta_package_graph_session_cache,
    _external_graph_signature,
    _ontology_catalog_module_id,
    _ontology_package_manifest_catalog,
    _package_graph_cache_request_signature,
    _source_text_manifest_hash,
    _stable_object_config_graph_package_branch_id,
    _try_load_catalog_cached_package_graphs,
    _try_load_cached_package_graphs,
    _workspace_materialization_implementation_policy,
    _workspace_materialization_package_manifest_paths,
    build_meta_graph_runtime_context_for_aware_package_manifests,
    build_meta_graph_runtime_context_for_workspace_required_projections,
    build_meta_graph_runtime_context_for_semantic_materialization,
    build_meta_workspace_materialization_runtime_context,
    resolve_workspace_required_projection_package_manifest_paths,
)
from aware_meta.runtime.handler_executor.index import MetaGraphFunctionImplOwnership
from aware_meta.runtime.package_index import (
    MetaRuntimePackageIndexPatch,
    MetaRuntimePackageIndexEntry,
    MetaRuntimeProjectionIndexEntry,
    MetaRuntimeSemanticObjectIndexEntry,
    build_meta_runtime_package_projection_index,
    apply_meta_runtime_package_index_patch,
    meta_runtime_package_projection_index_path,
    record_full_package_materialization_index,
    record_meta_runtime_package_index_patch,
)
from aware_meta.package_graph_reuse_cache import (
    OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_SOURCE_GRAPH,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
    object_config_graph_package_context_reuse_cache_path,
    object_config_graph_package_reuse_cache_path,
)
from aware_meta.graph.config.namespace.membership import (
    build_namespace_membership_payload_from_ocg_identity,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_enums import FunctionImplKind
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_id,
    stable_object_config_graph_package_id,
)


def _aware_repo_root() -> Path:
    return Path(__file__).resolve().parents[8]


def test_ontology_catalog_module_id_handles_external_workspace_dependency(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "home-checkout"
    repo_root.mkdir()
    module_root = (
        tmp_path / "deps" / "aware" / "workspaces" / "aware_kernel" / "modules" / "api"
    )
    module_root.mkdir(parents=True)

    module_id = _ontology_catalog_module_id(
        repo_root=repo_root,
        module_root=module_root,
    )

    assert module_id == "aware_kernel:api"


@pytest.fixture(autouse=True)
def _clear_meta_graph_context_session_caches() -> Iterator[None]:
    _clear_meta_package_graph_session_cache()
    _clear_meta_graph_runtime_index_snapshot_cache()
    yield
    _clear_meta_package_graph_session_cache()
    _clear_meta_graph_runtime_index_snapshot_cache()


def _runtime_graph(
    *,
    name: str = "Aware Tests",
    fqn_prefix: str = "aware.tests",
    projection_name: str = "Workspace",
    projection_hash: str = "sha256:test:Workspace",
) -> ObjectConfigGraph:
    graph_id = uuid4()
    class_config = ClassConfig(
        class_fqn=f"{fqn_prefix}.Workspace",
        name="Workspace",
    )
    return ObjectConfigGraph(
        id=graph_id,
        name=name,
        hash=f"sha256:test:{name}",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                object_config_graph_id=graph_id,
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_config.class_fqn,
                class_config=class_config,
            )
        ],
        object_projection_graphs=[
            ObjectProjectionGraph(
                object_config_graph_id=graph_id,
                language=CodeLanguage.aware,
                name=projection_name,
                projection_hash=projection_hash,
            )
        ],
    )


def _write_context_graph_cache(
    *,
    workspace_root: Path,
    manifest_path: Path,
    package_name: str,
    fqn_prefix: str,
    graph: ObjectConfigGraph,
    runtime_graph: ObjectConfigGraph | None = None,
    source_manifest_hash: str = "sha256:test:source-manifest",
    dependency_signature: str = "sha256:test:dependency-signature",
    runtime_graph_derivation_signature: str = (
        OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
    ),
) -> None:
    effective_runtime_graph = runtime_graph or graph
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    cache_path = object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "v": OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
                "cache_kind": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS
                ),
                "source_manifest_hash": source_manifest_hash,
                "dependency_signature": dependency_signature,
                "runtime_graph_derivation_signature": (
                    runtime_graph_derivation_signature
                ),
                "package_name": package_name,
                "fqn_prefix": fqn_prefix,
                "object_config_graph_id": str(graph.id),
                "object_config_graph_package_id": str(package_id),
                "source_object_config_graph_hash": graph.hash,
                "runtime_object_config_graph_hash": effective_runtime_graph.hash,
                "source_object_config_graph": _graph_cache_payload(graph),
                "runtime_object_config_graph": _graph_cache_payload(
                    effective_runtime_graph
                ),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_materialized_package_cache(
    *,
    workspace_root: Path,
    manifest_path: Path,
    package_name: str,
    fqn_prefix: str,
    graph: ObjectConfigGraph,
    materialization_index_receipt: dict[str, object] | None = None,
    source_manifest_hash: str = "sha256:test:source-manifest",
    dependency_signature: str = "sha256:test:dependency-signature",
) -> None:
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    cache_path = object_config_graph_package_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "v": OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
                "cache_kind": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE
                ),
                "source_manifest_hash": source_manifest_hash,
                "dependency_signature": dependency_signature,
                "package_name": package_name,
                "fqn_prefix": fqn_prefix,
                "object_config_graph_id": str(graph.id),
                "object_config_graph_hash": graph.hash,
                "object_config_graph_package_id": str(package_id),
                "object_config_graph": _graph_cache_payload(graph),
                "materialization_index_receipt": materialization_index_receipt,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _graph_cache_payload(graph: ObjectConfigGraph) -> dict[str, object]:
    payload = graph.model_dump(mode="json", by_alias=True, exclude_none=True)
    payload["namespace_membership"] = list(
        build_namespace_membership_payload_from_ocg_identity(ocg=graph)
    )
    return payload


def test_catalog_context_runtime_only_load_skips_source_graph_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_graph = _runtime_graph(
        name="Runtime Only Source",
        fqn_prefix="aware.runtime_only",
    )
    runtime_graph = source_graph.model_copy(
        update={
            "name": "Runtime Only Runtime",
            "hash": "sha256:test:runtime-only-runtime",
        }
    )
    identity = graph_context_module._PackageGraphCacheIdentity(  # noqa: SLF001
        package_name="runtime-only-ontology",
        fqn_prefix="aware.runtime_only",
        branch_id=uuid4(),
        object_config_graph_id=source_graph.id,
        object_config_graph_package_id=stable_object_config_graph_package_id(
            package_name="runtime-only-ontology",
            fqn_prefix="aware.runtime_only",
        ),
        source_manifest_hash="sha256:test:runtime-only-source-manifest",
        dependency_signature=_external_graph_signature(external_graphs=()),
    )
    payload = {
        "source_object_config_graph_hash": source_graph.hash,
        "runtime_object_config_graph_hash": runtime_graph.hash,
        "source_object_config_graph": {"invalid": "would-fail-if-loaded"},
        "runtime_object_config_graph": runtime_graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
    }
    original_loader = (
        graph_context_module._load_graph_payload_from_context_cache
    )  # noqa: SLF001
    loaded_payload_keys: list[str] = []

    def _observed_loader(**kwargs: object) -> ObjectConfigGraph | None:
        payload_key = kwargs["payload_key"]
        assert isinstance(payload_key, str)
        loaded_payload_keys.append(payload_key)
        if payload_key == "source_object_config_graph":
            raise AssertionError("runtime-only cache hit loaded source graph body")
        return original_loader(**kwargs)

    monkeypatch.setattr(
        graph_context_module,
        "_load_graph_payload_from_context_cache",
        _observed_loader,
    )

    cached_graphs = (
        graph_context_module._load_catalog_context_package_graphs(  # noqa: SLF001
            payload=payload,
            identity=identity,
            load_source_graph=False,
            phase_timings_s={},
            diagnostics={},
        )
    )

    assert cached_graphs is not None
    assert cached_graphs.source_graph is None
    assert cached_graphs.runtime_graph.id == runtime_graph.id
    assert cached_graphs.source_graph_ref.object_config_graph_hash == source_graph.hash
    assert loaded_payload_keys == ["runtime_object_config_graph"]


def _write_minimal_aware_manifest(
    *,
    manifest_path: Path,
    package_name: str,
    fqn_prefix: str,
    dependency_package_names: tuple[str, ...] = (),
) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "aware = 1",
        "",
        "[package]",
        f'package_name = "{package_name}"',
        f'fqn_prefix = "{fqn_prefix}"',
        'kind = "ontology"',
        "version_number = 1",
        f'title = "{package_name}"',
        f'description = "{package_name}"',
        "",
        "[build]",
        f'environment_slug = "{fqn_prefix}"',
    ]
    for dependency_package_name in dependency_package_names:
        lines.extend(
            [
                "",
                "[[dependencies]]",
                f'package_name = "{dependency_package_name}"',
            ]
        )
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_meta_graph_context_orders_manifest_targets_by_package_dependencies(
    tmp_path: Path,
) -> None:
    api_manifest_path = tmp_path / "api-service-dto" / "aware.toml"
    environment_manifest_path = tmp_path / "environment-service-dto" / "aware.toml"
    meta_manifest_path = tmp_path / "meta-service-dto" / "aware.toml"
    _write_minimal_aware_manifest(
        manifest_path=api_manifest_path,
        package_name="api-service-dto",
        fqn_prefix="aware_api_service_dto",
    )
    _write_minimal_aware_manifest(
        manifest_path=environment_manifest_path,
        package_name="environment-service-dto",
        fqn_prefix="aware_environment_service_dto",
        dependency_package_names=("meta-service-dto",),
    )
    _write_minimal_aware_manifest(
        manifest_path=meta_manifest_path,
        package_name="meta-service-dto",
        fqn_prefix="aware_meta_service_dto",
    )

    ordered_paths = graph_context_module._topologically_order_package_manifest_paths(
        (
            api_manifest_path,
            environment_manifest_path,
            meta_manifest_path,
        ),
        package_entries_by_manifest_path={},
    )

    assert ordered_paths == (
        api_manifest_path.resolve(),
        meta_manifest_path.resolve(),
        environment_manifest_path.resolve(),
    )


def test_meta_graph_runtime_context_builds_protocol_index_snapshot() -> None:
    graph = _runtime_graph()

    context = build_meta_graph_runtime_context(runtime_graphs=(graph,))

    assert isinstance(context, MetaGraphRuntimeContext)
    assert isinstance(context.index, MetaGraphRuntimeIndex)
    assert context.index.ocg.name == "Aware Tests"
    assert tuple(context.index.class_configs_by_id.values())[0].name == "Workspace"
    assert context.index.opg_by_hash["sha256:test:Workspace"].name == "Workspace"
    assert context.projection_hash_for_name("Workspace") == "sha256:test:Workspace"
    assert context.phase_timings_s["build_runtime_index_snapshot"] >= 0.0
    assert context.phase_timings_s["projection_hash_by_name"] >= 0.0
    assert context.phase_timings_s["total"] >= 0.0


def test_meta_graph_runtime_context_reuses_runtime_index_snapshot_cache() -> None:
    _clear_meta_graph_runtime_index_snapshot_cache()
    graph = _runtime_graph()

    first = build_meta_graph_runtime_context(runtime_graphs=(graph,))
    second = build_meta_graph_runtime_context(
        runtime_graphs=(graph.model_copy(deep=True),)
    )

    assert first.runtime_index_snapshot_cache_status == "miss"
    assert second.runtime_index_snapshot_cache_status == "hit"
    assert second.index is first.index
    assert second.projection_hash_for_name("Workspace") == "sha256:test:Workspace"


def test_meta_graph_runtime_context_cache_misses_on_graph_identity_drift() -> None:
    _clear_meta_graph_runtime_index_snapshot_cache()
    graph = _runtime_graph()
    updated_graph = graph.model_copy(deep=True)
    updated_graph.hash = "sha256:test:updated"

    first = build_meta_graph_runtime_context(runtime_graphs=(graph,))
    second = build_meta_graph_runtime_context(runtime_graphs=(updated_graph,))

    assert first.runtime_index_snapshot_cache_status == "miss"
    assert second.runtime_index_snapshot_cache_status == "miss"
    assert second.index is not first.index


def test_meta_graph_projection_lookup_preserves_authored_name_exactly() -> None:
    graph = _runtime_graph(projection_name="FocusScope")
    context = build_meta_graph_runtime_context(runtime_graphs=(graph,))

    assert context.projection_hash_for_name("FocusScope") == "sha256:test:Workspace"
    assert (
        find_meta_graph_projection_hash_by_name(
            index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
            projection_name="FocusScope",
        )
        == "sha256:test:Workspace"
    )

    with pytest.raises(ValueError, match="focus_scope"):
        context.projection_hash_for_name("focus_scope")


def test_meta_graph_context_rejects_conflicting_projection_names() -> None:
    graph = _runtime_graph()
    graph.object_projection_graphs.append(
        ObjectProjectionGraph(
            object_config_graph_id=graph.id,
            language=CodeLanguage.aware,
            name="Workspace",
            projection_hash="sha256:test:conflict",
        )
    )

    with pytest.raises(ValueError, match="Conflicting projection hashes"):
        build_meta_graph_runtime_context(runtime_graphs=(graph,))


def test_meta_graph_runtime_context_uses_shallow_composite_for_read_index() -> None:
    graph_a = _runtime_graph(
        name="Alpha",
        fqn_prefix="aware_alpha",
        projection_name="Alpha",
        projection_hash="sha256:test:Alpha",
    )
    graph_b = _runtime_graph(
        name="Beta",
        fqn_prefix="aware_beta",
        projection_name="Beta",
        projection_hash="sha256:test:Beta",
    )

    context = build_meta_graph_runtime_context(runtime_graphs=(graph_a, graph_b))

    assert context.composite is True
    assert context.index.ocg.id not in {graph_a.id, graph_b.id}
    assert context.index.ocg.object_config_graph_identity is not None
    assert context.index.ocg.object_config_graph_identity.key == "aware.runtime_context"
    assert {
        node.object_config_graph_id
        for node in context.index.ocg.object_config_graph_nodes
    } == {graph_a.id, graph_b.id}
    assert context.projection_hash_for_name("Alpha") == "sha256:test:Alpha"
    assert context.projection_hash_for_name("Beta") == "sha256:test:Beta"


def test_meta_graph_runtime_context_dedupes_projection_identity_in_composite() -> None:
    owner_graph = _runtime_graph(
        name="Owner",
        fqn_prefix="aware_owner",
        projection_name="ObjectConfigGraph",
        projection_hash="sha256:test:owner-object-config-graph",
    )
    copied_projection_graph = _runtime_graph(
        name="Consumer",
        fqn_prefix="aware_consumer",
        projection_name="ObjectConfigGraph",
        projection_hash="sha256:test:stale-copied-object-config-graph",
    )
    copied_projection_graph.object_projection_graphs[0].id = (
        owner_graph.object_projection_graphs[0].id
    )

    context = build_meta_graph_runtime_context(
        runtime_graphs=(owner_graph, copied_projection_graph),
    )

    matching_projection_graphs = [
        projection
        for projection in context.index.ocg.object_projection_graphs
        if projection.id == owner_graph.object_projection_graphs[0].id
    ]
    assert len(matching_projection_graphs) == 1
    assert matching_projection_graphs[0].projection_hash == (
        "sha256:test:owner-object-config-graph"
    )
    assert context.projection_hash_for_name("ObjectConfigGraph") == (
        "sha256:test:owner-object-config-graph"
    )


def test_meta_graph_runtime_context_keeps_source_and_runtime_graphs_split() -> None:
    source_graph = _runtime_graph(
        name="Source Demo",
        fqn_prefix="aware_demo",
        projection_name="Demo",
        projection_hash="sha256:test:Demo:source",
    )
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.name = "Runtime Demo"
    runtime_graph.hash = "sha256:test:Demo:runtime"
    runtime_graph.object_projection_graphs[0].projection_hash = (
        "sha256:test:Demo:runtime"
    )

    context = build_meta_graph_runtime_context(
        runtime_graphs=(runtime_graph,),
        source_graphs=(source_graph,),
    )

    assert context.source_graphs == (source_graph,)
    assert context.runtime_graphs == (runtime_graph,)
    assert context.source_graph_ids == (source_graph.id,)
    assert context.runtime_graph_ids == (runtime_graph.id,)
    assert context.projection_hash_for_name("Demo") == "sha256:test:Demo:runtime"


def test_meta_graph_runtime_context_derives_new_sources_with_runtime_dependency_closure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependency_runtime_graph = _runtime_graph(
        name="Dependency",
        fqn_prefix="aware_dependency",
        projection_name="Dependency",
        projection_hash="sha256:test:Dependency",
    )
    source_graph = _runtime_graph(
        name="Source",
        fqn_prefix="aware_source",
        projection_name="Source",
        projection_hash="sha256:test:Source",
    )
    source_graph.object_projection_graphs = []
    captured: dict[str, object] = {}

    def fake_derive_runtime_graphs(
        source_graphs: tuple[ObjectConfigGraph, ...],
        *,
        external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
        include_projection_graphs: bool = True,
    ) -> tuple[ObjectConfigGraph, ...]:
        captured["source_graphs"] = source_graphs
        captured["external_runtime_graphs"] = external_runtime_graphs
        captured["include_projection_graphs"] = include_projection_graphs
        runtime_graph = source_graph.model_copy(deep=True)
        runtime_graph.hash = "sha256:test:Source:runtime"
        runtime_graph.object_projection_graphs = []
        return (runtime_graph,)

    monkeypatch.setattr(
        graph_context_module,
        "derive_runtime_object_config_graphs",
        fake_derive_runtime_graphs,
    )

    context = build_meta_graph_runtime_context(
        runtime_graphs=(dependency_runtime_graph,),
        source_graphs=(source_graph,),
    )

    assert captured["source_graphs"] == (source_graph,)
    assert captured["external_runtime_graphs"] == (dependency_runtime_graph,)
    assert captured["include_projection_graphs"] is True
    assert context.runtime_graph_ids == (
        dependency_runtime_graph.id,
        source_graph.id,
    )


def test_meta_graph_runtime_context_does_not_rederive_explicit_runtime_graph_fqn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    explicit_runtime_graph = _runtime_graph(
        name="Dependency",
        fqn_prefix="aware_dependency",
        projection_name="Dependency",
        projection_hash="sha256:test:Dependency",
    )
    source_graph = _runtime_graph(
        name="Dependency Source",
        fqn_prefix="aware_dependency",
        projection_name="Dependency",
        projection_hash="sha256:test:Dependency:source",
    )
    captured: dict[str, object] = {}

    def fake_derive_runtime_graphs(
        source_graphs: tuple[ObjectConfigGraph, ...],
        *,
        external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
        include_projection_graphs: bool = True,
    ) -> tuple[ObjectConfigGraph, ...]:
        captured["source_graphs"] = source_graphs
        captured["external_runtime_graphs"] = external_runtime_graphs
        captured["include_projection_graphs"] = include_projection_graphs
        return ()

    monkeypatch.setattr(
        graph_context_module,
        "derive_runtime_object_config_graphs",
        fake_derive_runtime_graphs,
    )

    context = build_meta_graph_runtime_context(
        runtime_graphs=(explicit_runtime_graph,),
        source_graphs=(source_graph,),
    )

    assert captured == {}
    assert context.runtime_graph_ids == (explicit_runtime_graph.id,)
    assert context.source_graph_ids == (source_graph.id,)


def test_meta_graph_index_snapshot_has_no_legacy_runtime_dependency() -> None:
    source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/graph_context.py"
    ).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "RuntimeHarness" not in source
    assert "AwareRuntimeIndex" not in source


def test_meta_graph_context_loads_package_graphs_from_meta_reuse_cache(
    tmp_path: Path,
) -> None:
    _clear_meta_package_graph_session_cache()
    workspace_root = tmp_path
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    sources_root = package_root / "aware"
    sources_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text("", encoding="utf-8")
    source_text = "class Demo {}\nprojection Demo {\n    root demo.Demo\n}\n"
    (sources_root / "demo.aware").write_text(source_text, encoding="utf-8")

    package_name = "demo-ontology"
    fqn_prefix = "demo"
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    source_graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo",
    )
    source_graph.id = graph_id
    for node in source_graph.object_config_graph_nodes:
        node.object_config_graph_id = graph_id
    for projection in source_graph.object_projection_graphs:
        projection.object_config_graph_id = graph_id
    source_graph.object_projection_graph_declarations.append(
        ObjectProjectionGraphDeclaration(
            object_config_graph_id=graph_id,
            key="aware_demo:Demo",
            projection_name="Demo",
        )
    )
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.hash = "sha256:test:Demo:runtime"
    runtime_graph.object_projection_graphs[0].projection_hash = (
        "sha256:test:Demo:runtime"
    )
    runtime_graph.object_projection_graphs[0].projection_hash = (
        "sha256:test:Demo:runtime-projection"
    )

    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    cache_path = object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    )
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps(
            {
                "v": OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
                "cache_kind": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS
                ),
                "source_manifest_hash": _source_text_manifest_hash(
                    source_text_by_relative_path={"demo.aware": source_text}
                ),
                "dependency_signature": _external_graph_signature(external_graphs=()),
                "runtime_graph_derivation_signature": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
                ),
                "object_config_graph_id": str(graph_id),
                "object_config_graph_package_id": str(package_id),
                "source_object_config_graph_hash": source_graph.hash,
                "runtime_object_config_graph_hash": runtime_graph.hash,
                "source_object_config_graph": source_graph.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
                "runtime_object_config_graph": runtime_graph.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    spec = SimpleNamespace(
        package=SimpleNamespace(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        build=SimpleNamespace(
            sources_dir="aware",
            include_paths=("**/*.aware",),
            exclude_paths=(),
        ),
    )

    phase_timings_s: dict[str, float] = {}
    diagnostics: dict[str, object] = {}
    cached = _try_load_cached_package_graphs(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        spec=spec,
        external_graphs=(),
        phase_timings_s=phase_timings_s,
        diagnostics=diagnostics,
    )

    assert cached is not None
    assert diagnostics == {
        "cache_status": "hit",
        "cache_source": "durable_reuse_cache",
        "cache_miss_reason": None,
    }
    assert phase_timings_s["read_package_source_texts"] >= 0.0
    assert phase_timings_s["source_text_manifest_hash"] >= 0.0
    assert phase_timings_s["read_context_cache_payload"] >= 0.0
    assert phase_timings_s["load_runtime_graph_payload"] >= 0.0
    assert cached.source_graph.id == graph_id
    assert cached.source_graph.hash == source_graph.hash
    assert cached.runtime_graph.hash == runtime_graph.hash
    assert cached.runtime_graph.object_projection_graphs[0].projection_hash == (
        "sha256:test:Demo:runtime-projection"
    )
    assert cached.source_graph.object_projection_graphs[0].name == "Demo"
    assert (
        cached.source_graph.object_projection_graph_declarations[0].projection_name
        == "Demo"
    )


def test_meta_graph_context_non_strict_cache_reads_through_materialized_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    sources_root = package_root / "aware"
    sources_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text("", encoding="utf-8")
    source_text = "class Demo {}\nprojection Demo {\n    root demo.Demo\n}\n"
    (sources_root / "demo.aware").write_text(source_text, encoding="utf-8")

    package_name = "demo-ontology"
    fqn_prefix = "demo"
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    source_graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo:materialized",
    )
    source_graph.id = graph_id
    for node in source_graph.object_config_graph_nodes:
        node.object_config_graph_id = graph_id
    for projection in source_graph.object_projection_graphs:
        projection.object_config_graph_id = graph_id
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.hash = "sha256:test:Demo:runtime-from-materialized-cache"
    runtime_graph.object_projection_graphs[0].projection_hash = (
        "sha256:test:Demo:runtime-from-materialized-cache"
    )
    monkeypatch.setattr(
        "aware_meta.runtime.graph_context.derive_runtime_object_config_graph",
        lambda *_args, **_kwargs: SimpleNamespace(runtime_graph=runtime_graph),
    )
    source_manifest_hash = _source_text_manifest_hash(
        source_text_by_relative_path={"demo.aware": source_text}
    )
    fresh_dependency_signature = _external_graph_signature(external_graphs=())
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        runtime_graph=runtime_graph,
        source_manifest_hash=source_manifest_hash,
        dependency_signature="sha256:test:stale-context-dependency",
    )
    _write_materialized_package_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        source_manifest_hash=source_manifest_hash,
        dependency_signature=fresh_dependency_signature,
    )
    spec = SimpleNamespace(
        package=SimpleNamespace(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        build=SimpleNamespace(
            sources_dir="aware",
            include_paths=("**/*.aware",),
            exclude_paths=(),
        ),
    )
    phase_timings_s: dict[str, float] = {}
    diagnostics: dict[str, object] = {}

    cached = _try_load_cached_package_graphs(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        spec=spec,
        external_graphs=(),
        phase_timings_s=phase_timings_s,
        diagnostics=diagnostics,
    )

    assert cached is not None
    assert cached.runtime_graph.hash == runtime_graph.hash
    assert diagnostics["cache_status"] == "hit"
    assert diagnostics["cache_source"] == "materialized_package_cache"
    assert diagnostics["context_cache_miss_reason"] == "dependency_signature_mismatch"
    assert diagnostics["materialized_cache_status"] == "hit"
    assert diagnostics["context_cache_refresh_status"] == "written"
    assert "read_context_cache_payload" in phase_timings_s
    assert "read_materialized_cache_payload" in phase_timings_s
    assert "derive_runtime_graph_from_materialized_cache" in phase_timings_s
    assert "write_context_cache_from_materialized_payload" in phase_timings_s

    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    refreshed_payload = json.loads(
        object_config_graph_package_context_reuse_cache_path(
            aware_root=workspace_root,
            branch_id=branch_id,
            object_config_graph_package_id=package_id,
        ).read_text(encoding="utf-8")
    )
    assert refreshed_payload["dependency_signature"] == fresh_dependency_signature
    assert refreshed_payload["runtime_object_config_graph_hash"] == runtime_graph.hash


def test_meta_graph_context_reuses_package_graph_session_cache(
    tmp_path: Path,
) -> None:
    _clear_meta_package_graph_session_cache()
    workspace_root = tmp_path
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    sources_root = package_root / "aware"
    sources_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text("", encoding="utf-8")
    source_text = "class Demo {}\nprojection Demo {\n    root demo.Demo\n}\n"
    (sources_root / "demo.aware").write_text(source_text, encoding="utf-8")

    package_name = "demo-ontology"
    fqn_prefix = "demo"
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    source_graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo",
    )
    source_graph.id = graph_id
    for node in source_graph.object_config_graph_nodes:
        node.object_config_graph_id = graph_id
    for projection in source_graph.object_projection_graphs:
        projection.object_config_graph_id = graph_id
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.hash = "sha256:test:Demo:runtime"
    runtime_graph.object_projection_graphs[0].projection_hash = (
        "sha256:test:Demo:runtime"
    )
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        runtime_graph=runtime_graph,
        source_manifest_hash=_source_text_manifest_hash(
            source_text_by_relative_path={"demo.aware": source_text}
        ),
        dependency_signature=_external_graph_signature(external_graphs=()),
    )
    spec = SimpleNamespace(
        package=SimpleNamespace(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        build=SimpleNamespace(
            sources_dir="aware",
            include_paths=("**/*.aware",),
            exclude_paths=(),
        ),
    )

    first_timings: dict[str, float] = {}
    first_diagnostics: dict[str, object] = {}
    first = _try_load_cached_package_graphs(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        spec=spec,
        external_graphs=(),
        phase_timings_s=first_timings,
        diagnostics=first_diagnostics,
    )
    cache_path = object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=_stable_object_config_graph_package_branch_id(
            workspace_root=workspace_root,
            aware_toml_path=manifest_path,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        object_config_graph_package_id=stable_object_config_graph_package_id(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
    )
    cache_path.unlink()
    second_timings: dict[str, float] = {}
    second_diagnostics: dict[str, object] = {}
    second = _try_load_cached_package_graphs(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        spec=spec,
        external_graphs=(),
        phase_timings_s=second_timings,
        diagnostics=second_diagnostics,
    )

    assert first is not None
    assert second is first
    assert second is not None
    assert first_diagnostics["cache_source"] == "durable_reuse_cache"
    assert second_diagnostics == {
        "cache_status": "hit",
        "cache_source": "session",
        "cache_miss_reason": None,
    }
    assert second_timings["package_graph_session_cache_lookup"] >= 0.0
    assert "read_context_cache_payload" not in second_timings
    assert second.runtime_graph.hash == "sha256:test:Demo:runtime"


def test_meta_graph_context_strict_catalog_cache_skips_source_analysis(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    package_name = "demo-ontology"
    fqn_prefix = "demo"
    _write_minimal_aware_manifest(
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    source_graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo",
    )
    source_graph.id = graph_id
    for node in source_graph.object_config_graph_nodes:
        node.object_config_graph_id = graph_id
    for projection in source_graph.object_projection_graphs:
        projection.object_config_graph_id = graph_id
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.hash = "sha256:test:Demo:runtime"
    runtime_graph.object_projection_graphs[0].projection_hash = (
        "sha256:test:Demo:runtime"
    )
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        runtime_graph=runtime_graph,
        source_manifest_hash="sha256:test:source-from-commit",
        dependency_signature=_external_graph_signature(external_graphs=()),
    )
    entry = MetaRuntimePackageIndexEntry(
        module_id="demo",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=(manifest_path,),
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path={manifest_path.resolve(): entry},
        package_graph_cache_request_signature="sha256:test:request",
    )

    package_timing = context.package_timings[0]
    assert package_timing.cache_status == "hit"
    assert package_timing.cache_source == "catalog_context_reuse_cache"
    assert "read_package_source_texts" not in package_timing.phase_timings_s
    assert "analyze_meta_ocg_sources" not in package_timing.phase_timings_s
    assert context.projection_hash_for_name("Demo") == ("sha256:test:Demo:runtime")


def test_meta_graph_context_strict_catalog_cache_reads_through_materialized_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    package_name = "demo-ontology"
    fqn_prefix = "demo"
    _write_minimal_aware_manifest(
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    source_graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo:materialized",
    )
    source_graph.id = graph_id
    for node in source_graph.object_config_graph_nodes:
        node.object_config_graph_id = graph_id
    for projection in source_graph.object_projection_graphs:
        projection.object_config_graph_id = graph_id
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.hash = "sha256:test:Demo:runtime-from-materialized-cache"
    runtime_graph.object_projection_graphs[0].projection_hash = (
        "sha256:test:Demo:runtime-from-materialized-cache"
    )
    monkeypatch.setattr(
        "aware_meta.runtime.graph_context.derive_runtime_object_config_graph",
        lambda *_args, **_kwargs: SimpleNamespace(runtime_graph=runtime_graph),
    )
    source_manifest_hash = "sha256:test:source-from-committed-materialization"
    fresh_dependency_signature = _external_graph_signature(external_graphs=())
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        source_manifest_hash=source_manifest_hash,
        dependency_signature="sha256:test:stale-dependency-signature",
    )
    _write_materialized_package_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        source_manifest_hash=source_manifest_hash,
        dependency_signature=fresh_dependency_signature,
    )
    entry = MetaRuntimePackageIndexEntry(
        module_id="demo",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=(manifest_path,),
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path={manifest_path.resolve(): entry},
        package_graph_cache_request_signature="sha256:test:request",
    )

    package_timing = context.package_timings[0]
    assert package_timing.cache_status == "hit"
    assert package_timing.cache_source == "catalog_materialized_package_cache"
    assert "read_package_source_texts" not in package_timing.phase_timings_s
    assert "analyze_meta_ocg_sources" not in package_timing.phase_timings_s
    assert "read_catalog_context_cache_payload" in package_timing.phase_timings_s
    assert "read_catalog_materialized_cache_payload" in (package_timing.phase_timings_s)
    assert "derive_runtime_graph_from_materialized_cache" in (
        package_timing.phase_timings_s
    )
    assert "write_catalog_context_cache_from_materialized_payload" in (
        package_timing.phase_timings_s
    )

    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    context_cache_path = object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    )
    refreshed_payload = json.loads(context_cache_path.read_text(encoding="utf-8"))

    assert refreshed_payload["cache_kind"] == (
        OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS
    )
    assert refreshed_payload["source_manifest_hash"] == source_manifest_hash
    assert refreshed_payload["dependency_signature"] == fresh_dependency_signature
    assert refreshed_payload["runtime_graph_derivation_signature"] == (
        OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
    )
    assert refreshed_payload["runtime_object_config_graph_hash"] == (
        context.runtime_graph_by_package_name[package_name].hash
    )


def test_meta_graph_context_strict_catalog_cache_fails_closed_on_stale_read_through(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    package_name = "demo-ontology"
    fqn_prefix = "demo"
    _write_minimal_aware_manifest(
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    source_graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo:stale",
    )
    source_graph.id = graph_id
    for node in source_graph.object_config_graph_nodes:
        node.object_config_graph_id = graph_id
    for projection in source_graph.object_projection_graphs:
        projection.object_config_graph_id = graph_id
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        dependency_signature="sha256:test:stale-context-dependency",
    )
    _write_materialized_package_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        dependency_signature="sha256:test:stale-materialized-dependency",
    )
    diagnostics: dict[str, object] = {}
    phase_timings_s: dict[str, float] = {}

    cached_graphs = _try_load_catalog_cached_package_graphs(
        cache_owner_root=workspace_root,
        catalog_entry=MetaRuntimePackageIndexEntry(
            module_id="demo",
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            manifest_path=manifest_path,
        ),
        external_graphs=(),
        phase_timings_s=phase_timings_s,
        diagnostics=diagnostics,
    )

    assert cached_graphs is None
    assert diagnostics["cache_status"] == "miss"
    assert diagnostics["cache_miss_reason"] == "dependency_signature_mismatch"
    assert diagnostics["catalog_context_cache_status"] == "miss"
    assert diagnostics["catalog_context_cache_miss_reason"] == (
        "dependency_signature_mismatch"
    )
    assert diagnostics["catalog_materialized_cache_status"] == "miss"
    assert diagnostics["catalog_materialized_cache_miss_reason"] == (
        "dependency_signature_mismatch"
    )
    assert "read_package_source_texts" not in phase_timings_s
    assert "analyze_meta_ocg_sources" not in phase_timings_s


def test_meta_graph_context_rejects_stale_nested_namespace_cache_shape(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    package_name = "demo-ontology"
    fqn_prefix = "demo"
    _write_minimal_aware_manifest(
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    source_graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo:nested-stale",
    )
    source_graph.id = graph_id
    for node in source_graph.object_config_graph_nodes:
        node.object_config_graph_id = graph_id
    for projection in source_graph.object_projection_graphs:
        projection.object_config_graph_id = graph_id
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        dependency_signature=_external_graph_signature(external_graphs=()),
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    cache_path = object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    )
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    runtime_payload = payload["runtime_object_config_graph"]
    runtime_payload["object_projection_graph_declarations"] = [
        {
            "name": "Demo",
            "object_projection_graph_bindings": [
                {
                    "class_name": "Demo",
                    "domain_name": "default",
                    "fqn_prefix": fqn_prefix,
                    "id": str(uuid4()),
                    "schema_name": "demo",
                }
            ],
        }
    ]
    cache_path.write_text(
        json.dumps(payload, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    diagnostics: dict[str, object] = {}

    cached_graphs = _try_load_catalog_cached_package_graphs(
        cache_owner_root=workspace_root,
        catalog_entry=MetaRuntimePackageIndexEntry(
            module_id="demo",
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            manifest_path=manifest_path,
        ),
        external_graphs=(),
        phase_timings_s={},
        diagnostics=diagnostics,
    )

    assert cached_graphs is None
    assert diagnostics["cache_status"] == "miss"
    assert diagnostics["catalog_context_cache_miss_reason"] == (
        "runtime_graph_payload_invalid"
    )


def test_meta_graph_context_strict_catalog_cache_fails_closed_on_missing_payload(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    _write_minimal_aware_manifest(
        manifest_path=manifest_path,
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
    )
    entry = MetaRuntimePackageIndexEntry(
        module_id="demo",
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        manifest_path=manifest_path,
    )

    with pytest.raises(RuntimeError, match="catalog_cache_payload_missing"):
        build_meta_graph_runtime_context_for_aware_package_manifests(
            package_manifest_paths=(manifest_path,),
            workspace_root=workspace_root,
            strict_package_graph_cache=True,
            package_entries_by_manifest_path={manifest_path.resolve(): entry},
            package_graph_cache_request_signature="sha256:test:request",
        )


def test_meta_graph_context_strict_catalog_cache_uses_owner_root(
    tmp_path: Path,
) -> None:
    consumer_root = tmp_path / "home"
    owner_root = tmp_path / "kernel"
    consumer_root.mkdir()
    package_name = "demo-ontology"
    fqn_prefix = "aware_demo"
    manifest_path = (
        owner_root / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    _write_minimal_aware_manifest(
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    source_graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo",
    )
    source_graph.id = graph_id
    for node in source_graph.object_config_graph_nodes:
        node.object_config_graph_id = graph_id
    for projection in source_graph.object_projection_graphs:
        projection.object_config_graph_id = graph_id
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.hash = "sha256:test:Demo:runtime"
    runtime_graph.object_projection_graphs[0].projection_hash = (
        "sha256:test:Demo:runtime"
    )
    _write_context_graph_cache(
        workspace_root=owner_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=source_graph,
        runtime_graph=runtime_graph,
        source_manifest_hash="sha256:test:source-from-owner-root",
        dependency_signature=_external_graph_signature(external_graphs=()),
    )
    entry = MetaRuntimePackageIndexEntry(
        module_id="demo",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=(manifest_path,),
        workspace_root=consumer_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path={manifest_path.resolve(): entry},
        package_cache_owner_roots_by_manifest_path={
            manifest_path.resolve(): owner_root
        },
        package_graph_cache_request_signature="sha256:test:request",
    )

    package_timing = context.package_timings[0]
    assert package_timing.cache_status == "hit"
    assert package_timing.cache_source == "catalog_context_reuse_cache"
    assert "analyze_meta_ocg_sources" not in package_timing.phase_timings_s
    assert context.projection_hash_for_name("Demo") == ("sha256:test:Demo:runtime")


def test_meta_graph_context_source_analysis_allowed_writes_owner_root_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    consumer_root = tmp_path / "home"
    owner_root = tmp_path / "workspace_support"
    consumer_root.mkdir()
    package_name = "demo-ontology"
    fqn_prefix = "demo"
    package_root = owner_root / "modules" / "demo" / "structure" / "ontology"
    sources_root = package_root / "aware"
    sources_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    _write_minimal_aware_manifest(
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    (sources_root / "demo.aware").write_text("class Demo {}\n", encoding="utf-8")
    entry = MetaRuntimePackageIndexEntry(
        module_id="demo",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id

    def analyze_sources(**_: object) -> object:
        return SimpleNamespace(
            source_object_config_graph=graph,
            object_config_graph=graph.model_copy(deep=True),
        )

    monkeypatch.setattr(
        "aware_meta.semantic_analysis.analyze_meta_ocg_sources",
        analyze_sources,
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=(manifest_path,),
        workspace_root=consumer_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path={manifest_path.resolve(): entry},
        package_cache_owner_roots_by_manifest_path={
            manifest_path.resolve(): owner_root
        },
        source_analysis_allowed_manifest_paths=(manifest_path,),
        package_graph_cache_request_signature="sha256:test:request",
    )

    package_timing = context.package_timings[0]
    assert package_timing.cache_status == "analysis_fallback"
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=owner_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    assert object_config_graph_package_context_reuse_cache_path(
        aware_root=owner_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    ).is_file()
    assert not (
        consumer_root / ".aware" / "meta" / "object_config_graph_package_reuse"
    ).exists()


def test_meta_graph_context_strict_catalog_cache_fails_closed_on_catalog_drift(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    _write_minimal_aware_manifest(
        manifest_path=manifest_path,
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        dependency_package_names=("code-ontology",),
    )
    entry = MetaRuntimePackageIndexEntry(
        module_id="demo",
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        manifest_path=manifest_path,
        dependency_package_names=(),
    )

    with pytest.raises(RuntimeError, match="catalog dependency drift"):
        build_meta_graph_runtime_context_for_aware_package_manifests(
            package_manifest_paths=(manifest_path,),
            workspace_root=workspace_root,
            strict_package_graph_cache=True,
            package_entries_by_manifest_path={manifest_path.resolve(): entry},
            package_graph_cache_request_signature="sha256:test:request",
        )


def test_meta_graph_context_package_cache_request_signature_includes_projections(
    tmp_path: Path,
) -> None:
    manifest_path = (
        tmp_path / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    entry = MetaRuntimePackageIndexEntry(
        module_id="demo",
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        manifest_path=manifest_path,
    )

    first = _package_graph_cache_request_signature(
        repo_root=tmp_path,
        catalog_entries=(entry,),
        manifest_paths=(manifest_path,),
        runtime_package_names=("meta-ontology",),
        required_projection_names=("Workspace",),
        target_manifest_paths=(manifest_path,),
        include_dependency_closure=False,
    )
    second = _package_graph_cache_request_signature(
        repo_root=tmp_path,
        catalog_entries=(entry,),
        manifest_paths=(manifest_path,),
        runtime_package_names=("meta-ontology",),
        required_projection_names=("OntologyPackage",),
        target_manifest_paths=(manifest_path,),
        include_dependency_closure=False,
    )

    assert first != second


def test_meta_graph_context_package_graph_session_cache_misses_on_source_drift(
    tmp_path: Path,
) -> None:
    _clear_meta_package_graph_session_cache()
    workspace_root = tmp_path
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    sources_root = package_root / "aware"
    sources_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text("", encoding="utf-8")
    source_text = "class Demo {}\nprojection Demo {\n    root demo.Demo\n}\n"
    (sources_root / "demo.aware").write_text(source_text, encoding="utf-8")

    package_name = "demo-ontology"
    fqn_prefix = "aware_demo"
    graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=graph,
        source_manifest_hash=_source_text_manifest_hash(
            source_text_by_relative_path={"demo.aware": source_text}
        ),
        dependency_signature=_external_graph_signature(external_graphs=()),
    )
    spec = SimpleNamespace(
        package=SimpleNamespace(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        build=SimpleNamespace(
            sources_dir="aware",
            include_paths=("**/*.aware",),
            exclude_paths=(),
        ),
    )

    assert _try_load_cached_package_graphs(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        spec=spec,
        external_graphs=(),
        diagnostics={},
    )
    (sources_root / "demo.aware").write_text(
        "class Demo { name String }\nprojection Demo {\n    root demo.Demo\n}\n",
        encoding="utf-8",
    )
    cache_path = object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=_stable_object_config_graph_package_branch_id(
            workspace_root=workspace_root,
            aware_toml_path=manifest_path,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        object_config_graph_package_id=stable_object_config_graph_package_id(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
    )
    cache_path.unlink()
    diagnostics: dict[str, object] = {}

    assert (
        _try_load_cached_package_graphs(
            workspace_root=workspace_root,
            manifest_path=manifest_path,
            spec=spec,
            external_graphs=(),
            diagnostics=diagnostics,
        )
        is None
    )
    assert diagnostics["cache_status"] == "miss"
    assert diagnostics["cache_miss_reason"] == "context_cache_payload_missing"


def test_meta_graph_context_from_package_manifests_exposes_source_graphs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    sources_root = package_root / "aware"
    sources_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text("", encoding="utf-8")
    source_text = "class Demo {}\nprojection Demo {\n    root demo.Demo\n}\n"
    (sources_root / "demo.aware").write_text(source_text, encoding="utf-8")

    package_name = "demo-ontology"
    fqn_prefix = "aware_demo"
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    source_graph = _runtime_graph(
        name="Source Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo:source",
    )
    source_graph.id = graph_id
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.name = "Runtime Demo"
    runtime_graph.hash = "sha256:test:Demo:runtime"
    runtime_graph.object_projection_graphs[0].projection_hash = (
        "sha256:test:Demo:runtime"
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    cache_path = object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    )
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps(
            {
                "v": OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
                "cache_kind": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS
                ),
                "source_manifest_hash": _source_text_manifest_hash(
                    source_text_by_relative_path={"demo.aware": source_text}
                ),
                "dependency_signature": _external_graph_signature(external_graphs=()),
                "runtime_graph_derivation_signature": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
                ),
                "object_config_graph_id": str(graph_id),
                "object_config_graph_package_id": str(package_id),
                "source_object_config_graph_hash": source_graph.hash,
                "runtime_object_config_graph_hash": runtime_graph.hash,
                "source_object_config_graph": source_graph.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
                "runtime_object_config_graph": runtime_graph.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    spec = SimpleNamespace(
        package=SimpleNamespace(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            function_impl_ownership=None,
        ),
        build=SimpleNamespace(
            sources_dir="aware",
            include_paths=("**/*.aware",),
            exclude_paths=(),
        ),
        dependencies=(),
    )

    monkeypatch.setattr(
        "aware_meta.manifest.loader.load_aware_toml_spec",
        lambda *, toml_path: spec,
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=(manifest_path,),
        workspace_root=workspace_root,
    )

    assert len(context.source_graphs) == 1
    assert len(context.runtime_graphs) == 1
    assert context.source_graphs[0].name == "Source Demo"
    assert context.runtime_graphs[0].name == "Runtime Demo"
    assert context.source_graph_by_package_name[package_name].name == "Source Demo"
    assert context.runtime_graph_by_package_name[package_name].name == "Runtime Demo"
    assert context.projection_hash_for_name("Demo") == "sha256:test:Demo:runtime"


def test_meta_graph_context_rejects_stale_runtime_graph_derivation_cache(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    sources_root = package_root / "aware"
    sources_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text("", encoding="utf-8")
    source_text = "class Demo {}\nprojection Demo {\n    root demo.Demo\n}\n"
    (sources_root / "demo.aware").write_text(source_text, encoding="utf-8")

    package_name = "demo-ontology"
    fqn_prefix = "aware_demo"
    graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo:stale-runtime-projection",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=graph,
        source_manifest_hash=_source_text_manifest_hash(
            source_text_by_relative_path={"demo.aware": source_text}
        ),
        dependency_signature=_external_graph_signature(external_graphs=()),
        runtime_graph_derivation_signature="stale-runtime-derivation",
    )
    spec = SimpleNamespace(
        package=SimpleNamespace(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        build=SimpleNamespace(
            sources_dir="aware",
            include_paths=("**/*.aware",),
            exclude_paths=(),
        ),
    )

    diagnostics: dict[str, object] = {}

    assert (
        _try_load_cached_package_graphs(
            workspace_root=workspace_root,
            manifest_path=manifest_path,
            spec=spec,
            external_graphs=(),
            diagnostics=diagnostics,
        )
        is None
    )
    assert diagnostics["cache_miss_reason"] == (
        "runtime_graph_derivation_signature_mismatch"
    )


def test_meta_runtime_package_projection_index_uses_cached_graph_truth(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root
        / "modules"
        / "workspace"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "workspace-ontology"
    fqn_prefix = "aware_workspace"
    graph = _runtime_graph(
        name="Workspace",
        fqn_prefix=fqn_prefix,
        projection_name="Workspace",
        projection_hash="sha256:test:Workspace",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=graph,
    )

    package_index = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(
            MetaRuntimePackageIndexEntry(
                module_id="workspace",
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                manifest_path=manifest_path,
                dependency_package_names=("api-ontology",),
            ),
        ),
        required_projection_names=("Workspace",),
    )

    assert package_index.package_names_for_projection_names(("Workspace",)) == (
        package_name,
    )
    assert package_index.missing_projection_names(("Workspace",)) == ()
    assert (
        package_index.projections_by_name["Workspace"].projection_hash
        == "sha256:test:Workspace"
    )
    assert package_index.packages_by_name[package_name].projection_names == (
        "Workspace",
    )
    assert meta_runtime_package_projection_index_path(
        aware_root=workspace_root,
    ).is_file()
    assert not (manifest_path.parent / "aware").exists()


def test_meta_runtime_package_projection_index_rejects_stale_context_graph_cache(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root
        / "modules"
        / "workspace"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "workspace-ontology"
    fqn_prefix = "aware_workspace"
    graph = _runtime_graph(
        name="Workspace",
        fqn_prefix=fqn_prefix,
        projection_name="Workspace",
        projection_hash="sha256:test:stale-workspace",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=graph,
        runtime_graph_derivation_signature="stale-runtime-derivation",
    )

    package_index = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(
            MetaRuntimePackageIndexEntry(
                module_id="workspace",
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                manifest_path=manifest_path,
                dependency_package_names=(),
            ),
        ),
        required_projection_names=("Workspace",),
    )

    assert package_index.package_names_for_projection_names(("Workspace",)) == ()
    assert package_index.missing_projection_names(("Workspace",)) == ("Workspace",)


def test_meta_runtime_package_projection_index_records_full_materialization_receipt(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root
        / "modules"
        / "workspace"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "workspace-ontology"
    fqn_prefix = "aware_workspace"
    graph = _runtime_graph(
        name="Workspace",
        fqn_prefix=fqn_prefix,
        projection_name="Workspace",
        projection_hash="sha256:test:Workspace",
    )
    class_config = graph.object_config_graph_nodes[0].class_config
    assert class_config is not None
    class_config.class_config_function_configs.append(
        ClassConfigFunctionConfig(
            class_config_id=class_config.id,
            function_config=FunctionConfig(
                owner_key=class_config.class_fqn,
                name="rename",
                description="Rename the workspace.",
                kind=FunctionKind.instance,
                function_impl=FunctionImpl(
                    key="default",
                    kind=FunctionImplKind.instruction_body,
                ),
            ),
            position=0,
        )
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="workspace",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    source_commit_id = uuid4()
    semantic_root_commit_id = uuid4()
    semantic_package_commit_id = uuid4()
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )

    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=package_name,
        package_entries=(package_entry,),
        object_config_graph_payload=graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "source": {
                "code_package_object_instance_graph_commit_id": str(source_commit_id),
                "owned_file_paths": (
                    "workspaces/aware_workspace/modules/workspace/structure/ontology/aware/workspace.aware",
                ),
            },
            "semantic": {
                "object_config_graph_id": str(graph.id),
                "object_config_graph_hash": graph.hash,
                "object_config_graph_package_id": str(package_id),
                "object_config_graph_object_instance_graph_commit_id": str(
                    semantic_root_commit_id
                ),
                "object_config_graph_package_object_instance_graph_commit_id": str(
                    semantic_package_commit_id
                ),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": "Workspace",
                        "projection_hash": "sha256:test:Workspace",
                        "object_projection_graph_id": str(
                            graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
        source_manifest_hash="sha256:test:source-manifest",
        dependency_signature="sha256:test:dependency-signature",
    )

    package_index = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(package_entry,),
        required_projection_names=("Workspace",),
    )

    assert package_index.package_names_for_projection_names(("Workspace",)) == (
        package_name,
    )
    assert (
        package_index.projections_by_name["Workspace"].evidence_source
        == "materialization_index_receipt"
    )
    assert (
        package_index.projections_by_name[
            "Workspace"
        ].semantic_root_object_instance_graph_commit_id
        == semantic_root_commit_id
    )
    semantic_index = package_index.semantic_objects_by_key
    assert semantic_index["ocg_package:workspace-ontology"].object_kind == (
        "object_config_graph_package"
    )
    assert semantic_index["ocg:aware_workspace"].source_refs == ("workspace.aware",)
    assert (
        semantic_index["ocg:aware_workspace/node:aware_workspace.Workspace"].object_kind
        == "class"
    )
    function_key = "ocg:aware_workspace/node:aware_workspace.Workspace.rename"
    function_impl_key = f"{function_key}/function_impl:default"
    assert semantic_index[function_key].object_kind == "function"
    assert semantic_index[function_impl_key].object_kind == "function_impl"
    assert semantic_index[function_impl_key].runtime_delta_fingerprint is not None
    assert semantic_index[function_impl_key].payload["function_impl_signature"] == {
        "function_name": "rename",
        "function_owner_key": "aware_workspace.Workspace",
        "instruction_count": 0,
        "instruction_summaries": [],
        "instructions": [],
        "key": "default",
        "kind": "instruction_body",
    }
    assert (
        semantic_index[
            "ocg:aware_workspace"
        ].semantic_package_object_instance_graph_commit_id
        == semantic_package_commit_id
    )
    assert semantic_index["ocg:aware_workspace"].runtime_delta_fingerprint is not None
    assert not (manifest_path.parent / "aware").exists()


def test_meta_runtime_package_projection_index_full_materialization_replaces_package_projection_hash(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root
        / "modules"
        / "experience"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "experience-ontology"
    fqn_prefix = "aware_experience"
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="experience",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    stale_graph = _runtime_graph(
        name="Experience",
        fqn_prefix=fqn_prefix,
        projection_name="Actuator",
        projection_hash="sha256:test:stale-actuator",
    )
    current_graph = _runtime_graph(
        name="Experience",
        fqn_prefix=fqn_prefix,
        projection_name="Actuator",
        projection_hash="sha256:test:current-actuator",
    )
    for graph in (stale_graph, current_graph):
        graph.id = stable_object_config_graph_id(
            fqn_prefix=fqn_prefix,
            language=CodeLanguage.aware.value,
        )
        for node in graph.object_config_graph_nodes:
            node.object_config_graph_id = graph.id
        for projection in graph.object_projection_graphs:
            projection.object_config_graph_id = graph.id

    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=package_name,
        package_entries=(package_entry,),
        object_config_graph_payload=stale_graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(stale_graph.id),
                "object_config_graph_hash": stale_graph.hash,
                "object_config_graph_package_id": str(package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": "Actuator",
                        "projection_hash": "sha256:test:stale-actuator",
                        "object_projection_graph_id": str(
                            stale_graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
    )
    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=package_name,
        package_entries=(package_entry,),
        object_config_graph_payload=current_graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(current_graph.id),
                "object_config_graph_hash": current_graph.hash,
                "object_config_graph_package_id": str(package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": "Actuator",
                        "projection_hash": "sha256:test:current-actuator",
                        "object_projection_graph_id": str(
                            current_graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
    )

    package_index = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(package_entry,),
        required_projection_names=("Actuator",),
    )

    projection_entry = package_index.projections_by_name["Actuator"]
    assert projection_entry.package_name == package_name
    assert projection_entry.projection_hash == "sha256:test:current-actuator"
    assert projection_entry.evidence_source == "materialization_index_receipt"


def test_meta_runtime_package_projection_index_prefers_receipt_projection_identity(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root / "modules" / "code" / "structure" / "ontology" / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "code-ontology"
    fqn_prefix = "aware_code"
    graph = _runtime_graph(
        name="CodePackage",
        fqn_prefix=fqn_prefix,
        projection_name="CodePackage",
        projection_hash="sha256:test:graph-derived",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="workspace:code-ontology",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )

    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=package_name,
        package_entries=(package_entry,),
        object_config_graph_payload=graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(graph.id),
                "object_config_graph_hash": graph.hash,
                "object_config_graph_package_id": str(package_id),
                "object_config_graph_object_instance_graph_commit_id": str(uuid4()),
                "object_config_graph_package_object_instance_graph_commit_id": str(
                    uuid4()
                ),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": "CodePackage",
                        "projection_hash": "sha256:test:receipt-authoritative",
                        "object_projection_graph_id": str(
                            graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
        source_manifest_hash="sha256:test:source-manifest",
        dependency_signature="sha256:test:dependency-signature",
    )

    package_index = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(package_entry,),
        required_projection_names=("CodePackage",),
    )

    projection_entry = package_index.projections_by_name["CodePackage"]
    assert projection_entry.package_name == "code-ontology"
    assert projection_entry.evidence_source == "materialization_index_receipt"
    assert projection_entry.projection_hash == "sha256:test:receipt-authoritative"


def test_meta_runtime_package_projection_index_keeps_current_receipt_over_stale_index(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root / "modules" / "code" / "structure" / "ontology" / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "code-ontology"
    fqn_prefix = "aware_code"
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="code",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    graph = _runtime_graph(
        name="CodePackage",
        fqn_prefix=fqn_prefix,
        projection_name="CodePackage",
        projection_hash="sha256:test:current-graph",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    stale_receipt: dict[str, object] = {
        "semantic": {
            "object_config_graph_id": str(graph.id),
            "object_config_graph_hash": graph.hash,
            "object_config_graph_package_id": str(package_id),
        },
        "identity_plane": {
            "projection_identities": [
                {
                    "projection_name": "CodePackage",
                    "projection_hash": "sha256:test:stale-receipt",
                    "object_projection_graph_id": str(
                        graph.object_projection_graphs[0].id
                    ),
                }
            ],
        },
    }
    current_receipt: dict[str, object] = {
        "semantic": {
            "object_config_graph_id": str(graph.id),
            "object_config_graph_hash": graph.hash,
            "object_config_graph_package_id": str(package_id),
        },
        "identity_plane": {
            "projection_identities": [
                {
                    "projection_name": "CodePackage",
                    "projection_hash": "sha256:test:current-receipt",
                    "object_projection_graph_id": str(
                        graph.object_projection_graphs[0].id
                    ),
                }
            ],
        },
    }
    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=package_name,
        package_entries=(package_entry,),
        object_config_graph_payload=graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt=stale_receipt,
    )
    _write_materialized_package_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=graph,
        materialization_index_receipt=current_receipt,
    )

    rebuilt = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(
            replace(
                package_entry,
                dependency_package_names=("meta-ontology",),
            ),
        ),
        required_projection_names=("CodePackage",),
    )

    projection_entry = rebuilt.projections_by_name["CodePackage"]
    assert projection_entry.evidence_source == "materialization_index_receipt"
    assert projection_entry.projection_hash == "sha256:test:current-receipt"


def test_meta_runtime_package_projection_index_imports_external_owner_truth(
    tmp_path: Path,
) -> None:
    kernel_root = tmp_path / "kernel"
    workspace_root = tmp_path / "workspaces" / "aware_workspace"
    kernel_root.mkdir(parents=True)
    workspace_root.mkdir(parents=True)
    manifest_path = (
        workspace_root
        / "modules"
        / "workspace"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "workspace-ontology"
    fqn_prefix = "aware_workspace"
    graph = _runtime_graph(
        name="Workspace",
        fqn_prefix=fqn_prefix,
        projection_name="Workspace",
        projection_hash="sha256:test:external-owner-Workspace",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="workspace",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=package_name,
        package_entries=(package_entry,),
        object_config_graph_payload=graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(graph.id),
                "object_config_graph_hash": graph.hash,
                "object_config_graph_package_id": str(package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": "Workspace",
                        "projection_hash": "sha256:test:external-owner-Workspace",
                        "object_projection_graph_id": str(
                            graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
        source_manifest_hash="sha256:test:external-owner-source",
        dependency_signature="sha256:test:external-owner-dependencies",
    )

    package_index = build_meta_runtime_package_projection_index(
        repo_root=kernel_root,
        aware_root=kernel_root,
        package_entries=(package_entry,),
        required_projection_names=("Workspace",),
    )

    assert package_index.package_names_for_projection_names(("Workspace",)) == (
        package_name,
    )
    assert (
        package_index.projections_by_name["Workspace"].evidence_source
        == "materialization_index_receipt"
    )
    assert (
        package_index.projections_by_name["Workspace"].projection_hash
        == "sha256:test:external-owner-Workspace"
    )


def test_meta_runtime_package_projection_index_keeps_current_cache_over_stale_external_owner(
    tmp_path: Path,
) -> None:
    kernel_root = tmp_path / "kernel"
    workspace_root = tmp_path / "workspaces" / "aware_workspace"
    kernel_root.mkdir(parents=True)
    workspace_root.mkdir(parents=True)
    manifest_path = (
        workspace_root
        / "modules"
        / "workspace"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "workspace-ontology"
    fqn_prefix = "aware_workspace"
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="workspace",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    stale_graph = _runtime_graph(
        name="Workspace",
        fqn_prefix=fqn_prefix,
        projection_name="Workspace",
        projection_hash="sha256:test:stale-external-owner",
    )
    current_graph = _runtime_graph(
        name="Workspace",
        fqn_prefix=fqn_prefix,
        projection_name="Workspace",
        projection_hash="sha256:test:current-cache",
    )
    for graph in (stale_graph, current_graph):
        graph.id = stable_object_config_graph_id(
            fqn_prefix=fqn_prefix,
            language=CodeLanguage.aware.value,
        )
        for node in graph.object_config_graph_nodes:
            node.object_config_graph_id = graph.id
        for projection in graph.object_projection_graphs:
            projection.object_config_graph_id = graph.id

    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=package_name,
        package_entries=(package_entry,),
        object_config_graph_payload=stale_graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(stale_graph.id),
                "object_config_graph_hash": stale_graph.hash,
                "object_config_graph_package_id": str(package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": "Workspace",
                        "projection_hash": "sha256:test:stale-external-owner",
                        "object_projection_graph_id": str(
                            stale_graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
    )
    _write_materialized_package_cache(
        workspace_root=kernel_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=current_graph,
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(current_graph.id),
                "object_config_graph_hash": current_graph.hash,
                "object_config_graph_package_id": str(package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": "Workspace",
                        "projection_hash": "sha256:test:current-cache",
                        "object_projection_graph_id": str(
                            current_graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
    )

    package_index = build_meta_runtime_package_projection_index(
        repo_root=kernel_root,
        aware_root=kernel_root,
        package_entries=(package_entry,),
        required_projection_names=("Workspace",),
    )

    assert (
        package_index.projections_by_name["Workspace"].projection_hash
        == "sha256:test:current-cache"
    )


def test_meta_runtime_package_projection_index_imports_required_missing_projection_from_owner(
    tmp_path: Path,
) -> None:
    kernel_root = tmp_path / "kernel"
    workspace_root = tmp_path / "workspaces" / "aware_kernel"
    kernel_root.mkdir(parents=True)
    workspace_root.mkdir(parents=True)
    manifest_path = (
        workspace_root / "modules" / "code" / "ontology" / "structure" / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "code-ontology"
    fqn_prefix = "aware_code"
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="aware_kernel:code",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    stale_root_graph = _runtime_graph(
        name="Code",
        fqn_prefix=fqn_prefix,
        projection_name="CodePackage",
        projection_hash="sha256:test:stale-root-code-package",
    )
    fresh_owner_graph = _runtime_graph(
        name="Code",
        fqn_prefix=fqn_prefix,
        projection_name="CodePackage",
        projection_hash="sha256:test:fresh-owner-code-package",
    )
    fresh_owner_graph.object_projection_graphs.append(
        ObjectProjectionGraph(
            object_config_graph_id=fresh_owner_graph.id,
            language=CodeLanguage.aware,
            name="CodePackageConfig",
            projection_hash="sha256:test:fresh-owner-code-package-config",
        )
    )
    for graph in (stale_root_graph, fresh_owner_graph):
        graph.id = stable_object_config_graph_id(
            fqn_prefix=graph.fqn_prefix,
            language=CodeLanguage.aware.value,
        )
        for node in graph.object_config_graph_nodes:
            node.object_config_graph_id = graph.id
        for projection in graph.object_projection_graphs:
            projection.object_config_graph_id = graph.id

    _write_materialized_package_cache(
        workspace_root=kernel_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=stale_root_graph,
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(stale_root_graph.id),
                "object_config_graph_hash": stale_root_graph.hash,
                "object_config_graph_package_id": str(package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": "CodePackage",
                        "projection_hash": "sha256:test:stale-root-code-package",
                        "object_projection_graph_id": str(
                            stale_root_graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
        source_manifest_hash="sha256:test:stale-root-source",
        dependency_signature="sha256:test:stale-root-dependencies",
    )
    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=package_name,
        package_entries=(package_entry,),
        object_config_graph_payload=fresh_owner_graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(fresh_owner_graph.id),
                "object_config_graph_hash": fresh_owner_graph.hash,
                "object_config_graph_package_id": str(package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": projection.name,
                        "projection_hash": projection.projection_hash,
                        "object_projection_graph_id": str(projection.id),
                    }
                    for projection in fresh_owner_graph.object_projection_graphs
                ],
            },
        },
        source_manifest_hash="sha256:test:fresh-owner-source",
        dependency_signature="sha256:test:fresh-owner-dependencies",
    )

    package_index = build_meta_runtime_package_projection_index(
        repo_root=kernel_root,
        aware_root=kernel_root,
        package_entries=(package_entry,),
        required_projection_names=("CodePackageConfig",),
    )

    assert package_index.projections_by_name["CodePackage"].projection_hash == (
        "sha256:test:stale-root-code-package"
    )
    assert package_index.projections_by_name["CodePackageConfig"].projection_hash == (
        "sha256:test:fresh-owner-code-package-config"
    )
    assert package_index.packages_by_name[package_name].projection_names == (
        "CodePackage",
        "CodePackageConfig",
    )


def test_meta_runtime_package_projection_index_skips_stale_external_owner_extra_projection(
    tmp_path: Path,
) -> None:
    kernel_root = tmp_path / "kernel"
    workspace_root = tmp_path / "workspaces" / "aware_workspace"
    kernel_root.mkdir(parents=True)
    workspace_root.mkdir(parents=True)
    experience_manifest_path = (
        workspace_root
        / "modules"
        / "experience"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    identity_manifest_path = (
        workspace_root
        / "modules"
        / "identity"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    experience_manifest_path.parent.mkdir(parents=True)
    identity_manifest_path.parent.mkdir(parents=True)
    experience_manifest_path.write_text("", encoding="utf-8")
    identity_manifest_path.write_text("", encoding="utf-8")
    experience_entry = MetaRuntimePackageIndexEntry(
        module_id="experience",
        package_name="experience-ontology",
        fqn_prefix="aware_experience",
        manifest_path=experience_manifest_path,
    )
    identity_entry = MetaRuntimePackageIndexEntry(
        module_id="identity",
        package_name="identity-ontology",
        fqn_prefix="aware_identity",
        manifest_path=identity_manifest_path,
    )
    stale_experience_graph = _runtime_graph(
        name="Experience",
        fqn_prefix="aware_experience",
        projection_name="ActorConfig",
        projection_hash="sha256:test:stale-experience-actor-config",
    )
    current_experience_graph = _runtime_graph(
        name="Experience",
        fqn_prefix="aware_experience",
        projection_name="ProjectionExperience",
        projection_hash="sha256:test:current-experience-projection",
    )
    current_identity_graph = _runtime_graph(
        name="Identity",
        fqn_prefix="aware_identity",
        projection_name="ActorConfig",
        projection_hash="sha256:test:current-identity-actor-config",
    )
    for graph in (
        stale_experience_graph,
        current_experience_graph,
        current_identity_graph,
    ):
        graph.id = stable_object_config_graph_id(
            fqn_prefix=graph.fqn_prefix,
            language=CodeLanguage.aware.value,
        )
        for node in graph.object_config_graph_nodes:
            node.object_config_graph_id = graph.id
        for projection in graph.object_projection_graphs:
            projection.object_config_graph_id = graph.id

    stale_experience_package_id = stable_object_config_graph_package_id(
        package_name=experience_entry.package_name,
        fqn_prefix=experience_entry.fqn_prefix,
    )
    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=experience_entry.package_name,
        package_entries=(experience_entry,),
        object_config_graph_payload=stale_experience_graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(stale_experience_graph.id),
                "object_config_graph_hash": stale_experience_graph.hash,
                "object_config_graph_package_id": str(stale_experience_package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": "ActorConfig",
                        "projection_hash": (
                            "sha256:test:stale-experience-actor-config"
                        ),
                        "object_projection_graph_id": str(
                            stale_experience_graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
        source_manifest_hash="sha256:test:stale-experience-source",
        dependency_signature="sha256:test:stale-experience-dependencies",
    )
    for entry, graph, projection_name, projection_hash in (
        (
            experience_entry,
            current_experience_graph,
            "ProjectionExperience",
            "sha256:test:current-experience-projection",
        ),
        (
            identity_entry,
            current_identity_graph,
            "ActorConfig",
            "sha256:test:current-identity-actor-config",
        ),
    ):
        package_id = stable_object_config_graph_package_id(
            package_name=entry.package_name,
            fqn_prefix=entry.fqn_prefix,
        )
        _write_materialized_package_cache(
            workspace_root=kernel_root,
            manifest_path=entry.manifest_path,
            package_name=entry.package_name,
            fqn_prefix=entry.fqn_prefix,
            graph=graph,
            materialization_index_receipt={
                "semantic": {
                    "object_config_graph_id": str(graph.id),
                    "object_config_graph_hash": graph.hash,
                    "object_config_graph_package_id": str(package_id),
                },
                "identity_plane": {
                    "projection_identities": [
                        {
                            "projection_name": projection_name,
                            "projection_hash": projection_hash,
                            "object_projection_graph_id": str(
                                graph.object_projection_graphs[0].id
                            ),
                        }
                    ],
                },
            },
            source_manifest_hash=f"sha256:test:current:{entry.package_name}:source",
            dependency_signature=f"sha256:test:current:{entry.package_name}:deps",
        )

    package_index = build_meta_runtime_package_projection_index(
        repo_root=kernel_root,
        aware_root=kernel_root,
        package_entries=(experience_entry, identity_entry),
        required_projection_names=("ActorConfig", "ProjectionExperience"),
    )

    assert package_index.projections_by_name["ActorConfig"].package_name == (
        "identity-ontology"
    )
    assert package_index.projections_by_name["ActorConfig"].projection_hash == (
        "sha256:test:current-identity-actor-config"
    )
    assert (
        "ActorConfig"
        not in package_index.packages_by_name["experience-ontology"].projection_names
    )
    assert (
        package_index.projections_by_name["ProjectionExperience"].package_name
        == "experience-ontology"
    )


def test_meta_runtime_package_projection_index_rebuild_preserves_compatible_projection_entries(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root / "modules" / "meta" / "structure" / "ontology" / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "meta-ontology"
    fqn_prefix = "aware_meta"
    projection_name = "ObjectConfigGraphPackage"
    graph = _runtime_graph(
        name="Meta",
        fqn_prefix=fqn_prefix,
        projection_name=projection_name,
        projection_hash="sha256:test:ObjectConfigGraphPackage",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="meta",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name=package_name,
        package_entries=(package_entry,),
        object_config_graph_payload=graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(graph.id),
                "object_config_graph_hash": graph.hash,
                "object_config_graph_package_id": str(package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": projection_name,
                        "projection_hash": "sha256:test:ObjectConfigGraphPackage",
                        "object_projection_graph_id": str(
                            graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
        source_manifest_hash="sha256:test:source-manifest",
        dependency_signature="sha256:test:dependency-signature",
    )

    rebuilt = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(
            replace(
                package_entry,
                dependency_package_names=("code-ontology",),
            ),
        ),
        required_projection_names=(projection_name,),
    )

    assert rebuilt.package_names_for_projection_names((projection_name,)) == (
        package_name,
    )
    assert rebuilt.missing_projection_names((projection_name,)) == ()
    assert (
        rebuilt.projections_by_name[projection_name].evidence_source
        == "materialization_index_receipt"
    )
    assert rebuilt.packages_by_name[package_name].projection_names == (projection_name,)


def test_meta_runtime_package_projection_index_rebuild_does_not_preserve_absent_package(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    meta_manifest_path = (
        workspace_root / "modules" / "meta" / "structure" / "ontology" / "aware.toml"
    )
    home_manifest_path = (
        workspace_root / "modules" / "home" / "structure" / "ontology" / "aware.toml"
    )
    meta_manifest_path.parent.mkdir(parents=True)
    home_manifest_path.parent.mkdir(parents=True)
    meta_manifest_path.write_text("", encoding="utf-8")
    home_manifest_path.write_text("", encoding="utf-8")
    projection_name = "ObjectConfigGraphPackage"
    graph = _runtime_graph(
        name="Meta",
        fqn_prefix="aware_meta",
        projection_name=projection_name,
        projection_hash="sha256:test:ObjectConfigGraphPackage",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix="aware_meta",
        language=CodeLanguage.aware.value,
    )
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph.id
    for projection in graph.object_projection_graphs:
        projection.object_config_graph_id = graph.id
    meta_package_entry = MetaRuntimePackageIndexEntry(
        module_id="meta",
        package_name="meta-ontology",
        fqn_prefix="aware_meta",
        manifest_path=meta_manifest_path,
    )
    package_id = stable_object_config_graph_package_id(
        package_name="meta-ontology",
        fqn_prefix="aware_meta",
    )
    record_full_package_materialization_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        materialized_package_name="meta-ontology",
        package_entries=(meta_package_entry,),
        object_config_graph_payload=graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        materialization_index_receipt={
            "semantic": {
                "object_config_graph_id": str(graph.id),
                "object_config_graph_hash": graph.hash,
                "object_config_graph_package_id": str(package_id),
            },
            "identity_plane": {
                "projection_identities": [
                    {
                        "projection_name": projection_name,
                        "projection_hash": "sha256:test:ObjectConfigGraphPackage",
                        "object_projection_graph_id": str(
                            graph.object_projection_graphs[0].id
                        ),
                    }
                ],
            },
        },
    )

    rebuilt = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(
            MetaRuntimePackageIndexEntry(
                module_id="home",
                package_name="home-ontology",
                fqn_prefix="aware_home",
                manifest_path=home_manifest_path,
            ),
        ),
        required_projection_names=(projection_name,),
    )

    assert rebuilt.package_names_for_projection_names((projection_name,)) == ()
    assert rebuilt.missing_projection_names((projection_name,)) == (projection_name,)
    assert "meta-ontology" not in rebuilt.packages_by_name


def test_meta_required_projection_resolution_does_not_parse_source_declarations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kernel_root = tmp_path / "kernel"
    workspace_root = tmp_path / "workspaces" / "aware_workspace"
    manifest_path = (
        workspace_root
        / "modules"
        / "workspace"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    source_root = manifest_path.parent / "aware"
    source_root.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    (source_root / "workspace.aware").write_text(
        "class Workspace {}\nprojection Workspace {\n    root aware_workspace.Workspace\n}\n",
        encoding="utf-8",
    )
    entries_by_package_name = {
        "workspace-ontology": MetaRuntimePackageIndexEntry(
            module_id="workspace",
            package_name="workspace-ontology",
            fqn_prefix="aware_workspace",
            manifest_path=manifest_path,
        ),
    }

    def catalog(*, repo_root: Path) -> object:
        del repo_root
        return entries_by_package_name, {"workspace": "workspace-ontology"}

    monkeypatch.setattr(
        "aware_meta.runtime.graph_context._ontology_package_manifest_catalog",
        catalog,
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_environment",
        semantic_owner="aware_environment.provider",
        workspace_root=kernel_root,
        repo_root=kernel_root,
        context={"required_projection_names": ("Workspace",)},
    )

    with pytest.raises(
        ValueError,
        match="Required Meta runtime projections were not found",
    ):
        resolve_workspace_required_projection_package_manifest_paths(request)


def test_meta_runtime_package_index_patch_upserts_and_deletes_semantic_entries(
    tmp_path: Path,
) -> None:
    manifest_path = (
        tmp_path
        / "workspaces/aware_workspace/modules/workspace/structure/ontology/aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="workspace",
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
        manifest_path=manifest_path,
    )
    index = build_meta_runtime_package_projection_index(
        repo_root=tmp_path,
        aware_root=tmp_path,
        package_entries=(package_entry,),
    )
    semantic_entry = MetaRuntimeSemanticObjectIndexEntry(
        semantic_key="ocg:aware_workspace/node:aware_workspace.Workspace",
        object_kind="class",
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
        manifest_path=manifest_path,
        graph_semantic_key="ocg:aware_workspace",
        source_refs=("workspace.aware",),
    )
    projection_entry = MetaRuntimeProjectionIndexEntry(
        projection_name="Workspace",
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
        manifest_path=manifest_path,
        projection_hash="sha256:test:Workspace",
        evidence_source="runtime_delta_patch",
    )

    patched = apply_meta_runtime_package_index_patch(
        index=index,
        patch=MetaRuntimePackageIndexPatch(
            projection_upserts=(projection_entry,),
            semantic_object_upserts=(semantic_entry,),
            runtime_delta_fingerprint="sha256:test:delta",
        ),
    )
    assert patched.package_names_for_projection_names(("Workspace",)) == (
        "workspace-ontology",
    )
    assert (
        patched.semantic_objects_by_key[
            "ocg:aware_workspace/node:aware_workspace.Workspace"
        ].runtime_delta_fingerprint
        == "sha256:test:delta"
    )

    patched = apply_meta_runtime_package_index_patch(
        index=patched,
        patch=MetaRuntimePackageIndexPatch(
            projection_deletes=("Workspace",),
            semantic_object_deletes=(
                "ocg:aware_workspace/node:aware_workspace.Workspace",
            ),
        ),
    )

    assert (
        patched.semantic_objects_by_key.get(
            "ocg:aware_workspace/node:aware_workspace.Workspace"
        )
        is None
    )
    assert patched.missing_projection_names(("Workspace",)) == ("Workspace",)


def test_meta_runtime_package_index_patch_records_durable_index(
    tmp_path: Path,
) -> None:
    manifest_path = (
        tmp_path
        / "workspaces/aware_workspace/modules/workspace/structure/ontology/aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="workspace",
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
        manifest_path=manifest_path,
    )
    _ = build_meta_runtime_package_projection_index(
        repo_root=tmp_path,
        aware_root=tmp_path,
        package_entries=(package_entry,),
    )
    semantic_entry = MetaRuntimeSemanticObjectIndexEntry(
        semantic_key="ocg:aware_workspace/node:aware_workspace.Workspace",
        object_kind="class",
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
        manifest_path=manifest_path,
        graph_semantic_key="ocg:aware_workspace",
        source_refs=("workspace.aware",),
    )

    patched = record_meta_runtime_package_index_patch(
        aware_root=tmp_path,
        patch=MetaRuntimePackageIndexPatch(
            semantic_object_upserts=(semantic_entry,),
            runtime_delta_fingerprint="sha256:test:durable-delta",
        ),
    )

    assert patched is not None
    assert (
        patched.semantic_objects_by_key[
            "ocg:aware_workspace/node:aware_workspace.Workspace"
        ].runtime_delta_fingerprint
        == "sha256:test:durable-delta"
    )
    persisted = json.loads(
        meta_runtime_package_projection_index_path(
            aware_root=tmp_path,
        ).read_text(encoding="utf-8")
    )
    persisted_semantic_objects = cast(
        list[dict[str, object]],
        persisted["semantic_objects"],
    )
    assert {
        item["semantic_key"]: item["runtime_delta_fingerprint"]
        for item in persisted_semantic_objects
    }["ocg:aware_workspace/node:aware_workspace.Workspace"] == (
        "sha256:test:durable-delta"
    )

    patched = record_meta_runtime_package_index_patch(
        aware_root=tmp_path,
        patch=MetaRuntimePackageIndexPatch(
            semantic_object_deletes=(
                "ocg:aware_workspace/node:aware_workspace.Workspace",
            ),
        ),
    )

    assert patched is not None
    assert (
        "ocg:aware_workspace/node:aware_workspace.Workspace"
        not in patched.semantic_objects_by_key
    )


def test_meta_runtime_package_index_rebuild_preserves_delta_overlay(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    manifest_path = (
        workspace_root
        / "modules"
        / "workspace"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_name = "workspace-ontology"
    fqn_prefix = "aware_workspace"
    graph = _runtime_graph(
        name="Workspace",
        fqn_prefix=fqn_prefix,
        projection_name="Workspace",
        projection_hash="sha256:test:Workspace",
    )
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        graph=graph,
    )
    initial_package_entry = MetaRuntimePackageIndexEntry(
        module_id="workspace",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    _ = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(initial_package_entry,),
        required_projection_names=("Workspace",),
    )
    semantic_key = "ocg:aware_workspace/node:aware_workspace.Workspace"
    delta_head_commit_id = uuid4()
    delta_oig_commit_id = uuid4()

    patched = record_meta_runtime_package_index_patch(
        aware_root=workspace_root,
        patch=MetaRuntimePackageIndexPatch(
            semantic_object_upserts=(
                MetaRuntimeSemanticObjectIndexEntry(
                    semantic_key=semantic_key,
                    object_kind="class",
                    package_name=package_name,
                    fqn_prefix=fqn_prefix,
                    manifest_path=manifest_path,
                    graph_semantic_key="ocg:aware_workspace",
                    source_refs=("workspace.aware",),
                    semantic_package_head_commit_id=delta_head_commit_id,
                    semantic_package_object_instance_graph_commit_id=(
                        delta_oig_commit_id
                    ),
                    runtime_delta_fingerprint="sha256:test:delta-entry",
                    evidence_source="provider_delta_index_patch",
                    payload={
                        "class_signature": {
                            "description": "delta overlay description",
                        },
                    },
                ),
            ),
            runtime_delta_fingerprint="sha256:test:delta-overlay",
        ),
    )
    assert patched is not None

    rebuilt = build_meta_runtime_package_projection_index(
        repo_root=workspace_root,
        aware_root=workspace_root,
        package_entries=(
            replace(
                initial_package_entry,
                dependency_package_names=("api-ontology",),
            ),
        ),
        required_projection_names=("Workspace",),
    )

    preserved = rebuilt.semantic_objects_by_key[semantic_key]
    assert preserved.evidence_source == "provider_delta_index_patch"
    assert preserved.runtime_delta_fingerprint == "sha256:test:delta-overlay"
    assert preserved.semantic_package_head_commit_id == delta_head_commit_id
    assert preserved.semantic_package_object_instance_graph_commit_id == (
        delta_oig_commit_id
    )
    assert preserved.payload["class_signature"] == {
        "description": "delta overlay description",
    }


def test_meta_runtime_package_index_patch_concurrent_writes_use_unique_temps(
    tmp_path: Path,
) -> None:
    manifest_path = (
        tmp_path
        / "workspaces/aware_workspace/modules/workspace/structure/ontology/aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("", encoding="utf-8")
    package_entry = MetaRuntimePackageIndexEntry(
        module_id="workspace",
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
        manifest_path=manifest_path,
    )
    _ = build_meta_runtime_package_projection_index(
        repo_root=tmp_path,
        aware_root=tmp_path,
        package_entries=(package_entry,),
    )

    def write_patch(index: int) -> None:
        semantic_entry = MetaRuntimeSemanticObjectIndexEntry(
            semantic_key=(
                "ocg:aware_workspace/node:"
                f"aware_workspace.Workspace.Concurrent{index}"
            ),
            object_kind="class",
            package_name="workspace-ontology",
            fqn_prefix="aware_workspace",
            manifest_path=manifest_path,
            graph_semantic_key="ocg:aware_workspace",
            source_refs=("workspace.aware",),
        )
        patched = record_meta_runtime_package_index_patch(
            aware_root=tmp_path,
            patch=MetaRuntimePackageIndexPatch(
                semantic_object_upserts=(semantic_entry,),
                runtime_delta_fingerprint=f"sha256:test:concurrent-{index}",
            ),
        )
        assert patched is not None

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(write_patch, index) for index in range(24)]
        for future in futures:
            future.result()

    index_path = meta_runtime_package_projection_index_path(aware_root=tmp_path)
    payload = json.loads(index_path.read_text(encoding="utf-8"))

    assert payload["schema"] == "aware.meta.runtime.package_projection_index.v1"
    assert not tuple(index_path.parent.glob(f"{index_path.name}.*.tmp"))


def test_meta_graph_context_passes_only_declared_dependency_closure_graphs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    manifest_paths = tuple(
        workspace_root / "modules" / name / "structure" / "ontology" / "aware.toml"
        for name in ("alpha", "beta", "delta", "gamma")
    )
    for package_key, manifest_path in zip(
        ("alpha", "beta", "delta", "gamma"),
        manifest_paths,
    ):
        sources_root = manifest_path.parent / "aware"
        sources_root.mkdir(parents=True)
        manifest_path.write_text("", encoding="utf-8")
        (sources_root / f"{package_key}.aware").write_text(
            "class Demo {}\n",
            encoding="utf-8",
        )

    specs = {
        manifest_paths[0]: SimpleNamespace(
            package=SimpleNamespace(
                package_name="alpha-ontology",
                fqn_prefix="aware_alpha",
                function_impl_ownership=None,
            ),
            build=SimpleNamespace(
                sources_dir="aware",
                include_paths=("**/*.aware",),
                exclude_paths=(),
            ),
            dependencies=(),
        ),
        manifest_paths[1]: SimpleNamespace(
            package=SimpleNamespace(
                package_name="beta-ontology",
                fqn_prefix="aware_beta",
                function_impl_ownership=None,
            ),
            build=SimpleNamespace(
                sources_dir="aware",
                include_paths=("**/*.aware",),
                exclude_paths=(),
            ),
            dependencies=(SimpleNamespace(package_name="alpha-ontology"),),
        ),
        manifest_paths[2]: SimpleNamespace(
            package=SimpleNamespace(
                package_name="delta-ontology",
                fqn_prefix="aware_delta",
                function_impl_ownership=None,
            ),
            build=SimpleNamespace(
                sources_dir="aware",
                include_paths=("**/*.aware",),
                exclude_paths=(),
            ),
            dependencies=(),
        ),
        manifest_paths[3]: SimpleNamespace(
            package=SimpleNamespace(
                package_name="gamma-ontology",
                fqn_prefix="aware_gamma",
                function_impl_ownership=None,
            ),
            build=SimpleNamespace(
                sources_dir="aware",
                include_paths=("**/*.aware",),
                exclude_paths=(),
            ),
            dependencies=(SimpleNamespace(package_name="beta-ontology"),),
        ),
    }
    external_names_by_package: dict[str, tuple[str, ...]] = {}

    def load_spec(*, toml_path: Path) -> object:
        return specs[toml_path]

    def analyze_sources(
        *,
        package_root: Path,
        source_files: tuple[object, ...],
        manifest_path: Path,
        external_graphs: tuple[ObjectConfigGraph, ...],
        external_runtime_graphs: tuple[ObjectConfigGraph, ...],
        fail_on_error: bool,
    ) -> object:
        del package_root, source_files, external_runtime_graphs, fail_on_error
        spec = specs[manifest_path]
        package_name = spec.package.package_name
        external_names_by_package[package_name] = tuple(
            graph.name for graph in external_graphs
        )
        graph = _runtime_graph(
            name=package_name,
            fqn_prefix=spec.package.fqn_prefix,
            projection_name=package_name,
            projection_hash=f"sha256:test:{package_name}",
        )
        return SimpleNamespace(
            source_object_config_graph=graph,
            object_config_graph=graph.model_copy(deep=True),
        )

    monkeypatch.setattr(
        "aware_meta.manifest.loader.load_aware_toml_spec",
        load_spec,
    )
    monkeypatch.setattr(
        "aware_meta.semantic_analysis.analyze_meta_ocg_sources",
        analyze_sources,
    )

    build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=manifest_paths,
        workspace_root=workspace_root,
    )

    assert external_names_by_package["alpha-ontology"] == ()
    assert external_names_by_package["beta-ontology"] == ("alpha-ontology",)
    assert external_names_by_package["delta-ontology"] == ()
    assert external_names_by_package["gamma-ontology"] == (
        "alpha-ontology",
        "beta-ontology",
    )


def test_meta_graph_context_rejects_stale_package_reuse_cache_version(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    sources_root = package_root / "aware"
    sources_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text("", encoding="utf-8")
    source_text = "class Demo {}\n"
    (sources_root / "demo.aware").write_text(source_text, encoding="utf-8")

    package_name = "demo-ontology"
    fqn_prefix = "aware_demo"
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo",
    )
    graph.id = graph_id
    cache_path = object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    )
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps(
            {
                "v": OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION - 1,
                "cache_kind": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS
                ),
                "source_manifest_hash": _source_text_manifest_hash(
                    source_text_by_relative_path={"demo.aware": source_text}
                ),
                "dependency_signature": _external_graph_signature(external_graphs=()),
                "object_config_graph_id": str(graph_id),
                "object_config_graph_package_id": str(package_id),
                "source_object_config_graph_hash": graph.hash,
                "runtime_object_config_graph_hash": graph.hash,
                "source_object_config_graph": graph.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
                "runtime_object_config_graph": graph.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    spec = SimpleNamespace(
        package=SimpleNamespace(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        build=SimpleNamespace(
            sources_dir="aware",
            include_paths=("**/*.aware",),
            exclude_paths=(),
        ),
    )

    assert (
        _try_load_cached_package_graphs(
            workspace_root=workspace_root,
            manifest_path=manifest_path,
            spec=spec,
            external_graphs=(),
        )
        is None
    )


def test_meta_graph_context_rejects_source_only_package_reuse_cache(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    sources_root = package_root / "aware"
    sources_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text("", encoding="utf-8")
    source_text = "class Demo {}\n"
    (sources_root / "demo.aware").write_text(source_text, encoding="utf-8")

    package_name = "demo-ontology"
    fqn_prefix = "aware_demo"
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    package_id = stable_object_config_graph_package_id(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    branch_id = _stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    graph = _runtime_graph(
        name="Demo",
        fqn_prefix=fqn_prefix,
        projection_name="Demo",
        projection_hash="sha256:test:Demo",
    )
    graph.id = graph_id
    cache_path = object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    )
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps(
            {
                "v": OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
                "cache_kind": (
                    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_SOURCE_GRAPH
                ),
                "source_manifest_hash": _source_text_manifest_hash(
                    source_text_by_relative_path={"demo.aware": source_text}
                ),
                "dependency_signature": _external_graph_signature(external_graphs=()),
                "object_config_graph_id": str(graph_id),
                "object_config_graph_package_id": str(package_id),
                "source_object_config_graph_hash": graph.hash,
                "source_object_config_graph": graph.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    spec = SimpleNamespace(
        package=SimpleNamespace(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        build=SimpleNamespace(
            sources_dir="aware",
            include_paths=("**/*.aware",),
            exclude_paths=(),
        ),
    )

    assert (
        _try_load_cached_package_graphs(
            workspace_root=workspace_root,
            manifest_path=manifest_path,
            spec=spec,
            external_graphs=(),
        )
        is None
    )


def test_meta_graph_index_snapshot_can_be_built_directly_from_ocg() -> None:
    graph = _runtime_graph()

    index = build_meta_graph_runtime_index_snapshot(ocg=graph)

    assert isinstance(index, MetaGraphRuntimeIndex)
    assert (
        find_meta_graph_projection_hash_by_name(
            index=cast(MetaGraphRuntimeIndex, index),
            projection_name="Workspace",
        )
        == "sha256:test:Workspace"
    )


def test_meta_semantic_contract_declares_graph_runtime_context() -> None:
    runtime_context_descriptors = (
        AWARE_META_SEMANTIC_CONTRACT.materialization_runtime_context_for(
            semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        )
    )
    descriptors = AWARE_META_SEMANTIC_CONTRACT.materialization_execution_context_for(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
    )

    assert len(runtime_context_descriptors) == 1
    assert runtime_context_descriptors[0].callable_module == (
        "aware_meta.runtime.graph_context"
    )
    assert runtime_context_descriptors[0].callable_name == (
        "build_meta_workspace_materialization_runtime_context"
    )
    assert len(descriptors) == 1
    descriptor_by_key = {
        descriptor.context_key: descriptor for descriptor in descriptors
    }
    graph_descriptor = descriptor_by_key[META_GRAPH_RUNTIME_CONTEXT_KEY]
    assert graph_descriptor.callable_module == "aware_meta.runtime.graph_context"
    assert (
        graph_descriptor.callable_name
        == "build_meta_graph_runtime_context_for_semantic_materialization"
    )


def test_meta_graph_context_resolves_from_semantic_materialization_request() -> None:
    graph = _runtime_graph(projection_name="Workspace")
    request = SemanticPackageMaterializationExecutionContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        context_key=META_GRAPH_RUNTIME_CONTEXT_KEY,
        workspace_root=Path("/tmp/aware-test"),
        manifest_path=Path("/tmp/aware-test/aware.toml"),
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        context={
            SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY: {"enabled": True},
            "runtime_object_config_graphs": (graph,),
        },
    )

    context = build_meta_graph_runtime_context_for_semantic_materialization(request)

    assert context is not None
    assert context.projection_hash_for_name("Workspace") == "sha256:test:Workspace"


def test_meta_graph_context_skips_semantic_materialization_request_when_execution_disabled() -> (
    None
):
    graph = _runtime_graph(projection_name="Workspace")
    request = SemanticPackageMaterializationExecutionContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        context_key=META_GRAPH_RUNTIME_CONTEXT_KEY,
        workspace_root=Path("/tmp/aware-test"),
        manifest_path=Path("/tmp/aware-test/aware.toml"),
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        context={"runtime_object_config_graphs": (graph,)},
    )

    assert (
        build_meta_graph_runtime_context_for_semantic_materialization(request) is None
    )


def test_meta_graph_context_resolves_from_runtime_index_ocg() -> None:
    graph = _runtime_graph(projection_name="Workspace")
    request = SemanticPackageMaterializationExecutionContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        context_key=META_GRAPH_RUNTIME_CONTEXT_KEY,
        workspace_root=Path("/tmp/aware-test"),
        manifest_path=Path("/tmp/aware-test/aware.toml"),
        runtime=object(),
        index=build_meta_graph_runtime_index_snapshot(ocg=graph),
        actor_id=None,
        branch_id=uuid4(),
        context={SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY: {"enabled": True}},
    )

    context = build_meta_graph_runtime_context_for_semantic_materialization(request)

    assert context is not None
    assert context.runtime_graph_ids == (graph.id,)
    assert context.projection_hash_for_name("Workspace") == "sha256:test:Workspace"


def test_meta_workspace_materialization_runtime_context_uses_provider_package_scope() -> (
    None
):
    repo_root = _aware_repo_root()
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        workspace_root=repo_root,
        repo_root=repo_root,
        manifest_path=repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        context={
            "runtime_ontology_package_names": (
                "storage-ontology",
                "content-ontology",
                "code-ontology",
                "history-ontology",
                "meta-ontology",
            ),
        },
        provider_payload={
            "runtime_ontology_package_names": ("meta-ontology",),
        },
    )

    context = build_meta_workspace_materialization_runtime_context(request)

    assert context is not None
    assert context.projection_hash_for_name("ObjectConfigGraphPackage")
    assert context.projection_hash_for_name("CodePackage")


def test_meta_workspace_materialization_runtime_context_roots_runtime_state_at_workspace_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_meta.runtime.factory as runtime_factory

    repo_root = tmp_path / "kernel"
    workspace_root = tmp_path / "home"
    repo_root.mkdir()
    workspace_root.mkdir()
    manifest_path = (
        workspace_root / "modules" / "home" / "structure" / "ontology" / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text('[package]\nname = "home-ontology"\n', encoding="utf-8")
    captured: dict[str, object] = {}

    class _Runtime:
        context = SimpleNamespace(
            index=object(),
            phase_timings_s={"runtime_factory_total_s": 0.123},
            package_timings=(),
            runtime_graphs=(),
            source_graphs=(),
            projection_hash_for_name=lambda _name: "sha256:test",
        )

    def _build_runtime(**kwargs: object) -> object:
        captured.update(kwargs)
        return _Runtime()

    monkeypatch.setattr(
        runtime_factory,
        "build_meta_graph_runtime_for_aware_package_manifests",
        _build_runtime,
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=manifest_path,
        context={
            "runtime_handler_owner_prefixes": ("aware_workspace",),
        },
    )

    context = build_meta_workspace_materialization_runtime_context(request)

    assert context is not None
    assert captured["workspace_root"] == workspace_root
    assert captured["package_manifest_paths"] == (manifest_path.resolve(),)
    assert captured["handler_owner_prefixes"] == ("aware_workspace",)
    assert context.phase_timings_s["runtime_factory_total_s"] == 0.123
    for phase_name in (
        "workspace_provider_select_manifest_paths_s",
        "workspace_provider_package_cache_owner_roots_s",
        "workspace_provider_package_entries_s",
        "workspace_provider_source_analysis_allowed_paths_s",
        "workspace_provider_package_graph_cache_request_signature_s",
        "workspace_provider_handler_owner_prefixes_s",
        "workspace_provider_import_runtime_support_s",
        "workspace_provider_build_meta_graph_runtime_s",
        "workspace_provider_wrap_context_s",
        "workspace_provider_total_s",
    ):
        assert context.phase_timings_s[phase_name] >= 0.0


def test_meta_workspace_materialization_runtime_context_uses_strict_catalog_cache(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_meta.runtime.factory as runtime_factory

    repo_root = tmp_path / "kernel"
    workspace_root = tmp_path / "home"
    manifest_path = (
        workspace_root / "modules" / "home" / "structure" / "ontology" / "aware.toml"
    )
    support_owner_root = tmp_path / "aware_workspace"
    support_manifest_path = (
        support_owner_root
        / "modules"
        / "workspace"
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    _write_minimal_aware_manifest(
        manifest_path=manifest_path,
        package_name="home-ontology",
        fqn_prefix="aware_home",
    )
    _write_minimal_aware_manifest(
        manifest_path=support_manifest_path,
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
    )
    captured: dict[str, object] = {}

    class _Runtime:
        context = SimpleNamespace(
            index=object(),
            phase_timings_s={},
            package_timings=(),
            runtime_graphs=(),
            source_graphs=(),
            projection_hash_for_name=lambda _name: "sha256:test",
        )

    def _build_runtime(**kwargs: object) -> object:
        captured.update(kwargs)
        return _Runtime()

    monkeypatch.setattr(
        runtime_factory,
        "build_meta_graph_runtime_for_aware_package_manifests",
        _build_runtime,
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_ontology",
        semantic_owner="aware_ontology.provider",
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=manifest_path,
        context={
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    {
                        "module_id": "home",
                        "package_name": "home-ontology",
                        "fqn_prefix": "aware_home",
                        "owner_root": workspace_root.as_posix(),
                        "manifest_path": manifest_path.as_posix(),
                        "dependency_package_names": [],
                    },
                    {
                        "module_id": "workspace",
                        "package_name": "workspace-ontology",
                        "fqn_prefix": "aware_workspace",
                        "catalog_provenance": "provider_support",
                        "owner_root": support_owner_root.as_posix(),
                        "manifest_path": support_manifest_path.as_posix(),
                        "dependency_package_names": [],
                    },
                ],
            },
        },
    )

    context = build_meta_workspace_materialization_runtime_context(request)

    assert context is not None
    assert captured["strict_package_graph_cache"] is True
    assert captured["package_manifest_paths"] == (manifest_path.resolve(),)
    assert isinstance(captured["package_graph_cache_request_signature"], str)
    entries_by_manifest = captured["package_entries_by_manifest_path"]
    assert isinstance(entries_by_manifest, dict)
    assert entries_by_manifest[manifest_path.resolve()].package_name == (
        "home-ontology"
    )
    owner_roots_by_manifest = captured["package_cache_owner_roots_by_manifest_path"]
    assert isinstance(owner_roots_by_manifest, dict)
    assert owner_roots_by_manifest[manifest_path.resolve()] == workspace_root.resolve()
    assert captured["source_analysis_allowed_manifest_paths"] == (
        manifest_path.resolve(),
        support_manifest_path.resolve(),
    )


def test_meta_workspace_materialization_runtime_context_allows_runtime_support_refresh(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_meta.runtime.factory as runtime_factory

    repo_root = tmp_path / "kernel"
    workspace_root = tmp_path / "aware_kernel"
    storage_manifest_path = (
        repo_root / "modules" / "storage" / "structure" / "ontology" / "aware.toml"
    )
    content_manifest_path = (
        repo_root / "modules" / "content" / "structure" / "ontology" / "aware.toml"
    )
    code_manifest_path = (
        repo_root / "modules" / "code" / "structure" / "ontology" / "aware.toml"
    )
    _write_minimal_aware_manifest(
        manifest_path=storage_manifest_path,
        package_name="storage-ontology",
        fqn_prefix="aware_storage",
    )
    _write_minimal_aware_manifest(
        manifest_path=content_manifest_path,
        package_name="content-ontology",
        fqn_prefix="aware_content",
        dependency_package_names=("storage-ontology",),
    )
    _write_minimal_aware_manifest(
        manifest_path=code_manifest_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        dependency_package_names=("content-ontology",),
    )
    captured: dict[str, object] = {}

    class _Runtime:
        context = SimpleNamespace(
            index=object(),
            phase_timings_s={},
            package_timings=(),
            runtime_graphs=(),
            source_graphs=(),
            projection_hash_for_name=lambda _name: "sha256:test",
        )

    def _build_runtime(**kwargs: object) -> object:
        captured.update(kwargs)
        return _Runtime()

    monkeypatch.setattr(
        runtime_factory,
        "build_meta_graph_runtime_for_aware_package_manifests",
        _build_runtime,
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_ontology",
        semantic_owner="aware_ontology.provider",
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=content_manifest_path,
        context={
            "runtime_ontology_package_names": ("code-ontology",),
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    {
                        "module_id": "storage",
                        "package_name": "storage-ontology",
                        "fqn_prefix": "aware_storage",
                        "owner_root": repo_root.as_posix(),
                        "manifest_path": storage_manifest_path.as_posix(),
                        "dependency_package_names": [],
                    },
                    {
                        "module_id": "content",
                        "package_name": "content-ontology",
                        "fqn_prefix": "aware_content",
                        "owner_root": repo_root.as_posix(),
                        "manifest_path": content_manifest_path.as_posix(),
                        "dependency_package_names": ["storage-ontology"],
                    },
                    {
                        "module_id": "code",
                        "package_name": "code-ontology",
                        "fqn_prefix": "aware_code",
                        "owner_root": repo_root.as_posix(),
                        "manifest_path": code_manifest_path.as_posix(),
                        "dependency_package_names": ["content-ontology"],
                    },
                ],
            },
        },
    )

    context = build_meta_workspace_materialization_runtime_context(request)

    selected_paths = (
        storage_manifest_path.resolve(),
        content_manifest_path.resolve(),
        code_manifest_path.resolve(),
    )
    assert context is not None
    assert captured["strict_package_graph_cache"] is True
    assert captured["package_manifest_paths"] == selected_paths
    assert captured["source_analysis_allowed_manifest_paths"] == selected_paths


def test_meta_workspace_materialization_runtime_context_uses_handler_backed_ocg_mutations() -> (
    None
):
    policy = _workspace_materialization_implementation_policy()

    assert policy.default_function_impl_ownership is (
        MetaGraphFunctionImplOwnership.authored
    )


def test_meta_workspace_materialization_manifest_paths_honor_no_dependency_closure() -> (
    None
):
    repo_root = _aware_repo_root()
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        workspace_root=repo_root,
        repo_root=repo_root,
        manifest_path=repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        context={
            "runtime_ontology_package_names": (
                "storage-ontology",
                "content-ontology",
                "code-ontology",
                "history-ontology",
                "meta-ontology",
            ),
            "runtime_include_package_dependency_closure": False,
        },
    )

    paths = _workspace_materialization_package_manifest_paths(request)

    assert paths == (
        (
            repo_root
            / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml"
        ).resolve(),
    )


def test_meta_workspace_materialization_manifest_paths_use_runtime_package_names_and_target() -> (
    None
):
    repo_root = _aware_repo_root()
    target_manifest_path = (
        repo_root / "workspaces/aware_home/modules/home/structure/ontology/aware.toml"
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_ontology",
        semantic_owner="aware_ontology.provider",
        workspace_root=repo_root,
        repo_root=repo_root,
        manifest_path=target_manifest_path,
        context={
            "runtime_ontology_package_names": (
                "storage-ontology",
                "content-ontology",
                "code-ontology",
                "history-ontology",
                "meta-ontology",
                "ontology-ontology",
            ),
            "runtime_include_package_dependency_closure": False,
        },
    )

    paths = _workspace_materialization_package_manifest_paths(request)

    assert paths == (
        (
            repo_root
            / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml"
        ).resolve(),
        target_manifest_path.resolve(),
    )


def test_meta_workspace_materialization_manifest_paths_can_isolate_target_from_dependency_bootstrap() -> (
    None
):
    repo_root = _aware_repo_root()
    target_manifest_path = (
        repo_root / "workspaces/aware_kernel/modules/api/ontology/aware.ontology.toml"
    )
    target_source_manifest_path = (
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml"
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_ontology",
        semantic_owner="aware_ontology.provider",
        workspace_root=repo_root / "workspaces/aware_kernel",
        repo_root=repo_root,
        manifest_path=target_manifest_path,
        context={
            "runtime_ontology_package_names": (
                "storage-ontology",
                "content-ontology",
                "code-ontology",
                "history-ontology",
                "meta-ontology",
                "ontology-ontology",
            ),
            "runtime_include_package_dependency_closure": False,
        },
        provider_payload={
            SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY: (
                SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS
            ),
        },
    )

    paths = _workspace_materialization_package_manifest_paths(request)

    assert target_source_manifest_path.resolve() not in paths
    assert paths == (
        (
            repo_root
            / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml"
        ).resolve(),
        (
            repo_root
            / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml"
        ).resolve(),
    )


def test_meta_workspace_materialization_manifest_paths_resolve_ontology_target_to_source_manifest() -> (
    None
):
    repo_root = _aware_repo_root()
    target_manifest_path = (
        repo_root / "workspaces/aware_home/modules/home/ontology/aware.ontology.toml"
    )
    source_manifest_path = (
        repo_root / "workspaces/aware_home/modules/home/ontology/structure/aware.toml"
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_ontology",
        semantic_owner="aware_ontology.provider",
        workspace_root=repo_root,
        repo_root=repo_root,
        manifest_path=target_manifest_path,
        context={
            "runtime_ontology_package_names": ("meta-ontology",),
            "runtime_include_package_dependency_closure": False,
        },
    )

    paths = _workspace_materialization_package_manifest_paths(request)

    assert paths == (
        (
            repo_root
            / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml"
        ).resolve(),
        source_manifest_path.resolve(),
    )


def test_meta_workspace_materialization_manifest_paths_exclude_api_target_from_meta_context() -> (
    None
):
    repo_root = _aware_repo_root()
    target_manifest_path = (
        repo_root / "workspaces/aware_workspace/apis/workspace/aware.api.toml"
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_api",
        semantic_owner="aware_api.provider",
        workspace_root=repo_root / "workspaces/aware_workspace",
        repo_root=repo_root,
        manifest_path=target_manifest_path,
        context={
            "runtime_ontology_package_names": ("api-ontology",),
            "runtime_include_package_dependency_closure": False,
        },
    )

    paths = _workspace_materialization_package_manifest_paths(request)

    assert target_manifest_path.resolve() not in paths
    assert all(path.name == "aware.toml" for path in paths)
    assert (
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml"
    ).resolve() in paths


def test_meta_workspace_materialization_manifest_paths_fail_closed_for_missing_runtime_package() -> (
    None
):
    repo_root = _aware_repo_root()
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_ontology",
        semantic_owner="aware_ontology.provider",
        workspace_root=repo_root,
        repo_root=repo_root,
        manifest_path=repo_root
        / "workspaces/aware_home/modules/home/structure/ontology/aware.toml",
        context={
            "runtime_ontology_package_names": ("missing-ontology",),
            "runtime_include_package_dependency_closure": False,
        },
    )

    with pytest.raises(ValueError, match="missing-ontology"):
        _workspace_materialization_package_manifest_paths(request)


def test_meta_workspace_manifest_paths_resolve_required_projection_from_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path

    def manifest(module_id: str) -> Path:
        path = (
            workspace_root
            / "modules"
            / module_id
            / "structure"
            / "ontology"
            / "aware.toml"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        return path

    entries_by_package_name = {
        "api-ontology": MetaRuntimePackageIndexEntry(
            module_id="api",
            package_name="api-ontology",
            fqn_prefix="aware_api",
            manifest_path=manifest("api"),
        ),
        "workspace-ontology": MetaRuntimePackageIndexEntry(
            module_id="workspace",
            package_name="workspace-ontology",
            fqn_prefix="aware_workspace",
            manifest_path=manifest("workspace"),
            dependency_package_names=("api-ontology",),
        ),
        "meta-ontology": MetaRuntimePackageIndexEntry(
            module_id="meta",
            package_name="meta-ontology",
            fqn_prefix="aware_meta",
            manifest_path=manifest("meta"),
        ),
        "code-ontology": MetaRuntimePackageIndexEntry(
            module_id="code",
            package_name="code-ontology",
            fqn_prefix="aware_code",
            manifest_path=manifest("code"),
        ),
    }
    graph = _runtime_graph(
        name="Workspace",
        fqn_prefix="aware_workspace",
        projection_name="Workspace",
        projection_hash="sha256:test:Workspace",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix="aware_workspace",
        language=CodeLanguage.aware.value,
    )
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=entries_by_package_name["workspace-ontology"].manifest_path,
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
        graph=graph,
    )

    def catalog(*, repo_root: Path) -> object:
        del repo_root
        return entries_by_package_name, {
            "meta": "meta-ontology",
            "code": "code-ontology",
            "workspace": "workspace-ontology",
            "api": "api-ontology",
        }

    monkeypatch.setattr(
        "aware_meta.runtime.graph_context._ontology_package_manifest_catalog",
        catalog,
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        workspace_root=workspace_root,
        repo_root=workspace_root,
        manifest_path=entries_by_package_name["meta-ontology"].manifest_path,
        context={
            "runtime_ontology_package_names": ("meta-ontology", "code-ontology"),
            "runtime_include_package_dependency_closure": False,
            "required_projection_names": ("Workspace",),
        },
    )

    paths = _workspace_materialization_package_manifest_paths(request)

    assert paths == (
        entries_by_package_name["api-ontology"].manifest_path,
        entries_by_package_name["workspace-ontology"].manifest_path,
        entries_by_package_name["meta-ontology"].manifest_path,
        entries_by_package_name["code-ontology"].manifest_path,
    )
    assert not (
        entries_by_package_name["workspace-ontology"].manifest_path.parent / "aware"
    ).exists()


def test_meta_required_projection_manifest_paths_are_resolved_from_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path

    def manifest(module_id: str) -> Path:
        path = (
            workspace_root
            / "modules"
            / module_id
            / "structure"
            / "ontology"
            / "aware.toml"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        return path

    entries_by_package_name = {
        "api-ontology": MetaRuntimePackageIndexEntry(
            module_id="api",
            package_name="api-ontology",
            fqn_prefix="aware_api",
            manifest_path=manifest("api"),
        ),
        "workspace-ontology": MetaRuntimePackageIndexEntry(
            module_id="workspace",
            package_name="workspace-ontology",
            fqn_prefix="aware_workspace",
            manifest_path=manifest("workspace"),
            dependency_package_names=("api-ontology",),
        ),
    }
    graph = _runtime_graph(
        name="Workspace",
        fqn_prefix="aware_workspace",
        projection_name="Workspace",
        projection_hash="sha256:test:Workspace",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix="aware_workspace",
        language=CodeLanguage.aware.value,
    )
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=entries_by_package_name["workspace-ontology"].manifest_path,
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
        graph=graph,
    )

    def catalog(*, repo_root: Path) -> object:
        del repo_root
        return entries_by_package_name, {"workspace": "workspace-ontology"}

    monkeypatch.setattr(
        "aware_meta.runtime.graph_context._ontology_package_manifest_catalog",
        catalog,
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_environment",
        semantic_owner="aware_environment.provider",
        workspace_root=workspace_root,
        repo_root=workspace_root,
        context={"required_projection_names": ("Workspace",)},
    )

    paths = resolve_workspace_required_projection_package_manifest_paths(request)

    assert paths == (
        entries_by_package_name["api-ontology"].manifest_path,
        entries_by_package_name["workspace-ontology"].manifest_path,
    )


def test_meta_required_projection_manifest_paths_use_catalog_projection_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    api_manifest_path = (
        workspace_root / "modules" / "api" / "structure" / "ontology" / "aware.toml"
    )
    workspace_manifest_path = (
        workspace_root
        / "modules"
        / "workspace"
        / "structure"
        / "ontology"
        / "aware.toml"
    )

    def fail_index_build(**_kwargs: object) -> object:
        raise AssertionError("projection index should not be built")

    monkeypatch.setattr(
        graph_context_module,
        "build_meta_runtime_package_projection_index",
        fail_index_build,
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_environment",
        semantic_owner="aware_environment.provider",
        workspace_root=workspace_root,
        repo_root=workspace_root,
        context={
            "required_projection_names": ("Workspace",),
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    {
                        "module_id": "api",
                        "package_name": "api-ontology",
                        "fqn_prefix": "aware_api",
                        "manifest_path": api_manifest_path.as_posix(),
                        "dependency_package_names": [],
                    },
                    {
                        "module_id": "workspace",
                        "package_name": "workspace-ontology",
                        "fqn_prefix": "aware_workspace",
                        "manifest_path": workspace_manifest_path.as_posix(),
                        "dependency_package_names": ["api-ontology"],
                        "projection_names": ["Workspace"],
                    },
                ],
            },
        },
    )

    paths = resolve_workspace_required_projection_package_manifest_paths(request)

    assert paths == (api_manifest_path.resolve(), workspace_manifest_path.resolve())


def test_ontology_package_manifest_catalog_resolves_module_first_facade(
    tmp_path: Path,
) -> None:
    module_root = tmp_path / "modules" / "home"
    ontology_root = module_root / "ontology"
    source_manifest_path = ontology_root / "structure" / "aware.toml"
    source_manifest_path.parent.mkdir(parents=True)
    (ontology_root / "aware.ontology.toml").write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'source_manifest = "structure/aware.toml"',
                "",
                "[[dependencies]]",
                'package_name = "code-ontology"',
                "",
            )
        ),
        encoding="utf-8",
    )
    source_manifest_path.write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_home"',
                "",
                "[[dependencies]]",
                'package_name = "content-ontology"',
                "",
            )
        ),
        encoding="utf-8",
    )
    (module_root / "aware.module.toml").write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[module]",
                'stable_ids_ownership = "compiler"',
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "ontology/aware.ontology.toml"',
                'visibility = "module"',
                "",
            )
        ),
        encoding="utf-8",
    )

    entries_by_package_name, package_names_by_module_id = (
        _ontology_package_manifest_catalog(repo_root=tmp_path)
    )

    entry = entries_by_package_name["home-ontology"]
    assert entry.module_id == "home"
    assert entry.fqn_prefix == "aware_home"
    assert entry.manifest_path == source_manifest_path.resolve()
    assert entry.dependency_package_names == (
        "code-ontology",
        "content-ontology",
    )
    assert package_names_by_module_id == {"home": "home-ontology"}


def test_ontology_package_manifest_catalog_includes_workspace_modules(
    tmp_path: Path,
) -> None:
    def write_module(
        module_root: Path,
        *,
        package_name: str,
        fqn_prefix: str,
        dependency_package_names: tuple[str, ...] = (),
    ) -> Path:
        ontology_root = module_root / "ontology"
        source_manifest_path = ontology_root / "structure" / "aware.toml"
        source_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        dependency_lines: list[str] = []
        for dependency_package_name in dependency_package_names:
            dependency_lines.extend(
                [
                    "",
                    "[[dependencies]]",
                    f'package_name = "{dependency_package_name}"',
                ]
            )
        (ontology_root / "aware.ontology.toml").write_text(
            "\n".join(
                (
                    "aware_ontology = 1",
                    "",
                    "[ontology]",
                    f'package_name = "{package_name}"',
                    f'fqn_prefix = "{fqn_prefix}"',
                    'source_manifest = "structure/aware.toml"',
                    *dependency_lines,
                    "",
                )
            ),
            encoding="utf-8",
        )
        source_manifest_path.write_text(
            "\n".join(
                (
                    "aware = 1",
                    "",
                    "[package]",
                    f'package_name = "{package_name}"',
                    f'fqn_prefix = "{fqn_prefix}"',
                    'kind = "ontology"',
                    "",
                    "[build]",
                    'environment_slug = "test"',
                    "",
                )
            ),
            encoding="utf-8",
        )
        (module_root / "aware.module.toml").write_text(
            "\n".join(
                (
                    "aware = 1",
                    "",
                    "[[packages]]",
                    'id = "ontology"',
                    'kind = "ontology"',
                    'manifest = "ontology/aware.ontology.toml"',
                    'visibility = "module"',
                    "",
                )
            ),
            encoding="utf-8",
        )
        return source_manifest_path

    content_manifest_path = write_module(
        tmp_path / "modules" / "content",
        package_name="content-ontology",
        fqn_prefix="aware_content",
    )
    conversation_manifest_path = write_module(
        tmp_path / "workspaces" / "aware_coordination" / "modules" / "conversation",
        package_name="conversation-ontology",
        fqn_prefix="aware_conversation",
        dependency_package_names=("content-ontology",),
    )

    entries_by_package_name, package_names_by_module_id = (
        _ontology_package_manifest_catalog(repo_root=tmp_path)
    )

    assert entries_by_package_name["content-ontology"].manifest_path == (
        content_manifest_path.resolve()
    )
    conversation_entry = entries_by_package_name["conversation-ontology"]
    assert conversation_entry.module_id == "aware_coordination:conversation"
    assert conversation_entry.manifest_path == conversation_manifest_path.resolve()
    assert conversation_entry.dependency_package_names == ("content-ontology",)
    assert package_names_by_module_id["aware_coordination:conversation"] == (
        "conversation-ontology"
    )


def test_meta_graph_context_for_required_projections_uses_manifest_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path

    def manifest(module_id: str) -> Path:
        path = (
            workspace_root
            / "modules"
            / module_id
            / "structure"
            / "ontology"
            / "aware.toml"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        return path

    entries_by_package_name = {
        "api-ontology": MetaRuntimePackageIndexEntry(
            module_id="api",
            package_name="api-ontology",
            fqn_prefix="aware_api",
            manifest_path=manifest("api"),
        ),
        "workspace-ontology": MetaRuntimePackageIndexEntry(
            module_id="workspace",
            package_name="workspace-ontology",
            fqn_prefix="aware_workspace",
            manifest_path=manifest("workspace"),
            dependency_package_names=("api-ontology",),
        ),
    }
    graph = _runtime_graph(
        name="Workspace",
        fqn_prefix="aware_workspace",
        projection_name="Workspace",
        projection_hash="sha256:test:Workspace",
    )
    graph.id = stable_object_config_graph_id(
        fqn_prefix="aware_workspace",
        language=CodeLanguage.aware.value,
    )
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=entries_by_package_name["workspace-ontology"].manifest_path,
        package_name="workspace-ontology",
        fqn_prefix="aware_workspace",
        graph=graph,
    )

    def catalog(*, repo_root: Path) -> object:
        del repo_root
        return entries_by_package_name, {"workspace": "workspace-ontology"}

    seen: dict[str, object] = {}

    def build_context(
        *,
        package_manifest_paths: tuple[Path, ...],
        workspace_root: Path | None,
        composition_context_id: object | None,
        composite_name: str,
        package_entries_by_manifest_path: object,
    ) -> MetaGraphRuntimeContext:
        seen["package_manifest_paths"] = package_manifest_paths
        seen["workspace_root"] = workspace_root
        seen["composition_context_id"] = composition_context_id
        seen["composite_name"] = composite_name
        seen["package_entries_by_manifest_path"] = package_entries_by_manifest_path
        return build_meta_graph_runtime_context(runtime_graphs=(graph,))

    monkeypatch.setattr(
        "aware_meta.runtime.graph_context._ontology_package_manifest_catalog",
        catalog,
    )
    monkeypatch.setattr(
        "aware_meta.runtime.graph_context.build_meta_graph_runtime_context_for_aware_package_manifests",
        build_context,
    )

    context = build_meta_graph_runtime_context_for_workspace_required_projections(
        repo_root=workspace_root,
        aware_root=workspace_root,
        required_projection_names=("Workspace",),
        composite_name="Required Workspace Test Context",
    )

    assert seen["package_manifest_paths"] == (
        entries_by_package_name["api-ontology"].manifest_path,
        entries_by_package_name["workspace-ontology"].manifest_path,
    )
    assert seen["package_entries_by_manifest_path"] == {
        entry.manifest_path: entry for entry in entries_by_package_name.values()
    }
    assert seen["workspace_root"] == workspace_root.resolve()
    assert seen["composite_name"] == "Required Workspace Test Context"
    assert context.projection_hash_for_name("Workspace") == "sha256:test:Workspace"


def test_meta_workspace_materialization_manifest_paths_add_required_projection_packages() -> (
    None
):
    repo_root = _aware_repo_root()
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        workspace_root=repo_root,
        repo_root=repo_root,
        manifest_path=repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        context={
            "runtime_ontology_package_names": ("code-ontology", "meta-ontology"),
            "runtime_include_package_dependency_closure": False,
            "required_projection_names": ("Workspace",),
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    {
                        "module_id": "api",
                        "package_name": "api-ontology",
                        "fqn_prefix": "aware_api",
                        "manifest_path": (
                            "workspaces/aware_kernel/modules/api/ontology/"
                            "structure/aware.toml"
                        ),
                        "dependency_package_names": [
                            "code-ontology",
                            "meta-ontology",
                        ],
                    },
                    {
                        "module_id": "code",
                        "package_name": "code-ontology",
                        "fqn_prefix": "aware_code",
                        "manifest_path": "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
                        "dependency_package_names": [],
                    },
                    {
                        "module_id": "meta",
                        "package_name": "meta-ontology",
                        "fqn_prefix": "aware_meta",
                        "manifest_path": "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
                        "dependency_package_names": [
                            "code-ontology",
                        ],
                    },
                    {
                        "module_id": "workspace",
                        "package_name": "workspace-ontology",
                        "fqn_prefix": "aware_workspace",
                        "manifest_path": (
                            "workspaces/aware_workspace/modules/workspace/"
                            "structure/ontology/aware.toml"
                        ),
                        "dependency_package_names": [
                            "api-ontology",
                            "code-ontology",
                            "meta-ontology",
                        ],
                        "projection_names": ["Workspace"],
                    },
                ],
            },
        },
    )

    paths = _workspace_materialization_package_manifest_paths(request)

    assert (
        repo_root
        / "workspaces/aware_workspace/modules/workspace/structure/ontology/aware.toml"
    ).resolve() in paths
    assert (
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml"
    ).resolve() in paths


def test_meta_workspace_materialization_manifest_paths_close_target_dependencies(
    tmp_path: Path,
) -> None:
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        workspace_root=tmp_path,
        repo_root=tmp_path,
        manifest_path=tmp_path / "ontologies/social/structure/aware.toml",
        context={
            "runtime_include_package_dependency_closure": False,
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    {
                        "module_id": "content",
                        "package_name": "content-ontology",
                        "fqn_prefix": "aware_content",
                        "manifest_path": ("ontologies/content/structure/aware.toml"),
                        "dependency_package_names": [],
                    },
                    {
                        "module_id": "reactivity",
                        "package_name": "reactivity-ontology",
                        "fqn_prefix": "aware_reactivity",
                        "manifest_path": ("ontologies/reactivity/structure/aware.toml"),
                        "dependency_package_names": [],
                    },
                    {
                        "module_id": "social",
                        "package_name": "social-ontology",
                        "fqn_prefix": "aware_social",
                        "manifest_path": "ontologies/social/structure/aware.toml",
                        "dependency_package_names": [
                            "content-ontology",
                            "reactivity-ontology",
                        ],
                    },
                ],
            },
        },
    )

    paths = _workspace_materialization_package_manifest_paths(request)

    assert paths == (
        (tmp_path / "ontologies/content/structure/aware.toml").resolve(),
        (tmp_path / "ontologies/reactivity/structure/aware.toml").resolve(),
        (tmp_path / "ontologies/social/structure/aware.toml").resolve(),
    )


def test_meta_workspace_materialization_manifest_paths_close_all_selected_targets(
    tmp_path: Path,
) -> None:
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        workspace_root=tmp_path,
        repo_root=tmp_path,
        manifest_path=tmp_path / "ontologies/conversation/structure/aware.toml",
        context={
            "runtime_include_package_dependency_closure": False,
            SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY: (
                (tmp_path / "ontologies/conversation/structure/aware.toml").as_posix(),
                (tmp_path / "ontologies/social/structure/aware.toml").as_posix(),
            ),
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    {
                        "module_id": "content",
                        "package_name": "content-ontology",
                        "fqn_prefix": "aware_content",
                        "manifest_path": ("ontologies/content/structure/aware.toml"),
                        "dependency_package_names": [],
                    },
                    {
                        "module_id": "conversation",
                        "package_name": "conversation-ontology",
                        "fqn_prefix": "aware_conversation",
                        "manifest_path": (
                            "ontologies/conversation/structure/aware.toml"
                        ),
                        "dependency_package_names": [
                            "content-ontology",
                        ],
                    },
                    {
                        "module_id": "reactivity",
                        "package_name": "reactivity-ontology",
                        "fqn_prefix": "aware_reactivity",
                        "manifest_path": ("ontologies/reactivity/structure/aware.toml"),
                        "dependency_package_names": [],
                    },
                    {
                        "module_id": "social",
                        "package_name": "social-ontology",
                        "fqn_prefix": "aware_social",
                        "manifest_path": "ontologies/social/structure/aware.toml",
                        "dependency_package_names": [
                            "content-ontology",
                            "reactivity-ontology",
                        ],
                    },
                ],
            },
        },
    )

    paths = _workspace_materialization_package_manifest_paths(request)

    assert paths == (
        (tmp_path / "ontologies/content/structure/aware.toml").resolve(),
        (tmp_path / "ontologies/conversation/structure/aware.toml").resolve(),
        (tmp_path / "ontologies/reactivity/structure/aware.toml").resolve(),
        (tmp_path / "ontologies/social/structure/aware.toml").resolve(),
    )
