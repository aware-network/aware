"""Metadata for code sections."""

from __future__ import annotations

from pydantic import BaseModel


class CodeSectionMetadata(BaseModel):
    """
    Base metadata class for code sections.

    Contains the description plus any language-specific metadata fields.
    """

    description: str | None = None
    requires_normalization: bool = True  # Whether additional normalization should be applied

    def get_description(self) -> str | None:
        """Get the description of the code section."""
        return self.description

    @classmethod
    def from_raw_comment(cls, raw_comment: str) -> CodeSectionMetadata:
        """
        Create a CodeSectionMetadata from a raw comment.
        """
        return cls(description=raw_comment)
