from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest

from _meta_runtime_test_paths import META_FIXTURES_ROOT, META_RUNTIME_ROOT, REPO_ROOT

_REPO_ROOT = REPO_ROOT
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_META_RUNTIME_ROOT_STR = str(META_RUNTIME_ROOT)
if _META_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _META_RUNTIME_ROOT_STR)

from aware_code.semantic_capability import (  # noqa: E402
    SemanticAnalysisCapabilityRequest,
)
from aware_code.semantic_function_call_execution import (  # noqa: E402
    SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY,
)
from aware_code.semantic_graph_execution import (  # noqa: E402
    SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY,
    SemanticGraphFunctionInvocation,
    SemanticGraphFunctionInvocationResult,
)
from aware_code.semantic_materialization import (  # noqa: E402
    SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
    SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY,
    SemanticPackageMaterializationRequest,
)
from aware_code.stable_ids import (  # noqa: E402
    code_package_generated_config_key,
    stable_code_package_config_id,
)
from aware_code_ontology.code.code_enums import CodeLanguage  # noqa: E402
from aware_code_ontology.code.code_plan import (  # noqa: E402
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_meta_ontology.graph.config.object_config_graph import (  # noqa: E402
    ObjectConfigGraph,
)
from aware_meta_ontology.graph.config.object_config_graph_package_implementation_policy_enums import (  # noqa: E402
    ObjectConfigGraphPackageFunctionImplOwnership,
    ObjectConfigGraphPackageFunctionImplParityPolicy,
)
from aware_meta.materialization import workspace_provider  # noqa: E402
import aware_meta.materialization.service as materialization_service  # noqa: E402
from aware_meta.materialization.semantic_function_call_resolution import (  # noqa: E402
    META_OCG_BUILD_FUNCTION_REF,
    META_OCG_CREATE_NODE_FUNCTION_REF,
    META_OCG_PACKAGE_BUILD_FUNCTION_REF,
)
from aware_meta.semantic_analysis import (  # noqa: E402
    analyze_meta_ocg_semantic_capability,
)


class _RecordingMetaGraphBackend:
    def __init__(self) -> None:
        self.invocations: list[SemanticGraphFunctionInvocation] = []

    async def invoke(
        self,
        invocation: SemanticGraphFunctionInvocation,
    ) -> SemanticGraphFunctionInvocationResult:
        self.invocations.append(invocation)
        commit_id = uuid4()
        return SemanticGraphFunctionInvocationResult(
            object_id=_object_id_for_semantic_key(invocation.result_semantic_key),
            commit_id=str(commit_id),
            head_commit_id=str(commit_id),
            adapter_kind="local",
            evidence={
                "ordinal": len(self.invocations),
                "response": {
                    "object_instance_graph_commit_id": str(commit_id),
                },
            },
        )


class _FakeOwnershipReceipt:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def as_payload(self) -> dict[str, object]:
        return dict(self._payload)


def _home_story_ontology_root() -> Path:
    return META_FIXTURES_ROOT / "home_story_ontology"


def _home_story_source_files(package_root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path.relative_to(package_root)
            for path in (package_root / "aware").rglob("*.aware")
        )
    )


def _home_story_change_preview(package_root: Path) -> dict[str, object]:
    relative_path = "home/home.aware"
    delta = CodePackageDelta(
        package_name="home-ontology",
        package_root=".",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        authority_kind="workspace_sdk",
        source_revision_id="meta-materialization-plan-evidence",
        paths=[
            CodePackageDeltaPath(
                relative_path=relative_path,
                kind=CodePackageDeltaKind.update,
                content_text=(package_root / "aware" / relative_path).read_text(
                    encoding="utf-8"
                ),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )
    analysis = analyze_meta_ocg_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=package_root,
            source_files=_home_story_source_files(package_root),
            manifest_path=package_root / "aware.toml",
            code_package_delta=delta,
        )
    )
    return analysis.change_preview.evidence_payload()


def test_generated_package_texts_skip_binary_generated_refs(tmp_path: Path) -> None:
    output_root = tmp_path / "aware_demo"
    aware_root = output_root / "_aware"
    aware_root.mkdir(parents=True)
    text_path = aware_root / "python.models.json"
    binary_path = aware_root / "orm.graph.binding.msgpack"
    text_path.write_text('{"models": []}\n', encoding="utf-8")
    binary_path.write_bytes(b"\x82\xa4demo\x01")

    texts = workspace_provider._generated_package_texts_by_relative_path(
        package_output=SimpleNamespace(
            generated_file_refs=(
                Path("_aware/python.models.json"),
                Path("_aware/orm.graph.binding.msgpack"),
            )
        ),
        output_root=output_root,
    )

    assert texts == {"_aware/python.models.json": '{"models": []}\n'}


def test_language_materialization_target_external_lowering_policy() -> None:
    def _target(
        language: CodeLanguage,
    ) -> workspace_provider._LanguageMaterializationTarget:  # noqa: SLF001
        return workspace_provider._LanguageMaterializationTarget(  # noqa: SLF001
            target_language_plugin_id=language,
            output_root=Path("modules/demo/out"),
            import_root="aware_demo",
            package_name="demo",
            materialization_source="ontology",
            code_package_surface="structure",
        )

    assert (
        workspace_provider._language_materialization_target_should_lower_external_graphs(  # noqa: SLF001
            target=_target(CodeLanguage.python),
        )
        is False
    )
    assert (
        workspace_provider._language_materialization_target_should_lower_external_graphs(  # noqa: SLF001
            target=_target(CodeLanguage.sql),
        )
        is False
    )
    assert (
        workspace_provider._language_materialization_target_should_lower_external_graphs(  # noqa: SLF001
            target=_target(CodeLanguage.dart),
        )
        is True
    )


def test_generated_package_texts_accept_workspace_relative_refs(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    output_root = (
        workspace_root
        / "modules"
        / "demo"
        / "structure"
        / "ontology"
        / "python"
        / "dto"
    )
    package_root = output_root / "aware_demo"
    package_root.mkdir(parents=True)
    generated_path = package_root / "demo.py"
    generated_path.write_text("class Demo:\n    pass\n", encoding="utf-8")
    workspace_relative_path = generated_path.relative_to(workspace_root)

    texts = workspace_provider._generated_package_texts_by_relative_path(
        package_output=SimpleNamespace(
            generated_file_refs=(workspace_relative_path,),
        ),
        output_root=output_root,
        workspace_root=workspace_root,
    )

    assert texts == {"aware_demo/demo.py": "class Demo:\n    pass\n"}


def test_ontology_package_catalog_resolves_workspace_ontology_descriptor(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    module_root = workspace_root / "modules" / "conversation"
    ontology_root = module_root / "ontology"
    source_root = ontology_root / "structure"
    source_root.mkdir(parents=True)
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
    (ontology_root / "aware.ontology.toml").write_text(
        "\n".join(
            (
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "conversation-ontology"',
                'fqn_prefix = "aware_conversation"',
                'source_manifest = "structure/aware.toml"',
                "",
            )
        ),
        encoding="utf-8",
    )
    (source_root / "aware.toml").write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[package]",
                'package_name = "conversation-ontology"',
                'fqn_prefix = "aware_conversation"',
                'kind = "ontology"',
                "version_number = 1",
                "",
                "[build]",
                'environment_slug = "aware_conversation"',
                "",
            )
        ),
        encoding="utf-8",
    )

    assert workspace_provider._ontology_package_fqn_prefix_catalog(  # noqa: SLF001
        workspace_root=workspace_root,
    ) == {"conversation-ontology": "aware_conversation"}


def test_leaf_external_graphs_skip_context_without_manifest_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    manifest_path = _write_provider_delta_workspace_manifest(
        workspace_root=workspace_root,
        dependency_package_names=(),
    )

    def _fail_if_context_scanned(
        context: Mapping[str, object],
    ) -> tuple[ObjectConfigGraph, ...]:
        raise AssertionError("external graph context should not be scanned")

    monkeypatch.setattr(
        workspace_provider,
        "_external_object_config_graphs_from_context",
        _fail_if_context_scanned,
    )

    assert (
        workspace_provider._leaf_external_object_config_graphs_from_context(  # noqa: SLF001
            context={"runtime_object_config_graphs": (object(),)},
            aware_toml_path=manifest_path,
            workspace_root=workspace_root,
        )
        == ()
    )


