from __future__ import annotations

from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.commit.commit_parent import CommitParent
from aware_history_ontology.stable_ids import stable_commit_parent_id
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id

from aware_meta.graph.instance.commit.body_codec import (
    OIG_COMMIT_BODY_CONTRACT,
    OIG_COMMIT_BODY_MEDIA_TYPE,
    ObjectInstanceGraphCommitBodyV1,
)
from aware_meta.graph.instance.commit.contract import (
    CommitActionDescriptor,
    JsonObject,
    ObjectInstanceGraphCommitEnvelope,
    ObjectInstanceGraphCommitIdentitySidecar,
    OigiHistoryDomainCommitProjection,
)
from aware_meta.graph.instance.commit.fs_backend import (
    _coerce_json_object,
)
from aware_meta.graph.instance.commit.json_payload import (
    _datetime_json_value,
    _enum_json_value,
    _json_graph_hash_source,
    _json_mapping,
    _json_optional_int,
    _json_optional_string,
    _json_required_datetime,
    _json_required_string,
    _json_required_uuid,
)


COMMIT_META_VERSION = 1
OBJECT_INSTANCE_GRAPH_COMMIT_REF_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_COMMIT_ENVELOPE_INDEX_VERSION = 2
OBJECT_INSTANCE_GRAPH_COMMIT_IDENTITY_SIDECAR_INDEX_VERSION = 1
OBJECT_INSTANCE_GRAPH_COMMIT_STORED_ENVELOPE_VERSION = (
    OBJECT_INSTANCE_GRAPH_COMMIT_ENVELOPE_INDEX_VERSION
)
OIGI_HISTORY_DOMAIN_COMMIT_PROJECTION_INDEX_VERSION = 1


def _commit_payload(commit: ObjectInstanceGraphCommit) -> JsonObject:
    return _coerce_json_object(
        commit.model_dump(mode="json", exclude_none=True),
        error_message=f"Commit {commit.commit.id} did not serialize to a JSON object",
    )


def _object_instance_graph_commit_ref_id(commit: ObjectInstanceGraphCommit) -> UUID:
    return stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )


