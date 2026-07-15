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
    from aware_interface_ontology.interface.render_component_package import RenderComponentPackage


class InterfacePackageRenderComponentPackage(ORMModel):
    # Relationships
    render_component_package: RenderComponentPackage

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    interface_package_id: UUID = Field(description="Foreign key for InterfacePackage.render_component_packages")
    render_component_package_id: UUID | None = Field(
        default=None, description="Foreign key for InterfacePackageRenderComponentPackage.render_component_package"
    )

    @classmethod
    async def build_via_interface_package(
        cls, interface_package_id: UUID, render_component_package_id: UUID, description: str | None = None
    ) -> InterfacePackageRenderComponentPackage:
        """
        Create one package-level Interface bridge to one RenderComponentPackage.

        Contract:
        - Parent `InterfacePackage` scope is injected by propagation.
        - Identity is keyed by the attached `RenderComponentPackage`.
        - This is the package/import seam for renderer component registries available to an
          Interface package.
        - It does not replace pane-level render specs or view/action/state bindings.
        """

        payload = {
            "interface_package_id": interface_package_id,
            "render_component_package_id": render_component_package_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_interface_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfacePackageRenderComponentPackage):
            return value
        return InterfacePackageRenderComponentPackage.validate_invocation_value(value)


class InterfacePackageRenderComponentPackageBuildViaInterfacePackageInput(BaseModel):
    interface_package_id: UUID = Field(description="Foreign key for InterfacePackage.render_component_packages")
    render_component_package_id: UUID
    description: str | None = Field(default=None)


class InterfacePackageRenderComponentPackageBuildViaInterfacePackageOutput(BaseModel):
    value: InterfacePackageRenderComponentPackage


FUNCTIONS = {
    "InterfacePackageRenderComponentPackage": {
        "build_via_interface_package": {
            "canonical": {
                "name": "build_via_interface_package",
                "description": "Create one package-level Interface bridge to one RenderComponentPackage.\n\nContract:\n- Parent `InterfacePackage` scope is injected by propagation.\n- Identity is keyed by the attached `RenderComponentPackage`.\n- This is the package/import seam for renderer component registries available to an\n  Interface package.\n- It does not replace pane-level render specs or view/action/state bindings.",
                "is_constructor": True,
            },
            "input": InterfacePackageRenderComponentPackageBuildViaInterfacePackageInput,
            "output": InterfacePackageRenderComponentPackageBuildViaInterfacePackageOutput,
        },
    },
}

__all__ = [
    "InterfacePackageRenderComponentPackage",
    "InterfacePackageRenderComponentPackageBuildViaInterfacePackageInput",
    "InterfacePackageRenderComponentPackageBuildViaInterfacePackageOutput",
    "FUNCTIONS",
]
