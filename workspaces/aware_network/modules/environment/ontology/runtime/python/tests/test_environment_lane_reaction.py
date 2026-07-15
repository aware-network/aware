# pyright: reportImplicitRelativeImport=false, reportMissingImports=false

from __future__ import annotations

from collections.abc import AsyncIterator
import sys
from types import SimpleNamespace
from uuid import uuid4

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
    _REPO_ROOT / "modules" / "history" / "structure" / "ontology" / "python",
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
    OntologyGraphCommitActionMetadata,
)
from aware_ontology_service_dto.graph.instance.commit_event import (  # noqa: E402
    OntologyCommitSubscriptionRequest,
)
from aware_ontology_service_dto.graph.instance.commit_event import (  # noqa: E402
    OntologyCommitSubscriptionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call_target import (  # noqa: E402
    OntologyGraphFunctionCallTarget,
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
from aware_meta_ontology.stable_ids import (  # noqa: E402
    stable_object_instance_graph_branch_id,
)
from aware_environment.reactions.environment_lane import (  # noqa: E402
    DEFAULT_ENVIRONMENT_TOPOLOGY_SUBSCRIBER_ID,
    ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID,
    EnvironmentOntologyApiClients,
    EnvironmentTopologyAttachFunctionPlanner,
    EnvironmentTopologyAttachPlan,
    EnvironmentTopologyAttachPlannerConfig,
    EnvironmentTopologyCommitSubscriber,
    EnvironmentTopologyOntologyGraphState,
    EnvironmentTopologyReactionRecord,
    EnvironmentTopologyThreadInterest,
    InMemoryEnvironmentTopologyReactionStore,
)


class _FakeCommitClient:
    def __init__(self, events: tuple[OntologyCommitEventEnvelope, ...] = ()) -> None:
        self.events = events
        self.subscription_requests: list[OntologyCommitSubscriptionRequest] = []

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
        self.subscription_requests.append(request)
        for event in self.events:
            yield event


class _FakeGraphClient:
    def __init__(
        self,
        *,
        invoke_status: str = "succeeded",
        lane_head_status: str = "succeeded",
        commit_status: str = "succeeded",
        commit_payload: dict[str, object] | None = None,
    ) -> None:
        self.invoke_status = invoke_status
        self.lane_head_status = lane_head_status
        self.commit_status = commit_status
        self.commit_payload = commit_payload
        self.lane_head_requests: list[OntologyGraphGetLaneHeadRequest] = []
        self.commit_requests: list[OntologyGraphGetObjectInstanceGraphCommitRequest] = (
            []
        )
        self.invoke_requests: list[OntologyGraphInvokeFunctionRequest] = []

    async def get_lane_head(
        self,
        request: OntologyGraphGetLaneHeadRequest,
    ) -> OntologyGraphGetLaneHeadResponse:
        self.lane_head_requests.append(request)
        return OntologyGraphGetLaneHeadResponse(
            status=self.lane_head_status,
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            domain_commit_id=(
                uuid4() if self.lane_head_status == "succeeded" else None
            ),
            graph_hash_post=(
                "sha256:head" if self.lane_head_status == "succeeded" else None
            ),
            object_instance_graph_id=(
                uuid4() if self.lane_head_status == "succeeded" else None
            ),
            root_object_id=(uuid4() if self.lane_head_status == "succeeded" else None),
            head_version=(1 if self.lane_head_status == "succeeded" else None),
            error=(
                None
                if self.lane_head_status == "succeeded"
                else "lane head unavailable"
            ),
        )

    async def get_object_instance_graph_commit(
        self,
        request: OntologyGraphGetObjectInstanceGraphCommitRequest,
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse:
        self.commit_requests.append(request)
        return OntologyGraphGetObjectInstanceGraphCommitResponse(
            status=self.commit_status,
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            domain_commit_id=request.domain_commit_id,
            object_instance_graph_commit_id=(
                uuid4() if self.commit_status == "succeeded" else None
            ),
            object_instance_graph_id=(
                uuid4() if self.commit_status == "succeeded" else None
            ),
            object_instance_graph_identity_id=(
                uuid4() if self.commit_status == "succeeded" else None
            ),
            root_object_id=(uuid4() if self.commit_status == "succeeded" else None),
            graph_hash_post=(
                "sha256:commit" if self.commit_status == "succeeded" else None
            ),
            commit=self.commit_payload,
            error=(
                None
                if self.commit_status == "succeeded"
                else "domain commit unavailable"
            ),
        )

    async def invoke_function(
        self,
        request: OntologyGraphInvokeFunctionRequest,
    ) -> OntologyGraphInvokeFunctionResponse:
        self.invoke_requests.append(request)
        return OntologyGraphInvokeFunctionResponse(
            status=self.invoke_status,
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            domain_commit_id=(uuid4() if self.invoke_status == "succeeded" else None),
            error=(None if self.invoke_status == "succeeded" else "attach failed"),
        )


class _FakePlanner:
    def __init__(self) -> None:
        self.events: list[OntologyCommitEventEnvelope] = []
        self.request = OntologyGraphInvokeFunctionRequest(
            actor_id=uuid4(),
            domain_branch_id=uuid4(),
            domain_projection_hash="Environment",
            call_target=OntologyGraphFunctionCallTarget.instance,
            target_object_id=uuid4(),
            function_id=uuid4(),
            kwargs={
                "domain_branch_id": str(uuid4()),
                "projection_hash": "domain",
                "title": None,
                "is_active": True,
            },
        )

    def build_attach_plan(
        self,
        ontology_graph_state: EnvironmentTopologyOntologyGraphState,
    ) -> EnvironmentTopologyAttachPlan | None:
        self.events.append(ontology_graph_state.event)
        return EnvironmentTopologyAttachPlan(request=self.request)


class _StaticThreadInterestResolver:
    def __init__(
        self, interests: tuple[EnvironmentTopologyThreadInterest, ...]
    ) -> None:
        self.interests = interests
        self.requests: list[tuple[OntologyCommitEventEnvelope, object]] = []

    async def resolve_thread_interests(
        self,
        *,
        event: OntologyCommitEventEnvelope,
        object_instance_graph_branch_id,
    ) -> tuple[EnvironmentTopologyThreadInterest, ...]:
        self.requests.append((event, object_instance_graph_branch_id))
        return self.interests


@pytest.mark.asyncio
async def test_environment_subscriber_consumes_ontology_stream_and_reenters_ontology_graph() -> (
    None
):
    event = _commit_event()
    interest = _thread_interest(event)
    commit = _FakeCommitClient(events=(event,))
    graph = _FakeGraphClient()
    planner = _FakePlanner()
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(commit=commit, graph=graph),
        planner=planner,
        thread_interest_resolver=_StaticThreadInterestResolver((interest,)),
    )

    outcomes = await subscriber.run(max_events=1)

    assert len(outcomes) == 1
    assert outcomes[0].status == "succeeded"
    assert commit.subscription_requests[0].subscriber_id == (
        DEFAULT_ENVIRONMENT_TOPOLOGY_SUBSCRIBER_ID
    )
    assert commit.subscription_requests[0].event_families == ["ontology.oig_commit"]
    assert planner.events == [event]
    assert len(graph.lane_head_requests) == 1
    assert graph.lane_head_requests[0].domain_branch_id == event.domain_branch_id
    assert graph.lane_head_requests[0].domain_projection_hash == (
        event.domain_projection_hash
    )
    assert len(graph.commit_requests) == 1
    assert graph.commit_requests[0].domain_commit_id == event.domain_commit_id
    assert graph.invoke_requests == [planner.request]
    assert outcomes[0].ontology_graph_state is not None
    assert outcomes[0].record is not None
    assert outcomes[0].record.lane_head_domain_commit_id is not None
    assert outcomes[0].record.object_instance_graph_commit_id is not None
    assert outcomes[0].record.object_instance_graph_branch_id == (
        interest.object_instance_graph_branch_id
    )
    assert outcomes[0].record.thread_id == interest.thread_id
    assert outcomes[0].record.topology_projection_hash == (
        interest.topology_projection_hash
    )


@pytest.mark.asyncio
async def test_environment_topology_attach_function_planner_builds_thread_attach_request() -> (
    None
):
    event = _commit_event(metadata={"package_name": "Home Devices"})
    interest = _thread_interest(event)
    graph = _FakeGraphClient(
        commit_payload={"object_instance_graph_name": "Fallback Name"}
    )
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_FakeCommitClient(),
            graph=graph,
        ),
        planner=EnvironmentTopologyAttachFunctionPlanner(
            EnvironmentTopologyAttachPlannerConfig()
        ),
        thread_interest_resolver=_StaticThreadInterestResolver((interest,)),
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "succeeded"
    assert len(graph.lane_head_requests) == 1
    assert len(graph.commit_requests) == 1
    assert len(graph.invoke_requests) == 1
    request = graph.invoke_requests[0]
    assert request.domain_branch_id == interest.topology_branch_id
    assert request.domain_projection_hash == interest.topology_projection_hash
    assert request.call_target == OntologyGraphFunctionCallTarget.instance
    assert request.target_object_id == interest.thread_id
    assert request.function_id == ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID
    assert request.kwargs["domain_branch_id"] == str(event.domain_branch_id)
    assert request.kwargs["projection_hash"] == event.domain_projection_hash
    assert request.kwargs["title"] == "Home Devices"
    assert request.kwargs["is_active"] is True
    assert getattr(request, "orchestration_context", None) is None


@pytest.mark.asyncio
async def test_environment_subscriber_skips_own_topology_attach_event_by_function_id() -> (
    None
):
    event = _commit_event(
        commit_action=OntologyGraphCommitActionMetadata(
            call_target=OntologyGraphFunctionCallTarget.instance,
            function_id=ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID,
            operation_label="ontology.graph.invoke_function",
            object_id=uuid4(),
        )
    )
    graph = _FakeGraphClient()
    planner = EnvironmentTopologyAttachFunctionPlanner(
        EnvironmentTopologyAttachPlannerConfig()
    )
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_FakeCommitClient(),
            graph=graph,
        ),
        planner=planner,
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "skipped"
    assert outcome.reason == "environment_topology_event"
    assert graph.lane_head_requests == []
    assert graph.commit_requests == []
    assert graph.invoke_requests == []