def _write_provider_delta_workspace_manifest(
    *,
    workspace_root: Path,
    dependency_package_names: tuple[str, ...],
) -> Path:
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    package_root.mkdir(parents=True)
    (workspace_root / "modules" / "demo" / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    dependency_lines = [
        line
        for package_name in dependency_package_names
        for line in ("", "[[dependencies]]", f'package_name = "{package_name}"')
    ]
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
                *dependency_lines,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if "dep-ontology" in dependency_package_names:
        _write_provider_delta_dependency_manifest(
            workspace_root=workspace_root,
            module_name="dep",
            package_name="dep-ontology",
            fqn_prefix="dep_demo",
        )
    _write_provider_delta_dependency_manifest(
        workspace_root=workspace_root,
        module_name="unused",
        package_name="unused-ontology",
        fqn_prefix="unused_demo",
    )
    return manifest_path


def _write_provider_delta_dependency_manifest(
    *,
    workspace_root: Path,
    module_name: str,
    package_name: str,
    fqn_prefix: str,
) -> None:
    package_root = workspace_root / "modules" / module_name / "structure" / "ontology"
    package_root.mkdir(parents=True)
    (workspace_root / "modules" / module_name / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                f'package_name = "{package_name}"',
                f'fqn_prefix = "{fqn_prefix}"',
                'kind = "ontology"',
                "",
                "[build]",
                f'environment_slug = "{fqn_prefix}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _runtime_test_graph(
    *,
    fqn_prefix: str,
    graph_hash: str,
) -> ObjectConfigGraph:
    return ObjectConfigGraph(
        id=uuid4(),
        name=fqn_prefix,
        hash=graph_hash,
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )


def test_provider_delta_source_graph_reports_actual_graph_stage() -> None:
    source_graph = _runtime_test_graph(
        fqn_prefix="aware_demo",
        graph_hash="source-hash",
    )
    runtime_graph = _runtime_test_graph(
        fqn_prefix="aware_demo",
        graph_hash="runtime-hash",
    )
    target = workspace_provider._LanguageMaterializationTarget(  # noqa: SLF001
        target_language_plugin_id=CodeLanguage.python,
        output_root=Path("runtime/aware_demo"),
        import_root="aware_demo",
        package_name="aware_demo",
        materialization_source="runtime_handlers",
        code_package_surface="runtime",
        renderer_kind="runtime_handlers_impl",
        source_is_runtime=True,
    )

    source_only = (
        workspace_provider._provider_delta_output_source_graph(  # noqa: SLF001
            target=target,
            context={"semantic_object_config_graphs": (source_graph,)},
        )
    )
    assert source_only is not None
    assert source_only.graph is source_graph
    assert source_only.source_is_runtime is False

    runtime_available = (
        workspace_provider._provider_delta_output_source_graph(  # noqa: SLF001
            target=target,
            context={
                "runtime_object_config_graphs": (runtime_graph,),
                "semantic_object_config_graphs": (source_graph,),
            },
        )
    )
    assert runtime_available is not None
    assert runtime_available.graph is runtime_graph
    assert runtime_available.source_is_runtime is True


def test_language_target_progress_payload_distinguishes_target_from_graph_stage() -> (
    None
):
    source_graph = _runtime_test_graph(
        fqn_prefix="aware_demo",
        graph_hash="source-hash",
    )
    target = workspace_provider._LanguageMaterializationTarget(  # noqa: SLF001
        target_language_plugin_id=CodeLanguage.python,
        output_root=Path("runtime/aware_demo"),
        import_root="aware_demo",
        package_name="aware_demo",
        materialization_source="runtime_handlers",
        code_package_surface="runtime",
        renderer_kind="runtime_handlers_impl",
        source_is_runtime=True,
    )

    payload = workspace_provider._language_target_progress_payload(  # noqa: SLF001
        target=target,
        source_graph=workspace_provider._LanguageMaterializationSourceGraph(  # noqa: SLF001
            graph=source_graph,
            source_is_runtime=False,
        ),
        target_index=0,
        target_count=1,
    )

    assert payload["source_is_runtime"] is True
    assert payload["target_source_is_runtime"] is True
    assert payload["materialization_source_graph_is_runtime"] is False
    assert payload["materialization_source_graph_hash"] == "source-hash"
    assert payload["materialization_source_graph_fqn_prefix"] == "aware_demo"


def test_meta_workspace_provider_dependency_runtime_graphs_follow_catalog_closure(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    manifest_path = workspace_root / "modules" / "sdk" / "structure" / "aware.toml"
    manifest_path.parent.mkdir(parents=True)
    source_graph = _runtime_test_graph(
        fqn_prefix="aware_sdk",
        graph_hash="sdk-hash",
    )
    runtime_graphs = (
        source_graph,
        _runtime_test_graph(
            fqn_prefix="aware_api",
            graph_hash="api-hash",
        ),
        _runtime_test_graph(
            fqn_prefix="aware_code",
            graph_hash="code-hash",
        ),
        _runtime_test_graph(
            fqn_prefix="aware_content",
            graph_hash="content-hash",
        ),
        _runtime_test_graph(
            fqn_prefix="aware_storage",
            graph_hash="storage-hash",
        ),
        _runtime_test_graph(
            fqn_prefix="aware_meta",
            graph_hash="meta-hash",
        ),
        _runtime_test_graph(
            fqn_prefix="aware_history",
            graph_hash="history-hash",
        ),
        _runtime_test_graph(
            fqn_prefix="aware_unrelated",
            graph_hash="unrelated-hash",
        ),
    )

    graphs = workspace_provider._package_dependency_runtime_object_config_graphs_from_context(  # noqa: SLF001
        context={
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": (
                    {
                        "package_name": "sdk-ontology",
                        "fqn_prefix": "aware_sdk",
                        "manifest_path": manifest_path.as_posix(),
                        "dependency_package_names": (
                            "api-ontology",
                            "code-ontology",
                            "meta-ontology",
                        ),
                    },
                    {
                        "package_name": "api-ontology",
                        "fqn_prefix": "aware_api",
                        "dependency_package_names": (
                            "meta-ontology",
                            "code-ontology",
                        ),
                    },
                    {
                        "package_name": "code-ontology",
                        "fqn_prefix": "aware_code",
                        "dependency_package_names": ("content-ontology",),
                    },
                    {
                        "package_name": "content-ontology",
                        "fqn_prefix": "aware_content",
                        "dependency_package_names": ("storage-ontology",),
                    },
                    {
                        "package_name": "storage-ontology",
                        "fqn_prefix": "aware_storage",
                        "dependency_package_names": (),
                    },
                    {
                        "package_name": "meta-ontology",
                        "fqn_prefix": "aware_meta",
                        "dependency_package_names": (
                            "code-ontology",
                            "content-ontology",
                            "history-ontology",
                        ),
                    },
                    {
                        "package_name": "history-ontology",
                        "fqn_prefix": "aware_history",
                        "dependency_package_names": ("code-ontology",),
                    },
                    {
                        "package_name": "unrelated-ontology",
                        "fqn_prefix": "aware_unrelated",
                        "dependency_package_names": (),
                    },
                ),
            },
            "runtime_object_config_graphs": runtime_graphs,
        },
        source_graph=source_graph,
        aware_toml_path=manifest_path,
        workspace_root=workspace_root,
    )

    assert tuple(graph.fqn_prefix for graph in graphs) == (
        "aware_storage",
        "aware_content",
        "aware_code",
        "aware_history",
        "aware_meta",
        "aware_api",
    )


def test_meta_workspace_provider_skips_runtime_graph_context_without_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    manifest_path = _write_provider_delta_workspace_manifest(
        workspace_root=workspace_root,
        dependency_package_names=(),
    )
    source_graph = _runtime_test_graph(
        fqn_prefix="aware_demo",
        graph_hash="demo-hash",
    )

    def fail_if_runtime_context_is_loaded(**_: object) -> tuple[ObjectConfigGraph, ...]:
        raise AssertionError("runtime graph context should not be loaded")

    monkeypatch.setattr(
        workspace_provider,
        "_external_runtime_object_config_graphs_from_context",
        fail_if_runtime_context_is_loaded,
    )

    graphs = workspace_provider._package_dependency_runtime_object_config_graphs_from_context(  # noqa: SLF001
        context={
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": (
                    {
                        "package_name": "demo-ontology",
                        "fqn_prefix": "aware_demo",
                        "manifest_path": manifest_path.as_posix(),
                        "dependency_package_names": (),
                    },
                ),
            },
            "runtime_object_config_graphs": (
                _runtime_test_graph(
                    fqn_prefix="aware_unrelated",
                    graph_hash="unrelated-hash",
                ),
            ),
        },
        source_graph=source_graph,
        aware_toml_path=manifest_path,
        workspace_root=workspace_root,
        include_transitive_dependencies=False,
    )

    assert graphs == ()


def _provider_delta_output_request(
    *,
    workspace_root: Path,
    manifest_path: Path | None,
    source_graph: ObjectConfigGraph,
    runtime_graphs: tuple[ObjectConfigGraph, ...],
) -> SimpleNamespace:
    package = (
        {
            "manifest_path": manifest_path.relative_to(workspace_root).as_posix(),
        }
        if manifest_path is not None
        else {}
    )
    return SimpleNamespace(
        workspace_root=workspace_root,
        package=package,
        context={
            "semantic_object_config_graphs": (source_graph,),
            "runtime_object_config_graphs": runtime_graphs,
            "language_materialization_targets": [
                {
                    "target_language_plugin_id": "python",
                    "output_root": "structure/ontology/python",
                    "import_root": "aware_demo_ontology",
                    "package_name": "demo-ontology",
                    "materialization_source": "ontology",
                    "code_package_surface": "structure",
                    "renderer_profile": "orm_runtime",
                },
            ],
        },
    )


def test_workspace_provider_reads_language_tooling_context() -> None:
    context = {
        SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY: {
            "schema": "aware.code.semantic-materialization.language-tooling.v1",
            "tools": [
                {
                    "tool_id": "dart.build_runner",
                    "state_env": {
                        "HOME": "/tmp/workspace/.aware/tooling/dart/home",
                        "PUB_CACHE": "/tmp/workspace/.aware/tooling/dart/pub-cache",
                    },
                    "executable_overrides": {
                        "dart": "/tmp/workspace/toolchains/dart-sdk/bin/dart",
                    },
                },
                {
                    "tool_id": "python.format.black",
                    "state_env": {},
                },
            ],
        }
    }

    assert workspace_provider._language_materialization_post_step_tool_mapping_by_tool_id(  # noqa: SLF001
        context=context,
        mapping_key="state_env",
    ) == {
        "dart.build_runner": {
            "HOME": "/tmp/workspace/.aware/tooling/dart/home",
            "PUB_CACHE": "/tmp/workspace/.aware/tooling/dart/pub-cache",
        }
    }
    assert workspace_provider._language_materialization_post_step_tool_mapping_by_tool_id(  # noqa: SLF001
        context=context,
        mapping_key="executable_overrides",
    ) == {
        "dart.build_runner": {
            "dart": "/tmp/workspace/toolchains/dart-sdk/bin/dart",
        }
    }


def _relationship_update_typed_plan() -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:" "ocg:aware_demo/relationship:demo"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.relationship.update",
                "semantic_key": "ocg:aware_demo/relationship:demo",
                "ontology_subject_kind": "relationship",
            },
        ),
    }


def _materialization_request(
    *,
    package_root: Path,
    change_preview: dict[str, object],
    context: dict[str, object] | None = None,
    workspace_root: Path = _REPO_ROOT,
) -> SemanticPackageMaterializationRequest:
    return SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=workspace_root,
        manifest_path=package_root / "aware.toml",
        context=context or {},
        code_package_delta=None,
        semantic_analysis=None,
        change_preview=change_preview,
    )


