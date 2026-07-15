from __future__ import annotations

from aware_experience.program.turn_semantics import (
    DefaultProgramTurnSemanticsPolicy,
    ProgramTurnDecisionContext,
    ProgramTurnTransition,
)


def test_input_instruction_forces_turn_switch_and_wait_signal() -> None:
    policy = DefaultProgramTurnSemanticsPolicy()
    decision = policy.decide(
        context=ProgramTurnDecisionContext(
            instruction_kind="program_config_instruction_input",
            step_index=0,
            total_steps=5,
        )
    )
    assert decision.transition == ProgramTurnTransition.switch_turn_wait_signal
    assert decision.reason == "input_instruction_requires_runtime_unlock"


def test_fully_qualified_input_instruction_forces_wait_signal() -> None:
    policy = DefaultProgramTurnSemanticsPolicy()
    decision = policy.decide(
        context=ProgramTurnDecisionContext(
            instruction_kind="program.program_config_instruction_input",
            step_index=1,
            total_steps=4,
        )
    )
    assert decision.transition == ProgramTurnTransition.switch_turn_wait_signal


def test_invoke_under_budget_stays_in_turn() -> None:
    policy = DefaultProgramTurnSemanticsPolicy(max_invokes_per_turn=4)
    decision = policy.decide(
        context=ProgramTurnDecisionContext(
            instruction_kind="invoke",
            step_index=1,
            total_steps=4,
            invokes_in_turn=2,
            elapsed_ms_in_turn=500,
        )
    )
    assert decision.transition == ProgramTurnTransition.stay_in_turn
    assert decision.reason == "continue_current_turn"


def test_invoke_budget_reached_switches_turn_and_continues_run() -> None:
    policy = DefaultProgramTurnSemanticsPolicy(max_invokes_per_turn=3)
    decision = policy.decide(
        context=ProgramTurnDecisionContext(
            instruction_kind="invoke",
            step_index=1,
            total_steps=8,
            invokes_in_turn=3,
            elapsed_ms_in_turn=300,
        )
    )
    assert decision.transition == ProgramTurnTransition.switch_turn_continue_run
    assert decision.reason == "invoke_budget_reached"


def test_elapsed_budget_reached_switches_turn_and_continues_run() -> None:
    policy = DefaultProgramTurnSemanticsPolicy(max_turn_elapsed_ms=1000)
    decision = policy.decide(
        context=ProgramTurnDecisionContext(
            instruction_kind="let",
            step_index=2,
            total_steps=8,
            invokes_in_turn=1,
            elapsed_ms_in_turn=1000,
        )
    )
    assert decision.transition == ProgramTurnTransition.switch_turn_continue_run
    assert decision.reason == "turn_time_budget_reached"


def test_last_step_terminalizes_program_run() -> None:
    policy = DefaultProgramTurnSemanticsPolicy()
    decision = policy.decide(
        context=ProgramTurnDecisionContext(
            instruction_kind="invoke",
            step_index=2,
            total_steps=3,
            invokes_in_turn=1,
        )
    )
    assert decision.transition == ProgramTurnTransition.terminal_program_run
    assert decision.reason == "plan_exhausted"


def test_failed_instruction_terminalizes_program_run() -> None:
    policy = DefaultProgramTurnSemanticsPolicy()
    decision = policy.decide(
        context=ProgramTurnDecisionContext(
            instruction_kind="invoke",
            step_index=0,
            total_steps=5,
            instruction_failed=True,
        )
    )
    assert decision.transition == ProgramTurnTransition.terminal_program_run
    assert decision.reason == "instruction_failed"
