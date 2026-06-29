from __future__ import annotations

import asyncio
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, cast
from uuid import UUID, uuid4

import pytest

from api_runtime_fixture_artifacts import (
    write_ontology_dependency_runtime_artifacts,
    write_python_models_manifest_for_refs,
)
from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code.semantic_materialization import (
    SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY,
    SemanticFunctionCallContext,
    SemanticPackageMaterializationInput,
    SemanticPackageMaterializationRequest,
    SemanticProviderDeltaDurableExecutionInputs,
    encode_semantic_function_call_context_by_provider,
)
from aware_code.semantic_function_call_execution import (
    SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY,
)
from aware_code.semantic_capability import SemanticAnalysisCapabilityRequest
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackagePathRole,
)
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_package_language_package import (
    ApiPackageLanguagePackage,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage
from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code_ontology.stable_ids import stable_code_package_id
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from aware_orm.session.session import Session
from _api_runtime_test_paths import (
    API_META_PACKAGE_MANIFEST_PATHS,
    API_META_PYTHON_ROOTS,
    REPO_ROOT,
)
from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
import aware_api_runtime.workspace_provider.provider as api_workspace_provider
import aware_api_runtime.workspace_provider.deltas.artifact_patch as api_artifact_patch
from aware_api_runtime.workspace_provider.deltas.transport import (
    api_delta_unsupported_reason,
    code_package_delta_from_provider_delta_request,
)
from aware_api_runtime.workspace_provider.deltas.semantic_analysis import (
    analyze_provider_delta_current_semantics,
)
from aware_api_runtime.workspace_provider.deltas.baseline import (
    api_delta_baseline_commit_refs,
    api_delta_baseline_hydration_preflight,
    api_delta_current_semantic_object_ids,
)
from aware_api_runtime.workspace_provider.deltas.dirty_diff import (
    api_delta_semantic_dirty_diff_from_analysis,
)
from aware_api_runtime.workspace_provider.deltas.typed_operations import (
    api_delta_typed_operation_plan,
)
from aware_api_runtime.workspace_provider.deltas.execution import (
    api_delta_typed_operation_execution_block,
    api_delta_typed_operation_execution_preflight,
)
from aware_api_runtime.workspace_provider.deltas.artifact_patch import (
    api_delta_api_client_service_protocol_patch_receipt,
)
from aware_api_runtime.workspace_provider.deltas.artifact_plan import (
    api_product_runtime_delta_plan,
)
from aware_api_runtime.workspace_provider.deltas.events import (
    api_delta_materialization_event_report,
    api_delta_materialization_event_report_with_workspace_aggregate_evidence,
)
from aware_api_runtime.semantic_functions.execution import (
    API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY,
    ApiSemanticFunctionCallInvocation,
    ApiSemanticFunctionCallInvocationResult,
)
from aware_api_runtime.source.semantic_analysis import analyze_api_semantic_capability
from aware_api_runtime.semantic_function_refs import (
    API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    API_CREATE_CAPABILITY_FUNCTION_REF,
    API_CREATE_FUNCTION_REF,
)
from aware_workspace.features.semantic_materialization.delta_contract import (
    WorkspaceSemanticMaterializationProviderDeltaRequest,
    build_workspace_semantic_materialization_provider_delta_request_bundle,
    classify_workspace_semantic_materialization_provider_delta_request,
    plan_workspace_semantic_materialization_provider_delta_adapter,
)

_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)


def _api_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return API_META_PACKAGE_MANIFEST_PATHS


def _api_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
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


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _write_module_owned_aware_api_dart_fixture(*, workspace_root: Path) -> None:
    _write(
        workspace_root / "aware.module.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[module]",
                'runtime_root = "ontology/runtime/python"',
                "",
                "[[packages]]",
                'id = "api_client_dart"',
                'kind = "code"',
                'manifest = "libs/api/dart/pubspec.yaml"',
                'visibility = "module"',
                "",
            ]
        ),
    )
    _write(
        workspace_root / "libs" / "api" / "dart" / "pubspec.yaml",
        "\n".join(
            [
                "name: aware_api",
                "version: 0.1.0",
                "",
            ]
        ),
    )


def _api_product_runtime_receipt(
    *,
    workspace_root: Path,
    package_name: str,
    artifact_role: str,
    path: Path,
) -> dict[str, object]:
    return {
        "producer_provider_key": "aware_api",
        "producer_key": "aware_api.product_runtime",
        "producer_kind": "api_product_build",
        "semantic_owner": "aware_api.provider",
        "output_key": "api.product_runtime_file",
        "output_kind": "file",
        "artifact_family": "api_product_runtime",
        "artifact_role": artifact_role,
        "artifact_key": f"{package_name}:{artifact_role}:{path.name}",
        "package_name": package_name,
        "path": path.as_posix(),
        "manifest_path": path.resolve().relative_to(workspace_root).as_posix(),
        "digest": "sha256-test",
        "digest_algorithm": "sha256",
        "size_bytes": path.stat().st_size,
        "status": "available",
        "runtime_contract_version": "aware.api.product_runtime.v1",
    }


class _RecordingApiExecutionBackend:
    def __init__(
        self,
        *,
        object_ids: tuple[str, ...] = (),
        commit_ids: tuple[str, ...] = (),
        branch_id: str | None = None,
    ) -> None:
        self.invocations: list[ApiSemanticFunctionCallInvocation] = []
        self.object_ids = object_ids
        self.commit_ids = commit_ids
        self.branch_id = branch_id

    async def invoke(
        self,
        invocation: ApiSemanticFunctionCallInvocation,
    ) -> ApiSemanticFunctionCallInvocationResult:
        self.invocations.append(invocation)
        ordinal = len(self.invocations)
        object_id = (
            self.object_ids[ordinal - 1]
            if ordinal <= len(self.object_ids)
            else "executed-object-id"
        )
        commit_id = (
            self.commit_ids[ordinal - 1] if ordinal <= len(self.commit_ids) else None
        )
        return ApiSemanticFunctionCallInvocationResult(
            object_id=object_id,
            commit_id=commit_id,
            head_commit_id=commit_id,
            branch_id=self.branch_id if commit_id is not None else None,
            evidence={"ordinal": ordinal},
        )


def _write_simple_api_delta_fixture(workspace_root: Path) -> Path:
    api_toml_path = workspace_root / "aware.api.toml"
    _write(
        api_toml_path,
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "demo-api"',
                'fqn_prefix = "aware_demo_api"',
                "version_number = 1",
                'title = "Demo API"',
                'description = "Demo API semantic package"',
                "",
                "[build]",
                'sources_dir = "apis"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
                'compilation_mode = "api_ontology"',
            ]
        )
        + "\n",
    )
    _write(
        workspace_root / "apis" / "demo.aware",
        "\n".join(
            [
                "api demo {",
                "    capability read_demo {",
                "        endpoint read_demo aware_demo_api.ReadDemoRequest {",
                "            response aware_demo_api.DemoResponse;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
    )
    return api_toml_path


def _demo_api_render_input_context_graph() -> ObjectConfigGraph:
    graph_id = uuid4()
    request_class = ClassConfig(
        class_fqn="aware_demo_api.ReadDemoRequest",
        name="ReadDemoRequest",
        is_base=True,
        class_config_attribute_configs=[],
    )
    response_class = ClassConfig(
        class_fqn="aware_demo_api.DemoResponse",
        name="DemoResponse",
        is_base=True,
        class_config_attribute_configs=[],
    )
    nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=request_class.class_fqn,
            object_config_graph_id=graph_id,
            class_config=request_class,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=response_class.class_fqn,
            object_config_graph_id=graph_id,
            class_config=response_class,
        ),
    ]
    for node in nodes:
        node.class_config.object_config_graph_node_id = node.id
    return ObjectConfigGraph(
        id=graph_id,
        name="demo_api_types",
        fqn_prefix="aware_demo_api",
        hash="sha256:demo_api_types",
        language=CodeLanguage.aware,
        object_config_graph_nodes=nodes,
    )


def _install_fake_dart_post_steps(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    from aware_meta.materialization import post_step_executor  # noqa: WPS433

    dart_home = tmp_path / "dart-home"
    dart_pub_cache = tmp_path / "pub-cache"
    fake_dart = tmp_path / "dart-sdk" / "bin" / "dart"

    def _fake_dart_post_step_run(
        *args: object,
        **kwargs: object,
    ) -> SimpleNamespace:
        _ = args
        cwd = kwargs.get("cwd")
        package_root = Path(str(cwd)) if cwd is not None else None
        lib_root = package_root / "lib" if package_root is not None else None
        if lib_root is not None and lib_root.is_dir():
            for source in sorted(
                lib_root.rglob("*.dart"),
                key=lambda path: path.as_posix(),
            ):
                if source.name.endswith((".freezed.dart", ".g.dart")):
                    continue
                for line in source.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if not stripped.startswith("part "):
                        continue
                    tokens = stripped.split("'")
                    if len(tokens) < 2:
                        continue
                    part_path = source.parent / tokens[1]
                    part_path.write_text(
                        f"part of '{source.name}';\n",
                        encoding="utf-8",
                    )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(
        post_step_executor.subprocess,
        "run",
        _fake_dart_post_step_run,
    )
    return (
        {
            "dart.pub_get": {
                "HOME": str(dart_home),
                "PUB_CACHE": str(dart_pub_cache),
            },
            "dart.build_runner": {
                "HOME": str(dart_home),
                "PUB_CACHE": str(dart_pub_cache),
            },
            "dart.format": {
                "HOME": str(dart_home),
            },
        },
        {
            "dart.pub_get": {"dart": str(fake_dart)},
            "dart.build_runner": {"dart": str(fake_dart)},
            "dart.format": {"dart": str(fake_dart)},
        },
    )


def _api_provider_delta_request(
    *,
    api_toml_path: Path,
    change_kind: str = "update",
    delta_change_kind: str | None = None,
    include_code_package_delta: bool = True,
    hint_package_relative_path: str = "apis/demo.aware",
    delta_relative_path: str = "apis/demo.aware",
) -> WorkspaceSemanticMaterializationProviderDeltaRequest:
    request_kwargs: dict[str, object] = {
        "package": {
            "package_name": "demo-api",
            "workspace_manifest_kind": "api",
            "manifest_path": api_toml_path.as_posix(),
            "source_code_package_id": "source-code-package-id",
        },
        "semantic_contract": {
            "module": "aware_api_runtime.semantic_contract",
            "provider_key": "aware_api",
            "role": "aware_api.provider",
            "name": "aware.semantic_provider",
        },
        "current_delta_fingerprint": "sha256:current",
        "delta_cause_hints": {
            "changed_path_count": 1,
            "source_owned_path_count": 1,
            "generated_fallout_path_count": 0,
            "changed_path_classifications": {"source_owned": 1},
            "top_changed_path_limit": 8,
            "top_changed_paths": [
                {
                    "path": hint_package_relative_path,
                    "change_kind": change_kind,
                    "classification": "source_owned",
                    "package_relative_path": hint_package_relative_path,
                    "language": "aware",
                    "is_structural": True,
                }
            ],
            "current_delta_fingerprint_available": True,
            "previous_delta_fingerprint_available": True,
        },
    }
    if include_code_package_delta:
        effective_delta_change_kind = delta_change_kind or change_kind
        content_text = None
        if effective_delta_change_kind != "delete":
            content_text = (api_toml_path.parent / delta_relative_path).read_text(
                encoding="utf-8"
            )
        request_kwargs["code_package_delta"] = CodePackageDelta(
            package_name="demo-api",
            package_root=".",
            sources_root="apis",
            manifest_relative_path=api_toml_path.name,
            authority_kind="workspace_provider_delta",
            source_revision_id="provider-delta-test",
            paths=[
                CodePackageDeltaPath(
                    relative_path=delta_relative_path,
                    kind=CodePackageDeltaKind(effective_delta_change_kind),
                    content_text=content_text,
                    language=CodeLanguage.aware,
                    is_structural=True,
                )
            ],
        )
    return WorkspaceSemanticMaterializationProviderDeltaRequest.model_validate(
        request_kwargs
    )


@pytest.mark.asyncio
async def test_api_workspace_provider_reports_full_rebuild_fallback_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_code_package_id = uuid4()
    package_commit_id = uuid4()
    package_head_commit_id = uuid4()
    api_object_instance_graph_commit_id = uuid4()
    source_object_instance_graph_commit_id = uuid4()
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"

    async def _fake_materialize_api_package_from_manifest(**_: object):
        return SimpleNamespace(
            api_toml_path=tmp_path / "aware.api.toml",
            api=SimpleNamespace(name="demo", id=uuid4()),
            api_package=SimpleNamespace(name="demo-api", id=uuid4()),
            source_code_package_id=source_code_package_id,
            api_source_path="apis/demo.aware",
            source_files=("apis/demo.aware",),
            phase_timings_s={},
            api_endpoint_catalog={},
            api_commit_id=uuid4(),
            api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
            source_object_instance_graph_commit_id=(
                source_object_instance_graph_commit_id
            ),
            package_commit_id=package_commit_id,
            package_head_commit_id=package_head_commit_id,
            generated_dto_graph_count=0,
            generated_dto_class_config_count=0,
        )

    def _fake_compile_api_workspace_for_product_runtime_receipts(**kwargs: object):
        assert kwargs["toml_path"] == tmp_path / "aware.api.toml"
        assert kwargs["workspace_root"] == tmp_path
        return SimpleNamespace(
            service_protocol_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
            )
        )

    def _fake_api_product_runtime_artifact_ownership_receipts(**kwargs: object):
        assert kwargs["package_name"] == "demo-api"
        assert kwargs["workspace_root"] == tmp_path
        assert kwargs["runtime_package_dir"] == runtime_package_dir
        assert kwargs["source_code_package_id"] == source_code_package_id
        assert (
            kwargs["source_object_instance_graph_commit_id"]
            == source_object_instance_graph_commit_id
        )
        return (
            {
                "producer_provider_key": "aware_api",
                "producer_key": "aware_api.product_runtime",
                "producer_kind": "api_product_build",
                "semantic_owner": "aware_api.provider",
                "output_key": "api.product_runtime_file",
                "output_kind": "file",
                "artifact_family": "api_product_runtime",
                "artifact_role": "runtime_file",
                "artifact_key": "demo-api:runtime_file:api.manifest.json",
                "package_name": "demo-api",
                "path": (runtime_package_dir / "api.manifest.json").as_posix(),
                "manifest_path": ".aware/api/runtime/demo-api/api.manifest.json",
                "status": "available",
                "runtime_contract_version": "aware.api.product_runtime.v1",
            },
        )

    monkeypatch.setattr(
        api_workspace_provider,
        "materialize_api_package_from_manifest",
        _fake_materialize_api_package_from_manifest,
    )
    monkeypatch.setattr(
        api_workspace_provider,
        "_compile_api_workspace_for_product_runtime_receipts",
        _fake_compile_api_workspace_for_product_runtime_receipts,
    )
    monkeypatch.setattr(
        api_workspace_provider,
        "_api_product_runtime_artifact_ownership_receipts",
        _fake_api_product_runtime_artifact_ownership_receipts,
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.api.toml",
        code_package_delta=CodePackageDelta(
            package_name="demo-api",
            paths=[
                CodePackageDeltaPath(
                    relative_path="apis/demo.aware",
                    kind=CodePackageDeltaKind.update,
                    language=CodeLanguage.aware,
                    is_structural=True,
                )
            ],
        ),
        change_preview={"affected_semantic_keys": ("demo",)},
    )

    result = await api_workspace_provider.materialize(request)

    assert result.mode == "full_rebuild"
    assert result.affected_semantic_keys == ("demo",)
    assert result.applied_semantic_keys == ("demo",)
    assert result.fallback_reason is not None
    assert "not implemented delta materialization" in result.fallback_reason
    assert result.commit_id == package_commit_id
    assert result.head_commit_id == package_head_commit_id
    assert result.details["semantic_function_call_execution"] == {
        "enabled": False,
        "continue_on_failure": False,
        "status": "disabled",
    }
    assert result.details["artifact_ownership_receipts"] == (
        {
            "producer_provider_key": "aware_api",
            "producer_key": "aware_api.product_runtime",
            "producer_kind": "api_product_build",
            "semantic_owner": "aware_api.provider",
            "output_key": "api.product_runtime_file",
            "output_kind": "file",
            "artifact_family": "api_product_runtime",
            "artifact_role": "runtime_file",
            "artifact_key": "demo-api:runtime_file:api.manifest.json",
            "package_name": "demo-api",
            "path": (runtime_package_dir / "api.manifest.json").as_posix(),
            "manifest_path": ".aware/api/runtime/demo-api/api.manifest.json",
            "status": "available",
            "runtime_contract_version": "aware.api.product_runtime.v1",
        },
    )
    compile_parity_receipt = result.details["compile_parity_receipts"][0]
    assert compile_parity_receipt["schema"] == (
        "aware.api.workspace_materialize.compile_parity_receipt.v1"
    )
    assert compile_parity_receipt["receipt_kind"] == (
        "api_workspace_materialize_compile_parity"
    )
    assert compile_parity_receipt["status"] == "incomplete"
    assert compile_parity_receipt["env_artifacts_required"] is False
    assert "api_client" in compile_parity_receipt["missing_required_evidence"]
    assert "service_protocol" in compile_parity_receipt["missing_required_evidence"]


@pytest.mark.asyncio
async def test_api_workspace_provider_compile_plan_input_emits_product_runtime_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_commit_id = uuid4()
    package_head_commit_id = uuid4()
    compile_plan_path = (
        tmp_path
        / ".aware"
        / "api"
        / "runtime"
        / "aware-actor-view-api"
        / "api.compile_plan.json"
    )
    runtime_package_dir = compile_plan_path.parent
    compile_plan_payload = {
        "schema_version": 9,
        "package_name": "aware-actor-view-api",
        "fqn_prefix": "aware_actor_view_api",
        "source_files": ["experience.view_api.generated"],
        "api_ownership": [],
        "api_ontology": [],
    }
    source_api_toml_path = tmp_path / "apis" / "actor_view" / "aware.api.toml"
    _write(
        source_api_toml_path,
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "aware-actor-view-api"',
                'fqn_prefix = "aware_actor_view_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
            ]
        )
        + "\n",
    )

    async def _fake_materialize_api_package_from_compile_plan_input(**kwargs: object):
        assert kwargs["compile_plan_payload"] == compile_plan_payload
        assert kwargs["compile_plan_path"] == compile_plan_path
        return SimpleNamespace(
            compile_plan_path=compile_plan_path,
            api=SimpleNamespace(name="aware_actor_views", id=uuid4()),
            api_package=SimpleNamespace(
                name="aware-actor-view-api",
                id=uuid4(),
            ),
            api_source_path="experience.view_api.generated",
            source_files=("experience.view_api.generated",),
            phase_timings_s={},
            api_endpoint_catalog={},
            generated_dto_graph_count=0,
            generated_dto_class_config_count=0,
            api_commit_id=uuid4(),
            api_object_instance_graph_commit_id=uuid4(),
            package_commit_id=package_commit_id,
            package_head_commit_id=package_head_commit_id,
        )

    def _fake_compile_api_product_runtime_from_compile_plan(**kwargs: object):
        assert kwargs["compile_plan_payload"] == compile_plan_payload
        assert kwargs["compile_plan_path"] == compile_plan_path
        assert kwargs["source_api_toml_path"] == source_api_toml_path.resolve()
        assert kwargs["workspace_root"] == tmp_path
        return SimpleNamespace(
            service_protocol_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
            )
        )

    def _fake_api_product_runtime_artifact_ownership_receipts(**kwargs: object):
        assert kwargs["package_name"] == "aware-actor-view-api"
        assert kwargs["workspace_root"] == tmp_path
        assert kwargs["runtime_package_dir"] == runtime_package_dir
        return (
            {
                "producer_provider_key": "aware_api",
                "producer_key": "aware_api.product_runtime",
                "producer_kind": "api_product_build",
                "semantic_owner": "aware_api.provider",
                "output_key": "api.product_runtime_file",
                "output_kind": "file",
                "artifact_family": "api_product_runtime",
                "artifact_role": "runtime_file",
                "artifact_key": ("aware-actor-view-api:runtime_file:api.manifest.json"),
                "package_name": "aware-actor-view-api",
                "path": (runtime_package_dir / "api.manifest.json").as_posix(),
                "manifest_path": (
                    ".aware/api/runtime/aware-actor-view-api/api.manifest.json"
                ),
                "status": "available",
                "runtime_contract_version": "aware.api.product_runtime.v1",
            },
        )

    monkeypatch.setattr(
        api_workspace_provider,
        "materialize_api_package_from_compile_plan_input",
        _fake_materialize_api_package_from_compile_plan_input,
    )
    monkeypatch.setattr(
        api_workspace_provider,
        "_compile_api_product_runtime_from_compile_plan",
        _fake_compile_api_product_runtime_from_compile_plan,
    )
    monkeypatch.setattr(
        api_workspace_provider,
        "_api_product_runtime_artifact_ownership_receipts",
        _fake_api_product_runtime_artifact_ownership_receipts,
    )

    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=compile_plan_path,
        materialization_input=SemanticPackageMaterializationInput(
            target_provider_key="aware_api",
            target_semantic_owner="aware_api.provider",
            target_input_key="aware_api.compile_plan",
            package_key="aware-actor-view-api",
            input_artifact_path=compile_plan_path,
            input_artifact_payload=compile_plan_payload,
            source_package_key="aware-control",
            source_manifest_path="apis/actor_view/aware.api.toml",
        ),
    )

    result = await api_workspace_provider.materialize(request)

    assert result.mode == "full_rebuild"
    assert result.commit_id == package_commit_id
    assert result.head_commit_id == package_head_commit_id
    assert result.details["artifact_ownership_receipts"][0]["package_name"] == (
        "aware-actor-view-api"
    )
    assert result.details["compile_parity_receipts"][0]["package_name"] == (
        "aware-actor-view-api"
    )


