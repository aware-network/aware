from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_code.types import JsonArray, JsonObject
from aware_history.stable_ids import stable_branch_id
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
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
PROJECTION_EXPERIENCE_GRAPH_IDENTITY_CLASS_FQN = (
    "aware_experience.projection.ProjectionExperienceGraphIdentity"
)
PROJECTION_EXPERIENCE_GRAPH_IDENTITY_PROFILE_CLASS_FQN = (
    "aware_experience.projection.ProjectionExperienceGraphIdentityProfile"
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


def _require_function_id(
    *,
    runtime: MetaGraphRuntime,
    class_fqn: str,
    function_name: str,
) -> UUID:
    assert runtime.context is not None
    matches: list[UUID] = []
    for class_config in runtime.context.index.class_configs_by_id.values():
        if class_config.class_fqn != class_fqn:
            continue
        for edge in class_config.class_config_function_configs:
            function_config = edge.function_config
            if function_config.name == function_name:
                matches.append(function_config.id)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise AssertionError(
            "FunctionConfig not found in Meta graph index: "
            f"class_fqn={class_fqn!r} function_name={function_name!r}"
        )
    raise AssertionError(
        "FunctionConfig is ambiguous in Meta graph index: "
        f"class_fqn={class_fqn!r} function_name={function_name!r} "
        f"matches={matches}"
    )


def _jsonify_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, list):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify_value(item) for key, item in value.items()}
    return value


async def _invoke_meta_function(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    projection_hash: str,
    target: Literal["constructor", "instance"],
    class_fqn: str,
    function_name: str,
    object_id: UUID | None = None,
    kwargs: dict[str, object] | None = None,
) -> MetaGraphCommitReceipt:
    assert runtime.context is not None
    index = runtime.context.index
    call_target = MetaGraphCallTarget.opg_constructor
    target_object_id: UUID | None = None
    object_projection_graph_id: UUID | None = index.opg_by_hash[projection_hash].id
    if target == "instance":
        call_target = MetaGraphCallTarget.instance
        target_object_id = object_id
        object_projection_graph_id = None
    return await runtime.invoke_function(
        MetaGraphInvokeFunctionInput(
            index=index,
            actor_id=lane.actor_id or META_SYSTEM_ACTOR_ID,
            function_id=_require_function_id(
                runtime=runtime,
                class_fqn=class_fqn,
                function_name=function_name,
            ),
            domain_branch_id=lane.branch_id,
            domain_projection_hash=projection_hash,
            call_target=call_target,
            target_object_id=target_object_id,
            object_projection_graph_id=object_projection_graph_id,
            args=JsonArray(),
            kwargs=JsonObject(
                {
                    str(key): _jsonify_value(value)
                    for key, value in (kwargs or {}).items()
                }
            ),
        )
    )


