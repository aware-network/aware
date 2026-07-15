from __future__ import annotations

import ast
from pathlib import Path
import sys
from uuid import uuid4

import pytest

_RUNTIME_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _RUNTIME_ROOT.parents[6]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_ATTENTION_RUNTIME_ROOT_STR = str(_RUNTIME_ROOT)
if _ATTENTION_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _ATTENTION_RUNTIME_ROOT_STR)
_TESTS_ROOT_STR = str(_RUNTIME_ROOT / "tests")
if _TESTS_ROOT_STR not in sys.path:
    sys.path.insert(0, _TESTS_ROOT_STR)

from aware_code.semantic_materialization import (  # noqa: E402
    SemanticPackageMaterializationRequest,
)
from aware_code.types import JsonArray  # noqa: E402
import aware_attention.materialization.workspace_provider as workspace_provider  # noqa: E402
from aware_attention.materialization.workspace_provider import materialize  # noqa: E402
from aware_attention_ontology.stable_ids import (
    stable_attention_package_id,
)  # noqa: E402
from aware_meta.runtime.graph_runtime import (  # noqa: E402
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from test_attention_materialization_service import (  # pyright: ignore[reportMissingImports] # noqa: E402
    _RecordingInvoker,
    _attention_index,
)


class _WorkspaceRuntimeWithoutManifest:
    def __init__(self) -> None:
        self._invoker = _RecordingInvoker()

    @property
    def requests(self) -> list[object]:
        return list(self._invoker.requests)

    async def invoke_function_with_index(self, **kwargs: object) -> object:
        return await self._invoker.invoke_function_with_index(**kwargs)


class _MetaGraphRuntimeWithoutManifest:
    def __init__(self) -> None:
        self.requests: list[MetaGraphInvokeFunctionInput] = []

    async def invoke_function(
        self, request: MetaGraphInvokeFunctionInput
    ) -> MetaGraphCommitReceipt:
        self.requests.append(request)
        return MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            payload={"ok": True},
            error=None,
            logs=(),
            execution_time_ms=1,
            root_object_id=uuid4(),
            graph_hash_pre=request.expected_graph_hash_pre,
            graph_hash_post=f"hash-{len(self.requests)}",
            changes=JsonArray(),
            function_call_id=uuid4(),
            function_call_response_id=uuid4(),
            commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
        )


def _write_control_attention_package(workspace_root: Path) -> Path:
    package_root = workspace_root / "attentions" / "aware_control_shell"
    package_root.mkdir(parents=True, exist_ok=True)
    _ = (package_root / "aware.attention.toml").write_text(
        "\n".join(
            [
                "aware_attention = 1",
                "",
                "[attention]",
                'package_name = "aware-control-shell-attention"',
                'fqn_prefix = "aware_control_shell_attention"',
                'title = "Aware Control Shell"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                'frame_mode = "horizontal"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (package_root / "control_shell.aware").write_text(
        "\n".join(
            [
                "layout control_shell default {",
                "    section identity {",
                '        title "Identity"',
                "        order 0",
                "        flex 1.0",
                "        visible true",
                "    }",
                "",
                "    section capabilities {",
                '        title "Capabilities"',
                "        order 1",
                "        flex 1.2",
                "        visible true",
                "    }",
                "",
                "    section territories {",
                '        title "Territories"',
                "        order 2",
                "        flex 1.0",
                "        visible true",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return package_root / "aware.attention.toml"


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_attention_workspace_provider_uses_meta_runtime_contracts() -> None:
    provider_path = Path(workspace_provider.__file__).resolve()

    assert "aware_runtime" not in _import_roots(provider_path)
    assert "aware_environment_service_dto" not in _import_roots(provider_path)


@pytest.mark.asyncio
async def test_attention_workspace_provider_compiles_and_materializes_layout(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    _ = (workspace_root / "aware.workspace.toml").write_text(
        "aware_workspace = 1\n",
        encoding="utf-8",
    )
    toml_path = _write_control_attention_package(workspace_root)
    runtime = _WorkspaceRuntimeWithoutManifest()

    result = await materialize(
        SemanticPackageMaterializationRequest(
            runtime=runtime,
            index=_attention_index(),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            manifest_path=toml_path.relative_to(workspace_root),
        )
    )

    assert result.details["attention_package_name"] == ("aware-control-shell-attention")
    assert result.details["layout_keys"] == ["control_shell"]
    assert result.details["section_keys_by_layout"] == {
        "control_shell": ["identity", "capabilities", "territories"]
    }
    receipt = result.details["attention_layout_materialization_receipt"]
    assert isinstance(receipt, dict)
    assert receipt["status"] == "succeeded"
    assert result.commit_id is not None
    assert result.head_commit_id is not None

    bundle = result.bundle_packages[0]
    assert bundle.package_key == "aware-control-shell-attention"
    assert bundle.semantic_root_kind == "attention_package"
    assert bundle.semantic_projection_name == "AttentionPackage"
    assert bundle.semantic_branch_id == stable_attention_package_id(
        name="aware-control-shell-attention"
    )

    artifact_path = workspace_root / str(
        result.details["compile_plan_artifact_relpath"]
    )
    assert artifact_path.exists()

    assert len(runtime.requests) == 25


@pytest.mark.asyncio
async def test_attention_workspace_provider_adapts_meta_graph_runtime(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    _ = (workspace_root / "aware.workspace.toml").write_text(
        "aware_workspace = 1\n",
        encoding="utf-8",
    )
    toml_path = _write_control_attention_package(workspace_root)
    runtime = _MetaGraphRuntimeWithoutManifest()

    result = await materialize(
        SemanticPackageMaterializationRequest(
            runtime=runtime,
            index=_attention_index(),
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            manifest_path=toml_path.relative_to(workspace_root),
        )
    )

    assert result.details["layout_keys"] == ["control_shell"]
    assert result.details["section_keys_by_layout"] == {
        "control_shell": ["identity", "capabilities", "territories"]
    }
    assert len(runtime.requests) == 25
    assert runtime.requests[0].domain_branch_id == stable_attention_package_id(
        name="aware-control-shell-attention"
    )
    assert runtime.requests[0].domain_projection_hash == "projection:AttentionPackage"
    assert result.commit_id is not None
