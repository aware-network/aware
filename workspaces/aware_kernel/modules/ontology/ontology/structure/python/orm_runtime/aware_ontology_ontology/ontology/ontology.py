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
    from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
    from aware_ontology_ontology.ontology.ontology_config import OntologyConfig


class Ontology(ORMModel):
    """
    Concrete ontology authority/worldline.
    `Ontology` is the instance/runtime layer materialized under
    `OntologyConfig.ontologies`; it indexes the ObjectInstanceGraphIdentity
    worldlines that exist under this ontology authority.
    """

    # Relationships
    object_instance_graph_identities: list[ObjectInstanceGraphIdentity] = Field(default_factory=list)
    ontology_config: OntologyConfig | None = Field(
        default=None, exclude=True, description="Reverse view for OntologyConfig.ontologies"
    )

    # Attributes
    description: str | None = Field(default=None)
    key: str
    status: str = Field(default="active")
    title: str | None = Field(default=None)

    # Foreign Keys
    ontology_config_id: UUID = Field(description="Foreign key for OntologyConfig.ontologies")

    @classmethod
    async def build_via_ontology_config(
        cls,
        ontology_config_id: UUID,
        key: str,
        title: str | None = None,
        description: str | None = None,
        status: str = "active",
    ) -> Ontology:
        """
        Create one concrete ontology authority/worldline.

        Contract:
        - Parent `OntologyConfig` scope is injected by propagation.
        - Identity is parent-scoped by `OntologyConfig.ontologies` plus `key`;
          the child does not author a reverse config reference.
        - `object_instance_graph_identities` is a reference/index surface for
          all OIGIs known to belong under this ontology authority.
        - Head/commit selection remains Meta/history truth and is not modeled
          as a shortcut on `Ontology`.
        """

        payload = {
            "ontology_config_id": ontology_config_id,
            "key": key,
            "title": title,
            "description": description,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_ontology_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Ontology):
            return value
        return Ontology.validate_invocation_value(value)


class OntologyBuildViaOntologyConfigInput(BaseModel):
    ontology_config_id: UUID = Field(description="Foreign key for OntologyConfig.ontologies")
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: str = Field(default="active")


class OntologyBuildViaOntologyConfigOutput(BaseModel):
    value: Ontology


FUNCTIONS = {
    "Ontology": {
        "build_via_ontology_config": {
            "canonical": {
                "name": "build_via_ontology_config",
                "description": "Create one concrete ontology authority/worldline.\n\nContract:\n- Parent `OntologyConfig` scope is injected by propagation.\n- Identity is parent-scoped by `OntologyConfig.ontologies` plus `key`;\n  the child does not author a reverse config reference.\n- `object_instance_graph_identities` is a reference/index surface for\n  all OIGIs known to belong under this ontology authority.\n- Head/commit selection remains Meta/history truth and is not modeled\n  as a shortcut on `Ontology`.",
                "is_constructor": True,
            },
            "input": OntologyBuildViaOntologyConfigInput,
            "output": OntologyBuildViaOntologyConfigOutput,
        },
    },
}

__all__ = [
    "Ontology",
    "OntologyBuildViaOntologyConfigInput",
    "OntologyBuildViaOntologyConfigOutput",
    "FUNCTIONS",
]
