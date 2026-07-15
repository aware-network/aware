from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Literal, Protocol
from uuid import UUID

ExperienceFeatureLeaseDesiredState = Literal["enabled", "disabled"]
ExperienceFeatureWorkerStatus = Literal[
    "running",
    "completed",
    "failed",
    "released",
]
ExperienceSupervisorStatus = Literal["running", "degraded"]


@dataclass(frozen=True, slots=True)
class ExperienceSessionScope:
    experience_name: str
    profile_key: str | None = None
    environment_id: UUID | None = None
    environment_session_id: UUID | None = None
    actor_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    workspace_session_id: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceSessionFeatureLease:
    lease_key: str
    session_scope: ExperienceSessionScope
    feature_key: str
    desired_state: ExperienceFeatureLeaseDesiredState = "enabled"
    config: Mapping[str, Any] = field(default_factory=dict)
    revision: int = 1


@dataclass(frozen=True, slots=True)
class ExperienceSessionFeatureRunResult:
    status: Literal["completed", "failed"]
    info: str | None = None
    last_error: str | None = None
    health: object | None = None


@dataclass(frozen=True, slots=True)
class ExperienceFeatureLeaseSnapshot:
    lease_key: str
    session_scope: ExperienceSessionScope
    feature_key: str
    desired_state: ExperienceFeatureLeaseDesiredState
    worker_status: ExperienceFeatureWorkerStatus
    revision: int
    info: str | None = None
    last_error: str | None = None
    health: object | None = None


@dataclass(frozen=True, slots=True)
class ExperienceSessionSnapshot:
    session_scope: ExperienceSessionScope
    feature_lease_count: int
    leases: tuple[ExperienceFeatureLeaseSnapshot, ...]


@dataclass(frozen=True, slots=True)
class ExperienceSupervisorSnapshot:
    status: ExperienceSupervisorStatus
    session_count: int
    feature_lease_count: int
    sessions: tuple[ExperienceSessionSnapshot, ...]


class ExperienceSessionFeatureAdapter(Protocol):
    feature_key: str

    async def run(
        self,
        lease: ExperienceSessionFeatureLease,
    ) -> ExperienceSessionFeatureRunResult: ...

    async def release(self, lease: ExperienceSessionFeatureLease) -> None: ...


@dataclass(slots=True)
class _LeaseRecord:
    lease: ExperienceSessionFeatureLease
    adapter: ExperienceSessionFeatureAdapter
    task: asyncio.Task[ExperienceSessionFeatureRunResult] | None
    snapshot: ExperienceFeatureLeaseSnapshot


