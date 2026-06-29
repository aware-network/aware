"""Regex filters for file system introspection."""

import re
from typing import List, Tuple
from pydantic import BaseModel

from aware_file_system.filters.base import Filter


class RegexPattern(BaseModel):
    """Model for a regex pattern with inclusion/exclusion flag."""

    pattern: re.Pattern
    include: bool = False  # Default to exclude (original behavior)


class Regex(Filter):
    """
    A filter that includes or excludes files based on regex patterns.

    Each pattern can be marked for inclusion or exclusion.
    - Include patterns: file is included if it matches ANY include pattern
    - Exclude patterns: file is excluded if it matches ANY exclude pattern

    If both include and exclude patterns are present:
    1. File must match at least one include pattern
    2. File must not match any exclude pattern

    If only exclude patterns are present:
    - File is included if it doesn't match any exclude pattern

    If only include patterns are present:
    - File is included only if it matches at least one include pattern
    """

    patterns: List[RegexPattern]

    def __init__(self, patterns: List[Tuple[re.Pattern, bool]]):
        """
        Initialize the filter with regex patterns.

        Args:
            patterns: List of (pattern, include) tuples
                pattern: Compiled regex pattern
                include: True for inclusion, False for exclusion
        """
        patterns = [RegexPattern(pattern=p, include=i) for p, i in patterns]
        super().__init__(patterns=patterns)

    def should_include(self, file_path: str) -> bool:
        """
        Determine whether a file should be included based on regex patterns.

        Args:
            file_path: The path of the file to be checked

        Returns:
            True if the file should be included, False otherwise
        """
        # Separate include and exclude patterns
        include_patterns = [p.pattern for p in self.patterns if p.include]
        exclude_patterns = [p.pattern for p in self.patterns if not p.include]

        # If we have include patterns, file must match at least one
        if include_patterns:
            included = False
            for pattern in include_patterns:
                if pattern.search(file_path):
                    included = True
                    break

            # If file doesn't match any include pattern, exclude it
            if not included:
                return False

        # If we have exclude patterns, file must not match any
        for pattern in exclude_patterns:
            if pattern.search(file_path):
                return False

        # File passes all checks
        return True
