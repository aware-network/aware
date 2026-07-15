"""Aware function metadata adapter that preserves docstring formatting."""

from __future__ import annotations

from aware_code.section.metadata import CodeSectionMetadata
from typing_extensions import override


class AwareFunctionMetadata(CodeSectionMetadata):
    """
    Metadata adapter for Aware functions that preserves docstring formatting.

    Unlike the general DescriptionNormalizer, this preserves:
    - Blank lines around sections
    - Indentation for Args/Returns sections
    - Original spacing and structure
    """

    @override
    @classmethod
    def from_raw_comment(cls, raw_comment: str) -> AwareFunctionMetadata:
        """
        Extract function metadata from an Aware function docstring.

        This preserves the original formatting of docstrings, only doing minimal cleanup.

        Args:
            raw_comment: The raw docstring/comment text

        Returns:
            AwareFunctionMetadata with preserved formatting
        """
        if not raw_comment:
            return cls()

        # Only do minimal cleanup - preserve formatting
        cleaned_description = cls._preserve_docstring_formatting(raw_comment)

        return cls(description=cleaned_description, requires_normalization=False)

    @staticmethod
    def _preserve_docstring_formatting(text: str) -> str | None:
        """
        Clean docstring text while preserving important formatting.

        Args:
            text: Raw docstring text

        Returns:
            Cleaned text with preserved formatting
        """
        if not text:
            return None

        # Convert line endings to \n
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove leading/trailing empty lines but preserve internal structure
        lines = normalized.split("\n")

        # Find first and last non-empty lines
        first_content = None
        last_content = None

        for i, line in enumerate(lines):
            if line.strip():
                if first_content is None:
                    first_content = i
                last_content = i

        if first_content is None:
            return None

        assert last_content is not None

        # Keep only the content lines (removing leading/trailing empty lines)
        content_lines = lines[first_content:last_content + 1]

        # Remove common leading whitespace from all lines (dedent)
        if content_lines:
            # Find minimum indentation of non-empty lines, excluding the first line
            # (the first line is typically the summary and may be at different indentation)
            indentations: list[int] = []
            for i, line in enumerate(content_lines):
                if line.strip() and i > 0:  # Skip first line for min calculation
                    indent = len(line) - len(line.lstrip())
                    indentations.append(indent)

            if indentations:
                min_indent = min(indentations)
                # Remove min_indent from lines after the first (excluding empty ones)
                dedented_lines: list[str] = []
                for i, line in enumerate(content_lines):
                    if i == 0:
                        # Keep first line as-is
                        dedented_lines.append(line)
                    elif line.strip():  # Non-empty line after first
                        if len(line) >= min_indent:
                            dedented_line = line[min_indent:]
                            dedented_lines.append(dedented_line)
                        else:
                            dedented_line = line.lstrip()
                            dedented_lines.append(dedented_line)
                    else:  # Empty line - preserve as empty
                        dedented_lines.append("")

                content_lines = dedented_lines
            else:
                # If no lines to measure (only first line), keep as is
                pass

        # Join back and return
        result = "\n".join(content_lines)
        return result if result.strip() else None
