from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_environment_sdk import (
    EnvironmentOntologyClient,
    EnvironmentOntologyContext,
    EnvironmentOntologyError,
)
from aware_environment_service_dto.environment.environment import (
    AttachEnvironmentOntologyRequest,
    AttachEnvironmentOntologyResponse,
    EnsureEnvironmentOntologyRuntimeRequest,
    EnsureEnvironmentOntologyRuntimeResponse,
    EnvironmentOntologyMembership,
    ListEnvironmentOntologiesRequest,
    ListEnvironmentOntologiesResponse,
)


class _RecordingOntologyCapability:
    def __init__(self, *, status: str = "succeeded") -> None:
        self.status = status
        self.attach_requests: list[AttachEnvironmentOntologyRequest] = []
        self.ensure_runtime_requests: list[EnsureEnvironmentOntologyRuntimeRequest] = []
        self.list_requests: list[ListEnvironmentOntologiesRequest] = []
        self.membership_id = uuid4()
        self.commit_id = uuid4()
        self.object_instance_graph_commit_id = uuid4()

    async def attach_environment_ontology(
        self,
        request: AttachEnvironmentOntologyRequest,
    ) -> AttachEnvironmentOntologyResponse:
        self.attach_requests.append(request)
        return AttachEnvironmentOntologyResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status=self.status,
            error=None if self.status == "succeeded" else "blocked",
            membership=(
                EnvironmentOntologyMembership(
                    environment_ontology_id=self.membership_id,
                    ontology_id=request.ontology_id,
                    role=request.role,
                    status=request.status,
                    title=request.title,
                    description=request.description,
                    commit_id=self.commit_id,
                    graph_hash_post="graph.after",
                    evidence={"source": "recording"},
                )
                if self.status == "succeeded"
                else None
            ),
            commit_id=self.commit_id if self.status == "succeeded" else None,
            object_instance_graph_commit_id=(
                self.object_instance_graph_commit_id
                if self.status == "succeeded"
                else None
            ),
            graph_hash_pre="graph.before" if self.status == "succeeded" else None,
            graph_hash_post="graph.after" if self.status == "succeeded" else None,
            evidence={"source": "recording"},
        )

    async def ensure_environment_ontology_runtime(
        self,
        request: EnsureEnvironmentOntologyRuntimeRequest,
    ) -> EnsureEnvironmentOntologyRuntimeResponse:
        self.ensure_runtime_requests.append(request)
        return EnsureEnvironmentOntologyRuntimeResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status=self.status,
            error=None if self.status == "succeeded" else "blocked",
            ontology_id=request.ontology_id,
            package_name=request.package_name,
            fqn_prefix=request.fqn_prefix,
            artifact_set_id=request.artifact_set_id or "agent-runtime-artifact-set",
            runtime_projection_descriptor_count=1,
            capability_object_count=1,
            capability_function_count=2,
            registered_artifact_ref_count=1,
            registry_artifact_ref_count=3,
            membership_commit_id=request.membership_commit_id,
            evidence={"source": "recording"},
        )

    async def list_environment_ontologies(
        self,
        request: ListEnvironmentOntologiesRequest,
    ) -> ListEnvironmentOntologiesResponse:
        self.list_requests.append(request)
        ontology_id = uuid4()
        return ListEnvironmentOntologiesResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status=self.status,
            error=None if self.status == "succeeded" else "blocked",
            memberships=(
                [
                    EnvironmentOntologyMembership(
                        environment_ontology_id=self.membership_id,
                        ontology_id=ontology_id,
                        role="runtime",
                        status="active",
                        title="Runtime ontology",
                        commit_id=request.commit_id,
                        graph_hash_post=request.expected_graph_hash_post,
                    )
                ]
                if self.status == "succeeded"
                else []
            ),
            commit_id=request.commit_id,
            object_instance_graph_commit_id=(
                self.object_instance_graph_commit_id
                if self.status == "succeeded"
                else None
            ),
            graph_hash_post=request.expected_graph_hash_post,
            evidence={"source": "recording"},
        )


class _RecordingEnvironmentApi:
    def __init__(self, *, status: str = "succeeded") -> None:
        self.ontology = _RecordingOntologyCapability(status=status)


class _RecordingGeneratedApiClient:
    def __init__(self, *, status: str = "succeeded") -> None:
        self.environment = _RecordingEnvironmentApi(status=status)


def _context() -> EnvironmentOntologyContext:
    return EnvironmentOntologyContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="environment.projection",
    )


