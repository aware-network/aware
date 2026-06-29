from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage


class CodeModuleCodePackage(ORMModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None, description="Association target reference to CodePackage")

    # Attributes
    manifest_relative_path: str | None = Field(default=None)
    mirrors_ontology: bool = Field(default=False)
    module_package_id: str | None = Field(default=None)
    module_package_kind: str | None = Field(default=None)
    module_relative_package_root: str | None = Field(default=None)
    semantic_contract_capabilities: list[str] = Field(default_factory=list)
    semantic_contract_module: str | None = Field(default=None)
    semantic_contract_name: str | None = Field(default=None)
    semantic_contract_owns_manifest_kinds: list[str] = Field(default_factory=list)
    semantic_contract_provider_key: str | None = Field(default=None)
    semantic_contract_role: str | None = Field(default=None)
    visibility: str = Field(default="module")

    # Foreign Keys
    code_package_id: UUID = Field(description="Join FK to CodePackage")
    code_module_id: UUID = Field(description="Join FK to CodeModule")
