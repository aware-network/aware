from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ProgramTurnTransition(str, Enum):
    """Canonical transition choices after one instruction checkpoint."""

    stay_in_turn = "stay_in_turn"
    switch_turn_continue_run = "switch_turn_continue_run"
    switch_turn_wait_signal = "switch_turn_wait_signal"
    terminal_program_run = "terminal_program_run"


@dataclass(frozen=True, slots=True)
class ProgramTurnDecision:
    transition: ProgramTurnTransition
    reason: str


@dataclass(frozen=True, slots=True)
class ProgramTurnDecisionContext:
    """Runtime checkpoint context for turn-transition decisions."""

    instruction_kind: str
    step_index: int
    total_steps: int
    invokes_in_turn: int = 0
    elapsed_ms_in_turn: int = 0
    awaiting_external_signal: bool = False
    instruction_failed: bool = False


class ProgramTurnSemanticsPolicy(Protocol):
    def decide(self, *, context: ProgramTurnDecisionContext) -> ProgramTurnDecision: ...


class DefaultProgramTurnSemanticsPolicy:
    """Default long-term semantics for `ProgramRun -> Turn` checkpointing.

    Contract:
    - One turn may execute multiple invoke instructions.
    - Input-like instructions force a turn switch and wait for external signal.
    - Budget boundaries may switch turn while keeping run active.
    - Plan exhaustion or hard failure terminalizes the program run.
    """

    _max_invokes_per_turn: int
    _max_turn_elapsed_ms: int

    def __init__(
        self,
        *,
        max_invokes_per_turn: int = 8,
        max_turn_elapsed_ms: int = 15_000,
    ) -> None:
        self._max_invokes_per_turn = max(int(max_invokes_per_turn), 1)
        self._max_turn_elapsed_ms = max(int(max_turn_elapsed_ms), 1)

    def decide(self, *, context: ProgramTurnDecisionContext) -> ProgramTurnDecision:
        instruction_kind = self._normalize_instruction_kind(context.instruction_kind)
        if context.instruction_failed:
            return ProgramTurnDecision(
                transition=ProgramTurnTransition.terminal_program_run,
                reason="instruction_failed",
            )
        if bool(context.awaiting_external_signal):
            return ProgramTurnDecision(
                transition=ProgramTurnTransition.switch_turn_wait_signal,
                reason="awaiting_external_signal",
            )
        if self._is_input_instruction(instruction_kind):
            return ProgramTurnDecision(
                transition=ProgramTurnTransition.switch_turn_wait_signal,
                reason="input_instruction_requires_runtime_unlock",
            )
        if context.invokes_in_turn >= self._max_invokes_per_turn:
            return ProgramTurnDecision(
                transition=ProgramTurnTransition.switch_turn_continue_run,
                reason="invoke_budget_reached",
            )
        if context.elapsed_ms_in_turn >= self._max_turn_elapsed_ms:
            return ProgramTurnDecision(
                transition=ProgramTurnTransition.switch_turn_continue_run,
                reason="turn_time_budget_reached",
            )
        if self._is_last_step(
            step_index=context.step_index,
            total_steps=context.total_steps,
        ):
            return ProgramTurnDecision(
                transition=ProgramTurnTransition.terminal_program_run,
                reason="plan_exhausted",
            )
        return ProgramTurnDecision(
            transition=ProgramTurnTransition.stay_in_turn,
            reason="continue_current_turn",
        )

    @staticmethod
    def _normalize_instruction_kind(raw: str) -> str:
        return str(raw or "").strip().casefold()

    @staticmethod
    def _is_last_step(*, step_index: int, total_steps: int) -> bool:
        total = max(int(total_steps), 0)
        if total <= 0:
            return True
        return int(step_index) >= total - 1

    @staticmethod
    def _is_input_instruction(instruction_kind: str) -> bool:
        if not instruction_kind:
            return False
        if instruction_kind in {
            "input",
            "plan_input",
            "program_config_instruction_input",
        }:
            return True
        return instruction_kind.endswith(".program_config_instruction_input")
