import io
import logging
import os
from pydantic import BaseModel
import re

from aware_file_system.filters.base import Filter

logger = logging.getLogger(__name__)


class GitIgnorePatterns(BaseModel):
    """
    Pydantic model to represent patterns for a directory.
    """

    directory: str
    patterns: list[str]  # Patterns associated with the directory and its parents


class GitIgnore(Filter):
    _root_path: str  # Root path of the project
    _patterns_cache: dict[str, list[str]]  # Cache for storing full patterns for each directory

    def setup(self, root_path: str) -> None:
        """
        Precompute patterns for all directories during the setup phase, aggregating patterns from parent directories.
        """
        self._root_path = root_path
        self._patterns_cache = {}
        self._precompute_patterns_recursively(root_path, [])
        logger.debug(f"Precomputed patterns: {self._patterns_cache}")

    def should_include(self, file_path: str) -> bool:
        """
        Check if the file should be included by fetching all relevant patterns directly from the precomputed cache.
        """
        # Always use the relative path for consistency
        relative_path_dir = os.path.relpath(os.path.dirname(file_path), self._root_path)

        # Directly lookup patterns that apply to this directory
        relevant_patterns = self._get_relevant_patterns(relative_path_dir)

        # Check if any of the relevant patterns match the file path
        for pattern in relevant_patterns:
            if self._matches_pattern(file_path, pattern):
                logger.debug(f"File {file_path} was excluded by .gitignore pattern {pattern}")
                return False

        return True

    def _precompute_patterns_recursively(self, current_dir: str, inherited_patterns: list[str]) -> None:
        """
        Recursively compute patterns for each directory and propagate patterns only to its subdirectories.
        """
        current_patterns = inherited_patterns.copy()

        # Check for .gitignore in the current directory
        gitignore_path = os.path.join(current_dir, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                current_patterns.extend(self._parse_gitignore(f, os.path.relpath(current_dir, current_dir)))

        # Cache the combined patterns for this directory using the relative path
        relative_dir = os.path.relpath(current_dir, self._root_path)
        self._patterns_cache[relative_dir] = current_patterns

        # Recursively process each subdirectory
        for entry in os.listdir(current_dir):
            subdir_path = os.path.join(current_dir, entry)
            if os.path.isdir(subdir_path):
                self._precompute_patterns_recursively(subdir_path, current_patterns)

    def _parse_gitignore(self, file: io.TextIOWrapper, base_path: str) -> list[str]:
        """
        Parse a .gitignore file and return patterns relevant for the directory.
        """
        patterns = []
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                if line.startswith("/"):
                    # Match the pattern starting from the base directory
                    pattern = os.path.join(base_path, line[1:])
                else:
                    # Match any path that includes the base directory
                    pattern = os.path.join("**", line)
                patterns.append(pattern)
        return patterns

    def _get_relevant_patterns(self, path_dir: str) -> list[str]:
        """
        Fetch relevant patterns for the directory by directly looking up in the precomputed cache.
        """
        return self._patterns_cache.get(path_dir, [])

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        regex = self._gitignore_pattern_to_regex(pattern)
        return regex.match(path) is not None

    def _gitignore_pattern_to_regex(self, pattern: str) -> re.Pattern:
        regex = re.escape(pattern)
        regex = regex.replace(r"\*\*", ".*")
        regex = regex.replace(r"\*", "[^/]*")
        regex = regex.replace(r"\?", "[^/]")
        if not pattern.startswith("/"):
            regex = "(.*/)?" + regex
        return re.compile(f"^{regex}(/.*)?$")
