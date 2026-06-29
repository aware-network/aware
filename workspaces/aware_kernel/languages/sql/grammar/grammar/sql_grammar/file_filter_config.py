"""SQL file filter for file system introspection."""

from aware_file_system.config import FilterConfig, RegexConfig


class SQLFileFilterConfig(FilterConfig):
    """Filter configuration specifically for SQL files."""

    use_gitignore: bool = True
    regex: list[RegexConfig] = [RegexConfig(pattern=r".*\.sql$", include=True)]
    max_file_size: int | None = None
    max_depth: int | None = None