def _object_instance_graph_commit_ref_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
) -> JsonObject:
    object_instance_graph_commit_id = _object_instance_graph_commit_ref_id(commit)
    return {
        "v": OBJECT_INSTANCE_GRAPH_COMMIT_REF_INDEX_VERSION,
        "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
        "domain_commit_id": str(commit.commit.id),
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "object_instance_graph_identity_id": str(
            commit.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(commit.object_instance_graph_id),
        "graph_hash_post": commit.graph_hash_post,
        "graph_hash_source": "state_hash",
    }


def _object_instance_graph_commit_ref_payload_from_envelope(
    *,
    branch_id: UUID,
    projection_hash: str,
    envelope: ObjectInstanceGraphCommitEnvelope,
) -> JsonObject:
    return {
        "v": OBJECT_INSTANCE_GRAPH_COMMIT_REF_INDEX_VERSION,
        "object_instance_graph_commit_id": str(
            envelope.object_instance_graph_commit_id
        ),
        "domain_commit_id": str(envelope.commit_id),
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "object_instance_graph_identity_id": str(
            envelope.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(envelope.object_instance_graph_id),
        "graph_hash_post": envelope.graph_hash_post,
        "graph_hash_source": envelope.graph_hash_source,
    }


def object_instance_graph_commit_envelope_from_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
) -> ObjectInstanceGraphCommitEnvelope:
    return ObjectInstanceGraphCommitEnvelope(
        commit_id=commit.commit.id,
        lane_id=commit.commit.lane_id,
        key=commit.commit.key,
        author_id=commit.commit.author_id,
        created_at=commit.commit.created_at,
        status=_enum_json_value(commit.commit.status),
        parent_commit_ids=tuple(
            parent.parent_commit_id for parent in commit.commit.commit_parents
        ),
        object_instance_graph_commit_id=_object_instance_graph_commit_ref_id(commit),
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        object_instance_graph_id=commit.object_instance_graph_id,
        object_instance_graph_key=commit.object_instance_graph_key,
        object_instance_graph_name=commit.object_instance_graph_name,
        object_instance_graph_description=commit.object_instance_graph_description,
        root_class_config_id=commit.root_class_config_id,
        root_source_object_id=commit.root_source_object_id,
        graph_hash_pre=commit.graph_hash_pre,
        graph_hash_post=commit.graph_hash_post,
        projection_hash=commit.projection_hash or projection_hash,
        source_language=_enum_json_value(commit.source_language),
    )


def _object_instance_graph_commit_envelope_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit: ObjectInstanceGraphCommit,
    body: ObjectInstanceGraphCommitBodyV1 | None = None,
    body_ref: str | None = None,
) -> JsonObject:
    envelope = object_instance_graph_commit_envelope_from_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    payload: JsonObject = {
        "v": OBJECT_INSTANCE_GRAPH_COMMIT_STORED_ENVELOPE_VERSION,
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "commit_id": str(envelope.commit_id),
        "lane_id": str(envelope.lane_id),
        "key": envelope.key,
        "author_id": str(envelope.author_id),
        "created_at": _datetime_json_value(envelope.created_at),
        "status": envelope.status,
        "parent_commit_ids": [
            str(parent_id) for parent_id in envelope.parent_commit_ids
        ],
        "object_instance_graph_commit_id": str(
            envelope.object_instance_graph_commit_id
        ),
        "object_instance_graph_identity_id": str(
            envelope.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(envelope.object_instance_graph_id),
        "object_instance_graph_key": envelope.object_instance_graph_key,
        "object_instance_graph_name": envelope.object_instance_graph_name,
        "root_class_config_id": str(envelope.root_class_config_id),
        "root_source_object_id": str(envelope.root_source_object_id),
        "graph_hash_pre": envelope.graph_hash_pre,
        "graph_hash_post": envelope.graph_hash_post,
        "graph_hash_source": envelope.graph_hash_source,
        "source_language": envelope.source_language,
    }
    if body is not None:
        payload["body_contract"] = OIG_COMMIT_BODY_CONTRACT
        payload["body_media_type"] = OIG_COMMIT_BODY_MEDIA_TYPE
        payload["body_ref"] = body_ref or f"{envelope.commit_id}.body.json"
        payload["body_sha256"] = body.sha256
        payload["body_size_bytes"] = len(body.canonical_bytes)
    if envelope.object_instance_graph_description is not None:
        payload["object_instance_graph_description"] = (
            envelope.object_instance_graph_description
        )
    if envelope.projection_hash is not None:
        payload["commit_projection_hash"] = envelope.projection_hash
    return payload


def _object_instance_graph_commit_envelope_payload_from_envelope(
    *,
    branch_id: UUID,
    projection_hash: str,
    envelope: ObjectInstanceGraphCommitEnvelope,
    body: ObjectInstanceGraphCommitBodyV1 | None = None,
    body_ref: str | None = None,
) -> JsonObject:
    payload: JsonObject = {
        "v": OBJECT_INSTANCE_GRAPH_COMMIT_STORED_ENVELOPE_VERSION,
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "commit_id": str(envelope.commit_id),
        "lane_id": str(envelope.lane_id),
        "key": envelope.key,
        "author_id": str(envelope.author_id),
        "created_at": _datetime_json_value(envelope.created_at),
        "status": envelope.status,
        "parent_commit_ids": [
            str(parent_id) for parent_id in envelope.parent_commit_ids
        ],
        "object_instance_graph_commit_id": str(
            envelope.object_instance_graph_commit_id
        ),
        "object_instance_graph_identity_id": str(
            envelope.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(envelope.object_instance_graph_id),
        "object_instance_graph_key": envelope.object_instance_graph_key,
        "object_instance_graph_name": envelope.object_instance_graph_name,
        "root_class_config_id": str(envelope.root_class_config_id),
        "root_source_object_id": str(envelope.root_source_object_id),
        "graph_hash_pre": envelope.graph_hash_pre,
        "graph_hash_post": envelope.graph_hash_post,
        "graph_hash_source": envelope.graph_hash_source,
        "source_language": envelope.source_language,
    }
    if envelope.object_instance_graph_description is not None:
        payload["object_instance_graph_description"] = (
            envelope.object_instance_graph_description
        )
    if envelope.projection_hash is not None:
        payload["commit_projection_hash"] = envelope.projection_hash
    resolved_body_contract = (
        body.payload.get("c") if body is not None else envelope.body_contract
    )
    if resolved_body_contract is not None:
        payload["body_contract"] = str(resolved_body_contract)
    resolved_body_media_type = (
        OIG_COMMIT_BODY_MEDIA_TYPE if body is not None else envelope.body_media_type
    )
    if resolved_body_media_type is not None:
        payload["body_media_type"] = str(resolved_body_media_type)
    resolved_body_ref = body_ref or envelope.body_ref
    if resolved_body_ref is not None:
        payload["body_ref"] = str(resolved_body_ref)
    resolved_body_sha256 = body.sha256 if body is not None else envelope.body_sha256
    if resolved_body_sha256 is not None:
        payload["body_sha256"] = str(resolved_body_sha256)
    resolved_body_size_bytes = (
        len(body.canonical_bytes) if body is not None else envelope.body_size_bytes
    )
    if resolved_body_size_bytes is not None:
        payload["body_size_bytes"] = int(resolved_body_size_bytes)
    return payload


def _object_instance_graph_commit_from_envelope(
    envelope: ObjectInstanceGraphCommitEnvelope,
) -> ObjectInstanceGraphCommit:
    commit_id = envelope.commit_id
    commit_parents = [
        CommitParent(
            id=stable_commit_parent_id(
                commit_id=commit_id,
                parent_commit_id=parent_commit_id,
            ),
            commit_id=commit_id,
            parent_commit_id=parent_commit_id,
        )
        for parent_commit_id in envelope.parent_commit_ids
    ]
    commit = Commit(
        id=commit_id,
        lane_id=envelope.lane_id,
        key=envelope.key,
        author_id=envelope.author_id,
        created_at=envelope.created_at,
        status=CommitStatus(envelope.status),
        commit_parents=commit_parents,
    )
    return ObjectInstanceGraphCommit(
        id=envelope.object_instance_graph_commit_id,
        commit=commit,
        commit_id=commit_id,
        object_instance_graph_identity_id=envelope.object_instance_graph_identity_id,
        object_instance_graph_id=envelope.object_instance_graph_id,
        object_instance_graph_key=envelope.object_instance_graph_key,
        object_instance_graph_name=envelope.object_instance_graph_name,
        object_instance_graph_description=(envelope.object_instance_graph_description),
        root_class_config_id=envelope.root_class_config_id,
        root_source_object_id=envelope.root_source_object_id,
        graph_hash_pre=envelope.graph_hash_pre,
        graph_hash_post=envelope.graph_hash_post,
        projection_hash=envelope.projection_hash,
        source_language=CodeLanguage(envelope.source_language),
    )


def _object_instance_graph_commit_envelope_from_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    payload: JsonObject,
) -> ObjectInstanceGraphCommitEnvelope:
    if payload.get("branch_id") != str(branch_id):
        raise ValueError(f"OIG commit envelope branch mismatch: {commit_id}")
    if payload.get("projection_hash") != projection_hash:
        raise ValueError(f"OIG commit envelope projection mismatch: {commit_id}")
    if payload.get("commit_id") != str(commit_id):
        raise ValueError(f"OIG commit envelope id mismatch: {commit_id}")
    parent_values = payload.get("parent_commit_ids")
    if not isinstance(parent_values, list):
        raise ValueError(f"OIG commit envelope parent list missing: {commit_id}")
    parent_commit_ids = tuple(UUID(str(parent_id)) for parent_id in parent_values)
    return ObjectInstanceGraphCommitEnvelope(
        commit_id=commit_id,
        lane_id=_json_required_uuid(payload, "lane_id"),
        key=_json_required_string(payload, "key"),
        author_id=_json_required_uuid(payload, "author_id"),
        created_at=_json_required_datetime(payload, "created_at"),
        status=_json_required_string(payload, "status"),
        parent_commit_ids=parent_commit_ids,
        object_instance_graph_commit_id=_json_required_uuid(
            payload,
            "object_instance_graph_commit_id",
        ),
        object_instance_graph_identity_id=_json_required_uuid(
            payload,
            "object_instance_graph_identity_id",
        ),
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        object_instance_graph_key=_json_required_string(
            payload,
            "object_instance_graph_key",
        ),
        object_instance_graph_name=_json_required_string(
            payload,
            "object_instance_graph_name",
        ),
        object_instance_graph_description=_json_optional_string(
            payload,
            "object_instance_graph_description",
        ),
        root_class_config_id=_json_required_uuid(payload, "root_class_config_id"),
        root_source_object_id=_json_required_uuid(payload, "root_source_object_id"),
        graph_hash_pre=_json_required_string(payload, "graph_hash_pre"),
        graph_hash_post=_json_required_string(payload, "graph_hash_post"),
        graph_hash_source=_json_graph_hash_source(payload),
        projection_hash=_json_optional_string(payload, "commit_projection_hash"),
        source_language=_json_required_string(payload, "source_language"),
        body_contract=_json_optional_string(payload, "body_contract"),
        body_media_type=_json_optional_string(payload, "body_media_type"),
        body_ref=_json_optional_string(payload, "body_ref"),
        body_sha256=_json_optional_string(payload, "body_sha256"),
        body_size_bytes=_json_optional_int(payload, "body_size_bytes"),
    )


def _object_instance_graph_commit_envelope_from_commit_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    payload: JsonObject,
) -> ObjectInstanceGraphCommitEnvelope:
    commit_payload = _json_mapping(payload, "commit")
    if _json_required_uuid(commit_payload, "id") != commit_id:
        raise ValueError(f"OIG commit payload id mismatch: {commit_id}")
    parent_values = commit_payload.get("commit_parents") or []
    if not isinstance(parent_values, list):
        raise ValueError(f"OIG commit parent list missing: {commit_id}")
    parent_commit_ids: list[UUID] = []
    for parent_value in parent_values:
        if not isinstance(parent_value, dict):
            raise ValueError(f"Invalid OIG commit parent payload: {commit_id}")
        parent_payload = _coerce_json_object(
            parent_value,
            error_message=f"Invalid OIG commit parent payload: {commit_id}",
        )
        parent_commit_ids.append(
            _json_required_uuid(parent_payload, "parent_commit_id")
        )
    oigi_id = _json_required_uuid(payload, "object_instance_graph_identity_id")
    return ObjectInstanceGraphCommitEnvelope(
        commit_id=commit_id,
        lane_id=_json_required_uuid(commit_payload, "lane_id"),
        key=_json_required_string(commit_payload, "key"),
        author_id=_json_required_uuid(commit_payload, "author_id"),
        created_at=_json_required_datetime(commit_payload, "created_at"),
        status=_json_required_string(commit_payload, "status"),
        parent_commit_ids=tuple(parent_commit_ids),
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=oigi_id,
            commit_id=commit_id,
        ),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        object_instance_graph_key=_json_required_string(
            payload,
            "object_instance_graph_key",
        ),
        object_instance_graph_name=_json_required_string(
            payload,
            "object_instance_graph_name",
        ),
        object_instance_graph_description=_json_optional_string(
            payload,
            "object_instance_graph_description",
        ),
        root_class_config_id=_json_required_uuid(payload, "root_class_config_id"),
        root_source_object_id=_json_required_uuid(payload, "root_source_object_id"),
        graph_hash_pre=_json_required_string(payload, "graph_hash_pre"),
        graph_hash_post=_json_required_string(payload, "graph_hash_post"),
        graph_hash_source=_json_graph_hash_source(payload),
        projection_hash=_json_optional_string(payload, "projection_hash")
        or projection_hash,
        source_language=_json_required_string(payload, "source_language"),
    )


