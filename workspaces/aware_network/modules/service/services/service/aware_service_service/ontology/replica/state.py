from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from time import time
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_orm.db.boot import ensure_db_schema_installed_multi


DEFAULT_SERVICE_ONTOLOGY_REPLICA_PROJECTOR_ID = (
    "aware_service_service.ontology_replica.receipt_index.v1"
)
SERVICE_LOCAL_STATE_OCG_MIGRATION_CONSUMER_KEY = "aware_service_service.local_state"
SERVICE_LOCAL_STATE_OCG_MIGRATION_CONSUMER_KIND = "service_local_state"

_OCG_MIGRATION_ARTIFACT_CONTRACT_VERSION = "aware.meta.ocg_migration_artifacts.v0"
_OCG_MIGRATION_ARTIFACT_FAMILY = "ocg_migration"
_OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY = "aware_meta"
_OCG_MIGRATION_ARTIFACT_PRODUCER_KEY = "aware_meta.ocg_migration_artifacts.v0"
_OCG_MIGRATION_DIGEST_ALGORITHM = "sha256"
_OCG_MIGRATION_ROLE_LANE_INDEX = "lane_index"
_OCG_MIGRATION_ROLE_DIALECT_MIGRATION = "dialect_migration"
_OCG_MIGRATION_ROLES = frozenset(
    {
        _OCG_MIGRATION_ROLE_LANE_INDEX,
        "ocg_delta",
        _OCG_MIGRATION_ROLE_DIALECT_MIGRATION,
        "baseline_schema",
    }
)
_OCG_MIGRATION_SUPPORTED_DIALECT = "sqlite"

_REPLICA_TABLES = {
    "service_ontology_ocg_migration_marker",
    "service_ontology_replica_apply_receipt",
    "service_ontology_replica_commit_receipt",
    "service_ontology_replica_cursor",
    "service_ontology_replica_subscription",
}


@dataclass(frozen=True, slots=True)
class ServiceOntologyReplicaSubscriptionSpec:
    branch_id: UUID
    projection_hash: str
    service_package_id: UUID | None = None
    service_name: str | None = None
    source_api_projection_id: UUID | None = None
    api_graph_projection_id: UUID | None = None
    replica_role: str = "ontology_replica"


@dataclass(frozen=True, slots=True)
class ServiceOntologyReplicaApplyOutcome:
    subscription_id: UUID
    commit_receipt_id: UUID
    apply_receipt_id: UUID
    commit_id: UUID
    duplicate: bool
    status: str


@dataclass(frozen=True, slots=True)
class ServiceOntologyReplicaCommitReceipt:
    actor_id: UUID
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    object_instance_graph_commit_id: UUID | None = None
    graph_hash_post: str | None = None
    object_instance_graph_id: UUID | None = None
    root_object_id: UUID | None = None
    head_version: int | None = None
    created_at_unix_ms: int | None = None
    operation_label: str | None = None
    call_target: object | None = None
    function_id: UUID | None = None
    object_id: UUID | None = None
    class_instance_identity_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ServiceOntologyOcgMigrationMarkerState:
    service_package_name: str
    service_local_state_db_path: Path
    package_key: str
    object_config_graph_id: str
    branch_id: str
    projection_hash: str
    ocg_head_commit_id: str
    marker_identity: str | None = None
    consumer_key: str = SERVICE_LOCAL_STATE_OCG_MIGRATION_CONSUMER_KEY
    consumer_kind: str = SERVICE_LOCAL_STATE_OCG_MIGRATION_CONSUMER_KIND
    artifact_contract_version: str = _OCG_MIGRATION_ARTIFACT_CONTRACT_VERSION
    object_config_graph_package_id: str | None = None
    source_object_instance_graph_id: str | None = None
    graph_hash_post: str | None = None
    applied_artifact_digest: str | None = None
    digest_algorithm: str | None = _OCG_MIGRATION_DIGEST_ALGORITHM
    status: str = "current"
    blocker_reason: str | None = None
    artifact_key: str | None = None
    manifest_path: str | None = None
    workspace_relative_path: str | None = None
    attempted_commit_ids: tuple[str, ...] = ()
    applied_commit_ids: tuple[str, ...] = ()
    receipt: Mapping[str, object] | None = None
    evidence: Mapping[str, object] | None = None
    applied_at_unix_ms: int | None = None
    updated_at_unix_ms: int | None = None


@dataclass(frozen=True, slots=True)
class ServiceOntologyOcgMigrationApplyResult:
    status: str
    marker_count: int = 0
    applied_marker_count: int = 0
    blocked_marker_count: int = 0
    blockers: tuple[str, ...] = ()
    markers: tuple[ServiceOntologyOcgMigrationMarkerState, ...] = ()
    evidence: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class _OcgMigrationLaneIdentity:
    package_key: str
    object_config_graph_id: str
    branch_id: str
    projection_hash: str
    object_config_graph_package_id: str | None = None
    source_object_instance_graph_id: str | None = None


@dataclass(frozen=True, slots=True)
class _OcgMigrationArtifactRecord:
    artifact_key: str
    artifact_role: str
    digest: str
    workspace_relative_path: str
    manifest_path: str
    provider_payload: Mapping[str, object]
    file_payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _OcgMigrationArtifactIssue:
    reason: str
    artifact_key: str | None
    provider_payload: Mapping[str, object]
    artifact_payload: Mapping[str, object]


