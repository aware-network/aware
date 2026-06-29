from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.module.code_module import CodeModule


class CodeModuleDependence(ORMModel):
    # Relationships
    dependence: CodeModule | None = Field(default=None)

    # Attributes
    name: str

    # Foreign Keys
    code_module_id: UUID = Field(description="Foreign key for CodeModule.dependences")
    dependence_id: UUID = Field(description="Foreign key for CodeModuleDependence.dependence")
