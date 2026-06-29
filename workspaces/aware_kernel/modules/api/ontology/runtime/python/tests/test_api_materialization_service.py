from __future__ import annotations

import ast
import asyncio
import os
from pathlib import Path
from types import SimpleNamespace
import json
import sys
from typing import Any, Callable, Mapping, Sequence, cast
from uuid import UUID, uuid4

import pytest

from _api_runtime_test_paths import (  # noqa: E402
    API_META_PACKAGE_MANIFEST_PATHS,
    API_META_PYTHON_ROOTS,
    API_RUNTIME_ROOT,
    REPO_ROOT as _REPO_ROOT,
)

_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_API_RUNTIME_ROOT = API_RUNTIME_ROOT
_API_RUNTIME_ROOT_STR = str(_API_RUNTIME_ROOT)
if _API_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _API_RUNTIME_ROOT_STR)

from aware_api_runtime.handlers._generated import (
    meta_handlers as api_meta_handlers,
)  # noqa: E402
from aware_meta.materialization import MaterializationLaneContext  # noqa: E402
from aware_meta.runtime import (  # noqa: E402
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.testing import IsolatedMetaAwareRoot  # noqa: E402
from aware_code_ontology.code.code_enums import CodeLanguage  # noqa: E402
from aware_api_runtime.ir import (  # noqa: E402
    encode_api_compile_plan_payload,
    build_api_compile_plan,
    emit_api_compile_plan_artifact,
)
from aware_api_runtime.compile import (  # noqa: E402
    compile_api_accessible_dependency_graphs_via_meta_runtime,
    compile_api_workspace,
)
from aware_api_runtime.ontology_graph.materialization import (  # noqa: E402
    build_api_ontology_materialization_plan,
    materialize_api_graph_ontology,
    resolve_api_ontology_materialization_specs,
)
from aware_api_runtime.ontology_graph.materialization.resolution import (  # noqa: E402
    _collect_accessible_object_config_graphs,
    _projection_matches,
    _resolve_object_projection_graph,
    _resolve_target_object_config_graph,
)
from aware_api_runtime.compile_materialization.service import (  # noqa: E402
    _api_endpoint_catalog_is_satisfied_by_session,
    ApiPackageMaterializationResult,
    build_generated_api_compile_plan_accessible_graphs,
    build_api_accessible_dependency_graphs_via_meta_runtime,
    materialize_api_package_from_compile_plan_input,
)
import aware_api_runtime.compile_materialization.service as api_materialization_service  # noqa: E402
from aware_api_runtime.workspace_provider.provider import (  # noqa: E402
    _compile_plan_payload_from_input,
)
from aware_api_runtime.models import (  # noqa: E402
    ProjectionOwnedClassTruth,
)
from aware_api_runtime.dependencies.runtime_resolution import (  # noqa: E402
    API_RUNTIME_SEMANTICS_FILENAME,
    _RuntimeDependencyPackage,
    _build_runtime_dependency_package,
    _compute_runtime_dependency_source_digest,
    _runtime_dependency_outputs_are_fresh_for_inputs,
    load_api_accessible_dependency_graphs,
    load_api_accessible_dependency_graphs_from_runtime_artifact,
    dump_api_accessible_dependency_graph_artifact_payload,
    load_api_dependency_class_config_ids,
    resolve_api_workspace_runtime_manifest,
)
from aware_meta.manifest.loader import load_aware_toml_spec  # noqa: E402
from aware_orm.runtime.models_manifest import (
    ModelsManifest,
    ClassModelEntry,
)  # noqa: E402
from aware_api_ontology.api.api import Api  # noqa: E402


from aware_api_ontology.api.api_capability import ApiCapability  # noqa: E402
from aware_api_ontology.api.api_capability_endpoint import (
    ApiCapabilityEndpoint,
)  # noqa: E402
from aware_meta_ontology.graph.config.object_config_graph import (
    ObjectConfigGraph,
)  # noqa: E402
from aware_meta_ontology.graph.config.object_config_graph_enums import (  # noqa: E402
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (  # noqa: E402
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_node_layout import (  # noqa: E402
    ObjectConfigGraphNodeLayout,
)
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (  # noqa: E402
    ObjectProjectionGraphDeclaration,
)
from aware_meta_ontology.graph.projection.object_projection_graph_binding import (  # noqa: E402
    ObjectProjectionGraphBinding,
)
from aware_meta.materialization import (
    stable_object_config_graph_package_branch_id,
)  # noqa: E402
from aware_meta_ontology.class_.class_config import ClassConfig  # noqa: E402

_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)


def _fake_meta_leaf_result(graph: ObjectConfigGraph) -> SimpleNamespace:
    return SimpleNamespace(object_config_graph=graph)


def _api_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == _REPO_ROOT
    return API_META_PACKAGE_MANIFEST_PATHS


def _api_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == _REPO_ROOT
    return API_META_PYTHON_ROOTS


def _prepend_api_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for python_root in _api_meta_python_roots(repo_root):
        if python_root.exists():
            syspath_prepend(str(python_root))


def _build_api_meta_runtime(*, repo_root: Path, aware_root: Path) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_api_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_API_META_HANDLER_MODULE,),
        bootstrap_modules=(_API_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


def test_api_materialization_service_has_no_direct_deprecated_runtime_imports() -> None:
    service_path = (
        _API_RUNTIME_ROOT
        / "aware_api_runtime"
        / "compile_materialization"
        / "service.py"
    )
    tree = ast.parse(
        service_path.read_text(encoding="utf-8"), filename=str(service_path)
    )

    deprecated_sites: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] == "aware_runtime":
                    deprecated_sites.append(f"{node.lineno}:{alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] == "aware_runtime":
                deprecated_sites.append(f"{node.lineno}:{node.module}")

    assert deprecated_sites == []


def test_api_phase_recorder_emits_workspace_progress_events() -> None:
    events: list[Mapping[str, object]] = []
    phase_timings_s: dict[str, float] = {}

    with api_materialization_service._api_materialization_progress_context(
        progress_callback=events.append,
        detail_payload={
            "materialization_kind": "api_manifest",
            "api_toml_path": "apis/example/aware.api.toml",
        },
    ):
        with api_materialization_service._record_phase(
            phase_timings_s,
            "materialize_api_product_runtime_artifacts.dart_public_package_refresh_from_runtime_artifacts",
        ):
            pass

    assert (
        "materialize_api_product_runtime_artifacts.dart_public_package_refresh_from_runtime_artifacts"
        in phase_timings_s
    )
    assert [event["status"] for event in events] == ["running", "succeeded"]
    assert all(event["phase_name"] == "api.package.subphase" for event in events)
    assert events[0]["detail_payload"] == {
        "materialization_kind": "api_manifest",
        "api_toml_path": "apis/example/aware.api.toml",
        "subphase_name": "materialize_api_product_runtime_artifacts.dart_public_package_refresh_from_runtime_artifacts",
    }
    assert "duration_s" not in events[0]
    assert isinstance(events[1]["duration_s"], float)


@pytest.mark.asyncio
async def test_api_phase_recorder_schedules_async_workspace_progress_events() -> None:
    events: list[Mapping[str, object]] = []
    phase_timings_s: dict[str, float] = {}

    async def _progress_callback(payload: Mapping[str, object]) -> None:
        events.append(dict(payload))

    with api_materialization_service._api_materialization_progress_context(
        progress_callback=_progress_callback,
        detail_payload={"materialization_kind": "api_manifest"},
    ):
        with api_materialization_service._record_phase(
            phase_timings_s,
            "resolve_api_package_materialization_spec",
        ):
            pass

    await asyncio.sleep(0)

    assert phase_timings_s["resolve_api_package_materialization_spec"] >= 0
    assert [event["status"] for event in events] == ["running", "succeeded"]
    assert all(event["phase_name"] == "api.package.subphase" for event in events)
    assert events[0]["detail_payload"] == {
        "materialization_kind": "api_manifest",
        "subphase_name": "resolve_api_package_materialization_spec",
    }


def test_api_phase_recorder_emits_workspace_failure_progress() -> None:
    events: list[Mapping[str, object]] = []
    phase_timings_s: dict[str, float] = {}

    with pytest.raises(ValueError, match="boom"):
        with api_materialization_service._api_materialization_progress_context(
            progress_callback=events.append,
            detail_payload={"materialization_kind": "api_compile_plan_input"},
        ):
            with api_materialization_service._record_phase(
                phase_timings_s,
                "materialize_api_compile_plan_ontology",
            ):
                raise ValueError("boom")

    assert phase_timings_s["materialize_api_compile_plan_ontology"] >= 0
    assert [event["status"] for event in events] == ["running", "failed"]
    assert events[1]["phase_name"] == "api.package.subphase"
    assert events[1]["error"] == "boom"
    assert events[1]["detail_payload"] == {
        "materialization_kind": "api_compile_plan_input",
        "subphase_name": "materialize_api_compile_plan_ontology",
        "error_type": "ValueError",
    }


def _write_api_workspace(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "api-anchor"',
                'fqn_prefix = "aware_api_anchor"',
                "",
                "[build]",
                'sources_dir = "apis/bindings"',
                'include_paths = ["**/*.aware"]',
                "",
            ]
        ),
        encoding="utf-8",
    )

    bindings = root / "apis" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "anchor.apis.aware").write_text(
        "\n".join(
            [
                "api api_anchor {",
                "    capability projection_resolution {",
                "        endpoint projection_resolution aware_api.default.api.Api {",
                "            response aware_api.default.api.ApiRoot;",
                "            stream server {",
                "                event snapshot aware_api.default.api.ApiGraph;",
                "                event delta aware_api.default.api.ApiCapability;",
                "            }",
                "        }",
                "    }",
                "    graph aware_api {",
                "        projection aware_api.api.ApiRootProjection {",
                "        }",
                "        capability projection_resolution {",
                "            function create_api aware_api.default.api.ApiRoot.create_api;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _projection_truth_for_api_anchor() -> (
    dict[str, dict[str, ProjectionOwnedClassTruth]]
):
    return {
        "aware_api.api.ApiRootProjection": {
            "ApiRoot": ProjectionOwnedClassTruth(
                class_fqn="aware_api_ontology.api.api_root.ApiRoot",
                attributes=frozenset({"apis"}),
                identity_key_attributes=frozenset({"name"}),
                relationship_targets=(("apis", "Api"),),
            ),
            "Api": ProjectionOwnedClassTruth(
                class_fqn="aware_api_ontology.api.api.Api",
                attributes=frozenset({"name", "description"}),
                identity_key_attributes=frozenset({"name"}),
            ),
        }
    }


def _build_compile_payload(tmp_path: Path) -> dict[str, object]:
    package_root = tmp_path / "api_anchor_workspace"
    package_root.mkdir(parents=True, exist_ok=True)
    toml_path = _write_api_workspace(package_root)
    compile_result = compile_api_workspace(toml_path=toml_path, repo_root=package_root)
    plan = build_api_compile_plan(
        snapshot=compile_result.snapshot,
        projection_truth_by_name=_projection_truth_for_api_anchor(),
    )
    artifact = emit_api_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=package_root / ".aware" / "api" / "runtime" / "anchor",
        repo_root=package_root,
    )
    payload_obj = cast(object, json.loads(artifact.path.read_text(encoding="utf-8")))
    if not isinstance(payload_obj, dict):
        raise AssertionError("api compile payload must be dict")
    return cast(dict[str, object], payload_obj)


def _write_dependency_class_config_workspace(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "dependency-proof-service-api"',
                'fqn_prefix = "aware_dependency_proof_service_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "home-api"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    bindings = root / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "service.apis.aware").write_text(
        "\n".join(
            [
                "api dependency_proof {",
                "    capability lock_door {",
                "        endpoint lock_door aware_home_api.door.LockDoor {",
                "            response aware_home_api.door.LockDoorResult;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ontology_root = root / "modules" / "home" / "structure" / "ontology"
    (ontology_root / "aware" / "home").mkdir(parents=True, exist_ok=True)
    _ = (ontology_root / "aware.toml").write_text(
        "\n".join(
            [
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
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home" / "door.aware").write_text(
        "\n".join(
            [
                "class Door {",
                "    label String",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    api_root = root / "apis" / "types" / "home"
    (api_root / "aware" / "door").mkdir(parents=True, exist_ok=True)
    _ = (api_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-api"',
                'fqn_prefix = "aware_home_api"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_home_api"',
                "",
                "[[dependencies]]",
                'package_name = "home-ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (api_root / "aware" / "door" / "endpoints.aware").write_text(
        "\n".join(
            [
                "class LockDoor {",
                "    label String",
                "}",
                "",
                "class LockDoorResult {",
                "    accepted Bool",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_explicit_namespace_dependency_workspace(root: Path) -> Path:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "explicit-namespace-service-api"',
                'fqn_prefix = "aware_explicit_namespace_service_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "home-api"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    bindings = root / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "service.apis.aware").write_text(
        "\n".join(
            [
                "api explicit_namespace {",
                "    capability lock_door {",
                "        endpoint lock_door aware_home_api.comms.models.LockDoor {",
                "            response aware_home_api.comms.models.LockDoorResult;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    api_root = root / "apis" / "types" / "home"
    (api_root / "aware" / "door").mkdir(parents=True, exist_ok=True)
    _ = (api_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-api"',
                'fqn_prefix = "aware_home_api"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_home_api"',
                "",
                "[build.namespace]",
                '"door/**/*.aware" = "comms.models"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (api_root / "aware" / "door" / "endpoints.aware").write_text(
        "\n".join(
            [
                "class DoorCommand {",
                "    operation String",
                "}",
                "",
                "class LockDoor augment models.DoorCommand {",
                "    label String",
                "}",
                "",
                "class LockDoorResult {",
                "    accepted Bool",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_dependency_python_models(
    *,
    package_root: Path,
    entries: list[ClassModelEntry],
    ontology_runtime: bool = False,
) -> None:
    if ontology_runtime:
        models_path = (
            package_root
            / "python"
            / "orm_runtime"
            / ".aware"
            / "materializations"
            / "python.models.json"
        )
    else:
        models_path = (
            package_root / ".aware" / "materializations" / "python.models.json"
        )
    models_path.parent.mkdir(parents=True, exist_ok=True)
    _ = models_path.write_text(
        ModelsManifest(language="python", classes=entries).model_dump_json(indent=2),
        encoding="utf-8",
    )


def _home_api_context_graph(
    *,
    request_class_config_id: UUID | None = None,
    response_class_config_id: UUID | None = None,
    include_source_layouts: bool = True,
) -> ObjectConfigGraph:
    graph_id = uuid4()
    request_class = ClassConfig(
        id=request_class_config_id or uuid4(),
        class_fqn="aware_home_api.door.LockDoor",
        name="LockDoor",
        is_base=True,
        class_config_attribute_configs=[],
    )
    response_class = ClassConfig(
        id=response_class_config_id or uuid4(),
        class_fqn="aware_home_api.door.LockDoorResult",
        name="LockDoorResult",
        is_base=True,
        class_config_attribute_configs=[],
    )
    request_node = ObjectConfigGraphNode(
        type=ObjectConfigGraphNodeType.class_,
        node_key=request_class.class_fqn,
        object_config_graph_id=graph_id,
        class_config=request_class,
    )
    response_node = ObjectConfigGraphNode(
        type=ObjectConfigGraphNodeType.class_,
        node_key=response_class.class_fqn,
        object_config_graph_id=graph_id,
        class_config=response_class,
    )
    request_class.object_config_graph_node_id = request_node.id
    response_class.object_config_graph_node_id = response_node.id
    if include_source_layouts:
        request_node.layouts = [
            ObjectConfigGraphNodeLayout(
                object_config_graph_node_id=request_node.id,
                layout_kind="aware",
                relative_path="door/service.aware",
                source_position=13,
            )
        ]
        response_node.layouts = [
            ObjectConfigGraphNodeLayout(
                object_config_graph_node_id=response_node.id,
                layout_kind="aware",
                relative_path="door/service.aware",
                source_position=89,
            )
        ]
    nodes = [request_node, response_node]
    return ObjectConfigGraph(
        id=graph_id,
        name="home-api",
        fqn_prefix="aware_home_api",
        hash="sha256:home_api",
        language=CodeLanguage.aware,
        object_config_graph_nodes=nodes,
    )


def _home_ontology_context_graph() -> ObjectConfigGraph:
    graph_id = uuid4()
    door_class = ClassConfig(
        id=uuid4(),
        class_fqn="aware_home.home.Door",
        name="Door",
        is_base=True,
        class_config_attribute_configs=[],
    )
    return ObjectConfigGraph(
        id=graph_id,
        name="home-ontology",
        fqn_prefix="aware_home",
        hash="sha256:home_ontology",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=door_class.class_fqn,
                object_config_graph_id=graph_id,
                class_config=door_class,
            ),
        ],
    )


def test_runtime_dependency_source_digest_ignores_runtime_tree(tmp_path: Path) -> None:
    module_root = tmp_path / "proof_module"
    package_root = module_root / "structure" / "ontology"
    aware_root = package_root / "aware"
    runtime_root = module_root / "runtime"
    aware_root.mkdir(parents=True, exist_ok=True)
    runtime_root.mkdir(parents=True, exist_ok=True)

    aware_toml_path = package_root / "aware.toml"
    real_spec_path = (
        _REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "storage"
        / "ontology"
        / "structure"
        / "aware.toml"
    )
    aware_toml_path.write_text(
        real_spec_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (aware_root / "proof.aware").write_text("class Proof {}\n", encoding="utf-8")
    (runtime_root / "handler.py").write_text("VALUE = 1\n", encoding="utf-8")

    package = _RuntimeDependencyPackage(
        package_name="proof-ontology",
        aware_toml_path=aware_toml_path.resolve(),
        package_root=package_root.resolve(),
        spec=load_aware_toml_spec(toml_path=aware_toml_path),
    )

    digest_before = _compute_runtime_dependency_source_digest(package=package)
    (runtime_root / "handler.py").write_text("VALUE = 2\n", encoding="utf-8")
    digest_after_runtime_change = _compute_runtime_dependency_source_digest(
        package=package
    )
    assert digest_after_runtime_change == digest_before

    (aware_root / "proof.aware").write_text(
        "class Proof { value String? }\n", encoding="utf-8"
    )
    digest_after_authored_change = _compute_runtime_dependency_source_digest(
        package=package
    )
    assert digest_after_authored_change != digest_before


def test_runtime_dependency_outputs_fresh_for_inputs_without_digest(
    tmp_path: Path,
) -> None:
    module_root = tmp_path / "proof_module"
    package_root = module_root / "structure" / "ontology"
    aware_root = package_root / "aware"
    aware_root.mkdir(parents=True, exist_ok=True)

    aware_toml_path = package_root / "aware.toml"
    real_spec_path = (
        _REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "storage"
        / "ontology"
        / "structure"
        / "aware.toml"
    )
    aware_toml_path.write_text(
        real_spec_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (aware_root / "proof.aware").write_text("class Proof {}\n", encoding="utf-8")

    package = _RuntimeDependencyPackage(
        package_name="proof-ontology",
        aware_toml_path=aware_toml_path.resolve(),
        package_root=package_root.resolve(),
        spec=load_aware_toml_spec(toml_path=aware_toml_path),
    )

    runtime_manifest_path = package.runtime_manifest_path
    runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path.write_text("{}", encoding="utf-8")
    package.python_models_path.parent.mkdir(parents=True, exist_ok=True)
    package.python_models_path.write_text(
        ModelsManifest(
            language="python",
            classes=[
                ClassModelEntry(
                    class_config_id=uuid4(),
                    module="proof",
                    name="Proof",
                    aware_class_ref="aware_proof.proof.Proof",
                )
            ],
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )
    outputs_mtime_ns = (
        max(
            aware_toml_path.stat().st_mtime_ns,
            (aware_root / "proof.aware").stat().st_mtime_ns,
        )
        + 10_000_000
    )
    os.utime(runtime_manifest_path, ns=(outputs_mtime_ns, outputs_mtime_ns))
    os.utime(package.python_models_path, ns=(outputs_mtime_ns, outputs_mtime_ns))

    assert _runtime_dependency_outputs_are_fresh_for_inputs(package=package) is True

    (aware_root / "proof.aware").write_text(
        "class Proof { value String? }\n", encoding="utf-8"
    )
    newer_input_mtime_ns = outputs_mtime_ns + 10_000_000
    os.utime(
        aware_root / "proof.aware", ns=(newer_input_mtime_ns, newer_input_mtime_ns)
    )

    assert _runtime_dependency_outputs_are_fresh_for_inputs(package=package) is False


def test_load_api_dependency_class_config_ids_uses_existing_models_metadata_without_runtime_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    api_root = tmp_path / "apis" / "types" / "home"
    ontology_root = tmp_path / "modules" / "home" / "structure" / "ontology"

    request_id = uuid4()
    response_id = uuid4()
    ontology_id = uuid4()
    _write_dependency_python_models(
        package_root=api_root,
        entries=[
            ClassModelEntry(
                class_config_id=request_id,
                module="aware_home_api.door.lock_door",
                name="LockDoor",
                aware_class_ref="aware_home_api.default.door.LockDoor",
            ),
            ClassModelEntry(
                class_config_id=response_id,
                module="aware_home_api.door.lock_door_result",
                name="LockDoorResult",
                aware_class_ref="aware_home_api.door.LockDoorResult",
            ),
        ],
    )
    _write_dependency_python_models(
        package_root=ontology_root,
        ontology_runtime=True,
        entries=[
            ClassModelEntry(
                class_config_id=ontology_id,
                module="aware_home_ontology.home.door",
                name="Door",
                aware_class_ref="aware_home.home.Door",
            ),
        ],
    )

    monkeypatch.setattr(
        "aware_api_runtime.dependencies.runtime_resolution._build_runtime_dependency_package",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("dependency build should not run")
        ),
    )

    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    class_config_id_by_ref = load_api_dependency_class_config_ids(snapshot=snapshot)

    assert class_config_id_by_ref["aware_home_api.default.door.LockDoor"] == request_id
    assert class_config_id_by_ref["aware_home_api.door.LockDoor"] == request_id
    assert class_config_id_by_ref["aware_home_api.door.LockDoorResult"] == response_id
    assert class_config_id_by_ref["aware_home.home.Door"] == ontology_id


def test_load_api_dependency_class_config_ids_rejects_missing_models_metadata_without_runtime_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    ontology_root = tmp_path / "modules" / "home" / "structure" / "ontology"

    ontology_id = uuid4()
    _write_dependency_python_models(
        package_root=ontology_root,
        ontology_runtime=True,
        entries=[
            ClassModelEntry(
                class_config_id=ontology_id,
                module="aware_home_ontology.home.door",
                name="Door",
                aware_class_ref="aware_home.home.Door",
            ),
        ],
    )

    monkeypatch.setattr(
        "aware_api_runtime.dependencies.runtime_resolution._build_runtime_dependency_package",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("dependency build should not run")
        ),
    )

    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    with pytest.raises(RuntimeError, match="Structure repository fallback is retired"):
        load_api_dependency_class_config_ids(snapshot=snapshot)


def test_load_api_dependency_class_config_ids_honors_namespace_mapping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_explicit_namespace_dependency_workspace(tmp_path)
    api_root = tmp_path / "apis" / "types" / "home"
    _write_dependency_python_models(
        package_root=api_root,
        entries=[
            ClassModelEntry(
                class_config_id=uuid4(),
                module="aware_home_api.comms.models.door_command",
                name="DoorCommand",
                aware_class_ref="aware_home_api.comms.models.DoorCommand",
            ),
            ClassModelEntry(
                class_config_id=uuid4(),
                module="aware_home_api.comms.models.lock_door",
                name="LockDoor",
                aware_class_ref="aware_home_api.comms.models.LockDoor",
            ),
            ClassModelEntry(
                class_config_id=uuid4(),
                module="aware_home_api.comms.models.lock_door_result",
                name="LockDoorResult",
                aware_class_ref="aware_home_api.comms.models.LockDoorResult",
            ),
        ],
    )

    monkeypatch.setattr(
        "aware_api_runtime.dependencies.runtime_resolution._build_runtime_dependency_package",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("dependency build should not run")
        ),
    )

    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    class_config_id_by_ref = load_api_dependency_class_config_ids(snapshot=snapshot)

    assert "aware_home_api.comms.models.DoorCommand" in class_config_id_by_ref
    assert "aware_home_api.comms.models.LockDoor" in class_config_id_by_ref
    assert "aware_home_api.comms.models.LockDoorResult" in class_config_id_by_ref


def test_resolve_api_package_spec_uses_context_graph_class_ids_without_authored_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    request_class_config_id = uuid4()
    response_class_config_id = uuid4()
    context_graph = _home_api_context_graph(
        request_class_config_id=request_class_config_id,
        response_class_config_id=response_class_config_id,
    )

    def _authored_fallback_should_not_run(**_: object) -> object:
        raise AssertionError("authored fallback should not run")

    monkeypatch.setattr(
        "aware_api_runtime.ir.compile_plan.load_api_dependency_class_config_ids",
        _authored_fallback_should_not_run,
    )

    spec = api_materialization_service.resolve_api_package_materialization_spec(
        api_toml_path=toml_path,
        workspace_root=tmp_path,
        accessible_graphs=(_home_ontology_context_graph(), context_graph),
    )

    ontology_payload = spec.compile_plan_payload["api_ontology"][0]
    assert ontology_payload["capability_endpoint_request_configs"][0][
        "class_config_id"
    ] == str(request_class_config_id)
    assert ontology_payload["capability_endpoint_response_configs"][0][
        "class_config_id"
    ] == str(response_class_config_id)


def test_api_dependency_graph_context_rejects_stale_runtime_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    request_class_config_id = uuid4()
    response_class_config_id = uuid4()
    fresh_api_graph = _home_api_context_graph(
        request_class_config_id=request_class_config_id,
        response_class_config_id=response_class_config_id,
    )
    stale_api_graph = _test_object_config_graph(
        package_name="home-api",
        fqn_prefix="aware_home_api",
        class_fqns=("aware_home_api.door.OldDoorRequest",),
    )
    ontology_graph = _home_ontology_context_graph()

    monkeypatch.setattr(
        api_materialization_service,
        "_complete_dependency_context_graphs_from_runtime_artifact",
        lambda **_: (ontology_graph, stale_api_graph),
    )
    monkeypatch.setattr(
        api_materialization_service,
        "load_api_accessible_dependency_graphs",
        lambda **_: (ontology_graph, fresh_api_graph),
    )

    context = api_materialization_service._api_dependency_graph_context(  # noqa: SLF001
        snapshot=snapshot,
        accessible_graphs=(),
        phase_timings_s={},
    )

    assert context.source == "dependency_runtime_artifacts"
    assert context.class_config_ids["aware_home_api.door.LockDoor"] == (
        request_class_config_id
    )
    assert context.class_config_ids["aware_home_api.door.LockDoorResult"] == (
        response_class_config_id
    )


def test_api_dependency_graph_context_rejects_missing_source_owned_api_dto_runtime_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    with toml_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "",
                    "[[semantic_package_exports]]",
                    'kind = "api_dto"',
                    'package_name = "home-api"',
                    'manifest_path = "apis/types/home/aware.toml"',
                    "",
                ]
            )
        )
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    stale_api_graph = _test_object_config_graph(
        package_name="home-api",
        fqn_prefix="aware_home_api",
        class_fqns=(
            "aware_home_api.door.LockDoor",
            "aware_home_api.door.LockDoorResult",
            "aware_home_api.door.RemovedProgramEndpoint",
        ),
    )
    ontology_graph = _home_ontology_context_graph()
    monkeypatch.setattr(
        api_materialization_service,
        "_complete_dependency_context_graphs_from_runtime_artifact",
        lambda **_: (ontology_graph, stale_api_graph),
    )
    monkeypatch.setattr(
        api_materialization_service,
        "load_api_accessible_dependency_graph_source_digests",
        lambda **_: {},
    )
    monkeypatch.setattr(
        api_materialization_service,
        "_load_existing_runtime_dependency_object_config_graph",
        lambda **_: None,
    )

    with pytest.raises(RuntimeError, match="Structure repository fallback is retired"):
        api_materialization_service._api_dependency_graph_context(  # noqa: SLF001
            snapshot=snapshot,
            accessible_graphs=(),
            phase_timings_s={},
        )


def test_complete_runtime_dependency_graph_artifact_requires_all_dependency_digests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    with toml_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "",
                    "[[semantic_package_exports]]",
                    'kind = "api_dto"',
                    'package_name = "home-api"',
                    'manifest_path = "apis/types/home/aware.toml"',
                    "",
                ]
            )
        )
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot

    monkeypatch.setattr(
        api_materialization_service,
        "_compute_runtime_dependency_source_digest",
        lambda *, package: f"current-{package.package_name}",
    )
    monkeypatch.setattr(
        api_materialization_service,
        "load_api_accessible_dependency_graph_source_digests",
        lambda **_: {"home-api": "current-home-api"},
    )
    monkeypatch.setattr(
        api_materialization_service,
        "load_api_accessible_dependency_graphs_from_runtime_artifact",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("stale complete artifact should not be loaded")
        ),
    )

    assert (
        api_materialization_service._complete_dependency_context_graphs_from_runtime_artifact(  # noqa: SLF001
            snapshot=snapshot,
            dependency_repo_roots=(),
        )
        is None
    )


def test_api_dependency_graph_context_keeps_fresh_source_owned_api_dto_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    with toml_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "",
                    "[[semantic_package_exports]]",
                    'kind = "api_dto"',
                    'package_name = "home-api"',
                    'manifest_path = "apis/types/home/aware.toml"',
                    "",
                ]
            )
        )
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    api_graph = _home_api_context_graph()
    ontology_graph = _home_ontology_context_graph()

    monkeypatch.setattr(
        api_materialization_service,
        "_complete_dependency_context_graphs_from_runtime_artifact",
        lambda **_: (ontology_graph, api_graph),
    )
    monkeypatch.setattr(
        api_materialization_service,
        "_compute_runtime_dependency_source_digest",
        lambda **_: "current-digest",
    )
    monkeypatch.setattr(
        api_materialization_service,
        "load_api_accessible_dependency_graph_source_digests",
        lambda **_: {"home-api": "current-digest"},
    )

    monkeypatch.setattr(
        api_materialization_service,
        "_load_required_runtime_dependency_object_config_graph",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("fresh source-owned API DTO artifact should be reused")
        ),
    )

    context = api_materialization_service._api_dependency_graph_context(  # noqa: SLF001
        snapshot=snapshot,
        accessible_graphs=(),
        phase_timings_s={},
    )

    assert context.source == "runtime_accessible_dependency_graphs_artifact"
    assert context.accessible_graphs == (ontology_graph, api_graph)


def test_api_dependency_graph_context_refreshes_source_owned_api_dto_without_layouts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    with toml_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "",
                    "[[semantic_package_exports]]",
                    'kind = "api_dto"',
                    'package_name = "home-api"',
                    'manifest_path = "apis/types/home/aware.toml"',
                    "",
                ]
            )
        )
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    layoutless_api_graph = _home_api_context_graph(include_source_layouts=False)
    refreshed_api_graph = _home_api_context_graph()
    ontology_graph = _home_ontology_context_graph()
    refreshed: list[str] = []

    monkeypatch.setattr(
        api_materialization_service,
        "_complete_dependency_context_graphs_from_runtime_artifact",
        lambda **_: (ontology_graph, layoutless_api_graph),
    )
    monkeypatch.setattr(
        api_materialization_service,
        "_compute_runtime_dependency_source_digest",
        lambda **_: "current-digest",
    )
    monkeypatch.setattr(
        api_materialization_service,
        "load_api_accessible_dependency_graph_source_digests",
        lambda **_: {"home-api": "current-digest"},
    )

    def _load_existing_runtime_dependency_object_config_graph(**_: object) -> object:
        refreshed.append("home-api")
        return refreshed_api_graph

    monkeypatch.setattr(
        api_materialization_service,
        "_load_existing_runtime_dependency_object_config_graph",
        _load_existing_runtime_dependency_object_config_graph,
    )

    context = api_materialization_service._api_dependency_graph_context(  # noqa: SLF001
        snapshot=snapshot,
        accessible_graphs=(),
        phase_timings_s={},
    )

    assert context.source == (
        "runtime_accessible_dependency_graphs_artifact"
        "_with_source_owned_api_dto_refresh"
    )
    assert refreshed == ["home-api"]
    assert context.accessible_graphs == (ontology_graph, refreshed_api_graph)


def test_api_dependency_graph_context_reuses_complete_workspace_semantic_context_for_materialization(
    tmp_path: Path,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    request_class_config_id = uuid4()
    response_class_config_id = uuid4()
    api_graph = _home_api_context_graph(
        request_class_config_id=request_class_config_id,
        response_class_config_id=response_class_config_id,
    )
    ontology_graph = _home_ontology_context_graph()

    graphs = api_materialization_service._api_dependency_graph_context_reusable_graphs_for_materialization(  # noqa: SLF001
        snapshot=snapshot,
        accessible_graphs=(ontology_graph, api_graph),
        source="workspace_semantic_context",
        dependency_repo_roots=(),
    )

    assert graphs is not None
    assert tuple(graph.name for graph in graphs) == ("home-ontology", "home-api")
    class_config_ids = (
        api_materialization_service.collect_api_dependency_class_config_ids_from_graphs(
            accessible_graphs=graphs,
        )
    )
    assert class_config_ids["aware_home_api.door.LockDoor"] == request_class_config_id
    assert (
        class_config_ids["aware_home_api.door.LockDoorResult"]
        == response_class_config_id
    )


def test_api_dependency_graph_context_does_not_reuse_layoutless_source_owned_workspace_context(
    tmp_path: Path,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    with toml_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "",
                    "[[semantic_package_exports]]",
                    'kind = "api_dto"',
                    'package_name = "home-api"',
                    'manifest_path = "apis/types/home/aware.toml"',
                    "",
                ]
            )
        )
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    layoutless_api_graph = _home_api_context_graph(include_source_layouts=False)
    ontology_graph = _home_ontology_context_graph()

    graphs = api_materialization_service._api_dependency_graph_context_reusable_graphs_for_materialization(  # noqa: SLF001
        snapshot=snapshot,
        accessible_graphs=(ontology_graph, layoutless_api_graph),
        source="workspace_semantic_context",
        dependency_repo_roots=(),
    )

    assert graphs is None


