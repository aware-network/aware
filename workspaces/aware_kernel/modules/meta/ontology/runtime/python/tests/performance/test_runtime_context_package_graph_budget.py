from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.package_graph_reuse_cache import (
    OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_CONTEXT_GRAPHS,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE,
    OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_VERSION,
    object_config_graph_package_context_reuse_cache_path,
    object_config_graph_package_reuse_cache_path,
)
from aware_meta.runtime.graph_context import (
    _clear_meta_graph_runtime_index_snapshot_cache,
    _clear_meta_package_graph_session_cache,
    _external_graph_signature,
    _source_text_manifest_hash,
    _stable_object_config_graph_package_branch_id,
    build_meta_graph_runtime_context_for_aware_package_manifests,
)
from aware_meta.runtime.package_index import MetaRuntimePackageIndexEntry
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_id,
    stable_object_config_graph_package_id,
)

from .budgets import BudgetTimer, assert_metric_lte
from .samples import build_meta_performance_runtime_graph


@pytest.fixture(autouse=True)
def _clear_meta_runtime_context_caches() -> Iterator[None]:
    _clear_meta_package_graph_session_cache()
    _clear_meta_graph_runtime_index_snapshot_cache()
    yield
    _clear_meta_package_graph_session_cache()
    _clear_meta_graph_runtime_index_snapshot_cache()


def test_runtime_context_strict_context_cache_hit_budget(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    fixture = _write_runtime_context_cache_fixture(
        workspace_root=workspace_root,
        dependency_package_names=("meta-perf-dep-0-ontology",),
    )

    timer = BudgetTimer.start(
        label="runtime_context_strict_context_cache_hit",
        max_duration_s=1.0,
    )
    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=fixture.manifest_paths,
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=fixture.entries_by_manifest_path,
        package_graph_cache_request_signature="sha256:meta-perf:context-hit",
    )
    elapsed_s = timer.assert_within_budget()

    assert_metric_lte(
        label="runtime_context_strict_context_cache_hit_s",
        actual=elapsed_s,
        maximum=1.0,
    )
    assert_metric_lte(
        label="runtime_context_load_package_graphs_s",
        actual=context.phase_timings_s["load_package_graphs"],
        maximum=0.75,
    )
    assert len(context.package_timings) == 3
    assert {timing.cache_status for timing in context.package_timings} == {"hit"}
    assert {timing.cache_source for timing in context.package_timings} == {
        "catalog_context_reuse_cache"
    }
    for timing in context.package_timings:
        _assert_no_source_analysis(timing.phase_timings_s)
        assert "load_catalog_source_graph_payload" in timing.phase_timings_s
        assert "load_catalog_runtime_graph_payload" in timing.phase_timings_s
        assert "read_catalog_materialized_cache_payload" not in (timing.phase_timings_s)


def test_runtime_context_strict_session_cache_budget_skips_payload_graph_loads(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    fixture = _write_runtime_context_cache_fixture(
        workspace_root=workspace_root,
        dependency_package_names=("meta-perf-dep-0-ontology",),
    )
    first = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=fixture.manifest_paths,
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=fixture.entries_by_manifest_path,
        package_graph_cache_request_signature="sha256:meta-perf:session-first",
    )

    timer = BudgetTimer.start(
        label="runtime_context_strict_session_cache_hit",
        max_duration_s=0.5,
    )
    second = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=fixture.manifest_paths,
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=fixture.entries_by_manifest_path,
        package_graph_cache_request_signature="sha256:meta-perf:session-second",
    )
    elapsed_s = timer.assert_within_budget()

    assert_metric_lte(
        label="runtime_context_strict_session_cache_hit_s",
        actual=elapsed_s,
        maximum=0.5,
    )
    assert second.phase_timings_s["load_package_graphs"] <= (
        first.phase_timings_s["load_package_graphs"] + 0.05
    )
    assert {timing.cache_source for timing in second.package_timings} == {
        "catalog_session"
    }
    for timing in second.package_timings:
        _assert_no_source_analysis(timing.phase_timings_s)
        assert "catalog_package_graph_session_cache_lookup" in (timing.phase_timings_s)
        assert "load_catalog_source_graph_payload" not in timing.phase_timings_s
        assert "load_catalog_runtime_graph_payload" not in timing.phase_timings_s
        assert "read_catalog_materialized_cache_payload" not in (timing.phase_timings_s)


