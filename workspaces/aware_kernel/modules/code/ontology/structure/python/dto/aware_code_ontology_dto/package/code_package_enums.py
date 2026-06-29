from __future__ import annotations

# Standard
from enum import Enum


class CodePackageConfigInputKind(Enum):
    manifest = "manifest"
    artifact = "artifact"
    package = "package"
    graph = "graph"
    delta = "delta"


class CodePackageConfigOutputKind(Enum):
    artifact = "artifact"
    code_package_delta = "code_package_delta"
    package = "package"


class CodePackageArtifactStatus(Enum):
    available = "available"
    missing = "missing"
    stale = "stale"
    optional = "optional"
    failed = "failed"


class CodePackageConfigRuntimeContextKind(Enum):
    ontology_package = "ontology_package"
    projection = "projection"
    environment = "environment"
    execution_context = "execution_context"
