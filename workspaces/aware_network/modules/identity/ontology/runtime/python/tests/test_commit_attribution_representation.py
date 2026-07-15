from __future__ import annotations

from uuid import UUID

import pytest

from aware_identity.representation import (
    build_commit_attribution_entries,
    parse_actor_label_mappings,
    render_commit_timeline_lines,
    resolve_actor_labels,
)


def test_parse_actor_label_mappings_requires_actor_uuid() -> None:
    with pytest.raises(ValueError, match="expected <actor_uuid>=<label>"):
        parse_actor_label_mappings(["human"])


def test_resolve_actor_labels_sets_primary_default() -> None:
    actor_id = UUID("00000000-0000-0000-0000-0000000000aa")
    labels = resolve_actor_labels(primary_actor_id=actor_id, raw_mappings=[])
    assert labels[str(actor_id)] == "human"


def test_build_and_render_commit_timeline_entries() -> None:
    human_actor = "00000000-0000-0000-0000-000000000001"
    agent_actor = "00000000-0000-0000-0000-000000000002"
    labels = {
        human_actor: "human:default",
        agent_actor: "agent:default",
    }
    receipts = [
        {
            "actor_id": human_actor,
            "branch_id": "00000000-0000-0000-0000-000000000011",
            "projection_hash": "abcdef0123456789",
            "commit_id": "00000000-0000-0000-0000-000000000111",
            "operation_label": "Conversation.add_message",
            "head_version": 4,
        },
        {
            "actor_id": agent_actor,
            "branch_id": "00000000-0000-0000-0000-000000000022",
            "projection_hash": "0123456789abcdef",
            "commit_id": "00000000-0000-0000-0000-000000000222",
            "operation_label": "Event.add_action",
            "head_version": 5,
        },
    ]

    entries = build_commit_attribution_entries(
        commit_receipts=receipts,
        actor_labels=labels,
    )

    assert len(entries) == 2
    assert entries[0].actor_label == "human:default"
    assert entries[1].operation_label == "Event.add_action"

    lines = render_commit_timeline_lines(entries=entries, limit=10)
    assert lines[0] == "turn.commit_timeline count=2"
    assert "actor=human:default" in lines[1]
    assert "op=Conversation.add_message" in lines[1]
    assert "actor=agent:default" in lines[2]
    assert "op=Event.add_action" in lines[2]
