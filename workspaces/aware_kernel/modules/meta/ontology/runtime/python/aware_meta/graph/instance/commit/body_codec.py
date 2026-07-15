from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
import hashlib
import json
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel

from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.attribute.attribute_value_link_change import (
    AttributeValueLinkChange,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id


OIG_COMMIT_BODY_CONTRACT = "aware.oig_commit_body.v1"
OIG_COMMIT_BODY_MEDIA_TYPE = "application/vnd.aware.oig-commit-body+json"
OIG_COMMIT_BODY_VERSION = 1
type OigCommitBodyJsonValue = (
    str
    | int
    | float
    | bool
    | None
    | Mapping[str, "OigCommitBodyJsonValue"]
    | Sequence["OigCommitBodyJsonValue"]
)


class OigCommitBodyCodecError(ValueError):
    """Raised when an OIG commit inline body is malformed or unsupported."""


@dataclass(frozen=True, slots=True)
class ObjectInstanceGraphCommitBodyV1:
    payload: Mapping[str, object]
    canonical_bytes: bytes
    sha256: str

    @property
    def commit_id(self) -> UUID:
        return UUID(str(self.payload["cid"]))

    @property
    def object_instance_graph_commit_id(self) -> UUID:
        return UUID(str(self.payload["ogc"]))

    @property
    def object_instance_graph_identity_id(self) -> UUID:
        return UUID(str(self.payload["oigi"]))

    @property
    def object_instance_graph_id(self) -> UUID:
        return UUID(str(self.payload["oig"]))


@dataclass(frozen=True, slots=True)
class OigCommitBodyFieldDeltaDraft:
    position: int
    property: str | None
    kind: ChangeDeltaKind | str
    payload: OigCommitBodyJsonValue


@dataclass(frozen=True, slots=True)
class OigCommitBodyChangeRefDraft:
    id: UUID
    key: str
    type: ChangeType | str
    created_at: datetime
    fields: tuple[OigCommitBodyFieldDeltaDraft, ...] = ()


@dataclass(frozen=True, slots=True)
class OigCommitBodyAttributeValueLinkChangeDraft:
    id: UUID
    attribute_value_link_id: UUID
    change: OigCommitBodyChangeRefDraft
    child_attribute_value_change: "OigCommitBodyAttributeValueChangeDraft | None" = None


@dataclass(frozen=True, slots=True)
class OigCommitBodyAttributeValueChangeDraft:
    id: UUID
    attribute_value_id: UUID
    change: OigCommitBodyChangeRefDraft
    attribute_value_link_changes: tuple[
        OigCommitBodyAttributeValueLinkChangeDraft, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class OigCommitBodyAttributeChangeDraft:
    id: UUID
    attribute_id: UUID
    change: OigCommitBodyChangeRefDraft
    value_root_change: OigCommitBodyAttributeValueChangeDraft | None = None


@dataclass(frozen=True, slots=True)
class OigCommitBodyClassInstanceChangeDraft:
    id: UUID
    class_instance_id: UUID
    change: OigCommitBodyChangeRefDraft
    attribute_changes: tuple[OigCommitBodyAttributeChangeDraft, ...] = ()


@dataclass(frozen=True, slots=True)
class OigCommitBodyRelationshipChangeDraft:
    id: UUID
    class_config_relationship_id: UUID
    source_class_instance_id: UUID
    target_class_instance_id: UUID
    change: OigCommitBodyChangeRefDraft


@dataclass(frozen=True, slots=True)
class OigCommitBodyRootChangeDraft:
    id: UUID
    type: ObjectInstanceGraphChangeType | str
    change: OigCommitBodyChangeRefDraft
    class_instance_changes: tuple[OigCommitBodyClassInstanceChangeDraft, ...] = ()
    class_instance_relationship_changes: tuple[
        OigCommitBodyRelationshipChangeDraft, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class OigCommitBodyDraft:
    roots: tuple[OigCommitBodyRootChangeDraft, ...]


def build_oig_commit_body(
    commit: ObjectInstanceGraphCommit,
) -> ObjectInstanceGraphCommitBodyV1:
    payload = build_oig_commit_body_payload(commit)
    canonical_bytes = canonical_oig_commit_body_bytes(payload)
    return ObjectInstanceGraphCommitBodyV1(
        payload=payload,
        canonical_bytes=canonical_bytes,
        sha256=hashlib.sha256(canonical_bytes).hexdigest(),
    )


def build_oig_commit_body_from_changes(
    *,
    commit_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    changes: Sequence[ObjectInstanceGraphChange],
) -> ObjectInstanceGraphCommitBodyV1:
    payload = build_oig_commit_body_payload_from_changes(
        commit_id=commit_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        changes=changes,
    )
    canonical_bytes = canonical_oig_commit_body_bytes(payload)
    return ObjectInstanceGraphCommitBodyV1(
        payload=payload,
        canonical_bytes=canonical_bytes,
        sha256=hashlib.sha256(canonical_bytes).hexdigest(),
    )


def build_oig_commit_body_from_draft(
    *,
    commit_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    draft: OigCommitBodyDraft,
) -> ObjectInstanceGraphCommitBodyV1:
    payload = build_oig_commit_body_payload_from_draft(
        commit_id=commit_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        draft=draft,
    )
    canonical_bytes = canonical_oig_commit_body_bytes(payload)
    return ObjectInstanceGraphCommitBodyV1(
        payload=payload,
        canonical_bytes=canonical_bytes,
        sha256=hashlib.sha256(canonical_bytes).hexdigest(),
    )


def build_oig_commit_body_payload(
    commit: ObjectInstanceGraphCommit,
) -> dict[str, object]:
    commit_id = _required_uuid(commit.commit_id or commit.commit.id, "commit_id")
    oigi_id = _required_uuid(
        commit.object_instance_graph_identity_id,
        "object_instance_graph_identity_id",
    )
    return {
        "c": OIG_COMMIT_BODY_CONTRACT,
        "v": OIG_COMMIT_BODY_VERSION,
        "cid": str(commit_id),
        "ogc": str(
            stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=oigi_id,
                commit_id=commit_id,
            )
        ),
        "oigi": str(oigi_id),
        "oig": str(
            _required_uuid(commit.object_instance_graph_id, "object_instance_graph_id")
        ),
        "r": [
            _object_instance_graph_change_payload(change)
            for change in commit.object_instance_graph_changes
        ],
    }


def build_oig_commit_body_payload_from_changes(
    *,
    commit_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    changes: Sequence[ObjectInstanceGraphChange],
) -> dict[str, object]:
    resolved_commit_id = _required_uuid(commit_id, "commit_id")
    resolved_oigi_id = _required_uuid(
        object_instance_graph_identity_id,
        "object_instance_graph_identity_id",
    )
    resolved_oig_id = _required_uuid(
        object_instance_graph_id,
        "object_instance_graph_id",
    )
    return {
        "c": OIG_COMMIT_BODY_CONTRACT,
        "v": OIG_COMMIT_BODY_VERSION,
        "cid": str(resolved_commit_id),
        "ogc": str(
            stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=resolved_oigi_id,
                commit_id=resolved_commit_id,
            )
        ),
        "oigi": str(resolved_oigi_id),
        "oig": str(resolved_oig_id),
        "r": [_object_instance_graph_change_payload(change) for change in changes],
    }


def build_oig_commit_body_payload_from_draft(
    *,
    commit_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    draft: OigCommitBodyDraft,
) -> dict[str, object]:
    resolved_commit_id = _required_uuid(commit_id, "commit_id")
    resolved_oigi_id = _required_uuid(
        object_instance_graph_identity_id,
        "object_instance_graph_identity_id",
    )
    resolved_oig_id = _required_uuid(
        object_instance_graph_id,
        "object_instance_graph_id",
    )
    return {
        "c": OIG_COMMIT_BODY_CONTRACT,
        "v": OIG_COMMIT_BODY_VERSION,
        "cid": str(resolved_commit_id),
        "ogc": str(
            stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=resolved_oigi_id,
                commit_id=resolved_commit_id,
            )
        ),
        "oigi": str(resolved_oigi_id),
        "oig": str(resolved_oig_id),
        "r": [_root_change_draft_payload(root) for root in draft.roots],
    }