@pytest.mark.asyncio
async def test_meta_leaf_materialization_receives_workspace_source_code_package_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "modules" / "demo" / "ontology"
    package_root.mkdir(parents=True)
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text("[package]\nname = 'demo'\n", encoding="utf-8")
    source_code_package_id = uuid4()
    captured: dict[str, object] = {}
    expected_result = object()

    async def _fake_leaf_materialization(**kwargs: object) -> object:
        captured.update(kwargs)
        return expected_result

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_package_leaf_from_manifest",
        _fake_leaf_materialization,
    )

    result = (
        await workspace_provider._materialize_leaf_package_if_supported(  # noqa: SLF001
            request=SemanticPackageMaterializationRequest(
                runtime=object(),
                index=SimpleNamespace(ocg=object(), opg_by_hash={}),
                actor_id=None,
                branch_id=uuid4(),
                workspace_root=workspace_root,
                manifest_path=manifest_path,
                source_code_package_id=source_code_package_id,
                context={},
                change_preview={},
            )
        )
    )

    assert result is expected_result
    assert captured["source_code_package_id"] == source_code_package_id


def test_meta_workspace_provider_does_not_import_runtime_harness_or_index() -> None:
    source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/materialization/workspace_provider.py"
    ).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "RuntimeHarness" not in source
    assert "AwareRuntimeIndex" not in source
    assert "CodeLanguage.python" not in source
    assert "runtime_handlers_meta" not in source


@pytest.mark.asyncio
async def test_meta_workspace_provider_leaf_materialization_uses_index_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    captured: dict[str, object] = {}

    async def fake_leaf_materialization(**kwargs: object) -> object:
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_package_leaf_from_manifest",
        fake_leaf_materialization,
    )
    index = SimpleNamespace(ocg=object(), opg_by_hash={})
    runtime = object()
    request = SemanticPackageMaterializationRequest(
        runtime=runtime,
        index=index,
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.toml",
        context={},
        code_package_delta=None,
        semantic_analysis=None,
        change_preview={},
    )

    result = (
        await workspace_provider._materialize_leaf_package_if_supported(  # noqa: SLF001
            request=request,
        )
    )

    assert result is sentinel
    assert captured["runtime"] is runtime
    assert captured["index"] is index


@pytest.mark.asyncio
async def test_meta_workspace_provider_leaf_materialization_forwards_force_fresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    captured: dict[str, object] = {}

    async def fake_leaf_materialization(**kwargs: object) -> object:
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_package_leaf_from_manifest",
        fake_leaf_materialization,
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=SimpleNamespace(ocg=object(), opg_by_hash={}),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.toml",
        context={
            "semantic_materialization_force_fresh": {
                "schema": "aware.workspace.semantic_materialization.force_fresh.v1",
                "enabled": True,
            },
        },
        code_package_delta=None,
        semantic_analysis=None,
        change_preview={},
    )

    result = (
        await workspace_provider._materialize_leaf_package_if_supported(  # noqa: SLF001
            request=request,
        )
    )

    assert result is sentinel
    assert captured["force_fresh_semantic_materialization"] is True


@pytest.mark.asyncio
async def test_meta_workspace_provider_leaf_external_graphs_follow_manifest_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_provider_delta_workspace_manifest(
        workspace_root=tmp_path,
        dependency_package_names=("dep-ontology",),
    )
    dep_graph = _runtime_test_graph(fqn_prefix="dep_demo", graph_hash="dep-hash")
    unused_graph = _runtime_test_graph(
        fqn_prefix="unused_demo",
        graph_hash="unused-hash",
    )
    captured: dict[str, object] = {}

    async def fake_leaf_materialization(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_package_leaf_from_manifest",
        fake_leaf_materialization,
    )

    await workspace_provider._materialize_leaf_package_if_supported(  # noqa: SLF001
        request=SemanticPackageMaterializationRequest(
            runtime=object(),
            index=SimpleNamespace(ocg=object(), opg_by_hash={}),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=tmp_path,
            manifest_path=manifest_path,
            context={
                SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                    "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                    "entries": (
                        {
                            "package_name": "dep-ontology",
                            "fqn_prefix": "dep_demo",
                        },
                        {
                            "package_name": "unused-ontology",
                            "fqn_prefix": "unused_demo",
                        },
                    ),
                },
                "runtime_object_config_graphs": (dep_graph, unused_graph),
            },
            code_package_delta=None,
            semantic_analysis=None,
            change_preview={},
        )
    )

    assert tuple(
        graph.fqn_prefix
        for graph in cast(tuple[ObjectConfigGraph, ...], captured["external_graphs"])
    ) == ("dep_demo",)


@pytest.mark.asyncio
async def test_meta_workspace_provider_leaf_external_graphs_prefer_runtime_graph_per_fqn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_provider_delta_workspace_manifest(
        workspace_root=tmp_path,
        dependency_package_names=("dep-ontology",),
    )
    runtime_dep_graph = _runtime_test_graph(
        fqn_prefix="dep_demo",
        graph_hash="dep-runtime-hash",
    )
    source_dep_graph = _runtime_test_graph(
        fqn_prefix="dep_demo",
        graph_hash="dep-source-hash",
    )
    captured: dict[str, object] = {}

    async def fake_leaf_materialization(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_package_leaf_from_manifest",
        fake_leaf_materialization,
    )

    await workspace_provider._materialize_leaf_package_if_supported(  # noqa: SLF001
        request=SemanticPackageMaterializationRequest(
            runtime=object(),
            index=SimpleNamespace(ocg=object(), opg_by_hash={}),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=tmp_path,
            manifest_path=manifest_path,
            context={
                SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                    "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                    "entries": (
                        {
                            "package_name": "dep-ontology",
                            "fqn_prefix": "dep_demo",
                        },
                    ),
                },
                "runtime_object_config_graphs": (runtime_dep_graph,),
                "semantic_object_config_graphs": (source_dep_graph,),
            },
            code_package_delta=None,
            semantic_analysis=None,
            change_preview={},
        )
    )

    assert captured["external_graphs"] == [runtime_dep_graph]


@pytest.mark.asyncio
async def test_meta_workspace_provider_leaf_external_graphs_drop_unrelated_context_without_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_provider_delta_workspace_manifest(
        workspace_root=tmp_path,
        dependency_package_names=(),
    )
    skill_graph = _runtime_test_graph(
        fqn_prefix="aware_skill",
        graph_hash="skill-hash",
    )
    captured: dict[str, object] = {}

    async def fake_leaf_materialization(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_package_leaf_from_manifest",
        fake_leaf_materialization,
    )

    await workspace_provider._materialize_leaf_package_if_supported(  # noqa: SLF001
        request=SemanticPackageMaterializationRequest(
            runtime=object(),
            index=SimpleNamespace(ocg=object(), opg_by_hash={}),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=tmp_path,
            manifest_path=manifest_path,
            context={
                "semantic_object_config_graphs": (skill_graph,),
            },
            code_package_delta=None,
            semantic_analysis=None,
            change_preview={},
        )
    )

    assert captured["external_graphs"] == []


