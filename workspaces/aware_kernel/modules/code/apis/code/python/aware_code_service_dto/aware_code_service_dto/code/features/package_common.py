from __future__ import annotations

# Standard
from enum import Enum


class CodePackagePathRole(Enum):
    """Package-relative path role visible to local filesystem classification."""

    authored_source = "authored_source"
    generated_code = "generated_code"
    generated_manifest = "generated_manifest"
    generated_metadata = "generated_metadata"