def canonical_oig_commit_body_bytes(payload: Mapping[str, object]) -> bytes:
    normalized = _canonical_json_value(payload)
    _validate_body_payload(normalized)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def decode_oig_commit_body(body_bytes: bytes) -> ObjectInstanceGraphCommitBodyV1:
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OigCommitBodyCodecError("invalid_oig_commit_body_json") from exc
    normalized = _canonical_json_value(payload)
    _validate_body_payload(normalized)
    normalized_payload = cast(Mapping[str, object], normalized)
    canonical_bytes = canonical_oig_commit_body_bytes(normalized_payload)
    return ObjectInstanceGraphCommitBodyV1(
        payload=normalized_payload,
        canonical_bytes=canonical_bytes,
        sha256=hashlib.sha256(canonical_bytes).hexdigest(),
    )


def object_instance_graph_changes_from_body(
    body: ObjectInstanceGraphCommitBodyV1,
) -> tuple[ObjectInstanceGraphChange, ...]:
    """Rehydrate only the replay change tree from an inline OIG commit body."""

    roots = body.payload.get("r")
    if not isinstance(roots, list):
        raise OigCommitBodyCodecError("oig_commit_body_roots_must_be_list")
    return tuple(
        _object_instance_graph_change_from_payload(
            payload=root,
            object_instance_graph_identity_id=body.object_instance_graph_identity_id,
            object_instance_graph_id=body.object_instance_graph_id,
        )
        for root in roots
    )