@pytest.mark.asyncio
async def test_meta_workspace_provider_leaf_language_materialization_uses_context_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    package_root.mkdir(parents=True)
    (workspace_root / "modules" / "demo" / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
                "",
                "[[dependencies]]",
                'package_name = "dep-ontology"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    dep_package_root = workspace_root / "modules" / "dep" / "structure" / "ontology"
    dep_package_root.mkdir(parents=True)
    (workspace_root / "modules" / "dep" / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (dep_package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "dep-ontology"',
                'fqn_prefix = "dep_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "dep_demo"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    unused_package_root = (
        workspace_root / "modules" / "unused" / "structure" / "ontology"
    )
    unused_package_root.mkdir(parents=True)
    (workspace_root / "modules" / "unused" / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (unused_package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "unused-ontology"',
                'fqn_prefix = "unused_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "unused_demo"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runtime_target_root = (
        workspace_root / "modules" / "demo" / "runtime" / "aware_demo_runtime"
    )
    dep_graph = ObjectConfigGraph(
        id=uuid4(),
        name="dep",
        hash="dep-hash",
        fqn_prefix="dep_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    unused_graph = ObjectConfigGraph(
        id=uuid4(),
        name="unused",
        hash="unused-hash",
        fqn_prefix="unused_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    stale_runtime_graph = ObjectConfigGraph(
        id=uuid4(),
        name="stale_demo_runtime",
        hash="stale-demo-runtime-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )

    calls: list[Any] = []

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        output_key = (
            "python.meta_runtime_handlers_provider"
            if request.renderer_kind == "runtime_handlers_meta"
            else "python.bootstrap_manifest"
        )
        return SimpleNamespace(
            ownership_receipts=(
                _FakeOwnershipReceipt(
                    {
                        "output_key": output_key,
                        "path": "generated.py",
                    }
                ),
            ),
            post_step_receipts=(),
            tool_steps=(
                SimpleNamespace(
                    name="render",
                    duration_s=1.25,
                    status="succeeded",
                ),
            ),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )
    leaf_result = SimpleNamespace(
        aware_toml_path=package_root / "aware.toml",
        object_config_graph=ObjectConfigGraph(
            id=uuid4(),
            name="demo",
            hash="demo-hash",
            fqn_prefix="aware_demo",
            language=CodeLanguage.aware,
            object_config_graph_nodes=[],
        ),
        code_package=SimpleNamespace(id=uuid4()),
        object_config_graph_package=SimpleNamespace(
            id=uuid4(),
            fqn_prefix="aware_demo",
            package_name="demo-ontology",
            function_impl_ownership=(
                ObjectConfigGraphPackageFunctionImplOwnership.compiler
            ),
            function_impl_parity_policy=(
                ObjectConfigGraphPackageFunctionImplParityPolicy.error
            ),
        ),
        object_config_graph_object_instance_graph_commit_id=uuid4(),
    )

    receipts = await workspace_provider._leaf_language_materialization_receipts(  # noqa: SLF001
        request=cast(
            Any,
            SimpleNamespace(
                context={
                    "runtime_object_config_graphs": (
                        dep_graph,
                        stale_runtime_graph,
                        unused_graph,
                    ),
                    "language_materialization_targets": [
                        {
                            "target_language_plugin_id": "python",
                            "output_root": ("modules/demo/structure/ontology/python"),
                            "import_root": "aware_demo_ontology",
                            "package_name": "demo-ontology",
                            "materialization_source": "ontology",
                            "code_package_surface": "structure",
                            "stable_ids_import_root": "aware_demo_ontology",
                            "renderer_profile": "orm_runtime",
                        },
                        {
                            "target_language_plugin_id": "python",
                            "output_root": ("modules/demo/runtime/aware_demo_runtime"),
                            "import_root": "aware_demo_runtime",
                            "package_name": "aware_demo_runtime",
                            "materialization_source": "runtime_handlers",
                            "code_package_surface": "runtime",
                            "renderer_kind": "runtime_handlers_meta",
                            "stable_ids_import_root": "aware_demo_ontology",
                            "source_is_runtime": True,
                        },
                        {
                            "target_language_plugin_id": "python",
                            "output_root": ("modules/other/structure/ontology/python"),
                            "import_root": "aware_other_ontology",
                            "package_name": "other-ontology",
                            "materialization_source": "ontology",
                            "code_package_surface": "structure",
                            "stable_ids_import_root": "aware_other_ontology",
                            "renderer_profile": "orm_runtime",
                        },
                    ],
                },
                workspace_root=workspace_root,
            ),
        ),
        leaf_result=cast(Any, leaf_result),
    )

    assert len(calls) == 2
    ontology_request = calls[0]
    assert ontology_request.target_language_plugin_id == CodeLanguage.python
    assert ontology_request.materialization_source == "ontology"
    assert ontology_request.renderer_profile == "orm_runtime"
    assert ontology_request.renderer_kind is None
    assert ontology_request.source_is_runtime is False
    assert ontology_request.output_root == package_root / "python"
    assert ontology_request.import_root == "aware_demo_ontology"
    assert tuple(
        graph.fqn_prefix for graph in ontology_request.external_runtime_graphs
    ) == ("dep_demo",)
    assert tuple(
        graph.fqn_prefix for graph in ontology_request.package_dependency_graphs
    ) == ("dep_demo",)
    runtime_handler_request = calls[1]
    assert runtime_handler_request.materialization_source == "runtime_handlers"
    assert runtime_handler_request.renderer_kind == "runtime_handlers_meta"
    assert runtime_handler_request.source_graph is leaf_result.object_config_graph
    assert runtime_handler_request.source_is_runtime is False
    assert runtime_handler_request.output_root == runtime_target_root
    assert runtime_handler_request.import_root == "aware_demo_runtime"
    assert runtime_handler_request.stable_ids_import_root == "aware_demo_ontology"
    assert (
        ontology_request.runtime_to_language_cache
        is runtime_handler_request.runtime_to_language_cache
    )
    assert ontology_request.runtime_to_language_cache is not None
    assert ontology_request.runtime_to_language_cache.deep_copy_stores is False
    assert (
        ontology_request.runtime_derivation_cache
        is runtime_handler_request.runtime_derivation_cache
    )
    assert ontology_request.runtime_derivation_cache is not None
    assert ontology_request.runtime_derivation_cache.deep_copy_stores is False
    assert [
        receipt["output_key"] for receipt in receipts.artifact_ownership_receipts
    ] == [
        "python.bootstrap_manifest",
        "python.meta_runtime_handlers_provider",
    ]
    assert all(
        str(receipt["path"]).startswith(str(workspace_root))
        for receipt in receipts.artifact_ownership_receipts
    )
    assert receipts.tool_timings_s == {
        "target_0.python.ontology.orm_runtime.render": 1.25,
        "target_1.python.runtime_handlers.runtime_handlers_meta.render": 1.25,
        "total": 2.5,
    }
    assert receipts.runtime_derivation_cache == {
        "entry_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "store_count": 0,
        "deep_copy_hits": False,
    }
    assert [receipt["timing_key"] for receipt in receipts.tool_step_receipts] == [
        "target_0.python.ontology.orm_runtime.render",
        "target_1.python.runtime_handlers.runtime_handlers_meta.render",
    ]
    assert receipts.runtime_to_language_cache == {
        "entry_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "store_count": 0,
        "deep_copy_hits": False,
    }


@pytest.mark.asyncio
async def test_meta_workspace_provider_leaf_language_materialization_reports_progress(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    package_root.mkdir(parents=True)
    (workspace_root / "modules" / "demo" / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="demo",
        hash="demo-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    progress_events: list[dict[str, object]] = []

    async def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    def fake_language_materialization(request: Any) -> object:
        assert request.target_language_plugin_id == CodeLanguage.python
        assert request.progress_callback is not None
        request.progress_callback(
            {
                "phase_name": "meta.language_target.subphase",
                "status": "running",
                "detail_payload": {"subphase_name": "render"},
            }
        )
        request.progress_callback(
            {
                "phase_name": "meta.language_target.subphase",
                "status": "succeeded",
                "duration_s": 1.25,
                "detail_payload": {
                    "subphase_name": "render",
                    "generated_file_count": 0,
                },
            }
        )
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(),
            generated_files=(),
            package_outputs=(),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )
    leaf_result = SimpleNamespace(
        aware_toml_path=package_root / "aware.toml",
        object_config_graph=source_graph,
        code_package=SimpleNamespace(id=uuid4()),
        object_config_graph_package=SimpleNamespace(
            id=uuid4(),
            fqn_prefix="aware_demo",
            package_name="demo-ontology",
            function_impl_ownership=(
                ObjectConfigGraphPackageFunctionImplOwnership.compiler
            ),
            function_impl_parity_policy=(
                ObjectConfigGraphPackageFunctionImplParityPolicy.error
            ),
        ),
        object_config_graph_object_instance_graph_commit_id=uuid4(),
    )

    await workspace_provider._leaf_language_materialization_receipts(  # noqa: SLF001
        request=cast(
            Any,
            SimpleNamespace(
                context={
                    "language_materialization_targets": [
                        {
                            "target_language_plugin_id": "python",
                            "output_root": ("modules/demo/structure/ontology/python"),
                            "import_root": "aware_demo_ontology",
                            "package_name": "demo-ontology",
                            "materialization_source": "ontology",
                            "code_package_surface": "structure",
                            "renderer_profile": "orm_runtime",
                        },
                    ],
                },
                workspace_root=workspace_root,
                progress_callback=progress_callback,
            ),
        ),
        leaf_result=cast(Any, leaf_result),
    )

    assert [(event["phase_name"], event["status"]) for event in progress_events] == [
        ("meta.language_materialization", "running"),
        ("meta.language_target", "running"),
        ("meta.language_target.subphase", "running"),
        ("meta.language_target.subphase", "succeeded"),
        ("meta.language_target", "succeeded"),
        ("meta.language_materialization", "succeeded"),
    ]
    running_detail = cast(dict[str, object], progress_events[0]["detail_payload"])
    assert running_detail["target_count"] == 1
    subphase_detail = cast(dict[str, object], progress_events[3]["detail_payload"])
    assert subphase_detail["subphase_name"] == "render"
    assert subphase_detail["target_language_plugin_id"] == "python"
    assert progress_events[3]["duration_s"] == 1.25
    target_detail = cast(dict[str, object], progress_events[4]["detail_payload"])
    assert target_detail["generated_code_package_ref_count"] == 0
    assert target_detail["generated_code_package_delta_count"] == 0


@pytest.mark.asyncio
async def test_meta_workspace_provider_leaf_materialization_reports_subphase_progress(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    progress_events: list[dict[str, object]] = []

    async def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    fake_leaf_result = object()

    async def fake_leaf_materialization(**kwargs: object) -> object:
        callback = kwargs.get("progress_callback")
        assert callback is not None
        await callback(
            {
                "phase_name": "meta.leaf_package.subphase",
                "status": "running",
                "detail_payload": {
                    "subphase_name": "build_object_config_graph_from_code",
                    "package_name": "demo-ontology",
                },
            }
        )
        await callback(
            {
                "phase_name": "meta.leaf_package.subphase",
                "status": "succeeded",
                "duration_s": 2.5,
                "detail_payload": {
                    "subphase_name": "build_object_config_graph_from_code",
                    "package_name": "demo-ontology",
                },
            }
        )
        return fake_leaf_result

    monkeypatch.setattr(
        workspace_provider,
        "_looks_like_meta_runtime_index",
        lambda _index: True,
    )
    monkeypatch.setattr(
        workspace_provider,
        "_validate_declared_generated_package_pin",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_package_leaf_from_manifest",
        fake_leaf_materialization,
    )

    manifest_path = tmp_path / "aware.toml"
    request = SimpleNamespace(
        runtime=object(),
        index=object(),
        actor_id=None,
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        context={},
        progress_callback=progress_callback,
    )

    result = (
        await workspace_provider._materialize_leaf_package_if_supported(  # noqa: SLF001
            request=cast(Any, request),
        )
    )

    assert result is fake_leaf_result
    assert [(event["phase_name"], event["status"]) for event in progress_events] == [
        ("meta.leaf_package.subphase", "running"),
        ("meta.leaf_package.subphase", "succeeded"),
    ]
    subphase_detail = cast(dict[str, object], progress_events[1]["detail_payload"])
    assert subphase_detail["manifest_path"] == manifest_path.as_posix()
    assert subphase_detail["subphase_name"] == "build_object_config_graph_from_code"
    assert subphase_detail["package_name"] == "demo-ontology"
    assert progress_events[1]["duration_s"] == 2.5


@pytest.mark.asyncio
async def test_meta_workspace_provider_language_target_failure_reports_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    package_root.mkdir(parents=True)
    (package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="demo",
        hash="demo-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    progress_events: list[dict[str, object]] = []

    def fake_language_materialization(request: Any) -> object:
        assert request.progress_callback is not None
        request.progress_callback(
            {
                "phase_name": "meta.language_target.subphase",
                "status": "failed",
                "duration_s": 2.0,
                "error": "demo recursion",
                "detail_payload": {
                    "subphase_name": "runtime_to_language",
                    "error_type": "RecursionError",
                },
            }
        )
        raise RecursionError("demo recursion")

    async def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )

    with pytest.raises(RecursionError, match="demo recursion"):
        await workspace_provider._leaf_language_materialization_receipts(  # noqa: SLF001
            request=cast(
                Any,
                SimpleNamespace(
                    context={
                        "language_materialization_targets": [
                            {
                                "target_language_plugin_id": "sql",
                                "output_root": ("modules/demo/structure/ontology/sql"),
                                "import_root": "aware_demo_sql",
                                "package_name": "demo-ontology",
                                "materialization_source": "ontology",
                                "code_package_surface": "structure",
                                "renderer_profile": "orm_runtime",
                            },
                        ],
                    },
                    workspace_root=workspace_root,
                    progress_callback=progress_callback,
                ),
            ),
            leaf_result=cast(
                Any,
                SimpleNamespace(
                    aware_toml_path=package_root / "aware.toml",
                    object_config_graph=source_graph,
                    code_package=SimpleNamespace(id=uuid4()),
                    object_config_graph_package=SimpleNamespace(
                        id=uuid4(),
                        fqn_prefix="aware_demo",
                        package_name="demo-ontology",
                    ),
                    object_config_graph_object_instance_graph_commit_id=uuid4(),
                ),
            ),
        )

    failed_events = [
        event
        for event in progress_events
        if event["phase_name"] == "meta.language_target" and event["status"] == "failed"
    ]
    assert len(failed_events) == 1
    failed_subphase_events = [
        event
        for event in progress_events
        if event["phase_name"] == "meta.language_target.subphase"
        and event["status"] == "failed"
    ]
    assert len(failed_subphase_events) == 1
    failed_subphase_detail = cast(
        dict[str, object],
        failed_subphase_events[0]["detail_payload"],
    )
    assert failed_subphase_detail["subphase_name"] == "runtime_to_language"
    assert failed_subphase_detail["target_language_plugin_id"] == "sql"
    assert failed_subphase_detail["error_type"] == "RecursionError"
    assert failed_subphase_events[0]["duration_s"] == 2.0
    failed_detail = cast(dict[str, object], failed_events[0]["detail_payload"])
    assert failed_detail["target_language_plugin_id"] == "sql"
    assert failed_detail["error_type"] == "RecursionError"
    traceback_tail = failed_detail["error_traceback_tail"]
    assert isinstance(traceback_tail, tuple)
    assert any("demo recursion" in line for line in traceback_tail)


@pytest.mark.parametrize(
    ("persistence_required", "expected_delta_count"),
    ((False, 0), (True, 1)),
)
@pytest.mark.asyncio
async def test_meta_workspace_provider_generated_code_package_snapshots_skip_deltas_without_persistence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    persistence_required: bool,
    expected_delta_count: int,
) -> None:
    workspace_root = tmp_path / "workspace"
    output_root = (
        workspace_root / "modules" / "demo" / "structure" / "ontology" / "python"
    )
    source_root = output_root / "aware_demo_ontology"
    source_root.mkdir(parents=True)
    generated_path = source_root / "__init__.py"
    generated_path.write_text("__all__ = []\n", encoding="utf-8")
    progress_events: list[dict[str, object]] = []
    commit_calls: list[dict[str, object]] = []

    def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    async def fake_commit_code_package_text_snapshot(**kwargs: object) -> object:
        commit_calls.append(dict(kwargs))
        return SimpleNamespace(
            code_package=SimpleNamespace(id=uuid4()),
            commit_id=uuid4(),
            head_commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
            object_count=3,
            change_count=1,
        )

    monkeypatch.setattr(
        workspace_provider,
        "find_meta_graph_projection_hash_by_name",
        lambda **_: "code-package-projection-hash",
    )
    monkeypatch.setattr(
        workspace_provider,
        "commit_code_package_text_snapshot",
        fake_commit_code_package_text_snapshot,
    )

    outputs = await workspace_provider._commit_language_materialization_code_packages(  # noqa: SLF001
        request=cast(
            Any,
            SimpleNamespace(
                index=object(),
                actor_id=None,
                workspace_root=workspace_root,
                context={
                    "workspace_materialization_persistence": {
                        "required": persistence_required,
                    },
                },
                progress_callback=progress_callback,
            ),
        ),
        leaf_result=cast(
            Any,
            SimpleNamespace(
                code_package=SimpleNamespace(id=uuid4()),
                object_config_graph_package=SimpleNamespace(id=uuid4()),
                object_config_graph_object_instance_graph_commit_id=uuid4(),
            ),
        ),
        target=workspace_provider._LanguageMaterializationTarget(  # noqa: SLF001
            target_language_plugin_id=CodeLanguage.python,
            output_root=output_root,
            import_root="aware_demo_ontology",
            package_name="demo-ontology",
            materialization_source="ontology",
            code_package_surface="structure",
            renderer_profile="orm_runtime",
        ),
        result=SimpleNamespace(
            package_outputs=(
                SimpleNamespace(
                    package_name="demo-ontology",
                    output_root=output_root,
                    import_root="aware_demo_ontology",
                    generated_file_refs=(Path("aware_demo_ontology/__init__.py"),),
                    deleted_file_refs=(),
                ),
            ),
        ),
    )

    assert len(commit_calls) == 1
    assert commit_calls[0]["unparsed_texts_by_relative_path"] == {
        "aware_demo_ontology/__init__.py": "__all__ = []\n",
    }
    assert len(outputs.refs) == 1
    assert len(outputs.deltas) == expected_delta_count
    assert outputs.refs[0]["full_delta_payload"] is persistence_required
    assert [(event["phase_name"], event["status"]) for event in progress_events] == [
        ("meta.generated_code_package_snapshot.collect_texts", "running"),
        ("meta.generated_code_package_snapshot.collect_texts", "succeeded"),
        ("meta.generated_code_package_snapshot", "running"),
        ("meta.generated_code_package_snapshot", "succeeded"),
    ]
    collect_detail = cast(dict[str, object], progress_events[0]["detail_payload"])
    assert collect_detail["include_package_inventory"] is True
    running_detail = cast(dict[str, object], progress_events[2]["detail_payload"])
    assert running_detail["full_delta_payload"] is persistence_required
    if persistence_required:
        delta = outputs.deltas[0]
        expected_manifest_kind = str(commit_calls[0]["manifest_kind"])
        expected_config_key = code_package_generated_config_key(
            materialization_source="ontology",
            renderer_kind=None,
            language=CodeLanguage.python,
            surface="structure",
            manifest_kind=expected_manifest_kind,
        )
        expected_config_id = stable_code_package_config_id(
            config_key=expected_config_key,
        )
        producer_payload = cast(
            dict[str, object],
            cast(dict[str, object], delta["production"])["producer"],
        )["provider_payload"]
        assert isinstance(producer_payload, dict)
        assert producer_payload["code_package_surface"] == "structure"
        assert producer_payload["manifest_kind"] == expected_manifest_kind
        assert producer_payload["code_package_config_key"] == expected_config_key
        assert producer_payload["code_package_config_id"] == str(expected_config_id)
        emission_payload = cast(
            dict[str, object],
            cast(dict[str, object], delta["production"])["emission_payload"],
        )
        assert emission_payload["code_package_surface"] == "structure"
        assert emission_payload["manifest_kind"] == expected_manifest_kind
        assert emission_payload["code_package_config_key"] == expected_config_key
        assert emission_payload["code_package_config_id"] == str(expected_config_id)
        paths = {
            path["relative_path"]: path
            for path in cast(tuple[dict[str, object], ...], delta["paths"])
        }
        assert (
            paths["aware_demo_ontology/__init__.py"]["content_text"] == "__all__ = []\n"
        )


@pytest.mark.asyncio
async def test_meta_workspace_provider_runtime_handler_snapshot_uses_explicit_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    output_root = workspace_root / "modules" / "network" / "runtime" / "aware_network"
    generated_path = output_root / "handlers" / "_generated" / "meta_handlers.py"
    handwritten_path = output_root / "handlers" / "impl" / "network" / "network_node.py"
    generated_path.parent.mkdir(parents=True)
    handwritten_path.parent.mkdir(parents=True)
    generated_path.write_text("AWARE_META_GRAPH_HANDLERS = {}\n", encoding="utf-8")
    handwritten_path.write_text(
        "def handwritten() -> None:\n    pass\n", encoding="utf-8"
    )
    progress_events: list[dict[str, object]] = []
    commit_calls: list[dict[str, object]] = []

    def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    async def fake_commit_code_package_text_snapshot(**kwargs: object) -> object:
        commit_calls.append(dict(kwargs))
        return SimpleNamespace(
            code_package=SimpleNamespace(id=uuid4()),
            commit_id=uuid4(),
            head_commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
            object_count=1,
            change_count=1,
        )

    monkeypatch.setattr(
        workspace_provider,
        "find_meta_graph_projection_hash_by_name",
        lambda **_: "code-package-projection-hash",
    )
    monkeypatch.setattr(
        workspace_provider,
        "commit_code_package_text_snapshot",
        fake_commit_code_package_text_snapshot,
    )

    await workspace_provider._commit_language_materialization_code_packages(  # noqa: SLF001
        request=cast(
            Any,
            SimpleNamespace(
                index=object(),
                actor_id=None,
                workspace_root=workspace_root,
                context={"workspace_materialization_persistence": {"required": True}},
                progress_callback=progress_callback,
            ),
        ),
        leaf_result=cast(
            Any,
            SimpleNamespace(
                code_package=SimpleNamespace(id=uuid4()),
                object_config_graph_package=SimpleNamespace(id=uuid4()),
                object_config_graph_object_instance_graph_commit_id=uuid4(),
            ),
        ),
        target=workspace_provider._LanguageMaterializationTarget(  # noqa: SLF001
            target_language_plugin_id=CodeLanguage.python,
            output_root=output_root,
            import_root="aware_network",
            package_name="network-ontology",
            materialization_source="runtime_handlers",
            code_package_surface="runtime",
            renderer_kind="runtime_handlers_impl",
        ),
        result=SimpleNamespace(
            package_outputs=(
                SimpleNamespace(
                    package_name="aware_network",
                    output_root=output_root,
                    import_root="aware_network",
                    generated_file_refs=(Path("handlers/_generated/meta_handlers.py"),),
                    deleted_file_refs=(),
                ),
            ),
        ),
    )

    assert len(commit_calls) == 1
    assert commit_calls[0]["unparsed_texts_by_relative_path"] == {
        "handlers/_generated/meta_handlers.py": "AWARE_META_GRAPH_HANDLERS = {}\n",
    }
    collect_detail = cast(dict[str, object], progress_events[0]["detail_payload"])
    assert collect_detail["include_package_inventory"] is False


@pytest.mark.asyncio
async def test_meta_workspace_provider_leaf_language_materialization_drops_external_graphs_without_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    package_root.mkdir(parents=True)
    (workspace_root / "modules" / "demo" / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="demo",
        hash="demo-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    dep_graph = ObjectConfigGraph(
        id=uuid4(),
        name="dep",
        hash="dep-hash",
        fqn_prefix="dep_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    calls: list[Any] = []

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )
    leaf_result = SimpleNamespace(
        aware_toml_path=package_root / "aware.toml",
        object_config_graph=source_graph,
        code_package=SimpleNamespace(id=uuid4()),
        object_config_graph_package=SimpleNamespace(
            id=uuid4(),
            fqn_prefix="aware_demo",
            package_name="demo-ontology",
        ),
        object_config_graph_object_instance_graph_commit_id=uuid4(),
    )

    receipts = await workspace_provider._leaf_language_materialization_receipts(  # noqa: SLF001
        request=cast(
            Any,
            SimpleNamespace(
                context={
                    "runtime_object_config_graphs": (dep_graph,),
                    "language_materialization_targets": [
                        {
                            "target_language_plugin_id": "python",
                            "output_root": ("modules/demo/structure/ontology/python"),
                            "import_root": "aware_demo_ontology",
                            "package_name": "demo-ontology",
                            "materialization_source": "ontology",
                            "code_package_surface": "structure",
                            "stable_ids_import_root": "aware_demo_ontology",
                            "renderer_profile": "orm_runtime",
                        },
                    ],
                },
                workspace_root=workspace_root,
            ),
        ),
        leaf_result=cast(Any, leaf_result),
    )

    assert len(calls) == 1
    assert calls[0].external_runtime_graphs == ()
    assert calls[0].package_dependency_graphs == ()
    assert calls[0].runtime_to_language_cache is not None
    assert calls[0].runtime_to_language_cache.deep_copy_stores is False
    assert calls[0].runtime_derivation_cache is not None
    assert calls[0].runtime_derivation_cache.deep_copy_stores is False
    assert receipts.runtime_derivation_cache == {
        "entry_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "store_count": 0,
        "deep_copy_hits": False,
    }


@pytest.mark.asyncio
async def test_meta_workspace_provider_delta_outputs_use_language_target_impact_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="demo",
        hash="demo-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    unrelated_graph = ObjectConfigGraph(
        id=uuid4(),
        name="unrelated",
        hash="unrelated-hash",
        fqn_prefix="unrelated_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    calls: list[Any] = []

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(
                SimpleNamespace(
                    name="render",
                    duration_s=0.5,
                    status="succeeded",
                    details={},
                ),
            ),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )

    result = await workspace_provider.materialize_provider_delta_outputs(
        request=SimpleNamespace(
            workspace_root=tmp_path,
            context={
                "semantic_object_config_graphs": (source_graph, unrelated_graph),
                "language_materialization_targets": [
                    {
                        "target_language_plugin_id": "python",
                        "output_root": "runtime/aware_demo_runtime",
                        "import_root": "aware_demo_runtime",
                        "package_name": "aware_demo_runtime",
                        "materialization_source": "runtime_handlers",
                        "code_package_surface": "runtime",
                        "renderer_kind": "runtime_handlers_impl",
                        "source_is_runtime": True,
                    },
                    {
                        "target_language_plugin_id": "python",
                        "output_root": "structure/ontology/python/dto",
                        "import_root": "aware_demo_ontology",
                        "package_name": "demo-ontology-dto",
                        "materialization_source": "ontology_dto",
                        "code_package_surface": "structure",
                        "renderer_profile": "ontology_dto",
                    },
                    {
                        "target_language_plugin_id": "python",
                        "output_root": "structure/ontology/python",
                        "import_root": "aware_demo_ontology",
                        "package_name": "demo-ontology",
                        "materialization_source": "ontology",
                        "code_package_surface": "structure",
                        "renderer_profile": "orm_runtime",
                    },
                    {
                        "target_language_plugin_id": "python",
                        "output_root": "runtime/aware_demo_runtime_meta",
                        "import_root": "aware_demo_runtime",
                        "package_name": "aware_demo_runtime",
                        "materialization_source": "runtime_handlers",
                        "code_package_surface": "runtime",
                        "renderer_kind": "runtime_handlers_meta",
                        "source_is_runtime": True,
                    },
                    {
                        "target_language_plugin_id": "sql",
                        "output_root": "structure/ontology/sql",
                        "import_root": "aware_demo_ontology",
                        "package_name": "demo-ontology-sql",
                        "materialization_source": "ontology",
                        "code_package_surface": "structure",
                        "renderer_profile": "orm_runtime",
                    },
                ],
            },
        ),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operations": (
                {
                    "operation_key": (
                        "meta_ocg_provider_delta:update:"
                        "ocg:aware_demo/relationship:demo"
                    ),
                    "operation_family": "update",
                    "provider_operation_type": "meta_ocg.relationship.update",
                    "semantic_key": "ocg:aware_demo/relationship:demo",
                    "ontology_subject_kind": "relationship",
                },
            ),
        },
    )

    target_impact_plan = result["provider_delta_language_target_impact_plan"]
    assert result["status"] == "provider_delta_output_materialization_ready"
    assert result["target_count"] == 5
    assert result["rendered_target_count"] == 3
    assert result["language_target_impact_selected_target_count"] == 3
    assert result["language_target_impact_skipped_target_count"] == 2
    assert isinstance(target_impact_plan, Mapping)
    assert target_impact_plan["impact_policy"] == "structural_language_targets_only"
    assert target_impact_plan["selected_target_indexes"] == (1, 2, 4)
    assert target_impact_plan["skipped_target_indexes"] == (0, 3)
    assert [call.materialization_source for call in calls] == [
        "ontology_dto",
        "ontology",
        "ontology",
    ]
    assert {
        call.runtime_to_language_cache.store_language_results for call in calls
    } == {
        False,
    }
    assert calls[0].runtime_to_language_cache is not None
    assert calls[0].runtime_to_language_cache.deep_copy_stores is False
    assert {call.reuse_external_runtime_graphs for call in calls} == {True}
    assert {call.derive_external_projection_graphs for call in calls} == {False}
    assert {id(call.runtime_derivation_cache) for call in calls} == {
        id(calls[0].runtime_derivation_cache)
    }
    assert calls[0].runtime_derivation_cache is not None
    assert calls[0].runtime_derivation_cache.deep_copy_stores is False
    assert result["tool_timings_s"] == {
        "target_1.python.ontology_dto.ontology_dto.render": 0.5,
        "target_2.python.ontology.orm_runtime.render": 0.5,
        "target_4.sql.ontology.orm_runtime.render": 0.5,
        "total": 1.5,
    }
    assert result["runtime_to_language_cache"] == {
        "entry_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "store_count": 0,
        "deep_copy_hits": False,
        "language_graph_store_enabled": False,
    }
    assert result["runtime_derivation_cache"] == {
        "entry_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "store_count": 0,
        "deep_copy_hits": False,
    }


@pytest.mark.asyncio
async def test_meta_provider_delta_api_package_uses_current_index_graph_without_hydration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="experience-service-api",
        hash="demo-hash",
        fqn_prefix="aware_experience_service_api",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    calls: list[Any] = []

    async def fail_hydrated_source_graph(**_kwargs: object) -> None:
        raise AssertionError(
            "API package materialization must not hydrate committed OIG"
        )

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(),
        )

    monkeypatch.setattr(
        workspace_provider,
        "_provider_delta_hydrated_output_source_graph",
        fail_hydrated_source_graph,
    )
    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )

    result = await workspace_provider.materialize_provider_delta_outputs(
        request=SimpleNamespace(
            workspace_root=tmp_path,
            context={
                "aware_meta.graph_runtime_context": SimpleNamespace(
                    index=SimpleNamespace(ocg=source_graph),
                ),
                "language_materialization_targets": [
                    {
                        "target_language_plugin_id": "python",
                        "output_root": "apis/experience/python",
                        "import_root": "aware_experience_service_api",
                        "package_name": "experience-service-api",
                        "materialization_source": "api",
                        "code_package_surface": "api",
                        "renderer_profile": "api_public_package",
                    },
                ],
            },
        ),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {
                "semantic_branch_id": str(uuid4()),
                "semantic_root_id": str(source_graph.id),
                "semantic_projection_hash": "sha256:test:projection",
            },
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
    )

    assert result["status"] == "provider_delta_output_materialization_ready"
    assert result["rendered_target_count"] == 1
    assert len(calls) == 1
    assert calls[0].source_graph is source_graph
    assert calls[0].materialization_source == "api"
    assert calls[0].renderer_profile == "api_public_package"


