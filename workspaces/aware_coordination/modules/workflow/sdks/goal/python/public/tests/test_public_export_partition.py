"""Freeze the legacy root-export partition before the breaking 0.3 wheel cut."""

from __future__ import annotations

import hashlib
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import aware_goal_sdk as sdk
import aware_goal_service_view_compat as compat


PARSER_EXPORTS = frozenset(
    {
        "GoalMarkdownImportError",
        "GoalMarkdownImportPlan",
        "GoalMarkdownLaneIssueSeed",
        "GoalMarkdownLaneSeed",
        "load_goal_markdown_import_plan",
        "parse_goal_markdown_import_plan",
    }
)
VIEW_APPLY_EXPORTS = frozenset(
    {
        "GoalMarkdownImportApplyResult",
        "apply_goal_markdown_import_plan",
        "goal_home_view_state_from_goal_markdown",
        "goal_home_view_state_from_markdown_import_plan",
    }
)


def _digest(names: set[str]) -> str:
    return hashlib.sha256("\n".join(sorted(names)).encode()).hexdigest()


def _groups(module: object) -> dict[str, set[str]]:
    groups: dict[str, set[str]] = {}
    for name, value in cast(Mapping[str, object], vars(module)).items():
        if name.startswith("_") and name.endswith("_EXPORTS"):
            assert type(value) is set
            assert all(type(item) is str for item in cast(set[object], value))
            groups[name] = cast(set[str], value)
    return groups


def test_exact_legacy_root_export_partition_is_frozen() -> None:
    neutral_groups = _groups(sdk)
    compat_groups = _groups(compat)
    assert set(neutral_groups) == {
        "_PHASE_OPERATION_EXPORTS",
        "_PHASE_DIRECTION_EXPORTS",
        "_MARKDOWN_SOURCE_EXPORTS",
        "_PHASE_MARKDOWN_EXPORTS",
        "_NATIVE_PHASE_MARKDOWN_EXPORTS",
        "_DEPENDENCY_VIEW_EXPORTS",
    }
    assert set(compat_groups) == {
        "_CLIENT_EXPORTS",
        "_OPERATION_EXPORTS",
        "_MARKDOWN_EXPORTS",
        "_MARKDOWN_IMPORT_EXPORTS",
        "_VIEW_STATE_EXPORTS",
    }
    assert neutral_groups["_MARKDOWN_SOURCE_EXPORTS"] == PARSER_EXPORTS
    assert compat_groups["_MARKDOWN_IMPORT_EXPORTS"] == VIEW_APPLY_EXPORTS
    neutral = set().union(*neutral_groups.values())
    compatibility = set().union(*compat_groups.values())
    all_dynamic = neutral | compatibility
    assert neutral.isdisjoint(compatibility)
    assert (len(all_dynamic), _digest(all_dynamic)) == (
        92,
        "24467085fb29f76ac2968ab7941ae559555bc2b84adf3c8725043a0c4e48dcc7",
    )
    assert (len(neutral), _digest(neutral)) == (
        45,
        "1ace6e0dccfd844ad684bf9b06ae54a12a53fcd60c81c127f244da22585467ce",
    )
    assert (len(compatibility), _digest(compatibility)) == (
        47,
        "13ec1cca195f1b5508b38fe4ea270ed3fc122574a7d4950412c11e8c35af8f89",
    )
    assert set(sdk.__all__) == neutral
    assert set(compat.__all__) == compatibility
    for name in compatibility:
        assert not hasattr(sdk, name)


def test_physical_package_partition_and_neutral_metadata() -> None:
    sdk_root = Path(__file__).parents[1]
    package_root = sdk_root / "aware_goal_sdk"
    assert {path.name for path in package_root.glob("*.py")} == {
        "__init__.py",
        "dependency_source.py",
        "dependency_view.py",
        "markdown_source.py",
        "native_phase_markdown.py",
        "native_phase_public_facts.py",
        "phase_direction.py",
        "phase_markdown_projection.py",
        "phase_operation.py",
    }
    compat_root = sdk_root.parent / "service_view_compat"
    assert {path.name for path in (compat_root / "aware_goal_service_view_compat").glob("*.py")} == {
        "__init__.py",
        "client.py",
        "dependency_projection.py",
        "landscape_projection.py",
        "markdown_import.py",
        "markdown_projection.py",
        "operation.py",
        "view_state_providers.py",
    }
    sdk_manifest = tomllib.loads((sdk_root / "pyproject.toml").read_text())
    compat_manifest = tomllib.loads((compat_root / "pyproject.toml").read_text())
    assert sdk_manifest["project"]["version"] == "0.3.0"
    assert sdk_manifest["project"]["dependencies"] == [
        "aware-goal-operational-runtime>=0.1.0"
    ]
    assert compat_manifest["project"]["name"] == "aware-goal-service-view-compat"
    assert "aware-goal-sdk>=0.3.0" in compat_manifest["project"]["dependencies"]
