from __future__ import annotations

import json
from pathlib import Path
import sys

_REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_NODE_RUNTIME_ROOT_STR = str(_REPO_ROOT / "modules" / "node" / "runtime")
if _NODE_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _NODE_RUNTIME_ROOT_STR)

from aware_node.compile import (  # noqa: E402
    build_node_compile_plan,
    compile_node_workspace,
    emit_node_compile_plan_artifact,
)
from aware_node.workspace import NodeWorkspace  # noqa: E402


def _write_node_toml(root: Path, *, node_ontology_mode: bool = False) -> Path:
    toml_path = root / "aware.node.toml"
    lines = [
        "aware_node = 1",
        "",
        "[node]",
        'package_name = "kernel-node"',
        'fqn_prefix = "aware_kernel_node"',
        'description = "Canonical kernel host"',
        "",
        "[build]",
        'sources_dir = "nodes"',
        'include_paths = ["**/*.aware"]',
        "exclude_paths = []",
    ]
    if node_ontology_mode:
        lines.append('compilation_mode = "node_ontology"')
    _ = toml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return toml_path


def _write_node_source(root: Path) -> None:
    nodes_dir = root / "nodes"
    nodes_dir.mkdir(parents=True, exist_ok=True)
    _ = (nodes_dir / "kernel_node.aware").write_text(
        "\n".join(
            [
                "node kernel_host {",
                "    environment kernel {",
                "        profile os.default package aware-workspace-environment-profile",
                "    }",
                "    ontology storage-ontology;",
                "    service aware_attention {",
                "        package experience aware-workspace-experience;",
                "    }",
                "    interface aware_workspace;",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_compile_node_workspace_returns_snapshot_only_for_raw_xor(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_node_toml(root)
    _write_node_source(root)

    result = compile_node_workspace(toml_path=toml_path, repo_root=root)

    assert result.snapshot.spec.node.package_name == "kernel-node"
    assert result.snapshot.source_files == (Path("nodes/kernel_node.aware"),)
    assert result.compile_plan is None
    assert result.compile_plan_artifact is None


def test_build_node_compile_plan_and_emit_artifact(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_node_toml(root, node_ontology_mode=True)
    _write_node_source(root)

    snapshot = NodeWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    plan = build_node_compile_plan(snapshot=snapshot)

    assert plan.schema_version == 3
    assert plan.package_name == "kernel-node"
    assert plan.fqn_prefix == "aware_kernel_node"
    assert plan.source_files == ("nodes/kernel_node.aware",)
    assert plan.node_ownership.name == "kernel_host"
    assert tuple(
        item.environment_handle for item in plan.node_ownership.environment_targets
    ) == ("kernel",)
    assert tuple(
        (
            mount.package_name,
            mount.profile_key,
            mount.mount_key,
            mount.mode,
            mount.position,
        )
        for item in plan.node_ownership.environment_targets
        for mount in item.profile_mounts
    ) == (
        (
            "aware-workspace-environment-profile",
            "os.default",
            "aware-workspace-environment-profile:os.default",
            "mounted",
            0,
        ),
    )
    assert tuple(item.service_name for item in plan.node_ownership.service_targets) == (
        "aware_attention",
    )
    assert tuple(
        (package.slot_key, package.package_name, package.language)
        for target in plan.node_ownership.service_targets
        for package in target.code_packages
    ) == (
        ("experience", "aware-workspace-experience", "aware"),
    )
    assert tuple(
        item.package_name for item in plan.node_ownership.ontology_targets
    ) == ("storage-ontology",)
    assert tuple(
        item.interface_name for item in plan.node_ownership.interface_targets
    ) == ("aware_workspace",)

    artifact = emit_node_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=(root / "runtime"),
        repo_root=root,
    )

    assert artifact.path.exists()
    assert artifact.relpath == "runtime/node.compile_plan.json"
    assert len(artifact.hash_sha256) == 64
    payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    assert payload["node_ownership"]["name"] == "kernel_host"
    assert payload["node_ownership"]["environment_targets"][0]["profile_mounts"] == [
        {
            "package_name": "aware-workspace-environment-profile",
            "profile_key": "os.default",
            "mount_key": "aware-workspace-environment-profile:os.default",
            "mode": "mounted",
            "position": 0,
            "source_path": "nodes/kernel_node.aware",
        }
    ]
    assert (
        payload["node_ownership"]["service_targets"][0]["service_name"]
        == "aware_attention"
    )
    assert payload["node_ownership"]["service_targets"][0]["code_packages"] == [
        {
            "slot_key": "experience",
            "package_name": "aware-workspace-experience",
            "language": "aware",
            "source_path": "nodes/kernel_node.aware",
        }
    ]
    assert (
        payload["node_ownership"]["ontology_targets"][0]["package_name"]
        == "storage-ontology"
    )


def test_compile_node_workspace_emits_plan_for_node_ontology(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_node_toml(root, node_ontology_mode=True)
    _write_node_source(root)

    result = compile_node_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
    )

    assert result.compile_plan is not None
    assert result.compile_plan_artifact is not None
    assert (
        result.compile_plan_artifact.relpath
        == ".aware/node/runtime/kernel-node/node.compile_plan.json"
    )
    payload = result.compile_plan_artifact.path.read_text(encoding="utf-8")
    assert '"name": "kernel_host"' in payload
    assert '"package_name": "aware-workspace-environment-profile"' in payload
    assert '"profile_key": "os.default"' in payload
    assert '"package_name": "storage-ontology"' in payload
    assert '"service_name": "aware_attention"' in payload
