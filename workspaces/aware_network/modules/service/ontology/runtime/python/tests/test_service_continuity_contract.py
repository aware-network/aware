from datetime import datetime, timezone
from uuid import uuid4

from aware_service_service_dto.continuity import (
    ServiceContinuityBlocker,
    ServiceContinuityFreshness,
    ServiceContinuityNextAction,
    ServiceContinuityObservation,
    ServiceContinuityStatus,
)


def test_service_continuity_observation_is_typed_domain_neutral_envelope() -> None:
    observation = ServiceContinuityObservation(
        observation_id=uuid4(),
        participant_ref="participant:conversation",
        service_package_ref="aware-conversation-service",
        continuity_contract_ref="conversation.continuity.v1",
        status=ServiceContinuityStatus.degraded,
        freshness=ServiceContinuityFreshness.live,
        observed_at=datetime.now(timezone.utc),
        authority_id="authority-1",
        authority_generation_id="generation-1",
        observation_receipt_ref="receipt:conversation:1",
        blockers=[
            ServiceContinuityBlocker(
                code="conversation_head_unavailable",
                message="Conversation head could not be observed.",
                retryable=True,
            )
        ],
        next_actions=[
            ServiceContinuityNextAction(
                action_key="observe_conversation_head",
                title="Observe Conversation head",
                capability_ref="conversation.continuity",
                endpoint_ref="conversation.continuity.observe",
            )
        ],
    )

    assert observation.schema_version == "service.continuity.observation.v1"
    assert observation.status is ServiceContinuityStatus.degraded
    assert observation.freshness is ServiceContinuityFreshness.live
    assert observation.blockers[0].retryable is True
    assert observation.next_actions[0].requires_live_authority is True
    assert "domain_payload" not in ServiceContinuityObservation.model_fields
    assert "metadata" not in ServiceContinuityObservation.model_fields
    assert "evidence" not in ServiceContinuityObservation.model_fields


def test_service_continuity_collection_defaults_are_not_shared() -> None:
    common = {
        "participant_ref": "participant:custom",
        "service_package_ref": "custom-service",
        "continuity_contract_ref": "custom.continuity.v1",
        "observed_at": datetime.now(timezone.utc),
    }
    first = ServiceContinuityObservation(observation_id=uuid4(), **common)
    second = ServiceContinuityObservation(observation_id=uuid4(), **common)

    first.blockers.append(
        ServiceContinuityBlocker(code="custom_blocker", message="Blocked")
    )

    assert second.blockers == []