def test_api_workspace_provider_compile_parity_receipt_is_complete(
    tmp_path: Path,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    runtime_manifest_path = runtime_package_dir / "api.manifest.json"
    compile_plan_path = runtime_package_dir / "api.compile_plan.json"
    api_client_path = (
        runtime_package_dir
        / "public_package"
        / "python"
        / "package"
        / "aware_demo_api"
        / "client.py"
    )
    service_protocol_path = (
        runtime_package_dir
        / "service_protocol"
        / "python"
        / "package"
        / "aware_demo_protocol"
        / "protocol.py"
    )
    _write(
        runtime_manifest_path,
        json.dumps(
            {
                "status": "ok",
                "api_package_name": "demo-api",
                "dependency_graph_mode": "meta_runtime",
                "accessible_dependency_graph_count": 2,
                "compile_plan_artifact_hash": "compile-plan-hash",
                "public_package_materialized": True,
                "service_protocol_materialized": True,
            },
            sort_keys=True,
        )
        + "\n",
    )
    _write(compile_plan_path, '{"schema_version": 1}\n')
    _write(api_client_path, "class DemoClient:\n    pass\n")
    _write(service_protocol_path, "class DemoProtocol:\n    pass\n")

    api_id = uuid4()
    api_package_id = uuid4()
    source_code_package_id = uuid4()
    source_object_instance_graph_commit_id = uuid4()
    api_object_instance_graph_commit_id = uuid4()
    package_head_commit_id = uuid4()

    receipts = (
        _api_product_runtime_receipt(
            workspace_root=tmp_path,
            package_name="demo-api",
            artifact_role="runtime_file",
            path=runtime_manifest_path,
        ),
        _api_product_runtime_receipt(
            workspace_root=tmp_path,
            package_name="demo-api",
            artifact_role="runtime_file",
            path=compile_plan_path,
        ),
        _api_product_runtime_receipt(
            workspace_root=tmp_path,
            package_name="demo-api",
            artifact_role="public_package_file",
            path=api_client_path,
        ),
        _api_product_runtime_receipt(
            workspace_root=tmp_path,
            package_name="demo-api",
            artifact_role="service_protocol_package_file",
            path=service_protocol_path,
        ),
    )

    receipt = api_workspace_provider._api_client_service_protocol_compile_parity_receipts(  # noqa: SLF001
        request=SimpleNamespace(
            workspace_root=tmp_path,
            manifest_path=tmp_path / "aware.api.toml",
            branch_id=uuid4(),
        ),
        result=SimpleNamespace(
            api=SimpleNamespace(name="demo", id=api_id),
            api_package=SimpleNamespace(name="demo-api", id=api_package_id),
            source_code_package_id=source_code_package_id,
            source_object_instance_graph_commit_id=(
                source_object_instance_graph_commit_id
            ),
            api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
            package_head_commit_id=package_head_commit_id,
            runtime_compile_plan_hash="compile-plan-hash",
            source_files=("apis/demo.aware",),
        ),
        artifact_ownership_receipts=receipts,
    )[
        0
    ]

    assert receipt["schema"] == (
        "aware.api.workspace_materialize.compile_parity_receipt.v1"
    )
    assert receipt["receipt_kind"] == "api_workspace_materialize_compile_parity"
    assert receipt["status"] == "compile_equivalent"
    assert receipt["env_artifacts_required"] is False
    assert receipt["missing_required_evidence"] == ()
    assert receipt["available_evidence"] == (
        "api_client",
        "compile_plan",
        "runtime_manifest",
        "service_protocol",
    )
    assert receipt["api_client"]["status"] == "available"
    assert receipt["service_protocol"]["status"] == "available"
    assert receipt["runtime_manifest"]["dependency_graph_mode"] == "meta_runtime"
    assert receipt["runtime_manifest"]["accessible_dependency_graph_count"] == 2
    assert receipt["compile_plan"]["runtime_compile_plan_hash"] == ("compile-plan-hash")
    assert receipt["compatibility_artifact_family"] == "api_product_runtime"
    assert str(receipt["receipt_id"]).startswith("sha256:")


def test_api_workspace_provider_compile_parity_requires_dart_evidence_when_declared(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_api_package_fixture(workspace_root=tmp_path)
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "home-story-api"
    runtime_manifest_path = runtime_package_dir / "api.manifest.json"
    compile_plan_path = runtime_package_dir / "api.compile_plan.json"
    api_client_path = (
        runtime_package_dir
        / "public_package"
        / "python"
        / "package"
        / "aware_home_story_api"
        / "client.py"
    )
    service_protocol_path = (
        runtime_package_dir
        / "service_protocol"
        / "python"
        / "package"
        / "aware_home_story_api_service_protocol"
        / "protocol.py"
    )
    dart_client_path = (
        tmp_path / "apis" / "home" / "dart" / "public" / "lib" / "client.dart"
    )
    _write(
        runtime_manifest_path,
        json.dumps(
            {
                "status": "ok",
                "api_package_name": "home-story-api",
                "compile_plan_artifact_hash": "compile-plan-hash",
                "public_package_materialized": True,
                "service_protocol_materialized": True,
            },
            sort_keys=True,
        )
        + "\n",
    )
    _write(compile_plan_path, '{"schema_version": 1}\n')
    _write(api_client_path, "class HomeStoryApiClient:\n    pass\n")
    _write(service_protocol_path, "class HomeStoryProtocol:\n    pass\n")
    _write(dart_client_path, "class HomeStoryApiClient {}\n")

    dart_receipt = _api_product_runtime_receipt(
        workspace_root=tmp_path,
        package_name="home-story-api",
        artifact_role="dart_public_package_file",
        path=dart_client_path,
    )
    dart_receipt["output_key"] = "dart.public_package_file"
    dart_receipt["target_language_plugin_id"] = "dart"
    receipts = (
        _api_product_runtime_receipt(
            workspace_root=tmp_path,
            package_name="home-story-api",
            artifact_role="runtime_file",
            path=runtime_manifest_path,
        ),
        _api_product_runtime_receipt(
            workspace_root=tmp_path,
            package_name="home-story-api",
            artifact_role="runtime_file",
            path=compile_plan_path,
        ),
        _api_product_runtime_receipt(
            workspace_root=tmp_path,
            package_name="home-story-api",
            artifact_role="public_package_file",
            path=api_client_path,
        ),
        _api_product_runtime_receipt(
            workspace_root=tmp_path,
            package_name="home-story-api",
            artifact_role="service_protocol_package_file",
            path=service_protocol_path,
        ),
        dart_receipt,
    )

    receipt = api_workspace_provider._api_client_service_protocol_compile_parity_receipts(  # noqa: SLF001
        request=SimpleNamespace(
            workspace_root=tmp_path,
            manifest_path=api_toml_path,
            branch_id=uuid4(),
        ),
        result=SimpleNamespace(
            api=SimpleNamespace(name="home_devices", id=uuid4()),
            api_package=SimpleNamespace(name="home-story-api", id=uuid4()),
            source_code_package_id=uuid4(),
            source_object_instance_graph_commit_id=uuid4(),
            api_object_instance_graph_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            runtime_compile_plan_hash="compile-plan-hash",
            source_files=("apis/bindings/home_devices.apis.aware",),
        ),
        artifact_ownership_receipts=receipts,
        language_post_step_receipts=(
            {
                "tool_id": "dart.build_runner",
                "target_language_plugin_id": "dart",
                "status": "succeeded",
            },
        ),
    )[
        0
    ]

    assert receipt["status"] == "compile_equivalent"
    assert receipt["missing_required_evidence"] == ()
    assert "dart_public_package" in receipt["required_evidence"]
    assert "dart_build_runner" in receipt["required_evidence"]
    assert receipt["dart_public_package"]["status"] == "available"
    assert receipt["language_post_steps"]["tool_ids"] == ("dart.build_runner",)


def test_api_workspace_provider_reports_dart_public_package_artifact_receipts(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "apis" / "interface" / "dart" / "public"
    client_path = package_root / "lib" / "client.dart"
    generated_path = package_root / "lib" / "client.g.dart"
    _write(package_root / "pubspec.yaml", "name: aware_interface_service_api\n")
    _write(client_path, "part 'client.g.dart';\n")
    _write(generated_path, "part of 'client.dart';\n")
    compile_result = SimpleNamespace(
        public_package_materialization=SimpleNamespace(
            render_job=SimpleNamespace(
                target=SimpleNamespace(package_root=package_root),
            ),
        ),
    )

    receipts = api_workspace_provider._api_dart_public_package_artifact_ownership_receipts(  # noqa: SLF001
        package_name="interface-service-api",
        workspace_root=tmp_path,
        dart_public_package_compile_result=compile_result,
        source_code_package_id=uuid4(),
        source_object_instance_graph_commit_id=uuid4(),
    )

    assert {receipt["manifest_path"] for receipt in receipts} == {
        "apis/interface/dart/public/lib/client.dart",
        "apis/interface/dart/public/lib/client.g.dart",
        "apis/interface/dart/public/pubspec.yaml",
    }
    assert {receipt["output_key"] for receipt in receipts} == {
        "dart.public_package_file"
    }
    assert {receipt["target_language_plugin_id"] for receipt in receipts} == {"dart"}


@pytest.mark.asyncio
async def test_api_workspace_provider_reuses_product_runtime_receipts_without_compile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_compile_plan_hash = "3d7f2f9f4b0c"
    source_code_package_id = uuid4()
    source_object_instance_graph_commit_id = uuid4()

    async def _fake_materialize_api_package_from_manifest(**_: object):
        return SimpleNamespace(
            api_toml_path=tmp_path / "aware.api.toml",
            api=SimpleNamespace(name="demo", id=uuid4()),
            api_package=SimpleNamespace(name="demo-api", id=uuid4()),
            runtime_compile_plan_hash=runtime_compile_plan_hash,
            source_code_package_id=source_code_package_id,
            api_source_path="apis/demo.aware",
            source_files=("apis/demo.aware",),
            phase_timings_s={},
            api_endpoint_catalog={},
            api_commit_id=uuid4(),
            api_object_instance_graph_commit_id=uuid4(),
            source_object_instance_graph_commit_id=(
                source_object_instance_graph_commit_id
            ),
            package_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            generated_dto_graph_count=0,
            generated_dto_class_config_count=0,
        )

    def _fake_existing_product_runtime_receipts(**kwargs: object):
        assert kwargs["package_name"] == "demo-api"
        assert kwargs["expected_runtime_compile_plan_hash"] == runtime_compile_plan_hash
        assert kwargs["expected_source_files"] == ("apis/demo.aware",)
        assert kwargs["source_code_package_id"] == source_code_package_id
        assert (
            kwargs["source_object_instance_graph_commit_id"]
            == source_object_instance_graph_commit_id
        )
        return (
            {
                "producer_provider_key": "aware_api",
                "producer_key": "aware_api.product_runtime",
                "producer_kind": "api_product_build",
                "semantic_owner": "aware_api.provider",
                "output_key": "api.product_runtime_file",
                "output_kind": "file",
                "artifact_family": "api_product_runtime",
                "artifact_role": "runtime_file",
                "artifact_key": "demo-api:runtime_file:api.manifest.json",
                "package_name": "demo-api",
                "path": (
                    tmp_path / ".aware/api/runtime/demo-api/api.manifest.json"
                ).as_posix(),
                "manifest_path": ".aware/api/runtime/demo-api/api.manifest.json",
                "status": "available",
                "runtime_contract_version": "aware.api.product_runtime.v1",
            },
        )

    def _compile_should_not_run(**_: object):  # pragma: no cover - failure path
        raise AssertionError(
            "compile_api_workspace should not run for matching runtime artifacts"
        )

    monkeypatch.setattr(
        api_workspace_provider,
        "materialize_api_package_from_manifest",
        _fake_materialize_api_package_from_manifest,
    )
    monkeypatch.setattr(
        api_workspace_provider,
        "_api_product_runtime_artifact_ownership_receipts_from_existing_runtime",
        _fake_existing_product_runtime_receipts,
    )
    monkeypatch.setattr(
        api_workspace_provider,
        "_compile_api_workspace_for_product_runtime_receipts",
        _compile_should_not_run,
    )

    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.api.toml",
        code_package_delta=None,
        change_preview={"affected_semantic_keys": ("demo",)},
    )

    result = await api_workspace_provider.materialize(request)

    assert result.details["artifact_ownership_receipts"][0]["producer_key"] == (
        "aware_api.product_runtime"
    )


def test_api_product_runtime_receipts_compile_with_workspace_dependency_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependency_root = (tmp_path / "aware").resolve()
    dependency_root.mkdir()
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    public_package_root = runtime_package_dir / "public_package" / "python" / "package"
    service_protocol_package_root = (
        runtime_package_dir / "service_protocol" / "python" / "package"
    )
    public_package_root.mkdir(parents=True)
    service_protocol_package_root.mkdir(parents=True)
    (runtime_package_dir / "api.manifest.json").write_text(
        '{"status":"ok"}\n',
        encoding="utf-8",
    )
    (public_package_root / "client.py").write_text(
        "class DemoApiClient:\n    pass\n",
        encoding="utf-8",
    )
    (service_protocol_package_root / "protocols.py").write_text(
        "class DemoProtocol:\n    pass\n",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}
    captured_existing: dict[str, object] = {}

    def _fake_existing_runtime(**kwargs: object) -> None:
        captured_existing.update(kwargs)
        return None

    def _fake_compile_runtime(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(
            service_protocol_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
            ),
        )

    monkeypatch.setattr(
        api_workspace_provider,
        "_api_product_runtime_artifact_ownership_receipts_from_existing_runtime",
        _fake_existing_runtime,
    )
    monkeypatch.setattr(
        api_workspace_provider,
        "_compile_api_workspace_for_product_runtime_receipts",
        _fake_compile_runtime,
    )

    receipts = api_workspace_provider._api_product_runtime_artifact_ownership_receipts_for_materialization(
        request=SimpleNamespace(
            manifest_path=tmp_path / "apis" / "demo" / "aware.api.toml",
            workspace_root=tmp_path,
        ),
        package_name="demo-api",
        runtime_compile_plan_hash="compile-plan-hash",
        source_files=("apis/demo/bindings.aware",),
        source_code_package_id=None,
        source_object_instance_graph_commit_id=None,
        dependency_repo_roots=(dependency_root,),
    )

    assert captured["dependency_repo_roots"] == (dependency_root,)
    assert captured_existing["dependency_repo_roots"] == (dependency_root,)
    assert {receipt["artifact_role"] for receipt in receipts} == {
        "public_package_file",
        "runtime_file",
        "service_protocol_package_file",
    }


def test_api_workspace_provider_existing_product_runtime_receipts_validate_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_manifest_path = tmp_path / "apis" / "demo" / "aware.api.toml"
    api_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    api_manifest_path.write_text(
        "\n".join(
            (
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "demo-api"',
                'fqn_prefix = "aware_demo_api"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["bindings.aware"]',
                'compilation_mode = "api_ontology"',
                "",
            )
        ),
        encoding="utf-8",
    )
    (api_manifest_path.parent / "bindings.aware").write_text(
        "api demo {}\n",
        encoding="utf-8",
    )
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    public_package_root = runtime_package_dir / "public_package" / "python" / "package"
    service_protocol_root = (
        runtime_package_dir / "service_protocol" / "python" / "package"
    )
    public_package_root.mkdir(parents=True)
    service_protocol_root.mkdir(parents=True)
    (public_package_root / "models.py").write_text(
        "class Demo: pass\n",
        encoding="utf-8",
    )
    (service_protocol_root / "protocols.py").write_text(
        "PROTOCOL = True\n",
        encoding="utf-8",
    )
    (runtime_package_dir / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "api_package_name": "demo-api",
                "api_toml_relpath": "apis/demo/aware.api.toml",
                "compile_plan_artifact_hash": "expected-hash",
                "public_package_materialized": True,
                "service_protocol_materialized": True,
                "source_files": ["apis/demo/bindings.aware"],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_package_dir / "api.runtime_semantics.json").write_text(
        json.dumps(
            {
                "kind": "api.runtime_semantics",
                "schema_version": 1,
                "api_package_name": "demo-api",
                "dependency_packages": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        api_workspace_provider,
        "_api_runtime_package_dir_for_manifest",
        lambda **_: runtime_package_dir,
    )

    receipts = api_workspace_provider._api_product_runtime_artifact_ownership_receipts_from_existing_runtime(
        manifest_path=api_manifest_path,
        workspace_root=tmp_path,
        package_name="demo-api",
        expected_runtime_compile_plan_hash="expected-hash",
        expected_source_files=("apis/demo/bindings.aware",),
        source_code_package_id=uuid4(),
        source_object_instance_graph_commit_id=uuid4(),
    )

    assert receipts is not None
    assert {receipt["artifact_role"] for receipt in receipts} == {
        "public_package_file",
        "runtime_file",
        "service_protocol_package_file",
    }
    assert (
        api_workspace_provider._api_product_runtime_artifact_ownership_receipts_from_existing_runtime(
            manifest_path=api_manifest_path,
            workspace_root=tmp_path,
            package_name="demo-api",
            expected_runtime_compile_plan_hash="stale-hash",
            expected_source_files=("apis/demo/bindings.aware",),
            source_code_package_id=None,
            source_object_instance_graph_commit_id=None,
        )
        is None
    )


def test_api_workspace_provider_existing_product_runtime_receipts_reject_stale_runtime_semantics_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_manifest_path = _write_existing_runtime_graph_target_api_workspace(tmp_path)
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "focus-api"
    (runtime_package_dir / "public_package" / "python" / "package").mkdir(
        parents=True,
    )
    (runtime_package_dir / "service_protocol" / "python" / "package").mkdir(
        parents=True,
    )
    (runtime_package_dir / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "api_package_name": "focus-api",
                "api_toml_relpath": "apis/focus/aware.api.toml",
                "compile_plan_artifact_hash": "expected-hash",
                "public_package_materialized": True,
                "service_protocol_materialized": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_package_dir / "api.accessible_dependency_graphs.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "graphs": [
                    {
                        "id": str(uuid4()),
                        "name": "focus-ontology",
                        "fqn_prefix": "aware_focus",
                        "object_config_graph_nodes": [],
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    stale_root = tmp_path / "targets" / "public" / "aware"
    stale_package_root = (
        stale_root / "modules" / "focus" / "structure" / "ontology"
    ).resolve()
    (runtime_package_dir / "api.runtime_semantics.json").write_text(
        json.dumps(
            {
                "kind": "api.runtime_semantics",
                "schema_version": 1,
                "api_package_name": "focus-api",
                "dependency_packages": [
                    {
                        "package_name": "focus-ontology",
                        "kind": "ontology",
                        "aware_toml_relpath": (
                            stale_package_root / "aware.toml"
                        ).as_posix(),
                        "package_root_relpath": stale_package_root.as_posix(),
                        "python_root_relpath": (
                            stale_package_root / "python"
                        ).as_posix(),
                        "runtime_root_relpath": (
                            stale_root / "modules" / "focus" / "runtime"
                        )
                        .resolve()
                        .as_posix(),
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        api_workspace_provider,
        "_api_runtime_package_dir_for_manifest",
        lambda **_: runtime_package_dir,
    )

    assert (
        api_workspace_provider._api_product_runtime_artifact_ownership_receipts_from_existing_runtime(
            manifest_path=api_manifest_path,
            workspace_root=tmp_path,
            package_name="focus-api",
            expected_runtime_compile_plan_hash="expected-hash",
            expected_source_files=None,
            source_code_package_id=None,
            source_object_instance_graph_commit_id=None,
        )
        is None
    )


def test_api_workspace_provider_existing_product_runtime_receipts_reject_stale_accessible_graphs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_manifest_path = _write_existing_runtime_graph_target_api_workspace(tmp_path)
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "focus-api"
    (runtime_package_dir / "public_package" / "python" / "package").mkdir(
        parents=True,
    )
    (runtime_package_dir / "service_protocol" / "python" / "package").mkdir(
        parents=True,
    )
    (runtime_package_dir / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "api_package_name": "focus-api",
                "api_toml_relpath": "apis/focus/aware.api.toml",
                "compile_plan_artifact_hash": "expected-hash",
                "public_package_materialized": True,
                "service_protocol_materialized": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_package_dir / "api.accessible_dependency_graphs.json").write_text(
        json.dumps({"schema_version": 1, "graphs": []}, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        api_workspace_provider,
        "_api_runtime_package_dir_for_manifest",
        lambda **_: runtime_package_dir,
    )

    assert (
        api_workspace_provider._api_product_runtime_artifact_ownership_receipts_from_existing_runtime(
            manifest_path=api_manifest_path,
            workspace_root=tmp_path,
            package_name="focus-api",
            expected_runtime_compile_plan_hash="expected-hash",
            expected_source_files=None,
            source_code_package_id=None,
            source_object_instance_graph_commit_id=None,
        )
        is None
    )


def test_api_workspace_provider_product_runtime_receipts_classify_roots(
    tmp_path: Path,
) -> None:
    from aware_api_runtime.build import (
        api_product_runtime_artifact_ownership_receipts,
    )

    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    public_root = runtime_package_dir / "public_package" / "python" / "package"
    service_protocol_root = (
        runtime_package_dir / "service_protocol" / "python" / "package"
    )
    runtime_manifest_path = runtime_package_dir / "api.manifest.json"
    public_pyproject_path = public_root / "pyproject.toml"
    public_client_path = public_root / "demo_api" / "client.py"
    public_build_helper_path = public_root / "demo_api" / "build" / "helpers.py"
    service_pyproject_path = service_protocol_root / "pyproject.toml"
    service_client_path = service_protocol_root / "demo_api_protocol" / "client.py"
    runtime_build_path = runtime_package_dir / "build" / "renderer.state.json"
    runtime_cache_path = runtime_package_dir / "cache" / "renderer.state.json"
    _write(runtime_manifest_path, '{"api": "demo"}\n')
    _write(public_pyproject_path, "[project]\nname = 'demo-api'\n")
    _write(public_client_path, "class DemoClient:\n    pass\n")
    _write(public_build_helper_path, "def generated_build_helper():\n    pass\n")
    _write(service_pyproject_path, "[project]\nname = 'demo-api-protocol'\n")
    _write(service_client_path, "class DemoProtocolClient:\n    pass\n")
    _write(runtime_build_path, '{"build": true}\n')
    _write(runtime_cache_path, '{"cache": true}\n')

    source_code_package_id = uuid4()
    source_object_instance_graph_commit_id = uuid4()
    receipts = api_product_runtime_artifact_ownership_receipts(
        package_name="demo-api",
        workspace_root=tmp_path,
        runtime_package_dir=runtime_package_dir,
        source_code_package_id=source_code_package_id,
        source_object_instance_graph_commit_id=(source_object_instance_graph_commit_id),
    )

    paths_by_role = {
        (receipt["artifact_role"], receipt["manifest_path"]) for receipt in receipts
    }
    assert ("runtime_file", ".aware/api/runtime/demo-api/api.manifest.json") in (
        paths_by_role
    )
    assert (
        "public_package_file",
        ".aware/api/runtime/demo-api/public_package/python/package/demo_api/client.py",
    ) in paths_by_role
    assert (
        "public_package_file",
        ".aware/api/runtime/demo-api/public_package/python/package/demo_api/build/"
        "helpers.py",
    ) in paths_by_role
    assert (
        "service_protocol_package_file",
        ".aware/api/runtime/demo-api/service_protocol/python/package/"
        "demo_api_protocol/client.py",
    ) in paths_by_role
    assert not any(
        str(receipt["manifest_path"]).startswith(".aware/api/runtime/demo-api/build/")
        for receipt in receipts
    )
    assert not any("/cache/" in str(receipt["manifest_path"]) for receipt in receipts)
    assert all(
        receipt["source_code_package_id"] == str(source_code_package_id)
        for receipt in receipts
    )
    assert all(
        receipt["source_object_instance_graph_commit_id"]
        == str(source_object_instance_graph_commit_id)
        for receipt in receipts
    )


def test_api_product_runtime_receipts_reject_source_package_roots(
    tmp_path: Path,
) -> None:
    from aware_api_runtime.build.service import (
        _api_product_runtime_artifact_ownership_receipts,
    )

    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    public_root = tmp_path / "modules" / "api" / "runtime" / "aware_api_runtime"
    service_protocol_root = (
        runtime_package_dir / "service_protocol" / "python" / "package"
    )
    _write(public_root / "build" / "service.py", "def source_helper():\n    pass\n")
    _write(
        service_protocol_root / "demo_api_protocol" / "client.py",
        "class C:\n    pass\n",
    )
    _write(runtime_package_dir / "api.manifest.json", '{"api": "demo"}\n')

    with pytest.raises(RuntimeError, match="outside the generated runtime package"):
        _api_product_runtime_artifact_ownership_receipts(
            package_name="demo-api",
            workspace_root=tmp_path,
            runtime_package_dir=runtime_package_dir,
            public_package_root=public_root,
            service_protocol_package_root=service_protocol_root,
        )


@pytest.mark.asyncio
async def test_api_provider_delta_workspace_facade_delegates_to_delta_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_api_runtime.workspace_provider.deltas import service as delta_service

    request = object()
    calls: list[object] = []

    async def _fake_materialize_delta(*, request: object) -> dict[str, object]:
        calls.append(request)
        return {"status": "delegated"}

    monkeypatch.setattr(
        delta_service,
        "materialize_delta",
        _fake_materialize_delta,
    )

    result = await api_workspace_provider.materialize_delta(request=request)

    assert result == {"status": "delegated"}
    assert calls == [request]


def test_api_provider_delta_transport_uses_code_package_delta_as_authority(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    request = _api_provider_delta_request(
        api_toml_path=api_toml_path,
        change_kind="delete",
        delta_change_kind="update",
        hint_package_relative_path="apis/misleading.aware",
        delta_relative_path="apis/demo.aware",
    )

    delta = code_package_delta_from_provider_delta_request(request=request)

    assert api_delta_unsupported_reason(request=request) is None
    assert tuple(path.relative_path for path in delta.paths) == ("apis/demo.aware",)
    assert tuple(path.kind for path in delta.paths) == (CodePackageDeltaKind.update,)


def test_api_provider_delta_semantic_analysis_indexes_authored_aware_delta(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    request = _api_provider_delta_request(api_toml_path=api_toml_path)
    request = request.model_copy(
        update={
            "code_package_delta": CodePackageDelta(
                package_name="demo-api",
                package_root=".",
                sources_root="apis",
                manifest_relative_path=api_toml_path.name,
                authority_kind="workspace_provider_delta",
                source_revision_id="semantic-analysis-module-test",
                paths=[
                    CodePackageDeltaPath(
                        relative_path="python/generated.py",
                        kind=CodePackageDeltaKind.update,
                        content_text="generated = True\n",
                        language=CodeLanguage.python,
                        is_structural=False,
                    ),
                    CodePackageDeltaPath(
                        relative_path="apis/demo.aware",
                        kind=CodePackageDeltaKind.update,
                        content_text=(tmp_path / "apis" / "demo.aware").read_text(
                            encoding="utf-8"
                        ),
                        language=CodeLanguage.aware,
                        is_structural=True,
                    ),
                ],
            )
        }
    )

    current_analysis = analyze_provider_delta_current_semantics(
        request=request,
        manifest_path=api_toml_path,
    )
    evidence = current_analysis.evidence_payload()

    assert current_analysis.diagnostic_payloads == ()
    assert current_analysis.applied_semantic_keys == (
        "api:demo",
        "api:demo/capability:read_demo",
        "api:demo/capability:read_demo/endpoint:read_demo",
    )
    assert current_analysis.analysis.change_preview.changed_source_files == (
        "apis/demo.aware",
    )
    assert evidence["status"] == "semantic_analysis_ready"
    assert evidence["current_semantic_delta_index_count"] == 3
    assert evidence["current_semantic_delta_index_keys"] == (
        "api:demo",
        "api:demo/capability:read_demo",
        "api:demo/capability:read_demo/endpoint:read_demo",
    )


def test_api_provider_delta_baseline_module_uses_workspace_baseline_ref(
    tmp_path: Path,
) -> None:
    _write_simple_api_delta_fixture(tmp_path)
    baseline_ref = {
        "source_object_instance_graph_commit_id": "source-oig-commit-id",
        "semantic_branch_id": "semantic-branch-id",
        "semantic_projection_name": "Api",
        "semantic_package_id": "api-package-id",
        "semantic_package_commit_id": "api-package-commit-id",
        "semantic_object_instance_graph_commit_id": "semantic-oig-commit-id",
        "semantic_root_kind": "api",
        "semantic_root_id": "api-root-id",
        "semantic_root_object_instance_graph_commit_id": "semantic-root-commit-id",
    }
    request = SimpleNamespace(
        baseline_ref=baseline_ref,
        previous_materialization_evidence={
            "available": True,
            "evidence_source": "workspace_semantic_package_receipt",
            "current_semantic_object_ids": {
                "api:demo": "api-object-id",
                "api:demo/capability:read_demo": "capability-object-id",
            },
        },
    )

    preflight = api_delta_baseline_hydration_preflight(request=request)

    assert api_delta_baseline_commit_refs(request=request) == {
        "baseline_source_object_instance_graph_commit_id": "source-oig-commit-id",
        "baseline_semantic_object_instance_graph_commit_id": ("semantic-oig-commit-id"),
        "baseline_semantic_root_object_instance_graph_commit_id": (
            "semantic-root-commit-id"
        ),
    }
    assert api_delta_current_semantic_object_ids(request=request) == {
        "api:demo": "api-object-id",
        "api:demo/capability:read_demo": "capability-object-id",
    }
    assert preflight["status"] == "current_head_context_available"
    assert preflight["current_head_context_sources"] == (
        "previous_materialization_evidence",
    )
    assert preflight["baseline_ref_hydrator_ready"] is True
    assert preflight["current_semantic_object_id_count"] == 2


def test_api_provider_delta_dirty_diff_compares_against_baseline_index(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    request = SimpleNamespace(
        code_package_delta=base_request.code_package_delta,
        baseline_ref={
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_projection_name": "Api",
            "semantic_package_id": "api-package-id",
            "semantic_package_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": "semantic-oig-commit-id",
            "semantic_root_kind": "api",
            "semantic_root_id": "api-root-id",
            "semantic_root_object_instance_graph_commit_id": (
                "semantic-root-commit-id"
            ),
        },
        previous_materialization_evidence={
            "available": True,
            "current_semantic_object_ids": {
                "api:demo": "api-object-id",
            },
        },
    )
    current_analysis = analyze_provider_delta_current_semantics(
        request=request,
        manifest_path=api_toml_path,
    )
    baseline_preflight = api_delta_baseline_hydration_preflight(request=request)

    dirty_diff = api_delta_semantic_dirty_diff_from_analysis(
        analysis=current_analysis.analysis,
        request=request,
        current_delta_fingerprint="sha256:current",
        baseline_hydration_preflight=baseline_preflight,
    )

    assert dirty_diff["baseline_index_compare_status"] == "baseline_index_compared"
    assert dirty_diff["dirty_entry_count"] == 3
    assert dirty_diff["dirty_operation_counts"] == {
        "api_update": 1,
        "api_capability_create": 1,
        "api_capability_endpoint_create": 1,
    }
    entries = dirty_diff["semantic_dirty_entries"]
    assert entries[0]["semantic_key"] == "api:demo"
    assert entries[0]["baseline_object_matched"] is True
    assert entries[0]["baseline_object_id"] == "api-object-id"
    assert entries[1]["baseline_compare_status"] == "baseline_object_missing"


def test_api_provider_delta_typed_operations_project_semantic_events(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    request = SimpleNamespace(
        code_package_delta=base_request.code_package_delta,
        baseline_ref={
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_projection_name": "Api",
            "semantic_package_id": "api-package-id",
            "semantic_package_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": "semantic-oig-commit-id",
            "semantic_root_kind": "api",
            "semantic_root_id": "api-root-id",
            "semantic_root_object_instance_graph_commit_id": (
                "semantic-root-commit-id"
            ),
        },
        previous_materialization_evidence={
            "available": True,
            "current_semantic_object_ids": {
                "api:demo": "api-object-id",
            },
        },
    )
    current_analysis = analyze_provider_delta_current_semantics(
        request=request,
        manifest_path=api_toml_path,
    )
    dirty_diff = api_delta_semantic_dirty_diff_from_analysis(
        analysis=current_analysis.analysis,
        request=request,
        current_delta_fingerprint="sha256:current",
        baseline_hydration_preflight=(
            api_delta_baseline_hydration_preflight(request=request)
        ),
    )

    typed_plan = api_delta_typed_operation_plan(
        analysis=current_analysis.analysis,
        semantic_dirty_diff=dirty_diff,
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
            "blocked": False,
        },
        function_call_plans=(),
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 3
    assert typed_plan["operation_family_counts"] == {"create": 2, "update": 1}
    operations = typed_plan["typed_operations"]
    assert operations[0]["provider_operation_type"] == "aware_api.api.update"
    assert operations[0]["baseline"]["object_id"] == "api-object-id"
    assert operations[0]["semantic_event_projection"]["event_key"] == (
        "aware_api.provider_delta.api.update"
    )
    assert operations[1]["api_operation"]["operation"] == "ensure_api_capability"
    assert operations[2]["api_operation"]["operation"] == (
        "ensure_api_capability_endpoint"
    )


def test_api_provider_delta_execution_preflight_allows_update_apply_upsert(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    request = SimpleNamespace(
        code_package_delta=base_request.code_package_delta,
        baseline_ref={
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_projection_name": "Api",
            "semantic_package_id": "api-package-id",
            "semantic_package_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": "semantic-oig-commit-id",
            "semantic_root_kind": "api",
            "semantic_root_id": "api-root-id",
            "semantic_root_object_instance_graph_commit_id": (
                "semantic-root-commit-id"
            ),
        },
        previous_materialization_evidence={
            "available": True,
            "current_semantic_object_ids": {
                "api:demo": "api-object-id",
            },
        },
    )
    current_analysis = analyze_provider_delta_current_semantics(
        request=request,
        manifest_path=api_toml_path,
    )
    dirty_diff = api_delta_semantic_dirty_diff_from_analysis(
        analysis=current_analysis.analysis,
        request=request,
        current_delta_fingerprint="sha256:current",
        baseline_hydration_preflight=(
            api_delta_baseline_hydration_preflight(request=request)
        ),
    )
    typed_plan = api_delta_typed_operation_plan(
        analysis=current_analysis.analysis,
        semantic_dirty_diff=dirty_diff,
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
            "blocked": False,
        },
        function_call_plans=(),
    )

    preflight = api_delta_typed_operation_execution_preflight(
        provider_delta_typed_operation_plan=typed_plan,
    )
    block = api_delta_typed_operation_execution_block(
        provider_delta_typed_operation_execution_preflight=preflight,
    )

    assert preflight["status"] == "typed_operation_execution_ready"
    assert preflight["reason"] == ("api_provider_delta_typed_operation_execution_ready")
    assert preflight["payload_complete"] is True
    assert preflight["typed_operation_count"] == 3
    assert preflight["create_operation_count"] == 2
    assert preflight["update_operation_count"] == 1
    assert preflight["typed_operation_executor_declared"] is True
    assert preflight["update_upsert_executor_support_ready"] is True
    assert preflight["operation_family_counts"] == {"create": 2, "update": 1}
    assert block is None


def test_api_provider_delta_artifact_patch_blocks_without_execution(
    tmp_path: Path,
) -> None:
    receipt = api_delta_api_client_service_protocol_patch_receipt(
        manifest_path=tmp_path / "aware.api.toml",
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        provider_delta_head_move_plan={
            "status": "head_move_plan_blocked",
            "reason": "baseline_required",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_blocked",
            "typed_operation_count": 0,
        },
        operation_execution={
            "status": "flag_required",
            "did_execute": False,
        },
        package_source_execution={
            "status": "operation_not_ready",
            "did_execute": False,
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
            },
        },
    )

    assert receipt["contract_version"] == (
        "aware.api.provider-delta-api-client-service-protocol-patch.v1"
    )
    assert receipt["status"] == "api_client_service_protocol_patch_blocked"
    assert receipt["readiness_status"] == (
        "api_client_service_protocol_patch_not_ready"
    )
    assert receipt["would_patch"] is False
    assert receipt["did_patch"] is False
    assert receipt["artifact_ownership_receipts"] == ()
    assert "operation_execution_not_applied:flag_required" in receipt["blockers"]
    assert "package_source_execution_not_applied:operation_not_ready" in (
        receipt["blockers"]
    )
    assert "head_ref_missing:semantic_head_commit_id" in receipt["blockers"]


def test_api_provider_delta_artifact_patch_applies_with_ready_runtime_delta_plan(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def _fake_renderer(**kwargs: object) -> tuple[dict[str, object], ...]:
        calls.append(dict(kwargs))
        public_receipt = {
            "producer_provider_key": "aware_api",
            "producer_key": "aware_api.product_runtime",
            "producer_kind": "api_product_build",
            "semantic_owner": "aware_api.provider",
            "output_key": "api.product_runtime_file",
            "output_kind": "file",
            "artifact_family": "api_product_runtime",
            "artifact_role": "public_package_file",
            "artifact_key": "demo-api:public_package_file:client.py",
            "package_name": "demo-api",
            "manifest_path": ".aware/api/runtime/demo-api/client.py",
            "status": "available",
            "runtime_contract_version": "aware.api.product_runtime.v1",
        }
        service_protocol_receipt = {
            "producer_provider_key": "aware_api",
            "producer_key": "aware_api.product_runtime",
            "producer_kind": "api_product_build",
            "semantic_owner": "aware_api.provider",
            "output_key": "api.product_runtime_file",
            "output_kind": "file",
            "artifact_family": "api_product_runtime",
            "artifact_role": "service_protocol_package_file",
            "artifact_key": "demo-api:service_protocol_package_file:protocol.py",
            "package_name": "demo-api",
            "manifest_path": ".aware/api/runtime/demo-api/protocol.py",
            "status": "available",
            "runtime_contract_version": "aware.api.product_runtime.v1",
        }
        return (
            public_receipt,
            service_protocol_receipt,
        )

    receipt = api_delta_api_client_service_protocol_patch_receipt(
        manifest_path=tmp_path / "aware.api.toml",
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operation_count": 3,
        },
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
            "source_delta_path_count": 1,
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        runtime_artifact_delta_plan={
            "status": "api_product_runtime_delta_plan_ready",
            "runtime_artifacts_current": True,
            "allow_runtime_artifact_refresh": True,
            "current_delta_fingerprint": "sha256:current",
            "patch_targets": ("api_client", "service_protocol"),
            "source_code_package_id": "source-code-package-id",
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_package_id": "api-package-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_head_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
        },
        materialization_event_report={
            "status": "api_materialization_event_report_ready",
            "language_delta_driver_ready": True,
            "semantic_world_change_events": (
                {
                    "generated_path_candidates": (
                        {
                            "target": "api_client",
                            "artifact_role": "public_package_file",
                            "runtime_package_relpath": (
                                "public_package/python/package/"
                                "aware_demo_api/client.py"
                            ),
                        },
                        {
                            "target": "service_protocol",
                            "artifact_role": "service_protocol_package_file",
                            "runtime_package_relpath": (
                                "service_protocol/python/package/"
                                "aware_demo_protocol/protocols.py"
                            ),
                        },
                    ),
                },
            ),
        },
        renderer=_fake_renderer,
    )

    assert receipt["status"] == "api_client_service_protocol_patch_applied"
    assert receipt["reason"] == (
        "api_provider_delta_api_client_service_protocol_patch_applied"
    )
    assert receipt["blocked"] is False
    assert receipt["would_patch"] is True
    assert receipt["did_patch"] is True
    assert receipt["artifact_ownership_receipt_count"] == 2
    assert receipt["artifact_role_counts"] == {
        "public_package_file": 1,
        "service_protocol_package_file": 1,
    }
    assert receipt["target_patch_status_counts"] == {"patched": 2}
    assert receipt["target_patch_executions"] == (
        {
            "target": "api_client",
            "status": "patched",
            "artifact_roles": ("public_package_file",),
            "artifact_ownership_receipt_count": 1,
            "generated_artifact_upserted_file_count": 0,
            "generated_artifact_deleted_file_count": 0,
            "generated_artifact_changed_file_count": 0,
            "generated_artifact_unchanged_file_count": 0,
        },
        {
            "target": "service_protocol",
            "status": "patched",
            "artifact_roles": ("service_protocol_package_file",),
            "artifact_ownership_receipt_count": 1,
            "generated_artifact_upserted_file_count": 0,
            "generated_artifact_deleted_file_count": 0,
            "generated_artifact_changed_file_count": 0,
            "generated_artifact_unchanged_file_count": 0,
        },
    )
    assert calls[0]["package_name"] == "demo-api"
    assert calls[0]["head_refs"] == receipt["head_refs"]
    assert calls[0]["patch_targets"] == ("api_client", "service_protocol")
    assert calls[0]["materialization_event_report"] == (
        receipt["materialization_event_report"]
    )
    assert receipt["materialization_event_artifact_driver_status"] == (
        "materialization_event_artifact_driver_ready"
    )
    assert receipt["materialization_event_artifact_driver"][
        "target_candidate_counts"
    ] == {
        "api_client": 1,
        "service_protocol": 1,
    }


def test_api_provider_delta_artifact_patch_allows_file_level_noop_target(
    tmp_path: Path,
) -> None:
    def _fake_renderer(
        **_: object,
    ) -> api_artifact_patch.ApiClientServiceProtocolPatchRenderResult:
        public_receipt = {
            "producer_provider_key": "aware_api",
            "producer_key": "aware_api.product_runtime",
            "producer_kind": "api_product_build",
            "semantic_owner": "aware_api.provider",
            "output_key": "api.product_runtime_file",
            "output_kind": "file",
            "artifact_family": "api_product_runtime",
            "artifact_role": "public_package_file",
            "artifact_key": "demo-api:public_package_file:client.py",
            "package_name": "demo-api",
            "manifest_path": ".aware/api/runtime/demo-api/client.py",
            "status": "available",
            "runtime_contract_version": "aware.api.product_runtime.v1",
            "generated_artifact_file_patch_change_kind": "update",
        }
        return api_artifact_patch.ApiClientServiceProtocolPatchRenderResult(
            artifact_ownership_receipts=(public_receipt,),
            generated_artifact_file_patch={
                "contract_version": ("aware.api.generated-artifact-file-patch.v1"),
                "status": "generated_artifact_file_patch_applied",
                "strategy": "before_after_digest",
                "receipt_scope": "changed_files",
                "requested_patch_targets": ("api_client", "service_protocol"),
                "changed_file_count": 1,
                "upserted_file_count": 1,
                "deleted_file_count": 0,
                "unchanged_file_count": 2,
                "target_file_patch_counts": (
                    {
                        "target": "api_client",
                        "artifact_roles": ("public_package_file",),
                        "scanned_file_count": 1,
                        "upserted_file_count": 1,
                        "deleted_file_count": 0,
                        "unchanged_file_count": 0,
                    },
                    {
                        "target": "service_protocol",
                        "artifact_roles": ("service_protocol_package_file",),
                        "scanned_file_count": 2,
                        "upserted_file_count": 0,
                        "deleted_file_count": 0,
                        "unchanged_file_count": 2,
                    },
                ),
            },
        )

    receipt = api_delta_api_client_service_protocol_patch_receipt(
        manifest_path=tmp_path / "aware.api.toml",
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operation_count": 3,
        },
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
            "source_delta_path_count": 1,
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        runtime_artifact_delta_plan={
            "status": "api_product_runtime_delta_plan_ready",
            "runtime_artifacts_current": True,
            "allow_runtime_artifact_refresh": True,
            "current_delta_fingerprint": "sha256:current",
            "patch_targets": ("api_client", "service_protocol"),
            "source_code_package_id": "source-code-package-id",
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_package_id": "api-package-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_head_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
        },
        renderer=_fake_renderer,
    )

    assert receipt["status"] == "api_client_service_protocol_patch_applied"
    assert receipt["artifact_ownership_receipt_count"] == 1
    assert receipt["generated_artifact_file_patch_status"] == (
        "generated_artifact_file_patch_applied"
    )
    assert receipt["generated_artifact_renderer_pruning_status"] == (
        "generated_artifact_renderer_pruning_applied"
    )
    assert (
        receipt["generated_artifact_renderer_pruning"]["emitted_changed_file_count"]
        == 1
    )
    assert (
        receipt["generated_artifact_renderer_pruning"]["pruned_unchanged_file_count"]
        == 2
    )
    assert receipt["target_patch_status_counts"] == {
        "no_changed_files": 1,
        "patched": 1,
    }
    assert receipt["target_patch_executions"][0]["status"] == "patched"
    assert receipt["target_patch_executions"][1]["status"] == "no_changed_files"


def test_api_provider_delta_artifact_patch_emits_language_artifact_delta_apply(
    tmp_path: Path,
) -> None:
    changed_relpath = "public_package/python/package/aware_demo_api/client.py"
    changed_path = (
        tmp_path / ".aware" / "api" / "runtime" / "demo-api" / changed_relpath
    )

    def _fake_renderer(
        **_: object,
    ) -> api_artifact_patch.ApiClientServiceProtocolPatchRenderResult:
        public_receipt = {
            "artifact_role": "public_package_file",
            "path": changed_path.as_posix(),
            "manifest_path": changed_path.relative_to(tmp_path).as_posix(),
            "status": "available",
            "digest": "current-digest",
        }
        return api_artifact_patch.ApiClientServiceProtocolPatchRenderResult(
            artifact_ownership_receipts=(public_receipt,),
            generated_artifact_file_patch={
                "contract_version": ("aware.api.generated-artifact-file-patch.v1"),
                "status": "generated_artifact_file_patch_applied",
                "strategy": "before_after_digest",
                "receipt_scope": "changed_files",
                "requested_patch_targets": ("api_client",),
                "changed_file_count": 1,
                "upserted_file_count": 1,
                "deleted_file_count": 0,
                "unchanged_file_count": 0,
                "changed_files": (
                    {
                        "target": "api_client",
                        "artifact_role": "public_package_file",
                        "path": changed_path.as_posix(),
                        "manifest_path": changed_path.relative_to(tmp_path).as_posix(),
                        "change_kind": "update",
                        "previous_digest": "previous-digest",
                        "current_digest": "current-digest",
                    },
                ),
                "deleted_files": (),
                "unchanged_files": (),
                "target_file_patch_counts": (
                    {
                        "target": "api_client",
                        "artifact_roles": ("public_package_file",),
                        "scanned_file_count": 1,
                        "upserted_file_count": 1,
                        "deleted_file_count": 0,
                        "unchanged_file_count": 0,
                    },
                ),
                "generated_path_candidate_file_scope": {
                    "status": "generated_path_candidate_file_scope_applied",
                    "source": "api_materialization_event_report",
                    "candidate_runtime_package_relpaths": (changed_relpath,),
                },
                "generated_artifact_renderer_candidate_scope": {
                    "status": "generated_artifact_renderer_candidate_scope_applied",
                    "renderer_candidate_path_count": 1,
                    "public_package_candidate_paths": ("client.py",),
                    "service_protocol_candidate_paths": (),
                },
            },
        )

    receipt = api_delta_api_client_service_protocol_patch_receipt(
        manifest_path=tmp_path / "aware.api.toml",
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operation_count": 1,
        },
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
            "source_delta_path_count": 1,
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        runtime_artifact_delta_plan={
            "status": "api_product_runtime_delta_plan_ready",
            "runtime_artifacts_current": True,
            "allow_runtime_artifact_refresh": True,
            "current_delta_fingerprint": "sha256:current",
            "patch_targets": ("api_client",),
            "source_code_package_id": "source-code-package-id",
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_package_id": "api-package-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_head_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
        },
        materialization_event_report={
            "status": "api_materialization_event_report_ready",
            "language_delta_driver_ready": True,
            "semantic_world_change_events": (
                {
                    "event_key": "aware_api.materialization.endpoint.update",
                    "semantic_key": "api:demo/capability:read/endpoint:read",
                    "verb": "update",
                    "ontology_subject_kind": "api_capability_endpoint",
                    "subject_label": "read",
                    "generated_path_candidates": (
                        {
                            "target": "api_client",
                            "artifact_role": "public_package_file",
                            "generated_path_kind": "client.py",
                            "runtime_package_relpath": changed_relpath,
                        },
                    ),
                },
            ),
        },
        renderer=_fake_renderer,
    )

    language_apply = receipt["language_artifact_delta_apply"]
    assert receipt["language_artifact_delta_apply_status"] == (
        "api_language_artifact_delta_apply_applied"
    )
    assert receipt["language_artifact_delta_apply_event_driven"] is True
    assert language_apply["event_driven"] is True
    assert language_apply["operation_count"] == 1
    assert language_apply["target_operation_counts"] == {"api_client": 1}
    operation = language_apply["operations"][0]
    assert operation["operation_family"] == "update"
    assert operation["language"] == "python"
    assert operation["event_driven"] is True
    assert operation["semantic_event_refs"][0]["semantic_key"] == (
        "api:demo/capability:read/endpoint:read"
    )


def test_api_provider_delta_artifact_patch_requires_plan_head_refs(
    tmp_path: Path,
) -> None:
    receipt = api_delta_api_client_service_protocol_patch_receipt(
        manifest_path=tmp_path / "aware.api.toml",
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operation_count": 3,
        },
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
            "source_delta_path_count": 1,
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        runtime_artifact_delta_plan={
            "status": "api_product_runtime_delta_plan_ready",
            "runtime_artifacts_current": True,
            "allow_runtime_artifact_refresh": True,
            "current_delta_fingerprint": "sha256:current",
            "patch_targets": ("api_client", "service_protocol"),
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
        },
    )

    assert receipt["status"] == "api_client_service_protocol_patch_blocked"
    assert receipt["would_patch"] is False
    assert (
        "runtime_artifact_delta_plan_ref_missing:semantic_head_commit_id"
        in receipt["blockers"]
    )
    assert (
        "runtime_artifact_delta_plan_ref_missing:semantic_branch_id"
        in receipt["blockers"]
    )


def test_api_provider_delta_artifact_patch_blocks_unsupported_target(
    tmp_path: Path,
) -> None:
    receipt = api_delta_api_client_service_protocol_patch_receipt(
        manifest_path=tmp_path / "aware.api.toml",
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operation_count": 3,
        },
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
            "source_delta_path_count": 1,
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        runtime_artifact_delta_plan={
            "status": "api_product_runtime_delta_plan_ready",
            "runtime_artifacts_current": True,
            "allow_runtime_artifact_refresh": True,
            "current_delta_fingerprint": "sha256:current",
            "patch_targets": ("api_client", "unknown_product"),
            "source_code_package_id": "source-code-package-id",
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_package_id": "api-package-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_head_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
        },
    )

    assert receipt["status"] == "api_client_service_protocol_patch_blocked"
    assert "patch_target_unsupported:unknown_product" in receipt["blockers"]
    assert receipt["patch_targets"] == ("api_client", "unknown_product")
    assert receipt["target_patch_status_counts"] == {"not_patched": 2}


def test_api_provider_delta_artifact_patch_requires_event_driver_targets(
    tmp_path: Path,
) -> None:
    receipt = api_delta_api_client_service_protocol_patch_receipt(
        manifest_path=tmp_path / "aware.api.toml",
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operation_count": 3,
        },
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
            "source_delta_path_count": 1,
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        runtime_artifact_delta_plan={
            "status": "api_product_runtime_delta_plan_ready",
            "runtime_artifacts_current": True,
            "allow_runtime_artifact_refresh": True,
            "current_delta_fingerprint": "sha256:current",
            "patch_targets": ("api_client", "service_protocol"),
            "source_code_package_id": "source-code-package-id",
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_package_id": "api-package-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_head_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
        },
        materialization_event_report={
            "status": "api_materialization_event_report_ready",
            "language_delta_driver_ready": True,
            "semantic_world_change_events": (
                {
                    "generated_path_candidates": (
                        {
                            "target": "api_client",
                            "artifact_role": "public_package_file",
                            "runtime_package_relpath": (
                                "public_package/python/package/"
                                "aware_demo_api/client.py"
                            ),
                        },
                    ),
                },
            ),
        },
    )

    assert receipt["status"] == "api_client_service_protocol_patch_blocked"
    assert receipt["reason"] == (
        "api_provider_delta_api_client_service_protocol_patch_requires_materialization_events"
    )
    assert "materialization_event_target_missing:service_protocol" in (
        receipt["blockers"]
    )
    assert receipt["materialization_event_artifact_driver_status"] == (
        "materialization_event_artifact_driver_blocked"
    )
    assert receipt["would_patch"] is False


def test_api_provider_delta_default_renderer_honors_api_client_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    public_root = runtime_package_dir / "public_package" / "python" / "package"
    changed_path = public_root / "aware_demo_api" / "client.py"
    unchanged_path = public_root / "aware_demo_api" / "__init__.py"
    _write(changed_path, "old client\n")
    _write(unchanged_path, "unchanged\n")
    refresh_calls: list[dict[str, object]] = []

    def _fake_refresh(**kwargs: object) -> SimpleNamespace:
        refresh_calls.append(dict(kwargs))
        _write(changed_path, "new client\n")
        return SimpleNamespace(
            snapshot=SimpleNamespace(repo_root=tmp_path),
            public_package_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
            ),
            service_protocol_materialization=None,
        )

    def _fake_receipts(**_: object) -> tuple[dict[str, object], ...]:
        return (
            {
                "artifact_role": "public_package_file",
                "path": changed_path.as_posix(),
                "manifest_path": changed_path.relative_to(tmp_path).as_posix(),
            },
            {
                "artifact_role": "public_package_file",
                "path": unchanged_path.as_posix(),
                "manifest_path": unchanged_path.relative_to(tmp_path).as_posix(),
            },
            {
                "artifact_role": "service_protocol_package_file",
                "manifest_path": "protocol.py",
            },
            {
                "artifact_role": "runtime_file",
                "manifest_path": "api.compile_plan.json",
            },
        )

    monkeypatch.setattr(
        "aware_api_runtime.compile.refresh_api_workspace_from_runtime_artifacts",
        _fake_refresh,
    )
    monkeypatch.setattr(
        "aware_api_runtime.build.api_product_runtime_artifact_ownership_receipts",
        _fake_receipts,
    )

    render_result = (
        api_artifact_patch._render_api_client_service_protocol_patch(  # noqa: SLF001
            manifest_path=tmp_path / "aware.api.toml",
            workspace_root=tmp_path,
            package_name="demo-api",
            head_refs={
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
            },
            runtime_artifact_delta_plan={},
            patch_targets=("api_client",),
        )
    )
    receipts = render_result.artifact_ownership_receipts

    assert refresh_calls == [
        {
            "toml_path": tmp_path / "aware.api.toml",
            "repo_root": tmp_path,
            "refresh_public_package": True,
            "refresh_service_protocol": False,
            "public_package_candidate_paths": (),
            "service_protocol_candidate_paths": (),
            "public_package_render_input_class_refs": None,
        }
    ]
    assert tuple(receipt["artifact_role"] for receipt in receipts) == (
        "public_package_file",
    )
    assert tuple(receipt["manifest_path"] for receipt in receipts) == (
        changed_path.relative_to(tmp_path).as_posix(),
    )
    file_patch = render_result.generated_artifact_file_patch
    assert file_patch is not None
    assert file_patch["status"] == "generated_artifact_file_patch_applied"
    assert file_patch["changed_file_count"] == 1
    assert file_patch["upserted_file_count"] == 1
    assert file_patch["unchanged_file_count"] == 1


def test_api_provider_delta_default_renderer_consumes_generated_path_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    changed_relpath = "public_package/python/package/aware_demo_api/client.py"
    unchanged_relpath = "public_package/python/package/aware_demo_api/__init__.py"
    changed_path = runtime_package_dir / changed_relpath
    unchanged_path = runtime_package_dir / unchanged_relpath
    _write(changed_path, "old client\n")
    _write(unchanged_path, "unchanged\n")
    refresh_calls: list[dict[str, object]] = []

    def _fake_refresh(**kwargs: object) -> SimpleNamespace:
        refresh_calls.append(dict(kwargs))
        _write(changed_path, "new client\n")
        return SimpleNamespace(
            snapshot=SimpleNamespace(repo_root=tmp_path),
            public_package_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
            ),
            service_protocol_materialization=None,
        )

    def _fake_receipts(**_: object) -> tuple[dict[str, object], ...]:
        return (
            {
                "artifact_role": "public_package_file",
                "path": changed_path.as_posix(),
                "manifest_path": changed_path.relative_to(tmp_path).as_posix(),
            },
            {
                "artifact_role": "public_package_file",
                "path": unchanged_path.as_posix(),
                "manifest_path": unchanged_path.relative_to(tmp_path).as_posix(),
            },
        )

    monkeypatch.setattr(
        "aware_api_runtime.compile.refresh_api_workspace_from_runtime_artifacts",
        _fake_refresh,
    )
    monkeypatch.setattr(
        "aware_api_runtime.build.api_product_runtime_artifact_ownership_receipts",
        _fake_receipts,
    )

    render_result = (
        api_artifact_patch._render_api_client_service_protocol_patch(  # noqa: SLF001
            manifest_path=tmp_path / "aware.api.toml",
            workspace_root=tmp_path,
            package_name="demo-api",
            head_refs={
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
            },
            runtime_artifact_delta_plan={
                "generated_path_candidate_plan": {
                    "status": "generated_path_candidate_plan_ready",
                    "candidate_filter_ready": True,
                    "candidates": (
                        {
                            "target": "api_client",
                            "artifact_role": "public_package_file",
                            "runtime_package_relpath": changed_relpath,
                        },
                    ),
                },
            },
            patch_targets=("api_client",),
        )
    )

    receipts = render_result.artifact_ownership_receipts
    assert refresh_calls == [
        {
            "toml_path": tmp_path / "aware.api.toml",
            "repo_root": tmp_path,
            "refresh_public_package": True,
            "refresh_service_protocol": False,
            "public_package_candidate_paths": (Path("client.py"),),
            "service_protocol_candidate_paths": (),
            "public_package_render_input_class_refs": None,
        }
    ]
    assert tuple(receipt["manifest_path"] for receipt in receipts) == (
        changed_path.relative_to(tmp_path).as_posix(),
    )
    file_patch = render_result.generated_artifact_file_patch
    assert file_patch is not None
    assert file_patch["changed_file_count"] == 1
    assert file_patch["unchanged_file_count"] == 0
    assert file_patch["target_file_patch_counts"] == (
        {
            "target": "api_client",
            "artifact_roles": ("public_package_file",),
            "scanned_file_count": 1,
            "upserted_file_count": 1,
            "deleted_file_count": 0,
            "unchanged_file_count": 0,
        },
    )
    assert file_patch["generated_path_candidate_file_scope_status"] == (
        "generated_path_candidate_file_scope_applied"
    )
    candidate_scope = file_patch["generated_path_candidate_file_scope"]
    assert candidate_scope["filter_applied"] is True
    assert candidate_scope["candidate_runtime_package_relpaths"] == (changed_relpath,)
    renderer_candidate_scope = file_patch["generated_artifact_renderer_candidate_scope"]
    assert renderer_candidate_scope["status"] == (
        "generated_artifact_renderer_candidate_scope_applied"
    )
    assert renderer_candidate_scope["public_package_candidate_paths"] == ("client.py",)
    assert renderer_candidate_scope["renderer_candidate_path_count"] == 1
    assert renderer_candidate_scope["full_target_file_count"] == 2
    assert (
        renderer_candidate_scope["estimated_renderer_file_invocation_pruned_count"] == 1
    )


def test_api_provider_delta_default_renderer_prefers_fragment_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    fragment_relpath = "public_package/python/package/aware_demo_api/client.py"
    event_relpath = "public_package/python/package/aware_demo_api/__init__.py"
    fragment_path = runtime_package_dir / fragment_relpath
    event_path = runtime_package_dir / event_relpath
    _write(fragment_path, "old client\n")
    _write(event_path, "unchanged\n")
    refresh_calls: list[dict[str, object]] = []

    def _fake_refresh(**kwargs: object) -> SimpleNamespace:
        refresh_calls.append(dict(kwargs))
        _write(fragment_path, "new client\n")
        return SimpleNamespace(
            snapshot=SimpleNamespace(repo_root=tmp_path),
            public_package_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
            ),
            service_protocol_materialization=None,
        )

    def _fake_receipts(**_: object) -> tuple[dict[str, object], ...]:
        return (
            {
                "artifact_role": "public_package_file",
                "path": fragment_path.as_posix(),
                "manifest_path": fragment_path.relative_to(tmp_path).as_posix(),
            },
            {
                "artifact_role": "public_package_file",
                "path": event_path.as_posix(),
                "manifest_path": event_path.relative_to(tmp_path).as_posix(),
            },
        )

    monkeypatch.setattr(
        "aware_api_runtime.compile.refresh_api_workspace_from_runtime_artifacts",
        _fake_refresh,
    )
    monkeypatch.setattr(
        "aware_api_runtime.build.api_product_runtime_artifact_ownership_receipts",
        _fake_receipts,
    )

    render_result = (
        api_artifact_patch._render_api_client_service_protocol_patch(  # noqa: SLF001
            manifest_path=tmp_path / "aware.api.toml",
            workspace_root=tmp_path,
            package_name="demo-api",
            head_refs={
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
            },
            runtime_artifact_delta_plan={
                "runtime_artifact_fragment_plan": {
                    "status": "api_runtime_artifact_fragment_plan_ready",
                    "fragment_ready": True,
                    "fragment_operation_count": 1,
                    "fragment_operations": (
                        {
                            "fragment_ready": True,
                            "generated_path_candidates": (
                                {
                                    "target": "api_client",
                                    "artifact_role": "public_package_file",
                                    "runtime_package_relpath": fragment_relpath,
                                },
                            ),
                        },
                    ),
                },
            },
            materialization_event_report={
                "status": "api_materialization_event_report_ready",
                "language_delta_driver_ready": True,
                "semantic_world_change_events": (
                    {
                        "generated_path_candidates": (
                            {
                                "target": "api_client",
                                "artifact_role": "public_package_file",
                                "runtime_package_relpath": event_relpath,
                            },
                        ),
                    },
                ),
            },
            patch_targets=("api_client",),
        )
    )

    assert refresh_calls == [
        {
            "toml_path": tmp_path / "aware.api.toml",
            "repo_root": tmp_path,
            "refresh_public_package": True,
            "refresh_service_protocol": False,
            "public_package_candidate_paths": (Path("client.py"),),
            "service_protocol_candidate_paths": (),
            "public_package_render_input_class_refs": (),
        }
    ]
    file_patch = render_result.generated_artifact_file_patch
    assert file_patch is not None
    candidate_scope = file_patch["generated_path_candidate_file_scope"]
    assert candidate_scope["source"] == "api_runtime_artifact_fragment_plan"
    assert candidate_scope["candidate_runtime_package_relpaths"] == (fragment_relpath,)
    fragment_execution = file_patch["generated_artifact_renderer_fragment_execution"]
    assert fragment_execution["status"] == ("api_renderer_fragment_execution_applied")
    assert fragment_execution["selected_file_scope_source"] == (
        "api_runtime_artifact_fragment_plan"
    )
    assert fragment_execution["renderer_candidate_path_count"] == 1
    render_input_pruning = file_patch["generated_artifact_render_input_pruning"]
    assert render_input_pruning["status"] == "api_render_input_pruning_applied"
    assert render_input_pruning["public_package_input_strategy"] == (
        "fragment_global_renderer_empty_graph"
    )
    assert render_input_pruning["public_package_graph_input_pruned"] is True
    assert render_input_pruning["public_package_render_input_class_refs"] == ()


def test_api_provider_delta_default_renderer_passes_fragment_class_refs_to_render_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    model_relpath = "public_package/python/package/aware_demo_api/models/lock_door.py"
    model_path = runtime_package_dir / model_relpath
    _write(model_path, "old model\n")
    refresh_calls: list[dict[str, object]] = []

    def _fake_refresh(**kwargs: object) -> SimpleNamespace:
        refresh_calls.append(dict(kwargs))
        _write(model_path, "new model\n")
        return SimpleNamespace(
            snapshot=SimpleNamespace(repo_root=tmp_path),
            public_package_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
                dto_graph=SimpleNamespace(
                    object_config_graph_nodes=(object(), object()),
                    hash="sha256:pruned-public-graph",
                ),
            ),
            service_protocol_materialization=None,
        )

    def _fake_receipts(**_: object) -> tuple[dict[str, object], ...]:
        return (
            {
                "artifact_role": "public_package_file",
                "path": model_path.as_posix(),
                "manifest_path": model_path.relative_to(tmp_path).as_posix(),
            },
        )

    monkeypatch.setattr(
        "aware_api_runtime.compile.refresh_api_workspace_from_runtime_artifacts",
        _fake_refresh,
    )
    monkeypatch.setattr(
        "aware_api_runtime.build.api_product_runtime_artifact_ownership_receipts",
        _fake_receipts,
    )

    render_result = (
        api_artifact_patch._render_api_client_service_protocol_patch(  # noqa: SLF001
            manifest_path=tmp_path / "aware.api.toml",
            workspace_root=tmp_path,
            package_name="demo-api",
            head_refs={
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
            },
            runtime_artifact_delta_plan={
                "runtime_artifact_fragment_plan": {
                    "status": "api_runtime_artifact_fragment_plan_ready",
                    "fragment_ready": True,
                    "fragment_operation_count": 1,
                    "fragment_operations": (
                        {
                            "fragment_ready": True,
                            "generated_path_candidates": (
                                {
                                    "target": "api_client",
                                    "artifact_role": "public_package_file",
                                    "runtime_package_relpath": model_relpath,
                                    "class_ref": "aware_demo_api.LockDoor",
                                },
                            ),
                        },
                    ),
                },
            },
            patch_targets=("api_client",),
        )
    )

    assert refresh_calls == [
        {
            "toml_path": tmp_path / "aware.api.toml",
            "repo_root": tmp_path,
            "refresh_public_package": True,
            "refresh_service_protocol": False,
            "public_package_candidate_paths": (Path("models/lock_door.py"),),
            "service_protocol_candidate_paths": (),
            "public_package_render_input_class_refs": ("aware_demo_api.LockDoor",),
        }
    ]
    file_patch = render_result.generated_artifact_file_patch
    assert file_patch is not None
    candidate_scope = file_patch["generated_path_candidate_file_scope"]
    assert candidate_scope["candidate_class_refs"] == ("aware_demo_api.LockDoor",)
    render_input_pruning = file_patch["generated_artifact_render_input_pruning"]
    assert render_input_pruning["status"] == "api_render_input_pruning_applied"
    assert render_input_pruning["public_package_input_strategy"] == (
        "fragment_class_ref_subset"
    )
    assert render_input_pruning["public_package_graph_input_pruned"] is True
    assert render_input_pruning["public_package_render_input_class_refs"] == (
        "aware_demo_api.LockDoor",
    )
    assert render_input_pruning["actual_public_package_graph_node_count"] == 2


def test_api_provider_delta_default_renderer_carries_service_protocol_sections(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    model_relpath = "public_package/python/package/aware_demo_api/models/lock_door.py"
    service_relpath = "service_protocol/python/package/aware_demo_protocol/protocols.py"
    model_path = runtime_package_dir / model_relpath
    service_path = runtime_package_dir / service_relpath
    _write(model_path, "old model\n")
    _write(service_path, "old protocol\n")
    refresh_calls: list[dict[str, object]] = []
    section_ref = {
        "section_ref_kind": "api_service_protocol_render_section_ref",
        "section_kind": "service_protocol_endpoint_binding",
        "section_key": (
            "api.service_protocol.endpoint_binding:demo.read_demo.read_demo"
        ),
        "semantic_key": "api:demo/capability:read_demo/endpoint:read_demo",
        "runtime_package_relpath": service_relpath,
        "api_name": "demo",
        "capability_name": "read_demo",
        "endpoint_name": "read_demo",
        "section_render_wired": True,
    }

    def _fake_refresh(**kwargs: object) -> SimpleNamespace:
        refresh_calls.append(dict(kwargs))
        _write(model_path, "new model\n")
        section_text = "NEW_PROTOCOL = True"
        service_protocol_section_manifest = {
            "contract_version": (
                api_artifact_patch.API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION
            ),
            "manifest_kind": "api_service_protocol_section_text_manifest",
            "renderer_key": "PythonApiServiceProtocolRendererLanguage",
            "target_relpath": "protocols.py",
            "text_digest_algorithm": "sha256",
            "section_count": 1,
            "sections": [
                {
                    "section_order": 0,
                    "section_key": section_ref["section_key"],
                    "section_kind": section_ref["section_kind"],
                    "line_count": 1,
                    "rendered_text_digest": (
                        "sha256:" + sha256(section_text.encode("utf-8")).hexdigest()
                    ),
                }
            ],
        }
        _write(
            service_path,
            "\n".join(
                [
                    section_text,
                    (
                        api_artifact_patch.API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME
                        + " = "
                        + json.dumps(
                            json.dumps(
                                service_protocol_section_manifest,
                                sort_keys=True,
                            )
                        )
                    ),
                    "",
                ]
            ),
        )
        return SimpleNamespace(
            snapshot=SimpleNamespace(repo_root=tmp_path),
            public_package_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
                dto_graph=SimpleNamespace(
                    object_config_graph_nodes=(object(), object()),
                    hash="sha256:pruned-public-graph",
                ),
            ),
            service_protocol_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
            ),
        )

    def _fake_receipts(**_: object) -> tuple[dict[str, object], ...]:
        return (
            {
                "artifact_role": "public_package_file",
                "path": model_path.as_posix(),
                "manifest_path": model_path.relative_to(tmp_path).as_posix(),
            },
            {
                "artifact_role": "service_protocol_package_file",
                "path": service_path.as_posix(),
                "manifest_path": service_path.relative_to(tmp_path).as_posix(),
            },
        )

    monkeypatch.setattr(
        "aware_api_runtime.compile.refresh_api_workspace_from_runtime_artifacts",
        _fake_refresh,
    )
    monkeypatch.setattr(
        "aware_api_runtime.build.api_product_runtime_artifact_ownership_receipts",
        _fake_receipts,
    )

    render_result = (
        api_artifact_patch._render_api_client_service_protocol_patch(  # noqa: SLF001
            manifest_path=tmp_path / "aware.api.toml",
            workspace_root=tmp_path,
            package_name="demo-api",
            head_refs={
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
            },
            runtime_artifact_delta_plan={
                "runtime_artifact_fragment_plan": {
                    "status": "api_runtime_artifact_fragment_plan_ready",
                    "fragment_ready": True,
                    "fragment_operation_count": 1,
                    "fragment_operations": (
                        {
                            "fragment_ready": True,
                            "generated_path_candidates": (
                                {
                                    "target": "api_client",
                                    "artifact_role": "public_package_file",
                                    "runtime_package_relpath": model_relpath,
                                    "class_ref": "aware_demo_api.LockDoor",
                                },
                                {
                                    "target": "service_protocol",
                                    "artifact_role": ("service_protocol_package_file"),
                                    "runtime_package_relpath": service_relpath,
                                    "render_section_refs": (section_ref,),
                                },
                            ),
                        },
                    ),
                },
            },
            patch_targets=("api_client", "service_protocol"),
        )
    )

    assert refresh_calls == [
        {
            "toml_path": tmp_path / "aware.api.toml",
            "repo_root": tmp_path,
            "refresh_public_package": False,
            "refresh_service_protocol": True,
            "public_package_candidate_paths": (Path("models/lock_door.py"),),
            "service_protocol_candidate_paths": (Path("protocols.py"),),
            "public_package_render_input_class_refs": ("aware_demo_api.LockDoor",),
        }
    ]
    file_patch = render_result.generated_artifact_file_patch
    assert file_patch is not None
    candidate_scope = file_patch["generated_path_candidate_file_scope"]
    assert candidate_scope["candidate_render_section_ref_count"] == 1
    assert candidate_scope["target_candidate_render_section_ref_counts"] == {
        "service_protocol": 1,
    }
    renderer_scope = file_patch["generated_artifact_renderer_candidate_scope"]
    assert renderer_scope["service_protocol_render_section_ref_count"] == 1
    render_input_pruning = file_patch["generated_artifact_render_input_pruning"]
    assert (
        render_input_pruning["status"] == "api_render_input_pruning_partially_applied"
    )
    assert render_input_pruning["public_package_graph_input_pruned"] is True
    assert render_input_pruning["service_protocol_full_input_required"] is True
    assert render_input_pruning["service_protocol_section_plan_status"] == (
        "api_service_protocol_render_section_plan_ready"
    )
    assert render_input_pruning["service_protocol_section_input_strategy"] == (
        "declarative_sections_ready_renderer_full_graph_required"
    )
    assert render_input_pruning["service_protocol_render_section_refs"] == (
        section_ref,
    )
    assert (
        render_input_pruning["service_protocol_section_render_execution_wired"] is True
    )
    assert render_input_pruning["service_protocol_section_patch_wired"] is False
    section_execution = file_patch["service_protocol_section_render_execution"]
    assert file_patch["service_protocol_section_render_execution_status"] == (
        "api_service_protocol_section_render_execution_applied"
    )
    assert section_execution["available"] is True
    assert section_execution["section_operation_count"] == 1
    assert section_execution["changed_section_operation_count"] == 1
    assert section_execution["noop_section_operation_count"] == 0
    assert section_execution["rendered_text_digest_available"] is True
    assert section_execution["section_patch_wired"] is False
    assert section_execution["filesystem_apply_wired"] is False
    section_operation = section_execution["section_operations"][0]
    assert section_operation["operation_family"] == "update"
    assert section_operation["section_key"] == section_ref["section_key"]
    assert section_operation["section_payload_digest"].startswith("sha256:")
    assert section_operation["rendered_text_digest_available"] is True
    assert section_operation["rendered_text_digest"] is not None
    assert section_operation["rendered_text_line_count"] == 1
    section_apply = file_patch["service_protocol_section_apply"]
    assert file_patch["service_protocol_section_apply_status"] == (
        "api_service_protocol_section_apply_applied"
    )
    assert section_apply["section_render_execution_status"] == (
        "api_service_protocol_section_render_execution_applied"
    )
    assert section_apply["section_operation_count"] == 1
    assert section_apply["strategy"] == (
        "local_full_file_refresh_with_section_ref_resolution"
    )
    assert section_apply["available"] is True
    assert section_apply["section_patch_wired"] is False
    assert section_apply["shared_filesystem_delta_apply_wired"] is False
    assert section_apply["render_section_ref_count"] == 1
    changed_service_files = tuple(
        item
        for item in file_patch["changed_files"]
        if item["target"] == "service_protocol"
    )
    assert changed_service_files[0]["service_protocol_render_section_refs"] == (
        section_ref,
    )


def test_api_provider_delta_default_renderer_consumes_materialization_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    changed_relpath = "public_package/python/package/aware_demo_api/client.py"
    unchanged_relpath = "public_package/python/package/aware_demo_api/__init__.py"
    changed_path = runtime_package_dir / changed_relpath
    unchanged_path = runtime_package_dir / unchanged_relpath
    _write(changed_path, "old client\n")
    _write(unchanged_path, "unchanged\n")
    refresh_calls: list[dict[str, object]] = []

    def _fake_refresh(**kwargs: object) -> SimpleNamespace:
        refresh_calls.append(dict(kwargs))
        _write(changed_path, "new client\n")
        return SimpleNamespace(
            snapshot=SimpleNamespace(repo_root=tmp_path),
            public_package_materialization=SimpleNamespace(
                runtime_package_dir=runtime_package_dir,
            ),
            service_protocol_materialization=None,
        )

    def _fake_receipts(**_: object) -> tuple[dict[str, object], ...]:
        return (
            {
                "artifact_role": "public_package_file",
                "path": changed_path.as_posix(),
                "manifest_path": changed_path.relative_to(tmp_path).as_posix(),
            },
            {
                "artifact_role": "public_package_file",
                "path": unchanged_path.as_posix(),
                "manifest_path": unchanged_path.relative_to(tmp_path).as_posix(),
            },
        )

    monkeypatch.setattr(
        "aware_api_runtime.compile.refresh_api_workspace_from_runtime_artifacts",
        _fake_refresh,
    )
    monkeypatch.setattr(
        "aware_api_runtime.build.api_product_runtime_artifact_ownership_receipts",
        _fake_receipts,
    )

    render_result = (
        api_artifact_patch._render_api_client_service_protocol_patch(  # noqa: SLF001
            manifest_path=tmp_path / "aware.api.toml",
            workspace_root=tmp_path,
            package_name="demo-api",
            head_refs={
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
            },
            runtime_artifact_delta_plan={},
            materialization_event_report={
                "status": "api_materialization_event_report_ready",
                "language_delta_driver_ready": True,
                "semantic_world_change_events": (
                    {
                        "generated_path_candidates": (
                            {
                                "target": "api_client",
                                "artifact_role": "public_package_file",
                                "runtime_package_relpath": changed_relpath,
                            },
                        ),
                    },
                ),
            },
            patch_targets=("api_client",),
        )
    )

    receipts = render_result.artifact_ownership_receipts
    assert refresh_calls == [
        {
            "toml_path": tmp_path / "aware.api.toml",
            "repo_root": tmp_path,
            "refresh_public_package": True,
            "refresh_service_protocol": False,
            "public_package_candidate_paths": (Path("client.py"),),
            "service_protocol_candidate_paths": (),
            "public_package_render_input_class_refs": None,
        }
    ]
    assert tuple(receipt["manifest_path"] for receipt in receipts) == (
        changed_path.relative_to(tmp_path).as_posix(),
    )
    file_patch = render_result.generated_artifact_file_patch
    assert file_patch is not None
    assert file_patch["changed_file_count"] == 1
    assert file_patch["unchanged_file_count"] == 0
    candidate_scope = file_patch["generated_path_candidate_file_scope"]
    assert candidate_scope["status"] == "generated_path_candidate_file_scope_applied"
    assert candidate_scope["source"] == "api_materialization_event_report"
    assert candidate_scope["candidate_runtime_package_relpaths"] == (changed_relpath,)


def _ready_demo_api_typed_operation_plan() -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "typed_operation_count": 3,
        "typed_operations": (
            {
                "semantic_key": "api:demo",
                "operation_family": "update",
                "ontology_subject_kind": "api",
                "provider_operation_type": "aware_api.api.update",
            },
            {
                "semantic_key": "api:demo/capability:read_demo",
                "operation_family": "create",
                "ontology_subject_kind": "api_capability",
                "provider_operation_type": "aware_api.api_capability.create",
            },
            {
                "semantic_key": ("api:demo/capability:read_demo/endpoint:read_demo"),
                "operation_family": "create",
                "ontology_subject_kind": "api_capability_endpoint",
                "provider_operation_type": ("aware_api.api_capability_endpoint.create"),
            },
        ),
    }


def test_api_product_runtime_delta_plan_accepts_emitted_runtime_artifact_evidence(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    request = _api_provider_delta_request(api_toml_path=api_toml_path)
    current_analysis = analyze_provider_delta_current_semantics(
        request=request,
        manifest_path=api_toml_path,
    )
    dirty_diff = api_delta_semantic_dirty_diff_from_analysis(
        analysis=current_analysis.analysis,
        request=request,
        current_delta_fingerprint="sha256:current",
        baseline_hydration_preflight=(
            api_delta_baseline_hydration_preflight(request=request)
        ),
    )
    typed_plan = _ready_demo_api_typed_operation_plan()
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"
    emitter_calls: list[dict[str, object]] = []

    def _fake_emitter(**kwargs: object) -> dict[str, object]:
        emitter_calls.append(dict(kwargs))
        return {
            "runtime_package_dir": runtime_package_dir.as_posix(),
            "runtime_compile_plan_hash": "runtime-plan-hash",
            "accessible_dependency_graph_count": 1,
            "emitted_runtime_artifacts": (
                {
                    "kind": "api.compile_plan",
                    "relpath": ".aware/api/runtime/demo-api/api.compile_plan.json",
                    "hash_sha256": "runtime-plan-hash",
                },
            ),
        }

    plan = api_product_runtime_delta_plan(
        manifest_path=api_toml_path,
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        snapshot=current_analysis.snapshot,
        analysis=current_analysis.analysis,
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan=typed_plan,
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        workspace_root=tmp_path,
        runtime_artifact_emitter=_fake_emitter,
        semantic_dirty_diff=dirty_diff,
    )

    assert plan["status"] == "api_product_runtime_delta_plan_ready"
    assert plan["runtime_artifacts_current"] is True
    assert plan["allow_runtime_artifact_refresh"] is True
    assert plan["did_update_runtime_artifacts"] is True
    assert plan["emitted_runtime_artifact_count"] == 1
    assert plan["runtime_package_dir"] == runtime_package_dir.as_posix()
    assert plan["runtime_compile_plan_hash"] == "runtime-plan-hash"
    assert plan["source_code_package_id"] == "source-code-package-id"
    assert plan["semantic_head_commit_id"] == "api-package-commit-id"
    assert emitter_calls[0]["package_name"] == "demo-api"
    assert emitter_calls[0]["analysis"] is current_analysis.analysis
    candidate_plan = plan["generated_path_candidate_plan"]
    assert candidate_plan["status"] == "generated_path_candidate_plan_ready"
    assert plan["generated_path_candidate_plan_status"] == (
        "generated_path_candidate_plan_ready"
    )
    assert plan["generated_path_candidate_filter_ready"] is True
    fragment_plan = plan["runtime_artifact_fragment_plan"]
    assert plan["runtime_artifact_fragment_plan_status"] == (
        "api_runtime_artifact_fragment_plan_ready"
    )
    assert plan["runtime_artifact_fragment_ready"] is True
    assert fragment_plan["fragment_operation_count"] == 3
    assert fragment_plan["blocked_fragment_operation_count"] == 0
    assert fragment_plan["operation_family_counts"] == {
        "create": 2,
        "update": 1,
    }
    assert plan["runtime_artifact_delta_strategy"] == (
        "delta_fragment_guided_current_analysis_emit"
    )
    assert candidate_plan["target_candidate_counts"]["api_client"] >= 1
    assert candidate_plan["target_candidate_counts"]["service_protocol"] >= 1
    candidate_relpaths = {
        item["runtime_package_relpath"] for item in candidate_plan["candidates"]
    }
    assert (
        "public_package/python/package/aware_demo_api/models/read_demo_request.py"
        in candidate_relpaths
    )
    assert (
        "service_protocol/python/package/aware_demo_protocol/protocols.py"
        in candidate_relpaths
    )
    assert {
        item["semantic_key"]
        for item in candidate_plan["candidates"]
        if item["target"] == "service_protocol"
    } >= {
        "api:demo",
        "api:demo/capability:read_demo",
        "api:demo/capability:read_demo/endpoint:read_demo",
    }
    endpoint_service_candidates = tuple(
        item
        for item in candidate_plan["candidates"]
        if item["target"] == "service_protocol"
        and item["semantic_key"] == ("api:demo/capability:read_demo/endpoint:read_demo")
    )
    assert len(endpoint_service_candidates) == 1
    endpoint_section_refs = endpoint_service_candidates[0]["render_section_refs"]
    assert {ref["section_kind"] for ref in endpoint_section_refs} >= {
        "service_protocol_endpoint_binding",
        "service_protocol_endpoint_invoker",
        "service_protocol_endpoint_execution",
        "service_protocol_capability_protocol",
        "service_protocol_api_protocol",
        "service_protocol_root_protocol",
    }
    assert "api.service_protocol.root_protocol" in {
        ref["section_key"] for ref in endpoint_section_refs
    }
    assert all(ref["section_render_wired"] is True for ref in endpoint_section_refs)


def test_api_runtime_artifact_fragment_plan_survives_full_source_blocker(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    request = _api_provider_delta_request(api_toml_path=api_toml_path)
    current_analysis = analyze_provider_delta_current_semantics(
        request=request,
        manifest_path=api_toml_path,
    )
    dirty_diff = api_delta_semantic_dirty_diff_from_analysis(
        analysis=current_analysis.analysis,
        request=request,
        current_delta_fingerprint="sha256:current",
        baseline_hydration_preflight=(
            api_delta_baseline_hydration_preflight(request=request)
        ),
    )
    typed_plan = _ready_demo_api_typed_operation_plan()
    snapshot = SimpleNamespace(
        repo_root=current_analysis.snapshot.repo_root,
        package_root=current_analysis.snapshot.package_root,
        spec_path=current_analysis.snapshot.spec_path,
        spec=current_analysis.snapshot.spec,
        source_files=(
            *current_analysis.snapshot.source_files,
            Path("apis/another-file.aware"),
        ),
    )

    plan = api_product_runtime_delta_plan(
        manifest_path=api_toml_path,
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        snapshot=snapshot,
        analysis=current_analysis.analysis,
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan=typed_plan,
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        workspace_root=tmp_path,
        semantic_dirty_diff=dirty_diff,
    )

    assert plan["status"] == "api_product_runtime_delta_plan_blocked"
    assert "runtime_artifact_delta_requires_full_source_set" in plan["blockers"]
    assert plan["runtime_artifacts_current"] is False
    assert plan["runtime_artifact_fragment_plan_status"] == (
        "api_runtime_artifact_fragment_plan_ready"
    )
    assert plan["runtime_artifact_fragment_ready"] is True
    assert plan["runtime_artifact_fragment_operation_count"] == 3
    assert plan["generated_path_candidate_plan_status"] == (
        "generated_path_candidate_plan_ready"
    )


def test_api_delta_materialization_event_report_projects_language_delta_targets(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    request = SimpleNamespace(
        code_package_delta=base_request.code_package_delta,
        baseline_ref={
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_projection_name": "Api",
            "semantic_package_id": "api-package-id",
            "semantic_package_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": "semantic-oig-commit-id",
            "semantic_root_kind": "api",
            "semantic_root_id": "api-root-id",
            "semantic_root_object_instance_graph_commit_id": (
                "semantic-root-commit-id"
            ),
        },
        previous_materialization_evidence={
            "available": True,
            "current_semantic_object_ids": {
                "api:demo": "api-object-id",
            },
        },
    )
    current_analysis = analyze_provider_delta_current_semantics(
        request=request,
        manifest_path=api_toml_path,
    )
    dirty_diff = api_delta_semantic_dirty_diff_from_analysis(
        analysis=current_analysis.analysis,
        request=request,
        current_delta_fingerprint="sha256:current",
        baseline_hydration_preflight=(
            api_delta_baseline_hydration_preflight(request=request)
        ),
    )
    typed_plan = api_delta_typed_operation_plan(
        analysis=current_analysis.analysis,
        semantic_dirty_diff=dirty_diff,
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
            "blocked": False,
        },
        function_call_plans=(),
    )
    runtime_package_dir = tmp_path / ".aware" / "api" / "runtime" / "demo-api"

    def _fake_emitter(**_: object) -> dict[str, object]:
        return {
            "runtime_package_dir": runtime_package_dir.as_posix(),
            "runtime_compile_plan_hash": "runtime-plan-hash",
            "accessible_dependency_graph_count": 1,
            "emitted_runtime_artifacts": (
                {
                    "kind": "api.compile_plan",
                    "relpath": ".aware/api/runtime/demo-api/api.compile_plan.json",
                    "hash_sha256": "runtime-plan-hash",
                },
            ),
        }

    runtime_plan = api_product_runtime_delta_plan(
        manifest_path=api_toml_path,
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        snapshot=current_analysis.snapshot,
        analysis=current_analysis.analysis,
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan=typed_plan,
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        workspace_root=tmp_path,
        runtime_artifact_emitter=_fake_emitter,
        semantic_dirty_diff=dirty_diff,
    )

    report = api_delta_materialization_event_report(
        semantic_dirty_diff=dirty_diff,
        provider_delta_typed_operation_plan=typed_plan,
        runtime_artifact_delta_plan=runtime_plan,
    )

    assert report["status"] == "api_materialization_event_report_ready"
    assert report["materialization_event_count"] == 3
    assert report["semantic_world_change_event_count"] == 3
    assert report["semantic_world_change_events"] == report["materialization_events"]
    assert report["readable_semantic_event_chain"] == (
        report["readable_materialization_event_chain"]
    )
    assert report["head_refs"]["semantic_branch_id"] == "semantic-branch-id"
    assert report["current_delta_fingerprint"] == "sha256:current"
    assert report["baseline_refs"]["baseline_branch_id"] == "semantic-branch-id"
    assert report["runtime_artifact_fragment_plan_status"] == (
        "api_runtime_artifact_fragment_plan_ready"
    )
    assert report["runtime_artifact_fragment_ready"] is True
    assert report["runtime_artifact_fragment_operation_count"] == 3
    assert report["language_delta_driver_ready"] is True
    assert report["event_dispatch_wired"] is False
    assert report["artifact_target_counts"] == {
        "api_client": 3,
        "service_protocol": 3,
    }
    events = report["materialization_events"]
    assert events[0]["event_key"] == "aware_api.materialization.api.update"
    endpoint_event = events[2]
    assert endpoint_event["semantic_key"] == (
        "api:demo/capability:read_demo/endpoint:read_demo"
    )
    assert endpoint_event["artifact_targets"] == (
        "api_client",
        "service_protocol",
    )
    assert endpoint_event["head_refs"]["semantic_branch_id"] == ("semantic-branch-id")
    assert {
        candidate["runtime_package_relpath"]
        for candidate in endpoint_event["generated_path_candidates"]
    } >= {
        "public_package/python/package/aware_demo_api/models/read_demo_request.py",
        "service_protocol/python/package/aware_demo_protocol/protocols.py",
    }
    endpoint_service_candidate = next(
        candidate
        for candidate in endpoint_event["generated_path_candidates"]
        if candidate["target"] == "service_protocol"
    )
    assert endpoint_service_candidate["render_section_ref_count"] > 0
    assert {
        ref["section_kind"] for ref in endpoint_service_candidate["render_section_refs"]
    } >= {
        "service_protocol_endpoint_binding",
        "service_protocol_endpoint_invoker",
        "service_protocol_endpoint_execution",
    }


def test_api_materialization_event_report_carries_workspace_aggregate_evidence() -> (
    None
):
    report = {
        "status": "api_materialization_event_report_ready",
        "semantic_world_change_event_count": 3,
        "readable_semantic_event_chain": {
            "status": "api_materialization_event_chain_ready",
        },
    }
    enriched = api_delta_materialization_event_report_with_workspace_aggregate_evidence(
        materialization_event_report=report,
        api_client_service_protocol_delta_patch={
            "status": "api_client_service_protocol_patch_applied",
            "did_patch": True,
            "patch_targets": ("api_client", "service_protocol"),
            "materialization_event_artifact_driver": {
                "status": "materialization_event_artifact_driver_ready",
                "source": "api_materialization_event_report",
                "target_candidate_counts": {
                    "api_client": 3,
                    "service_protocol": 3,
                },
            },
            "generated_artifact_file_patch": {
                "status": "generated_artifact_file_patch_applied",
                "changed_file_count": 2,
                "upserted_file_count": 2,
                "deleted_file_count": 0,
            },
            "generated_artifact_renderer_candidate_scope": {
                "status": "generated_artifact_renderer_candidate_scope_applied",
                "renderer_candidate_path_count": 2,
            },
            "language_artifact_delta_apply": {
                "status": "api_language_artifact_delta_apply_applied",
                "event_driven": True,
                "operation_count": 2,
                "changed_operation_count": 2,
                "deleted_operation_count": 0,
                "noop_operation_count": 1,
                "target_operation_counts": {
                    "api_client": 1,
                    "service_protocol": 1,
                },
            },
        },
    )

    evidence = enriched["workspace_aggregate_provider_evidence"]
    assert enriched["durable_provider_evidence_available"] is True
    assert enriched["workspace_aggregate_provider_evidence_status"] == (
        "api_workspace_aggregate_provider_evidence_ready"
    )
    assert evidence["contract_version"] == (
        "aware.api.provider-delta-workspace-aggregate-provider-evidence.v1"
    )
    assert evidence["provider_key"] == "aware_api"
    assert evidence["api_client_service_protocol_patch_status"] == (
        "api_client_service_protocol_patch_applied"
    )
    assert evidence["materialization_event_artifact_driver_status"] == (
        "materialization_event_artifact_driver_ready"
    )
    assert evidence["artifact_driver_target_candidate_counts"] == {
        "api_client": 3,
        "service_protocol": 3,
    }
    assert evidence["language_artifact_delta_apply_status"] == (
        "api_language_artifact_delta_apply_applied"
    )
    assert evidence["language_artifact_delta_apply_event_driven"] is True
    assert evidence["language_artifact_delta_apply_operation_count"] == 2
    assert evidence["language_artifact_delta_apply_target_operation_counts"] == {
        "api_client": 1,
        "service_protocol": 1,
    }
    assert evidence["workspace_envelope_retains_provider_report_payload"] is True
    assert evidence["workspace_aggregate_consumes_provider_envelope"] is True


def test_api_product_runtime_delta_plan_uses_context_graph_render_inputs(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    request = _api_provider_delta_request(api_toml_path=api_toml_path)
    current_analysis = analyze_provider_delta_current_semantics(
        request=request,
        manifest_path=api_toml_path,
    )
    context_graph = _demo_api_render_input_context_graph()
    request_class_config = context_graph.object_config_graph_nodes[0].class_config
    response_class_config = context_graph.object_config_graph_nodes[1].class_config
    assert request_class_config is not None
    assert response_class_config is not None

    plan = api_product_runtime_delta_plan(
        manifest_path=api_toml_path,
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        snapshot=current_analysis.snapshot,
        analysis=current_analysis.analysis,
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operation_count": 3,
        },
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        workspace_root=tmp_path,
        accessible_graphs=(context_graph,),
    )

    assert plan["status"] == "api_product_runtime_delta_plan_ready"
    assert plan["accessible_dependency_graph_source"] == "semantic_context"
    assert plan["accessible_dependency_graph_count"] == 1
    assert plan["emitted_runtime_artifact_count"] == 5

    compile_plan_path = (
        tmp_path / ".aware" / "api" / "runtime" / "demo-api" / "api.compile_plan.json"
    )
    compile_plan_payload = json.loads(compile_plan_path.read_text(encoding="utf-8"))
    endpoint_payload = compile_plan_payload["api_ownership"][0]["capabilities"][0][
        "endpoints"
    ][0]
    request_payload = endpoint_payload["request_config"]
    response_payload = request_payload["response_config"]
    assert request_payload["class_config_id"] == str(request_class_config.id)
    assert "class_config_id" not in response_payload
    ontology_payload = compile_plan_payload["api_ontology"][0]
    assert ontology_payload["capability_endpoint_request_configs"][0][
        "class_config_id"
    ] == str(request_class_config.id)
    assert ontology_payload["capability_endpoint_response_configs"][0][
        "class_config_id"
    ] == str(response_class_config.id)


def test_api_product_runtime_delta_plan_blocks_partial_source_sets(
    tmp_path: Path,
) -> None:
    api_toml_path = tmp_path / "aware.api.toml"
    snapshot = SimpleNamespace(
        repo_root=tmp_path,
        source_files=(Path("apis/one.aware"), Path("apis/two.aware")),
        spec=SimpleNamespace(
            api=SimpleNamespace(package_name="demo-api", fqn_prefix="aware_demo_api"),
            dependencies=(),
        ),
    )
    analysis = SimpleNamespace(
        diagnostics=(),
        source_files=("apis/one.aware",),
        api_ownership=(object(),),
    )

    plan = api_product_runtime_delta_plan(
        manifest_path=api_toml_path,
        package_name="demo-api",
        current_delta_fingerprint="sha256:current",
        snapshot=snapshot,
        analysis=analysis,
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "reason": "ready",
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operation_count": 3,
        },
        operation_execution={
            "status": "executed",
            "did_execute": True,
        },
        package_source_execution={
            "status": "executed",
            "did_execute": True,
            "source_update_strategy": "code_package_delta",
        },
        commit_ref_payload={
            "bundle_package": {
                "source_code_package_id": "source-code-package-id",
                "source_object_instance_graph_commit_id": "source-oig-commit-id",
                "semantic_package_id": "api-package-id",
                "semantic_branch_id": "semantic-branch-id",
                "semantic_head_commit_id": "api-package-commit-id",
                "semantic_object_instance_graph_commit_id": ("api-package-commit-id"),
            },
        },
        workspace_root=tmp_path,
    )

    assert plan["status"] == "api_product_runtime_delta_plan_blocked"
    assert plan["runtime_artifacts_current"] is False
    assert "runtime_artifact_delta_requires_full_source_set" in plan["blockers"]


@pytest.mark.asyncio
async def test_api_provider_delta_executes_typed_update_apply_upsert(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    backend = _RecordingApiExecutionBackend(
        object_ids=(
            "api-object-id",
            "capability-object-id",
            "endpoint-object-id",
            "source-code-package-id",
            "source-code-package-id",
            "api-package-id",
        ),
        commit_ids=(
            "api-root-update-commit-id",
            "api-capability-create-commit-id",
            "api-endpoint-create-commit-id",
            "source-code-package-build-commit-id",
            "source-code-package-upsert-commit-id",
            "api-package-commit-id",
        ),
        branch_id="semantic-branch-id",
    )
    durable_execution_inputs = SemanticProviderDeltaDurableExecutionInputs(
        provider_key="aware_api",
        semantic_owner="aware_api.provider",
        semantic_branch_id="semantic-branch-id",
        semantic_projection_hash="api-projection-hash",
        semantic_projection_name="Api",
        author_id="author-id",
        provider_inputs={
            API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY: backend,
        },
    ).model_dump(mode="python")

    def _compile_should_not_run(**_: object) -> object:
        raise AssertionError("API provider-delta must not run full API compile")

    monkeypatch.setattr(
        api_workspace_provider,
        "_compile_api_workspace_for_product_runtime_receipts",
        _compile_should_not_run,
    )

    execution_request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        code_package_delta=base_request.code_package_delta,
        delta_cause_hints=base_request.delta_cause_hints,
        baseline_ref={
            "source_object_instance_graph_commit_id": "source-oig-commit-id",
            "semantic_branch_id": "semantic-branch-id",
            "semantic_projection_name": "Api",
            "semantic_package_id": "api-package-id",
            "semantic_package_commit_id": "api-package-commit-id",
            "semantic_object_instance_graph_commit_id": "semantic-oig-commit-id",
            "semantic_root_kind": "api",
            "semantic_root_id": "api-object-id",
            "semantic_root_object_instance_graph_commit_id": (
                "semantic-root-commit-id"
            ),
        },
        previous_materialization_evidence={
            "available": True,
            "current_semantic_object_ids": {
                "api:demo": "api-object-id",
            },
        },
        execute_provider_delta_materialization=True,
        semantic_function_call_execution_context={
            SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: (
                encode_semantic_function_call_context_by_provider(
                    {
                        "aware_api": SemanticFunctionCallContext(
                            resolved_argument_ref_object_ids={
                                "aware_demo_api.ReadDemoRequest": (
                                    "request-class-config-id"
                                ),
                            },
                        ),
                    }
                )
            ),
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY: (
                durable_execution_inputs
            ),
        },
    )

    result = await api_workspace_provider.materialize_delta(request=execution_request)

    details = result["details"]
    operation_execution = details["provider_delta_operation_execution"]
    typed_execution = operation_execution["typed_operation_execution"]
    assert result["status"] == "succeeded"
    assert details["provider_delta_typed_operation_execution_status"] == (
        "typed_operation_execution_ready"
    )
    assert operation_execution["status"] == "executed"
    assert operation_execution["reason"] == (
        "api_provider_delta_typed_operation_execution_invoked"
    )
    assert operation_execution["did_execute"] is True
    assert typed_execution["status_counts"] == {"invoked": 3}
    assert typed_execution["current_semantic_object_id_count"] == 1
    assert typed_execution["resolved_argument_ref_object_id_count"] == 1
    assert len(backend.invocations) == 6
    assert [invocation.function_ref for invocation in backend.invocations[:3]] == [
        API_CREATE_FUNCTION_REF,
        API_CREATE_CAPABILITY_FUNCTION_REF,
        API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    ]
    assert backend.invocations[0].call_target == "constructor"
    assert backend.invocations[1].receiver_object_id == "api-object-id"
    assert backend.invocations[2].receiver_object_id == "capability-object-id"
    assert backend.invocations[2].arguments["request_class_config_id"] == (
        "request-class-config-id"
    )
    package_source_execution = details[
        "provider_delta_package_source_operation_execution"
    ]
    assert package_source_execution["source_update_strategy"] == ("code_package_delta")
    assert package_source_execution["source_delta_path_count"] == 1
    assert package_source_execution["source_delta_kind_counts"] == {"update": 1}
    runtime_delta_plan = details["api_product_runtime_delta_plan"]
    assert runtime_delta_plan["status"] == "api_product_runtime_delta_plan_blocked"
    assert runtime_delta_plan["reason"] == "api_product_runtime_delta_execution_failed"
    assert runtime_delta_plan["runtime_artifacts_current"] is False
    assert (
        "runtime_artifact_delta_execution_failed:RuntimeError: "
        "api_endpoint_class_refs_require_accessible_dependency_graphs"
    ) in runtime_delta_plan["blockers"]
    delta_patch = details["api_client_service_protocol_delta_patch"]
    assert delta_patch["readiness_status"] == (
        "api_client_service_protocol_patch_ready"
    )
    assert delta_patch["status"] == "api_client_service_protocol_patch_blocked"
    assert delta_patch["reason"] == (
        "api_provider_delta_api_client_service_protocol_patch_requires_runtime_artifact_delta_plan"
    )
    assert delta_patch["would_patch"] is False
    assert delta_patch["did_patch"] is False
    assert (
        "runtime_artifact_delta_plan_not_ready:api_product_runtime_delta_plan_blocked"
        in delta_patch["blockers"]
    )
    assert "runtime_artifacts_current_false" in delta_patch["blockers"]
    assert delta_patch["artifact_ownership_receipts"] == ()
    assert details["artifact_ownership_receipts"] == ()
    assert delta_patch["head_refs"]["semantic_head_commit_id"] == (
        "api-package-commit-id"
    )
    assert backend.invocations[4].call_target == "instance"
    assert backend.invocations[4].receiver_object_id == "source-code-package-id"
    assert "CodePackage.apply_delta" in backend.invocations[4].function_ref
    source_delta = backend.invocations[4].arguments["delta"]
    assert source_delta["paths"] == [
        {
            "relative_path": "apis/demo.aware",
            "kind": "update",
            "content_text": (api_toml_path.parent / "apis" / "demo.aware").read_text(
                encoding="utf-8"
            ),
            "content_plan": None,
            "before_hash": None,
            "after_hash": None,
            "size_bytes": None,
            "language": "aware",
            "is_structural": True,
            "path_role": "authored_source",
            "production": None,
        }
    ]


@pytest.mark.asyncio
async def test_api_provider_delta_result_falls_back_for_delete_delta(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    request = _api_provider_delta_request(
        api_toml_path=api_toml_path,
        change_kind="delete",
    )

    result = await api_workspace_provider.materialize_delta(request=request)

    assert result["status"] == "fallback_required"
    assert result["fallback_reason"] == "api_delta_delete_requires_full_rebuild"
    assert result["package"] == request.package.model_dump(mode="json")
    assert result["semantic_contract"] == request.semantic_contract.model_dump(
        mode="json"
    )
    assert result["current_delta_fingerprint"] == "sha256:current"
    assert result["commit_ref_contract"]["status"] == (
        "not_applicable_fallback_required"
    )
    assert result["commit_ref_contract"]["receipt_persistence_contract_ready"] is False
    assert result["bundle_package"]["source_code_package_id"] == (
        "source-code-package-id"
    )
    assert result["bundle_package"]["commit_ref_contract_status"] == (
        "not_applicable_fallback_required"
    )
    assert result["details"]["production_execution_wired"] is False


@pytest.mark.asyncio
async def test_api_provider_delta_requires_transported_code_package_delta(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    request = _api_provider_delta_request(
        api_toml_path=api_toml_path,
        include_code_package_delta=False,
    )

    result = await api_workspace_provider.materialize_delta(request=request)

    assert result["status"] == "fallback_required"
    assert result["fallback_reason"] == "api_delta_code_package_delta_required"
    assert result["details"]["delta_cause_hints"]["top_changed_paths"] == (
        {
            "path": "apis/demo.aware",
            "change_kind": "update",
            "classification": "source_owned",
            "package_relative_path": "apis/demo.aware",
            "language": "aware",
            "is_structural": True,
            "path_role": None,
        },
    )


@pytest.mark.asyncio
async def test_api_provider_delta_uses_code_package_delta_over_path_hints(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    request = _api_provider_delta_request(
        api_toml_path=api_toml_path,
        change_kind="delete",
        delta_change_kind="update",
        hint_package_relative_path="apis/misleading.aware",
        delta_relative_path="apis/demo.aware",
    )

    result = await api_workspace_provider.materialize_delta(request=request)

    operation_plan = result["details"]["delta_operation_plan"]
    assert result["status"] == "succeeded"
    assert result["applied_semantic_keys"] == (
        "api:demo",
        "api:demo/capability:read_demo",
        "api:demo/capability:read_demo/endpoint:read_demo",
    )
    assert operation_plan["changed_source_files"] == ("apis/demo.aware",)
    assert operation_plan["affected_api_names"] == ("demo",)
    assert result["details"]["api_current_semantic_analysis"]["status"] == (
        "semantic_analysis_ready"
    )
    assert (
        result["details"]["api_current_semantic_analysis"][
            "current_semantic_delta_index_count"
        ]
        == 3
    )
    assert result["details"]["api_semantic_dirty_diff"]["status"] == (
        "semantic_dirty_diff_ready"
    )
    assert result["details"]["api_semantic_dirty_diff"]["dirty_entry_count"] == 3
    assert result["details"]["semantic_dirty_diff"] == (
        result["details"]["api_semantic_dirty_diff"]
    )
    assert result["details"]["provider_delta_semantic_dirty_event_report"] == (
        result["details"]["api_materialization_event_report"]
    )
    aggregate_evidence = result["details"]["api_materialization_event_report"][
        "workspace_aggregate_provider_evidence"
    ]
    assert (
        result["details"]["api_materialization_event_report"][
            "workspace_aggregate_provider_evidence_status"
        ]
        == "api_workspace_aggregate_provider_evidence_blocked"
    )
    assert aggregate_evidence["provider_key"] == "aware_api"
    assert aggregate_evidence["workspace_aggregate_consumes_provider_envelope"] is True
    assert (
        aggregate_evidence["workspace_envelope_retains_provider_report_payload"] is True
    )
    assert result["details"]["provider_delta_typed_operation_plan"]["status"] == (
        "typed_operation_plan_blocked"
    )
    assert (
        result["details"]["provider_delta_typed_operation_plan"][
            "blocked_operation_count"
        ]
        == 3
    )


@pytest.mark.asyncio
async def test_api_provider_delta_bundle_dry_run_invokes_real_adapter(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    request = _api_provider_delta_request(api_toml_path=api_toml_path)
    provider = {
        "provider_key": "aware_api",
        "semantic_owner": "aware_api.provider",
        "callable_module": "aware_api_runtime.workspace_provider",
        "callable_name": "materialize",
        "metadata": {
            SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY: {
                "callable_module": ("aware_api_runtime.workspace_provider"),
                "callable_name": SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
            },
        },
    }
    classification = classify_workspace_semantic_materialization_provider_delta_request(
        request=request,
        provider=provider,
    )
    adapter_plan = plan_workspace_semantic_materialization_provider_delta_adapter(
        request=request,
        classification=classification,
    )
    bundle = build_workspace_semantic_materialization_provider_delta_request_bundle(
        requests=(request,),
        classifications=(classification,),
        adapter_plans=(adapter_plan,),
    )
    bundle_path = tmp_path / "provider-delta-request-bundle.json"
    bundle_path.write_text(
        json.dumps(bundle.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    from aware_workspace.cli.workspace_command import (  # noqa: WPS433
        _workspace_provider_delta_adapter_dry_run_diagnostics_from_bundle_path,
    )

    diagnostics = (
        await _workspace_provider_delta_adapter_dry_run_diagnostics_from_bundle_path(
            bundle_path=bundle_path,
        )
    )

    diagnostic = diagnostics[0]
    result = diagnostic["result"]
    bundle_package = result["bundle_package"]
    commit_ref_contract = result["commit_ref_contract"]
    operation_plan = result["details"]["delta_operation_plan"]
    assert classification.reason == "provider_declares_delta_adapter"
    assert adapter_plan.status == "ready_non_executing"
    assert (
        diagnostic["provider_delta_request_key"] == request.provider_delta_request_key
    )
    assert diagnostic["dry_run_status"] == "passed"
    assert diagnostic["dry_run_reason"] == "adapter_result_contract_valid"
    assert diagnostic["adapter_invoked"] is True
    assert diagnostic["production_execution_wired"] is False
    assert diagnostic["result_status"] == "succeeded"
    assert result["status"] == "succeeded"
    assert result["applied_semantic_keys"] == [
        "api:demo",
        "api:demo/capability:read_demo",
        "api:demo/capability:read_demo/endpoint:read_demo",
    ]
    assert result["details"]["mode"] == "api_provider_delta_result_dry_run"
    assert result["details"]["production_execution_wired"] is False
    operation_execution = result["details"]["provider_delta_operation_execution"]
    assert {
        key: operation_execution[key]
        for key in (
            "execution_kind",
            "required_flag",
            "flag_requested",
            "operation_count",
            "semantic_function_call_plan_count",
            "would_execute",
            "did_execute",
            "would_persist",
            "receipt_persistence_contract_ready",
            "status",
            "reason",
            "execution_wired",
            "semantic_function_call_resolution_count",
            "semantic_function_call_resolution_status_counts",
        )
    } == {
        "execution_kind": "api_provider_delta_operation_execution",
        "required_flag": "execute_provider_delta_materialization",
        "flag_requested": False,
        "operation_count": 3,
        "semantic_function_call_plan_count": 3,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "receipt_persistence_contract_ready": False,
        "status": "flag_required",
        "reason": ("api_provider_delta_operation_execution_requires_explicit_flag"),
        "execution_wired": False,
        "semantic_function_call_resolution_count": 0,
        "semantic_function_call_resolution_status_counts": {},
    }
    assert operation_execution["durable_execution_inputs_status"] == (
        "durable_execution_inputs_unavailable"
    )
    assert (
        operation_execution["durable_execution_inputs_shared_contract_available"]
        is False
    )
    dry_run_durable_preflight = operation_execution[
        "durable_execution_inputs_preflight"
    ]
    assert dry_run_durable_preflight["available"] is False
    assert dry_run_durable_preflight["common_inputs_available"] is False
    assert result["details"]["semantic_delta_count"] == 3
    assert operation_plan["plan_kind"] == "api_provider_delta_operation_plan"
    assert operation_plan["status"] == "ready_non_executing"
    assert operation_plan["reason"] == "api_provider_delta_operation_plan_ready"
    assert operation_plan["changed_source_files"] == ["apis/demo.aware"]
    assert operation_plan["affected_api_names"] == ["demo"]
    assert operation_plan["affected_capability_names"] == ["read_demo"]
    assert operation_plan["required_materializations"] == [
        "api_compile_plan",
        "api_ontology_plan",
    ]
    assert operation_plan["operation_count"] == 3
    assert operation_plan["semantic_delta_count"] == 3
    assert operation_plan["semantic_event_count"] == 3
    assert operation_plan["action_binding_count"] == 3
    assert operation_plan["semantic_function_call_plan_count"] == 3
    assert operation_plan["semantic_deltas"][0]["semantic_key"] == "api:demo"
    assert operation_plan["semantic_deltas"][2]["semantic_key"] == (
        "api:demo/capability:read_demo/endpoint:read_demo"
    )
    assert [
        plan["function_ref"] for plan in operation_plan["semantic_function_call_plans"]
    ] == [
        API_CREATE_FUNCTION_REF,
        API_CREATE_CAPABILITY_FUNCTION_REF,
        API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    ]
    assert [
        plan["metadata"]["preview_status"]
        for plan in operation_plan["semantic_function_call_plans"]
    ] == ["unresolved_templates", "ready", "ready"]
    assert operation_plan["semantic_function_call_plans"][0]["metadata"][
        "unresolved_templates"
    ] == [
        {
            "target": "arguments.description",
            "template": "payload.description",
        }
    ]
    assert operation_plan["apply_wired"] is False
    assert operation_plan["would_execute"] is False
    assert operation_plan["would_persist"] is False
    assert commit_ref_contract["contract_version"] == (
        "aware.workspace.semantic-materialization.provider-delta-commit-ref.v1"
    )
    assert commit_ref_contract["status"] == "missing_durable_refs"
    assert commit_ref_contract["reason"] == (
        "api_provider_delta_dry_run_does_not_materialize_commits"
    )
    assert commit_ref_contract["receipt_persistence_contract_ready"] is False
    assert commit_ref_contract["available_fields"] == ["source_code_package_id"]
    assert commit_ref_contract["missing_required_fields"] == [
        "source_object_instance_graph_commit_id",
        "semantic_package_id",
        "semantic_branch_id",
        "semantic_object_instance_graph_commit_id",
    ]
    assert bundle_package["package_key"] == "demo-api"
    assert bundle_package["package_kind"] == "api"
    assert bundle_package["semantic_owner_module"] == "aware_api"
    assert bundle_package["semantic_package_kind"] == "api"
    assert bundle_package["semantic_contract_provider_key"] == "aware_api"
    assert bundle_package["source_code_package_id"] == "source-code-package-id"
    assert bundle_package["semantic_package_id"] is None
    assert bundle_package["semantic_branch_id"] is None
    assert bundle_package["semantic_object_instance_graph_commit_id"] is None
    assert bundle_package["commit_ref_contract_status"] == "missing_durable_refs"
    assert bundle_package["receipt_persistence_contract_ready"] is False
    assert result["bundle_packages"] == [bundle_package]


@pytest.mark.asyncio
async def test_api_provider_delta_executes_operation_plan_when_flagged(
    tmp_path: Path,
) -> None:
    api_toml_path = _write_simple_api_delta_fixture(tmp_path)
    base_request = _api_provider_delta_request(api_toml_path=api_toml_path)
    backend = _RecordingApiExecutionBackend(
        object_ids=(
            "api-object-id",
            "capability-object-id",
            "endpoint-object-id",
            "source-code-package-id",
            "source-code-package-id",
            "api-package-id",
        ),
        commit_ids=(
            "api-root-commit-id",
            "api-capability-commit-id",
            "api-endpoint-commit-id",
            "source-code-package-build-commit-id",
            "source-code-package-upsert-commit-id",
            "api-package-commit-id",
        ),
        branch_id="semantic-branch-id",
    )
    durable_execution_inputs = SemanticProviderDeltaDurableExecutionInputs(
        provider_key="aware_api",
        semantic_owner="aware_api.provider",
        semantic_branch_id="semantic-branch-id",
        semantic_projection_hash="api-projection-hash",
        semantic_projection_name="Api",
        author_id="author-id",
        provider_inputs={
            API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY: backend,
        },
    ).model_dump(mode="python")
    execution_request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        code_package_delta=base_request.code_package_delta,
        delta_cause_hints=base_request.delta_cause_hints,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        execute_provider_delta_materialization=True,
        semantic_function_call_execution_context={
            SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: (
                encode_semantic_function_call_context_by_provider(
                    {
                        "aware_api": SemanticFunctionCallContext(
                            resolved_argument_ref_object_ids={
                                "aware_demo_api.ReadDemoRequest": (
                                    "request-class-config-id"
                                ),
                            },
                        ),
                    }
                )
            ),
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY: (
                durable_execution_inputs
            ),
        },
    )

    result = await api_workspace_provider.materialize_delta(request=execution_request)

    details = result["details"]
    operation_execution = details["provider_delta_operation_execution"]
    durable_preflight = details["provider_delta_durable_execution_inputs_preflight"]
    assert result["status"] == "succeeded"
    assert details["mode"] == "api_provider_delta_operation_execution"
    assert details["production_execution_wired"] is True
    assert details["provider_delta_durable_execution_inputs_status"] == (
        "durable_execution_inputs_ready"
    )
    assert durable_preflight["shared_execution_inputs_contract_available"] is True
    assert durable_preflight["common_inputs_available"] is True
    assert durable_preflight["api_execution_backend_provider_input_available"] is True
    assert durable_preflight["provider_input_keys"] == (
        API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY,
    )
    assert operation_execution["status"] == "executed"
    assert operation_execution["reason"] == (
        "api_provider_delta_operation_execution_invoked"
    )
    assert operation_execution["flag_requested"] is True
    assert operation_execution["execution_wired"] is True
    assert operation_execution["would_execute"] is True
    assert operation_execution["did_execute"] is True
    assert operation_execution["would_persist"] is False
    assert operation_execution["receipt_persistence_contract_ready"] is False
    assert (
        operation_execution["durable_execution_inputs_shared_contract_available"]
        is True
    )
    assert operation_execution["durable_execution_inputs_status"] == (
        "durable_execution_inputs_ready"
    )
    assert operation_execution["semantic_function_call_resolution_count"] == 3
    assert operation_execution["semantic_function_call_resolution_status_counts"] == {
        "create_child": 2,
        "create_root": 1,
    }
    assert operation_execution["semantic_function_call_resolution_context"] == {
        "current_semantic_object_id_count": 0,
        "resolved_argument_ref_object_id_count": 1,
        "schema": "semantic_function_call_context",
    }
    function_execution = operation_execution["semantic_function_call_execution"]
    assert function_execution["status"] == "executed"
    assert function_execution["status_counts"] == {"invoked": 3}
    assert function_execution["step_count"] == 3
    package_source_execution = details[
        "provider_delta_package_source_operation_execution"
    ]
    assert package_source_execution["status"] == "executed"
    assert package_source_execution["reason"] == (
        "api_provider_delta_package_source_execution_invoked"
    )
    assert package_source_execution["did_execute"] is True
    assert package_source_execution["step_count"] == 3
    assert len(backend.invocations) == 6
    assert [invocation.function_ref for invocation in backend.invocations[:3]] == [
        API_CREATE_FUNCTION_REF,
        API_CREATE_CAPABILITY_FUNCTION_REF,
        API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    ]
    assert backend.invocations[0].call_target == "constructor"
    assert backend.invocations[1].receiver_object_id == "api-object-id"
    assert backend.invocations[2].receiver_object_id == "capability-object-id"
    assert backend.invocations[2].arguments["request_class_config_id"] == (
        "request-class-config-id"
    )
    assert backend.invocations[3].call_target == "constructor"
    assert "CodePackage.build" in backend.invocations[3].function_ref
    assert backend.invocations[4].call_target == "instance"
    assert backend.invocations[4].receiver_object_id == "source-code-package-id"
    assert "CodePackage.apply_delta" in backend.invocations[4].function_ref
    assert package_source_execution["source_update_strategy"] == ("code_package_delta")
    assert package_source_execution["source_delta_path_count"] == 1
    assert package_source_execution["source_delta_kind_counts"] == {"update": 1}
    assert [
        path["relative_path"]
        for path in backend.invocations[4].arguments["delta"]["paths"]
    ] == ["apis/demo.aware"]
    assert backend.invocations[5].call_target == "constructor"
    assert "ApiPackage.build" in backend.invocations[5].function_ref
    assert backend.invocations[5].arguments["api_id"] == "api-object-id"
    assert (
        backend.invocations[5].arguments["api_object_instance_graph_commit_id"]
        == "api-root-commit-id"
    )
    assert backend.invocations[5].arguments["source_code_package_id"] == (
        "source-code-package-id"
    )
    assert result["commit_ref_contract"]["status"] == "ready"
    assert result["commit_ref_contract"]["reason"] == (
        "api_provider_delta_operation_execution_materialized_refs"
    )
    assert result["commit_ref_contract"]["available_fields"] == [
        "source_code_package_id",
        "source_object_instance_graph_commit_id",
        "semantic_package_id",
        "semantic_branch_id",
        "semantic_object_instance_graph_commit_id",
    ]
    assert result["commit_ref_contract"]["missing_required_fields"] == []
    assert result["commit_ref_contract"]["receipt_persistence_contract_ready"] is True
    assert result["commit_ref_contract"]["would_persist"] is False
    assert result["bundle_package"]["semantic_branch_id"] == "semantic-branch-id"
    assert result["bundle_package"]["semantic_head_commit_id"] == (
        "api-package-commit-id"
    )
    assert result["bundle_package"]["semantic_object_instance_graph_commit_id"] == (
        "api-package-commit-id"
    )
    assert result["bundle_package"]["semantic_package_id"] == "api-package-id"
    assert result["bundle_package"]["source_code_package_id"] == (
        "source-code-package-id"
    )
    assert result["bundle_package"]["source_object_instance_graph_commit_id"] == (
        "source-code-package-upsert-commit-id"
    )
    assert result["bundle_package"]["semantic_root_id"] == "api-object-id"
    assert (
        result["bundle_package"]["semantic_root_object_instance_graph_commit_id"]
        == "api-root-commit-id"
    )
    assert details["operation_commit_ref_status"] == "partial_refs"
    assert details["operation_commit_ref_available_required_fields"] == [
        "source_code_package_id",
        "source_object_instance_graph_commit_id",
        "semantic_package_id",
        "semantic_branch_id",
        "semantic_object_instance_graph_commit_id",
    ]
    assert details["operation_commit_ref_missing_required_fields_after_operation"] == []
    assert details["package_source_commit_ref_status"] == "ready"


@pytest.mark.asyncio
async def test_api_provider_delta_commit_ref_probe_materializes_durable_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "api_provider_delta_commit_ref_probe"
    workspace_root.mkdir(parents=True, exist_ok=True)
    api_toml_path = _write_api_package_fixture(workspace_root=workspace_root)
    _write_module_owned_aware_api_dart_fixture(workspace_root=workspace_root)
    source_code_package_config_id = source_code_package_config_ref(
        manifest_kind="aware_api_toml",
        surface="api",
    ).config_id
    source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name="home-story-api",
        language=CodeLanguage.aware.value,
    )
    base_request = WorkspaceSemanticMaterializationProviderDeltaRequest.model_validate(
        {
            "package": {
                "package_name": "home-story-api",
                "workspace_manifest_kind": "api",
                "manifest_path": api_toml_path.as_posix(),
                "source_code_package_id": str(source_code_package_id),
            },
            "semantic_contract": {
                "module": "aware_api_runtime.semantic_contract",
                "provider_key": "aware_api",
                "role": "aware_api.provider",
                "name": "aware.semantic_provider",
            },
            "current_delta_fingerprint": "sha256:home-current",
            "code_package_delta": CodePackageDelta(
                package_name="home-story-api",
                package_root=".",
                sources_root="apis/bindings",
                manifest_relative_path=api_toml_path.name,
                authority_kind="workspace_provider_delta",
                source_revision_id="api-provider-delta-probe-test",
                paths=[
                    CodePackageDeltaPath(
                        relative_path="apis/bindings/home_devices.apis.aware",
                        kind=CodePackageDeltaKind.update,
                        content_text=(
                            workspace_root
                            / "apis"
                            / "bindings"
                            / "home_devices.apis.aware"
                        ).read_text(encoding="utf-8"),
                        language=CodeLanguage.aware,
                        is_structural=True,
                    )
                ],
            ),
            "delta_cause_hints": {
                "changed_path_count": 1,
                "source_owned_path_count": 1,
                "generated_fallout_path_count": 0,
                "changed_path_classifications": {"source_owned": 1},
                "top_changed_path_limit": 8,
                "top_changed_paths": [
                    {
                        "path": "apis/bindings/home_devices.apis.aware",
                        "change_kind": "update",
                        "classification": "source_owned",
                        "package_relative_path": (
                            "apis/bindings/home_devices.apis.aware"
                        ),
                        "language": "aware",
                        "is_structural": True,
                    }
                ],
                "current_delta_fingerprint_available": True,
                "previous_delta_fingerprint_available": True,
            },
        }
    )

    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_api_provider_delta_commit_ref_probe",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index
        branch_id = uuid4()
        from aware_meta.materialization import post_step_executor  # noqa: WPS433

        dart_home = tmp_path / "dart-home"
        dart_pub_cache = tmp_path / "pub-cache"
        fake_dart = tmp_path / "dart-sdk" / "bin" / "dart"

        def _fake_dart_post_step_run(
            *args: object,
            **kwargs: object,
        ) -> SimpleNamespace:
            _ = args
            cwd = kwargs.get("cwd")
            package_root = Path(str(cwd)) if cwd is not None else None
            lib_root = package_root / "lib" if package_root is not None else None
            if lib_root is not None and lib_root.is_dir():
                for source in sorted(
                    lib_root.rglob("*.dart"),
                    key=lambda path: path.as_posix(),
                ):
                    if source.name.endswith((".freezed.dart", ".g.dart")):
                        continue
                    for line in source.read_text(encoding="utf-8").splitlines():
                        stripped = line.strip()
                        if not stripped.startswith("part "):
                            continue
                        tokens = stripped.split("'")
                        if len(tokens) < 2:
                            continue
                        part_path = source.parent / tokens[1]
                        part_path.write_text(
                            f"part of '{source.name}';\n",
                            encoding="utf-8",
                        )
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        monkeypatch.setattr(
            post_step_executor.subprocess,
            "run",
            _fake_dart_post_step_run,
        )
        probe_request = SimpleNamespace(
            package=base_request.package,
            semantic_contract=base_request.semantic_contract,
            current_delta_fingerprint=base_request.current_delta_fingerprint,
            code_package_delta=base_request.code_package_delta,
            delta_cause_hints=base_request.delta_cause_hints,
            previous_materialization_evidence=(
                base_request.previous_materialization_evidence
            ),
            enable_commit_ref_probe=True,
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            context={
                "workspace_dependency_roots": {
                    "roots": [repo_root.as_posix()],
                },
                SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY: {
                    "contract_version": (
                        "aware.code.semantic-materialization.language-tooling.v1"
                    ),
                    "tools": [
                        {
                            "tool_id": "dart.pub_get",
                            "state_env": {
                                "HOME": str(dart_home),
                                "PUB_CACHE": str(dart_pub_cache),
                            },
                            "executable_overrides": {
                                "dart": str(fake_dart),
                            },
                        },
                        {
                            "tool_id": "dart.build_runner",
                            "state_env": {
                                "HOME": str(dart_home),
                                "PUB_CACHE": str(dart_pub_cache),
                            },
                            "executable_overrides": {
                                "dart": str(fake_dart),
                            },
                        },
                        {
                            "tool_id": "dart.format",
                            "state_env": {
                                "HOME": str(dart_home),
                            },
                            "executable_overrides": {
                                "dart": str(fake_dart),
                            },
                        },
                    ],
                },
            },
        )

        result = await api_workspace_provider.materialize_delta(request=probe_request)

    commit_ref_contract = result["commit_ref_contract"]
    bundle_package = result["bundle_package"]
    operation_plan = result["details"]["delta_operation_plan"]
    assert result["status"] == "succeeded"
    assert result["details"].get("commit_ref_probe_error") is None, result[
        "details"
    ].get("commit_ref_probe_error")
    assert result["details"]["commit_ref_probe_status"] == "executed", result["details"]
    assert result["details"]["mode"] == "api_provider_delta_commit_ref_probe"
    assert result["details"]["commit_ref_probe_status"] == "executed"
    assert result["details"]["commit_ref_probe_executed"] is True
    assert result["details"]["production_execution_wired"] is False
    assert operation_plan["status"] == "ready_non_executing"
    assert operation_plan["changed_source_files"] == (
        "apis/bindings/home_devices.apis.aware",
    )
    assert operation_plan["affected_api_names"] == ("home_devices",)
    assert operation_plan["semantic_delta_count"] == 3
    assert operation_plan["semantic_function_call_plan_count"] == 3
    assert operation_plan["semantic_deltas"][0]["semantic_key"] == ("api:home_devices")
    assert operation_plan["semantic_function_call_plans"][2]["function_ref"] == (
        API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF
    )
    assert operation_plan["would_execute"] is False
    assert operation_plan["would_persist"] is False
    assert commit_ref_contract["status"] == "ready"
    assert commit_ref_contract["reason"] == (
        "api_provider_delta_commit_ref_probe_materialized_refs"
    )
    assert commit_ref_contract["receipt_persistence_contract_ready"] is True
    assert commit_ref_contract["missing_required_fields"] == []
    assert commit_ref_contract["available_fields"] == [
        "source_code_package_id",
        "source_object_instance_graph_commit_id",
        "semantic_package_id",
        "semantic_branch_id",
        "semantic_object_instance_graph_commit_id",
    ]
    assert bundle_package["package_key"] == "home-story-api"
    assert bundle_package["source_code_package_id"] == str(source_code_package_id)
    assert bundle_package["source_object_instance_graph_commit_id"]
    assert bundle_package["semantic_package_id"]
    assert bundle_package["semantic_branch_id"] == str(branch_id)
    assert bundle_package["semantic_head_commit_id"]
    assert bundle_package["semantic_object_instance_graph_commit_id"]
    assert bundle_package["semantic_root_id"]
    assert bundle_package["semantic_root_object_instance_graph_commit_id"]
    assert bundle_package["commit_ref_contract_status"] == "ready"
    assert bundle_package["receipt_persistence_contract_ready"] is True
    assert tuple(result["bundle_packages"]) == (bundle_package,)


@pytest.mark.asyncio
async def test_api_workspace_provider_passes_context_graphs_to_materialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}
    context_graph = ObjectConfigGraph(
        id=uuid4(),
        name="Attention",
        fqn_prefix="aware_attention",
        hash="hash",
        language=CodeLanguage.aware,
    )

    async def _fake_materialize_api_package_from_manifest(**kwargs: object):
        observed.update(kwargs)
        return SimpleNamespace(
            api_toml_path=tmp_path / "aware.api.toml",
            api=SimpleNamespace(name="demo", id=uuid4()),
            api_package=SimpleNamespace(name="demo-api", id=uuid4()),
            source_code_package_id=uuid4(),
            api_source_path="apis/demo.aware",
            source_files=("apis/demo.aware",),
            phase_timings_s={},
            api_endpoint_catalog={},
            api_commit_id=uuid4(),
            api_object_instance_graph_commit_id=uuid4(),
            package_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            generated_dto_graph_count=0,
            generated_dto_class_config_count=0,
        )

    monkeypatch.setattr(
        api_workspace_provider,
        "materialize_api_package_from_manifest",
        _fake_materialize_api_package_from_manifest,
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.api.toml",
        context={"semantic_object_config_graphs": (context_graph,)},
    )

    await api_workspace_provider.materialize(request)

    assert observed["accessible_graphs"] == (context_graph,)


@pytest.mark.asyncio
async def test_api_dto_export_provider_passes_context_graphs_to_materialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.compile as api_compile_mod
    import aware_api_runtime.compile_materialization.service as api_materialization_service
    import aware_api_runtime.packages.materialization as api_products_mod

    observed: dict[str, object] = {}
    context_graph = ObjectConfigGraph(
        id=uuid4(),
        name="Code",
        fqn_prefix="aware_code",
        hash="hash",
        language=CodeLanguage.aware,
    )
    dto_graph = ObjectConfigGraph(
        id=uuid4(),
        name="NetworkServiceDto",
        fqn_prefix="aware_network_service_dto",
        hash="dto-hash",
        language=CodeLanguage.aware,
    )
    api_toml_path = tmp_path / "aware.api.toml"
    dto_manifest_path = tmp_path / "dto" / "aware.toml"
    dto_package_root = tmp_path / "dto" / "python"
    _write(dto_package_root / "pyproject.toml", "[project]\nname = 'dto'\n")
    _write(
        dto_package_root / "aware_network_service_dto" / "__init__.py",
        "VALUE = 1\n",
    )
    _write(
        dto_package_root
        / "aware_network_service_dto"
        / "_aware"
        / "python.models.json",
        "{}\n",
    )

    class _Workspace:
        def build_snapshot(self) -> object:
            return SimpleNamespace(
                spec=SimpleNamespace(
                    api=SimpleNamespace(package_name="network-service-api"),
                ),
            )

    def _fake_materialize_api_dto_packages(**kwargs: object) -> tuple[object, ...]:
        observed.update(kwargs)
        return (
            SimpleNamespace(
                semantic_package_export=SimpleNamespace(
                    package_name="network-service-dto",
                ),
                dependency_package=SimpleNamespace(graph=dto_graph),
                import_root="aware_network_service_dto",
                materialization_result=SimpleNamespace(
                    files=(
                        dto_package_root / "pyproject.toml",
                        dto_package_root / "aware_network_service_dto" / "__init__.py",
                        dto_package_root
                        / "aware_network_service_dto"
                        / "_aware"
                        / "python.models.json",
                    )
                ),
                package_root=dto_package_root,
            ),
        )

    async def _fake_resolve_source_owned_api_dto_export_accessible_graphs(
        **kwargs: object,
    ) -> tuple[object, ...]:
        observed["resolver_accessible_graphs"] = kwargs["accessible_graphs"]
        return tuple(cast(tuple[object, ...], kwargs["accessible_graphs"]))

    monkeypatch.setattr(
        api_workspace_provider,
        "_api_dto_declaring_api_toml_path",
        lambda request: api_toml_path,
    )
    monkeypatch.setattr(
        api_workspace_provider.APIWorkspace,
        "from_toml",
        lambda **_: _Workspace(),
    )
    monkeypatch.setattr(
        api_workspace_provider,
        "_api_dto_export_for_manifest",
        lambda **_: SimpleNamespace(package_name="network-service-dto"),
    )
    monkeypatch.setattr(
        api_compile_mod,
        "resolve_api_runtime_package_dir",
        lambda **_: tmp_path / "runtime",
    )
    monkeypatch.setattr(
        api_materialization_service,
        "resolve_source_owned_api_dto_export_accessible_graphs",
        _fake_resolve_source_owned_api_dto_export_accessible_graphs,
    )
    monkeypatch.setattr(
        api_products_mod,
        "materialize_api_dto_packages",
        _fake_materialize_api_dto_packages,
    )
    monkeypatch.setattr(
        api_workspace_provider,
        "_api_dto_artifact_ownership_receipts",
        lambda **_: (),
    )

    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=dto_manifest_path,
        context={
            "workspace_manifest_kind": "api_dto",
            "semantic_object_config_graphs": (context_graph,),
        },
    )

    result = await api_workspace_provider.materialize(request)

    assert observed["resolver_accessible_graphs"] == (context_graph,)
    assert observed["accessible_graphs"] == (context_graph,)
    deltas = result.details["generated_code_package_deltas"]
    assert isinstance(deltas, list)
    assert len(deltas) == 1
    delta = deltas[0]
    assert isinstance(delta, dict)
    assert delta["package_name"] == "aware_network_service_dto"
    assert delta["package_root"] == "dto/python"
    assert delta["sources_root"] == "aware_network_service_dto"
    assert delta["manifest_relative_path"] == "dto/python/pyproject.toml"
    delta_paths = cast(list[dict[str, object]], delta["paths"])
    assert {path["relative_path"] for path in delta_paths} == {
        "pyproject.toml",
        "aware_network_service_dto/__init__.py",
    }
    assert all("_aware" not in str(path["relative_path"]) for path in delta_paths)
    assert {path["relative_path"]: path["path_role"] for path in delta_paths} == {
        "pyproject.toml": CodePackagePathRole.generated_manifest.value,
        "aware_network_service_dto/__init__.py": (
            CodePackagePathRole.generated_code.value
        ),
    }


def test_api_provider_delta_reads_context_graphs_for_runtime_plan() -> None:
    context_graph = _demo_api_render_input_context_graph()
    request = SimpleNamespace(
        semantic_function_call_execution_context={
            "semantic_object_config_graphs": (context_graph,),
        },
    )

    assert api_workspace_provider._api_delta_semantic_object_config_graphs_from_request(  # noqa: SLF001
        request=request,
    ) == (
        context_graph,
    )


@pytest.mark.asyncio
async def test_api_provider_delta_commit_ref_probe_passes_context_graphs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context_graph = _demo_api_render_input_context_graph()
    branch_id = uuid4()
    observed: dict[str, object] = {}

    async def _fake_materialize_api_package_from_manifest(**kwargs: object):
        observed.update(kwargs)
        return SimpleNamespace(
            api=SimpleNamespace(id=uuid4(), name="demo"),
            api_package=SimpleNamespace(id=uuid4(), name="demo-api"),
            source_code_package_id=uuid4(),
            source_object_instance_graph_commit_id=uuid4(),
            api_object_instance_graph_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            phase_timings_s={},
        )

    expected_tool_env = {
        "dart.build_runner": {
            "HOME": (tmp_path / "home").as_posix(),
        },
    }
    expected_executable_overrides = {
        "dart.build_runner": {
            "dart": "/tmp/fake-dart",
        },
    }
    monkeypatch.setattr(
        api_workspace_provider,
        "materialize_api_package_from_manifest",
        _fake_materialize_api_package_from_manifest,
    )
    request = SimpleNamespace(
        enable_commit_ref_probe=True,
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=branch_id,
        workspace_root=tmp_path,
        semantic_function_call_execution_context={
            "semantic_object_config_graphs": (context_graph,),
        },
        context={
            SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY: {
                "contract_version": (
                    "aware.code.semantic-materialization.language-tooling.v1"
                ),
                "tools": [
                    {
                        "tool_id": "dart.build_runner",
                        "state_env": expected_tool_env["dart.build_runner"],
                        "executable_overrides": (
                            expected_executable_overrides["dart.build_runner"]
                        ),
                    }
                ],
            }
        },
    )

    commit_ref_payload, details = (
        await api_workspace_provider._api_delta_commit_ref_payload_for_succeeded_delta(  # noqa: SLF001
            request=request,
            package_payload={
                "package_name": "demo-api",
                "source_code_package_id": str(uuid4()),
            },
            semantic_contract_payload={
                "provider_key": "aware_api",
                "role": "aware_api.provider",
                "name": "aware.semantic_provider",
            },
            manifest_path=tmp_path / "aware.api.toml",
            operation_execution={},
            package_source_execution={},
        )
    )

    assert observed["accessible_graphs"] == (context_graph,)
    assert observed["post_step_tool_env_by_tool_id"] == expected_tool_env
    assert observed["post_step_executable_overrides_by_tool_id"] == (
        expected_executable_overrides
    )
    assert observed["branch_id"] == branch_id
    assert details["commit_ref_probe_status"] == "executed"
    assert commit_ref_payload["commit_ref_contract"]["status"] == "ready"


@pytest.mark.asyncio
async def test_api_workspace_provider_reports_semantic_function_call_plan_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_materialize_api_package_from_manifest(**_: object):
        return SimpleNamespace(
            api_toml_path=tmp_path / "aware.api.toml",
            api=SimpleNamespace(name="demo", id=uuid4()),
            api_package=SimpleNamespace(name="demo-api", id=uuid4()),
            source_code_package_id=uuid4(),
            api_source_path="apis/demo.aware",
            source_files=("apis/demo.aware",),
            phase_timings_s={},
            api_endpoint_catalog={},
            api_commit_id=uuid4(),
            package_commit_id=uuid4(),
            api_object_instance_graph_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            generated_dto_graph_count=0,
            generated_dto_class_config_count=0,
        )

    monkeypatch.setattr(
        api_workspace_provider,
        "materialize_api_package_from_manifest",
        _fake_materialize_api_package_from_manifest,
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.api.toml",
        change_preview={
            "affected_semantic_keys": ("demo",),
            "semantic_events": (
                {
                    "event_key": "aware_api.api_capability_endpoint.upserted",
                    "semantic_key": (
                        "api:demo/capability:read_demo/endpoint:read_demo"
                    ),
                    "payload": {
                        "capability_semantic_key": ("api:demo/capability:read_demo"),
                        "name": "read_demo",
                        "description": None,
                        "request_class_ref": "aware_demo_api.ReadDemoRequest",
                    },
                },
            ),
            "action_bindings": (
                {
                    "action_key": (
                        "aware_api.api_capability_endpoint.upserted." "apply_ontology"
                    ),
                    "event_key": "aware_api.api_capability_endpoint.upserted",
                    "action_type": "function_call",
                    "function_call_binding": {
                        "binding_key": (
                            "aware_api.api_capability_endpoint.upserted."
                            "api_capability_create_endpoint"
                        ),
                        "event_key": ("aware_api.api_capability_endpoint.upserted"),
                        "function_ref": API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
                        "receiver_semantic_key_template": (
                            "payload.capability_semantic_key"
                        ),
                        "argument_bindings": {
                            "name": "payload.name",
                            "description": "payload.description",
                        },
                        "argument_ref_bindings": {
                            "request_class_config_id": ("payload.request_class_ref"),
                        },
                        "result_semantic_key_template": "semantic_key",
                        "metadata": {
                            "argument_ref_resolution": "class_config_id",
                        },
                    },
                },
            ),
        },
    )

    result = await api_workspace_provider.materialize(request)

    assert len(result.semantic_function_call_plans) == 1
    plan = result.semantic_function_call_plans[0]
    assert plan.function_ref == API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF
    assert plan.receiver_semantic_key == "api:demo/capability:read_demo"
    assert plan.arguments == {"description": None, "name": "read_demo"}
    assert plan.argument_refs == {
        "request_class_config_id": "aware_demo_api.ReadDemoRequest",
    }
    assert result.details["semantic_function_call_plan_count"] == 1
    assert result.details["semantic_function_call_plans"] == (plan.evidence_payload(),)
    assert result.details["semantic_function_call_resolution_count"] == 1
    assert result.details["semantic_function_call_resolution_status_counts"] == {
        "unresolved_receiver": 1,
    }
    resolutions = cast(
        tuple[dict[str, object], ...],
        result.details["semantic_function_call_resolutions"],
    )
    resolution = resolutions[0]
    assert resolution["status"] == "unresolved_receiver"
    assert resolution["function_ref"] == API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF
    assert resolution["arguments"] == {"description": None, "name": "read_demo"}
    assert resolution["argument_refs"] == {
        "request_class_config_id": "aware_demo_api.ReadDemoRequest",
    }
    assert resolution["event_key"] == "aware_api.api_capability_endpoint.upserted"
    assert resolution["binding_key"] == (
        "aware_api.api_capability_endpoint.upserted." "api_capability_create_endpoint"
    )
    assert resolution["action_key"] == (
        "aware_api.api_capability_endpoint.upserted.apply_ontology"
    )
    assert resolution["receiver_semantic_key"] == ("api:demo/capability:read_demo")
    assert resolution["result_semantic_key"] == (
        "api:demo/capability:read_demo/endpoint:read_demo"
    )
    assert resolution["reason"] == (
        "Receiver semantic key is neither current nor planned in batch."
    )
    assert result.details["semantic_function_call_resolution_context"] == {
        "current_semantic_object_id_count": 0,
        "resolved_argument_ref_object_id_count": 0,
        "schema": "semantic_function_call_context",
    }
    assert result.details["semantic_function_call_execution"] == {
        "enabled": False,
        "continue_on_failure": False,
        "status": "disabled",
    }


@pytest.mark.asyncio
async def test_api_workspace_provider_resolves_function_call_plans_from_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_materialize_api_package_from_manifest(**_: object):
        return SimpleNamespace(
            api_toml_path=tmp_path / "aware.api.toml",
            api=SimpleNamespace(name="demo", id=uuid4()),
            api_package=SimpleNamespace(name="demo-api", id=uuid4()),
            source_code_package_id=uuid4(),
            api_source_path="apis/demo.aware",
            source_files=("apis/demo.aware",),
            phase_timings_s={},
            api_endpoint_catalog={},
            api_commit_id=uuid4(),
            package_commit_id=uuid4(),
            api_object_instance_graph_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            generated_dto_graph_count=0,
            generated_dto_class_config_count=0,
        )

    monkeypatch.setattr(
        api_workspace_provider,
        "materialize_api_package_from_manifest",
        _fake_materialize_api_package_from_manifest,
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.api.toml",
        context={
            SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: (
                encode_semantic_function_call_context_by_provider(
                    {
                        "aware_api": SemanticFunctionCallContext(
                            current_semantic_object_ids={
                                "api:demo/capability:read_demo": ("capability-id"),
                            },
                            resolved_argument_ref_object_ids={
                                "aware_demo_api.ReadDemoRequest": (
                                    "request-class-config-id"
                                ),
                            },
                        ),
                    }
                )
            ),
        },
        change_preview={
            "semantic_events": (
                {
                    "event_key": "aware_api.api_capability_endpoint.upserted",
                    "semantic_key": (
                        "api:demo/capability:read_demo/endpoint:read_demo"
                    ),
                    "payload": {
                        "capability_semantic_key": ("api:demo/capability:read_demo"),
                        "name": "read_demo",
                        "description": None,
                        "request_class_ref": "aware_demo_api.ReadDemoRequest",
                    },
                },
            ),
            "action_bindings": (
                {
                    "action_key": (
                        "aware_api.api_capability_endpoint.upserted." "apply_ontology"
                    ),
                    "event_key": "aware_api.api_capability_endpoint.upserted",
                    "action_type": "function_call",
                    "function_call_binding": {
                        "binding_key": (
                            "aware_api.api_capability_endpoint.upserted."
                            "api_capability_create_endpoint"
                        ),
                        "event_key": ("aware_api.api_capability_endpoint.upserted"),
                        "function_ref": API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
                        "receiver_semantic_key_template": (
                            "payload.capability_semantic_key"
                        ),
                        "argument_bindings": {
                            "name": "payload.name",
                            "description": "payload.description",
                        },
                        "argument_ref_bindings": {
                            "request_class_config_id": ("payload.request_class_ref"),
                        },
                        "result_semantic_key_template": "semantic_key",
                        "metadata": {
                            "argument_ref_resolution": "class_config_id",
                        },
                    },
                },
            ),
        },
    )

    result = await api_workspace_provider.materialize(request)

    assert result.details["semantic_function_call_resolution_status_counts"] == {
        "create_child": 1,
    }
    assert result.details["semantic_function_call_resolution_context"] == {
        "current_semantic_object_id_count": 1,
        "resolved_argument_ref_object_id_count": 1,
        "schema": "semantic_function_call_context",
    }
    resolutions = cast(
        tuple[dict[str, object], ...],
        result.details["semantic_function_call_resolutions"],
    )
    resolution = resolutions[0]
    assert resolution["status"] == "create_child"
    assert resolution["function_ref"] == API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF
    assert resolution["arguments"] == {"description": None, "name": "read_demo"}
    assert resolution["argument_refs"] == {
        "request_class_config_id": "aware_demo_api.ReadDemoRequest",
    }
    assert resolution["resolved_argument_refs"] == {
        "request_class_config_id": "request-class-config-id",
    }
    assert resolution["receiver_source"] == "current"
    assert resolution["receiver_semantic_key"] == ("api:demo/capability:read_demo")
    assert resolution["receiver_object_id"] == "capability-id"
    assert resolution["result_semantic_key"] == (
        "api:demo/capability:read_demo/endpoint:read_demo"
    )


@pytest.mark.asyncio
async def test_api_workspace_provider_executes_function_call_plans_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_materialize_api_package_from_manifest(**_: object):
        return SimpleNamespace(
            api_toml_path=tmp_path / "aware.api.toml",
            api=SimpleNamespace(name="demo", id=uuid4()),
            api_package=SimpleNamespace(name="demo-api", id=uuid4()),
            source_code_package_id=uuid4(),
            api_source_path="apis/demo.aware",
            source_files=("apis/demo.aware",),
            phase_timings_s={},
            api_endpoint_catalog={},
            api_commit_id=uuid4(),
            package_commit_id=uuid4(),
            api_object_instance_graph_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            generated_dto_graph_count=0,
            generated_dto_class_config_count=0,
        )

    monkeypatch.setattr(
        api_workspace_provider,
        "materialize_api_package_from_manifest",
        _fake_materialize_api_package_from_manifest,
    )
    backend = _RecordingApiExecutionBackend()
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.api.toml",
        context={
            SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY: (
                encode_semantic_function_call_context_by_provider(
                    {
                        "aware_api": SemanticFunctionCallContext(
                            current_semantic_object_ids={
                                "api:demo/capability:read_demo": ("capability-id"),
                            },
                            resolved_argument_ref_object_ids={
                                "aware_demo_api.ReadDemoRequest": (
                                    "request-class-config-id"
                                ),
                            },
                        ),
                    }
                )
            ),
            SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY: {
                "enabled": True,
            },
            API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY: backend,
        },
        change_preview={
            "semantic_events": (
                {
                    "event_key": "aware_api.api_capability_endpoint.upserted",
                    "semantic_key": (
                        "api:demo/capability:read_demo/endpoint:read_demo"
                    ),
                    "payload": {
                        "capability_semantic_key": ("api:demo/capability:read_demo"),
                        "name": "read_demo",
                        "description": None,
                        "request_class_ref": "aware_demo_api.ReadDemoRequest",
                    },
                },
            ),
            "action_bindings": (
                {
                    "action_key": (
                        "aware_api.api_capability_endpoint.upserted." "apply_ontology"
                    ),
                    "event_key": "aware_api.api_capability_endpoint.upserted",
                    "action_type": "function_call",
                    "function_call_binding": {
                        "binding_key": (
                            "aware_api.api_capability_endpoint.upserted."
                            "api_capability_create_endpoint"
                        ),
                        "event_key": ("aware_api.api_capability_endpoint.upserted"),
                        "function_ref": API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
                        "receiver_semantic_key_template": (
                            "payload.capability_semantic_key"
                        ),
                        "argument_bindings": {
                            "name": "payload.name",
                            "description": "payload.description",
                        },
                        "argument_ref_bindings": {
                            "request_class_config_id": ("payload.request_class_ref"),
                        },
                        "result_semantic_key_template": "semantic_key",
                        "metadata": {
                            "argument_ref_resolution": "class_config_id",
                        },
                    },
                },
            ),
        },
    )

    result = await api_workspace_provider.materialize(request)

    assert len(backend.invocations) == 1
    invocation = backend.invocations[0]
    assert invocation.call_target == "instance"
    assert invocation.provider_key == "aware_api"
    assert invocation.receiver_object_id == "capability-id"
    assert invocation.function_ref == API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF
    assert invocation.arguments == {
        "description": None,
        "name": "read_demo",
        "request_class_config_id": "request-class-config-id",
    }
    assert result.details["semantic_function_call_execution"] == {
        "enabled": True,
        "continue_on_failure": False,
        "status": "executed",
        "step_count": 1,
        "status_counts": {"invoked": 1},
        "steps": (
            {
                "status": "invoked",
                "resolution_status": "create_child",
                "function_ref": API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
                "semantic_key": ("api:demo/capability:read_demo/endpoint:read_demo"),
                "result_object_id": "executed-object-id",
                "receiver_object_id": "capability-id",
                "evidence": {
                    "resolution": {
                        "status": "create_child",
                        "function_ref": (API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF),
                        "arguments": {
                            "description": None,
                            "name": "read_demo",
                        },
                        "argument_refs": {
                            "request_class_config_id": (
                                "aware_demo_api.ReadDemoRequest"
                            ),
                        },
                        "resolved_argument_refs": {
                            "request_class_config_id": ("request-class-config-id"),
                        },
                        "unresolved_argument_refs": {},
                        "dependencies": (),
                        "binding_key": (
                            "aware_api.api_capability_endpoint.upserted."
                            "api_capability_create_endpoint"
                        ),
                        "action_key": (
                            "aware_api.api_capability_endpoint.upserted."
                            "apply_ontology"
                        ),
                        "event_key": ("aware_api.api_capability_endpoint.upserted"),
                        "receiver_source": "current",
                        "receiver_semantic_key": ("api:demo/capability:read_demo"),
                        "receiver_object_id": "capability-id",
                        "result_semantic_key": (
                            "api:demo/capability:read_demo/endpoint:read_demo"
                        ),
                    },
                    "invocation": {
                        "provider_key": "aware_api",
                        "call_target": "instance",
                        "function_ref": (API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF),
                        "arguments": {
                            "description": None,
                            "name": "read_demo",
                            "request_class_config_id": ("request-class-config-id"),
                        },
                        "evidence": {
                            "status": "create_child",
                            "function_ref": (
                                API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF
                            ),
                            "arguments": {
                                "description": None,
                                "name": "read_demo",
                            },
                            "argument_refs": {
                                "request_class_config_id": (
                                    "aware_demo_api.ReadDemoRequest"
                                ),
                            },
                            "resolved_argument_refs": {
                                "request_class_config_id": ("request-class-config-id"),
                            },
                            "unresolved_argument_refs": {},
                            "dependencies": (),
                            "binding_key": (
                                "aware_api.api_capability_endpoint.upserted."
                                "api_capability_create_endpoint"
                            ),
                            "action_key": (
                                "aware_api.api_capability_endpoint.upserted."
                                "apply_ontology"
                            ),
                            "event_key": ("aware_api.api_capability_endpoint.upserted"),
                            "receiver_source": "current",
                            "receiver_semantic_key": ("api:demo/capability:read_demo"),
                            "receiver_object_id": "capability-id",
                            "result_semantic_key": (
                                "api:demo/capability:read_demo/endpoint:" "read_demo"
                            ),
                        },
                        "receiver_object_id": "capability-id",
                        "result_semantic_key": (
                            "api:demo/capability:read_demo/endpoint:read_demo"
                        ),
                    },
                    "result": {
                        "object_id": "executed-object-id",
                        "evidence": {"ordinal": 1},
                    },
                },
            },
        ),
    }


@pytest.mark.asyncio
async def test_api_semantic_analysis_preview_flows_into_workspace_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(
        tmp_path / "apis" / "demo.aware",
        "\n".join(
            [
                "api demo {",
                "    capability read_demo {",
                "        endpoint read_demo aware_demo_api.ReadDemoRequest {",
                "            response aware_demo_api.DemoResponse;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
    )
    delta = CodePackageDelta(
        package_name="demo-api",
        package_root=".",
        sources_root="apis",
        manifest_relative_path="aware.api.toml",
        authority_kind="workspace_sdk",
        source_revision_id="semantic-event-preview-e2e",
        paths=[
            CodePackageDeltaPath(
                relative_path="apis/demo.aware",
                kind=CodePackageDeltaKind.update,
                content_text=(tmp_path / "apis" / "demo.aware").read_text(
                    encoding="utf-8"
                ),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )
    analysis = analyze_api_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=tmp_path,
            source_files=(Path("apis/demo.aware"),),
            code_package_delta=delta,
        )
    )

    async def _fake_materialize_api_package_from_manifest(**_: object):
        return SimpleNamespace(
            api_toml_path=tmp_path / "aware.api.toml",
            api=SimpleNamespace(name="demo", id=uuid4()),
            api_package=SimpleNamespace(name="demo-api", id=uuid4()),
            source_code_package_id=uuid4(),
            api_source_path="apis/demo.aware",
            source_files=("apis/demo.aware",),
            phase_timings_s={},
            api_endpoint_catalog={},
            api_commit_id=uuid4(),
            package_commit_id=uuid4(),
            api_object_instance_graph_commit_id=uuid4(),
            package_head_commit_id=uuid4(),
            generated_dto_graph_count=0,
            generated_dto_class_config_count=0,
        )

    monkeypatch.setattr(
        api_workspace_provider,
        "materialize_api_package_from_manifest",
        _fake_materialize_api_package_from_manifest,
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.api.toml",
        code_package_delta=delta,
        semantic_analysis=analysis,
        change_preview=analysis.change_preview.evidence_payload(),
    )

    result = await api_workspace_provider.materialize(request)

    assert result.mode == "full_rebuild"
    assert result.affected_semantic_keys == ("demo",)
    assert len(result.semantic_function_call_plans) == 3
    assert tuple(plan.function_ref for plan in result.semantic_function_call_plans) == (
        API_CREATE_FUNCTION_REF,
        API_CREATE_CAPABILITY_FUNCTION_REF,
        API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    )
    endpoint_plan = result.semantic_function_call_plans[-1]
    assert endpoint_plan.receiver_semantic_key == "api:demo/capability:read_demo"
    assert endpoint_plan.arguments == {
        "description": None,
        "name": "read_demo",
    }
    assert endpoint_plan.argument_refs == {
        "request_class_config_id": "aware_demo_api.ReadDemoRequest",
    }
    assert endpoint_plan.metadata["preview_status"] == "ready"
    assert result.details["semantic_function_call_plan_count"] == 3
    assert result.details["semantic_function_call_resolution_status_counts"] == {
        "create_child": 1,
        "create_root": 1,
        "needs_ref_resolution": 1,
    }
    resolutions = cast(
        tuple[dict[str, object], ...],
        result.details["semantic_function_call_resolutions"],
    )
    endpoint_resolution = resolutions[-1]
    assert endpoint_resolution["status"] == "needs_ref_resolution"
    assert endpoint_resolution["receiver_source"] == "planned"
    assert endpoint_resolution["unresolved_argument_refs"] == {
        "request_class_config_id": "aware_demo_api.ReadDemoRequest",
    }


def _write_api_package_fixture(
    *,
    workspace_root: Path,
    extra_api: bool = False,
    include_projection_binding: bool = False,
    include_dart_package: bool = True,
) -> Path:
    _write_home_ontology_fixture(
        workspace_root=workspace_root,
        include_projection=include_projection_binding,
    )
    _write_api_type_package_fixture(
        workspace_root=workspace_root,
        include_projection_binding=include_projection_binding,
    )
    api_toml_path = workspace_root / "aware.api.toml"
    _write(
        api_toml_path,
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "home-story-api"',
                'fqn_prefix = "aware_home_story_api"',
                "version_number = 5",
                'title = "Home Story API"',
                'description = "Home story API semantic package"',
                "",
                "[build]",
                'sources_dir = "apis/bindings"',
                'include_paths = ["**/*.aware"]',
                'exclude_paths = ["**/*.draft.aware"]',
                "force_fresh_scan = true",
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "home-api"',
                "version_number = 2",
                "",
                "[[dependencies]]",
                'package_name = "home-ontology"',
                "version_number = 3",
                "",
                "[targets.python]",
                'root_dir = "apis/home/python"',
                "",
                "[targets.python.public_package]",
                'package_dir = "aware_home_story_api"',
                'root_dir = "apis/home/python/public"',
                "",
                "[targets.python.service_protocol]",
                'package_dir = "aware_home_story_api_service_protocol"',
                'root_dir = "apis/home/python/service_protocol"',
                "",
                "[targets.dart]",
                'root_dir = "apis/home/dart"',
                "",
                "[targets.dart.public_package]",
                'package_dir = "aware_home_story_api"',
                'root_dir = "apis/home/dart/public"',
            ]
        )
        + "\n",
    )
    lines = [
        "api home_devices {",
        "    capability lock_door {",
        "        endpoint lock_door aware_home_api.door.LockDoor;",
        "    }",
        "    graph aware_home {",
    ]
    if include_projection_binding:
        lines.extend(
            [
                "        projection aware_home.Home {",
                "        }",
            ]
        )
    lines.extend(
        [
            "        capability lock_door {",
            "            function lock aware_home.home.Door.lock;",
            "        }",
            "    }",
            "}",
            "",
        ]
    )
    if extra_api:
        lines.extend(
            [
                "api windows {",
                "    capability open_window {",
                "        endpoint open_window aware_home_story_api.models.OpenWindow;",
                "    }",
                "    graph aware_home {",
                "        capability open_window {",
                "            function open aware_home.home.Window.open;",
                "        }",
                "    }",
                "}",
                "",
            ]
        )
    _write(
        workspace_root / "apis" / "bindings" / "home_devices.apis.aware",
        "\n".join(lines),
    )
    _write_api_generated_language_package_fixtures(
        workspace_root=workspace_root,
        include_dart_package=include_dart_package,
    )
    return api_toml_path


def _write_api_generated_language_package_fixtures(
    *, workspace_root: Path, include_dart_package: bool = True
) -> None:
    public_root = workspace_root / "apis" / "home" / "python" / "public"
    _write(
        public_root / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "aware-home-story-api"',
                'version = "0.0.0"',
                "",
            ]
        ),
    )
    _write(public_root / "README.md", "Home Story API client package.\n")
    _write(
        public_root / "aware_home_story_api" / "__init__.py",
        '"""Home Story API client fixture."""\n',
    )
    _write(
        public_root / "aware_home_story_api" / "client.py",
        "class HomeStoryApiClient:\n    pass\n",
    )
    _write(public_root / "aware_home_story_api" / "py.typed", "")
    _write_bytes(
        public_root
        / "aware_home_story_api"
        / "_aware"
        / "ocg.binding.snapshot.msgpack",
        b"\x82\xa4hash\xa6fixture",
    )

    protocol_root = workspace_root / "apis" / "home" / "python" / "service_protocol"
    _write(
        protocol_root / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "aware-home-story-api-service-protocol"',
                'version = "0.0.0"',
                "",
            ]
        ),
    )
    _write(protocol_root / "README.md", "Home Story service protocol package.\n")
    _write(
        protocol_root / "aware_home_story_api_service_protocol" / "__init__.py",
        '"""Home Story API service protocol fixture."""\n',
    )
    _write(
        protocol_root / "aware_home_story_api_service_protocol" / "protocols.py",
        "async def invoke_home_devices__lock_door() -> None:\n    return None\n",
    )
    _write(
        protocol_root / "aware_home_story_api_service_protocol" / "py.typed",
        "",
    )
    _write_bytes(
        protocol_root
        / "aware_home_story_api_service_protocol"
        / "_aware"
        / "ocg.binding.snapshot.msgpack",
        b"\x82\xa4hash\xa6fixture",
    )

    if not include_dart_package:
        return

    dart_root = workspace_root / "apis" / "home" / "dart" / "public"
    _write(
        dart_root / "pubspec.yaml",
        "\n".join(
            [
                "name: aware_home_story_api",
                "version: 0.0.0",
                "environment:",
                "  sdk: ^3.0.0",
                "",
            ]
        ),
    )
    _write(dart_root / "pubspec.lock", "# fixture\n")
    _write(dart_root / "README.md", "Home Story Dart API fixture.\n")
    _write(
        dart_root / "lib" / "aware_home_story_api.dart",
        "library aware_home_story_api;\n",
    )


def _write_existing_runtime_graph_target_api_workspace(workspace_root: Path) -> Path:
    api_toml_path = workspace_root / "apis" / "focus" / "aware.api.toml"
    _write(
        api_toml_path,
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "focus-api"',
                'fqn_prefix = "aware_focus_api"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
            ]
        )
        + "\n",
    )
    _write(
        api_toml_path.parent / "bindings" / "focus.apis.aware",
        "\n".join(
            [
                "api focus {",
                "    graph aware_focus {",
                "        projection aware_focus.FocusScope {",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
    )
    ontology_root = workspace_root / "modules" / "focus" / "structure" / "ontology"
    _write(
        ontology_root / "aware.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "focus-ontology"',
                'fqn_prefix = "aware_focus"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_focus"',
                "",
            ]
        )
        + "\n",
    )
    _write(
        ontology_root / "aware" / "focus" / "focus_scope.aware",
        "\n".join(
            [
                "class FocusScope {",
                "    key String key",
                "}",
                "",
            ]
        ),
    )
    return api_toml_path