@pytest.mark.asyncio
async def test_environment_subscriber_fails_when_thread_interest_projection_missing() -> (
    None
):
    event = _commit_event()
    interest = _thread_interest(event, topology_projection_hash=" ")
    graph = _FakeGraphClient()
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_FakeCommitClient(),
            graph=graph,
        ),
        planner=EnvironmentTopologyAttachFunctionPlanner(
            EnvironmentTopologyAttachPlannerConfig()
        ),
        thread_interest_resolver=_StaticThreadInterestResolver((interest,)),
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "failed"
    assert outcome.reason == "planner_failed"
    assert len(graph.lane_head_requests) == 1
    assert len(graph.commit_requests) == 1
    assert graph.invoke_requests == []
    assert outcome.record is not None
    assert outcome.record.status == "failed"
    assert outcome.record.reason == "planner_failed"
    assert outcome.record.error is not None
    assert "topology projection hash" in outcome.record.error


@pytest.mark.asyncio
async def test_environment_subscriber_skips_when_no_thread_oigb_interest() -> None:
    event = _commit_event()
    graph = _FakeGraphClient()
    planner = _FakePlanner()
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_FakeCommitClient(),
            graph=graph,
        ),
        planner=planner,
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "skipped"
    assert outcome.reason == "no_thread_oigb_interest"
    assert planner.events == []
    assert graph.lane_head_requests == []
    assert graph.commit_requests == []
    assert graph.invoke_requests == []


