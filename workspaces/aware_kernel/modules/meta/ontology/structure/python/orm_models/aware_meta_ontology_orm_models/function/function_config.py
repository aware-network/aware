from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_config_enums import FunctionKind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.function.code_section_function import CodeSectionFunction
    from aware_meta_ontology_orm_models.function.function_config_attribute_config import FunctionConfigAttributeConfig
    from aware_meta_ontology_orm_models.function.function_config_invocation import FunctionConfigInvocation
    from aware_meta_ontology_orm_models.function.function_impl import FunctionImpl


class FunctionConfig(ORMModel):
    # Relationships
    function_config_attribute_configs: list[FunctionConfigAttributeConfig] = Field(default_factory=list)
    invocations: list[FunctionConfigInvocation] = Field(default_factory=list)
    function_impl: FunctionImpl | None = Field(default=None)
    code_section_function: CodeSectionFunction | None = Field(default=None, exclude=True)

    # Attributes
    owner_key: str
    name: str
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    is_async: bool = Field(default=False)
    kind: FunctionKind = Field(default=FunctionKind.instance)

    # Foreign Keys
    code_section_function_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionConfig.code_section_function"
    )