def oig_commit_body_sha256(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_oig_commit_body_bytes(payload)).hexdigest()


def oig_commit_body_change_ref_draft_from_change(
    change: Change,
    *,
    fields: Sequence[ChangeDelta] = (),
) -> OigCommitBodyChangeRefDraft:
    return OigCommitBodyChangeRefDraft(
        id=_required_uuid(change.id, "change.id"),
        key=str(change.key),
        type=change.type,
        created_at=change.created_at,
        fields=tuple(_field_delta_draft_from_change_delta(delta) for delta in fields),
    )


def oig_commit_body_class_instance_change_draft_from_change(
    change: ClassInstanceChange,
) -> OigCommitBodyClassInstanceChangeDraft:
    return OigCommitBodyClassInstanceChangeDraft(
        id=_required_uuid(change.id, "class_instance_change.id"),
        class_instance_id=_required_uuid(
            change.class_instance_id,
            "class_instance_change.ci",
        ),
        change=oig_commit_body_change_ref_draft_from_change(
            change.change,
            fields=change.change.change_deltas,
        ),
        attribute_changes=tuple(
            oig_commit_body_attribute_change_draft_from_change(item)
            for item in change.attribute_changes
        ),
    )


def oig_commit_body_attribute_change_draft_from_change(
    change: AttributeChange,
) -> OigCommitBodyAttributeChangeDraft:
    return OigCommitBodyAttributeChangeDraft(
        id=_required_uuid(change.id, "attribute_change.id"),
        attribute_id=_required_uuid(change.attribute_id, "attribute_change.attr"),
        change=oig_commit_body_change_ref_draft_from_change(
            change.change,
            fields=change.change.change_deltas,
        ),
        value_root_change=(
            oig_commit_body_attribute_value_change_draft_from_change(
                change.value_root_change
            )
            if change.value_root_change is not None
            else None
        ),
    )


def oig_commit_body_attribute_value_change_draft_from_change(
    change: AttributeValueChange,
) -> OigCommitBodyAttributeValueChangeDraft:
    return OigCommitBodyAttributeValueChangeDraft(
        id=_required_uuid(change.id, "attribute_value_change.id"),
        attribute_value_id=_required_uuid(
            change.attribute_value_id,
            "attribute_value_change.av",
        ),
        change=oig_commit_body_change_ref_draft_from_change(
            change.change,
            fields=change.change.change_deltas,
        ),
        attribute_value_link_changes=tuple(
            oig_commit_body_attribute_value_link_change_draft_from_change(item)
            for item in change.attribute_value_link_changes
        ),
    )


def oig_commit_body_attribute_value_link_change_draft_from_change(
    change: AttributeValueLinkChange,
) -> OigCommitBodyAttributeValueLinkChangeDraft:
    return OigCommitBodyAttributeValueLinkChangeDraft(
        id=_required_uuid(change.id, "attribute_value_link_change.id"),
        attribute_value_link_id=_required_uuid(
            change.attribute_value_link_id,
            "attribute_value_link_change.avl",
        ),
        change=oig_commit_body_change_ref_draft_from_change(
            change.change,
            fields=change.change.change_deltas,
        ),
        child_attribute_value_change=(
            oig_commit_body_attribute_value_change_draft_from_change(
                change.child_attribute_value_change
            )
            if change.child_attribute_value_change is not None
            else None
        ),
    )


def oig_commit_body_relationship_change_draft_from_change(
    change: ClassInstanceRelationshipChange,
) -> OigCommitBodyRelationshipChangeDraft:
    return OigCommitBodyRelationshipChangeDraft(
        id=_required_uuid(change.id, "relationship_change.id"),
        class_config_relationship_id=_required_uuid(
            change.class_config_relationship_id,
            "relationship_change.rel",
        ),
        source_class_instance_id=_required_uuid(
            change.source_class_instance_id,
            "relationship_change.from",
        ),
        target_class_instance_id=_required_uuid(
            change.target_class_instance_id,
            "relationship_change.to",
        ),
        change=oig_commit_body_change_ref_draft_from_change(change.change),
    )


def _object_instance_graph_change_payload(
    change: ObjectInstanceGraphChange,
) -> dict[str, object]:
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "object_instance_graph_change.id")),
            "t": _enum_value(change.type),
            "ch": _change_ref_payload(change.change),
            "ci": [
                _class_instance_change_payload(item)
                for item in change.class_instance_changes
            ],
            "rel": [
                _relationship_change_payload(item)
                for item in change.class_instance_relationship_changes
            ],
        }
    )


