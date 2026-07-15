"""Environment reaction from Ontology commit fanout to Environment topology."""

from __future__ import annotations

# pyright: reportMissingImports=false

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from aware_code.types import JsonObject
from aware_meta_ontology.stable_ids import (
    stable_function_config_id,
    stable_object_instance_graph_branch_id,
)
from aware_ontology_service_dto.graph.instance.commit_event import (
    OntologyCommitEventEnvelope,
)
from aware_ontology_service_dto.graph.instance.commit_event import (
    OntologyCommitSubscriptionRequest,
)
from aware_ontology_service_dto.graph.instance.commit_event import (
    OntologyCommitSubscriptionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call_target import (
    OntologyGraphFunctionCallTarget,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphInvokeFunctionRequest,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphInvokeFunctionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetLaneHeadRequest,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetLaneHeadResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetObjectInstanceGraphCommitRequest,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetObjectInstanceGraphCommitResponse,
)

DEFAULT_ENVIRONMENT_TOPOLOGY_SUBSCRIBER_ID = "aware_environment.topology"
DEFAULT_ENVIRONMENT_ENVIRONMENT_LANE_SUBSCRIBER_ID = (
    DEFAULT_ENVIRONMENT_TOPOLOGY_SUBSCRIBER_ID
)
ONTOLOGY_OIG_COMMIT_EVENT_FAMILY = "ontology.oig_commit"
ENVIRONMENT_TOPOLOGY_ATTACH_OWNER_KEY = "aware_environment.thread.Thread"
ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_NAME = "attach_lane"
ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID = stable_function_config_id(
    owner_key=ENVIRONMENT_TOPOLOGY_ATTACH_OWNER_KEY,
    name=ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_NAME,
    kind="instance",
)


class OntologyCommitSubscriptionClient(Protocol):
    async def subscribe(
        self,
        request: OntologyCommitSubscriptionRequest,
    ) -> OntologyCommitSubscriptionResponse: ...

    def stream_subscribe(
        self,
        request: OntologyCommitSubscriptionRequest,
    ) -> AsyncIterator[OntologyCommitEventEnvelope]: ...


class OntologyGraphInvokeClient(Protocol):
    async def get_lane_head(
        self,
        request: OntologyGraphGetLaneHeadRequest,
    ) -> OntologyGraphGetLaneHeadResponse: ...

    async def get_object_instance_graph_commit(
        self,
        request: OntologyGraphGetObjectInstanceGraphCommitRequest,
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse: ...

    async def invoke_function(
        self,
        request: OntologyGraphInvokeFunctionRequest,
    ) -> OntologyGraphInvokeFunctionResponse: ...


class GeneratedOntologyApiClient(Protocol):
    @property
    def commit(self) -> OntologyCommitSubscriptionClient: ...

    @property
    def graph(self) -> OntologyGraphInvokeClient: ...


class GeneratedOntologyApiRootClient(Protocol):
    @property
    def ontology(self) -> GeneratedOntologyApiClient: ...


@dataclass(frozen=True, slots=True)
class EnvironmentOntologyApiClients:
    """Generated Ontology API client ports used by Environment lane reactions."""

    commit: OntologyCommitSubscriptionClient
    graph: OntologyGraphInvokeClient

    @classmethod
    def from_ontology_api_client(
        cls,
        client: GeneratedOntologyApiRootClient,
    ) -> "EnvironmentOntologyApiClients":
        ontology = client.ontology
        return cls(
            commit=ontology.commit,
            graph=ontology.graph,
        )


@dataclass(frozen=True, slots=True)
class EnvironmentTopologyAttachPlan:
    request: OntologyGraphInvokeFunctionRequest
    reason: str = "attach_domain_lane_to_thread"


@dataclass(frozen=True, slots=True)
class EnvironmentTopologyThreadInterest:
    """Environment-owned Thread interest in a committed OIG branch."""

    object_instance_graph_branch_id: UUID
    thread_id: UUID
    topology_branch_id: UUID
    topology_projection_hash: str
    title: str | None = None
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class EnvironmentTopologyOntologyGraphState:
    event: OntologyCommitEventEnvelope
    object_instance_graph_branch_id: UUID
    thread_interest: EnvironmentTopologyThreadInterest
    lane_head: OntologyGraphGetLaneHeadResponse
    object_instance_graph_commit: OntologyGraphGetObjectInstanceGraphCommitResponse


class EnvironmentTopologyThreadInterestResolver(Protocol):
    async def resolve_thread_interests(
        self,
        *,
        event: OntologyCommitEventEnvelope,
        object_instance_graph_branch_id: UUID,
    ) -> tuple[EnvironmentTopologyThreadInterest, ...]: ...


@dataclass(frozen=True, slots=True)
class NoopEnvironmentTopologyThreadInterestResolver:
    async def resolve_thread_interests(
        self,
        *,
        event: OntologyCommitEventEnvelope,
        object_instance_graph_branch_id: UUID,
    ) -> tuple[EnvironmentTopologyThreadInterest, ...]:
        return ()


class EnvironmentTopologyAttachPlanner(Protocol):
    def build_attach_plan(
        self,
        ontology_graph_state: EnvironmentTopologyOntologyGraphState,
    ) -> EnvironmentTopologyAttachPlan | None: ...


@dataclass(frozen=True, slots=True)
class EnvironmentTopologyAttachPlannerConfig:
    """Policy inputs required for Environment Environment lane attachment."""

    function_id: UUID = ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID
    attach_title_metadata_keys: tuple[str, ...] = (
        "title",
        "package_name",
        "package",
        "operation_label",
    )
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class EnvironmentTopologyAttachFunctionPlanner:
    """Build Environment lane attach calls from Environment-owned thread interests."""

    config: EnvironmentTopologyAttachPlannerConfig

    def build_attach_plan(
        self,
        ontology_graph_state: EnvironmentTopologyOntologyGraphState,
    ) -> EnvironmentTopologyAttachPlan | None:
        event = ontology_graph_state.event
        thread_interest = ontology_graph_state.thread_interest

        topology_projection_hash = thread_interest.topology_projection_hash.strip()
        if not topology_projection_hash:
            raise ValueError(
                "Environment topology attach planner requires thread-interest "
                "topology projection hash"
            )

        if (
            event.domain_branch_id == thread_interest.topology_branch_id
            and event.domain_projection_hash == topology_projection_hash
        ):
            return None

        request = OntologyGraphInvokeFunctionRequest(
            actor_id=event.actor_id,
            domain_branch_id=thread_interest.topology_branch_id,
            domain_projection_hash=topology_projection_hash,
            call_target=OntologyGraphFunctionCallTarget.instance,
            target_object_id=thread_interest.thread_id,
            function_id=self.config.function_id,
            kwargs=JsonObject(
                {
                    "domain_branch_id": str(event.domain_branch_id),
                    "projection_hash": event.domain_projection_hash,
                    "title": thread_interest.title
                    or _attachment_title(
                        ontology_graph_state=ontology_graph_state,
                        metadata_keys=self.config.attach_title_metadata_keys,
                    ),
                    "is_active": thread_interest.is_active,
                }
            ),
        )
        return EnvironmentTopologyAttachPlan(request=request)


@dataclass(frozen=True, slots=True)
class EnvironmentTopologyReactionRecord:
    subscriber_id: str
    event_id: UUID
    status: str
    reason: str | None = None
    domain_branch_id: UUID | None = None
    domain_projection_hash: str | None = None
    ontology_domain_commit_id: UUID | None = None
    lane_head_domain_commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    object_instance_graph_branch_id: UUID | None = None
    thread_id: UUID | None = None
    topology_branch_id: UUID | None = None
    topology_projection_hash: str | None = None
    affected_thread_count: int = 0
    error: str | None = None
    response_domain_commit_id: UUID | None = None


class EnvironmentTopologyReactionStore(Protocol):
    def get(
        self,
        *,
        subscriber_id: str,
        event_id: UUID,
    ) -> EnvironmentTopologyReactionRecord | None: ...

    def put(self, record: EnvironmentTopologyReactionRecord) -> None: ...


@dataclass(slots=True)
class InMemoryEnvironmentTopologyReactionStore:
    _records: dict[tuple[str, UUID], EnvironmentTopologyReactionRecord] = field(
        default_factory=dict
    )

    def get(
        self,
        *,
        subscriber_id: str,
        event_id: UUID,
    ) -> EnvironmentTopologyReactionRecord | None:
        return self._records.get((subscriber_id, event_id))

    def put(self, record: EnvironmentTopologyReactionRecord) -> None:
        self._records[(record.subscriber_id, record.event_id)] = record


@dataclass(frozen=True, slots=True)
class EnvironmentTopologyReactionOutcome:
    status: str
    event_id: UUID
    reason: str | None = None
    request: OntologyGraphInvokeFunctionRequest | None = None
    response: OntologyGraphInvokeFunctionResponse | None = None
    requests: tuple[OntologyGraphInvokeFunctionRequest, ...] = ()
    responses: tuple[OntologyGraphInvokeFunctionResponse, ...] = ()
    thread_interests: tuple[EnvironmentTopologyThreadInterest, ...] = ()
    ontology_graph_state: EnvironmentTopologyOntologyGraphState | None = None
    record: EnvironmentTopologyReactionRecord | None = None


@dataclass(slots=True)
class EnvironmentTopologyCommitSubscriber:
    """Environment-owned subscriber over the Ontology commit stream.

    This component consumes the generated Ontology API client boundary. It does
    not import Meta service internals and does not read Meta's local commit
    store. Follow-up topology writes re-enter through
    `ontology.graph.invoke_function`.
    """

    clients: EnvironmentOntologyApiClients
    planner: EnvironmentTopologyAttachPlanner
    thread_interest_resolver: EnvironmentTopologyThreadInterestResolver = field(
        default_factory=NoopEnvironmentTopologyThreadInterestResolver
    )
    store: EnvironmentTopologyReactionStore = field(
        default_factory=InMemoryEnvironmentTopologyReactionStore
    )
    subscriber_id: str = DEFAULT_ENVIRONMENT_TOPOLOGY_SUBSCRIBER_ID
    topology_projection_name: str = "EnvironmentProfile"

    async def run(
        self,
        *,
        resume_after_event_id: UUID | None = None,
        max_events: int | None = None,
    ) -> tuple[EnvironmentTopologyReactionOutcome, ...]:
        request = OntologyCommitSubscriptionRequest(
            subscriber_id=self.subscriber_id,
            event_families=[ONTOLOGY_OIG_COMMIT_EVENT_FAMILY],
            include_artifact_refs=False,
            resume_after_event_id=resume_after_event_id,
        )
        response = await self.clients.commit.subscribe(request)
        if not response.accepted:
            raise RuntimeError(
                "Ontology commit subscription rejected: "
                f"subscriber_id={self.subscriber_id}"
            )

        outcomes: list[EnvironmentTopologyReactionOutcome] = []
        async for event in self.clients.commit.stream_subscribe(request):
            outcomes.append(await self.process_event(event))
            if max_events is not None and len(outcomes) >= max_events:
                break
        return tuple(outcomes)

    async def process_event(
        self,
        event: OntologyCommitEventEnvelope,
    ) -> EnvironmentTopologyReactionOutcome:
        previous = self.store.get(
            subscriber_id=self.subscriber_id,
            event_id=event.event_id,
        )
        if previous is not None and previous.status == "succeeded":
            return EnvironmentTopologyReactionOutcome(
                status="duplicate",
                event_id=event.event_id,
                reason="already_succeeded",
                record=previous,
            )

        skip_reason = _skip_reason(event)
        if skip_reason is not None:
            record = self._record(
                event=event,
                status="skipped",
                reason=skip_reason,
            )
            return EnvironmentTopologyReactionOutcome(
                status="skipped",
                event_id=event.event_id,
                reason=skip_reason,
                record=record,
            )

        try:
            object_instance_graph_branch_id = _event_object_instance_graph_branch_id(
                event
            )
            thread_interests = (
                await self.thread_interest_resolver.resolve_thread_interests(
                    event=event,
                    object_instance_graph_branch_id=object_instance_graph_branch_id,
                )
            )
        except Exception as exc:
            error = str(exc)
            record = self._record(
                event=event,
                status="failed",
                reason="thread_interest_resolution_failed",
                error=error,
            )
            return EnvironmentTopologyReactionOutcome(
                status="failed",
                event_id=event.event_id,
                reason="thread_interest_resolution_failed",
                record=record,
            )

        if not thread_interests:
            record = self._record(
                event=event,
                status="skipped",
                reason="no_thread_oigb_interest",
                object_instance_graph_branch_id=object_instance_graph_branch_id,
            )
            return EnvironmentTopologyReactionOutcome(
                status="skipped",
                event_id=event.event_id,
                reason="no_thread_oigb_interest",
                thread_interests=thread_interests,
                record=record,
            )

        requests: list[OntologyGraphInvokeFunctionRequest] = []
        responses: list[OntologyGraphInvokeFunctionResponse] = []
        last_graph_state: EnvironmentTopologyOntologyGraphState | None = None
        for thread_interest in thread_interests:
            if (
                thread_interest.object_instance_graph_branch_id
                != object_instance_graph_branch_id
            ):
                record = self._record(
                    event=event,
                    status="failed",
                    reason="thread_interest_oigb_mismatch",
                    error=(
                        "Environment thread interest targets a different "
                        "ObjectInstanceGraphBranch"
                    ),
                    object_instance_graph_branch_id=object_instance_graph_branch_id,
                    thread_interest=thread_interest,
                    affected_thread_count=len(thread_interests),
                )
                return EnvironmentTopologyReactionOutcome(
                    status="failed",
                    event_id=event.event_id,
                    reason="thread_interest_oigb_mismatch",
                    thread_interests=thread_interests,
                    record=record,
                )

            ontology_graph_state = await self._resolve_ontology_graph_state(
                event=event,
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                thread_interest=thread_interest,
                affected_thread_count=len(thread_interests),
            )
            if isinstance(ontology_graph_state, EnvironmentTopologyReactionOutcome):
                return ontology_graph_state
            last_graph_state = ontology_graph_state

            try:
                plan = self.planner.build_attach_plan(ontology_graph_state)
            except Exception as exc:
                error = str(exc)
                record = self._record(
                    event=event,
                    status="failed",
                    reason="planner_failed",
                    error=error,
                    ontology_graph_state=ontology_graph_state,
                    affected_thread_count=len(thread_interests),
                )
                return EnvironmentTopologyReactionOutcome(
                    status="failed",
                    event_id=event.event_id,
                    reason="planner_failed",
                    thread_interests=thread_interests,
                    ontology_graph_state=ontology_graph_state,
                    record=record,
                )

            if plan is None:
                continue

            self._record(
                event=event,
                status="started",
                reason=plan.reason,
                ontology_graph_state=ontology_graph_state,
                affected_thread_count=len(thread_interests),
            )
            response = await self.clients.graph.invoke_function(plan.request)
            requests.append(plan.request)
            responses.append(response)
            if response.status != "succeeded":
                error = response.error or "Ontology graph invoke failed"
                record = self._record(
                    event=event,
                    status="failed",
                    reason=plan.reason,
                    error=error,
                    response=response,
                    ontology_graph_state=ontology_graph_state,
                    affected_thread_count=len(thread_interests),
                )
                return EnvironmentTopologyReactionOutcome(
                    status="failed",
                    event_id=event.event_id,
                    reason=error,
                    request=plan.request,
                    response=response,
                    requests=tuple(requests),
                    responses=tuple(responses),
                    thread_interests=thread_interests,
                    ontology_graph_state=ontology_graph_state,
                    record=record,
                )

        if not requests:
            record = self._record(
                event=event,
                status="skipped",
                reason="planner_skipped",
                ontology_graph_state=last_graph_state,
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                affected_thread_count=len(thread_interests),
            )
            return EnvironmentTopologyReactionOutcome(
                status="skipped",
                event_id=event.event_id,
                reason="planner_skipped",
                thread_interests=thread_interests,
                ontology_graph_state=last_graph_state,
                record=record,
            )

        record = self._record(
            event=event,
            status="succeeded",
            reason="attach_domain_lane_to_thread",
            response=responses[-1],
            ontology_graph_state=last_graph_state,
            affected_thread_count=len(thread_interests),
        )
        return EnvironmentTopologyReactionOutcome(
            status="succeeded",
            event_id=event.event_id,
            reason="attach_domain_lane_to_thread",
            request=requests[0],
            response=responses[0],
            requests=tuple(requests),
            responses=tuple(responses),
            thread_interests=thread_interests,
            ontology_graph_state=last_graph_state,
            record=record,
        )

    async def _resolve_ontology_graph_state(
        self,
        *,
        event: OntologyCommitEventEnvelope,
        object_instance_graph_branch_id: UUID,
        thread_interest: EnvironmentTopologyThreadInterest,
        affected_thread_count: int,
    ) -> EnvironmentTopologyOntologyGraphState | EnvironmentTopologyReactionOutcome:
        lane_head = await self.clients.graph.get_lane_head(
            OntologyGraphGetLaneHeadRequest(
                actor_id=event.actor_id,
                domain_branch_id=event.domain_branch_id,
                domain_projection_hash=event.domain_projection_hash,
            )
        )
        if lane_head.status != "succeeded":
            return self._failed_ontology_read_outcome(
                event=event,
                reason="lane_head_unavailable",
                error=_ontology_read_error(
                    operation="ontology.graph.get_lane_head",
                    status=lane_head.status,
                    error=lane_head.error,
                ),
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                thread_interest=thread_interest,
                affected_thread_count=affected_thread_count,
            )

        object_instance_graph_commit = (
            await self.clients.graph.get_object_instance_graph_commit(
                OntologyGraphGetObjectInstanceGraphCommitRequest(
                    actor_id=event.actor_id,
                    domain_branch_id=event.domain_branch_id,
                    domain_projection_hash=event.domain_projection_hash,
                    domain_commit_id=event.domain_commit_id,
                )
            )
        )
        if object_instance_graph_commit.status != "succeeded":
            return self._failed_ontology_read_outcome(
                event=event,
                reason="object_instance_graph_commit_unavailable",
                error=_ontology_read_error(
                    operation="ontology.graph.get_object_instance_graph_commit",
                    status=object_instance_graph_commit.status,
                    error=object_instance_graph_commit.error,
                ),
                object_instance_graph_branch_id=object_instance_graph_branch_id,
                thread_interest=thread_interest,
                affected_thread_count=affected_thread_count,
            )

        return EnvironmentTopologyOntologyGraphState(
            event=event,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            thread_interest=thread_interest,
            lane_head=lane_head,
            object_instance_graph_commit=object_instance_graph_commit,
        )

    def _failed_ontology_read_outcome(
        self,
        *,
        event: OntologyCommitEventEnvelope,
        reason: str,
        error: str,
        object_instance_graph_branch_id: UUID | None = None,
        thread_interest: EnvironmentTopologyThreadInterest | None = None,
        affected_thread_count: int = 0,
    ) -> EnvironmentTopologyReactionOutcome:
        record = self._record(
            event=event,
            status="failed",
            reason=reason,
            error=error,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            thread_interest=thread_interest,
            affected_thread_count=affected_thread_count,
        )
        return EnvironmentTopologyReactionOutcome(
            status="failed",
            event_id=event.event_id,
            reason=reason,
            thread_interests=(
                (thread_interest,) if thread_interest is not None else ()
            ),
            record=record,
        )

    def _record(
        self,
        *,
        event: OntologyCommitEventEnvelope,
        status: str,
        reason: str | None,
        error: str | None = None,
        response: OntologyGraphInvokeFunctionResponse | None = None,
        ontology_graph_state: EnvironmentTopologyOntologyGraphState | None = None,
        object_instance_graph_branch_id: UUID | None = None,
        thread_interest: EnvironmentTopologyThreadInterest | None = None,
        affected_thread_count: int = 0,
    ) -> EnvironmentTopologyReactionRecord:
        resolved_thread_interest = (
            thread_interest
            if thread_interest is not None
            else (
                ontology_graph_state.thread_interest
                if ontology_graph_state is not None
                else None
            )
        )
        record = EnvironmentTopologyReactionRecord(
            subscriber_id=self.subscriber_id,
            event_id=event.event_id,
            status=status,
            reason=reason,
            domain_branch_id=event.domain_branch_id,
            domain_projection_hash=event.domain_projection_hash,
            ontology_domain_commit_id=event.domain_commit_id,
            lane_head_domain_commit_id=(
                ontology_graph_state.lane_head.domain_commit_id
                if ontology_graph_state is not None
                else None
            ),
            object_instance_graph_commit_id=(
                ontology_graph_state.object_instance_graph_commit.object_instance_graph_commit_id
                if ontology_graph_state is not None
                else None
            ),
            object_instance_graph_branch_id=(
                object_instance_graph_branch_id
                or (
                    ontology_graph_state.object_instance_graph_branch_id
                    if ontology_graph_state is not None
                    else None
                )
            ),
            thread_id=(
                resolved_thread_interest.thread_id
                if resolved_thread_interest is not None
                else None
            ),
            topology_branch_id=(
                resolved_thread_interest.topology_branch_id
                if resolved_thread_interest is not None
                else None
            ),
            topology_projection_hash=(
                resolved_thread_interest.topology_projection_hash
                if resolved_thread_interest is not None
                else None
            ),
            affected_thread_count=(
                affected_thread_count
                if affected_thread_count
                else (1 if resolved_thread_interest is not None else 0)
            ),
            error=error,
            response_domain_commit_id=(
                response.domain_commit_id if response is not None else None
            ),
        )
        self.store.put(record)
        return record


def _skip_reason(event: OntologyCommitEventEnvelope) -> str | None:
    if event.event_family != ONTOLOGY_OIG_COMMIT_EVENT_FAMILY:
        return "unsupported_event_family"
    if event.metadata.get("environment_topology_event") is True:
        return "environment_topology_event"
    if (
        event.commit_action is not None
        and event.commit_action.function_id == ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID
    ):
        return "environment_topology_event"
    return None


def _event_object_instance_graph_branch_id(
    event: OntologyCommitEventEnvelope,
) -> UUID:
    materialized_oigb_id = getattr(event, "object_instance_graph_branch_id", None)
    if isinstance(materialized_oigb_id, UUID):
        return materialized_oigb_id
    return stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=event.object_instance_graph_identity_id,
        branch_id=event.domain_branch_id,
    )


def _attachment_title(
    *,
    ontology_graph_state: EnvironmentTopologyOntologyGraphState,
    metadata_keys: tuple[str, ...],
) -> str | None:
    event = ontology_graph_state.event
    for key in metadata_keys:
        value = event.metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if event.commit_action is not None:
        operation_label = event.commit_action.operation_label
        if operation_label is not None and operation_label.strip():
            return operation_label.strip()
    commit_payload = ontology_graph_state.object_instance_graph_commit.commit
    if isinstance(commit_payload, dict):
        for key in (
            "object_instance_graph_name",
            "object_instance_graph_key",
            "source_language",
        ):
            value = commit_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return event.domain_projection_hash


def _ontology_read_error(
    *,
    operation: str,
    status: str,
    error: str | None,
) -> str:
    return error or f"{operation} returned status={status}"


__all__ = [
    "DEFAULT_ENVIRONMENT_TOPOLOGY_SUBSCRIBER_ID",
    "DEFAULT_ENVIRONMENT_ENVIRONMENT_LANE_SUBSCRIBER_ID",
    "ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_ID",
    "ENVIRONMENT_TOPOLOGY_ATTACH_FUNCTION_NAME",
    "ENVIRONMENT_TOPOLOGY_ATTACH_OWNER_KEY",
    "EnvironmentOntologyApiClients",
    "EnvironmentTopologyAttachFunctionPlanner",
    "EnvironmentTopologyAttachPlan",
    "EnvironmentTopologyAttachPlanner",
    "EnvironmentTopologyAttachPlannerConfig",
    "EnvironmentTopologyCommitSubscriber",
    "EnvironmentTopologyOntologyGraphState",
    "EnvironmentTopologyReactionOutcome",
    "EnvironmentTopologyReactionRecord",
    "EnvironmentTopologyReactionStore",
    "EnvironmentTopologyThreadInterest",
    "EnvironmentTopologyThreadInterestResolver",
    "InMemoryEnvironmentTopologyReactionStore",
    "NoopEnvironmentTopologyThreadInterestResolver",
    "ONTOLOGY_OIG_COMMIT_EVENT_FAMILY",
    "GeneratedOntologyApiClient",
    "GeneratedOntologyApiRootClient",
    "OntologyCommitSubscriptionClient",
    "OntologyGraphInvokeClient",
]