@pytest.mark.asyncio
async def test_source_owned_api_dto_pre_resolve_reuses_complete_runtime_graph_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    with toml_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "",
                    "[[semantic_package_exports]]",
                    'kind = "api_dto"',
                    'package_name = "home-api"',
                    'manifest_path = "apis/types/home/aware.toml"',
                    "",
                ]
            )
        )
    api_graph = _home_api_context_graph()
    ontology_graph = _home_ontology_context_graph()

    monkeypatch.setattr(
        api_materialization_service,
        "_complete_dependency_context_graphs_from_runtime_artifact",
        lambda **_: (ontology_graph, api_graph),
    )
    monkeypatch.setattr(
        api_materialization_service,
        "_compute_runtime_dependency_source_digest",
        lambda **_: "current-digest",
    )
    monkeypatch.setattr(
        api_materialization_service,
        "load_api_accessible_dependency_graph_source_digests",
        lambda **_: {"home-api": "current-digest"},
    )
    monkeypatch.setattr(
        api_materialization_service,
        "_available_dependency_context_graphs_from_runtime_artifacts",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("complete runtime graph cache should be enough")
        ),
    )

    async def _meta_compile_should_not_run(
        **_: object,
    ) -> tuple[ObjectConfigGraph, ...]:
        raise AssertionError("fresh complete runtime graph cache should be reused")

    monkeypatch.setattr(
        api_materialization_service,
        "build_api_accessible_dependency_graphs_via_meta_runtime",
        _meta_compile_should_not_run,
    )

    graphs = await api_materialization_service.resolve_source_owned_api_dto_export_accessible_graphs(
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        api_toml_path=toml_path,
    )

    assert graphs == (ontology_graph, api_graph)


