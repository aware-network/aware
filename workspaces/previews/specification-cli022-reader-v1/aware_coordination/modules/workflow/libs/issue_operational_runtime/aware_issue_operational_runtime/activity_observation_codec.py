from __future__ import annotations

import json
from collections.abc import Mapping
from typing import NoReturn, cast

from .activity_observation import (
    MAX_WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_BYTES,
    WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA,
    ActivityOutcome,
    WorkflowIssueActivityHeadV1,
    WorkflowIssueActivityHorizonV1,
    WorkflowIssueActivityMemberV1,
    WorkflowIssueActivityObservationError,
    WorkflowIssueActivitySelectionKind,
    WorkflowIssueActivitySelectionV1,
    WorkflowIssueActivityUnavailableReason,
    _canonical,
    _validated_closure_wires,
    derive_workflow_issue_activity_head,
    derive_workflow_issue_activity_horizon,
    derive_workflow_issue_activity_member,
    derive_workflow_issue_activity_owner_observation,
    derive_workflow_issue_activity_selection,
    derive_workflow_issue_activity_unavailable,
)
from .codec import _event, _issue
from .contracts import AuthorityKind, IssueTimeAuthority


def _fail(code: str) -> NoReturn:
    raise WorkflowIssueActivityObservationError(code)


def _obj(value: object, keys: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        _fail("invalid_wire_object")
    return cast(dict[str, object], value)


def _array(value: object) -> list[object]:
    if type(value) is not list:
        _fail("invalid_wire_array")
    return cast(list[object], value)


def _str(value: object) -> str:
    if type(value) is not str:
        _fail("invalid_wire_string")
    return cast(str, value)


def _int(value: object) -> int:
    if type(value) is not int:
        _fail("invalid_wire_integer")
    return cast(int, value)


def _nullable_str(value: object) -> str | None:
    return None if value is None else _str(value)


def _owner(raw: object):
    body = _obj(
        raw,
        {
            "schema_version",
            "authority_kind",
            "authority_ref",
            "authority_generation",
            "authority_receipt_ref",
            "store_generation",
            "journal_epoch",
            "earliest_cursor",
            "latest_cursor",
            "next_cursor",
            "owner_observation_ref",
            "owner_observation_digest",
        },
    )
    latest = body["latest_cursor"]
    return derive_workflow_issue_activity_owner_observation(
        authority_kind=AuthorityKind(_str(body["authority_kind"])),
        authority_ref=_str(body["authority_ref"]),
        authority_generation=_int(body["authority_generation"]),
        authority_receipt_ref=_nullable_str(body["authority_receipt_ref"]),
        store_generation=_int(body["store_generation"]),
        journal_epoch=_str(body["journal_epoch"]),
        earliest_cursor=_int(body["earliest_cursor"]),
        latest_cursor=None if latest is None else _int(latest),
        next_cursor=_int(body["next_cursor"]),
    )


def _head(raw: object) -> WorkflowIssueActivityHeadV1:
    body = _obj(
        raw,
        {
            "schema_version",
            "owner_observation",
            "authority_kind",
            "authority_ref",
            "authority_generation",
            "authority_receipt_ref",
            "issue_ref",
            "issue_revision",
            "issue_revision_ref",
            "lifecycle_state",
            "owner_ref",
            "issue_snapshot",
            "issue_snapshot_digest",
            "head_ref",
            "head_digest",
        },
    )
    return derive_workflow_issue_activity_head(
        owner_observation=_owner(body["owner_observation"]),
        issue_snapshot=_issue(cast(Mapping[str, object], body["issue_snapshot"])),
    )


def _outcome(raw: object) -> ActivityOutcome:
    if type(raw) is not dict:
        _fail("invalid_wire_object")
    raw_object = cast(dict[str, object], raw)
    kind = _str(raw_object.get("outcome_kind"))
    if kind == "selected":
        body = _obj(
            raw,
            {
                "schema_version",
                "owner_observation",
                "authority_ref",
                "authority_generation",
                "journal_epoch",
                "event_ref",
                "event_cursor",
                "event_kind",
                "issue_ref",
                "issue_revision",
                "issue_revision_ref",
                "lifecycle_state",
                "activity_at",
                "activity_time_authority",
                "actor_execution_ref",
                "source_receipt_ref",
                "affected_refs",
                "issue_snapshot",
                "issue_snapshot_digest",
                "event",
                "activity_ref",
                "activity_digest",
                "outcome_kind",
            },
        )
        return derive_workflow_issue_activity_member(
            owner_observation=_owner(body["owner_observation"]),
            issue_snapshot=_issue(cast(Mapping[str, object], body["issue_snapshot"])),
            event=_event(cast(Mapping[str, object], body["event"])),
            activity_at=_str(body["activity_at"]),
            activity_time_authority=IssueTimeAuthority(
                _str(body["activity_time_authority"])
            ),
            actor_execution_ref=_nullable_str(body["actor_execution_ref"]),
        )
    if kind == "unavailable":
        body = _obj(
            raw,
            {
                "schema_version",
                "owner_observation",
                "authority_kind",
                "authority_ref",
                "authority_generation",
                "authority_receipt_ref",
                "store_generation",
                "journal_epoch",
                "issue_ref",
                "selection_kind",
                "requested_issue_revision_ref",
                "reason",
                "detail",
                "observed_at",
                "unavailable_ref",
                "unavailable_digest",
                "outcome_kind",
            },
        )
        return derive_workflow_issue_activity_unavailable(
            owner_observation=_owner(body["owner_observation"]),
            issue_ref=_str(body["issue_ref"]),
            selection_kind=WorkflowIssueActivitySelectionKind(
                _str(body["selection_kind"])
            ),
            requested_issue_revision_ref=_nullable_str(
                body["requested_issue_revision_ref"]
            ),
            reason=WorkflowIssueActivityUnavailableReason(_str(body["reason"])),
            detail=_str(body["detail"]),
            observed_at=_str(body["observed_at"]),
        )
    _fail("invalid_outcome_kind")


def _horizon(
    raw: object,
    outcomes: tuple[ActivityOutcome, ...],
    heads: tuple[WorkflowIssueActivityHeadV1, ...],
) -> WorkflowIssueActivityHorizonV1:
    body = _obj(
        raw,
        {
            "schema_version",
            "owner_observation",
            "observed_at",
            "heads",
            "outcome_coordinates",
            "head_closure_digest",
            "outcome_closure_digest",
            "horizon_ref",
            "horizon_digest",
        },
    )
    owner = _owner(body["owner_observation"])
    return derive_workflow_issue_activity_horizon(
        owner_observation=owner,
        observed_at=_str(body["observed_at"]),
        heads=tuple(item for item in heads if item.owner_observation == owner),
        outcomes=outcomes,
    )


def _selection(
    raw: object,
    horizons: tuple[WorkflowIssueActivityHorizonV1, ...],
    outcomes: tuple[ActivityOutcome, ...],
) -> WorkflowIssueActivitySelectionV1:
    body = _obj(
        raw,
        {
            "schema_version",
            "horizon_ref",
            "horizon_digest",
            "selection_kind",
            "issue_ref",
            "requested_issue_revision_ref",
            "outcome_kind",
            "outcome_ref",
            "outcome_digest",
            "selection_ref",
            "selection_digest",
        },
    )
    href = _str(body["horizon_ref"])
    oref = _str(body["outcome_ref"])
    hs = [x for x in horizons if x.horizon_ref == href]
    os = [
        x
        for x in outcomes
        if (
            x.activity_ref
            if isinstance(x, WorkflowIssueActivityMemberV1)
            else x.unavailable_ref
        )
        == oref
    ]
    if len(hs) != 1 or len(os) != 1:
        _fail("selection_closure_mismatch")
    return derive_workflow_issue_activity_selection(
        horizon=hs[0],
        selection_kind=WorkflowIssueActivitySelectionKind(_str(body["selection_kind"])),
        issue_ref=_str(body["issue_ref"]),
        requested_issue_revision_ref=_nullable_str(
            body["requested_issue_revision_ref"]
        ),
        outcome=os[0],
    )


def encode_workflow_issue_activity_observation_closure(
    *,
    heads: tuple[WorkflowIssueActivityHeadV1, ...],
    horizons: tuple[WorkflowIssueActivityHorizonV1, ...],
    outcomes: tuple[ActivityOutcome, ...],
    selections: tuple[WorkflowIssueActivitySelectionV1, ...],
) -> bytes:
    head_wires, horizon_wires, outcome_wires, selection_wires = (
        _validated_closure_wires(
            heads=heads, horizons=horizons, outcomes=outcomes, selections=selections
        )
    )
    root = {
        "heads": head_wires,
        "horizons": horizon_wires,
        "outcomes": outcome_wires,
        "schema_version": WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA,
        "selections": selection_wires,
    }
    return _canonical(root)


def _fast_owner(value):
    return {
        name: (
            getattr(value, name).value
            if name == "authority_kind"
            else getattr(value, name)
        )
        for name in (
            "schema_version",
            "authority_kind",
            "authority_ref",
            "authority_generation",
            "authority_receipt_ref",
            "store_generation",
            "journal_epoch",
            "earliest_cursor",
            "latest_cursor",
            "next_cursor",
            "owner_observation_ref",
            "owner_observation_digest",
        )
    }


def _fast_head(value):
    return {
        "schema_version": value.schema_version,
        "owner_observation": _fast_owner(value.owner_observation),
        "authority_kind": value.authority_kind.value,
        "authority_ref": value.authority_ref,
        "authority_generation": value.authority_generation,
        "authority_receipt_ref": value.authority_receipt_ref,
        "issue_ref": value.issue_ref,
        "issue_revision": value.issue_revision,
        "issue_revision_ref": value.issue_revision_ref,
        "lifecycle_state": value.lifecycle_state.value,
        "owner_ref": value.owner_ref,
        "issue_snapshot": value.issue_snapshot.to_wire(),
        "issue_snapshot_digest": value.issue_snapshot_digest,
        "head_ref": value.head_ref,
        "head_digest": value.head_digest,
    }


def _fast_outcome(value: ActivityOutcome):
    if isinstance(value, WorkflowIssueActivityMemberV1):
        return {
            "schema_version": value.schema_version,
            "owner_observation": _fast_owner(value.owner_observation),
            "authority_ref": value.authority_ref,
            "authority_generation": value.authority_generation,
            "journal_epoch": value.journal_epoch,
            "event_ref": value.event_ref,
            "event_cursor": value.event_cursor,
            "event_kind": value.event_kind.value,
            "issue_ref": value.issue_ref,
            "issue_revision": value.issue_revision,
            "issue_revision_ref": value.issue_revision_ref,
            "lifecycle_state": value.lifecycle_state.value,
            "activity_at": value.activity_at,
            "activity_time_authority": value.activity_time_authority.value,
            "actor_execution_ref": value.actor_execution_ref,
            "source_receipt_ref": value.source_receipt_ref,
            "affected_refs": list(value.affected_refs),
            "issue_snapshot": value.issue_snapshot.to_wire(),
            "issue_snapshot_digest": value.issue_snapshot_digest,
            "event": value.event.to_wire(),
            "activity_ref": value.activity_ref,
            "activity_digest": value.activity_digest,
            "outcome_kind": "selected",
        }
    return {
        "schema_version": value.schema_version,
        "owner_observation": _fast_owner(value.owner_observation),
        "authority_kind": value.authority_kind.value,
        "authority_ref": value.authority_ref,
        "authority_generation": value.authority_generation,
        "authority_receipt_ref": value.authority_receipt_ref,
        "store_generation": value.store_generation,
        "journal_epoch": value.journal_epoch,
        "issue_ref": value.issue_ref,
        "selection_kind": value.selection_kind.value,
        "requested_issue_revision_ref": value.requested_issue_revision_ref,
        "reason": value.reason.value,
        "detail": value.detail,
        "observed_at": value.observed_at,
        "unavailable_ref": value.unavailable_ref,
        "unavailable_digest": value.unavailable_digest,
        "outcome_kind": "unavailable",
    }


def _fast_horizon(value):
    return {
        "schema_version": value.schema_version,
        "owner_observation": _fast_owner(value.owner_observation),
        "observed_at": value.observed_at,
        "heads": [_fast_head(item) for item in value.heads],
        "outcome_coordinates": [list(item) for item in value.outcome_coordinates],
        "head_closure_digest": value.head_closure_digest,
        "outcome_closure_digest": value.outcome_closure_digest,
        "horizon_ref": value.horizon_ref,
        "horizon_digest": value.horizon_digest,
    }


def _fast_selection(value):
    return {
        "schema_version": value.schema_version,
        "horizon_ref": value.horizon_ref,
        "horizon_digest": value.horizon_digest,
        "selection_kind": value.selection_kind.value,
        "issue_ref": value.issue_ref,
        "requested_issue_revision_ref": value.requested_issue_revision_ref,
        "outcome_kind": value.outcome_kind.value,
        "outcome_ref": value.outcome_ref,
        "outcome_digest": value.outcome_digest,
        "selection_ref": value.selection_ref,
        "selection_digest": value.selection_digest,
    }


def _validate_decoded_shape(heads, horizons, outcomes, selections) -> None:
    if heads != tuple(
        sorted(
            heads,
            key=lambda item: (
                item.owner_observation.owner_observation_ref.encode(),
                item.issue_ref.encode(),
            ),
        )
    ):
        _fail("noncanonical_order")
    if horizons != tuple(
        sorted(
            horizons,
            key=lambda item: item.owner_observation.owner_observation_ref.encode(),
        )
    ):
        _fail("noncanonical_order")

    def outcome_key(item):
        return (
            item.owner_observation.owner_observation_ref.encode(),
            item.issue_ref.encode(),
            (
                "selected"
                if isinstance(item, WorkflowIssueActivityMemberV1)
                else "unavailable"
            ).encode(),
            (
                item.activity_ref
                if isinstance(item, WorkflowIssueActivityMemberV1)
                else item.unavailable_ref
            ).encode(),
        )

    if outcomes != tuple(sorted(outcomes, key=outcome_key)):
        _fail("noncanonical_order")
    if selections != tuple(
        sorted(
            selections,
            key=lambda item: _canonical(
                [
                    item.horizon_ref,
                    item.issue_ref,
                    item.selection_kind.value,
                    item.requested_issue_revision_ref,
                ]
            ),
        )
    ):
        _fail("noncanonical_order")
    expected = {
        (h.horizon_ref, ref) for h in horizons for _, ref in h.outcome_coordinates
    }
    actual = {(s.horizon_ref, s.outcome_ref) for s in selections}
    if len(actual) != len(selections) or actual != expected:
        _fail("selection_completeness_mismatch")
    if {
        (h.owner_observation.owner_observation_ref, item.head_ref)
        for h in horizons
        for item in h.heads
    } != {
        (item.owner_observation.owner_observation_ref, item.head_ref) for item in heads
    }:
        _fail("head_completeness_mismatch")


def decode_workflow_issue_activity_observation_closure(payload: bytes):
    if (
        type(payload) is not bytes
        or len(payload) > MAX_WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_BYTES
    ):
        _fail("invalid_payload")

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                _fail("duplicate_json_key")
            result[key] = value
        return result

    try:
        raw = json.loads(payload, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkflowIssueActivityObservationError("invalid_json") from exc
    root = _obj(raw, {"heads", "horizons", "outcomes", "schema_version", "selections"})
    if root["schema_version"] != WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA:
        _fail("schema_mismatch")
    outcomes = tuple(_outcome(x) for x in _array(root["outcomes"]))
    heads = tuple(_head(x) for x in _array(root["heads"]))
    outcome_groups: dict[str, list[ActivityOutcome]] = {}
    for outcome in outcomes:
        outcome_groups.setdefault(
            outcome.owner_observation.owner_observation_ref, []
        ).append(outcome)
    horizon_values = []
    for raw_horizon in _array(root["horizons"]):
        horizon_object = cast(dict[str, object], raw_horizon)
        owner = _owner(horizon_object["owner_observation"])
        horizon_values.append(
            _horizon(
                raw_horizon,
                tuple(outcome_groups.get(owner.owner_observation_ref, ())),
                heads,
            )
        )
    horizons = tuple(horizon_values)
    selections = tuple(
        _selection(x, horizons, outcomes) for x in _array(root["selections"])
    )
    _validate_decoded_shape(heads, horizons, outcomes, selections)
    expected = _canonical(
        {
            "heads": [_fast_head(x) for x in heads],
            "horizons": [_fast_horizon(x) for x in horizons],
            "outcomes": [_fast_outcome(x) for x in outcomes],
            "schema_version": WORKFLOW_ISSUE_ACTIVITY_OBSERVATION_SCHEMA,
            "selections": [_fast_selection(x) for x in selections],
        }
    )
    if payload != expected:
        _fail("noncanonical_payload")
    return heads, horizons, outcomes, selections
