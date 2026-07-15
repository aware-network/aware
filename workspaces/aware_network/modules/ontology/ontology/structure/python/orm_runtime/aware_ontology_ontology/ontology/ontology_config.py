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
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology.ontology.ontology import Ontology


class OntologyConfig(ORMModel):
    """
    Canonical config/schema root for one ontology.
    `OntologyPackage` remains package/distribution truth and points at
    `ObjectConfigGraphPackage`. `OntologyConfig` is the ontology-owned config
    root that points at the actual `ObjectConfigGraph` schema it configures.
    """

    # Relationships
    object_config_graph: ObjectConfigGraph | None = Field(default=None)
    object_config_graph_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    ontologies: list[Ontology] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    fqn_prefix: str
    name: str
    schema_hash: str | None = Field(default=None)
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    object_config_graph_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyConfig.object_config_graph"
    )
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyConfig.object_config_graph_object_instance_graph_commit"
    )

    @classmethod
    async def build(
        cls,
        name: str,
        fqn_prefix: str,
        object_config_graph_id: UUID | None = None,
        object_config_graph_object_instance_graph_commit_id: UUID | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        schema_hash: str | None = None,
    ) -> OntologyConfig:
        """
        Create the ontology-owned config/schema root.

        Contract:
        - Identity is keyed by `(name, fqn_prefix)` and intentionally matches
          the package-level semantic identity.
        - `object_config_graph_id` points at Meta-owned schema truth.
        - `object_config_graph_object_instance_graph_commit_id` pins the exact
          OCG root commit used to replay this config.
        - Package-level OCG package replay stays on `OntologyPackage`; the
          config root owns the direct OCG relationship.
        """

        payload = {
            "name": name,
            "fqn_prefix": fqn_prefix,
            "object_config_graph_id": object_config_graph_id,
            "object_config_graph_object_instance_graph_commit_id": object_config_graph_object_instance_graph_commit_id,
            "version_number": version_number,
            "title": title,
            "description": description,
            "schema_hash": schema_hash,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, OntologyConfig):
            return value
        return OntologyConfig.validate_invocation_value(value)

    async def create_ontology(
        self, key: str, title: str | None = None, description: str | None = None, status: str = "active"
    ) -> Ontology:
        """
        Create one concrete ontology authority/worldline for this config.

        Contract:
        - Parent `OntologyConfig` scope is injected by propagation.
        - OIGI membership is registered through the Ontology authority surface;
          this constructor only creates the ontology authority root.
        """

        payload = {"key": key, "title": title, "description": description, "status": status}
        result = await invoke_instance(orm_model=self, function_name="create_ontology", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_ontology_ontology.ontology.ontology import Ontology

        if isinstance(value, Ontology):
            return value
        return Ontology.validate_invocation_value(value)


class OntologyConfigBuildInput(BaseModel):
    name: str
    fqn_prefix: str
    object_config_graph_id: UUID | None = Field(default=None)
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    schema_hash: str | None = Field(default=None)


class OntologyConfigBuildOutput(BaseModel):
    value: OntologyConfig


class OntologyConfigCreateOntologyInput(BaseModel):
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: str = Field(default="active")


class OntologyConfigCreateOntologyOutput(BaseModel):
    value: Ontology


FUNCTIONS = {
    "OntologyConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the ontology-owned config/schema root.\n\nContract:\n- Identity is keyed by `(name, fqn_prefix)` and intentionally matches\n  the package-level semantic identity.\n- `object_config_graph_id` points at Meta-owned schema truth.\n- `object_config_graph_object_instance_graph_commit_id` pins the exact\n  OCG root commit used to replay this config.\n- Package-level OCG package replay stays on `OntologyPackage`; the\n  config root owns the direct OCG relationship.",
                "is_constructor": True,
            },
            "input": OntologyConfigBuildInput,
            "output": OntologyConfigBuildOutput,
        },
        "create_ontology": {
            "canonical": {
                "name": "create_ontology",
                "description": "Create one concrete ontology authority/worldline for this config.\n\nContract:\n- Parent `OntologyConfig` scope is injected by propagation.\n- OIGI membership is registered through the Ontology authority surface;\n  this constructor only creates the ontology authority root.",
                "is_constructor": False,
            },
            "input": OntologyConfigCreateOntologyInput,
            "output": OntologyConfigCreateOntologyOutput,
        },
    },
}

__all__ = [
    "OntologyConfig",
    "OntologyConfigBuildInput",
    "OntologyConfigBuildOutput",
    "OntologyConfigCreateOntologyInput",
    "OntologyConfigCreateOntologyOutput",
    "FUNCTIONS",
]
