from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import msgpack
import pytest

from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_LIFECYCLE_PROFILE_CONTEXT_KEY,
    SemanticPackageMaterializationExecutionContext,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    SemanticPackageMaterializationRequest,
)


_TEST_FILE = Path(__file__).resolve()
_KERNEL_WORKSPACE_ROOT = _TEST_FILE.parents[6]
_KERNEL_MODULES_ROOT = _KERNEL_WORKSPACE_ROOT / "modules"
_NETWORK_WORKSPACE_ROOT = _TEST_FILE.parents[8] / "workspaces" / "aware_network"


def _prepend_runtime_roots(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for module_id in ("code", "meta", "ontology"):
        monkeypatch.syspath_prepend(
            str(_KERNEL_MODULES_ROOT / module_id / "ontology" / "runtime" / "python")
        )


def _ontology_runtime_artifact_set_receipt(receipts: object) -> Mapping[str, object]:
    if not isinstance(receipts, (list, tuple)):
        raise AssertionError("Ontology runtime artifact-set receipts unavailable.")
    for receipt in receipts:
        if (
            isinstance(receipt, Mapping)
            and receipt.get("output_key") == "ontology_runtime_artifact_set"
        ):
            return receipt
    raise AssertionError("Ontology runtime artifact-set receipt missing.")


def _patch_ontology_runtime_bundle_writer(
    *,
    monkeypatch: pytest.MonkeyPatch,
    workspace_provider: object,
) -> Path:
    observed_manifest_path: Path | None = None

    def _fake_write_ontology_runtime_bundle(**kwargs: object) -> object:
        nonlocal observed_manifest_path
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        observed_manifest_path = (
            output_dir / "ontology.runtime.manifest.json"
        ).resolve()
        observed_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        observed_manifest_path.write_text(
            '{"environment":{"id":"demo-runtime"}}\n',
            encoding="utf-8",
        )
        contract_path = observed_manifest_path.parent / "bundle.contract.json"
        contract_path.write_text("{}\n", encoding="utf-8")
        db_schema_registry_path = (
            observed_manifest_path.parent / "db.schema.registry.json"
        )
        db_schema_registry_path.write_text(
            '{"entries":[{"sql_root":"/tmp/demo/sql"}]}\n',
            encoding="utf-8",
        )
        return SimpleNamespace(
            manifest_path=observed_manifest_path,
            contract_path=contract_path,
            db_schema_registry_path=db_schema_registry_path,
            artifact_count=7,
        )

    monkeypatch.setattr(
        workspace_provider,
        "write_ontology_runtime_bundle",
        _fake_write_ontology_runtime_bundle,
    )
    return Path(
        "modules/demo/structure/ontology/.aware/ontology/runtime/ontology.runtime.manifest.json"
    )


def _patch_no_runtime_graph_closure(
    *,
    monkeypatch: pytest.MonkeyPatch,
    workspace_provider: object,
) -> None:
    monkeypatch.setattr(
        workspace_provider,
        "_target_runtime_object_config_graph_from_manifest_closure",
        lambda **_: None,
    )


def _fake_ontology_projection_hash_by_name(**kwargs: object) -> str:
    projection_name = kwargs["projection_name"]
    assert isinstance(projection_name, str)
    return {
        "OntologyConfig": "ontology-config-projection",
        "OntologyPackage": "ontology-package-projection",
    }[projection_name]


def test_ontology_provider_reuses_execution_context_dependency_graphs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_ontology.materialization import workspace_provider

    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="Source Meta",
        description=None,
        hash="sha256:source-meta",
        fqn_prefix="aware_meta",
        language=CodeLanguage.aware,
    )
    runtime_graph = ObjectConfigGraph(
        id=source_graph.id,
        name="Runtime Meta",
        description=None,
        hash="sha256:runtime-meta",
        fqn_prefix="aware_meta",
        language=CodeLanguage.aware,
    )
    meta_context = SimpleNamespace(
        source_graphs=(source_graph,),
        runtime_graphs=(runtime_graph,),
        source_graph_by_package_name={"meta-ontology": source_graph},
        runtime_graph_by_package_name={"meta-ontology": runtime_graph},
    )
    execution_context = SemanticPackageMaterializationExecutionContext(
        entries={
            "aware_meta.graph_runtime_context": SimpleNamespace(
                meta_context=meta_context,
            )
        }
    )
    request = SimpleNamespace(context={}, execution_context=execution_context)

    context = workspace_provider._request_context_with_execution_context_entries(  # noqa: SLF001
        request=request
    )

    assert (
        workspace_provider._object_config_graphs_for_kind_from_context(  # noqa: SLF001
            context=context,
            graph_kind="runtime",
        )
        == (runtime_graph,)
    )
    assert (
        workspace_provider._object_config_graphs_for_kind_from_context(  # noqa: SLF001
            context=context,
            graph_kind="source",
        )
        == (source_graph,)
    )
    assert workspace_provider._complete_dependency_graphs_from_context_by_package_name(  # noqa: SLF001
        context=context,
        package_names=("meta-ontology",),
    ) == (
        runtime_graph,
    )


def test_ontology_provider_reuses_direct_workspace_dependency_graph_maps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_ontology.materialization import workspace_provider

    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="Source Storage",
        description=None,
        hash="sha256:source-storage",
        fqn_prefix="aware_storage",
        language=CodeLanguage.aware,
    )
    runtime_graph = ObjectConfigGraph(
        id=source_graph.id,
        name="Runtime Storage",
        description=None,
        hash="sha256:runtime-storage",
        fqn_prefix="aware_storage",
        language=CodeLanguage.aware,
    )
    context = {
        "semantic_object_config_graphs_by_package_name": {
            "storage-ontology": source_graph
        },
        "runtime_object_config_graphs_by_package_name": {
            "storage-ontology": runtime_graph
        },
    }

    assert workspace_provider._complete_dependency_graphs_from_context_by_package_name(  # noqa: SLF001
        context=context,
        package_names=("storage-ontology",),
    ) == (
        runtime_graph,
    )


def test_ontology_provider_accepts_runtime_only_dependency_graph_maps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_ontology.materialization import workspace_provider

    runtime_graph = ObjectConfigGraph(
        id=uuid4(),
        name="Runtime Storage",
        description=None,
        hash="sha256:runtime-storage",
        fqn_prefix="aware_storage",
        language=CodeLanguage.aware,
    )
    context = {
        "runtime_object_config_graphs_by_package_name": {
            "storage-ontology": runtime_graph
        },
    }

    assert workspace_provider._complete_dependency_graphs_from_context_by_package_name(  # noqa: SLF001
        context=context,
        package_names=("storage-ontology",),
    ) == (
        runtime_graph,
    )


def test_ontology_provider_external_graphs_ignore_unrelated_context_graphs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_ontology.materialization import workspace_provider

    dependency_graph = ObjectConfigGraph(
        id=uuid4(),
        name="Runtime Storage",
        description=None,
        hash="sha256:runtime-storage",
        fqn_prefix="aware_storage",
        language=CodeLanguage.aware,
    )
    unrelated_graph = ObjectConfigGraph(
        id=uuid4(),
        name="Runtime Experience",
        description=None,
        hash="sha256:runtime-experience",
        fqn_prefix="aware_experience",
        language=CodeLanguage.aware,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_target_dependency_object_config_graphs",
        lambda **_: (dependency_graph,),
    )

    assert workspace_provider._external_object_config_graphs_for_request(  # noqa: SLF001
        request=SimpleNamespace(),
        source=SimpleNamespace(package_name="demo-ontology"),
        context={"runtime_object_config_graphs": (unrelated_graph,)},
    ) == (dependency_graph,)


def test_ontology_runtime_bundle_uses_target_runtime_graph_from_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_meta_ontology.graph.projection.object_projection_graph import (
        ObjectProjectionGraph,
    )
    from aware_ontology.materialization import workspace_provider

    graph_id = uuid4()
    source_graph = ObjectConfigGraph(
        id=graph_id,
        name="Source Demo",
        description=None,
        hash="sha256:source-demo",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_projection_graphs=(),
    )
    runtime_graph = ObjectConfigGraph(
        id=graph_id,
        name="Runtime Demo",
        description=None,
        hash="sha256:runtime-demo",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_projection_graphs=(
            ObjectProjectionGraph(
                id=uuid4(),
                name="RuntimeProjection",
                projection_hash="runtime.projection",
                language=CodeLanguage.aware,
                object_config_graph_id=graph_id,
                supports_virtual_build=True,
                object_projection_graph_nodes=(),
            ),
        ),
    )
    dependency_graph = ObjectConfigGraph(
        id=uuid4(),
        name="Runtime Dependency",
        description=None,
        hash="sha256:runtime-dependency",
        fqn_prefix="aware_dependency",
        language=CodeLanguage.aware,
    )
    context = {
        "aware_meta.graph_runtime_context": SimpleNamespace(
            meta_context=SimpleNamespace(
                runtime_graph_by_package_name={
                    "demo-ontology": runtime_graph,
                }
            )
        )
    }
    source_manifest_path = (
        tmp_path / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    source_manifest_path.parent.mkdir(parents=True)
    source_manifest_path.write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                'title = "Demo Ontology"',
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )
    source = workspace_provider._OntologyPackageSource(  # noqa: SLF001
        ontology_toml_path=tmp_path / "modules" / "demo" / "aware.ontology.toml",
        source_manifest_path=source_manifest_path,
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        version_number=1,
        title="Demo",
        description=None,
        manifest_relative_path="modules/demo/structure/ontology/aware.toml",
        package_root="modules/demo",
        sources_root="modules/demo/structure/ontology/aware",
    )
    leaf_result = SimpleNamespace(object_config_graph=source_graph)
    observed: dict[str, object] = {}

    def _fake_write_ontology_runtime_bundle(**kwargs: object) -> object:
        observed.update(kwargs)
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        manifest_path = output_dir / "ontology.runtime.manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            '{"environment":{"id":"demo-runtime"}}\n',
            encoding="utf-8",
        )
        contract_path = output_dir / "bundle.contract.json"
        contract_path.write_text("{}\n", encoding="utf-8")
        return SimpleNamespace(
            manifest_path=manifest_path.resolve(),
            contract_path=contract_path,
            db_schema_registry_path=None,
            artifact_count=6,
        )

    monkeypatch.setattr(
        workspace_provider,
        "write_ontology_runtime_bundle",
        _fake_write_ontology_runtime_bundle,
    )

    target = workspace_provider._target_runtime_object_config_graph_from_context(  # noqa: SLF001
        context=context,
        source=source,
    )
    assert target is runtime_graph
    descriptors = (
        workspace_provider._runtime_projection_descriptors_for_ocg(  # noqa: SLF001
            target
        )
    )
    assert descriptors[0]["projection_name"] == "RuntimeProjection"
    assert descriptors[0]["projection_hash"] == "runtime.projection"

    details = workspace_provider._runtime_bundle_manifest_details(  # noqa: SLF001
        source=source,
        leaf_result=leaf_result,
        runtime_graph=target,
        external_graphs=(dependency_graph,),
    )

    assert observed["canonical_graph"] is runtime_graph
    assert observed["binding_graph"] is runtime_graph
    assert observed["external_graphs"] == (dependency_graph,)
    assert details["runtime_bundle_manifest_status"] == "available"


