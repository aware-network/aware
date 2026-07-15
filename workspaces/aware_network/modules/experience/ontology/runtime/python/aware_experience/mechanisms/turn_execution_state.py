from __future__ import annotations

# Experience Ontology
from aware_experience_ontology.turn.turn_enums import (
    TurnExecutionState,
    TurnExecutionTerminalStatus,
)


def normalized_turn_state_value(state: TurnExecutionState | str | None) -> str:
    if state is None:
        return ""
    raw = getattr(state, "value", state)
    return str(raw or "").strip().casefold()


def normalized_turn_terminal_status_value(
    status: TurnExecutionTerminalStatus | str | None,
) -> str:
    if status is None:
        return ""
    raw = getattr(status, "value", status)
    return str(raw or "").strip().casefold()