def _class_instance_change_payload(
    change: ClassInstanceChange,
) -> dict[str, object]:
    fields = _field_delta_payloads(change.change.change_deltas)
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "class_instance_change.id")),
            "ci": str(
                _required_uuid(change.class_instance_id, "class_instance_change.ci")
            ),
            "cc": _field_value(fields, "class_config_id"),
            "src": _field_value(fields, "source_object_id"),
            "ch": _change_ref_payload(change.change),
            "f": fields,
            "a": [_attribute_change_payload(item) for item in change.attribute_changes],
        }
    )


def _attribute_change_payload(change: AttributeChange) -> dict[str, object]:
    fields = _field_delta_payloads(change.change.change_deltas)
    value_change = (
        _attribute_value_change_payload(change.value_root_change)
        if change.value_root_change is not None
        else None
    )
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "attribute_change.id")),
            "attr": str(_required_uuid(change.attribute_id, "attribute_change.attr")),
            "ac": _field_value(fields, "attribute_config_id"),
            "ch": _change_ref_payload(change.change),
            "f": fields,
            "val": value_change,
        }
    )


def _attribute_value_change_payload(
    change: AttributeValueChange,
) -> dict[str, object]:
    fields = _field_delta_payloads(change.change.change_deltas)
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "attribute_value_change.id")),
            "av": str(
                _required_uuid(
                    change.attribute_value_id,
                    "attribute_value_change.av",
                )
            ),
            "ch": _change_ref_payload(change.change),
            "f": fields,
            "l": [
                _attribute_value_link_change_payload(item)
                for item in change.attribute_value_link_changes
            ],
        }
    )


def _attribute_value_link_change_payload(
    change: AttributeValueLinkChange,
) -> dict[str, object]:
    fields = _field_delta_payloads(change.change.change_deltas)
    child = (
        _attribute_value_change_payload(change.child_attribute_value_change)
        if change.child_attribute_value_change is not None
        else None
    )
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "attribute_value_link_change.id")),
            "avl": str(
                _required_uuid(
                    change.attribute_value_link_id,
                    "attribute_value_link_change.avl",
                )
            ),
            "ch": _change_ref_payload(change.change),
            "f": fields,
            "child": child,
        }
    )


def _relationship_change_payload(
    change: ClassInstanceRelationshipChange,
) -> dict[str, object]:
    return {
        "id": str(_required_uuid(change.id, "relationship_change.id")),
        "rel": str(
            _required_uuid(
                change.class_config_relationship_id,
                "relationship_change.rel",
            )
        ),
        "from": str(
            _required_uuid(
                change.source_class_instance_id,
                "relationship_change.from",
            )
        ),
        "to": str(
            _required_uuid(
                change.target_class_instance_id,
                "relationship_change.to",
            )
        ),
        "ch": _change_ref_payload(change.change),
    }


def _root_change_draft_payload(
    change: OigCommitBodyRootChangeDraft,
) -> dict[str, object]:
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "root.id")),
            "t": _enum_value(change.type),
            "ch": _change_ref_draft_payload(change.change),
            "ci": [
                _class_instance_change_draft_payload(item)
                for item in change.class_instance_changes
            ],
            "rel": [
                _relationship_change_draft_payload(item)
                for item in change.class_instance_relationship_changes
            ],
        }
    )


def _class_instance_change_draft_payload(
    change: OigCommitBodyClassInstanceChangeDraft,
) -> dict[str, object]:
    fields = _field_delta_draft_payloads(change.change.fields)
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "class_instance_change.id")),
            "ci": str(
                _required_uuid(change.class_instance_id, "class_instance_change.ci")
            ),
            "cc": _field_value(fields, "class_config_id"),
            "src": _field_value(fields, "source_object_id"),
            "ch": _change_ref_draft_payload(change.change),
            "f": fields,
            "a": [
                _attribute_change_draft_payload(item)
                for item in change.attribute_changes
            ],
        }
    )


def _attribute_change_draft_payload(
    change: OigCommitBodyAttributeChangeDraft,
) -> dict[str, object]:
    fields = _field_delta_draft_payloads(change.change.fields)
    value_change = (
        _attribute_value_change_draft_payload(change.value_root_change)
        if change.value_root_change is not None
        else None
    )
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "attribute_change.id")),
            "attr": str(_required_uuid(change.attribute_id, "attribute_change.attr")),
            "ac": _field_value(fields, "attribute_config_id"),
            "ch": _change_ref_draft_payload(change.change),
            "f": fields,
            "val": value_change,
        }
    )


def _attribute_value_change_draft_payload(
    change: OigCommitBodyAttributeValueChangeDraft,
) -> dict[str, object]:
    fields = _field_delta_draft_payloads(change.change.fields)
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "attribute_value_change.id")),
            "av": str(
                _required_uuid(
                    change.attribute_value_id,
                    "attribute_value_change.av",
                )
            ),
            "ch": _change_ref_draft_payload(change.change),
            "f": fields,
            "l": [
                _attribute_value_link_change_draft_payload(item)
                for item in change.attribute_value_link_changes
            ],
        }
    )


