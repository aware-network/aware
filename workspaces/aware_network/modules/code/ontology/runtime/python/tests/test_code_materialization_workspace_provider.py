from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_code.handlers._generated import meta_handlers as code_meta_handlers
from aware_code.materialization.workspace_provider import materialize, materialize_delta
from aware_code.semantic_contract import AWARE_CODE_SEMANTIC_CONTRACT
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_CAPABILITY,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
    SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY,
    SemanticPackageMaterializationRequest,
)
from aware_meta.handlers._generated import meta_handlers as meta_meta_handlers
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from _code_runtime_test_paths import CODE_PACKAGE_MANIFEST_PATHS, REPO_ROOT


def _code_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return CODE_PACKAGE_MANIFEST_PATHS


def _build_code_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_code_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            code_meta_handlers,
            meta_meta_handlers,
        ),
        bootstrap_modules=(
            code_meta_handlers,
            meta_meta_handlers,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.asyncio
async def test_code_materialization_provider_commits_selected_raw_package(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    workspace_root = tmp_path / "workspace"
    _write(
        workspace_root / "libs" / "demo" / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "aware-demo-lib"',
                'version = "0.1.0"',
                "",
            ]
        ),
    )
    _write(
        workspace_root / "libs" / "demo" / "aware_demo_lib" / "__init__.py",
        'VALUE = "demo"\n',
    )
    _write(
        workspace_root / "libs" / "demo" / "aware_demo_lib" / "client.py",
        "def value() -> str:\n    return VALUE\n",
    )
    _write(
        workspace_root / "libs" / "demo" / "dist" / "ignored.py",
        "SHOULD_NOT_APPEAR = True\n",
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index

        result = await materialize(
            SemanticPackageMaterializationRequest(
                runtime=runtime,
                index=idx,
                actor_id=None,
                branch_id=uuid4(),
                workspace_root=workspace_root,
                manifest_path=Path("libs/demo/pyproject.toml"),
            )
        )

    bundle = result.bundle_packages[0]
    assert result.details["package_name"] == "aware-demo-lib"
    assert result.details["manifest_kind"] == "pyproject_toml"
    assert result.details["path_count"] == 3
    assert result.commit_id is not None
    assert result.head_commit_id is not None
    assert bundle.package_key == "aware-demo-lib"
    assert bundle.semantic_projection_name == "CodePackage"
    assert bundle.semantic_root_kind == "code_package"
    assert bundle.source_code_package_id == bundle.semantic_package_id


def test_code_materialization_contract_declares_functional_delta_adapter() -> None:
    (participation,) = AWARE_CODE_SEMANTIC_CONTRACT.capability_participation_for(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
    )
    adapter = participation.metadata[SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY]

    assert adapter["callable_module"] == "aware_code.materialization.workspace_provider"
    assert adapter["callable_name"] == "materialize_delta"
    assert adapter[SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY] is True
    readiness = adapter[SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY]
    assert readiness["status"] == "ready"
    assert readiness["workspace_delta_first_ready_operation_count"] == 1

    (runtime_context,) = (
        AWARE_CODE_SEMANTIC_CONTRACT.materialization_runtime_context_for(
            semantic_owner="aware_code.provider",
        )
    )
    assert (
        runtime_context.callable_module
        == "aware_code.materialization.runtime_context"
    )
    assert runtime_context.callable_name == (
        "build_code_workspace_materialization_runtime_context"
    )
    assert runtime_context.required is True


@pytest.mark.asyncio
async def test_code_materialization_delta_provider_commits_text_snapshot(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    workspace_root = tmp_path / "workspace"
    _write(
        workspace_root / "libs" / "demo" / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "aware-demo-lib"',
                'version = "0.1.0"',
                "",
            ]
        ),
    )
    _write(
        workspace_root / "libs" / "demo" / "aware_demo_lib" / "__init__.py",
        'VALUE = "demo"\n',
    )
    _write(
        workspace_root / "libs" / "demo" / "aware_demo_lib" / "client.py",
        "def value() -> str:\n    return VALUE\n",
    )
    branch_id = uuid4()

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        assert runtime.context is not None
        idx = runtime.context.index

        result = await materialize_delta(
            request=SimpleNamespace(
                package=SimpleNamespace(
                    package_name="aware-demo-lib",
                    workspace_manifest_kind="code",
                    manifest_path="libs/demo/pyproject.toml",
                    source_code_package_id=None,
                ),
                semantic_contract=SimpleNamespace(
                    module="aware_code.semantic_contract",
                    provider_key="aware_code",
                    role="aware_code.provider",
                    name="aware.semantic_provider",
                ),
                current_delta_fingerprint="sha256:test",
                code_package_delta=CodePackageDelta(
                    package_name="aware-demo-lib",
                    package_root="libs/demo",
                    sources_root="libs/demo",
                    manifest_relative_path="libs/demo/pyproject.toml",
                    authority_kind="aware_dev.materialize.local_fs",
                    paths=(
                        CodePackageDeltaPath(
                            relative_path="aware_demo_lib/client.py",
                            kind=CodePackageDeltaKind.update,
                            content_text=(
                                "def value() -> str:\n"
                                "    return VALUE + '-updated'\n"
                            ),
                            language=CodeLanguage.python,
                        ),
                    ),
                ),
                previous_materialization_evidence={},
                baseline_ref=None,
                provider_delta_lane_state=None,
                runtime=runtime,
                index=idx,
                actor_id=None,
                branch_id=branch_id,
                workspace_root=workspace_root,
                execute_provider_delta_materialization=True,
            )
        )

    bundle_package = result["bundle_package"]
    details = result["details"]
    operation_execution = details["provider_delta_operation_execution"]
    semantic_execution = operation_execution["semantic_function_call_execution"]

    assert result["status"] == "succeeded"
    assert result["applied_semantic_keys"] == ["aware-demo-lib"]
    assert bundle_package["semantic_projection_name"] == "CodePackage"
    assert bundle_package["semantic_root_kind"] == "code_package"
    assert bundle_package["source_code_package_id"] == bundle_package["semantic_package_id"]
    assert bundle_package["semantic_object_instance_graph_commit_id"]
    assert bundle_package["source_object_instance_graph_commit_id"]
    assert details["mode"] == "delta"
    assert details["path_count"] == 3
    assert details["changed_path_count"] == 1
    assert semantic_execution["status"] == "executed"
    assert semantic_execution["status_counts"]["blocked"] == 0
