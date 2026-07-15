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
    from aware_code_ontology.package.code_package import CodePackage


class EconomyPackage(ORMModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)

    # Attributes
    name: str

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for EconomyPackage.source_code_package"
    )

    @classmethod
    async def build(cls, name: str, source_code_package_id: UUID | None = None) -> EconomyPackage:
        """
        Create the canonical Economy-owned semantic package root.

        Contract:
        - Identity is keyed by Economy package `name`.
        - `EconomyPackage` is the package/public root for authored Economy truth.
        - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
          package.
        - Concrete price/contract materialization remains Economy-owned and will resolve under this
          package rail, not under Service.
        """

        payload = {"name": name, "source_code_package_id": source_code_package_id}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EconomyPackage):
            return value
        return EconomyPackage.validate_invocation_value(value)


class EconomyPackageBuildInput(BaseModel):
    name: str
    source_code_package_id: UUID | None = Field(default=None)


class EconomyPackageBuildOutput(BaseModel):
    value: EconomyPackage


FUNCTIONS = {
    "EconomyPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Economy-owned semantic package root.\n\nContract:\n- Identity is keyed by Economy package `name`.\n- `EconomyPackage` is the package/public root for authored Economy truth.\n- `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf\n  package.\n- Concrete price/contract materialization remains Economy-owned and will resolve under this\n  package rail, not under Service.",
                "is_constructor": True,
            },
            "input": EconomyPackageBuildInput,
            "output": EconomyPackageBuildOutput,
        },
    },
}

__all__ = [
    "EconomyPackage",
    "EconomyPackageBuildInput",
    "EconomyPackageBuildOutput",
    "FUNCTIONS",
]