def test_ontology_runtime_sql_graph_accepts_dependency_construct_targets() -> None:
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_ontology.runtime_bundle import _ontology_runtime_sql_graph

    api_graph_path = (
        _NETWORK_WORKSPACE_ROOT
        / "modules/api/ontology/structure/.aware/ontology/runtime/ocg.snapshot.msgpack"
    )
    meta_graph_path = (
        _KERNEL_WORKSPACE_ROOT
        / "modules/meta/ontology/structure/.aware/ontology/runtime/ocg.snapshot.msgpack"
    )
    api_graph = ObjectConfigGraph.model_validate(
        msgpack.unpackb(api_graph_path.read_bytes(), raw=False, strict_map_key=False)
    )
    meta_graph = ObjectConfigGraph.model_validate(
        msgpack.unpackb(meta_graph_path.read_bytes(), raw=False, strict_map_key=False)
    )

    with pytest.raises(ValueError, match="construct propagation target function"):
        _ontology_runtime_sql_graph(api_graph)

    sql_graph = _ontology_runtime_sql_graph(
        api_graph,
        external_graphs=(meta_graph,),
    )

    assert sql_graph.fqn_prefix == api_graph.fqn_prefix
    assert sql_graph.object_config_graph_nodes


def test_ontology_runtime_sql_graph_ignores_recursive_private_runtime_state() -> None:
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_ontology.runtime_bundle import _ontology_runtime_sql_graph

    class _RecursivePrivateState:
        def __deepcopy__(self, memo: object) -> object:
            from copy import deepcopy

            return deepcopy(self, memo)

    graph = ObjectConfigGraph(
        id=uuid4(),
        name="Recursive Private State",
        description=None,
        hash="sha256:recursive-private-state",
        fqn_prefix="aware_recursive_private_state",
        language=CodeLanguage.aware,
    )
    graph._bound_session = _RecursivePrivateState()  # noqa: SLF001

    with pytest.raises(RecursionError):
        graph.model_copy(deep=True)

    sql_graph = _ontology_runtime_sql_graph(graph)

    assert sql_graph.fqn_prefix == graph.fqn_prefix
    assert sql_graph.object_config_graph_nodes == []