def _write_home_ontology_fixture(
    *, workspace_root: Path, include_projection: bool = False
) -> None:
    package_root = workspace_root / "modules" / "home" / "structure" / "ontology"
    _write(
        package_root / "aware.toml",
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
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
            ]
        )
        + "\n",
    )
    _write(
        package_root / "aware" / "home" / "door.aware",
        "\n".join(
            [
                "class Door {",
                "    label String key",
                "",
                "    fn lock(",
                "        force Bool = false",
                "    ) -> Bool {",
                '        """Lock this door."""',
                "    }",
                "}",
                "",
            ]
        ),
    )
    if include_projection:
        _write(
            package_root / "aware" / "home" / "home.aware",
            "\n".join(
                [
                    "class Home {",
                    "    doors Door[]",
                    "}",
                    "",
                ]
            ),
        )
        _write(
            package_root / "aware" / "home_projection.aware",
            "\n".join(
                [
                    "projection Home is_branchable {",
                    "    root home.Home",
                    "",
                    "    home.Home::doors",
                    "}",
                    "",
                ]
            ),
        )
    write_ontology_dependency_runtime_artifacts(
        package_root=package_root,
        package_name="home-ontology",
        fqn_prefix="aware_home",
        class_refs=(
            ("aware_home.home.Door", "aware_home.home.Home")
            if include_projection
            else ("aware_home.home.Door",)
        ),
        projection_names=("Home",) if include_projection else (),
    )


