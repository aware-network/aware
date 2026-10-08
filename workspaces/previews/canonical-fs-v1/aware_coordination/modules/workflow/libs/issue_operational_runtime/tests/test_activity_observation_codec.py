# pyright: reportMissingImports=false
from __future__ import annotations

import hashlib
import json

import pytest
from test_activity_observation import make_closure

from aware_issue_operational_runtime import (
    WorkflowIssueActivityObservationError,
    decode_workflow_issue_activity_observation_closure,
    encode_workflow_issue_activity_observation_closure,
)


def test_complete_closure_round_trips_canonical_bytes() -> None:
    heads, horizons, outcomes, selections = make_closure()
    payload = encode_workflow_issue_activity_observation_closure(
        heads=heads, horizons=horizons, outcomes=outcomes, selections=selections
    )
    assert len(payload) == 12_788
    assert (
        hashlib.sha256(payload).hexdigest()
        == "ebbe87c5f36b7163ea54976cd48b5ddf53d1360a03e2e4371a1fadfe8e289e81"
    )
    decoded = decode_workflow_issue_activity_observation_closure(payload)
    assert decoded == (heads, horizons, outcomes, selections)
    assert (
        encode_workflow_issue_activity_observation_closure(
            heads=decoded[0],
            horizons=decoded[1],
            outcomes=decoded[2],
            selections=decoded[3],
        )
        == payload
    )


def test_boolean_integer_substitution_rejects() -> None:
    heads, horizons, outcomes, selections = make_closure()
    payload = encode_workflow_issue_activity_observation_closure(
        heads=heads, horizons=horizons, outcomes=outcomes, selections=selections
    )
    poisoned = payload.replace(b'"store_generation":7', b'"store_generation":true')
    with pytest.raises(WorkflowIssueActivityObservationError):
        decode_workflow_issue_activity_observation_closure(poisoned)


def test_coherent_historical_authority_restamp_rejects() -> None:
    heads, horizons, outcomes, selections = make_closure()
    payload = encode_workflow_issue_activity_observation_closure(
        heads=heads, horizons=horizons, outcomes=outcomes, selections=selections
    )
    root = json.loads(payload)
    historical = next(
        item
        for item in root["outcomes"]
        if item["outcome_kind"] == "selected" and item["authority_generation"] == 1
    )
    historical["issue_snapshot"]["authority"]["receipt_ref"] = "receipt:forged"
    poisoned = json.dumps(root, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(WorkflowIssueActivityObservationError):
        decode_workflow_issue_activity_observation_closure(poisoned)


def test_noncanonical_json_and_duplicate_keys_reject() -> None:
    with pytest.raises(WorkflowIssueActivityObservationError):
        decode_workflow_issue_activity_observation_closure(b'{"heads":[], "heads":[]}')


def test_payload_type_and_limit_reject() -> None:
    with pytest.raises(WorkflowIssueActivityObservationError):
        decode_workflow_issue_activity_observation_closure(bytearray(b"{}"))  # pyright: ignore[reportArgumentType]
