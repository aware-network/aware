from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import msgpack
import pytest

from aware_api_runtime.dependencies.runtime_resolution import (
    API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME,
    API_RUNTIME_SEMANTICS_FILENAME,
    RuntimeRequirementsError,
    _RuntimeDependencyPackage,
    _build_aware_toml_package_index,
    _compute_runtime_dependency_source_digest,
    _load_existing_dependency_object_config_graph,
    _resolve_api_dependency_packages,
    _runtime_dependency_ocg_outputs_are_fresh_for_inputs,
    _runtime_dependency_outputs_are_fresh_for_inputs,
    load_api_accessible_dependency_graphs,
    resolve_api_workspace_runtime_manifest,
)
from aware_api_runtime.workspace import APIWorkspace
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_edge import (
    ObjectProjectionGraphEdge,
)


def test_accessible_dependency_graph_loads_artifact_projection_edges(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_cross_ocg_dependency_workspace(tmp_path)
    content_root = tmp_path / "modules" / "content" / "structure" / "ontology"
    memory_root = tmp_path / "modules" / "memory" / "structure" / "ontology"
    _write_runtime_ocg_snapshot(
        package_root=content_root,
        package_name="content-ontology",
        fqn_prefix="aware_content",
    )
    _write_runtime_ocg_snapshot(
        package_root=memory_root,
        package_name="memory-ontology",
        fqn_prefix="aware_memory",
        graph=_object_config_graph_with_projection_edges(
            package_name="memory-ontology",
            fqn_prefix="aware_memory",
            projection_name="MemoryEpisodic",
            edge_count=2,
        ),
    )

    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=tmp_path,
    ).build_snapshot()

    graphs = load_api_accessible_dependency_graphs(snapshot=snapshot)

    memory_graph = next(graph for graph in graphs if graph.name == "memory-ontology")
    memory_projection_edges = [
        edge
        for opg in memory_graph.object_projection_graphs
        if "memory" in (opg.name or "").casefold()
        for edge in opg.object_projection_graph_edges
    ]
    assert len(memory_projection_edges) == 2


def test_accessible_dependency_graph_requires_runtime_artifact(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_runtime_root_api_workspace(root=tmp_path)
    module_root = tmp_path / "modules" / "home"
    package_root = module_root / "structure" / "ontology"
    aware_root = package_root / "aware" / "home"
    aware_root.mkdir(parents=True)
    _write_aware_package_toml(
        package_root / "aware.toml",
        package_name="home-ontology",
        fqn_prefix="aware_home",
    )
    (aware_root / "door.aware").write_text(
        "class Door { label String key }\n",
        encoding="utf-8",
    )
    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=tmp_path,
    ).build_snapshot()

    with pytest.raises(RuntimeError, match="Structure repository fallback is retired"):
        load_api_accessible_dependency_graphs(snapshot=snapshot)