def test_runtime_context_materialized_readthrough_budget_refreshes_context_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    package_name = "meta-perf-lab-ontology"
    fqn_prefix = "aware_meta_perf_lab"
    manifest_path = _write_aware_manifest(
        workspace_root=workspace_root,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        module_name="meta_perf_lab",
        dependency_package_names=(),
    )
    source_graph = _stable_graph(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        class_count=8,
    )
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.hash = f"{source_graph.hash}:runtime-from-materialized-cache"
    source_manifest_hash = "sha256:meta-perf:source"
    fresh_dependency_signature = _external_graph_signature(external_graphs=())
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_graph=source_graph,
        runtime_graph=runtime_graph,
        source_manifest_hash=source_manifest_hash,
        dependency_signature="sha256:meta-perf:stale-dependency",
    )
    _write_materialized_package_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_graph=source_graph,
        source_manifest_hash=source_manifest_hash,
        dependency_signature=fresh_dependency_signature,
    )
    monkeypatch.setattr(
        "aware_meta.runtime.graph_context.derive_runtime_object_config_graph",
        lambda *_args, **_kwargs: SimpleNamespace(runtime_graph=runtime_graph),
    )

    entry = _entry(
        module_id="meta_perf_lab",
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
    )
    timer = BudgetTimer.start(
        label="runtime_context_materialized_readthrough",
        max_duration_s=1.0,
    )
    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=(manifest_path,),
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path={manifest_path.resolve(): entry},
        package_graph_cache_request_signature="sha256:meta-perf:readthrough",
    )
    elapsed_s = timer.assert_within_budget()

    assert_metric_lte(
        label="runtime_context_materialized_readthrough_s",
        actual=elapsed_s,
        maximum=1.0,
    )
    timing = context.package_timings[0]
    assert timing.cache_status == "hit"
    assert timing.cache_source == "catalog_materialized_package_cache"
    _assert_no_source_analysis(timing.phase_timings_s)
    assert "derive_runtime_graph_from_materialized_cache" in timing.phase_timings_s
    assert "write_catalog_context_cache_from_materialized_payload" in (
        timing.phase_timings_s
    )
    refreshed_payload = json.loads(
        _context_cache_path(
            workspace_root=workspace_root,
            manifest_path=manifest_path,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ).read_text(encoding="utf-8")
    )
    assert refreshed_payload["dependency_signature"] == fresh_dependency_signature
    assert refreshed_payload["runtime_object_config_graph_hash"] == runtime_graph.hash


def test_runtime_context_non_strict_materialized_readthrough_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    package_name = "meta-perf-lab-ontology"
    fqn_prefix = "aware_meta_perf_lab"
    manifest_path = _write_aware_manifest(
        workspace_root=workspace_root,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        module_name="meta_perf_lab",
        dependency_package_names=(),
    )
    source_text = (
        "class Demo {}\nprojection Demo {\n    root aware_meta_perf_lab.Demo\n}\n"
    )
    sources_root = manifest_path.parent / "aware"
    sources_root.mkdir(parents=True)
    (sources_root / "demo.aware").write_text(source_text, encoding="utf-8")
    source_graph = _stable_graph(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        class_count=8,
    )
    runtime_graph = source_graph.model_copy(deep=True)
    runtime_graph.hash = f"{source_graph.hash}:runtime-from-materialized-cache"
    source_manifest_hash = _source_text_manifest_hash(
        source_text_by_relative_path={"demo.aware": source_text}
    )
    fresh_dependency_signature = _external_graph_signature(external_graphs=())
    _write_context_graph_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_graph=source_graph,
        runtime_graph=runtime_graph,
        source_manifest_hash=source_manifest_hash,
        dependency_signature="sha256:meta-perf:stale-dependency",
    )
    _write_materialized_package_cache(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_graph=source_graph,
        source_manifest_hash=source_manifest_hash,
        dependency_signature=fresh_dependency_signature,
    )
    monkeypatch.setattr(
        "aware_meta.runtime.graph_context.derive_runtime_object_config_graph",
        lambda *_args, **_kwargs: SimpleNamespace(runtime_graph=runtime_graph),
    )

    timer = BudgetTimer.start(
        label="runtime_context_non_strict_materialized_readthrough",
        max_duration_s=1.0,
    )
    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=(manifest_path,),
        workspace_root=workspace_root,
    )
    elapsed_s = timer.assert_within_budget()

    assert_metric_lte(
        label="runtime_context_non_strict_materialized_readthrough_s",
        actual=elapsed_s,
        maximum=1.0,
    )
    timing = context.package_timings[0]
    assert timing.cache_status == "hit"
    assert timing.cache_source == "materialized_package_cache"
    assert "read_package_source_texts" in timing.phase_timings_s
    assert "analyze_meta_ocg_sources" not in timing.phase_timings_s
    assert "read_materialized_cache_payload" in timing.phase_timings_s
    assert "derive_runtime_graph_from_materialized_cache" in timing.phase_timings_s
    assert "write_context_cache_from_materialized_payload" in (timing.phase_timings_s)
    refreshed_payload = json.loads(
        _context_cache_path(
            workspace_root=workspace_root,
            manifest_path=manifest_path,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ).read_text(encoding="utf-8")
    )
    assert refreshed_payload["dependency_signature"] == fresh_dependency_signature
    assert refreshed_payload["runtime_object_config_graph_hash"] == runtime_graph.hash


@dataclass(frozen=True)
class _RuntimeContextCacheFixture:
    manifest_paths: tuple[Path, ...]
    entries_by_manifest_path: dict[Path, MetaRuntimePackageIndexEntry]


