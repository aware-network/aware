from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.identity.identity_pattern_enums import IdentityPatternType

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_text import ContentPartText
    from aware_identity_ontology_dto.identity.identity_pattern_evidence import IdentityPatternEvidence


class IdentityPattern(BaseModel):
    # Relationships
    content_part_text: ContentPartText | None = Field(default=None)
    identity_pattern_evidences: list[IdentityPatternEvidence] = Field(default_factory=list)

    # Attributes
    category: str = Field(description="Pattern category: technical, workflow, personal, etc.")
    confidence: float = Field(description="Confidence level from 0.0 to 1.0")
    evidence_count: int = Field(default=0, description="Number of supporting evidence entries")
    last_applied: datetime | None = Field(default=None, description="Last time pattern was applied by an agent")
    pattern_key: str = Field(description="Unique identifier for the pattern within the identity scope")
    pattern_type: IdentityPatternType = Field(description="type of pattern: fact (validated) or hypothesis (emerging)")
    target_confidence: float | None = Field(default=None, description="Target confidence for hypothesis promotion")
