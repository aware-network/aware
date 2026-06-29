"""
Code section render context for surgical code editing.

This module provides the CodeSectionRenderContext dataclass that carries only the core essentials
for rendering operations. All other dependencies are injected into renderers.

Part of the primitive/code layer - language-agnostic and entity-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass

# Code Infrastructure
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section import CodeSection

from aware_code.section.writer_surgical import CodeSectionWriterSurgical


@dataclass
class CodeSectionRenderContext:
    """
    Minimal context object passed to entity renderers.

    Contains only the core essentials for rendering operations:
    - The code object being modified
    - The positioned writer ready to write

    All other dependencies (section_index, builder, schema, layout_strategy, graphs)
    are injected into the renderer instances via dependency injection.

    Part of the primitive/code layer - this is language-agnostic and entity-agnostic.
    """

    # Core rendering essentials
    code: Code
    writer: CodeSectionWriterSurgical

    # Optional context for UPDATE operations
    section: CodeSection | None = None
    insertion_point: int | None = None

    @property
    def is_create_operation(self) -> bool:
        """True if this is a CREATE operation (no existing section)."""
        return self.section is None

    @property
    def is_update_operation(self) -> bool:
        """True if this is an UPDATE operation (has existing section)."""
        return self.section is not None

    @property
    def language(self) -> CodeLanguage | None:
        """The language of the code."""
        return self.code.language

    def positioned_at(self, insertion_point: int) -> CodeSectionRenderContext:
        """
        Create a new context positioned at a specific insertion point.

        Args:
            insertion_point: Byte position for insertion

        Returns:
            New CodeSectionRenderContext with writer positioned at insertion point
        """
        # Position the writer
        self.writer.cursor = insertion_point
        self.writer.at_line_start = True

        # Return a new context with updated insertion point
        return CodeSectionRenderContext(
            code=self.code,
            writer=self.writer,
            section=self.section,
            insertion_point=insertion_point,
        )

    def without_insertion_hint(self) -> CodeSectionRenderContext:
        """Return a clone of this context with the insertion hint cleared."""

        return CodeSectionRenderContext(
            code=self.code,
            writer=self.writer,
            section=self.section,
            insertion_point=None,
        )

    def for_section(self, section: CodeSection) -> CodeSectionRenderContext:
        """
        Create a new context for working with an existing section.

        Args:
            section: The code section to work with

        Returns:
            New CodeSectionRenderContext for UPDATE operations on the section
        """
        if section.code_id != self.code.id:
            raise ValueError(
                f"Code section {section.id} belongs to code_id={section.code_id}, but context code_id={self.code.id}"
            )
        return CodeSectionRenderContext(
            code=self.code,
            writer=self.writer,
            section=section,
            insertion_point=None,
        )