@pytest.mark.asyncio
async def test_meta_provider_delta_hydrated_output_source_graph_returns_language_wrapper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="demo-ontology",
        hash="demo-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )

    class _FakeCachedLaneMaterializer:
        def __init__(self, **_kwargs: object) -> None:
            pass

        async def get(self, **_kwargs: object) -> object:
            return SimpleNamespace(oig=object())

    def _fake_reify_oig_root_model(**_kwargs: object) -> ObjectConfigGraph:
        return source_graph

    from aware_meta.graph.instance.commit import materialization_cache  # noqa: E402
    from aware_meta.runtime import oig_model_reifier  # noqa: E402

    monkeypatch.setattr(
        materialization_cache,
        "CachedLaneMaterializer",
        _FakeCachedLaneMaterializer,
    )
    monkeypatch.setattr(
        oig_model_reifier,
        "reify_oig_root_model",
        _fake_reify_oig_root_model,
    )

    target = workspace_provider._LanguageMaterializationTarget(  # noqa: SLF001
        target_language_plugin_id=CodeLanguage.python,
        output_root=tmp_path / "structure" / "ontology" / "python",
        import_root="aware_demo_ontology",
        package_name="demo-ontology",
        materialization_source="ontology",
        code_package_surface="structure",
        renderer_profile="orm_runtime",
    )
    branch_id = uuid4()
    result = await workspace_provider._provider_delta_hydrated_output_source_graph(  # noqa: SLF001
        context={
            "aware_meta.graph_runtime_context": SimpleNamespace(
                index=SimpleNamespace(
                    ocg=source_graph,
                    opg_by_hash={"sha256:test:projection": object()},
                    attribute_configs_by_id={},
                    class_configs_by_id={},
                ),
            ),
        },
        workspace_root=tmp_path,
        provider_delta_head_move_applied_receipt={
            "head_refs": {
                "semantic_branch_id": str(branch_id),
                "semantic_root_id": str(source_graph.id),
                "semantic_projection_hash": "sha256:test:projection",
            }
        },
        target=target,
    )

    assert result is not None
    assert result.graph is source_graph
    assert result.source_is_runtime is False


