"""
Description normalization utilities for consistent handling across languages.

This module provides utilities to normalize text descriptions extracted from code comments
and docstrings to ensure consistent formatting when converting between different languages
(e.g., SQL to Aware). This prevents spurious diffs caused by whitespace and indentation differences.
"""

import re
import textwrap
from typing import Optional


class DescriptionNormalizer:
    """
    Utility class for normalizing text descriptions extracted from code.

    Handles:
    - Consistent indentation normalization using textwrap.dedent
    - Line ending normalization
    - Trailing whitespace cleanup
    - Consistent spacing around parameters/returns sections
    """

    @staticmethod
    def normalize_description(text: Optional[str]) -> Optional[str]:
        """
        Normalize a description text for consistent formatting.

        Args:
            text: The raw description text to normalize

        Returns:
            Normalized description text, or None if input was None/empty
        """
        if not text:
            return None

        # Convert all line endings to \n
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        # Handle the case where first line has no indentation but subsequent lines do
        lines = normalized.split("\n")
        if len(lines) > 1:
            # Find the minimum indentation of non-empty lines (excluding the first line)
            indentations = []
            for line in lines[1:]:  # Skip first line
                if line.strip():  # Only consider non-empty lines
                    indent = len(line) - len(line.lstrip())
                    indentations.append(indent)

            if indentations:
                min_indent = min(indentations)
                # Remove the minimum indentation from all lines except the first
                normalized_lines = [lines[0]]  # Keep first line as-is
                for line in lines[1:]:
                    if line.strip():  # Non-empty line
                        # Remove min_indent spaces if they exist
                        if len(line) >= min_indent and line[:min_indent].isspace():
                            normalized_lines.append(line[min_indent:])
                        else:
                            normalized_lines.append(line.lstrip())
                    else:
                        normalized_lines.append("")  # Keep empty lines
                normalized = "\n".join(normalized_lines)

        # Strip trailing whitespace from each line
        lines = normalized.split("\n")
        lines = [line.rstrip() for line in lines]

        # Rejoin and strip leading/trailing empty lines
        normalized = "\n".join(lines).strip()

        # Normalize spacing around common documentation patterns
        normalized = DescriptionNormalizer._normalize_doc_patterns(normalized)

        return normalized if normalized else None

    @staticmethod
    def _normalize_doc_patterns(text: str) -> str:
        """
        Normalize common documentation patterns like Parameters/Returns sections.

        Args:
            text: Text to normalize

        Returns:
            Text with normalized documentation patterns
        """
        # Normalize "Parameters:" sections - ensure consistent spacing
        text = re.sub(
            r"(\n\s*)Parameters:\s*(\n\s*)",
            r"\1Parameters:\2",
            text,
            flags=re.MULTILINE,
        )

        # Normalize "Returns:" sections - ensure consistent spacing
        text = re.sub(r"(\n\s*)Returns:\s*(\n\s*)", r"\1Returns:\2", text, flags=re.MULTILINE)

        # Normalize parameter descriptions - ensure consistent spacing
        # This handles both "param_name:" and "    param_name:" patterns
        # NOTE: Do not consume newlines after the ':' (keep headings like "Notes:" stable).
        text = re.sub(r"(\n)\s*(\w+):[ \t]+", r"\1\2: ", text, flags=re.MULTILINE)

        return text

    @staticmethod
    def normalize_for_rendering(text: Optional[str], preserve_structure: bool = True) -> Optional[str]:
        """
        Normalize text specifically for code rendering.

        This is used when emitting descriptions in generated code to ensure
        they don't have extra indentation that would cause diffs.

        Args:
            text: The description text to normalize
            preserve_structure: Whether to preserve the internal structure of the text

        Returns:
            Normalized text ready for code rendering
        """
        if not text:
            return None

        # Start with basic normalization
        normalized = DescriptionNormalizer.normalize_description(text)

        if not normalized:
            return None

        if not preserve_structure:
            # For simple cases, just make it a single line
            normalized = " ".join(normalized.split())

        return normalized
