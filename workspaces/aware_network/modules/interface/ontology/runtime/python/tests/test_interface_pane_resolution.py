from __future__ import annotations

from uuid import uuid4

import pytest

from aware_interface import (
    InterfaceRuntimeFocusState,
    InterfaceWindowLayoutSectionState,
    InterfaceWindowLayoutState,
    InterfaceResolvedSectionStateAddress,
    resolve_bundle_backed_pane_descriptors,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
    InterfacePaneConfigBundle,
    InterfacePaneProjectionExperienceViewBundle,
    InterfacePaneSectionMountBundle,
    InterfacePaneViewInvocationActionBundle,
    InterfaceWindowConfigBundle,
    InterfaceWindowConfigLayoutBundle,
    InterfaceWindowLayoutSectionBundle,
)


def test_resolve_bundle_backed_pane_descriptors_prefers_bundle_section_mounts() -> None:
    section_config_id = uuid4()
    pane_config_id = uuid4()
    pane_package_id = uuid4()
    projection_view_id = uuid4()
    layout_section_id = uuid4()
    section_focus_scope_id = uuid4()
    focus_scope_id = uuid4()
    branch_id = uuid4()

    window_layout = InterfaceWindowLayoutState(
        source_kind="interface_bootstrap",
        window_key="bootstrap",
        layout_key="bootstrap.control-plane",
        sections=(
            InterfaceWindowLayoutSectionState(
                section_key="actions",
                layout_config_section_config_id=section_config_id,
                title="Action Center",
                is_visible=True,
                projection_view_id="entry.control-plane",
                pane_key="action_center",
            ),
        ),
    )
    bundle = InterfaceConfigBundle(
        interface_config_id=uuid4(),
        interface_package_id=uuid4(),
        interface_package_name="aware-control-plane-interface",
        name="aware-control-plane",
        pane_configs=[
            InterfacePaneConfigBundle(
                pane_config_id=pane_config_id,
                pane_package_id=pane_package_id,
                pane_package_name="identity-pane-package",
                name="Identity Admission",
                pane_kind="identity",
                description="Identity signup and actor admission.",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=projection_view_id,
                        view_ref="identity.default",
                        invocation_actions=[
                            InterfacePaneViewInvocationActionBundle(
                                projection_experience_view_invocation_action_id=uuid4(),
                                action_key="signup",
                                action_kind="api",
                                target_ref="identity.signup.signup",
                                label="Sign up",
                                receipt_policy=None,
                                confirmation_policy=None,
                                optimistic_policy=None,
                            ),
                            InterfacePaneViewInvocationActionBundle(
                                projection_experience_view_invocation_action_id=uuid4(),
                                action_key="signup_sdk",
                                action_kind="sdk",
                                target_ref="identity_sdk.signup",
                                label="Sign up via SDK",
                                receipt_policy=None,
                                confirmation_policy=None,
                                optimistic_policy=None,
                            ),
                        ],
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=section_config_id,
                            )
                        ],
                    )
                ],
            )
        ],
    )

    descriptors = resolve_bundle_backed_pane_descriptors(
        window_layout=window_layout,
        interface_config_bundle=bundle,
        projection_view_id_fallback="entry.control-plane",
        section_state_addresses={
            "actions": InterfaceResolvedSectionStateAddress(
                section_key="actions",
                layout_section_id=layout_section_id,
                section_focus_scope_id=section_focus_scope_id,
                focus_scope_id=focus_scope_id,
                branch_id=branch_id,
                state_projection_hash="sha256:test:actions",
            ),
        },
        default_pane_kind=lambda section: section.pane_key or section.section_key,
        state_source_kind_for_section=lambda _section_key: "allowed_actions",
        summary_for_section=lambda _section_key, _projection_view_id: None,
        action_keys_for_section=lambda _section_key: ("signup_via_profile",),
    )

    assert len(descriptors) == 1
    descriptor = descriptors[0]
    assert descriptor.section_key == "actions"
    assert descriptor.layout_config_section_config_id == section_config_id
    assert descriptor.layout_section_id == layout_section_id
    assert descriptor.section_focus_scope_id == section_focus_scope_id
    assert descriptor.focus_scope_id == focus_scope_id
    assert descriptor.branch_id == branch_id
    assert descriptor.pane_kind == "identity"
    assert descriptor.pane_config_id == pane_config_id
    assert descriptor.pane_package_id == pane_package_id
    assert descriptor.pane_package_name == "identity-pane-package"
    assert descriptor.projection_view_id == str(projection_view_id)
    assert descriptor.title == "Action Center"
    assert descriptor.summary == "Identity signup and actor admission."
    assert descriptor.narrative_key == "bootstrap.control-plane.actions"
    assert descriptor.state_source_kind == "allowed_actions"
    assert descriptor.state_projection_hash == "sha256:test:actions"
    assert descriptor.action_keys == (
        "signup_via_profile",
        "signup",
        "signup_sdk",
    )
    assert tuple(action.target_ref for action in descriptor.action_targets) == (
        "identity.signup.signup",
        "identity_sdk.signup",
    )