@pytest.mark.asyncio
async def test_source_owned_api_dto_pre_resolve_refreshes_only_stale_export_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    with toml_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "",
                    "[[semantic_package_exports]]",
                    'kind = "api_dto"',
                    'package_name = "home-api"',
                    'manifest_path = "apis/types/home/aware.toml"',
                    "",
                ]
            )
        )
    stale_api_graph = _home_api_context_graph()
    refreshed_api_graph = _home_api_context_graph()
    ontology_graph = _home_ontology_context_graph()
    refresh_inputs: list[tuple[str | None, ...]] = []

    monkeypatch.setattr(
        api_materialization_service,
        "_complete_dependency_context_graphs_from_runtime_artifact",
        lambda **_: (ontology_graph, stale_api_graph),
    )
    monkeypatch.setattr(
        api_materialization_service,
        "_compute_runtime_dependency_source_digest",
        lambda **_: "current-digest",
    )
    monkeypatch.setattr(
        api_materialization_service,
        "load_api_accessible_dependency_graph_source_digests",
        lambda **_: {"home-api": "stale-digest"},
    )
    monkeypatch.setattr(
        api_materialization_service,
        "_source_owned_api_dto_graph_cache_is_fresh_for_inputs",
        lambda **_: False,
    )
    monkeypatch.setattr(
        api_materialization_service,
        "find_meta_graph_projection_hash_by_name",
        lambda **_: "projection-hash",
    )

    async def _refresh_via_meta(
        *,
        accessible_graphs: tuple[ObjectConfigGraph, ...],
        **_: object,
    ) -> tuple[ObjectConfigGraph, ...]:
        refresh_inputs.append(tuple(graph.name for graph in accessible_graphs))
        return (ontology_graph, refreshed_api_graph)

    monkeypatch.setattr(
        api_materialization_service,
        "build_api_accessible_dependency_graphs_via_meta_runtime",
        _refresh_via_meta,
    )

    graphs = await api_materialization_service.resolve_source_owned_api_dto_export_accessible_graphs(
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        api_toml_path=toml_path,
    )

    assert refresh_inputs == [("home-ontology",)]
    assert graphs == (ontology_graph, refreshed_api_graph)