def test_ontology_runtime_graph_manifest_closure_resolves_missing_target(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_meta_ontology.graph.config.object_config_graph import (
        ObjectConfigGraph,
    )
    from aware_meta_ontology.graph.projection.object_projection_graph import (
        ObjectProjectionGraph,
    )
    from aware_ontology.materialization import workspace_provider

    target_graph_id = uuid4()
    target_runtime_graph = ObjectConfigGraph(
        id=target_graph_id,
        name="Runtime Demo",
        description=None,
        hash="sha256:runtime-demo",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_projection_graphs=(
            ObjectProjectionGraph(
                id=uuid4(),
                name="RuntimeProjection",
                projection_hash="runtime.projection",
                language=CodeLanguage.aware,
                object_config_graph_id=target_graph_id,
                supports_virtual_build=True,
                object_projection_graph_nodes=(),
            ),
        ),
    )
    dependency_graph = ObjectConfigGraph(
        id=uuid4(),
        name="Runtime Dependency",
        description=None,
        hash="sha256:runtime-dependency",
        fqn_prefix="aware_dep",
        language=CodeLanguage.aware,
    )
    context = {
        "aware_meta.graph_runtime_context": SimpleNamespace(
            meta_context=SimpleNamespace(
                runtime_graph_by_package_name={
                    "dep-ontology": dependency_graph,
                },
                source_graph_by_package_name={
                    "dep-ontology": dependency_graph,
                },
            )
        )
    }
    source_manifest_path = (
        tmp_path / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    source_manifest_path.parent.mkdir(parents=True)
    source_manifest_path.write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )
    source = workspace_provider._OntologyPackageSource(  # noqa: SLF001
        ontology_toml_path=tmp_path / "modules" / "demo" / "aware.ontology.toml",
        source_manifest_path=source_manifest_path,
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        version_number=1,
        title="Demo",
        description=None,
        manifest_relative_path="modules/demo/structure/ontology/aware.toml",
        package_root="modules/demo",
        sources_root="modules/demo/structure/ontology/aware",
    )
    package_manifest_paths = (
        tmp_path / "modules" / "dep" / "structure" / "ontology" / "aware.toml",
        source_manifest_path,
    )
    observed: dict[str, object] = {}

    monkeypatch.setattr(
        workspace_provider,
        "resolve_meta_runtime_package_manifest_closure_for_package_names",
        lambda **_: package_manifest_paths,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_dependency_package_names_for_manifest_paths",
        lambda **_: ("dep-ontology",),
    )

    def _build_meta_graph_runtime_context(**kwargs: object) -> object:
        observed["package_manifest_paths"] = kwargs["package_manifest_paths"]
        return SimpleNamespace(
            runtime_graph_by_package_name={
                "demo-ontology": target_runtime_graph,
            },
            runtime_graphs=(dependency_graph, target_runtime_graph),
        )

    monkeypatch.setattr(
        workspace_provider,
        "build_meta_graph_runtime_context_for_aware_package_manifests",
        _build_meta_graph_runtime_context,
    )

    target = workspace_provider._target_runtime_object_config_graph_from_manifest_closure(  # noqa: SLF001
        request=SimpleNamespace(
            workspace_root=tmp_path,
            environment_id=uuid4(),
            context={},
        ),
        source=source,
        context=context,
    )

    assert target is target_runtime_graph
    assert observed["package_manifest_paths"] == package_manifest_paths


@pytest.mark.asyncio
async def test_ontology_provider_bridges_meta_language_outputs_before_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider

    workspace_root = tmp_path / "workspace"
    module_root = workspace_root / "modules" / "demo"
    ontology_root = module_root / "structure" / "ontology"
    ontology_root.mkdir(parents=True)
    ontology_toml_path = module_root / "aware.ontology.toml"
    source_manifest_path = ontology_root / "aware.toml"
    ontology_toml_path.write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'source_manifest = "structure/ontology/aware.toml"',
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
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                'title = "Demo Ontology"',
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )
    runtime_manifest_relpath = _patch_ontology_runtime_bundle_writer(
        monkeypatch=monkeypatch,
        workspace_provider=workspace_provider,
    )
    runtime_manifest_path = workspace_root / runtime_manifest_relpath

    source_code_package_id = uuid4()
    leaf_before = _fake_leaf_result(package_name="demo-ontology")
    leaf_after = _fake_leaf_result(package_name="demo-ontology")
    leaf_after.phase_timings_s = {
        "build_object_config_graph_from_code": 101.25,
        "total": 410.868,
    }
    leaf_after.semantic_commit_phase_timings_s = {
        "reuse_existing_object_config_graph_semantic_lane": 3.5,
        "total": 4.0,
    }
    observed: dict[str, object] = {}
    progress_events: list[dict[str, object]] = []
    config_commit = workspace_provider._OntologyConfigCommitResult(  # noqa: SLF001
        ontology_config_id=uuid4(),
        config_commit_id=uuid4(),
        config_head_commit_id=uuid4(),
        config_object_instance_graph_commit_id=uuid4(),
        commit_perf_ms={},
    )
    package_commit = workspace_provider._OntologyPackageCommitResult(  # noqa: SLF001
        ontology_package_id=uuid4(),
        package_commit_id=uuid4(),
        package_head_commit_id=uuid4(),
        package_object_instance_graph_commit_id=uuid4(),
        commit_perf_ms={},
    )

    async def _fake_leaf_materialization(**kwargs: object) -> object:
        observed["leaf_aware_toml_path"] = kwargs["aware_toml_path"]
        observed["leaf_source_code_package_id"] = kwargs.get("source_code_package_id")
        observed["leaf_force_fresh"] = kwargs.get(
            "force_fresh_semantic_materialization"
        )
        progress_callback = kwargs.get("progress_callback")
        observed["leaf_progress_callback_present"] = callable(progress_callback)
        if callable(progress_callback):
            await progress_callback(
                {
                    "phase_name": "meta.leaf_package.subphase",
                    "status": "running",
                    "detail_payload": {
                        "package_name": "demo-ontology",
                        "subphase_name": "build_object_config_graph_from_code",
                    },
                }
            )
        return leaf_before

    async def _fake_language_bridge(
        *,
        request: object,
        leaf_result: object,
    ) -> object:
        observed["bridge_request_manifest"] = getattr(request, "manifest_path")
        observed["bridge_leaf_result"] = leaf_result
        return SimpleNamespace(
            leaf_result=leaf_after,
            materialized_language_packages=(
                {
                    "package_name": "demo-ontology",
                    "language": "python",
                    "package_root": "modules/demo/structure/ontology/python",
                },
            ),
            details={
                "artifact_ownership_receipts": (
                    {
                        "producer_provider_key": "aware_meta",
                        "producer_key": (
                            "aware_meta.object_config_graph." "language_materialization"
                        ),
                        "artifact_family": "ocg_language_materialization",
                        "artifact_role": "source_code",
                        "output_key": "generated_language_files",
                    },
                ),
                "language_post_step_receipts": (
                    {"status": "succeeded", "tool": "python.bootstrap"},
                ),
                "generated_code_package_deltas": (
                    {
                        "package_name": "demo-ontology",
                        "package_root": "modules/demo/structure/ontology/python",
                        "authority_kind": "semantic_materialization",
                        "source_revision_id": "semantic-materialization:test",
                        "paths": (),
                    },
                ),
                "language_materialization_code_package_deltas": (
                    {
                        "package_name": "demo-ontology",
                        "package_root": "modules/demo/structure/ontology/python",
                        "authority_kind": "semantic_materialization",
                        "source_revision_id": "semantic-materialization:test",
                        "paths": (),
                    },
                ),
                "materialized_language_packages": (
                    {
                        "package_name": "demo-ontology",
                        "language": "python",
                    },
                ),
                "materialized_language_package_count": 1,
                "compile_parity_receipts": (
                    {
                        "receipt_kind": ("meta_workspace_materialize_compile_parity"),
                        "status": "compile_equivalent",
                    },
                ),
            },
        )

    async def _fake_commit_config_snapshot(**kwargs: object) -> object:
        observed["config_commit_leaf_result"] = kwargs["leaf_result"]
        return config_commit

    async def _fake_commit_snapshot(**kwargs: object) -> object:
        observed["commit_leaf_result"] = kwargs["leaf_result"]
        observed["package_ontology_config_commit"] = kwargs["ontology_config_commit"]
        return package_commit

    monkeypatch.setattr(
        workspace_provider.meta_service,
        "materialize_object_config_graph_package_leaf_from_manifest",
        _fake_leaf_materialization,
    )
    monkeypatch.setattr(
        workspace_provider.meta_workspace_provider,
        "materialize_object_config_graph_package_leaf_language_outputs",
        _fake_language_bridge,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_commit_ontology_config_snapshot",
        _fake_commit_config_snapshot,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_commit_ontology_package_snapshot",
        _fake_commit_snapshot,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_external_object_config_graphs_for_request",
        lambda **_: (),
    )
    _patch_no_runtime_graph_closure(
        monkeypatch=monkeypatch,
        workspace_provider=workspace_provider,
    )
    monkeypatch.setattr(
        workspace_provider,
        "find_meta_graph_projection_hash_by_name",
        _fake_ontology_projection_hash_by_name,
    )

    async def _progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    result = await workspace_provider.materialize(
        SemanticPackageMaterializationRequest(
            runtime=object(),
            index=object(),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            manifest_path=ontology_toml_path,
            source_code_package_id=source_code_package_id,
            context={
                "semantic_materialization_force_fresh": {
                    "schema": "aware.workspace.semantic_materialization.force_fresh.v1",
                    "enabled": True,
                },
            },
            progress_callback=_progress_callback,
        )
    )

    assert observed["leaf_aware_toml_path"] == source_manifest_path.resolve()
    assert observed["leaf_source_code_package_id"] == source_code_package_id
    assert observed["leaf_force_fresh"] is True
    assert observed["leaf_progress_callback_present"] is True
    assert progress_events == [
        {
            "phase_name": "meta.leaf_package.subphase",
            "status": "running",
            "detail_payload": {
                "package_name": "demo-ontology",
                "subphase_name": "build_object_config_graph_from_code",
            },
        }
    ]
    assert observed["bridge_request_manifest"] == source_manifest_path.resolve()
    assert observed["bridge_leaf_result"] is leaf_before
    assert observed["config_commit_leaf_result"] is leaf_after
    assert observed["commit_leaf_result"] is leaf_after
    assert observed["package_ontology_config_commit"] is config_commit
    assert result.details["ontology_config_id"] == str(config_commit.ontology_config_id)
    assert result.details["ontology_config_commit_id"] == str(
        config_commit.config_commit_id
    )
    assert result.details["ontology_config_object_instance_graph_commit_id"] == str(
        config_commit.config_object_instance_graph_commit_id
    )
    materialized_roots = cast(
        tuple[Mapping[str, object], ...],
        result.details["materialized_semantic_roots"],
    )
    assert [root["semantic_projection_name"] for root in materialized_roots] == [
        "OntologyConfig",
        "OntologyPackage",
    ]
    assert materialized_roots[0]["semantic_package_id"] == str(
        config_commit.ontology_config_id
    )
    assert materialized_roots[0]["semantic_object_instance_graph_commit_id"] == str(
        config_commit.config_object_instance_graph_commit_id
    )
    assert materialized_roots[1]["semantic_package_id"] == str(
        package_commit.ontology_package_id
    )
    assert materialized_roots[1]["semantic_object_instance_graph_commit_id"] == str(
        package_commit.package_object_instance_graph_commit_id
    )
    assert [bundle.semantic_projection_name for bundle in result.bundle_packages] == [
        "OntologyConfig",
        "OntologyPackage",
    ]
    config_bundle, package_bundle = result.bundle_packages
    assert config_bundle.package_key == "demo-ontology"
    assert config_bundle.semantic_package_id == config_commit.ontology_config_id
    assert config_bundle.semantic_root_id == config_commit.ontology_config_id
    assert config_bundle.semantic_root_kind == "OntologyConfig"
    assert config_bundle.semantic_projection_hash == "ontology-config-projection"
    assert config_bundle.semantic_object_instance_graph_commit_id == (
        config_commit.config_object_instance_graph_commit_id
    )
    assert package_bundle.package_key == "demo-ontology"
    assert package_bundle.semantic_package_id == package_commit.ontology_package_id
    assert package_bundle.semantic_root_id == package_commit.ontology_package_id
    assert package_bundle.semantic_root_kind == "OntologyPackage"
    assert package_bundle.semantic_projection_hash == "ontology-package-projection"
    assert package_bundle.semantic_object_instance_graph_commit_id == (
        package_commit.package_object_instance_graph_commit_id
    )
    assert result.details["manifest_path"] == ontology_toml_path.as_posix()
    assert result.details["source_manifest_path"] == (
        source_manifest_path.resolve().as_posix()
    )
    assert result.details["runtime_bundle_manifest_path"] == (
        runtime_manifest_path.resolve().as_posix()
    )
    assert (
        result.details["runtime_bundle_manifest_workspace_relative_path"]
        == runtime_manifest_relpath.as_posix()
    )
    assert result.details["runtime_bundle_manifest_status"] == "available"
    assert str(result.details["runtime_bundle_manifest_digest"]).startswith("sha256:")
    assert result.details["meta_leaf_phase_timings_s"] == {
        "build_object_config_graph_from_code": 101.25,
        "total": 410.868,
    }
    assert result.details["meta_leaf_semantic_commit_phase_timings_s"] == {
        "reuse_existing_object_config_graph_semantic_lane": 3.5,
        "total": 4.0,
    }
    assert result.details["artifact_ownership_receipts"]
    artifact_set_receipt = _ontology_runtime_artifact_set_receipt(
        result.details["artifact_ownership_receipts"]
    )
    artifact_set_payload = cast(
        Mapping[str, object],
        result.details["ontology_runtime_artifact_set"],
    )
    assert artifact_set_receipt["artifact_family"] == ("ontology_runtime_artifact_set")
    assert artifact_set_receipt["artifact_role"] == "runtime_artifact_set"
    assert (
        artifact_set_receipt["artifact_key"] == artifact_set_payload["artifact_set_id"]
    )
    assert artifact_set_receipt["runtime_contract_version"] == (
        "aware.ontology.runtime_artifact_set.v1"
    )
    assert artifact_set_receipt["ontology_runtime_artifact_set"] == (
        artifact_set_payload
    )
    runtime_descriptors = cast(
        list[Mapping[str, object]],
        artifact_set_payload["runtime_projection_descriptors"],
    )
    environment_descriptor = next(
        descriptor
        for descriptor in runtime_descriptors
        if descriptor["projection_name"] == "Environment"
    )
    assert environment_descriptor["projection_hash"] == "environment.projection"
    assert environment_descriptor["constructor_function_id"] is not None
    assert environment_descriptor["object_config_graph_id"] == (
        result.details["object_config_graph_id"]
    )
    artifact_roles = {
        artifact["artifact_role"]
        for artifact in cast(
            list[Mapping[str, object]], artifact_set_payload["artifacts"]
        )
    }
    assert "runtime_bundle_manifest" in artifact_roles
    assert "db_schema_registry" in artifact_roles
    runtime_bundle_artifact = next(
        artifact
        for artifact in cast(
            list[Mapping[str, object]], artifact_set_payload["artifacts"]
        )
        if artifact["artifact_role"] == "runtime_bundle_manifest"
    )
    assert runtime_bundle_artifact["status"] == "available"
    assert runtime_bundle_artifact["manifest_path"] == (
        runtime_manifest_path.resolve().as_posix()
    )
    db_schema_artifact = next(
        artifact
        for artifact in cast(
            list[Mapping[str, object]], artifact_set_payload["artifacts"]
        )
        if artifact["artifact_role"] == "db_schema_registry"
    )
    assert db_schema_artifact["manifest_path"].endswith("db.schema.registry.json")
    assert db_schema_artifact["provider_payload"] == {
        "package_kind": "ontology",
        "backend_targets": ["postgres"],
        "sql_roots": ["/tmp/demo/sql"],
    }
    provider_payload = cast(
        Mapping[str, object], artifact_set_receipt["provider_payload"]
    )
    assert provider_payload["runtime_projection_descriptor_count"] == len(
        runtime_descriptors
    )
    assert result.details["language_post_step_receipts"]
    assert result.details["generated_code_package_deltas"]
    assert result.details["language_materialization_code_package_deltas"]
    assert result.details["materialized_language_package_count"] == 1
    assert result.details["compile_parity_receipts"]
    bridge = cast(
        dict[str, object],
        result.details["meta_language_materialization_bridge"],
    )
    assert bridge["provider_key"] == "aware_meta"
    assert bridge["status"] == "completed"


