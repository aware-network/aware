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
async def test_projection_experience_constructor_rails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_experience_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.stable_ids import (
        stable_projection_experience_branch_id,
        stable_projection_experience_id,
        stable_projection_experience_node_id,
        stable_projection_experience_node_identity_id,
        stable_projection_experience_view_id,
    )

    ns = uuid5(NAMESPACE_URL, "aware://tests/experience/projection-experience/v2")
    environment_id = uuid5(ns, "environment")
    thread_id = uuid5(ns, "thread")
    lane = LaneIds(
        branch_id=stable_branch_id(environment_id=environment_id, thread_id=thread_id),
    )
    opgi_id = uuid5(ns, "opgi")
    api_view_id = uuid5(ns, "api-view")
    projection_node_id = uuid5(ns, "projection_node")
    projection_node_channel_id = uuid5(ns, "projection_node_channel")
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name="workspace",
    )
    branch_id = stable_projection_experience_branch_id(
        projection_experience_id=projection_experience_id,
        name="assistance",
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
    node_channel_id = stable_projection_experience_node_id(
        projection_experience_id=projection_experience_id,
        object_projection_graph_node_id=projection_node_channel_id,
        key="channel",
    )
    node_channel_identity_id = stable_projection_experience_node_identity_id(
        projection_experience_node_id=node_channel_id,
        key="news_channel",
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
                    function_name="create_branch",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "name": "assistance",
                    },
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
        assertions_projection.expect_instance(projection_experience_id)
        assertions_projection.expect_instance(branch_id)
        assertions_projection.expect_instance(node_id)
        assertions_projection.expect_instance(node_identity_id)
        assertions_projection.expect_instance(node_channel_id)
        assertions_projection.expect_instance(node_channel_identity_id)
        assertions_projection.expect_instance(view_id)
        assertions_projection.expect_edge(
            source_id=projection_experience_id,
            target_id=branch_id,
            relationship_name="projection_experience_branches",
        )
        assertions_projection.expect_edge(
            source_id=projection_experience_id,
            target_id=view_id,
            relationship_name="projection_experience_views",
        )
        assertions_projection.expect_edge(
            source_id=projection_experience_id,
            target_id=node_id,
            relationship_name="projection_experience_nodes",
        )
        assertions_projection.expect_edge(
            source_id=node_id,
            target_id=node_identity_id,
            relationship_name="projection_experience_node_identities",
        )
        assertions_projection.expect_edge(
            source_id=node_channel_id,
            target_id=node_channel_identity_id,
            relationship_name="projection_experience_node_identities",
        )
        assertions_projection.expect_primitive(
            instance_id=projection_experience_id,
            field_name="name",
            expected="workspace",
        )
        assertions_projection.expect_primitive(
            instance_id=branch_id,
            field_name="name",
            expected="assistance",
        )
        assertions_projection.expect_primitive(
            instance_id=view_id,
            field_name="name",
            expected="home",
        )
        assertions_projection.expect_primitive(
            instance_id=view_id,
            field_name="api_view_id",
            expected=api_view_id,
        )
        assertions_projection.expect_primitive(
            instance_id=node_id,
            field_name="key",
            expected="door",
        )
        assertions_projection.expect_primitive(
            instance_id=node_identity_id,
            field_name="key",
            expected="front_door",
        )

        branch_repeat = await _invoke_meta_function(
            runtime=runtime,
            lane=lane,
            projection_hash=result_projection.projection_hash,
            target="instance",
            class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
            function_name="create_branch",
            object_id=projection_experience_id,
            kwargs={"name": "assistance"},
        )
        assert branch_repeat.status == "succeeded", branch_repeat.error
        assert branch_repeat.commit_id is None

        view_repeat = await _invoke_meta_function(
            runtime=runtime,
            lane=lane,
            projection_hash=result_projection.projection_hash,
            target="instance",
            class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
            function_name="create_view",
            object_id=projection_experience_id,
            kwargs={
                "api_view_id": api_view_id,
                "name": "home",
            },
        )
        assert view_repeat.status == "succeeded", view_repeat.error
        assert view_repeat.commit_id is None


@pytest.mark.asyncio
async def test_projection_experience_fail_closed_blank_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_experience_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.stable_ids import stable_projection_experience_id

    ns = uuid5(
        NAMESPACE_URL,
        "aware://tests/experience/projection-experience/fail-closed/v1",
    )
    environment_id = uuid5(ns, "environment")
    thread_id = uuid5(ns, "thread")
    lane = LaneIds(
        branch_id=stable_branch_id(environment_id=environment_id, thread_id=thread_id),
    )
    opgi_id = uuid5(ns, "opgi")
    api_view_id = uuid5(ns, "api-view")
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name="workspace",
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        assert runtime.context is not None
        projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime.context.index,
            projection_name="ProjectionExperience",
        )

        with pytest.raises(RuntimeError, match="non-empty name"):
            await _invoke_meta_function(
                runtime=runtime,
                lane=lane,
                projection_hash=projection_hash,
                target="constructor",
                class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
                function_name="create",
                kwargs={
                    "object_projection_graph_identity_id": opgi_id,
                    "name": "   ",
                },
            )

        projection_ok = await _invoke_meta_function(
            runtime=runtime,
            lane=lane,
            projection_hash=projection_hash,
            target="constructor",
            class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
            function_name="create",
            kwargs={
                "object_projection_graph_identity_id": opgi_id,
                "name": "workspace",
            },
        )
        assert projection_ok.status == "succeeded", projection_ok.error
        assert projection_ok.root_object_id == projection_experience_id

        with pytest.raises(RuntimeError, match="non-empty name"):
            await _invoke_meta_function(
                runtime=runtime,
                lane=lane,
                projection_hash=projection_hash,
                target="instance",
                class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
                function_name="create_branch",
                object_id=projection_experience_id,
                kwargs={
                    "name": "",
                },
            )

        with pytest.raises(RuntimeError, match="non-empty name"):
            await _invoke_meta_function(
                runtime=runtime,
                lane=lane,
                projection_hash=projection_hash,
                target="instance",
                class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
                function_name="create_view",
                object_id=projection_experience_id,
                kwargs={
                    "api_view_id": api_view_id,
                    "name": " ",
                },
            )

        with pytest.raises(RuntimeError, match="non-empty name"):
            await _invoke_meta_function(
                runtime=runtime,
                lane=lane,
                projection_hash=projection_hash,
                target="instance",
                class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
                function_name="create_graph",
                object_id=projection_experience_id,
                kwargs={
                    "name": " ",
                },
            )

        with pytest.raises(
            RuntimeError,
            match="requires existing ObjectInstanceGraphIdentity",
        ):
            await _invoke_meta_function(
                runtime=runtime,
                lane=lane,
                projection_hash=projection_hash,
                target="instance",
                class_fqn=PROJECTION_EXPERIENCE_CLASS_FQN,
                function_name="create_oigi",
                object_id=projection_experience_id,
                kwargs={
                    "object_instance_graph_identity_id": uuid5(ns, "missing-oigi"),
                    "key": "runtime.main",
                },
            )
