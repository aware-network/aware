from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_sdk_ontology_dto.sdk.sdk_operation import SdkOperation


class SdkOperationDependency(BaseModel):
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
