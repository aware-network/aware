from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_runtime.invocation import (
    ApiInvocationDispatchResult,
    ApiInvocationIR,
    ApiInvocationRuntimeProtocol,
    ApiInvocationSourceCommit,
    dispatch_api_invocation,
)
from aware_api_ontology.api.api_capability_endpoint_stream_config import (
    ApiCapabilityEndpointStreamConfig,
)
from aware_api_ontology.api.api_call_stream_event import ApiCallStreamEvent
from aware_code.types import JsonObject
from aware_api_ontology.stable_ids import stable_api_call_id
from aware_api_ontology.api.api_capability_endpoint_stream_enums import (
    ApiCapabilityEndpointStreamEventKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_experience_ontology.action.action_experience import ActionExperience
from aware_experience_ontology.action.action_experience_invocation import (
    ActionExperienceInvocation,
)
from aware_experience_ontology.action.action_experience_invocation_request_field import (
    ActionExperienceInvocationRequestField,
)
from aware_experience_ontology.environment.environment_experience_event import (
    EnvironmentExperienceEvent,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_experience.program.action_continuation import (
    ProgramActionContinuationTargetValues,
)
from aware_reactivity_service_dto.reactivity.action_execution import (
    ActionExecution,
    ReactivityActionExecutionClaimRequest,
    ReactivityActionExecutionClaimResponse,
)
from aware_reactivity_service_dto.reactivity.action_feedback import ActionFeedback
from aware_reactivity_service_dto.reactivity.action_feedback_enums import (
    ActionExecutionClaimStatus,
    ActionExecutionStatus,
    ActionFeedbackStage,
    ActionFeedbackStatus,
    ActionIntentStatus,
    ActionTerminalStatus,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
)
from aware_reactivity_service_dto.reactivity.action_terminal import ActionTerminal
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishRequest,
    ReactivityActionLifecyclePublishResponse,
)

from .composer import (
    ActionDispatchBindingNodeSource,
    ActionDispatchCompositionContext,
    ActionDispatchRequestFieldBinding,
    ActionRequestCompositionError,
    compose_action_request_payload,
)
from .fulfillment import (
    ActionDispatchTerminalOutcome,
    ActionTerminalFulfillmentError,
    ActionTerminalFulfillmentInvoker,
    invoke_terminal_action_fulfillment,
)

if TYPE_CHECKING:
    from aware_experience.program.action_continuation_activation import (
        ProgramActionContinuationActivationResult,
        ProgramActionContinuationActivationRuntime,
    )

ACTION_DISPATCH_PUBLISHER_ID = "experience.action_dispatch"
DEFAULT_EXECUTION_KEY = "primary"
ACTION_DISPATCH_ACCEPTED_REASON = "action_dispatch_accepted"
AMBIGUOUS_BINDING_REASON = "action_dispatch_binding_ambiguous"
MISSING_ACTION_CONFIG_REASON = "action_intent_missing_action_config"
MISSING_ACTION_CONFIG_ANCHOR_REASON = "action_dispatch_action_config_anchor_missing"
MISSING_BINDING_REASON = "action_dispatch_binding_not_found"
NON_API_BINDING_REASON = "action_dispatch_binding_not_api_target"
ENDPOINT_MISMATCH_REASON = "action_dispatch_endpoint_anchor_mismatch"
MISSING_STREAM_EVENT_CONFIG_REASON = "action_dispatch_stream_event_config_missing"
MISSING_ROLE_EVIDENCE_REASON = "action_dispatch_role_evidence_missing"
DENIED_ROLE_EVIDENCE_REASON = "action_dispatch_role_evidence_denied"
AD_HOC_REQUEST_PAYLOAD_REJECTED_REASON = (
    "action_request_composition_ad_hoc_payload_rejected"
)
_ACTION_DISPATCH_CALL_KEY_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/action-dispatch/api-call/v1",
)
_REACTIVITY_STABLE_ID_NAMESPACE = uuid5(NAMESPACE_URL, "aware://reactivity/v1")


class ReactivityActionLifecyclePublisher(Protocol):
    async def publish_action_lifecycle(
        self,
        request: ReactivityActionLifecyclePublishRequest,
    ) -> ReactivityActionLifecyclePublishResponse: ...


class ReactivityActionExecutionClaimer(Protocol):
    async def claim_action_execution(
        self,
        request: ReactivityActionExecutionClaimRequest,
    ) -> ReactivityActionExecutionClaimResponse: ...


class ApiInvocationDispatcher(Protocol):
    async def __call__(
        self,
        *,
        runtime: ApiInvocationRuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        source_lane: MaterializationLaneContext,
        target_lane: MaterializationLaneContext,
        ir: ApiInvocationIR,
        source_commit: ApiInvocationSourceCommit | None = None,
        call_key: UUID | None = None,
        commit: bool = True,
        publish: bool = False,
        receipt_projection_backend: str | None = None,
    ) -> ApiInvocationDispatchResult: ...


@dataclass(frozen=True, slots=True)
class ActionDispatchBinding:
    """Resolved action dispatch policy summary used by the bridge."""

    action_binding_id: UUID
    experience_invocation_action_config_id: UUID
    api_capability_endpoint_id: UUID
    action_config_api_capability_endpoint_id: UUID
    request_class_config_id: UUID | None
    request_class_config: ClassConfig | None = None
    environment_experience_profile_config_id: UUID | None = None
    environment_profile_config_id: UUID | None = None
    environment_profile_key: str | None = None
    environment_experience_event_id: UUID | None = None
    event_config_id: UUID | None = None
    action_experience_id: UUID | None = None
    response_class_config_id: UUID | None = None
    stream_event_class_config_ids: Mapping[str, UUID] | None = None
    role_policies: tuple[ActionDispatchRolePolicy, ...] = ()
    request_fields: tuple[ActionDispatchRequestFieldBinding, ...] = ()
    binding_node_sources: Mapping[str, ActionDispatchBindingNodeSource] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class ActionDispatchRolePolicy:
    role_config_id: UUID
    policy_key: str = "invoke"
    requirement_kind: str = "admitted_actor_role"


@dataclass(frozen=True, slots=True)
class ActionDispatchRoleEvidence:
    role_config_id: UUID
    policy_key: str = "invoke"
    actor_id: UUID | None = None
    role_assignment_binding_id: UUID | None = None
    granted: bool = True


