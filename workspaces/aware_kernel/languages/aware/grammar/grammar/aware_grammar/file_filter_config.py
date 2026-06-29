"""Aware file filter for file system introspection."""

from aware_file_system.config import FilterConfig, RegexConfig


class AwareFileFilterConfig(FilterConfig):
    """Filter configuration specifically for Aware files."""

    use_gitignore: bool = True
    regex: list[RegexConfig] = [RegexConfig(pattern=r".*\.aware$", include=True)]
    max_file_size: int | None = None
    max_depth: int | None = None