@pytest.mark.asyncio
async def test_ontology_provider_skips_meta_language_outputs_for_semantic_render_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider

    workspace_root = tmp_path / "workspace"
    module_root = workspace_root / "modules" / "demo"
    ontology_root = module_root / "structure" / "ontology"
    ontology_root.mkdir(parents=True)
    ontology_toml_path = module_root / "aware.ontology.toml"
    source_manifest_path = ontology_root / "aware.toml"
    ontology_toml_path.write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'source_manifest = "structure/ontology/aware.toml"',
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
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                'title = "Demo Ontology"',
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )

    leaf_result = _fake_leaf_result(package_name="demo-ontology")
    observed: dict[str, object] = {}
    config_commit = workspace_provider._OntologyConfigCommitResult(  # noqa: SLF001
        ontology_config_id=uuid4(),
        config_commit_id=uuid4(),
        config_head_commit_id=uuid4(),
        config_object_instance_graph_commit_id=uuid4(),
        commit_perf_ms={},
    )

    async def _fake_leaf_materialization(**kwargs: object) -> object:
        observed["leaf_aware_toml_path"] = kwargs["aware_toml_path"]
        return leaf_result

    async def _unexpected_language_bridge(
        *,
        request: object,
        leaf_result: object,
    ) -> object:
        raise AssertionError("semantic render profiles must not run language outputs")

    async def _fake_commit_config_snapshot(**kwargs: object) -> object:
        observed["config_commit_leaf_result"] = kwargs["leaf_result"]
        return config_commit

    async def _fake_commit_snapshot(**kwargs: object) -> object:
        observed["commit_leaf_result"] = kwargs["leaf_result"]
        observed["package_ontology_config_commit"] = kwargs["ontology_config_commit"]
        return workspace_provider._OntologyPackageCommitResult(  # noqa: SLF001
            ontology_package_id=uuid4(),
            package_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            package_object_instance_graph_commit_id=uuid4(),
            commit_perf_ms={},
        )

    monkeypatch.setattr(
        workspace_provider.meta_service,
        "materialize_object_config_graph_package_leaf_from_manifest",
        _fake_leaf_materialization,
    )
    monkeypatch.setattr(
        workspace_provider.meta_workspace_provider,
        "materialize_object_config_graph_package_leaf_language_outputs",
        _unexpected_language_bridge,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_commit_ontology_config_snapshot",
        _fake_commit_config_snapshot,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_commit_ontology_package_snapshot",
        _fake_commit_snapshot,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_external_object_config_graphs_for_request",
        lambda **_: (),
    )
    _patch_no_runtime_graph_closure(
        monkeypatch=monkeypatch,
        workspace_provider=workspace_provider,
    )
    monkeypatch.setattr(
        workspace_provider,
        "find_meta_graph_projection_hash_by_name",
        _fake_ontology_projection_hash_by_name,
    )
    _patch_ontology_runtime_bundle_writer(
        monkeypatch=monkeypatch,
        workspace_provider=workspace_provider,
    )

    result = await workspace_provider.materialize(
        SemanticPackageMaterializationRequest(
            runtime=object(),
            index=object(),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            manifest_path=ontology_toml_path,
            context={
                SEMANTIC_MATERIALIZATION_LIFECYCLE_PROFILE_CONTEXT_KEY: {
                    "schema": (
                        "aware.workspace.semantic_materialization."
                        "lifecycle_profile.v1"
                    ),
                    "render_profile": "semantic",
                    "requested_stages": (
                        "semantic_status",
                        "semantic_plan",
                        "semantic_apply",
                    ),
                    "execution_mode": "stage_gated",
                }
            },
        )
    )

    assert observed["leaf_aware_toml_path"] == source_manifest_path.resolve()
    assert observed["config_commit_leaf_result"] is leaf_result
    assert observed["commit_leaf_result"] is leaf_result
    assert observed["package_ontology_config_commit"] is config_commit
    assert result.details["materialized_language_package_count"] == 0
    assert _ontology_runtime_artifact_set_receipt(
        result.details["artifact_ownership_receipts"]
    )
    assert result.details["language_post_step_receipts"] == ()
    assert result.details["compile_parity_receipts"] == ()
    assert result.details["language_materialization_status"] == "skipped"
    assert (
        result.details["language_materialization_skip_reason"]
        == "render_profile_not_compile_parity"
    )
    bridge = cast(
        dict[str, object],
        result.details["meta_language_materialization_bridge"],
    )
    assert bridge["provider_key"] == "aware_meta"
    assert bridge["status"] == "skipped"
    assert bridge["render_profile"] == "semantic"
    assert bridge["materialized_language_package_count"] == 0


@pytest.mark.asyncio
async def test_ontology_provider_bridges_language_outputs_for_reuse_without_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider

    workspace_root = tmp_path / "workspace"
    module_root = workspace_root / "modules" / "demo"
    ontology_root = module_root / "structure" / "ontology"
    ontology_root.mkdir(parents=True)
    ontology_toml_path = module_root / "aware.ontology.toml"
    source_manifest_path = ontology_root / "aware.toml"
    ontology_toml_path.write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'source_manifest = "structure/ontology/aware.toml"',
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
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )

    leaf_result = _fake_leaf_result(package_name="demo-ontology")
    leaf_after = _fake_leaf_result(package_name="demo-ontology")
    leaf_result.semantic_commit_strategy = "fingerprint_reuse"
    observed: dict[str, object] = {}
    config_commit = workspace_provider._OntologyConfigCommitResult(  # noqa: SLF001
        ontology_config_id=uuid4(),
        config_commit_id=uuid4(),
        config_head_commit_id=uuid4(),
        config_object_instance_graph_commit_id=uuid4(),
        commit_perf_ms={},
    )

    async def _fake_leaf_materialization(**_: object) -> object:
        return leaf_result

    async def _fake_language_bridge(
        *,
        request: object,
        leaf_result: object,
    ) -> object:
        observed["bridge_request_manifest"] = getattr(request, "manifest_path")
        observed["bridge_leaf_result"] = leaf_result
        return SimpleNamespace(
            leaf_result=leaf_after,
            materialized_language_packages=(
                {
                    "package_name": "demo-ontology",
                    "language": "python",
                    "package_root": "modules/demo/structure/ontology/python",
                },
            ),
            details={
                "artifact_ownership_receipts": (
                    {
                        "producer_provider_key": "aware_meta",
                        "producer_key": (
                            "aware_meta.object_config_graph." "language_materialization"
                        ),
                        "artifact_family": "ocg_language_materialization",
                        "artifact_role": "source_code",
                        "output_key": "generated_language_files",
                    },
                ),
                "generated_code_package_deltas": (),
                "language_materialization_code_package_deltas": (),
                "materialized_language_packages": (
                    {
                        "package_name": "demo-ontology",
                        "language": "python",
                    },
                ),
                "materialized_language_package_count": 1,
                "compile_parity_receipts": (
                    {
                        "receipt_kind": ("meta_workspace_materialize_compile_parity"),
                        "status": "compile_equivalent",
                    },
                ),
            },
        )

    async def _fake_commit_config_snapshot(**kwargs: object) -> object:
        observed["config_commit_leaf_result"] = kwargs["leaf_result"]
        return config_commit

    async def _fake_commit_snapshot(**kwargs: object) -> object:
        observed["commit_leaf_result"] = kwargs["leaf_result"]
        observed["package_ontology_config_commit"] = kwargs["ontology_config_commit"]
        return workspace_provider._OntologyPackageCommitResult(  # noqa: SLF001
            ontology_package_id=uuid4(),
            package_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            package_object_instance_graph_commit_id=uuid4(),
            commit_perf_ms={},
        )

    monkeypatch.setattr(
        workspace_provider.meta_service,
        "materialize_object_config_graph_package_leaf_from_manifest",
        _fake_leaf_materialization,
    )
    monkeypatch.setattr(
        workspace_provider.meta_workspace_provider,
        "materialize_object_config_graph_package_leaf_language_outputs",
        _fake_language_bridge,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_commit_ontology_config_snapshot",
        _fake_commit_config_snapshot,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_commit_ontology_package_snapshot",
        _fake_commit_snapshot,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_external_object_config_graphs_for_request",
        lambda **_: (),
    )
    _patch_no_runtime_graph_closure(
        monkeypatch=monkeypatch,
        workspace_provider=workspace_provider,
    )
    monkeypatch.setattr(
        workspace_provider,
        "find_meta_graph_projection_hash_by_name",
        _fake_ontology_projection_hash_by_name,
    )
    _patch_ontology_runtime_bundle_writer(
        monkeypatch=monkeypatch,
        workspace_provider=workspace_provider,
    )

    result = await workspace_provider.materialize(
        SemanticPackageMaterializationRequest(
            runtime=object(),
            index=object(),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            manifest_path=ontology_toml_path,
            context={},
        )
    )

    assert observed["bridge_request_manifest"] == source_manifest_path.resolve()
    assert observed["bridge_leaf_result"] is leaf_result
    assert observed["config_commit_leaf_result"] is leaf_after
    assert observed["commit_leaf_result"] is leaf_after
    assert observed["package_ontology_config_commit"] is config_commit
    assert result.details["artifact_ownership_receipts"]
    assert result.details["materialized_language_package_count"] == 1
    assert result.details["compile_parity_receipts"]
    bridge = cast(
        dict[str, object],
        result.details["meta_language_materialization_bridge"],
    )
    assert bridge["status"] == "completed"