def _write_runtime_context_cache_fixture(
    *,
    workspace_root: Path,
    dependency_package_names: tuple[str, ...],
) -> _RuntimeContextCacheFixture:
    package_specs = (
        (
            "meta_perf_dep_0",
            "meta-perf-dep-0-ontology",
            "aware_meta_perf_dep_0",
            (),
            5,
        ),
        (
            "meta_perf_dep_1",
            "meta-perf-dep-1-ontology",
            "aware_meta_perf_dep_1",
            (),
            5,
        ),
        (
            "meta_perf_lab",
            "meta-perf-lab-ontology",
            "aware_meta_perf_lab",
            dependency_package_names,
            10,
        ),
    )
    graphs_by_package_name: dict[str, ObjectConfigGraph] = {}
    manifest_paths: list[Path] = []
    entries_by_manifest_path: dict[Path, MetaRuntimePackageIndexEntry] = {}
    for (
        module_name,
        package_name,
        fqn_prefix,
        dependencies,
        class_count,
    ) in package_specs:
        manifest_path = _write_aware_manifest(
            workspace_root=workspace_root,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            module_name=module_name,
            dependency_package_names=dependencies,
        )
        source_graph = _stable_graph(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            class_count=class_count,
        )
        runtime_graph = source_graph.model_copy(deep=True)
        runtime_graph.hash = f"{source_graph.hash}:runtime"
        external_graphs = tuple(
            graphs_by_package_name[dependency] for dependency in dependencies
        )
        _write_context_graph_cache(
            workspace_root=workspace_root,
            manifest_path=manifest_path,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            source_graph=source_graph,
            runtime_graph=runtime_graph,
            source_manifest_hash=f"sha256:meta-perf:{package_name}:source",
            dependency_signature=_external_graph_signature(
                external_graphs=external_graphs
            ),
        )
        graphs_by_package_name[package_name] = source_graph
        manifest_paths.append(manifest_path)
        entries_by_manifest_path[manifest_path.resolve()] = _entry(
            module_id=module_name,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            manifest_path=manifest_path,
            dependency_package_names=dependencies,
        )
    return _RuntimeContextCacheFixture(
        manifest_paths=tuple(manifest_paths),
        entries_by_manifest_path=entries_by_manifest_path,
    )


def _stable_graph(
    *,
    package_name: str,
    fqn_prefix: str,
    class_count: int,
) -> ObjectConfigGraph:
    graph = build_meta_performance_runtime_graph(
        fqn_prefix=fqn_prefix,
        graph_name=package_name,
        class_count=class_count,
        attributes_per_class=4,
        include_relationships=True,
    )
    graph_id = stable_object_config_graph_id(
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware.value,
    )
    graph.id = graph_id
    for node in graph.object_config_graph_nodes:
        node.object_config_graph_id = graph_id
    return graph


def _entry(
    *,
    module_id: str,
    package_name: str,
    fqn_prefix: str,
    manifest_path: Path,
    dependency_package_names: tuple[str, ...] = (),
) -> MetaRuntimePackageIndexEntry:
    return MetaRuntimePackageIndexEntry(
        module_id=module_id,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
        dependency_package_names=dependency_package_names,
    )


def _write_aware_manifest(
    *,
    workspace_root: Path,
    package_name: str,
    fqn_prefix: str,
    module_name: str,
    dependency_package_names: tuple[str, ...],
) -> Path:
    manifest_path = (
        workspace_root
        / "modules"
        / module_name
        / "structure"
        / "ontology"
        / "aware.toml"
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "aware = 1",
        "",
        "[package]",
        f'package_name = "{package_name}"',
        f'fqn_prefix = "{fqn_prefix}"',
        'kind = "ontology"',
        "version_number = 1",
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
    return manifest_path


def _write_context_graph_cache(
    *,
    workspace_root: Path,
    manifest_path: Path,
    package_name: str,
    fqn_prefix: str,
    source_graph: ObjectConfigGraph,
    runtime_graph: ObjectConfigGraph,
    source_manifest_hash: str,
    dependency_signature: str,
) -> None:
    cache_path = _context_cache_path(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
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
                    OBJECT_CONFIG_GRAPH_PACKAGE_CONTEXT_GRAPHS_DERIVATION_SIGNATURE
                ),
                "package_name": package_name,
                "fqn_prefix": fqn_prefix,
                "object_config_graph_id": str(source_graph.id),
                "object_config_graph_package_id": str(
                    stable_object_config_graph_package_id(
                        package_name=package_name,
                        fqn_prefix=fqn_prefix,
                    )
                ),
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


def _write_materialized_package_cache(
    *,
    workspace_root: Path,
    manifest_path: Path,
    package_name: str,
    fqn_prefix: str,
    source_graph: ObjectConfigGraph,
    source_manifest_hash: str,
    dependency_signature: str,
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
                "object_config_graph_id": str(source_graph.id),
                "object_config_graph_hash": source_graph.hash,
                "object_config_graph_package_id": str(package_id),
                "object_config_graph": source_graph.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _context_cache_path(
    *,
    workspace_root: Path,
    manifest_path: Path,
    package_name: str,
    fqn_prefix: str,
) -> Path:
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
    return object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    )


def _assert_no_source_analysis(phase_timings_s: Mapping[str, float]) -> None:
    assert "read_package_source_texts" not in phase_timings_s
    assert "analyze_meta_ocg_sources" not in phase_timings_s
