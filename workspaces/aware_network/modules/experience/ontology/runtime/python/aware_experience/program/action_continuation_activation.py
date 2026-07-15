from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.stable_ids import stable_api_call_id
from aware_experience.action_dispatch.fulfillment import (
    ActionDispatchTerminalOutcome,
    ActionTerminalFulfillmentError,
    ActionTerminalFulfillmentInvoker,
    invoke_terminal_action_fulfillment,
)
from aware_experience.program.action_continuation_graph import (
    ProgramActionContinuationActivationInput,
    ProgramActionContinuationCompositeResult,
    ProgramActionContinuationGraphError,
    ProgramActionContinuationGraphResult,
    ProgramActionContinuationGraphStep,
    execute_program_action_continuation_graph,
)
from aware_experience.program.action_continuation_hydration import (
    ProgramActionContinuationHydrationError,
    hydrate_program_action_continuation_graph,
)
from aware_experience.program.snapshot_contract import ProgramOntologySnapshot
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_reactivity_ontology.action.action_config import ActionConfig


_PROGRAM_CONTINUATION_CALL_KEY_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/program-action-continuation/api-call/v1",
)


class ProgramActionContinuationActivationError(ValueError):
    """A committed continuation graph could not activate safely."""


class ProgramActionContinuationSnapshotResolver(Protocol):
    async def resolve_action_continuation_candidates(
        self,
        *,
        action_config_id: UUID,
        event_config_id: UUID,
    ) -> tuple[ProgramOntologySnapshot, ...]: ...


class ProgramActionContinuationActivationRuntime(Protocol):
    async def activate(
        self,
        *,
        initial_action_config_id: UUID,
        initial_event_config_id: UUID,
        initial_api_capability_endpoint_id: UUID,
        initial_outcome: ActionDispatchTerminalOutcome,
    ) -> ProgramActionContinuationActivationResult | None: ...


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationEndpointRoute:
    api_capability_endpoint_id: UUID
    endpoint_ref: str
    discriminant: str


@dataclass(frozen=True, slots=True)
class ProgramActionContinuationActivationResult:
    program_config_id: UUID
    program_impl_id: UUID
    initial_program_impl_instruction_intent_id: UUID
    graph_result: ProgramActionContinuationGraphResult