def _attribute_value_link_change_draft_payload(
    change: OigCommitBodyAttributeValueLinkChangeDraft,
) -> dict[str, object]:
    fields = _field_delta_draft_payloads(change.change.fields)
    child = (
        _attribute_value_change_draft_payload(change.child_attribute_value_change)
        if change.child_attribute_value_change is not None
        else None
    )
    return _without_none(
        {
            "id": str(_required_uuid(change.id, "attribute_value_link_change.id")),
            "avl": str(
                _required_uuid(
                    change.attribute_value_link_id,
                    "attribute_value_link_change.avl",
                )
            ),
            "ch": _change_ref_draft_payload(change.change),
            "f": fields,
            "child": child,
        }
    )


def _relationship_change_draft_payload(
    change: OigCommitBodyRelationshipChangeDraft,
) -> dict[str, object]:
    return {
        "id": str(_required_uuid(change.id, "relationship_change.id")),
        "rel": str(
            _required_uuid(
                change.class_config_relationship_id,
                "relationship_change.rel",
            )
        ),
        "from": str(
            _required_uuid(
                change.source_class_instance_id,
                "relationship_change.from",
            )
        ),
        "to": str(
            _required_uuid(
                change.target_class_instance_id,
                "relationship_change.to",
            )
        ),
        "ch": _change_ref_draft_payload(change.change),
    }


def _change_ref_draft_payload(change: OigCommitBodyChangeRefDraft) -> dict[str, object]:
    return {
        "id": str(_required_uuid(change.id, "change.id")),
        "key": str(change.key),
        "op": _enum_value(change.type),
        "at": _datetime_text(change.created_at),
    }


def _change_ref_payload(change: Change) -> dict[str, object]:
    return {
        "id": str(_required_uuid(change.id, "change.id")),
        "key": str(change.key),
        "op": _enum_value(change.type),
        "at": _datetime_text(change.created_at),
    }


def _field_delta_payloads(deltas: Sequence[ChangeDelta]) -> list[dict[str, object]]:
    return [
        _field_delta_payload(delta) for delta in sorted(deltas, key=_delta_sort_key)
    ]


def _field_delta_draft_payloads(
    deltas: Sequence[OigCommitBodyFieldDeltaDraft],
) -> list[dict[str, object]]:
    return [
        _field_delta_draft_payload(delta)
        for delta in sorted(deltas, key=_delta_draft_sort_key)
    ]


def _field_delta_draft_payload(
    delta: OigCommitBodyFieldDeltaDraft,
) -> dict[str, object]:
    return _without_none(
        {
            "pos": int(delta.position),
            "p": delta.property,
            "op": _enum_value(delta.kind),
            "x": _canonical_json_value(delta.payload),
        }
    )


def _field_delta_payload(delta: ChangeDelta) -> dict[str, object]:
    return _without_none(
        {
            "pos": int(delta.position),
            "p": delta.property,
            "op": _enum_value(delta.kind),
            "x": _canonical_json_value(delta.payload),
        }
    )


def _field_delta_draft_from_change_delta(
    delta: ChangeDelta,
) -> OigCommitBodyFieldDeltaDraft:
    return OigCommitBodyFieldDeltaDraft(
        position=int(delta.position),
        property=delta.property,
        kind=delta.kind,
        payload=cast(OigCommitBodyJsonValue, _canonical_json_value(delta.payload)),
    )


def _object_instance_graph_change_from_payload(
    *,
    payload: object,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
) -> ObjectInstanceGraphChange:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("oig_commit_root_change_must_be_object")
    root_payload = _mapping_payload(payload)
    return ObjectInstanceGraphChange.model_construct(
        id=_required_uuid(root_payload.get("id"), "root.id"),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        type=ObjectInstanceGraphChangeType(
            _required_text(root_payload.get("t"), "root.t")
        ),
        change=_change_from_payload(root_payload.get("ch"), fields=()),
        change_id=_change_id(root_payload.get("ch"), "root.ch"),
        class_instance_changes=[
            _class_instance_change_from_payload(item)
            for item in _required_list(root_payload.get("ci"), "root.ci")
        ],
        class_instance_relationship_changes=[
            _relationship_change_from_payload(item)
            for item in _required_list(root_payload.get("rel"), "root.rel")
        ],
    )


