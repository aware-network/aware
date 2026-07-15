"""Surgical writer for constructing CodeSection instances with cursor-based insertion."""

from __future__ import annotations

from types import TracebackType
from typing import Literal, final
from uuid import UUID

# Code Ontology
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Kernel Graph Ontology Code
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Aware Content
from aware_content.builder import get_text, get_segment_text

# Code Runtime
from aware_code.section.builder import build_section_from_bytes, make_identity_hash
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.spec import SectionSpec, AssembleFn
from aware_code.types.json import Json

from aware_utils.logging import logger


@final
class CodeSectionScopeSurgical:
    """
    Surgical context manager for a code section scope.

    Tracks segments and allows building a code section by writing tokens with
    proper cursor-based insertion support.
    """

    def __init__(
        self,
        writer: CodeSectionWriterSurgical,
        assemble: AssembleFn,
        section_type: CodeSectionType,
        qualname: str,
        parent_id: UUID | None = None,
        reference: str | None = None,
        indent_level: int = 0,
        metadata: Json | None = None,
    ):
        """
        Initialize a surgical section scope.

        Args:
            writer: The parent surgical section writer
            section_type: The type of section to create
            qualname: Fully qualified name for the section
            parent_id: Optional ID of parent section
            reference: Optional reference string for lookup
            indent_level: Current indentation level
            metadata: Optional metadata dict for surgical editing support
        """
        self.writer = writer
        self.section_type = section_type
        self.qualname = qualname
        self.parent_id = parent_id
        self.reference = reference
        self.indent_level = indent_level
        self._assemble = assemble
        self.metadata: Json = metadata if metadata is not None else Json()
        self.start_pos = self.writer.cursor
        self.named_segments: dict[str, ContentPartTextSegment | list[ContentPartTextSegment]] = {}
        self.nested_code_sections: dict[str, CodeSection | list[CodeSection]] = {}
        self._segment_parts: list[ContentPartTextSegment] = []
        self._parent_scope: CodeSectionScopeSurgical | None = None

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

    def __enter__(self) -> CodeSectionScopeSurgical:
        """Enter the surgical section scope context."""
        # Register this scope as the active scope in the writer
        self.writer.push_scope(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """
        Exit the surgical section scope context.

        Updates the section with final byte positions and calls the assembly function.
        """
        # Unregister this scope from the writer
        _ = self.writer.pop_scope()

        if exc_type is not None:
            return False

        end_pos = self.writer.cursor

        # Update the section with the real content
        code_text = get_text(self.writer.code.content_part_text)
        body_bytes = code_text[self.start_pos : end_pos].encode("utf-8")

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

    def indent(self, levels: int = 1) -> IndentScopeSurgical:
        """
        Create an indentation scope.

        Args:
            levels: Number of indentation levels to add

        Returns:
            An indentation scope context manager
        """
        return IndentScopeSurgical(self, levels)

    def token(self, txt: str, name: str | None = None) -> ContentPartTextSegment:
        """
        Add a token to the section with surgical insertion support.

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

            # Create the segment using surgical insertion
            segment = self.writer.insert_token(txt)
        else:
            # Apply indentation if at the start of a line and the text has content
            if self.writer.at_line_start and self.indent_level > 0 and txt.strip():
                indent_text = " " * (self.indent_level * self.writer.indent_size)
                segment = self.writer.insert_token(indent_text + txt)
            else:
                segment = self.writer.insert_token(txt)

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
        text = get_segment_text(segment)

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
        indent_level: int = 0,
    ) -> CodeSectionScopeSurgical:
        """Start a nested section. SSOT is start_section(SectionSpec(...))."""
        nested_scope = self.writer.start_section(
            spec,
            qualname=qualname,
            reference=reference,
            parent_id=parent_id,
            metadata=metadata,
            indent_level=indent_level or self.indent_level,
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
        Map a list of segments to a name for assembly usage.

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
class IndentScopeSurgical:
    """Context manager for indented blocks of code in surgical mode."""

    def __init__(self, section_scope: CodeSectionScopeSurgical, levels: int = 1):
        """
        Initialize a surgical indentation scope.

        Args:
            section_scope: The surgical section scope to indent
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
class CodeSectionWriterSurgical:
    """
    Surgical writer for constructing CodeSection instances with cursor-based insertion.

    This writer supports true insertion at specific positions within existing content,
    unlike the standard CodeSectionWriter which only supports appending.
    """

    def __init__(self, code: Code, index: CodeSectionBuilderIndex, indent_size: int = 4):
        """
        Initialize the surgical section writer.

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

        # Surgical writer operates on inline_text for deterministic byte offsets.
        if self.code.content_part_text.inline_text is None:
            self.code.content_part_text.inline_text = ""

        # Active scope tracking for scope reuse without context duplication
        self._active_scope: CodeSectionScopeSurgical | None = None
        self._scope_stack: list[CodeSectionScopeSurgical] = []

    def _push_scope(self, scope: CodeSectionScopeSurgical) -> None:
        """
        Push a new scope onto the scope stack and make it active.

        Args:
            scope: The scope to push and activate
        """
        if self._active_scope is not None:
            self._scope_stack.append(self._active_scope)
        self._active_scope = scope

    def _pop_scope(self) -> CodeSectionScopeSurgical | None:
        """
        Pop the current active scope and restore the previous one.

        Returns:
            The scope that was popped
        """
        current_scope = self._active_scope
        if self._scope_stack:
            self._active_scope = self._scope_stack.pop()
        else:
            self._active_scope = None
        return current_scope

    def get_active_scope(self) -> CodeSectionScopeSurgical | None:
        """
        Get the currently active scope for reuse by child renderers.

        Returns:
            The currently active scope, or None if no scope is active
        """
        return self._active_scope

    def has_active_scope(self) -> bool:
        """
        Check if there is an active scope that children can reuse.

        Returns:
            True if there is an active scope, False otherwise
        """
        return self._active_scope is not None

    def __enter__(self) -> CodeSectionWriterSurgical:
        """Enter the surgical writer context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Exit the surgical writer context."""
        return False

    def _insert_token(self, txt: str) -> ContentPartTextSegment:
        """
        Insert a token at the current cursor position (SURGICAL INSERTION).

        This is the key difference from CodeSectionWriter._append_token:
        - CodeSectionWriter always appends to the end (text += txt)
        - CodeSectionWriterSurgical inserts at cursor position

        Args:
            txt: The text to insert

        Returns:
            Content part text segment for the inserted text
        """
        start = self._cursor

        # SURGICAL INSERTION: Insert at cursor position instead of appending
        current_text = self.code.content_part_text.inline_text or ""
        before_cursor = current_text[: self._cursor]
        after_cursor = current_text[self._cursor :]
        new_text = before_cursor + txt + after_cursor

        # Update the content with the inserted text
        self.code.content_part_text.inline_text = new_text

        # Update cursor position
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

    def push_scope(self, scope: CodeSectionScopeSurgical) -> None:
        self._push_scope(scope)

    def pop_scope(self) -> CodeSectionScopeSurgical | None:
        return self._pop_scope()

    def insert_token(self, txt: str) -> ContentPartTextSegment:
        return self._insert_token(txt)

    def token(self, txt: str, _name: str | None = None) -> ContentPartTextSegment:
        """
        Add a token to the content at the current cursor position.

        Args:
            txt: The text to add
            name: Optional name to identify the segment

        Returns:
            The created content part text segment
        """
        segment = self.insert_token(txt)
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
        indent_level: int = 0,
    ) -> CodeSectionScopeSurgical:
        """Start a new surgical section using an explicit SectionSpec (preferred)."""
        return CodeSectionScopeSurgical(
            writer=self,
            assemble=spec.assemble,
            qualname=qualname,
            parent_id=parent_id,
            reference=reference,
            indent_level=indent_level,
            metadata=metadata,
            section_type=spec.section_type,
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
            parts.append(get_segment_text(section.content_part_text_segment))

            # Add joiner if not the last section
            if i < len(sections) - 1:
                parts.append(joiner)

        if end_text:
            parts.append(end_text)

        return "".join(parts)

    def shift_offsets(self, from_byte: int, delta: int) -> None:
        """
        Shift byte offsets for all sections in a code object that come after the given position.

        This is crucial for maintaining correct byte positions after insertions/deletions.

        Args:
            code: The code object containing the sections
            from_byte: The byte position after which to shift offsets
            delta: The number of bytes to shift (positive for insertion, negative for deletion)
        """
        # Find all sections in this code that start after from_byte
        for section in self.code.code_sections:
            if section.content_part_text_segment.byte_start is None:
                logger.warning(f"Section {section.id} has no byte start")
                continue
            if section.content_part_text_segment.byte_end is None:
                logger.warning(f"Section {section.id} has no byte end")
                continue
            if section.content_part_text_segment.byte_start >= from_byte:
                section.content_part_text_segment.byte_start += delta
                section.content_part_text_segment.byte_end += delta

    def replace_segment_text(self, segment: ContentPartTextSegment, new_text: str) -> None:
        """
        Replace the text content of a specific segment.

        This is the core of surgical editing - replacing specific parts without
        re-rendering entire sections.

        Args:
            segment: The ContentPartTextSegment to replace
            new_text: The new text content
        """
        if segment.byte_start is None or segment.byte_end is None:
            # Fallback: attempt to locate the segment text within the current
            # code buffer so we can derive byte offsets on the fly. Some legacy
            # sections do not persist byte positions, but we can usually infer
            # them from the stored segment text.
            segment_text = get_segment_text(segment) or ""
            if segment_text:
                logger.debug(
                    "Inferring byte positions for segment %s via substring search (snippet=%r)",
                    getattr(segment, "id", None),
                    segment_text[:120],
                )
                haystack = self.code.content_part_text.inline_text or ""
                candidate_index = haystack.find(segment_text)
                if candidate_index != -1:
                    segment.byte_start = candidate_index
                    segment.byte_end = candidate_index + len(segment_text)
            if segment.byte_start is None or segment.byte_end is None:
                logger.warning(f"Segment {segment.id} has no byte positions and could not be inferred")
                return
        old_text = self.code.content_part_text.inline_text or ""
        old_length = segment.byte_end - segment.byte_start
        new_length = len(new_text)

        # Replace the text
        before = old_text[: segment.byte_start]
        after = old_text[segment.byte_end :]
        logger.warning(
            "Replacing segment %s start=%s end=%s old_len=%s new_len=%s snippet_before=%r new_snippet=%r",
            getattr(segment, "id", None),
            segment.byte_start,
            segment.byte_end,
            old_length,
            new_length,
            old_text[segment.byte_start : segment.byte_end][:120],
            new_text[:120],
        )
        self.code.content_part_text.inline_text = before + new_text + after

        # Update segment end position
        segment.byte_end = segment.byte_start + new_length

        # Shift all subsequent offsets
        delta = new_length - old_length
        if delta != 0:
            self.shift_offsets(segment.byte_end, delta)

    def replace_section_text(self, section: CodeSection, new_text: str) -> None:
        """Replace the full text of a section in-place using its primary segment."""
        segment = section.content_part_text_segment
        if not segment:
            logger.warning("Cannot replace section text: section has no content segment")
            return

        self.replace_segment_text(segment, new_text)

    def insert_segment(self, byte_start: int, byte_end: int, text: str) -> ContentPartTextSegment:
        """
        Insert new text at a specific position and create a ContentPartTextSegment for it.

        This method:
        1. Inserts text at the specified position
        2. Creates a ContentPartTextSegment for the inserted content
        3. Handles offset shifting for subsequent sections
        4. Returns the new segment

        Args:
            byte_start: Position where to insert the text
            byte_end: End position (usually same as byte_start for pure insertion)
            text: The text content to insert

        Returns:
            ContentPartTextSegment representing the inserted content
        """
        old_text = self.code.content_part_text.inline_text or ""
        text_length = len(text)

        # Insert the text at the specified position
        before = old_text[:byte_start]
        after = old_text[byte_end:]
        self.code.content_part_text.inline_text = before + text + after

        # Create a ContentPartTextSegment for the inserted content
        new_segment = ContentPartTextSegment(
            content_part_text=self.code.content_part_text,
            byte_start=byte_start,
            byte_end=byte_start + text_length,
        )

        # Shift all subsequent offsets
        delta = text_length - (byte_end - byte_start)
        if delta != 0:
            self.shift_offsets(byte_start + text_length, delta)

        return new_segment

    def insertion_scope(self, position: int) -> InsertionScope:
        """
        Create an insertion scope for surgical insertions at a specific position.

        This provides a clean context manager API for ad-hoc insertions that automatically:
        - Positions the writer at the specified location
        - Tracks content length changes
        - Shifts offsets for any existing sections after the insertion

        Args:
            position: Absolute byte position where insertion should occur

        Returns:
            Context manager that handles surgical insertion workflow

        Example:
            with writer.insertion_scope(insertion_point) as scope:
                scope.token("new content")
                scope.token(" more content")
        """
        return InsertionScope(self, position)


@final
class IndentScopeInsertion:
    """Context manager for indented blocks of code in insertion scopes."""

    def __init__(self, insertion_scope: "InsertionScope", levels: int = 1):
        """
        Initialize an insertion indentation scope.

        Args:
            insertion_scope: The insertion scope to indent
            levels: Number of indentation levels to add
        """
        self.insertion_scope = insertion_scope
        self.levels = levels

    def __enter__(self) -> "InsertionScope":
        """Increase the indentation level and return the scope for method chaining."""
        self.insertion_scope.indent_level += self.levels
        return self.insertion_scope

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Decrease the indentation level."""
        self.insertion_scope.indent_level -= self.levels
        return False


@final
class InsertionScope:
    """
    Context manager for surgical insertions with automatic offset management.

    Handles the complete workflow:
    1. Position writer at insertion point
    2. Capture initial content state
    3. Allow token insertion via proxy methods
    4. Calculate insertion length on exit
    5. Shift offsets for affected sections
    6. Track indentation levels and automatically apply them
    """

    def __init__(self, writer: CodeSectionWriterSurgical, position: int):
        """
        Initialize insertion scope.

        Args:
            writer: The surgical writer to use
            position: Absolute byte position for insertion
        """
        self._writer = writer
        self._position = position
        self._original_cursor = writer.cursor
        self._initial_length = len(writer.code.content_part_text.inline_text or "")
        self._indent_level = 0  # Track indentation level for this scope
        self._at_line_start = True  # Track if we're at the start of a line

    @property
    def indent_level(self) -> int:
        return self._indent_level

    @indent_level.setter
    def indent_level(self, value: int) -> None:
        self._indent_level = value

    def __enter__(self) -> "InsertionScope":
        """Enter the insertion scope and position the writer."""
        # Position writer at insertion point
        self._writer.cursor = self._position
        self._writer.at_line_start = True
        self._at_line_start = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Exit scope and handle offset shifting."""
        if exc_type is not None:
            return False

        # Calculate how much content was inserted
        final_length = len(self._writer.code.content_part_text.inline_text or "")
        inserted_length = final_length - self._initial_length

        # Shift offsets for any sections after our insertion point
        if inserted_length > 0:
            self._writer.shift_offsets(self._position, inserted_length)

        # Don't restore cursor - let it stay where the insertion ended
        return False

    def token(self, txt: str, name: str | None = None) -> ContentPartTextSegment:
        """
        Insert a token at the current position with automatic indentation.

        When at the start of a line, automatically applies the current indentation level.

        Args:
            txt: The text to add
            name: Optional name to identify the segment

        Returns:
            The created content part text segment
        """
        # If we're at the start of a line and have indentation, apply it
        if self._at_line_start and self._indent_level > 0 and txt and not txt.isspace():
            indent_text = "    " * self._indent_level  # 4 spaces per level
            segment = self._writer.token(indent_text + txt, name)
        else:
            segment = self._writer.token(txt, name)

        # Update line start tracking
        self._at_line_start = txt.endswith("\n")

        return segment

    def start_section(
        self,
        spec: SectionSpec,
        *,
        qualname: str,
        reference: str | None = None,
        parent_id: UUID | None = None,
        metadata: Json | None = None,
    ) -> CodeSectionScopeSurgical:
        """Start a new section within the insertion scope. SSOT is start_section(SectionSpec(...))."""
        return self._writer.start_section(
            spec,
            qualname=qualname,
            reference=reference,
            parent_id=parent_id,
            metadata=metadata,
            indent_level=self._indent_level,
        )

    def indent(self, levels: int = 1) -> IndentScopeInsertion:
        """
        Create an indentation scope within the insertion.

        Args:
            levels: Number of indentation levels to add (default: 1)

        Returns:
            Context manager that temporarily increases indentation

        Example:
            with scope.indent():
                scope.token("def function():\n")
                with scope.indent():
                    scope.token('\"\"\"Docstring\"\"\"\\n')
                    scope.token("pass\n")
        """
        return IndentScopeInsertion(self, levels)
