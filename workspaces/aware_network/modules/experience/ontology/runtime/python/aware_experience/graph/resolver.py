from uuid import UUID

from aware_experience_ontology.projection.projection_experience_graph_identity import (
    ProjectionExperienceGraphIdentity,
)

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.handler_context import (
    current_handler_context,
    current_handler_index,
    current_handler_session,
)


def _resolve_object_instance_graph_identity_opg(
    index: MetaGraphRuntimeIndex,
) -> ObjectProjectionGraph | None:
    return next(
        (
            opg
            for opg in index.ocg.object_projection_graphs
            if (opg.name or "").strip() == "ObjectInstanceGraphIdentity"
        ),
        None,
    )


def _resolve_projection_experience_opg(
    index: MetaGraphRuntimeIndex,
) -> ObjectProjectionGraph | None:
    return next(
        (
            opg
            for opg in index.ocg.object_projection_graphs
            if (opg.name or "").strip() == "ProjectionExperience"
        ),
        None,
    )


def _resolve_projection_experience_graph_opg(
    index: MetaGraphRuntimeIndex,
) -> ObjectProjectionGraph | None:
    return next(
        (
            opg
            for opg in index.ocg.object_projection_graphs
            if (opg.name or "").strip() == "ProjectionExperienceGraph"
        ),
        None,
    )


async def _lane_contains_source_object_id(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph | None,
    branch_id: UUID | None,
    source_object_id: UUID,
    missing_projection_error: str,
    missing_branch_error: str,
) -> bool:
    if opg is None:
        raise RuntimeError(missing_projection_error)
    if branch_id is None:
        raise RuntimeError(missing_branch_error)
    source_object_ids = await _materialize_lane_instance_ids(
        index=index,
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
    )
    return source_object_id in source_object_ids


async def object_instance_graph_identity_exists_via_lane(
    *,
    object_instance_graph_identity_id: UUID,
) -> bool:
    index = current_handler_index()
    handler_ctx = current_handler_context()
    return await _lane_contains_source_object_id(
        index=index,
        opg=_resolve_object_instance_graph_identity_opg(index=index),
        branch_id=handler_ctx.branch_id,
        source_object_id=object_instance_graph_identity_id,
        missing_projection_error="ProjectionExperience.create_oigi requires object_instance_graph_identity projection",
        missing_branch_error="ProjectionExperience.create_oigi requires branch_id lane context",
    )


async def projection_experience_exists_via_lane(
    *,
    projection_experience_id: UUID,
) -> bool:
    index = current_handler_index()
    handler_ctx = current_handler_context()
    return await _lane_contains_source_object_id(
        index=index,
        opg=_resolve_projection_experience_opg(index=index),
        branch_id=handler_ctx.branch_id,
        source_object_id=projection_experience_id,
        missing_projection_error=(
            "ProjectionExperienceGraph.create_via_projection requires projection_experience projection"
        ),
        missing_branch_error="ProjectionExperienceGraph.create_via_projection requires branch_id lane context",
    )


async def projection_experience_owns_view_via_lane(
    *,
    projection_experience_view_id: UUID,
) -> bool:
    index = current_handler_index()
    handler_ctx = current_handler_context()
    return await _lane_contains_source_object_id(
        index=index,
        opg=_resolve_projection_experience_opg(index=index),
        branch_id=handler_ctx.branch_id,
        source_object_id=projection_experience_view_id,
        missing_projection_error=(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires projection_experience "
            + "projection"
        ),
        missing_branch_error=(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires branch_id lane context"
        ),
    )


async def projection_experience_owns_node_identity_via_lane(
    *,
    projection_experience_node_identity_id: UUID,
) -> bool:
    index = current_handler_index()
    handler_ctx = current_handler_context()
    return await _lane_contains_source_object_id(
        index=index,
        opg=_resolve_projection_experience_opg(index=index),
        branch_id=handler_ctx.branch_id,
        source_object_id=projection_experience_node_identity_id,
        missing_projection_error="ProjectionExperienceGraph.create_identity requires projection_experience projection",
        missing_branch_error="ProjectionExperienceGraph.create_identity requires branch_id lane context",
    )


async def projection_experience_owns_section_surface_via_lane(
    *,
    projection_experience_section_surface_id: UUID,
) -> bool:
    index = current_handler_index()
    handler_ctx = current_handler_context()
    return await _lane_contains_source_object_id(
        index=index,
        opg=_resolve_projection_experience_opg(index=index),
        branch_id=handler_ctx.branch_id,
        source_object_id=projection_experience_section_surface_id,
        missing_projection_error=(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires projection_experience "
            + "projection"
        ),
        missing_branch_error=(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires branch_id lane context"
        ),
    )


