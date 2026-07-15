from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import pytest

from aware_history.stable_ids import stable_branch_id
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    LaneIds,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from ._experience_runtime_test_paths import REPO_ROOT


PROJECTION_EXPERIENCE_CLASS_FQN = "aware_experience.projection.ProjectionExperience"
PROJECTION_EXPERIENCE_NODE_CLASS_FQN = (
    "aware_experience.projection.ProjectionExperienceNode"
)
PROJECTION_EXPERIENCE_GRAPH_CLASS_FQN = (
    "aware_experience.projection.ProjectionExperienceGraph"
)
PROJECTION_EXPERIENCE_SECTION_GRAPH_BINDING_CLASS_FQN = (
    "aware_experience.projection.ProjectionExperienceSectionGraphBinding"
)


def _experience_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
    )


def _experience_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/sdk/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/sdk/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/python",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_models",
        repo_root / "workspaces/aware_kernel/modules/meta/ontology/runtime/python",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/runtime/python",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/runtime/python",
    )


def _prepend_experience_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for python_root in _experience_meta_python_roots(repo_root):
        if python_root.exists():
            monkeypatch.syspath_prepend(str(python_root))


def _build_experience_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    from aware_experience.handlers._generated import (  # noqa: WPS433
        meta_handlers as experience_meta_handlers,
    )
    from aware_meta.handlers._generated import (  # noqa: WPS433
        meta_handlers as meta_meta_handlers,
    )
    from aware_reactivity.handlers._generated import (  # noqa: WPS433
        meta_handlers as reactivity_meta_handlers,
    )

    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_experience_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, meta_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
        bootstrap_modules=(
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, meta_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
    )
    assert runtime.context is not None
    return runtime


@pytest.mark.asyncio
async def test_projection_experience_section_graph_binding_graph_anchor_rails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_attention_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_attention_ontology.stable_ids import (
        stable_layout_config_id,
        stable_layout_config_section_config_id,
    )
    from aware_experience_ontology.stable_ids import (
        stable_projection_experience_graph_id,
        stable_projection_experience_graph_identity_id,
        stable_projection_experience_id,
        stable_projection_experience_node_id,
        stable_projection_experience_node_identity_id,
        stable_projection_experience_section_graph_binding_id,
        stable_projection_experience_view_id,
    )

    ns = uuid5(
        NAMESPACE_URL,
        "aware://tests/experience/projection-experience-section-graph-binding/v2",
    )
    environment_id = uuid5(ns, "environment")
    thread_id = uuid5(ns, "thread")
    lane = LaneIds(
        branch_id=stable_branch_id(environment_id=environment_id, thread_id=thread_id),
    )
    opgi_id = uuid5(ns, "opgi")
    api_view_id = uuid5(ns, "api-view")
    projection_node_id = uuid5(ns, "projection_node")
    layout_config_id = stable_layout_config_id(key="home-layout")
    layout_config_section_config_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config_id,
        section_key="coordination.primary",
    )

    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name="workspace",
    )
    view_id = stable_projection_experience_view_id(
        projection_experience_id=projection_experience_id,
        name="home",
    )
    node_id = stable_projection_experience_node_id(
        projection_experience_id=projection_experience_id,
        object_projection_graph_node_id=projection_node_id,
        key="door",
    )
    node_identity_id = stable_projection_experience_node_identity_id(
        projection_experience_node_id=node_id,
        key="front_door",
    )
    graph_id = stable_projection_experience_graph_id(
        projection_experience_id=projection_experience_id,
        name="home_default",
    )
    graph_identity_id = stable_projection_experience_graph_identity_id(
        projection_experience_graph_id=graph_id,
        projection_experience_node_identity_id=node_identity_id,
        key="front_door",
    )
    binding_id = stable_projection_experience_section_graph_binding_id(
        projection_experience_id=projection_experience_id,
        layout_config_section_config_id=layout_config_section_config_id,
        projection_experience_view_id=view_id,
        projection_experience_graph_identity_id=graph_identity_id,
        binding_key="issue.primary",
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        result_projection, assertions_projection = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ProjectionExperience",
            root_class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
                    function_name="create",
                    kwargs={
                        "object_projection_graph_identity_id": opgi_id,
                        "name": "workspace",
                    },
                    expected_root_object_id=projection_experience_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
                    function_name="create_view",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "api_view_id": api_view_id,
                        "name": "home",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
                    function_name="create_node",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "object_projection_graph_node_id": projection_node_id,
                        "key": "door",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_NODE_CLASS_FQN,
                    function_name="create_identity",
                    object_id=node_id,
                    kwargs={"key": "front_door"},
                ),
            ],
        )

        assert result_projection.root_object_id == projection_experience_id
        assertions_projection.expect_instance(view_id)
        assertions_projection.expect_instance(node_id)
        assertions_projection.expect_instance(node_identity_id)

        result_graph, assertions_graph = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ProjectionExperienceGraph",
            root_class_fqn=PROJECTION_EXPERIENCE_GRAPH_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=PROJECTION_EXPERIENCE_GRAPH_CLASS_FQN,
                    function_name="create_via_projection_experience",
                    kwargs={
                        "projection_experience_id": projection_experience_id,
                        "name": "home_default",
                    },
                    expected_root_object_id=graph_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_GRAPH_CLASS_FQN,
                    function_name="create_identity",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "projection_experience_node_identity_id": node_identity_id,
                        "key": "front_door",
                        "is_root": True,
                    },
                ),
            ],
        )

        assert result_graph.root_object_id == graph_id
        assertions_graph.expect_instance(graph_identity_id)
        assertions_graph.expect_edge(
            source_id=graph_id,
            target_id=graph_identity_id,
            relationship_name="projection_experience_graph_identities",
        )

        result_binding, assertions_binding = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ProjectionExperienceSectionGraphBinding",
            root_class_fqn=PROJECTION_EXPERIENCE_SECTION_GRAPH_BINDING_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=PROJECTION_EXPERIENCE_SECTION_GRAPH_BINDING_CLASS_FQN,
                    function_name="build_via_projection_experience",
                    kwargs={
                        "projection_experience_id": projection_experience_id,
                        "layout_config_section_config_id": (
                            layout_config_section_config_id
                        ),
                        "projection_experience_view_id": view_id,
                        "projection_experience_graph_identity_id": graph_identity_id,
                        "binding_key": "issue.primary",
                        "section_key": "coordination.primary",
                    },
                    expected_root_object_id=binding_id,
                ),
            ],
        )

        assert result_binding.root_object_id == binding_id
        assertions_binding.expect_instance(binding_id)
        assertions_binding.expect_primitive(
            instance_id=binding_id,
            field_name="projection_experience_id",
            expected=projection_experience_id,
        )
        assertions_binding.expect_primitive(
            instance_id=binding_id,
            field_name="layout_config_section_config_id",
            expected=layout_config_section_config_id,
        )
        assertions_binding.expect_primitive(
            instance_id=binding_id,
            field_name="projection_experience_view_id",
            expected=view_id,
        )
        assertions_binding.expect_primitive(
            instance_id=binding_id,
            field_name="projection_experience_graph_identity_id",
            expected=graph_identity_id,
        )
        assertions_binding.expect_primitive(
            instance_id=binding_id,
            field_name="binding_key",
            expected="issue.primary",
        )
        assertions_binding.expect_primitive(
            instance_id=binding_id,
            field_name="section_key",
            expected="coordination.primary",
        )
