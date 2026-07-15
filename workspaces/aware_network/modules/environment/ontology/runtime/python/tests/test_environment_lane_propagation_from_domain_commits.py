from __future__ import annotations

from collections.abc import AsyncIterator
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
    _REPO_ROOT / "apis" / "meta" / "python" / "aware_meta_service_api",
    _REPO_ROOT
    / "workspaces"
    / "aware_kernel"
    / "modules"
    / "ontology"
    / "apis"
    / "ontology"
    / "python"
    / "aware_ontology_service_dto",
    _REPO_ROOT / "libs" / "api" / "python",
    _REPO_ROOT / "modules" / "meta" / "structure" / "ontology" / "python",
    ENVIRONMENT_RUNTIME_ROOT,
    ENVIRONMENT_ONTOLOGY_ROOT / "structure/python/orm_runtime",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

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
from aware_meta_ontology.stable_ids import (  # noqa: E402
    stable_object_instance_graph_branch_id,
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


class _QueuedCommitClient:
    def __init__(self, events: tuple[OntologyCommitEventEnvelope, ...]) -> None:
        self.events = events
        self.subscription_requests: list[OntologyCommitSubscriptionRequest] = []
        self.stream_requests: list[OntologyCommitSubscriptionRequest] = []

    async def subscribe(
        self,
        request: OntologyCommitSubscriptionRequest,
    ) -> OntologyCommitSubscriptionResponse:
        self.subscription_requests.append(request)
        return OntologyCommitSubscriptionResponse(
            subscriber_id=request.subscriber_id,
            accepted=True,
            resume_after_event_id=request.resume_after_event_id,
        )

    async def stream_subscribe(
        self,
        request: OntologyCommitSubscriptionRequest,
    ) -> AsyncIterator[OntologyCommitEventEnvelope]:
        self.stream_requests.append(request)
        for event in self.events:
            yield event


class _RecordingGraphClient:
    def __init__(
        self,
        *,
        lane_head_commit_ids: tuple[UUID, ...],
        topology_projection_hash: str = "environment-profile-projection",
    ) -> None:
        self._lane_head_commit_ids = list(lane_head_commit_ids)
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
        domain_commit_id = (
            self._lane_head_commit_ids.pop(0) if self._lane_head_commit_ids else uuid4()
        )
        return OntologyGraphGetLaneHeadResponse(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            domain_commit_id=domain_commit_id,
            graph_hash_post=f"sha256:{domain_commit_id.hex}",
            object_instance_graph_id=request.domain_branch_id,
            root_object_id=request.domain_branch_id,
            head_version=len(self.lane_head_requests),
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
            object_instance_graph_commit_id=uuid4(),
            object_instance_graph_id=request.domain_branch_id,
            object_instance_graph_identity_id=uuid4(),
            root_object_id=request.domain_branch_id,
            graph_hash_post=f"sha256:{request.domain_commit_id.hex}",
            commit={
                "object_instance_graph_key": str(request.domain_branch_id),
                "object_instance_graph_name": "Domain lane",
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


class _ThreadInterestResolver:
    def __init__(
        self,
        *,
        thread_id: UUID,
        topology_branch_id: UUID,
        topology_projection_hash: str,
    ) -> None:
        self.thread_id = thread_id
        self.topology_branch_id = topology_branch_id
        self.topology_projection_hash = topology_projection_hash
        self.requests: list[tuple[OntologyCommitEventEnvelope, UUID]] = []

    async def resolve_thread_interests(
        self,
        *,
        event: OntologyCommitEventEnvelope,
        object_instance_graph_branch_id: UUID,
    ) -> tuple[EnvironmentTopologyThreadInterest, ...]:
        self.requests.append((event, object_instance_graph_branch_id))
        return (
            EnvironmentTopologyThreadInterest(
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                thread_id=self.thread_id,
                topology_branch_id=self.topology_branch_id,
                topology_projection_hash=self.topology_projection_hash,
            ),
        )


@pytest.mark.asyncio
async def test_domain_commit_events_propagate_to_thread_attach_through_ontology_api() -> (
    None
):
    environment_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/environment-lane-propagation/environment",
    )
    thread_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/environment-lane-propagation/thread",
    )
    domain_branch_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/environment-lane-propagation/domain-branch",
    )
    object_instance_graph_identity_id = uuid5(
        NAMESPACE_URL,
        "aware://tests/environment/environment-lane-propagation/oigi",
    )
    domain_projection_hash = "domain-projection"
    domain_commit_ids = (
        uuid5(
            NAMESPACE_URL,
            "aware://tests/environment/environment-lane-propagation/commit/1",
        ),
        uuid5(
            NAMESPACE_URL,
            "aware://tests/environment/environment-lane-propagation/commit/2",
        ),
    )
    events = tuple(
        _commit_event(
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            domain_commit_id=domain_commit_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            metadata={"title": title},
        )
        for domain_commit_id, title in zip(
            domain_commit_ids,
            ("Domain constructor", "Domain update"),
        )
    )
    commit = _QueuedCommitClient(events)
    graph = _RecordingGraphClient(lane_head_commit_ids=domain_commit_ids)
    topology_branch_id = stable_environment_profile_id(
        environment_id=environment_id,
        key="bootstrap",
    )
    thread_interest_resolver = _ThreadInterestResolver(
        thread_id=thread_id,
        topology_branch_id=topology_branch_id,
        topology_projection_hash=graph.topology_projection_hash,
    )
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(commit=commit, graph=graph),
        planner=EnvironmentTopologyAttachFunctionPlanner(
            EnvironmentTopologyAttachPlannerConfig(),
        ),
        thread_interest_resolver=thread_interest_resolver,
    )

    outcomes = await subscriber.run(max_events=2)

    assert [outcome.status for outcome in outcomes] == ["succeeded", "succeeded"]
    assert len(commit.subscription_requests) == 1
    assert len(commit.stream_requests) == 1
    subscribe_request = commit.subscription_requests[0]
    assert subscribe_request.event_families == ["ontology.oig_commit"]
    assert subscribe_request.include_artifact_refs is False
    expected_oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch_id=domain_branch_id,
    )
    assert [
        object_instance_graph_branch_id
        for _event, object_instance_graph_branch_id in thread_interest_resolver.requests
    ] == [expected_oigb_id, expected_oigb_id]
    assert [request.domain_branch_id for request in graph.lane_head_requests] == [
        domain_branch_id,
        domain_branch_id,
    ]
    assert [request.domain_commit_id for request in graph.commit_requests] == list(
        domain_commit_ids,
    )

    assert len(graph.invoke_requests) == 2
    assert [outcome.record for outcome in outcomes][0] is not None
    assert [outcome.record for outcome in outcomes][1] is not None
    assert [
        outcome.record.lane_head_domain_commit_id
        for outcome in outcomes
        if outcome.record is not None
    ] == list(domain_commit_ids)
    for request, event in zip(graph.invoke_requests, events):
        assert request.domain_branch_id == topology_branch_id
        assert request.domain_projection_hash == graph.topology_projection_hash
        assert request.call_target == OntologyGraphFunctionCallTarget.instance
        assert request.target_object_id == thread_id
        assert request.function_id == ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID
        assert request.kwargs["domain_branch_id"] == str(domain_branch_id)
        assert request.kwargs["projection_hash"] == domain_projection_hash
        assert getattr(request, "orchestration_context", None) is None
        assert request.actor_id == event.actor_id

    assert [request.kwargs["title"] for request in graph.invoke_requests] == [
        "Domain constructor",
        "Domain update",
    ]


