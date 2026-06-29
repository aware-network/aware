"""Writer for constructing CodeSection instances from meta representations."""

from __future__ import annotations
from types import TracebackType
from typing import Literal, final
from uuid import UUID

from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Aware Content
from aware_content.builder import get_segment_text

# Code Runtime
from aware_code.section.builder import build_section_from_bytes, make_identity_hash
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.spec import SectionSpec, AssembleFn
from aware_code.types.json import Json


@final
class CodeSectionScope:
    """
    Context manager for a code section scope.

    Tracks segments and allows building a code section by writing tokens.
    """

    def __init__(
        self,
        writer: CodeSectionWriter,
        spec: SectionSpec,
        qualname: str,
        parent_id: UUID | None = None,
        reference: str | None = None,
        indent_level: int = 0,
        metadata: Json | None = None,
    ):
        """
        Initialize a section scope.

        Args:
            writer: The parent section writer
            spec: SectionSpec containing the section type and assembly function
            qualname: Fully qualified name for the section
            parent_id: Optional ID of parent section
            reference: Optional reference string for lookup
            indent_level: Current indentation level
            metadata: Optional metadata dict for surgical editing support
        """
        self.writer = writer
        self.section_type = spec.section_type
        self.qualname = qualname
        self.parent_id = parent_id
        self.reference = reference
        self.indent_level = indent_level
        self._assemble: AssembleFn = spec.assemble
        self.metadata: Json = metadata if metadata is not None else Json()
        self.start_pos = self.writer.cursor
        self.named_segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]] = {}
        self.nested_code_sections: dict[str, CodeSection | list[CodeSection]] = {}
        self._segment_parts: list[ContentPartTextSegment] = []
        self._parent_scope: CodeSectionScope | None = None

        # Create the section early so its ID is available
        self.code_section = self._create_temp_section()

    def _create_temp_section(self) -> CodeSection:
        """
        Create a temporary CodeSection with minimal content.
        The section will be updated with the real content on exit.
        """
        # Create a temporary section with the same start and end
        body_bytes = b""  # Empty body for now

        # Create the base CodeSection using the builder's method
        code_section = build_section_from_bytes(
            section_index=self.writer.index,
            code_section_type=self.section_type,
            code=self.writer.code,
            qualname=self.qualname,
            body_bytes=body_bytes,
            byte_start=self.start_pos,
            byte_end=self.start_pos,  # Temporary end position is the same as start
            parent_id=self.parent_id,
            reference=self.reference,
            metadata=self.metadata,
        )
        return code_section

    def __enter__(self) -> CodeSectionScope:
        """Enter the section scope context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """
        Exit the section scope context.

        Updates the section with final byte positions and calls the assembler.
        """
        if exc_type is not None:
            return False

        end_pos = self.writer.cursor

        # Update the section with the real content
        text = self.writer.code.content_part_text.inline_text or ""
        body_bytes = text[self.start_pos : end_pos].encode("utf-8")

        # Update the existing section's segment
        self.code_section.content_part_text_segment.byte_end = end_pos

        # Update the identity hash
        self.code_section.identity_hash = make_identity_hash(
            code_section_type=self.section_type,
            code_id=self.writer.code.id,
            qualname=self.qualname,
            body_bytes=body_bytes,
        )

        # Assemble the domain object (explicit function only).
        _ = self._assemble(self.code_section, self.named_segments, self.nested_code_sections)

        # Register with parent scope if it exists
        if hasattr(self, "_parent_scope") and self._parent_scope is not None:
            # Use the section type name as the default registration name
            section_name = self.section_type.value
            self._parent_scope.register_nested_section(section_name, self.code_section)

        return False

    def indent(self, levels: int = 1) -> IndentScope:
        """
        Create an indentation scope.

        Args:
            levels: Number of indentation levels to add

        Returns:
            An indentation scope context manager
        """
        return IndentScope(self, levels)

    def token(self, txt: str, name: str | None = None) -> ContentPartTextSegment:
        """
        Add a token to the section.

        Args:
            txt: The text to add
            name: Optional name to identify the segment for assembly

        Returns:
            The created content part text segment
        """
        # Handle multi-line tokens to ensure proper indentation after line breaks
        if "\n" in txt and self.indent_level > 0:
            lines = txt.split("\n")
            indent = " " * (self.indent_level * self.writer.indent_size)

            # Apply indentation for the first line if at line start and line has content
            if self.writer.at_line_start and lines[0].strip():
                lines[0] = indent + lines[0]

            # Indent all lines after the first that have content
            for i in range(1, len(lines)):
                if lines[i].strip():  # Only indent lines with non-whitespace content
                    lines[i] = indent + lines[i]

            # Rejoin the text with the correct indentation
            txt = "\n".join(lines)

            # Create the segment
            segment = self.writer.append_token(txt)
        else:
            # Apply indentation if at the start of a line and the text has content
            if self.writer.at_line_start and self.indent_level > 0 and txt.strip():
                indent_text = " " * (self.indent_level * self.writer.indent_size)
                segment = self.writer.append_token(indent_text + txt)
            else:
                segment = self.writer.append_token(txt)

        # If a name is provided, store the segment
        if name:
            self.named_segments[name] = segment

        # Keep track of all segments for composition
        self._segment_parts.append(segment)

        # Update line start tracking
        self.writer.at_line_start = txt.endswith("\n")

        return segment

    def section(self, section: CodeSection) -> ContentPartTextSegment:
        """
        Reference an existing section's content.

        This doesn't duplicate the content, but allows referencing
        another section's content as part of this section's content.

        Args:
            section: An existing code section to reference

        Returns:
            The segment that was inserted
        """
        # Create a new segment from the section's segment
        new_segment = self.segment(section.content_part_text_segment)

        # Track this as a section reference
        self.writer.referenced_sections[new_segment.id] = section.id

        return new_segment

    def segment(self, segment: ContentPartTextSegment) -> ContentPartTextSegment:
        """
        Include an existing segment in this section.

        This doesn't duplicate the content, but allows embedding
        an existing segment as part of this section's content.

        Args:
            segment: An existing content part text segment to include

        Returns:
            The segment that was inserted
        """
        # Get the text from the segment
        text = get_segment_text(content_part_text_segment=segment)

        # Add it to our section
        return self.token(text)

    def start_section(
        self,
        spec: SectionSpec,
        *,
        qualname: str,
        reference: str | None = None,
        parent_id: UUID | None = None,
        metadata: Json | None = None,
    ) -> CodeSectionScope:
        """Start a nested section using an explicit SectionSpec."""
        nested_scope = self.writer.start_section(
            spec,
            qualname=qualname,
            reference=reference,
            parent_id=parent_id,
            metadata=metadata,
            indent_level=self.indent_level,
        )
        nested_scope._parent_scope = self
        return nested_scope

    def compose(self, segments: list[ContentPartTextSegment], name: str | None = None) -> ContentPartTextSegment:
        """
        Compose multiple segments into a single named segment.

        Args:
            segments: List of segments to compose
            name: Optional name for the composed segment

        Returns:
            A single segment spanning all input segments
        """
        if not segments:
            raise ValueError("Cannot compose empty segment list")

        if len(segments) == 1:
            # If name provided, store single segment under that name
            if name and segments[0]:
                self.named_segments[name] = segments[0]
            return segments[0]

        # Get first and last segment
        first = segments[0]
        last = segments[-1]

        # Create a new segment that spans from first to last
        composed_segment = ContentPartTextSegment(
            content_part_text=first.content_part_text,
            byte_start=first.byte_start,
            byte_end=last.byte_end,
        )

        # Store under name if provided
        if name:
            self.named_segments[name] = composed_segment

        return composed_segment

    def map_segments_by_name(self, segments: list[ContentPartTextSegment], name: str) -> list[ContentPartTextSegment]:
        """
        Map a list of segments to a name for assembler usage.

        This is the proper way to store lists of segments that assemblers expect,
        rather than directly manipulating named_segments.

        Args:
            segments: List of segments to map
            name: Name to store the segments under

        Returns:
            The same list of segments (for chaining)
        """
        if not segments:
            raise ValueError("Cannot map empty segment list")

        # Store the list of segments under the name
        self.named_segments[name] = segments

        return segments

    def register_nested_section(self, name: str, code_section: CodeSection) -> None:
        """
        Register a nested code section with this scope.

        Args:
            name: Name to store the section under
            code_section: The nested code section to register
        """
        if name in self.nested_code_sections:
            # If name already exists, convert to list or append to existing list
            existing = self.nested_code_sections[name]
            if isinstance(existing, list):
                existing.append(code_section)
            else:
                self.nested_code_sections[name] = [existing, code_section]
        else:
            self.nested_code_sections[name] = code_section


@final
class IndentScope:
    """Context manager for indented blocks of code."""

    def __init__(self, section_scope: CodeSectionScope, levels: int = 1):
        """
        Initialize an indentation scope.

        Args:
            section_scope: The section scope to indent
            levels: Number of indentation levels to add
        """
        self.section_scope = section_scope
        self.levels = levels

    def __enter__(self) -> None:
        """Increase the indentation level."""
        self.section_scope.indent_level += self.levels

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Decrease the indentation level."""
        self.section_scope.indent_level -= self.levels
        return False


