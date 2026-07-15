from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_text import ContentPartText
    from aware_identity_ontology_dto.identity.identity import Identity


class IdentityPatternEvidence(BaseModel):
    # Relationships
    observer: Identity | None = Field(default=None)
    content_part_text: ContentPartText | None = Field(default=None)

    # Attributes
    confidence_impact: float = Field(
        description="Impact on pattern confidence from -1.0 (strong negative) to +1.0 (strong positive)"
    )
    context_summary: str = Field(description="Brief summary of context where evidence was collected")
    evidence_type: str = Field(description="type of evidence: application, observation, test, validation, etc.")
    outcome: str = Field(description="Outcome: successful, failed, mixed, inconclusive, etc.")