async def projection_experience_graph_owns_graph_identity_via_lane(
    *,
    projection_experience_graph_identity_id: UUID,
) -> bool:
    index = current_handler_index()
    handler_ctx = current_handler_context()
    return await _lane_contains_source_object_id(
        index=index,
        opg=_resolve_projection_experience_graph_opg(index=index),
        branch_id=handler_ctx.branch_id,
        source_object_id=projection_experience_graph_identity_id,
        missing_projection_error=(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires "
            + "projection_experience_graph projection"
        ),
        missing_branch_error=(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires "
            + "branch_id lane context"
        ),
    )


async def hydrate_projection_experience_graph_identity_into_active_session(
    *,
    projection_experience_graph_identity_id: UUID,
) -> ProjectionExperienceGraphIdentity | None:
    session = current_handler_session()
    existing = session.imap_get(
        ProjectionExperienceGraphIdentity,
        projection_experience_graph_identity_id,
    )
    if existing is not None:
        return existing

    index = current_handler_index()
    handler_ctx = current_handler_context()
    graph_opg = _resolve_projection_experience_graph_opg(index=index)
    if graph_opg is None:
        raise RuntimeError(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires "
            + "projection_experience_graph projection"
        )
    if handler_ctx.branch_id is None:
        raise RuntimeError(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires "
            + "branch_id lane context"
        )

    head = await FSCommitStore().head(
        branch_id=handler_ctx.branch_id,
        projection_hash=graph_opg.projection_hash,
    )
    if head is None or not head.get("commit_id"):
        return None

    commit_id = UUID(str(head["commit_id"]))
    oig_id = (
        UUID(str(head["object_instance_graph_id"]))
        if head.get("object_instance_graph_id")
        else None
    )
    oig, _ = await CachedLaneMaterializer().get(
        branch_id=handler_ctx.branch_id,
        ocg=index.ocg,
        opg=graph_opg,
        commit_id=commit_id,
        oig_id=oig_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    scratch = reify_oig_session(
        index=index,
        opg=graph_opg,
        oig=oig,
        branch_id=handler_ctx.branch_id,
    )
    hydrated = scratch.imap_get(
        ProjectionExperienceGraphIdentity,
        projection_experience_graph_identity_id,
    )
    if hydrated is None:
        return None

    session.merge(hydrated)
    return session.imap_get(
        ProjectionExperienceGraphIdentity,
        projection_experience_graph_identity_id,
    )


async def object_instance_graph_identity_owns_class_instance_identity_via_lane(
    *,
    class_instance_identity_id: UUID,
) -> bool:
    index = current_handler_index()
    handler_ctx = current_handler_context()
    oigi_opg = _resolve_object_instance_graph_identity_opg(index=index)
    if oigi_opg is None:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity requires object_instance_graph_identity projection"
        )
    if handler_ctx.branch_id is None:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity requires branch_id lane context"
        )
    source_object_ids = await _materialize_lane_instance_ids(
        index=index,
        branch_id=handler_ctx.branch_id,
        projection_hash=oigi_opg.projection_hash,
    )
    return class_instance_identity_id in source_object_ids


async def object_instance_graph_identity_owns_class_instance_relationship_identity_via_lane(
    *,
    class_instance_relationship_identity_id: UUID,
) -> bool:
    index = current_handler_index()
    handler_ctx = current_handler_context()
    oigi_opg = _resolve_object_instance_graph_identity_opg(index=index)
    if oigi_opg is None:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge requires object_instance_graph_identity projection"
        )
    if handler_ctx.branch_id is None:
        raise RuntimeError(
            "ProjectionExperienceOIGI.create_node_class_identity_edge requires branch_id lane context"
        )
    source_object_ids = await _materialize_lane_instance_ids(
        index=index,
        branch_id=handler_ctx.branch_id,
        projection_hash=oigi_opg.projection_hash,
    )
    return class_instance_relationship_identity_id in source_object_ids


async def _materialize_lane_instance_ids(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> set[UUID]:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or not head.get("commit_id"):
        return set()

    commit_id = UUID(str(head["commit_id"]))
    oig_id_raw = head.get("object_instance_graph_id")
    oig_id = UUID(str(oig_id_raw)) if oig_id_raw else None
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        return set()

    oig, _idx = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        oig_id=oig_id,
    )
    source_object_ids: set[UUID] = set()
    for instance in oig.class_instances:
        source_object_id = getattr(instance, "source_object_id", None)
        if not isinstance(source_object_id, UUID):
            raise RuntimeError(
                "Lane materialization produced ClassInstance without "
                "source_object_id "
                f"(class_instance_id={getattr(instance, 'id', None)} "
                f"projection_hash={projection_hash})"
            )
        source_object_ids.add(source_object_id)
    return source_object_ids
