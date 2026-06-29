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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_sdk_ontology.sdk.sdk_surface_method import SdkSurfaceMethod


class SdkSurface(ORMModel):
    """
    SDK conceptual surface truth.
    A surface groups stable SDK methods around one product concept. It is not a
    CLI command and does not replace API endpoint truth; CLI, Skill, and other
    renderers project from surface methods.
    """

    # Relationships
    methods: list[SdkSurfaceMethod] = Field(default_factory=list)

    # Attributes
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    sdk_config_id: UUID = Field(description="Foreign key for SdkConfig.surfaces")

    async def add_method(
        self,
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
        """Add one stable method under this SDK surface."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="add_method", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_surface_method import SdkSurfaceMethod

        if isinstance(value, SdkSurfaceMethod):
            return value
        return SdkSurfaceMethod.validate_invocation_value(value)

    @classmethod
    async def build_via_sdk_config(
        cls, sdk_config_id: UUID, name: str, title: str | None = None, description: str | None = None
    ) -> SdkSurface:
        """
        Create one SDK-owned conceptual surface.

        Contract:
        - Identity is scoped by parent `SdkConfig` and surface `name`.
        - Surface names are stable conceptual groups, not command paths.
        - Methods bind the surface to SDK operations and effect policy.
        """

        payload = {"sdk_config_id": sdk_config_id, "name": name, "title": title, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_sdk_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkSurface):
            return value
        return SdkSurface.validate_invocation_value(value)


class SdkSurfaceAddMethodInput(BaseModel):
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


class SdkSurfaceAddMethodOutput(BaseModel):
    value: SdkSurfaceMethod


class SdkSurfaceBuildViaSdkConfigInput(BaseModel):
    sdk_config_id: UUID = Field(description="Foreign key for SdkConfig.surfaces")
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class SdkSurfaceBuildViaSdkConfigOutput(BaseModel):
    value: SdkSurface


FUNCTIONS = {
    "SdkSurface": {
        "add_method": {
            "canonical": {
                "name": "add_method",
                "description": "Add one stable method under this SDK surface.",
                "is_constructor": False,
            },
            "input": SdkSurfaceAddMethodInput,
            "output": SdkSurfaceAddMethodOutput,
        },
        "build_via_sdk_config": {
            "canonical": {
                "name": "build_via_sdk_config",
                "description": "Create one SDK-owned conceptual surface.\n\nContract:\n- Identity is scoped by parent `SdkConfig` and surface `name`.\n- Surface names are stable conceptual groups, not command paths.\n- Methods bind the surface to SDK operations and effect policy.",
                "is_constructor": True,
            },
            "input": SdkSurfaceBuildViaSdkConfigInput,
            "output": SdkSurfaceBuildViaSdkConfigOutput,
        },
    },
}

__all__ = [
    "SdkSurface",
    "SdkSurfaceAddMethodInput",
    "SdkSurfaceAddMethodOutput",
    "SdkSurfaceBuildViaSdkConfigInput",
    "SdkSurfaceBuildViaSdkConfigOutput",
    "FUNCTIONS",
]
