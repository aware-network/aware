from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config_function_config import ClassConfigFunctionConfig


class ApiGraphFunction(ORMModel):
    # Relationships
    class_config_function_config: ClassConfigFunctionConfig | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_graph_id: UUID = Field(description="Foreign key for ApiGraph.api_graph_functions")
    class_config_function_config_id: UUID = Field(
        description="Foreign key for ApiGraphFunction.class_config_function_config"
    )
