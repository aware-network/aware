import logging
import re
from collections.abc import Iterable
from typing import List

from aware_file_system.filters.base import Filter
from aware_file_system.filters.gitignore import GitIgnore
from aware_file_system.filters.default import Size, Depth
from aware_file_system.filters.regex import Regex
from aware_file_system.config import FilterConfig

logger = logging.getLogger(__name__)


class Composite(Filter):
    """
    A filter that combines multiple filters using the composite pattern.

    This filter allows for complex filter combinations by applying multiple
    filters and including a file only if all filters agree to include it.
    """

    all_filters: List[Filter]

    def add_filters(self, filters: List[Filter]) -> None:
        """
        Add a list of filters to the composite filter.

        Args:
            filters: The filters to add
        """
        self.all_filters.extend(filters)

    def should_include(self, file_path: str) -> bool:
        """
        Determine whether a file should be included by applying all filters.

        Args:
            file_path: The path of the file to be checked

        Returns:
            True if all filters agree to include the file, False otherwise
        """
        for filter_ in self.all_filters:
            result = filter_.should_include(file_path)
            if not result:
                logger.debug(
                    f"File {file_path} was excluded by {filter_.__class__.__name__}"
                )
                return False
        return True

    def should_include_directory(self, directory_path: str) -> bool:
        """Apply only filters with directory-safe traversal semantics."""
        for filter_ in self.all_filters:
            if isinstance(filter_, GitIgnore) and not filter_.should_include_directory(
                directory_path
            ):
                logger.debug("Directory %s was excluded by GitIgnore", directory_path)
                return False
        return True

    def included_files(self, file_paths: Iterable[str]) -> set[str]:
        """Apply filter policy in bounded batches where a filter supports it."""

        included = set(file_paths)
        for filter_ in self.all_filters:
            batch = getattr(filter_, "included_files", None)
            if batch is not None:
                included = batch(included)
            else:
                included = {
                    file_path
                    for file_path in included
                    if filter_.should_include(file_path)
                }
        return included

    @classmethod
    def from_config(cls, config: FilterConfig, root_path: str) -> "Composite":
        """
        Create a composite filter from configuration.

        Args:
            config: Filter configuration
            root_path: Root path of the project

        Returns:
            Configured composite filter
        """
        filter_list = []

        # GitIgnore Filter
        if config.use_gitignore:
            gitignore_filter = GitIgnore()
            gitignore_filter.setup(root_path)
            filter_list.append(gitignore_filter)

        # Regex Filter
        if config.regex:
            # Convert RegexConfig objects to (pattern, include) tuples
            pattern_tuples = [(re.compile(r.pattern), r.include) for r in config.regex]
            regex_filter = Regex(patterns=pattern_tuples)
            filter_list.append(regex_filter)

        # Size Filter
        if config.max_file_size is not None:
            size_filter = Size(max_size=config.max_file_size)
            filter_list.append(size_filter)

        # Depth Filter
        if config.max_depth is not None:
            depth_filter = Depth(max_depth=config.max_depth, root_path=root_path)
            filter_list.append(depth_filter)

        return Composite(all_filters=filter_list)
