from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest

from _meta_runtime_support import (
    build_interface_meta_runtime,
    isolated_meta_aware_root,
)
from _interface_runtime_test_paths import REPO_ROOT


@pytest.mark.asyncio
async def test_interface_config_bundle_materializes_canonical_interface_ontology(tmp_path: Path, monkeypatch) -> None:
    repo_root = REPO_ROOT

    monkeypatch.syspath_prepend(
        str(repo_root / "workspaces" / "aware_network" / "modules" / "interface" / "ontology" / "runtime" / "python")
    )

    import aware_interface_service_dto  # noqa: F401
    import aware_interface_ontology  # noqa: F401

    from aware_interface.ontology.materialization import materialize_interface_config_bundle
    from aware_interface_service_dto.comms.models.interface_config_bundle import (
        InterfaceConfigBundle,
        InterfacePaneConfigBundle,
        InterfacePaneProjectionExperienceViewBundle,
        InterfacePaneSectionMountBundle,
        InterfaceWindowConfigBundle,
        InterfaceWindowConfigLayoutBundle,
        InterfaceWindowLayoutSectionBundle,
    )
    from aware_attention_ontology.stable_ids import stable_layout_config_id
    from aware_interface_ontology.stable_ids import (
        stable_interface_config_id,
        stable_interface_config_pane_config_id,
        stable_interface_config_pane_config_section_config_id,
        stable_interface_package_id,
        stable_interface_config_window_config_id,
        stable_pane_config_id,
        stable_window_config_id,
        stable_window_config_layout_config_id,
    )

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = context.index
        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()

        namespace = uuid5(NAMESPACE_URL, "aware://tests/interface/config-materialization")
        interface_package_name = "aware-control-plane"
        interface_config_name = "aware-control-plane"
        pane_name = "identity"
        pane_kind = "identity"
        pane_narrative_key = "identity.story"
        window_key = "main"
        layout_key = "workspace"
        interface_config_id = stable_interface_config_id(name=interface_config_name)
        interface_package_id = stable_interface_package_id(name=interface_package_name)
        window_config_id = stable_window_config_id(key=window_key)
        layout_config_id = stable_layout_config_id(key=layout_key)
        projection_experience_view_id = uuid5(namespace, "projection-experience-view:identity.default")
        pane_config_id = stable_pane_config_id(
            projection_experience_view_id=projection_experience_view_id,
            name=pane_name,
        )
        layout_config_section_config_id = uuid5(namespace, "layout-config-section:left.identity")
        interface_config_window_config_id = stable_interface_config_window_config_id(
            interface_config_id=interface_config_id,
            window_config_id=window_config_id,
        )
        window_config_layout_config_id = stable_window_config_layout_config_id(
            window_config_id=window_config_id,
            layout_config_id=layout_config_id,
        )
        projection_binding_id = pane_config_id
        interface_config_pane_config_id = stable_interface_config_pane_config_id(
            interface_config_id=interface_config_id,
            pane_config_id=pane_config_id,
        )
        section_mount_id = stable_interface_config_pane_config_section_config_id(
            interface_config_pane_config_id=interface_config_pane_config_id,
            layout_config_section_config_id=layout_config_section_config_id,
        )

        bundle = InterfaceConfigBundle(
            interface_package_id=interface_package_id,
            interface_package_name=interface_package_name,
            interface_config_id=interface_config_id,
            name=interface_config_name,
            description="Aware control plane bundle",
            window_configs=[
                InterfaceWindowConfigBundle(
                    interface_config_window_config_id=interface_config_window_config_id,
                    window_config_id=window_config_id,
                    key=window_key,
                    description="Main operator window",
                    layout_configs=[
                        InterfaceWindowConfigLayoutBundle(
                            window_config_layout_config_id=window_config_layout_config_id,
                            layout_config_id=layout_config_id,
                            key=layout_key,
                            is_default=True,
                            sections=[
                                InterfaceWindowLayoutSectionBundle(
                                    layout_config_section_config_id=layout_config_section_config_id,
                                    key="left_identity",
                                )
                            ],
                        )
                    ],
                )
            ],
            pane_configs=[
                InterfacePaneConfigBundle(
                    pane_config_id=pane_config_id,
                    name=pane_name,
                    pane_kind=pane_kind,
                    narrative_key=pane_narrative_key,
                    description="Identity admission pane",
                    projection_experience_views=[
                        InterfacePaneProjectionExperienceViewBundle(
                            binding_id=projection_binding_id,
                            projection_experience_view_id=projection_experience_view_id,
                            view_ref="identity.default",
                            section_mounts=[
                                InterfacePaneSectionMountBundle(
                                    mount_id=section_mount_id,
                                    layout_config_section_config_id=layout_config_section_config_id,
                                )
                            ],
                        )
                    ],
                )
            ],
        )

        result = await materialize_interface_config_bundle(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            bundle=bundle,
        )

        assert result.branch_id == interface_config_id
        assert result.interface_config.id == interface_config_id
        assert result.interface_config.name == interface_config_name
        assert tuple(window.id for window in result.window_configs) == (window_config_id,)
        assert tuple(binding.id for binding in result.interface_config_window_configs) == (
            interface_config_window_config_id,
        )
        assert tuple(binding.window_config_id for binding in result.interface_config_window_configs) == (
            window_config_id,
        )
        assert tuple(binding.id for binding in result.window_config_layout_configs) == (window_config_layout_config_id,)
        assert tuple(binding.layout_config_id for binding in result.window_config_layout_configs) == (layout_config_id,)
        assert tuple(pane.id for pane in result.pane_configs) == (pane_config_id,)
        assert tuple(binding.id for binding in result.interface_config_pane_configs) == (
            interface_config_pane_config_id,
        )
        assert tuple(binding.pane_config_id for binding in result.interface_config_pane_configs) == (pane_config_id,)
        assert tuple(binding.narrative_key for binding in result.interface_config_pane_configs) == (pane_narrative_key,)
        assert tuple(pane.pane_kind for pane in result.pane_configs) == (pane_kind,)
        assert tuple(binding.id for binding in result.projection_experience_view_bindings) == (projection_binding_id,)
        assert tuple(mount.id for mount in result.section_mounts) == (section_mount_id,)
        assert result.last_commit_id is not None
        assert result.last_head_commit_id is not None

        rerun = await materialize_interface_config_bundle(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=result.branch_id,
            bundle=bundle,
        )

        assert rerun.interface_config.id == interface_config_id
        assert tuple(window.id for window in rerun.window_configs) == (window_config_id,)
        assert tuple(pane.id for pane in rerun.pane_configs) == (pane_config_id,)
        assert tuple(binding.narrative_key for binding in rerun.interface_config_pane_configs) == (pane_narrative_key,)
        assert rerun.last_head_commit_id is not None


