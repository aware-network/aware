from pathlib import Path

from pydantic import BaseModel

from aware_code.semantic_package.schemas import SemanticPackageDescriptor
from aware_code_ontology.code.code_enums import CodeLanguage


class CodePackageInfo(BaseModel):
    """Information about a discovered code package."""

    name: str
    root_path: Path
    manifest_path: Path
    language: CodeLanguage
    metadata: dict[str, object]
    semantic_packages: tuple[SemanticPackageDescriptor, ...] = ()
