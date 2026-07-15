from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest

from aware_interface.manifest import load_aware_app_toml_spec
from aware_interface.manifest.app_launch_selection import (
    AwareAppCommittedScreenEvidence,
    AwareAppLaunchDescriptor,
    AwareAppPackageLaunchEvidence,
    render_aware_app_launch_descriptor_json,
    render_aware_app_launch_manifest_dart,
)


_REPO_ROOT = Path(__file__).resolve().parents[8]
_HOME_APP_ROOT = (
    _REPO_ROOT
    / "workspaces"
    / "aware_home"
    / "modules"
    / "home"
    / "apps"
    / "aware_home"
)
_APP_PACKAGE_ID = UUID("11111111-1111-4111-8111-111111111111")
_APP_BRANCH_ID = UUID("22222222-2222-4222-8222-222222222222")
_APP_COMMIT_ID = UUID("33333333-3333-4333-8333-333333333333")
_CONTROL_SCREEN_ID = UUID("44444444-4444-4444-8444-444444444444")
_HOME_SCREEN_ID = UUID("55555555-5555-4555-8555-555555555555")
_CONTROL_EXPERIENCE_ID = UUID("66666666-6666-4666-8666-666666666666")
_HOME_EXPERIENCE_ID = UUID("77777777-7777-4777-8777-777777777777")
_CONTROL_LAYOUT_ID = UUID("88888888-8888-4888-8888-888888888888")
_HOME_LAYOUT_ID = UUID("99999999-9999-4999-8999-999999999999")


def _descriptor(
    *,
    default_screen_key: str = "control",
    duplicate_home: bool = False,
) -> AwareAppLaunchDescriptor:
    screens = (
        AwareAppCommittedScreenEvidence(
            app_config_screen_config_id=_CONTROL_SCREEN_ID,
            screen_key="control",
            projection_experience_id=_CONTROL_EXPERIENCE_ID,
            projection_experience_layout_graph_binding_id=_CONTROL_LAYOUT_ID,
        ),
        AwareAppCommittedScreenEvidence(
            app_config_screen_config_id=_HOME_SCREEN_ID,
            screen_key="home",
            projection_experience_id=_HOME_EXPERIENCE_ID,
            projection_experience_layout_graph_binding_id=_HOME_LAYOUT_ID,
        ),
    )
    if duplicate_home:
        screens = (*screens, screens[-1])
    return AwareAppLaunchDescriptor(
        app_id="aware-home",
        display_name="Aware Home",
        app_package=AwareAppPackageLaunchEvidence(
            package_name="aware-home-app",
            app_package_id=_APP_PACKAGE_ID,
            branch_id=_APP_BRANCH_ID,
            object_instance_graph_commit_id=_APP_COMMIT_ID,
        ),
        default_screen_key=default_screen_key,
        screens=screens,
    )


def test_json_and_dart_launch_artifacts_share_committed_coordinates() -> None:
    spec = load_aware_app_toml_spec(toml_path=_HOME_APP_ROOT / "aware.app.toml")
    descriptor = _descriptor()

    payload = json.loads(render_aware_app_launch_descriptor_json(descriptor))
    dart = render_aware_app_launch_manifest_dart(
        spec=spec,
        source_manifest_path=Path("apps/aware_home/aware.app.toml"),
        descriptor=descriptor,
    )

    assert payload["schema"] == "aware.app.launch.v0"
    assert payload["app_package"] == {
        "app_package_id": str(_APP_PACKAGE_ID),
        "branch_id": str(_APP_BRANCH_ID),
        "object_instance_graph_commit_id": str(_APP_COMMIT_ID),
        "package_name": "aware-home-app",
    }
    assert payload["default_screen_key"] == "control"
    assert [screen["screen_key"] for screen in payload["screens"]] == [
        "control",
        "home",
    ]
    for value in (
        _APP_PACKAGE_ID,
        _APP_BRANCH_ID,
        _APP_COMMIT_ID,
        _CONTROL_SCREEN_ID,
        _HOME_SCREEN_ID,
        _CONTROL_EXPERIENCE_ID,
        _HOME_EXPERIENCE_ID,
        _CONTROL_LAYOUT_ID,
        _HOME_LAYOUT_ID,
    ):
        assert str(value) in dart
    assert (
        "environment" not in render_aware_app_launch_descriptor_json(descriptor).lower()
    )


def test_launch_descriptor_rejects_duplicate_and_missing_default_screens() -> None:
    with pytest.raises(ValueError, match="duplicate screen_key"):
        _descriptor(duplicate_home=True)
    with pytest.raises(ValueError, match="default screen is not committed"):
        _descriptor(default_screen_key="missing")
