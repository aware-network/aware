from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class NetworkStream(BaseModel):
    """
    NOTE (Canonical Era, 2026-02):
    `NetworkStream` / `NetworkStreamFrame` are currently **NOT used on the wire**.
    Streaming today uses the universal transport envelope:
    - `NetworkOperation(message_type=stream)` notifications
    - carrying domain-specific service-operation payloads (e.g. Temporal Mutation Sessions).
    Temporal Mutation Sessions (Content collaboration) use server-ordered `revision`
    and `subscribe(from_revision)` for resume, not transport-level `seq/ack/heartbeat`.
    If/when we need transport-level seq/ack semantics shared across *all* streaming
    rails, we can extend `aware_network_service_dto` to include a wire-level `NetworkStreamFrame`.
    Until then, treat these models as reserved/future transport semantics.
    Reference: `docs/architecture/temporal-mutation-sessions.md`.
    """

    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)

    # Attributes
    closed_at: datetime | None = Field(default=None)