@pytest.mark.asyncio
async def test_projection_experience_graph_profile_rails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_experience_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.stable_ids import (
        stable_projection_experience_graph_id,
        stable_projection_experience_graph_identity_edge_id,
        stable_projection_experience_graph_identity_id,
        stable_projection_experience_graph_identity_profile_exemplar_id,
        stable_projection_experience_graph_identity_profile_id,
        stable_projection_experience_id,
        stable_projection_experience_node_id,
        stable_projection_experience_node_identity_edge_id,
        stable_projection_experience_node_identity_id,
    )

    ns = uuid5(NAMESPACE_URL, "aware://tests/experience/projection-experience-graph/v2")
    environment_id = uuid5(ns, "environment")
    thread_id = uuid5(ns, "thread")
    lane = LaneIds(
        branch_id=stable_branch_id(environment_id=environment_id, thread_id=thread_id),
    )
    opgi_id = uuid5(ns, "opgi")
    projection_node_id = uuid5(ns, "projection_node")
    projection_node_channel_id = uuid5(ns, "projection_node_channel")
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name="workspace",
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
    node_channel_id = stable_projection_experience_node_id(
        projection_experience_id=projection_experience_id,
        object_projection_graph_node_id=projection_node_channel_id,
        key="channel",
    )
    node_channel_identity_id = stable_projection_experience_node_identity_id(
        projection_experience_node_id=node_channel_id,
        key="news_channel",
    )
    graph_id = stable_projection_experience_graph_id(
        projection_experience_id=projection_experience_id,
        name="home_default",
    )
    root_graph_identity_id = stable_projection_experience_graph_identity_id(
        projection_experience_graph_id=graph_id,
        projection_experience_node_identity_id=node_identity_id,
        key="front_door",
    )
    child_graph_identity_id = stable_projection_experience_graph_identity_id(
        projection_experience_graph_id=graph_id,
        projection_experience_node_identity_id=node_channel_identity_id,
        key="front_door.news_channel",
    )
    node_identity_edge_id = stable_projection_experience_node_identity_edge_id(
        projection_experience_graph_id=graph_id,
        parent_projection_experience_node_identity_id=node_identity_id,
        child_projection_experience_node_identity_id=node_channel_identity_id,
    )
    graph_identity_edge_id = stable_projection_experience_graph_identity_edge_id(
        projection_experience_graph_id=graph_id,
        parent_projection_experience_graph_identity_id=root_graph_identity_id,
        child_projection_experience_graph_identity_id=child_graph_identity_id,
        projection_experience_node_identity_edge_id=node_identity_edge_id,
    )
    profile_id = stable_projection_experience_graph_identity_profile_id(
        projection_experience_graph_identity_id=root_graph_identity_id,
    )
    exemplar_id = stable_projection_experience_graph_identity_profile_exemplar_id(
        projection_experience_graph_identity_profile_id=profile_id,
        key="door_primary",
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        assert runtime.context is not None
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
                    kwargs={
                        "key": "front_door",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
                    function_name="create_node",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "object_projection_graph_node_id": projection_node_channel_id,
                        "key": "channel",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_NODE_CLASS_FQN,
                    function_name="create_identity",
                    object_id=node_channel_id,
                    kwargs={
                        "key": "news_channel",
                    },
                ),
            ],
        )
        assert result_projection.root_object_id == projection_experience_id
        assertions_projection.expect_instance(node_identity_id)
        assertions_projection.expect_instance(node_channel_identity_id)

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
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_GRAPH_CLASS_FQN,
                    function_name="create_identity",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "projection_experience_node_identity_id": (
                            node_channel_identity_id
                        ),
                        "key": "front_door.news_channel",
                        "is_root": False,
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_GRAPH_CLASS_FQN,
                    function_name="create_node_identity_edge",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "parent_projection_experience_node_identity_id": (
                            node_identity_id
                        ),
                        "child_projection_experience_node_identity_id": (
                            node_channel_identity_id
                        ),
                        "key": "door->channel",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_GRAPH_CLASS_FQN,
                    function_name="create_graph_identity_edge",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "parent_projection_experience_graph_identity_id": (
                            root_graph_identity_id
                        ),
                        "child_projection_experience_graph_identity_id": (
                            child_graph_identity_id
                        ),
                        "projection_experience_node_identity_edge_id": (
                            node_identity_edge_id
                        ),
                        "key": "front_door->news_channel",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_GRAPH_IDENTITY_CLASS_FQN,
                    function_name="create_profile",
                    object_id=root_graph_identity_id,
                    kwargs={
                        "review_label": "Front Door",
                        "resolution_prompts": ["door", "front door"],
                        "aliases": ["entry door"],
                        "summary": "Primary entrance object",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_GRAPH_IDENTITY_PROFILE_CLASS_FQN,
                    function_name="create_exemplar",
                    object_id=profile_id,
                    kwargs={
                        "key": "door_primary",
                        "label": "Front Door Daylight",
                        "prompt_hint": "door",
                        "note": "Primary home-story exemplar",
                        "is_primary": True,
                    },
                ),
            ],
        )
        assert result_graph.root_object_id == graph_id
        assertions_graph.expect_instance(graph_id)
        assertions_graph.expect_instance(root_graph_identity_id)
        assertions_graph.expect_instance(child_graph_identity_id)
        assertions_graph.expect_instance(node_identity_edge_id)
        assertions_graph.expect_instance(graph_identity_edge_id)
        assertions_graph.expect_instance(profile_id)
        assertions_graph.expect_instance(exemplar_id)
        assertions_graph.expect_edge(
            source_id=graph_id,
            target_id=root_graph_identity_id,
            relationship_name="projection_experience_graph_identities",
        )
        assertions_graph.expect_edge(
            source_id=graph_id,
            target_id=child_graph_identity_id,
            relationship_name="projection_experience_graph_identities",
        )
        assertions_graph.expect_edge(
            source_id=graph_id,
            target_id=node_identity_edge_id,
            relationship_name="projection_experience_node_identity_edges",
        )
        assertions_graph.expect_edge(
            source_id=graph_id,
            target_id=graph_identity_edge_id,
            relationship_name="projection_experience_graph_identity_edges",
        )
        assertions_graph.expect_edge(
            source_id=root_graph_identity_id,
            target_id=profile_id,
            relationship_name="projection_experience_graph_identity_profile",
        )
        assertions_graph.expect_edge(
            source_id=profile_id,
            target_id=exemplar_id,
            relationship_name="exemplars",
        )
        assertions_graph.expect_primitive(
            instance_id=graph_id,
            field_name="name",
            expected="home_default",
        )
        assertions_graph.expect_primitive(
            instance_id=root_graph_identity_id,
            field_name="is_root",
            expected=True,
        )
        assertions_graph.expect_primitive(
            instance_id=profile_id,
            field_name="review_label",
            expected="Front Door",
        )
        assertions_graph.expect_primitive(
            instance_id=profile_id,
            field_name="resolution_prompts",
            expected=["door", "front door"],
        )
        assertions_graph.expect_primitive(
            instance_id=exemplar_id,
            field_name="is_primary",
            expected=True,
        )

        profile_repeat = await _invoke_meta_function(
            runtime=runtime,
            lane=lane,
            projection_hash=result_graph.projection_hash,
            target="instance",
            class_fqn=PROJECTION_EXPERIENCE_GRAPH_IDENTITY_CLASS_FQN,
            function_name="create_profile",
            object_id=root_graph_identity_id,
            kwargs={
                "review_label": "Front Door",
                "resolution_prompts": ["door", "front door"],
                "aliases": ["entry door"],
                "summary": "Primary entrance object",
            },
        )
        assert profile_repeat.status == "succeeded", profile_repeat.error
        assert profile_repeat.commit_id is None

        exemplar_repeat = await _invoke_meta_function(
            runtime=runtime,
            lane=lane,
            projection_hash=result_graph.projection_hash,
            target="instance",
            class_fqn=PROJECTION_EXPERIENCE_GRAPH_IDENTITY_PROFILE_CLASS_FQN,
            function_name="create_exemplar",
            object_id=profile_id,
            kwargs={
                "key": "door_primary",
                "label": "Front Door Daylight",
                "prompt_hint": "door",
                "note": "Primary home-story exemplar",
                "is_primary": True,
            },
        )
        assert exemplar_repeat.status == "succeeded", exemplar_repeat.error
        assert exemplar_repeat.commit_id is None


