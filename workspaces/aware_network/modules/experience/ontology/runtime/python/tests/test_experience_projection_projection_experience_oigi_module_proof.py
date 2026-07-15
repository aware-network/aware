from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_code.types import JsonArray, JsonObject
from aware_history.stable_ids import stable_branch_id
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID, resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    LaneIds,
    MetaOIGAssertions,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
from aware_meta_ontology.class_.class_instance_relationship_identity import (
    ClassInstanceRelationshipIdentity,
)
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_orm.session.change_collector import ORMChangeSet
from ._experience_runtime_test_paths import REPO_ROOT


OBJECT_INSTANCE_GRAPH_IDENTITY_CLASS_FQN = (
    "aware_meta.graph.instance.ObjectInstanceGraphIdentity"
)
PROJECTION_EXPERIENCE_CLASS_FQN = "aware_experience.projection.ProjectionExperience"
PROJECTION_EXPERIENCE_NODE_CLASS_FQN = (
    "aware_experience.projection.ProjectionExperienceNode"
)
PROJECTION_EXPERIENCE_OIGI_CLASS_FQN = (
    "aware_experience.projection.ProjectionExperienceOIGI"
)
_OIGI_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://tests/experience/projection-experience-oigi/oigi-snapshot/v1",
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


async def _assertions_for_committed_head(
    *,
    runtime_index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> MetaOIGAssertions:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id")
    assert head.get("object_instance_graph_id")
    opg = runtime_index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=runtime_index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=runtime_index.attribute_configs_by_id,
        class_configs_by_id=runtime_index.class_configs_by_id,
    )
    return MetaOIGAssertions(oig=oig, index=runtime_index)


async def _load_before_oig(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    domain_oig_id: UUID,
    root_object_id: UUID,
):
    opg = index.opg_by_hash[projection_hash]
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is not None and head.get("commit_id") is not None:
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        return oig
    return build_rooted_object_instance_graph_base(
        key=str(branch_id),
        name=f"OIG_{branch_id.hex[:8]}",
        description="ROOTED_BASE",
        object_config_graph=index.ocg,
        object_projection_graph=opg,
        root_source_object_id=root_object_id,
        oig_id=domain_oig_id,
    )