def _write_api_type_package_fixture(
    *,
    workspace_root: Path,
    include_projection_binding: bool = False,
) -> None:
    package_root = workspace_root / "apis" / "types" / "home"
    aware_toml_lines = [
        "aware = 1",
        "",
        "[package]",
        'package_name = "home-api"',
        'fqn_prefix = "aware_home_api"',
        'kind = "api"',
        "",
        "[build]",
        'environment_slug = "aware_home_api"',
        'sources_dir = "aware"',
        'include_paths = ["**/*.aware"]',
    ]
    if include_projection_binding:
        aware_toml_lines.extend(
            [
                "",
                "[[dependencies]]",
                'package_name = "home-ontology"',
            ]
        )
    _write(
        package_root / "aware.toml",
        "\n".join(aware_toml_lines) + "\n",
    )
    _write(
        package_root / "aware" / "door" / "endpoints.aware",
        "\n".join(
            [
                "class LockDoor {",
                "    label String",
                "}",
                "",
            ]
        ),
    )
    if include_projection_binding:
        _write(
            package_root / "aware" / "door" / "keys.aware",
            "\n".join(
                [
                    "class DoorDevice {",
                    "    door_label String",
                    "}",
                    "",
                ]
            ),
        )
        _write(
            package_root / "aware" / "bindings.aware",
            "\n".join(
                [
                    "binding aware_home_api aware_home {",
                    "    map door_by_label door.DoorDevice home.Door.label {",
                    "        template {",
                    '            "{door_label}"',
                    "        }",
                    "    }",
                    "}",
                    "",
                ]
            ),
        )
    write_python_models_manifest_for_refs(
        package_root=package_root,
        class_refs=(
            (
                "aware_home_api.door.LockDoor",
                "aware_home_api.door.DoorDevice",
            )
            if include_projection_binding
            else ("aware_home_api.door.LockDoor",)
        ),
    )