def _commit_parent_ids_from_commit_payload(
    *,
    commit_id: UUID,
    commit_payload: JsonObject,
) -> tuple[UUID, ...]:
    parent_values = commit_payload.get("commit_parents") or []
    if not isinstance(parent_values, list):
        raise ValueError(f"OIG commit parent list missing: {commit_id}")
    parent_commit_ids: list[UUID] = []
    for parent_value in parent_values:
        if not isinstance(parent_value, dict):
            raise ValueError(f"Invalid OIG commit parent payload: {commit_id}")
        parent_payload = _coerce_json_object(
            parent_value,
            error_message=f"Invalid OIG commit parent payload: {commit_id}",
        )
        parent_commit_ids.append(
            _json_required_uuid(parent_payload, "parent_commit_id")
        )
    return tuple(parent_commit_ids)


def _commit_class_instance_ids_from_payload(
    *,
    commit_id: UUID,
    payload: JsonObject,
) -> tuple[UUID, ...]:
    root_change_values = payload.get("object_instance_graph_changes") or []
    if not isinstance(root_change_values, list):
        raise ValueError(f"OIG commit change list missing: {commit_id}")
    class_instance_ids: set[UUID] = set()
    for root_change_value in root_change_values:
        if not isinstance(root_change_value, dict):
            raise ValueError(f"Invalid OIG root change payload: {commit_id}")
        root_change_payload = _coerce_json_object(
            root_change_value,
            error_message=f"Invalid OIG root change payload: {commit_id}",
        )
        class_change_values = root_change_payload.get("class_instance_changes") or []
        if not isinstance(class_change_values, list):
            raise ValueError(f"Invalid OIG class change list: {commit_id}")
        for class_change_value in class_change_values:
            if not isinstance(class_change_value, dict):
                raise ValueError(f"Invalid OIG class change payload: {commit_id}")
            class_change_payload = _coerce_json_object(
                class_change_value,
                error_message=f"Invalid OIG class change payload: {commit_id}",
            )
            class_instance_ids.add(
                _json_required_uuid(class_change_payload, "class_instance_id")
            )
    return tuple(sorted(class_instance_ids, key=str))


