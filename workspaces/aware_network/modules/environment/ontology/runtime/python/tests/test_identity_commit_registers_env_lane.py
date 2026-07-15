from __future__ import annotations

import sys
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from ._environment_runtime_test_paths import (
    ENVIRONMENT_ONTOLOGY_ROOT,
    ENVIRONMENT_RUNTIME_ROOT,
    REPO_ROOT,
)

_REPO_ROOT = REPO_ROOT
for _path in (
    _REPO_ROOT / "apis" / "meta" / "python" / "aware_ontology_service_dto",
    _REPO_ROOT / "libs" / "api" / "python",
    _REPO_ROOT / "modules" / "meta" / "structure" / "ontology" / "python",
    ENVIRONMENT_RUNTIME_ROOT,
    ENVIRONMENT_ONTOLOGY_ROOT / "structure/python/orm_runtime",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_ontology_service_dto.graph.instance.commit_event import (  # noqa: E402
    OntologyGraphCommitActionMetadata,
)
from aware_ontology_service_dto.graph.instance.commit_event import (  # noqa: E402
    OntologyCommitEventEnvelope,
)
from aware_ontology_service_dto.graph.instance.commit_event import (  # noqa: E402
    OntologyCommitSubscriptionRequest,
)
from aware_ontology_service_dto.graph.instance.commit_event import (  # noqa: E402
    OntologyCommitSubscriptionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (  # noqa: E402
    OntologyGraphGetLaneHeadRequest,
)
from aware_ontology_service_dto.graph.instance.function_call import (  # noqa: E402
    OntologyGraphGetLaneHeadResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (  # noqa: E402
    OntologyGraphGetObjectInstanceGraphCommitRequest,
)
from aware_ontology_service_dto.graph.instance.function_call import (  # noqa: E402
    OntologyGraphGetObjectInstanceGraphCommitResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (  # noqa: E402
    OntologyGraphInvokeFunctionRequest,
)
from aware_ontology_service_dto.graph.instance.function_call import (  # noqa: E402
    OntologyGraphInvokeFunctionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (  # noqa: E402
    OntologyGraphResolveProjectionRequest,
)
from aware_ontology_service_dto.graph.instance.function_call import (  # noqa: E402
    OntologyGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call_target import (  # noqa: E402
    OntologyGraphFunctionCallTarget,
)
from aware_environment.reactions.environment_lane import (  # noqa: E402
    ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID,
    EnvironmentOntologyApiClients,
    EnvironmentTopologyAttachFunctionPlanner,
    EnvironmentTopologyAttachPlannerConfig,
    EnvironmentTopologyCommitSubscriber,
    EnvironmentTopologyThreadInterest,
)
from aware_environment.stable_ids import stable_environment_profile_id  # noqa: E402


class _UnusedCommitClient:
    async def subscribe(
        self,
        request: OntologyCommitSubscriptionRequest,
    ) -> OntologyCommitSubscriptionResponse:
        return OntologyCommitSubscriptionResponse(
            subscriber_id=request.subscriber_id,
            accepted=True,
        )


class _IdentityGraphClient:
    def __init__(
        self,
        *,
        lane_head_commit_id: UUID,
        object_instance_graph_commit_id: UUID,
        object_instance_graph_id: UUID,
        object_instance_graph_identity_id: UUID,
        topology_projection_hash: str = "environment-profile-projection",
    ) -> None:
        self.lane_head_commit_id = lane_head_commit_id
        self.object_instance_graph_commit_id = object_instance_graph_commit_id
        self.object_instance_graph_id = object_instance_graph_id
        self.object_instance_graph_identity_id = object_instance_graph_identity_id
        self.topology_projection_hash = topology_projection_hash
        self.lane_head_requests: list[OntologyGraphGetLaneHeadRequest] = []
        self.commit_requests: list[OntologyGraphGetObjectInstanceGraphCommitRequest] = (
            []
        )
        self.projection_requests: list[OntologyGraphResolveProjectionRequest] = []
        self.invoke_requests: list[OntologyGraphInvokeFunctionRequest] = []

    async def get_lane_head(
        self,
        request: OntologyGraphGetLaneHeadRequest,
    ) -> OntologyGraphGetLaneHeadResponse:
        self.lane_head_requests.append(request)
        return OntologyGraphGetLaneHeadResponse(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            domain_commit_id=self.lane_head_commit_id,
            graph_hash_post="sha256:identity-head",
            object_instance_graph_id=self.object_instance_graph_id,
            root_object_id=request.domain_branch_id,
            head_version=1,
            error=None,
        )

    async def get_object_instance_graph_commit(
        self,
        request: OntologyGraphGetObjectInstanceGraphCommitRequest,
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse:
        self.commit_requests.append(request)
        return OntologyGraphGetObjectInstanceGraphCommitResponse(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            domain_commit_id=request.domain_commit_id,
            object_instance_graph_commit_id=self.object_instance_graph_commit_id,
            object_instance_graph_id=self.object_instance_graph_id,
            object_instance_graph_identity_id=self.object_instance_graph_identity_id,
            root_object_id=request.domain_branch_id,
            graph_hash_post="sha256:identity-commit",
            commit={
                "object_instance_graph_key": str(request.domain_branch_id),
                "object_instance_graph_name": "Identity",
            },
            error=None,
        )

    async def invoke_function(
        self,
        request: OntologyGraphInvokeFunctionRequest,
    ) -> OntologyGraphInvokeFunctionResponse:
        self.invoke_requests.append(request)
        return OntologyGraphInvokeFunctionResponse(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            domain_commit_id=uuid4(),
            error=None,
        )

    async def resolve_projection(
        self,
        request: OntologyGraphResolveProjectionRequest,
    ) -> OntologyGraphResolveProjectionResponse:
        self.projection_requests.append(request)
        return OntologyGraphResolveProjectionResponse(
            status="succeeded",
            actor_id=request.actor_id,
            projection_name=request.projection_name,
            projection_hash=self.topology_projection_hash,
            error=None,
        )


class _StaticThreadInterestResolver:
    def __init__(
        self,
        interests: tuple[EnvironmentTopologyThreadInterest, ...],
    ) -> None:
        self.interests = interests

    async def resolve_thread_interests(
        self,
        *,
        event: OntologyCommitEventEnvelope,
        object_instance_graph_branch_id: UUID,
    ) -> tuple[EnvironmentTopologyThreadInterest, ...]:
        _ = event
        return tuple(
            interest
            for interest in self.interests
            if interest.object_instance_graph_branch_id
            == object_instance_graph_branch_id
        )


@pytest.mark.asyncio
async def test_identity_constructor_commit_event_registers_environment_lane_via_meta_reaction() -> (
    None
):
    environment_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/identity-env-lane/environment",
    )
    thread_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/identity-env-lane/thread",
    )
    identity_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/identity-env-lane/identity",
    )
    identity_projection_hash = "identity-projection"
    identity_commit_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/identity-env-lane/commit",
    )
    identity_function_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/identity-env-lane/signup-function",
    )
    object_instance_graph_commit_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    event = _identity_commit_event(
        identity_id=identity_id,
        identity_projection_hash=identity_projection_hash,
        identity_commit_id=identity_commit_id,
        identity_function_id=identity_function_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
    )
    graph = _IdentityGraphClient(
        lane_head_commit_id=identity_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
    )
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_UnusedCommitClient(),
            graph=graph,
        ),
        planner=EnvironmentTopologyAttachFunctionPlanner(
            EnvironmentTopologyAttachPlannerConfig(),
        ),
        thread_interest_resolver=_StaticThreadInterestResolver(
            (
                EnvironmentTopologyThreadInterest(
                    object_instance_graph_branch_id=event.object_instance_graph_branch_id,
                    thread_id=thread_id,
                    topology_branch_id=stable_environment_profile_id(
                        environment_id=environment_id,
                        key="bootstrap",
                    ),
                    topology_projection_hash=graph.topology_projection_hash,
                ),
            )
        ),
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "succeeded"
    assert len(graph.lane_head_requests) == 1
    assert graph.lane_head_requests[0].domain_branch_id == identity_id
    assert graph.lane_head_requests[0].domain_projection_hash == (
        identity_projection_hash
    )
    assert len(graph.commit_requests) == 1
    assert graph.commit_requests[0].domain_commit_id == identity_commit_id
    assert graph.projection_requests == []
    assert len(graph.invoke_requests) == 1

    request = graph.invoke_requests[0]
    assert request.actor_id == event.actor_id
    assert request.domain_branch_id == stable_environment_profile_id(
        environment_id=environment_id,
        key="bootstrap",
    )
    assert request.domain_projection_hash == graph.topology_projection_hash
    assert request.call_target == OntologyGraphFunctionCallTarget.instance
    assert request.target_object_id == thread_id
    assert request.function_id == ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID
    assert request.kwargs["domain_branch_id"] == str(identity_id)
    assert request.kwargs["projection_hash"] == identity_projection_hash
    assert request.kwargs["title"] == "Identity.signup_via_profile"
    assert request.kwargs["is_active"] is True
    assert not hasattr(request, "orchestration_context")

    assert outcome.ontology_graph_state is not None
    assert outcome.ontology_graph_state.lane_head.domain_commit_id == identity_commit_id
    assert (
        outcome.ontology_graph_state.object_instance_graph_commit.object_instance_graph_commit_id
        == object_instance_graph_commit_id
    )
    assert outcome.record is not None
    assert outcome.record.status == "succeeded"
    assert outcome.record.ontology_domain_commit_id == identity_commit_id
    assert outcome.record.object_instance_graph_commit_id == (
        object_instance_graph_commit_id
    )
    assert outcome.record.topology_projection_hash == graph.topology_projection_hash


@pytest.mark.asyncio
async def test_identity_constructor_commit_without_thread_interest_is_skipped_before_meta_reads() -> (
    None
):
    event = _identity_commit_event(
        identity_id=uuid4(),
        identity_projection_hash="identity-projection",
        identity_commit_id=uuid4(),
        identity_function_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        object_instance_graph_id=uuid4(),
        object_instance_graph_identity_id=uuid4(),
    )
    graph = _IdentityGraphClient(
        lane_head_commit_id=event.domain_commit_id,
        object_instance_graph_commit_id=event.object_instance_graph_commit_id,
        object_instance_graph_id=event.object_instance_graph_id,
        object_instance_graph_identity_id=event.object_instance_graph_identity_id,
    )
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_UnusedCommitClient(),
            graph=graph,
        ),
        planner=EnvironmentTopologyAttachFunctionPlanner(
            EnvironmentTopologyAttachPlannerConfig(),
        ),
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "skipped"
    assert outcome.reason == "no_thread_oigb_interest"
    assert graph.lane_head_requests == []
    assert graph.commit_requests == []
    assert graph.projection_requests == []
    assert graph.invoke_requests == []


