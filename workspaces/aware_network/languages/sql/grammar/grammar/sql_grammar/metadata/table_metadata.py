"""
Table-level metadata handling for ORM models.

This module provides classes for managing metadata at the table level,
including ownership configurations and documentation.
"""

from __future__ import annotations

import re
from typing import ClassVar, Self, cast
from typing_extensions import override

from aware_code.section.metadata import CodeSectionMetadata

# Import the normalizer
from aware_utils.description_normalizer import DescriptionNormalizer

# Table metadata comments
DESCRIPTION_TAG = "description"
ICON_TAG = "icon"


class SQLTableMetadata(CodeSectionMetadata):
    """
    Metadata for database tables.

    This class holds table-level information extracted from SQL comments:

    - icon: Optional visual representation
    - branchable: Whether this table is branchable
    - Additional metadata that may be added in the future
    """

    description: str | None = None
    icon: str | None = None

    # Table metadata patterns
    TABLE_TAG_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"([a-z_]+)(?::([^;]+))?;?", re.IGNORECASE)

    def update(self, other: SQLTableMetadata) -> None:
        """
        Update this metadata with values from another metadata instance.

        Args:
            other: The metadata to update from
        """
        if other.description:
            self.description = other.description

        if other.icon:
            self.icon = other.icon

    @override
    @classmethod
    def from_raw_comment(cls, raw_comment: str) -> Self:
        """
        Parse table-level metadata from a SQL comment.

        Args:
            raw_comment: The table comment to parse

        Returns:
            SQLTableMetadata instance with extracted metadata
        """
        # Create base SQLTableMetadata
        metadata = cls(description=None, icon=None)

        if not raw_comment:
            return metadata

        # Normalize comment for parsing
        normalized_comment = re.sub(r"\s+", " ", raw_comment)

        # Use regex to find all table tags
        matches = cast(list[tuple[str, str]], cls.TABLE_TAG_PATTERN.findall(normalized_comment))
        for match in matches:
            key = match[0].strip() if match[0] else ""
            value = match[1].strip() if len(match) > 1 and match[1] else None

            if key == ICON_TAG and value:
                metadata.icon = value
            elif key == DESCRIPTION_TAG and value:
                # Normalize the description using the common normalizer
                metadata.description = DescriptionNormalizer.normalize_description(value)
            # Handle any other metadata tags here

        return metadata