def _commit_class_instance_ids_from_commit(
    commit: ObjectInstanceGraphCommit,
) -> tuple[UUID, ...]:
    class_instance_ids: set[UUID] = set()
    for root_change in commit.object_instance_graph_changes:
        for class_change in root_change.class_instance_changes:
            class_instance_id = class_change.class_instance_id
            if isinstance(class_instance_id, UUID):
                class_instance_ids.add(class_instance_id)
    return tuple(sorted(class_instance_ids, key=str))


def _commit_class_instance_ids_from_body(
    body: ObjectInstanceGraphCommitBodyV1,
) -> tuple[UUID, ...]:
    roots = body.payload.get("r") or []
    if not isinstance(roots, list):
        raise ValueError(f"OIG commit body root list missing: {body.commit_id}")
    class_instance_ids: set[UUID] = set()
    for root_value in roots:
        if not isinstance(root_value, dict):
            raise ValueError(f"Invalid OIG body root payload: {body.commit_id}")
        root_payload = _coerce_json_object(
            root_value,
            error_message=f"Invalid OIG body root payload: {body.commit_id}",
        )
        class_change_values = root_payload.get("ci") or []
        if not isinstance(class_change_values, list):
            raise ValueError(f"Invalid OIG body class change list: {body.commit_id}")
        for class_change_value in class_change_values:
            if not isinstance(class_change_value, dict):
                raise ValueError(
                    f"Invalid OIG body class change payload: {body.commit_id}"
                )
            class_change_payload = _coerce_json_object(
                class_change_value,
                error_message=f"Invalid OIG body class change payload: {body.commit_id}",
            )
            class_instance_ids.add(_json_required_uuid(class_change_payload, "ci"))
    return tuple(sorted(class_instance_ids, key=str))


