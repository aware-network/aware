from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_config_enums import FunctionKind

if TYPE_CHECKING:
    from aware_code_ontology_dto.function.code_section_function import CodeSectionFunction
    from aware_meta_ontology_dto.function.function_config_attribute_config import FunctionConfigAttributeConfig
    from aware_meta_ontology_dto.function.function_config_invocation import FunctionConfigInvocation
    from aware_meta_ontology_dto.function.function_impl import FunctionImpl


class FunctionConfig(BaseModel):
    # Relationships
    function_config_attribute_configs: list[FunctionConfigAttributeConfig] = Field(default_factory=list)
    invocations: list[FunctionConfigInvocation] = Field(default_factory=list)
    function_impl: FunctionImpl | None = Field(default=None)
    code_section_function: CodeSectionFunction | None = Field(default=None)

    # Attributes
    owner_key: str
    name: str
    description: str | None = Field(default=None)
    verb: str | None = Field(default=None)
    is_async: bool = Field(default=False)
    kind: FunctionKind = Field(default=FunctionKind.instance)
