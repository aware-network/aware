"""Python file filter configuration."""

from aware_file_system.config import FilterConfig, RegexConfig


class PythonFileFilterConfig(FilterConfig):
    """Filter configuration specifically for Python files."""

    use_gitignore: bool = True
    regex: list[RegexConfig] = [RegexConfig(pattern=r".*\.py$", include=True)]
    max_file_size: int | None = None
    max_depth: int | None = None