@dataclass(frozen=True, slots=True)
class HydratedProgramActionContinuationActivationRuntime:
    snapshot_resolver: ProgramActionContinuationSnapshotResolver
    action_configs_by_id: Mapping[UUID, ActionConfig]
    api_capability_endpoints_by_id: Mapping[UUID, ApiCapabilityEndpoint]
    class_configs_by_id: Mapping[UUID, ClassConfig]
    endpoint_routes_by_id: Mapping[UUID, ProgramActionContinuationEndpointRoute]
    activation_inputs_by_key: Mapping[str, ProgramActionContinuationActivationInput]
    terminal_fulfillment_invoker: ActionTerminalFulfillmentInvoker

    async def activate(
        self,
        *,
        initial_action_config_id: UUID,
        initial_event_config_id: UUID,
        initial_api_capability_endpoint_id: UUID,
        initial_outcome: ActionDispatchTerminalOutcome,
    ) -> ProgramActionContinuationActivationResult | None:
        if not initial_outcome.succeeded:
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_initial_outcome_not_succeeded"
            )
        if (
            initial_outcome.api_capability_endpoint_id
            != initial_api_capability_endpoint_id
        ):
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_initial_endpoint_mismatch"
            )
        candidates = (
            await self.snapshot_resolver.resolve_action_continuation_candidates(
                action_config_id=initial_action_config_id,
                event_config_id=initial_event_config_id,
            )
        )
        if not candidates:
            return None
        if len(candidates) != 1:
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_activation_ambiguous"
            )
        snapshot = candidates[0]
        try:
            hydrated = hydrate_program_action_continuation_graph(
                snapshot=snapshot,
                action_configs_by_id=self.action_configs_by_id,
                api_capability_endpoints_by_id=(self.api_capability_endpoints_by_id),
                class_configs_by_id=self.class_configs_by_id,
            )
        except ProgramActionContinuationHydrationError as exc:
            raise ProgramActionContinuationActivationError(str(exc)) from exc

        initial_matches = [
            intent
            for intent_id in hydrated.initial_program_impl_instruction_intent_ids
            if (intent := snapshot.instruction_intents_by_id.get(intent_id)) is not None
            and intent.action_config_id == initial_action_config_id
            and intent.event_config_id == initial_event_config_id
        ]
        if len(initial_matches) != 1:
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_initial_intent_unresolved"
            )
        initial_intent = initial_matches[0]
        if (
            initial_intent.api_capability_endpoint_id
            != initial_api_capability_endpoint_id
        ):
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_initial_intent_endpoint_mismatch"
            )
        if (
            initial_intent.response_class_config_id
            != initial_outcome.response_class_config_id
        ):
            raise ProgramActionContinuationActivationError(
                "program_action_continuation_initial_response_class_mismatch"
            )

        async def dispatch(
            step: ProgramActionContinuationGraphStep,
            continuation: ProgramActionContinuationCompositeResult,
        ) -> ActionDispatchTerminalOutcome:
            route = self.endpoint_routes_by_id.get(
                step.target_api_capability_endpoint_id
            )
            if route is None:
                raise ProgramActionContinuationActivationError(
                    "program_action_continuation_endpoint_route_missing:"
                    + str(step.target_api_capability_endpoint_id)
                )
            if (
                route.api_capability_endpoint_id
                != step.target_api_capability_endpoint_id
            ):
                raise ProgramActionContinuationActivationError(
                    "program_action_continuation_endpoint_route_mismatch"
                )
            call_key = derive_program_action_continuation_api_call_key(
                initial_api_call_key=initial_outcome.api_call_key,
                program_impl_id=snapshot.program_impl.id,
                target_program_impl_instruction_intent_id=(
                    step.target_program_impl_instruction_intent_id
                ),
            )
            try:
                return await invoke_terminal_action_fulfillment(
                    invoker=self.terminal_fulfillment_invoker,
                    endpoint_ref=route.endpoint_ref,
                    discriminant=route.discriminant,
                    request_values=continuation.request_payload,
                    api_call_key=call_key,
                    expected_api_call_id=stable_api_call_id(
                        api_capability_endpoint_id=(
                            step.target_api_capability_endpoint_id
                        ),
                        call_key=call_key,
                    ),
                    expected_api_capability_endpoint_id=(
                        step.target_api_capability_endpoint_id
                    ),
                    response_class_config_id=(step.target_response_class_config_id),
                )
            except ActionTerminalFulfillmentError as exc:
                raise ProgramActionContinuationActivationError(str(exc)) from exc

        try:
            graph_result = await execute_program_action_continuation_graph(
                initial_outcomes_by_instruction_intent_id={
                    initial_intent.id: initial_outcome
                },
                activation_inputs_by_key=self.activation_inputs_by_key,
                steps=hydrated.steps,
                dispatch=dispatch,
                class_configs_by_id=self.class_configs_by_id,
            )
        except ProgramActionContinuationGraphError as exc:
            raise ProgramActionContinuationActivationError(str(exc)) from exc
        return ProgramActionContinuationActivationResult(
            program_config_id=snapshot.program_config.id,
            program_impl_id=snapshot.program_impl.id,
            initial_program_impl_instruction_intent_id=initial_intent.id,
            graph_result=graph_result,
        )


def derive_program_action_continuation_api_call_key(
    *,
    initial_api_call_key: UUID,
    program_impl_id: UUID,
    target_program_impl_instruction_intent_id: UUID,
) -> UUID:
    return uuid5(
        _PROGRAM_CONTINUATION_CALL_KEY_NAMESPACE,
        (
            f"{initial_api_call_key}:{program_impl_id}:"
            f"{target_program_impl_instruction_intent_id}"
        ),
    )


__all__ = [
    "HydratedProgramActionContinuationActivationRuntime",
    "ProgramActionContinuationActivationError",
    "ProgramActionContinuationActivationResult",
    "ProgramActionContinuationActivationRuntime",
    "ProgramActionContinuationEndpointRoute",
    "ProgramActionContinuationSnapshotResolver",
    "derive_program_action_continuation_api_call_key",
]
