from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Attention Ontology
from aware_attention_ontology.actor.actor_focus_enums import ActorFocusLevelType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_attention_ontology.actor.actor_focus_evidence import ActorFocusEvidence
    from aware_attention_ontology.actor.actor_focus_request import ActorFocusRequest
    from aware_attention_ontology.focus.focus import Focus
    from aware_identity_ontology.actor.actor import Actor


class ActorFocus(ORMModel):
    """Relationship Subject (Actor) -> Attention (Focus) -> Branch (Object)"""

    # Relationships
    actor: Actor | None = Field(default=None, exclude=True)
    focus: Focus | None = Field(default=None, exclude=True)
    evidences: list[ActorFocusEvidence] = Field(default_factory=list, exclude=True)

    # Attributes
    level: ActorFocusLevelType | None = Field(default=ActorFocusLevelType.medium)
    weight: float = Field(default=0.0)
    weight_algorithm: str | None = Field(default=None)
    weight_computed_at: datetime | None = Field(default=None)
    evidence_count: int = Field(default=0)
    last_evidence_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    last_accessed: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)

    # Foreign Keys
    actor_id: UUID = Field(description="Foreign key for ActorFocus.actor")
    focus_id: UUID = Field(description="Foreign key for ActorFocus.focus")

    @classmethod
    async def create(
        cls,
        actor_id: UUID,
        focus_id: UUID,
        level: ActorFocusLevelType | None = ActorFocusLevelType.medium,
        weight: float = 0.0,
        expires_at: datetime | None = None,
        is_active: bool = True,
    ) -> ActorFocus:
        """Builds a new ActorFocus owned by Attention for one Identity Actor."""

        payload = {
            "actor_id": actor_id,
            "focus_id": focus_id,
            "level": level,
            "weight": weight,
            "expires_at": expires_at,
            "is_active": is_active,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorFocus):
            return value
        return ActorFocus.validate_invocation_value(value)

    async def create_request(
        self,
        sender_id: UUID,
        confidence: float,
        expires_at: datetime,
        rationale: str,
        suggested_level: ActorFocusLevelType = ActorFocusLevelType.medium,
    ) -> ActorFocusRequest:
        """Creates a new ActorFocusRequest."""

        payload = {
            "sender_id": sender_id,
            "confidence": confidence,
            "expires_at": expires_at,
            "rationale": rationale,
            "suggested_level": suggested_level,
        }
        result = await invoke_instance(orm_model=self, function_name="create_request", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.actor.actor_focus_request import ActorFocusRequest

        if isinstance(value, ActorFocusRequest):
            return value
        return ActorFocusRequest.validate_invocation_value(value)

    async def record_evidence(
        self,
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
    ) -> ActorFocusEvidence:
        """Records one evidence receipt that contributes to this ActorFocus weight."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="record_evidence", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.actor.actor_focus_evidence import ActorFocusEvidence

        if isinstance(value, ActorFocusEvidence):
            return value
        return ActorFocusEvidence.validate_invocation_value(value)


class ActorFocusCreateInput(BaseModel):
    actor_id: UUID
    focus_id: UUID
    level: ActorFocusLevelType | None = Field(default=ActorFocusLevelType.medium)
    weight: float = Field(default=0.0)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)


class ActorFocusCreateOutput(BaseModel):
    value: ActorFocus


class ActorFocusCreateRequestInput(BaseModel):
    sender_id: UUID
    confidence: float
    expires_at: datetime
    rationale: str
    suggested_level: ActorFocusLevelType = Field(default=ActorFocusLevelType.medium)


class ActorFocusCreateRequestOutput(BaseModel):
    value: ActorFocusRequest


class ActorFocusRecordEvidenceInput(BaseModel):
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


class ActorFocusRecordEvidenceOutput(BaseModel):
    value: ActorFocusEvidence


FUNCTIONS = {
    "ActorFocus": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Builds a new ActorFocus owned by Attention for one Identity Actor.",
                "is_constructor": True,
            },
            "input": ActorFocusCreateInput,
            "output": ActorFocusCreateOutput,
        },
        "create_request": {
            "canonical": {
                "name": "create_request",
                "description": "Creates a new ActorFocusRequest.",
                "is_constructor": False,
            },
            "input": ActorFocusCreateRequestInput,
            "output": ActorFocusCreateRequestOutput,
        },
        "record_evidence": {
            "canonical": {
                "name": "record_evidence",
                "description": "Records one evidence receipt that contributes to this ActorFocus weight.",
                "is_constructor": False,
            },
            "input": ActorFocusRecordEvidenceInput,
            "output": ActorFocusRecordEvidenceOutput,
        },
    },
}

__all__ = [
    "ActorFocus",
    "ActorFocusCreateInput",
    "ActorFocusCreateOutput",
    "ActorFocusCreateRequestInput",
    "ActorFocusCreateRequestOutput",
    "ActorFocusRecordEvidenceInput",
    "ActorFocusRecordEvidenceOutput",
    "FUNCTIONS",
]
