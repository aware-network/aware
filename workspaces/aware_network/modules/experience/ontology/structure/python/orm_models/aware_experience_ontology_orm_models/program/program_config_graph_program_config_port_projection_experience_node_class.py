from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node_class_identity import (
        ProjectionExperienceNodeClassIdentity,
    )


class ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass(ORMModel):
    """
    Graph-level binding edge for one program port-node contract.
    Contract:
    - Wires one ProgramConfigPortProjectionExperienceNode requirement to one
    shared projection node-class identity bridge.
    - Keeps ProgramConfig pure contract while enabling deterministic runtime resolution.
    """

    # Relationships
    projection_experience_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(
        default=None, exclude=True
    )
    program_config_port_projection_experience_node: ProgramConfigPortProjectionExperienceNode | None = Field(
        default=None, exclude=True
    )

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    program_config_graph_program_config_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphProgramConfig.port_projection_experience_node_classes"
    )
    projection_experience_node_class_identity_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.projection_experience_node_class_identity"
    )
    program_config_port_projection_experience_node_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.program_config_port_projection_experience_node"
    )