@pytest.mark.asyncio
async def test_ontology_provider_skips_language_outputs_for_complete_reuse_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider

    workspace_root = tmp_path / "workspace"
    module_root = workspace_root / "modules" / "demo"
    ontology_root = module_root / "structure" / "ontology"
    ontology_root.mkdir(parents=True)
    ontology_toml_path = module_root / "aware.ontology.toml"
    source_manifest_path = ontology_root / "aware.toml"
    ontology_toml_path.write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'source_manifest = "structure/ontology/aware.toml"',
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
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )

    leaf_result = _fake_leaf_result(package_name="demo-ontology")
    leaf_result.semantic_commit_strategy = "fingerprint_reuse"
    leaf_result.object_config_graph_package.language_materializations = (
        SimpleNamespace(
            materialized_packages=(
                SimpleNamespace(
                    code_package_id=uuid4(),
                    object_config_graph_object_instance_graph_commit_id=uuid4(),
                    code_package_object_instance_graph_commit_id=uuid4(),
                    status="materialized",
                ),
            ),
        ),
    )
    observed: dict[str, object] = {}
    config_commit = workspace_provider._OntologyConfigCommitResult(  # noqa: SLF001
        ontology_config_id=uuid4(),
        config_commit_id=uuid4(),
        config_head_commit_id=uuid4(),
        config_object_instance_graph_commit_id=uuid4(),
        commit_perf_ms={},
    )

    async def _fake_leaf_materialization(**_: object) -> object:
        return leaf_result

    async def _unexpected_language_bridge(**_: object) -> object:
        raise AssertionError(
            "language bridge should not run for complete fingerprint reuse"
        )

    async def _fake_commit_config_snapshot(**kwargs: object) -> object:
        observed["config_commit_leaf_result"] = kwargs["leaf_result"]
        return config_commit

    async def _fake_commit_snapshot(**kwargs: object) -> object:
        observed["commit_leaf_result"] = kwargs["leaf_result"]
        observed["package_ontology_config_commit"] = kwargs["ontology_config_commit"]
        return workspace_provider._OntologyPackageCommitResult(  # noqa: SLF001
            ontology_package_id=uuid4(),
            package_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            package_object_instance_graph_commit_id=uuid4(),
            commit_perf_ms={},
        )

    monkeypatch.setattr(
        workspace_provider.meta_service,
        "materialize_object_config_graph_package_leaf_from_manifest",
        _fake_leaf_materialization,
    )
    monkeypatch.setattr(
        workspace_provider.meta_workspace_provider,
        "materialize_object_config_graph_package_leaf_language_outputs",
        _unexpected_language_bridge,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_commit_ontology_config_snapshot",
        _fake_commit_config_snapshot,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_commit_ontology_package_snapshot",
        _fake_commit_snapshot,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_external_object_config_graphs_for_request",
        lambda **_: (),
    )
    _patch_no_runtime_graph_closure(
        monkeypatch=monkeypatch,
        workspace_provider=workspace_provider,
    )
    monkeypatch.setattr(
        workspace_provider,
        "find_meta_graph_projection_hash_by_name",
        _fake_ontology_projection_hash_by_name,
    )
    _patch_ontology_runtime_bundle_writer(
        monkeypatch=monkeypatch,
        workspace_provider=workspace_provider,
    )

    result = await workspace_provider.materialize(
        SemanticPackageMaterializationRequest(
            runtime=object(),
            index=object(),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            manifest_path=ontology_toml_path,
            context={},
        )
    )

    assert observed["config_commit_leaf_result"] is leaf_result
    assert observed["commit_leaf_result"] is leaf_result
    assert observed["package_ontology_config_commit"] is config_commit
    assert result.details["language_materialization_status"] == "skipped"
    assert (
        result.details["language_materialization_skip_reason"] == "semantic_leaf_reused"
    )
    assert result.details["language_materialization_reuse_strategy"] == (
        "fingerprint_reuse"
    )
    assert result.details["language_artifact_completeness_status"] == "complete"
    assert result.details["language_artifact_completeness_reason"] == (
        "materialized_language_packages_present"
    )
    assert result.details["language_artifact_completeness_target_count"] == 1
    assert result.details["language_artifact_completeness_package_count"] == 1
    bridge = cast(
        dict[str, object],
        result.details["meta_language_materialization_bridge"],
    )
    assert bridge["status"] == "skipped"
    assert bridge["render_profile"] == "compile_parity"


@pytest.mark.asyncio
async def test_ontology_provider_delta_delegates_to_meta_ocg_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_code_ontology.code.code_plan import (
        CodePackageDelta,
        CodePackageDeltaKind,
        CodePackageDeltaPath,
        CodePackagePathRole,
    )

    workspace_root = tmp_path / "workspace"
    module_root = workspace_root / "modules" / "demo"
    ontology_root = module_root / "structure" / "ontology"
    ontology_root.mkdir(parents=True)
    ontology_toml_path = module_root / "aware.ontology.toml"
    source_manifest_path = ontology_root / "aware.toml"
    ontology_toml_path.write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'source_manifest = "structure/ontology/aware.toml"',
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
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )
    observed: dict[str, object] = {}

    async def _fake_meta_delta(*, request: object) -> dict[str, object]:
        observed["request"] = request
        return {
            "contract_version": (
                "aware.workspace.semantic-materialization." "provider-delta-result.v1"
            ),
            "status": "succeeded",
            "package": getattr(request, "package").__dict__,
            "semantic_contract": getattr(request, "semantic_contract").__dict__,
            "current_delta_fingerprint": getattr(
                request,
                "current_delta_fingerprint",
            ),
            "applied_semantic_keys": ["ocg:aware_demo"],
            "skipped_semantic_keys": [],
            "stale_semantic_keys": [],
            "details": {"provider_delta_operation_execution": {"status": "ok"}},
            "bundle_package": {
                "semantic_package_id": "ocg-package-id",
                "semantic_branch_id": "branch-id",
                "semantic_object_instance_graph_commit_id": ("ocg-package-oig"),
            },
        }

    monkeypatch.setattr(
        workspace_provider.meta_workspace_provider,
        "materialize_delta",
        _fake_meta_delta,
    )
    request = SimpleNamespace(
        package=SimpleNamespace(
            package_name="demo-ontology",
            workspace_manifest_kind="ontology",
            manifest_path=ontology_toml_path.as_posix(),
            source_code_package_id="source-code-package-id",
        ),
        semantic_contract=SimpleNamespace(
            module="aware_ontology.semantic_contract",
            provider_key="aware_ontology",
            role="aware_ontology.provider",
            name="aware.semantic_provider",
        ),
        current_delta_fingerprint="sha256:demo",
        code_package_delta=CodePackageDelta(
            package_name="demo-ontology",
            package_root="modules/demo",
            sources_root=".",
            manifest_relative_path="modules/demo/aware.ontology.toml",
            authority_kind="local_fs_view",
            source_revision_id="test-current",
            paths=[
                CodePackageDeltaPath(
                    relative_path="structure/ontology/aware/home/model.aware",
                    kind=CodePackageDeltaKind.update,
                    content_text="class Room { name String }\n",
                    content_plan=None,
                    before_hash=None,
                    after_hash=None,
                    size_bytes=None,
                    language=CodeLanguage.aware,
                    is_structural=True,
                    path_role=CodePackagePathRole.authored_source,
                    production=None,
                )
            ],
            production=None,
            warnings=[],
        ),
        previous_materialization_evidence={
            "materialization": {
                "details": {
                    "semantic_branch_id": "branch-id",
                    "source_code_package_id": "source-code-package-id",
                    "source_code_package_object_instance_graph_commit_id": (
                        "source-oig"
                    ),
                    "object_config_graph_id": "ocg-id",
                    "object_config_graph_object_instance_graph_commit_id": ("ocg-oig"),
                    "object_config_graph_head_commit_id": "ocg-head",
                    "object_config_graph_package_id": "ocg-package-id",
                    "object_config_graph_package_commit_id": ("ocg-package-commit"),
                    "object_config_graph_package_head_commit_id": ("ocg-package-head"),
                    "object_config_graph_package_object_instance_graph_commit_id": (
                        "ocg-package-oig"
                    ),
                    "materialization_index_receipts": [
                        {
                            "lane_projection_hashes": {
                                "object_config_graph": "ocg-projection",
                                "object_config_graph_package": (
                                    "ocg-package-projection"
                                ),
                            },
                        },
                    ],
                },
            },
        },
        baseline_ref={
            "semantic_branch_id": "branch-id",
            "semantic_projection_name": "OntologyPackage",
            "semantic_projection_hash": "ontology-projection",
            "source_object_instance_graph_commit_id": "source-oig",
        },
        context={
            "workspace_root": workspace_root.as_posix(),
            "required_projection_names": ("OntologyPackage",),
            "runtime_ontology_package_names": ("ontology-ontology",),
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY: {
                "provider_key": "aware_ontology",
                "semantic_owner": "aware_ontology.provider",
            },
        },
    )

    result = await workspace_provider.materialize_delta(request=request)

    meta_request = cast(object, observed["request"])
    assert getattr(meta_request.package, "manifest_path") == (
        source_manifest_path.resolve().as_posix()
    )
    assert getattr(meta_request.semantic_contract, "provider_key") == "aware_meta"
    assert getattr(meta_request.semantic_contract, "role") == "aware_meta.provider"
    assert meta_request.baseline_ref["semantic_projection_name"] == (
        "ObjectConfigGraph"
    )
    assert meta_request.baseline_ref["semantic_projection_hash"] == ("ocg-projection")
    assert meta_request.baseline_ref["semantic_package_id"] == "ocg-package-id"
    assert (
        meta_request.baseline_ref["semantic_object_instance_graph_commit_id"]
        == "ocg-head"
    )
    assert (
        meta_request.baseline_ref["semantic_package_object_instance_graph_commit_id"]
        == "ocg-package-oig"
    )
    assert meta_request.code_package_delta.package_root == (
        "modules/demo/structure/ontology"
    )
    assert meta_request.code_package_delta.sources_root == "aware"
    assert meta_request.code_package_delta.manifest_relative_path == "aware.toml"
    assert meta_request.code_package_delta.paths[0].relative_path == (
        "aware/home/model.aware"
    )
    durable_inputs = meta_request.context[
        SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY
    ]
    assert durable_inputs["provider_key"] == "aware_meta"
    assert durable_inputs["semantic_projection_hash"] == "ocg-projection"
    assert "OntologyPackage" not in meta_request.context["required_projection_names"]
    assert "ObjectConfigGraph" in meta_request.context["required_projection_names"]
    assert "ontology-ontology" not in (
        meta_request.context["runtime_ontology_package_names"]
    )
    assert "meta-ontology" in meta_request.context["runtime_ontology_package_names"]
    assert result["package"]["manifest_path"] == ontology_toml_path.as_posix()
    assert result["semantic_contract"]["provider_key"] == "aware_ontology"
    assert result["details"]["ontology_provider_delta_bridge"]["status"] == (
        "delegated_to_meta"
    )


