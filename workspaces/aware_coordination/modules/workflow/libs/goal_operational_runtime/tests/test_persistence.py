from __future__ import annotations

import json

import pytest

from aware_goal_operational_runtime import (
    GoalEventKind,
    GoalJournal,
    GoalOperationalRecord,
    InMemoryGoalStateStore,
    ReplayOutcome,
    decode_goal_operational_record,
    encode_goal_operational_record,
)
from aware_goal_operational_runtime.persistence import (
    append_journal_event,
    replay_journal,
)


def test_record_codec_round_trips_and_rejects_unknown_structure(state) -> None:
    record = GoalOperationalRecord(
        authority_ref=state.authority.authority_ref,
        state=state,
        journal=GoalJournal(epoch="epoch-1", retention_limit=4),
    )
    encoded = encode_goal_operational_record(record)
    assert decode_goal_operational_record(encoded) == record

    raw = json.loads(encoded)
    raw["unexpected"] = True
    with pytest.raises(ValueError, match="keys"):
        decode_goal_operational_record(json.dumps(raw))


def test_atomic_store_compare_and_set_reports_current_generation(state) -> None:
    store = InMemoryGoalStateStore()
    authority_ref = state.authority.authority_ref
    initial = encode_goal_operational_record(
        GoalOperationalRecord(
            authority_ref=authority_ref,
            state=state,
            journal=GoalJournal(epoch="epoch-1", retention_limit=4),
        )
    )
    created = store.create(authority_ref, initial)
    changed = store.compare_and_set(
        authority_ref,
        expected_generation=0,
        payload=initial,
    )
    stale = store.compare_and_set(
        authority_ref,
        expected_generation=0,
        payload=initial,
    )
    assert created.applied and created.current.generation == 0
    assert changed.applied and changed.current.generation == 1
    assert not stale.applied and stale.current.generation == 1


def test_bounded_journal_reports_events_gap_reset_and_ahead(state) -> None:
    record = GoalOperationalRecord(
        authority_ref=state.authority.authority_ref,
        state=state,
        journal=GoalJournal(epoch="epoch-1", retention_limit=2),
    )
    for generation in range(1, 4):
        record = append_journal_event(
            record,
            kind=GoalEventKind.GOAL_CHANGED,
            client_intent_id=f"intent:{generation}",
            store_generation=generation,
            receipt_ref=f"receipt:{generation}",
            state_digest=f"sha256:{generation}",
        )

    events = replay_journal(record, epoch="epoch-1", after_cursor=1)
    gap = replay_journal(record, epoch="epoch-1", after_cursor=0)
    reset = replay_journal(record, epoch="old", after_cursor=0)
    ahead = replay_journal(record, epoch="epoch-1", after_cursor=9)
    assert events.outcome is ReplayOutcome.EVENTS
    assert tuple(event.cursor for event in events.events) == (2, 3)
    assert gap.outcome is ReplayOutcome.GAP and gap.reset_record == record
    assert reset.outcome is ReplayOutcome.RESET and reset.reset_record == record
    assert ahead.outcome is ReplayOutcome.AHEAD
