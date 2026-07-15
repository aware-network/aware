from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Mapping
import hashlib
import inspect
from pathlib import Path
import time
from uuid import UUID

from aware_history_ontology.lane.lane import Lane
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_commit_id,
)
from aware_orm.session.autobind import disable_autobind
from aware_utils.logging import logger

from aware_meta.graph.instance.commit.body_codec import (
    OIG_COMMIT_BODY_CONTRACT,
    ObjectInstanceGraphCommitBodyV1,
    build_oig_commit_body,
    decode_oig_commit_body,
)
from aware_meta.graph.instance.commit.contract import (
    CommitActionDescriptor,
    JsonObject,
    LaneHeadCommitReceipt,
    LaneHeadWatcher,
    ObjectInstanceGraphCommitBodyRecord,
    ObjectInstanceGraphCommitEnvelope,
    ObjectInstanceGraphCommitHealthMetadata,
    ObjectInstanceGraphCommitIdentityMetadata,
    ObjectInstanceGraphCommitIdentitySidecar,
    ObjectInstanceGraphCommitRef,
    OigiHistoryDomainCommitProjection,
)
from aware_meta.graph.instance.commit.fs_backend import (
    _atomic_write,
    _atomic_write_rebuildable_sidecar,
    _coerce_json_object,
    _dump_json,
    _file_sha256,
    _file_stat_payload,
    _path_is_relative_to,
    _read_json_object,
    _resolve_aware_root,
    _resolve_oig_root,
    _try_read_json_object,
)
from aware_meta.graph.instance.commit.fs_runtime_state import (
    _SESSION_JSON_FILE_CACHE,
    _lane_append_lock,
)
from aware_meta.graph.instance.commit.perf_trace import record_commit_perf_elapsed
from aware_meta.graph.instance.commit.json_payload import (
    _json_optional_int,
    _json_optional_string,
    _json_optional_uuid,
)
from aware_meta.graph.instance.commit.stored_commit_records import (
    OBJECT_INSTANCE_GRAPH_COMMIT_ENVELOPE_INDEX_VERSION,
    OBJECT_INSTANCE_GRAPH_COMMIT_IDENTITY_SIDECAR_INDEX_VERSION,
    object_instance_graph_commit_envelope_from_commit,
    _commit_meta_payload,
    _commit_payload,
    _object_instance_graph_commit_envelope_from_payload,
    _object_instance_graph_commit_envelope_payload,
    _object_instance_graph_commit_envelope_payload_from_envelope,
    _object_instance_graph_commit_from_envelope,
    _object_instance_graph_commit_identity_sidecar_from_commit,
    _object_instance_graph_commit_identity_sidecar_from_commit_payload,
    _object_instance_graph_commit_identity_sidecar_from_payload,
    _object_instance_graph_commit_identity_sidecar_from_record,
    _object_instance_graph_commit_identity_sidecar_payload_from_sidecar,
    _object_instance_graph_commit_ref_id,
    _object_instance_graph_commit_ref_payload,
    _object_instance_graph_commit_ref_payload_from_envelope,
    _oigi_history_domain_commit_projection_from_payload,
    _oigi_history_domain_commit_projection_payload,
)


HEAD_VERSION = 1
OBJECT_INSTANCE_GRAPH_COMMIT_HEALTH_INDEX_VERSION = 1


def _record_fs_commit_store_elapsed(
    *,
    phase: str,
    started: float,
    metadata: Mapping[str, object],
) -> None:
    record_commit_perf_elapsed(
        phase=f"oig_commit_store.{phase}",
        started=started,
        category="meta.oig.commit_store",
        metadata=metadata,
    )


def _write_rebuildable_commit_index_json(path: Path, payload: JsonObject) -> None:
    _atomic_write_rebuildable_sidecar(path, _dump_json(payload))
    _SESSION_JSON_FILE_CACHE.invalidate_path(path)