def _write_environment_module_fixture(*, workspace_root: Path) -> None:
    module_root = workspace_root / "modules" / "demo"
    _write(
        module_root / "aware.module.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[module]",
                'stable_ids_ownership = "compiler"',
                'stable_ids_parity_policy = "error"',
                "",
                "[[packages]]",
                'aware_toml_path = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
    )
    _write(
        module_root / "structure" / "ontology" / "aware.toml",
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
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
            ]
        )
        + "\n",
    )
    _write(
        module_root / "structure" / "ontology" / "aware" / "demo" / "demo_root.aware",
        "class DemoRoot {\n    name String\n}\n",
    )
    _write(
        workspace_root / "aware.environment.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[environment]",
                'handle = "kernel"',
                'title = "Aware Kernel"',
                'canonical_language = "aware"',
                'modules = ["demo"]',
            ]
        )
        + "\n",
    )


async def _hydrate_projection_session(
    *,
    index,
    branch_id,
    projection_hash: str,
) -> Session:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id") is not None
    assert head.get("object_instance_graph_id") is not None
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )


def test_resolve_api_package_materialization_spec_rejects_multiple_api_declarations(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "api_package_spec_multiple"
    workspace_root.mkdir(parents=True, exist_ok=True)
    api_toml_path = _write_api_package_fixture(
        workspace_root=workspace_root, extra_api=True
    )

    from aware_api_runtime.compile_materialization import (
        resolve_api_package_materialization_spec,
    )  # noqa: WPS433

    with pytest.raises(RuntimeError, match="exactly one canonical `api` declaration"):
        _ = resolve_api_package_materialization_spec(
            api_toml_path=api_toml_path,
            workspace_root=workspace_root,
        )


def test_api_language_code_package_targets_skip_missing_declared_dart_root(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "api_package_targets_missing_dart"
    workspace_root.mkdir(parents=True, exist_ok=True)
    api_toml_path = _write_api_package_fixture(
        workspace_root=workspace_root,
        include_dart_package=False,
    )

    from aware_api_runtime.compile_materialization.service import (  # noqa: WPS433
        _api_language_code_package_targets,
    )
    from aware_api_runtime.workspace import APIWorkspace  # noqa: WPS433

    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=workspace_root,
    ).build_snapshot()
    targets = _api_language_code_package_targets(
        snapshot=snapshot,
        workspace_root=workspace_root,
    )

    assert [target.output_key for target in targets] == [
        "python.public_package",
        "python.service_protocol_package",
    ]
    assert not (workspace_root / "apis" / "home" / "dart").exists()


def test_api_language_code_package_targets_skip_empty_declared_dart_package(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "api_package_targets_empty_dart"
    workspace_root.mkdir(parents=True, exist_ok=True)
    api_toml_path = _write_api_package_fixture(
        workspace_root=workspace_root,
        include_dart_package=False,
    )
    empty_dart_package_root = (
        workspace_root / "apis" / "home" / "dart" / "public" / "aware_home_story_api"
    )
    (empty_dart_package_root / "lib" / "default").mkdir(parents=True)

    from aware_api_runtime.compile_materialization.service import (  # noqa: WPS433
        _api_language_code_package_targets,
    )
    from aware_api_runtime.workspace import APIWorkspace  # noqa: WPS433

    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=workspace_root,
    ).build_snapshot()
    targets = _api_language_code_package_targets(
        snapshot=snapshot,
        workspace_root=workspace_root,
    )

    assert [target.output_key for target in targets] == [
        "python.public_package",
        "python.service_protocol_package",
    ]


def test_api_language_code_package_targets_reject_nonempty_dart_package_without_pubspec(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "api_package_targets_partial_dart"
    workspace_root.mkdir(parents=True, exist_ok=True)
    api_toml_path = _write_api_package_fixture(
        workspace_root=workspace_root,
        include_dart_package=False,
    )
    partial_dart_package_root = (
        workspace_root / "apis" / "home" / "dart" / "public" / "aware_home_story_api"
    )
    (partial_dart_package_root / "lib").mkdir(parents=True)
    (partial_dart_package_root / "lib" / "client.dart").write_text(
        "class HomeStoryApiClient {}\n",
        encoding="utf-8",
    )

    from aware_api_runtime.compile_materialization.service import (  # noqa: WPS433
        _api_language_code_package_targets,
    )
    from aware_api_runtime.workspace import APIWorkspace  # noqa: WPS433

    snapshot = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=workspace_root,
    ).build_snapshot()

    with pytest.raises(
        FileNotFoundError,
        match="targets.dart.public_package.pubspec_yaml must resolve to a file",
    ):
        _api_language_code_package_targets(
            snapshot=snapshot,
            workspace_root=workspace_root,
        )


@pytest.mark.asyncio
async def test_materialize_api_package_from_manifest_commits_canonical_package_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "api_package_materialization"
    workspace_root.mkdir(parents=True, exist_ok=True)
    api_toml_path = _write_api_package_fixture(workspace_root=workspace_root)
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_api_package_materialization", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        from aware_api_runtime.compile_materialization import (  # noqa: WPS433
            materialize_api_package_from_manifest,
            resolve_api_package_materialization_spec,
        )

        spec = await asyncio.to_thread(
            resolve_api_package_materialization_spec,
            api_toml_path=api_toml_path,
            workspace_root=workspace_root,
        )
        assert spec.package_name == "home-story-api"
        assert spec.api_name == "home_devices"
        assert spec.api_source_path == "apis/bindings/home_devices.apis.aware"
        assert spec.source_files == ("apis/bindings/home_devices.apis.aware",)
        assert spec.api_endpoint_catalog == {
            "home_devices": {"lock_door": ("lock_door",)}
        }

        branch_id = uuid4()

        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Api",
        )
        api_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ApiPackage",
        )
        assert api_projection_hash
        assert api_package_projection_hash
        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )
        assert code_package_projection_hash

        from aware_meta.materialization import post_step_executor  # noqa: WPS433

        dart_home = tmp_path / "dart-home"
        dart_pub_cache = tmp_path / "pub-cache"
        fake_dart = tmp_path / "dart-sdk" / "bin" / "dart"
        observed_dart_post_steps: list[dict[str, object]] = []

        def _fake_dart_post_step_run(
            *args: object,
            **kwargs: object,
        ) -> SimpleNamespace:
            observed_dart_post_steps.append({"args": args, "kwargs": kwargs})
            cwd = kwargs.get("cwd")
            package_root = Path(str(cwd)) if cwd is not None else None
            lib_root = package_root / "lib" if package_root is not None else None
            if lib_root is not None and lib_root.is_dir():
                for source in sorted(
                    lib_root.rglob("*.dart"), key=lambda path: path.as_posix()
                ):
                    if source.name.endswith((".freezed.dart", ".g.dart")):
                        continue
                    for line in source.read_text(encoding="utf-8").splitlines():
                        stripped = line.strip()
                        if not stripped.startswith("part "):
                            continue
                        tokens = stripped.split("'")
                        if len(tokens) < 2:
                            continue
                        part_path = source.parent / tokens[1]
                        part_path.write_text(
                            f"part of '{source.name}';\n",
                            encoding="utf-8",
                        )
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        monkeypatch.setattr(
            post_step_executor.subprocess, "run", _fake_dart_post_step_run
        )

        result = await materialize_api_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            dependency_repo_roots=(repo_root,),
            post_step_tool_env_by_tool_id={
                "dart.pub_get": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.build_runner": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.format": {
                    "HOME": str(dart_home),
                },
            },
            post_step_executable_overrides_by_tool_id={
                "dart.pub_get": {"dart": str(fake_dart)},
                "dart.build_runner": {"dart": str(fake_dart)},
                "dart.format": {"dart": str(fake_dart)},
            },
        )

        assert observed_dart_post_steps
        assert result.api_toml_path == api_toml_path.resolve()
        assert result.workspace_root == workspace_root.resolve()
        assert result.manifest_spec.api.package_name == "home-story-api"
        assert result.api.name == "home_devices"
        assert result.api_package.name == "home-story-api"
        assert result.api_package.api_id == result.api.id
        assert (
            result.api_package.api_object_instance_graph_commit_id
            == result.api_object_instance_graph_commit_id
        )
        assert result.api_head_commit_id is not None
        assert result.api_package.fqn_prefix == "aware_home_story_api"
        assert result.api_package.version_number == 5
        assert result.api_package.title == "Home Story API"
        assert result.api_package.description == "Home story API semantic package"
        assert result.api_package.aware_api_version == 1
        assert result.api_package.manifest_relative_path == "aware.api.toml"
        assert result.api_package.package_root == "."
        assert result.api_package.sources_root == "apis/bindings"
        assert list(result.api_package.include_paths) == ["**/*.aware"]
        assert list(result.api_package.exclude_paths) == ["**/*.draft.aware"]
        assert result.api_package.force_fresh_scan is True
        assert result.api_package.compilation_mode == "api_ontology"
        assert list(result.api_package.dependencies) == [
            {"package_name": "home-api", "version_number": 2},
            {"package_name": "home-ontology", "version_number": 3},
        ]
        assert dict(result.api_package.targets) == {
            "python": {
                "root_dir": "apis/home/python",
                "public_package": {
                    "package_dir": "aware_home_story_api",
                    "root_dir": "apis/home/python/public",
                },
                "service_protocol": {
                    "package_dir": "aware_home_story_api_service_protocol",
                    "root_dir": "apis/home/python/service_protocol",
                },
            },
            "dart": {
                "root_dir": "apis/home/dart",
                "public_package": {
                    "package_dir": "aware_home_story_api",
                    "root_dir": "apis/home/dart/public",
                },
            },
        }
        assert result.api_source_path == "apis/bindings/home_devices.apis.aware"
        assert result.source_files == ("apis/bindings/home_devices.apis.aware",)
        assert result.phase_timings_s["total"] >= 0.0
        assert result.phase_timings_s["resolve_api_package_materialization_spec"] >= 0.0
        assert result.phase_timings_s["hydrate_api_from_head"] >= 0.0
        assert (
            result.phase_timings_s["api_graph.snapshot:home_devices.commit_to_lane"]
            >= 0.0
        )
        assert "api_graph.plan:home_devices.create_api" not in result.phase_timings_s
        assert result.phase_timings_s["commit_code_package_text_snapshot"] >= 0.0
        assert "upsert_code_package_sources" not in result.phase_timings_s
        assert result.phase_timings_s["commit_api_package_manifest_snapshot"] >= 0.0
        assert "build_api_package_manifest_truth" not in result.phase_timings_s
        assert result.api_endpoint_catalog == {
            "home_devices": {"lock_door": ("lock_door",)}
        }
        api_source_code_package_config_id = source_code_package_config_ref(
            manifest_kind="aware_api_toml",
            surface="api",
        ).config_id
        python_code_package_config_id = source_code_package_config_ref(
            manifest_kind="pyproject_toml",
            surface="api",
        ).config_id
        dart_code_package_config_id = source_code_package_config_ref(
            manifest_kind="pubspec_yaml",
            surface="api",
        ).config_id
        assert result.source_code_package_id == stable_code_package_id(
            code_package_config_id=api_source_code_package_config_id,
            package_name="home-story-api",
            language=CodeLanguage.aware.value,
        )
        assert result.language_code_package_ids == (
            stable_code_package_id(
                code_package_config_id=python_code_package_config_id,
                package_name="aware_home_story_api",
                language=CodeLanguage.python.value,
            ),
            stable_code_package_id(
                code_package_config_id=python_code_package_config_id,
                package_name="aware_home_story_protocol",
                language=CodeLanguage.python.value,
            ),
            stable_code_package_id(
                code_package_config_id=dart_code_package_config_id,
                package_name="aware_home_story_api",
                language=CodeLanguage.dart.value,
            ),
        )
        assert [item["output_key"] for item in result.language_code_package_refs] == [
            "python.public_package",
            "python.service_protocol_package",
            "dart.public_package",
        ]
        assert [item["package_root"] for item in result.language_code_package_refs] == [
            "apis/home/python/public",
            "apis/home/python/service_protocol",
            "apis/home/dart/public",
        ]
        assert result.source_object_instance_graph_commit_id is not None
        assert result.api_commit_id is not None
        assert result.api_head_commit_id is not None
        assert result.package_commit_id is not None
        assert result.package_head_commit_id is not None
        assert not (
            workspace_root
            / "apis"
            / "types"
            / "home"
            / ".aware"
            / "environment"
            / "runtime"
            / "environment.manifest.json"
        ).exists()
        assert not (
            workspace_root
            / "modules"
            / "home"
            / "structure"
            / "ontology"
            / ".aware"
            / "environment"
            / "runtime"
            / "environment.manifest.json"
        ).exists()

        api_session = await _hydrate_projection_session(
            index=index,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        capabilities = [
            obj
            for obj in api_session.imap_all_objects()
            if isinstance(obj, ApiCapability)
        ]
        endpoints = [
            obj
            for obj in api_session.imap_all_objects()
            if isinstance(obj, ApiCapabilityEndpoint)
        ]
        assert any((cap.name or "").strip() == "lock_door" for cap in capabilities)
        assert any(
            (endpoint.name or "").strip() == "lock_door" for endpoint in endpoints
        )
        api_package_session = await _hydrate_projection_session(
            index=index,
            branch_id=branch_id,
            projection_hash=api_package_projection_hash,
        )
        language_packages = [
            obj
            for obj in api_package_session.imap_all_objects()
            if isinstance(obj, ApiPackageLanguagePackage)
        ]
        assert sorted(item.output_key for item in language_packages) == [
            "dart.public_package",
            "python.public_package",
            "python.service_protocol_package",
        ]
        assert {item.code_package_id for item in language_packages} == set(
            result.language_code_package_ids
        )

        code_package_session = await _hydrate_projection_session(
            index=index,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
        )
        code_packages = [
            obj
            for obj in code_package_session.imap_all_objects()
            if isinstance(obj, CodePackage)
        ]
        assert len(code_packages) == 1
        code_package = code_packages[0]
        assert code_package.id == result.source_code_package_id
        assert code_package.package_name == "home-story-api"
        assert code_package.language == CodeLanguage.aware
        assert code_package.surface == "api"
        assert code_package.manifest_relative_path == "aware.api.toml"
        assert code_package.package_root == "."
        assert code_package.sources_root == "apis/bindings"
        for language_ref in result.language_code_package_refs:
            language_code_package_session = await _hydrate_projection_session(
                index=index,
                branch_id=language_ref["branch_id"],
                projection_hash=code_package_projection_hash,
            )
            language_code_packages = [
                obj
                for obj in language_code_package_session.imap_all_objects()
                if isinstance(obj, CodePackage)
            ]
            assert len(language_code_packages) == 1
            language_code_package = language_code_packages[0]
            assert language_code_package.id == language_ref["code_package_id"]
            assert language_code_package.package_name == language_ref["package_name"]
            assert (
                language_code_package.manifest_relative_path
                == language_ref["manifest_relative_path"]
            )
            assert language_code_package.package_root == language_ref["package_root"]
            assert language_code_package.surface == "api"

        rerun = await materialize_api_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            dependency_repo_roots=(repo_root,),
            post_step_tool_env_by_tool_id={
                "dart.pub_get": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.build_runner": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.format": {
                    "HOME": str(dart_home),
                },
            },
            post_step_executable_overrides_by_tool_id={
                "dart.pub_get": {"dart": str(fake_dart)},
                "dart.build_runner": {"dart": str(fake_dart)},
                "dart.format": {"dart": str(fake_dart)},
            },
        )
        assert rerun.api.id == result.api.id
        assert rerun.api_package.id == result.api_package.id
        assert (
            rerun.api_package.api_object_instance_graph_commit_id
            == rerun.api_object_instance_graph_commit_id
        )
        assert rerun.api_head_commit_id == result.api_head_commit_id
        assert rerun.source_code_package_id == result.source_code_package_id
        assert rerun.language_code_package_ids == result.language_code_package_ids
        assert [
            item["code_package_id"] for item in rerun.language_code_package_refs
        ] == [item["code_package_id"] for item in result.language_code_package_refs]
        assert rerun.phase_timings_s["total"] >= 0.0
        assert rerun.phase_timings_s["hydrate_api_from_head"] >= 0.0
        assert rerun.phase_timings_s["check_api_package_manifest_truth"] >= 0.0
        assert (
            rerun.phase_timings_s["sync_api_package_manifest_truth_skipped_current"]
            == 0.0
        )
        assert "sync_api_package_manifest_truth" not in rerun.phase_timings_s
        assert rerun.api_endpoint_catalog == result.api_endpoint_catalog
        assert rerun.package_commit_id is None
        assert rerun.package_head_commit_id == result.package_head_commit_id

        import aware_api_runtime.compile_materialization.service as package_service  # noqa: WPS433

        original_object_instance_graph_commit_id = (
            package_service._object_instance_graph_commit_id_from_domain_commit
        )
        churned_api_object_instance_graph_commit_id = uuid4()

        async def _churn_api_object_instance_graph_commit_id(**kwargs: object):
            if kwargs["projection_hash"] == api_projection_hash:
                return churned_api_object_instance_graph_commit_id
            return await original_object_instance_graph_commit_id(**kwargs)

        equivalence_checks: list[tuple[object, object]] = []

        async def _api_roots_are_semantically_equivalent(**kwargs: object) -> bool:
            equivalence_checks.append(
                (
                    kwargs["left_object_instance_graph_commit_id"],
                    kwargs["right_object_instance_graph_commit_id"],
                )
            )
            return True

        monkeypatch.setattr(
            package_service,
            "_object_instance_graph_commit_id_from_domain_commit",
            _churn_api_object_instance_graph_commit_id,
        )
        monkeypatch.setattr(
            package_service,
            "_api_roots_are_semantically_equivalent",
            _api_roots_are_semantically_equivalent,
        )

        equivalent_rerun = await materialize_api_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            dependency_repo_roots=(repo_root,),
            post_step_tool_env_by_tool_id={
                "dart.pub_get": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.build_runner": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.format": {
                    "HOME": str(dart_home),
                },
            },
            post_step_executable_overrides_by_tool_id={
                "dart.pub_get": {"dart": str(fake_dart)},
                "dart.build_runner": {"dart": str(fake_dart)},
                "dart.format": {"dart": str(fake_dart)},
            },
        )
        assert equivalent_rerun.api.id == result.api.id
        assert equivalent_rerun.api_package.id == result.api_package.id
        assert (
            equivalent_rerun.api_object_instance_graph_commit_id
            == churned_api_object_instance_graph_commit_id
        )
        assert (
            equivalent_rerun.api_package.api_object_instance_graph_commit_id
            == result.api_object_instance_graph_commit_id
        )
        assert equivalence_checks == [
            (
                result.api_object_instance_graph_commit_id,
                churned_api_object_instance_graph_commit_id,
            )
        ]
        assert (
            equivalent_rerun.phase_timings_s[
                "sync_api_package_manifest_truth_skipped_equivalent_api_root"
            ]
            == 0.0
        )
        assert "sync_api_package_manifest_truth" not in equivalent_rerun.phase_timings_s
        assert equivalent_rerun.package_commit_id is None
        assert equivalent_rerun.package_head_commit_id == result.package_head_commit_id

        unresolved_commit_id_only_checks: list[tuple[object, object]] = []

        async def _api_roots_are_unresolved(
            **kwargs: object,
        ) -> bool | None:
            unresolved_commit_id_only_checks.append(
                (
                    kwargs["left_object_instance_graph_commit_id"],
                    kwargs["right_object_instance_graph_commit_id"],
                )
            )
            return None

        monkeypatch.setattr(
            package_service,
            "_api_roots_are_semantically_equivalent",
            _api_roots_are_unresolved,
        )

        unresolved_commit_id_only_rerun = await materialize_api_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            dependency_repo_roots=(repo_root,),
            post_step_tool_env_by_tool_id={
                "dart.pub_get": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.build_runner": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.format": {
                    "HOME": str(dart_home),
                },
            },
            post_step_executable_overrides_by_tool_id={
                "dart.pub_get": {"dart": str(fake_dart)},
                "dart.build_runner": {"dart": str(fake_dart)},
                "dart.format": {"dart": str(fake_dart)},
            },
        )
        assert unresolved_commit_id_only_rerun.api.id == result.api.id
        assert unresolved_commit_id_only_rerun.api_package.id == result.api_package.id
        assert (
            unresolved_commit_id_only_rerun.api_object_instance_graph_commit_id
            == churned_api_object_instance_graph_commit_id
        )
        assert (
            unresolved_commit_id_only_rerun.api_package.api_object_instance_graph_commit_id
            == result.api_object_instance_graph_commit_id
        )
        assert unresolved_commit_id_only_checks == [
            (
                result.api_object_instance_graph_commit_id,
                churned_api_object_instance_graph_commit_id,
            )
        ]
        assert (
            unresolved_commit_id_only_rerun.phase_timings_s[
                "sync_api_package_manifest_truth_skipped_unresolved_api_commit_id_only"
            ]
            == 0.0
        )
        assert (
            "sync_api_package_manifest_truth"
            not in unresolved_commit_id_only_rerun.phase_timings_s
        )
        assert unresolved_commit_id_only_rerun.package_commit_id is None
        assert (
            unresolved_commit_id_only_rerun.package_head_commit_id
            == result.package_head_commit_id
        )

        non_equivalent_checks: list[tuple[object, object]] = []

        async def _api_roots_are_not_semantically_equivalent(
            **kwargs: object,
        ) -> bool | None:
            non_equivalent_checks.append(
                (
                    kwargs["left_object_instance_graph_commit_id"],
                    kwargs["right_object_instance_graph_commit_id"],
                )
            )
            return False

        monkeypatch.setattr(
            package_service,
            "_api_roots_are_semantically_equivalent",
            _api_roots_are_not_semantically_equivalent,
        )

        non_equivalent_rerun = await materialize_api_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            dependency_repo_roots=(repo_root,),
            post_step_tool_env_by_tool_id={
                "dart.pub_get": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.build_runner": {
                    "HOME": str(dart_home),
                    "PUB_CACHE": str(dart_pub_cache),
                },
                "dart.format": {
                    "HOME": str(dart_home),
                },
            },
            post_step_executable_overrides_by_tool_id={
                "dart.pub_get": {"dart": str(fake_dart)},
                "dart.build_runner": {"dart": str(fake_dart)},
                "dart.format": {"dart": str(fake_dart)},
            },
        )
        assert non_equivalent_rerun.api.id == result.api.id
        assert non_equivalent_rerun.api_package.id == result.api_package.id
        assert (
            non_equivalent_rerun.api_object_instance_graph_commit_id
            == churned_api_object_instance_graph_commit_id
        )
        assert (
            non_equivalent_rerun.api_package.api_object_instance_graph_commit_id
            == churned_api_object_instance_graph_commit_id
        )
        assert non_equivalent_checks == [
            (
                result.api_object_instance_graph_commit_id,
                churned_api_object_instance_graph_commit_id,
            )
        ]
        assert (
            non_equivalent_rerun.phase_timings_s["commit_api_package_manifest_snapshot"]
            >= 0.0
        )
        assert (
            "sync_api_package_manifest_truth"
            not in non_equivalent_rerun.phase_timings_s
        )
        assert non_equivalent_rerun.package_commit_id is not None
        assert (
            non_equivalent_rerun.package_head_commit_id != result.package_head_commit_id
        )