@pytest.mark.asyncio
async def test_environment_subscriber_treats_successful_duplicate_as_noop() -> None:
    event = _commit_event()
    interest = _thread_interest(event)
    store = InMemoryEnvironmentTopologyReactionStore()
    store.put(
        EnvironmentTopologyReactionRecord(
            subscriber_id=DEFAULT_ENVIRONMENT_TOPOLOGY_SUBSCRIBER_ID,
            event_id=event.event_id,
            status="succeeded",
        )
    )
    graph = _FakeGraphClient()
    planner = _FakePlanner()
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_FakeCommitClient(),
            graph=graph,
        ),
        planner=planner,
        thread_interest_resolver=_StaticThreadInterestResolver((interest,)),
        store=store,
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "duplicate"
    assert outcome.reason == "already_succeeded"
    assert planner.events == []
    assert graph.lane_head_requests == []
    assert graph.commit_requests == []
    assert graph.invoke_requests == []


@pytest.mark.asyncio
async def test_environment_subscriber_records_failed_ontology_graph_reentry() -> None:
    event = _commit_event()
    interest = _thread_interest(event)
    graph = _FakeGraphClient(invoke_status="failed")
    planner = _FakePlanner()
    store = InMemoryEnvironmentTopologyReactionStore()
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_FakeCommitClient(),
            graph=graph,
        ),
        planner=planner,
        thread_interest_resolver=_StaticThreadInterestResolver((interest,)),
        store=store,
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "failed"
    assert outcome.reason == "attach failed"
    assert len(graph.lane_head_requests) == 1
    assert len(graph.commit_requests) == 1
    assert len(graph.invoke_requests) == 1
    record = store.get(
        subscriber_id=DEFAULT_ENVIRONMENT_TOPOLOGY_SUBSCRIBER_ID,
        event_id=event.event_id,
    )
    assert record is not None
    assert record.status == "failed"
    assert record.error == "attach failed"