def _class_instance_change_from_payload(payload: object) -> ClassInstanceChange:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("class_instance_change_must_be_object")
    item = _mapping_payload(payload)
    change_payload = item.get("ch")
    fields = _required_list(item.get("f"), "ci.f")
    change = _change_from_payload(change_payload, fields=fields)
    return ClassInstanceChange.model_construct(
        id=_required_uuid(item.get("id"), "ci.id"),
        class_instance_id=_required_uuid(item.get("ci"), "ci.ci"),
        change=change,
        change_id=change.id,
        attribute_changes=[
            _attribute_change_from_payload(
                payload=attr_payload,
                class_instance_change_id=_required_uuid(item.get("id"), "ci.id"),
            )
            for attr_payload in _required_list(item.get("a"), "ci.a")
        ],
    )


def _attribute_change_from_payload(
    *,
    payload: object,
    class_instance_change_id: UUID,
) -> AttributeChange:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("attribute_change_must_be_object")
    item = _mapping_payload(payload)
    fields = _required_list(item.get("f"), "attr.f")
    change = _change_from_payload(item.get("ch"), fields=fields)
    value_root_payload = item.get("val")
    value_root_change = (
        _attribute_value_change_from_payload(value_root_payload)
        if value_root_payload is not None
        else None
    )
    return AttributeChange.model_construct(
        id=_required_uuid(item.get("id"), "attr.id"),
        class_instance_change_id=class_instance_change_id,
        attribute_id=_required_uuid(item.get("attr"), "attr.attr"),
        change=change,
        change_id=change.id,
        value_root_change=value_root_change,
        value_root_change_id=(
            value_root_change.id if value_root_change is not None else None
        ),
    )


def _attribute_value_change_from_payload(payload: object) -> AttributeValueChange:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("attribute_value_change_must_be_object")
    item = _mapping_payload(payload)
    value_change_id = _required_uuid(item.get("id"), "av.id")
    fields = _required_list(item.get("f"), "av.f")
    change = _change_from_payload(item.get("ch"), fields=fields)
    return AttributeValueChange.model_construct(
        id=value_change_id,
        attribute_value_id=_required_uuid(item.get("av"), "av.av"),
        change=change,
        change_id=change.id,
        attribute_value_link_changes=[
            _attribute_value_link_change_from_payload(
                payload=link_payload,
                attribute_value_change_id=value_change_id,
            )
            for link_payload in _required_list(item.get("l"), "av.l")
        ],
    )


def _attribute_value_link_change_from_payload(
    *,
    payload: object,
    attribute_value_change_id: UUID,
) -> AttributeValueLinkChange:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("attribute_value_link_change_must_be_object")
    item = _mapping_payload(payload)
    fields = _required_list(item.get("f"), "avl.f")
    change = _change_from_payload(item.get("ch"), fields=fields)
    child_payload = item.get("child")
    child_change = (
        _attribute_value_change_from_payload(child_payload)
        if child_payload is not None
        else None
    )
    return AttributeValueLinkChange.model_construct(
        id=_required_uuid(item.get("id"), "avl.id"),
        attribute_value_link_id=_required_uuid(item.get("avl"), "avl.avl"),
        attribute_value_change_id=attribute_value_change_id,
        change=change,
        change_id=change.id,
        child_attribute_value_change=child_change,
        child_attribute_value_change_id=(
            child_change.id if child_change is not None else None
        ),
    )


def _relationship_change_from_payload(
    payload: object,
) -> ClassInstanceRelationshipChange:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("relationship_change_must_be_object")
    item = _mapping_payload(payload)
    change = _change_from_payload(item.get("ch"), fields=())
    return ClassInstanceRelationshipChange.model_construct(
        id=_required_uuid(item.get("id"), "rel.id"),
        class_config_relationship_id=_required_uuid(item.get("rel"), "rel.rel"),
        source_class_instance_id=_required_uuid(item.get("from"), "rel.from"),
        target_class_instance_id=_required_uuid(item.get("to"), "rel.to"),
        change=change,
        change_id=change.id,
    )


def _change_from_payload(
    payload: object,
    *,
    fields: Sequence[object],
) -> Change:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("change_ref_must_be_object")
    item = _mapping_payload(payload)
    change_id = _required_uuid(item.get("id"), "change.id")
    return Change.model_construct(
        id=change_id,
        key=_required_text(item.get("key"), "change.key"),
        created_at=_datetime_from_text(_required_text(item.get("at"), "change.at")),
        type=ChangeType(_required_text(item.get("op"), "change.op")),
        change_deltas=[
            _field_delta_from_payload(
                payload=field_payload,
                change_id=change_id,
            )
            for field_payload in fields
        ],
    )


