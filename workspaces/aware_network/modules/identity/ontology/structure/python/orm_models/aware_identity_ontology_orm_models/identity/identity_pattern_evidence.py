from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_text import ContentPartText
    from aware_identity_ontology_orm_models.identity.identity import Identity


class IdentityPatternEvidence(ORMModel):
    # Relationships
    observer: Identity | None = Field(default=None, exclude=True)
    content_part_text: ContentPartText | None = Field(default=None, exclude=True)

    # Attributes
    confidence_impact: float = Field(
        description="Impact on pattern confidence from -1.0 (strong negative) to +1.0 (strong positive)"
    )
    context_summary: str = Field(description="Brief summary of context where evidence was collected")
    evidence_type: str = Field(description="type of evidence: application, observation, test, validation, etc.")
    outcome: str = Field(description="Outcome: successful, failed, mixed, inconclusive, etc.")

    # Foreign Keys
    identity_pattern_id: UUID = Field(description="Foreign key for IdentityPattern.identity_pattern_evidences")
    observer_id: UUID | None = Field(default=None, description="Foreign key for IdentityPatternEvidence.observer")
    content_part_text_id: UUID = Field(description="Foreign key for IdentityPatternEvidence.content_part_text")
