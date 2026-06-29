from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import TypeAlias, cast
from uuid import UUID

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_delta import (
    ObjectConfigGraphDelta,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

from aware_meta.graph.config.lane.common import OCG_DELTA_HINT_VERSION
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.ocg_delta import build_ocg_delta_from_oig_commit

JsonObject: TypeAlias = dict[str, object]

OCG_MIGRATION_ARTIFACT_CONTRACT_ID = "aware.meta.ocg_migration_artifacts"
OCG_MIGRATION_ARTIFACT_CONTRACT_VERSION = "0"
OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION = (
    f"{OCG_MIGRATION_ARTIFACT_CONTRACT_ID}.v0"
)
OCG_MIGRATION_ARTIFACT_FAMILY = "ocg_migration"
OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY = "aware_meta"
OCG_MIGRATION_ARTIFACT_PRODUCER_KEY = "aware_meta.ocg_migration_artifacts.v0"

ARTIFACT_ROLE_LANE_INDEX = "lane_index"
ARTIFACT_ROLE_OCG_DELTA = "ocg_delta"
ARTIFACT_ROLE_DIALECT_MIGRATION = "dialect_migration"

DEFAULT_DIALECTS: tuple[str, ...] = ("sqlite",)
JSON_MEDIA_TYPE = "application/vnd.aware.meta.ocg-migration+json"
SHA256 = "sha256"


class MetaOcgMigrationArtifactError(ValueError):
    """Raised when a requested OCG migration artifact bundle cannot be honest."""


@dataclass(frozen=True, slots=True)
class MetaOcgMigrationArtifact:
    artifact_family: str
    artifact_role: str
    artifact_key: str
    digest_algorithm: str
    digest: str
    media_type: str
    payload: JsonObject
    path: Path | None = None


@dataclass(frozen=True, slots=True)
class MetaOcgMigrationArtifactBundle:
    status: str
    package_key: str
    object_config_graph_package_id: UUID | None
    object_config_graph_id: UUID
    branch_id: UUID
    projection_hash: str
    head_commit_id: UUID
    artifacts: tuple[MetaOcgMigrationArtifact, ...]
    receipt: JsonObject

    @property
    def lane_index(self) -> MetaOcgMigrationArtifact:
        for artifact in self.artifacts:
            if artifact.artifact_role == ARTIFACT_ROLE_LANE_INDEX:
                return artifact
        raise MetaOcgMigrationArtifactError("OCG migration bundle is missing lane_index artifact")

    def artifacts_by_role(self) -> dict[str, tuple[MetaOcgMigrationArtifact, ...]]:
        grouped: dict[str, list[MetaOcgMigrationArtifact]] = {}
        for artifact in self.artifacts:
            grouped.setdefault(artifact.artifact_role, []).append(artifact)
        return {role: tuple(items) for role, items in grouped.items()}


@dataclass(frozen=True, slots=True)
class _LaneCommit:
    commit: ObjectInstanceGraphCommit
    parent_commit_id: UUID | None


async def build_ocg_migration_artifact_bundle(
    *,
    store: FSCommitStore,
    schema_graph: ObjectConfigGraph,
    package_key: str,
    object_config_graph_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    object_config_graph_package_id: UUID | None = None,
    object_instance_graph_id: UUID | None = None,
    head_commit_id: UUID | None = None,
    dialects: Iterable[str] = DEFAULT_DIALECTS,
    output_root: Path | None = None,
) -> MetaOcgMigrationArtifactBundle:
    """Build honest Meta-owned OCG migration artifacts for a committed lane.

    The producer consumes only Meta lane state: HEAD, commit payloads, optional
    OCG delta hints, and OIG commit content. Workspace publication remains a
    later consumer of these artifacts.
    """

    clean_package_key = _require_text(package_key, "package_key")
    clean_projection_hash = _require_text(projection_hash, "projection_hash")
    clean_dialects = _normalize_dialects(dialects)
    expected_oig_id = object_instance_graph_id or object_config_graph_id

    lane_head = await store.head(
        branch_id=branch_id,
        projection_hash=clean_projection_hash,
    )
    if lane_head is None:
        raise MetaOcgMigrationArtifactError(
            "Cannot build OCG migration artifacts without lane HEAD"
        )

    actual_head_commit_id = _required_uuid(lane_head, "commit_id")
    if head_commit_id is not None and actual_head_commit_id != head_commit_id:
        raise MetaOcgMigrationArtifactError(
            "Requested OCG migration artifact head does not match lane HEAD: "
            + f"requested={head_commit_id} actual={actual_head_commit_id}"
        )

    lane_commits = await _load_linear_lane_commits(
        store=store,
        branch_id=branch_id,
        projection_hash=clean_projection_hash,
        head_commit_id=actual_head_commit_id,
        expected_object_instance_graph_id=expected_oig_id,
        head_payload=lane_head,
    )

    artifacts: list[MetaOcgMigrationArtifact] = []
    commit_index_entries: list[JsonObject] = []
    for lane_commit in lane_commits:
        commit = lane_commit.commit
        commit_id = commit.commit.id
        parent_commit_id = lane_commit.parent_commit_id
        delta, delta_source = _load_or_build_commit_delta(
            store=store,
            schema_graph=schema_graph,
            branch_id=branch_id,
            projection_hash=clean_projection_hash,
            commit=commit,
            object_config_graph_id=object_config_graph_id,
        )
        delta_artifact = _artifact(
            role=ARTIFACT_ROLE_OCG_DELTA,
            key=_artifact_key(
                package_key=clean_package_key,
                object_config_graph_id=object_config_graph_id,
                branch_id=branch_id,
                projection_hash=clean_projection_hash,
                artifact_role=ARTIFACT_ROLE_OCG_DELTA,
                commit_id=commit_id,
            ),
            payload=_delta_artifact_payload(
                package_key=clean_package_key,
                object_config_graph_package_id=object_config_graph_package_id,
                object_config_graph_id=object_config_graph_id,
                source_object_instance_graph_id=expected_oig_id,
                branch_id=branch_id,
                projection_hash=clean_projection_hash,
                commit=commit,
                parent_commit_id=parent_commit_id,
                delta=delta,
                delta_source=delta_source,
            ),
        )
        artifacts.append(delta_artifact)

        dialect_artifact_keys: list[str] = []
        for dialect in clean_dialects:
            dialect_artifact = _artifact(
                role=ARTIFACT_ROLE_DIALECT_MIGRATION,
                key=_artifact_key(
                    package_key=clean_package_key,
                    object_config_graph_id=object_config_graph_id,
                    branch_id=branch_id,
                    projection_hash=clean_projection_hash,
                    artifact_role=ARTIFACT_ROLE_DIALECT_MIGRATION,
                    commit_id=commit_id,
                    dialect=dialect,
                ),
                payload=_dialect_artifact_payload(
                    package_key=clean_package_key,
                    object_config_graph_package_id=object_config_graph_package_id,
                    object_config_graph_id=object_config_graph_id,
                    source_object_instance_graph_id=expected_oig_id,
                    branch_id=branch_id,
                    projection_hash=clean_projection_hash,
                    commit=commit,
                    parent_commit_id=parent_commit_id,
                    dialect=dialect,
                    delta=delta,
                    source_delta_artifact_key=delta_artifact.artifact_key,
                ),
            )
            artifacts.append(dialect_artifact)
            dialect_artifact_keys.append(dialect_artifact.artifact_key)

        commit_index_entries.append(
            {
                "commit_id": str(commit_id),
                "parent_commit_id": None if parent_commit_id is None else str(parent_commit_id),
                "graph_hash_pre": commit.graph_hash_pre,
                "graph_hash_post": commit.graph_hash_post,
                "delta_artifact_key": delta_artifact.artifact_key,
                "delta_digest": delta_artifact.digest,
                "dialect_migration_artifact_keys": dialect_artifact_keys,
            }
        )

    lane_index_artifact = _artifact(
        role=ARTIFACT_ROLE_LANE_INDEX,
        key=_artifact_key(
            package_key=clean_package_key,
            object_config_graph_id=object_config_graph_id,
            branch_id=branch_id,
            projection_hash=clean_projection_hash,
            artifact_role=ARTIFACT_ROLE_LANE_INDEX,
            commit_id=actual_head_commit_id,
        ),
        payload=_lane_index_payload(
            package_key=clean_package_key,
            object_config_graph_package_id=object_config_graph_package_id,
            object_config_graph_id=object_config_graph_id,
            source_object_instance_graph_id=expected_oig_id,
            branch_id=branch_id,
            projection_hash=clean_projection_hash,
            head_commit_id=actual_head_commit_id,
            head_payload=lane_head,
            commit_entries=commit_index_entries,
            dialects=clean_dialects,
        ),
    )
    artifacts.insert(0, lane_index_artifact)

    artifacts_tuple = tuple(
        _write_artifact(output_root=output_root, artifact=artifact)
        for artifact in artifacts
    )
    receipt: JsonObject = {
        "contract_id": OCG_MIGRATION_ARTIFACT_CONTRACT_ID,
        "contract_version": OCG_MIGRATION_ARTIFACT_CONTRACT_VERSION,
        "runtime_contract_version": OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION,
        "producer_provider_key": OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY,
        "producer_key": OCG_MIGRATION_ARTIFACT_PRODUCER_KEY,
        "artifact_family": OCG_MIGRATION_ARTIFACT_FAMILY,
        "package_key": clean_package_key,
        "object_config_graph_package_id": (
            None if object_config_graph_package_id is None else str(object_config_graph_package_id)
        ),
        "object_config_graph_id": str(object_config_graph_id),
        "object_instance_graph_id": str(expected_oig_id),
        "source_object_instance_graph_id": str(expected_oig_id),
        "branch_id": str(branch_id),
        "projection_hash": clean_projection_hash,
        "head_commit_id": str(actual_head_commit_id),
        "lane_index_artifact_key": lane_index_artifact.artifact_key,
        "lane_index_digest": lane_index_artifact.digest,
        "artifact_count": len(artifacts_tuple),
        "commit_count": len(lane_commits),
        "dialects": list(clean_dialects),
        "status": "ocg_migration_artifacts_ready",
    }
    return MetaOcgMigrationArtifactBundle(
        status="ocg_migration_artifacts_ready",
        package_key=clean_package_key,
        object_config_graph_package_id=object_config_graph_package_id,
        object_config_graph_id=object_config_graph_id,
        branch_id=branch_id,
        projection_hash=clean_projection_hash,
        head_commit_id=actual_head_commit_id,
        artifacts=artifacts_tuple,
        receipt=receipt,
    )


async def _load_linear_lane_commits(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    head_commit_id: UUID,
    expected_object_instance_graph_id: UUID,
    head_payload: Mapping[str, object],
) -> tuple[_LaneCommit, ...]:
    current_commit_id: UUID | None = head_commit_id
    seen: set[UUID] = set()
    reversed_commits: list[_LaneCommit] = []

    while current_commit_id is not None:
        if current_commit_id in seen:
            raise MetaOcgMigrationArtifactError(
                f"OCG migration lane contains a commit cycle at {current_commit_id}"
            )
        seen.add(current_commit_id)

        commit = await store.get_commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=current_commit_id,
        )
        if commit is None:
            raise MetaOcgMigrationArtifactError(
                f"OCG migration lane HEAD chain references missing commit {current_commit_id}"
            )

        _validate_commit_identity(
            commit=commit,
            branch_id=branch_id,
            projection_hash=projection_hash,
            expected_object_instance_graph_id=expected_object_instance_graph_id,
        )
        parent_commit_id = _single_parent_commit_id(commit)
        reversed_commits.append(
            _LaneCommit(commit=commit, parent_commit_id=parent_commit_id)
        )
        current_commit_id = parent_commit_id

    lane_commits = tuple(reversed(reversed_commits))
    if not lane_commits:
        raise MetaOcgMigrationArtifactError("OCG migration lane contains no commits")

    for index, lane_commit in enumerate(lane_commits):
        expected_parent = None if index == 0 else lane_commits[index - 1].commit.commit.id
        if lane_commit.parent_commit_id != expected_parent:
            raise MetaOcgMigrationArtifactError(
                "OCG migration lane parent chain is not linear: "
                + f"commit={lane_commit.commit.commit.id} "
                + f"parent={lane_commit.parent_commit_id} expected={expected_parent}"
            )
        if index == 0:
            continue
        previous = lane_commits[index - 1].commit
        current = lane_commit.commit
        if previous.graph_hash_post and current.graph_hash_pre:
            if previous.graph_hash_post != current.graph_hash_pre:
                raise MetaOcgMigrationArtifactError(
                    "OCG migration lane graph hash continuity mismatch: "
                    + f"commit={current.commit.id} "
                    + f"graph_hash_pre={current.graph_hash_pre} "
                    + f"expected={previous.graph_hash_post}"
                )

    head_graph_hash_post = head_payload.get("graph_hash_post")
    if (
        isinstance(head_graph_hash_post, str)
        and head_graph_hash_post
        and head_graph_hash_post != lane_commits[-1].commit.graph_hash_post
    ):
        raise MetaOcgMigrationArtifactError(
            "OCG migration lane HEAD graph_hash_post does not match head commit"
        )
    return lane_commits


