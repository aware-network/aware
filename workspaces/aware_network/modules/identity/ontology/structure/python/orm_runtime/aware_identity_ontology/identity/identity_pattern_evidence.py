from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_instance

# Types
from aware_types import Vector

if TYPE_CHECKING:
    from aware_content_ontology.part.content_part_text import ContentPartText
    from aware_identity_ontology.identity.identity import Identity


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

    async def find_similar_by_content(
        self,
        query_vector: Vector,
        result_count: int,
        min_similarity: float,
        identity_pattern_id: UUID,
        evidence_type: str | None = None,
        outcome: str | None = None,
    ) -> None:
        """
        Finds similar identity pattern evidence by content similarity search.
        Parameters: identity_pattern_id: Pattern to search evidence for
        query_vector: Vector to search against evidence content
        result_count: Maximum number of results
        min_similarity: Minimum similarity threshold
        evidence_type: Optional filter by evidence type
        outcome: Optional filter by outcome
        Returns: Table with evidence details and similarity scores
        """

        payload = {
            "query_vector": query_vector,
            "result_count": result_count,
            "min_similarity": min_similarity,
            "identity_pattern_id": identity_pattern_id,
            "evidence_type": evidence_type,
            "outcome": outcome,
        }
        await invoke_instance(orm_model=self, function_name="find_similar_by_content", payload=payload)
        return None


class IdentityPatternEvidenceFindSimilarByContentInput(BaseModel):
    query_vector: Vector
    result_count: int
    min_similarity: float
    identity_pattern_id: UUID
    evidence_type: str | None = Field(default=None)
    outcome: str | None = Field(default=None)


class IdentityPatternEvidenceFindSimilarByContentOutput(BaseModel):
    pass


FUNCTIONS = {
    "IdentityPatternEvidence": {
        "find_similar_by_content": {
            "canonical": {
                "name": "find_similar_by_content",
                "description": "Finds similar identity pattern evidence by content similarity search.\nParameters: identity_pattern_id: Pattern to search evidence for\nquery_vector: Vector to search against evidence content\nresult_count: Maximum number of results\nmin_similarity: Minimum similarity threshold\nevidence_type: Optional filter by evidence type\noutcome: Optional filter by outcome\nReturns: Table with evidence details and similarity scores",
                "is_constructor": False,
            },
            "input": IdentityPatternEvidenceFindSimilarByContentInput,
            "output": IdentityPatternEvidenceFindSimilarByContentOutput,
        },
    },
}

__all__ = [
    "IdentityPatternEvidence",
    "IdentityPatternEvidenceFindSimilarByContentInput",
    "IdentityPatternEvidenceFindSimilarByContentOutput",
    "FUNCTIONS",
]
