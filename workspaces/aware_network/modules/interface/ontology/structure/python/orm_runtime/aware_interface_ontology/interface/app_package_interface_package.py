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
    from aware_interface_ontology.interface.interface_package import InterfacePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class AppPackageInterfacePackage(ORMModel):
    # Relationships
    interface_package: InterfacePackage | None = Field(default=None)
    interface_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    role: str = Field(default="interface")

    # Foreign Keys
    app_package_id: UUID = Field(description="Foreign key for AppPackage.interface_packages")
    interface_package_id: UUID = Field(description="Foreign key for AppPackageInterfacePackage.interface_package")
    interface_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for AppPackageInterfacePackage.interface_package_object_instance_graph_commit",
    )

    @classmethod
    async def build_via_app_package(
        cls,
        app_package_id: UUID,
        interface_package_id: UUID,
        interface_package_object_instance_graph_commit_id: UUID | None = None,
        role: str = "interface",
        description: str | None = None,
    ) -> AppPackageInterfacePackage:
        """
        Create one app package dependency on an InterfacePackage.

        Contract:
        - Parent AppPackage scope is injected by propagation.
        - Identity is keyed by the attached InterfacePackage.
        - InterfacePackage supplies reusable interface composition; AppConfig
          screen selection remains Experience layout-binding oriented.
        """

        payload = {
            "app_package_id": app_package_id,
            "interface_package_id": interface_package_id,
            "interface_package_object_instance_graph_commit_id": interface_package_object_instance_graph_commit_id,
            "role": role,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_app_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, AppPackageInterfacePackage):
            return value
        return AppPackageInterfacePackage.validate_invocation_value(value)


class AppPackageInterfacePackageBuildViaAppPackageInput(BaseModel):
    app_package_id: UUID = Field(description="Foreign key for AppPackage.interface_packages")
    interface_package_id: UUID
    interface_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    role: str = Field(default="interface")
    description: str | None = Field(default=None)


class AppPackageInterfacePackageBuildViaAppPackageOutput(BaseModel):
    value: AppPackageInterfacePackage


FUNCTIONS = {
    "AppPackageInterfacePackage": {
        "build_via_app_package": {
            "canonical": {
                "name": "build_via_app_package",
                "description": "Create one app package dependency on an InterfacePackage.\n\nContract:\n- Parent AppPackage scope is injected by propagation.\n- Identity is keyed by the attached InterfacePackage.\n- InterfacePackage supplies reusable interface composition; AppConfig\n  screen selection remains Experience layout-binding oriented.",
                "is_constructor": True,
            },
            "input": AppPackageInterfacePackageBuildViaAppPackageInput,
            "output": AppPackageInterfacePackageBuildViaAppPackageOutput,
        },
    },
}

__all__ = [
    "AppPackageInterfacePackage",
    "AppPackageInterfacePackageBuildViaAppPackageInput",
    "AppPackageInterfacePackageBuildViaAppPackageOutput",
    "FUNCTIONS",
]