@pytest.mark.asyncio
async def test_ontology_provider_delta_bridge_passes_seeded_meta_baseline_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider
    from aware_code_ontology.code.code_enums import CodeLanguage
    from aware_code_ontology.code.code_plan import (
        CodePackageDelta,
        CodePackageDeltaKind,
        CodePackageDeltaPath,
        CodePackagePathRole,
    )
    from aware_meta.runtime.package_index import stable_meta_runtime_package_branch_id

    workspace_root = tmp_path / "workspace"
    module_root = workspace_root / "modules" / "demo"
    ontology_root = module_root / "structure" / "ontology"
    ontology_root.mkdir(parents=True)
    ontology_toml_path = module_root / "aware.ontology.toml"
    source_manifest_path = ontology_root / "aware.toml"
    ontology_toml_path.write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'source_manifest = "structure/ontology/aware.toml"',
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
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )
    expected_branch_id = stable_meta_runtime_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=source_manifest_path,
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
    )
    expected_package_id = "ocg-package-id"
    observed: dict[str, object] = {}

    async def _fake_meta_delta(*, request: object) -> dict[str, object]:
        observed["request"] = request
        return {
            "contract_version": (
                "aware.workspace.semantic-materialization." "provider-delta-result.v1"
            ),
            "status": "succeeded",
            "package": getattr(request, "package").__dict__,
            "semantic_contract": getattr(request, "semantic_contract").__dict__,
            "current_delta_fingerprint": getattr(
                request,
                "current_delta_fingerprint",
            ),
            "applied_semantic_keys": ["ocg:aware_demo"],
            "skipped_semantic_keys": [],
            "stale_semantic_keys": [],
            "details": {"provider_delta_operation_execution": {"status": "ok"}},
            "bundle_package": {
                "semantic_package_id": str(expected_package_id),
                "semantic_branch_id": str(expected_branch_id),
                "semantic_object_instance_graph_commit_id": "semantic-oig",
            },
        }

    monkeypatch.setattr(
        workspace_provider.meta_workspace_provider,
        "materialize_delta",
        _fake_meta_delta,
    )
    request = SimpleNamespace(
        package=SimpleNamespace(
            package_name="demo-ontology",
            workspace_manifest_kind="ontology",
            manifest_path=ontology_toml_path.as_posix(),
            source_code_package_id="source-code-package-id",
        ),
        semantic_contract=SimpleNamespace(
            module="aware_ontology.semantic_contract",
            provider_key="aware_ontology",
            role="aware_ontology.provider",
            name="aware.semantic_provider",
        ),
        current_delta_fingerprint="sha256:demo",
        code_package_delta=CodePackageDelta(
            package_name="demo-ontology",
            package_root="modules/demo",
            sources_root=".",
            manifest_relative_path="modules/demo/aware.ontology.toml",
            authority_kind="local_fs_view",
            source_revision_id="test-current",
            paths=[
                CodePackageDeltaPath(
                    relative_path="structure/ontology/aware/home/model.aware",
                    kind=CodePackageDeltaKind.update,
                    content_text="class Room { name String }\n",
                    content_plan=None,
                    before_hash=None,
                    after_hash=None,
                    size_bytes=None,
                    language=CodeLanguage.aware,
                    is_structural=True,
                    path_role=CodePackagePathRole.authored_source,
                    production=None,
                )
            ],
            production=None,
            warnings=[],
        ),
        previous_materialization_evidence={
            "materialization": {
                "details": {
                    "source_code_package_id": "source-code-package-id",
                    "source_code_package_object_instance_graph_commit_id": (
                        "previous-source-oig"
                    ),
                    "object_config_graph_id": "ocg-id",
                    "object_config_graph_object_instance_graph_commit_id": ("ocg-oig"),
                    "object_config_graph_head_commit_id": "ocg-head",
                    "object_config_graph_package_id": expected_package_id,
                    "object_config_graph_package_commit_id": ("ocg-package-commit"),
                    "object_config_graph_package_head_commit_id": ("ocg-package-head"),
                    "object_config_graph_package_object_instance_graph_commit_id": (
                        "ocg-package-oig"
                    ),
                    "materialization_index_receipts": [
                        {
                            "lane_projection_hashes": {
                                "object_config_graph": "ocg-projection",
                                "object_config_graph_package": (
                                    "ocg-package-projection"
                                ),
                            },
                        },
                    ],
                },
            },
        },
        baseline_ref=None,
        baseline_source_object_instance_graph_commit_id=None,
        baseline_semantic_object_instance_graph_commit_id=None,
        baseline_semantic_root_object_instance_graph_commit_id=None,
        provider_delta_lane_state={
            "status": "empty_lane",
            "package": {"package_name": "demo-ontology"},
            "source_code_package_id": "source-code-package-id",
            "source_object_instance_graph_commit_id": "seed-source-oig",
        },
        context={
            "workspace_root": workspace_root.as_posix(),
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY: {
                "provider_key": "aware_ontology",
                "semantic_owner": "aware_ontology.provider",
            },
        },
        execute_provider_delta_materialization=True,
    )

    await workspace_provider.materialize_delta(request=request)

    meta_request = cast(object, observed["request"])
    assert meta_request.provider_delta_lane_state["status"] == "empty_lane"
    assert meta_request.baseline_ref["semantic_branch_id"] == str(expected_branch_id)
    assert meta_request.baseline_ref["semantic_package_id"] == str(expected_package_id)
    assert meta_request.baseline_ref["source_object_instance_graph_commit_id"] == (
        "seed-source-oig"
    )
    assert meta_request.baseline_source_object_instance_graph_commit_id == (
        "seed-source-oig"
    )
    assert meta_request.baseline_semantic_object_instance_graph_commit_id
    assert meta_request.baseline_semantic_root_object_instance_graph_commit_id


@pytest.mark.asyncio
async def test_ontology_provider_delta_resolves_meta_baseline_from_package_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider

    workspace_root = tmp_path / "workspace"
    module_root = workspace_root / "modules" / "demo"
    ontology_root = module_root / "structure" / "ontology"
    ontology_root.mkdir(parents=True)
    ontology_toml_path = module_root / "aware.ontology.toml"
    source_manifest_path = ontology_root / "aware.toml"
    ontology_toml_path.write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'source_manifest = "structure/ontology/aware.toml"',
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
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )
    package_id = uuid4()
    root_id = uuid4()
    package_head_commit_id = uuid4()
    package_oig_commit_id = uuid4()
    root_head_commit_id = uuid4()
    root_oig_commit_id = uuid4()
    source_oig_commit_id = uuid4()
    observed: dict[str, object] = {}

    async def _fake_meta_delta(*, request: object) -> dict[str, object]:
        observed["request"] = request
        return {
            "contract_version": (
                "aware.workspace.semantic-materialization." "provider-delta-result.v1"
            ),
            "status": "succeeded",
            "package": getattr(request, "package").__dict__,
            "semantic_contract": getattr(request, "semantic_contract").__dict__,
            "current_delta_fingerprint": "sha256:demo",
            "applied_semantic_keys": ["ocg:aware_demo"],
            "skipped_semantic_keys": [],
            "stale_semantic_keys": [],
            "details": {},
        }

    index_entry = SimpleNamespace(
        semantic_key="ocg_package:demo-ontology",
        object_kind="object_config_graph_package",
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        manifest_path=source_manifest_path.resolve(),
        object_id=package_id,
        entity_id=None,
        graph_semantic_key=None,
        parent_semantic_key=None,
        owner_semantic_key=None,
        node_key=None,
        attribute_name=None,
        source_refs=("aware.toml",),
        object_config_graph_id=root_id,
        object_config_graph_hash=None,
        semantic_package_head_commit_id=package_head_commit_id,
        semantic_package_object_instance_graph_commit_id=package_oig_commit_id,
        semantic_root_head_commit_id=root_head_commit_id,
        semantic_root_object_instance_graph_commit_id=root_oig_commit_id,
        source_head_commit_id=None,
        source_object_instance_graph_commit_id=source_oig_commit_id,
        runtime_delta_fingerprint="sha256:package",
        evidence_source="test",
        payload={
            "semantic_key": "ocg_package:demo-ontology",
            "object_kind": "object_config_graph_package",
        },
    )
    monkeypatch.setattr(
        workspace_provider,
        "load_meta_runtime_package_projection_index",
        lambda *, aware_root: SimpleNamespace(
            semantic_objects_by_key={
                "ocg_package:demo-ontology": index_entry,
            },
        ),
    )
    monkeypatch.setattr(
        workspace_provider.meta_workspace_provider,
        "materialize_delta",
        _fake_meta_delta,
    )
    request = SimpleNamespace(
        package=SimpleNamespace(
            package_name="demo-ontology",
            workspace_manifest_kind="ontology",
            manifest_path=ontology_toml_path.as_posix(),
            source_code_package_id="source-code-package-id",
        ),
        semantic_contract=SimpleNamespace(
            module="aware_ontology.semantic_contract",
            provider_key="aware_ontology",
            role="aware_ontology.provider",
            name="aware.semantic_provider",
        ),
        current_delta_fingerprint="sha256:demo",
        code_package_delta=None,
        previous_materialization_evidence={
            "evidence_source": "workspace_build_materialization_receipt",
            "baseline_ref": {
                "semantic_package_id": "ontology-package-id",
                "semantic_root_id": "ontology-package-id",
            },
        },
        baseline_ref={
            "semantic_branch_id": "branch-id",
            "semantic_projection_name": "OntologyPackage",
            "semantic_projection_hash": "ontology-projection",
            "source_code_package_id": "source-code-package-id",
            "source_object_instance_graph_commit_id": str(source_oig_commit_id),
        },
        context={
            "workspace_root": workspace_root.as_posix(),
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY: {
                "provider_key": "aware_ontology",
                "semantic_owner": "aware_ontology.provider",
            },
        },
    )

    await workspace_provider.materialize_delta(request=request)

    meta_request = cast(object, observed["request"])
    assert meta_request.baseline_ref["semantic_package_id"] == str(package_id)
    assert meta_request.baseline_ref["semantic_root_id"] == str(root_id)
    assert meta_request.baseline_ref["semantic_object_instance_graph_commit_id"] == str(
        root_head_commit_id
    )
    assert meta_request.baseline_ref[
        "semantic_package_object_instance_graph_commit_id"
    ] == str(package_oig_commit_id)
    assert meta_request.baseline_ref[
        "semantic_root_object_instance_graph_commit_id"
    ] == str(root_oig_commit_id)
    assert meta_request.previous_materialization_evidence[
        "baseline_semantic_object_index"
    ]["ocg_package:demo-ontology"]["object_id"] == str(package_id)
    durable_inputs = meta_request.context[
        SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY
    ]
    assert durable_inputs["semantic_package_id"] == str(package_id)
    assert durable_inputs["semantic_root_id"] == str(root_id)