def _load_or_build_commit_delta(
    *,
    store: FSCommitStore,
    schema_graph: ObjectConfigGraph,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
    object_config_graph_id: UUID,
) -> tuple[ObjectConfigGraphDelta, str]:
    hint = _load_commit_delta_hint(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    if hint is not None:
        delta = hint
        delta_source = "hint"
    else:
        delta = build_ocg_delta_from_oig_commit(commit=commit, schema_graph=schema_graph)
        delta_source = "oig_commit"

    if delta.object_config_graph_id != object_config_graph_id:
        raise MetaOcgMigrationArtifactError(
            "OCG migration delta object_config_graph_id mismatch: "
            + f"delta={delta.object_config_graph_id} expected={object_config_graph_id}"
        )

    delta = _ensure_delta_hashes_match_commit(delta=delta, commit=commit)
    return delta, delta_source


def _load_commit_delta_hint(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
) -> ObjectConfigGraphDelta | None:
    commit_id = commit.commit.id
    hint_path = store.ocg_delta_hint_path(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    if not hint_path.exists():
        return None
    try:
        raw = json.loads(hint_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise MetaOcgMigrationArtifactError(
            f"OCG migration delta hint is unreadable: {hint_path}"
        ) from exc
    if not isinstance(raw, dict):
        raise MetaOcgMigrationArtifactError(
            f"OCG migration delta hint must be a JSON object: {hint_path}"
        )

    hint = cast(Mapping[str, object], raw)
    if hint.get("v") != OCG_DELTA_HINT_VERSION:
        raise MetaOcgMigrationArtifactError(
            f"OCG migration delta hint version mismatch: {hint_path}"
        )
    if hint.get("branch_id") != str(branch_id):
        raise MetaOcgMigrationArtifactError(
            f"OCG migration delta hint branch_id mismatch: {hint_path}"
        )
    if hint.get("projection_hash") != projection_hash:
        raise MetaOcgMigrationArtifactError(
            f"OCG migration delta hint projection_hash mismatch: {hint_path}"
        )
    if hint.get("commit_id") != str(commit_id):
        raise MetaOcgMigrationArtifactError(
            f"OCG migration delta hint commit_id mismatch: {hint_path}"
        )

    delta_payload = hint.get("ocg_delta")
    if not isinstance(delta_payload, dict):
        raise MetaOcgMigrationArtifactError(
            f"OCG migration delta hint missing ocg_delta object: {hint_path}"
        )
    try:
        return ObjectConfigGraphDelta.model_validate(delta_payload)
    except Exception as exc:
        raise MetaOcgMigrationArtifactError(
            f"OCG migration delta hint has invalid ocg_delta: {hint_path}"
        ) from exc


def _ensure_delta_hashes_match_commit(
    *,
    delta: ObjectConfigGraphDelta,
    commit: ObjectInstanceGraphCommit,
) -> ObjectConfigGraphDelta:
    updates: dict[str, object] = {}
    if delta.graph_hash_pre is None:
        updates["graph_hash_pre"] = commit.graph_hash_pre
    elif commit.graph_hash_pre and delta.graph_hash_pre != commit.graph_hash_pre:
        raise MetaOcgMigrationArtifactError(
            "OCG migration delta graph_hash_pre does not match commit"
        )

    if delta.graph_hash_post is None:
        updates["graph_hash_post"] = commit.graph_hash_post
    elif commit.graph_hash_post and delta.graph_hash_post != commit.graph_hash_post:
        raise MetaOcgMigrationArtifactError(
            "OCG migration delta graph_hash_post does not match commit"
        )

    if updates:
        return delta.model_copy(update=updates)
    return delta


def _validate_commit_identity(
    *,
    commit: ObjectInstanceGraphCommit,
    branch_id: UUID,
    projection_hash: str,
    expected_object_instance_graph_id: UUID,
) -> None:
    del branch_id
    if commit.projection_hash and commit.projection_hash != projection_hash:
        raise MetaOcgMigrationArtifactError(
            "OCG migration lane commit projection_hash mismatch: "
            + f"commit={commit.commit.id} commit_projection={commit.projection_hash} "
            + f"lane_projection={projection_hash}"
        )
    if commit.object_instance_graph_id != expected_object_instance_graph_id:
        raise MetaOcgMigrationArtifactError(
            "OCG migration lane commit object_instance_graph_id mismatch: "
            + f"commit={commit.commit.id} oig={commit.object_instance_graph_id} "
            + f"expected={expected_object_instance_graph_id}"
        )
    if not commit.graph_hash_post:
        raise MetaOcgMigrationArtifactError(
            f"OCG migration lane commit {commit.commit.id} is missing graph_hash_post"
        )


def _single_parent_commit_id(commit: ObjectInstanceGraphCommit) -> UUID | None:
    parents = commit.commit.commit_parents
    if len(parents) > 1:
        raise MetaOcgMigrationArtifactError(
            f"OCG migration lane commit {commit.commit.id} has {len(parents)} parents"
        )
    return None if not parents else parents[0].parent_commit_id


def _lane_index_payload(
    *,
    package_key: str,
    object_config_graph_package_id: UUID | None,
    object_config_graph_id: UUID,
    source_object_instance_graph_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    head_commit_id: UUID,
    head_payload: Mapping[str, object],
    commit_entries: Iterable[JsonObject],
    dialects: Iterable[str],
) -> JsonObject:
    return {
        "contract_id": OCG_MIGRATION_ARTIFACT_CONTRACT_ID,
        "contract_version": OCG_MIGRATION_ARTIFACT_CONTRACT_VERSION,
        "runtime_contract_version": OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION,
        "artifact_family": OCG_MIGRATION_ARTIFACT_FAMILY,
        "artifact_role": ARTIFACT_ROLE_LANE_INDEX,
        "producer_provider_key": OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY,
        "producer_key": OCG_MIGRATION_ARTIFACT_PRODUCER_KEY,
        "package_key": package_key,
        "object_config_graph_package_id": (
            None if object_config_graph_package_id is None else str(object_config_graph_package_id)
        ),
        "object_config_graph_id": str(object_config_graph_id),
        "source_object_instance_graph_id": str(source_object_instance_graph_id),
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "head_commit_id": str(head_commit_id),
        "head_graph_hash_post": head_payload.get("graph_hash_post"),
        "dialects": list(dialects),
        "commits": list(commit_entries),
    }


def _delta_artifact_payload(
    *,
    package_key: str,
    object_config_graph_package_id: UUID | None,
    object_config_graph_id: UUID,
    source_object_instance_graph_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
    parent_commit_id: UUID | None,
    delta: ObjectConfigGraphDelta,
    delta_source: str,
) -> JsonObject:
    return {
        "contract_id": OCG_MIGRATION_ARTIFACT_CONTRACT_ID,
        "contract_version": OCG_MIGRATION_ARTIFACT_CONTRACT_VERSION,
        "artifact_family": OCG_MIGRATION_ARTIFACT_FAMILY,
        "artifact_role": ARTIFACT_ROLE_OCG_DELTA,
        "producer_key": OCG_MIGRATION_ARTIFACT_PRODUCER_KEY,
        "package_key": package_key,
        "object_config_graph_package_id": (
            None if object_config_graph_package_id is None else str(object_config_graph_package_id)
        ),
        "object_config_graph_id": str(object_config_graph_id),
        "source_object_instance_graph_id": str(source_object_instance_graph_id),
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "commit_id": str(commit.commit.id),
        "parent_commit_id": None if parent_commit_id is None else str(parent_commit_id),
        "graph_hash_pre": commit.graph_hash_pre,
        "graph_hash_post": commit.graph_hash_post,
        "delta_source": delta_source,
        "object_config_graph_delta": cast(
            object,
            delta.model_dump(mode="json", exclude_none=True, by_alias=True),
        ),
    }


def _dialect_artifact_payload(
    *,
    package_key: str,
    object_config_graph_package_id: UUID | None,
    object_config_graph_id: UUID,
    source_object_instance_graph_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
    parent_commit_id: UUID | None,
    dialect: str,
    delta: ObjectConfigGraphDelta,
    source_delta_artifact_key: str,
) -> JsonObject:
    node_delta_count = len(delta.node_deltas)
    migration_kind = "noop" if node_delta_count == 0 else "unsupported_failfast"
    payload: JsonObject = {
        "contract_id": OCG_MIGRATION_ARTIFACT_CONTRACT_ID,
        "contract_version": OCG_MIGRATION_ARTIFACT_CONTRACT_VERSION,
        "artifact_family": OCG_MIGRATION_ARTIFACT_FAMILY,
        "artifact_role": ARTIFACT_ROLE_DIALECT_MIGRATION,
        "producer_key": OCG_MIGRATION_ARTIFACT_PRODUCER_KEY,
        "package_key": package_key,
        "object_config_graph_package_id": (
            None if object_config_graph_package_id is None else str(object_config_graph_package_id)
        ),
        "object_config_graph_id": str(object_config_graph_id),
        "source_object_instance_graph_id": str(source_object_instance_graph_id),
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "commit_id": str(commit.commit.id),
        "parent_commit_id": None if parent_commit_id is None else str(parent_commit_id),
        "dialect": dialect,
        "migration_kind": migration_kind,
        "graph_hash_pre": commit.graph_hash_pre,
        "graph_hash_post": commit.graph_hash_post,
        "source_delta_artifact_key": source_delta_artifact_key,
        "node_delta_count": node_delta_count,
    }
    if migration_kind == "unsupported_failfast":
        payload["unsupported_reason"] = (
            "Dialect migration compilation is intentionally not implemented in "
            "Meta OCG migration artifact producer v0."
        )
    return payload


def _artifact(*, role: str, key: str, payload: JsonObject) -> MetaOcgMigrationArtifact:
    return MetaOcgMigrationArtifact(
        artifact_family=OCG_MIGRATION_ARTIFACT_FAMILY,
        artifact_role=role,
        artifact_key=key,
        digest_algorithm=SHA256,
        digest=_sha256_json(payload),
        media_type=JSON_MEDIA_TYPE,
        payload=payload,
    )


def _write_artifact(
    *,
    output_root: Path | None,
    artifact: MetaOcgMigrationArtifact,
) -> MetaOcgMigrationArtifact:
    if output_root is None:
        return artifact
    relative_path = _artifact_relative_path(artifact)
    target = output_root / relative_path
    _atomic_write_text(target, _canonical_json(artifact.payload) + "\n")
    return MetaOcgMigrationArtifact(
        artifact_family=artifact.artifact_family,
        artifact_role=artifact.artifact_role,
        artifact_key=artifact.artifact_key,
        digest_algorithm=artifact.digest_algorithm,
        digest=artifact.digest,
        media_type=artifact.media_type,
        payload=artifact.payload,
        path=target,
    )


def _artifact_relative_path(artifact: MetaOcgMigrationArtifact) -> Path:
    parts = [_safe_path_part(part) for part in artifact.artifact_key.split("/") if part]
    if not parts:
        raise MetaOcgMigrationArtifactError("OCG migration artifact key cannot be empty")
    return Path(*parts).with_suffix(".json")


def _artifact_key(
    *,
    package_key: str,
    object_config_graph_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    artifact_role: str,
    commit_id: UUID,
    dialect: str | None = None,
) -> str:
    parts = [
        package_key,
        str(object_config_graph_id),
        str(branch_id),
        projection_hash,
        artifact_role,
        str(commit_id),
    ]
    if dialect is not None:
        parts.append(dialect)
    return "/".join(parts)


def _required_uuid(payload: Mapping[str, object], key: str) -> UUID:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MetaOcgMigrationArtifactError(f"OCG migration lane HEAD missing {key}")
    try:
        return UUID(value)
    except Exception as exc:
        raise MetaOcgMigrationArtifactError(
            f"OCG migration lane HEAD has invalid {key}: {value}"
        ) from exc


def _require_text(value: str, name: str) -> str:
    clean = value.strip()
    if not clean:
        raise MetaOcgMigrationArtifactError(f"{name} is required")
    return clean


def _normalize_dialects(dialects: Iterable[str]) -> tuple[str, ...]:
    clean = tuple(dict.fromkeys(_require_text(dialect, "dialect") for dialect in dialects))
    if not clean:
        raise MetaOcgMigrationArtifactError("At least one migration dialect is required")
    return clean


def _sha256_json(payload: JsonObject) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_json(payload: JsonObject) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _safe_path_part(value: str) -> str:
    return (
        value.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace(" ", "_")
    )


def _atomic_write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as file_handle:
        _ = file_handle.write(data)
        file_handle.flush()
    _ = tmp.replace(path)


__all__ = [
    "ARTIFACT_ROLE_DIALECT_MIGRATION",
    "ARTIFACT_ROLE_LANE_INDEX",
    "ARTIFACT_ROLE_OCG_DELTA",
    "DEFAULT_DIALECTS",
    "MetaOcgMigrationArtifact",
    "MetaOcgMigrationArtifactBundle",
    "MetaOcgMigrationArtifactError",
    "OCG_MIGRATION_ARTIFACT_CONTRACT_ID",
    "OCG_MIGRATION_ARTIFACT_CONTRACT_VERSION",
    "OCG_MIGRATION_ARTIFACT_FAMILY",
    "OCG_MIGRATION_ARTIFACT_PRODUCER_KEY",
    "OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY",
    "OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION",
    "build_ocg_migration_artifact_bundle",
]