def test_api_runtime_resolution_import_activation_includes_dependency_module_runtime_roots(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_runtime_root_api_workspace(root=tmp_path)
    module_root = tmp_path / "modules" / "home"
    package_root = module_root / "structure" / "ontology"
    aware_root = package_root / "aware" / "home"
    python_root = package_root / "python"
    runtime_root = module_root / "runtime"
    aware_root.mkdir(parents=True)
    python_root.mkdir(parents=True)
    runtime_root.mkdir(parents=True)
    aware_toml_path = package_root / "aware.toml"
    _write_aware_package_toml(
        aware_toml_path,
        package_name="home-ontology",
        fqn_prefix="aware_home",
    )
    (aware_root / "door.aware").write_text(
        "class Door { label String key }\n",
        encoding="utf-8",
    )
    _write_runtime_ocg_snapshot(
        package_root=package_root,
        package_name="home-ontology",
        fqn_prefix="aware_home",
    )

    resolution = resolve_api_workspace_runtime_manifest(
        toml_path=api_toml_path,
        repo_root=tmp_path,
        kernel_repo_root=tmp_path,
        core_module_ids=(),
    )

    assert python_root.resolve() in resolution.python_roots
    assert runtime_root.resolve() not in resolution.python_roots
    assert python_root.resolve() in resolution.import_activation.roots
    assert runtime_root.resolve() in resolution.import_activation.roots
    assert resolution.module_manifest_paths == ()
    assert resolution.manifest_path.name == API_RUNTIME_SEMANTICS_FILENAME
    assert resolution.manifest_path.is_file()
    graphs_path = (
        tmp_path
        / ".aware"
        / "api"
        / "runtime"
        / "runtime-root-proof-api"
        / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME
    )
    assert graphs_path.is_file()


def test_api_runtime_resolution_rejects_environment_composition_requests(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_runtime_root_api_workspace(root=tmp_path)

    with pytest.raises(RuntimeRequirementsError, match="no longer composes"):
        resolve_api_workspace_runtime_manifest(
            toml_path=api_toml_path,
            repo_root=tmp_path,
            kernel_repo_root=tmp_path,
            environment_toml=tmp_path / "aware.environment.toml",
        )

    with pytest.raises(RuntimeRequirementsError, match="no longer introspects"):
        resolve_api_workspace_runtime_manifest(
            toml_path=api_toml_path,
            repo_root=tmp_path,
            kernel_repo_root=tmp_path,
            core_module_ids=("api",),
        )


def test_api_graph_target_package_is_accessible_dependency(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_api_graph_target_workspace(root=tmp_path)
    _write_runtime_ocg_snapshot(
        package_root=tmp_path / "modules" / "attention" / "structure" / "ontology",
        package_name="attention-ontology",
        fqn_prefix="aware_attention",
    )

    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=tmp_path,
    ).build_snapshot()

    packages = _resolve_api_dependency_packages(snapshot=snapshot)
    graphs = load_api_accessible_dependency_graphs(snapshot=snapshot)

    assert [package.package_name for package in packages] == ["attention-ontology"]
    assert [graph.name for graph in graphs] == ["attention-ontology"]
    assert graphs[0].fqn_prefix == "aware_attention"


def test_runtime_dependency_freshness_ignores_generated_aware_source_index(
    tmp_path: Path,
) -> None:
    module_root = tmp_path / "modules" / "home"
    package_root = module_root / "structure" / "ontology"
    aware_root = package_root / "aware" / "home"
    aware_root.mkdir(parents=True, exist_ok=True)
    (aware_root / "door.aware").write_text(
        "class Door { label String }\n", encoding="utf-8"
    )
    aware_toml_path = package_root / "aware.toml"
    _write_aware_package_toml(
        aware_toml_path,
        package_name="home-ontology",
        fqn_prefix="aware_home",
    )
    package = _RuntimeDependencyPackage(
        package_name="home-ontology",
        aware_toml_path=aware_toml_path.resolve(),
        package_root=package_root.resolve(),
        spec=load_aware_toml_spec(toml_path=aware_toml_path),
    )
    package.runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    package.runtime_manifest_path.write_text("{}", encoding="utf-8")
    package.python_models_path.parent.mkdir(parents=True, exist_ok=True)
    package.python_models_path.write_text("{}", encoding="utf-8")

    digest_before = _compute_runtime_dependency_source_digest(package=package)
    generated_index = package_root / "aware" / ".aware" / "repository.idx"
    generated_index.parent.mkdir(parents=True, exist_ok=True)
    generated_index.write_text("generated scanner state\n", encoding="utf-8")
    later_mtime_ns = (
        max(
            package.runtime_manifest_path.stat().st_mtime_ns,
            package.python_models_path.stat().st_mtime_ns,
        )
        + 1_000_000
    )
    os.utime(generated_index, ns=(later_mtime_ns, later_mtime_ns))

    assert _compute_runtime_dependency_source_digest(package=package) == digest_before
    assert _runtime_dependency_outputs_are_fresh_for_inputs(package=package)


def test_runtime_dependency_ocg_freshness_does_not_require_python_models(
    tmp_path: Path,
) -> None:
    module_root = tmp_path / "modules" / "home"
    package_root = module_root / "structure" / "ontology"
    aware_root = package_root / "aware" / "home"
    aware_root.mkdir(parents=True, exist_ok=True)
    source_path = aware_root / "door.aware"
    source_path.write_text("class Door { label String }\n", encoding="utf-8")
    aware_toml_path = package_root / "aware.toml"
    _write_aware_package_toml(
        aware_toml_path,
        package_name="home-ontology",
        fqn_prefix="aware_home",
    )
    package = _RuntimeDependencyPackage(
        package_name="home-ontology",
        aware_toml_path=aware_toml_path.resolve(),
        package_root=package_root.resolve(),
        spec=load_aware_toml_spec(toml_path=aware_toml_path),
    )
    runtime_manifest_path = package.runtime_manifest_path
    runtime_root = runtime_manifest_path.parent
    runtime_root.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path.write_text(
        '{"ocg": {"snapshot": "ocg.snapshot.msgpack"}}\n',
        encoding="utf-8",
    )
    ocg_snapshot_path = runtime_root / "ocg.snapshot.msgpack"
    ocg_snapshot_path.write_bytes(b"not-a-real-snapshot")
    package.python_models_path.parent.mkdir(parents=True, exist_ok=True)
    package.python_models_path.write_text("{}", encoding="utf-8")

    latest_input_mtime_ns = max(
        aware_toml_path.stat().st_mtime_ns,
        source_path.stat().st_mtime_ns,
    )
    fresh_output_mtime_ns = latest_input_mtime_ns + 10_000_000
    stale_python_mtime_ns = latest_input_mtime_ns - 10_000_000
    os.utime(
        runtime_manifest_path,
        ns=(fresh_output_mtime_ns, fresh_output_mtime_ns),
    )
    os.utime(
        ocg_snapshot_path,
        ns=(fresh_output_mtime_ns, fresh_output_mtime_ns),
    )
    os.utime(
        package.python_models_path,
        ns=(stale_python_mtime_ns, stale_python_mtime_ns),
    )

    assert _runtime_dependency_outputs_are_fresh_for_inputs(package=package) is False
    assert _runtime_dependency_ocg_outputs_are_fresh_for_inputs(package=package) is True


def test_existing_dependency_ocg_loads_runtime_snapshot_artifact(
    tmp_path: Path,
) -> None:
    module_root = tmp_path / "modules" / "home"
    package_root = module_root / "structure" / "ontology"
    aware_root = package_root / "aware" / "home"
    aware_root.mkdir(parents=True, exist_ok=True)
    (aware_root / "door.aware").write_text(
        "class Door { label String }\n", encoding="utf-8"
    )
    aware_toml_path = package_root / "aware.toml"
    _write_aware_package_toml(
        aware_toml_path,
        package_name="home-ontology",
        fqn_prefix="aware_home",
    )
    package = _RuntimeDependencyPackage(
        package_name="home-ontology",
        aware_toml_path=aware_toml_path.resolve(),
        package_root=package_root.resolve(),
        spec=load_aware_toml_spec(toml_path=aware_toml_path),
    )
    runtime_manifest_path = package.runtime_manifest_path
    runtime_root = runtime_manifest_path.parent
    runtime_root.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path.write_text(
        '{"ocg": {"snapshot": "ocg.snapshot.msgpack"}}\n',
        encoding="utf-8",
    )
    graph = ObjectConfigGraph(
        name="home-ontology",
        fqn_prefix="aware_home",
        hash="sha256:home",
        language=CodeLanguage.aware,
    )
    (runtime_root / "ocg.snapshot.msgpack").write_bytes(
        msgpack.packb(
            graph.model_dump(mode="json", exclude_none=True),
            use_bin_type=True,
        )
    )
    package.runtime_source_digest_path.parent.mkdir(parents=True, exist_ok=True)
    package.runtime_source_digest_path.write_text(
        _compute_runtime_dependency_source_digest(package=package),
        encoding="utf-8",
    )

    loaded = _load_existing_dependency_object_config_graph(package=package)

    assert loaded is not None
    assert loaded.name == "home-ontology"
    assert loaded.fqn_prefix == "aware_home"
    assert loaded.hash == "sha256:home"


def test_runtime_dependency_package_resolution_ignores_generated_aware_toml(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_runtime_root_api_workspace(root=tmp_path)
    authored_package_root = tmp_path / "modules" / "home" / "structure" / "ontology"
    _write_aware_package_toml(
        authored_package_root / "aware.toml",
        package_name="home-ontology",
        fqn_prefix="aware_home",
    )
    generated_package_root = tmp_path / ".aware" / "materialized" / "home"
    _write_aware_package_toml(
        generated_package_root / "aware.toml",
        package_name="home-ontology",
        fqn_prefix="generated_home",
    )

    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=tmp_path,
    ).build_snapshot()

    packages = _resolve_api_dependency_packages(snapshot=snapshot)

    assert [package.package_name for package in packages] == ["home-ontology"]
    assert (
        packages[0].aware_toml_path == (authored_package_root / "aware.toml").resolve()
    )


def test_runtime_dependency_package_index_prefers_module_inventory_over_proof_fixture(
    tmp_path: Path,
) -> None:
    module_root = tmp_path / "modules" / "home"
    module_package_root = (
        module_root / "apis" / "home_devices" / "packages" / "home_api"
    )
    proof_package_root = (
        tmp_path
        / "docs"
        / "proofs"
        / "api-delta-generated-artifacts"
        / "versions"
        / "packages"
        / "home_api"
    )
    _write_aware_package_toml(
        proof_package_root / "aware.toml",
        package_name="home-api",
        fqn_prefix="aware_home_api_stale",
        kind="api",
    )
    _write_aware_package_toml(
        module_package_root / "aware.toml",
        package_name="home-api",
        fqn_prefix="aware_home_api",
        kind="api",
    )
    (module_root / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "home_api"',
                'kind = "api"',
                'manifest = "apis/home_devices/packages/home_api/aware.toml"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    index = _build_aware_toml_package_index(repo_root=tmp_path)

    assert index["home-api"] == (module_package_root / "aware.toml").resolve()


def test_runtime_dependency_package_resolution_falls_back_to_kernel_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace_root = tmp_path / "workspaces" / "aware_workspace"
    kernel_root = tmp_path / "kernel"
    api_toml_path = _write_runtime_root_api_workspace(root=workspace_root)
    workspace_package_root = (
        workspace_root / "modules" / "home" / "structure" / "ontology"
    )
    kernel_package_root = kernel_root / "modules" / "code" / "structure" / "api"
    _write_aware_package_toml(
        workspace_package_root / "aware.toml",
        package_name="home-ontology",
        fqn_prefix="aware_home",
        dependencies=("code-api",),
    )
    _write_aware_package_toml(
        kernel_package_root / "aware.toml",
        package_name="code-api",
        fqn_prefix="aware_code_api",
        kind="api",
    )

    monkeypatch.setenv("AWARE_KERNEL_REPO_ROOT", str(kernel_root))
    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=workspace_root,
    ).build_snapshot()

    packages = _resolve_api_dependency_packages(snapshot=snapshot)

    assert [package.package_name for package in packages] == [
        "code-api",
        "home-ontology",
    ]
    assert packages[0].aware_toml_path == (kernel_package_root / "aware.toml").resolve()
    assert (
        packages[1].aware_toml_path == (workspace_package_root / "aware.toml").resolve()
    )


def test_runtime_dependency_package_resolution_uses_explicit_dependency_roots(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace_root = tmp_path / "workspaces" / "aware_workspace"
    kernel_root = tmp_path / "kernel"
    api_toml_path = _write_runtime_root_api_workspace(root=workspace_root)
    workspace_package_root = (
        workspace_root / "modules" / "home" / "structure" / "ontology"
    )
    kernel_package_root = kernel_root / "modules" / "code" / "structure" / "api"
    _write_aware_package_toml(
        workspace_package_root / "aware.toml",
        package_name="home-ontology",
        fqn_prefix="aware_home",
        dependencies=("code-api",),
    )
    _write_aware_package_toml(
        kernel_package_root / "aware.toml",
        package_name="code-api",
        fqn_prefix="aware_code_api",
        kind="api",
    )
    monkeypatch.delenv("AWARE_KERNEL_REPO_ROOT", raising=False)
    monkeypatch.delenv("AWARE_REPOSITORY_ROOT", raising=False)
    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=workspace_root,
    ).build_snapshot()

    packages = _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=(kernel_root,),
    )

    assert [package.package_name for package in packages] == [
        "code-api",
        "home-ontology",
    ]
    assert packages[0].aware_toml_path == (kernel_package_root / "aware.toml").resolve()
    assert (
        packages[1].aware_toml_path == (workspace_package_root / "aware.toml").resolve()
    )


def _write_runtime_root_api_workspace(*, root: Path) -> Path:
    bindings_root = root / "bindings"
    bindings_root.mkdir(parents=True, exist_ok=True)
    (bindings_root / "runtime_root.apis.aware").write_text(
        "api runtime_root_proof {}\n",
        encoding="utf-8",
    )
    toml_path = root / "aware.api.toml"
    toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "runtime-root-proof-api"',
                'fqn_prefix = "aware_runtime_root_proof_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                "",
                "[[dependencies]]",
                'package_name = "home-ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_cross_ocg_dependency_workspace(root: Path) -> Path:
    api_toml_path = root / "aware.api.toml"
    api_toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "memory-service-api"',
                'fqn_prefix = "aware_memory_service_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                "",
                "[[dependencies]]",
                'package_name = "memory-ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    bindings_root = root / "bindings"
    bindings_root.mkdir(parents=True, exist_ok=True)
    (bindings_root / "memory.apis.aware").write_text(
        "\n".join(
            [
                "api memory_service {",
                "    capability read_memory {",
                "        endpoint read_episode aware_memory.memory.MemoryEpisode {",
                "            response aware_memory.memory.MemoryEpisode;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    content_root = root / "modules" / "content" / "structure" / "ontology"
    (content_root / "aware" / "content").mkdir(parents=True, exist_ok=True)
    _write_aware_package_toml(
        content_root / "aware.toml",
        package_name="content-ontology",
        fqn_prefix="aware_content",
    )
    (content_root / "aware" / "content" / "content_item.aware").write_text(
        "\n".join(
            [
                "class ContentItem {",
                "    name String key",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    memory_root = root / "modules" / "memory" / "structure" / "ontology"
    (memory_root / "aware" / "memory").mkdir(parents=True, exist_ok=True)
    _write_aware_package_toml(
        memory_root / "aware.toml",
        package_name="memory-ontology",
        fqn_prefix="aware_memory",
        dependencies=("content-ontology",),
    )
    (memory_root / "aware" / "memory" / "memory_episodic.aware").write_text(
        "\n".join(
            [
                "class MemoryEpisodic {",
                "    episodes MemoryEpisode[]",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (memory_root / "aware" / "memory" / "memory_episode.aware").write_text(
        "\n".join(
            [
                "class MemoryEpisode {",
                "    content aware_content.content.ContentItem key",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (memory_root / "aware" / "memory" / "memory_projection.aware").write_text(
        "\n".join(
            [
                "projection MemoryEpisodic {",
                "    root memory.MemoryEpisodic",
                "    memory.MemoryEpisodic::episodes",
                "    memory.MemoryEpisode::content",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return api_toml_path


def _write_api_graph_target_workspace(*, root: Path) -> Path:
    api_bindings_root = root / "apis" / "attention" / "bindings"
    api_bindings_root.mkdir(parents=True, exist_ok=True)
    (api_bindings_root / "attention.apis.aware").write_text(
        "\n".join(
            [
                "api attention {",
                "    graph aware_attention {",
                "        projection aware_attention.FocusScope;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    api_toml_path = root / "apis" / "attention" / "aware.api.toml"
    api_toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "attention-service-api"',
                'fqn_prefix = "aware_attention_service_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                "",
            ]
        ),
        encoding="utf-8",
    )

    attention_root = root / "modules" / "attention" / "structure" / "ontology"
    (attention_root / "aware" / "focus").mkdir(parents=True, exist_ok=True)
    _write_aware_package_toml(
        attention_root / "aware.toml",
        package_name="attention-ontology",
        fqn_prefix="aware_attention",
    )
    (attention_root / "aware" / "focus" / "focus_scope.aware").write_text(
        "\n".join(
            [
                "class FocusScope {",
                "    name String key",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (attention_root / "aware" / "focus" / "focus_scope_projection.aware").write_text(
        "\n".join(
            [
                "projection FocusScope {",
                "    root focus.FocusScope",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return api_toml_path


def _write_aware_package_toml(
    path: Path,
    *,
    package_name: str,
    fqn_prefix: str,
    kind: str = "ontology",
    dependencies: tuple[str, ...] = (),
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "aware = 1",
        "",
        "[package]",
        f'package_name = "{package_name}"',
        f'fqn_prefix = "{fqn_prefix}"',
        f'kind = "{kind}"',
        "",
        "[build]",
        f'environment_slug = "{fqn_prefix}"',
        "",
    ]
    for dependency in dependencies:
        lines.extend(
            [
                "[[dependencies]]",
                f'package_name = "{dependency}"',
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_runtime_ocg_snapshot(
    *,
    package_root: Path,
    package_name: str,
    fqn_prefix: str,
    graph: ObjectConfigGraph | None = None,
) -> ObjectConfigGraph:
    aware_toml_path = package_root / "aware.toml"
    package = _RuntimeDependencyPackage(
        package_name=package_name,
        aware_toml_path=aware_toml_path.resolve(),
        package_root=package_root.resolve(),
        spec=load_aware_toml_spec(toml_path=aware_toml_path),
    )
    runtime_root = package.runtime_manifest_path.parent
    runtime_root.mkdir(parents=True, exist_ok=True)
    package.runtime_manifest_path.write_text(
        '{"ocg": {"snapshot": "ocg.snapshot.msgpack"}}\n',
        encoding="utf-8",
    )
    resolved_graph = graph or ObjectConfigGraph(
        id=uuid4(),
        name=package_name,
        fqn_prefix=fqn_prefix,
        hash=f"sha256:{package_name}",
        language=CodeLanguage.aware,
    )
    (runtime_root / "ocg.snapshot.msgpack").write_bytes(
        msgpack.packb(
            resolved_graph.model_dump(mode="json", exclude_none=True),
            use_bin_type=True,
        )
    )
    package.runtime_source_digest_path.parent.mkdir(parents=True, exist_ok=True)
    package.runtime_source_digest_path.write_text(
        _compute_runtime_dependency_source_digest(package=package),
        encoding="utf-8",
    )
    return resolved_graph


def _object_config_graph_with_projection_edges(
    *,
    package_name: str,
    fqn_prefix: str,
    projection_name: str,
    edge_count: int,
) -> ObjectConfigGraph:
    graph_id = uuid4()
    opg_id = uuid4()
    return ObjectConfigGraph(
        id=graph_id,
        name=package_name,
        fqn_prefix=fqn_prefix,
        hash=f"sha256:{package_name}",
        language=CodeLanguage.aware,
        object_projection_graphs=[
            ObjectProjectionGraph(
                id=opg_id,
                object_config_graph_id=graph_id,
                name=projection_name,
                language=CodeLanguage.aware,
                projection_hash=f"sha256:{projection_name}",
                object_projection_graph_edges=[
                    ObjectProjectionGraphEdge(
                        id=uuid4(),
                        object_projection_graph_id=opg_id,
                        class_config_relationship_id=uuid4(),
                    )
                    for _ in range(edge_count)
                ],
            )
        ],
    )