def _object_instance_graph_commit_identity_sidecar_payload_from_sidecar(
    *,
    branch_id: UUID,
    projection_hash: str,
    sidecar: ObjectInstanceGraphCommitIdentitySidecar,
    file_size: int,
    file_mtime_ns: int,
    file_ctime_ns: int,
) -> JsonObject:
    return {
        "v": OBJECT_INSTANCE_GRAPH_COMMIT_IDENTITY_SIDECAR_INDEX_VERSION,
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "commit_id": str(sidecar.commit_id),
        "object_instance_graph_identity_id": str(
            sidecar.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(sidecar.object_instance_graph_id),
        "parent_commit_ids": [
            str(parent_id) for parent_id in sidecar.parent_commit_ids
        ],
        "class_instance_ids": [
            str(class_instance_id) for class_instance_id in sidecar.class_instance_ids
        ],
        "file_size": file_size,
        "file_mtime_ns": file_mtime_ns,
        "file_ctime_ns": file_ctime_ns,
    }


def _object_instance_graph_commit_identity_sidecar_from_commit(
    *,
    commit: ObjectInstanceGraphCommit,
) -> ObjectInstanceGraphCommitIdentitySidecar:
    return ObjectInstanceGraphCommitIdentitySidecar(
        commit_id=commit.commit.id,
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        object_instance_graph_id=commit.object_instance_graph_id,
        parent_commit_ids=tuple(
            parent.parent_commit_id for parent in commit.commit.commit_parents
        ),
        class_instance_ids=_commit_class_instance_ids_from_commit(commit),
    )


def _object_instance_graph_commit_identity_sidecar_from_record(
    *,
    envelope: ObjectInstanceGraphCommitEnvelope,
    body: ObjectInstanceGraphCommitBodyV1,
) -> ObjectInstanceGraphCommitIdentitySidecar:
    return ObjectInstanceGraphCommitIdentitySidecar(
        commit_id=envelope.commit_id,
        object_instance_graph_identity_id=envelope.object_instance_graph_identity_id,
        object_instance_graph_id=envelope.object_instance_graph_id,
        parent_commit_ids=envelope.parent_commit_ids,
        class_instance_ids=_commit_class_instance_ids_from_body(body),
    )


def _object_instance_graph_commit_identity_sidecar_from_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    payload: JsonObject,
) -> ObjectInstanceGraphCommitIdentitySidecar:
    if payload.get("branch_id") != str(branch_id):
        raise ValueError(f"OIG commit identity sidecar branch mismatch: {commit_id}")
    if payload.get("projection_hash") != projection_hash:
        raise ValueError(
            f"OIG commit identity sidecar projection mismatch: {commit_id}"
        )
    if payload.get("commit_id") != str(commit_id):
        raise ValueError(f"OIG commit identity sidecar id mismatch: {commit_id}")
    parent_values = payload.get("parent_commit_ids")
    class_instance_values = payload.get("class_instance_ids")
    if not isinstance(parent_values, list):
        raise ValueError(
            f"OIG commit identity sidecar parent list missing: {commit_id}"
        )
    if not isinstance(class_instance_values, list):
        raise ValueError(f"OIG commit identity sidecar class list missing: {commit_id}")
    return ObjectInstanceGraphCommitIdentitySidecar(
        commit_id=commit_id,
        object_instance_graph_identity_id=_json_required_uuid(
            payload,
            "object_instance_graph_identity_id",
        ),
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        parent_commit_ids=tuple(UUID(str(parent_id)) for parent_id in parent_values),
        class_instance_ids=tuple(
            UUID(str(class_instance_id)) for class_instance_id in class_instance_values
        ),
    )