@pytest.mark.asyncio
async def test_meta_workspace_provider_delta_outputs_keep_cache_for_reusable_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="demo",
        hash="demo-hash",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    calls: list[Any] = []

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(
                SimpleNamespace(
                    name="render",
                    duration_s=0.25,
                    status="succeeded",
                    details={},
                ),
            ),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )

    result = await workspace_provider.materialize_provider_delta_outputs(
        request=SimpleNamespace(
            workspace_root=tmp_path,
            context={
                "semantic_object_config_graphs": (source_graph,),
                "language_materialization_targets": [
                    {
                        "target_language_plugin_id": "python",
                        "output_root": "runtime/aware_demo_runtime",
                        "import_root": "aware_demo_runtime",
                        "package_name": "aware_demo_runtime",
                        "materialization_source": "runtime_handlers",
                        "code_package_surface": "runtime",
                        "renderer_kind": "runtime_handlers_impl",
                        "source_is_runtime": True,
                    },
                    {
                        "target_language_plugin_id": "python",
                        "output_root": "runtime/aware_demo_runtime_meta",
                        "import_root": "aware_demo_runtime",
                        "package_name": "aware_demo_runtime",
                        "materialization_source": "runtime_handlers",
                        "code_package_surface": "runtime",
                        "renderer_kind": "runtime_handlers_meta",
                        "source_is_runtime": True,
                    },
                ],
            },
        ),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operations": (
                {
                    "operation_key": (
                        "meta_ocg_provider_delta:update:"
                        "ocg:aware_demo/function_impl:demo"
                    ),
                    "operation_family": "update",
                    "provider_operation_type": "meta_ocg.function_impl.update",
                    "semantic_key": "ocg:aware_demo/function_impl:demo",
                    "ontology_subject_kind": "function_impl",
                },
            ),
        },
    )

    assert result["status"] == "provider_delta_output_materialization_ready"
    assert result["rendered_target_count"] == 2
    assert [call.renderer_kind for call in calls] == [
        "runtime_handlers_impl",
        "runtime_handlers_meta",
    ]
    assert {
        call.runtime_to_language_cache.store_language_results for call in calls
    } == {
        True,
    }
    assert calls[0].runtime_to_language_cache is not None
    assert calls[0].runtime_to_language_cache.deep_copy_stores is False
    assert {id(call.runtime_derivation_cache) for call in calls} == {
        id(calls[0].runtime_derivation_cache)
    }
    assert calls[0].runtime_derivation_cache is not None
    assert calls[0].runtime_derivation_cache.deep_copy_stores is False
    assert result["runtime_to_language_cache"] == {
        "entry_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "store_count": 0,
        "deep_copy_hits": False,
    }
    assert result["runtime_derivation_cache"] == {
        "entry_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "store_count": 0,
        "deep_copy_hits": False,
    }


