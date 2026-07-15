from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from aware_environment_service.navigation_models import (
    EnvironmentNavigationContextViewSpec,
)
from aware_environment_service.session_service import (
    EnvironmentSessionAttentionResolutionSpec,
    ResolveEnvironmentSessionAttentionRequestSpec,
)


class EnvironmentSessionAttentionCommittedSnapshot(BaseModel):
    """Committed EnvironmentSession -> Thread/Layout -> Attention resolution."""

    environment_session_id: UUID
    environment_id: UUID
    environment_profile_id: UUID | None = None
    environment_navigation_context_id: UUID | None = None
    environment_session_thread_id: UUID | None = None
    environment_session_attention_session_id: UUID | None = None
    thread_id: UUID | None = None
    thread_layout_id: UUID | None = None
    attention_session_id: UUID | None = None
    identity_session_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    root_object_id: UUID | None = None
    commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    graph_hash_post: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentSessionAttentionCommittedSnapshotProvider(Protocol):
    async def resolve_environment_session_attention_snapshot(
        self,
        *,
        request: ResolveEnvironmentSessionAttentionRequestSpec,
    ) -> EnvironmentSessionAttentionCommittedSnapshot | Mapping[str, object] | None:
        ...


class EnvironmentSessionAttentionNavigationContextViewProvider(Protocol):
    async def resolve_environment_navigation_context_view(
        self,
        *,
        request: ResolveEnvironmentSessionAttentionRequestSpec,
    ) -> EnvironmentNavigationContextViewSpec | Mapping[str, object] | None:
        ...


class EnvironmentSessionAttentionNavigationContextSnapshotProvider:
    """Adapt committed EnvironmentNavigationContext views into snapshots."""

    def __init__(
        self,
        *,
        context_provider: EnvironmentSessionAttentionNavigationContextViewProvider,
    ) -> None:
        self._context_provider = context_provider

    async def resolve_environment_session_attention_snapshot(
        self,
        *,
        request: ResolveEnvironmentSessionAttentionRequestSpec,
    ) -> EnvironmentSessionAttentionCommittedSnapshot | None:
        context_payload = (
            await self._context_provider.resolve_environment_navigation_context_view(
                request=request,
            )
        )
        if context_payload is None:
            return None
        return committed_snapshot_from_navigation_context_view(
            _navigation_context_view(context_payload)
        )


class CommittedEnvironmentSessionAttentionBackend:
    """Resolve Environment session attention from committed Environment state."""

    def __init__(
        self,
        *,
        snapshot_provider: EnvironmentSessionAttentionCommittedSnapshotProvider,
    ) -> None:
        self._snapshot_provider = snapshot_provider

    async def resolve_environment_session_attention(
        self,
        *,
        request: ResolveEnvironmentSessionAttentionRequestSpec,
    ) -> EnvironmentSessionAttentionResolutionSpec | None:
        snapshot_payload = (
            await self._snapshot_provider.resolve_environment_session_attention_snapshot(
                request=request,
            )
        )
        if snapshot_payload is None:
            return None
        snapshot = _snapshot(snapshot_payload)
        blockers = _snapshot_blockers(snapshot, request=request)
        status = "blocked" if blockers else "resolved"
        return EnvironmentSessionAttentionResolutionSpec(
            environment_session_id=snapshot.environment_session_id,
            environment_navigation_context_id=(
                snapshot.environment_navigation_context_id
            ),
            environment_session_thread_id=snapshot.environment_session_thread_id,
            environment_session_attention_session_id=(
                snapshot.environment_session_attention_session_id
            ),
            environment_id=snapshot.environment_id,
            environment_profile_id=snapshot.environment_profile_id,
            thread_id=snapshot.thread_id,
            thread_layout_id=snapshot.thread_layout_id,
            attention_session_id=snapshot.attention_session_id,
            identity_session_id=snapshot.identity_session_id,
            status=status,
            blockers=blockers,
            evidence={
                **dict(snapshot.evidence),
                "source": "aware_environment_service.session_attention_backend",
                "committed_snapshot": True,
                "snapshot_branch_id": _uuid_text(snapshot.branch_id),
                "snapshot_projection_hash": snapshot.projection_hash,
                "snapshot_commit_id": _uuid_text(snapshot.commit_id),
                "snapshot_object_instance_graph_commit_id": _uuid_text(
                    snapshot.object_instance_graph_commit_id
                ),
                "snapshot_root_object_id": _uuid_text(snapshot.root_object_id),
                "snapshot_graph_hash_post": snapshot.graph_hash_post,
            },
        )