def test_api_product_runtime_materialization_uses_compile_plan_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context_graph = _home_api_context_graph()
    compile_plan_payload = {
        "schema_version": 9,
        "package_name": "dependency-proof-service-api",
        "fqn_prefix": "aware_dependency_proof_service_api",
        "source_files": ["bindings/service.apis.aware"],
        "api_ownership": [],
        "api_ontology": [],
    }
    snapshot = SimpleNamespace(
        spec=SimpleNamespace(
            targets=SimpleNamespace(dart=None),
            semantic_package_exports=(object(),),
        ),
    )
    observed: dict[str, object] = {}

    def _legacy_compile_should_not_run(**_: object) -> object:
        raise AssertionError("legacy TOML compile should not run")

    def _compile_from_plan(**kwargs: object) -> object:
        observed.update(kwargs)
        return SimpleNamespace(service_protocol_materialization=object())

    monkeypatch.setattr(
        "aware_api_runtime.compile.compile_api_workspace",
        _legacy_compile_should_not_run,
    )
    monkeypatch.setattr(
        "aware_api_runtime.compile.compile_api_product_runtime_from_compile_plan_payload",
        _compile_from_plan,
    )

    (
        compile_result,
        dart_result,
        post_step_receipts,
    ) = api_materialization_service._materialize_api_product_runtime_artifacts_for_language_packages(  # noqa: SLF001
        api_toml_path=tmp_path / "aware.api.toml",
        workspace_root=tmp_path,
        snapshot=cast(Any, snapshot),
        runtime_compile_plan_payload=compile_plan_payload,
        accessible_graphs=(context_graph,),
        dependency_repo_roots=(),
        phase_timings_s={},
        post_step_tool_env_by_tool_id=None,
        post_step_executable_overrides_by_tool_id=None,
    )

    assert compile_result.service_protocol_materialization is not None
    assert dart_result is None
    assert post_step_receipts == ()
    assert observed["compile_plan_payload"] == compile_plan_payload
    assert observed["repo_root"] == tmp_path
    assert observed["accessible_graphs"] == (context_graph,)


def test_load_api_accessible_dependency_graphs_requires_runtime_artifacts_without_runtime_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)

    monkeypatch.setattr(
        "aware_api_runtime.dependencies.runtime_resolution._build_runtime_dependency_package",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("dependency runtime build should not run")
        ),
    )

    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    with pytest.raises(RuntimeError, match="Structure repository fallback is retired"):
        load_api_accessible_dependency_graphs(snapshot=snapshot)


def _test_object_config_graph(
    *,
    package_name: str,
    fqn_prefix: str,
    class_fqns: tuple[str, ...] = (),
) -> ObjectConfigGraph:
    graph_id = uuid4()
    nodes: list[ObjectConfigGraphNode] = []
    for class_fqn in class_fqns:
        class_name = class_fqn.rsplit(".", 1)[-1]
        class_config = ClassConfig.model_construct(
            id=uuid4(),
            class_fqn=class_fqn,
            name=class_name,
            class_config_attribute_configs=[],
            class_config_function_configs=[],
            class_config_relationships=[],
        )
        node = ObjectConfigGraphNode.model_construct(
            id=uuid4(),
            type=ObjectConfigGraphNodeType.class_,
            node_key=class_fqn,
            object_config_graph_id=graph_id,
            class_config=class_config,
            layouts=[],
        )
        class_config.object_config_graph_node_id = node.id
        nodes.append(node)
    return ObjectConfigGraph.model_construct(
        id=graph_id,
        name=package_name,
        hash=f"sha256:{package_name}",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_annotations=[],
        object_config_graph_mirrors=[],
        object_config_graph_nodes=nodes,
        object_config_graph_overlays=[],
        object_config_graph_bindings=[],
        object_config_graph_relationships=[],
        object_projection_graph_declarations=[],
        object_projection_graphs=[],
    )


def _attach_home_door_projection(graph: ObjectConfigGraph) -> None:
    declaration_id = uuid4()
    graph.object_projection_graph_declarations.append(
        ObjectProjectionGraphDeclaration.model_construct(
            id=declaration_id,
            key="aware_home:DoorView",
            projection_name="DoorView",
            object_config_graph_id=graph.id,
            object_projection_graph_bindings=[
                ObjectProjectionGraphBinding.model_construct(
                    id=uuid4(),
                    fqn_prefix="aware_home",
                    domain_name="default",
                    schema_name="home",
                    class_name="Door",
                    attribute_name=None,
                    target_projection_name=None,
                    side=None,
                    object_projection_graph_declaration_id=declaration_id,
                )
            ],
        )
    )


@pytest.mark.asyncio
async def test_api_lane_root_hydration_uses_meta_oig_reifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = SimpleNamespace()
    branch_id = uuid4()
    root_id = uuid4()
    opg = SimpleNamespace(projection_hash="api-test-projection")
    oig = SimpleNamespace(id=uuid4())
    root = SimpleNamespace(id=root_id)
    captured: dict[str, object] = {}

    async def _fake_oig_from_head(**kwargs: object) -> object:
        captured["oig_kwargs"] = kwargs
        return opg, oig

    def _fake_reify(**kwargs: object) -> object:
        captured["reify_kwargs"] = kwargs
        return root

    monkeypatch.setattr(
        api_materialization_service,
        "_hydrate_lane_oig_from_head",
        _fake_oig_from_head,
    )
    monkeypatch.setattr(
        api_materialization_service,
        "reify_oig_root_model",
        _fake_reify,
    )

    hydrated = await api_materialization_service._hydrate_lane_root_from_head(
        index=cast(Any, index),
        branch_id=branch_id,
        projection_hash="api-test-projection",
        root_id=root_id,
        root_type=cast(Any, Api),
    )

    assert hydrated is root
    assert captured["oig_kwargs"] == {
        "index": index,
        "branch_id": branch_id,
        "projection_hash": "api-test-projection",
    }
    assert captured["reify_kwargs"] == {
        "index": index,
        "opg": opg,
        "oig": oig,
        "model_type": Api,
        "root_id": root_id,
        "branch_id": branch_id,
    }