@pytest.mark.asyncio
async def test_ontology_provider_delta_prefers_latest_ocg_baseline_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider

    workspace_root = tmp_path / "workspace"
    module_root = workspace_root / "modules" / "demo"
    ontology_root = module_root / "structure" / "ontology"
    ontology_root.mkdir(parents=True)
    ontology_toml_path = module_root / "aware.ontology.toml"
    source_manifest_path = ontology_root / "aware.toml"
    ontology_toml_path.write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'source_manifest = "structure/ontology/aware.toml"',
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
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "version_number = 1",
                "",
                "[build]",
                'environment_slug = "demo"',
                'sources_dir = "aware"',
                "",
            )
        ),
        encoding="utf-8",
    )
    stale_domain_commit_id = uuid4()
    latest_domain_commit_id = uuid4()
    latest_oig_commit_id = uuid4()
    latest_package_id = uuid4()
    latest_root_id = uuid4()
    observed: dict[str, object] = {}

    async def _fake_meta_delta(*, request: object) -> dict[str, object]:
        observed["request"] = request
        return {
            "contract_version": (
                "aware.workspace.semantic-materialization." "provider-delta-result.v1"
            ),
            "status": "succeeded",
            "package": getattr(request, "package").__dict__,
            "semantic_contract": getattr(request, "semantic_contract").__dict__,
            "current_delta_fingerprint": "sha256:demo",
            "applied_semantic_keys": ["ocg:aware_demo"],
            "skipped_semantic_keys": [],
            "stale_semantic_keys": [],
            "details": {},
        }

    monkeypatch.setattr(
        workspace_provider.meta_workspace_provider,
        "materialize_delta",
        _fake_meta_delta,
    )
    request = SimpleNamespace(
        package=SimpleNamespace(
            package_name="demo-ontology",
            workspace_manifest_kind="ontology",
            manifest_path=ontology_toml_path.as_posix(),
            source_code_package_id="source-code-package-id",
        ),
        semantic_contract=SimpleNamespace(
            module="aware_ontology.semantic_contract",
            provider_key="aware_ontology",
            role="aware_ontology.provider",
            name="aware.semantic_provider",
        ),
        current_delta_fingerprint="sha256:demo",
        code_package_delta=None,
        previous_materialization_evidence={
            "materialization": {
                "details": {
                    "semantic_branch_id": "branch-id",
                    "source_code_package_id": "source-code-package-id",
                    "source_code_package_object_instance_graph_commit_id": (
                        "source-oig"
                    ),
                    "object_config_graph_id": "stale-root-id",
                    "object_config_graph_head_commit_id": str(stale_domain_commit_id),
                    "object_config_graph_object_instance_graph_commit_id": (
                        "stale-root-oig-commit"
                    ),
                    "object_config_graph_package_id": "stale-package-id",
                    "object_config_graph_package_head_commit_id": (
                        "stale-package-head"
                    ),
                    "object_config_graph_package_object_instance_graph_commit_id": (
                        "stale-package-oig-commit"
                    ),
                    "materialization_index_receipts": [
                        {
                            "lane_projection_hashes": {
                                "object_config_graph": "stale-ocg-projection",
                            },
                        },
                    ],
                },
            },
        },
        baseline_ref={
            "source": "workspace_provider_delta_materialization_receipt",
            "semantic_branch_id": "branch-id",
            "semantic_projection_name": "ObjectConfigGraph",
            "semantic_projection_hash": "latest-ocg-projection",
            "semantic_package_id": str(latest_package_id),
            "semantic_package_commit_id": str(latest_domain_commit_id),
            "semantic_head_commit_id": str(latest_domain_commit_id),
            "semantic_object_instance_graph_commit_id": str(latest_oig_commit_id),
            "semantic_root_id": str(latest_root_id),
            "semantic_root_object_instance_graph_commit_id": str(latest_oig_commit_id),
            "source_code_package_id": "source-code-package-id",
            "source_object_instance_graph_commit_id": "source-oig",
        },
        context={
            "workspace_root": workspace_root.as_posix(),
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY: {
                "provider_key": "aware_ontology",
                "semantic_owner": "aware_ontology.provider",
            },
        },
    )

    await workspace_provider.materialize_delta(request=request)

    meta_request = cast(object, observed["request"])
    assert meta_request.baseline_ref["semantic_projection_hash"] == (
        "latest-ocg-projection"
    )
    assert meta_request.baseline_ref["semantic_package_id"] == (str(latest_package_id))
    assert meta_request.baseline_ref["semantic_package_commit_id"] == (
        str(latest_domain_commit_id)
    )
    assert meta_request.baseline_ref["semantic_object_instance_graph_commit_id"] == str(
        latest_domain_commit_id
    )
    assert meta_request.baseline_ref["semantic_root_commit_id"] == (
        str(latest_domain_commit_id)
    )
    assert meta_request.baseline_ref[
        "semantic_root_object_instance_graph_commit_id"
    ] == str(latest_oig_commit_id)
    assert meta_request.baseline_ref[
        "semantic_package_object_instance_graph_commit_id"
    ] == str(latest_oig_commit_id)
    durable_inputs = meta_request.context[
        SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY
    ]
    assert durable_inputs["semantic_object_instance_graph_commit_id"] == (
        str(latest_domain_commit_id)
    )
    assert durable_inputs["semantic_package_commit_id"] == (
        str(latest_domain_commit_id)
    )
    assert str(stale_domain_commit_id) not in {
        meta_request.baseline_ref["semantic_object_instance_graph_commit_id"],
        durable_inputs["semantic_object_instance_graph_commit_id"],
    }


