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
    from aware_environment_ontology.environment.environment_config import EnvironmentConfig
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology.ontology.ontology_config import OntologyConfig


class EnvironmentConfigOntologyConfig(ORMModel):
    # Relationships
    ontology_config: OntologyConfig | None = Field(default=None)
    ontology_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    environment_config: EnvironmentConfig | None = Field(
        default=None, exclude=True, description="Reverse view for EnvironmentConfig.ontology_configs"
    )

    # Attributes
    fqn_prefix: str
    name: str

    # Foreign Keys
    environment_config_id: UUID = Field(description="Foreign key for EnvironmentConfig.ontology_configs")
    ontology_config_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentConfigOntologyConfig.ontology_config"
    )
    ontology_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentConfigOntologyConfig.ontology_config_object_instance_graph_commit",
    )

    @classmethod
    async def build_via_environment_config(
        cls,
        environment_config_id: UUID,
        name: str,
        fqn_prefix: str,
        ontology_config_object_instance_graph_commit_id: UUID | None = None,
    ) -> EnvironmentConfigOntologyConfig:
        """
        Create a deterministic EnvironmentConfig-owned edge to one OntologyConfig.

        Contract:
        - Parent `EnvironmentConfig` scope is injected by propagation.
        - Target OntologyConfig identity is resolved from `(name, fqn_prefix)`.
        - OCG authority remains on `OntologyConfig.object_config_graph`.
        - The optional commit pin lets runtime replay exact ontology config truth
          without reopening source manifests.
        """

        payload = {
            "environment_config_id": environment_config_id,
            "name": name,
            "fqn_prefix": fqn_prefix,
            "ontology_config_object_instance_graph_commit_id": ontology_config_object_instance_graph_commit_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_environment_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentConfigOntologyConfig):
            return value
        return EnvironmentConfigOntologyConfig.validate_invocation_value(value)


class EnvironmentConfigOntologyConfigBuildViaEnvironmentConfigInput(BaseModel):
    environment_config_id: UUID = Field(description="Foreign key for EnvironmentConfig.ontology_configs")
    name: str
    fqn_prefix: str
    ontology_config_object_instance_graph_commit_id: UUID | None = Field(default=None)


class EnvironmentConfigOntologyConfigBuildViaEnvironmentConfigOutput(BaseModel):
    value: EnvironmentConfigOntologyConfig


FUNCTIONS = {
    "EnvironmentConfigOntologyConfig": {
        "build_via_environment_config": {
            "canonical": {
                "name": "build_via_environment_config",
                "description": "Create a deterministic EnvironmentConfig-owned edge to one OntologyConfig.\n\nContract:\n- Parent `EnvironmentConfig` scope is injected by propagation.\n- Target OntologyConfig identity is resolved from `(name, fqn_prefix)`.\n- OCG authority remains on `OntologyConfig.object_config_graph`.\n- The optional commit pin lets runtime replay exact ontology config truth\n  without reopening source manifests.",
                "is_constructor": True,
            },
            "input": EnvironmentConfigOntologyConfigBuildViaEnvironmentConfigInput,
            "output": EnvironmentConfigOntologyConfigBuildViaEnvironmentConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentConfigOntologyConfig",
    "EnvironmentConfigOntologyConfigBuildViaEnvironmentConfigInput",
    "EnvironmentConfigOntologyConfigBuildViaEnvironmentConfigOutput",
    "FUNCTIONS",
]