class FSCommitStore:
    """Filesystem-backed commit store per `(branch_id, projection_hash)`."""

    _lane_head_watchers: set[LaneHeadWatcher] = set()
    _aware_root: Path
    _oig_root: Path

    def __init__(self, root_dir: Path | None = None) -> None:
        self._aware_root = _resolve_aware_root(root_dir)
        self._oig_root = _resolve_oig_root(root_dir)
        self._commit_envelope_read_metrics: dict[str, int] = {
            "commit_envelope_index_hit_count": 0,
            "commit_envelope_full_body_fallback_count": 0,
            "commit_envelope_missing_commit_file_count": 0,
            "commit_envelope_fallback_failure_count": 0,
            "commit_identity_sidecar_index_hit_count": 0,
            "commit_identity_sidecar_full_body_fallback_count": 0,
            "commit_identity_sidecar_missing_commit_file_count": 0,
            "commit_identity_sidecar_fallback_failure_count": 0,
        }

    @property
    def aware_root(self) -> Path:
        return self._aware_root

    def _lane_dir(self, branch_id: UUID, projection_hash: str) -> Path:
        return self._oig_root / str(branch_id) / projection_hash

    def _commits_dir(self, branch_id: UUID, projection_hash: str) -> Path:
        return self._lane_dir(branch_id, projection_hash) / "commits"

    def commit_file_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"

    def commit_body_file_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return self._commits_dir(branch_id, projection_hash) / f"{commit_id}.body.json"

    def commit_envelope_read_metrics_snapshot(self) -> dict[str, int]:
        return dict(self._commit_envelope_read_metrics)

    def _increment_commit_envelope_read_metric(self, key: str) -> None:
        self._commit_envelope_read_metrics[key] = (
            self._commit_envelope_read_metrics.get(key, 0) + 1
        )

    def _object_instance_graph_commit_ref_index_dir(
        self, branch_id: UUID, projection_hash: str
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "object_instance_graph_commits"
        )

    def _object_instance_graph_commit_health_index_dir(
        self, branch_id: UUID, projection_hash: str
    ) -> Path:
        return self._lane_dir(branch_id, projection_hash) / "indexes" / "commit_health"

    def _object_instance_graph_commit_health_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._object_instance_graph_commit_health_index_dir(
                branch_id, projection_hash
            )
            / f"{commit_id}.json"
        )

    def _object_instance_graph_commit_envelope_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "commit_envelopes"
            / f"{commit_id}.json"
        )

    def _object_instance_graph_commit_identity_sidecar_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "commit_identity_sidecars"
            / f"{commit_id}.json"
        )

    def _oigi_history_domain_commit_projection_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        domain_commit_id: UUID,
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "indexes"
            / "oigi_history_domain_commits"
            / f"{domain_commit_id}.json"
        )

    def _object_instance_graph_commit_ref_index_path(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
    ) -> Path:
        return (
            self._object_instance_graph_commit_ref_index_dir(branch_id, projection_hash)
            / f"{object_instance_graph_commit_id}.json"
        )

    def _write_object_instance_graph_commit_health_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit.commit.id}.json"
        )
        if not commit_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        payload: JsonObject = {
            "v": OBJECT_INSTANCE_GRAPH_COMMIT_HEALTH_INDEX_VERSION,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit.commit.id),
            "object_instance_graph_id": str(commit.object_instance_graph_id),
            "object_instance_graph_identity_id": str(
                commit.object_instance_graph_identity_id
            ),
            "graph_hash_post": str(commit.graph_hash_post or ""),
            "parent_count": len(commit.commit.commit_parents),
            "file_size": file_size,
            "file_mtime_ns": file_mtime_ns,
            "file_ctime_ns": file_ctime_ns,
            "file_sha256": _file_sha256(commit_path),
        }
        path = self._object_instance_graph_commit_health_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=f"Existing OIG commit health index is unreadable: {path}",
            )
            if existing_payload == payload:
                return
        _write_rebuildable_commit_index_json(path, payload)

    def _write_object_instance_graph_commit_health_index_from_record(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        envelope: ObjectInstanceGraphCommitEnvelope,
    ) -> None:
        commit_path = self.commit_file_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=envelope.commit_id,
        )
        if not commit_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        payload: JsonObject = {
            "v": OBJECT_INSTANCE_GRAPH_COMMIT_HEALTH_INDEX_VERSION,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(envelope.commit_id),
            "object_instance_graph_id": str(envelope.object_instance_graph_id),
            "object_instance_graph_identity_id": str(
                envelope.object_instance_graph_identity_id
            ),
            "graph_hash_post": str(envelope.graph_hash_post or ""),
            "parent_count": len(envelope.parent_commit_ids),
            "file_size": file_size,
            "file_mtime_ns": file_mtime_ns,
            "file_ctime_ns": file_ctime_ns,
            "file_sha256": _file_sha256(commit_path),
        }
        if envelope.body_sha256 is not None:
            payload["body_sha256"] = envelope.body_sha256
        if envelope.body_size_bytes is not None:
            payload["body_size_bytes"] = envelope.body_size_bytes
        path = self._object_instance_graph_commit_health_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=envelope.commit_id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=f"Existing OIG commit health index is unreadable: {path}",
            )
            if existing_payload == payload:
                return
        _write_rebuildable_commit_index_json(path, payload)

    def _write_object_instance_graph_commit_ref_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        object_instance_graph_commit_id = _object_instance_graph_commit_ref_id(commit)
        payload = _object_instance_graph_commit_ref_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        path = self._object_instance_graph_commit_ref_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
        if path.exists():
            existing_payload = _read_json_object(
                path,
                error_message=f"Existing OIG commit ref index is unreadable: {path}",
            )
            if existing_payload != payload:
                raise ValueError(
                    f"Existing OIG commit ref index differs: {object_instance_graph_commit_id}"
                )
            return
        _write_rebuildable_commit_index_json(path, payload)

    def _write_object_instance_graph_commit_ref_index_from_envelope(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        envelope: ObjectInstanceGraphCommitEnvelope,
    ) -> None:
        object_instance_graph_commit_id = envelope.object_instance_graph_commit_id
        payload = _object_instance_graph_commit_ref_payload_from_envelope(
            branch_id=branch_id,
            projection_hash=projection_hash,
            envelope=envelope,
        )
        path = self._object_instance_graph_commit_ref_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
        if path.exists():
            existing_payload = _read_json_object(
                path,
                error_message=f"Existing OIG commit ref index is unreadable: {path}",
            )
            if existing_payload != payload:
                raise ValueError(
                    f"Existing OIG commit ref index differs: {object_instance_graph_commit_id}"
                )
            return
        _write_rebuildable_commit_index_json(path, payload)

    def _write_object_instance_graph_commit_envelope_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit.commit.id}.json"
        )
        if not commit_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        payload = _object_instance_graph_commit_envelope_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )
        payload["file_size"] = file_size
        payload["file_mtime_ns"] = file_mtime_ns
        payload["file_ctime_ns"] = file_ctime_ns
        path = self._object_instance_graph_commit_envelope_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=f"Existing OIG commit envelope index is unreadable: {path}",
            )
            if existing_payload == payload:
                return
        _write_rebuildable_commit_index_json(path, payload)

    def _write_object_instance_graph_commit_envelope_index_from_payload(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        envelope: ObjectInstanceGraphCommitEnvelope,
        payload: JsonObject,
    ) -> None:
        commit_path = self.commit_file_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=envelope.commit_id,
        )
        if not commit_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        index_payload = dict(payload)
        index_payload["file_size"] = file_size
        index_payload["file_mtime_ns"] = file_mtime_ns
        index_payload["file_ctime_ns"] = file_ctime_ns
        path = self._object_instance_graph_commit_envelope_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=envelope.commit_id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=f"Existing OIG commit envelope index is unreadable: {path}",
            )
            if existing_payload == index_payload:
                return
        _write_rebuildable_commit_index_json(path, index_payload)

    def _write_object_instance_graph_commit_identity_sidecar_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit.commit.id}.json"
        )
        if not commit_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        payload = _object_instance_graph_commit_identity_sidecar_payload_from_sidecar(
            branch_id=branch_id,
            projection_hash=projection_hash,
            sidecar=_object_instance_graph_commit_identity_sidecar_from_commit(
                commit=commit,
            ),
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
        )
        path = self._object_instance_graph_commit_identity_sidecar_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit.commit.id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=(
                    "Existing OIG commit identity sidecar index is unreadable: "
                    + str(path)
                ),
            )
            if existing_payload == payload:
                return
        _write_rebuildable_commit_index_json(path, payload)

    def _write_object_instance_graph_commit_identity_sidecar_index_from_record(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        envelope: ObjectInstanceGraphCommitEnvelope,
        body: ObjectInstanceGraphCommitBodyV1,
    ) -> None:
        commit_path = self.commit_file_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=envelope.commit_id,
        )
        if not commit_path.exists():
            return
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        payload = _object_instance_graph_commit_identity_sidecar_payload_from_sidecar(
            branch_id=branch_id,
            projection_hash=projection_hash,
            sidecar=_object_instance_graph_commit_identity_sidecar_from_record(
                envelope=envelope,
                body=body,
            ),
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
        )
        path = self._object_instance_graph_commit_identity_sidecar_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=envelope.commit_id,
        )
        if path.exists():
            existing_payload = _try_read_json_object(
                path,
                log_prefix=f"Existing OIG commit identity sidecar index is unreadable: {path}",
            )
            if existing_payload == payload:
                return
        _write_rebuildable_commit_index_json(path, payload)

    def _remove_stale_object_instance_graph_commit_ref_index(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
        domain_commit_id: UUID,
    ) -> None:
        path = self._object_instance_graph_commit_ref_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
        if not path.exists():
            return
        existing_payload = _read_json_object(
            path,
            error_message=f"Existing stale OIG commit ref index is unreadable: {path}",
        )
        if (
            existing_payload.get("domain_commit_id") != str(domain_commit_id)
            or existing_payload.get("branch_id") != str(branch_id)
            or existing_payload.get("projection_hash") != projection_hash
        ):
            raise ValueError(
                "Refusing to remove OIG commit ref index for a different domain commit: "
                + f"{object_instance_graph_commit_id}"
            )
        path.unlink()
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)

    def _repair_existing_commit_identity_metadata(
        self,
        *,
        commit_path: Path,
        existing_commit_payload: JsonObject,
        commit: ObjectInstanceGraphCommit,
    ) -> UUID | None:
        existing_oig_id = _json_optional_uuid(
            existing_commit_payload,
            "object_instance_graph_id",
        )
        if existing_oig_id != commit.object_instance_graph_id:
            raise ValueError(
                "Existing commit OIG id differs from payload: " + f"{commit.commit.id}"
            )
        existing_oigi_id = _json_optional_uuid(
            existing_commit_payload,
            "object_instance_graph_identity_id",
        )
        if existing_oigi_id is None:
            raise ValueError(
                "Existing commit missing object_instance_graph_identity_id: "
                + f"{commit.commit.id}"
            )
        if existing_oigi_id == commit.object_instance_graph_identity_id:
            return None

        stale_ref_id = stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=existing_oigi_id,
            commit_id=commit.commit.id,
        )
        _atomic_write(commit_path, _dump_json(_commit_payload(commit)))
        _SESSION_JSON_FILE_CACHE.invalidate_path(commit_path)
        return stale_ref_id

    def ocg_delta_hint_path(
        self, *, branch_id: UUID, projection_hash: str, commit_id: UUID
    ) -> Path:
        return (
            self._lane_dir(branch_id, projection_hash)
            / "hints"
            / "ocg_deltas"
            / f"{commit_id}.json"
        )

    def put_ocg_delta_hint(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
        payload: JsonObject,
    ) -> bool:
        """Persist an OCGΔ hint payload for a commit (idempotent, fail-closed on mismatch)."""
        path = self.ocg_delta_hint_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )

        def _read_existing_hint() -> JsonObject:
            return _read_json_object(
                path,
                error_message=f"Existing OCGΔ hint is unreadable: {path}",
            )

        if path.exists():
            existing = _read_existing_hint()
            if existing == payload:
                return False
            if existing.get("v") != payload.get("v"):
                _atomic_write(path, _dump_json(payload))
                _SESSION_JSON_FILE_CACHE.invalidate_path(path)
                existing = _read_existing_hint()
            if existing != payload:
                raise ValueError(
                    f"Existing OCGΔ hint differs from expected payload: {path}"
                )
            return True

        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)
        existing = _read_existing_hint()
        if existing != payload:
            raise ValueError(
                f"Existing OCGΔ hint differs from expected payload: {path}"
            )
        return True

    @classmethod
    def register_lane_head_watcher(cls, watcher: LaneHeadWatcher) -> None:
        cls._lane_head_watchers.add(watcher)

    @classmethod
    def unregister_lane_head_watcher(cls, watcher: LaneHeadWatcher) -> None:
        cls._lane_head_watchers.discard(watcher)

    @classmethod
    async def _dispatch_lane_head_watchers(cls, receipt: LaneHeadCommitReceipt) -> None:
        if not cls._lane_head_watchers:
            return

        for watcher in tuple(cls._lane_head_watchers):
            try:
                result = watcher(receipt)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:
                logger.warning("Lane head watcher failed: %s", exc)

    async def put_commit_record(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        envelope: ObjectInstanceGraphCommitEnvelope,
        body: ObjectInstanceGraphCommitBodyV1,
        commit_action: CommitActionDescriptor | None = None,
        write_health_index: bool = True,
    ) -> bool:
        if envelope.commit_id != body.commit_id:
            raise ValueError(
                "OIG commit envelope/body commit_id mismatch: "
                + f"envelope={envelope.commit_id} body={body.commit_id}"
            )
        if (
            envelope.object_instance_graph_commit_id
            != body.object_instance_graph_commit_id
        ):
            raise ValueError(
                "OIG commit envelope/body object_instance_graph_commit_id mismatch: "
                + f"envelope={envelope.object_instance_graph_commit_id} "
                + f"body={body.object_instance_graph_commit_id}"
            )
        if (
            envelope.object_instance_graph_identity_id
            != body.object_instance_graph_identity_id
        ):
            raise ValueError(
                "OIG commit envelope/body object_instance_graph_identity_id mismatch: "
                + f"envelope={envelope.object_instance_graph_identity_id} "
                + f"body={body.object_instance_graph_identity_id}"
            )
        if envelope.object_instance_graph_id != body.object_instance_graph_id:
            raise ValueError(
                "OIG commit envelope/body object_instance_graph_id mismatch: "
                + f"envelope={envelope.object_instance_graph_id} "
                + f"body={body.object_instance_graph_id}"
            )

        commits_dir = self._commits_dir(branch_id, projection_hash)
        commits_dir.mkdir(parents=True, exist_ok=True)
        commit_path = self.commit_file_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=envelope.commit_id,
        )
        body_path = self.commit_body_file_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=envelope.commit_id,
        )
        body_ref = body_path.name
        trace_metadata: dict[str, object] = {
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(envelope.commit_id),
            "object_instance_graph_id": str(envelope.object_instance_graph_id),
            "object_instance_graph_identity_id": str(
                envelope.object_instance_graph_identity_id
            ),
        }
        envelope_payload_started = time.monotonic()
        envelope_payload = _object_instance_graph_commit_envelope_payload_from_envelope(
            branch_id=branch_id,
            projection_hash=projection_hash,
            envelope=envelope,
            body=body,
            body_ref=body_ref,
        )
        _record_fs_commit_store_elapsed(
            phase="put_commit_record.build_envelope_payload",
            started=envelope_payload_started,
            metadata=trace_metadata,
        )

        wrote_commit = False
        body_write_started = time.monotonic()
        if body_path.exists():
            existing_body = body_path.read_bytes()
            if existing_body != body.canonical_bytes:
                raise ValueError(
                    f"Existing OIG commit body differs: {envelope.commit_id}"
                )
        else:
            _atomic_write(body_path, body.canonical_bytes.decode("utf-8"))
            _SESSION_JSON_FILE_CACHE.invalidate_path(body_path)
            wrote_commit = True
        _record_fs_commit_store_elapsed(
            phase="put_commit_record.write_or_validate_body",
            started=body_write_started,
            metadata=trace_metadata,
        )

        envelope_write_started = time.monotonic()
        if commit_path.exists():
            existing_envelope_payload = _read_json_object(
                commit_path,
                error_message=f"Existing OIG commit envelope is unreadable: {commit_path}",
            )
            if existing_envelope_payload != envelope_payload:
                raise ValueError(
                    f"Existing OIG commit envelope differs: {envelope.commit_id}"
                )
        else:
            _atomic_write(commit_path, _dump_json(envelope_payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(commit_path)
            wrote_commit = True
        _record_fs_commit_store_elapsed(
            phase="put_commit_record.write_or_validate_envelope",
            started=envelope_write_started,
            metadata=trace_metadata,
        )

        meta_write_started = time.monotonic()
        meta_payload = _commit_meta_payload(commit_action)
        if meta_payload is not None:
            meta_path = commits_dir / f"{envelope.commit_id}.meta.json"
            if meta_path.exists():
                existing_meta_payload = _read_json_object(
                    meta_path,
                    error_message=f"Existing commit metadata is unreadable: {meta_path}",
                )
                if existing_meta_payload != meta_payload:
                    raise ValueError(
                        f"Existing commit metadata differs: {envelope.commit_id}"
                    )
            else:
                _atomic_write(meta_path, _dump_json(meta_payload))
                _SESSION_JSON_FILE_CACHE.invalidate_path(meta_path)
        _record_fs_commit_store_elapsed(
            phase="put_commit_record.write_or_validate_meta",
            started=meta_write_started,
            metadata={
                **trace_metadata,
                "has_commit_action": commit_action is not None,
            },
        )

        ref_index_started = time.monotonic()
        self._write_object_instance_graph_commit_ref_index_from_envelope(
            branch_id=branch_id,
            projection_hash=projection_hash,
            envelope=envelope,
        )
        _record_fs_commit_store_elapsed(
            phase="put_commit_record.write_ref_index",
            started=ref_index_started,
            metadata=trace_metadata,
        )
        envelope_index_started = time.monotonic()
        self._write_object_instance_graph_commit_envelope_index_from_payload(
            branch_id=branch_id,
            projection_hash=projection_hash,
            envelope=envelope,
            payload=envelope_payload,
        )
        _record_fs_commit_store_elapsed(
            phase="put_commit_record.write_envelope_index",
            started=envelope_index_started,
            metadata=trace_metadata,
        )
        identity_sidecar_started = time.monotonic()
        self._write_object_instance_graph_commit_identity_sidecar_index_from_record(
            branch_id=branch_id,
            projection_hash=projection_hash,
            envelope=envelope,
            body=body,
        )
        _record_fs_commit_store_elapsed(
            phase="put_commit_record.write_identity_sidecar_index",
            started=identity_sidecar_started,
            metadata=trace_metadata,
        )
        health_index_started = time.monotonic()
        if write_health_index:
            self._write_object_instance_graph_commit_health_index_from_record(
                branch_id=branch_id,
                projection_hash=projection_hash,
                envelope=envelope,
            )
            health_phase = "put_commit_record.write_health_index"
        else:
            health_phase = "put_commit_record.defer_health_index"
        _record_fs_commit_store_elapsed(
            phase=health_phase,
            started=health_index_started,
            metadata={
                **trace_metadata,
                "write_health_index": write_health_index,
            },
        )
        return wrote_commit

    async def get_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommit | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            self._increment_commit_envelope_read_metric(
                "commit_envelope_missing_commit_file_count"
            )
            return None
        try:
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                commit_path,
                log_prefix=f"Failed reading commit {commit_id}",
            )
            if payload is None:
                return None
            with disable_autobind():
                envelope = _object_instance_graph_commit_envelope_from_payload(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=commit_id,
                    payload=payload,
                )
                return _object_instance_graph_commit_from_envelope(envelope)
        except Exception as exc:
            logger.warning("Failed reading commit %s: %s", commit_id, exc)
            return None

    async def get_commit_envelope(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitEnvelope | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            return None
        envelope_path = self._object_instance_graph_commit_envelope_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        if envelope_path.exists():
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                envelope_path,
                log_prefix=f"Failed reading commit envelope {commit_id}",
            )
            if payload is not None:
                try:
                    if (
                        payload.get("v")
                        == OBJECT_INSTANCE_GRAPH_COMMIT_ENVELOPE_INDEX_VERSION
                        and _json_optional_int(payload, "file_size") == file_size
                        and _json_optional_int(payload, "file_mtime_ns")
                        == file_mtime_ns
                        and _json_optional_int(payload, "file_ctime_ns")
                        == file_ctime_ns
                    ):
                        self._increment_commit_envelope_read_metric(
                            "commit_envelope_index_hit_count"
                        )
                        return _object_instance_graph_commit_envelope_from_payload(
                            branch_id=branch_id,
                            projection_hash=projection_hash,
                            commit_id=commit_id,
                            payload=payload,
                        )
                except Exception as exc:
                    logger.warning(
                        "Failed parsing commit envelope %s: %s", commit_id, exc
                    )

        self._increment_commit_envelope_read_metric(
            "commit_envelope_full_body_fallback_count"
        )
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            commit_path,
            log_prefix=f"Failed reading commit envelope fallback {commit_id}",
        )
        if payload is None:
            self._increment_commit_envelope_read_metric(
                "commit_envelope_fallback_failure_count"
            )
            return None
        try:
            return _object_instance_graph_commit_envelope_from_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                payload=payload,
            )
        except Exception as exc:
            logger.warning(
                "Failed parsing commit envelope fallback %s: %s", commit_id, exc
            )
            self._increment_commit_envelope_read_metric(
                "commit_envelope_fallback_failure_count"
            )
            return None

    async def get_commit_body(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitBodyV1 | None:
        envelope = await self.get_commit_envelope(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if envelope is None:
            return None
        return self._read_commit_body_for_envelope(
            branch_id=branch_id,
            projection_hash=projection_hash,
            envelope=envelope,
        )

    def _read_commit_body_for_envelope(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        envelope: ObjectInstanceGraphCommitEnvelope,
    ) -> ObjectInstanceGraphCommitBodyV1:
        commit_id = envelope.commit_id
        if envelope.body_contract != OIG_COMMIT_BODY_CONTRACT:
            raise ValueError(
                "Unsupported OIG commit body contract: "
                + f"commit_id={commit_id} contract={envelope.body_contract}"
            )
        body_ref = envelope.body_ref or f"{commit_id}.body.json"
        commits_dir = self._commits_dir(branch_id, projection_hash).resolve()
        body_path = (commits_dir / body_ref).resolve()
        if not _path_is_relative_to(body_path, commits_dir):
            raise ValueError(f"OIG commit body ref escapes commits dir: {commit_id}")
        if not body_path.is_file():
            raise ValueError(f"OIG commit body file missing: {body_path}")
        body_bytes = body_path.read_bytes()
        if (
            envelope.body_size_bytes is not None
            and len(body_bytes) != envelope.body_size_bytes
        ):
            raise ValueError(
                "OIG commit body size mismatch: "
                + f"commit_id={commit_id} expected={envelope.body_size_bytes} "
                + f"actual={len(body_bytes)}"
            )
        body_sha256 = hashlib.sha256(body_bytes).hexdigest()
        if envelope.body_sha256 is not None and body_sha256 != envelope.body_sha256:
            raise ValueError(
                "OIG commit body sha256 mismatch: "
                + f"commit_id={commit_id} expected={envelope.body_sha256} "
                + f"actual={body_sha256}"
            )
        body = decode_oig_commit_body(body_bytes)
        if body.commit_id != envelope.commit_id:
            raise ValueError(f"OIG commit body commit_id mismatch: {commit_id}")
        if (
            body.object_instance_graph_commit_id
            != envelope.object_instance_graph_commit_id
        ):
            raise ValueError(
                f"OIG commit body object_instance_graph_commit_id mismatch: {commit_id}"
            )
        if (
            body.object_instance_graph_identity_id
            != envelope.object_instance_graph_identity_id
        ):
            raise ValueError(
                f"OIG commit body object_instance_graph_identity_id mismatch: {commit_id}"
            )
        if body.object_instance_graph_id != envelope.object_instance_graph_id:
            raise ValueError(
                f"OIG commit body object_instance_graph_id mismatch: {commit_id}"
            )
        return body

    async def get_commit_record(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitBodyRecord | None:
        envelope = await self.get_commit_envelope(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if envelope is None:
            return None
        body = await self.get_commit_body(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if body is None:
            return None
        return ObjectInstanceGraphCommitBodyRecord(envelope=envelope, body=body)

    async def get_commit_identity_sidecar(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitIdentitySidecar | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            self._increment_commit_envelope_read_metric(
                "commit_identity_sidecar_missing_commit_file_count"
            )
            return None
        sidecar_path = self._object_instance_graph_commit_identity_sidecar_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        if sidecar_path.exists():
            payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                sidecar_path,
                log_prefix=f"Failed reading commit identity sidecar {commit_id}",
            )
            if payload is not None:
                try:
                    if (
                        payload.get("v")
                        == OBJECT_INSTANCE_GRAPH_COMMIT_IDENTITY_SIDECAR_INDEX_VERSION
                        and _json_optional_int(payload, "file_size") == file_size
                        and _json_optional_int(payload, "file_mtime_ns")
                        == file_mtime_ns
                        and _json_optional_int(payload, "file_ctime_ns")
                        == file_ctime_ns
                    ):
                        self._increment_commit_envelope_read_metric(
                            "commit_identity_sidecar_index_hit_count"
                        )
                        return (
                            _object_instance_graph_commit_identity_sidecar_from_payload(
                                branch_id=branch_id,
                                projection_hash=projection_hash,
                                commit_id=commit_id,
                                payload=payload,
                            )
                        )
                except Exception as exc:
                    logger.warning(
                        "Failed parsing commit identity sidecar %s: %s",
                        commit_id,
                        exc,
                    )

        self._increment_commit_envelope_read_metric(
            "commit_identity_sidecar_full_body_fallback_count"
        )
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            commit_path,
            log_prefix=f"Failed reading commit identity sidecar fallback {commit_id}",
        )
        if payload is None:
            self._increment_commit_envelope_read_metric(
                "commit_identity_sidecar_fallback_failure_count"
            )
            return None
        try:
            envelope = _object_instance_graph_commit_envelope_from_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                payload=payload,
            )
            body = self._read_commit_body_for_envelope(
                branch_id=branch_id,
                projection_hash=projection_hash,
                envelope=envelope,
            )
            sidecar = _object_instance_graph_commit_identity_sidecar_from_record(
                envelope=envelope,
                body=body,
            )
        except Exception as split_exc:
            try:
                sidecar = (
                    _object_instance_graph_commit_identity_sidecar_from_commit_payload(
                        commit_id=commit_id,
                        payload=payload,
                    )
                )
            except Exception as legacy_exc:
                logger.warning(
                    "Failed parsing commit identity sidecar fallback %s: "
                    "split=%s legacy=%s",
                    commit_id,
                    split_exc,
                    legacy_exc,
                )
                self._increment_commit_envelope_read_metric(
                    "commit_identity_sidecar_fallback_failure_count"
                )
                return None

        sidecar_payload = (
            _object_instance_graph_commit_identity_sidecar_payload_from_sidecar(
                branch_id=branch_id,
                projection_hash=projection_hash,
                sidecar=sidecar,
                file_size=file_size,
                file_mtime_ns=file_mtime_ns,
                file_ctime_ns=file_ctime_ns,
            )
        )
        try:
            _write_rebuildable_commit_index_json(sidecar_path, sidecar_payload)
        except Exception as exc:
            logger.warning(
                "Failed writing repaired commit identity sidecar %s: %s",
                commit_id,
                exc,
            )
        return sidecar

    async def get_oigi_history_domain_commit_projection(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        domain_commit_id: UUID,
    ) -> OigiHistoryDomainCommitProjection | None:
        path = self._oigi_history_domain_commit_projection_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_commit_id=domain_commit_id,
        )
        if not path.exists():
            return None
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            path,
            log_prefix=f"Failed reading OIGI history projection index {domain_commit_id}",
        )
        if payload is None:
            return None
        try:
            return _oigi_history_domain_commit_projection_from_payload(
                branch_id=branch_id,
                projection_hash=projection_hash,
                domain_commit_id=domain_commit_id,
                payload=payload,
            )
        except Exception as exc:
            logger.warning(
                "Failed parsing OIGI history projection index %s: %s",
                domain_commit_id,
                exc,
            )
            return None

    def put_oigi_history_domain_commit_projection(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        projection: OigiHistoryDomainCommitProjection,
    ) -> bool:
        path = self._oigi_history_domain_commit_projection_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_commit_id=projection.domain_commit_id,
        )
        payload = _oigi_history_domain_commit_projection_payload(
            projection=projection,
        )
        if path.exists():
            existing_payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
                path,
                log_prefix=(
                    "Existing OIGI history projection index is unreadable: " + str(path)
                ),
            )
            if existing_payload == payload:
                return False
        _atomic_write(path, _dump_json(payload))
        _SESSION_JSON_FILE_CACHE.invalidate_path(path)
        return True

    async def get_commit_identity_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitIdentityMetadata | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            return None
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            commit_path,
            log_prefix=f"Failed reading commit identity metadata {commit_id}",
        )
        if payload is None:
            return None
        object_instance_graph_id = _json_optional_uuid(
            payload,
            "object_instance_graph_id",
        )
        object_instance_graph_identity_id = _json_optional_uuid(
            payload,
            "object_instance_graph_identity_id",
        )
        if (
            object_instance_graph_id is None
            or object_instance_graph_identity_id is None
        ):
            return None
        return ObjectInstanceGraphCommitIdentityMetadata(
            object_instance_graph_id=object_instance_graph_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
        )

    async def get_commit_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> ObjectInstanceGraphCommitHealthMetadata | None:
        commit_path = (
            self._commits_dir(branch_id, projection_hash) / f"{commit_id}.json"
        )
        if not commit_path.exists():
            return None
        file_size, file_mtime_ns, file_ctime_ns = _file_stat_payload(commit_path)
        health_path = self._object_instance_graph_commit_health_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if not health_path.exists():
            return None
        payload = _SESSION_JSON_FILE_CACHE.try_read_json_object(
            health_path,
            log_prefix=f"Failed reading commit health metadata {commit_id}",
        )
        if payload is None:
            return None
        if payload.get("v") != OBJECT_INSTANCE_GRAPH_COMMIT_HEALTH_INDEX_VERSION:
            return None
        if payload.get("branch_id") != str(branch_id):
            return None
        if payload.get("projection_hash") != projection_hash:
            return None
        if payload.get("commit_id") != str(commit_id):
            return None
        if _json_optional_int(payload, "file_size") != file_size:
            return None
        if _json_optional_int(payload, "file_mtime_ns") != file_mtime_ns:
            return None
        if _json_optional_int(payload, "file_ctime_ns") != file_ctime_ns:
            return None
        if _json_optional_string(payload, "file_sha256") != _file_sha256(commit_path):
            return None

        object_instance_graph_id = _json_optional_uuid(
            payload,
            "object_instance_graph_id",
        )
        object_instance_graph_identity_id = _json_optional_uuid(
            payload,
            "object_instance_graph_identity_id",
        )
        graph_hash_post = _json_optional_string(payload, "graph_hash_post")
        parent_count = _json_optional_int(payload, "parent_count")
        file_sha256 = _json_optional_string(payload, "file_sha256")
        if (
            object_instance_graph_id is None
            or object_instance_graph_identity_id is None
            or not graph_hash_post
            or parent_count is None
            or not file_sha256
        ):
            return None
        return ObjectInstanceGraphCommitHealthMetadata(
            commit_id=commit_id,
            projection_hash=projection_hash,
            object_instance_graph_id=object_instance_graph_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            graph_hash_post=graph_hash_post,
            parent_count=parent_count,
            file_size=file_size,
            file_mtime_ns=file_mtime_ns,
            file_ctime_ns=file_ctime_ns,
            file_sha256=file_sha256,
        )

    def write_commit_health_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> None:
        self._write_object_instance_graph_commit_health_index(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
        )

    async def head(self, *, branch_id: UUID, projection_hash: str) -> JsonObject | None:
        head_path = self._lane_dir(branch_id, projection_hash) / "HEAD.json"
        if not head_path.exists():
            return None
        return _SESSION_JSON_FILE_CACHE.try_read_json_object(
            head_path,
            log_prefix="Failed reading HEAD",
        )

    async def iter_lane_heads_by_projection(
        self,
        *,
        projection_hash: str,
    ) -> AsyncIterator[tuple[UUID, JsonObject]]:
        projection = projection_hash.strip()
        if not projection or not self._oig_root.exists():
            return

        try:
            branch_dirs = sorted(
                (path for path in self._oig_root.iterdir() if path.is_dir()),
                key=lambda path: path.name,
            )
        except Exception:
            return

        for branch_dir in branch_dirs:
            try:
                branch_id = UUID(branch_dir.name)
            except Exception:
                continue

            head = await self.head(branch_id=branch_id, projection_hash=projection)
            if head is None:
                continue
            if _json_optional_string(head, "commit_id") is None:
                continue
            yield branch_id, head

    async def head_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> ObjectInstanceGraphCommit | None:
        head = await self.head(branch_id=branch_id, projection_hash=projection_hash)
        if head is None:
            return None
        commit_id_text = _json_optional_string(head, "commit_id")
        if commit_id_text is None:
            return None
        try:
            return await self.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=UUID(commit_id_text),
            )
        except Exception:
            return None

    async def head_for_lane(self, *, lane: Lane) -> JsonObject | None:
        return await self.head(branch_id=lane.branch_id, projection_hash=lane.lane_hash)

    async def head_commit_for_lane(
        self, *, lane: Lane
    ) -> ObjectInstanceGraphCommit | None:
        return await self.head_commit(
            branch_id=lane.branch_id, projection_hash=lane.lane_hash
        )

    async def domain_commit_id_for_object_instance_graph_commit_id(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
    ) -> UUID | None:
        """Resolve a typed OIG commit wrapper id to its domain commit id in O(1).

        New commit writes maintain a sidecar index. The HEAD check is a bounded
        compatibility repair for stores written before the index existed.
        """

        path = self._object_instance_graph_commit_ref_index_path(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
        if path.exists():
            payload = _read_json_object(
                path,
                error_message=f"Invalid OIG commit ref index JSON object: {path}",
            )
            indexed_id = _json_optional_uuid(payload, "object_instance_graph_commit_id")
            domain_commit_id = _json_optional_uuid(payload, "domain_commit_id")
            if (
                indexed_id != object_instance_graph_commit_id
                or domain_commit_id is None
            ):
                raise ValueError(f"Invalid OIG commit ref index payload: {path}")
            return domain_commit_id

        head = await self.head(branch_id=branch_id, projection_hash=projection_hash)
        if head is None:
            return None
        head_domain_commit_id = _json_optional_uuid(head, "commit_id")
        head_object_instance_graph_commit_id = _json_optional_uuid(
            head,
            "object_instance_graph_commit_id",
        )
        if (
            head_domain_commit_id is None
            or head_object_instance_graph_commit_id != object_instance_graph_commit_id
        ):
            return None
        head_envelope = await self.get_commit_envelope(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_domain_commit_id,
        )
        if head_envelope is None:
            return None

        self._write_object_instance_graph_commit_ref_index_from_envelope(
            branch_id=branch_id,
            projection_hash=projection_hash,
            envelope=head_envelope,
        )
        return head_domain_commit_id

    async def domain_commit_refs_for_object_instance_graph_commit_id(
        self,
        *,
        projection_hash: str,
        object_instance_graph_commit_id: UUID,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        """Find branches containing an indexed typed OIG commit wrapper id."""

        projection = projection_hash.strip()
        if not projection or not self._oig_root.exists():
            return ()

        refs: list[ObjectInstanceGraphCommitRef] = []
        try:
            branch_dirs = sorted(
                (path for path in self._oig_root.iterdir() if path.is_dir()),
                key=lambda path: path.name,
            )
        except Exception:
            return ()

        for branch_dir in branch_dirs:
            try:
                branch_id = UUID(branch_dir.name)
            except Exception:
                continue

            path = self._object_instance_graph_commit_ref_index_path(
                branch_id=branch_id,
                projection_hash=projection,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
            )
            if path.exists():
                payload = _read_json_object(
                    path,
                    error_message=f"Invalid OIG commit ref index JSON object: {path}",
                )
                indexed_id = _json_optional_uuid(
                    payload,
                    "object_instance_graph_commit_id",
                )
                domain_commit_id = _json_optional_uuid(payload, "domain_commit_id")
                indexed_projection = _json_optional_string(payload, "projection_hash")
                indexed_branch_id = _json_optional_uuid(payload, "branch_id")
                if (
                    indexed_id != object_instance_graph_commit_id
                    or domain_commit_id is None
                    or indexed_projection != projection
                    or indexed_branch_id != branch_id
                ):
                    raise ValueError(f"Invalid OIG commit ref index payload: {path}")
                refs.append(
                    ObjectInstanceGraphCommitRef(
                        branch_id=branch_id,
                        projection_hash=projection,
                        object_instance_graph_commit_id=object_instance_graph_commit_id,
                        domain_commit_id=domain_commit_id,
                        object_instance_graph_identity_id=_json_optional_uuid(
                            payload,
                            "object_instance_graph_identity_id",
                        ),
                        object_instance_graph_id=_json_optional_uuid(
                            payload,
                            "object_instance_graph_id",
                        ),
                        graph_hash_post=_json_optional_string(
                            payload,
                            "graph_hash_post",
                        ),
                    )
                )
                continue

            domain_commit_id = (
                await self.domain_commit_id_for_object_instance_graph_commit_id(
                    branch_id=branch_id,
                    projection_hash=projection,
                    object_instance_graph_commit_id=object_instance_graph_commit_id,
                )
            )
            if domain_commit_id is not None:
                indexed_payload: Mapping[str, object] = {}
                if path.exists():
                    indexed_payload = _read_json_object(
                        path,
                        error_message=(
                            f"Invalid OIG commit ref index JSON object: {path}"
                        ),
                    )
                refs.append(
                    ObjectInstanceGraphCommitRef(
                        branch_id=branch_id,
                        projection_hash=projection,
                        object_instance_graph_commit_id=object_instance_graph_commit_id,
                        domain_commit_id=domain_commit_id,
                        object_instance_graph_identity_id=(
                            _json_optional_uuid(
                                indexed_payload,
                                "object_instance_graph_identity_id",
                            )
                        ),
                        object_instance_graph_id=_json_optional_uuid(
                            indexed_payload,
                            "object_instance_graph_id",
                        ),
                        graph_hash_post=_json_optional_string(
                            indexed_payload,
                            "graph_hash_post",
                        ),
                    )
                )

        return tuple(refs)

    async def domain_commit_refs_for_object_instance_graph_commit_ids(
        self,
        *,
        projection_hash: str,
        object_instance_graph_commit_ids: Iterable[UUID],
        allow_head_fallback: bool = True,
    ) -> dict[UUID, tuple[ObjectInstanceGraphCommitRef, ...]]:
        """Find branches containing indexed typed OIG commit wrapper ids in one pass."""

        projection = projection_hash.strip()
        requested_ids = frozenset(object_instance_graph_commit_ids)
        refs_by_id: dict[UUID, list[ObjectInstanceGraphCommitRef]] = {
            object_instance_graph_commit_id: []
            for object_instance_graph_commit_id in requested_ids
        }
        if not projection or not requested_ids or not self._oig_root.exists():
            return {key: tuple(value) for key, value in refs_by_id.items()}

        try:
            branch_dirs = sorted(
                (path for path in self._oig_root.iterdir() if path.is_dir()),
                key=lambda path: path.name,
            )
        except Exception:
            return {key: tuple(value) for key, value in refs_by_id.items()}

        seen_refs: set[tuple[UUID, UUID, UUID]] = set()
        for branch_dir in branch_dirs:
            try:
                branch_id = UUID(branch_dir.name)
            except Exception:
                continue

            index_dir = self._object_instance_graph_commit_ref_index_dir(
                branch_id,
                projection,
            )
            if not index_dir.is_dir():
                continue
            for path in sorted(index_dir.glob("*.json"), key=lambda item: item.name):
                try:
                    object_instance_graph_commit_id = UUID(path.stem)
                except Exception:
                    continue
                if object_instance_graph_commit_id not in requested_ids:
                    continue
                payload = _read_json_object(
                    path,
                    error_message=f"Invalid OIG commit ref index JSON object: {path}",
                )
                indexed_id = _json_optional_uuid(
                    payload,
                    "object_instance_graph_commit_id",
                )
                domain_commit_id = _json_optional_uuid(payload, "domain_commit_id")
                indexed_projection = _json_optional_string(payload, "projection_hash")
                indexed_branch_id = _json_optional_uuid(payload, "branch_id")
                if (
                    indexed_id != object_instance_graph_commit_id
                    or domain_commit_id is None
                    or indexed_projection != projection
                    or indexed_branch_id != branch_id
                ):
                    raise ValueError(f"Invalid OIG commit ref index payload: {path}")
                ref_key = (
                    object_instance_graph_commit_id,
                    branch_id,
                    domain_commit_id,
                )
                if ref_key not in seen_refs:
                    seen_refs.add(ref_key)
                    refs_by_id[object_instance_graph_commit_id].append(
                        ObjectInstanceGraphCommitRef(
                            branch_id=branch_id,
                            projection_hash=projection,
                            object_instance_graph_commit_id=object_instance_graph_commit_id,
                            domain_commit_id=domain_commit_id,
                            object_instance_graph_identity_id=_json_optional_uuid(
                                payload,
                                "object_instance_graph_identity_id",
                            ),
                            object_instance_graph_id=_json_optional_uuid(
                                payload,
                                "object_instance_graph_id",
                            ),
                            graph_hash_post=_json_optional_string(
                                payload,
                                "graph_hash_post",
                            ),
                        )
                    )

        fallback_requested_ids = frozenset(
            object_instance_graph_commit_id
            for object_instance_graph_commit_id, refs in refs_by_id.items()
            if not refs
        )
        if not fallback_requested_ids or not allow_head_fallback:
            return {key: tuple(value) for key, value in refs_by_id.items()}

        for branch_dir in branch_dirs:
            try:
                branch_id = UUID(branch_dir.name)
            except Exception:
                continue

            head = await self.head(branch_id=branch_id, projection_hash=projection)
            if head is None:
                continue
            head_domain_commit_id = _json_optional_uuid(head, "commit_id")
            head_object_instance_graph_commit_id = _json_optional_uuid(
                head,
                "object_instance_graph_commit_id",
            )
            if (
                head_domain_commit_id is None
                or head_object_instance_graph_commit_id is None
                or head_object_instance_graph_commit_id not in fallback_requested_ids
            ):
                continue
            head_envelope = await self.get_commit_envelope(
                branch_id=branch_id,
                projection_hash=projection,
                commit_id=head_domain_commit_id,
            )
            if head_envelope is None:
                continue
            self._write_object_instance_graph_commit_ref_index_from_envelope(
                branch_id=branch_id,
                projection_hash=projection,
                envelope=head_envelope,
            )
            ref_key = (
                head_object_instance_graph_commit_id,
                branch_id,
                head_domain_commit_id,
            )
            if ref_key in seen_refs:
                continue
            seen_refs.add(ref_key)
            refs_by_id[head_object_instance_graph_commit_id].append(
                ObjectInstanceGraphCommitRef(
                    branch_id=branch_id,
                    projection_hash=projection,
                    object_instance_graph_commit_id=head_object_instance_graph_commit_id,
                    domain_commit_id=head_domain_commit_id,
                    object_instance_graph_identity_id=(
                        head_envelope.object_instance_graph_identity_id
                    ),
                    object_instance_graph_id=head_envelope.object_instance_graph_id,
                    graph_hash_post=head_envelope.graph_hash_post,
                )
            )

        return {key: tuple(value) for key, value in refs_by_id.items()}

    @staticmethod
    def _elapsed_ms(*, started: float, ended: float | None = None) -> int:
        stop = time.monotonic() if ended is None else ended
        return max(int((stop - started) * 1000), 0)

    async def _load_commit_map(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> dict[str, ObjectInstanceGraphCommit]:
        commits_dir = self._commits_dir(branch_id, projection_hash)
        commit_map: dict[str, ObjectInstanceGraphCommit] = {}
        if not commits_dir.exists():
            return commit_map

        for entry in commits_dir.glob("*.json"):
            try:
                data = _SESSION_JSON_FILE_CACHE.read_json_object(
                    entry,
                    error_message=f"Invalid commit JSON object: {entry}",
                )
                with disable_autobind():
                    commit_id = UUID(entry.stem)
                    envelope = _object_instance_graph_commit_envelope_from_payload(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=commit_id,
                        payload=data,
                    )
                    commit = _object_instance_graph_commit_from_envelope(envelope)
                commit_map[str(commit.commit.id)] = commit
            except Exception:
                continue
        return commit_map

    async def iter_lineage_forward(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        head_commit_id: UUID,
        stop_at_commit_id: UUID | None,
    ) -> AsyncIterator[ObjectInstanceGraphCommit]:
        chain: list[ObjectInstanceGraphCommit] = []
        current_commit_id: UUID | None = head_commit_id
        seen_commit_ids: set[UUID] = set()

        while (
            current_commit_id is not None and current_commit_id not in seen_commit_ids
        ):
            seen_commit_ids.add(current_commit_id)
            lookup_commit_id = current_commit_id
            commit = await self.get_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=lookup_commit_id,
            )
            if commit is None:
                domain_commit_id = (
                    await self.domain_commit_id_for_object_instance_graph_commit_id(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        object_instance_graph_commit_id=current_commit_id,
                    )
                )
                if domain_commit_id is not None:
                    lookup_commit_id = domain_commit_id
                    commit = await self.get_commit(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=lookup_commit_id,
                    )
            if commit is None:
                raise ValueError(
                    f"Missing commit file for {current_commit_id} in lane ({branch_id}, {projection_hash})"
                )

            chain.append(commit)
            if stop_at_commit_id is not None and stop_at_commit_id in {
                current_commit_id,
                lookup_commit_id,
            }:
                break

            parents = commit.commit.commit_parents
            if len(parents) > 1:
                raise ValueError(
                    f"Non-linear commit {commit.commit.id} has {len(parents)} parents"
                )
            current_commit_id = parents[0].parent_commit_id if parents else None

        for commit in reversed(chain):
            if stop_at_commit_id is not None and commit.commit.id == stop_at_commit_id:
                continue
            yield commit

    async def iter_lineage_forward_records(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        head_commit_id: UUID,
        stop_at_commit_id: UUID | None,
    ) -> AsyncIterator[ObjectInstanceGraphCommitBodyRecord]:
        chain: list[ObjectInstanceGraphCommitBodyRecord] = []
        current_commit_id: UUID | None = head_commit_id
        seen_commit_ids: set[UUID] = set()

        while (
            current_commit_id is not None and current_commit_id not in seen_commit_ids
        ):
            seen_commit_ids.add(current_commit_id)
            lookup_commit_id = current_commit_id
            record = await self.get_commit_record(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=lookup_commit_id,
            )
            if record is None:
                domain_commit_id = (
                    await self.domain_commit_id_for_object_instance_graph_commit_id(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        object_instance_graph_commit_id=current_commit_id,
                    )
                )
                if domain_commit_id is not None:
                    lookup_commit_id = domain_commit_id
                    record = await self.get_commit_record(
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        commit_id=lookup_commit_id,
                    )
            if record is None:
                raise ValueError(
                    f"Missing commit record for {current_commit_id} in lane ({branch_id}, {projection_hash})"
                )

            chain.append(record)
            if stop_at_commit_id is not None and stop_at_commit_id in {
                current_commit_id,
                lookup_commit_id,
            }:
                break

            parents = record.envelope.parent_commit_ids
            if len(parents) > 1:
                raise ValueError(
                    f"Non-linear commit {record.commit_id} has {len(parents)} parents"
                )
            current_commit_id = parents[0] if parents else None

        for record in reversed(chain):
            if (
                stop_at_commit_id is not None
                and record.envelope.commit_id == stop_at_commit_id
            ):
                continue
            yield record

    async def put_commit_file(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
        commit_action: CommitActionDescriptor | None = None,
    ) -> bool:
        if not commit.graph_hash_post:
            raise ValueError(
                f"put_commit_file requires commit.graph_hash_post (commit_id={commit.commit.id})"
            )
        if commit.projection_hash and commit.projection_hash != projection_hash:
            raise ValueError(
                f"put_commit_file projection_hash mismatch: lane={projection_hash} commit={commit.projection_hash}"
            )
        return await self.put_commit_record(
            branch_id=branch_id,
            projection_hash=projection_hash,
            envelope=object_instance_graph_commit_envelope_from_commit(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit=commit,
            ),
            body=build_oig_commit_body(commit),
            commit_action=commit_action,
        )

    def _repair_head_commit_identity_metadata(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
    ) -> bool:
        head_path = self._lane_dir(branch_id, projection_hash) / "HEAD.json"
        if not head_path.exists():
            return False
        head_payload = _read_json_object(
            head_path,
            error_message=f"Existing HEAD is unreadable: {head_path}",
        )
        head_commit_id = _json_optional_uuid(head_payload, "commit_id")
        if head_commit_id != commit.commit.id:
            return False

        head_graph_hash_post = _json_optional_string(head_payload, "graph_hash_post")
        if head_graph_hash_post and head_graph_hash_post != commit.graph_hash_post:
            raise ValueError(
                "Existing HEAD graph_hash_post differs from commit payload: "
                + f"{commit.commit.id}"
            )
        head_oig_id = _json_optional_uuid(head_payload, "object_instance_graph_id")
        if head_oig_id is not None and head_oig_id != commit.object_instance_graph_id:
            raise ValueError(
                "Existing HEAD object_instance_graph_id differs from commit payload: "
                + f"{commit.commit.id}"
            )

        expected_oig_commit_id = str(_object_instance_graph_commit_ref_id(commit))
        if _json_optional_string(
            head_payload, "object_instance_graph_commit_id"
        ) == expected_oig_commit_id and _json_optional_string(
            head_payload, "object_instance_graph_id"
        ) == str(
            commit.object_instance_graph_id
        ):
            return False

        repaired_payload = dict(head_payload)
        repaired_payload["object_instance_graph_id"] = str(
            commit.object_instance_graph_id
        )
        repaired_payload["object_instance_graph_commit_id"] = expected_oig_commit_id
        repaired_payload["v"] = HEAD_VERSION
        _atomic_write(
            head_path,
            _dump_json(
                _coerce_json_object(
                    repaired_payload,
                    error_message=f"Repaired HEAD did not serialize: {head_path}",
                )
            ),
        )
        _SESSION_JSON_FILE_CACHE.invalidate_path(head_path)
        return True

    async def append(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit: ObjectInstanceGraphCommit,
        root_object_id: UUID | None = None,
        commit_action: CommitActionDescriptor | None = None,
        object_projection_graph_identity_id: UUID | None = None,
    ) -> dict[str, int]:
        return await self.append_record(
            branch_id=branch_id,
            projection_hash=projection_hash,
            record=ObjectInstanceGraphCommitBodyRecord(
                envelope=object_instance_graph_commit_envelope_from_commit(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit=commit,
                ),
                body=build_oig_commit_body(commit),
            ),
            root_object_id=root_object_id,
            commit_action=commit_action,
            object_projection_graph_identity_id=object_projection_graph_identity_id,
        )

    async def append_record(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        record: ObjectInstanceGraphCommitBodyRecord,
        root_object_id: UUID | None = None,
        commit_action: CommitActionDescriptor | None = None,
        object_projection_graph_identity_id: UUID | None = None,
        write_health_index: bool = True,
    ) -> dict[str, int]:
        append_total_started = time.monotonic()
        perf: dict[str, int] = {}
        envelope = record.envelope
        trace_metadata: dict[str, object] = {
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(envelope.commit_id),
            "object_instance_graph_id": str(envelope.object_instance_graph_id),
            "object_instance_graph_identity_id": str(
                envelope.object_instance_graph_identity_id
            ),
        }

        if not envelope.graph_hash_post:
            raise ValueError(
                "Lane append requires envelope.graph_hash_post "
                + f"(commit_id={envelope.commit_id})"
            )
        if envelope.projection_hash and envelope.projection_hash != projection_hash:
            raise ValueError(
                "Lane append projection_hash mismatch: "
                + f"lane={projection_hash} envelope={envelope.projection_hash}"
            )
        if (
            root_object_id is not None
            and root_object_id != envelope.root_source_object_id
        ):
            raise ValueError(
                f"Lane append root_object_id mismatch: explicit={root_object_id} "
                + f"envelope.root_source_object_id={envelope.root_source_object_id}"
            )

        lock_path = self._lane_dir(branch_id, projection_hash) / "locks" / "append.lock"
        lock_wait_started = time.monotonic()
        lock_acquired = 0.0
        lock_released = 0.0

        async with _lane_append_lock(lock_path=lock_path):
            lock_acquired = time.monotonic()
            perf["lock_wait_ms"] = self._elapsed_ms(
                started=lock_wait_started, ended=lock_acquired
            )
            record_commit_perf_elapsed(
                phase="oig_commit_store.append_record.lock_wait",
                started=lock_wait_started,
                ended=lock_acquired,
                category="meta.oig.commit_store",
                metadata=trace_metadata,
            )
            lane_dir = self._lane_dir(branch_id, projection_hash)

            head_read_started = time.monotonic()
            head = await self.head(branch_id=branch_id, projection_hash=projection_hash)
            perf["head_read_ms"] = self._elapsed_ms(started=head_read_started)
            _record_fs_commit_store_elapsed(
                phase="append_record.head_read",
                started=head_read_started,
                metadata=trace_metadata,
            )

            head_commit_id = (
                _json_optional_uuid(head, "commit_id") if head is not None else None
            )
            previous_hash = (
                _json_optional_string(head, "graph_hash_post")
                if head is not None
                else None
            )
            previous_oig_id = (
                _json_optional_string(head, "object_instance_graph_id")
                if head is not None
                else None
            )
            if previous_oig_id is not None and previous_oig_id != str(
                envelope.object_instance_graph_id
            ):
                raise ValueError(
                    f"Lane OIG id mismatch: branch_id={branch_id} "
                    + f"projection_hash={projection_hash} head_object_instance_graph_id={previous_oig_id} "
                    + f"commit_object_instance_graph_id={envelope.object_instance_graph_id}"
                )

            validation_started = time.monotonic()
            parent_ids = envelope.parent_commit_ids
            if len(parent_ids) > 1:
                raise ValueError(
                    f"Non-linear commit {envelope.commit_id} has {len(parent_ids)} parents"
                )
            parent_id = parent_ids[0] if parent_ids else None

            if head_commit_id is None and parent_id is not None:
                raise ValueError(
                    f"First commit {envelope.object_instance_graph_commit_id} must not have a parent"
                )
            if head_commit_id is not None and parent_id != head_commit_id:
                raise ValueError(
                    f"Lane parent mismatch: parent={parent_id} expected={head_commit_id}"
                )
            if (
                previous_hash
                and envelope.graph_hash_pre
                and previous_hash != envelope.graph_hash_pre
            ):
                raise ValueError(
                    f"HEAD mismatch: expected graph_hash_pre={previous_hash}, "
                    + f"got {envelope.graph_hash_pre} for commit {envelope.object_instance_graph_commit_id}"
                )
            perf["validation_ms"] = self._elapsed_ms(started=validation_started)
            _record_fs_commit_store_elapsed(
                phase="append_record.validation",
                started=validation_started,
                metadata=trace_metadata,
            )

            write_commit_started = time.monotonic()
            _ = await self.put_commit_record(
                branch_id=branch_id,
                projection_hash=projection_hash,
                envelope=envelope,
                body=record.body,
                commit_action=commit_action,
                write_health_index=write_health_index,
            )
            perf["write_commit_file_ms"] = self._elapsed_ms(
                started=write_commit_started
            )
            if not write_health_index:
                perf["write_health_index_deferred_count"] = 1
            _record_fs_commit_store_elapsed(
                phase="append_record.put_commit_record",
                started=write_commit_started,
                metadata={
                    **trace_metadata,
                    "write_health_index": write_health_index,
                },
            )
            perf["write_commit_ref_index_ms"] = perf["write_commit_file_ms"]
            perf["write_meta_file_ms"] = (
                0 if commit_action is None else perf["write_commit_file_ms"]
            )

            resolved_root_object_id = (
                envelope.root_source_object_id
                if root_object_id is None
                else root_object_id
            )
            head_payload: JsonObject = {
                "commit_id": str(envelope.commit_id),
                "graph_hash_post": envelope.graph_hash_post,
                "graph_hash_source": envelope.graph_hash_source,
                "object_instance_graph_id": str(envelope.object_instance_graph_id),
                "root_object_id": str(resolved_root_object_id),
                "object_instance_graph_commit_id": str(
                    envelope.object_instance_graph_commit_id
                ),
                "v": HEAD_VERSION,
            }
            write_head_started = time.monotonic()
            head_path = lane_dir / "HEAD.json"
            _atomic_write(head_path, _dump_json(head_payload))
            _SESSION_JSON_FILE_CACHE.invalidate_path(head_path)
            perf["write_head_ms"] = self._elapsed_ms(started=write_head_started)
            _record_fs_commit_store_elapsed(
                phase="append_record.write_head",
                started=write_head_started,
                metadata=trace_metadata,
            )

            receipt = LaneHeadCommitReceipt(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=envelope.commit_id,
                object_instance_graph_commit_id=envelope.object_instance_graph_commit_id,
                created_at_unix_ms=int(envelope.created_at.timestamp() * 1000),
                graph_hash_post=envelope.graph_hash_post,
                object_instance_graph_id=envelope.object_instance_graph_id,
                object_instance_graph_identity_id=envelope.object_instance_graph_identity_id,
                object_instance_graph_branch_id=stable_object_instance_graph_branch_id(
                    object_instance_graph_identity_id=envelope.object_instance_graph_identity_id,
                    branch_id=branch_id,
                ),
                object_projection_graph_id=None,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                root_object_id=resolved_root_object_id,
                author_id=envelope.author_id,
                commit_action=commit_action,
                class_instance_identity_id=(
                    None
                    if commit_action is None
                    else commit_action.class_instance_identity_id
                ),
            )
            watcher_dispatch_started = time.monotonic()
            await self._dispatch_lane_head_watchers(receipt)
            perf["dispatch_watcher_ms"] = self._elapsed_ms(
                started=watcher_dispatch_started
            )
            _record_fs_commit_store_elapsed(
                phase="append_record.dispatch_watchers",
                started=watcher_dispatch_started,
                metadata=trace_metadata,
            )
            lock_released = time.monotonic()

        perf["lock_hold_ms"] = self._elapsed_ms(
            started=lock_acquired, ended=lock_released
        )
        record_commit_perf_elapsed(
            phase="oig_commit_store.append_record.lock_hold",
            started=lock_acquired,
            ended=lock_released,
            category="meta.oig.commit_store",
            metadata=trace_metadata,
        )
        perf["total_ms"] = self._elapsed_ms(started=append_total_started)
        _record_fs_commit_store_elapsed(
            phase="append_record.total",
            started=append_total_started,
            metadata=trace_metadata,
        )
        return perf

    async def append_for_lane(
        self,
        *,
        lane: Lane,
        commit: ObjectInstanceGraphCommit,
        root_object_id: UUID | None = None,
    ) -> None:
        _ = await self.append(
            branch_id=lane.branch_id,
            projection_hash=lane.lane_hash,
            commit=commit,
            root_object_id=root_object_id,
        )
