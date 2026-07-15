from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_sdk_ontology.sdk.sdk_operation import SdkOperation


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

    @classmethod
    async def create_via_sdk_operation(
        cls,
        sdk_operation_id: UUID,
        target_sdk_operation_id: UUID,
        target_operation_ref: str,
        target_sdk_name: str,
        target_operation_name: str,
        target_package_name: str | None = None,
        role: str = "dependency",
        order: int = 1,
        required: bool = True,
        description: str | None = None,
    ) -> SdkOperationDependency:
        """
        Create one deterministic SDK operation dependency edge.

        Contract:
        - Parent `SdkOperation` scope is injected by propagation.
        - `target_sdk_operation_id` points at the canonical target operation identity.
        - `target_operation_ref` preserves authored `sdk_name.operation_name` syntax.
        - External operation refs must be backed by a declared `SdkPackageDependency`.
        - Runtime composition may use this edge; API endpoint bindings remain ingress truth.
        """

        payload = {
            "sdk_operation_id": sdk_operation_id,
            "target_sdk_operation_id": target_sdk_operation_id,
            "target_operation_ref": target_operation_ref,
            "target_sdk_name": target_sdk_name,
            "target_operation_name": target_operation_name,
            "target_package_name": target_package_name,
            "role": role,
            "order": order,
            "required": required,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_sdk_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkOperationDependency):
            return value
        return SdkOperationDependency.validate_invocation_value(value)


class SdkOperationDependencyCreateViaSdkOperationInput(BaseModel):
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.sdk_operation_dependencies")
    target_sdk_operation_id: UUID
    target_operation_ref: str
    target_sdk_name: str
    target_operation_name: str
    target_package_name: str | None = Field(default=None)
    role: str = Field(default="dependency")
    order: int = Field(default=1)
    required: bool = Field(default=True)
    description: str | None = Field(default=None)


class SdkOperationDependencyCreateViaSdkOperationOutput(BaseModel):
    value: SdkOperationDependency


FUNCTIONS = {
    "SdkOperationDependency": {
        "create_via_sdk_operation": {
            "canonical": {
                "name": "create_via_sdk_operation",
                "description": "Create one deterministic SDK operation dependency edge.\n\nContract:\n- Parent `SdkOperation` scope is injected by propagation.\n- `target_sdk_operation_id` points at the canonical target operation identity.\n- `target_operation_ref` preserves authored `sdk_name.operation_name` syntax.\n- External operation refs must be backed by a declared `SdkPackageDependency`.\n- Runtime composition may use this edge; API endpoint bindings remain ingress truth.",
                "is_constructor": True,
            },
            "input": SdkOperationDependencyCreateViaSdkOperationInput,
            "output": SdkOperationDependencyCreateViaSdkOperationOutput,
        },
    },
}

__all__ = [
    "SdkOperationDependency",
    "SdkOperationDependencyCreateViaSdkOperationInput",
    "SdkOperationDependencyCreateViaSdkOperationOutput",
    "FUNCTIONS",
]
