from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.attention.attention_package_layout_config import AttentionPackageLayoutConfig
    from aware_code_ontology_dto.package.code_package import CodePackage


class AttentionPackage(BaseModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    layout_configs: list[AttentionPackageLayoutConfig] = Field(default_factory=list)

    # Attributes
    name: str