class ServiceOntologyReplicaStateStore:
    """ServiceHost-local receipt/cursor state for ontology replica workers."""

    def __init__(
        self,
        *,
        connection: sqlite3.Connection,
        db_path: Path,
        environment_id: UUID,
        schema_sql_root: Path,
        schema_hash: str,
    ) -> None:
        self._connection = connection
        self.db_path = db_path
        self.environment_id = environment_id
        self.schema_sql_root = schema_sql_root
        self.schema_hash = schema_hash

    @classmethod
    async def open(
        cls,
        *,
        db_path: Path,
        environment_id: UUID,
        schema_sql_root: Path | None = None,
    ) -> "ServiceOntologyReplicaStateStore":
        resolved_db_path = Path(db_path).expanduser().resolve()
        resolved_db_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_schema_root = (
            Path(schema_sql_root).expanduser().resolve()
            if schema_sql_root is not None
            else default_service_ontology_replica_sqlite_root()
        )
        schema_hash = _schema_hash(sql_root=resolved_schema_root)
        connection = sqlite3.connect(resolved_db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        await ensure_db_schema_installed_multi(
            connection=connection,
            sql_roots=(resolved_schema_root,),
            environment_id=environment_id,
            ocg_hash=schema_hash,
            ocg_head_commit_id=None,
            adapter="sqlite",
        )
        return cls(
            connection=connection,
            db_path=resolved_db_path,
            environment_id=environment_id,
            schema_sql_root=resolved_schema_root,
            schema_hash=schema_hash,
        )

    def close(self) -> None:
        self._connection.close()

    def ensure_subscription(
        self,
        *,
        spec: ServiceOntologyReplicaSubscriptionSpec,
    ) -> UUID:
        subscription_id = service_ontology_replica_subscription_id(spec=spec)
        with self._connection:
            self._connection.execute(
                """
INSERT INTO service_ontology_replica_subscription (
  id,
  service_package_id,
  service_name,
  branch_id,
  projection_hash,
  source_api_projection_id,
  api_graph_projection_id,
  replica_role,
  status,
  v
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
  service_package_id=excluded.service_package_id,
  service_name=excluded.service_name,
  source_api_projection_id=excluded.source_api_projection_id,
  api_graph_projection_id=excluded.api_graph_projection_id,
  replica_role=excluded.replica_role,
  status=excluded.status,
  v=excluded.v;
""".strip(),
                (
                    str(subscription_id),
                    _uuid_text(spec.service_package_id),
                    spec.service_name,
                    str(spec.branch_id),
                    _projection_hash(spec.projection_hash),
                    _uuid_text(spec.source_api_projection_id),
                    _uuid_text(spec.api_graph_projection_id),
                    spec.replica_role,
                    "active",
                    1,
                ),
            )
        return subscription_id

    def record_commit_receipt(
        self,
        *,
        subscription_id: UUID,
        receipt: ServiceOntologyReplicaCommitReceipt,
        parent_commit_id: UUID | None = None,
    ) -> UUID:
        commit_receipt_id = service_ontology_replica_commit_receipt_id(
            subscription_id=subscription_id,
            commit_id=receipt.commit_id,
        )
        parent_commit_receipt_id = (
            service_ontology_replica_commit_receipt_id(
                subscription_id=subscription_id,
                commit_id=parent_commit_id,
            )
            if parent_commit_id is not None
            else None
        )
        with self._connection:
            self._connection.execute(
                """
INSERT INTO service_ontology_replica_commit_receipt (
  id,
  subscription_id,
  parent_commit_receipt_id,
  branch_id,
  projection_hash,
  commit_id,
  object_instance_graph_commit_id,
  parent_commit_id,
  graph_hash_pre,
  graph_hash_post,
  object_instance_graph_id,
  root_object_id,
  head_version,
  created_at_unix_ms,
  operation_label,
  call_target,
  function_id,
  object_id,
  class_instance_identity_id,
  apply_status,
  error,
  v
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
  object_instance_graph_commit_id=excluded.object_instance_graph_commit_id,
  parent_commit_id=excluded.parent_commit_id,
  graph_hash_post=excluded.graph_hash_post,
  object_instance_graph_id=excluded.object_instance_graph_id,
  root_object_id=excluded.root_object_id,
  head_version=excluded.head_version,
  created_at_unix_ms=excluded.created_at_unix_ms,
  operation_label=excluded.operation_label,
  call_target=excluded.call_target,
  function_id=excluded.function_id,
  object_id=excluded.object_id,
  class_instance_identity_id=excluded.class_instance_identity_id,
  v=excluded.v;
""".strip(),
                (
                    str(commit_receipt_id),
                    str(subscription_id),
                    _uuid_text(parent_commit_receipt_id),
                    str(receipt.branch_id),
                    _projection_hash(receipt.projection_hash),
                    str(receipt.commit_id),
                    _uuid_text(receipt.object_instance_graph_commit_id),
                    _uuid_text(parent_commit_id),
                    None,
                    receipt.graph_hash_post,
                    _uuid_text(receipt.object_instance_graph_id),
                    _uuid_text(receipt.root_object_id),
                    receipt.head_version,
                    receipt.created_at_unix_ms,
                    receipt.operation_label,
                    _json_or_text(receipt.call_target),
                    _uuid_text(receipt.function_id),
                    _uuid_text(receipt.object_id),
                    _uuid_text(receipt.class_instance_identity_id),
                    "pending",
                    None,
                    1,
                ),
            )
        return commit_receipt_id

    def record_apply_success(
        self,
        *,
        subscription_id: UUID,
        commit_receipt_id: UUID,
        receipt: ServiceOntologyReplicaCommitReceipt,
        projector_id: str = DEFAULT_SERVICE_ONTOLOGY_REPLICA_PROJECTOR_ID,
        projector_version: str | None = None,
        schema_version: str | None = None,
        class_row_count: int = 0,
        association_row_count: int = 0,
        mutation_row_count: int = 0,
    ) -> ServiceOntologyReplicaApplyOutcome:
        apply_receipt_id = service_ontology_replica_apply_receipt_id(
            subscription_id=subscription_id,
            commit_id=receipt.commit_id,
            projector_id=projector_id,
        )
        duplicate = self._row_exists(
            table="service_ontology_replica_apply_receipt",
            row_id=apply_receipt_id,
        )
        now_ms = _unix_ms()
        with self._connection:
            if not duplicate:
                self._connection.execute(
                    """
INSERT INTO service_ontology_replica_apply_receipt (
  id,
  subscription_id,
  commit_receipt_id,
  branch_id,
  projection_hash,
  commit_id,
  projector_id,
  projector_version,
  schema_version,
  started_at_unix_ms,
  finished_at_unix_ms,
  class_row_count,
  association_row_count,
  mutation_row_count,
  idempotency_status,
  status,
  error,
  v
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""".strip(),
                    (
                        str(apply_receipt_id),
                        str(subscription_id),
                        str(commit_receipt_id),
                        str(receipt.branch_id),
                        _projection_hash(receipt.projection_hash),
                        str(receipt.commit_id),
                        projector_id,
                        projector_version,
                        schema_version,
                        now_ms,
                        now_ms,
                        class_row_count,
                        association_row_count,
                        mutation_row_count,
                        "applied",
                        "succeeded",
                        None,
                        1,
                    ),
                )
                self._connection.execute(
                    """
UPDATE service_ontology_replica_commit_receipt
SET apply_status = ?, error = NULL
WHERE id = ?;
""".strip(),
                    ("applied", str(commit_receipt_id)),
                )
            self._advance_cursor(
                subscription_id=subscription_id,
                commit_receipt_id=commit_receipt_id,
                receipt=receipt,
                projector_id=projector_id,
                observed_at_unix_ms=now_ms,
            )
        return ServiceOntologyReplicaApplyOutcome(
            subscription_id=subscription_id,
            commit_receipt_id=commit_receipt_id,
            apply_receipt_id=apply_receipt_id,
            commit_id=receipt.commit_id,
            duplicate=duplicate,
            status="duplicate" if duplicate else "applied",
        )

    def record_apply_failure(
        self,
        *,
        subscription_id: UUID,
        commit_receipt_id: UUID,
        receipt: ServiceOntologyReplicaCommitReceipt,
        error: str,
        projector_id: str = DEFAULT_SERVICE_ONTOLOGY_REPLICA_PROJECTOR_ID,
        projector_version: str | None = None,
        schema_version: str | None = None,
    ) -> ServiceOntologyReplicaApplyOutcome:
        apply_receipt_id = service_ontology_replica_apply_receipt_id(
            subscription_id=subscription_id,
            commit_id=receipt.commit_id,
            projector_id=projector_id,
        )
        now_ms = _unix_ms()
        error_text = str(error or "projection_apply_failed")
        with self._connection:
            self._connection.execute(
                """
INSERT INTO service_ontology_replica_apply_receipt (
  id,
  subscription_id,
  commit_receipt_id,
  branch_id,
  projection_hash,
  commit_id,
  projector_id,
  projector_version,
  schema_version,
  started_at_unix_ms,
  finished_at_unix_ms,
  class_row_count,
  association_row_count,
  mutation_row_count,
  idempotency_status,
  status,
  error,
  v
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
  finished_at_unix_ms=excluded.finished_at_unix_ms,
  idempotency_status=excluded.idempotency_status,
  status=excluded.status,
  error=excluded.error,
  v=excluded.v;
""".strip(),
                (
                    str(apply_receipt_id),
                    str(subscription_id),
                    str(commit_receipt_id),
                    str(receipt.branch_id),
                    _projection_hash(receipt.projection_hash),
                    str(receipt.commit_id),
                    projector_id,
                    projector_version,
                    schema_version,
                    now_ms,
                    now_ms,
                    0,
                    0,
                    0,
                    "failed",
                    "failed",
                    error_text,
                    1,
                ),
            )
            self._connection.execute(
                """
UPDATE service_ontology_replica_commit_receipt
SET apply_status = ?, error = ?
WHERE id = ?;
""".strip(),
                ("failed", error_text, str(commit_receipt_id)),
            )
        return ServiceOntologyReplicaApplyOutcome(
            subscription_id=subscription_id,
            commit_receipt_id=commit_receipt_id,
            apply_receipt_id=apply_receipt_id,
            commit_id=receipt.commit_id,
            duplicate=False,
            status="failed",
        )

    def fetch_cursor(
        self,
        *,
        subscription_id: UUID,
        projector_id: str = DEFAULT_SERVICE_ONTOLOGY_REPLICA_PROJECTOR_ID,
    ) -> dict[str, Any] | None:
        cursor_id = service_ontology_replica_cursor_id(
            subscription_id=subscription_id,
            projector_id=projector_id,
        )
        return self._fetch_row(
            table="service_ontology_replica_cursor",
            row_id=cursor_id,
        )

    def fetch_subscription(self, *, subscription_id: UUID) -> dict[str, Any] | None:
        return self._fetch_row(
            table="service_ontology_replica_subscription",
            row_id=subscription_id,
        )

    def fetch_commit_receipt(
        self,
        *,
        commit_receipt_id: UUID,
    ) -> dict[str, Any] | None:
        return self._fetch_row(
            table="service_ontology_replica_commit_receipt",
            row_id=commit_receipt_id,
        )

    def fetch_ocg_migration_marker(
        self,
        *,
        service_package_name: str,
        package_key: str,
        object_config_graph_id: str,
        branch_id: str,
        projection_hash: str,
        consumer_key: str = SERVICE_LOCAL_STATE_OCG_MIGRATION_CONSUMER_KEY,
    ) -> dict[str, Any] | None:
        cursor = self._connection.execute(
            """
SELECT *
FROM service_ontology_ocg_migration_marker
WHERE service_package_name = ?
  AND service_local_state_db_path = ?
  AND consumer_key = ?
  AND package_key = ?
  AND object_config_graph_id = ?
  AND branch_id = ?
  AND projection_hash = ?
LIMIT 1;
""".strip(),
            (
                service_package_name,
                self.db_path.as_posix(),
                consumer_key,
                package_key,
                object_config_graph_id,
                branch_id,
                projection_hash,
            ),
        )
        row = cursor.fetchone()
        return _decode_marker_row(row) if row is not None else None

    def apply_ocg_migration_artifacts(
        self,
        *,
        service_package_name: str,
        workspace_root: Path,
        artifacts: Iterable[object],
        now_unix_ms: int | None = None,
    ) -> ServiceOntologyOcgMigrationApplyResult:
        resolved_workspace_root = Path(workspace_root).expanduser().resolve()
        records, issues = _load_ocg_migration_artifact_records(
            workspace_root=resolved_workspace_root,
            artifacts=artifacts,
        )
        if not records and not issues:
            return ServiceOntologyOcgMigrationApplyResult(
                status="skipped",
                evidence={
                    "status": "skipped",
                    "reason": "no_service_local_state_ocg_migration_artifacts",
                    "artifact_count": 0,
                },
            )

        write_time = now_unix_ms or _unix_ms()
        written_markers: list[ServiceOntologyOcgMigrationMarkerState] = []
        blockers: list[str] = []
        for issue in issues:
            blockers.append(issue.reason)
            blocked = _blocked_marker_from_artifact_issue(
                store=self,
                service_package_name=service_package_name,
                issue=issue,
                now_unix_ms=write_time,
            )
            if blocked is None:
                continue
            self._write_ocg_migration_marker(blocked)
            written_markers.append(blocked)

        for group in _group_ocg_migration_artifact_records(records).values():
            marker, group_blockers = _ocg_migration_marker_from_artifact_group(
                store=self,
                service_package_name=service_package_name,
                group=group,
                now_unix_ms=write_time,
            )
            blockers.extend(group_blockers)
            if marker is None:
                continue
            self._write_ocg_migration_marker(marker)
            written_markers.append(marker)

        blocked_count = sum(
            1 for marker in written_markers if marker.status == "blocked"
        )
        applied_count = sum(
            1 for marker in written_markers if marker.status == "applied"
        )
        status = (
            "blocked"
            if blocked_count
            else (
                "applied"
                if applied_count
                else "current" if written_markers else "skipped"
            )
        )
        return ServiceOntologyOcgMigrationApplyResult(
            status=status,
            marker_count=len(written_markers),
            applied_marker_count=applied_count,
            blocked_marker_count=blocked_count,
            blockers=tuple(blockers),
            markers=tuple(written_markers),
            evidence={
                "status": status,
                "artifact_count": len(records) + len(issues),
                "valid_artifact_count": len(records),
                "invalid_artifact_count": len(issues),
                "marker_count": len(written_markers),
                "applied_marker_count": applied_count,
                "blocked_marker_count": blocked_count,
                "blockers": list(blockers),
                "markers": [
                    _ocg_migration_marker_evidence(marker) for marker in written_markers
                ],
            },
        )

    def count_rows(self, *, table: str) -> int:
        _validate_table(table)
        cursor = self._connection.execute(f"SELECT COUNT(*) FROM {table};")
        return int(cursor.fetchone()[0])

    def _advance_cursor(
        self,
        *,
        subscription_id: UUID,
        commit_receipt_id: UUID,
        receipt: ServiceOntologyReplicaCommitReceipt,
        projector_id: str,
        observed_at_unix_ms: int,
    ) -> None:
        cursor_id = service_ontology_replica_cursor_id(
            subscription_id=subscription_id,
            projector_id=projector_id,
        )
        self._connection.execute(
            """
INSERT INTO service_ontology_replica_cursor (
  id,
  subscription_id,
  head_commit_receipt_id,
  branch_id,
  projection_hash,
  projector_id,
  head_commit_id,
  graph_hash_post,
  head_version,
  last_applied_at_unix_ms,
  status,
  v
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
  head_commit_receipt_id=excluded.head_commit_receipt_id,
  head_commit_id=excluded.head_commit_id,
  graph_hash_post=excluded.graph_hash_post,
  head_version=excluded.head_version,
  last_applied_at_unix_ms=excluded.last_applied_at_unix_ms,
  status=excluded.status,
  v=excluded.v;
""".strip(),
            (
                str(cursor_id),
                str(subscription_id),
                str(commit_receipt_id),
                str(receipt.branch_id),
                _projection_hash(receipt.projection_hash),
                projector_id,
                str(receipt.commit_id),
                receipt.graph_hash_post,
                receipt.head_version,
                observed_at_unix_ms,
                "active",
                1,
            ),
        )

    def _row_exists(self, *, table: str, row_id: UUID) -> bool:
        return self._fetch_row(table=table, row_id=row_id) is not None

    def _write_ocg_migration_marker(
        self,
        marker: ServiceOntologyOcgMigrationMarkerState,
    ) -> None:
        marker_identity = marker.marker_identity or _ocg_migration_marker_identity(
            service_package_name=marker.service_package_name,
            service_local_state_db_path=marker.service_local_state_db_path,
            consumer_key=marker.consumer_key,
            package_key=marker.package_key,
            object_config_graph_id=marker.object_config_graph_id,
            branch_id=marker.branch_id,
            projection_hash=marker.projection_hash,
        )
        with self._connection:
            self._connection.execute(
                """
INSERT INTO service_ontology_ocg_migration_marker (
  id,
  marker_identity,
  service_package_name,
  service_local_state_db_path,
  consumer_key,
  consumer_kind,
  package_key,
  artifact_contract_version,
  object_config_graph_package_id,
  object_config_graph_id,
  source_object_instance_graph_id,
  branch_id,
  projection_hash,
  ocg_head_commit_id,
  graph_hash_post,
  applied_artifact_digest,
  digest_algorithm,
  status,
  blocker_reason,
  artifact_key,
  manifest_path,
  workspace_relative_path,
  attempted_commit_ids,
  applied_commit_ids,
  receipt,
  evidence,
  applied_at_unix_ms,
  updated_at_unix_ms,
  v
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(marker_identity) DO UPDATE SET
  ocg_head_commit_id=excluded.ocg_head_commit_id,
  graph_hash_post=excluded.graph_hash_post,
  applied_artifact_digest=excluded.applied_artifact_digest,
  digest_algorithm=excluded.digest_algorithm,
  status=excluded.status,
  blocker_reason=excluded.blocker_reason,
  artifact_key=excluded.artifact_key,
  manifest_path=excluded.manifest_path,
  workspace_relative_path=excluded.workspace_relative_path,
  attempted_commit_ids=excluded.attempted_commit_ids,
  applied_commit_ids=excluded.applied_commit_ids,
  receipt=excluded.receipt,
  evidence=excluded.evidence,
  applied_at_unix_ms=excluded.applied_at_unix_ms,
  updated_at_unix_ms=excluded.updated_at_unix_ms,
  v=excluded.v;
""".strip(),
                (
                    str(UUID(marker_identity)),
                    marker_identity,
                    marker.service_package_name,
                    marker.service_local_state_db_path.as_posix(),
                    marker.consumer_key,
                    marker.consumer_kind,
                    marker.package_key,
                    marker.artifact_contract_version,
                    marker.object_config_graph_package_id,
                    marker.object_config_graph_id,
                    marker.source_object_instance_graph_id,
                    marker.branch_id,
                    marker.projection_hash,
                    marker.ocg_head_commit_id,
                    marker.graph_hash_post,
                    marker.applied_artifact_digest,
                    marker.digest_algorithm,
                    marker.status,
                    marker.blocker_reason,
                    marker.artifact_key,
                    marker.manifest_path,
                    marker.workspace_relative_path,
                    _json_dump(list(marker.attempted_commit_ids)),
                    _json_dump(list(marker.applied_commit_ids)),
                    _json_dump(dict(marker.receipt or {})),
                    _json_dump(dict(marker.evidence or {})),
                    marker.applied_at_unix_ms,
                    marker.updated_at_unix_ms,
                    1,
                ),
            )

    def _fetch_row(self, *, table: str, row_id: UUID) -> dict[str, Any] | None:
        _validate_table(table)
        cursor = self._connection.execute(
            f"SELECT * FROM {table} WHERE id = ?;",
            (str(row_id),),
        )
        row = cursor.fetchone()
        return dict(row) if row is not None else None


def default_service_ontology_replica_sqlite_root() -> Path:
    return Path(__file__).resolve().parents[3] / "db" / "sqlite"


def service_ontology_replica_subscription_id(
    *,
    spec: ServiceOntologyReplicaSubscriptionSpec,
) -> UUID:
    return _stable_uuid(
        "subscription",
        _uuid_text(spec.service_package_id) or "unknown-package",
        spec.service_name or "unknown-service",
        str(spec.branch_id),
        _projection_hash(spec.projection_hash),
    )


def service_ontology_replica_commit_receipt_id(
    *,
    subscription_id: UUID,
    commit_id: UUID,
) -> UUID:
    return _stable_uuid("commit", str(subscription_id), str(commit_id))


def service_ontology_replica_apply_receipt_id(
    *,
    subscription_id: UUID,
    commit_id: UUID,
    projector_id: str,
) -> UUID:
    return _stable_uuid("apply", str(subscription_id), str(commit_id), projector_id)


def service_ontology_replica_cursor_id(
    *,
    subscription_id: UUID,
    projector_id: str,
) -> UUID:
    return _stable_uuid("cursor", str(subscription_id), projector_id)


def service_ontology_ocg_migration_marker_id(
    *,
    service_package_name: str,
    service_local_state_db_path: Path,
    consumer_key: str,
    package_key: str,
    object_config_graph_id: str,
    branch_id: str,
    projection_hash: str,
) -> UUID:
    return UUID(
        _ocg_migration_marker_identity(
            service_package_name=service_package_name,
            service_local_state_db_path=service_local_state_db_path,
            consumer_key=consumer_key,
            package_key=package_key,
            object_config_graph_id=object_config_graph_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
    )


def _ocg_migration_marker_identity(
    *,
    service_package_name: str,
    service_local_state_db_path: Path,
    consumer_key: str,
    package_key: str,
    object_config_graph_id: str,
    branch_id: str,
    projection_hash: str,
) -> str:
    return str(
        _stable_uuid(
            "ocg-migration-marker",
            service_package_name,
            service_local_state_db_path.expanduser().resolve().as_posix(),
            consumer_key,
            package_key,
            object_config_graph_id,
            branch_id,
            projection_hash,
        )
    )


def _schema_hash(*, sql_root: Path) -> str:
    contract_path = sql_root / "_aware" / "sqlite_orm_schema_contract.json"
    if not contract_path.is_file():
        raise RuntimeError(
            "Service ontology replica SQLite schema contract is missing: "
            f"{contract_path}"
        )
    return "sha256:" + sha256(contract_path.read_bytes()).hexdigest()


def _stable_uuid(*tokens: str) -> UUID:
    return uuid5(NAMESPACE_URL, "aware.service.ontology_replica:" + ":".join(tokens))


def _projection_hash(value: str) -> str:
    token = str(value or "").strip()
    if not token:
        raise ValueError("projection_hash must be non-empty")
    return token


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _json_or_text(value: object | None) -> str | None:
    if value is None:
        return None
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return json.dumps(
            model_dump(mode="json", exclude_none=True),
            sort_keys=True,
            separators=(",", ":"),
        )
    try:
        return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    except TypeError:
        return str(value)


def _unix_ms() -> int:
    return int(time() * 1000)


def _load_ocg_migration_artifact_records(
    *,
    workspace_root: Path,
    artifacts: Iterable[object],
) -> tuple[
    tuple[_OcgMigrationArtifactRecord, ...],
    tuple[_OcgMigrationArtifactIssue, ...],
]:
    records: list[_OcgMigrationArtifactRecord] = []
    issues: list[_OcgMigrationArtifactIssue] = []
    for artifact in artifacts:
        artifact_payload = _artifact_ref_payload(artifact)
        if not _is_service_local_state_ocg_migration_payload(artifact_payload):
            continue
        provider_payload = _json_object(artifact_payload.get("provider_payload"))
        artifact_key = _optional_text(artifact_payload.get("artifact_key"))
        issue = _validate_ocg_migration_artifact_ref_payload(artifact_payload)
        if issue is not None:
            issues.append(
                _OcgMigrationArtifactIssue(
                    reason=issue,
                    artifact_key=artifact_key,
                    provider_payload=provider_payload,
                    artifact_payload=artifact_payload,
                )
            )
            continue
        workspace_relative_path = str(
            _optional_text(artifact_payload.get("workspace_relative_path"))
        )
        target = _safe_workspace_relative_target(
            workspace_root=workspace_root,
            workspace_relative_path=workspace_relative_path,
        )
        if target is None:
            issues.append(
                _OcgMigrationArtifactIssue(
                    reason="ocg_migration_artifact_path_unsafe",
                    artifact_key=artifact_key,
                    provider_payload=provider_payload,
                    artifact_payload=artifact_payload,
                )
            )
            continue
        if not target.is_file():
            issues.append(
                _OcgMigrationArtifactIssue(
                    reason="ocg_migration_artifact_file_missing",
                    artifact_key=artifact_key,
                    provider_payload=provider_payload,
                    artifact_payload=artifact_payload,
                )
            )
            continue
        try:
            raw_file_payload = json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            issues.append(
                _OcgMigrationArtifactIssue(
                    reason="ocg_migration_artifact_json_unreadable",
                    artifact_key=artifact_key,
                    provider_payload=provider_payload,
                    artifact_payload=artifact_payload,
                )
            )
            continue
        if not isinstance(raw_file_payload, Mapping):
            issues.append(
                _OcgMigrationArtifactIssue(
                    reason="ocg_migration_artifact_json_not_object",
                    artifact_key=artifact_key,
                    provider_payload=provider_payload,
                    artifact_payload=artifact_payload,
                )
            )
            continue
        file_payload = _json_object(raw_file_payload)
        expected_digest = str(_normalize_sha256(artifact_payload.get("digest")))
        if _json_sha256(file_payload) != expected_digest:
            issues.append(
                _OcgMigrationArtifactIssue(
                    reason="ocg_migration_artifact_digest_mismatch",
                    artifact_key=artifact_key,
                    provider_payload=provider_payload,
                    artifact_payload=artifact_payload,
                )
            )
            continue
        mismatch = _first_ocg_migration_identity_mismatch(
            provider_payload=provider_payload,
            file_payload=file_payload,
        )
        if mismatch is not None:
            issues.append(
                _OcgMigrationArtifactIssue(
                    reason=mismatch,
                    artifact_key=artifact_key,
                    provider_payload=provider_payload,
                    artifact_payload=artifact_payload,
                )
            )
            continue
        records.append(
            _OcgMigrationArtifactRecord(
                artifact_key=str(artifact_key),
                artifact_role=str(
                    _optional_text(artifact_payload.get("artifact_role"))
                ),
                digest=expected_digest,
                workspace_relative_path=workspace_relative_path,
                manifest_path=str(
                    _optional_text(artifact_payload.get("manifest_path"))
                ),
                provider_payload=provider_payload,
                file_payload=file_payload,
            )
        )
    return tuple(records), tuple(issues)


def _validate_ocg_migration_artifact_ref_payload(
    payload: Mapping[str, object],
) -> str | None:
    if _optional_text(payload.get("producer_provider_key")) != (
        _OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY
    ):
        return "ocg_migration_producer_provider_key_mismatch"
    if (
        _optional_text(payload.get("producer_key"))
        != _OCG_MIGRATION_ARTIFACT_PRODUCER_KEY
    ):
        return "ocg_migration_producer_key_mismatch"
    role = _optional_text(payload.get("artifact_role"))
    if role not in _OCG_MIGRATION_ROLES:
        return "ocg_migration_artifact_role_unsupported"
    if _optional_text(payload.get("artifact_key")) is None:
        return "ocg_migration_artifact_key_missing"
    if _normalize_sha256(payload.get("digest")) is None:
        return "ocg_migration_artifact_digest_missing"
    if _optional_text(payload.get("digest_algorithm")) != (
        _OCG_MIGRATION_DIGEST_ALGORITHM
    ):
        return "ocg_migration_artifact_digest_algorithm_unsupported"
    if _optional_text(payload.get("workspace_relative_path")) is None:
        return "ocg_migration_workspace_relative_path_missing"
    if _optional_text(payload.get("manifest_path")) is None:
        return "ocg_migration_manifest_path_missing"
    if _optional_text(payload.get("runtime_contract_version")) != (
        _OCG_MIGRATION_ARTIFACT_CONTRACT_VERSION
    ):
        return "ocg_migration_runtime_contract_version_mismatch"
    provider_payload = _json_object(payload.get("provider_payload"))
    if _ocg_migration_lane_identity_from_payload(provider_payload) is None:
        return "ocg_migration_provider_payload_identity_missing"
    if _optional_text(provider_payload.get("head_commit_id")) is None:
        return "ocg_migration_provider_payload_head_missing"
    return None


def _group_ocg_migration_artifact_records(
    records: Iterable[_OcgMigrationArtifactRecord],
) -> dict[tuple[str, str, str, str], tuple[_OcgMigrationArtifactRecord, ...]]:
    grouped: dict[tuple[str, str, str, str], list[_OcgMigrationArtifactRecord]] = {}
    for record in records:
        identity = _ocg_migration_lane_identity_from_payload(record.provider_payload)
        if identity is None:
            continue
        key = (
            identity.package_key,
            identity.object_config_graph_id,
            identity.branch_id,
            identity.projection_hash,
        )
        grouped.setdefault(key, []).append(record)
    return {key: tuple(items) for key, items in grouped.items()}


def _ocg_migration_marker_from_artifact_group(
    *,
    store: ServiceOntologyReplicaStateStore,
    service_package_name: str,
    group: tuple[_OcgMigrationArtifactRecord, ...],
    now_unix_ms: int,
) -> tuple[ServiceOntologyOcgMigrationMarkerState | None, tuple[str, ...]]:
    identity = _ocg_migration_lane_identity_from_payload(group[0].provider_payload)
    if identity is None:
        return None, ("ocg_migration_group_identity_missing",)
    lane_records = [
        record
        for record in group
        if record.artifact_role == _OCG_MIGRATION_ROLE_LANE_INDEX
    ]
    if len(lane_records) != 1:
        return (
            _blocked_marker_from_identity(
                store=store,
                service_package_name=service_package_name,
                identity=identity,
                blocker_reason="ocg_migration_lane_index_missing_or_ambiguous",
                attempted_commit_ids=(),
                artifact_key=None,
                now_unix_ms=now_unix_ms,
            ),
            ("ocg_migration_lane_index_missing_or_ambiguous",),
        )
    lane_record = lane_records[0]
    lane_payload = lane_record.file_payload
    head_commit_id = _optional_text(lane_payload.get("head_commit_id"))
    if head_commit_id is None:
        return (
            _blocked_marker_from_identity(
                store=store,
                service_package_name=service_package_name,
                identity=identity,
                blocker_reason="ocg_migration_lane_head_missing",
                attempted_commit_ids=(),
                artifact_key=lane_record.artifact_key,
                now_unix_ms=now_unix_ms,
            ),
            ("ocg_migration_lane_head_missing",),
        )
    commit_entries = _ocg_migration_lane_commit_entries(lane_payload.get("commits"))
    commit_ids = tuple(entry["commit_id"] for entry in commit_entries)
    if head_commit_id not in commit_ids:
        return (
            _blocked_marker_from_identity(
                store=store,
                service_package_name=service_package_name,
                identity=identity,
                blocker_reason="ocg_migration_lane_head_not_in_commits",
                attempted_commit_ids=commit_ids or (head_commit_id,),
                artifact_key=lane_record.artifact_key,
                now_unix_ms=now_unix_ms,
            ),
            ("ocg_migration_lane_head_not_in_commits",),
        )

    existing = store.fetch_ocg_migration_marker(
        service_package_name=service_package_name,
        package_key=identity.package_key,
        object_config_graph_id=identity.object_config_graph_id,
        branch_id=identity.branch_id,
        projection_hash=identity.projection_hash,
    )
    existing_head = (
        None if existing is None else _optional_text(existing.get("ocg_head_commit_id"))
    )
    if existing_head is not None and existing_head not in commit_ids:
        return (
            _blocked_marker_from_identity(
                store=store,
                service_package_name=service_package_name,
                identity=identity,
                blocker_reason="ocg_migration_marker_head_not_in_lane",
                attempted_commit_ids=commit_ids,
                artifact_key=lane_record.artifact_key,
                now_unix_ms=now_unix_ms,
            ),
            ("ocg_migration_marker_head_not_in_lane",),
        )

    if existing_head is not None:
        pending_entries = commit_entries[commit_ids.index(existing_head) + 1 :]
    else:
        pending_entries = commit_entries
    dialects_by_commit = _ocg_migration_dialect_records_by_commit(group)
    blockers: list[str] = []
    unsupported_entry: Mapping[str, str] | None = None
    for entry in pending_entries:
        commit_id = entry["commit_id"]
        dialect_record = dialects_by_commit.get(commit_id)
        if dialect_record is None:
            blockers.append("ocg_migration_sqlite_dialect_artifact_missing")
            unsupported_entry = entry
            break
        dialect_payload = dialect_record.file_payload
        if _optional_text(dialect_payload.get("dialect")) != (
            _OCG_MIGRATION_SUPPORTED_DIALECT
        ):
            blockers.append("ocg_migration_dialect_unsupported")
            unsupported_entry = entry
            break
        migration_kind = _optional_text(dialect_payload.get("migration_kind"))
        if migration_kind != "noop":
            reason = (
                _optional_text(dialect_payload.get("unsupported_reason"))
                or f"ocg_migration_kind_unsupported:{migration_kind}"
            )
            blockers.append(reason)
            unsupported_entry = entry
            break
    if blockers:
        fallback_head = (
            existing_head
            or _optional_text(
                None
                if unsupported_entry is None
                else unsupported_entry.get("parent_commit_id")
            )
            or head_commit_id
        )
        return (
            _blocked_marker_from_identity(
                store=store,
                service_package_name=service_package_name,
                identity=identity,
                blocker_reason=blockers[0],
                attempted_commit_ids=commit_ids,
                artifact_key=lane_record.artifact_key,
                now_unix_ms=now_unix_ms,
                fallback_head_commit_id=fallback_head,
            ),
            tuple(blockers),
        )

    applied_commit_ids = tuple(entry["commit_id"] for entry in pending_entries)
    graph_hash_post = _optional_text(lane_payload.get("head_graph_hash_post"))
    if graph_hash_post is None:
        head_entry = next(
            entry for entry in commit_entries if entry["commit_id"] == head_commit_id
        )
        graph_hash_post = _optional_text(head_entry.get("graph_hash_post"))
    status = "applied" if existing is not None and applied_commit_ids else "current"
    marker = ServiceOntologyOcgMigrationMarkerState(
        service_package_name=service_package_name,
        service_local_state_db_path=store.db_path,
        package_key=identity.package_key,
        object_config_graph_package_id=identity.object_config_graph_package_id,
        object_config_graph_id=identity.object_config_graph_id,
        source_object_instance_graph_id=identity.source_object_instance_graph_id,
        branch_id=identity.branch_id,
        projection_hash=identity.projection_hash,
        ocg_head_commit_id=head_commit_id,
        graph_hash_post=graph_hash_post,
        applied_artifact_digest=lane_record.digest,
        status=status,
        artifact_key=lane_record.artifact_key,
        manifest_path=lane_record.manifest_path,
        workspace_relative_path=lane_record.workspace_relative_path,
        attempted_commit_ids=commit_ids,
        applied_commit_ids=applied_commit_ids,
        receipt={"lane_index": dict(lane_payload)},
        evidence={
            "source": "aware_service_service.local_state.ocg_migration",
            "policy": "noop_only_v0",
            "pending_commit_count": len(pending_entries),
            "applied_commit_count": len(applied_commit_ids),
            "existing_head_commit_id": existing_head,
        },
        applied_at_unix_ms=now_unix_ms if applied_commit_ids else None,
        updated_at_unix_ms=now_unix_ms,
    )
    return marker, ()


def _blocked_marker_from_artifact_issue(
    *,
    store: ServiceOntologyReplicaStateStore,
    service_package_name: str,
    issue: _OcgMigrationArtifactIssue,
    now_unix_ms: int,
) -> ServiceOntologyOcgMigrationMarkerState | None:
    identity = _ocg_migration_lane_identity_from_payload(issue.provider_payload)
    if identity is None:
        return None
    head_commit_id = (
        _optional_text(issue.provider_payload.get("head_commit_id"))
        or _optional_text(issue.provider_payload.get("commit_id"))
        or "."
    )
    return _blocked_marker_from_identity(
        store=store,
        service_package_name=service_package_name,
        identity=identity,
        blocker_reason=issue.reason,
        attempted_commit_ids=(head_commit_id,),
        artifact_key=issue.artifact_key,
        now_unix_ms=now_unix_ms,
        fallback_head_commit_id=head_commit_id,
    )


def _blocked_marker_from_identity(
    *,
    store: ServiceOntologyReplicaStateStore,
    service_package_name: str,
    identity: _OcgMigrationLaneIdentity,
    blocker_reason: str,
    attempted_commit_ids: tuple[str, ...],
    artifact_key: str | None,
    now_unix_ms: int,
    fallback_head_commit_id: str | None = None,
) -> ServiceOntologyOcgMigrationMarkerState:
    existing = store.fetch_ocg_migration_marker(
        service_package_name=service_package_name,
        package_key=identity.package_key,
        object_config_graph_id=identity.object_config_graph_id,
        branch_id=identity.branch_id,
        projection_hash=identity.projection_hash,
    )
    existing_head = (
        None if existing is None else _optional_text(existing.get("ocg_head_commit_id"))
    )
    return ServiceOntologyOcgMigrationMarkerState(
        service_package_name=service_package_name,
        service_local_state_db_path=store.db_path,
        package_key=identity.package_key,
        object_config_graph_package_id=identity.object_config_graph_package_id,
        object_config_graph_id=identity.object_config_graph_id,
        source_object_instance_graph_id=identity.source_object_instance_graph_id,
        branch_id=identity.branch_id,
        projection_hash=identity.projection_hash,
        ocg_head_commit_id=existing_head or fallback_head_commit_id or ".",
        graph_hash_post=(
            None
            if existing is None
            else _optional_text(existing.get("graph_hash_post"))
        ),
        applied_artifact_digest=(
            None
            if existing is None
            else _optional_text(existing.get("applied_artifact_digest"))
        ),
        status="blocked",
        blocker_reason=blocker_reason,
        artifact_key=artifact_key,
        attempted_commit_ids=attempted_commit_ids,
        applied_commit_ids=(
            ()
            if existing is None
            else tuple(_json_array(existing.get("applied_commit_ids")))
        ),
        receipt={"blocked": True, "blocker_reason": blocker_reason},
        evidence={
            "source": "aware_service_service.local_state.ocg_migration",
            "policy": "noop_only_v0",
            "blocker_reason": blocker_reason,
            "existing_head_commit_id": existing_head,
        },
        updated_at_unix_ms=now_unix_ms,
    )


def _ocg_migration_lane_identity_from_payload(
    payload: Mapping[str, object],
) -> _OcgMigrationLaneIdentity | None:
    package_key = _optional_text(payload.get("package_key"))
    object_config_graph_id = _optional_text(payload.get("object_config_graph_id"))
    branch_id = _optional_text(payload.get("branch_id"))
    projection_hash = _optional_text(payload.get("projection_hash"))
    if (
        not package_key
        or not object_config_graph_id
        or not branch_id
        or not projection_hash
    ):
        return None
    return _OcgMigrationLaneIdentity(
        package_key=package_key,
        object_config_graph_package_id=_optional_text(
            payload.get("object_config_graph_package_id")
        ),
        object_config_graph_id=object_config_graph_id,
        source_object_instance_graph_id=_optional_text(
            payload.get("source_object_instance_graph_id")
        ),
        branch_id=branch_id,
        projection_hash=projection_hash,
    )


def _ocg_migration_lane_commit_entries(value: object) -> tuple[Mapping[str, str], ...]:
    if not isinstance(value, list):
        return ()
    entries: list[Mapping[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        commit_id = _optional_text(item.get("commit_id"))
        if commit_id is None:
            continue
        entries.append(
            {
                "commit_id": commit_id,
                "parent_commit_id": _optional_text(item.get("parent_commit_id")) or "",
                "graph_hash_post": _optional_text(item.get("graph_hash_post")) or "",
            }
        )
    return tuple(entries)


def _ocg_migration_dialect_records_by_commit(
    records: Iterable[_OcgMigrationArtifactRecord],
) -> dict[str, _OcgMigrationArtifactRecord]:
    result: dict[str, _OcgMigrationArtifactRecord] = {}
    for record in records:
        if record.artifact_role != _OCG_MIGRATION_ROLE_DIALECT_MIGRATION:
            continue
        commit_id = _optional_text(record.file_payload.get("commit_id"))
        if commit_id is not None:
            result[commit_id] = record
    return result


def _first_ocg_migration_identity_mismatch(
    *,
    provider_payload: Mapping[str, object],
    file_payload: Mapping[str, object],
) -> str | None:
    for key in (
        "package_key",
        "object_config_graph_id",
        "source_object_instance_graph_id",
        "branch_id",
        "projection_hash",
    ):
        provider_value = _optional_text(provider_payload.get(key))
        file_value = _optional_text(file_payload.get(key))
        if provider_value is not None and file_value is not None:
            if provider_value != file_value:
                return f"ocg_migration_artifact_{key}_mismatch"
    provider_role = _optional_text(provider_payload.get("artifact_role"))
    file_role = _optional_text(file_payload.get("artifact_role"))
    if (
        provider_role is not None
        and file_role is not None
        and provider_role != file_role
    ):
        return "ocg_migration_artifact_role_mismatch"
    return None


def _artifact_ref_payload(artifact: object) -> Mapping[str, object]:
    if isinstance(artifact, Mapping):
        return _json_object(artifact)
    model_dump = getattr(artifact, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json", exclude_none=True)
        return _json_object(payload)
    keys = (
        "artifact_family",
        "artifact_key",
        "artifact_role",
        "required_for",
        "producer_provider_key",
        "producer_key",
        "digest",
        "digest_algorithm",
        "workspace_relative_path",
        "manifest_path",
        "runtime_contract_version",
        "provider_payload",
    )
    return {
        key: value
        for key in keys
        if (value := getattr(artifact, key, None)) is not None
    }


def _is_service_local_state_ocg_migration_payload(
    payload: Mapping[str, object],
) -> bool:
    return _optional_text(
        payload.get("artifact_family")
    ) == _OCG_MIGRATION_ARTIFACT_FAMILY and SERVICE_LOCAL_STATE_OCG_MIGRATION_CONSUMER_KIND in _string_tuple(
        payload.get("required_for")
    )


def _safe_workspace_relative_target(
    *,
    workspace_root: Path,
    workspace_relative_path: str,
) -> Path | None:
    relative_path = Path(workspace_relative_path)
    if relative_path.is_absolute() or any(part == ".." for part in relative_path.parts):
        return None
    target = (workspace_root / relative_path).resolve()
    try:
        target.relative_to(workspace_root)
    except ValueError:
        return None
    return target


def _normalize_sha256(value: object) -> str | None:
    token = _optional_text(value)
    if token is None or len(token) != 64:
        return None
    if any(char not in "0123456789abcdef" for char in token.lower()):
        return None
    return token.lower()


def _json_sha256(value: Mapping[str, object]) -> str:
    return sha256(_json_dump(value).encode("utf-8")).hexdigest()


def _json_dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _json_object(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _json_array(value: object) -> tuple[object, ...]:
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return ()
        return tuple(loaded) if isinstance(loaded, list) else ()
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, tuple):
        return value
    return ()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _decode_marker_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    for key in ("attempted_commit_ids", "applied_commit_ids"):
        payload[key] = tuple(str(item) for item in _json_array(payload.get(key)))
    for key in ("receipt", "evidence"):
        raw = payload.get(key)
        if isinstance(raw, str):
            try:
                loaded = json.loads(raw)
            except json.JSONDecodeError:
                loaded = {}
            payload[key] = loaded if isinstance(loaded, dict) else {}
    return payload


def _ocg_migration_marker_evidence(
    marker: ServiceOntologyOcgMigrationMarkerState,
) -> dict[str, object]:
    return {
        "service_package_name": marker.service_package_name,
        "service_local_state_db_path": marker.service_local_state_db_path.as_posix(),
        "consumer_key": marker.consumer_key,
        "package_key": marker.package_key,
        "object_config_graph_id": marker.object_config_graph_id,
        "branch_id": marker.branch_id,
        "projection_hash": marker.projection_hash,
        "ocg_head_commit_id": marker.ocg_head_commit_id,
        "status": marker.status,
        "blocker_reason": marker.blocker_reason,
        "attempted_commit_ids": list(marker.attempted_commit_ids),
        "applied_commit_ids": list(marker.applied_commit_ids),
    }


def _validate_table(table: str) -> None:
    if table not in _REPLICA_TABLES:
        raise ValueError(f"Unsupported Service ontology replica table: {table!r}")


__all__ = [
    "DEFAULT_SERVICE_ONTOLOGY_REPLICA_PROJECTOR_ID",
    "SERVICE_LOCAL_STATE_OCG_MIGRATION_CONSUMER_KIND",
    "SERVICE_LOCAL_STATE_OCG_MIGRATION_CONSUMER_KEY",
    "ServiceOntologyOcgMigrationApplyResult",
    "ServiceOntologyOcgMigrationMarkerState",
    "ServiceOntologyReplicaApplyOutcome",
    "ServiceOntologyReplicaCommitReceipt",
    "ServiceOntologyReplicaStateStore",
    "ServiceOntologyReplicaSubscriptionSpec",
    "default_service_ontology_replica_sqlite_root",
    "service_ontology_ocg_migration_marker_id",
    "service_ontology_replica_apply_receipt_id",
    "service_ontology_replica_commit_receipt_id",
    "service_ontology_replica_cursor_id",
    "service_ontology_replica_subscription_id",
]
