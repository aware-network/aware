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


class SdkSurfaceMethod(ORMModel):
    """
    SDK surface method truth.
    Surface methods are the stable SDK-facing method contract that renderers can
    project into CLI commands, Skill targets, or other invocation affordances.
    """

    # Relationships
    target_sdk_operation: SdkOperation | None = Field(default=None)

    # Attributes
    name: str
    operation_ref: str
    operation_name: str
    method_family: str
    effect: str = Field(default="read")
    mutation_scope: str = Field(default="none")
    confirmation_policy: str = Field(default="none")
    execution_mode: str = Field(default="request_response")
    runtime_binding_kind: str = Field(default="unbound")
    description: str | None = Field(default=None)

    # Foreign Keys
    sdk_surface_id: UUID = Field(description="Foreign key for SdkSurface.methods")
    target_sdk_operation_id: UUID | None = Field(
        default=None, description="Foreign key for SdkSurfaceMethod.target_sdk_operation"
    )

    @classmethod
    async def create_via_sdk_surface(
        cls,
        sdk_surface_id: UUID,
        name: str,
        target_sdk_operation_id: UUID,
        operation_ref: str,
        operation_name: str,
        method_family: str,
        effect: str = "read",
        mutation_scope: str = "none",
        confirmation_policy: str = "none",
        execution_mode: str = "request_response",
        runtime_binding_kind: str = "unbound",
        description: str | None = None,
    ) -> SdkSurfaceMethod:
        """
        Create one deterministic SDK surface method.

        Contract:
        - Parent `SdkSurface` scope is injected by propagation.
        - `target_sdk_operation_id` points at local SDK operation truth.
        - `method_family` is a stable small taxonomy, not a product verb.
        - Effect and confirmation policy are explicit; runtime adapters must not
          infer safety from operation names once this metadata is present.
        """

        payload = {
            "sdk_surface_id": sdk_surface_id,
            "name": name,
            "target_sdk_operation_id": target_sdk_operation_id,
            "operation_ref": operation_ref,
            "operation_name": operation_name,
            "method_family": method_family,
            "effect": effect,
            "mutation_scope": mutation_scope,
            "confirmation_policy": confirmation_policy,
            "execution_mode": execution_mode,
            "runtime_binding_kind": runtime_binding_kind,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_sdk_surface", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkSurfaceMethod):
            return value
        return SdkSurfaceMethod.validate_invocation_value(value)


class SdkSurfaceMethodCreateViaSdkSurfaceInput(BaseModel):
    sdk_surface_id: UUID = Field(description="Foreign key for SdkSurface.methods")
    name: str
    target_sdk_operation_id: UUID
    operation_ref: str
    operation_name: str
    method_family: str
    effect: str = Field(default="read")
    mutation_scope: str = Field(default="none")
    confirmation_policy: str = Field(default="none")
    execution_mode: str = Field(default="request_response")
    runtime_binding_kind: str = Field(default="unbound")
    description: str | None = Field(default=None)


class SdkSurfaceMethodCreateViaSdkSurfaceOutput(BaseModel):
    value: SdkSurfaceMethod


FUNCTIONS = {
    "SdkSurfaceMethod": {
        "create_via_sdk_surface": {
            "canonical": {
                "name": "create_via_sdk_surface",
                "description": "Create one deterministic SDK surface method.\n\nContract:\n- Parent `SdkSurface` scope is injected by propagation.\n- `target_sdk_operation_id` points at local SDK operation truth.\n- `method_family` is a stable small taxonomy, not a product verb.\n- Effect and confirmation policy are explicit; runtime adapters must not\n  infer safety from operation names once this metadata is present.",
                "is_constructor": True,
            },
            "input": SdkSurfaceMethodCreateViaSdkSurfaceInput,
            "output": SdkSurfaceMethodCreateViaSdkSurfaceOutput,
        },
    },
}

__all__ = [
    "SdkSurfaceMethod",
    "SdkSurfaceMethodCreateViaSdkSurfaceInput",
    "SdkSurfaceMethodCreateViaSdkSurfaceOutput",
    "FUNCTIONS",
]