@pytest.mark.asyncio
async def test_interface_snapshot_materialization_bridges_removed_attribute_replay(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = REPO_ROOT

    monkeypatch.syspath_prepend(
        str(repo_root / "workspaces" / "aware_network" / "modules" / "interface" / "ontology" / "runtime" / "python")
    )

    import aware_interface_service_dto  # noqa: F401
    import aware_interface_ontology  # noqa: F401

    from aware_attention_ontology.stable_ids import stable_layout_config_id
    from aware_interface.ontology.materialization import materialize_interface_config_bundle
    from aware_interface_service_dto.comms.models.interface_config_bundle import (
        InterfaceConfigBundle,
        InterfacePaneConfigBundle,
        InterfacePaneProjectionExperienceViewBundle,
        InterfacePaneSectionMountBundle,
        InterfaceWindowConfigBundle,
        InterfaceWindowConfigLayoutBundle,
        InterfaceWindowLayoutSectionBundle,
    )
    from aware_interface_ontology.stable_ids import (
        stable_interface_config_id,
        stable_interface_config_pane_config_id,
        stable_interface_config_pane_config_section_config_id,
        stable_interface_config_window_config_id,
        stable_interface_package_id,
        stable_pane_config_id,
        stable_window_config_id,
        stable_window_config_layout_config_id,
    )
    from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
    from aware_meta.graph.instance.commit.materializer import OIGMaterializer
    from aware_meta.runtime import find_meta_graph_projection_hash_by_name

    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        index = context.index
        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()

        namespace = uuid5(
            NAMESPACE_URL,
            "aware://tests/interface/config-materialization/schema-replacement",
        )
        interface_package_name = "aware-control-plane"
        interface_config_name = "aware-control-plane"
        pane_name = "identity"
        pane_kind = "identity"
        pane_narrative_key = "identity.story"
        window_key = "main"
        layout_key = "workspace"
        interface_config_id = stable_interface_config_id(name=interface_config_name)
        interface_package_id = stable_interface_package_id(name=interface_package_name)
        window_config_id = stable_window_config_id(key=window_key)
        layout_config_id = stable_layout_config_id(key=layout_key)
        projection_experience_view_id = uuid5(
            namespace,
            "projection-experience-view:identity.default",
        )
        pane_config_id = stable_pane_config_id(
            projection_experience_view_id=projection_experience_view_id,
            name=pane_name,
        )
        layout_config_section_config_id = uuid5(
            namespace,
            "layout-config-section:left.identity",
        )
        interface_config_window_config_id = stable_interface_config_window_config_id(
            interface_config_id=interface_config_id,
            window_config_id=window_config_id,
        )
        window_config_layout_config_id = stable_window_config_layout_config_id(
            window_config_id=window_config_id,
            layout_config_id=layout_config_id,
        )
        interface_config_pane_config_id = stable_interface_config_pane_config_id(
            interface_config_id=interface_config_id,
            pane_config_id=pane_config_id,
        )
        section_mount_id = stable_interface_config_pane_config_section_config_id(
            interface_config_pane_config_id=interface_config_pane_config_id,
            layout_config_section_config_id=layout_config_section_config_id,
        )

        def bundle(description_suffix: str) -> InterfaceConfigBundle:
            return InterfaceConfigBundle(
                interface_package_id=interface_package_id,
                interface_package_name=interface_package_name,
                interface_config_id=interface_config_id,
                name=interface_config_name,
                description=f"Aware control plane bundle {description_suffix}",
                window_configs=[
                    InterfaceWindowConfigBundle(
                        interface_config_window_config_id=(interface_config_window_config_id),
                        window_config_id=window_config_id,
                        key=window_key,
                        description=f"Main operator window {description_suffix}",
                        layout_configs=[
                            InterfaceWindowConfigLayoutBundle(
                                window_config_layout_config_id=(window_config_layout_config_id),
                                layout_config_id=layout_config_id,
                                key=layout_key,
                                is_default=True,
                                sections=[
                                    InterfaceWindowLayoutSectionBundle(
                                        layout_config_section_config_id=(layout_config_section_config_id),
                                        key="left_identity",
                                    )
                                ],
                            )
                        ],
                    )
                ],
                pane_configs=[
                    InterfacePaneConfigBundle(
                        pane_config_id=pane_config_id,
                        name=pane_name,
                        pane_kind=pane_kind,
                        narrative_key=pane_narrative_key,
                        description=f"Identity admission pane {description_suffix}",
                        projection_experience_views=[
                            InterfacePaneProjectionExperienceViewBundle(
                                binding_id=pane_config_id,
                                projection_experience_view_id=(projection_experience_view_id),
                                view_ref="identity.default",
                                section_mounts=[
                                    InterfacePaneSectionMountBundle(
                                        mount_id=section_mount_id,
                                        layout_config_section_config_id=(layout_config_section_config_id),
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )

        initial = await materialize_interface_config_bundle(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            bundle=bundle("v1"),
            prefer_snapshot_materialization=True,
        )

        original_get = OIGMaterializer.get

        async def stale_schema_get(self, *args, **kwargs):
            raise RuntimeError(
                "Missing AttributeConfig for "
                "attribute_config_id=56dd8b83-fabf-5e83-b12e-5bdb3abdcebe "
                "class_instance_id=fee0807e-7f12-5839-8201-e494c2b02e19 "
                "class_config_id=5dad0929-125d-5238-9906-35ab07a4d110 "
                "attribute_id=de3b1606-1aee-5ca3-a07b-ebd5544d81e0"
            )

        monkeypatch.setattr(OIGMaterializer, "get", stale_schema_get)

        replacement = await materialize_interface_config_bundle(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=initial.branch_id,
            bundle=bundle("v2"),
            prefer_snapshot_materialization=True,
        )

        assert replacement.last_commit_id != initial.last_commit_id
        interface_config_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="InterfaceConfig",
        )
        interface_head = await FSCommitStore(root_dir=aware_root).head(
            branch_id=interface_config_id,
            projection_hash=interface_config_projection_hash,
        )
        assert interface_head is not None
        assert interface_head["commit_id"] == str(replacement.last_commit_id)

        monkeypatch.setattr(OIGMaterializer, "get", original_get)

        rerun = await materialize_interface_config_bundle(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=initial.branch_id,
            bundle=bundle("v2"),
            prefer_snapshot_materialization=True,
        )

        assert rerun.last_commit_id == replacement.last_commit_id
        assert tuple(mount.id for mount in rerun.section_mounts) == (section_mount_id,)