@final
class CodeSectionWriter:
    """
    Writer for constructing CodeSection instances.

    Tracks byte positions and provides an API for constructing code sections
    without manual byte math.
    """

    def __init__(self, code: Code, index: CodeSectionBuilderIndex, indent_size: int = 4):
        """
        Initialize the section writer.

        Args:
            code: The code object to write to
            index: Shared index of sections
            indent_size: Number of spaces per indentation level
        """
        self.code = code
        self.index = index
        self.indent_size = indent_size
        self._cursor = 0
        self._at_line_start = True  # Track if we're at the start of a line
        self.referenced_sections: dict[UUID, UUID] = {}  # Maps segment_id -> section_id
        self.indent_level = 0  # Default indentation level

        # Initialize inline text if not already done (writer is inline-text only).
        if self.code.content_part_text.inline_text is None:
            self.code.content_part_text.inline_text = ""

    def __enter__(self) -> CodeSectionWriter:
        """Enter the writer context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Exit the writer context."""
        return False

    def _append_token(self, txt: str) -> ContentPartTextSegment:
        """
        Append a token to the content part text.

        Args:
            txt: The text to append

        Returns:
            Content part text segment for the appended text
        """
        start = self._cursor
        current = self.code.content_part_text.inline_text or ""
        self.code.content_part_text.inline_text = current + txt
        self._cursor += len(txt)

        return ContentPartTextSegment(
            content_part_text=self.code.content_part_text,
            byte_start=start,
            byte_end=self._cursor,
        )

    @property
    def cursor(self) -> int:
        return self._cursor

    @cursor.setter
    def cursor(self, value: int) -> None:
        self._cursor = value

    @property
    def at_line_start(self) -> bool:
        return self._at_line_start

    @at_line_start.setter
    def at_line_start(self, value: bool) -> None:
        self._at_line_start = value

    def append_token(self, txt: str) -> ContentPartTextSegment:
        return self._append_token(txt)

    def token(self, txt: str, _name: str | None = None) -> ContentPartTextSegment:
        """
        Add a token to the content.

        Args:
            txt: The text to add
            name: Optional name to identify the segment

        Returns:
            The created content part text segment
        """
        segment = self.append_token(txt)
        # Update line start tracking
        self.at_line_start = txt.endswith("\n")
        return segment

    def start_section(
        self,
        spec: SectionSpec,
        *,
        qualname: str,
        reference: str | None = None,
        parent_id: UUID | None = None,
        metadata: Json | None = None,
        indent_level: int | None = None,
    ) -> CodeSectionScope:
        """Start a new section using an explicit SectionSpec (preferred)."""
        # IMPORTANT: preserve indent level from the caller scope. Writer-level indent is always 0.
        return CodeSectionScope(
            writer=self,
            spec=spec,
            qualname=qualname,
            parent_id=parent_id,
            reference=reference,
            indent_level=(int(indent_level) if indent_level is not None else self.indent_level),
            metadata=metadata,
        )

    def get_section_by_ref(self, code_section_type: CodeSectionType, reference: str) -> CodeSection | None:
        """
        Get a section by its reference.

        Args:
            code_section_type: Type of the section to retrieve
            reference: The section reference string

        Returns:
            The section if found, None otherwise
        """
        return self.index.get_by_ref(code_section_type, reference)

    def compose_sections(
        self,
        sections: list[CodeSection],
        joiner: str = "",
        start_text: str = "",
        end_text: str = "",
    ) -> str:
        """
        Compose multiple sections into a single text string.

        Args:
            sections: List of code sections to compose
            joiner: Optional text to join sections with
            start_text: Optional text to prepend
            end_text: Optional text to append

        Returns:
            Composed text string
        """
        parts: list[str] = []

        if start_text:
            parts.append(start_text)

        for i, section in enumerate(sections):
            # Get the section's content
            parts.append(get_segment_text(content_part_text_segment=section.content_part_text_segment))

            # Add joiner if not the last section
            if i < len(sections) - 1:
                parts.append(joiner)

        if end_text:
            parts.append(end_text)

        return "".join(parts)
