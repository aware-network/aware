from __future__ import annotations

from collections.abc import Iterable
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_meta.enum.instance.option_resolver import build_enum_option_resolver
from aware_meta.graph.config.lane.common import (
    DEFAULT_OCG_COMMIT_STATUS,
    DEFAULT_OCG_SOURCE_LANGUAGE,
    SEED_CREATED_AT,
    SYSTEM_ACTOR_ID,
)
from aware_meta.graph.config.lane.errors import GraphIdentitySeedError
from aware_meta.graph.config.lane.plan import GraphIdentitySeedPlan
from aware_meta.graph.config.lane.projection import (
    compose_ocg_seed_schema_graph,
    resolve_ocg_seed_projection_context,
)
from aware_meta.graph.config.lane.registry import collect_orm_models
from aware_meta.graph.instance.builder import (
    build_object_instance_graph,
    build_rooted_object_instance_graph_base,
)
from aware_meta.graph.instance.commit.builder import (
    OigCommitBuildError,
    build_object_instance_graph_commit,
    build_object_instance_graph_commit_from_changes,
)
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.validator import OigCommitValidationError
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_orm.models.base_model import BaseORMModel


def _identity_seed_commit_id(*, branch_id: UUID, projection_hash: str, graph_hash_post: str) -> UUID:
    if not (projection_hash or "").strip():
        raise GraphIdentitySeedError("Identity seed commit id requires a non-empty projection_hash")
    if not (graph_hash_post or "").strip():
        raise GraphIdentitySeedError("Identity seed commit id requires a non-empty graph_hash_post")
    return uuid5(
        NAMESPACE_URL,
        f"aware:identity-seed:{branch_id}:{projection_hash}:{graph_hash_post}",
    )


async def ensure_graph_identity_seeded_lane(
    *,
    root_instance: BaseORMModel,
    ocg: ObjectConfigGraph,
    branch_id: UUID,
    opg_name: str,
    author_id: UUID = SYSTEM_ACTOR_ID,
    external_graphs: Iterable[ObjectConfigGraph] = (),
    store: FSCommitStore | None = None,
    allow_append: bool = True,
) -> GraphIdentitySeedPlan:
    """Ensure a deterministic seed commit exists for an identity projection lane."""
    identity_id = root_instance.id
    if str(identity_id) != str(branch_id):
        raise GraphIdentitySeedError(
            "Identity seed requires branch_id to equal root_instance.id: "
            + f"branch_id={branch_id} root_instance_id={identity_id}"
        )

    external_graphs_list = list(external_graphs or ())
    _schema_graph, opg = resolve_ocg_seed_projection_context(
        ocg=ocg, external_graphs=external_graphs_list, opg_name=opg_name
    )
    if not opg.projection_hash:
        raise GraphIdentitySeedError(
            f"Identity seed requires ObjectProjectionGraph.projection_hash: opg_name={opg_name!r}"
        )

    store = store or FSCommitStore()
    head = await store.head(branch_id=branch_id, projection_hash=opg.projection_hash)
    head_commit_id = head.get("commit_id") if head else None
    lane_empty = not bool(head_commit_id)
    if not lane_empty:
        head_oig_id = head.get("object_instance_graph_id") if head else None
        if head_oig_id and str(head_oig_id) != str(identity_id):
            raise GraphIdentitySeedError(
                "Identity lane head has mismatched object_instance_graph_id: "
                + f"branch_id={branch_id} head_object_instance_graph_id={head_oig_id} expected={identity_id}"
            )
        return GraphIdentitySeedPlan(
            seeded=False,
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            object_instance_graph_id=identity_id,
            root_object_id=identity_id,
            commit_id=(UUID(str(head_commit_id)) if head_commit_id else None),
            graph_hash_post=(
                str(head["graph_hash_post"])
                if head is not None and "graph_hash_post" in head and head["graph_hash_post"] is not None
                else None
            ),
        )

    if lane_empty and not allow_append:
        raise GraphIdentitySeedError(
            "Identity lane is empty (no HEAD commit). "
            + "Compiler must emit identity seeds before runtime boot. "
            + f"branch_id={branch_id} projection_hash={opg.projection_hash} opg_name={opg_name!r}"
        )

    plan, commit = _build_identity_seed_plan_and_commit(
        root_instance=root_instance,
        ocg=ocg,
        branch_id=branch_id,
        opg_name=opg_name,
        author_id=author_id,
        external_graphs=external_graphs_list,
    )
    commit_id = plan.commit_id
    if commit_id is None:
        raise GraphIdentitySeedError("Identity seed plan missing deterministic commit_id")

    existing = await store.get_commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=commit_id,
    )
    if existing is not None:
        if existing.graph_hash_pre != commit.graph_hash_pre or existing.graph_hash_post != commit.graph_hash_post:
            raise GraphIdentitySeedError(
                "Existing identity seed commit differs from expected payload: "
                + f"branch_id={branch_id} projection_hash={opg.projection_hash} seed_commit_id={commit_id}"
            )
        parents = existing.commit.commit_parents
        if parents:
            raise GraphIdentitySeedError(
                f"Identity seed commit must not have parents: commit_id={commit_id} parents={len(parents)}"
            )
        return GraphIdentitySeedPlan(
            seeded=False,
            branch_id=plan.branch_id,
            projection_hash=plan.projection_hash,
            object_instance_graph_id=plan.object_instance_graph_id,
            root_object_id=plan.root_object_id,
            commit_id=plan.commit_id,
            graph_hash_pre=plan.graph_hash_pre,
            graph_hash_post=plan.graph_hash_post,
        )

    if not allow_append:
        raise GraphIdentitySeedError(
            "Missing deterministic identity seed commit (compiler must emit it): "
            + f"branch_id={branch_id} projection_hash={opg.projection_hash} seed_commit_id={commit_id}"
        )

    try:
        _ = await store.append(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            commit=commit,
            root_object_id=identity_id,
        )
    except OigCommitBuildError as exc:
        raise GraphIdentitySeedError(f"Failed to build identity seed commit: {exc}") from exc
    except (ValueError, OigCommitValidationError) as exc:
        raise GraphIdentitySeedError(f"Failed to emit identity seed commit: {exc}") from exc

    return plan


