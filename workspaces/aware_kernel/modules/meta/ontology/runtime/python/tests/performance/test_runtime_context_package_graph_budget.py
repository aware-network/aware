from __future__ import annotations

import json
from threading import Barrier
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
    object_config_graph_package_runtime_index_sidecar_cache_path,
    object_config_graph_package_reuse_cache_path,
    write_object_config_graph_package_runtime_index_sidecar_cache_payload,
)
import aware_meta.runtime.graph_context as graph_context_module
from aware_meta.runtime.graph_context import (
    _clear_meta_graph_runtime_index_snapshot_cache,
    _clear_meta_package_graph_session_cache,
    _external_graph_signature,
    _object_config_graph_payload_for_context_cache,
    _source_text_manifest_hash,
    _stable_object_config_graph_package_branch_id,
    MetaGraphRuntimeCompactContextError,
    MetaGraphRuntimeContext,
    build_meta_graph_runtime_context_for_aware_package_manifests,
)
from aware_meta.runtime.package_index import MetaRuntimePackageIndexEntry
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_id,
    stable_object_config_graph_package_id,
)
from aware_orm.session.change_collector import is_change_tracking_hooks_enabled

from .budgets import assert_metric_lte
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

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=fixture.manifest_paths,
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=fixture.entries_by_manifest_path,
        package_graph_cache_request_signature="sha256:meta-perf:context-hit",
    )

    _assert_context_budget_lte(
        label="runtime_context_strict_context_cache_hit_s",
        context=context,
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


def test_runtime_context_strict_runtime_only_cache_hit_budget(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    fixture = _write_runtime_context_cache_fixture(
        workspace_root=workspace_root,
        dependency_package_names=("meta-perf-dep-0-ontology",),
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=fixture.manifest_paths,
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=fixture.entries_by_manifest_path,
        package_graph_cache_request_signature="sha256:meta-perf:runtime-only-hit",
        load_source_graph_payloads=False,
    )

    _assert_context_budget_lte(
        label="runtime_context_strict_runtime_only_cache_hit_s",
        context=context,
        maximum=0.75,
    )
    assert_metric_lte(
        label="runtime_context_runtime_only_load_package_graphs_s",
        actual=context.phase_timings_s["load_package_graphs"],
        maximum=0.6,
    )
    assert len(context.package_timings) == 3
    assert {timing.cache_status for timing in context.package_timings} == {"hit"}
    assert {timing.cache_source for timing in context.package_timings} == {
        "catalog_context_reuse_cache"
    }
    for timing in context.package_timings:
        _assert_no_source_analysis(timing.phase_timings_s)
        assert "load_catalog_source_graph_payload" not in timing.phase_timings_s
        assert "load_catalog_runtime_graph_payload" in timing.phase_timings_s
        assert "load_catalog_runtime_graph_payload.model_validate" in (
            timing.phase_timings_s
        )
        assert "load_catalog_runtime_graph_payload.namespace_evidence_check" in (
            timing.phase_timings_s
        )
        assert "read_catalog_materialized_cache_payload" not in (timing.phase_timings_s)


def test_runtime_context_cache_body_hydration_disables_mutation_hooks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    fixture = _write_runtime_context_cache_fixture(
        workspace_root=workspace_root,
        dependency_package_names=(),
    )
    observed_hook_states: list[bool] = []
    original_model_validate = ObjectConfigGraph.model_validate

    def _observed_model_validate(
        _cls: type[ObjectConfigGraph], value: object
    ) -> ObjectConfigGraph:
        observed_hook_states.append(is_change_tracking_hooks_enabled())
        return original_model_validate(value)

    monkeypatch.setattr(
        ObjectConfigGraph,
        "model_validate",
        classmethod(_observed_model_validate),
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=fixture.manifest_paths,
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=fixture.entries_by_manifest_path,
        package_graph_cache_request_signature="sha256:meta-perf:read-only-hydration",
        load_source_graph_payloads=False,
    )

    assert observed_hook_states
    assert observed_hook_states == [False] * len(observed_hook_states)
    assert is_change_tracking_hooks_enabled() is True
    assert {timing.cache_status for timing in context.package_timings} == {"hit"}
    for timing in context.package_timings:
        assert "load_catalog_runtime_graph_payload.model_validate" in (
            timing.phase_timings_s
        )


def test_runtime_context_strict_runtime_only_loads_runtime_payloads_concurrently(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    fixture = _write_runtime_context_cache_fixture(
        workspace_root=workspace_root,
        dependency_package_names=("meta-perf-dep-0-ontology",),
    )
    original_loader = graph_context_module._load_graph_payload_from_context_cache
    runtime_payload_load_barrier = Barrier(len(fixture.manifest_paths))
    loaded_payload_keys: list[str] = []

    def _observed_loader(**kwargs: object) -> ObjectConfigGraph | None:
        payload_key = kwargs["payload_key"]
        assert isinstance(payload_key, str)
        loaded_payload_keys.append(payload_key)
        if payload_key == "source_object_config_graph":
            raise AssertionError("runtime-only fast path loaded source graph body")
        if payload_key == "runtime_object_config_graph":
            runtime_payload_load_barrier.wait(timeout=5.0)
        return original_loader(**kwargs)

    monkeypatch.setattr(
        graph_context_module,
        "_load_graph_payload_from_context_cache",
        _observed_loader,
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=fixture.manifest_paths,
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=fixture.entries_by_manifest_path,
        package_graph_cache_request_signature=(
            "sha256:meta-perf:runtime-only-concurrent"
        ),
        load_source_graph_payloads=False,
    )

    assert loaded_payload_keys == [
        "runtime_object_config_graph",
        "runtime_object_config_graph",
        "runtime_object_config_graph",
    ]
    assert "strict_runtime_only_load_runtime_graph_payloads" in (
        context.phase_timings_s
    )
    for timing in context.package_timings:
        assert "load_catalog_runtime_index_sidecar" in timing.phase_timings_s
        assert "load_catalog_source_graph_payload" not in timing.phase_timings_s


def test_runtime_context_strict_runtime_only_index_only_skips_graph_body_loads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path
    fixture = _write_runtime_context_cache_fixture(
        workspace_root=workspace_root,
        dependency_package_names=("meta-perf-dep-0-ontology",),
    )
    loaded_payload_keys: list[str] = []

    def _observed_loader(**kwargs: object) -> ObjectConfigGraph | None:
        payload_key = kwargs["payload_key"]
        assert isinstance(payload_key, str)
        loaded_payload_keys.append(payload_key)
        raise AssertionError("index-only context loaded an OCG body payload")

    monkeypatch.setattr(
        graph_context_module,
        "_load_graph_payload_from_context_cache",
        _observed_loader,
    )

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=fixture.manifest_paths,
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=fixture.entries_by_manifest_path,
        package_graph_cache_request_signature=(
            "sha256:meta-perf:runtime-only-index-only"
        ),
        load_source_graph_payloads=False,
        runtime_context_graph_body_requirement="index_only",
    )

    _assert_context_budget_lte(
        label="runtime_context_strict_runtime_only_index_only_s",
        context=context,
        maximum=0.35,
    )
    assert loaded_payload_keys == []
    assert context.runtime_context_graph_body_requirement == "index_only"
    assert "strict_runtime_only_load_runtime_graph_payloads" not in (
        context.phase_timings_s
    )
    assert "strict_runtime_only_build_index_only_graphs" in context.phase_timings_s
    assert len(context.runtime_graphs) == 3
    assert context.index.class_configs_by_id == {}
    assert context.index.relationships_by_id == {}
    for timing in context.package_timings:
        assert "read_catalog_runtime_index_sidecar_cache_payload" in (
            timing.phase_timings_s
        )
        assert "read_catalog_context_cache_payload" not in timing.phase_timings_s
        assert "load_catalog_runtime_index_sidecar" in timing.phase_timings_s
        assert "load_catalog_source_graph_payload" not in timing.phase_timings_s
        assert "load_catalog_runtime_graph_payload" not in timing.phase_timings_s


def test_runtime_context_index_only_rejection_identifies_deficient_package(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    fixture = _write_runtime_context_cache_fixture(
        workspace_root=workspace_root,
        dependency_package_names=("meta-perf-dep-0-ontology",),
    )
    manifest_path = fixture.manifest_paths[1]
    package_name = "meta-perf-dep-1-ontology"
    fqn_prefix = "aware_meta_perf_dep_1"
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
    object_config_graph_package_runtime_index_sidecar_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    ).unlink()
    object_config_graph_package_context_reuse_cache_path(
        aware_root=workspace_root,
        branch_id=branch_id,
        object_config_graph_package_id=package_id,
    ).unlink()

    with pytest.raises(MetaGraphRuntimeCompactContextError) as raised:
        build_meta_graph_runtime_context_for_aware_package_manifests(
            package_manifest_paths=fixture.manifest_paths,
            workspace_root=workspace_root,
            strict_package_graph_cache=True,
            package_entries_by_manifest_path=fixture.entries_by_manifest_path,
            package_graph_cache_request_signature=(
                "sha256:meta-perf:index-only-rejection"
            ),
            load_source_graph_payloads=False,
            runtime_context_graph_body_requirement="index_only",
        )

    evidence = raised.value.evidence
    assert evidence["package_name"] == package_name
    assert evidence["manifest_path"] == manifest_path.resolve().as_posix()
    assert evidence["cache_owner_root"] == workspace_root.resolve().as_posix()
    assert evidence["reason"] == "catalog_cache_payload_missing"
    assert evidence["cache_diagnostics"] == {
        "cache_miss_reason": "catalog_cache_payload_missing",
        "cache_status": "miss",
        "context_cache_miss_reason": "catalog_cache_payload_missing",
        "context_cache_status": "miss",
    }


def test_runtime_context_index_only_rejection_reports_signature_coordinates(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    fixture = _write_runtime_context_cache_fixture(
        workspace_root=workspace_root,
        dependency_package_names=("meta-perf-dep-0-ontology",),
    )
    manifest_path = fixture.manifest_paths[2]
    package_name = "meta-perf-lab-ontology"
    fqn_prefix = "aware_meta_perf_lab"
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
    paths = (
        object_config_graph_package_runtime_index_sidecar_cache_path(
            aware_root=workspace_root,
            branch_id=branch_id,
            object_config_graph_package_id=package_id,
        ),
        object_config_graph_package_context_reuse_cache_path(
            aware_root=workspace_root,
            branch_id=branch_id,
            object_config_graph_package_id=package_id,
        ),
    )
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["dependency_signature"] = "sha256:stale-dependency-signature"
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    with pytest.raises(MetaGraphRuntimeCompactContextError) as raised:
        build_meta_graph_runtime_context_for_aware_package_manifests(
            package_manifest_paths=fixture.manifest_paths,
            workspace_root=workspace_root,
            strict_package_graph_cache=True,
            package_entries_by_manifest_path=fixture.entries_by_manifest_path,
            package_graph_cache_request_signature=(
                "sha256:meta-perf:index-only-signature-rejection"
            ),
            load_source_graph_payloads=False,
            runtime_context_graph_body_requirement="index_only",
        )

    diagnostics = raised.value.evidence["cache_diagnostics"]
    assert isinstance(diagnostics, dict)
    assert diagnostics["cache_miss_reason"] == "dependency_signature_mismatch"
    assert diagnostics["dependency_signature_actual"] == (
        "sha256:stale-dependency-signature"
    )
    assert diagnostics["dependency_signature_expected"] != (
        diagnostics["dependency_signature_actual"]
    )


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

    second = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=fixture.manifest_paths,
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path=fixture.entries_by_manifest_path,
        package_graph_cache_request_signature="sha256:meta-perf:session-second",
    )

    _assert_context_budget_lte(
        label="runtime_context_strict_session_cache_hit_s",
        context=second,
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
    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=(manifest_path,),
        workspace_root=workspace_root,
        strict_package_graph_cache=True,
        package_entries_by_manifest_path={manifest_path.resolve(): entry},
        package_graph_cache_request_signature="sha256:meta-perf:readthrough",
    )

    _assert_context_budget_lte(
        label="runtime_context_materialized_readthrough_s",
        context=context,
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

    context = build_meta_graph_runtime_context_for_aware_package_manifests(
        package_manifest_paths=(manifest_path,),
        workspace_root=workspace_root,
    )

    _assert_context_budget_lte(
        label="runtime_context_non_strict_materialized_readthrough_s",
        context=context,
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
    identity = graph_context_module._PackageGraphCacheIdentity(  # noqa: SLF001
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        branch_id=_stable_object_config_graph_package_branch_id(
            workspace_root=workspace_root,
            aware_toml_path=manifest_path,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        object_config_graph_id=source_graph.id,
        object_config_graph_package_id=stable_object_config_graph_package_id(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        source_manifest_hash=source_manifest_hash,
        dependency_signature=dependency_signature,
    )
    runtime_index_sidecar_payload = (
        graph_context_module._runtime_package_index_sidecar_payload(  # noqa: SLF001
            identity=identity,
            source_graph=source_graph,
            runtime_graph=runtime_graph,
        )
    )
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
                "runtime_package_index_sidecar": runtime_index_sidecar_payload,
                "source_object_config_graph": (
                    _object_config_graph_payload_for_context_cache(source_graph)
                ),
                "runtime_object_config_graph": (
                    _object_config_graph_payload_for_context_cache(runtime_graph)
                ),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    write_object_config_graph_package_runtime_index_sidecar_cache_payload(
        aware_root=workspace_root,
        branch_id=identity.branch_id,
        object_config_graph_package_id=identity.object_config_graph_package_id,
        payload=graph_context_module._runtime_package_index_sidecar_cache_payload(  # noqa: SLF001
            identity=identity,
            sidecar_payload=runtime_index_sidecar_payload,
        ),
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
                "object_config_graph": (
                    _object_config_graph_payload_for_context_cache(source_graph)
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


def _assert_context_budget_lte(
    *,
    label: str,
    context: MetaGraphRuntimeContext,
    maximum: float,
) -> None:
    actual = context.phase_timings_s["total"]
    assert actual <= maximum, (
        f"{label} exceeded budget: actual={actual} max={maximum} "
        f"context_phases={context.phase_timings_s} "
        f"package_phases="
        f"{[(timing.package_name, timing.cache_status, timing.cache_source, timing.phase_timings_s) for timing in context.package_timings]}"
    )
