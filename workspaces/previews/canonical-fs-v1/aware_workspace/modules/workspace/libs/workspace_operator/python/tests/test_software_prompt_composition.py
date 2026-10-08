from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from aware_workspace_operator.prompt_composition import (
    compose_software_templates,
    load_software_prompt_profile,
    load_software_template_files,
)
from aware_workspace_operator.pipeline.stages.scaffold import (
    ensure_seed_bundle,
    ensure_software_rules_bundle,
)


_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "aware_workspace_operator"
_SOFTWARE_CONFIG_ROOT = _PACKAGE_ROOT / "assets" / "software"


def test_software_prompt_composition_tracks_unresolved_tokens() -> None:
    template_files = load_software_template_files(
        template_root=(
            _SOFTWARE_CONFIG_ROOT / "templates" / "mental-model-v1"
        ).resolve()
    )
    profile = load_software_prompt_profile(
        profile_path=(
            _SOFTWARE_CONFIG_ROOT / "profiles" / "external-default-v1.toml"
        ).resolve(),
        profile_id="external-default-v1",
        assets_root=(_SOFTWARE_CONFIG_ROOT / "assets").resolve(),
    )

    result = compose_software_templates(
        template_id="mental-model-v1",
        profile=profile,
        template_files=template_files,
    )

    assert result.template_id == "mental-model-v1"
    assert result.profile_id == "external-default-v1"
    assert result.strict_unresolved is True
    assert result.unresolved_tokens == []
    assert result.unresolved_by_file["0-config.md"] == []
    rendered_by_name = {item.name: item.rendered_text for item in result.files}
    assert (
        "docs/rules/SOFTWARE/assets/minimal-references/0-config.md"
        in rendered_by_name["0-config.md"]
    )
    assert "docs/aware/grammar/README.md" not in rendered_by_name["0-config.md"]
    assert (
        "docs/rules/SOFTWARE/assets/minimal-references/1-runtime.md"
        in rendered_by_name["1-runtime.md"]
    )
    assert "libs/runtime/aware_runtime/function_call/mutation_boundary.py" not in (
        rendered_by_name["1-runtime.md"]
    )
    assert (
        "docs/rules/SOFTWARE/assets/minimal-references/2-representation.md"
        in rendered_by_name["2-representation.md"]
    )
    assert "apps/interface_flutter/aware_pane_runtime/docs/projection-views.md" not in (
        rendered_by_name["2-representation.md"]
    )
    assert (
        "docs/rules/SOFTWARE/assets/minimal-references/3-programs.md"
        in rendered_by_name["3-programs.md"]
    )
    assert "Programs CORE:" in rendered_by_name["3-programs.md"]
    assert (
        "docs/rules/SOFTWARE/assets/minimal-references/4-policy.md"
        in rendered_by_name["4-policy.md"]
    )
    assert (
        "RoleConfigClassConfigFunctionConfig.function_config_id"
        in rendered_by_name["4-policy.md"]
    )
    assert (
        "docs/rules/SOFTWARE/assets/minimal-references/5-reactivity.md"
        in rendered_by_name["5-reactivity.md"]
    )
    assert "ActorSubscription CORE:" in rendered_by_name["5-reactivity.md"]
    assert "6-subscription.md" not in rendered_by_name


def test_software_prompt_composition_strict_profile_fails_on_unresolved(
    tmp_path: Path,
) -> None:
    template_root = tmp_path / "template"
    profile_path = tmp_path / "strict.toml"
    template_root.mkdir(parents=True, exist_ok=True)
    (template_root / "index.md").write_text("Hello {missing_key}\n", encoding="utf-8")
    profile_path.write_text(
        (
            "version = 1\n"
            'template_id = "mental-model-v1"\n'
            "strict_unresolved = true\n\n"
            "[replacements]\n"
        ),
        encoding="utf-8",
    )

    template_files = load_software_template_files(template_root=template_root)
    profile = load_software_prompt_profile(
        profile_path=profile_path,
        profile_id="strict",
    )
    with pytest.raises(ValueError, match="unresolved template tokens"):
        _ = compose_software_templates(
            template_id="mental-model-v1",
            profile=profile,
            template_files=template_files,
        )


def test_software_prompt_profile_asset_replacement_is_resolved(
    tmp_path: Path,
) -> None:
    assets_root = tmp_path / "assets"
    profile_path = tmp_path / "asset-profile.toml"
    section_asset = assets_root / "section-core" / "0-config" / "core.md"
    section_asset.parent.mkdir(parents=True, exist_ok=True)
    section_asset.write_text(
        "CORE section payload from asset.\n",
        encoding="utf-8",
    )
    profile_path.write_text(
        (
            "version = 1\n"
            'template_id = "mental-model-v1"\n'
            "strict_unresolved = false\n\n"
            "[replacements]\n"
            'sample = "asset://section-core/0-config/core.md"\n'
        ),
        encoding="utf-8",
    )

    profile = load_software_prompt_profile(
        profile_path=profile_path,
        profile_id="asset-profile",
        assets_root=assets_root,
    )

    assert profile.replacements["sample"] == "CORE section payload from asset.\n"


def test_software_rules_bundle_uses_package_assets_and_exports_act_react(
    tmp_path: Path,
) -> None:
    status = ensure_software_rules_bundle(
        repo_root=tmp_path,
        write_software_rules_bundle=True,
        template_id="mental-model-v1",
        profile_id="external-default-v1",
    )

    exported_root = tmp_path / "docs" / "rules" / "SOFTWARE"
    toolkit_root = exported_root / "assets" / "act-react-v1"
    assert Path(status.source_root) == _SOFTWARE_CONFIG_ROOT.resolve()
    assert (exported_root / "3-programs.md").is_file()
    assert (toolkit_root / "act-react.v1.schema.json").is_file()
    assert (toolkit_root / "conformance" / "README.md").is_file()
    assert (toolkit_root / "conformance" / "runner.py").is_file()

    schema = json.loads(
        (toolkit_root / "act-react.v1.schema.json").read_text(encoding="utf-8")
    )
    assert schema["$id"] == "https://awareos.dev/schemas/act-react.v1.schema.json"

    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "protocol_version": "act-react.v1",
                "runtime_id": "workspace-operator-test",
                "results": [
                    {"id": f"AR-{index:02d}", "status": "pass"}
                    for index in range(1, 11)
                ],
            }
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(toolkit_root / "conformance" / "runner.py"),
            "--report",
            str(report_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_seed_bundle_uses_current_workspace_package_assets(tmp_path: Path) -> None:
    status = ensure_seed_bundle(
        repo_root=tmp_path,
        write_seed_bundle=True,
    )

    source_root = _PACKAGE_ROOT / "assets" / "seeds"
    generated_root = tmp_path / "configs" / "seeds"
    assert Path(status.source_root) == source_root.resolve()
    assert {path.name for path in generated_root.iterdir()} == {
        "README.md",
        "aware.programs.toml",
        "aware_kernel.seed.aware",
        "aware_kernel.seed.profile.toml",
        "aware_kernel.seed.toml",
    }
    program_text = (generated_root / "aware_kernel.seed.aware").read_text(
        encoding="utf-8"
    )
    assert "kernel_executor_secondary" in program_text
    assert "economy:EconomySettlementRoleConfigPolicies_v1" in program_text
