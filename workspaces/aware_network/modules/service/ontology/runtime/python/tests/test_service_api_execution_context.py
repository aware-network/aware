from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast
from uuid import uuid4

from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationContext,
    LaneCommitReceiptNotification,
)
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
    service_api_host_context,
)
from aware_service_runtime.api_ingress.environment_commit_context import (
    current_service_environment_commit_reader,
    current_service_environment_commit_receipt_source,
)
from aware_service_runtime.contracts import (
    ServiceGraphGateway,
    ServiceLaneSubscriptionBinding,
    ServiceOperationContext,
)


class _ReceiptSource:
    def stream_commit_receipts(
        self,
        *,
        subscriber_id: str,
        resume_after_commit_id: object = None,
    ) -> AsyncIterator[LaneCommitReceiptNotification]:
        _ = (subscriber_id, resume_after_commit_id)
        raise AssertionError("test only verifies context carrying")


class _CommitReader:
    async def get_object_instance_graph_commit(self, **kwargs: object) -> object:
        _ = kwargs
        raise AssertionError("test only verifies context carrying")


def test_service_api_host_context_scopes_and_resets() -> None:
    assert current_service_api_host_context() is None
    operation_context = ServiceOperationContext(
        actor_id=None,
        branch_id=uuid4(),
        projection_hash="service.api.host.context",
    )
    environment_context = EnvironmentOperationContext(
        actor_id=None,
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=operation_context.branch_id,
        projection_hash=operation_context.projection_hash,
    )
    graph_gateway = cast(ServiceGraphGateway, object())
    lane_subscription = ServiceLaneSubscriptionBinding(
        service_branch_id=uuid4(),
        service_config_api_projection_id=uuid4(),
        api_graph_projection_id=uuid4(),
        object_instance_graph_branch_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:test-subscription",
    )
    receipt_source = _ReceiptSource()
    commit_reader = _CommitReader()

    with service_api_host_context(
        operation_context=operation_context,
        environment_context=environment_context,
        graph_gateway=graph_gateway,
        service_name="aware_attention",
        lane_subscriptions=(lane_subscription,),
        environment_commit_receipt_source=receipt_source,
        environment_commit_reader=commit_reader,
    ) as host_context:
        assert current_service_api_host_context() == host_context
        assert host_context.operation_context == operation_context
        assert host_context.environment_context == environment_context
        assert host_context.graph_gateway is graph_gateway
        assert host_context.service_name == "aware_attention"
        assert host_context.lane_subscriptions == (lane_subscription,)
        assert host_context.environment_commit_receipt_source is receipt_source
        assert host_context.environment_commit_reader is commit_reader
        assert current_service_environment_commit_receipt_source() is receipt_source
        assert current_service_environment_commit_reader() is commit_reader

    assert current_service_api_host_context() is None
    assert current_service_environment_commit_receipt_source() is None
    assert current_service_environment_commit_reader() is None
