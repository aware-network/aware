from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.config.object_config_graph_package import ObjectConfigGraphPackage


class ObjectConfigGraphPackageBuild(BaseModel):
    """
    Build intent / invocation settings for building a canonical OCG package.
    This is deliberately separate from ObjectConfigGraphPackage so the package
    spine remains portable and stable, while build knobs can vary per workspace,
    CI job, or environment.
    """

    # Relationships
    object_config_graph_package: ObjectConfigGraphPackage | None = Field(default=None)

    # Attributes
    environment_slug: str
    sources_dir: str = Field(
        default="aware",
        description='Directory containing the canonical `.aware` sources for this package.\nThis is always interpreted relative to the `aware.toml` location.\nDefaults to "aware" (mirrors the `pyproject` convention: package folder matches name).',
    )
    include_paths: list[str] = Field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = Field(default_factory=list)
    force_fresh_scan: bool = Field(default=True)
