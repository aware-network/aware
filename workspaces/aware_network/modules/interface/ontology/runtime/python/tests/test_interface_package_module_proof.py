from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    isolated_meta_aware_root,
    rehydrate_lane_root_from_head,
)
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_interface_ontology.stable_ids import (
    stable_interface_config_id,
    stable_interface_package_id,
    stable_pane_config_id,
    stable_pane_package_id,
)
from _interface_runtime_test_paths import REPO_ROOT


@pytest.mark.asyncio
async def test_interface_package_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        from aware_interface_ontology.interface.interface_config import InterfaceConfig
        from aware_interface_ontology.interface.interface_package import InterfacePackage

        ids = _runtime_ids()
        interface_config_name = "aware-control-plane"
        source_package_name = "aware_interface_test_source_package"
        source_code_package_id = _interface_source_code_package_id(
            package_name=source_package_name,
        )
        interface_config_id = stable_interface_config_id(
            name=interface_config_name,
        )
        interface_package_id = stable_interface_package_id(
            name=interface_config_name,
        )

        config_lane = runtime.bind(
            branch_id=interface_config_id,
            projection="InterfaceConfig",
            actor_id=ids["actor_id"],
        )
        with config_lane.activate(commit=True, publish=False):
            await InterfaceConfig.build(
                name=interface_config_name,
                description="Interface package proof",
            )

        package_lane = runtime.bind(
            branch_id=interface_package_id,
            projection="InterfacePackage",
            actor_id=ids["actor_id"],
        )
        with package_lane.activate(commit=True, publish=False):
            await InterfacePackage.build(
                name=interface_config_name,
                interface_config_id=interface_config_id,
                source_code_package_id=source_code_package_id,
                fqn_prefix="aware.interface.control_plane",
                version_number=9,
                title="Control Plane Interface",
                description="Interface package module proof",
                aware_interface_version=1,
                manifest_relative_path="interfaces/control_plane/aware.interface.toml",
                package_root="interfaces/control_plane",
                sources_root="interfaces/control_plane/bindings",
                config_bundle_path=("interfaces/control_plane/bundles/interface.config.bundle.json"),
                include_paths=["bindings/**/*.aware"],
                exclude_paths=["bindings/**/*.draft.aware"],
                force_fresh_scan=False,
                compilation_mode="interface_ontology",
                dependencies=[
                    {
                        "package_name": "control-plane-api",
                        "version_number": 2,
                        "kind": "api_package",
                    }
                ],
                dart={
                    "package_path": "dart/control_plane_interface",
                    "package_name": "control_plane_interface",
                },
            )

        committed_config = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=interface_config_id,
            projection_name="InterfaceConfig",
            root_id=interface_config_id,
            root_type=InterfaceConfig,
        )
        committed_package = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=interface_package_id,
            projection_name="InterfacePackage",
            root_id=interface_package_id,
            root_type=InterfacePackage,
        )

        assert committed_config.id == interface_config_id
        assert committed_config.name == interface_config_name
        assert committed_package.id == interface_package_id
        assert committed_package.name == interface_config_name
        assert committed_package.interface_config_id == interface_config_id
        assert committed_package.source_code_package_id == source_code_package_id
        assert committed_package.fqn_prefix == "aware.interface.control_plane"
        assert committed_package.version_number == 9
        assert committed_package.title == "Control Plane Interface"
        assert committed_package.description == "Interface package module proof"
        assert committed_package.aware_interface_version == 1
        assert committed_package.manifest_relative_path == "interfaces/control_plane/aware.interface.toml"
        assert committed_package.package_root == "interfaces/control_plane"
        assert committed_package.sources_root == "interfaces/control_plane/bindings"
        assert committed_package.config_bundle_path == "interfaces/control_plane/bundles/interface.config.bundle.json"
        assert list(committed_package.include_paths) == ["bindings/**/*.aware"]
        assert list(committed_package.exclude_paths) == ["bindings/**/*.draft.aware"]
        assert committed_package.force_fresh_scan is False
        assert committed_package.compilation_mode == "interface_ontology"
        assert list(committed_package.dependencies) == [
            {
                "package_name": "control-plane-api",
                "version_number": 2,
                "kind": "api_package",
            }
        ]
        assert dict(committed_package.dart) == {
            "package_path": "dart/control_plane_interface",
            "package_name": "control_plane_interface",
        }


