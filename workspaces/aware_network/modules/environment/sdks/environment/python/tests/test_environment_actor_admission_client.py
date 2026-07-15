from __future__ import annotations

from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_environment_sdk import (
    EnvironmentActorAdmissionClient,
    EnvironmentActorAdmissionContext,
    EnvironmentActorAdmissionError,
)
from aware_environment_service_dto.environment.environment import (
    AdmitEnvironmentActorRequest,
    AdmitEnvironmentActorResponse,
    EnvironmentActorAdmissionReceipt,
    EnvironmentActorAdmissionRoleBinding,
    EnvironmentActorAdmissionRoleEligibility,
)


class _RecordingActorAdmissionClient:
    def __init__(self, *, accepted: bool = True) -> None:
        self.accepted = accepted
        self.requests: list[AdmitEnvironmentActorRequest] = []
        self.environment_profile_actor_config_id = uuid4()
        self.actor_config_role_config_id = uuid4()
        self.role_config_id = uuid4()
        self.role_id = uuid4()
        self.actor_role_id = uuid4()
        self.role_class_instance_id = uuid4()
        self.role_config_class_config_id = uuid4()
        self.oig_identity_id = uuid4()

    async def admit_actor(
        self,
        request: AdmitEnvironmentActorRequest,
    ) -> AdmitEnvironmentActorResponse:
        self.requests.append(request)
        status = "admitted" if self.accepted else "rejected"
        error = (
            None
            if self.accepted
            else "environment_actor_config_role_eligibility_not_found"
        )
        eligible_roles = [
            EnvironmentActorAdmissionRoleEligibility(
                environment_profile_actor_config_id=(
                    self.environment_profile_actor_config_id
                ),
                actor_config_role_config_id=self.actor_config_role_config_id,
                role_config_id=self.role_config_id,
                role_config_name="aware.environment.member",
            )
        ]
        bindings = (
            [
                EnvironmentActorAdmissionRoleBinding(
                    environment_profile_actor_config_id=(
                        self.environment_profile_actor_config_id
                    ),
                    actor_config_role_config_id=self.actor_config_role_config_id,
                    role_config_id=self.role_config_id,
                    role_config_name="aware.environment.member",
                    actor_id=cast(UUID, request.actor_id),
                    role_id=self.role_id,
                    actor_role_id=self.actor_role_id,
                    role_class_instance_id=self.role_class_instance_id,
                    class_instance_identity_id=request.class_instance_identity_id,
                    role_config_class_config_id=self.role_config_class_config_id,
                    object_instance_graph_identity_id=self.oig_identity_id,
                    object_instance_graph_branch_key=(
                        request.object_instance_graph_branch_key
                    ),
                    object_instance_graph_branch_id=(
                        request.object_instance_graph_branch_id
                    ),
                )
            ]
            if self.accepted
            else []
        )
        return AdmitEnvironmentActorResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            request_id=request.request_id,
            accepted=self.accepted,
            status=status,
            error=error,
            evidence=cast(Any, {"source": "recording-client"}),
            receipt=EnvironmentActorAdmissionReceipt(
                accepted=self.accepted,
                status=status,
                reason=request.reason,
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                environment_profile_id=request.environment_profile_id,
                environment_profile_actor_config_id=(
                    self.environment_profile_actor_config_id if self.accepted else None
                ),
                actor_config_id=request.actor_config_id,
                class_instance_identity_id=request.class_instance_identity_id,
                object_instance_graph_branch_key=(
                    request.object_instance_graph_branch_key
                ),
                object_instance_graph_branch_id=(
                    request.object_instance_graph_branch_id
                ),
                requested_role_config_ids=list(request.requested_role_config_ids),
                requested_role_config_names=list(request.requested_role_config_names),
                eligible_roles=eligible_roles,
                bindings=bindings,
                blockers=[] if self.accepted else [cast(str, error)],
                evidence=cast(Any, {"binding_count": len(bindings)}),
            ),
        )


class _RecordingEnvironmentApi:
    def __init__(self, *, accepted: bool = True) -> None:
        self.actor_admission = _RecordingActorAdmissionClient(accepted=accepted)


class _RecordingGeneratedApiClient:
    def __init__(self, *, accepted: bool = True) -> None:
        self.environment = _RecordingEnvironmentApi(accepted=accepted)


def _context() -> EnvironmentActorAdmissionContext:
    return EnvironmentActorAdmissionContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
    )


@pytest.mark.asyncio
async def test_environment_actor_admission_client_builds_request_and_receipt() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentActorAdmissionClient(
        api_client=api_client,
        context=context,
    )
    request_id = uuid4()
    environment_profile_id = uuid4()
    actor_config_id = uuid4()
    class_instance_identity_id = uuid4()
    role_config_id = uuid4()
    branch_id = uuid4()

    receipt = await client.admit_actor(
        request_id=request_id,
        environment_profile_id=str(environment_profile_id),
        actor_config_id=actor_config_id,
        class_instance_identity_id=class_instance_identity_id,
        object_instance_graph_branch_key="main",
        object_instance_graph_branch_id=branch_id,
        requested_role_config_ids=[str(role_config_id)],
        requested_role_config_names=["aware.environment.member"],
        reason="join shared environment",
        evidence={"source": "sdk-test"},
    )

    requests = api_client.environment.actor_admission.requests
    assert len(requests) == 1
    request = requests[0]
    assert request.actor_id == context.actor_id
    assert request.environment_id == context.environment_id
    assert request.request_id == request_id
    assert request.environment_profile_id == environment_profile_id
    assert request.actor_config_id == actor_config_id
    assert request.class_instance_identity_id == class_instance_identity_id
    assert request.object_instance_graph_branch_key == "main"
    assert request.object_instance_graph_branch_id == branch_id
    assert request.requested_role_config_ids == [role_config_id]
    assert request.requested_role_config_names == ["aware.environment.member"]
    assert dict(request.evidence) == {"source": "sdk-test"}

    assert receipt.accepted is True
    assert receipt.status == "admitted"
    assert receipt.error is None
    assert receipt.actor_id == context.actor_id
    assert receipt.environment_id == context.environment_id
    assert receipt.environment_profile_id == environment_profile_id
    assert receipt.actor_config_id == actor_config_id
    assert receipt.class_instance_identity_id == class_instance_identity_id
    assert receipt.eligible_role_count == 1
    assert receipt.binding_count == 1
    assert receipt.eligible_roles[0].role_config_name == "aware.environment.member"
    assert receipt.bindings[0].actor_id == context.actor_id
    assert receipt.blockers == ()
    assert receipt.dto_receipt is not None
    assert receipt.dto_receipt.environment_id == context.environment_id
    assert receipt.raw_response is not None


@pytest.mark.asyncio
async def test_environment_actor_admission_client_raises_on_rejection() -> None:
    api_client = _RecordingGeneratedApiClient(accepted=False)
    context = _context()
    client = EnvironmentActorAdmissionClient(
        api_client=api_client,
        context=context,
    )

    with pytest.raises(EnvironmentActorAdmissionError) as exc_info:
        await client.admit_actor(
            environment_profile_id=uuid4(),
            actor_config_id=uuid4(),
            class_instance_identity_id=uuid4(),
        )

    receipt = exc_info.value.receipt
    assert receipt.accepted is False
    assert receipt.status == "rejected"
    assert receipt.error == "environment_actor_config_role_eligibility_not_found"
    assert receipt.binding_count == 0
    assert receipt.eligible_role_count == 1
    assert receipt.blockers == ("environment_actor_config_role_eligibility_not_found",)
    assert receipt.dto_receipt is not None
    assert receipt.raw_response is not None
