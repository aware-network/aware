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


class CodeSemanticPackageBinding(ORMModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None)

    # Attributes
    code_package_config_key: str | None = Field(default=None)
    code_module_name: str | None = Field(default=None)
    capabilities: list[str] = Field(default_factory=list)
    manifest_relative_path: str | None = Field(default=None)
    module_package_id: str
    module_package_kind: str | None = Field(default=None)
    module_relative_package_root: str | None = Field(default=None)
    owned_manifest_kinds: list[str] = Field(default_factory=list)
    semantic_contract_module: str | None = Field(default=None)
    semantic_contract_name: str
    semantic_contract_role: str
    status: str = Field(default="bound")

    # Foreign Keys
    code_semantic_provider_registration_id: UUID = Field(
        description="Foreign key for CodeSemanticProviderRegistration.semantic_package_bindings"
    )
    code_package_id: UUID = Field(description="Foreign key for CodeSemanticPackageBinding.code_package")