@pytest.mark.asyncio
async def test_environment_topology_events_do_not_reenter_thread_attach() -> None:
    event = _commit_event(metadata={"environment_topology_event": True})
    commit = _QueuedCommitClient((event,))
    graph = _RecordingGraphClient(lane_head_commit_ids=(event.domain_commit_id,))
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(commit=commit, graph=graph),
        planner=EnvironmentTopologyAttachFunctionPlanner(
            EnvironmentTopologyAttachPlannerConfig(),
        ),
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "skipped"
    assert outcome.reason == "environment_topology_event"
    assert graph.lane_head_requests == []
    assert graph.commit_requests == []
    assert graph.projection_requests == []
    assert graph.invoke_requests == []


def test_environment_lane_propagation_proof_uses_ontology_api_boundary() -> None:
    source = __file__
    text = open(source, encoding="utf-8").read()

    disallowed_markers = (
        "aware_" "runtime",
        "aware_" "environment_artifacts",
        "register_domain_lane_" "to_thread",
        "advance_environment_lane_" "head",
        "resolve_environment_lane_" "context",
        "hydrate_orm_graph_" "from_oig",
    )

    assert [marker for marker in disallowed_markers if marker in text] == []


def _commit_event(
    *,
    domain_branch_id: UUID | None = None,
    domain_projection_hash: str = "domain-projection",
    domain_commit_id: UUID | None = None,
    object_instance_graph_identity_id: UUID | None = None,
    metadata: dict[str, object] | None = None,
) -> OntologyCommitEventEnvelope:
    branch_id = domain_branch_id or uuid4()
    commit_id = domain_commit_id or uuid4()
    oigi_id = object_instance_graph_identity_id or uuid4()
    object_instance_graph_branch_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=oigi_id,
        branch_id=branch_id,
    )
    return OntologyCommitEventEnvelope(
        event_id=uuid4(),
        emitted_at_unix_ms=1,
        ontology_authority_id="aware_meta",
        actor_id=uuid4(),
        domain_branch_id=branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=commit_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        object_instance_graph_commit_id=uuid4(),
        object_instance_graph_id=branch_id,
        object_instance_graph_identity_id=oigi_id,
        graph_hash_post=f"sha256:{commit_id.hex}",
        metadata=metadata or {},
    )
