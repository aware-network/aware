from uuid import UUID

from aware_identity_ontology.role.role import Role


def build_role(
    role_config_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_branch_key: str = "all",
    object_instance_graph_branch_id: UUID | None = None,
) -> Role:
    return Role(
        role_config_id=role_config_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_branch_key=object_instance_graph_branch_key,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
    )
