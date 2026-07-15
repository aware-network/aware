from uuid import UUID

from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_branch_relationship_id,
)


def test_stable_object_instance_graph_branch_relationship_id_is_deterministic() -> None:
    a = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    b = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    assert stable_object_instance_graph_branch_relationship_id(
        object_instance_graph_branch_id=a,
        target_object_instance_graph_branch_id=b,
    ) == stable_object_instance_graph_branch_relationship_id(
        object_instance_graph_branch_id=a,
        target_object_instance_graph_branch_id=b,
    )
    assert stable_object_instance_graph_branch_relationship_id(
        object_instance_graph_branch_id=a,
        target_object_instance_graph_branch_id=b,
    ) != stable_object_instance_graph_branch_relationship_id(
        object_instance_graph_branch_id=b,
        target_object_instance_graph_branch_id=a,
    )
