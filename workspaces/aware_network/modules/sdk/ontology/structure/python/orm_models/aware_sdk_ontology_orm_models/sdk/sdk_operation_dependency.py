from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_sdk_ontology_orm_models.sdk.sdk_operation import SdkOperation


class SdkOperationDependency(ORMModel):
    """
    SDK operation-to-operation dependency edge.
    This is SDK composition truth. It does not replace API endpoint bindings;
    it records that one SDK operation is allowed to orchestrate another SDK
    operation from the same SDK config or from a declared SDK package
    dependency closure.
    """

    # Relationships
    target_sdk_operation: SdkOperation | None = Field(default=None)

    # Attributes
    target_operation_ref: str
    target_sdk_name: str
    target_operation_name: str
    target_package_name: str | None = Field(default=None)
    role: str = Field(default="dependency")
    order: int = Field(default=1)
    required: bool = Field(default=True)
    description: str | None = Field(default=None)

    # Foreign Keys
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.sdk_operation_dependencies")
    target_sdk_operation_id: UUID = Field(description="Foreign key for SdkOperationDependency.target_sdk_operation")
