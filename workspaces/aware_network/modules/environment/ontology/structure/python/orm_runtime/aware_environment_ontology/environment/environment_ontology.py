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
    from aware_environment_ontology.environment.environment import Environment
    from aware_ontology_ontology.ontology.ontology import Ontology


class EnvironmentOntology(ORMModel):
    """
    Runtime Environment to Ontology authority bridge.
    Contract:
    - Environment records which Ontology authorities are available in this
    runtime territory.
    - Ontology owns ObjectInstanceGraphIdentity inventory discovery.
    - This bridge must not duplicate OIG/OIGI membership.
    """

    # Relationships
    ontology: Ontology | None = Field(default=None)
    environment: Environment | None = Field(
        default=None, exclude=True, description="Reverse view for Environment.ontologies"
    )

    # Attributes
    role: str = Field(default="runtime")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    environment_id: UUID = Field(description="Foreign key for Environment.ontologies")
    ontology_id: UUID = Field(description="Foreign key for EnvironmentOntology.ontology")

    @classmethod
    async def build_via_environment(
        cls,
        environment_id: UUID,
        ontology_id: UUID,
        role: str = "runtime",
        status: str = "active",
        title: str | None = None,
        description: str | None = None,
    ) -> EnvironmentOntology:
        """
        Construct one Environment-owned Ontology membership.

        Contract:
        - Parent Environment scope is injected by propagation.
        - Identity is Environment path plus target Ontology.
        - `ontology_id` points to the Ontology authority root.
        - OIGI inventory remains reachable only from the linked Ontology.
        """

        payload = {
            "environment_id": environment_id,
            "ontology_id": ontology_id,
            "role": role,
            "status": status,
            "title": title,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentOntology):
            return value
        return EnvironmentOntology.validate_invocation_value(value)


class EnvironmentOntologyBuildViaEnvironmentInput(BaseModel):
    environment_id: UUID = Field(description="Foreign key for Environment.ontologies")
    ontology_id: UUID
    role: str = Field(default="runtime")
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)


class EnvironmentOntologyBuildViaEnvironmentOutput(BaseModel):
    value: EnvironmentOntology


FUNCTIONS = {
    "EnvironmentOntology": {
        "build_via_environment": {
            "canonical": {
                "name": "build_via_environment",
                "description": "Construct one Environment-owned Ontology membership.\n\nContract:\n- Parent Environment scope is injected by propagation.\n- Identity is Environment path plus target Ontology.\n- `ontology_id` points to the Ontology authority root.\n- OIGI inventory remains reachable only from the linked Ontology.",
                "is_constructor": True,
            },
            "input": EnvironmentOntologyBuildViaEnvironmentInput,
            "output": EnvironmentOntologyBuildViaEnvironmentOutput,
        },
    },
}

__all__ = [
    "EnvironmentOntology",
    "EnvironmentOntologyBuildViaEnvironmentInput",
    "EnvironmentOntologyBuildViaEnvironmentOutput",
    "FUNCTIONS",
]