@pytest.mark.asyncio
async def test_materialize_api_package_from_manifest_commits_code_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "api_package_materialization_batch_upserts"
    workspace_root.mkdir(parents=True, exist_ok=True)
    api_toml_path = _write_api_package_fixture(workspace_root=workspace_root)

    async def _unexpected_single_upsert(
        self: CodePackage,
        relative_path: str,
        content_text: str,
        language: CodeLanguage | None = None,
    ) -> object:
        _ = (self, relative_path, content_text, language)
        raise AssertionError("single-file code upsert path should not run")

    async def _unexpected_batch_upsert(
        self: CodePackage,
        relative_paths: list[str],
        content_texts: list[str],
        language: CodeLanguage | None = None,
    ) -> None:
        _ = (self, relative_paths, content_texts, language)
        raise AssertionError("runtime code upsert path should not run")

    monkeypatch.setattr(CodePackage, "upsert_code_from_text", _unexpected_single_upsert)
    monkeypatch.setattr(CodePackage, "upsert_codes_from_text", _unexpected_batch_upsert)
    post_step_tool_env_by_tool_id, post_step_executable_overrides_by_tool_id = (
        _install_fake_dart_post_steps(tmp_path=tmp_path, monkeypatch=monkeypatch)
    )
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_api_package_materialization_batch_upserts",
        persistence_backend="fs",
    ) as aware_root:
        from aware_api_runtime.compile_materialization import (
            materialize_api_package_from_manifest,
        )  # noqa: WPS433

        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        result = await materialize_api_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            dependency_repo_roots=(repo_root,),
            post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
            post_step_executable_overrides_by_tool_id=(
                post_step_executable_overrides_by_tool_id
            ),
        )

        assert result.api.name == "home_devices"
        assert result.source_code_package_id is not None
        assert result.source_object_instance_graph_commit_id is not None
        assert result.phase_timings_s["commit_code_package_text_snapshot"] >= 0.0
        assert (
            "invoke_code_package_upsert_codes_from_text" not in result.phase_timings_s
        )