@pytest.mark.asyncio
async def test_api_accessible_dependency_graphs_use_meta_runtime_package_materialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    calls: list[dict[str, object]] = []

    async def _fake_materialize_meta_package(**kwargs: object) -> SimpleNamespace:
        calls.append(dict(kwargs))
        aware_toml_path = Path(str(kwargs["aware_toml_path"]))
        spec = load_aware_toml_spec(toml_path=aware_toml_path)
        package_name = spec.package.package_name
        fqn_prefix = spec.package.fqn_prefix
        assert kwargs[
            "package_branch_id"
        ] == stable_object_config_graph_package_branch_id(
            workspace_root=tmp_path,
            aware_toml_path=aware_toml_path,
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        )
        if package_name == "home-ontology":
            assert kwargs["external_graphs"] == []
        elif package_name == "home-api":
            dependency_graphs = cast(list[ObjectConfigGraph], kwargs["external_graphs"])
            assert [graph.name for graph in dependency_graphs] == ["home-ontology"]
        else:  # pragma: no cover - defensive fixture guard
            raise AssertionError(f"unexpected package compile request: {package_name}")

        graph = _test_object_config_graph(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        )
        return _fake_meta_leaf_result(graph)

    monkeypatch.setattr(
        "aware_api_runtime.compile_materialization.service.materialize_object_config_graph_package_leaf_from_manifest",
        _fake_materialize_meta_package,
    )

    graphs = await build_api_accessible_dependency_graphs_via_meta_runtime(
        snapshot=snapshot,
        runtime=cast(Any, object()),
        index=cast(Any, SimpleNamespace(opg_by_hash={})),
        actor_id=None,
        branch_id=uuid4(),
        target_projection_hash="ObjectConfigGraphPackage",
        object_config_graph_projection_hash="",
        include_object_config_graph=True,
    )

    assert [
        load_aware_toml_spec(
            toml_path=Path(str(call["aware_toml_path"]))
        ).package.package_name
        for call in calls
    ] == ["home-ontology", "home-api"]
    assert [Path(str(call["workspace_root"])).as_posix() for call in calls] == [
        tmp_path.as_posix(),
        tmp_path.as_posix(),
    ]
    assert [graph.name for graph in graphs] == ["home-ontology", "home-api"]


@pytest.mark.asyncio
async def test_api_meta_runtime_materialization_reuses_available_dependency_graphs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    home_ontology = _test_object_config_graph(
        package_name="home-ontology",
        fqn_prefix="aware_home",
        class_fqns=("aware_home.default.home.Door",),
    )
    calls: list[dict[str, object]] = []

    async def _fake_materialize_meta_package(**kwargs: object) -> SimpleNamespace:
        calls.append(dict(kwargs))
        aware_toml_path = Path(str(kwargs["aware_toml_path"]))
        spec = load_aware_toml_spec(toml_path=aware_toml_path)
        assert spec.package.package_name == "home-api"
        dependency_graphs = cast(list[ObjectConfigGraph], kwargs["external_graphs"])
        assert [graph.name for graph in dependency_graphs] == ["home-ontology"]
        assert dependency_graphs[0].id == home_ontology.id
        graph = _test_object_config_graph(
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
        )
        return _fake_meta_leaf_result(graph)

    monkeypatch.setattr(
        "aware_api_runtime.compile_materialization.service.materialize_object_config_graph_package_leaf_from_manifest",
        _fake_materialize_meta_package,
    )

    graphs = await build_api_accessible_dependency_graphs_via_meta_runtime(
        snapshot=snapshot,
        runtime=cast(Any, object()),
        index=cast(Any, SimpleNamespace(opg_by_hash={})),
        actor_id=None,
        branch_id=uuid4(),
        target_projection_hash="ObjectConfigGraphPackage",
        object_config_graph_projection_hash="",
        include_object_config_graph=True,
        accessible_graphs=(home_ontology,),
    )

    assert [
        load_aware_toml_spec(
            toml_path=Path(str(call["aware_toml_path"]))
        ).package.package_name
        for call in calls
    ] == ["home-api"]
    assert [graph.name for graph in graphs] == ["home-ontology", "home-api"]


@pytest.mark.asyncio
async def test_api_meta_runtime_materialization_refreshes_source_owned_dto_without_layouts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    with toml_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "",
                    "[[semantic_package_exports]]",
                    'kind = "api_dto"',
                    'package_name = "home-api"',
                    'manifest_path = "apis/types/home/aware.toml"',
                    "",
                ]
            )
        )
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    home_ontology = _test_object_config_graph(
        package_name="home-ontology",
        fqn_prefix="aware_home",
        class_fqns=("aware_home.default.home.Door",),
    )
    layoutless_home_api = _home_api_context_graph(include_source_layouts=False)
    calls: list[dict[str, object]] = []

    async def _fake_materialize_meta_package(**kwargs: object) -> SimpleNamespace:
        calls.append(dict(kwargs))
        aware_toml_path = Path(str(kwargs["aware_toml_path"]))
        spec = load_aware_toml_spec(toml_path=aware_toml_path)
        assert spec.package.package_name == "home-api"
        graph = _home_api_context_graph()
        return _fake_meta_leaf_result(graph)

    monkeypatch.setattr(
        "aware_api_runtime.compile_materialization.service.materialize_object_config_graph_package_leaf_from_manifest",
        _fake_materialize_meta_package,
    )

    graphs = await build_api_accessible_dependency_graphs_via_meta_runtime(
        snapshot=snapshot,
        runtime=cast(Any, object()),
        index=cast(Any, SimpleNamespace(opg_by_hash={})),
        actor_id=None,
        branch_id=uuid4(),
        target_projection_hash="ObjectConfigGraphPackage",
        object_config_graph_projection_hash="",
        include_object_config_graph=True,
        accessible_graphs=(home_ontology, layoutless_home_api),
    )

    assert [
        load_aware_toml_spec(
            toml_path=Path(str(call["aware_toml_path"]))
        ).package.package_name
        for call in calls
    ] == ["home-api"]
    assert [graph.name for graph in graphs] == ["home-ontology", "home-api"]
    refreshed_home_api = graphs[1]
    assert refreshed_home_api.object_config_graph_nodes[0].layouts


@pytest.mark.asyncio
async def test_api_meta_runtime_materialization_uses_dependency_package_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspaces" / "aware_workspace"
    kernel_root = tmp_path / "kernel"
    api_toml_path = workspace_root / "aware.api.toml"
    api_toml_path.parent.mkdir(parents=True, exist_ok=True)
    api_toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "split-root-service-api"',
                'fqn_prefix = "aware_split_root_service_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "home-ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    bindings_root = workspace_root / "bindings"
    bindings_root.mkdir(parents=True, exist_ok=True)
    (bindings_root / "service.apis.aware").write_text(
        "api split_root {}\n", encoding="utf-8"
    )
    package_root = kernel_root / "modules" / "home" / "structure" / "ontology"
    (package_root / "aware" / "home").mkdir(parents=True, exist_ok=True)
    aware_toml_path = package_root / "aware.toml"
    aware_toml_path.write_text(
        "\n".join(
            [
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
            ]
        ),
        encoding="utf-8",
    )
    (package_root / "aware" / "home" / "door.aware").write_text(
        "class Door {}\n", encoding="utf-8"
    )
    monkeypatch.setenv("AWARE_KERNEL_REPO_ROOT", str(kernel_root))
    snapshot = compile_api_workspace(
        toml_path=api_toml_path,
        repo_root=workspace_root,
    ).snapshot
    calls: list[dict[str, object]] = []

    async def _fake_materialize_meta_package(**kwargs: object) -> SimpleNamespace:
        calls.append(dict(kwargs))
        spec = load_aware_toml_spec(toml_path=aware_toml_path)
        graph = _test_object_config_graph(
            package_name=spec.package.package_name,
            fqn_prefix=spec.package.fqn_prefix,
        )
        return _fake_meta_leaf_result(graph)

    monkeypatch.setattr(
        "aware_api_runtime.compile_materialization.service.materialize_object_config_graph_package_leaf_from_manifest",
        _fake_materialize_meta_package,
    )

    graphs = await build_api_accessible_dependency_graphs_via_meta_runtime(
        snapshot=snapshot,
        runtime=cast(Any, object()),
        index=cast(Any, SimpleNamespace(opg_by_hash={})),
        actor_id=None,
        branch_id=uuid4(),
        target_projection_hash="ObjectConfigGraphPackage",
        object_config_graph_projection_hash="",
        include_object_config_graph=True,
    )

    assert [graph.name for graph in graphs] == ["home-ontology"]
    assert len(calls) == 1
    call = calls[0]
    assert Path(str(call["workspace_root"])) == kernel_root.resolve()
    assert call["package_branch_id"] == stable_object_config_graph_package_branch_id(
        workspace_root=kernel_root,
        aware_toml_path=aware_toml_path,
        package_name="home-ontology",
        fqn_prefix="aware_home",
    )


@pytest.mark.asyncio
async def test_api_meta_runtime_dependency_graphs_preserve_local_opg_bodies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot

    async def _fake_materialize_meta_package(**kwargs: object) -> SimpleNamespace:
        aware_toml_path = Path(str(kwargs["aware_toml_path"]))
        spec = load_aware_toml_spec(toml_path=aware_toml_path)
        package_name = spec.package.package_name
        fqn_prefix = spec.package.fqn_prefix
        if package_name == "home-api":
            dependency_graphs = cast(list[ObjectConfigGraph], kwargs["external_graphs"])
            assert len(dependency_graphs) == 1
            assert dependency_graphs[0].object_projection_graph_declarations
            assert dependency_graphs[0].object_projection_graphs

        graph = _test_object_config_graph(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            class_fqns=(
                ("aware_home.default.home.Door",)
                if package_name == "home-ontology"
                else ()
            ),
        )
        if package_name == "home-ontology":
            _attach_home_door_projection(graph)

        return _fake_meta_leaf_result(graph)

    monkeypatch.setattr(
        "aware_api_runtime.compile_materialization.service.materialize_object_config_graph_package_leaf_from_manifest",
        _fake_materialize_meta_package,
    )

    graphs = await build_api_accessible_dependency_graphs_via_meta_runtime(
        snapshot=snapshot,
        runtime=cast(Any, object()),
        index=cast(Any, SimpleNamespace(opg_by_hash={})),
        actor_id=None,
        branch_id=uuid4(),
        target_projection_hash="ObjectConfigGraphPackage",
        object_config_graph_projection_hash="",
        include_object_config_graph=True,
    )

    home_graph = next(graph for graph in graphs if graph.name == "home-ontology")
    assert {opg.name for opg in home_graph.object_projection_graphs} == {"DoorView"}


