from __future__ import annotations

from pathlib import Path
import sys

_RUNTIME_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _RUNTIME_ROOT.parents[6]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_ATTENTION_RUNTIME_ROOT_STR = str(_RUNTIME_ROOT)
if _ATTENTION_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _ATTENTION_RUNTIME_ROOT_STR)

from aware_attention_ontology.stable_ids import (
    stable_attention_package_id,
)  # noqa: E402
from aware_attention.compile import (  # noqa: E402
    compile_attention_anchor_workspace,
    compile_attention_workspace,
)
from aware_attention.materialization.service import (
    load_attention_compile_plan_payloads,
)  # noqa: E402


def _write_anchor(root: Path) -> Path:
    anchor_path = (
        root / "attention_layout_workspace" / "anchors" / "layout_section.anchor.toml"
    )
    anchor_path.parent.mkdir(parents=True, exist_ok=True)
    _ = anchor_path.write_text(
        "\n".join(
            [
                "[layout]",
                'key = "workspace-default"',
                'title = "Workspace Default"',
                'description = "Primary attention layout anchor"',
                "",
                "[section]",
                'key = "workspace"',
                'title = "Workspace"',
                'description = "Primary attention section anchor"',
                "",
                "[focus_scope]",
                'title = "Main Scope"',
                'description = "Anchor focus scope for workspace section"',
                "is_active = true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return anchor_path


def _write_attention_toml(root: Path) -> Path:
    package_root = root / "attention_layout_workspace"
    package_root.mkdir(parents=True, exist_ok=True)
    _ = (package_root / "aware.attention.toml").write_text(
        "\n".join(
            [
                "aware_attention = 1",
                "",
                "[attention]",
                'package_name = "attention_layout_workspace"',
                'fqn_prefix = "aware_attention_layout_workspace"',
                "",
                "[build]",
                'anchor_path = "anchors/layout_section.anchor.toml"',
                'sources_dir = "."',
                "include_paths = []",
                "exclude_paths = []",
                'frame_mode = "vertical"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_anchor(root)
    return package_root / "aware.attention.toml"


def _write_multisection_attention_toml(root: Path) -> Path:
    package_root = root / "aware_workspace_shell"
    package_root.mkdir(parents=True, exist_ok=True)
    _ = (package_root / "aware.attention.toml").write_text(
        "\n".join(
            [
                "aware_attention = 1",
                "",
                "[attention]",
                'package_name = "aware_workspace_shell"',
                'fqn_prefix = "aware_workspace_shell"',
                'title = "Aware Workspace Shell"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                'frame_mode = "vertical"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (package_root / "workspace_shell.aware").write_text(
        "\n".join(
            [
                "layout ide_workbench default {",
                "    section orchestration",
                "    section primary",
                "    section inspector",
                "    section console",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return package_root / "aware.attention.toml"


def _write_configured_section_attention_toml(root: Path) -> Path:
    package_root = root / "aware_coordination_shell"
    package_root.mkdir(parents=True, exist_ok=True)
    _ = (package_root / "aware.attention.toml").write_text(
        "\n".join(
            [
                "aware_attention = 1",
                "",
                "[attention]",
                'package_name = "aware_coordination_shell"',
                'fqn_prefix = "aware_coordination_shell"',
                'title = "Aware Coordination Shell"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                'frame_mode = "vertical"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _ = (package_root / "coordination_shell.aware").write_text(
        "\n".join(
            [
                "layout coordination_center default {",
                "    section conversation {",
                '        title "Conversation"',
                "        order 0",
                "        flex 0.9",
                "        visible true",
                "    }",
                "",
                "    section goal {",
                '        title "Goal / Lane / Issue"',
                '        description "Shared goal structure"',
                "        order 1",
                "        flex 2.4",
                "        is_visible true",
                "    }",
                "",
                "    section work_item {",
                '        title "Work Item"',
                "        order 2",
                "        flex 1.2",
                "        visible true",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return package_root / "aware.attention.toml"


def _write_control_shell_attention_toml(root: Path) -> Path:
    package_root = root / "attentions" / "aware_control_shell"
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
            ]
        )
        + "\n",
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


def test_compile_attention_anchor_workspace_returns_plan_without_emitting(
    tmp_path: Path,
) -> None:
    anchor_path = _write_anchor(tmp_path)

    result = compile_attention_anchor_workspace(
        anchor_path=anchor_path,
        repo_root=tmp_path,
    )

    assert result.package_name == "attention_layout_workspace"
    assert result.source_files == (
        "attention_layout_workspace/anchors/layout_section.anchor.toml",
    )
    assert result.compile_plan.package_name == "attention_layout_workspace"
    assert result.compile_plan_artifact is None


def test_compile_attention_anchor_workspace_emits_compile_plan_artifact(
    tmp_path: Path,
) -> None:
    anchor_path = _write_anchor(tmp_path)

    result = compile_attention_anchor_workspace(
        anchor_path=anchor_path,
        repo_root=tmp_path,
        emit_compile_plan=True,
        frame_mode="horizontal",
    )

    assert result.compile_plan_artifact is not None
    assert result.compile_plan_artifact.relpath == (
        ".aware/attention/runtime/attention_layout_workspace/attention.compile_plan.json"
    )
    payloads = load_attention_compile_plan_payloads(repo_root=tmp_path)
    assert len(payloads) == 1
    assert payloads[0]["package_name"] == "attention_layout_workspace"
    layout_rows = payloads[0]["layout_ontology"]
    assert isinstance(layout_rows, list)
    assert layout_rows[0]["frame_mode"] == "horizontal"


def test_compile_attention_workspace_returns_plan_without_emitting(
    tmp_path: Path,
) -> None:
    toml_path = _write_attention_toml(tmp_path)

    result = compile_attention_workspace(
        toml_path=toml_path,
        repo_root=tmp_path,
    )

    assert result.snapshot is not None
    assert result.package_name == "attention_layout_workspace"
    assert (
        result.anchor_path
        == tmp_path
        / "attention_layout_workspace"
        / "anchors"
        / "layout_section.anchor.toml"
    )
    assert result.source_files == (
        "attention_layout_workspace/anchors/layout_section.anchor.toml",
    )
    assert result.compile_plan.package_name == "attention_layout_workspace"
    assert result.compile_plan.attention_package_id == str(
        stable_attention_package_id(name="attention_layout_workspace")
    )
    assert result.compile_plan_artifact is None
    assert result.compile_plan.layout_ontology[0].frame_mode == "vertical"


def test_compile_attention_workspace_emits_compile_plan_artifact(
    tmp_path: Path,
) -> None:
    toml_path = _write_attention_toml(tmp_path)

    result = compile_attention_workspace(
        toml_path=toml_path,
        repo_root=tmp_path,
        emit_compile_plan=True,
        frame_mode="horizontal",
    )

    assert result.compile_plan_artifact is not None
    assert result.compile_plan_artifact.relpath == (
        ".aware/attention/runtime/attention_layout_workspace/attention.compile_plan.json"
    )
    payloads = load_attention_compile_plan_payloads(repo_root=tmp_path)
    assert len(payloads) == 1
    assert payloads[0]["package_name"] == "attention_layout_workspace"
    assert payloads[0]["attention_package_id"] == str(
        stable_attention_package_id(name="attention_layout_workspace")
    )
    assert payloads[0]["source_files"] == [
        "attention_layout_workspace/anchors/layout_section.anchor.toml",
    ]
    layout_rows = payloads[0]["layout_ontology"]
    assert isinstance(layout_rows, list)
    assert layout_rows[0]["frame_mode"] == "horizontal"


def test_compile_attention_workspace_supports_multisection_layouts(
    tmp_path: Path,
) -> None:
    toml_path = _write_multisection_attention_toml(tmp_path)

    result = compile_attention_workspace(
        toml_path=toml_path,
        repo_root=tmp_path,
        emit_compile_plan=True,
    )

    assert result.compile_plan_artifact is not None
    assert result.package_name == "aware_workspace_shell"
    assert result.source_files == ("aware_workspace_shell/workspace_shell.aware",)
    assert len(result.compile_plan.layout_ontology) == 1
    layout = result.compile_plan.layout_ontology[0]
    assert layout.layout_key == "ide_workbench"
    assert [section.section_key for section in layout.sections] == [
        "orchestration",
        "primary",
        "inspector",
        "console",
    ]
    assert [section.order for section in layout.sections] == [0, 1, 2, 3]
    assert [section.flex for section in layout.sections] == [1.0, 1.0, 1.0, 1.0]
    assert all(section.is_visible for section in layout.sections)

    payloads = load_attention_compile_plan_payloads(repo_root=tmp_path)
    assert len(payloads) == 1
    assert payloads[0]["package_name"] == "aware_workspace_shell"
    layout_rows = payloads[0]["layout_ontology"]
    assert isinstance(layout_rows, list)
    assert layout_rows[0]["layout_key"] == "ide_workbench"
    assert [section["section_key"] for section in layout_rows[0]["sections"]] == [
        "orchestration",
        "primary",
        "inspector",
        "console",
    ]


def test_compile_attention_workspace_lowers_authored_section_config_fields(
    tmp_path: Path,
) -> None:
    toml_path = _write_configured_section_attention_toml(tmp_path)

    result = compile_attention_workspace(
        toml_path=toml_path,
        repo_root=tmp_path,
        emit_compile_plan=True,
    )

    assert result.compile_plan_artifact is not None
    layout = result.compile_plan.layout_ontology[0]
    assert layout.layout_key == "coordination_center"
    assert [section.section_key for section in layout.sections] == [
        "conversation",
        "goal",
        "work_item",
    ]
    assert [section.title for section in layout.sections] == [
        "Conversation",
        "Goal / Lane / Issue",
        "Work Item",
    ]
    assert [section.description for section in layout.sections] == [
        None,
        "Shared goal structure",
        None,
    ]
    assert [section.order for section in layout.sections] == [0, 1, 2]
    assert [section.flex for section in layout.sections] == [0.9, 2.4, 1.2]
    assert [section.is_visible for section in layout.sections] == [True, True, True]

    payloads = load_attention_compile_plan_payloads(repo_root=tmp_path)
    assert len(payloads) == 1
    section_rows = payloads[0]["layout_ontology"][0]["sections"]
    assert [section["title"] for section in section_rows] == [
        "Conversation",
        "Goal / Lane / Issue",
        "Work Item",
    ]
    assert [section["flex"] for section in section_rows] == [0.9, 2.4, 1.2]


def test_compile_control_shell_attention_package_uses_product_section_keys(
    tmp_path: Path,
) -> None:
    toml_path = _write_control_shell_attention_toml(tmp_path)

    result = compile_attention_workspace(
        toml_path=toml_path,
        repo_root=tmp_path,
    )

    assert result.package_name == "aware-control-shell-attention"
    assert result.source_files == (
        "attentions/aware_control_shell/control_shell.aware",
    )
    layout = result.compile_plan.layout_ontology[0]
    assert layout.layout_key == "control_shell"
    assert [section.section_key for section in layout.sections] == [
        "identity",
        "capabilities",
        "territories",
    ]
    assert [section.title for section in layout.sections] == [
        "Identity",
        "Capabilities",
        "Territories",
    ]