def _object_instance_graph_commit_identity_sidecar_from_commit_payload(
    *,
    commit_id: UUID,
    payload: JsonObject,
) -> ObjectInstanceGraphCommitIdentitySidecar:
    commit_payload = _json_mapping(payload, "commit")
    if _json_required_uuid(commit_payload, "id") != commit_id:
        raise ValueError(f"OIG commit payload id mismatch: {commit_id}")
    return ObjectInstanceGraphCommitIdentitySidecar(
        commit_id=commit_id,
        object_instance_graph_identity_id=_json_required_uuid(
            payload,
            "object_instance_graph_identity_id",
        ),
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        parent_commit_ids=_commit_parent_ids_from_commit_payload(
            commit_id=commit_id,
            commit_payload=commit_payload,
        ),
        class_instance_ids=_commit_class_instance_ids_from_payload(
            commit_id=commit_id,
            payload=payload,
        ),
    )


def _oigi_history_domain_commit_projection_payload(
    *,
    projection: OigiHistoryDomainCommitProjection,
) -> JsonObject:
    return {
        "v": OIGI_HISTORY_DOMAIN_COMMIT_PROJECTION_INDEX_VERSION,
        "domain_commit_id": str(projection.domain_commit_id),
        "domain_branch_id": str(projection.domain_branch_id),
        "domain_projection_hash": projection.domain_projection_hash,
        "domain_lane_id": str(projection.domain_lane_id),
        "history_commit_id": str(projection.history_commit_id),
        "object_instance_graph_identity_id": str(
            projection.object_instance_graph_identity_id
        ),
        "object_instance_graph_id": str(projection.object_instance_graph_id),
        "oigi_projection_hash": projection.oigi_projection_hash,
        "oigi_lane_commit_id": str(projection.oigi_lane_commit_id),
        "oigi_graph_hash_post": projection.oigi_graph_hash_post,
    }