@pytest.mark.asyncio
async def test_projection_experience_graph_fail_closed_profile_payloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_experience_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.stable_ids import (
        stable_projection_experience_graph_id,
        stable_projection_experience_graph_identity_id,
        stable_projection_experience_id,
        stable_projection_experience_node_id,
        stable_projection_experience_node_identity_id,
    )

    ns = uuid5(
        NAMESPACE_URL,
        "aware://tests/experience/projection-experience-graph/fail-closed/v2",
    )
    environment_id = uuid5(ns, "environment")
    thread_id = uuid5(ns, "thread")
    lane = LaneIds(
        branch_id=stable_branch_id(environment_id=environment_id, thread_id=thread_id),
    )
    opgi_id = uuid5(ns, "opgi")
    projection_node_id = uuid5(ns, "projection_node")
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name="workspace",
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

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        assert runtime.context is not None
        graph_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime.context.index,
            projection_name="ProjectionExperienceGraph",
        )
        await run_meta_runtime_proof(
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
        await run_meta_runtime_proof(
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

        with pytest.raises(RuntimeError, match="non-empty review_label"):
            await _invoke_meta_function(
                runtime=runtime,
                lane=lane,
                projection_hash=graph_projection_hash,
                target="instance",
                class_fqn=PROJECTION_EXPERIENCE_GRAPH_IDENTITY_CLASS_FQN,
                function_name="create_profile",
                object_id=graph_identity_id,
                kwargs={
                    "review_label": "  ",
                    "resolution_prompts": ["door"],
                },
            )

        with pytest.raises(RuntimeError, match="non-empty resolution_prompts"):
            await _invoke_meta_function(
                runtime=runtime,
                lane=lane,
                projection_hash=graph_projection_hash,
                target="instance",
                class_fqn=PROJECTION_EXPERIENCE_GRAPH_IDENTITY_CLASS_FQN,
                function_name="create_profile",
                object_id=graph_identity_id,
                kwargs={
                    "review_label": "Front Door",
                    "resolution_prompts": [],
                },
            )
