"""
SQL Object Config Relationship Metadata handling.

This module provides classes for extracting and managing relationship metadata
from SQL column comments, separating relationship configuration from other metadata.
"""

from __future__ import annotations

import re
from typing import ClassVar, Self

from pydantic import BaseModel

# Use existing enums from aware_meta
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)

# Relationship metadata constants
FORWARD_COMMENT = "forward"
REVERSE_COMMENT = "reverse"
LAZY_LOADING = "lazy"
EAGER_LOADING = "eager"
SERIALISABLE_COMMENT = "serialisable"


class RelationshipSideConfig(BaseModel):
    """Configuration for one side of a relationship."""

    direction: ClassConfigRelationshipDirection
    loading_strategy: ClassConfigRelationshipSideLoadingStrategy = ClassConfigRelationshipSideLoadingStrategy.eager
    is_serialisable: bool = True


class RelationshipConfig(BaseModel):
    """Complete relationship configuration parsed from comment."""

    forward_side: RelationshipSideConfig | None = None
    reverse_side: RelationshipSideConfig | None = None

    def has_configuration(self) -> bool:
        """Check if any relationship configuration is present."""
        return self.forward_side is not None or self.reverse_side is not None


class SQLObjectConfigRelationshipMetadata(BaseModel):
    """
    Extracts and manages relationship metadata from SQL column comments.

    This class is responsible for:
    1. Detecting relationship metadata in column comments
    2. Parsing relationship configurations
    3. Returning cleaned comments with relationship metadata removed
    """

    relationship_config: RelationshipConfig | None = None
    original_relationship_string: str | None = None

    # Pattern to detect relationship metadata - improved to handle more cases
    RELATIONSHIP_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b({FORWARD_COMMENT}|{REVERSE_COMMENT})\b.*?(?:;|$)", re.IGNORECASE | re.DOTALL
    )

    # Enhanced pattern to capture standalone relationship parts better
    RELATIONSHIP_PART_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b({FORWARD_COMMENT}|{REVERSE_COMMENT})\b[^;]*", re.IGNORECASE
    )

    # Pattern to detect relationship tag in structured format
    RELATIONSHIP_TAG_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"relationship:\s*([^;]+)(?:;|$)", re.IGNORECASE
    )

    # Regular expressions for relationship parsing
    CREATE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"create[:=](read|write|admin)\b", re.IGNORECASE)

    @classmethod
    def from_raw_comment(cls, comment: str) -> tuple[Self, str]:
        """
        Extract relationship metadata from raw comment and return cleaned comment.

        Args:
            comment: Raw SQL column comment

        Returns:
            Tuple of (relationship_metadata, cleaned_comment)
            - relationship_metadata: Parsed relationship configuration
            - cleaned_comment: Comment with relationship metadata removed
        """
        if not comment:
            return cls(), comment

        normalized_comment = comment.strip()
        relationship_metadata = cls()
        cleaned_comment = normalized_comment

        # Check for structured format with relationship tag
        relationship_tag_match = cls.RELATIONSHIP_TAG_PATTERN.search(normalized_comment)
        if relationship_tag_match:
            # Extract relationship metadata from tag
            relationship_value = relationship_tag_match.group(1).strip()
            relationship_metadata.relationship_config = cls._parse_relationship_metadata(relationship_value)
            relationship_metadata.original_relationship_string = relationship_value

            # Remove the relationship tag from the comment
            cleaned_comment = cls.RELATIONSHIP_TAG_PATTERN.sub("", cleaned_comment).strip()

            # Clean up any trailing semicolons or extra whitespace
            cleaned_comment = re.sub(r";\s*$", "", cleaned_comment).strip()
        else:
            # Check for inline relationship metadata (not in tags)
            relationship_matches = list(cls.RELATIONSHIP_PATTERN.finditer(normalized_comment))
            if not relationship_matches:
                # Try alternative pattern for standalone relationship parts
                relationship_matches = list(cls.RELATIONSHIP_PART_PATTERN.finditer(normalized_comment))

            if relationship_matches:
                # For inline relationship metadata, preserve the original string as-is
                # Extract the span that covers all relationship parts
                start_pos = min(match.start() for match in relationship_matches)
                end_pos = max(match.end() for match in relationship_matches)

                # Store original relationship string (preserve original formatting)
                original_relationship = normalized_comment[start_pos:end_pos].strip()
                # Remove trailing semicolon if present
                original_relationship = re.sub(r";\s*$", "", original_relationship).strip()
                relationship_metadata.original_relationship_string = original_relationship
                relationship_metadata.relationship_config = cls._parse_relationship_metadata(original_relationship)

                # Remove relationship parts from the comment
                cleaned_comment = normalized_comment[:start_pos] + normalized_comment[end_pos:]

                # Clean up the remaining comment
                cleaned_comment = re.sub(r";\s*;", ";", cleaned_comment)  # Remove double semicolons
                cleaned_comment = re.sub(r"^;\s*|;\s*$", "", cleaned_comment)  # Remove leading/trailing semicolons
                cleaned_comment = cleaned_comment.strip()
            else:
                # Check if the entire comment looks like relationship metadata
                if cls._looks_like_relationship_metadata(normalized_comment):
                    # Treat entire comment as relationship metadata
                    relationship_metadata.relationship_config = cls._parse_relationship_metadata(normalized_comment)
                    relationship_metadata.original_relationship_string = normalized_comment
                    cleaned_comment = ""  # No remaining comment

        return relationship_metadata, cleaned_comment

    @classmethod
    def _parse_relationship_metadata(cls, relationship_metadata: str) -> RelationshipConfig:
        """
        Parse relationship metadata string into RelationshipConfig.

        Args:
            relationship_metadata: The relationship metadata string to parse

        Returns:
            RelationshipConfig with parsed relationship configuration
        """
        if not relationship_metadata:
            return RelationshipConfig()

        relationship_config = RelationshipConfig()

        # Convert to lowercase for parsing
        comment_lower = relationship_metadata.lower()

        # Handle standalone relationship keywords (no direction specified)
        standalone_keywords = [
            LAZY_LOADING,
            EAGER_LOADING,
        ]
        if comment_lower.strip() in standalone_keywords:
            # For standalone keywords, create a minimal config
            # This allows the metadata to be stored but indicates it's not a full relationship config
            return RelationshipConfig()  # Empty config but will be stored as original string

        # Check if comment contains commas but not semicolons
        if "," in comment_lower and ";" not in comment_lower:
            # Split by commas (legacy support)
            sections = [s.strip() for s in comment_lower.split(",")]
        else:
            # Split by semicolons (preferred method)
            sections = [s.strip() for s in comment_lower.split(";")]

        # Parse each section
        for section in sections:
            if not section:
                continue

            # Handle both colon-separated and space-separated formats
            # Colon format: "forward:ownership:interface:lazy"
            # Legacy format: "forward ownership interface:lazy"

            # Check if this section starts with a known direction word followed by space
            # This indicates legacy space-separated format
            starts_with_direction_and_space = section.startswith(f"{FORWARD_COMMENT} ") or section.startswith(
                f"{REVERSE_COMMENT} "
            )

            if starts_with_direction_and_space:
                # Handle legacy space-separated format
                space_parts = section.split()
                parts: list[str] = []
                for part in space_parts:
                    if ":" in part:
                        # Split parts like "interface:lazy" but keep them connected
                        parts.extend(part.split(":"))
                    else:
                        parts.append(part)
            elif ":" in section:
                # Split by colon for the structured format (only if not legacy)
                parts = [p.strip() for p in section.split(":")]
            else:
                # Single word or phrase - treat as parts
                parts = section.split()

            if not parts:
                continue

            # First part is direction
            direction_str = parts[0]

            # Determine direction
            if direction_str == FORWARD_COMMENT:
                direction = ClassConfigRelationshipDirection.forward
            elif direction_str == REVERSE_COMMENT:
                direction = ClassConfigRelationshipDirection.reverse
            else:
                continue

            # Create side configuration
            side_config = RelationshipSideConfig(direction=direction)

            # Process parts to configure the side
            cls._configure_relationship_side(side_config, parts)

            # Store the side configuration
            if direction == ClassConfigRelationshipDirection.forward:
                relationship_config.forward_side = side_config
            else:
                relationship_config.reverse_side = side_config

        return relationship_config

    @classmethod
    def _configure_relationship_side(cls, side_config: RelationshipSideConfig, parts: list[str]) -> None:
        """
        Configure a relationship side based on parsed parts.

        Args:
            side_config: The side configuration to update
            parts: List of parsed parts from the comment section
        """
        # Process parts
        if len(parts) == 2 and parts[1] == LAZY_LOADING:
            # Special case: {direction}:lazy means lazy loading for all contexts
            side_config.loading_strategy = ClassConfigRelationshipSideLoadingStrategy.lazy
            # Default serialisable = False for lazy loading
            side_config.is_serialisable = False
        elif len(parts) == 3 and parts[1] == LAZY_LOADING and parts[2] == SERIALISABLE_COMMENT:
            # Special case: {direction}:lazy:serialisable
            side_config.loading_strategy = ClassConfigRelationshipSideLoadingStrategy.lazy
            # Explicit serialisable = True for lazy:serialisable
            side_config.is_serialisable = True
        else:
            # Process additional parts
            for i, part in enumerate(parts[1:], 1):
                if part == LAZY_LOADING:
                    if i == 1:
                        side_config.loading_strategy = ClassConfigRelationshipSideLoadingStrategy.lazy
                        # Default serialisable = False for lazy loading
                        side_config.is_serialisable = False

                        # Check if next part is serialisable
                        if i < len(parts) - 1 and parts[i + 1] == SERIALISABLE_COMMENT:
                            side_config.is_serialisable = True
                elif part == EAGER_LOADING:
                    # If we have standalone 'eager' not immediately after a context,
                    # assume it applies to all contexts
                    if i == 1:
                        side_config.loading_strategy = ClassConfigRelationshipSideLoadingStrategy.eager
                        # Eager is always serialisable = True
                        side_config.is_serialisable = True

    @classmethod
    def _looks_like_relationship_metadata(cls, comment: str) -> bool:
        """
        Check if a comment looks like relationship metadata.

        Args:
            comment: The comment to check

        Returns:
            True if it looks like relationship metadata, False otherwise
        """
        comment_lower = comment.lower().strip()

        # Check for relationship keywords
        relationship_keywords = [
            FORWARD_COMMENT,
            REVERSE_COMMENT,
            LAZY_LOADING,
            EAGER_LOADING,
            SERIALISABLE_COMMENT,
        ]

        # Check if comment starts with or contains relationship keywords
        if any(keyword in comment_lower for keyword in relationship_keywords):
            return True

        # Check for relationship patterns like "forward:lazy" or "reverse:lazy"
        if re.search(rf"\b({FORWARD_COMMENT}|{REVERSE_COMMENT})\b", comment_lower):
            return True

        # Check for common relationship patterns
        if re.search(r"\b(forward|reverse)[:;\s]", comment_lower):
            return True

        # Check if the entire comment is just a single relationship keyword
        if comment_lower in relationship_keywords:
            return True

        return False

    def has_relationship_metadata(self) -> bool:
        """
        Check if this instance has relationship metadata.

        Returns:
            True if relationship metadata is present, False otherwise
        """
        # Check if we have either a parsed relationship config OR an original relationship string
        # This handles cases like standalone keywords ("lazy") that are relationship metadata
        # but don't parse into a full relationship configuration
        return (self.relationship_config is not None and self.relationship_config.has_configuration()) or bool(
            self.original_relationship_string
        )

    def get_relationship_config(self) -> RelationshipConfig | None:
        """
        Get the parsed relationship configuration.

        Returns:
            RelationshipConfig object or None if no relationship configuration
        """
        return self.relationship_config if self.has_relationship_metadata() else None

    def get_relationship_metadata_string(self) -> str | None:
        """
        Get the relationship metadata as a string for backward compatibility.

        Returns:
            Original relationship metadata string or None if no relationship metadata
        """
        if not self.has_relationship_metadata():
            return None

        return self.original_relationship_string