@pytest.mark.asyncio
async def test_api_meta_runtime_package_materialization_failure_includes_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot

    async def _fake_materialize_meta_package(**_: object) -> SimpleNamespace:
        raise RuntimeError("synthetic commit failure")

    monkeypatch.setattr(
        "aware_api_runtime.compile_materialization.service.materialize_object_config_graph_package_leaf_from_manifest",
        _fake_materialize_meta_package,
    )

    with pytest.raises(RuntimeError) as exc_info:
        await build_api_accessible_dependency_graphs_via_meta_runtime(
            snapshot=snapshot,
            runtime=cast(Any, object()),
            index=cast(Any, SimpleNamespace(opg_by_hash={})),
            actor_id=None,
            branch_id=uuid4(),
            target_projection_hash="ObjectConfigGraphPackage",
            object_config_graph_projection_hash="",
            include_object_config_graph=True,
        )

    message = str(exc_info.value)
    assert "Direct Meta runtime package OCG materialization failed" in message
    assert "package_name='home-ontology'" in message
    assert "aware_toml_path=" in message
    assert "package_branch_id=" in message
    assert "error_type='RuntimeError'" in message
    assert "error='synthetic commit failure'" in message


@pytest.mark.asyncio
async def test_api_accessible_dependency_graphs_reuse_workspace_context_by_package_fqn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    home_ontology = _test_object_config_graph(
        package_name="aware_home",
        fqn_prefix="aware_home",
        class_fqns=("aware_home.default.home.Door",),
    )
    _attach_home_door_projection(home_ontology)
    home_api = _test_object_config_graph(
        package_name="aware_home_api",
        fqn_prefix="aware_home_api",
        class_fqns=(
            "aware_home_api.default.door.LockDoor",
            "aware_home_api.default.door.LockDoorResult",
        ),
    )

    async def _fail_meta_package_compile(*_: object, **__: object) -> object:
        raise AssertionError("Workspace semantic context should satisfy dependencies")

    monkeypatch.setattr(
        "aware_api_runtime.compile_materialization.service.materialize_object_config_graph_package_leaf_from_manifest",
        _fail_meta_package_compile,
    )

    graphs = await build_api_accessible_dependency_graphs_via_meta_runtime(
        snapshot=snapshot,
        runtime=cast(Any, object()),
        index=cast(Any, SimpleNamespace(opg_by_hash={})),
        actor_id=None,
        branch_id=uuid4(),
        target_projection_hash="ObjectConfigGraphPackage",
        object_config_graph_projection_hash="",
        include_object_config_graph=True,
        accessible_graphs=(home_ontology, home_api),
    )

    graph_by_fqn = {graph.fqn_prefix: graph for graph in graphs}
    assert sorted(graph_by_fqn) == ["aware_home", "aware_home_api"]
    assert {
        opg.name for opg in graph_by_fqn["aware_home"].object_projection_graphs
    } == {"DoorView"}


def test_compile_api_workspace_meta_runtime_graph_mode_feeds_plan_and_products(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    meta_calls: list[Path | None] = []

    def _fake_meta_dependency_compile(
        *,
        snapshot: object,
        kernel_repo_root: str | Path | None = None,
        dependency_repo_roots: Sequence[str | Path] = (),
    ) -> tuple[ObjectConfigGraph, ...]:
        assert dependency_repo_roots == ()
        meta_calls.append(None if kernel_repo_root is None else Path(kernel_repo_root))
        return (
            _test_object_config_graph(
                package_name="home-ontology",
                fqn_prefix="aware_home",
                class_fqns=("aware_home.default.home.Door",),
            ),
            _test_object_config_graph(
                package_name="home-api",
                fqn_prefix="aware_home_api",
                class_fqns=(
                    "aware_home_api.default.door.LockDoor",
                    "aware_home_api.default.door.LockDoorResult",
                ),
            ),
        )

    monkeypatch.setattr(
        "aware_api_runtime.compile.compile_api_accessible_dependency_graphs_via_meta_runtime",
        _fake_meta_dependency_compile,
    )

    def _fake_materialize_api_dto_packages(**_: object) -> tuple[object, ...]:
        return ()

    def _fake_materialize_service_protocol(**kwargs: object) -> object:
        plan = cast(Any, kwargs["plan"])
        runtime_package_dir = cast(Path, kwargs["runtime_package_dir"])
        runtime_package_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = runtime_package_dir / "api.compile_plan.json"
        artifact_path.write_text(
            json.dumps(encode_api_compile_plan_payload(plan=plan), sort_keys=True),
            encoding="utf-8",
        )
        artifact = SimpleNamespace(
            path=artifact_path,
            relpath=artifact_path.relative_to(tmp_path).as_posix(),
            hash_sha256="test-compile-plan-hash",
        )
        target = SimpleNamespace(package_root=tmp_path / "generated")
        public_package_materialization = SimpleNamespace(
            render_job=SimpleNamespace(target=target)
        )
        return SimpleNamespace(
            public_package_materialization=public_package_materialization,
            render_job=SimpleNamespace(target=target),
            runtime_artifacts=SimpleNamespace(compile_plan=artifact),
        )

    monkeypatch.setattr(
        "aware_api_runtime.compile.materialize_api_dto_packages",
        _fake_materialize_api_dto_packages,
    )
    monkeypatch.setattr(
        "aware_api_runtime.compile.materialize_api_service_protocol",
        _fake_materialize_service_protocol,
    )
    monkeypatch.setattr(
        "aware_api_runtime.compile.resolve_api_runtime_semantic_artifacts",
        lambda **_: None,
    )

    result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=tmp_path,
        materialize_service_protocol=True,
        dependency_graph_mode="meta_runtime",
        kernel_repo_root=_REPO_ROOT,
    )

    assert meta_calls == [_REPO_ROOT]
    assert result.dependency_graph_mode == "meta_runtime"
    assert result.accessible_dependency_graph_count == 2
    assert result.compile_plan is not None
    endpoint = result.compile_plan.api_ownership[0].capabilities[0].endpoints[0]
    assert endpoint.request_config.class_config_id is not None
    assert endpoint.request_config.response_config is not None
    assert endpoint.request_config.response_config.class_config_id is not None
    assert result.runtime_artifacts is not None
    payload = json.loads(result.runtime_artifacts.compile_plan.path.read_text())
    assert payload["api_ownership"][0]["capabilities"][0]["endpoints"][0][
        "request_config"
    ]["class_config_id"] == str(endpoint.request_config.class_config_id)
    manifest_path = (
        tmp_path
        / ".aware"
        / "api"
        / "runtime"
        / "dependency-proof-service-api"
        / "api.manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["dependency_graph_mode"] == "meta_runtime"
    assert manifest["accessible_dependency_graph_count"] == 2


def test_compile_api_workspace_rejects_compat_dependency_graph_mode(
    tmp_path: Path,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)

    with pytest.raises(ValueError, match="Expected 'meta_runtime'"):
        compile_api_workspace(
            toml_path=toml_path,
            repo_root=tmp_path,
            materialize_service_protocol=True,
            dependency_graph_mode="compat_authored",
        )


def test_compile_api_meta_runtime_uses_meta_package_manifest_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toml_path = _write_dependency_class_config_workspace(tmp_path)
    snapshot = compile_api_workspace(toml_path=toml_path, repo_root=tmp_path).snapshot
    kernel_root = (tmp_path / "kernel").resolve()
    manifest_paths = (
        kernel_root / "modules/code/ontology/structure/aware.toml",
        kernel_root / "modules/content/ontology/structure/aware.toml",
        kernel_root / "modules/history/ontology/structure/aware.toml",
        kernel_root / "modules/meta/ontology/structure/aware.toml",
    )
    runtime_index = SimpleNamespace(opg_by_hash={})
    runtime = SimpleNamespace(context=SimpleNamespace(index=runtime_index))
    captured: dict[str, Any] = {}

    def _fake_resolve_meta_manifest_closure(
        *,
        repo_root: Path,
        package_names: object,
    ) -> tuple[Path, ...]:
        captured["repo_root"] = repo_root
        captured["package_names"] = tuple(cast(Any, package_names))
        return manifest_paths

    def _fake_build_meta_runtime(**kwargs: Any) -> object:
        captured["runtime_kwargs"] = kwargs
        return runtime

    def _fake_projection_hash(
        *,
        index: object,
        projection_name: str,
    ) -> str:
        captured.setdefault("projection_lookups", []).append((index, projection_name))
        return f"sha256:test:{projection_name}"

    async def _fake_build_dependency_graphs(
        **kwargs: Any,
    ) -> tuple[ObjectConfigGraph, ...]:
        captured["builder_kwargs"] = kwargs
        return (
            _test_object_config_graph(
                package_name="home-api",
                fqn_prefix="aware_home_api",
            ),
        )

    monkeypatch.setattr(
        "aware_api_runtime.compile.resolve_meta_runtime_package_manifest_closure_for_package_names",
        _fake_resolve_meta_manifest_closure,
    )
    monkeypatch.setattr(
        "aware_api_runtime.compile.build_meta_graph_runtime_for_aware_package_manifests",
        _fake_build_meta_runtime,
    )
    monkeypatch.setattr(
        "aware_api_runtime.compile.find_meta_graph_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_api_runtime.compile_materialization.service.build_api_accessible_dependency_graphs_via_meta_runtime",
        _fake_build_dependency_graphs,
    )

    graphs = compile_api_accessible_dependency_graphs_via_meta_runtime(
        snapshot=snapshot,
        kernel_repo_root=kernel_root,
    )

    assert [graph.name for graph in graphs] == ["home-api"]
    assert captured["repo_root"] == kernel_root
    assert captured["package_names"] == ("meta-ontology",)
    runtime_kwargs = cast(dict[str, Any], captured["runtime_kwargs"])
    assert runtime_kwargs["package_manifest_paths"] == manifest_paths
    assert runtime_kwargs["workspace_root"] == kernel_root
    assert runtime_kwargs["composite_name"] == ("API Compile Meta Runtime Context")
    assert captured["projection_lookups"] == [
        (runtime_index, "ObjectConfigGraph"),
        (runtime_index, "ObjectConfigGraphPackage"),
    ]
    builder_kwargs = cast(dict[str, Any], captured["builder_kwargs"])
    assert builder_kwargs["runtime"] is runtime
    assert builder_kwargs["index"] is runtime_index
    assert "environment_id" not in builder_kwargs
    assert "process_id" not in builder_kwargs
    assert "thread_id" not in builder_kwargs
    assert builder_kwargs["target_projection_hash"] == (
        "sha256:test:ObjectConfigGraphPackage"
    )
    assert builder_kwargs["object_config_graph_projection_hash"] == (
        "sha256:test:ObjectConfigGraph"
    )


def test_api_materialization_specs_and_plan_from_compile_payload(
    tmp_path: Path,
) -> None:
    payload = _build_compile_payload(tmp_path)
    specs = resolve_api_ontology_materialization_specs(compile_plan_payloads=[payload])
    assert len(specs) == 1

    spec = specs[0]
    assert spec.api_name == "api_anchor"
    assert spec.source_path == "apis/bindings/anchor.apis.aware"
    assert spec.plan.api.name == "api_anchor"
    assert len(spec.plan.capabilities) == 1
    assert len(spec.plan.capability_endpoints) == 1
    assert len(spec.plan.capability_endpoint_request_configs) == 1
    assert len(spec.plan.capability_endpoint_response_configs) == 1
    assert len(spec.plan.capability_endpoint_stream_configs) == 1
    assert len(spec.plan.capability_endpoint_stream_event_configs) == 2
    assert len(spec.plan.capability_endpoint_functions) == 1
    assert not hasattr(spec.plan, "capability_endpoint_projection_read_targets")
    assert not hasattr(
        spec.plan, "capability_endpoint_projection_read_target_functions"
    )
    assert len(spec.plan.graphs) == 1
    assert len(spec.plan.graph_functions) == 1
    assert len(spec.plan.graph_projections) == 1
    assert len(spec.plan.graph_capabilities) == 1
    assert len(spec.plan.graph_capability_functions) == 1

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api_projection_hash",
    )
    plan = build_api_ontology_materialization_plan(lane=lane, specs=specs)
    assert plan.module_id == "api"
    assert plan.pipeline_id == "api.compile_plan.ontology"
    assert len(plan.steps) == 1
    assert plan.steps[0].step_kind == "api.ontology"
    payload = cast(dict[str, object], plan.steps[0].payload)
    api_payload = cast(dict[str, object], payload["api"])
    assert api_payload["name"] == "api_anchor"


