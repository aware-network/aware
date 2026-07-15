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

# Identity Ontology
from aware_identity_ontology.identity.identity_pattern_enums import IdentityPatternType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_instance

# Types
from aware_types import Vector

if TYPE_CHECKING:
    from aware_content_ontology.part.content_part_text import ContentPartText
    from aware_identity_ontology.identity.identity_pattern_evidence import IdentityPatternEvidence


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

    async def find_similar_across_identities(
        self,
        query_vector: Vector,
        result_count: int,
        min_similarity: float,
        pattern_type: str | None = None,
        min_confidence: float | None = 0.7,
        exclude_identity_id: UUID | None = None,
    ) -> None:
        """
        Finds similar patterns across all identities for cross-identity learning.
        Useful for agents to learn from successful patterns of other identities.
        Parameters: query_vector: Vector to search against
        result_count: Maximum number of results
        min_similarity: Minimum similarity threshold
        exclude_identity_id: Optional identity to exclude from search
        pattern_type: Optional filter by pattern type
        min_confidence: Minimum confidence threshold (default 0.7 for quality)
        Returns: Table with pattern details from multiple identities
        """

        payload = {
            "query_vector": query_vector,
            "result_count": result_count,
            "min_similarity": min_similarity,
            "pattern_type": pattern_type,
            "min_confidence": min_confidence,
            "exclude_identity_id": exclude_identity_id,
        }
        await invoke_instance(orm_model=self, function_name="find_similar_across_identities", payload=payload)
        return None

    async def find_similar_by_content(
        self,
        query_vector: Vector,
        result_count: int,
        min_similarity: float,
        identity_id: UUID,
        pattern_type: str | None = None,
        min_confidence: float | None = 0.7,
    ) -> None:
        """
        Finds similar identity patterns by content similarity search with identity-specific filtering.
        Parameters: identity_id: Identity to search patterns for
        query_vector: Vector to search against pattern content
        result_count: Maximum number of results
        min_similarity: Minimum similarity threshold
        pattern_type: Optional filter by pattern type ('fact' or 'hypothesis')
        min_confidence: Minimum pattern confidence threshold
        Returns: Table with pattern details and similarity scores
        """

        payload = {
            "query_vector": query_vector,
            "result_count": result_count,
            "min_similarity": min_similarity,
            "identity_id": identity_id,
            "pattern_type": pattern_type,
            "min_confidence": min_confidence,
        }
        await invoke_instance(orm_model=self, function_name="find_similar_by_content", payload=payload)
        return None

    async def promote_to_fact(self) -> bool:
        """Promotes a pattern to a fact."""

        payload = {}
        result = await invoke_instance(orm_model=self, function_name="promote_to_fact", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        return value

    async def record_application(self, successful: bool, evidence_description: str | None = None) -> None:
        """Records the application of a pattern."""

        payload = {"successful": successful, "evidence_description": evidence_description}
        await invoke_instance(orm_model=self, function_name="record_application", payload=payload)
        return None


class IdentityPatternFindSimilarAcrossIdentitiesInput(BaseModel):
    query_vector: Vector
    result_count: int
    min_similarity: float
    pattern_type: str | None = Field(default=None)
    min_confidence: float | None = Field(default=0.7)
    exclude_identity_id: UUID | None = Field(default=None)


class IdentityPatternFindSimilarAcrossIdentitiesOutput(BaseModel):
    pass


class IdentityPatternFindSimilarByContentInput(BaseModel):
    query_vector: Vector
    result_count: int
    min_similarity: float
    identity_id: UUID
    pattern_type: str | None = Field(default=None)
    min_confidence: float | None = Field(default=0.7)


class IdentityPatternFindSimilarByContentOutput(BaseModel):
    pass


class IdentityPatternPromoteToFactInput(BaseModel):
    pass


class IdentityPatternPromoteToFactOutput(BaseModel):
    value: bool


class IdentityPatternRecordApplicationInput(BaseModel):
    successful: bool
    evidence_description: str | None = Field(default=None)


class IdentityPatternRecordApplicationOutput(BaseModel):
    pass


FUNCTIONS = {
    "IdentityPattern": {
        "find_similar_across_identities": {
            "canonical": {
                "name": "find_similar_across_identities",
                "description": "Finds similar patterns across all identities for cross-identity learning.\nUseful for agents to learn from successful patterns of other identities.\nParameters: query_vector: Vector to search against\nresult_count: Maximum number of results\nmin_similarity: Minimum similarity threshold\nexclude_identity_id: Optional identity to exclude from search\npattern_type: Optional filter by pattern type\nmin_confidence: Minimum confidence threshold (default 0.7 for quality)\nReturns: Table with pattern details from multiple identities",
                "is_constructor": False,
            },
            "input": IdentityPatternFindSimilarAcrossIdentitiesInput,
            "output": IdentityPatternFindSimilarAcrossIdentitiesOutput,
        },
        "find_similar_by_content": {
            "canonical": {
                "name": "find_similar_by_content",
                "description": "Finds similar identity patterns by content similarity search with identity-specific filtering.\nParameters: identity_id: Identity to search patterns for\nquery_vector: Vector to search against pattern content\nresult_count: Maximum number of results\nmin_similarity: Minimum similarity threshold\npattern_type: Optional filter by pattern type ('fact' or 'hypothesis')\nmin_confidence: Minimum pattern confidence threshold\nReturns: Table with pattern details and similarity scores",
                "is_constructor": False,
            },
            "input": IdentityPatternFindSimilarByContentInput,
            "output": IdentityPatternFindSimilarByContentOutput,
        },
        "promote_to_fact": {
            "canonical": {
                "name": "promote_to_fact",
                "description": "Promotes a pattern to a fact.",
                "is_constructor": False,
            },
            "input": IdentityPatternPromoteToFactInput,
            "output": IdentityPatternPromoteToFactOutput,
        },
        "record_application": {
            "canonical": {
                "name": "record_application",
                "description": "Records the application of a pattern.",
                "is_constructor": False,
            },
            "input": IdentityPatternRecordApplicationInput,
            "output": IdentityPatternRecordApplicationOutput,
        },
    },
}

__all__ = [
    "IdentityPattern",
    "IdentityPatternFindSimilarAcrossIdentitiesInput",
    "IdentityPatternFindSimilarAcrossIdentitiesOutput",
    "IdentityPatternFindSimilarByContentInput",
    "IdentityPatternFindSimilarByContentOutput",
    "IdentityPatternPromoteToFactInput",
    "IdentityPatternPromoteToFactOutput",
    "IdentityPatternRecordApplicationInput",
    "IdentityPatternRecordApplicationOutput",
    "FUNCTIONS",
]
