from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import (
    JsonArray,
    JsonObject,
    JsonValue,
)


class TemporalMutationDiagnostic(BaseModel):
    """
    Temporal mutation service-operation payload DTOs.
    These DTOs preserve the useful convergence/session shape for future
    service-to-service infrastructure. They are not an ontology mutation product
    rail, do not sit behind Environment, and intentionally do not augment or
    register with the Environment service-operation discriminator.
    """

    # Attributes
    code: str
    severity: str = Field(default="error")
    summary: str
    detail: str | None = Field(default=None)
    context: JsonObject = Field(default_factory=JsonObject)


class TemporalMutationServiceOperation(BaseModel):
    # Attributes
    service: str = Field(default="temporal_mutation")
    operation: str = Field(
        default="open_session", description="Operation discriminator for temporal mutation messages."
    )
    session_id: UUID | None = Field(
        default=None, description="Session identifier (server-assigned unless provided by client)."
    )
    branch_id: UUID | None = Field(default=None, description="Lane identity (base of the overlay).")
    projection_hash: str | None = Field(default=None)
    base_commit_id: UUID | None = Field(default=None)
    base_graph_hash_post: str | None = Field(default=None)
    revision: int | None = Field(default=None, description="Server-ordered revision for subscriber convergence.")
    expected_revision: int | None = Field(default=None)
    from_revision: int | None = Field(default=None)
    actor_id: UUID | None = Field(
        default=None, description="Provenance (author of the applied op; distinct from subscriber actor)."
    )
    function_id: UUID | None = Field(default=None, description="Temporal apply payload.")
    object_id: UUID | None = Field(default=None)
    args: JsonArray = Field(default_factory=JsonArray)
    kwargs: JsonObject = Field(default_factory=JsonObject)
    status: str | None = Field(default=None, description="Result payload.")
    error_code: str | None = Field(default=None)
    error: str | None = Field(default=None)
    diagnostic: TemporalMutationDiagnostic | None = Field(default=None)
    payload: JsonValue | None = Field(default=None)
    changes: JsonArray = Field(default_factory=JsonArray)
    graph_hash_pre: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None, description="Optional finalized receipt-plane commit evidence.")
    commit_message: str | None = Field(default=None)
