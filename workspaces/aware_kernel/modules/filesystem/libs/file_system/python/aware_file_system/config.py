from pydantic import BaseModel, Field
from typing import Optional, List
import yaml

from aware_file_system.configs import get_config_path


class RegexConfig(BaseModel):
    """Configuration for a regex pattern."""

    pattern: str
    include: bool = False


class FilterConfig(BaseModel):
    use_gitignore: bool = True
    regex: List[RegexConfig] = Field(default_factory=list, description="Regex patterns with include/exclude flags")
    max_file_size: Optional[int] = Field(None, description="Maximum file size in bytes")
    max_depth: Optional[int] = None
    ignored_extensions: Optional[List[str]] = Field(
        default=None,
        description="Additional file extensions to ignore (with or without leading dot).",
    )
    ignored_dirs: Optional[List[str]] = Field(
        default=None,
        description="Additional directory names to ignore during scans.",
    )
    inherit_ignore_defaults: bool = Field(
        default=True,
        description="If true, merge custom ignore lists with watcher defaults; otherwise replace them.",
    )


class CodeIntrospectionFilterConfig(FilterConfig):
    """
    Filter configuration specifically for code introspection.

    Combines gitignore patterns with additional exclusions for files that exist
    but aren't relevant for code analysis (images, docs, examples, migrations, etc.)

    This profile is heuristic and non-authoritative. Do not use it for
    canonical workspace status, commit, or delta rails because user-owned source
    can legitimately live under paths such as demos, examples, docs, or README
    files.
    """

    use_gitignore: bool = True
    regex: List[RegexConfig] = Field(
        default_factory=lambda: [
            # Major directory exclusions (high impact)
            RegexConfig(pattern=r".*/docker/supabase(/.*)?$", include=False),
            RegexConfig(pattern=r".*/node_modules(/.*)?$", include=False),
            RegexConfig(pattern=r".*/migrations(/.*)?$", include=False),
            RegexConfig(pattern=r".*/_blog(/.*)?$", include=False),
            # Asset and media files (combined patterns)
            RegexConfig(
                pattern=r".*\.(ttf|otf|woff|woff2|png|jpg|jpeg|gif|ico|svg|webp|mp4|mov|avi)$",
                include=False,
            ),
            RegexConfig(pattern=r".*/assets/(fonts|img|images)(/.*)?$", include=False),
            # Documentation files (essential only)
            RegexConfig(pattern=r".*/README\.md$", include=False),
            RegexConfig(pattern=r".*/\.git(ignore|modules|attributes)$", include=False),
            # Example and demo directories
            RegexConfig(pattern=r".*/example[s]?(/.*)?$", include=False),
            RegexConfig(pattern=r".*/demo[s]?(/.*)?$", include=False),
            # Generated and lock files
            RegexConfig(pattern=r".*\.(min\.js|min\.css|map)$", include=False),
            RegexConfig(pattern=r".*/package-lock\.json$", include=False),
        ]
    )
    max_file_size: Optional[int] = Field(default=None, description="Maximum file size in bytes")
    max_depth: Optional[int] = Field(default=None, description="Maximum depth of the file system")


class CanonicalSourceFilterConfig(FilterConfig):
    """
    Canonical file observation profile for workspace status and deltas.

    The profile excludes infrastructure/runtime noise only. It intentionally
    does not exclude semantic/user path names such as demos, examples, docs,
    README files, migrations, or assets; those names can carry canonical source.
    """

    use_gitignore: bool = True
    regex: List[RegexConfig] = Field(
        default_factory=lambda: [
            RegexConfig(pattern=r".*/\.git(/.*)?$", include=False),
            RegexConfig(pattern=r".*/\.aware(/.*)?$", include=False),
            RegexConfig(pattern=r".*/_aware(/.*)?$", include=False),
            RegexConfig(pattern=r".*/__pycache__(/.*)?$", include=False),
            RegexConfig(pattern=r".*/\.pytest_cache(/.*)?$", include=False),
            RegexConfig(pattern=r".*/\.mypy_cache(/.*)?$", include=False),
            RegexConfig(pattern=r".*/\.ruff_cache(/.*)?$", include=False),
            RegexConfig(pattern=r".*/node_modules(/.*)?$", include=False),
            RegexConfig(pattern=r".*/\.venv(/.*)?$", include=False),
            RegexConfig(pattern=r".*/venv(/.*)?$", include=False),
            RegexConfig(pattern=r".*/build(/.*)?$", include=False),
            RegexConfig(pattern=r".*/dist(/.*)?$", include=False),
            RegexConfig(pattern=r".*/\.dart_tool(/.*)?$", include=False),
            RegexConfig(pattern=r".*/\.fvm(/.*)?$", include=False),
            RegexConfig(pattern=r".*/target(/.*)?$", include=False),
            RegexConfig(pattern=r".*/htmlcov(/.*)?$", include=False),
            RegexConfig(pattern=r".*\.(pyc|pyo|pyd|so|dll|dylib|class)$", include=False),
        ]
    )
    max_file_size: Optional[int] = Field(default=None, description="Maximum file size in bytes")
    max_depth: Optional[int] = Field(default=None, description="Maximum depth of the file system")


class FileSystemConfig(BaseModel):
    root_path: str = Field(..., description="Root directory of the file system to analyze")
    generate_tree: bool = Field(True, description="Generate tree structure of the file system")
    export_json: bool = Field(True, description="Export file system structure to JSON")


class Config(BaseModel):
    file_system: FileSystemConfig = Field(default_factory=FileSystemConfig.model_construct)
    filter: FilterConfig = Field(default_factory=FilterConfig.model_construct)

    @classmethod
    def load_from_file_name(cls, file_name: str = "default.yaml") -> "Config":
        config_path = get_config_path()
        config_file_path = config_path / file_name
        with open(config_file_path, "r") as f:
            config_dict = yaml.safe_load(f)
            return cls.model_validate(config_dict)


# Helper function for creating regex configs
def regex_include(pattern: str) -> RegexConfig:
    """Create an include regex pattern configuration."""
    return RegexConfig(pattern=pattern, include=True)


def regex_exclude(pattern: str) -> RegexConfig:
    """Create an exclude regex pattern configuration."""
    return RegexConfig(pattern=pattern, include=False)
