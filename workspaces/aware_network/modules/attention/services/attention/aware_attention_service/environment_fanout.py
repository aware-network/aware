from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, cast
from uuid import UUID

from aware_attention_service_dto.attention.section.models import (
    AttentionSectionFocusTarget,
    AttentionSectionSnapshot,
)
from aware_attention_service_dto.attention.section.service_operation import (
    ActivateAttentionSectionObservableRequest,
    AttentionSectionActivationScope,
)
from aware_environment_sdk import EnvironmentCommitReceiptSource
from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)

DEFAULT_ATTENTION_ENVIRONMENT_FANOUT_SUBSCRIBER_ID = (
    "aware_attention.environment_fanout.focus_attach"
)


class AttentionSectionActivationAuthority(Protocol):
    async def activate_section_observable(
        self,
        request: ActivateAttentionSectionObservableRequest,
    ) -> AttentionSectionSnapshot: ...

    async def ensure_focus_scope_commit(
        self,
        *,
        focus_scope_id: UUID,
        focus_id: UUID,
        object_instance_graph_commit_id: UUID,
    ) -> None: ...


class AttentionEnvironmentFocusResolver(Protocol):
    async def resolve_focus_routes(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
    ) -> Sequence["AttentionEnvironmentFocusRoute"]: ...


@dataclass(frozen=True, slots=True)
class AttentionEnvironmentFocusRoute:
    """Committed Attention route that is already watching an Environment target."""

    focus_scope_id: UUID
    focus_id: UUID
    section_key: str | None = None
    observable_id: UUID | None = None
    focus_target: AttentionSectionFocusTarget | None = None


@dataclass(frozen=True, slots=True)
class AttentionEnvironmentFocusBinding:
    """Section/observable routing for Environment receipt driven focus attach."""

    section_key: str
    observable_id: UUID
    focus_scope_id: UUID | None = None
    section_title: str | None = None
    section_description: str | None = None
    focus_scope_title: str | None = None
    focus_scope_description: str | None = None
    target_type: str = "oigb"
    description: str | None = None
    rationale: str = "environment_lane_commit_receipt"

    def __post_init__(self) -> None:
        section_key = self.section_key.strip()
        if not section_key:
            raise ValueError(
                "Attention Environment focus binding requires section_key."
            )
        target_type = self.target_type.strip()
        if not target_type:
            raise ValueError(
                "Attention Environment focus binding requires target_type."
            )
        rationale = self.rationale.strip()
        if not rationale:
            raise ValueError("Attention Environment focus binding requires rationale.")
        object.__setattr__(self, "section_key", section_key)
        object.__setattr__(self, "target_type", target_type)
        object.__setattr__(self, "rationale", rationale)


@dataclass(frozen=True, slots=True)
class AttentionEnvironmentFocusAttachOutcome:
    commit_id: UUID
    status: str
    section_key: str | None = None
    observable_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    focus_target: AttentionSectionFocusTarget | None = None
    object_instance_graph_commit_id: UUID | None = None
    provenance_status: str | None = None
    provenance_reason: str | None = None
    reason: str | None = None