@dataclass(frozen=True, slots=True)
class ActionDispatchRolePreflightResult:
    status: str
    reason: str | None = None
    required_policies: tuple[ActionDispatchRolePolicy, ...] = ()
    accepted_evidence: tuple[ActionDispatchRoleEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class ActionDispatchBindingResolution:
    status: str
    reason: str | None = None
    binding: ActionDispatchBinding | None = None
    candidate_count: int = 0


@dataclass(frozen=True, slots=True)
class ActionDispatchPublishResult:
    status: str
    reason: str | None = None
    action_execution_id: UUID | None = None
    action_feedback_id: UUID | None = None
    action_terminal_status: ActionTerminalStatus | None = None
    published_count: int = 0


@dataclass(frozen=True, slots=True)
class ActionDispatchExecutionStartResult:
    status: str
    reason: str | None = None
    action_execution_id: UUID | None = None
    action_feedback_id: UUID | None = None
    api_call_key: UUID | None = None
    published_count: int = 0


@dataclass(frozen=True, slots=True)
class ActionDispatchApiCallResult:
    status: str
    action_execution_id: UUID
    api_call_id: UUID
    api_capability_endpoint_id: UUID
    call_key: UUID
    request_model_id: UUID
    request_class_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID | None
    projection_hash: str | None


@dataclass(frozen=True, slots=True)
class ActionDispatchBridgeResult:
    status: str
    reason: str | None = None
    binding_resolution: ActionDispatchBindingResolution | None = None
    role_preflight: ActionDispatchRolePreflightResult | None = None
    execution_claim: ReactivityActionExecutionClaimResponse | None = None
    rejection: ActionDispatchPublishResult | None = None
    execution_start: ActionDispatchExecutionStartResult | None = None
    api_call: ActionDispatchApiCallResult | None = None
    terminal_outcome: ActionDispatchTerminalOutcome | None = None
    terminal: ActionDispatchPublishResult | None = None
    program_continuation_activation: (
        ProgramActionContinuationActivationResult | None
    ) = None


def derive_action_dispatch_action_execution_id(
    *,
    action_intent_id: UUID,
    execution_key: str = DEFAULT_EXECUTION_KEY,
) -> UUID:
    """Derive the Reactivity ActionExecution id without creating the row.

    This mirrors Reactivity's compiler-owned stable-id formula so the bridge can
    derive the ApiCall key before publishing the execution correlation through
    the Reactivity service boundary.
    """

    execution_key_norm = (
        execution_key or ""
    ).casefold().strip() or DEFAULT_EXECUTION_KEY
    return uuid5(
        _REACTIVITY_STABLE_ID_NAMESPACE,
        f"aware:action_execution:{action_intent_id}:{execution_key_norm}",
    )


def derive_action_dispatch_api_call_key(*, action_execution_id: UUID) -> UUID:
    """Derive the API call key for one action execution.

    The bridge waits for Reactivity to accept and identify the ActionExecution,
    then derives the ApiCall `call_key` from that durable execution identity.
    Retrying the same execution therefore targets the same ApiCall receipt.
    """

    return uuid5(
        _ACTION_DISPATCH_CALL_KEY_NAMESPACE,
        f"action_execution:{action_execution_id}",
    )


def resolve_action_dispatch_binding_from_environment_profile(
    *,
    profile_config: EnvironmentExperienceProfileConfig,
    intent: ReactivityActionIntent,
    index: MetaGraphRuntimeIndex | None = None,
) -> ActionDispatchBindingResolution:
    """Resolve the A1 chain from one environment-scoped profile config.

    EnvironmentExperienceProfileConfig scopes Event -> Action activation
    policy. The API endpoint is anchored by ActionConfig; Experience must match
    that endpoint and only contributes activation/provenance.
    """

    if intent.action_config_id is None:
        return ActionDispatchBindingResolution(
            status="failed",
            reason=MISSING_ACTION_CONFIG_REASON,
        )

    api_candidates: list[ActionDispatchBinding] = []
    non_api_candidate_count = 0
    for event in profile_config.events:
        for event_action in event.actions:
            action_experience = event_action.action_experience
            if action_experience is None:
                continue
            if action_experience.action_config_id != intent.action_config_id:
                continue
            action_config = action_experience.action_config
            if action_config is None:
                return ActionDispatchBindingResolution(
                    status="failed",
                    reason=MISSING_ACTION_CONFIG_ANCHOR_REASON,
                )
            anchor_endpoint_id = action_config.api_capability_endpoint_id
            if anchor_endpoint_id is None:
                return ActionDispatchBindingResolution(
                    status="failed",
                    reason=MISSING_ACTION_CONFIG_ANCHOR_REASON,
                )
            for invocation in action_experience.action_experience_invocations:
                invocation_config = invocation.experience_invocation_action_config
                if invocation_config is None:
                    continue
                if invocation_config.api_capability_endpoint is None:
                    non_api_candidate_count += 1
                    continue
                activation_endpoint_id = (
                    invocation_config.api_capability_endpoint_id
                    or invocation_config.api_capability_endpoint.id
                )
                if activation_endpoint_id != anchor_endpoint_id:
                    return ActionDispatchBindingResolution(
                        status="failed",
                        reason=ENDPOINT_MISMATCH_REASON,
                    )
                binding = _binding_from_action_experience_invocation(
                    profile_config=profile_config,
                    event=event,
                    action_experience=action_experience,
                    invocation=invocation,
                    invocation_config=invocation_config,
                    anchor_endpoint_id=anchor_endpoint_id,
                    index=index,
                )
                api_candidates.append(binding)

    if not api_candidates and non_api_candidate_count:
        return ActionDispatchBindingResolution(
            status="failed",
            reason=NON_API_BINDING_REASON,
            candidate_count=non_api_candidate_count,
        )
    if not api_candidates:
        return ActionDispatchBindingResolution(
            status="failed",
            reason=MISSING_BINDING_REASON,
        )
    if len(api_candidates) > 1:
        return ActionDispatchBindingResolution(
            status="failed",
            reason=AMBIGUOUS_BINDING_REASON,
            candidate_count=len(api_candidates),
        )
    return ActionDispatchBindingResolution(
        status="resolved",
        binding=api_candidates[0],
        candidate_count=1,
    )


async def dispatch_requested_action_intent(
    *,
    profile_config: EnvironmentExperienceProfileConfig,
    intent: ReactivityActionIntent,
    reactivity: ReactivityActionLifecyclePublisher,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    environment_id: UUID | None = None,
    source_lane: MaterializationLaneContext,
    target_lane: MaterializationLaneContext,
    ir: ApiInvocationIR,
    source_commit: ApiInvocationSourceCommit | None = None,
    request_id: UUID | None = None,
    created_at_unix_ms: int = 0,
    commit: bool = True,
    publish: bool = False,
    receipt_projection_backend: str | None = None,
    publisher_id: str = ACTION_DISPATCH_PUBLISHER_ID,
    role_evidence: tuple[ActionDispatchRoleEvidence, ...] = (),
    subscription_id: UUID | None = None,
    api_dispatcher: ApiInvocationDispatcher = dispatch_api_invocation,
    terminal_fulfillment_invoker: ActionTerminalFulfillmentInvoker | None = None,
    execution_claimer: ReactivityActionExecutionClaimer | None = None,
    program_continuation: ProgramActionContinuationTargetValues | None = None,
    program_continuation_activation_runtime: (
        ProgramActionContinuationActivationRuntime | None
    ) = None,
) -> ActionDispatchBridgeResult:
    """Dispatch one requested intent through the typed action/API bridge.

    The coordinator only composes existing plane-owned ports:
    Experience resolves the binding, Reactivity owns lifecycle publication, and
    API owns ApiCall materialization.
    """

    if intent.status is not ActionIntentStatus.requested:
        return ActionDispatchBridgeResult(
            status="skipped",
            reason="action_intent_not_requested",
        )

    binding_resolution = resolve_action_dispatch_binding_from_environment_profile(
        profile_config=profile_config,
        intent=intent,
        index=index,
    )
    binding = binding_resolution.binding
    if binding is None:
        return ActionDispatchBridgeResult(
            status="binding_failed",
            reason=binding_resolution.reason,
            binding_resolution=binding_resolution,
        )

    role_preflight = validate_action_dispatch_role_preflight(
        binding=binding,
        role_evidence=role_evidence,
    )
    if role_preflight.status != "allowed":
        return ActionDispatchBridgeResult(
            status="role_denied",
            reason=role_preflight.reason,
            binding_resolution=binding_resolution,
            role_preflight=role_preflight,
        )

    action_execution_id = derive_action_dispatch_action_execution_id(
        action_intent_id=intent.action_intent_id,
        execution_key=DEFAULT_EXECUTION_KEY,
    )
    api_call_key = derive_action_dispatch_api_call_key(
        action_execution_id=action_execution_id,
    )
    try:
        resolved_ir = _compose_declared_request_ir(
            ir=ir,
            intent=intent,
            binding=binding,
            action_execution_id=action_execution_id,
            api_call_key=api_call_key,
            actor_id=actor_id,
            environment_id=environment_id,
            subscription_id=subscription_id,
            source_commit=source_commit,
            program_continuation=program_continuation,
        )
    except ActionRequestCompositionError as exc:
        rejection = await publish_action_dispatch_rejection(
            reactivity=reactivity,
            intent=intent,
            binding=binding,
            action_execution_id=action_execution_id,
            request_id=request_id,
            created_at_unix_ms=created_at_unix_ms,
            publisher_id=publisher_id,
            reason=str(exc),
        )
        return ActionDispatchBridgeResult(
            status="composition_rejected",
            reason=str(exc),
            binding_resolution=binding_resolution,
            role_preflight=role_preflight,
            rejection=rejection,
        )
    execution_claim: ReactivityActionExecutionClaimResponse | None = None
    if execution_claimer is not None:
        execution_claim = await execution_claimer.claim_action_execution(
            ReactivityActionExecutionClaimRequest(
                request_id=request_id,
                claimant_id=publisher_id,
                intent=intent,
                execution_key=DEFAULT_EXECUTION_KEY,
                execution_context=JsonObject(
                    {
                        "action_binding_id": str(binding.action_binding_id),
                        "api_capability_endpoint_id": str(
                            binding.api_capability_endpoint_id
                        ),
                    }
                ),
            )
        )
        if not execution_claim.accepted:
            return ActionDispatchBridgeResult(
                status="claim_failed",
                reason=execution_claim.error or "action_execution_claim_rejected",
                binding_resolution=binding_resolution,
                role_preflight=role_preflight,
                execution_claim=execution_claim,
            )
        if execution_claim.claim_status is not ActionExecutionClaimStatus.claimed:
            return ActionDispatchBridgeResult(
                status="claim_replay_skipped",
                reason=(
                    execution_claim.claim_status.value
                    if execution_claim.claim_status is not None
                    else "action_execution_claim_status_missing"
                ),
                binding_resolution=binding_resolution,
                role_preflight=role_preflight,
                execution_claim=execution_claim,
            )
        claimed_execution = execution_claim.action_execution
        if (
            claimed_execution is None
            or claimed_execution.action_execution_id != action_execution_id
        ):
            return ActionDispatchBridgeResult(
                status="claim_failed",
                reason="action_execution_claim_identity_mismatch",
                binding_resolution=binding_resolution,
                role_preflight=role_preflight,
                execution_claim=execution_claim,
            )
    if terminal_fulfillment_invoker is not None:
        expected_api_call_id = stable_api_call_id(
            api_capability_endpoint_id=binding.api_capability_endpoint_id,
            call_key=api_call_key,
        )
        execution_start = await publish_action_dispatch_execution_start(
            reactivity=reactivity,
            intent=intent,
            binding=binding,
            action_execution_id=action_execution_id,
            api_call_id=expected_api_call_id,
            api_call_key=api_call_key,
            request_id=request_id,
            created_at_unix_ms=created_at_unix_ms,
            publisher_id=publisher_id,
        )
        try:
            terminal_outcome = await invoke_terminal_action_fulfillment(
                invoker=terminal_fulfillment_invoker,
                endpoint_ref=resolved_ir.endpoint_ref,
                discriminant=resolved_ir.discriminant,
                request_values=resolved_ir.request_payload,
                api_call_key=api_call_key,
                expected_api_call_id=expected_api_call_id,
                expected_api_capability_endpoint_id=(
                    binding.api_capability_endpoint_id
                ),
                response_class_config_id=binding.response_class_config_id,
            )
        except ActionTerminalFulfillmentError as exc:
            return ActionDispatchBridgeResult(
                status="fulfillment_failed",
                reason=str(exc),
                binding_resolution=binding_resolution,
                role_preflight=role_preflight,
                execution_claim=execution_claim,
                execution_start=execution_start,
            )
        terminal = await publish_action_dispatch_terminal_outcome(
            reactivity=reactivity,
            intent=intent,
            binding=binding,
            action_execution_id=action_execution_id,
            outcome=terminal_outcome,
            request_id=request_id,
            created_at_unix_ms=created_at_unix_ms,
            publisher_id=publisher_id,
        )
        request_class_config_id = (
            resolved_ir.request_class_config_id or binding.request_class_config_id
        )
        if request_class_config_id is None:
            raise RuntimeError(
                "Terminal action fulfillment requires request ClassConfig identity."
            )
        api_call = ActionDispatchApiCallResult(
            status="materialized",
            action_execution_id=action_execution_id,
            api_call_id=terminal_outcome.api_call_id,
            api_capability_endpoint_id=(terminal_outcome.api_capability_endpoint_id),
            call_key=terminal_outcome.api_call_key,
            request_model_id=terminal_outcome.request_model_id,
            request_class_config_id=request_class_config_id,
            commit_id=None,
            head_commit_id=None,
            branch_id=None,
            projection_hash=None,
        )
        continuation_activation: ProgramActionContinuationActivationResult | None = None
        if terminal_outcome.succeeded and program_continuation_activation_runtime:
            action_config_id = intent.action_config_id
            event_config_id = binding.event_config_id
            if action_config_id is None or event_config_id is None:
                return ActionDispatchBridgeResult(
                    status="continuation_failed",
                    reason="program_action_continuation_initial_anchor_missing",
                    binding_resolution=binding_resolution,
                    role_preflight=role_preflight,
                    execution_claim=execution_claim,
                    execution_start=execution_start,
                    api_call=api_call,
                    terminal_outcome=terminal_outcome,
                    terminal=terminal,
                )
            from aware_experience.program.action_continuation_activation import (
                ProgramActionContinuationActivationError,
            )

            try:
                continuation_activation = (
                    await program_continuation_activation_runtime.activate(
                        initial_action_config_id=action_config_id,
                        initial_event_config_id=event_config_id,
                        initial_api_capability_endpoint_id=(
                            binding.api_capability_endpoint_id
                        ),
                        initial_outcome=terminal_outcome,
                    )
                )
            except ProgramActionContinuationActivationError as exc:
                return ActionDispatchBridgeResult(
                    status="continuation_failed",
                    reason=str(exc),
                    binding_resolution=binding_resolution,
                    role_preflight=role_preflight,
                    execution_claim=execution_claim,
                    execution_start=execution_start,
                    api_call=api_call,
                    terminal_outcome=terminal_outcome,
                    terminal=terminal,
                )
        return ActionDispatchBridgeResult(
            status=(
                "fulfilled" if terminal_outcome.succeeded else "fulfillment_failed"
            ),
            reason=terminal.reason,
            binding_resolution=binding_resolution,
            role_preflight=role_preflight,
            execution_claim=execution_claim,
            execution_start=execution_start,
            api_call=api_call,
            terminal_outcome=terminal_outcome,
            terminal=terminal,
            program_continuation_activation=continuation_activation,
        )

    api_call = await dispatch_action_api_call(
        action_execution_id=action_execution_id,
        api_call_key=api_call_key,
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        source_lane=source_lane,
        target_lane=target_lane,
        ir=resolved_ir,
        source_commit=source_commit,
        commit=commit,
        publish=publish,
        receipt_projection_backend=receipt_projection_backend,
        api_dispatcher=api_dispatcher,
    )
    execution_start = await publish_action_dispatch_execution_start(
        reactivity=reactivity,
        intent=intent,
        binding=binding,
        action_execution_id=action_execution_id,
        api_call_id=api_call.api_call_id,
        api_call_key=api_call_key,
        request_id=request_id,
        created_at_unix_ms=created_at_unix_ms,
        publisher_id=publisher_id,
    )
    return ActionDispatchBridgeResult(
        status="dispatched",
        reason=execution_start.reason,
        binding_resolution=binding_resolution,
        role_preflight=role_preflight,
        execution_claim=execution_claim,
        execution_start=execution_start,
        api_call=api_call,
    )


async def publish_action_dispatch_terminal_outcome(
    *,
    reactivity: ReactivityActionLifecyclePublisher,
    intent: ReactivityActionIntent,
    binding: ActionDispatchBinding,
    action_execution_id: UUID,
    outcome: ActionDispatchTerminalOutcome,
    request_id: UUID | None = None,
    created_at_unix_ms: int = 0,
    publisher_id: str = ACTION_DISPATCH_PUBLISHER_ID,
) -> ActionDispatchPublishResult:
    """Publish lifecycle-only terminal evidence from API-owned outcome truth."""

    reason = f"api_call_outcome:{outcome.status}"
    feedback_status = (
        ActionFeedbackStatus.succeeded
        if outcome.succeeded
        else ActionFeedbackStatus.failed
    )
    terminal_status = (
        ActionTerminalStatus.succeeded
        if outcome.succeeded
        else ActionTerminalStatus.failed
    )
    feedback = _build_action_feedback(
        intent=intent,
        binding=binding,
        action_execution_id=action_execution_id,
        sequence=2,
        created_at_unix_ms=created_at_unix_ms,
        stage=ActionFeedbackStage.terminal,
        status=feedback_status,
        publisher_id=publisher_id,
        message=reason,
        result_info=reason,
    )
    feedback_response = await _publish_lifecycle(
        reactivity=reactivity,
        request=ReactivityActionLifecyclePublishRequest(
            request_id=request_id,
            publisher_id=publisher_id,
            feedback=feedback,
        ),
        operation="action API outcome feedback publish",
    )
    terminal_receipt = _build_action_terminal(
        intent=intent,
        binding=binding,
        action_execution_id=action_execution_id,
        created_at_unix_ms=created_at_unix_ms,
        terminal_status=terminal_status,
        info=reason if outcome.succeeded else None,
        error=(outcome.error or reason) if not outcome.succeeded else None,
    )
    terminal_response = await _publish_lifecycle(
        reactivity=reactivity,
        request=ReactivityActionLifecyclePublishRequest(
            request_id=request_id,
            publisher_id=publisher_id,
            terminal=terminal_receipt,
        ),
        operation="action API outcome terminal publish",
    )
    returned_execution_id = terminal_response.action_execution_id
    if (
        returned_execution_id is not None
        and returned_execution_id != action_execution_id
    ):
        raise RuntimeError(
            "Reactivity lifecycle publish returned mismatched terminal "
            "action_execution_id."
        )
    return ActionDispatchPublishResult(
        status=feedback_status.value,
        reason=reason,
        action_execution_id=action_execution_id,
        action_feedback_id=feedback_response.action_feedback_id,
        action_terminal_status=terminal_status,
        published_count=(
            feedback_response.published_count + terminal_response.published_count
        ),
    )


def _compose_declared_request_ir(
    *,
    ir: ApiInvocationIR,
    intent: ReactivityActionIntent,
    binding: ActionDispatchBinding,
    action_execution_id: UUID,
    api_call_key: UUID,
    actor_id: UUID | None,
    environment_id: UUID | None,
    subscription_id: UUID | None,
    source_commit: ApiInvocationSourceCommit | None,
    program_continuation: ProgramActionContinuationTargetValues | None,
) -> ApiInvocationIR:
    if not binding.request_fields and program_continuation is None:
        return ir
    if ir.request_payload:
        raise ActionRequestCompositionError(AD_HOC_REQUEST_PAYLOAD_REJECTED_REASON)
    if (
        ir.request_class_config_id is not None
        and binding.request_class_config_id is not None
        and ir.request_class_config_id != binding.request_class_config_id
    ):
        raise ActionRequestCompositionError(
            "action_request_composition_request_class_config_mismatch"
        )
    if program_continuation is not None:
        _validate_program_action_continuation_target(
            intent=intent,
            binding=binding,
            continuation=program_continuation,
        )

    composed_request = compose_action_request_payload(
        request_class_config=binding.request_class_config,
        request_fields=binding.request_fields,
        context=ActionDispatchCompositionContext(
            environment_id=environment_id,
            event_id=intent.event_id,
            event_config_id=binding.event_config_id,
            event_activation_id=None,
            event_type=intent.event_type,
            event_source=intent.source,
            event_status=None,
            commit_branch_id=(
                source_commit.branch_id
                if source_commit is not None
                else intent.branch_id
            ),
            commit_projection_hash=(
                source_commit.projection_hash
                if source_commit is not None
                else intent.projection_hash
            ),
            commit_id=(
                source_commit.commit_id
                if source_commit is not None
                else intent.commit_id
            ),
            commit_object_instance_graph_id=(
                source_commit.object_instance_graph_id
                if source_commit is not None
                else intent.object_instance_graph_id
            ),
            commit_object_instance_graph_commit_id=(
                source_commit.object_instance_graph_commit_id
                if source_commit is not None
                else None
            ),
            intent_id=intent.action_intent_id,
            intent_key=intent.intent_key,
            intent_action_config_id=intent.action_config_id,
            intent_event_config_condition_config_id=(
                intent.event_config_condition_config_id
            ),
            intent_action_type=intent.action_type,
            intent_root_object_id=intent.root_object_id,
            intent_focus_scope_id=intent.focus_scope_id,
            intent_focus_id=intent.focus_id,
            intent_view_id=intent.view_id,
            intent_interface_id=intent.interface_id,
            intent_window_id=intent.window_id,
            intent_window_layout_id=intent.window_layout_id,
            intent_window_section_id=intent.window_section_id,
            intent_visible_window_section_ids=tuple(intent.visible_window_section_ids),
            intent_graph_hash_post=intent.graph_hash_post,
            execution_id=action_execution_id,
            execution_key=DEFAULT_EXECUTION_KEY,
            api_call_key=api_call_key,
            action_binding_id=binding.action_binding_id,
            action_experience_id=binding.action_experience_id,
            environment_profile_id=binding.environment_profile_config_id,
            environment_event_id=binding.environment_experience_event_id,
            invocation_config_id=binding.experience_invocation_action_config_id,
            endpoint_id=binding.api_capability_endpoint_id,
            actor_id=actor_id,
            subscription_id=subscription_id,
            binding_node_sources=binding.binding_node_sources,
        ),
        precomposed_values_by_attribute_config_id=(
            program_continuation.target_values_by_attribute_config_id
            if program_continuation is not None
            else None
        ),
    )
    return replace(ir, **{"request_payload": composed_request})


def _validate_program_action_continuation_target(
    *,
    intent: ReactivityActionIntent,
    binding: ActionDispatchBinding,
    continuation: ProgramActionContinuationTargetValues,
) -> None:
    if continuation.target_action_config_id != intent.action_config_id:
        raise ActionRequestCompositionError(
            "action_request_composition_continuation_action_config_mismatch"
        )
    if (
        continuation.target_api_capability_endpoint_id
        != binding.api_capability_endpoint_id
    ):
        raise ActionRequestCompositionError(
            "action_request_composition_continuation_endpoint_mismatch"
        )
    if continuation.target_request_class_config_id != binding.request_class_config_id:
        raise ActionRequestCompositionError(
            "action_request_composition_continuation_request_class_mismatch"
        )


def validate_action_dispatch_role_preflight(
    *,
    binding: ActionDispatchBinding,
    role_evidence: tuple[ActionDispatchRoleEvidence, ...] = (),
) -> ActionDispatchRolePreflightResult:
    """Validate Experience action-entrypoint role policy evidence.

    Evidence is caller/resolver supplied. Experience checks it against the
    resolved invocation config policy; Identity remains the owner of concrete
    ActorRole truth.
    """

    if not binding.role_policies:
        return ActionDispatchRolePreflightResult(
            status="allowed",
            required_policies=(),
            accepted_evidence=(),
        )

    accepted: list[ActionDispatchRoleEvidence] = []
    for policy in binding.role_policies:
        matching = tuple(
            evidence
            for evidence in role_evidence
            if evidence.role_config_id == policy.role_config_id
            and evidence.policy_key == policy.policy_key
        )
        granted = tuple(evidence for evidence in matching if evidence.granted)
        if granted:
            accepted.append(granted[0])
            continue
        return ActionDispatchRolePreflightResult(
            status="denied",
            reason=(
                DENIED_ROLE_EVIDENCE_REASON
                if matching
                else MISSING_ROLE_EVIDENCE_REASON
            ),
            required_policies=binding.role_policies,
            accepted_evidence=tuple(accepted),
        )

    return ActionDispatchRolePreflightResult(
        status="allowed",
        required_policies=binding.role_policies,
        accepted_evidence=tuple(accepted),
    )


async def publish_action_dispatch_rejection(
    *,
    reactivity: ReactivityActionLifecyclePublisher,
    intent: ReactivityActionIntent,
    binding: ActionDispatchBinding,
    action_execution_id: UUID,
    request_id: UUID | None = None,
    created_at_unix_ms: int = 0,
    publisher_id: str = ACTION_DISPATCH_PUBLISHER_ID,
    reason: str,
) -> ActionDispatchPublishResult:
    """Publish fail-closed rejected execution + feedback without an ApiCall."""

    execution = _build_action_execution(
        intent=intent,
        binding=binding,
        action_execution_id=action_execution_id,
        api_call_id=None,
        status=ActionExecutionStatus.rejected,
        publisher_id=publisher_id,
        result_info=reason,
    )
    execution_response = await _publish_lifecycle(
        reactivity=reactivity,
        request=ReactivityActionLifecyclePublishRequest(
            request_id=request_id,
            publisher_id=publisher_id,
            execution=execution,
        ),
        operation="action lifecycle rejection execution publish",
    )
    returned_action_execution_id = execution_response.action_execution_id
    if (
        returned_action_execution_id is not None
        and returned_action_execution_id != action_execution_id
    ):
        raise RuntimeError(
            "Reactivity lifecycle publish returned mismatched rejected "
            "action_execution_id."
        )

    feedback = _build_action_feedback(
        intent=intent,
        binding=binding,
        action_execution_id=action_execution_id,
        sequence=1,
        created_at_unix_ms=created_at_unix_ms,
        stage=ActionFeedbackStage.dispatch,
        status=ActionFeedbackStatus.rejected,
        publisher_id=publisher_id,
        message=reason,
        result_info=reason,
    )
    feedback_response = await _publish_lifecycle(
        reactivity=reactivity,
        request=ReactivityActionLifecyclePublishRequest(
            request_id=request_id,
            publisher_id=publisher_id,
            feedback=feedback,
        ),
        operation="action lifecycle rejection feedback publish",
    )
    return ActionDispatchPublishResult(
        status=ActionFeedbackStatus.rejected.value,
        reason=reason,
        action_execution_id=action_execution_id,
        action_feedback_id=feedback_response.action_feedback_id,
        published_count=(
            execution_response.published_count + feedback_response.published_count
        ),
    )


async def dispatch_action_api_call(
    *,
    action_execution_id: UUID,
    api_call_key: UUID,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    source_lane: MaterializationLaneContext,
    target_lane: MaterializationLaneContext,
    ir: ApiInvocationIR,
    source_commit: ApiInvocationSourceCommit | None = None,
    commit: bool = True,
    publish: bool = False,
    receipt_projection_backend: str | None = None,
    api_dispatcher: ApiInvocationDispatcher = dispatch_api_invocation,
) -> ActionDispatchApiCallResult:
    """Materialize ApiCall through the API runtime using the execution key.

    The bridge does not construct ApiCall ontology objects. It hands the API
    runtime a deterministic `call_key` derived from the planned
    ActionExecution id, so API receipt idempotency is anchored before
    Reactivity publishes the execution correlation.
    """

    dispatch_result = await api_dispatcher(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        source_lane=source_lane,
        target_lane=target_lane,
        ir=ir,
        source_commit=source_commit,
        call_key=api_call_key,
        commit=commit,
        publish=publish,
        receipt_projection_backend=receipt_projection_backend,
    )
    binding = dispatch_result.materialized_call.binding
    if binding.call_key != api_call_key:
        raise RuntimeError(
            "API runtime dispatch returned ApiCall with mismatched call_key."
        )
    return ActionDispatchApiCallResult(
        status="materialized",
        action_execution_id=action_execution_id,
        api_call_id=binding.api_call_id,
        api_capability_endpoint_id=binding.api_capability_endpoint_id,
        call_key=binding.call_key,
        request_model_id=binding.request_model_id,
        request_class_config_id=binding.request_class_config_id,
        commit_id=binding.commit_id,
        head_commit_id=binding.head_commit_id,
        branch_id=binding.branch_id,
        projection_hash=binding.projection_hash,
    )


async def publish_action_dispatch_execution_start(
    *,
    reactivity: ReactivityActionLifecyclePublisher,
    intent: ReactivityActionIntent,
    binding: ActionDispatchBinding,
    action_execution_id: UUID | None = None,
    api_call_id: UUID | None = None,
    api_call_key: UUID | None = None,
    request_id: UUID | None = None,
    created_at_unix_ms: int = 0,
    publisher_id: str = ACTION_DISPATCH_PUBLISHER_ID,
) -> ActionDispatchExecutionStartResult:
    """Publish accepted lifecycle evidence correlated to an ApiCall receipt."""

    if intent.status is not ActionIntentStatus.requested:
        return ActionDispatchExecutionStartResult(
            status="skipped",
            reason="action_intent_not_requested",
        )

    resolved_action_execution_id = action_execution_id or (
        derive_action_dispatch_action_execution_id(
            action_intent_id=intent.action_intent_id,
            execution_key=DEFAULT_EXECUTION_KEY,
        )
    )
    resolved_api_call_key = api_call_key or derive_action_dispatch_api_call_key(
        action_execution_id=resolved_action_execution_id,
    )

    execution = _build_action_execution(
        intent=intent,
        binding=binding,
        action_execution_id=resolved_action_execution_id,
        api_call_id=api_call_id,
        status=ActionExecutionStatus.accepted,
        publisher_id=publisher_id,
        result_info=ACTION_DISPATCH_ACCEPTED_REASON,
    )
    execution_response = await _publish_lifecycle(
        reactivity=reactivity,
        request=ReactivityActionLifecyclePublishRequest(
            request_id=request_id,
            publisher_id=publisher_id,
            execution=execution,
        ),
        operation="action lifecycle execution publish",
    )
    returned_action_execution_id = execution_response.action_execution_id
    if returned_action_execution_id is None:
        raise RuntimeError(
            "Reactivity lifecycle publish did not return action_execution_id."
        )
    if returned_action_execution_id != resolved_action_execution_id:
        raise RuntimeError(
            "Reactivity lifecycle publish returned mismatched action_execution_id."
        )

    feedback = _build_action_feedback(
        intent=intent,
        binding=binding,
        action_execution_id=resolved_action_execution_id,
        sequence=1,
        created_at_unix_ms=created_at_unix_ms,
        stage=ActionFeedbackStage.dispatch,
        status=ActionFeedbackStatus.accepted,
        publisher_id=publisher_id,
        message=ACTION_DISPATCH_ACCEPTED_REASON,
        result_info=ACTION_DISPATCH_ACCEPTED_REASON,
    )
    feedback_response = await _publish_lifecycle(
        reactivity=reactivity,
        request=ReactivityActionLifecyclePublishRequest(
            request_id=request_id,
            publisher_id=publisher_id,
            feedback=feedback,
        ),
        operation="action lifecycle dispatch feedback publish",
    )
    return ActionDispatchExecutionStartResult(
        status="accepted",
        reason=ACTION_DISPATCH_ACCEPTED_REASON,
        action_execution_id=resolved_action_execution_id,
        action_feedback_id=feedback_response.action_feedback_id,
        api_call_key=resolved_api_call_key,
        published_count=(
            execution_response.published_count + feedback_response.published_count
        ),
    )


async def publish_action_dispatch_stream_feedback(
    *,
    reactivity: ReactivityActionLifecyclePublisher,
    intent: ReactivityActionIntent,
    binding: ActionDispatchBinding,
    action_execution_id: UUID,
    api_call_stream_event: ApiCallStreamEvent,
    request_id: UUID | None = None,
    created_at_unix_ms: int = 0,
    publisher_id: str = ACTION_DISPATCH_PUBLISHER_ID,
) -> ActionDispatchPublishResult:
    """Publish envelope-only feedback derived from an API stream receipt."""

    stream_event_id = api_call_stream_event.id
    if stream_event_id is None:
        raise ValueError("ApiCallStreamEvent feedback mapping requires receipt id.")
    stream_event_config = (
        api_call_stream_event.api_capability_endpoint_stream_event_config
    )
    if stream_event_config is None:
        raise ValueError(MISSING_STREAM_EVENT_CONFIG_REASON)

    stream_reason = f"api_stream_event:{stream_event_config.kind.value}"
    stage, status = _feedback_envelope_for_stream_kind(stream_event_config.kind)
    feedback = _build_action_feedback(
        intent=intent,
        binding=binding,
        action_execution_id=action_execution_id,
        api_call_stream_event_id=stream_event_id,
        sequence=api_call_stream_event.sequence,
        created_at_unix_ms=created_at_unix_ms,
        stage=stage,
        status=status,
        publisher_id=publisher_id,
        message=stream_reason,
        result_info=stream_reason,
    )
    feedback_response = await _publish_lifecycle(
        reactivity=reactivity,
        request=ReactivityActionLifecyclePublishRequest(
            request_id=request_id,
            publisher_id=publisher_id,
            feedback=feedback,
        ),
        operation="action stream feedback publish",
    )
    published_count = feedback_response.published_count
    terminal_status = _terminal_status_for_stream_kind(stream_event_config.kind)
    if terminal_status is not None:
        terminal = _build_action_terminal(
            intent=intent,
            binding=binding,
            action_execution_id=action_execution_id,
            created_at_unix_ms=created_at_unix_ms,
            terminal_status=terminal_status,
            info=(
                None
                if terminal_status is ActionTerminalStatus.failed
                else stream_reason
            ),
            error=(
                stream_reason
                if terminal_status is ActionTerminalStatus.failed
                else None
            ),
        )
        terminal_response = await _publish_lifecycle(
            reactivity=reactivity,
            request=ReactivityActionLifecyclePublishRequest(
                request_id=request_id,
                publisher_id=publisher_id,
                terminal=terminal,
            ),
            operation="action terminal publish",
        )
        returned_action_execution_id = terminal_response.action_execution_id
        if (
            returned_action_execution_id is not None
            and returned_action_execution_id != action_execution_id
        ):
            raise RuntimeError(
                "Reactivity lifecycle publish returned mismatched terminal "
                "action_execution_id."
            )
        published_count += terminal_response.published_count

    return ActionDispatchPublishResult(
        status=status.value,
        reason=stream_reason,
        action_execution_id=action_execution_id,
        action_feedback_id=feedback_response.action_feedback_id,
        action_terminal_status=terminal_status,
        published_count=published_count,
    )


def _feedback_envelope_for_stream_kind(
    kind: ApiCapabilityEndpointStreamEventKind,
) -> tuple[ActionFeedbackStage, ActionFeedbackStatus]:
    if kind is ApiCapabilityEndpointStreamEventKind.complete:
        return ActionFeedbackStage.terminal, ActionFeedbackStatus.succeeded
    if kind is ApiCapabilityEndpointStreamEventKind.error:
        return ActionFeedbackStage.terminal, ActionFeedbackStatus.failed
    if kind is ApiCapabilityEndpointStreamEventKind.snapshot:
        return ActionFeedbackStage.execute, ActionFeedbackStatus.responded
    return ActionFeedbackStage.execute, ActionFeedbackStatus.running


def _terminal_status_for_stream_kind(
    kind: ApiCapabilityEndpointStreamEventKind,
) -> ActionTerminalStatus | None:
    if kind is ApiCapabilityEndpointStreamEventKind.complete:
        return ActionTerminalStatus.succeeded
    if kind is ApiCapabilityEndpointStreamEventKind.error:
        return ActionTerminalStatus.failed
    return None


def _binding_from_action_experience_invocation(
    *,
    profile_config: EnvironmentExperienceProfileConfig,
    event: EnvironmentExperienceEvent,
    action_experience: ActionExperience,
    invocation: ActionExperienceInvocation,
    invocation_config: ExperienceInvocationActionConfig,
    anchor_endpoint_id: UUID,
    index: MetaGraphRuntimeIndex | None,
) -> ActionDispatchBinding:
    endpoint = invocation_config.api_capability_endpoint
    if endpoint is None:
        raise ValueError("Action dispatch binding resolution requires an API target.")
    endpoint_id = invocation_config.api_capability_endpoint_id or endpoint.id
    if endpoint_id is None:
        raise ValueError(
            "Action dispatch binding resolution requires ApiCapabilityEndpoint.id."
        )
    request_config = endpoint.request_config
    response_config = request_config.response_config if request_config else None
    stream_config = request_config.stream_config if request_config else None
    return ActionDispatchBinding(
        action_binding_id=_required_id(invocation, label="ActionExperienceInvocation"),
        experience_invocation_action_config_id=_required_id(
            invocation_config,
            label="ExperienceInvocationActionConfig",
        ),
        api_capability_endpoint_id=endpoint_id,
        action_config_api_capability_endpoint_id=anchor_endpoint_id,
        request_class_config_id=(
            request_config.class_config_id if request_config is not None else None
        ),
        request_class_config=(
            request_config.class_config if request_config is not None else None
        ),
        environment_experience_profile_config_id=profile_config.id,
        environment_profile_config_id=profile_config.environment_profile_config_id,
        environment_profile_key=profile_config.key,
        environment_experience_event_id=event.id,
        event_config_id=event.event_config_id,
        action_experience_id=action_experience.id,
        response_class_config_id=(
            response_config.class_config_id if response_config is not None else None
        ),
        stream_event_class_config_ids=_stream_event_class_config_ids(stream_config),
        role_policies=_role_policies(invocation_config),
        request_fields=_request_field_bindings(invocation),
        binding_node_sources=_binding_node_sources(
            profile_config=profile_config,
            invocation_config=invocation_config,
            index=index,
        ),
    )


def _role_policies(
    invocation_config: ExperienceInvocationActionConfig,
) -> tuple[ActionDispatchRolePolicy, ...]:
    return tuple(
        ActionDispatchRolePolicy(
            role_config_id=policy.role_config_id,
            policy_key=policy.policy_key,
            requirement_kind=policy.requirement_kind,
        )
        for policy in invocation_config.role_policies
    )


def _stream_event_class_config_ids(
    stream_config: ApiCapabilityEndpointStreamConfig | None,
) -> Mapping[str, UUID]:
    if stream_config is None:
        return {}
    resolved: dict[str, UUID] = {}
    for event_config in stream_config.api_capability_endpoint_stream_event_configs:
        resolved[event_config.kind.value] = event_config.class_config_id
    return resolved


def _request_field_bindings(
    invocation: ActionExperienceInvocation,
) -> tuple[ActionDispatchRequestFieldBinding, ...]:
    fields: list[ActionDispatchRequestFieldBinding] = []
    for request_field in invocation.request_fields:
        fields.append(_request_field_binding(request_field))
    fields.sort(
        key=lambda item: (
            item.position if item.position is not None else 0,
            item.attribute_name or "",
            str(item.attribute_config_id or ""),
        )
    )
    return tuple(fields)


def _request_field_binding(
    field: ActionExperienceInvocationRequestField,
) -> ActionDispatchRequestFieldBinding:
    attribute_config = field.attribute_config
    return ActionDispatchRequestFieldBinding(
        request_field_id=field.id,
        attribute_config_id=field.attribute_config_id,
        attribute_name=(
            attribute_config.name if attribute_config is not None else None
        ),
        source_ref=field.source_ref,
        required=field.required,
        position=field.position,
    )


def _binding_node_sources(
    *,
    profile_config: EnvironmentExperienceProfileConfig,
    invocation_config: ExperienceInvocationActionConfig,
    index: MetaGraphRuntimeIndex | None,
) -> Mapping[str, ActionDispatchBindingNodeSource]:
    projection_experience_id = invocation_config.projection_experience_id
    projection_experience = None
    for experience_bridge in profile_config.experiences:
        if experience_bridge.projection_experience_id != projection_experience_id:
            continue
        projection_experience = experience_bridge.projection_experience
        break
    if projection_experience is None:
        return {}

    class_identities_by_node_identity_id = {}
    for projection_oigi in projection_experience.projection_experience_oigis:
        for node_class_identity in projection_oigi.node_class_identities:
            class_identities_by_node_identity_id[
                node_class_identity.projection_experience_node_identity_id
            ] = node_class_identity

    sources: dict[str, ActionDispatchBindingNodeSource] = {}
    for node in projection_experience.projection_experience_nodes:
        for node_identity in node.projection_experience_node_identities:
            node_class_identity = class_identities_by_node_identity_id.get(
                node_identity.id
            )
            if node_class_identity is None:
                continue
            class_config_id = None
            class_instance_identity = node_class_identity.class_instance_identity
            if (
                class_instance_identity is not None
                and class_instance_identity.class_instance is not None
            ):
                class_config_id = class_instance_identity.class_instance.class_config_id
            if class_config_id is None:
                class_config_id = _projection_node_class_config_id(
                    index=index,
                    projection_experience_node=node,
                )
            if node_identity.key in sources:
                raise ValueError(
                    "Action dispatch binding node source alias is ambiguous: "
                    f"{node_identity.key}"
                )
            sources[node_identity.key] = ActionDispatchBindingNodeSource(
                alias=node_identity.key,
                class_instance_identity_id=(
                    node_class_identity.class_instance_identity_id
                ),
                class_config_id=class_config_id,
                object_id=(
                    class_instance_identity.class_instance.source_object_id
                    if class_instance_identity is not None
                    and class_instance_identity.class_instance is not None
                    else None
                ),
            )
    return sources


def _projection_node_class_config_id(
    *,
    index: MetaGraphRuntimeIndex | None,
    projection_experience_node: ProjectionExperienceNode,
) -> UUID | None:
    object_projection_graph_node = (
        projection_experience_node.object_projection_graph_node
    )
    class_config_id = (
        None
        if object_projection_graph_node is None
        else object_projection_graph_node.class_config_id
    )
    if isinstance(class_config_id, UUID):
        return class_config_id
    if index is None:
        return None
    object_projection_graph_node_id = (
        projection_experience_node.object_projection_graph_node_id
    )
    if not isinstance(object_projection_graph_node_id, UUID):
        return None
    try:
        object_projection_graphs = index.ocg.object_projection_graphs
    except AttributeError:
        return None
    for opg in object_projection_graphs:
        for node in opg.object_projection_graph_nodes or ():
            if node.id != object_projection_graph_node_id:
                continue
            resolved_class_config_id = node.class_config_id
            return (
                resolved_class_config_id
                if isinstance(resolved_class_config_id, UUID)
                else None
            )
    return None


def _required_id(
    instance: ActionExperienceInvocation | ExperienceInvocationActionConfig,
    *,
    label: str,
) -> UUID:
    if instance.id is None:
        raise ValueError(f"Action dispatch binding resolution requires {label}.id.")
    return instance.id


def _build_action_execution(
    *,
    intent: ReactivityActionIntent,
    binding: ActionDispatchBinding,
    action_execution_id: UUID | None,
    api_call_id: UUID | None = None,
    status: ActionExecutionStatus,
    publisher_id: str,
    result_info: str,
) -> ActionExecution:
    return ActionExecution(
        action_execution_id=action_execution_id,
        action_intent_id=intent.action_intent_id,
        event_id=intent.event_id,
        event_type=intent.event_type,
        source=intent.source,
        branch_id=intent.branch_id,
        projection_hash=intent.projection_hash,
        commit_id=intent.commit_id,
        event_config_condition_config_id=intent.event_config_condition_config_id,
        action_binding_id=binding.action_binding_id,
        action_config_id=intent.action_config_id,
        action_type=intent.action_type,
        root_object_id=intent.root_object_id,
        object_instance_graph_id=intent.object_instance_graph_id,
        graph_hash_post=intent.graph_hash_post,
        execution_key=DEFAULT_EXECUTION_KEY,
        status=status,
        executor_ref=publisher_id,
        api_call_id=api_call_id,
        result_info=result_info,
    )


def _build_action_feedback(
    *,
    intent: ReactivityActionIntent,
    binding: ActionDispatchBinding,
    action_execution_id: UUID,
    api_call_stream_event_id: UUID | None = None,
    sequence: int,
    created_at_unix_ms: int,
    stage: ActionFeedbackStage,
    status: ActionFeedbackStatus,
    publisher_id: str,
    message: str,
    result_info: str,
) -> ActionFeedback:
    return ActionFeedback(
        action_intent_id=intent.action_intent_id,
        action_execution_id=action_execution_id,
        event_id=intent.event_id,
        sequence=sequence,
        created_at_unix_ms=created_at_unix_ms,
        stage=stage,
        status=status,
        action_binding_id=binding.action_binding_id,
        action_config_id=intent.action_config_id,
        action_type=intent.action_type,
        message=message,
        api_call_stream_event_id=api_call_stream_event_id,
        executor_ref=publisher_id,
        result_info=result_info,
    )


def _build_action_terminal(
    *,
    intent: ReactivityActionIntent,
    binding: ActionDispatchBinding,
    action_execution_id: UUID,
    created_at_unix_ms: int,
    terminal_status: ActionTerminalStatus,
    info: str | None,
    error: str | None,
) -> ActionTerminal:
    return ActionTerminal(
        action_execution_id=action_execution_id,
        event_id=intent.event_id,
        terminal_status=terminal_status,
        handled=terminal_status is ActionTerminalStatus.succeeded,
        created_at_unix_ms=created_at_unix_ms,
        action_binding_id=binding.action_binding_id,
        action_config_id=intent.action_config_id,
        action_type=intent.action_type,
        info=info,
        error=error,
    )


async def _publish_lifecycle(
    *,
    reactivity: ReactivityActionLifecyclePublisher,
    request: ReactivityActionLifecyclePublishRequest,
    operation: str,
) -> ReactivityActionLifecyclePublishResponse:
    response = await reactivity.publish_action_lifecycle(request)
    if response.accepted is False or response.error:
        raise RuntimeError(
            response.error or response.info or f"Reactivity rejected {operation}."
        )
    return response
