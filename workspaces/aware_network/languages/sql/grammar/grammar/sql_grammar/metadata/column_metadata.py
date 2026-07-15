"""
Column-level metadata handling for SQL attributes.

This module provides classes for managing metadata at the column level,
including descriptions and relationship configurations.
"""

from __future__ import annotations

from typing import Self
from typing_extensions import override

from aware_code.section.metadata import CodeSectionMetadata

# Import the normalizer
from aware_utils.description_normalizer import DescriptionNormalizer

# Import relationship metadata handler
from sql_grammar.metadata.object_config_relationship_metadata import (
    RelationshipConfig,
    SQLObjectConfigRelationshipMetadata,
)


class SQLColumnMetadata(CodeSectionMetadata):
    """
    Metadata for database columns/attributes.

    This class holds column-level information extracted from SQL comments:

    - description: Clean human-readable description of the column
    - relationship_metadata: Parsed relationship configuration object (if any)
    """

    description: str | None = None
    relationship_metadata: SQLObjectConfigRelationshipMetadata | None = None

    def update(self, other: SQLColumnMetadata) -> None:
        """
        Update this metadata with values from another metadata instance.

        Args:
            other: The metadata to update from
        """
        # Only update description if we don't already have one
        if other.description and not self.description:
            self.description = other.description

        if other.relationship_metadata:
            self.relationship_metadata = other.relationship_metadata

    @override
    @classmethod
    def from_raw_comment(cls, raw_comment: str) -> Self:
        """
        Parse column-level metadata from a SQL comment using two-stage processing.

        Stage 1: Extract relationship metadata and get cleaned comment
        Stage 2: Treat remaining cleaned comment as description

        Args:
            raw_comment: The raw column comment to parse

        Returns:
            SQLColumnMetadata instance with extracted metadata
        """
        if not raw_comment:
            return cls()

        # Stage 1: Extract relationship metadata
        relationship_metadata, cleaned_comment = SQLObjectConfigRelationshipMetadata.from_raw_comment(raw_comment)

        # Stage 2: Treat remaining cleaned comment as description
        column_metadata = cls()

        # Set relationship metadata if found
        if relationship_metadata.has_relationship_metadata():
            column_metadata.relationship_metadata = relationship_metadata

        # Set description from cleaned comment
        if cleaned_comment.strip():
            column_metadata.description = DescriptionNormalizer.normalize_description(cleaned_comment.strip())

        return column_metadata

    def get_clean_description(self) -> str | None:
        """
        Get the clean description without any metadata directives.

        Returns:
            Clean description string or None if no description
        """
        return self.description

    def get_relationship_metadata(self) -> str | None:
        """
        Get the raw relationship metadata string for backward compatibility.

        Returns:
            Raw relationship metadata string or None if no relationship metadata
        """
        if self.relationship_metadata and self.relationship_metadata.has_relationship_metadata():
            return self.relationship_metadata.get_relationship_metadata_string()
        return None

    def get_relationship_config(self) -> RelationshipConfig | None:
        """
        Get the parsed relationship configuration.

        Returns:
            RelationshipConfig object or None if no relationship configuration
        """
        if self.relationship_metadata:
            return self.relationship_metadata.get_relationship_config()
        return None

    def has_relationship_metadata(self) -> bool:
        """
        Check if this column has relationship metadata.

        Returns:
            True if relationship metadata is present, False otherwise
        """
        return self.relationship_metadata is not None and self.relationship_metadata.has_relationship_metadata()