@pytest.mark.asyncio
async def test_pane_package_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        from aware_interface_ontology.interface.pane_config import PaneConfig
        from aware_interface_ontology.interface.pane_package import PanePackage

        ids = _runtime_ids()
        pane_name = "door_control"
        source_package_name = "aware_door_control_pane"
        source_code_package_id = stable_code_package_id(
            code_package_config_id=stable_code_package_config_id(
                config_key=code_package_source_config_key(
                    manifest_kind="aware_pane_toml",
                    surface="representation",
                )
            ),
            package_name=source_package_name,
            language="python",
        )
        projection_experience_view_id = uuid4()
        pane_config_id = stable_pane_config_id(
            projection_experience_view_id=projection_experience_view_id,
            name=pane_name,
        )
        pane_package_id = stable_pane_package_id(name=pane_name)
        config_lane = runtime.bind(
            branch_id=pane_config_id,
            projection="PaneConfig",
            actor_id=ids["actor_id"],
        )
        with config_lane.activate(commit=True, publish=False):
            await PaneConfig.build(
                name=pane_name,
                projection_experience_view_id=projection_experience_view_id,
                pane_kind="door",
                view_ref="door.default",
                description="Door pane package proof",
            )

        package_lane = runtime.bind(
            branch_id=pane_package_id,
            projection="PanePackage",
            actor_id=ids["actor_id"],
        )
        with package_lane.activate(commit=True, publish=False):
            await PanePackage.build(
                name=pane_name,
                pane_config_id=pane_config_id,
                source_code_package_id=source_code_package_id,
                fqn_prefix="aware.home_story.panes",
                pane_name=pane_name,
                version_number=5,
                title="Door Control Pane",
                description="Pane package module proof",
                aware_pane_version=1,
                manifest_relative_path="panes/door_control/aware.pane.toml",
                package_root="panes/door_control",
                sources_root="panes/door_control/python",
                include_paths=["python/**/*.py"],
                exclude_paths=["python/**/__pycache__/**"],
                force_fresh_scan=False,
                python={
                    "package_path": "python/aware_door_control_pane",
                    "import_root": "aware_door_control_pane",
                },
                dart={
                    "package_path": "dart/aware_door_control_pane",
                    "package_name": "aware_door_control_pane",
                },
            )

        committed_config = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=pane_config_id,
            projection_name="PaneConfig",
            root_id=pane_config_id,
            root_type=PaneConfig,
        )
        committed_package = await rehydrate_lane_root_from_head(
            runtime=runtime,
            aware_root=aware_root,
            branch_id=pane_package_id,
            projection_name="PanePackage",
            root_id=pane_package_id,
            root_type=PanePackage,
        )

        assert committed_config.id == pane_config_id
        assert committed_config.name == pane_name
        assert committed_config.pane_kind == "door"
        assert committed_package.id == pane_package_id
        assert committed_package.name == pane_name
        assert committed_package.pane_config_id == pane_config_id
        assert committed_package.source_code_package_id == source_code_package_id
        assert committed_package.fqn_prefix == "aware.home_story.panes"
        assert committed_package.pane_name == pane_name
        assert committed_package.version_number == 5
        assert committed_package.title == "Door Control Pane"
        assert committed_package.description == "Pane package module proof"
        assert committed_package.aware_pane_version == 1
        assert committed_package.manifest_relative_path == ("panes/door_control/aware.pane.toml")
        assert committed_package.package_root == "panes/door_control"
        assert committed_package.sources_root == "panes/door_control/python"
        assert list(committed_package.include_paths) == ["python/**/*.py"]
        assert list(committed_package.exclude_paths) == ["python/**/__pycache__/**"]
        assert committed_package.force_fresh_scan is False
        assert dict(committed_package.python) == {
            "package_path": "python/aware_door_control_pane",
            "import_root": "aware_door_control_pane",
        }
        assert dict(committed_package.dart) == {
            "package_path": "dart/aware_door_control_pane",
            "package_name": "aware_door_control_pane",
        }


def _runtime_ids() -> dict[str, UUID]:
    return {
        "environment_id": uuid4(),
        "process_id": uuid4(),
        "thread_id": uuid4(),
        "actor_id": uuid4(),
    }


def _interface_source_code_package_id(*, package_name: str) -> UUID:
    return stable_code_package_id(
        code_package_config_id=stable_code_package_config_id(
            config_key=code_package_source_config_key(
                manifest_kind="aware_interface_toml",
                surface="representation",
            )
        ),
        package_name=package_name,
        language="aware",
    )
