from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest

from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_service_runtime.api_ingress.environment_commit_context import (
    current_service_environment_commit_receipt_source,
    require_service_environment_commit_receipt_source,
)
from aware_service_runtime.api_ingress.host_context import service_api_host_context
from aware_service_runtime.contracts import ServiceOperationContext


class _ReceiptSource:
    def stream_commit_receipts(
        self,
        *,
        subscriber_id: str,
        resume_after_commit_id: UUID | None = None,
    ) -> AsyncIterator[LaneCommitReceiptNotification]:
        _ = (subscriber_id, resume_after_commit_id)
        raise AssertionError("test only verifies context lookup")


def test_service_environment_commit_receipt_source_context_lookup() -> None:
    receipt_source = _ReceiptSource()

    assert current_service_environment_commit_receipt_source() is None
    with pytest.raises(RuntimeError, match="Environment fanout configured"):
        require_service_environment_commit_receipt_source()

    with service_api_host_context(
        operation_context=ServiceOperationContext(
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="service.environment.commit.context",
        ),
        environment_commit_receipt_source=receipt_source,
    ):
        assert current_service_environment_commit_receipt_source() is receipt_source
        assert require_service_environment_commit_receipt_source() is receipt_source

    assert current_service_environment_commit_receipt_source() is None