def committed_snapshot_from_navigation_context_view(
    context: EnvironmentNavigationContextViewSpec,
) -> EnvironmentSessionAttentionCommittedSnapshot:
    evidence = dict(context.evidence)
    return EnvironmentSessionAttentionCommittedSnapshot(
        environment_session_id=context.environment_session_id,
        environment_id=context.environment_id,
        environment_profile_id=_evidence_uuid(evidence, "environment_profile_id"),
        environment_navigation_context_id=context.environment_navigation_context_id,
        environment_session_thread_id=(
            _evidence_uuid(evidence, "environment_session_thread_id")
            or _evidence_uuid(evidence, "session_thread_id")
        ),
        environment_session_attention_session_id=(
            _evidence_uuid(evidence, "environment_session_attention_session_id")
            or _evidence_uuid(evidence, "session_attention_session_id")
        ),
        thread_id=context.selected_thread_id or _evidence_uuid(evidence, "thread_id"),
        thread_layout_id=_evidence_uuid(evidence, "thread_layout_id"),
        attention_session_id=_evidence_uuid(evidence, "attention_session_id"),
        identity_session_id=(
            _evidence_uuid(evidence, "identity_session_id")
            or _evidence_uuid(evidence, "attention_identity_session_id")
        ),
        branch_id=context.branch_id,
        projection_hash=context.projection_hash,
        root_object_id=context.root_object_id,
        commit_id=context.commit_id,
        object_instance_graph_commit_id=context.object_instance_graph_commit_id,
        graph_hash_post=context.graph_hash_post,
        evidence=evidence,
    )


def _snapshot(
    snapshot_payload: EnvironmentSessionAttentionCommittedSnapshot | Mapping[str, object],
) -> EnvironmentSessionAttentionCommittedSnapshot:
    if isinstance(snapshot_payload, EnvironmentSessionAttentionCommittedSnapshot):
        return snapshot_payload
    return EnvironmentSessionAttentionCommittedSnapshot.model_validate(
        dict(snapshot_payload)
    )


def _navigation_context_view(
    context_payload: EnvironmentNavigationContextViewSpec | Mapping[str, object],
) -> EnvironmentNavigationContextViewSpec:
    if isinstance(context_payload, EnvironmentNavigationContextViewSpec):
        return context_payload
    return EnvironmentNavigationContextViewSpec.model_validate(dict(context_payload))


def _snapshot_blockers(
    snapshot: EnvironmentSessionAttentionCommittedSnapshot,
    *,
    request: ResolveEnvironmentSessionAttentionRequestSpec,
) -> list[str]:
    blockers: list[str] = []
    if request.branch_id is not None:
        if snapshot.branch_id is None:
            blockers.append("environment_session_attention_branch_missing")
        elif snapshot.branch_id != request.branch_id:
            blockers.append("environment_session_attention_branch_mismatch")
    if request.projection_hash is not None:
        if snapshot.projection_hash is None:
            blockers.append("environment_session_attention_projection_hash_missing")
        elif snapshot.projection_hash != request.projection_hash:
            blockers.append("environment_session_attention_projection_hash_mismatch")
    if snapshot.commit_id is None:
        blockers.append("environment_session_attention_commit_missing")
    if snapshot.object_instance_graph_commit_id is None:
        blockers.append(
            "environment_session_attention_object_instance_graph_commit_missing"
        )
    if snapshot.environment_session_thread_id is None:
        blockers.append("environment_session_thread_missing")
    if snapshot.thread_id is None:
        blockers.append("environment_session_thread_thread_missing")
    if snapshot.thread_layout_id is None:
        blockers.append("environment_session_thread_layout_missing")
    if snapshot.environment_session_attention_session_id is None:
        blockers.append("environment_session_attention_session_missing")
    if snapshot.attention_session_id is None:
        blockers.append("attention_session_missing")
    return list(dict.fromkeys(blockers))


def _evidence_uuid(evidence: Mapping[str, object], key: str) -> UUID | None:
    value = evidence.get(key)
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


__all__ = [
    "CommittedEnvironmentSessionAttentionBackend",
    "EnvironmentSessionAttentionCommittedSnapshot",
    "EnvironmentSessionAttentionCommittedSnapshotProvider",
    "EnvironmentSessionAttentionNavigationContextSnapshotProvider",
    "EnvironmentSessionAttentionNavigationContextViewProvider",
    "committed_snapshot_from_navigation_context_view",
]