@pytest.mark.asyncio
async def test_environment_ontology_client_attach_builds_request() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentOntologyClient(api_client=api_client, context=context)
    ontology_id = uuid4()
    expected_head_commit_id = uuid4()

    result = await client.attach_ontology(
        ontology_id=ontology_id,
        role="runtime",
        status="active",
        title="Runtime ontology",
        description="Attached for proof",
        expected_graph_hash_pre="graph.before",
        expected_head_commit_id=expected_head_commit_id,
        publish=True,
    )

    assert result.status == "succeeded"
    assert result.membership is not None
    assert result.membership.ontology_id == ontology_id
    assert result.commit_id == api_client.environment.ontology.commit_id

    request = api_client.environment.ontology.attach_requests[0]
    assert request.actor_id == context.actor_id
    assert request.environment_id == context.environment_id
    assert request.branch_id == context.branch_id
    assert request.projection_hash == context.projection_hash
    assert request.ontology_id == ontology_id
    assert request.expected_head_commit_id == expected_head_commit_id
    assert request.publish is True


@pytest.mark.asyncio
async def test_environment_ontology_client_list_builds_request() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentOntologyClient(api_client=api_client, context=context)
    commit_id = uuid4()

    result = await client.list_ontologies(
        commit_id=commit_id,
        expected_graph_hash_post="graph.after",
    )

    assert result.status == "succeeded"
    assert result.commit_id == commit_id
    assert len(result.memberships) == 1
    assert result.memberships[0].commit_id == commit_id

    request = api_client.environment.ontology.list_requests[0]
    assert request.actor_id == context.actor_id
    assert request.environment_id == context.environment_id
    assert request.branch_id == context.branch_id
    assert request.projection_hash == context.projection_hash
    assert request.commit_id == commit_id
    assert request.expected_graph_hash_post == "graph.after"


@pytest.mark.asyncio
async def test_environment_ontology_client_ensure_runtime_builds_request() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentOntologyClient(api_client=api_client, context=context)
    ontology_id = uuid4()
    membership_commit_id = uuid4()

    result = await client.ensure_runtime(
        ontology_id=ontology_id,
        package_name="agent-ontology",
        fqn_prefix="aware_agent",
        artifact_set_id="agent-runtime-artifact-set",
        materialization_ref="agent.materialization.test",
        source_payload={"package_name": "agent-ontology"},
        membership_commit_id=membership_commit_id,
    )

    assert result.status == "succeeded"
    assert result.ontology_id == ontology_id
    assert result.artifact_set_id == "agent-runtime-artifact-set"
    assert result.capability_function_count == 2
    assert result.registry_artifact_ref_count == 3
    assert result.membership_commit_id == membership_commit_id

    request = api_client.environment.ontology.ensure_runtime_requests[0]
    assert request.actor_id == context.actor_id
    assert request.environment_id == context.environment_id
    assert request.branch_id == context.branch_id
    assert request.projection_hash == context.projection_hash
    assert request.ontology_id == ontology_id
    assert request.package_name == "agent-ontology"
    assert request.fqn_prefix == "aware_agent"
    assert request.materialization_ref == "agent.materialization.test"
    assert request.source_payload == {"package_name": "agent-ontology"}
    assert request.membership_commit_id == membership_commit_id


@pytest.mark.asyncio
async def test_environment_ontology_client_raises_on_failed_attach() -> None:
    api_client = _RecordingGeneratedApiClient(status="failed")
    client = EnvironmentOntologyClient(api_client=api_client, context=_context())

    with pytest.raises(EnvironmentOntologyError):
        await client.attach_ontology(ontology_id=uuid4())


@pytest.mark.asyncio
async def test_environment_ontology_client_raises_on_failed_runtime() -> None:
    api_client = _RecordingGeneratedApiClient(status="failed")
    client = EnvironmentOntologyClient(api_client=api_client, context=_context())

    with pytest.raises(EnvironmentOntologyError):
        await client.ensure_runtime(package_name="agent-ontology")


def test_environment_ontology_context_from_object() -> None:
    class _Context:
        actor_id = uuid4()
        environment_id = uuid4()
        branch_id = uuid4()
        projection_hash = "environment.projection"

    context = EnvironmentOntologyContext.from_object(_Context())

    assert isinstance(context.environment_id, UUID)
    assert context.actor_id == _Context.actor_id
    assert context.branch_id == _Context.branch_id
    assert context.projection_hash == "environment.projection"