@dataclass(slots=True)
class AttentionEnvironmentFanoutFocusConsumer:
    """Consumes Environment lane receipts and delegates focus attach to Attention."""

    source: EnvironmentCommitReceiptSource
    authority: AttentionSectionActivationAuthority
    binding: AttentionEnvironmentFocusBinding | None = None
    resolver: AttentionEnvironmentFocusResolver | None = None
    subscriber_id: str = DEFAULT_ATTENTION_ENVIRONMENT_FANOUT_SUBSCRIBER_ID

    def __post_init__(self) -> None:
        if self.binding is None and self.resolver is None:
            raise ValueError(
                "Attention Environment fanout requires either a static focus "
                "binding or a committed focus resolver."
            )

    async def run(
        self,
        *,
        resume_after_commit_id: UUID | None = None,
        max_receipts: int | None = None,
    ) -> tuple[AttentionEnvironmentFocusAttachOutcome, ...]:
        outcomes: list[AttentionEnvironmentFocusAttachOutcome] = []
        receipt_stream = self.source.stream_commit_receipts(
            subscriber_id=self.subscriber_id,
            resume_after_commit_id=resume_after_commit_id,
        )
        try:
            async for receipt in receipt_stream:
                if self.binding is not None:
                    request, focus_target, reason = (
                        activation_request_from_environment_receipt(
                            receipt=receipt,
                            binding=self.binding,
                        )
                    )
                    if request is None:
                        outcomes.append(
                            AttentionEnvironmentFocusAttachOutcome(
                                commit_id=receipt.commit_id,
                                status="skipped",
                                reason=reason,
                            )
                        )
                    else:
                        snapshot = await self.authority.activate_section_observable(
                            request
                        )
                        provenance_status, provenance_reason = (
                            await self._ensure_focus_scope_commit_from_receipt(
                                snapshot=snapshot,
                                receipt=receipt,
                            )
                        )
                        outcomes.append(
                            AttentionEnvironmentFocusAttachOutcome(
                                commit_id=receipt.commit_id,
                                status="activated",
                                section_key=request.section_key,
                                observable_id=request.observable_id,
                                focus_scope_id=snapshot.focus_scope_id,
                                focus_id=snapshot.focus_id,
                                focus_target=focus_target,
                                object_instance_graph_commit_id=(
                                    receipt.object_instance_graph_commit_id
                                ),
                                provenance_status=provenance_status,
                                provenance_reason=provenance_reason,
                            ),
                        )
                else:
                    outcomes.extend(
                        await self._pin_resolved_focus_routes_from_receipt(
                            receipt=receipt,
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

    async def _ensure_focus_scope_commit_from_receipt(
        self,
        *,
        snapshot: AttentionSectionSnapshot,
        receipt: LaneCommitReceiptNotification,
    ) -> tuple[str, str | None]:
        object_instance_graph_commit_id = receipt.object_instance_graph_commit_id
        if object_instance_graph_commit_id is None:
            return "skipped", "missing_object_instance_graph_commit_id"
        focus_scope_id = snapshot.focus_scope_id
        if focus_scope_id is None:
            return "skipped", "missing_focus_scope_id"
        focus_id = snapshot.focus_id
        if focus_id is None:
            return "skipped", "missing_focus_id"
        await self.authority.ensure_focus_scope_commit(
            focus_scope_id=focus_scope_id,
            focus_id=focus_id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
        return "pinned", None

    async def _pin_resolved_focus_routes_from_receipt(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
    ) -> tuple[AttentionEnvironmentFocusAttachOutcome, ...]:
        object_instance_graph_commit_id = receipt.object_instance_graph_commit_id
        if object_instance_graph_commit_id is None:
            return (
                AttentionEnvironmentFocusAttachOutcome(
                    commit_id=receipt.commit_id,
                    status="skipped",
                    object_instance_graph_commit_id=None,
                    provenance_status="skipped",
                    provenance_reason="missing_object_instance_graph_commit_id",
                ),
            )
        resolver = self.resolver
        if resolver is None:
            return (
                AttentionEnvironmentFocusAttachOutcome(
                    commit_id=receipt.commit_id,
                    status="skipped",
                    object_instance_graph_commit_id=object_instance_graph_commit_id,
                    reason="missing_committed_focus_resolver",
                ),
            )
        routes = tuple(await resolver.resolve_focus_routes(receipt=receipt))
        if not routes:
            return (
                AttentionEnvironmentFocusAttachOutcome(
                    commit_id=receipt.commit_id,
                    status="skipped",
                    object_instance_graph_commit_id=object_instance_graph_commit_id,
                    reason="no_matching_active_focus",
                ),
            )
        outcomes: list[AttentionEnvironmentFocusAttachOutcome] = []
        for route in routes:
            await self.authority.ensure_focus_scope_commit(
                focus_scope_id=route.focus_scope_id,
                focus_id=route.focus_id,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
            )
            outcomes.append(
                AttentionEnvironmentFocusAttachOutcome(
                    commit_id=receipt.commit_id,
                    status="pinned",
                    section_key=route.section_key,
                    observable_id=route.observable_id,
                    focus_scope_id=route.focus_scope_id,
                    focus_id=route.focus_id,
                    focus_target=route.focus_target,
                    object_instance_graph_commit_id=object_instance_graph_commit_id,
                    provenance_status="pinned",
                    provenance_reason=None,
                )
            )
        return tuple(outcomes)


def activation_request_from_environment_receipt(
    *,
    receipt: LaneCommitReceiptNotification,
    binding: AttentionEnvironmentFocusBinding,
) -> tuple[
    ActivateAttentionSectionObservableRequest | None,
    AttentionSectionFocusTarget | None,
    str | None,
]:
    object_projection_graph_identity_id = receipt.object_projection_graph_identity_id
    if object_projection_graph_identity_id is None:
        return None, None, "missing_object_projection_graph_identity_id"
    object_instance_graph_branch_id = receipt.object_instance_graph_branch_id
    if object_instance_graph_branch_id is None:
        return None, None, "missing_object_instance_graph_branch_id"

    focus_target = AttentionSectionFocusTarget(
        kind="materialized",
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        projection_hash=(receipt.projection_hash or "").strip() or None,
        target_type=binding.target_type,
        target_id=object_instance_graph_branch_id,
        description=(
            binding.description
            or f"Environment lane commit receipt {receipt.commit_id}"
        ),
    )
    return (
        ActivateAttentionSectionObservableRequest(
            section_key=binding.section_key,
            observable_id=binding.observable_id,
            activation_scope=AttentionSectionActivationScope(
                focus_scope_id=binding.focus_scope_id,
                branch_id=receipt.branch_id,
                state_projection_hash=(receipt.projection_hash or "").strip() or None,
                focus_target=focus_target,
            ),
            rationale=binding.rationale,
            section_title=binding.section_title,
            section_description=binding.section_description,
            focus_scope_title=binding.focus_scope_title,
            focus_scope_description=binding.focus_scope_description,
        ),
        focus_target,
        None,
    )


__all__ = [
    "DEFAULT_ATTENTION_ENVIRONMENT_FANOUT_SUBSCRIBER_ID",
    "AttentionEnvironmentFanoutFocusConsumer",
    "AttentionEnvironmentFocusAttachOutcome",
    "AttentionEnvironmentFocusBinding",
    "AttentionEnvironmentFocusResolver",
    "AttentionEnvironmentFocusRoute",
    "AttentionSectionActivationAuthority",
    "activation_request_from_environment_receipt",
]
