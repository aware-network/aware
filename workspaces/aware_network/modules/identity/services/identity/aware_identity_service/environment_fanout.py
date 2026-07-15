from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol, cast
from uuid import UUID

from aware_environment_sdk import EnvironmentCommitReceiptSource
from aware_identity.actor.commit import (
    ActorCommitMaterializationContext,
    ensure_actor_commit,
)
from aware_identity_service_dto.actor.commit import (
    ActorCommitEnsureReceipt,
)
from aware_identity_service_dto.actor.commit import (
    ActorCommitEnsureRequest,
)
from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)

DEFAULT_IDENTITY_ACTOR_COMMIT_SUBSCRIBER_ID = (
    "aware_identity.actor_commit.environment_fanout"
)


class IdentityActorCommitReceiptAuthority(Protocol):
    async def ensure_actor_commit_from_environment_receipt(
        self,
        receipt: LaneCommitReceiptNotification,
    ) -> ActorCommitEnsureReceipt: ...


class IdentityActorCommitMaterializationContextProvider(Protocol):
    async def actor_commit_context_for_environment_receipt(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
        request: ActorCommitEnsureRequest,
    ) -> ActorCommitMaterializationContext: ...


@dataclass(frozen=True, slots=True)
class IdentityActorCommitEnvironmentAuthority:
    """Identity authority that reacts to Environment lane commit fanout."""

    context_provider: IdentityActorCommitMaterializationContextProvider

    async def ensure_actor_commit_from_environment_receipt(
        self,
        receipt: LaneCommitReceiptNotification,
    ) -> ActorCommitEnsureReceipt:
        request = actor_commit_ensure_request_from_environment_receipt(receipt)
        context = await self.context_provider.actor_commit_context_for_environment_receipt(
            receipt=receipt,
            request=request,
        )
        return await ensure_actor_commit(
            request=request,
            context=context,
        )


@dataclass(frozen=True, slots=True)
class IdentityActorCommitFanoutOutcome:
    commit_id: UUID
    object_instance_graph_commit_id: UUID
    status: str
    actor_id: UUID | None = None
    actor_commit_id: UUID | None = None
    actor_commit_created: bool = False
    reason: str | None = None


@dataclass(slots=True)
class IdentityActorCommitEnvironmentFanoutConsumer:
    """Consumes Environment lane commit fanout and ensures ActorCommit records."""

    source: EnvironmentCommitReceiptSource
    authority: IdentityActorCommitReceiptAuthority
    subscriber_id: str = DEFAULT_IDENTITY_ACTOR_COMMIT_SUBSCRIBER_ID

    async def run(
        self,
        *,
        resume_after_commit_id: UUID | None = None,
        max_receipts: int | None = None,
    ) -> tuple[IdentityActorCommitFanoutOutcome, ...]:
        outcomes: list[IdentityActorCommitFanoutOutcome] = []
        receipt_stream = self.source.stream_commit_receipts(
            subscriber_id=self.subscriber_id,
            resume_after_commit_id=resume_after_commit_id,
        )
        try:
            async for receipt in receipt_stream:
                if receipt.actor_id is None:
                    outcomes.append(
                        IdentityActorCommitFanoutOutcome(
                            commit_id=receipt.commit_id,
                            object_instance_graph_commit_id=(
                                receipt.object_instance_graph_commit_id
                            ),
                            actor_id=None,
                            status="skipped",
                            reason="missing_actor_id",
                        )
                    )
                else:
                    ensured = (
                        await self.authority.ensure_actor_commit_from_environment_receipt(
                            receipt
                        )
                    )
                    outcomes.append(
                        IdentityActorCommitFanoutOutcome(
                            commit_id=receipt.commit_id,
                            object_instance_graph_commit_id=(
                                receipt.object_instance_graph_commit_id
                            ),
                            actor_id=receipt.actor_id,
                            actor_commit_id=ensured.actor_commit.actor_commit_id,
                            actor_commit_created=ensured.actor_commit_created,
                            status="ensured",
                        )
                    )
                if max_receipts is not None and len(outcomes) >= max_receipts:
                    break
        finally:
            aclose = cast(
                Callable[[], Awaitable[None]] | None,
                getattr(receipt_stream, "aclose", None),
            )
            if aclose is not None:
                await aclose()
        return tuple(outcomes)


def actor_commit_ensure_request_from_environment_receipt(
    receipt: LaneCommitReceiptNotification,
) -> ActorCommitEnsureRequest:
    if receipt.actor_id is None:
        raise ValueError("Identity ActorCommit fanout receipt is missing actor_id.")
    object_instance_graph_commit_id = getattr(
        receipt,
        "object_instance_graph_commit_id",
        None,
    )
    if object_instance_graph_commit_id is None:
        raise ValueError(
            "Identity ActorCommit fanout receipt is missing mandatory "
            "object_instance_graph_commit_id."
        )
    return ActorCommitEnsureRequest(
        actor_id=receipt.actor_id,
        domain_branch_id=receipt.branch_id,
        domain_projection_hash=receipt.projection_hash,
        domain_commit_id=receipt.commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        environment_id=receipt.environment_id,
        process_id=receipt.process_id,
        thread_id=receipt.thread_id,
        receipt_actor_id=receipt.actor_id,
        created_at_unix_ms=receipt.created_at_unix_ms,
        operation_label=receipt.operation_label,
        call_target=_call_target_value(receipt.call_target),
        function_id=receipt.function_id,
        object_id=receipt.object_id,
        class_instance_identity_id=receipt.class_instance_identity_id,
        graph_hash_post=receipt.graph_hash_post,
        object_instance_graph_id=receipt.object_instance_graph_id,
        root_object_id=receipt.root_object_id,
        head_version=receipt.head_version,
        source="environment_lane_commit_receipt",
    )


def _call_target_value(value: object) -> str | None:
    if value is None:
        return None
    raw_value = getattr(value, "value", value)
    text = str(raw_value).strip()
    return text or None


__all__ = [
    "DEFAULT_IDENTITY_ACTOR_COMMIT_SUBSCRIBER_ID",
    "IdentityActorCommitEnvironmentAuthority",
    "IdentityActorCommitEnvironmentFanoutConsumer",
    "IdentityActorCommitFanoutOutcome",
    "IdentityActorCommitMaterializationContextProvider",
    "IdentityActorCommitReceiptAuthority",
    "actor_commit_ensure_request_from_environment_receipt",
]