def test_resolve_bundle_backed_pane_descriptors_falls_back_without_bundle_match() -> (
    None
):
    section_config_id = uuid4()
    window_layout = InterfaceWindowLayoutState(
        source_kind="interface_bootstrap",
        window_key="bootstrap",
        layout_key="bootstrap.control-plane",
        sections=(
            InterfaceWindowLayoutSectionState(
                section_key="context",
                layout_config_section_config_id=section_config_id,
                title="Runtime Context",
                is_visible=True,
                projection_view_id="entry.control-plane",
                pane_key="runtime_context",
            ),
        ),
    )

    descriptors = resolve_bundle_backed_pane_descriptors(
        window_layout=window_layout,
        interface_config_bundle=None,
        projection_view_id_fallback="entry.control-plane",
        section_state_addresses=None,
        default_pane_kind=lambda section: section.pane_key or section.section_key,
        state_source_kind_for_section=lambda _section_key: "resolved_view",
        summary_for_section=lambda _section_key, _projection_view_id: "Context summary",
        action_keys_for_section=lambda _section_key: (),
    )

    assert len(descriptors) == 1
    descriptor = descriptors[0]
    assert descriptor.layout_config_section_config_id == section_config_id
    assert descriptor.pane_kind == "runtime_context"
    assert descriptor.pane_config_id is None
    assert descriptor.pane_package_id is None
    assert descriptor.pane_package_name is None
    assert descriptor.narrative_key == "bootstrap.control-plane.context"
    assert descriptor.summary == "Context summary"


