from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.identity.identity_pattern_enums import IdentityPatternType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_text import ContentPartText
    from aware_identity_ontology_orm_models.identity.identity_pattern_evidence import IdentityPatternEvidence


class IdentityPattern(ORMModel):
    # Relationships
    content_part_text: ContentPartText | None = Field(default=None, exclude=True)
    identity_pattern_evidences: list[IdentityPatternEvidence] = Field(default_factory=list, exclude=True)

    # Attributes
    category: str = Field(description="Pattern category: technical, workflow, personal, etc.")
    confidence: float = Field(description="Confidence level from 0.0 to 1.0")
    evidence_count: int = Field(default=0, description="Number of supporting evidence entries")
    last_applied: datetime | None = Field(default=None, description="Last time pattern was applied by an agent")
    pattern_key: str = Field(description="Unique identifier for the pattern within the identity scope")
    pattern_type: IdentityPatternType = Field(description="type of pattern: fact (validated) or hypothesis (emerging)")
    target_confidence: float | None = Field(default=None, description="Target confidence for hypothesis promotion")

    # Foreign Keys
    identity_id: UUID = Field(description="Foreign key for Identity.identity_patterns")
    content_part_text_id: UUID = Field(description="Foreign key for IdentityPattern.content_part_text")
