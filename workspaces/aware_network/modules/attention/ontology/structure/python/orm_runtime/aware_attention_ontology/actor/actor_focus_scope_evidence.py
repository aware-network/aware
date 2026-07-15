from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject


class ActorFocusScopeEvidence(ORMModel):
    """Attention-owned evidence row that contributes to an ActorFocusScope weight."""

    # Attributes
    evidence_key: str
    kind: str
    source_type: str | None = Field(default=None)
    source_id: UUID | None = Field(default=None)
    source_key: str | None = Field(default=None)
    weight_delta: float = Field(default=0.0)
    confidence: float | None = Field(default=None)
    observed_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    rationale: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)

    # Foreign Keys
    actor_focus_scope_id: UUID = Field(description="Foreign key for ActorFocusScope.evidences")

    @classmethod
    async def create_via_actor_focus_scope(
        cls,
        actor_focus_scope_id: UUID,
        evidence_key: str,
        kind: str,
        source_type: str | None = None,
        source_id: UUID | None = None,
        source_key: str | None = None,
        weight_delta: float = 0.0,
        confidence: float | None = None,
        observed_at: datetime | None = None,
        expires_at: datetime | None = None,
        rationale: str | None = None,
        metadata: JsonObject | None = None,
    ) -> ActorFocusScopeEvidence:
        """Builds an ActorFocusScopeEvidence receipt under an ActorFocusScope."""

        payload = {
            "actor_focus_scope_id": actor_focus_scope_id,
            "evidence_key": evidence_key,
            "kind": kind,
            "source_type": source_type,
            "source_id": source_id,
            "source_key": source_key,
            "weight_delta": weight_delta,
            "confidence": confidence,
            "observed_at": observed_at,
            "expires_at": expires_at,
            "rationale": rationale,
            "metadata": metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_actor_focus_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorFocusScopeEvidence):
            return value
        return ActorFocusScopeEvidence.validate_invocation_value(value)


class ActorFocusScopeEvidenceCreateViaActorFocusScopeInput(BaseModel):
    actor_focus_scope_id: UUID = Field(description="Foreign key for ActorFocusScope.evidences")
    evidence_key: str
    kind: str
    source_type: str | None = Field(default=None)
    source_id: UUID | None = Field(default=None)
    source_key: str | None = Field(default=None)
    weight_delta: float = Field(default=0.0)
    confidence: float | None = Field(default=None)
    observed_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    rationale: str | None = Field(default=None)
    metadata: JsonObject | None = Field(default=None)


class ActorFocusScopeEvidenceCreateViaActorFocusScopeOutput(BaseModel):
    value: ActorFocusScopeEvidence


FUNCTIONS = {
    "ActorFocusScopeEvidence": {
        "create_via_actor_focus_scope": {
            "canonical": {
                "name": "create_via_actor_focus_scope",
                "description": "Builds an ActorFocusScopeEvidence receipt under an ActorFocusScope.",
                "is_constructor": True,
            },
            "input": ActorFocusScopeEvidenceCreateViaActorFocusScopeInput,
            "output": ActorFocusScopeEvidenceCreateViaActorFocusScopeOutput,
        },
    },
}

__all__ = [
    "ActorFocusScopeEvidence",
    "ActorFocusScopeEvidenceCreateViaActorFocusScopeInput",
    "ActorFocusScopeEvidenceCreateViaActorFocusScopeOutput",
    "FUNCTIONS",
]
