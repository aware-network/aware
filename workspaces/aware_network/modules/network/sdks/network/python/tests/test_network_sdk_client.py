from __future__ import annotations

from uuid import uuid4

import pytest

from aware_network_sdk import NetworkSdkClient
from aware_network_service_dto.comms.models.network_service import (
    NetworkNodePublicationCoverage,
    NetworkNodePublicationEnvironment,
    NetworkNodePublicationIntent,
    NetworkNodePublicationNode,
    NetworkReconcileNodePublicationResponse,
)


class _PublicationApi:
    def __init__(self) -> None:
        self.requests = []

    async def reconcile_node_publication(self, request):  # noqa: ANN001, ANN201
        self.requests.append(request)
        return NetworkReconcileNodePublicationResponse(
            status="converged",
            publication_digest=request.intent.publication_digest,
            coverage=NetworkNodePublicationCoverage(
                node_registered=True,
                environment_published=True,
                hosted_service_package_ids=[],
                missing_hosted_service_package_ids=[],
                unexpected_hosted_service_package_ids=[],
            ),
            hosted_services=[],
            commit_receipts=[],
        )


class _NetworkApi:
    def __init__(self) -> None:
        self.publication = _PublicationApi()


class _ApiClient:
    def __init__(self) -> None:
        self.network = _NetworkApi()


@pytest.mark.asyncio
async def test_network_sdk_exposes_only_composite_publication_mutation() -> None:
    api_client = _ApiClient()
    client = NetworkSdkClient(api_client=api_client)
    actor_id = uuid4()
    node_id = uuid4()
    environment_id = uuid4()
    intent = NetworkNodePublicationIntent(
        publication_digest="sha256:test",
        node=NetworkNodePublicationNode(
            node_id=node_id,
            public_key="node-key",
            hostname="127.0.0.1",
            port=8911,
        ),
        environment=NetworkNodePublicationEnvironment(
            environment_id=environment_id,
            experience_names=[],
        ),
        hosted_services=[],
    )

    response = await client.reconcile_node_publication(
        intent=intent,
        actor_id=actor_id,
    )

    assert response.status == "converged"
    assert response.publication_digest == intent.publication_digest
    assert api_client.network.publication.requests[0].actor_id == actor_id
    assert api_client.network.publication.requests[0].intent == intent
    assert not hasattr(client, "register_node")
    assert not hasattr(client, "publish_environment")
    assert not hasattr(client, "publish_hosted_service")
