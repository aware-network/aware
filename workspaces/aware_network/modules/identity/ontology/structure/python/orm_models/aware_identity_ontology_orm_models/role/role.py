from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.role.role_class_instance import RoleClassInstance
    from aware_identity_ontology_orm_models.role.role_config import RoleConfig
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class Role(ORMModel):
    # Relationships
    role_class_instances: list[RoleClassInstance] = Field(default_factory=list)
    role_config: RoleConfig | None = Field(default=None, exclude=True)
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None, exclude=True)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Attributes
    object_instance_graph_branch_key: str = Field(default="all")

    # Foreign Keys
    role_config_id: UUID = Field(description="Foreign key for Role.role_config")
    object_instance_graph_identity_id: UUID = Field(description="Foreign key for Role.object_instance_graph_identity")
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for Role.object_instance_graph_branch"
    )