@pytest.mark.asyncio
async def test_meta_workspace_provider_delta_outputs_prune_external_graphs_to_manifest_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_provider_delta_workspace_manifest(
        workspace_root=tmp_path,
        dependency_package_names=("dep-ontology",),
    )
    source_graph = _runtime_test_graph(fqn_prefix="aware_demo", graph_hash="demo-hash")
    dep_graph = _runtime_test_graph(fqn_prefix="dep_demo", graph_hash="dep-hash")
    unused_graph = _runtime_test_graph(
        fqn_prefix="unused_demo",
        graph_hash="unused-hash",
    )
    calls: list[Any] = []

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )

    result = await workspace_provider.materialize_provider_delta_outputs(
        request=_provider_delta_output_request(
            workspace_root=tmp_path,
            manifest_path=manifest_path,
            source_graph=source_graph,
            runtime_graphs=(dep_graph, unused_graph),
        ),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
        provider_delta_typed_operation_plan=_relationship_update_typed_plan(),
    )

    assert result["status"] == "provider_delta_output_materialization_ready"
    assert len(calls) == 1
    assert tuple(graph.fqn_prefix for graph in calls[0].external_runtime_graphs) == (
        "dep_demo",
    )
    assert tuple(graph.fqn_prefix for graph in calls[0].package_dependency_graphs) == (
        "dep_demo",
    )


@pytest.mark.asyncio
async def test_meta_workspace_provider_delta_outputs_drop_external_graphs_without_manifest_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_provider_delta_workspace_manifest(
        workspace_root=tmp_path,
        dependency_package_names=(),
    )
    source_graph = _runtime_test_graph(fqn_prefix="aware_demo", graph_hash="demo-hash")
    dep_graph = _runtime_test_graph(fqn_prefix="dep_demo", graph_hash="dep-hash")
    calls: list[Any] = []

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )

    result = await workspace_provider.materialize_provider_delta_outputs(
        request=_provider_delta_output_request(
            workspace_root=tmp_path,
            manifest_path=manifest_path,
            source_graph=source_graph,
            runtime_graphs=(dep_graph,),
        ),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
        provider_delta_typed_operation_plan=_relationship_update_typed_plan(),
    )

    assert result["status"] == "provider_delta_output_materialization_ready"
    assert len(calls) == 1
    assert calls[0].external_runtime_graphs == ()
    assert calls[0].package_dependency_graphs == ()


@pytest.mark.asyncio
async def test_meta_workspace_provider_delta_outputs_keep_broad_external_graphs_without_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_graph = _runtime_test_graph(fqn_prefix="aware_demo", graph_hash="demo-hash")
    dep_graph = _runtime_test_graph(fqn_prefix="dep_demo", graph_hash="dep-hash")
    calls: list[Any] = []

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )

    result = await workspace_provider.materialize_provider_delta_outputs(
        request=_provider_delta_output_request(
            workspace_root=tmp_path,
            manifest_path=None,
            source_graph=source_graph,
            runtime_graphs=(dep_graph,),
        ),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
        provider_delta_typed_operation_plan=_relationship_update_typed_plan(),
    )

    assert result["status"] == "provider_delta_output_materialization_ready"
    assert len(calls) == 1
    assert tuple(graph.fqn_prefix for graph in calls[0].external_runtime_graphs) == (
        "dep_demo",
    )
    assert calls[0].package_dependency_graphs == ()


@pytest.mark.asyncio
async def test_meta_workspace_provider_reports_non_mutating_plan_evidence() -> None:
    package_root = _home_story_ontology_root()
    change_preview = _home_story_change_preview(package_root)

    result = await workspace_provider.materialize(
        _materialization_request(
            package_root=package_root,
            change_preview=change_preview,
        )
    )

    assert result.mode == "noop"
    assert result.bundle_packages == ()
    assert result.applied_semantic_keys == ()
    assert result.skipped_semantic_keys == result.affected_semantic_keys
    assert result.commit_id is None
    assert result.head_commit_id is None
    assert result.details["semantic_truth_graph"] == "runtime_ocg"
    assert result.details["source_graph_role"] == "compiler_ir"
    assert result.details["runtime_graph_role"] == "runtime_ocg"
    assert cast(int, result.details["semantic_function_call_plan_count"]) >= 5
    execution = cast(
        dict[str, object],
        result.details["semantic_function_call_execution"],
    )
    assert execution["status"] == "disabled"
    assert "not enabled" in cast(str, execution["reason"])


@pytest.mark.asyncio
async def test_meta_workspace_provider_reports_backend_unavailable_when_enabled() -> (
    None
):
    package_root = _home_story_ontology_root()
    change_preview = _home_story_change_preview(package_root)

    result = await workspace_provider.materialize(
        _materialization_request(
            package_root=package_root,
            change_preview=change_preview,
            context={
                SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY: {
                    "enabled": True,
                },
            },
        )
    )

    assert result.mode == "noop"
    assert result.applied_semantic_keys == ()
    assert result.skipped_semantic_keys == result.affected_semantic_keys
    execution = cast(
        dict[str, object],
        result.details["semantic_function_call_execution"],
    )
    assert execution["enabled"] is True
    assert execution["status"] == "backend_unavailable"
    assert "no Meta graph execution backend" in cast(str, execution["reason"])