async def _commit_object_instance_graph_identity_snapshot(
    *,
    runtime: MetaGraphRuntime,
    branch_id: UUID,
    object_projection_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    object_instance_graph_identity_id: UUID,
    class_instance_rows: tuple[tuple[UUID, UUID, str], ...],
    relationship_rows: tuple[tuple[UUID, UUID, str], ...],
) -> MetaOIGAssertions:
    assert runtime.context is not None
    index = runtime.context.index
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ObjectInstanceGraphIdentity",
    )
    opg = index.opg_by_hash[projection_hash]
    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=projection_hash,
    )
    if opgi is None:
        raise AssertionError(
            "ObjectInstanceGraphIdentity snapshot missing projection identity"
        )
    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    domain_oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )

    class_identities = [
        ClassInstanceIdentity(
            id=class_instance_identity_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            class_instance_id=class_instance_id,
            label=label,
        )
        for class_instance_identity_id, class_instance_id, label in class_instance_rows
    ]
    relationship_identities = [
        ClassInstanceRelationshipIdentity(
            id=relationship_identity_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            class_instance_relationship_id=relationship_id,
            label=label,
        )
        for relationship_identity_id, relationship_id, label in relationship_rows
    ]
    root = ObjectInstanceGraphIdentity(
        id=object_instance_graph_identity_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        label="runtime.main",
        class_instance_identities=class_identities,
        class_instance_relationship_identities=relationship_identities,
    )
    objects_by_id = {
        root.id: root,
        **{item.id: item for item in class_identities},
        **{item.id: item for item in relationship_identities},
    }
    before_oig = await _load_before_oig(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_oig_id=domain_oig_id,
        root_object_id=object_instance_graph_identity_id,
    )
    object_ids = frozenset(objects_by_id)
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=object_ids,
        touched_ids=object_ids,
        deleted_ids=frozenset(),
        objects_by_id=dict(objects_by_id),
        scalar_fields_by_id={},
        list_fields_by_id={},
        scalar_baseline={},
        list_baseline={},
        list_added={},
        list_removed={},
    )
    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=domain_oigi_id,
        ocg=index.ocg,
        opg=opg,
        change_set=change_set,
        class_configs_by_id=index.class_configs_by_id,
        relationships_by_id=index.relationships_by_id,
        enum_option_resolver=default_meta_enum_option_resolver,
        class_instance_resolver=None,
        union_selections=None,
    )
    if not changes:
        raise AssertionError("ObjectInstanceGraphIdentity snapshot produced no changes")
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    commit_id = uuid5(
        _OIGI_SNAPSHOT_COMMIT_NAMESPACE,
        (
            f"{branch_id}:{projection_hash}:{object_instance_graph_identity_id}:"
            f"{after_oig.hash}"
        ),
    )
    commit = await FSLaneCommitter().commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_identity_id=domain_oigi_id,
        object_instance_graph_id=domain_oig_id,
        before_oig=before_oig,
        root_object_id=object_instance_graph_identity_id,
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=resolve_meta_author_id(None),
        commit_id=commit_id,
        commit_action=CommitActionDescriptor(
            operation_label="ObjectInstanceGraphIdentity.test_snapshot",
            call_target="test_materialization",
            object_id=object_instance_graph_identity_id,
        ),
    )
    if commit is None or commit.commit is None:
        raise AssertionError("ObjectInstanceGraphIdentity snapshot did not commit")
    return await _assertions_for_committed_head(
        runtime_index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )


