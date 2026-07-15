from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.role.role_class_instance import RoleClassInstance
    from aware_identity_ontology_dto.role.role_config import RoleConfig
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class Role(BaseModel):
    # Relationships
    role_class_instances: list[RoleClassInstance] = Field(default_factory=list)
    role_config: RoleConfig | None = Field(default=None)
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)

    # Attributes
    object_instance_graph_branch_key: str = Field(default="all")