@pytest.mark.asyncio
async def test_meta_workspace_provider_emits_lifecycle_artifact_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    package_root.mkdir(parents=True)
    (package_root / "aware.toml").write_text(
        "[package]\nname='demo'\n", encoding="utf-8"
    )
    code_package = materialization_service.CodePackage(
        id=uuid4(),
        package_name="demo-ontology",
        language=materialization_service.CodeLanguage.aware,
        surface="structure",
        manifest_kind="aware_toml",
        manifest_relative_path="modules/demo/structure/ontology/aware.toml",
        package_root="modules/demo/structure/ontology",
        sources_root="modules/demo/structure/ontology/aware",
        fqn_prefix="aware_demo",
    )
    object_config_graph = materialization_service.ObjectConfigGraph(
        id=uuid4(),
        name="demo",
        hash="sha256:demo",
        fqn_prefix="aware_demo",
        language=materialization_service.CodeLanguage.aware,
    )
    leaf_result = materialization_service.ObjectConfigGraphPackageLeafMaterializationResult(
        aware_toml_path=package_root / "aware.toml",
        package_branch_id=uuid4(),
        code_package=code_package,
        object_config_graph_package=materialization_service.ObjectConfigGraphPackage(
            id=uuid4(),
            package_name="demo-ontology",
            fqn_prefix="aware_demo",
            source_code_package=code_package,
            source_code_package_id=code_package.id,
            object_config_graph=object_config_graph,
            object_config_graph_id=object_config_graph.id,
            object_config_graph_object_instance_graph_commit_id=uuid4(),
        ),
        object_config_graph=object_config_graph,
        owned_file_paths=(),
        code_package_commit_id=None,
        code_package_head_commit_id=uuid4(),
        code_package_object_instance_graph_commit_id=uuid4(),
        object_config_graph_commit_id=None,
        object_config_graph_head_commit_id=uuid4(),
        object_config_graph_object_instance_graph_commit_id=uuid4(),
        object_config_graph_package_commit_id=None,
        object_config_graph_package_head_commit_id=uuid4(),
        object_config_graph_package_object_instance_graph_commit_id=uuid4(),
        phase_timings_s={},
        code_package_build_runtime_telemetry={},
        code_package_build_invoke_perf_ms={},
        code_package_upsert_runtime_telemetry={},
        code_package_upsert_invoke_perf_ms={},
        semantic_commit_strategy="fingerprint_reuse",
        semantic_commit_fallback_reset=False,
        semantic_commit_phase_timings_s={},
        materialization_index_receipt={
            "schema": (
                "aware_meta.object_config_graph_package."
                "materialization_index_receipt.v1"
            ),
            "provider_key": "aware_meta",
            "receipt_kind": ("object_config_graph_package_materialization_index"),
            "cache_status": "fingerprint_reuse",
            "cache_key": {
                "package_name": "demo-ontology",
                "object_config_graph_hash": "sha256:demo",
            },
        },
    )

    async def _fake_leaf_materialization(**_: object) -> object:
        return leaf_result

    monkeypatch.setattr(
        workspace_provider,
        "_materialize_leaf_package_if_supported",
        _fake_leaf_materialization,
    )

    result = await workspace_provider.materialize(
        _materialization_request(
            package_root=package_root,
            change_preview={"affected_semantic_keys": ["ocg:demo"]},
            workspace_root=workspace_root,
        )
    )

    receipts = cast(
        tuple[dict[str, object], ...], result.details["artifact_ownership_receipts"]
    )
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt["producer_provider_key"] == "aware_meta"
    assert receipt["artifact_role"] == "lifecycle_receipt"
    assert receipt["output_key"] == "language_materialization_lifecycle_receipt"
    assert str(receipt["path"]).startswith(
        (workspace_root / ".aware" / "materializations").as_posix()
    )
    assert "_aware" not in Path(str(receipt["path"])).parts
    assert Path(str(receipt["path"])).is_file()
    index_receipts = cast(
        tuple[dict[str, object], ...],
        result.details["materialization_index_receipts"],
    )
    assert len(index_receipts) == 1
    index_receipt = index_receipts[0]
    assert (
        index_receipt["receipt_kind"]
        == "object_config_graph_package_materialization_index"
    )
    assert index_receipt["cache_status"] == "fingerprint_reuse"
    index_cache_key = cast(dict[str, object], index_receipt["cache_key"])
    assert index_cache_key["package_name"] == "demo-ontology"
    assert result.details["materialized_language_packages"] == ()
    assert result.details["materialized_language_package_count"] == 0
    assert result.semantic_object_config_graphs == (object_config_graph,)


@pytest.mark.asyncio
async def test_meta_workspace_provider_executes_via_graph_backend_when_enabled() -> (
    None
):
    package_root = _home_story_ontology_root()
    change_preview = _home_story_change_preview(package_root)
    backend = _RecordingMetaGraphBackend()

    result = await workspace_provider.materialize(
        _materialization_request(
            package_root=package_root,
            change_preview=change_preview,
            context={
                SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY: {
                    "enabled": True,
                },
                SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY: {
                    "aware_meta": backend,
                },
            },
        )
    )

    execution = cast(
        dict[str, object],
        result.details["semantic_function_call_execution"],
    )
    assert execution["status"] == "executed"
    assert cast(dict[str, int], execution["status_counts"]) == {
        "invoked": len(backend.invocations),
    }
    assert result.mode == "delta"
    assert result.applied_semantic_keys
    assert result.skipped_semantic_keys == ()
    assert result.commit_id is not None
    assert result.head_commit_id == result.commit_id
    assert len(result.bundle_packages) == 1
    bundle = result.bundle_packages[0]
    assert bundle.package_key == "home-ontology"
    assert str(bundle.semantic_package_id) == _object_id_for_semantic_key(
        "ocg_package:home-ontology"
    )
    assert str(bundle.semantic_root_id) == _object_id_for_semantic_key("ocg:aware_home")
    assert bundle.semantic_head_commit_id == result.commit_id

    assert tuple(invocation.provider_key for invocation in backend.invocations) == (
        "aware_meta",
    ) * len(backend.invocations)
    assert backend.invocations[0].function_ref == META_OCG_BUILD_FUNCTION_REF
    assert backend.invocations[0].call_target == "constructor"
    assert backend.invocations[0].arguments == {
        "name": "aware_home",
        "hash": backend.invocations[0].arguments["hash"],
        "fqn_prefix": "aware_home",
        "language": "aware",
    }
    package_invocation = next(
        invocation
        for invocation in backend.invocations
        if invocation.function_ref == META_OCG_PACKAGE_BUILD_FUNCTION_REF
    )
    assert package_invocation.arguments["package_name"] == "home-ontology"
    assert package_invocation.arguments["fqn_prefix"] == "aware_home"
    assert package_invocation.arguments["object_config_graph_id"] == (
        _object_id_for_semantic_key("ocg:aware_home")
    )
    assert package_invocation.arguments.get(
        "object_config_graph_object_instance_graph_commit_id"
    )

    node_invocations = tuple(
        invocation
        for invocation in backend.invocations
        if invocation.function_ref == META_OCG_CREATE_NODE_FUNCTION_REF
    )
    assert node_invocations
    assert all(invocation.call_target == "instance" for invocation in node_invocations)
    assert {invocation.receiver_object_id for invocation in node_invocations} == {
        _object_id_for_semantic_key("ocg:aware_home")
    }
    assert {
        invocation.arguments.get("node_key")
        for invocation in node_invocations
        if invocation.arguments.get("type") == "relationship"
    } == {
        "aware_home.default.home.Home:doors:one_to_many:aware_home.default.home.Door",
        "aware_home.default.home.Home:tvs:one_to_many:aware_home.default.home.Tv",
    }


@pytest.mark.asyncio
async def test_meta_workspace_provider_resolves_runtime_relationship_node_plans() -> (
    None
):
    package_root = _home_story_ontology_root()
    change_preview = _home_story_change_preview(package_root)

    result = await workspace_provider.materialize(
        _materialization_request(
            package_root=package_root,
            change_preview=change_preview,
        )
    )

    resolutions = cast(
        tuple[dict[str, object], ...],
        tuple(
            cast(
                tuple[object, ...], result.details["semantic_function_call_resolutions"]
            )
        ),
    )
    relationship_node_resolutions = tuple(
        resolution
        for resolution in resolutions
        if resolution["function_ref"] == META_OCG_CREATE_NODE_FUNCTION_REF
        and _resolution_arguments(resolution).get("type") == "relationship"
    )
    assert {
        _resolution_arguments(resolution).get("node_key")
        for resolution in relationship_node_resolutions
    } == {
        "aware_home.default.home.Home:doors:one_to_many:aware_home.default.home.Door",
        "aware_home.default.home.Home:tvs:one_to_many:aware_home.default.home.Tv",
    }
    assert all(
        resolution["status"] == "create_child"
        for resolution in relationship_node_resolutions
    )
    assert all(
        _resolution_metadata(resolution)["semantic_truth_graph"] == "runtime_ocg"
        for resolution in relationship_node_resolutions
    )


@pytest.mark.asyncio
async def test_meta_workspace_provider_marks_existing_runtime_nodes_noop() -> None:
    package_root = _home_story_ontology_root()
    change_preview = _home_story_change_preview(package_root)
    current_home_id = str(uuid4())

    result = await workspace_provider.materialize(
        _materialization_request(
            package_root=package_root,
            change_preview=change_preview,
            context={
                SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: {
                    "aware_meta": {
                        "current_semantic_object_ids": {
                            "ocg:aware_home/node:aware_home.default.home.Home": (
                                current_home_id
                            ),
                        },
                    },
                },
            },
        )
    )

    resolutions = cast(
        tuple[dict[str, object], ...],
        tuple(
            cast(
                tuple[object, ...], result.details["semantic_function_call_resolutions"]
            )
        ),
    )
    home_resolution = next(
        resolution
        for resolution in resolutions
        if resolution.get("result_semantic_key")
        == "ocg:aware_home/node:aware_home.default.home.Home"
    )
    assert home_resolution["status"] == "noop_existing"
    assert home_resolution["result_object_id"] == current_home_id
    status_counts = cast(
        dict[str, int],
        result.details["semantic_function_call_resolution_status_counts"],
    )
    assert status_counts["noop_existing"] == 1


def _resolution_arguments(resolution: dict[str, object]) -> dict[str, object]:
    return cast(dict[str, object], resolution["arguments"])


def _resolution_metadata(resolution: dict[str, object]) -> dict[str, object]:
    return cast(dict[str, object], resolution["metadata"])


def _object_id_for_semantic_key(semantic_key: str | None) -> str:
    if semantic_key is None:
        semantic_key = "unknown"
    return str(uuid5(NAMESPACE_URL, f"aware-test://meta/{semantic_key}"))