@pytest.mark.asyncio
async def test_projection_experience_oigi_bridge_rails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_experience_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.stable_ids import (
        stable_projection_experience_id,
        stable_projection_experience_node_class_identity_edge_id,
        stable_projection_experience_node_class_identity_id,
        stable_projection_experience_node_id,
        stable_projection_experience_node_identity_id,
        stable_projection_experience_oigi_id,
    )
    from aware_meta_ontology.stable_ids import (
        stable_class_instance_identity_id,
        stable_class_instance_relationship_identity_id,
    )

    ns = uuid5(NAMESPACE_URL, "aware://tests/experience/projection-experience-oigi/v1")
    environment_id = uuid5(ns, "environment")
    thread_id = uuid5(ns, "thread")
    lane = LaneIds(
        branch_id=stable_branch_id(environment_id=environment_id, thread_id=thread_id),
    )
    opgi_id = uuid5(ns, "opgi")
    object_instance_graph_id = uuid5(ns, "object-instance-graph")
    object_instance_graph_identity_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi_id,
        object_instance_graph_id=object_instance_graph_id,
    )
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
    projection_experience_oigi_id = stable_projection_experience_oigi_id(
        projection_experience_id=projection_experience_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
    )
    class_instance_id = uuid5(ns, "class-instance-door")
    class_instance_channel_id = uuid5(ns, "class-instance-channel")
    class_instance_relationship_id = uuid5(ns, "class-instance-relationship")
    class_instance_identity_id = stable_class_instance_identity_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        class_instance_id=class_instance_id,
    )
    class_instance_channel_identity_id = stable_class_instance_identity_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        class_instance_id=class_instance_channel_id,
    )
    class_instance_relationship_identity_id = (
        stable_class_instance_relationship_identity_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            class_instance_relationship_id=class_instance_relationship_id,
        )
    )
    node_class_identity_id = stable_projection_experience_node_class_identity_id(
        projection_experience_oigi_id=projection_experience_oigi_id,
        projection_experience_node_identity_id=node_identity_id,
        class_instance_identity_id=class_instance_identity_id,
        key="front_door",
    )
    node_class_identity_channel_id = (
        stable_projection_experience_node_class_identity_id(
            projection_experience_oigi_id=projection_experience_oigi_id,
            projection_experience_node_identity_id=node_channel_identity_id,
            class_instance_identity_id=class_instance_channel_identity_id,
            key="front_door.news_channel",
        )
    )
    node_class_identity_edge_id = (
        stable_projection_experience_node_class_identity_edge_id(
            projection_experience_oigi_id=projection_experience_oigi_id,
            parent_node_class_identity_id=node_class_identity_id,
            child_node_class_identity_id=node_class_identity_channel_id,
            class_instance_relationship_identity_id=(
                class_instance_relationship_identity_id
            ),
        )
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        _result_projection, assertions_projection = await run_meta_runtime_proof(
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
                    kwargs={"key": "news_channel"},
                ),
            ],
        )
        assertions_projection.expect_instance(node_identity_id)
        assertions_projection.expect_instance(node_channel_identity_id)

        assertions_oigi_root = await _commit_object_instance_graph_identity_snapshot(
            runtime=runtime,
            branch_id=lane.branch_id,
            object_projection_graph_identity_id=opgi_id,
            object_instance_graph_id=object_instance_graph_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            class_instance_rows=(
                (class_instance_identity_id, class_instance_id, "front_door"),
                (
                    class_instance_channel_identity_id,
                    class_instance_channel_id,
                    "front_door.news_channel",
                ),
            ),
            relationship_rows=(
                (
                    class_instance_relationship_identity_id,
                    class_instance_relationship_id,
                    "front_door->news_channel",
                ),
            ),
        )
        assertions_oigi_root.expect_instance(class_instance_identity_id)
        assertions_oigi_root.expect_instance(class_instance_channel_identity_id)
        assertions_oigi_root.expect_instance(class_instance_relationship_identity_id)

        result_oigi, assertions_oigi = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ProjectionExperienceOIGI",
            root_class_fqn=PROJECTION_EXPERIENCE_OIGI_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=PROJECTION_EXPERIENCE_OIGI_CLASS_FQN,
                    function_name="build_via_projection_experience",
                    kwargs={
                        "projection_experience_id": projection_experience_id,
                        "object_instance_graph_identity_id": (
                            object_instance_graph_identity_id
                        ),
                        "key": "runtime.main",
                    },
                    expected_root_object_id=projection_experience_oigi_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_OIGI_CLASS_FQN,
                    function_name="create_node_class_identity",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "projection_experience_node_identity_id": node_identity_id,
                        "class_instance_identity_id": class_instance_identity_id,
                        "key": "front_door",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_OIGI_CLASS_FQN,
                    function_name="create_node_class_identity",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "projection_experience_node_identity_id": (
                            node_channel_identity_id
                        ),
                        "class_instance_identity_id": (
                            class_instance_channel_identity_id
                        ),
                        "key": "front_door.news_channel",
                    },
                ),
                ProofCall(
                    target="instance",
                    class_fqn=PROJECTION_EXPERIENCE_OIGI_CLASS_FQN,
                    function_name="create_node_class_identity_edge",
                    object_id=ROOT_OBJECT_ID,
                    kwargs={
                        "parent_node_class_identity_id": node_class_identity_id,
                        "child_node_class_identity_id": (
                            node_class_identity_channel_id
                        ),
                        "class_instance_relationship_identity_id": (
                            class_instance_relationship_identity_id
                        ),
                        "key": "front_door->news_channel",
                    },
                ),
            ],
        )
        assert result_oigi.root_object_id == projection_experience_oigi_id
        assertions_oigi.expect_instance(projection_experience_oigi_id)
        assertions_oigi.expect_instance(node_class_identity_id)
        assertions_oigi.expect_instance(node_class_identity_channel_id)
        assertions_oigi.expect_instance(node_class_identity_edge_id)
        assertions_oigi.expect_edge(
            source_id=projection_experience_oigi_id,
            target_id=node_class_identity_id,
            relationship_name="node_class_identities",
        )
        assertions_oigi.expect_edge(
            source_id=projection_experience_oigi_id,
            target_id=node_class_identity_channel_id,
            relationship_name="node_class_identities",
        )
        assertions_oigi.expect_edge(
            source_id=projection_experience_oigi_id,
            target_id=node_class_identity_edge_id,
            relationship_name="node_class_identity_edges",
        )
        assertions_oigi.expect_primitive(
            instance_id=projection_experience_oigi_id,
            field_name="key",
            expected="runtime.main",
        )
        assertions_oigi.expect_primitive(
            instance_id=node_class_identity_id,
            field_name="key",
            expected="front_door",
        )
        assertions_oigi.expect_primitive(
            instance_id=node_class_identity_edge_id,
            field_name="key",
            expected="front_door->news_channel",
        )

        replay_identity = await _invoke_meta_function(
            runtime=runtime,
            lane=lane,
            projection_hash=result_oigi.projection_hash,
            target="instance",
            class_fqn=PROJECTION_EXPERIENCE_OIGI_CLASS_FQN,
            function_name="create_node_class_identity",
            object_id=projection_experience_oigi_id,
            kwargs={
                "projection_experience_node_identity_id": node_identity_id,
                "class_instance_identity_id": class_instance_identity_id,
                "key": "front_door",
            },
        )
        assert replay_identity.status == "succeeded", replay_identity.error
        assert replay_identity.commit_id is None


