from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Protocol
from uuid import UUID

from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.graph.instance.orm_persistence import stage_domain_persistence
from aware_orm.session.session import Session
from aware_utils.logging import logger


class MetaOrmProjectionIndex(Protocol):
    ocg: Any
    opg_by_hash: dict[str, Any]
    attribute_configs_by_id: dict[UUID, Any]
    class_configs_by_id: dict[UUID, Any]


@dataclass(frozen=True, slots=True)
class LaneProjectionCatchupResult:
    branch_id: UUID
    projection_hash: str
    head_commit_id: UUID | None
    object_instance_graph_id: UUID | None
    commits_applied: int
    skipped_reason: str | None = None


def _session_backend_name(session: Session) -> str:
    raw = getattr(session, "_backend_name", None)
    if isinstance(raw, str) and raw.strip():
        return raw.strip().lower()
    env = os.getenv("AWARE_PERSISTENCE_BACKEND", "").strip().lower()
    if env:
        return env
    return "noop" if session.skip_db else "db"


async def ensure_lane_projection_caught_up(
    *,
    index: MetaOrmProjectionIndex,
    branch_id: UUID,
    projection_hash: str,
    head_commit_id: UUID | None = None,
    object_instance_graph_id: UUID | None = None,
    commit_store: FSCommitStore | None = None,
    session: Session | None = None,
    commit_every: int = 25,
) -> LaneProjectionCatchupResult:
    """Replay a committed OIG lane into the DB read model through the ORM projector.

    The filesystem commit log remains the source of truth. This helper only catches the
    derived SQL projection up to a known lane head by replaying commits through
    ``stage_domain_persistence``; it does not seed rows directly.
    """

    resolved_session = session or Session(branch_id=branch_id)
    backend = _session_backend_name(resolved_session)
    if resolved_session.skip_db or backend != "db":
        return LaneProjectionCatchupResult(
            branch_id=branch_id,
            projection_hash=projection_hash,
            head_commit_id=head_commit_id,
            object_instance_graph_id=object_instance_graph_id,
            commits_applied=0,
            skipped_reason=f"backend:{backend}",
        )

    store = commit_store or FSCommitStore()
    resolved_head_commit_id = head_commit_id
    resolved_oig_id = object_instance_graph_id
    if resolved_head_commit_id is None or resolved_oig_id is None:
        head = await store.head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if head is None or not head.get("commit_id"):
            return LaneProjectionCatchupResult(
                branch_id=branch_id,
                projection_hash=projection_hash,
                head_commit_id=None,
                object_instance_graph_id=None,
                commits_applied=0,
                skipped_reason="missing_head",
            )
        resolved_head_commit_id = UUID(str(head["commit_id"]))
        raw_oig_id = head.get("object_instance_graph_id")
        if raw_oig_id is not None:
            resolved_oig_id = UUID(str(raw_oig_id))

    if resolved_oig_id is None:
        raise RuntimeError(
            "Lane projection catch-up requires object_instance_graph_id: "
            f"branch_id={branch_id} projection_hash={projection_hash} "
            f"head_commit_id={resolved_head_commit_id}"
        )

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Lane projection catch-up cannot resolve projection hash in runtime index: "
            f"{projection_hash} (branch_id={branch_id})"
        )

    commits = [
        commit
        async for commit in store.iter_lineage_forward(
            branch_id=branch_id,
            projection_hash=projection_hash,
            head_commit_id=resolved_head_commit_id,
            stop_at_commit_id=None,
        )
    ]
    if not commits:
        return LaneProjectionCatchupResult(
            branch_id=branch_id,
            projection_hash=projection_hash,
            head_commit_id=resolved_head_commit_id,
            object_instance_graph_id=resolved_oig_id,
            commits_applied=0,
            skipped_reason="empty_lineage",
        )

    bootstrap_commit = commits[0]
    if bootstrap_commit.object_instance_graph_id != resolved_oig_id:
        raise RuntimeError(
            "Lane projection catch-up bootstrap OIG mismatch: "
            f"expected={resolved_oig_id} actual={bootstrap_commit.object_instance_graph_id} "
            f"(branch_id={branch_id} projection_hash={projection_hash})"
        )

    graph = build_rooted_object_instance_graph_base(
        key=bootstrap_commit.object_instance_graph_key,
        name=bootstrap_commit.object_instance_graph_name,
        description=bootstrap_commit.object_instance_graph_description or "",
        object_config_graph=index.ocg,
        object_projection_graph=opg,
        root_source_object_id=bootstrap_commit.root_source_object_id,
        root_class_config_id=bootstrap_commit.root_class_config_id,
        oig_id=resolved_oig_id,
    )

    commits_applied = 0
    staged_since_commit = 0
    try:
        for commit in commits:
            if commit.object_instance_graph_id != resolved_oig_id:
                raise RuntimeError(
                    "Lane projection catch-up OIG id mismatch: "
                    f"expected={resolved_oig_id} actual={commit.object_instance_graph_id} "
                    f"(branch_id={branch_id} projection_hash={projection_hash} "
                    f"commit_id={commit.commit.id})"
                )

            before_oig = graph.model_copy(deep=True)
            apply_object_instance_graph_changes(
                graph=graph,
                changes=commit.object_instance_graph_changes,
                attribute_configs_by_id=index.attribute_configs_by_id,
                class_configs_by_id=index.class_configs_by_id,
            )
            graph_index = build_index(graph)
            graph.hash = compute_hash(graph, index=graph_index)

            expected_pre = (commit.graph_hash_pre or "").strip()
            expected_post = (commit.graph_hash_post or "").strip()
            if expected_pre and expected_pre != before_oig.hash:
                raise RuntimeError(
                    "Lane projection catch-up graph_hash_pre mismatch: "
                    f"expected={expected_pre} actual={before_oig.hash} "
                    f"(branch_id={branch_id} projection_hash={projection_hash} "
                    f"commit_id={commit.commit.id})"
                )
            if expected_post and expected_post != graph.hash:
                raise RuntimeError(
                    "Lane projection catch-up graph_hash_post mismatch: "
                    f"expected={expected_post} actual={graph.hash} "
                    f"(branch_id={branch_id} projection_hash={projection_hash} "
                    f"commit_id={commit.commit.id})"
                )

            await stage_domain_persistence(
                index=index,
                session=resolved_session,
                branch_id=branch_id,
                projection_hash=projection_hash,
                before_oig=before_oig,
                after_oig=graph,
                changes=commit.object_instance_graph_changes,
            )
            commits_applied += 1
            staged_since_commit += 1
            if commit_every > 0 and staged_since_commit >= commit_every:
                await resolved_session.commit()
                staged_since_commit = 0

        if staged_since_commit:
            await resolved_session.commit()
    except Exception:
        try:
            await resolved_session.rollback()
        except Exception:
            logger.exception(
                "Lane projection catch-up rollback failed "
                "(branch_id=%s projection_hash=%s)",
                branch_id,
                projection_hash,
            )
        raise

    return LaneProjectionCatchupResult(
        branch_id=branch_id,
        projection_hash=projection_hash,
        head_commit_id=resolved_head_commit_id,
        object_instance_graph_id=resolved_oig_id,
        commits_applied=commits_applied,
        skipped_reason=None,
    )


__all__ = [
    "LaneProjectionCatchupResult",
    "ensure_lane_projection_caught_up",
]
