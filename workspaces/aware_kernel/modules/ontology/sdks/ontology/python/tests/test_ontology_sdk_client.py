from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

from aware_ontology_sdk import OntologySdkClient, OntologySdkError
from aware_ontology_service_dto.graph.config.package_compile import (
    OntologyObjectConfigGraphPackageEnsureResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetLaneHeadResponse,
    OntologyGraphInvokeFunctionResponse,
    OntologyGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.graph.instance.commit_event import (
    OntologyCommitEventEnvelope,
    OntologyCommitSubscriptionResponse,
)
from aware_ontology_service_dto.persistence.readiness import (
    OntologyDatabaseArtifactReceipt,
    OntologyPersistenceEnsureReadyResponse,
)
from aware_ontology_service_dto.runtime.artifact_set import (
    OntologyMaterializedSemanticRootRef,
    OntologyRuntimeArtifactSet,
    OntologyRuntimeArtifactSetProvenance,
    OntologyRuntimeProjectionDescriptor,
    OntologyRuntimeArtifactSetResolveResponse,
)


ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
BRANCH_ID = UUID("22222222-2222-4222-8222-222222222222")
FUNCTION_ID = UUID("33333333-3333-4333-8333-333333333333")
EVENT_ID = UUID("44444444-4444-4444-8444-444444444444")
OBJECT_INSTANCE_GRAPH_BRANCH_ID = UUID("99999999-2222-4222-8222-999999999999")
ONTOLOGY_CONFIG_ID = UUID("aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa")
ONTOLOGY_CONFIG_OIGI_COMMIT_ID = UUID("aaaaaaaa-3333-4333-8333-aaaaaaaaaaaa")


class _PackageClient:
    def __init__(self) -> None:
        self.last_request = None

    async def ensure_object_config_graph_package(self, request):
        self.last_request = request
        return OntologyObjectConfigGraphPackageEnsureResponse(
            status="succeeded",
            actor_id=request.actor_id,
            aware_toml_path=request.aware_toml_path,
            package_name="ontology-ontology",
        )


class _GraphClient:
    def __init__(self) -> None:
        self.last_lane_head_request = None
        self.last_projection_request = None
        self.last_invoke_request = None

    async def get_lane_head(self, request):
        self.last_lane_head_request = request
        return OntologyGraphGetLaneHeadResponse(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            head_version=7,
        )

    async def get_object_instance_graph_commit(self, request):
        raise AssertionError("not used by this focused test")

    async def resolve_projection(self, request):
        self.last_projection_request = request
        return OntologyGraphResolveProjectionResponse(
            status="succeeded",
            actor_id=request.actor_id,
            projection_name=request.projection_name,
            projection_hash=request.projection_hash,
        )

    async def invoke_function(self, request):
        self.last_invoke_request = request
        return OntologyGraphInvokeFunctionResponse(
            status="succeeded",
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            payload={"ok": True},
        )


class _PersistenceClient:
    def __init__(self) -> None:
        self.last_request = None

    async def ensure_ready(self, request):
        self.last_request = request
        return OntologyPersistenceEnsureReadyResponse(
            status="ready",
            actor_id=request.actor_id,
            sql_root_count=len(request.database_artifact_receipt.sql_roots),
        )


class _CommitClient:
    def __init__(self) -> None:
        self.last_subscribe_request = None
        self.last_stream_request = None

    async def subscribe(self, request):
        self.last_subscribe_request = request
        return OntologyCommitSubscriptionResponse(
            subscriber_id=request.subscriber_id,
            accepted=True,
            resume_after_event_id=request.resume_after_event_id,
        )

    async def stream_subscribe(self, request):
        self.last_stream_request = request
        yield OntologyCommitEventEnvelope(
            event_id=EVENT_ID,
            emitted_at_unix_ms=1,
            ontology_authority_id="aware_ontology",
            actor_id=ACTOR_ID,
            domain_branch_id=BRANCH_ID,
            domain_projection_hash="projection",
            domain_commit_id=UUID("55555555-5555-4555-8555-555555555555"),
            object_instance_graph_commit_id=(
                UUID("66666666-6666-4666-8666-666666666666")
            ),
            object_instance_graph_id=UUID("77777777-7777-4777-8777-777777777777"),
            object_instance_graph_branch_id=OBJECT_INSTANCE_GRAPH_BRANCH_ID,
            object_instance_graph_identity_id=(
                UUID("88888888-8888-4888-8888-888888888888")
            ),
            graph_hash_post="graph.hash",
        )


class _RuntimeClient:
    def __init__(self) -> None:
        self.last_request = None

    async def resolve_runtime_artifact_set(self, request):
        self.last_request = request
        return OntologyRuntimeArtifactSetResolveResponse(
            status="resolved",
            actor_id=request.actor_id,
            package_name=request.package_name,
            fqn_prefix=request.fqn_prefix,
            artifact_set=OntologyRuntimeArtifactSet(
                artifact_set_id="ontology-runtime-artifact-set:test",
                package_name=request.package_name or "ontology-ontology",
                fqn_prefix=request.fqn_prefix or "aware_ontology",
                activation_allowed=False,
                runtime_projection_descriptors=[
                    OntologyRuntimeProjectionDescriptor(
                        projection_name="Environment",
                        projection_hash="environment.projection",
                        object_projection_graph_id=(
                            UUID("99999999-9999-4999-8999-999999999999")
                        ),
                        constructor_function_id=FUNCTION_ID,
                        object_config_graph_id=(
                            UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
                        ),
                    )
                ],
                materialized_semantic_roots=[
                    OntologyMaterializedSemanticRootRef(
                        semantic_root_kind="OntologyConfig",
                        semantic_projection_name="OntologyConfig",
                        semantic_projection_hash="ontology-config.projection",
                        semantic_package_id=ONTOLOGY_CONFIG_ID,
                        semantic_root_id=ONTOLOGY_CONFIG_ID,
                        semantic_object_instance_graph_commit_id=(
                            ONTOLOGY_CONFIG_OIGI_COMMIT_ID
                        ),
                        semantic_root_object_instance_graph_commit_id=(
                            ONTOLOGY_CONFIG_OIGI_COMMIT_ID
                        ),
                    )
                ],
                provenance=OntologyRuntimeArtifactSetProvenance(
                    source_kind="ontology_materialization",
                    ontology_config_id=ONTOLOGY_CONFIG_ID,
                    ontology_config_object_instance_graph_commit_id=(
                        ONTOLOGY_CONFIG_OIGI_COMMIT_ID
                    ),
                ),
            ),
        )


class _OntologyNamespace:
    def __init__(self) -> None:
        self.package = _PackageClient()
        self.graph = _GraphClient()
        self.persistence = _PersistenceClient()
        self.commit = _CommitClient()
        self.runtime = _RuntimeClient()


class _GeneratedApiClient:
    def __init__(self) -> None:
        self.ontology = _OntologyNamespace()


@pytest.mark.asyncio
async def test_sdk_wraps_generated_api_client_operations() -> None:
    api_client = _GeneratedApiClient()
    sdk = OntologySdkClient(api_client=api_client)

    package_response = await sdk.ensure_object_config_graph_package(
        actor_id=ACTOR_ID,
        aware_toml_path="modules/ontology/aware.ontology.toml",
        workspace_root="/repo",
        include_object_config_graph=True,
    )
    assert package_response.package_name == "ontology-ontology"
    package_request = api_client.ontology.package.last_request
    assert package_request is not None
    assert package_request.workspace_root == "/repo"
    assert package_request.include_object_config_graph is True

    lane_response = await sdk.get_lane_head(
        actor_id=ACTOR_ID,
        domain_branch_id=BRANCH_ID,
        domain_projection_hash="projection",
    )
    assert lane_response.head_version == 7

    projection_response = await sdk.resolve_projection(
        actor_id=ACTOR_ID,
        projection_name="runtime",
        include_available=True,
    )
    assert projection_response.projection_name == "runtime"
    projection_request = api_client.ontology.graph.last_projection_request
    assert projection_request is not None
    assert projection_request.include_available is True

    invoke_response = await sdk.invoke_function(
        actor_id=ACTOR_ID,
        domain_branch_id=BRANCH_ID,
        domain_projection_hash="projection",
        function_id=FUNCTION_ID,
        call_target="opg_constructor",
        args=("value",),
        kwargs={"name": "example"},
        publish=True,
    )
    assert invoke_response.payload == {"ok": True}
    invoke_request = api_client.ontology.graph.last_invoke_request
    assert invoke_request is not None
    assert invoke_request.call_target.value == "opg_constructor"
    assert list(invoke_request.args) == ["value"]
    assert dict(invoke_request.kwargs) == {"name": "example"}
    assert invoke_request.publish is True

    readiness_response = await sdk.ensure_ready(
        actor_id=ACTOR_ID,
        database_artifact_receipt=OntologyDatabaseArtifactReceipt(
            sql_roots=["sql/ontology"],
        ),
    )
    assert readiness_response.status == "ready"
    assert readiness_response.sql_root_count == 1

    runtime_response = await sdk.resolve_runtime_artifact_set(
        actor_id=ACTOR_ID,
        package_name="ontology-ontology",
        fqn_prefix="aware_ontology",
        source_payload={"schema": "aware_ontology.workspace_materialize.v1"},
    )
    assert runtime_response.status == "resolved"
    assert runtime_response.artifact_set is not None
    assert runtime_response.artifact_set.activation_allowed is False
    assert (
        runtime_response.artifact_set.provenance.ontology_config_id
        == ONTOLOGY_CONFIG_ID
    )
    assert (
        runtime_response.artifact_set.provenance.ontology_config_object_instance_graph_commit_id
        == ONTOLOGY_CONFIG_OIGI_COMMIT_ID
    )
    roots = sdk.materialized_semantic_roots(runtime_response.artifact_set)
    assert [root.semantic_projection_name for root in roots] == ["OntologyConfig"]
    config_root = sdk.find_materialized_semantic_root(
        runtime_response.artifact_set,
        semantic_root_kind="OntologyConfig",
    )
    assert config_root is not None
    assert config_root.semantic_projection_hash == "ontology-config.projection"
    assert config_root.semantic_package_id == ONTOLOGY_CONFIG_ID
    runtime_descriptor = runtime_response.artifact_set.runtime_projection_descriptors[0]
    assert runtime_descriptor.projection_name == "Environment"
    assert runtime_descriptor.constructor_function_id == FUNCTION_ID
    runtime_request = api_client.ontology.runtime.last_request
    assert runtime_request is not None
    assert runtime_request.package_name == "ontology-ontology"
    assert runtime_request.source_payload == {
        "schema": "aware_ontology.workspace_materialize.v1"
    }

    subscribe_response = await sdk.subscribe_commits(
        subscriber_id="sdk:test",
        branch_filters=(BRANCH_ID,),
        projection_hash_filters=("projection",),
    )
    assert subscribe_response.accepted is True
    subscribe_request = api_client.ontology.commit.last_subscribe_request
    assert subscribe_request is not None
    assert subscribe_request.subscriber_id == "sdk:test"
    assert subscribe_request.branch_filters == [BRANCH_ID]

    stream = sdk.stream_commits(
        subscriber_id="sdk:test",
        branch_filters=(BRANCH_ID,),
        projection_hash_filters=("projection",),
    )
    events = [event async for event in stream]
    assert events[0].event_id == EVENT_ID
    stream_request = api_client.ontology.commit.last_stream_request
    assert stream_request is not None
    assert stream_request.projection_hash_filters == ["projection"]


@pytest.mark.asyncio
async def test_sdk_rejects_failed_product_response() -> None:
    class _FailingPackageClient(_PackageClient):
        async def ensure_object_config_graph_package(self, request):
            return OntologyObjectConfigGraphPackageEnsureResponse(
                status="failed",
                error="missing graph source",
            )

    api_client = _GeneratedApiClient()
    api_client.ontology.package = _FailingPackageClient()
    sdk = OntologySdkClient(api_client=api_client)

    with pytest.raises(OntologySdkError, match="missing graph source"):
        await sdk.ensure_object_config_graph_package(
            aware_toml_path="modules/ontology/aware.ontology.toml",
        )


def test_sdk_does_not_import_service_protocol_or_internals() -> None:
    package_root = Path(__file__).parents[1] / "aware_ontology_sdk"
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in package_root.rglob("*.py")
    )
    assert "aware_ontology_service_protocol" not in source
    assert "services.ontology" not in source
