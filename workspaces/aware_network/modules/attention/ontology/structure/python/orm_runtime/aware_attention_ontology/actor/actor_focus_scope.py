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
    from aware_attention_ontology.actor.actor_focus_scope_evidence import ActorFocusScopeEvidence
    from aware_attention_ontology.actor.actor_focus_scope_request import ActorFocusScopeRequest
    from aware_attention_ontology.focus.focus_scope import FocusScope
    from aware_identity_ontology.actor.actor import Actor


class ActorFocusScope(ORMModel):
    # Relationships
    actor: Actor | None = Field(default=None, exclude=True)
    focus_scope: FocusScope | None = Field(default=None, exclude=True)
    requests: list[ActorFocusScopeRequest] = Field(default_factory=list, exclude=True)
    evidences: list[ActorFocusScopeEvidence] = Field(default_factory=list, exclude=True)

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
    actor_id: UUID = Field(description="Foreign key for ActorFocusScope.actor")
    focus_scope_id: UUID = Field(description="Foreign key for ActorFocusScope.focus_scope")

    @classmethod
    async def create(cls, actor_id: UUID, focus_scope_id: UUID) -> ActorFocusScope:
        """Builds a new ActorFocusScope by linking an Identity Actor to FocusScope."""

        payload = {"actor_id": actor_id, "focus_scope_id": focus_scope_id}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActorFocusScope):
            return value
        return ActorFocusScope.validate_invocation_value(value)

    async def add_request(self, focus_scope_request_id: UUID) -> ActorFocusScopeRequest:
        """Links a FocusScopeRequest under this ActorFocusScope."""

        payload = {"focus_scope_request_id": focus_scope_request_id}
        result = await invoke_instance(orm_model=self, function_name="add_request", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.actor.actor_focus_scope_request import ActorFocusScopeRequest

        if isinstance(value, ActorFocusScopeRequest):
            return value
        return ActorFocusScopeRequest.validate_invocation_value(value)

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
    ) -> ActorFocusScopeEvidence:
        """Records one evidence receipt that contributes to this ActorFocusScope weight."""

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
        from aware_attention_ontology.actor.actor_focus_scope_evidence import ActorFocusScopeEvidence

        if isinstance(value, ActorFocusScopeEvidence):
            return value
        return ActorFocusScopeEvidence.validate_invocation_value(value)


class ActorFocusScopeCreateInput(BaseModel):
    actor_id: UUID
    focus_scope_id: UUID


class ActorFocusScopeCreateOutput(BaseModel):
    value: ActorFocusScope


class ActorFocusScopeAddRequestInput(BaseModel):
    focus_scope_request_id: UUID


class ActorFocusScopeAddRequestOutput(BaseModel):
    value: ActorFocusScopeRequest


class ActorFocusScopeRecordEvidenceInput(BaseModel):
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


class ActorFocusScopeRecordEvidenceOutput(BaseModel):
    value: ActorFocusScopeEvidence


FUNCTIONS = {
    "ActorFocusScope": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Builds a new ActorFocusScope by linking an Identity Actor to FocusScope.",
                "is_constructor": True,
            },
            "input": ActorFocusScopeCreateInput,
            "output": ActorFocusScopeCreateOutput,
        },
        "add_request": {
            "canonical": {
                "name": "add_request",
                "description": "Links a FocusScopeRequest under this ActorFocusScope.",
                "is_constructor": False,
            },
            "input": ActorFocusScopeAddRequestInput,
            "output": ActorFocusScopeAddRequestOutput,
        },
        "record_evidence": {
            "canonical": {
                "name": "record_evidence",
                "description": "Records one evidence receipt that contributes to this ActorFocusScope weight.",
                "is_constructor": False,
            },
            "input": ActorFocusScopeRecordEvidenceInput,
            "output": ActorFocusScopeRecordEvidenceOutput,
        },
    },
}

__all__ = [
    "ActorFocusScope",
    "ActorFocusScopeCreateInput",
    "ActorFocusScopeCreateOutput",
    "ActorFocusScopeAddRequestInput",
    "ActorFocusScopeAddRequestOutput",
    "ActorFocusScopeRecordEvidenceInput",
    "ActorFocusScopeRecordEvidenceOutput",
    "FUNCTIONS",
]
