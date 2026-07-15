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


class PanePackageRenderComponentPackage(ORMModel):
    # Relationships
    render_component_package: RenderComponentPackage

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    pane_package_id: UUID = Field(description="Foreign key for PanePackage.render_component_packages")
    render_component_package_id: UUID | None = Field(
        default=None, description="Foreign key for PanePackageRenderComponentPackage.render_component_package"
    )

    @classmethod
    async def build_via_pane_package(
        cls, pane_package_id: UUID, render_component_package_id: UUID, description: str | None = None
    ) -> PanePackageRenderComponentPackage:
        """
        Create one package-level Pane bridge to one RenderComponentPackage.

        Contract:
        - Parent `PanePackage` scope is injected by propagation.
        - Identity is keyed by the attached `RenderComponentPackage`.
        - This declares which rich renderer component contracts a pane package may reference from
          authored render specs.
        - Components remain reusable renderer capabilities; they never replace PaneConfig,
          PaneRenderSpec, or canonical StateBinding/ActionBinding truth.
        """

        payload = {
            "pane_package_id": pane_package_id,
            "render_component_package_id": render_component_package_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_pane_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PanePackageRenderComponentPackage):
            return value
        return PanePackageRenderComponentPackage.validate_invocation_value(value)


class PanePackageRenderComponentPackageBuildViaPanePackageInput(BaseModel):
    pane_package_id: UUID = Field(description="Foreign key for PanePackage.render_component_packages")
    render_component_package_id: UUID
    description: str | None = Field(default=None)


class PanePackageRenderComponentPackageBuildViaPanePackageOutput(BaseModel):
    value: PanePackageRenderComponentPackage


FUNCTIONS = {
    "PanePackageRenderComponentPackage": {
        "build_via_pane_package": {
            "canonical": {
                "name": "build_via_pane_package",
                "description": "Create one package-level Pane bridge to one RenderComponentPackage.\n\nContract:\n- Parent `PanePackage` scope is injected by propagation.\n- Identity is keyed by the attached `RenderComponentPackage`.\n- This declares which rich renderer component contracts a pane package may reference from\n  authored render specs.\n- Components remain reusable renderer capabilities; they never replace PaneConfig,\n  PaneRenderSpec, or canonical StateBinding/ActionBinding truth.",
                "is_constructor": True,
            },
            "input": PanePackageRenderComponentPackageBuildViaPanePackageInput,
            "output": PanePackageRenderComponentPackageBuildViaPanePackageOutput,
        },
    },
}

__all__ = [
    "PanePackageRenderComponentPackage",
    "PanePackageRenderComponentPackageBuildViaPanePackageInput",
    "PanePackageRenderComponentPackageBuildViaPanePackageOutput",
    "FUNCTIONS",
]
