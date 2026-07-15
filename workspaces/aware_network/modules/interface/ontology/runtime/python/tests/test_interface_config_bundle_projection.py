from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[8]
for _path in (
    _REPO_ROOT,
    _REPO_ROOT
    / "workspaces"
    / "aware_network"
    / "modules"
    / "interface"
    / "ontology"
    / "runtime"
    / "python",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_attention_ontology.layout.layout_config import LayoutConfig  # noqa: E402
from aware_attention_ontology.layout.layout_config_section_config import (  # noqa: E402
    LayoutConfigSectionConfig,
)
from aware_api_ontology.api.api_view import ApiView  # noqa: E402
from aware_api_ontology.api.api_view_capability_endpoint import (  # noqa: E402
    ApiViewCapabilityEndpoint,
)
from aware_experience_ontology.projection.projection_experience_view import (  # noqa: E402
    ProjectionExperienceView,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (  # noqa: E402,E501
    ExperienceInvocationActionTargetKind,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (  # noqa: E402,E501
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (  # noqa: E402,E501
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_interface.config_bundle_projection import (  # noqa: E402
    InterfaceConfigBundleProjectionError,
    project_interface_config_bundle_from_committed_package,
)
from aware_interface.package_ref_resolution import (  # noqa: E402
    InterfaceRuntimePackageRef,
    ResolvedInterfaceRuntimePackageRef,
)
from aware_interface_ontology.interface.interface_config import (
    InterfaceConfig,
)  # noqa: E402
from aware_interface_ontology.interface.interface_config_pane_config import (  # noqa: E402
    InterfaceConfigPaneConfig,
)
from aware_interface_ontology.interface.interface_config_pane_config_section_config import (  # noqa: E402,E501
    InterfaceConfigPaneConfigSectionConfig,
)
from aware_interface_ontology.interface.interface_config_window_config import (  # noqa: E402
    InterfaceConfigWindowConfig,
)
from aware_interface_ontology.interface.interface_package import (
    InterfacePackage,
)  # noqa: E402
from aware_interface_ontology.interface.interface_package_pane_package import (  # noqa: E402
    InterfacePackagePanePackage,
)
from aware_interface_ontology.interface.pane_config import PaneConfig  # noqa: E402
from aware_interface_ontology.interface.pane_package import PanePackage  # noqa: E402
from aware_interface_ontology.interface.window_config import WindowConfig  # noqa: E402
from aware_interface_ontology.interface.window_config_layout_config import (  # noqa: E402
    WindowConfigLayoutConfig,
)
from aware_meta_ontology.graph.projection.object_projection_graph_observable import (  # noqa: E402
    ObjectProjectionGraphObservable,
)


def test_project_interface_config_bundle_from_committed_package_derives_observable_from_experience(
    tmp_path: Path,
) -> None:
    resolved = _resolved_interface_ref(tmp_path=tmp_path)

    bundle = project_interface_config_bundle_from_committed_package(resolved)

    assert bundle.interface_package_id == resolved.interface_package_id
    assert bundle.interface_package_name == "aware-workspace-interface"
    assert bundle.apis == []
    assert bundle.window_configs[0].key == "main"
    assert bundle.window_configs[0].layout_configs[0].key == "ide"
    assert bundle.window_configs[0].layout_configs[0].is_default is True
    assert bundle.window_configs[0].layout_configs[0].sections[0].key == "primary"

    pane = bundle.pane_configs[0]
    assert pane.name == "workspace_control"
    assert pane.pane_package_name == "aware-workspace-control-pane"
    assert pane.narrative_key == "workspace.control"
    assert pane.api_capability_endpoints == []
    assert pane.sdk_operations == []

    projection_view = pane.projection_experience_views[0]
    assert projection_view.view_ref == "aware_workspace.control.main"
    assert projection_view.projection_view_key == "control.main"
    assert projection_view.object_projection_graph_observable_id == _OBSERVABLE_ID
    assert projection_view.state_model_id == _STATE_MODEL_ID
    assert len(projection_view.invocation_actions) == 2
    assert projection_view.invocation_actions[0].action_key == "load_status"
    assert projection_view.invocation_actions[0].action_kind == "api"
    assert projection_view.invocation_actions[0].target_ref == "workspace.status.status"
    assert (
        projection_view.invocation_actions[0].api_capability_endpoint_id
        == _API_CAPABILITY_ENDPOINT_ID
    )
    assert projection_view.invocation_actions[1].action_key == "refresh_status"
    assert projection_view.invocation_actions[1].action_kind == "api"
    assert projection_view.invocation_actions[1].target_ref == "workspace.status.status"
    assert (
        projection_view.invocation_actions[1].api_capability_endpoint_id
        == _API_CAPABILITY_ENDPOINT_ID
    )


def test_project_interface_config_bundle_rejects_missing_projection_view_hydration(
    tmp_path: Path,
) -> None:
    resolved = _resolved_interface_ref(
        tmp_path=tmp_path,
        hydrate_projection_experience_view=False,
    )

    with pytest.raises(
        InterfaceConfigBundleProjectionError,
        match="missing hydrated projection_experience_view",
    ):
        project_interface_config_bundle_from_committed_package(resolved)


_INTERFACE_PACKAGE_ID = uuid4()
_INTERFACE_CONFIG_ID = uuid4()
_PANE_CONFIG_ID = uuid4()
_PANE_PACKAGE_ID = uuid4()
_WINDOW_CONFIG_ID = uuid4()
_LAYOUT_CONFIG_ID = uuid4()
_SECTION_CONFIG_ID = uuid4()
_PROJECTION_EXPERIENCE_VIEW_ID = uuid4()
_STATE_MODEL_ID = uuid4()
_API_VIEW_ID = uuid4()
_API_CAPABILITY_ENDPOINT_ID = uuid4()
_OBSERVABLE_ID = uuid4()


def _resolved_interface_ref(
    *,
    tmp_path: Path,
    hydrate_projection_experience_view: bool = True,
) -> ResolvedInterfaceRuntimePackageRef:
    manifest_path = tmp_path / "interfaces" / "aware_workspace" / "aware.interface.toml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("aware_interface = 1\n", encoding="utf-8")

    section_config = LayoutConfigSectionConfig.model_construct(
        id=_SECTION_CONFIG_ID,
        layout_config_id=_LAYOUT_CONFIG_ID,
        section_key="primary",
        order=0,
    )
    layout_config = LayoutConfig.model_construct(
        id=_LAYOUT_CONFIG_ID,
        key="ide",
        title="IDE",
        section_configs=[section_config],
    )
    layout_binding = WindowConfigLayoutConfig.model_construct(
        id=uuid4(),
        window_config_id=_WINDOW_CONFIG_ID,
        layout_config_id=_LAYOUT_CONFIG_ID,
        layout_config=layout_config,
        is_default=True,
    )
    window_config = WindowConfig.model_construct(
        id=_WINDOW_CONFIG_ID,
        key="main",
        layout_configs=[layout_binding],
    )
    window_binding = InterfaceConfigWindowConfig.model_construct(
        id=uuid4(),
        interface_config_id=_INTERFACE_CONFIG_ID,
        window_config_id=_WINDOW_CONFIG_ID,
        window_config=window_config,
    )

    observable = ObjectProjectionGraphObservable.model_construct(
        id=_OBSERVABLE_ID,
        object_projection_graph_identity_id=uuid4(),
        key="workspace:control",
        observable_key="control",
    )
    projection_view = (
        ProjectionExperienceView.model_construct(
            id=_PROJECTION_EXPERIENCE_VIEW_ID,
            projection_experience_id=uuid4(),
            api_view_id=_API_VIEW_ID,
            api_view=ApiView.model_construct(
                id=_API_VIEW_ID,
                api_id=uuid4(),
                object_projection_graph_observable_id=_OBSERVABLE_ID,
                object_projection_graph_observable=observable,
                state_model_id=_STATE_MODEL_ID,
                name="control_main",
                view_ref="workspace.control_main",
            ),
            name="main",
            invocation_action_configs=[
                ProjectionExperienceViewInvocationActionConfig.model_construct(
                    id=uuid4(),
                    projection_experience_view_id=_PROJECTION_EXPERIENCE_VIEW_ID,
                    api_view_capability_endpoint_id=uuid4(),
                    api_view_capability_endpoint=ApiViewCapabilityEndpoint.model_construct(
                        id=uuid4(),
                        api_view_id=_API_VIEW_ID,
                        action_key="load_status",
                        api_capability_endpoint_id=_API_CAPABILITY_ENDPOINT_ID,
                        endpoint_ref="workspace.status.status",
                    ),
                    experience_invocation_action_config_id=uuid4(),
                    experience_invocation_action_config=ExperienceInvocationActionConfig.model_construct(
                        id=uuid4(),
                        projection_experience_id=uuid4(),
                        target_kind=ExperienceInvocationActionTargetKind.api,
                        api_capability_endpoint_id=_API_CAPABILITY_ENDPOINT_ID,
                    ),
                    action_key="load_status",
                    label="Load status",
                ),
                ProjectionExperienceViewInvocationActionConfig.model_construct(
                    id=uuid4(),
                    projection_experience_view_id=_PROJECTION_EXPERIENCE_VIEW_ID,
                    api_view_capability_endpoint_id=uuid4(),
                    api_view_capability_endpoint=ApiViewCapabilityEndpoint.model_construct(
                        id=uuid4(),
                        api_view_id=_API_VIEW_ID,
                        action_key="refresh_status",
                        api_capability_endpoint_id=_API_CAPABILITY_ENDPOINT_ID,
                        endpoint_ref="workspace.status.status",
                    ),
                    experience_invocation_action_config_id=uuid4(),
                    experience_invocation_action_config=ExperienceInvocationActionConfig.model_construct(
                        id=uuid4(),
                        projection_experience_id=uuid4(),
                        target_kind=ExperienceInvocationActionTargetKind.api,
                        api_capability_endpoint_id=_API_CAPABILITY_ENDPOINT_ID,
                    ),
                    action_key="refresh_status",
                    label="Refresh status",
                ),
            ],
        )
        if hydrate_projection_experience_view
        else None
    )
    pane_config = PaneConfig.model_construct(
        id=_PANE_CONFIG_ID,
        projection_experience_view_id=_PROJECTION_EXPERIENCE_VIEW_ID,
        projection_experience_view=projection_view,
        name="workspace_control",
        pane_kind="workspace",
        view_ref="aware_workspace.control.main",
    )
    pane_join_id = uuid4()
    section_mount = InterfaceConfigPaneConfigSectionConfig.model_construct(
        id=uuid4(),
        interface_config_pane_config_id=pane_join_id,
        layout_config_section_config_id=_SECTION_CONFIG_ID,
        is_default=True,
    )
    pane_join = InterfaceConfigPaneConfig.model_construct(
        id=pane_join_id,
        interface_config_id=_INTERFACE_CONFIG_ID,
        pane_config_id=_PANE_CONFIG_ID,
        pane_config=pane_config,
        narrative_key="workspace.control",
        section_mounts=[section_mount],
    )
    interface_config = InterfaceConfig.model_construct(
        id=_INTERFACE_CONFIG_ID,
        name="aware_workspace",
        interface_config_window_configs=[window_binding],
        interface_config_pane_configs=[pane_join],
    )

    pane_package = PanePackage.model_construct(
        id=_PANE_PACKAGE_ID,
        name="aware-workspace-control-pane",
        pane_config_id=_PANE_CONFIG_ID,
    )
    pane_package_binding = InterfacePackagePanePackage.model_construct(
        id=uuid4(),
        interface_package_id=_INTERFACE_PACKAGE_ID,
        pane_package_id=_PANE_PACKAGE_ID,
        pane_package=pane_package,
    )
    interface_package = InterfacePackage.model_construct(
        id=_INTERFACE_PACKAGE_ID,
        name="aware-workspace-interface",
        interface_config_id=_INTERFACE_CONFIG_ID,
        interface_config=interface_config,
        manifest_relative_path=manifest_path.relative_to(tmp_path).as_posix(),
        pane_packages=[pane_package_binding],
    )

    package_ref = InterfaceRuntimePackageRef(
        family_key="interface",
        package_kind="interface",
        package_name="aware-workspace-interface",
    )
    return ResolvedInterfaceRuntimePackageRef(
        package_ref=package_ref,
        materialized_workspace_root=tmp_path,
        manifest_path=manifest_path,
        manifest_relative_path=manifest_path.relative_to(tmp_path).as_posix(),
        package_name="aware-workspace-interface",
        fqn_prefix="aware_workspace_interface",
        config_bundle_path=None,
        interface_package_id=_INTERFACE_PACKAGE_ID,
        interface_config_id=_INTERFACE_CONFIG_ID,
        interface_config_object_instance_graph_commit_id=uuid4(),
        interface_package=interface_package,
        interface_config=interface_config,
    )
