from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.function.function_config import FunctionConfig


class ClassConfigFunctionConfig(ORMModel):
    # Relationships
    function_config: FunctionConfig

    # Attributes
    is_public: bool = Field(default=True)
    is_constructor: bool = Field(default=False)
    position: int = Field(default=0)

    # Foreign Keys
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_function_configs")
    function_config_id: UUID | None = Field(
        default=None, description="Foreign key for ClassConfigFunctionConfig.function_config"
    )