def _field_delta_from_payload(
    *,
    payload: object,
    change_id: UUID,
) -> ChangeDelta:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("field_delta_must_be_object")
    item = _mapping_payload(payload)
    position = item.get("pos")
    if not isinstance(position, int):
        raise OigCommitBodyCodecError("field_delta_pos_must_be_int")
    property_name = item.get("p")
    if property_name is not None and not isinstance(property_name, str):
        raise OigCommitBodyCodecError("field_delta_property_must_be_text")
    return ChangeDelta.model_construct(
        id=uuid5(
            NAMESPACE_URL,
            f"{OIG_COMMIT_BODY_CONTRACT}:change_delta:{change_id}:{position}:{property_name or ''}",
        ),
        change_id=change_id,
        position=position,
        property=property_name,
        kind=ChangeDeltaKind(_required_text(item.get("op"), "field.op")),
        payload=_canonical_json_value(item.get("x")),
    )


def _change_id(payload: object, name: str) -> UUID:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("change_ref_must_be_object")
    return _required_uuid(_mapping_payload(payload).get("id"), name)


def _mapping_payload(payload: Mapping[object, object]) -> Mapping[str, object]:
    return {str(key): value for key, value in payload.items()}


def _required_list(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise OigCommitBodyCodecError(name + "_must_be_list")
    return list(value)


def _datetime_from_text(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OigCommitBodyCodecError("change_at_must_be_datetime") from exc


def _delta_sort_key(delta: ChangeDelta) -> tuple[int, str]:
    return (int(delta.position), str(delta.property or ""))


def _delta_draft_sort_key(delta: OigCommitBodyFieldDeltaDraft) -> tuple[int, str]:
    return (int(delta.position), str(delta.property or ""))


def _field_value(fields: Sequence[Mapping[str, object]], property_name: str) -> object:
    for field in fields:
        if field.get("p") != property_name:
            continue
        payload = field.get("x")
        if isinstance(payload, Mapping) and "value" in payload:
            return payload["value"]
        return payload
    return None


def _validate_body_payload(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("oig_commit_body_must_be_object")
    if "object_instance_graph_changes" in payload:
        raise OigCommitBodyCodecError("legacy_oig_commit_payload_rejected")
    _reject_unknown_keys(payload, {"c", "v", "cid", "ogc", "oigi", "oig", "r"})
    if payload.get("c") != OIG_COMMIT_BODY_CONTRACT:
        raise OigCommitBodyCodecError(
            "unsupported_oig_commit_body_contract:" + str(payload.get("c"))
        )
    if payload.get("v") != OIG_COMMIT_BODY_VERSION:
        raise OigCommitBodyCodecError(
            "unsupported_oig_commit_body_version:" + str(payload.get("v"))
        )
    for key in ("cid", "ogc", "oigi", "oig"):
        _required_uuid(payload.get(key), key)
    roots = payload.get("r")
    if not isinstance(roots, list):
        raise OigCommitBodyCodecError("oig_commit_body_roots_must_be_list")
    for root in roots:
        _validate_root_change(root)


def _validate_root_change(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("oig_commit_root_change_must_be_object")
    _reject_unknown_keys(payload, {"id", "t", "ch", "ci", "rel"})
    _required_uuid(payload.get("id"), "root.id")
    _required_text(payload.get("t"), "root.t")
    _validate_change_ref(payload.get("ch"))
    _validate_list(payload.get("ci"), "root.ci", _validate_class_instance_change)
    _validate_list(payload.get("rel"), "root.rel", _validate_relationship_change)


def _validate_class_instance_change(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("class_instance_change_must_be_object")
    _reject_unknown_keys(payload, {"id", "ci", "cc", "src", "ch", "f", "a"})
    _required_uuid(payload.get("id"), "ci.id")
    _required_uuid(payload.get("ci"), "ci.ci")
    _optional_uuid(payload.get("cc"), "ci.cc")
    _optional_uuid(payload.get("src"), "ci.src")
    _validate_change_ref(payload.get("ch"))
    _validate_list(payload.get("f"), "ci.f", _validate_field_delta)
    _validate_list(payload.get("a"), "ci.a", _validate_attribute_change)


def _validate_attribute_change(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("attribute_change_must_be_object")
    _reject_unknown_keys(payload, {"id", "attr", "ac", "ch", "f", "val"})
    _required_uuid(payload.get("id"), "attr.id")
    _required_uuid(payload.get("attr"), "attr.attr")
    _optional_uuid(payload.get("ac"), "attr.ac")
    _validate_change_ref(payload.get("ch"))
    _validate_list(payload.get("f"), "attr.f", _validate_field_delta)
    value_change = payload.get("val")
    if value_change is not None:
        _validate_attribute_value_change(value_change)


def _validate_attribute_value_change(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("attribute_value_change_must_be_object")
    _reject_unknown_keys(payload, {"id", "av", "ch", "f", "l"})
    _required_uuid(payload.get("id"), "av.id")
    _required_uuid(payload.get("av"), "av.av")
    _validate_change_ref(payload.get("ch"))
    _validate_list(payload.get("f"), "av.f", _validate_field_delta)
    _validate_list(payload.get("l"), "av.l", _validate_attribute_value_link_change)


def _validate_attribute_value_link_change(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("attribute_value_link_change_must_be_object")
    _reject_unknown_keys(payload, {"id", "avl", "ch", "f", "child"})
    _required_uuid(payload.get("id"), "avl.id")
    _required_uuid(payload.get("avl"), "avl.avl")
    _validate_change_ref(payload.get("ch"))
    _validate_list(payload.get("f"), "avl.f", _validate_field_delta)
    child = payload.get("child")
    if child is not None:
        _validate_attribute_value_change(child)


def _validate_relationship_change(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("relationship_change_must_be_object")
    _reject_unknown_keys(payload, {"id", "rel", "from", "to", "ch"})
    _required_uuid(payload.get("id"), "rel.id")
    _required_uuid(payload.get("rel"), "rel.rel")
    _required_uuid(payload.get("from"), "rel.from")
    _required_uuid(payload.get("to"), "rel.to")
    _validate_change_ref(payload.get("ch"))


def _validate_change_ref(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("change_ref_must_be_object")
    _reject_unknown_keys(payload, {"id", "key", "op", "at"})
    _required_uuid(payload.get("id"), "change.id")
    _required_text(payload.get("key"), "change.key")
    _required_text(payload.get("op"), "change.op")
    _required_text(payload.get("at"), "change.at")


def _validate_field_delta(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise OigCommitBodyCodecError("field_delta_must_be_object")
    _reject_unknown_keys(payload, {"pos", "p", "op", "x"})
    if not isinstance(payload.get("pos"), int):
        raise OigCommitBodyCodecError("field_delta_pos_must_be_int")
    property_name = payload.get("p")
    if property_name is not None:
        _required_text(property_name, "field.p")
    _required_text(payload.get("op"), "field.op")


def _validate_list(
    value: object,
    name: str,
    item_validator: Any,
) -> None:
    if not isinstance(value, list):
        raise OigCommitBodyCodecError(name + "_must_be_list")
    for item in value:
        item_validator(item)


def _reject_unknown_keys(payload: Mapping[object, object], allowed: set[str]) -> None:
    keys = {str(key) for key in payload}
    unknown = keys - allowed
    if unknown:
        raise OigCommitBodyCodecError(
            "unknown_oig_commit_body_keys:" + ",".join(sorted(unknown))
        )


def _canonical_json_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return _datetime_text(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, BaseModel):
        return _canonical_json_value(value.model_dump(mode="json", exclude_none=True))
    if isinstance(value, Mapping):
        return {str(key): _canonical_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_json_value(item) for item in value]
    raise OigCommitBodyCodecError(
        "unsupported_oig_commit_body_json_value:" + type(value).__name__
    )


def _without_none(payload: Mapping[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value is not None}


def _enum_value(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _datetime_text(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _required_uuid(value: object, name: str) -> UUID:
    if value is None:
        raise OigCommitBodyCodecError(name + "_required")
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise OigCommitBodyCodecError(name + "_must_be_uuid") from exc


def _optional_uuid(value: object, name: str) -> None:
    if value is not None:
        _required_uuid(value, name)


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise OigCommitBodyCodecError(name + "_must_be_text")
    return value


__all__ = [
    "OIG_COMMIT_BODY_CONTRACT",
    "OIG_COMMIT_BODY_MEDIA_TYPE",
    "OIG_COMMIT_BODY_VERSION",
    "OigCommitBodyAttributeChangeDraft",
    "OigCommitBodyAttributeValueChangeDraft",
    "OigCommitBodyAttributeValueLinkChangeDraft",
    "ObjectInstanceGraphCommitBodyV1",
    "OigCommitBodyChangeRefDraft",
    "OigCommitBodyCodecError",
    "OigCommitBodyClassInstanceChangeDraft",
    "OigCommitBodyDraft",
    "OigCommitBodyFieldDeltaDraft",
    "OigCommitBodyJsonValue",
    "OigCommitBodyRelationshipChangeDraft",
    "OigCommitBodyRootChangeDraft",
    "build_oig_commit_body",
    "build_oig_commit_body_from_draft",
    "build_oig_commit_body_from_changes",
    "build_oig_commit_body_payload",
    "build_oig_commit_body_payload_from_draft",
    "build_oig_commit_body_payload_from_changes",
    "canonical_oig_commit_body_bytes",
    "decode_oig_commit_body",
    "object_instance_graph_changes_from_body",
    "oig_commit_body_attribute_change_draft_from_change",
    "oig_commit_body_attribute_value_change_draft_from_change",
    "oig_commit_body_attribute_value_link_change_draft_from_change",
    "oig_commit_body_change_ref_draft_from_change",
    "oig_commit_body_class_instance_change_draft_from_change",
    "oig_commit_body_relationship_change_draft_from_change",
    "oig_commit_body_sha256",
]