def test_projection_match_requires_canonical_projection_identity() -> None:
    graph = SimpleNamespace(fqn_prefix="aware_attention")
    opg = SimpleNamespace(name="FocusScope")
    assert _projection_matches(
        target_graph=cast(Any, graph),
        opg=cast(Any, opg),
        target="aware_attention.FocusScope",
    )
    assert _projection_matches(
        target_graph=cast(Any, graph),
        opg=cast(Any, opg),
        target="FocusScope",
    )
    assert not _projection_matches(
        target_graph=cast(Any, graph),
        opg=cast(Any, opg),
        target="aware_attention.FocusScopeProjection",
    )
    assert not _projection_matches(
        target_graph=cast(Any, graph),
        opg=cast(Any, opg),
        target="FocusScopeProjection",
    )
    assert not _projection_matches(
        target_graph=cast(Any, graph),
        opg=cast(Any, opg),
        target="aware_attention.focus_scope",
    )
    assert not _projection_matches(
        target_graph=cast(Any, graph),
        opg=cast(Any, opg),
        target="focus_scope",
    )


def test_accessible_graph_collection_prefers_runtime_artifact_projection_detail() -> (
    None
):
    graph_id = uuid4()
    rich_graph = SimpleNamespace(
        id=graph_id,
        name="attention-ontology",
        fqn_prefix="aware_attention",
        object_projection_graphs=(SimpleNamespace(name="FocusScope"),),
        object_config_graph_nodes=(object(),),
        object_config_graph_bindings=(),
        object_config_graph_relationships=(),
    )
    skeletal_graph = SimpleNamespace(
        id=graph_id,
        name="aware_attention",
        fqn_prefix="aware_attention",
        object_projection_graphs=(),
        object_config_graph_nodes=(),
        object_config_graph_bindings=(),
        object_config_graph_relationships=(),
    )
    root_graph = SimpleNamespace(
        id=uuid4(),
        name="environment",
        fqn_prefix="aware_environment",
        object_projection_graphs=(),
        object_config_graph_nodes=(),
        object_config_graph_bindings=(),
        object_config_graph_relationships=(
            SimpleNamespace(target_object_config_graph=skeletal_graph),
        ),
    )
    index = SimpleNamespace(ocg=root_graph)

    accessible_graphs = _collect_accessible_object_config_graphs(
        index=cast(Any, index),
        extra_graphs=(cast(Any, rich_graph),),
    )
    target_graph = _resolve_target_object_config_graph(
        index=cast(Any, index),
        accessible_graphs=cast(Any, accessible_graphs),
        target="aware_attention",
        projection_specs=("aware_attention.FocusScope",),
    )

    assert target_graph is rich_graph
    assert (
        _resolve_object_projection_graph(
            index=cast(Any, index),
            target_graph=cast(Any, target_graph),
            projection_target="aware_attention.FocusScope",
            accessible_graphs=cast(Any, accessible_graphs),
        ).name
        == "FocusScope"
    )


def test_api_endpoint_catalog_detects_partial_committed_api_lane() -> None:
    api_id = uuid4()
    capability_id = uuid4()
    endpoint_id = uuid4()
    catalog = {"home_devices": {"open_door": ("open_door",)}}
    complete_session = SimpleNamespace(
        imap_all_objects=lambda: (
            Api.model_construct(id=api_id, name="home_devices"),
            ApiCapability.model_construct(
                id=capability_id,
                api_id=api_id,
                name="open_door",
            ),
            ApiCapabilityEndpoint.model_construct(
                id=endpoint_id,
                api_capability_id=capability_id,
                name="open_door",
            ),
        )
    )
    partial_session = SimpleNamespace(
        imap_all_objects=lambda: (
            Api.model_construct(id=api_id, name="home_devices"),
            ApiCapability.model_construct(
                id=capability_id,
                api_id=api_id,
                name="open_door",
            ),
        )
    )

    assert _api_endpoint_catalog_is_satisfied_by_session(
        session=cast(Any, complete_session),
        api_endpoint_catalog=catalog,
    )
    assert not _api_endpoint_catalog_is_satisfied_by_session(
        session=cast(Any, partial_session),
        api_endpoint_catalog=catalog,
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason=(
        "Commit-backed API ontology materialization onto ProjectionKey still depends on a broader "
        "runtime lane: canonical ObjectConfigGraphBindingClass rows are not exposed through the composed "
        "environment root yet, so this integration proof remains blocked outside the api-graph ontology cut."
    )
)
async def test_api_materialization_executes_commit_backed_ontology_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = await asyncio.to_thread(_build_compile_payload, tmp_path)
    repo_root = _REPO_ROOT
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Api",
        )
        lane = MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash=api_projection_hash,
        )

        receipt = await materialize_api_graph_ontology(
            index=index,
            actor_id=None,
            lane=lane,
            compile_plan_payloads=[payload],
        )
        assert receipt is not None
        assert receipt.status == "succeeded"
        assert len(receipt.steps) == 1
        step = receipt.steps[0]
        assert step.status == "succeeded"
        assert step.commit_id is not None
        assert step.head_commit_id is not None
        assert step.details["api_name"] == "api_anchor"
        assert step.details["capability_count"] == 1
        assert step.details["endpoint_count"] == 1
        assert step.details["request_config_count"] == 1
        assert step.details["response_config_count"] == 1
        assert step.details["stream_config_count"] == 1
        assert step.details["stream_event_config_count"] == 2
        assert step.details["endpoint_function_count"] == 1
        assert "endpoint_projection_read_target_count" not in step.details
        assert "endpoint_projection_read_target_function_count" not in step.details
        assert step.details["graph_count"] == 1
        assert step.details["graph_function_count"] == 1
        assert step.details["graph_projection_count"] == 1
    assert step.details["graph_capability_count"] == 1
    assert step.details["graph_capability_function_count"] == 1


def test_generated_api_compile_plan_accessible_graph_has_namespace_evidence() -> None:
    payload = _generated_view_api_compile_plan_payload()

    generated_graph = build_generated_api_compile_plan_accessible_graphs(
        compile_plan_payload=payload,
    )[-1]
    generated_payload = dump_api_accessible_dependency_graph_artifact_payload(
        graph=generated_graph,
    )

    assert isinstance(generated_payload, dict)
    assert any(
        entry["package"] == "aware_actor_view_api"
        and entry["fqn"]
        == (
            "aware_actor_view_api.view_resolution."
            "AwareActorRolesActorRolesV1ViewResolveRequest"
        )
        and entry["symbol"] == "AwareActorRolesActorRolesV1ViewResolveRequest"
        for entry in generated_payload["namespace_membership"]
    )


@pytest.mark.asyncio
async def test_materialize_api_package_from_compile_plan_input_commits_generated_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _generated_view_api_compile_plan_payload()
    compile_plan_path = (
        tmp_path
        / ".aware"
        / "api"
        / "runtime"
        / "aware-actor-view-api"
        / "api.compile_plan.json"
    )
    compile_plan_path.parent.mkdir(parents=True, exist_ok=True)
    compile_plan_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    repo_root = _REPO_ROOT
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_generated_api", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index
        result = await materialize_api_package_from_compile_plan_input(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=tmp_path,
            compile_plan_payload=payload,
            compile_plan_path=compile_plan_path,
        )

    assert result.api.name == "aware_actor_views"
    assert result.api_source_path == "experience.view_api.generated"
    assert result.api_package.name == "aware-actor-view-api"
    assert result.api_package.api_id == result.api.id
    assert result.api_package.source_code_package_id is None
    assert result.api_package.compilation_mode == "compile_plan"
    assert result.api_package.manifest_relative_path == (
        ".aware/api/runtime/aware-actor-view-api/api.compile_plan.json"
    )
    assert result.api_endpoint_catalog == {
        "aware_actor_views": {
            "aware_actor_roles_actor_roles_v1": ("resolve",),
        }
    }
    assert result.generated_dto_graph_count == 1
    assert result.generated_dto_class_config_count == 2
    assert result.package_commit_id is not None
    assert result.package_head_commit_id is not None
    generated_graph = build_generated_api_compile_plan_accessible_graphs(
        compile_plan_payload=payload,
    )[-1]
    generated_payload = dump_api_accessible_dependency_graph_artifact_payload(
        graph=generated_graph,
    )
    assert isinstance(generated_payload, dict)
    assert any(
        entry["package"] == "aware_actor_view_api"
        and entry["fqn"]
        == (
            "aware_actor_view_api.view_resolution."
            "AwareActorRolesActorRolesV1ViewResolveRequest"
        )
        and entry["symbol"] == "AwareActorRolesActorRolesV1ViewResolveRequest"
        for entry in generated_payload["namespace_membership"]
    )


def test_authored_api_materialization_result_exposes_zero_generated_dto_counts() -> (
    None
):
    result = ApiPackageMaterializationResult(
        api_toml_path=Path("apis/agent/aware.api.toml"),
        workspace_root=Path("."),
        manifest_spec=cast(Any, object()),
        api=cast(Any, SimpleNamespace(id=uuid4(), name="agent_api")),
        api_package=cast(Any, SimpleNamespace(id=uuid4(), name="agent-api")),
        api_source_path="apis/agent",
        source_files=("apis/agent/api.aware",),
        phase_timings_s={},
        runtime_compile_plan_hash="test-runtime-compile-plan",
        api_endpoint_catalog={},
        source_code_package_id=None,
        source_object_instance_graph_commit_id=None,
        api_commit_id=None,
        api_head_commit_id=None,
        api_object_instance_graph_commit_id=None,
        package_commit_id=None,
        package_head_commit_id=None,
    )

    assert result.generated_dto_graph_count == 0
    assert result.generated_dto_class_config_count == 0


