from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest

from aware_attention.handlers._generated import meta_handlers as attention_meta_handlers
from aware_attention.materialization import service as attention_materialization_service
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from ._attention_module_proof_paths import REPO_ROOT


ATTENTION_LAYOUT_CONFIG_CLASS_FQN = "aware_attention.layout.LayoutConfig"
ATTENTION_PACKAGE_CLASS_FQN = "aware_attention.attention.AttentionPackage"

_ATTENTION_META_HANDLERS_ANY: Any = attention_meta_handlers
_ATTENTION_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ATTENTION_META_HANDLERS_ANY,
)
_ATTENTION_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ATTENTION_META_HANDLERS_ANY,
)


def _attention_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
    )


def _build_attention_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_attention_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_ATTENTION_META_HANDLER_MODULE,),
        bootstrap_modules=(_ATTENTION_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


@pytest.mark.asyncio
async def test_attention_package_build_constructor_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    from aware_attention_ontology.stable_ids import stable_attention_package_id

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_attention_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        package_name = "aware-control-shell-attention"
        package_id = stable_attention_package_id(name=package_name)

        lane = LaneIds(
            branch_id=package_id,
            actor_id=uuid4(),
        )

        _result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="AttentionPackage",
            root_class_fqn=ATTENTION_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ATTENTION_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": package_name,
                        "source_code_package_id": None,
                    },
                    expected_root_object_id=package_id,
                ),
            ],
        )

        assertions.expect_instance(package_id)
        assertions.expect_primitive(
            instance_id=package_id,
            field_name="name",
            expected=package_name,
        )


@pytest.mark.asyncio
async def test_attention_package_duplicate_layout_attachment_is_noop(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    from aware_attention_ontology.stable_ids import (
        stable_attention_package_id,
        stable_attention_package_layout_config_id,
        stable_layout_config_id,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_attention_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        package_name = "aware-control-shell-attention"
        package_id = stable_attention_package_id(name=package_name)
        layout_config_id = stable_layout_config_id(key="coordination_center")
        membership_id = stable_attention_package_layout_config_id(
            attention_package_id=package_id,
            layout_config_id=layout_config_id,
        )

        result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(branch_id=package_id, actor_id=uuid4()),
            opg_name="AttentionPackage",
            root_class_fqn=ATTENTION_PACKAGE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ATTENTION_PACKAGE_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "name": package_name,
                        "source_code_package_id": None,
                    },
                    expected_root_object_id=package_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_PACKAGE_CLASS_FQN,
                    function_name="attach_layout_config",
                    object_id=package_id,
                    kwargs={"layout_config_id": layout_config_id},
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_PACKAGE_CLASS_FQN,
                    function_name="attach_layout_config",
                    object_id=package_id,
                    kwargs={"layout_config_id": layout_config_id},
                    allow_noop_commit=True,
                ),
            ],
        )

        assert len(result.responses) == 3
        assert result.responses[2].commit_id is None
        assert len(result.commits) == 2
        assert result.head["commit_id"] == str(result.responses[1].commit_id)
        assertions.expect_instance(membership_id)
        assertions.expect_edge(
            source_id=package_id,
            target_id=membership_id,
            relationship_name="layout_configs",
        )
        assert runtime.context is not None
        package_target = (
            attention_materialization_service._resolve_projection_invoke_target(
                index=runtime.context.index,
                projection_name="AttentionPackage",
            )
        )
        package_head = (
            await attention_materialization_service._load_attention_package_lane_head(
                index=runtime.context.index,
                target=package_target,
                attention_package_id=package_id,
            )
        )
        assert package_head is not None
        assert package_head.commit_id == result.responses[1].commit_id
        assert package_head.graph_hash_post == result.responses[1].graph_hash_post
        assert [item.id for item in package_head.root.layout_configs] == [membership_id]


@pytest.mark.asyncio
async def test_layout_config_build_add_section_config_chain(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_attention_ontology  # noqa: F401
    from aware_attention_ontology.stable_ids import (
        stable_layout_config_id,
        stable_layout_config_section_config_id,
        stable_section_config_id,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_attention_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        layout_config_key = "workspace-default"
        section_config_key = "workspace"
        layout_config_id = stable_layout_config_id(key=layout_config_key)
        layout_config_section_config_id = stable_layout_config_section_config_id(
            layout_config_id=layout_config_id,
            section_key=section_config_key,
        )
        section_config_id = stable_section_config_id(
            layout_config_section_config_id=layout_config_section_config_id,
            key=section_config_key,
        )

        lane = LaneIds(
            branch_id=layout_config_id,
            actor_id=uuid4(),
        )

        _result, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="LayoutConfig",
            root_class_fqn=ATTENTION_LAYOUT_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ATTENTION_LAYOUT_CONFIG_CLASS_FQN,
                    function_name="build",
                    kwargs={
                        "key": layout_config_key,
                        "title": "Workspace Default",
                        "description": None,
                    },
                    expected_root_object_id=layout_config_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ATTENTION_LAYOUT_CONFIG_CLASS_FQN,
                    function_name="add_section_config",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "section_key": section_config_key,
                        "title": "Workspace",
                        "description": None,
                        "order": 0,
                        "flex": 1.0,
                        "is_visible": True,
                    },
                ),
            ],
        )

        assertions.expect_instance(layout_config_id)
        assertions.expect_instance(layout_config_section_config_id)
        assertions.expect_instance(section_config_id)
        assertions.expect_edge(
            source_id=layout_config_id,
            target_id=layout_config_section_config_id,
            relationship_name="section_configs",
        )
        assertions.expect_edge(
            source_id=layout_config_section_config_id,
            target_id=section_config_id,
            relationship_name="section_config",
        )
        assertions.expect_primitive(
            instance_id=layout_config_section_config_id,
            field_name="section_key",
            expected=section_config_key,
        )
        assertions.expect_primitive(
            instance_id=section_config_id,
            field_name="key",
            expected=section_config_key,
        )