def test_resolve_bundle_backed_pane_descriptors_supports_multi_mount_sections() -> None:
    workspace_section_id = uuid4()
    controls_left_section_id = uuid4()
    controls_right_section_id = uuid4()
    bundle = InterfaceConfigBundle(
        interface_config_id=uuid4(),
        interface_package_id=uuid4(),
        interface_package_name="home-story-interface",
        name="aware_app",
        window_configs=[
            InterfaceWindowConfigBundle(
                interface_config_window_config_id=uuid4(),
                window_config_id=uuid4(),
                key="main",
                layout_configs=[
                    InterfaceWindowConfigLayoutBundle(
                        window_config_layout_config_id=uuid4(),
                        layout_config_id=uuid4(),
                        key="configuration_map",
                        is_default=True,
                        sections=[
                            InterfaceWindowLayoutSectionBundle(
                                layout_config_section_config_id=workspace_section_id,
                                key="workspace",
                            ),
                            InterfaceWindowLayoutSectionBundle(
                                layout_config_section_config_id=controls_left_section_id,
                                key="controls_left",
                            ),
                            InterfaceWindowLayoutSectionBundle(
                                layout_config_section_config_id=controls_right_section_id,
                                key="controls_right",
                            ),
                        ],
                    )
                ],
            )
        ],
        pane_configs=[
            InterfacePaneConfigBundle(
                pane_config_id=uuid4(),
                pane_package_id=uuid4(),
                pane_package_name="home-story-home-overview-pane",
                name="home_overview",
                pane_kind="home",
                narrative_key="home.primary",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=uuid4(),
                        view_ref="home_story.overview.home",
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=workspace_section_id,
                            )
                        ],
                    )
                ],
            ),
            InterfacePaneConfigBundle(
                pane_config_id=uuid4(),
                pane_package_id=uuid4(),
                pane_package_name="home-story-door-control-pane",
                name="door_control",
                pane_kind="door",
                narrative_key="security.control",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=uuid4(),
                        view_ref="home_story.security.door",
                        invocation_actions=[
                            InterfacePaneViewInvocationActionBundle(
                                projection_experience_view_invocation_action_id=uuid4(),
                                action_key="unlock_door",
                                action_kind="api",
                                target_ref="home_devices.unlock_door.unlock_door",
                            )
                        ],
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=controls_left_section_id,
                            )
                        ],
                    )
                ],
            ),
            InterfacePaneConfigBundle(
                pane_config_id=uuid4(),
                pane_package_id=uuid4(),
                pane_package_name="home-story-tv-status-pane",
                name="tv_status",
                pane_kind="tv",
                narrative_key="entertainment.control",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=uuid4(),
                        view_ref="home_story.entertainment.tv",
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=controls_right_section_id,
                            )
                        ],
                    )
                ],
            ),
        ],
    )
    workspace_layout_section_id = uuid4()
    controls_left_layout_section_id = uuid4()
    controls_right_layout_section_id = uuid4()
    focus_scope_id = uuid4()
    branch_id = uuid4()

    window_layout = InterfaceWindowLayoutState(
        source_kind="interface_bundle",
        window_key="main",
        layout_key="configuration_map",
        sections=(
            InterfaceWindowLayoutSectionState(
                section_key="workspace",
                layout_config_section_config_id=workspace_section_id,
                title="Workspace",
                is_visible=True,
                projection_view_id="home_story.overview.home",
            ),
            InterfaceWindowLayoutSectionState(
                section_key="controls_left",
                layout_config_section_config_id=controls_left_section_id,
                title="Controls Left",
                is_visible=True,
                projection_view_id="home_story.security.door",
            ),
            InterfaceWindowLayoutSectionState(
                section_key="controls_right",
                layout_config_section_config_id=controls_right_section_id,
                title="Controls Right",
                is_visible=True,
                projection_view_id="home_story.entertainment.tv",
            ),
        ),
    )

    descriptors = resolve_bundle_backed_pane_descriptors(
        window_layout=window_layout,
        interface_config_bundle=bundle,
        projection_view_id_fallback="home_story.overview.home",
        section_state_addresses={
            "workspace": InterfaceResolvedSectionStateAddress(
                section_key="workspace",
                layout_section_id=workspace_layout_section_id,
                section_focus_scope_id=uuid4(),
                focus_scope_id=focus_scope_id,
                branch_id=branch_id,
                state_projection_hash="section:configuration_map:workspace",
            ),
            "controls_left": InterfaceResolvedSectionStateAddress(
                section_key="controls_left",
                layout_section_id=controls_left_layout_section_id,
                section_focus_scope_id=uuid4(),
                focus_scope_id=focus_scope_id,
                branch_id=branch_id,
                state_projection_hash="section:configuration_map:controls_left",
            ),
            "controls_right": InterfaceResolvedSectionStateAddress(
                section_key="controls_right",
                layout_section_id=controls_right_layout_section_id,
                section_focus_scope_id=uuid4(),
                focus_scope_id=focus_scope_id,
                branch_id=branch_id,
                state_projection_hash="section:configuration_map:controls_right",
            ),
        },
        default_pane_kind=lambda section: section.pane_key or section.section_key,
        state_source_kind_for_section=lambda _section_key: "resolved_view",
        summary_for_section=lambda section_key, _projection_view_id: f"{section_key} summary",
        action_keys_for_section=lambda _section_key: (),
    )

    assert [(pane.section_key, pane.pane_kind) for pane in descriptors] == [
        ("workspace", "home"),
        ("controls_left", "door"),
        ("controls_right", "tv"),
    ]
    assert descriptors[0].title == "Workspace"
    assert descriptors[0].narrative_key == "home.primary"
    assert descriptors[0].layout_section_id == workspace_layout_section_id
    assert descriptors[0].state_projection_hash == "section:configuration_map:workspace"
    assert descriptors[0].pane_package_name == "home-story-home-overview-pane"
    assert descriptors[0].pane_package_id is not None
    assert descriptors[1].title == "Controls Left"
    assert descriptors[1].narrative_key == "security.control"
    assert descriptors[1].layout_section_id == controls_left_layout_section_id
    assert (
        descriptors[1].state_projection_hash
        == "section:configuration_map:controls_left"
    )
    assert descriptors[1].action_keys
    assert descriptors[1].pane_package_name == "home-story-door-control-pane"
    assert descriptors[1].pane_package_id is not None
    assert descriptors[2].title == "Controls Right"
    assert descriptors[2].narrative_key == "entertainment.control"
    assert descriptors[2].layout_section_id == controls_right_layout_section_id
    assert (
        descriptors[2].state_projection_hash
        == "section:configuration_map:controls_right"
    )
    assert descriptors[2].pane_package_name == "home-story-tv-status-pane"
    assert descriptors[2].pane_package_id is not None


