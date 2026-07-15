from typing import Any
from pathlib import Path
from pydantic import BaseModel

# Primitive
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage


class CodeModuleInfo(BaseModel):
    """Information about a discovered code module."""

    name: str
    root_path: Path
    language: CodeLanguage
    entry_points: list[Path]
    metadata: dict[str, Any]  # Additional language-specific metadata


class CodeModuleFileInfo(BaseModel):
    """Structured information about a file within a code module for linkage."""

    code: Code
    relative_path: str  # Path relative to module
    is_entry_point: bool