@pytest.mark.asyncio
async def test_ontology_config_snapshot_commit_uses_meta_runtime_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider

    actor_id = uuid4()
    branch_id = uuid4()
    projection_hash = "ontology-config-projection"
    opgi_id = uuid4()
    before_oig = SimpleNamespace(hash="sha256:before")
    after_oig = SimpleNamespace(hash="sha256:after")
    changes = (SimpleNamespace(kind="create"),)
    observed: dict[str, object] = {}
    index = SimpleNamespace(
        opg_by_hash={
            projection_hash: SimpleNamespace(id=uuid4()),
        },
        ocg=SimpleNamespace(id=uuid4()),
        class_configs_by_id={},
        relationships_by_id={},
        attribute_configs_by_id={},
    )
    source = workspace_provider._OntologyPackageSource(  # noqa: SLF001
        ontology_toml_path=Path("modules/demo/aware.ontology.toml"),
        source_manifest_path=Path("modules/demo/structure/ontology/aware.toml"),
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        version_number=1,
        title="Demo",
        description=None,
        manifest_relative_path="modules/demo/structure/ontology/aware.toml",
        package_root="modules/demo",
        sources_root="modules/demo/structure/ontology/aware",
    )
    leaf_result = _fake_leaf_result(package_name="demo-ontology")

    def _fake_resolve_meta_graph_ocgi_opgi(**kwargs: object) -> tuple[None, object]:
        observed["graph_identity"] = kwargs
        return None, SimpleNamespace(id=opgi_id)

    def _fake_build_rooted_object_instance_graph_base(**kwargs: object) -> object:
        observed["build_rooted_oig"] = kwargs
        return before_oig

    def _fake_build_oig_changes(**kwargs: object) -> object:
        observed["changes"] = kwargs
        return changes

    def _fake_materialize_meta_oig_post(**kwargs: object) -> object:
        observed["oig_post"] = kwargs
        return after_oig

    def _fake_resolve_meta_author_id(value: object) -> object:
        observed.setdefault("authors", []).append(value)
        return actor_id

    class _FakeCommitter:
        async def commit(self, **kwargs: object) -> object:
            observed["commit"] = kwargs
            return SimpleNamespace(
                commit=SimpleNamespace(id=uuid4()),
                object_instance_graph_identity_id=kwargs[
                    "object_instance_graph_identity_id"
                ],
            )

        def last_commit_perf_profile_snapshot(self) -> dict[str, int]:
            return {"test_commit_ms": 1}

    monkeypatch.setattr(
        workspace_provider,
        "resolve_meta_graph_ocgi_opgi",
        _fake_resolve_meta_graph_ocgi_opgi,
    )
    monkeypatch.setattr(
        workspace_provider,
        "build_rooted_object_instance_graph_base",
        _fake_build_rooted_object_instance_graph_base,
    )
    monkeypatch.setattr(
        workspace_provider,
        "build_object_instance_graph_changes_from_orm_change_set",
        _fake_build_oig_changes,
    )
    monkeypatch.setattr(
        workspace_provider,
        "materialize_meta_oig_post",
        _fake_materialize_meta_oig_post,
    )
    monkeypatch.setattr(
        workspace_provider,
        "resolve_meta_author_id",
        _fake_resolve_meta_author_id,
    )
    monkeypatch.setattr(workspace_provider, "FSLaneCommitter", _FakeCommitter)

    result = await workspace_provider._commit_ontology_config_snapshot(  # noqa: SLF001
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        source=source,
        leaf_result=leaf_result,
    )

    graph_identity = cast(dict[str, object], observed["graph_identity"])
    assert graph_identity["index"] is index
    assert graph_identity["projection_hash"] == projection_hash
    oig_post = cast(dict[str, object], observed["oig_post"])
    assert oig_post["before_oig"] is before_oig
    assert oig_post["changes"] is changes
    changes_call = cast(dict[str, object], observed["changes"])
    change_set = changes_call["change_set"]
    config = next(iter(change_set.objects_by_id.values()))
    assert config.id == result.ontology_config_id
    assert config.object_config_graph_id == leaf_result.object_config_graph.id
    assert config.object_config_graph_object_instance_graph_commit_id == (
        leaf_result.object_config_graph_object_instance_graph_commit_id
    )
    assert config.schema_hash == leaf_result.object_config_graph.hash
    assert config.ontologies == []
    commit = cast(dict[str, object], observed["commit"])
    assert commit["root_object_id"] == result.ontology_config_id
    assert commit["graph_hash_pre"] == "sha256:before"
    assert commit["graph_hash_post"] == "sha256:after"
    assert commit["author_id"] == actor_id
    assert observed["authors"] == [actor_id]
    assert result.commit_perf_ms == {"test_commit_ms": 1}


@pytest.mark.asyncio
async def test_ontology_package_snapshot_commit_uses_meta_runtime_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.materialization import workspace_provider

    actor_id = uuid4()
    branch_id = uuid4()
    projection_hash = "ontology-package-projection"
    opgi_id = uuid4()
    before_oig = SimpleNamespace(hash="sha256:before")
    after_oig = SimpleNamespace(hash="sha256:after")
    changes = (SimpleNamespace(kind="create"),)
    observed: dict[str, object] = {}
    index = SimpleNamespace(
        opg_by_hash={
            projection_hash: SimpleNamespace(id=uuid4()),
        },
        ocg=SimpleNamespace(id=uuid4()),
        class_configs_by_id={},
        relationships_by_id={},
        attribute_configs_by_id={},
    )
    source = workspace_provider._OntologyPackageSource(  # noqa: SLF001
        ontology_toml_path=Path("modules/demo/aware.ontology.toml"),
        source_manifest_path=Path("modules/demo/structure/ontology/aware.toml"),
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        version_number=1,
        title="Demo",
        description=None,
        manifest_relative_path="modules/demo/structure/ontology/aware.toml",
        package_root="modules/demo",
        sources_root="modules/demo/structure/ontology/aware",
    )
    leaf_result = _fake_leaf_result(package_name="demo-ontology")
    config_commit = workspace_provider._OntologyConfigCommitResult(  # noqa: SLF001
        ontology_config_id=uuid4(),
        config_commit_id=uuid4(),
        config_head_commit_id=uuid4(),
        config_object_instance_graph_commit_id=uuid4(),
        commit_perf_ms={},
    )

    def _fake_resolve_meta_graph_ocgi_opgi(**kwargs: object) -> tuple[None, object]:
        observed["graph_identity"] = kwargs
        return None, SimpleNamespace(id=opgi_id)

    def _fake_build_rooted_object_instance_graph_base(**kwargs: object) -> object:
        observed["build_rooted_oig"] = kwargs
        return before_oig

    def _fake_build_oig_changes(**kwargs: object) -> object:
        observed["changes"] = kwargs
        return changes

    def _fake_materialize_meta_oig_post(**kwargs: object) -> object:
        observed["oig_post"] = kwargs
        return after_oig

    def _fake_resolve_meta_author_id(value: object) -> object:
        observed.setdefault("authors", []).append(value)
        return actor_id

    class _FakeCommitter:
        async def commit(self, **kwargs: object) -> object:
            observed["commit"] = kwargs
            return SimpleNamespace(
                commit=SimpleNamespace(id=uuid4()),
                object_instance_graph_identity_id=kwargs[
                    "object_instance_graph_identity_id"
                ],
            )

        def last_commit_perf_profile_snapshot(self) -> dict[str, int]:
            return {"test_commit_ms": 1}

    monkeypatch.setattr(
        workspace_provider,
        "resolve_meta_graph_ocgi_opgi",
        _fake_resolve_meta_graph_ocgi_opgi,
    )
    monkeypatch.setattr(
        workspace_provider,
        "build_rooted_object_instance_graph_base",
        _fake_build_rooted_object_instance_graph_base,
    )
    monkeypatch.setattr(
        workspace_provider,
        "build_object_instance_graph_changes_from_orm_change_set",
        _fake_build_oig_changes,
    )
    monkeypatch.setattr(
        workspace_provider,
        "materialize_meta_oig_post",
        _fake_materialize_meta_oig_post,
    )
    monkeypatch.setattr(
        workspace_provider,
        "resolve_meta_author_id",
        _fake_resolve_meta_author_id,
    )
    monkeypatch.setattr(workspace_provider, "FSLaneCommitter", _FakeCommitter)

    result = await workspace_provider._commit_ontology_package_snapshot(  # noqa: SLF001
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        source=source,
        leaf_result=leaf_result,
        ontology_config_commit=config_commit,
    )

    graph_identity = cast(dict[str, object], observed["graph_identity"])
    assert graph_identity["index"] is index
    assert graph_identity["projection_hash"] == projection_hash
    oig_post = cast(dict[str, object], observed["oig_post"])
    assert oig_post["before_oig"] is before_oig
    assert oig_post["changes"] is changes
    changes_call = cast(dict[str, object], observed["changes"])
    change_set = changes_call["change_set"]
    package = next(iter(change_set.objects_by_id.values()))
    assert package.ontology_config_id == config_commit.ontology_config_id
    assert package.ontology_config_object_instance_graph_commit_id == (
        config_commit.config_object_instance_graph_commit_id
    )
    commit = cast(dict[str, object], observed["commit"])
    assert commit["graph_hash_pre"] == "sha256:before"
    assert commit["graph_hash_post"] == "sha256:after"
    assert commit["author_id"] == actor_id
    assert observed["authors"] == [actor_id]
    assert result.commit_perf_ms == {"test_commit_ms": 1}


def _fake_leaf_result(*, package_name: str) -> object:
    function_edge_id = uuid4()
    function_id = uuid4()
    root_node_id = uuid4()
    root_class_config_id = uuid4()
    object_config_graph = SimpleNamespace(
        id=uuid4(),
        hash="sha256:demo-ocg",
        fqn_prefix="aware_demo",
        object_config_graph_nodes=(
            SimpleNamespace(
                class_config=SimpleNamespace(
                    class_config_function_configs=(
                        SimpleNamespace(
                            id=function_edge_id,
                            function_config=SimpleNamespace(id=function_id),
                        ),
                    )
                )
            ),
        ),
        object_projection_graphs=(
            SimpleNamespace(
                id=uuid4(),
                name="Environment",
                projection_hash="environment.projection",
                supports_virtual_build=True,
                object_projection_graph_constructors=(
                    SimpleNamespace(
                        root_node_id=root_node_id,
                        function_constructor_id=function_edge_id,
                    ),
                ),
                object_projection_graph_nodes=(
                    SimpleNamespace(
                        id=root_node_id,
                        class_config_id=root_class_config_id,
                    ),
                ),
            ),
        ),
    )
    return SimpleNamespace(
        aware_toml_path=Path("modules/demo/structure/ontology/aware.toml"),
        package_branch_id=uuid4(),
        code_package=SimpleNamespace(id=uuid4()),
        code_package_commit_id=uuid4(),
        code_package_head_commit_id=uuid4(),
        code_package_object_instance_graph_commit_id=uuid4(),
        object_config_graph=object_config_graph,
        object_config_graph_commit_id=uuid4(),
        object_config_graph_head_commit_id=uuid4(),
        object_config_graph_object_instance_graph_commit_id=uuid4(),
        object_config_graph_package=SimpleNamespace(
            id=uuid4(),
            package_name=package_name,
            fqn_prefix="aware_demo",
        ),
        object_config_graph_package_commit_id=uuid4(),
        object_config_graph_package_head_commit_id=uuid4(),
        object_config_graph_package_object_instance_graph_commit_id=uuid4(),
        semantic_commit_strategy="full_rebuild",
        semantic_commit_fallback_reset=False,
    )