def test_identity_commit_environment_lane_proof_uses_meta_event_boundary() -> None:
    with open(__file__, encoding="utf-8") as source:
        text = source.read()

    disallowed_markers = (
        "aware_" "runtime",
        "aware_" "environment_artifacts",
        "resolve_environment_lane_" "context",
        "hydrate_orm_graph_" "from_oig",
        "resolve_environment_runtime_" "manifest",
        "Runtime" "Harness",
    )

    assert [marker for marker in disallowed_markers if marker in text] == []


def _identity_commit_event(
    *,
    identity_id: UUID,
    identity_projection_hash: str,
    identity_commit_id: UUID,
    identity_function_id: UUID,
    object_instance_graph_commit_id: UUID,
    object_instance_graph_id: UUID,
    object_instance_graph_identity_id: UUID,
) -> OntologyCommitEventEnvelope:
    return OntologyCommitEventEnvelope(
        event_id=uuid4(),
        emitted_at_unix_ms=1,
        ontology_authority_id="aware_meta",
        actor_id=uuid4(),
        domain_branch_id=identity_id,
        domain_projection_hash=identity_projection_hash,
        domain_commit_id=identity_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=object_instance_graph_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_branch_id=uuid4(),
        graph_hash_post="sha256:identity",
        root_object_id=identity_id,
        commit_action=OntologyGraphCommitActionMetadata(
            call_target=OntologyGraphFunctionCallTarget.opg_constructor,
            function_id=identity_function_id,
            operation_label="Identity.signup_via_profile",
            object_id=None,
            source_class_instance_identity_id=uuid4(),
        ),
    )
