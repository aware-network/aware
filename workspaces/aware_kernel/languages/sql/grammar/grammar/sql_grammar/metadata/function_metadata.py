from __future__ import annotations

from enum import Enum
import re
from typing import ClassVar, Self
from typing_extensions import override

from aware_code.section.metadata import CodeSectionMetadata

# Import the normalizer
from aware_utils.description_normalizer import DescriptionNormalizer


class SQLFunctionType(str, Enum):
    """Type of a SQL function."""

    CLASS = "class"  # Class-level function
    INSTANCE = "instance"  # Instance-level function


class SQLFunctionMetadata(CodeSectionMetadata):
    """Metadata for a SQL function extracted from SQL comments."""

    description: str | None = None
    function_table: str
    function_name: str
    function_type: SQLFunctionType
    function_class_values: dict[str, str]

    DOCSTRING_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"DOCSTRING:\s*(.*?)(?:\nMETADATA:|$)", re.DOTALL)
    METADATA_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"METADATA:(.*?)(?:\n\w+:|$)", re.DOTALL)

    @property
    def is_valid(self) -> bool:
        """Check if this metadata is valid (has a function table)."""
        return bool(self.function_table)

    @override
    @classmethod
    def from_raw_comment(cls, raw_comment: str) -> Self:
        """
        Extract function metadata from a SQL function comment.

        Args:
            raw_comment: The SQL function comment containing docstring and metadata

        Returns:
            SQLFunctionMetadata object containing the extracted metadata
        """
        if not raw_comment:
            return cls(
                description=None,
                function_table="",
                function_name="",
                function_type=SQLFunctionType.CLASS,
                function_class_values={},
            )

        # Extract docstring
        docstring_match = cls.DOCSTRING_PATTERN.search(raw_comment)
        raw_description = docstring_match.group(1).strip() if docstring_match else None

        # Normalize the description to ensure consistent formatting
        description = DescriptionNormalizer.normalize_description(raw_description)

        # Extract metadata section
        metadata_match = cls.METADATA_PATTERN.search(raw_comment)
        metadata_dict: dict[str, str] = {}

        if metadata_match:
            metadata_content = metadata_match.group(1).strip()
            for line in metadata_content.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata_dict[key.strip()] = value.strip()

        # Extract specific metadata fields
        function_table: str = metadata_dict.get("Function Table", "")
        function_name: str = metadata_dict.get("Function Name", "")

        # Parse function type
        function_type_str: str = metadata_dict.get("Function Type", "class")
        try:
            function_type = SQLFunctionType(function_type_str)
        except ValueError:
            # Default to CLASS if invalid type is provided
            function_type = SQLFunctionType.CLASS

        # Parse function class values
        function_class_values: dict[str, str] = {}
        function_class_values_str: str = metadata_dict.get("Function Class Values", "")
        if function_class_values_str:
            for pair in function_class_values_str.split(","):
                pair_str = pair.strip()
                if "=" in pair_str:
                    key, value = pair_str.split("=", 1)
                    function_class_values[key.strip()] = value.strip()

        return cls(
            description=description,
            function_table=function_table,
            function_name=function_name,
            function_type=function_type,
            function_class_values=function_class_values,
        )
