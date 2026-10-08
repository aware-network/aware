from __future__ import annotations

import json

import pytest
from aware_issue_operational_runtime import (
    CancellationToken,
    EnsureIssueIntent,
    HostOutcome,
    InMemoryIssueStateStore,
    IssueJournal,
    IssueOperationalRecord,
    IssueOperationalRuntimeHost,
    ReplayOutcome,
    decode_operational_record,
    encode_operational_record,
)
from conftest import context


def test_codec_round_trip_and_unknown_field_rejection(state) -> None:
    record = IssueOperationalRecord(
        state.authority.authority_ref,
        state,
        IssueJournal("epoch-1", 8),
    )
    encoded = encode_operational_record(record)
    assert decode_operational_record(encoded) == record
    raw = json.loads(encoded)
    raw["extra"] = True
    with pytest.raises(ValueError, match="keys"):
        decode_operational_record(json.dumps(raw))


def test_host_persists_receipt_and_replays_bounded_journal(actor, state) -> None:
    host = IssueOperationalRuntimeHost(InMemoryIssueStateStore(), journal_retention=1)
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="epoch-1")
    result = host.submit(
        authority_ref,
        EnsureIssueIntent(
            context(actor, "ensure", issue_revision=None), "fb/demo", "Demo"
        ),
    )
    assert result.receipt is not None
    assert result.receipt.observation_cursor == 1
    replay = host.replay(authority_ref, epoch="epoch-1", after_cursor=0)
    assert replay is not None
    assert replay.outcome is ReplayOutcome.EVENTS
    assert replay.events[0].affected_refs == result.receipt.affected_refs
    reset = host.replay(authority_ref, epoch="old", after_cursor=0)
    assert reset is not None
    assert reset.outcome is ReplayOutcome.RESET
    assert reset.reset_state is not None


def test_cancelled_intent_never_persists(actor, state) -> None:
    host = IssueOperationalRuntimeHost(InMemoryIssueStateStore())
    authority_ref = state.authority.authority_ref
    assert host.admit_authority(authority_ref, state, epoch="epoch-1")
    token = CancellationToken()
    token.cancel()
    result = host.submit(
        authority_ref,
        EnsureIssueIntent(
            context(actor, "ensure", issue_revision=None), "fb/demo", "Demo"
        ),
        cancellation=token,
    )
    assert result.outcome is HostOutcome.CANCELLED
    current = host.read(authority_ref)
    assert current is not None and current.state.issues == ()