@pytest.mark.asyncio
async def test_environment_subscriber_fails_before_planning_when_lane_head_missing() -> (
    None
):
    event = _commit_event()
    interest = _thread_interest(event)
    graph = _FakeGraphClient(lane_head_status="empty")
    planner = _FakePlanner()
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_FakeCommitClient(),
            graph=graph,
        ),
        planner=planner,
        thread_interest_resolver=_StaticThreadInterestResolver((interest,)),
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "failed"
    assert outcome.reason == "lane_head_unavailable"
    assert planner.events == []
    assert len(graph.lane_head_requests) == 1
    assert graph.commit_requests == []
    assert graph.invoke_requests == []
    assert outcome.record is not None
    assert outcome.record.error == "lane head unavailable"


@pytest.mark.asyncio
async def test_environment_subscriber_fails_before_planning_when_commit_missing() -> (
    None
):
    event = _commit_event()
    interest = _thread_interest(event)
    graph = _FakeGraphClient(commit_status="missing")
    planner = _FakePlanner()
    subscriber = EnvironmentTopologyCommitSubscriber(
        clients=EnvironmentOntologyApiClients(
            commit=_FakeCommitClient(),
            graph=graph,
        ),
        planner=planner,
        thread_interest_resolver=_StaticThreadInterestResolver((interest,)),
    )

    outcome = await subscriber.process_event(event)

    assert outcome.status == "failed"
    assert outcome.reason == "object_instance_graph_commit_unavailable"
    assert planner.events == []
    assert len(graph.lane_head_requests) == 1
    assert len(graph.commit_requests) == 1
    assert graph.invoke_requests == []
    assert outcome.record is not None
    assert outcome.record.error == "domain commit unavailable"


def test_environment_ontology_api_clients_wrap_generated_client_shape() -> None:
    commit = _FakeCommitClient()
    graph = _FakeGraphClient()

    generated = SimpleNamespace(
        ontology=SimpleNamespace(
            commit=commit,
            graph=graph,
        )
    )

    clients = EnvironmentOntologyApiClients.from_ontology_api_client(generated)

    assert clients.commit is commit
    assert clients.graph is graph


def _commit_event(
    *,
    commit_action: OntologyGraphCommitActionMetadata | None = None,
    metadata: dict[str, object] | None = None,
) -> OntologyCommitEventEnvelope:
    branch_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    object_instance_graph_branch_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch_id=branch_id,
    )
    return OntologyCommitEventEnvelope(
        event_id=uuid4(),
        emitted_at_unix_ms=1,
        ontology_authority_id="aware_meta",
        actor_id=uuid4(),
        domain_branch_id=branch_id,
        domain_projection_hash="domain",
        domain_commit_id=uuid4(),
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        object_instance_graph_commit_id=uuid4(),
        object_instance_graph_id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        graph_hash_post="post",
        commit_action=commit_action,
        metadata=metadata or {},
    )


def _thread_interest(
    event: OntologyCommitEventEnvelope,
    *,
    topology_projection_hash: str = "environment-profile-projection",
) -> EnvironmentTopologyThreadInterest:
    object_instance_graph_branch_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=event.object_instance_graph_identity_id,
        branch_id=event.domain_branch_id,
    )
    return EnvironmentTopologyThreadInterest(
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        thread_id=uuid4(),
        topology_branch_id=uuid4(),
        topology_projection_hash=topology_projection_hash,
    )