@pytest.mark.asyncio
async def test_projection_experience_oigi_fail_closed_on_unknown_class_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_experience_ontology  # noqa: F401
    import aware_history_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.stable_ids import (
        stable_projection_experience_id,
        stable_projection_experience_node_id,
        stable_projection_experience_node_identity_id,
        stable_projection_experience_oigi_id,
    )
    from aware_meta_ontology.stable_ids import stable_object_instance_graph_identity_id

    ns = uuid5(
        NAMESPACE_URL,
        "aware://tests/experience/projection-experience-oigi/fail-closed/v1",
    )
    environment_id = uuid5(ns, "environment")
    thread_id = uuid5(ns, "thread")
    lane = LaneIds(
        branch_id=stable_branch_id(environment_id=environment_id, thread_id=thread_id),
    )
    opgi_id = uuid5(ns, "opgi")
    object_instance_graph_identity_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi_id,
        object_instance_graph_id=uuid5(ns, "object-instance-graph"),
    )
    projection_node_id = uuid5(ns, "projection-node")
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
    projection_experience_oigi_id = stable_projection_experience_oigi_id(
        projection_experience_id=projection_experience_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        _result_projection, _assertions_projection = await run_meta_runtime_proof(
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
        result_oigi, _assertions_oigi = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="ProjectionExperienceOIGI",
            root_class_fqn=PROJECTION_EXPERIENCE_OIGI_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=PROJECTION_EXPERIENCE_OIGI_CLASS_FQN,
                    function_name="build_via_projection_experience",
                    kwargs={
                        "projection_experience_id": projection_experience_id,
                        "object_instance_graph_identity_id": (
                            object_instance_graph_identity_id
                        ),
                        "key": "runtime.main",
                    },
                    expected_root_object_id=projection_experience_oigi_id,
                ),
            ],
        )

        with pytest.raises(RuntimeError, match="requires known ClassInstanceIdentity"):
            await _invoke_meta_function(
                runtime=runtime,
                lane=lane,
                projection_hash=result_oigi.projection_hash,
                target="instance",
                class_fqn=PROJECTION_EXPERIENCE_OIGI_CLASS_FQN,
                function_name="create_node_class_identity",
                object_id=projection_experience_oigi_id,
                kwargs={
                    "projection_experience_node_identity_id": node_identity_id,
                    "class_instance_identity_id": uuid5(
                        ns,
                        "missing-class-instance-identity",
                    ),
                    "key": "front_door",
                },
            )
