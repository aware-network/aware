"""Read-only split-preparation diagnostics, not a production operation catalog.

These characterize pinned predecessor sources. Passing them does not establish
a neutral SDK, owner admission, migration, installation or API compatibility.
"""

from __future__ import annotations

import ast
import hashlib
import json
import tomllib
from pathlib import Path

import pytest

REPOSITORY_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)
WORKSPACE = Path("workspaces/aware_workspace/modules/workspace")
WORKFLOW = Path("workspaces/aware_coordination/modules/workflow")
INPUTS_PATH = Path(
    "docs/reports/workspace-sdk-runtime-physical-split-inputs-20261009.json"
)
TREES = {
    "sdk": WORKSPACE / "sdks/workspace/python/public/aware_workspace_sdk",
    "runtime": WORKSPACE / "libs/workspace_runtime/aware_workspace_runtime",
    "operator": WORKSPACE / "libs/workspace_operator/python/aware_workspace_operator",
}
PIN_PATHS = (
    WORKSPACE / "aware.module.toml",
    WORKSPACE / "sdks/workspace/aware/aware.sdk.toml",
    WORKSPACE / "sdks/workspace/aware/workspace_sdk.aware",
    WORKSPACE / "sdks/workspace/python/public/pyproject.toml",
    WORKSPACE / "libs/workspace_runtime/pyproject.toml",
    WORKSPACE / "libs/workspace_operator/python/pyproject.toml",
    WORKFLOW / "sdks/issue/filesystem_adapter/python/pyproject.toml",
    WORKFLOW
    / "sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/provider.py",
)


def source_imports(body: str) -> frozenset[str]:
    """Collect explicit imports, including imports in functions/TYPE_CHECKING.

    This is an AST source diagnostic; dynamic imports and transitive dependency
    closure require separate qualification, not inferred absence.
    """
    modules: set[str] = set()
    for node in ast.walk(ast.parse(body)):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            modules.add(node.module)
    return frozenset(modules)


def tree_observation(root: Path) -> dict[str, object]:
    transcript = bytearray()
    imports: set[str] = set()
    paths = sorted(root.rglob("*.py"))
    for path in paths:
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        body = path.read_bytes()
        transcript.extend(relative.encode("utf-8") + b"\0")
        transcript.extend(hashlib.sha256(body).digest())
        imports.update(source_imports(body.decode("utf-8")))
    return {
        "python_files": len(paths),
        "source_tree_sha256": hashlib.sha256(transcript).hexdigest(),
        "explicit_import_roots": sorted({name.split(".")[0] for name in imports}),
    }


def observe_inputs() -> dict[str, object]:
    """Observe the selected source cohorts; never discover execution authority."""
    return {
        "purpose": "workspace-split-preparation-predecessor-observation",
        "runtime_split_implemented": False,
        "tree_digest_encoding": "sorted repository-relative UTF-8 path, NUL, raw SHA-256 body digest",
        "trees": {
            name: tree_observation(REPOSITORY_ROOT / relative)
            for name, relative in TREES.items()
        },
        "pins": {
            path.as_posix(): hashlib.sha256(
                (REPOSITORY_ROOT / path).read_bytes()
            ).hexdigest()
            for path in PIN_PATHS
        },
    }


def _body(path: Path) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def test_preparation_inputs_are_current() -> None:
    recorded = json.loads(_body(INPUTS_PATH))
    assert recorded == observe_inputs(), (
        "Reobserve changed suppliers before scoped extraction"
    )


@pytest.mark.parametrize("name", tuple(TREES))
def test_complete_named_python_cohort_is_nonempty(name: str) -> None:
    observation = tree_observation(REPOSITORY_ROOT / TREES[name])
    assert observation["python_files"] > 0
    assert len(observation["source_tree_sha256"]) == 64


@pytest.mark.parametrize(
    "body, expected",
    (
        ("from .local import x", frozenset()),
        ("import os.path as p", frozenset({"os.path"})),
        ("def f():\n from foreign.sdk import Client", frozenset({"foreign.sdk"})),
        ("if TYPE_CHECKING:\n import foreign.runtime", frozenset({"foreign.runtime"})),
    ),
)
def test_import_inventory_handles_non_top_level_imports(
    body: str, expected: frozenset[str]
) -> None:
    assert source_imports(body) == expected


def test_predecessor_sdk_is_service_coupled_not_a_neutral_successor() -> None:
    metadata = tomllib.loads(
        _body(WORKSPACE / "sdks/workspace/python/public/pyproject.toml")
    )
    assert metadata["project"]["name"] == "aware-workspace-sdk"
    dependencies = metadata["project"]["dependencies"]
    assert "aware_workspace_service_api" in dependencies
    assert "aware_workspace_service_dto" in dependencies
    assert "aware-orm" in dependencies


def test_predecessor_issue_adapter_has_a_direct_workspace_operator_edge() -> None:
    imports = source_imports(_body(PIN_PATHS[-1]))
    assert "aware_workspace_operator" in imports


def test_predecessor_operator_has_reverse_issue_runtime_and_physical_io_edges() -> None:
    imports = source_imports(_body(TREES["operator"] / "commit.py"))
    assert {"aware_issue_operational_runtime", "fcntl", "os", "subprocess"} <= imports


def test_predecessor_runtime_includes_physical_source_observation() -> None:
    imports = source_imports(_body(TREES["runtime"] / "source_observation_io.py"))
    assert {"os", "stat"} <= imports


def test_semantic_revision_commit_and_git_writer_are_not_identical_contracts() -> None:
    semantic = source_imports(_body(TREES["sdk"] / "features/session/commit_api.py"))
    physical = ast.parse(_body(TREES["operator"] / "commit.py"))
    functions = {
        node.name for node in physical.body if isinstance(node, ast.FunctionDef)
    }
    assert "aware_workspace_service_dto.workspace.service_operation" in semantic
    assert "run_workspace_commit" in functions
    assert "run_workspace_authorized_commit" in functions


def test_preparation_does_not_claim_a_split_or_new_package_selection() -> None:
    recorded = json.loads(_body(INPUTS_PATH))
    assert recorded["runtime_split_implemented"] is False
    manifest = tomllib.loads(_body(WORKSPACE / "aware.module.toml"))
    registrations = {row["id"]: row["manifest"] for row in manifest["packages"]}
    assert (
        registrations["workspace_sdk_python"]
        == "sdks/workspace/python/public/pyproject.toml"
    )
    assert registrations["workspace_runtime"] == "libs/workspace_runtime/pyproject.toml"
    assert (
        registrations["workspace_operator"]
        == "libs/workspace_operator/python/pyproject.toml"
    )


if __name__ == "__main__":
    # Diagnostic stdout only. Source changes must use the admitted editor rail.
    print(json.dumps(observe_inputs(), indent=2, sort_keys=True))