def test_api_product_materialization_uses_meta_graph_transform_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_api_runtime.packages import materialization as product_materialization
    from aware_meta.materialization.schemas import (
        LocalMaterializationExecutionResult,
        MaterializationConfig,
        MaterializationSource,
    )

    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="api_product",
        hash="source-ref",
        fqn_prefix="aware_api_product",
        language=CodeLanguage.aware,
    )
    runtime_graph = source_graph.model_copy(update={"hash": "runtime-ref"})
    language_graph = source_graph.model_copy(
        update={"hash": "language-ref", "language": CodeLanguage.python}
    )
    transform_requests: list[object] = []
    render_requests: list[object] = []
    declared_requests: list[object] = []

    class _FakeGraphTransformService:
        def transform(self, request: object) -> object:
            transform_requests.append(request)
            return SimpleNamespace(
                source_graph=source_graph,
                runtime_graph=runtime_graph,
                language_external_graphs=(),
                generated_ocg_node_manifest=None,
                source_graph_ref="source-ref",
                runtime_graph_ref="runtime-ref",
                language_graph_ref="language-ref",
                require_language_graph=lambda: language_graph,
            )

    class _FakeLayout:
        def __init__(self) -> None:
            self.bound_graphs: list[ObjectConfigGraph] = []

        def bind_graph(self, graph: ObjectConfigGraph) -> None:
            self.bound_graphs.append(graph)

    def _fake_render_language_materialization(request: object) -> object:
        render_requests.append(request)
        written = tmp_path / "generated.py"
        written.write_text("# generated\n", encoding="utf-8")
        return SimpleNamespace(
            written_files=(written,),
            warnings=(),
            renderer_names=("default",),
            renderer_file_counts={"default": 1},
            renderer_warning_counts={"default": 0},
        )

    def _fake_build_language_materialization_packages(request: object) -> object:
        _ = request
        return SimpleNamespace(package_results=(), warnings=(), metrics={})

    def _fake_produce_language_plugin_declared_outputs(request: object) -> object:
        declared_requests.append(request)
        return SimpleNamespace(generated_files=(), warnings=(), metrics={})

    monkeypatch.setattr(
        product_materialization,
        "GraphMaterializationTransformService",
        _FakeGraphTransformService,
    )
    monkeypatch.setattr(
        product_materialization,
        "render_language_materialization",
        _fake_render_language_materialization,
    )
    monkeypatch.setattr(
        product_materialization,
        "build_language_materialization_packages",
        _fake_build_language_materialization_packages,
    )
    monkeypatch.setattr(
        product_materialization,
        "produce_language_plugin_declared_outputs",
        _fake_produce_language_plugin_declared_outputs,
    )

    layout = _FakeLayout()
    result = product_materialization._materialize_graph_via_meta(
        aware_root=tmp_path,
        layout_strategy=cast(Any, layout),
        materialization_config=MaterializationConfig(
            name="api-product",
            target_language=CodeLanguage.python,
            target_output_dir=tmp_path,
            source_package_name="api-product",
            import_root="aware_api_product",
            source=MaterializationSource.api,
        ),
        object_config_graph=source_graph,
    )

    transform_request = transform_requests[0]
    assert getattr(transform_request, "source_graph") is source_graph
    assert getattr(transform_request, "source_stage") == "source_graph"
    assert getattr(transform_request, "target_stage") == "language_graph"
    assert getattr(transform_request, "graph_profile") == "public_dto"
    assert layout.bound_graphs == [language_graph]
    assert getattr(render_requests[0], "language_graph") is language_graph
    assert getattr(render_requests[0], "source_graph") is source_graph
    assert getattr(declared_requests[0], "runtime_graph") is runtime_graph
    assert getattr(declared_requests[0], "language_graph") is language_graph
    assert isinstance(result, LocalMaterializationExecutionResult)
    assert result.files == [tmp_path / "generated.py"]


def test_api_dto_full_render_cleans_stale_runtime_and_python_package_output(
    tmp_path: Path,
) -> None:
    from aware_api_runtime.packages import materialization as product_materialization
    from aware_meta.graph.config.package_strategy import ObjectConfigGraphPackageSpec
    from aware_meta.materialization.schemas import (
        MaterializationConfig,
        MaterializationSource,
    )

    aware_root = tmp_path
    runtime_output_dir = (
        aware_root / ".aware" / "api" / "runtime" / "environment-service-dto"
    )
    stale_runtime_file = runtime_output_dir / "render" / "stale.py"
    stale_runtime_file.parent.mkdir(parents=True, exist_ok=True)
    stale_runtime_file.write_text("# stale runtime render\n", encoding="utf-8")

    package_root = aware_root / "apis" / "environment" / "python"
    stale_package_file = (
        package_root / "aware_environment_service_dto" / "environment" / "stale.py"
    )
    stale_package_file.parent.mkdir(parents=True, exist_ok=True)
    stale_package_file.write_text("# stale package\n", encoding="utf-8")

    materialization_config = MaterializationConfig(
        name="environment-service-dto",
        target_language=CodeLanguage.python,
        target_output_dir=runtime_output_dir,
        source_package_name="environment-service-dto",
        import_root="aware_environment_service_dto",
        source=MaterializationSource.api,
        packages=[
            ObjectConfigGraphPackageSpec(
                name="environment-service-dto",
                package_name="environment-service-dto",
                package_root=package_root,
                import_root="aware_environment_service_dto",
                metadata={"aware_package_kind": "api_dto"},
            )
        ],
    )

    product_materialization._clean_api_runtime_render_output_for_full_render(
        aware_root=aware_root,
        materialization_config=materialization_config,
        candidate_paths=(),
    )
    product_materialization._clean_api_python_package_output_for_full_render(
        aware_root=aware_root,
        materialization_config=materialization_config,
        candidate_paths=(),
    )

    assert not stale_runtime_file.exists()
    assert not stale_package_file.exists()


def _generated_view_api_compile_plan_payload() -> dict[str, object]:
    return {
        "schema_version": 9,
        "package_name": "aware-actor-view-api",
        "fqn_prefix": "aware_actor_view_api",
        "source_files": ["experience.view_api.generated"],
        "generated_dto_namespace_roots": [
            {
                "path": "view_resolution",
                "namespace": "view_resolution",
            }
        ],
        "api_ontology": [
            {
                "api": {
                    "name": "aware_actor_views",
                    "description": None,
                    "source_path": "experience.view_api.generated",
                },
                "capabilities": [
                    {
                        "api_name": "aware_actor_views",
                        "name": "aware_actor_roles_actor_roles_v1",
                        "description": (
                            "Resolve Experience view "
                            "aware_actor_roles.actor.roles.v1."
                        ),
                        "source_path": "actor_roles.aware",
                    }
                ],
                "capability_endpoints": [
                    {
                        "api_name": "aware_actor_views",
                        "capability_name": "aware_actor_roles_actor_roles_v1",
                        "name": "resolve",
                        "description": (
                            "Pure read Experience view resolution endpoint."
                        ),
                        "source_path": "actor_roles.aware",
                    }
                ],
                "capability_endpoint_request_configs": [
                    {
                        "api_name": "aware_actor_views",
                        "capability_name": "aware_actor_roles_actor_roles_v1",
                        "endpoint_name": "resolve",
                        "class_ref": (
                            "aware_actor_view_api.view_resolution."
                            "AwareActorRolesActorRolesV1ViewResolveRequest"
                        ),
                        "class_config_id": None,
                        "description": "Focus scope for actor roles view.",
                        "source_path": "actor_roles.aware",
                    }
                ],
                "capability_endpoint_response_configs": [
                    {
                        "api_name": "aware_actor_views",
                        "capability_name": "aware_actor_roles_actor_roles_v1",
                        "endpoint_name": "resolve",
                        "class_ref": (
                            "aware_actor_view_api.view_resolution."
                            "AwareActorRolesActorRolesV1ViewResolveResponse"
                        ),
                        "class_config_id": None,
                        "description": "View-state envelope for actor roles.",
                        "source_path": "actor_roles.aware",
                    }
                ],
                "capability_endpoint_stream_configs": [],
                "capability_endpoint_stream_event_configs": [],
                "capability_endpoint_functions": [],
                "graphs": [],
                "graph_functions": [],
                "graph_projections": [],
                "graph_capabilities": [],
                "graph_capability_functions": [],
            }
        ],
    }


def test_generated_api_compile_plan_input_rejects_path_only_evidence(
    tmp_path: Path,
) -> None:
    with pytest.raises(RuntimeError, match="durable input_artifact_payload"):
        _compile_plan_payload_from_input(
            input_payload={},
            input_artifact_path=tmp_path / ".aware" / "api.compile_plan.json",
        )


@pytest.mark.asyncio
async def test_home_sample_api_runtime_resolution_includes_workspace_api_dependency_truth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = _REPO_ROOT
    workspace_root = (repo_root / "workspaces" / "aware_home").resolve()
    api_toml_path = (
        workspace_root / "modules" / "home" / "apis" / "home_devices" / "aware.api.toml"
    )
    test_root = Path("/tmp") / f"aware-api-runtime-home-sample-{uuid4()}"
    monkeypatch.setenv(
        "AWARE_META_SERVICE_EVENT_STORE_ROOT",
        str(test_root / "meta-events"),
    )
    monkeypatch.setenv("AWARE_ROOT", str(test_root / "aware-root"))

    compile_result = await asyncio.to_thread(
        compile_api_workspace,
        toml_path=api_toml_path,
        repo_root=workspace_root,
        materialize_service_protocol=True,
        dependency_graph_mode="meta_runtime",
        kernel_repo_root=repo_root,
    )
    assert compile_result.service_protocol_materialization is not None

    resolution = await asyncio.to_thread(
        resolve_api_workspace_runtime_manifest,
        toml_path=api_toml_path,
        repo_root=workspace_root,
    )
    for import_root in reversed(resolution.import_activation.roots):
        monkeypatch.syspath_prepend(str(import_root))
    assert resolution.module_manifest_paths == ()
    assert resolution.manifest_path.name == API_RUNTIME_SEMANTICS_FILENAME
    semantics_payload = json.loads(resolution.manifest_path.read_text(encoding="utf-8"))
    assert semantics_payload["kind"] == "api.runtime_semantics"
    assert semantics_payload["api_package_name"] == "home-devices-api"
    assert semantics_payload["registered_class_config_count"] >= 1
    dependency_graphs = load_api_accessible_dependency_graphs_from_runtime_artifact(
        runtime_package_dir=resolution.manifest_path.parent,
    )
    class_fqns = {
        node.class_config.class_fqn
        for graph in dependency_graphs
        for node in graph.object_config_graph_nodes
        if node.class_config is not None and node.class_config.class_fqn
    }
    assert "aware_home_api.default.door.DoorByLabel" in class_fqns
    dependency_class_config_ids = await asyncio.to_thread(
        load_api_dependency_class_config_ids,
        snapshot=compile_result.snapshot,
    )
    door_by_label_id = dependency_class_config_ids["aware_home_api.door.DoorByLabel"]
    graph_class_config_ids = {
        node.class_config.id
        for graph in dependency_graphs
        for node in graph.object_config_graph_nodes
        if node.class_config is not None
    }
    assert door_by_label_id in graph_class_config_ids


def test_api_runtime_dependency_build_is_externalized() -> None:
    repo_root = _REPO_ROOT.resolve()
    aware_toml_path = (
        repo_root
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "code"
        / "ontology"
        / "structure"
        / "aware.toml"
    ).resolve()
    package = _RuntimeDependencyPackage(
        package_name="code-ontology",
        aware_toml_path=aware_toml_path,
        package_root=aware_toml_path.parent.resolve(),
        spec=load_aware_toml_spec(toml_path=aware_toml_path),
    )

    with pytest.raises(RuntimeError, match="not built by aware_api_runtime"):
        _build_runtime_dependency_package(
            package=package,
            repo_root=repo_root,
            author_id=uuid4(),
        )