@pytest.mark.asyncio
async def test_materialize_api_package_from_manifest_allows_shared_branch_with_unrelated_environment_code_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "api_package_materialization_existing_code_package"
    workspace_root.mkdir(parents=True, exist_ok=True)
    _write_environment_module_fixture(workspace_root=workspace_root)
    api_toml_path = _write_api_package_fixture(workspace_root=workspace_root)
    post_step_tool_env_by_tool_id, post_step_executable_overrides_by_tool_id = (
        _install_fake_dart_post_steps(tmp_path=tmp_path, monkeypatch=monkeypatch)
    )
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_api_package_materialization_existing_code_package",
        persistence_backend="fs",
    ) as aware_root:
        from aware_api_runtime.compile_materialization import (
            materialize_api_package_from_manifest,
        )  # noqa: WPS433

        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        branch_id = uuid4()

        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )
        unrelated_code_package_config_id = source_code_package_config_ref(
            manifest_kind="aware_toml",
            surface="structure",
        ).config_id
        unrelated_code_package_snapshot = await commit_code_package_text_snapshot(
            index=index,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=unrelated_code_package_config_id,
            package_name="demo-ontology",
            language=CodeLanguage.aware,
            surface="structure",
            manifest_kind="aware_toml",
            manifest_relative_path="modules/demo/structure/ontology/aware.toml",
            package_root="modules/demo/structure/ontology",
            sources_root="aware",
            fqn_prefix="aware_demo",
            source_texts_by_relative_path={
                "aware/demo/demo_root.aware": "class DemoRoot {\n    name String\n}\n",
            },
        )

        expected_api_code_package_config_id = source_code_package_config_ref(
            manifest_kind="aware_api_toml",
            surface="api",
        ).config_id
        expected_api_code_package_id = stable_code_package_id(
            code_package_config_id=expected_api_code_package_config_id,
            package_name="home-story-api",
            language=CodeLanguage.aware.value,
        )
        assert unrelated_code_package_snapshot.code_package.id != (
            expected_api_code_package_id
        )

        result = await materialize_api_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            dependency_repo_roots=(repo_root,),
            post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
            post_step_executable_overrides_by_tool_id=(
                post_step_executable_overrides_by_tool_id
            ),
        )

        assert result.source_code_package_id == expected_api_code_package_id
        assert result.source_code_package_id != (
            unrelated_code_package_snapshot.code_package.id
        )
        assert result.api_package.source_code_package_id == expected_api_code_package_id


