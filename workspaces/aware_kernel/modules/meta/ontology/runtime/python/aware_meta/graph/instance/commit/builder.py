"""Canonical OIG commit builder.

SSOT: `ObjectInstanceGraphCommit` containing a Change-graph payload:

Commit → ObjectInstanceGraphChange[] → Change(type) → ChangeDelta[] (delta-only)

This module is intentionally pure and deterministic:
- No DB lookups
- No branch head mutation (branches are head pointers, like git)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from aware_history_ontology.stable_ids import stable_lane_id
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.commit.commit_parent import CommitParent
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.graph.instance.commit.contract import (
    ObjectInstanceGraphCommitRootMetadata,
)

from aware_orm.session.autobind import disable_autobind


class OigCommitBuildError(ValueError):
    pass


DEFAULT_SOURCE_LANGUAGE: CodeLanguage = CodeLanguage("python")
DEFAULT_COMMIT_STATUS: CommitStatus = CommitStatus("local")


def extract_object_instance_graph_commit_root_metadata(
    *,
    graph: ObjectInstanceGraph,
) -> ObjectInstanceGraphCommitRootMetadata:
    if not (graph.key or "").strip():
        raise OigCommitBuildError(
            "Rooted OIG commit metadata requires ObjectInstanceGraph.key"
        )
    root_class_instance: ClassInstance = graph.root_class_instance
    if (
        graph.root_class_instance_id is not None
        and root_class_instance.id != graph.root_class_instance_id
    ):
        raise OigCommitBuildError(
            "Rooted OIG commit metadata root_class_instance mismatch: "
            + f"root_class_instance.id={root_class_instance.id} expected={graph.root_class_instance_id}"
        )
    return ObjectInstanceGraphCommitRootMetadata(
        object_instance_graph_key=graph.key,
        object_instance_graph_name=graph.name,
        object_instance_graph_description=graph.description,
        root_class_config_id=root_class_instance.class_config_id,
        root_source_object_id=root_class_instance.source_object_id,
    )


def build_object_instance_graph_commit(
    *,
    old: ObjectInstanceGraph,
    new: ObjectInstanceGraph,
    branch_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_projection_graph: ObjectProjectionGraph,
    author_id: UUID,
    parent_commit_id: UUID | None = None,
    commit_id: UUID | None = None,
    source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
    status: CommitStatus = DEFAULT_COMMIT_STATUS,
    created_at: datetime | None = None,
) -> ObjectInstanceGraphCommit | None:
    """
    Build an `ObjectInstanceGraphCommit` from two OIG snapshots.

    The commit payload is generated via the canonical OIG diff:
    `diff_object_instance_graph_changes(old, new)`.

    Returns None when no changes are detected.
    """
    if old.id != new.id:
        raise OigCommitBuildError(
            f"Snapshots must target the same OIG id; old={old.id} new={new.id}"
        )
    if old.object_projection_graph_id != new.object_projection_graph_id:
        raise OigCommitBuildError("Snapshots must share object_projection_graph_id")
    if old.object_projection_graph_id != object_projection_graph.id:
        raise OigCommitBuildError(
            "Snapshots must match the provided ObjectProjectionGraph; "
            + f"graph_opg_id={old.object_projection_graph_id} opg_id={object_projection_graph.id}"
        )
    if not object_projection_graph.projection_hash:
        raise OigCommitBuildError(
            "ObjectProjectionGraph.projection_hash is required to build lane commits"
        )

    commit_created_at = created_at or datetime.now(timezone.utc)

    pre_hash = compute_hash(old, index=build_index(old))
    post_hash = compute_hash(new, index=build_index(new))

    changes = diff_object_instance_graph_changes(
        old=old,
        new=new,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        created_at=commit_created_at,
    )
    if not changes:
        if pre_hash != post_hash:
            raise OigCommitBuildError(
                f"No Change graph produced, but OIG content hash changed. pre={pre_hash} post={post_hash}"
            )
        return None

    return build_object_instance_graph_commit_from_changes(
        before_oig=old,
        changes=changes,
        branch_id=branch_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=old.id,
        projection_hash=object_projection_graph.projection_hash,
        graph_hash_pre=pre_hash,
        graph_hash_post=post_hash,
        author_id=author_id,
        parent_commit_id=parent_commit_id,
        commit_id=commit_id,
        source_language=source_language,
        status=status,
        created_at=commit_created_at,
    )


def build_object_instance_graph_commit_from_changes(
    *,
    before_oig: ObjectInstanceGraph,
    changes: list[ObjectInstanceGraphChange],
    branch_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    projection_hash: str,
    graph_hash_pre: str,
    graph_hash_post: str,
    author_id: UUID,
    parent_commit_id: UUID | None = None,
    commit_id: UUID | None = None,
    source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
    status: CommitStatus = DEFAULT_COMMIT_STATUS,
    created_at: datetime | None = None,
) -> ObjectInstanceGraphCommit:
    """
    Build an `ObjectInstanceGraphCommit` from a precomputed Change graph payload.

    This function is used by the snapshot-diff rail today, but it is also the
    canonical hook for future incremental (mutation-log) change detection.
    """
    if not changes:
        raise OigCommitBuildError(
            "Commit must include at least one ObjectInstanceGraphChange"
        )
    if before_oig.id != object_instance_graph_id:
        raise OigCommitBuildError(
            "Commit before_oig id mismatch: "
            + f"before_oig.id={before_oig.id} object_instance_graph_id={object_instance_graph_id}"
        )
    for change in changes:
        if (
            change.object_instance_graph_identity_id
            != object_instance_graph_identity_id
        ):
            raise OigCommitBuildError(
                "Commit change tree owner mismatch: "
                + f"have={change.object_instance_graph_identity_id} expected={object_instance_graph_identity_id}"
            )
        if change.object_instance_graph_id != object_instance_graph_id:
            raise OigCommitBuildError(
                "Commit change tree payload mismatch: "
                + f"have={change.object_instance_graph_id} expected={object_instance_graph_id}"
            )

    commit_created_at = created_at or datetime.now(timezone.utc)
    rooted_metadata = extract_object_instance_graph_commit_root_metadata(
        graph=before_oig
    )
    return _build_object_instance_graph_commit_from_root_metadata(
        root_metadata=rooted_metadata,
        changes=changes,
        branch_id=branch_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        projection_hash=projection_hash,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        author_id=author_id,
        parent_commit_id=parent_commit_id,
        commit_id=commit_id,
        source_language=source_language,
        status=status,
        created_at=commit_created_at,
    )


def build_object_instance_graph_commit_from_shallow_changes(
    *,
    root_metadata: ObjectInstanceGraphCommitRootMetadata,
    changes: list[ObjectInstanceGraphChange],
    branch_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    projection_hash: str,
    graph_hash_pre: str,
    graph_hash_post: str,
    author_id: UUID,
    parent_commit_id: UUID | None = None,
    commit_id: UUID | None = None,
    source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
    status: CommitStatus = DEFAULT_COMMIT_STATUS,
    created_at: datetime | None = None,
) -> ObjectInstanceGraphCommit:
    if not changes:
        raise OigCommitBuildError(
            "Commit must include at least one ObjectInstanceGraphChange"
        )
    for change in changes:
        if (
            change.object_instance_graph_identity_id
            != object_instance_graph_identity_id
        ):
            raise OigCommitBuildError(
                "Commit change tree owner mismatch: "
                + f"have={change.object_instance_graph_identity_id} expected={object_instance_graph_identity_id}"
            )
        if change.object_instance_graph_id != object_instance_graph_id:
            raise OigCommitBuildError(
                "Commit change tree payload mismatch: "
                + f"have={change.object_instance_graph_id} expected={object_instance_graph_id}"
            )

    return _build_object_instance_graph_commit_from_root_metadata(
        root_metadata=root_metadata,
        changes=changes,
        branch_id=branch_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        projection_hash=projection_hash,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        author_id=author_id,
        parent_commit_id=parent_commit_id,
        commit_id=commit_id,
        source_language=source_language,
        status=status,
        created_at=created_at or datetime.now(timezone.utc),
    )


def _build_object_instance_graph_commit_from_root_metadata(
    *,
    root_metadata: ObjectInstanceGraphCommitRootMetadata,
    changes: list[ObjectInstanceGraphChange],
    branch_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    projection_hash: str,
    graph_hash_pre: str,
    graph_hash_post: str,
    author_id: UUID,
    parent_commit_id: UUID | None,
    commit_id: UUID | None,
    source_language: CodeLanguage,
    status: CommitStatus,
    created_at: datetime,
) -> ObjectInstanceGraphCommit:
    resolved_commit_id = commit_id or uuid4()
    lane_id = stable_lane_id(branch_id=branch_id, lane_hash=projection_hash)

    with disable_autobind():
        commit = Commit(
            id=resolved_commit_id,
            lane_id=lane_id,
            key=str(resolved_commit_id),
            author_id=author_id,
            status=status,
            created_at=created_at,
            commit_parents=[],
        )
    if parent_commit_id is not None:
        with disable_autobind():
            commit.commit_parents.append(
                CommitParent(
                    commit_id=commit.id,
                    parent_commit_id=parent_commit_id,
                )
            )

    with disable_autobind():
        return ObjectInstanceGraphCommit(
            commit=commit,
            commit_id=commit.id,
            object_instance_graph_changes=changes,
            object_instance_graph_key=root_metadata.object_instance_graph_key,
            object_instance_graph_name=root_metadata.object_instance_graph_name,
            object_instance_graph_description=root_metadata.object_instance_graph_description,
            root_class_config_id=root_metadata.root_class_config_id,
            root_source_object_id=root_metadata.root_source_object_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            projection_hash=projection_hash,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            source_language=source_language,
        )


def build_object_instance_graph_seed_commit(
    *,
    rooted_oig: ObjectInstanceGraph,
    branch_id: UUID,
    object_instance_graph_identity_id: UUID,
    projection_hash: str,
    graph_hash_pre: str,
    graph_hash_post: str,
    author_id: UUID,
    parent_commit_id: UUID | None = None,
    commit_id: UUID | None = None,
    source_language: CodeLanguage = DEFAULT_SOURCE_LANGUAGE,
    status: CommitStatus = DEFAULT_COMMIT_STATUS,
    created_at: datetime | None = None,
) -> ObjectInstanceGraphCommit:
    """Build a canonical rooted seed commit with no change payload.

    This is allowed only for empty-lane bootstrap when the constructor result is
    semantically identical to the rooted base snapshot.
    """
    if parent_commit_id is not None:
        raise OigCommitBuildError("Seed commit must not declare a parent_commit_id")
    if not projection_hash:
        raise OigCommitBuildError("projection_hash is required")
    if graph_hash_pre != graph_hash_post:
        raise OigCommitBuildError(
            "Seed commit requires graph_hash_pre == graph_hash_post: "
            + f"pre={graph_hash_pre} post={graph_hash_post}"
        )

    commit_created_at = created_at or datetime.now(timezone.utc)
    rooted_metadata = extract_object_instance_graph_commit_root_metadata(
        graph=rooted_oig
    )
    return _build_object_instance_graph_commit_from_root_metadata(
        root_metadata=rooted_metadata,
        changes=[],
        branch_id=branch_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=rooted_oig.id,
        projection_hash=projection_hash,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        author_id=author_id,
        parent_commit_id=None,
        commit_id=commit_id,
        source_language=source_language,
        status=status,
        created_at=commit_created_at,
    )


__all__ = [
    "OigCommitBuildError",
    "build_object_instance_graph_commit",
    "build_object_instance_graph_commit_from_changes",
    "build_object_instance_graph_commit_from_shallow_changes",
    "build_object_instance_graph_seed_commit",
    "extract_object_instance_graph_commit_root_metadata",
]