async def preview_graph_identity_seed_plan(
    *,
    root_instance: BaseORMModel,
    ocg: ObjectConfigGraph,
    branch_id: UUID,
    opg_name: str,
    author_id: UUID = SYSTEM_ACTOR_ID,
    external_graphs: Iterable[ObjectConfigGraph] = (),
) -> GraphIdentitySeedPlan:
    """Build the current deterministic identity-seed plan without touching the commit store."""
    plan, _commit = _build_identity_seed_plan_and_commit(
        root_instance=root_instance,
        ocg=ocg,
        branch_id=branch_id,
        opg_name=opg_name,
        author_id=author_id,
        external_graphs=external_graphs,
    )
    return plan


def _build_identity_seed_plan_and_commit(
    *,
    root_instance: BaseORMModel,
    ocg: ObjectConfigGraph,
    branch_id: UUID,
    opg_name: str,
    author_id: UUID,
    external_graphs: Iterable[ObjectConfigGraph],
) -> tuple[GraphIdentitySeedPlan, ObjectInstanceGraphCommit]:
    identity_id = root_instance.id
    if str(identity_id) != str(branch_id):
        raise GraphIdentitySeedError(
            "Identity seed requires branch_id to equal root_instance.id: "
            + f"branch_id={branch_id} root_instance_id={identity_id}"
        )

    external_graphs_list = list(external_graphs or ())
    schema_graph, opg = resolve_ocg_seed_projection_context(
        ocg=ocg,
        external_graphs=external_graphs_list,
        opg_name=opg_name,
    )
    if not opg.projection_hash:
        raise GraphIdentitySeedError(
            f"Identity seed requires ObjectProjectionGraph.projection_hash: opg_name={opg_name!r}"
        )

    objects_by_id = collect_orm_models(root_instance)
    if not objects_by_id:
        raise GraphIdentitySeedError("Identity seed requires at least one ORM object (empty root_instance)")

    schema_view = compose_ocg_seed_schema_graph(
        schema_graph=schema_graph,
        external_graphs=external_graphs_list,
    )
    before_oig = build_rooted_object_instance_graph_base(
        key=opg_name,
        name=opg_name,
        description=f"{opg_name} seed base snapshot",
        object_config_graph=schema_view,
        object_projection_graph=opg,
        root_source_object_id=root_instance.id,
        oig_id=branch_id,
    )
    enum_option_resolver = build_enum_option_resolver(object_config_graph=schema_view)
    after_oig = build_object_instance_graph(
        root_instance=root_instance,
        object_config_graph=schema_view,
        object_projection_graph=opg,
        name=opg_name,
        description=f"{opg_name} seed snapshot",
        oig_id=branch_id,
        instance_registry=sorted(objects_by_id.values(), key=lambda o: str(o.id)),
        enum_option_resolver=enum_option_resolver,
    )

    seed_commit = build_object_instance_graph_commit(
        old=before_oig,
        new=after_oig,
        branch_id=branch_id,
        object_instance_graph_identity_id=before_oig.id,
        object_projection_graph=opg,
        author_id=author_id,
        commit_id=None,
        created_at=SEED_CREATED_AT,
        source_language=DEFAULT_OCG_SOURCE_LANGUAGE,
        status=DEFAULT_OCG_COMMIT_STATUS,
    )
    if seed_commit is None:
        raise GraphIdentitySeedError("Identity seed produced no changes")
    changes = seed_commit.object_instance_graph_changes
    if not changes:
        raise GraphIdentitySeedError("Identity seed commit missing change payload")
    if not seed_commit.projection_hash:
        raise GraphIdentitySeedError("Identity seed commit missing projection_hash")
    if not seed_commit.graph_hash_post:
        raise GraphIdentitySeedError("Identity seed commit missing graph_hash_post")

    commit_id = _identity_seed_commit_id(
        branch_id=branch_id,
        projection_hash=seed_commit.projection_hash,
        graph_hash_post=seed_commit.graph_hash_post,
    )
    commit = build_object_instance_graph_commit_from_changes(
        before_oig=before_oig,
        changes=changes,
        branch_id=branch_id,
        object_instance_graph_identity_id=seed_commit.object_instance_graph_identity_id,
        object_instance_graph_id=seed_commit.object_instance_graph_id,
        projection_hash=seed_commit.projection_hash,
        graph_hash_pre=seed_commit.graph_hash_pre,
        graph_hash_post=seed_commit.graph_hash_post,
        author_id=author_id,
        parent_commit_id=None,
        commit_id=commit_id,
        source_language=DEFAULT_OCG_SOURCE_LANGUAGE,
        status=DEFAULT_OCG_COMMIT_STATUS,
        created_at=SEED_CREATED_AT,
    )
    return GraphIdentitySeedPlan(
        seeded=True,
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_id=identity_id,
        root_object_id=identity_id,
        commit_id=commit_id,
        graph_hash_pre=commit.graph_hash_pre,
        graph_hash_post=commit.graph_hash_post,
    ), commit