@pytest.mark.asyncio
async def test_materialize_api_package_from_manifest_uses_authored_projection_fallback_without_runtime_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "api_package_materialization_projection_fallback"
    workspace_root.mkdir(parents=True, exist_ok=True)
    api_toml_path = _write_api_package_fixture(
        workspace_root=workspace_root,
        include_projection_binding=True,
    )
    post_step_tool_env_by_tool_id, post_step_executable_overrides_by_tool_id = (
        _install_fake_dart_post_steps(tmp_path=tmp_path, monkeypatch=monkeypatch)
    )

    monkeypatch.setattr(
        "aware_api_runtime.dependencies.runtime_resolution._build_runtime_dependency_package",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("dependency runtime build should not run")
        ),
    )
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_api_package_materialization_projection_fallback",
        persistence_backend="fs",
    ) as aware_root:
        from aware_api_runtime.compile_materialization import (
            materialize_api_package_from_manifest,
        )  # noqa: WPS433

        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        result = await materialize_api_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            api_toml_path=api_toml_path,
            dependency_repo_roots=(repo_root,),
            post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
            post_step_executable_overrides_by_tool_id=(
                post_step_executable_overrides_by_tool_id
            ),
        )

        assert result.api.name == "home_devices"
        assert result.api_package.name == "home-story-api"
        assert not (
            workspace_root
            / "modules"
            / "home"
            / "structure"
            / "ontology"
            / ".aware"
            / "environment"
            / "runtime"
            / "environment.manifest.json"
        ).exists()
        assert not (
            workspace_root
            / "apis"
            / "types"
            / "home"
            / ".aware"
            / "environment"
            / "runtime"
            / "environment.manifest.json"
        ).exists()
