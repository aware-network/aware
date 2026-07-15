from __future__ import annotations

# Standard
from enum import Enum


class ProgramAttributeType(Enum):
    input = "input"
    output = "output"


class ProgramBranchBindingMode(Enum):
    create = "create"
    reference = "reference"


class ProgramRunStatus(Enum):
    pending = "pending"
    running = "running"
    terminal = "terminal"


class ProgramSlotOnBind(Enum):
    replace = "replace"
    if_empty = "if_empty"
    sticky = "sticky"


class ProgramTurnDecisionReason(Enum):
    continue_current_turn = "continue_current_turn"
    input_instruction_requires_runtime_unlock = "input_instruction_requires_runtime_unlock"
    invoke_budget_reached = "invoke_budget_reached"
    turn_time_budget_reached = "turn_time_budget_reached"
    awaiting_external_signal = "awaiting_external_signal"
    instruction_failed = "instruction_failed"
    plan_exhausted = "plan_exhausted"


class ProgramTurnTransition(Enum):
    stay_in_turn = "stay_in_turn"
    switch_turn_continue_run = "switch_turn_continue_run"
    switch_turn_wait_signal = "switch_turn_wait_signal"
    terminal_program_run = "terminal_program_run"