def test_resolve_bundle_backed_pane_descriptors_prefers_active_observable_over_other_candidates() -> (
    None
):
    section_config_id = uuid4()
    graph_observable_id = uuid4()
    code_observable_id = uuid4()
    code_state_model_id = uuid4()
    window_layout = InterfaceWindowLayoutState(
        source_kind="interface_bundle",
        window_key="main",
        layout_key="ide_workbench",
        sections=(
            InterfaceWindowLayoutSectionState(
                section_key="primary",
                layout_config_section_config_id=section_config_id,
                title="Primary",
                is_visible=True,
            ),
        ),
    )
    bundle = InterfaceConfigBundle(
        interface_config_id=uuid4(),
        interface_package_id=uuid4(),
        interface_package_name="aware-workspace-interface",
        name="aware_workspace",
        pane_configs=[
            InterfacePaneConfigBundle(
                pane_config_id=uuid4(),
                pane_package_id=uuid4(),
                pane_package_name="workspace-graph-pane",
                name="Graph",
                pane_kind="ocg_viewer",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=uuid4(),
                        object_projection_graph_observable_id=graph_observable_id,
                        view_ref="workspace.graph.default",
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=section_config_id,
                            )
                        ],
                    )
                ],
                api_capability_endpoints=[],
            ),
            InterfacePaneConfigBundle(
                pane_config_id=uuid4(),
                pane_package_id=uuid4(),
                pane_package_name="workspace-code-pane",
                name="Code",
                pane_kind="repository_editor",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=uuid4(),
                        object_projection_graph_observable_id=code_observable_id,
                        state_model_id=code_state_model_id,
                        view_ref="workspace.code.default",
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=section_config_id,
                            )
                        ],
                    )
                ],
                api_capability_endpoints=[],
            ),
        ],
    )

    descriptors = resolve_bundle_backed_pane_descriptors(
        window_layout=window_layout,
        interface_config_bundle=bundle,
        active_focus=InterfaceRuntimeFocusState(
            layout_key="ide_workbench",
            section_key="primary",
            observable_id=code_observable_id,
        ),
        projection_view_id_fallback=None,
        section_state_addresses={
            "primary": InterfaceResolvedSectionStateAddress(
                section_key="primary",
                observable_id=code_observable_id,
            ),
        },
        default_pane_kind=lambda section: section.pane_key or section.section_key,
        state_source_kind_for_section=lambda _section_key: "section_focus_scope_lane",
        summary_for_section=lambda _section_key, _projection_view_id: None,
        action_keys_for_section=lambda _section_key: (),
    )

    assert len(descriptors) == 1
    assert descriptors[0].pane_kind == "repository_editor"
    assert descriptors[0].object_projection_graph_observable_id == code_observable_id
    assert descriptors[0].state_model_id == code_state_model_id
    assert descriptors[0].state_source_kind == "experience_view_state"


