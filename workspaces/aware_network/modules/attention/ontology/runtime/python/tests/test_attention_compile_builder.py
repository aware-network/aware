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

from aware_attention.builder import (  # noqa: E402
    build_attention_compile_plan_from_anchor,
    emit_attention_compile_plan_artifact,
)
from aware_attention_ontology.stable_ids import (  # noqa: E402
    stable_layout_config_id,
    stable_layout_config_section_config_id,
    stable_section_config_id,
)


def _anchor_payload() -> dict[str, object]:
    return {
        "layout": {
            "key": "workspace-default",
            "title": "Workspace Default",
            "description": "Primary attention layout anchor",
        },
        "section": {
            "key": "workspace",
            "title": "Workspace",
            "description": "Primary attention section anchor",
        },
        "focus_scope": {
            "title": "Main Scope",
            "description": "Anchor focus scope for workspace section",
            "is_active": True,
        },
    }


def test_build_attention_compile_plan_from_anchor_uses_stable_ids() -> None:
    plan = build_attention_compile_plan_from_anchor(
        anchor_payload=_anchor_payload(),
        package_name="attention_layout_workspace",
        source_files=("anchors/layout_section.anchor.toml",),
    )

    assert plan.schema_version == 1
    assert plan.package_name == "attention_layout_workspace"
    assert plan.source_files == ("anchors/layout_section.anchor.toml",)
    assert len(plan.layout_ontology) == 1

    layout = plan.layout_ontology[0]
    expected_layout_config_id = stable_layout_config_id(key="workspace-default")
    expected_layout_config_section_config_id = stable_layout_config_section_config_id(
        layout_config_id=expected_layout_config_id,
        section_key="workspace",
    )
    expected_section_config_id = stable_section_config_id(
        layout_config_section_config_id=expected_layout_config_section_config_id,
        key="workspace",
    )

    assert layout.layout_config_id == str(expected_layout_config_id)
    assert layout.layout_key == "workspace-default"
    assert layout.frame_mode == "vertical"
    assert len(layout.sections) == 1

    section = layout.sections[0]
    assert section.layout_config_section_config_id == str(
        expected_layout_config_section_config_id
    )
    assert section.section_config_id == str(expected_section_config_id)
    assert section.section_key == "workspace"
    assert section.order == 0
    assert section.flex == 1.0
    assert section.is_visible is True


def test_emit_attention_compile_plan_artifact_writes_deterministic_payload(
    tmp_path: Path,
) -> None:
    plan = build_attention_compile_plan_from_anchor(
        anchor_payload=_anchor_payload(),
        package_name="attention_layout_workspace",
        source_files=("anchors/layout_section.anchor.toml",),
        frame_mode="grid",
    )

    artifact = emit_attention_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=tmp_path / "runtime",
        repo_root=tmp_path,
    )

    assert artifact.path.exists()
    assert artifact.relpath == "runtime/attention.compile_plan.json"
    assert len(artifact.hash_sha256) == 64
    payload = artifact.path.read_text(encoding="utf-8")
    assert '"layout_ontology"' in payload
    assert '"frame_mode": "grid"' in payload
    assert '"layout_key": "workspace-default"' in payload
    assert '"section_key": "workspace"' in payload