def _oigi_history_domain_commit_projection_from_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
    payload: JsonObject,
) -> OigiHistoryDomainCommitProjection:
    if payload.get("v") != OIGI_HISTORY_DOMAIN_COMMIT_PROJECTION_INDEX_VERSION:
        raise ValueError(
            "OIGI history domain commit projection index version mismatch: "
            + str(domain_commit_id)
        )
    if payload.get("object_instance_graph_id") != str(branch_id):
        raise ValueError(
            "OIGI history domain commit projection branch mismatch: "
            + str(domain_commit_id)
        )
    if payload.get("oigi_projection_hash") != projection_hash:
        raise ValueError(
            "OIGI history domain commit projection hash mismatch: "
            + str(domain_commit_id)
        )
    if payload.get("domain_commit_id") != str(domain_commit_id):
        raise ValueError(
            "OIGI history domain commit projection id mismatch: "
            + str(domain_commit_id)
        )
    return OigiHistoryDomainCommitProjection(
        domain_commit_id=domain_commit_id,
        domain_branch_id=_json_required_uuid(payload, "domain_branch_id"),
        domain_projection_hash=_json_required_string(
            payload,
            "domain_projection_hash",
        ),
        domain_lane_id=_json_required_uuid(payload, "domain_lane_id"),
        history_commit_id=_json_required_uuid(payload, "history_commit_id"),
        object_instance_graph_identity_id=_json_required_uuid(
            payload,
            "object_instance_graph_identity_id",
        ),
        object_instance_graph_id=_json_required_uuid(
            payload,
            "object_instance_graph_id",
        ),
        oigi_projection_hash=_json_required_string(payload, "oigi_projection_hash"),
        oigi_lane_commit_id=_json_required_uuid(payload, "oigi_lane_commit_id"),
        oigi_graph_hash_post=_json_required_string(payload, "oigi_graph_hash_post"),
    )


def _object_instance_graph_commit_object_projection_graph_id(
    commit: ObjectInstanceGraphCommit,
) -> UUID | None:
    object_instance_graph = getattr(commit, "object_instance_graph", None)
    if object_instance_graph is None:
        return None
    value = getattr(object_instance_graph, "object_projection_graph_id", None)
    return value if isinstance(value, UUID) else None


def _commit_meta_payload(
    commit_action: CommitActionDescriptor | None,
) -> JsonObject | None:
    if commit_action is None:
        return None

    payload: JsonObject = {
        "v": COMMIT_META_VERSION,
        "operation_label": commit_action.operation_label,
    }
    if commit_action.call_target is not None:
        payload["call_target"] = commit_action.call_target
    if commit_action.function_id is not None:
        payload["function_id"] = str(commit_action.function_id)
    if commit_action.object_id is not None:
        payload["object_id"] = str(commit_action.object_id)
    if commit_action.class_instance_identity_id is not None:
        payload["class_instance_identity_id"] = str(
            commit_action.class_instance_identity_id
        )
    return payload


def _commit_payload_matches(
    existing: JsonObject, commit: ObjectInstanceGraphCommit
) -> bool:
    return (
        _json_optional_string(existing, "graph_hash_post") == commit.graph_hash_post
        and _json_optional_string(existing, "graph_hash_pre") == commit.graph_hash_pre
        and _json_optional_string(existing, "projection_hash") == commit.projection_hash
    )
