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
    from aware_interface_ontology.interface.pane_package import PanePackage


class InterfacePackagePanePackage(ORMModel):
    # Relationships
    pane_package: PanePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    interface_package_id: UUID = Field(description="Foreign key for InterfacePackage.pane_packages")
    pane_package_id: UUID = Field(description="Foreign key for InterfacePackagePanePackage.pane_package")

    @classmethod
    async def build_via_interface_package(
        cls, interface_package_id: UUID, pane_package_id: UUID, description: str | None = None
    ) -> InterfacePackagePanePackage:
        """
        Create one package-level Interface bridge to one PanePackage.

        Contract:
        - Parent `InterfacePackage` scope is injected by propagation.
        - Identity is keyed by the attached `PanePackage`.
        - This is the package/import seam for authored Interface pane composition.
        - It does not replace config-level PaneConfig composition inside InterfaceConfig.
        """

        payload = {
            "interface_package_id": interface_package_id,
            "pane_package_id": pane_package_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_interface_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfacePackagePanePackage):
            return value
        return InterfacePackagePanePackage.validate_invocation_value(value)


class InterfacePackagePanePackageBuildViaInterfacePackageInput(BaseModel):
    interface_package_id: UUID = Field(description="Foreign key for InterfacePackage.pane_packages")
    pane_package_id: UUID
    description: str | None = Field(default=None)


class InterfacePackagePanePackageBuildViaInterfacePackageOutput(BaseModel):
    value: InterfacePackagePanePackage


FUNCTIONS = {
    "InterfacePackagePanePackage": {
        "build_via_interface_package": {
            "canonical": {
                "name": "build_via_interface_package",
                "description": "Create one package-level Interface bridge to one PanePackage.\n\nContract:\n- Parent `InterfacePackage` scope is injected by propagation.\n- Identity is keyed by the attached `PanePackage`.\n- This is the package/import seam for authored Interface pane composition.\n- It does not replace config-level PaneConfig composition inside InterfaceConfig.",
                "is_constructor": True,
            },
            "input": InterfacePackagePanePackageBuildViaInterfacePackageInput,
            "output": InterfacePackagePanePackageBuildViaInterfacePackageOutput,
        },
    },
}

__all__ = [
    "InterfacePackagePanePackage",
    "InterfacePackagePanePackageBuildViaInterfacePackageInput",
    "InterfacePackagePanePackageBuildViaInterfacePackageOutput",
    "FUNCTIONS",
]
