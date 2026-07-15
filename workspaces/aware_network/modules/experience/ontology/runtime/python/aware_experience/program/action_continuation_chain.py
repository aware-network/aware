from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from aware_experience.action_dispatch.fulfillment import (
    ActionDispatchTerminalOutcome,
)
from aware_experience.program.action_continuation import (
    ProgramActionContinuationContract,
    ProgramActionContinuationError,
    ProgramActionContinuationResult,
    compose_program_action_continuation,
)
from aware_meta_ontology.class_.class_config import ClassConfig


class ProgramActionContinuationChainError(ValueError):
    """An explicitly selected continuation chain cannot execute safely."""


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationChainStep:
    contract: ProgramActionContinuationContract
    source_response_class_config: ClassConfig
    target_request_class_config: ClassConfig
    target_response_class_config_id: UUID
    source_receipt_class_config: ClassConfig | None = None


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationChainResult:
    initial_outcome: ActionDispatchTerminalOutcome
    continuations: tuple[ProgramActionContinuationResult, ...]
    dispatched_outcomes: tuple[ActionDispatchTerminalOutcome, ...]

    @property
    def terminal_outcome(self) -> ActionDispatchTerminalOutcome:
        return self.dispatched_outcomes[-1]


ProgramActionContinuationDispatch = Callable[
    [ProgramActionContinuationChainStep, ProgramActionContinuationResult],
    Awaitable[ActionDispatchTerminalOutcome],
]


async def execute_program_action_continuation_chain(
    *,
    initial_outcome: ActionDispatchTerminalOutcome,
    steps: Sequence[ProgramActionContinuationChainStep],
    dispatch: ProgramActionContinuationDispatch,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
) -> ProgramActionContinuationChainResult:
    """Compose and dispatch one explicitly authored continuation sequence."""

    if not steps:
        raise ProgramActionContinuationChainError(
            "program_action_continuation_chain_steps_missing"
        )

    current_outcome = initial_outcome
    continuations: list[ProgramActionContinuationResult] = []
    outcomes: list[ActionDispatchTerminalOutcome] = []
    previous_step: ProgramActionContinuationChainStep | None = None
    for step in steps:
        if previous_step is not None:
            _require_connected_steps(previous=previous_step, current=step)
        try:
            continuation = compose_program_action_continuation(
                contract=step.contract,
                source_outcome=current_outcome,
                source_response_class_config=step.source_response_class_config,
                target_request_class_config=step.target_request_class_config,
                source_receipt_class_config=step.source_receipt_class_config,
                class_configs_by_id=class_configs_by_id,
            )
        except ProgramActionContinuationError as exc:
            raise ProgramActionContinuationChainError(str(exc)) from exc

        target_outcome = await dispatch(step, continuation)
        _require_target_outcome(step=step, outcome=target_outcome)
        continuations.append(continuation)
        outcomes.append(target_outcome)
        current_outcome = target_outcome
        previous_step = step

    return ProgramActionContinuationChainResult(
        initial_outcome=initial_outcome,
        continuations=tuple(continuations),
        dispatched_outcomes=tuple(outcomes),
    )


def _require_connected_steps(
    *,
    previous: ProgramActionContinuationChainStep,
    current: ProgramActionContinuationChainStep,
) -> None:
    previous_contract = previous.contract
    current_contract = current.contract
    if (
        current_contract.source_sequence != previous_contract.target_sequence
        or current_contract.source_program_impl_instruction_intent_id
        != previous_contract.target_program_impl_instruction_intent_id
        or current_contract.source_action_config_id
        != previous_contract.target_action_config_id
        or current_contract.source_api_capability_endpoint_id
        != previous_contract.target_api_capability_endpoint_id
        or current_contract.source_response_class_config_id
        != previous.target_response_class_config_id
    ):
        raise ProgramActionContinuationChainError(
            "program_action_continuation_chain_step_disconnected"
        )


def _require_target_outcome(
    *,
    step: ProgramActionContinuationChainStep,
    outcome: ActionDispatchTerminalOutcome | None,
) -> None:
    if outcome is None:
        raise ProgramActionContinuationChainError(
            "program_action_continuation_chain_target_outcome_missing"
        )
    if not outcome.succeeded:
        raise ProgramActionContinuationChainError(
            "program_action_continuation_chain_target_outcome_not_succeeded"
        )
    if (
        outcome.api_capability_endpoint_id
        != step.contract.target_api_capability_endpoint_id
    ):
        raise ProgramActionContinuationChainError(
            "program_action_continuation_chain_target_endpoint_mismatch"
        )
    if outcome.response_class_config_id != step.target_response_class_config_id:
        raise ProgramActionContinuationChainError(
            "program_action_continuation_chain_target_response_class_mismatch"
        )


__all__ = [
    "ProgramActionContinuationChainError",
    "ProgramActionContinuationChainResult",
    "ProgramActionContinuationChainStep",
    "execute_program_action_continuation_chain",
]
