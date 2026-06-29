from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

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
    from aware_sdk_ontology.sdk.sdk_operation import SdkOperation
    from aware_sdk_ontology.sdk.sdk_surface import SdkSurface


class SdkConfig(ORMModel):
    """
    Canonical SDK semantic root.
    SDKs are local orchestration surfaces over committed API contracts. They do
    not own API ingress truth; operation endpoint bindings point back to
    `ApiCapabilityEndpoint`.
    """

    # Relationships
    operations: list[SdkOperation] = Field(default_factory=list)
    surfaces: list[SdkSurface] = Field(default_factory=list)

    # Attributes
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)

    @classmethod
    async def build(cls, name: str, title: str | None = None, description: str | None = None) -> SdkConfig:
        """
        Create one canonical reusable SDK definition.

        Contract:
        - `SdkConfig` is the semantic orchestration root for generated/handwritten SDK surfaces.
        - `SdkOperation` is SDK-owned local operation truth.
        - `SdkOperationApiCapabilityEndpoint` binds each SDK operation to API-owned endpoint truth.
        - Runtime language adapters consume this config; they do not invent SDK/API contracts.
        """

        payload = {"name": name, "title": title, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkConfig):
            return value
        return SdkConfig.validate_invocation_value(value)

    async def add_operation(
        self, name: str, title: str | None = None, description: str | None = None, implementation_ref: str | None = None
    ) -> SdkOperation:
        """Add one SDK-owned operation under this SDK config."""

        payload = {"name": name, "title": title, "description": description, "implementation_ref": implementation_ref}
        result = await invoke_instance(orm_model=self, function_name="add_operation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_operation import SdkOperation

        if isinstance(value, SdkOperation):
            return value
        return SdkOperation.validate_invocation_value(value)

    async def add_surface(self, name: str, title: str | None = None, description: str | None = None) -> SdkSurface:
        """Add one SDK-owned conceptual surface under this SDK config."""

        payload = {"name": name, "title": title, "description": description}
        result = await invoke_instance(orm_model=self, function_name="add_surface", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_surface import SdkSurface

        if isinstance(value, SdkSurface):
            return value
        return SdkSurface.validate_invocation_value(value)


class SdkConfigBuildInput(BaseModel):
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class SdkConfigBuildOutput(BaseModel):
    value: SdkConfig


class SdkConfigAddOperationInput(BaseModel):
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    implementation_ref: str | None = Field(default=None)


class SdkConfigAddOperationOutput(BaseModel):
    value: SdkOperation


class SdkConfigAddSurfaceInput(BaseModel):
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class SdkConfigAddSurfaceOutput(BaseModel):
    value: SdkSurface


FUNCTIONS = {
    "SdkConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one canonical reusable SDK definition.\n\nContract:\n- `SdkConfig` is the semantic orchestration root for generated/handwritten SDK surfaces.\n- `SdkOperation` is SDK-owned local operation truth.\n- `SdkOperationApiCapabilityEndpoint` binds each SDK operation to API-owned endpoint truth.\n- Runtime language adapters consume this config; they do not invent SDK/API contracts.",
                "is_constructor": True,
            },
            "input": SdkConfigBuildInput,
            "output": SdkConfigBuildOutput,
        },
        "add_operation": {
            "canonical": {
                "name": "add_operation",
                "description": "Add one SDK-owned operation under this SDK config.",
                "is_constructor": False,
            },
            "input": SdkConfigAddOperationInput,
            "output": SdkConfigAddOperationOutput,
        },
        "add_surface": {
            "canonical": {
                "name": "add_surface",
                "description": "Add one SDK-owned conceptual surface under this SDK config.",
                "is_constructor": False,
            },
            "input": SdkConfigAddSurfaceInput,
            "output": SdkConfigAddSurfaceOutput,
        },
    },
}

__all__ = [
    "SdkConfig",
    "SdkConfigBuildInput",
    "SdkConfigBuildOutput",
    "SdkConfigAddOperationInput",
    "SdkConfigAddOperationOutput",
    "SdkConfigAddSurfaceInput",
    "SdkConfigAddSurfaceOutput",
    "FUNCTIONS",
]