def test_resolve_bundle_backed_pane_descriptors_raises_for_ambiguous_active_observable_bindings() -> (
    None
):
    section_config_id = uuid4()
    shared_observable_id = uuid4()
    window_layout = InterfaceWindowLayoutState(
        source_kind="interface_bundle",
        window_key="main",
        layout_key="ide_workbench",
        sections=(
            InterfaceWindowLayoutSectionState(
                section_key="primary",
                layout_config_section_config_id=section_config_id,
                title="Primary",
                is_visible=True,
            ),
        ),
    )
    bundle = InterfaceConfigBundle(
        interface_config_id=uuid4(),
        interface_package_id=uuid4(),
        interface_package_name="aware-workspace-interface",
        name="aware_workspace",
        pane_configs=[
            InterfacePaneConfigBundle(
                pane_config_id=uuid4(),
                pane_package_id=uuid4(),
                pane_package_name="workspace-graph-pane",
                name="Graph",
                pane_kind="ocg_viewer",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=uuid4(),
                        object_projection_graph_observable_id=shared_observable_id,
                        view_ref="workspace.primary.graph",
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=section_config_id,
                            )
                        ],
                    )
                ],
                api_capability_endpoints=[],
            ),
            InterfacePaneConfigBundle(
                pane_config_id=uuid4(),
                pane_package_id=uuid4(),
                pane_package_name="workspace-code-pane",
                name="Code",
                pane_kind="repository_editor",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=uuid4(),
                        object_projection_graph_observable_id=shared_observable_id,
                        view_ref="workspace.primary.code",
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=section_config_id,
                            )
                        ],
                    )
                ],
                api_capability_endpoints=[],
            ),
        ],
    )

    with pytest.raises(
        ValueError, match="multiple `observable -> experience view -> pane` bindings"
    ):
        _ = resolve_bundle_backed_pane_descriptors(
            window_layout=window_layout,
            interface_config_bundle=bundle,
            active_focus=InterfaceRuntimeFocusState(
                layout_key="ide_workbench",
                section_key="primary",
                observable_id=shared_observable_id,
            ),
            projection_view_id_fallback=None,
            section_state_addresses=None,
            default_pane_kind=lambda section: section.pane_key or section.section_key,
            state_source_kind_for_section=lambda _section_key: "section_focus_scope_lane",
            summary_for_section=lambda _section_key, _projection_view_id: None,
            action_keys_for_section=lambda _section_key: (),
        )


def test_resolve_bundle_backed_pane_descriptors_does_not_select_unresolved_multiple_candidates() -> (
    None
):
    section_config_id = uuid4()
    graph_observable_id = uuid4()
    code_observable_id = uuid4()
    window_layout = InterfaceWindowLayoutState(
        source_kind="interface_bundle",
        window_key="main",
        layout_key="ide_workbench",
        sections=(
            InterfaceWindowLayoutSectionState(
                section_key="primary",
                layout_config_section_config_id=section_config_id,
                title="Primary",
                is_visible=True,
            ),
        ),
    )
    bundle = InterfaceConfigBundle(
        interface_config_id=uuid4(),
        interface_package_id=uuid4(),
        interface_package_name="aware-workspace-interface",
        name="aware_workspace",
        pane_configs=[
            InterfacePaneConfigBundle(
                pane_config_id=uuid4(),
                pane_package_id=uuid4(),
                pane_package_name="workspace-graph-pane",
                name="Graph",
                pane_kind="ocg_viewer",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=uuid4(),
                        object_projection_graph_observable_id=graph_observable_id,
                        view_ref="workspace.graph.default",
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=section_config_id,
                            )
                        ],
                    )
                ],
                api_capability_endpoints=[],
            ),
            InterfacePaneConfigBundle(
                pane_config_id=uuid4(),
                pane_package_id=uuid4(),
                pane_package_name="workspace-code-pane",
                name="Code",
                pane_kind="repository_editor",
                projection_experience_views=[
                    InterfacePaneProjectionExperienceViewBundle(
                        binding_id=uuid4(),
                        projection_experience_view_id=uuid4(),
                        object_projection_graph_observable_id=code_observable_id,
                        view_ref="workspace.code.default",
                        section_mounts=[
                            InterfacePaneSectionMountBundle(
                                mount_id=uuid4(),
                                layout_config_section_config_id=section_config_id,
                            )
                        ],
                    )
                ],
                api_capability_endpoints=[],
            ),
        ],
    )

    descriptors = resolve_bundle_backed_pane_descriptors(
        window_layout=window_layout,
        interface_config_bundle=bundle,
        active_focus=None,
        projection_view_id_fallback=None,
        section_state_addresses=None,
        default_pane_kind=lambda section: section.pane_key or section.section_key,
        state_source_kind_for_section=lambda _section_key: "section_focus_scope_lane",
        summary_for_section=lambda _section_key, _projection_view_id: None,
        action_keys_for_section=lambda _section_key: (),
    )

    assert len(descriptors) == 1
    assert descriptors[0].pane_config_id is None
    assert descriptors[0].object_projection_graph_observable_id is None
    assert descriptors[0].state_source_kind == "section_focus_scope_lane"