class ExperienceSupervisorManager:
    def __init__(
        self,
        *,
        feature_adapters: Mapping[str, ExperienceSessionFeatureAdapter],
    ) -> None:
        self._feature_adapters = dict(feature_adapters)
        self._records: dict[str, _LeaseRecord] = {}
        self._lock = asyncio.Lock()
        self._revision = 0

    async def ensure_feature(
        self,
        *,
        session_scope: ExperienceSessionScope,
        feature_key: str,
        config: Mapping[str, Any] | None = None,
        lease_key: str | None = None,
    ) -> ExperienceFeatureLeaseSnapshot:
        adapter = self._require_adapter(feature_key)
        resolved_lease_key = lease_key or build_experience_session_feature_lease_key(
            session_scope=session_scope,
            feature_key=feature_key,
        )
        async with self._lock:
            self._collect_completed_locked()
            existing = self._records.get(resolved_lease_key)
            if existing is not None and existing.snapshot.desired_state == "enabled":
                return existing.snapshot

            self._revision += 1
            lease = ExperienceSessionFeatureLease(
                lease_key=resolved_lease_key,
                session_scope=session_scope,
                feature_key=feature_key,
                desired_state="enabled",
                config=dict(config or {}),
                revision=self._revision,
            )
            task = asyncio.create_task(adapter.run(lease))
            snapshot = ExperienceFeatureLeaseSnapshot(
                lease_key=lease.lease_key,
                session_scope=lease.session_scope,
                feature_key=lease.feature_key,
                desired_state="enabled",
                worker_status="running",
                revision=lease.revision,
                info="Experience session feature lease enabled.",
            )
            self._records[lease.lease_key] = _LeaseRecord(
                lease=lease,
                adapter=adapter,
                task=task,
                snapshot=snapshot,
            )
            return snapshot

    async def release_feature(
        self,
        *,
        session_scope: ExperienceSessionScope,
        feature_key: str,
        lease_key: str | None = None,
    ) -> ExperienceFeatureLeaseSnapshot | None:
        resolved_lease_key = lease_key or build_experience_session_feature_lease_key(
            session_scope=session_scope,
            feature_key=feature_key,
        )
        async with self._lock:
            self._collect_completed_locked()
            record = self._records.get(resolved_lease_key)
            if record is None:
                return None
            lease = record.lease

        await record.adapter.release(lease)
        if record.task is not None and not record.task.done():
            record.task.cancel()

        async with self._lock:
            self._revision += 1
            current = self._records.get(resolved_lease_key)
            if current is None:
                return None
            disabled_lease = replace(
                current.lease,
                desired_state="disabled",
                revision=self._revision,
            )
            snapshot = ExperienceFeatureLeaseSnapshot(
                lease_key=current.lease.lease_key,
                session_scope=current.lease.session_scope,
                feature_key=current.lease.feature_key,
                desired_state="disabled",
                worker_status="released",
                revision=self._revision,
                info="Experience session feature lease released.",
                health=current.snapshot.health,
            )
            current.lease = disabled_lease
            current.snapshot = snapshot
            return snapshot

    async def get_feature_snapshot(
        self,
        *,
        session_scope: ExperienceSessionScope,
        feature_key: str,
        lease_key: str | None = None,
    ) -> ExperienceFeatureLeaseSnapshot | None:
        resolved_lease_key = lease_key or build_experience_session_feature_lease_key(
            session_scope=session_scope,
            feature_key=feature_key,
        )
        async with self._lock:
            self._collect_completed_locked()
            record = self._records.get(resolved_lease_key)
            return record.snapshot if record is not None else None

    async def get_session_snapshot(
        self,
        *,
        session_scope: ExperienceSessionScope,
    ) -> ExperienceSessionSnapshot:
        async with self._lock:
            self._collect_completed_locked()
            leases = _sort_lease_snapshots(
                record.snapshot
                for record in self._records.values()
                if record.lease.session_scope == session_scope
            )
        return ExperienceSessionSnapshot(
            session_scope=session_scope,
            feature_lease_count=len(leases),
            leases=leases,
        )

    async def get_snapshot(self) -> ExperienceSupervisorSnapshot:
        async with self._lock:
            self._collect_completed_locked()
            by_scope: dict[
                ExperienceSessionScope,
                list[ExperienceFeatureLeaseSnapshot],
            ] = {}
            for record in self._records.values():
                by_scope.setdefault(record.lease.session_scope, []).append(
                    record.snapshot,
                )
            sessions = tuple(
                ExperienceSessionSnapshot(
                    session_scope=scope,
                    feature_lease_count=len(leases),
                    leases=_sort_lease_snapshots(leases),
                )
                for scope, leases in sorted(
                    by_scope.items(),
                    key=lambda item: _scope_sort_key(item[0]),
                )
            )
            feature_lease_count = sum(
                session.feature_lease_count for session in sessions
            )
            status: ExperienceSupervisorStatus = (
                "degraded"
                if any(
                    lease.worker_status == "failed"
                    for session in sessions
                    for lease in session.leases
                )
                else "running"
            )
        return ExperienceSupervisorSnapshot(
            status=status,
            session_count=len(sessions),
            feature_lease_count=feature_lease_count,
            sessions=sessions,
        )

    def _require_adapter(self, feature_key: str) -> ExperienceSessionFeatureAdapter:
        adapter = self._feature_adapters.get(feature_key)
        if adapter is None:
            raise ValueError(f"Unknown Experience supervisor feature: {feature_key}")
        return adapter

    def _collect_completed_locked(self) -> None:
        for record in self._records.values():
            task = record.task
            if task is None or not task.done():
                continue
            if record.snapshot.desired_state == "disabled":
                continue
            try:
                result = task.result()
            except asyncio.CancelledError:
                result = ExperienceSessionFeatureRunResult(
                    status="completed",
                    info="Experience session feature worker was cancelled.",
                )
            except Exception as exc:
                result = ExperienceSessionFeatureRunResult(
                    status="failed",
                    last_error=str(exc),
                    info="Experience session feature worker failed.",
                )
            record.snapshot = ExperienceFeatureLeaseSnapshot(
                lease_key=record.lease.lease_key,
                session_scope=record.lease.session_scope,
                feature_key=record.lease.feature_key,
                desired_state=record.lease.desired_state,
                worker_status=result.status,
                revision=record.lease.revision,
                info=result.info,
                last_error=result.last_error,
                health=result.health,
            )


def build_experience_session_feature_lease_key(
    *,
    session_scope: ExperienceSessionScope,
    feature_key: str,
) -> str:
    scope_parts = (
        session_scope.experience_name,
        session_scope.profile_key,
        session_scope.environment_id,
        session_scope.environment_session_id,
        session_scope.actor_id,
        session_scope.process_id,
        session_scope.thread_id,
        session_scope.branch_id,
        session_scope.projection_hash,
        session_scope.workspace_session_id,
    )
    normalized_scope = ":".join(
        str(part) if part is not None else "-" for part in scope_parts
    )
    return f"{feature_key}:{normalized_scope}"


def _sort_lease_snapshots(
    leases: Any,
) -> tuple[ExperienceFeatureLeaseSnapshot, ...]:
    return tuple(sorted(leases, key=lambda lease: lease.lease_key))


def _scope_sort_key(scope: ExperienceSessionScope) -> tuple[str, ...]:
    return tuple(
        str(part) if part is not None else ""
        for part in (
            scope.experience_name,
            scope.profile_key,
            scope.environment_id,
            scope.environment_session_id,
            scope.actor_id,
            scope.process_id,
            scope.thread_id,
            scope.branch_id,
            scope.projection_hash,
            scope.workspace_session_id,
        )
    )


__all__ = [
    "ExperienceFeatureLeaseDesiredState",
    "ExperienceFeatureLeaseSnapshot",
    "ExperienceFeatureWorkerStatus",
    "ExperienceSessionFeatureAdapter",
    "ExperienceSessionFeatureLease",
    "ExperienceSessionFeatureRunResult",
    "ExperienceSessionScope",
    "ExperienceSessionSnapshot",
    "ExperienceSupervisorManager",
    "ExperienceSupervisorSnapshot",
    "ExperienceSupervisorStatus",
    "build_experience_session_feature_lease_key",
]
